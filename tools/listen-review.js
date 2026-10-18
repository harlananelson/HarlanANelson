/* Post-session transcript review.
 *
 * The recorded audio and the Spanish transcript are sent together. The
 * default destination is the Home GPU. A cloud host is refused. The reply
 * is a list of suggestions; nothing here edits the transcript.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  if (root) { root.ListenReview = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var CLOUD_HOSTS = {
    'api.openai.com': 1,
    'api.anthropic.com': 1
  };

  function reviewTarget(opts) {
    opts = opts || {};
    var raw = String(opts.reviewUrl || '').trim();
    var base = String(opts.homeGpuHttp || '').replace(/\/$/, '');
    var url = raw || (base ? base + '/api/review' : '');
    if (!url) { return { ok: false, reason: 'no-gpu', cloud: false, url: '' }; }
    var host = '';
    try { host = new URL(url).hostname.toLowerCase(); }
    catch (e) { return { ok: false, reason: 'bad-url', cloud: false, url: url }; }
    if (CLOUD_HOSTS[host]) {
      return { ok: false, reason: 'cloud-refused', cloud: true, url: url };
    }
    return { ok: true, reason: '', cloud: false, url: url, engine: 'homegpu' };
  }

  function parseSuggestions(payload) {
    var list = payload && (payload.suggestions || payload.corrections);
    if (!Array.isArray(list)) { return []; }
    var out = [];
    list.forEach(function (s, i) {
      if (!s) { return; }
      var from = String(s.from != null ? s.from : (s.original || '')).trim();
      var to = String(s.to != null ? s.to : (s.suggestion || '')).trim();
      if (!from || !to || from === to) { return; }
      out.push({
        id: s.id != null ? s.id : i,
        line: typeof s.line === 'number' ? s.line : null,
        from: from,
        to: to,
        reason: String(s.reason || '').trim()
      });
    });
    return out;
  }

  function lineText(ln) {
    return ln.text != null ? ln.text : ln.es;
  }

  // Copy the lines and replace one only when the caller has accepted it.
  // A suggestion that does not match the current text is left untouched.
  // A missing line index is resolved by an exact match on `from`.
  function acceptSuggestion(lines, suggestion) {
    var next = (lines || []).map(function (ln) { return Object.assign({}, ln); });
    if (!suggestion || !suggestion.from || suggestion.from === suggestion.to) {
      return { ok: false, reason: 'empty', lines: next };
    }
    var idx = suggestion.line;
    if (typeof idx !== 'number') {
      idx = -1;
      for (var i = 0; i < next.length; i++) {
        if (lineText(next[i]) === suggestion.from) { idx = i; break; }
      }
    }
    if (typeof idx !== 'number' || idx < 0 || !next[idx]) {
      return { ok: false, reason: 'missing-line', lines: next };
    }
    if (lineText(next[idx]) !== suggestion.from) {
      return { ok: false, reason: 'stale', lines: next };
    }
    if (next[idx].text != null) { next[idx].text = suggestion.to; }
    if (next[idx].es != null) { next[idx].es = suggestion.to; }
    next[idx].acceptedSuggestion = true;
    return { ok: true, reason: '', line: idx, lines: next };
  }

  return {
    reviewTarget: reviewTarget,
    parseSuggestions: parseSuggestions,
    acceptSuggestion: acceptSuggestion
  };
});
