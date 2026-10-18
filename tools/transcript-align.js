/* Align a transcript with a separately recorded reference.
 *
 * Harlan's check: find an anchor phrase that appears in both (for example
 * "El conocer a Dios"), then compare word for word from there. Case and
 * punctuation are ignored. Accents stay, because they are part of the word.
 *
 * This does not rewrite either string. It only reports the difference.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) { module.exports = api; }
  if (root) { root.TranscriptAlign = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function normalize(text) {
    return String(text == null ? '' : text)
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]+/gu, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function tokenize(text) {
    var n = normalize(text);
    return n ? n.split(' ') : [];
  }

  function indexOfGram(tokens, gram, from) {
    var start = from || 0;
    if (!gram || !gram.length || gram.length > tokens.length) { return -1; }
    var i, j, ok;
    for (i = start; i <= tokens.length - gram.length; i++) {
      ok = true;
      for (j = 0; j < gram.length; j++) {
        if (tokens[i + j] !== gram[j]) { ok = false; break; }
      }
      if (ok) { return i; }
    }
    return -1;
  }

  // First shared run of `n` words. Scans the reference from the left and
  // takes the earliest hit in the hypothesis.
  function findSharedGram(refTokens, hypTokens, n) {
    var i, slice, at;
    if (n < 1) { return null; }
    for (i = 0; i <= refTokens.length - n; i++) {
      slice = refTokens.slice(i, i + n);
      at = indexOfGram(hypTokens, slice);
      if (at >= 0) { return { ref: i, hyp: at, gram: slice }; }
    }
    return null;
  }

  function locateAnchor(refTokens, hypTokens, opts) {
    opts = opts || {};
    if (opts.anchor) {
      var gram = tokenize(opts.anchor);
      if (!gram.length) { return { ok: false, reason: 'empty-anchor' }; }
      var refAt = indexOfGram(refTokens, gram);
      var hypAt = indexOfGram(hypTokens, gram);
      if (refAt < 0 || hypAt < 0) {
        return { ok: false, reason: 'anchor-not-found', anchor: gram.join(' '), refAt: refAt, hypAt: hypAt };
      }
      return { ok: true, ref: refAt, hyp: hypAt, gram: gram };
    }
    var n = opts.anchorN || 4;
    var found = null;
    var size;
    for (size = n; size >= 2 && !found; size--) {
      found = findSharedGram(refTokens, hypTokens, size);
    }
    if (!found) { return { ok: false, reason: 'anchor-not-found' }; }
    return { ok: true, ref: found.ref, hyp: found.hyp, gram: found.gram };
  }

  // Word-level edit script. Ties prefer a match, then a substitution,
  // then a deletion of a reference word, then an insertion.
  function alignWords(ref, hyp) {
    var n = ref.length;
    var m = hyp.length;
    var dp = [];
    var i, j, sub, del, ins, eq, subCost, delCost, insCost;
    for (i = 0; i <= n; i++) {
      dp[i] = new Array(m + 1);
      dp[i][0] = i;
    }
    for (j = 0; j <= m; j++) { dp[0][j] = j; }
    for (i = 1; i <= n; i++) {
      for (j = 1; j <= m; j++) {
        sub = dp[i - 1][j - 1] + (ref[i - 1] === hyp[j - 1] ? 0 : 1);
        del = dp[i - 1][j] + 1;
        ins = dp[i][j - 1] + 1;
        dp[i][j] = sub < del ? (sub < ins ? sub : ins) : (del < ins ? del : ins);
      }
    }
    var ops = [];
    i = n;
    j = m;
    while (i > 0 || j > 0) {
      eq = i > 0 && j > 0 && ref[i - 1] === hyp[j - 1];
      subCost = (i > 0 && j > 0) ? dp[i - 1][j - 1] + (eq ? 0 : 1) : Infinity;
      delCost = i > 0 ? dp[i - 1][j] + 1 : Infinity;
      insCost = j > 0 ? dp[i][j - 1] + 1 : Infinity;
      if (i > 0 && j > 0 && subCost === dp[i][j] && (eq || (subCost <= delCost && subCost <= insCost))) {
        ops.push({ type: eq ? 'equal' : 'sub', ref: ref[i - 1], hyp: hyp[j - 1] });
        i--;
        j--;
      } else if (i > 0 && delCost === dp[i][j] && delCost <= insCost) {
        ops.push({ type: 'del', ref: ref[i - 1], hyp: '' });
        i--;
      } else {
        ops.push({ type: 'ins', ref: '', hyp: hyp[j - 1] });
        j--;
      }
    }
    ops.reverse();
    return ops;
  }

  function errorPhrases(ops) {
    var out = [];
    var cur = null;
    (ops || []).forEach(function (op) {
      if (!op || op.type === 'equal') {
        if (cur) { out.push(cur); cur = null; }
        return;
      }
      if (!cur) { cur = { ref: [], hyp: [] }; }
      if (op.ref) { cur.ref.push(op.ref); }
      if (op.hyp) { cur.hyp.push(op.hyp); }
    });
    if (cur) { out.push(cur); }
    return out.map(function (p) {
      return { ref: p.ref.join(' '), hyp: p.hyp.join(' ') };
    });
  }

  var SENTENCE_STOP = {
    el: 1, la: 1, los: 1, las: 1, un: 1, una: 1, de: 1, del: 1, al: 1, a: 1,
    y: 1, o: 1, u: 1, que: 1, en: 1, es: 1, no: 1, te: 1, tu: 1, su: 1, se: 1,
    lo: 1, le: 1, me: 1, mi: 1, por: 1, para: 1, con: 1, como: 1
  };

  function splitSentences(text) {
    return String(text == null ? '' : text)
      .split(/(?<=[.!?…])\s+/)
      .map(function (s) { return s.replace(/\s+/g, ' ').trim(); })
      .filter(Boolean);
  }

  function contentWords(tokens) {
    return tokens.filter(function (w) { return w.length > 2 && !SENTENCE_STOP[w]; });
  }

  // How many content words of `need` occur, in order, inside `hay`.
  function coveredCount(need, hay) {
    var found = 0;
    var j = 0;
    var i, at;
    for (i = 0; i < need.length; i++) {
      at = -1;
      for (var k = j; k < hay.length; k++) {
        if (hay[k] === need[i]) { at = k; break; }
      }
      if (at >= 0) { found++; j = at + 1; }
    }
    return found;
  }

  // Whole reference sentences the transcript does not contain, plus
  // sentences that start out present and then drop off. Word-level
  // substitutions inside a sentence that is otherwise there are not misses.
  function missedSentences(reference, hypothesis, opts) {
    opts = opts || {};
    var minCoverage = typeof opts.minCoverage === 'number' ? opts.minCoverage : 0.5;
    var hyp = tokenize(hypothesis);
    var missed = [];
    var partial = [];
    splitSentences(reference).forEach(function (sentence) {
      var words = contentWords(tokenize(sentence));
      if (words.length < 3) { return; }
      var found = coveredCount(words, hyp);
      var coverage = found / words.length;
      var entry = { sentence: sentence, coverage: coverage, words: words.length, found: found };
      if (coverage < minCoverage) { missed.push(entry); return; }
      var tail = 0;
      for (var i = words.length - 1; i >= 0; i--) {
        if (hyp.indexOf(words[i]) < 0) { tail++; }
        else { break; }
      }
      if (tail >= 2) {
        entry.droppedTail = words.slice(words.length - tail).join(' ');
        partial.push(entry);
      }
    });
    return { missed: missed, partial: partial };
  }

  function align(reference, hypothesis, opts) {
    var refTokens = tokenize(reference);
    var hypTokens = tokenize(hypothesis);
    var where = locateAnchor(refTokens, hypTokens, opts);
    if (!where.ok) {
      return {
        ok: false,
        reason: where.reason,
        anchor: where.anchor || '',
        referenceWords: refTokens,
        hypothesisWords: hypTokens
      };
    }
    var refFrom = refTokens.slice(where.ref);
    var hypFrom = hypTokens.slice(where.hyp);
    var ops = alignWords(refFrom, hypFrom);
    var substitutions = 0;
    var deletions = 0;
    var insertions = 0;
    var matches = 0;
    ops.forEach(function (op) {
      if (op.type === 'equal') { matches++; }
      else if (op.type === 'sub') { substitutions++; }
      else if (op.type === 'del') { deletions++; }
      else if (op.type === 'ins') { insertions++; }
    });
    var errors = substitutions + deletions + insertions;
    var denom = refFrom.length;
    return {
      ok: true,
      anchor: where.gram.join(' '),
      refStart: where.ref,
      hypStart: where.hyp,
      ops: ops,
      phrases: errorPhrases(ops),
      matches: matches,
      substitutions: substitutions,
      deletions: deletions,
      insertions: insertions,
      errors: errors,
      referenceLength: denom,
      hypothesisLength: hypFrom.length,
      wer: denom ? errors / denom : 0
    };
  }

  return {
    normalize: normalize,
    tokenize: tokenize,
    indexOfGram: indexOfGram,
    alignWords: alignWords,
    errorPhrases: errorPhrases,
    splitSentences: splitSentences,
    missedSentences: missedSentences,
    align: align
  };
});
