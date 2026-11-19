/* Scripture cards for Listen.
 *
 * Change PASSAGE_TRANSLATIONS to switch the text that is shown. Only the
 * ids in PASSAGE_SOURCES are fetched. NIV is not a source. The card never
 * reads a model string (ev.es / ev.en): those have come back as copyright
 * commentary instead of the verse.
 *
 * English default: World English Bible (web). Also allowed: kjv, asv.
 * Spanish default: Reina-Valera 1909 (rv1909), fetched as getBible "valera".
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  if (root) { root.ListenPassage = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var PASSAGE_TRANSLATIONS = {
    en: 'web',
    es: 'rv1909'
  };

  var PASSAGE_SOURCES = {
    web: { getbible: 'web', lang: 'en', name: 'World English Bible' },
    kjv: { getbible: 'kjv', lang: 'en', name: 'King James Version' },
    asv: { getbible: 'asv', lang: 'en', name: 'American Standard Version' },
    rv1909: { getbible: 'valera', lang: 'es', name: 'Reina-Valera 1909' }
  };

  var QUERY = 'https://query.getbible.net/v2/';

  var REFUSAL = [
    /\bbiblica\b/i,
    /\bcopyright\b/i,
    /\bNIV\b/,
    /new international version/i,
    /nueva versi[oó]n internacional/i,
    /riquezas injustas/i,
    /all rights reserved/i,
    /\bno puedo\b/i,
    /\bi can(?:not|'t)\b/i,
    /as an ai\b/i
  ];

  var cache = {};

  function translations() {
    return { en: PASSAGE_TRANSLATIONS.en, es: PASSAGE_TRANSLATIONS.es };
  }

  function sourceFor(id) {
    if (!id || !PASSAGE_SOURCES[id]) { return null; }
    return PASSAGE_SOURCES[id];
  }

  function isRefusal(text) {
    var s = String(text || '');
    if (!s.trim()) { return true; }
    for (var i = 0; i < REFUSAL.length; i++) {
      if (REFUSAL[i].test(s)) { return true; }
    }
    return false;
  }

  function cleanRef(ref) {
    var s = String(ref == null ? '' : ref).replace(/\s+/g, ' ').trim();
    if (!s || s.length > 120 || isRefusal(s)) { return ''; }
    return s;
  }

  function formatLine(ref, text) {
    if (!ref) { return ''; }
    if (text) { return '📖 ' + ref + ' — ' + text; }
    return '📖 ' + ref;
  }

  function verseTextFromQuery(payload) {
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) { return ''; }
    if (payload.code || payload.type && payload.status) { return ''; }
    var chapters = [];
    Object.keys(payload).forEach(function (k) {
      var ch = payload[k];
      if (ch && Array.isArray(ch.verses)) { chapters.push(ch); }
    });
    chapters.sort(function (a, b) {
      return (a.book_nr || 0) - (b.book_nr || 0) || (a.chapter || 0) - (b.chapter || 0);
    });
    var parts = [];
    chapters.forEach(function (ch) {
      var verses = ch.verses.slice().sort(function (a, b) { return (a.verse || 0) - (b.verse || 0); });
      verses.forEach(function (v) {
        var t = String(v && v.text || '').replace(/\s+/g, ' ').trim();
        if (t) { parts.push(t); }
      });
    });
    var text = parts.join(' ');
    if (!text || isRefusal(text)) { return ''; }
    return text;
  }

  function lookupUrl(translationId, reference) {
    var src = sourceFor(translationId);
    var ref = cleanRef(reference);
    if (!src || !ref) { return ''; }
    return QUERY + src.getbible + '/' + encodeURIComponent(ref);
  }

  function cardFromEvent(ev, texts) {
    texts = texts || {};
    var refEs = cleanRef(ev && ev.ref_es);
    var refEn = cleanRef(ev && ev.ref_en);
    var esText = (!texts.es || isRefusal(texts.es)) ? '' : String(texts.es).replace(/\s+/g, ' ').trim();
    var enText = (!texts.en || isRefusal(texts.en)) ? '' : String(texts.en).replace(/\s+/g, ' ').trim();
    return {
      es: formatLine(refEs, esText),
      en: formatLine(refEn, enText),
      ref_es: refEs,
      ref_en: refEn
    };
  }

  function fetchText(url, fetchImpl, opts) {
    if (!url) { return Promise.resolve(''); }
    if (cache[url]) { return Promise.resolve(cache[url]); }
    var ms = (opts && opts.timeoutMs) || 8000;
    var ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) { ctrl.abort(); } }, ms);
    return fetchImpl(url, ctrl ? { signal: ctrl.signal } : undefined).then(function (res) {
      if (!res || !res.ok) { return ''; }
      return res.json();
    }).then(function (json) {
      var text = verseTextFromQuery(json);
      if (text) { cache[url] = text; }
      return text;
    }).catch(function () { return ''; }).then(function (text) {
      clearTimeout(timer);
      return text;
    });
  }

  function fill(ev, opts) {
    opts = opts || {};
    var fetchImpl = opts.fetch || (typeof fetch === 'function' ? fetch : null);
    var chosen = opts.translations || PASSAGE_TRANSLATIONS;
    var refEs = cleanRef(ev && ev.ref_es);
    var refEn = cleanRef(ev && ev.ref_en);
    function refFor(lang) {
      if (lang === 'en') { return refEn || refEs; }
      return refEs || refEn;
    }
    var jobs = ['es', 'en'].map(function (lang) {
      var url = lookupUrl(chosen[lang], refFor(lang));
      if (!url || !fetchImpl) { return Promise.resolve([lang, '']); }
      return fetchText(url, fetchImpl, opts).then(function (text) { return [lang, text]; });
    });
    return Promise.all(jobs).then(function (pairs) {
      var texts = {};
      pairs.forEach(function (p) { texts[p[0]] = p[1]; });
      return cardFromEvent(ev, texts);
    });
  }

  return {
    PASSAGE_TRANSLATIONS: PASSAGE_TRANSLATIONS,
    PASSAGE_SOURCES: PASSAGE_SOURCES,
    translations: translations,
    sourceFor: sourceFor,
    isRefusal: isRefusal,
    cleanRef: cleanRef,
    lookupUrl: lookupUrl,
    verseTextFromQuery: verseTextFromQuery,
    cardFromEvent: cardFromEvent,
    fill: fill
  };
});
