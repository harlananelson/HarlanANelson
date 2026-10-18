/* Listen stream guard.
 *
 * Spanish sermon transcript comes first. This module decides what becomes a
 * line: clear decoder loops collapse to one line marked ×N (they are not
 * deleted), rhetorical repetition stays, and a server segment id is accepted
 * once so a reconnect cannot append the same row again.
 *
 * The translation choice for Scripture is NOT here — see
 * live-translator-passage.js. This file does not call a model.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  if (root) { root.ListenStream = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // Inside one line, 4+ copies of the same short phrase are a decoder loop.
  // A second copy of the same finished sentence is a duplicate row.
  // Alternating different sentences are real preaching.
  var MIN_REPEATS = 4;
  var MIN_CONSECUTIVE = 2;
  var MAX_GRAM = 8;
  // Whisper's compression_ratio_threshold. Used only together with a
  // repeated n-gram that already covers most of the line, so ordinary
  // Spanish prose is not collapsed.
  var COMPRESSION_RATIO_THRESHOLD = 2.4;
  var COVERAGE = 0.7;

  // One short vocabulary hint. Silas and Sila are both here so the
  // recognizer is not pulled toward "Silvia". It is NOT chained onto the
  // previous transcript: condition_on_previous_text is how loops start.
  var SERMON_PROMPT = 'Pablo, Silas, Sila, Macedonia, calabozo, Espíritu Santo.';

  var UNCERTAIN_WORD_RULE =
    'If a word is not a real word or looks mis-heard, do not guess a replacement and do not invent a gloss. ' +
    'Leave the word and mark it with [?]. Write “carnavozo [?]”, not a guessed spelling, and “pasemonia [?]”, never “phantom”.';

  // The model must not turn a mild exclamation into a swear, or add words
  // the speaker did not say. The post-check flags a miss; it does not invent
  // a milder English word in its place.
  var LITERAL_TRANSLATION_RULE =
    'Translate literally. Do not intensify, add, or invent words that are not in the source. ' +
    'Never introduce profanity. A mild exclamation stays mild: “caramba” is like “wow” or “gosh”, never “damn”. ' +
    'Do not strengthen the tone beyond the words that were said.';

  var EN_PROFANITY_RE = /\b(?:god\s*damn(?:ed)?|goddammit|dammit|damn(?:ed)?(?:\s+it)?|motherfuckers?|fuck(?:ing|ed|er)?|shitty|shit|assholes?|bitches|bitch|what the hell|the hell)\b/gi;
  var ES_STRONG = {
    mierda: 1, joder: 1, jodido: 1, jodida: 1, carajo: 1, puta: 1, puto: 1,
    coño: 1, cojones: 1, cabrón: 1, cabron: 1, malparido: 1, verga: 1,
    chingar: 1, chingada: 1, pinche: 1, pendejo: 1, pendeja: 1,
    maldición: 1, maldicion: 1, maldito: 1, maldita: 1
  };

  function flagUnmatchedProfanity(source, translation) {
    var original = String(translation == null ? '' : translation);
    var srcKeys = {};
    tokenize(source).forEach(function (w) {
      var k = wordKey(w);
      if (k) { srcKeys[k] = true; }
    });
    if (Object.keys(srcKeys).some(function (k) { return ES_STRONG[k]; })) {
      return { flagged: false, text: original, words: [] };
    }
    var words = [];
    var text = original.replace(EN_PROFANITY_RE, function (m, offset, whole) {
      var after = whole.slice(offset + m.length, offset + m.length + 6);
      if (/^\s*\[\?\]/.test(after)) { return m; }
      words.push(m);
      return m + ' [?]';
    });
    return { flagged: words.length > 0, text: text, words: words };
  }

  function sermonPrompt() { return SERMON_PROMPT; }

  // `previous` is accepted so callers cannot accidentally concatenate it.
  function chainPrompt(previous, hint) {
    var h = String(hint == null ? SERMON_PROMPT : hint).replace(/\s+/g, ' ').trim();
    return h;
  }

  function tokenize(text) {
    return String(text == null ? '' : text).replace(/\s+/g, ' ').trim().split(' ').filter(Boolean);
  }

  function wordKey(w) {
    return String(w || '').toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '');
  }

  function norm(text) {
    return tokenize(text).map(wordKey).filter(Boolean).join(' ');
  }

  function tidy(s) {
    return String(s || '').replace(/\s+/g, ' ').replace(/[\s,;:.!?…]+$/g, '').trim();
  }

  function marker(base, count) {
    // Keep sentence punctuation ("Amén."). Only a trailing comma is noise
    // left over from a repeated fragment.
    var b = String(base || '').replace(/\s+/g, ' ').replace(/[\s,;:]+$/g, '').trim();
    return b + ' ×' + count;
  }

  // Join recognized pieces in order. Never keep only the last piece:
  // "hizo Pablo, adoró, cantaron Sila" has to survive the join.
  function joinUtterance(parts) {
    return (parts || []).map(function (p) {
      return String(p == null ? '' : p).replace(/\s+/g, ' ').trim();
    }).filter(Boolean).join(' ');
  }

  function compareHeard(heard, outputs) {
    var joined = Array.isArray(outputs) ? outputs.join(' ') : String(outputs || '');
    var heardKeys = norm(heard).split(' ').filter(Boolean);
    var outKeys = norm(joined).split(' ').filter(Boolean);
    var outSet = {};
    outKeys.forEach(function (w) { outSet[w] = (outSet[w] || 0) + 1; });
    var missing = [];
    heardKeys.forEach(function (w) {
      if (!outSet[w] && missing.indexOf(w) < 0) { missing.push(w); }
    });
    return {
      missing: missing,
      hasSilvia: !!outSet.silvia,
      hasDice: !!outSet.dice
    };
  }

  function utf8Bytes(text) {
    if (typeof TextEncoder !== 'undefined') { return new TextEncoder().encode(String(text || '')); }
    var s = unescape(encodeURIComponent(String(text || '')));
    var out = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) { out[i] = s.charCodeAt(i) & 255; }
    return out;
  }

  // Byte-oriented LZ77 size, enough to tell a 40× hallucination from a sentence.
  function compressionRatio(text) {
    var bytes = utf8Bytes(text);
    var n = bytes.length;
    if (n < 24) { return 1; }
    var out = 0;
    var i = 0;
    var window = 512;
    while (i < n) {
      var best = 0;
      var start = i - window;
      if (start < 0) { start = 0; }
      var step = (i - start) > 256 ? 2 : 1;
      for (var j = start; j < i; j += step) {
        var k = 0;
        var limit = n - i;
        if (limit > 64) { limit = 64; }
        while (k < limit && bytes[i + k] === bytes[j + k]) { k++; }
        if (k > best) { best = k; }
      }
      if (best >= 4) { out += 3; i += best; }
      else { out += 1; i += 1; }
    }
    return n / Math.max(1, out);
  }

  function sameGram(keys, a, b, n) {
    for (var k = 0; k < n; k++) {
      if (!keys[a + k] || keys[a + k] !== keys[b + k]) { return false; }
    }
    return true;
  }

  function packHit(words, start, n, count) {
    var base = tidy(words.slice(start, start + n).join(' '));
    if (!base) { return null; }
    return {
      start: start,
      n: n,
      count: count,
      covered: count * n,
      base: base,
      key: norm(base)
    };
  }

  // Consecutive short gram. Misses a repeated sentence longer than MAX_GRAM.
  function findGram(words, keys) {
    var best = null;
    var n, i, count, j, covered, hit;
    for (n = 1; n <= MAX_GRAM && n <= Math.floor(keys.length / MIN_REPEATS); n++) {
      for (i = 0; i + n * MIN_REPEATS <= keys.length; i++) {
        count = 1;
        j = i + n;
        while (j + n <= keys.length && sameGram(keys, i, j, n)) {
          count++;
          j += n;
        }
        if (count < MIN_REPEATS) { continue; }
        covered = count * n;
        if (covered < keys.length * COVERAGE) { continue; }
        if (!best || covered > best.covered || (covered === best.covered && n < best.n)) {
          hit = packHit(words, i, n, count);
          if (hit) { best = hit; }
        }
      }
    }
    return best;
  }

  // Period of the suffix, up to a sentence length. This is what catches
  // "usted lo que necesita es un mejor sueldo" when the whole clause repeats
  // and a short gram would only see a rotated slice of it.
  function findPeriod(words, keys) {
    var n = keys.length;
    var maxP = Math.min(32, Math.floor(n / MIN_REPEATS));
    var best = null;
    var p, i, matched, region, count, covered, start, hit;
    for (p = 1; p <= maxP; p++) {
      matched = 0;
      for (i = n - 1; i >= p; i--) {
        if (!keys[i] || keys[i] !== keys[i - p]) { break; }
        matched++;
      }
      if (!matched) { continue; }
      region = matched + p;
      if (region > n) { region = n; }
      count = Math.floor(region / p);
      covered = count * p;
      if (count < MIN_REPEATS || covered < n * COVERAGE) { continue; }
      start = n - covered;
      hit = packHit(words, start, p, count);
      if (!hit) { continue; }
      if (!best || hit.covered > best.covered || (hit.covered === best.covered && hit.count > best.count) ||
          (hit.covered === best.covered && hit.count === best.count && hit.n < best.n)) {
        best = hit;
      }
    }
    return best;
  }

  // A clear intra-line decoder loop: one phrase, 4+ times, covering most of
  // the string. A normal sermon sentence, including parallel wording
  // ("uno … el otro"), does not qualify.
  function detectLoop(text) {
    var words = tokenize(text);
    var keys = words.map(wordKey);
    if (keys.length < MIN_REPEATS) { return null; }
    var gram = findGram(words, keys);
    var period = findPeriod(words, keys);
    var best = null;
    if (period && (!gram || period.covered >= gram.covered)) { best = period; }
    else { best = gram; }
    if (!best) { return null; }
    var ratio = compressionRatio(text);
    // Compression confirms a long loop. A clean 4× gram on a short line
    // (ratio may stay under the threshold) still collapses.
    if (ratio < COMPRESSION_RATIO_THRESHOLD && best.covered < keys.length * 0.9) { return null; }
    return {
      base: best.base,
      count: best.count,
      key: best.key,
      display: marker(best.base, best.count),
      ratio: ratio,
      covered: best.covered
    };
  }

  // Standard Whisper temperature ladder. Attempt 0 is greedy. A later
  // attempt is sampled, still with no previous-text prompt.
  var TEMPERATURES = [0, 0.2, 0.4, 0.6, 0.8, 1.0];

  function decodeDecision(text, attempt) {
    var loop = detectLoop(text);
    var ratio = compressionRatio(text);
    var attemptN = attempt || 0;
    if (attemptN < 0) { attemptN = 0; }
    var hot = !!loop || ratio >= COMPRESSION_RATIO_THRESHOLD;
    var next = attemptN + 1;
    var retry = hot && next < TEMPERATURES.length;
    var useAttempt = retry ? next : Math.min(attemptN, TEMPERATURES.length - 1);
    return {
      loop: loop,
      ratio: ratio,
      retry: retry,
      attempt: useAttempt,
      temperature: TEMPERATURES[useAttempt],
      collapse: !!loop && !retry,
      translate: !hot
    };
  }

  function createTranscript(opts) {
    var minRepeats = (opts && opts.minRepeats) || MIN_REPEATS;
    var minConsecutive = (opts && opts.minConsecutive) || MIN_CONSECUTIVE;
    var lines = [];
    var nextLocal = 1;
    var byServer = {};
    var replay = null;
    var lastKey = '';
    var run = 0;
    var partialLoop = false;

    function snapshot() {
      return lines.map(function (ln) {
        return {
          id: ln.id,
          serverId: ln.serverId,
          text: ln.text,
          base: ln.base,
          key: ln.key,
          count: ln.count,
          collapsed: ln.collapsed
        };
      });
    }

    function find(id) {
      for (var i = 0; i < lines.length; i++) {
        if (lines[i].id === id) { return lines[i]; }
      }
      return null;
    }

    function remember(line, serverId) {
      if (serverId == null || serverId === '') { return; }
      line.serverId = serverId;
      byServer[String(serverId)] = line;
    }

    function pushLine(base, key, count, collapsed, serverId, id) {
      var line = {
        id: id != null ? id : nextLocal++,
        serverId: serverId == null ? null : serverId,
        base: base,
        key: key,
        count: count,
        collapsed: !!collapsed,
        text: collapsed ? marker(base, count) : base
      };
      if (line.id >= nextLocal) { nextLocal = line.id + 1; }
      lines.push(line);
      remember(line, serverId);
      return line;
    }

    function fold(key, count) {
      var group = [];
      var i = lines.length - 1;
      while (i >= 0 && lines[i].key === key) {
        group.unshift(lines[i]);
        i--;
      }
      if (!group.length) { return null; }
      var keep = group[0];
      keep.count = count;
      keep.collapsed = true;
      keep.base = keep.base || keep.text;
      keep.text = marker(keep.base, count);
      var drop = {};
      for (var g = 1; g < group.length; g++) {
        drop[group[g].id] = group[g];
        if (group[g].serverId != null) { byServer[String(group[g].serverId)] = keep; }
      }
      if (group.length > 1) {
        lines = lines.filter(function (ln) { return !drop[ln.id]; });
      }
      return keep;
    }

    function partial(text) {
      var loop = detectLoop(text);
      if (!loop) {
        partialLoop = false;
        return { action: 'show', text: String(text == null ? '' : text), resetAudio: false, translate: true };
      }
      var resetAudio = !partialLoop;
      partialLoop = true;
      return {
        action: 'show',
        text: loop.display,
        resetAudio: resetAudio,
        translate: false,
        collapsed: true,
        count: loop.count
      };
    }

    function add(text, meta) {
      meta = meta || {};
      var serverId = meta.serverId;
      var raw = String(text == null ? '' : text);
      if (serverId != null && serverId !== '' && byServer[String(serverId)]) {
        var existing = byServer[String(serverId)];
        var rewritten = detectLoop(raw);
        if (rewritten) {
          if (existing.collapsed && existing.key === rewritten.key && existing.count === rewritten.count) {
            return { action: 'duplicate', reason: 'id', line: existing, lines: snapshot() };
          }
          existing.base = rewritten.base;
          existing.key = rewritten.key;
          existing.count = rewritten.count;
          existing.collapsed = true;
          existing.text = rewritten.display;
          lastKey = rewritten.key;
          run = minRepeats;
          return { action: 'update', reason: 'id', collapsed: true, translate: false, line: existing, lines: snapshot() };
        }
        if (existing.collapsed || norm(existing.base || existing.text) === norm(raw) || norm(existing.text) === norm(raw)) {
          return { action: 'duplicate', reason: 'id', line: existing, lines: snapshot() };
        }
        existing.base = raw;
        existing.key = norm(raw);
        existing.count = 1;
        existing.collapsed = false;
        existing.text = raw;
        lastKey = existing.key;
        run = 1;
        return { action: 'update', reason: 'id', collapsed: false, translate: true, line: existing, lines: snapshot() };
      }
      var keyNow = norm(raw);
      if (replay && keyNow && replay[keyNow]) {
        return { action: 'duplicate', reason: 'reconnect', lines: snapshot() };
      }
      var loop = detectLoop(raw);
      if (loop) {
        var looped = pushLine(loop.base, loop.key, loop.count, true, serverId, meta.localId);
        lastKey = loop.key;
        run = minRepeats;
        partialLoop = false;
        return { action: 'keep', collapsed: true, translate: false, line: looped, lines: snapshot() };
      }
      if (keyNow && keyNow === lastKey) { run += 1; }
      else { run = 1; lastKey = keyNow; }
      if (keyNow && run >= minConsecutive) {
        var folded = fold(keyNow, run);
        if (serverId != null && serverId !== '') {
          if (folded) { remember(folded, serverId); }
          else { byServer[String(serverId)] = folded; }
        }
        partialLoop = false;
        return { action: 'collapse', translate: false, count: run, line: folded, lines: snapshot() };
      }
      var line = pushLine(raw, keyNow, 1, false, serverId, meta.localId);
      partialLoop = false;
      return { action: 'keep', collapsed: false, translate: true, line: line, lines: snapshot() };
    }

    function beginReplay() {
      replay = {};
      lines.forEach(function (ln) {
        if (ln.key) { replay[ln.key] = true; }
        var b = norm(ln.base || '');
        if (b) { replay[b] = true; }
      });
    }

    function endReplay() { replay = null; }

    function retry(id) {
      var line = find(id);
      if (!line) { return { ok: false, length: lines.length }; }
      return { ok: true, line: line, length: lines.length, added: false };
    }

    return {
      partial: partial,
      add: add,
      beginReplay: beginReplay,
      endReplay: endReplay,
      retry: retry,
      lines: snapshot
    };
  }

  function enqueueTranslation(queue, job) {
    var next = queue.slice();
    for (var i = 0; i < next.length; i++) {
      if (next[i].id === job.id) { next[i] = job; return next; }
    }
    next.push(job);
    return next;
  }

  function formatMarkdown(lines) {
    var out = ['# Spanish → English Transcript', ''];
    (lines || []).forEach(function (ln) {
      var es = (ln && (ln.text || ln.base)) || '';
      if (!es) { return; }
      out.push(es);
      if (ln.en) { out.push(ln.en); }
      out.push('');
    });
    return out.join('\n').replace(/\n+$/, '\n');
  }

  function createAudioGate(opts) {
    var hangMs = (opts && opts.hangMs) || 1400;
    var maxMs = (opts && opts.maxMs) || 22000;
    var phase = 'idle';
    var sentMs = 0;
    var silenceMs = 0;
    var dropUntilSilence = false;
    return {
      noteFrame: function (f) {
        f = f || {};
        var frameMs = f.frameMs || 0;
        var voiced = f.rms >= f.threshold;
        if (dropUntilSilence) {
          if (!voiced) {
            silenceMs += frameMs;
            if (silenceMs >= hangMs) {
              dropUntilSilence = false;
              silenceMs = 0;
              phase = 'idle';
              sentMs = 0;
            }
          } else {
            silenceMs = 0;
          }
          return { send: false, reset: false, reason: 'repetition' };
        }
        if (!voiced) {
          if (phase !== 'open') { return { send: false, sendPreroll: false, reset: false, reason: 'silence' }; }
          silenceMs += frameMs;
          if (silenceMs >= hangMs) {
            phase = 'idle';
            sentMs = 0;
            silenceMs = 0;
            return { send: false, reset: false, trimmed: true, reason: 'silence' };
          }
          sentMs += frameMs;
          return { send: true, reset: false };
        }
        var opening = phase !== 'open';
        silenceMs = 0;
        phase = 'open';
        sentMs += frameMs;
        if (sentMs >= maxMs) {
          phase = 'idle';
          sentMs = 0;
          return { send: true, sendPreroll: opening, reset: true, reason: 'max' };
        }
        return { send: true, sendPreroll: opening, reset: false };
      },
      forceReset: function () {
        phase = 'idle';
        sentMs = 0;
        silenceMs = 0;
        dropUntilSilence = true;
        return { reset: true, reason: 'repetition' };
      },
      sentMs: function () { return sentMs; }
    };
  }

  // Decode options for one utterance. No previous-text prompt. Temperature
  // 0 is greedy; a fallback attempt samples. compression_ratio_threshold is
  // the client-side gate (this on-device build does not apply it itself).
  function whisperDecodeOptions(language, attempt) {
    var i = attempt || 0;
    if (i < 0) { i = 0; }
    if (i >= TEMPERATURES.length) { i = TEMPERATURES.length - 1; }
    var temperature = TEMPERATURES[i];
    var opts = {
      task: 'transcribe',
      return_timestamps: false,
      temperature: temperature,
      do_sample: temperature > 0,
      compression_ratio_threshold: COMPRESSION_RATIO_THRESHOLD,
      condition_on_previous_text: false,
      condition_on_prev_tokens: false
    };
    if (language) { opts.language = language; }
    return opts;
  }

  return {
    MIN_REPEATS: MIN_REPEATS,
    MIN_CONSECUTIVE: MIN_CONSECUTIVE,
    COMPRESSION_RATIO_THRESHOLD: COMPRESSION_RATIO_THRESHOLD,
    TEMPERATURES: TEMPERATURES,
    SERMON_PROMPT: SERMON_PROMPT,
    UNCERTAIN_WORD_RULE: UNCERTAIN_WORD_RULE,
    LITERAL_TRANSLATION_RULE: LITERAL_TRANSLATION_RULE,
    flagUnmatchedProfanity: flagUnmatchedProfanity,
    sermonPrompt: sermonPrompt,
    chainPrompt: chainPrompt,
    joinUtterance: joinUtterance,
    compareHeard: compareHeard,
    norm: norm,
    compressionRatio: compressionRatio,
    detectLoop: detectLoop,
    decodeDecision: decodeDecision,
    createTranscript: createTranscript,
    enqueueTranslation: enqueueTranslation,
    formatMarkdown: formatMarkdown,
    createAudioGate: createAudioGate,
    whisperDecodeOptions: whisperDecodeOptions
  };
});
