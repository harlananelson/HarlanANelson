var test = require('node:test');
var assert = require('node:assert/strict');
var S = require('./live-translator-stream.js');

var ESPIRITU = 'El Espíritu Santo, ';
var ALABANZA = 'alabanza, bendición, alabanza, bendición,';
var BENDIGA = 'Espíritu Santo, Dios te bendiga.';
var PABLO = 'Por eso que Pablo, a pesar de que esté en Macedonia, callemos a Pablo, está preso.';
var QUIEN = '¿Quién es Pablo?';
var SENTADITO = 'Pablo está sentadito.';

function times(s, n) {
  var out = '';
  for (var i = 0; i < n; i++) { out += s; }
  return out.trim();
}

test('El Espíritu Santo repeated 40 times collapses to one marked instance', function () {
  var raw = times(ESPIRITU, 40);
  var loop = S.detectLoop(raw);
  assert.ok(loop);
  assert.equal(loop.count, 40);
  assert.equal(loop.display, 'El Espíritu Santo ×40');
  assert.ok(loop.display.indexOf('El Espíritu Santo, El Espíritu') < 0);

  var t = S.createTranscript();
  var d = t.add(raw, { serverId: 'p1' });
  assert.equal(d.action, 'keep');
  assert.equal(d.translate, false);
  assert.equal(d.lines.length, 1);
  assert.equal(d.lines[0].text, 'El Espíritu Santo ×40');
  var again = t.add(raw, { serverId: 'p1' });
  assert.equal(again.action, 'duplicate');
  assert.equal(again.lines.length, 1);
});

test('partial Espíritu loop is shown once with a marker and asks for one audio reset', function () {
  var t = S.createTranscript();
  var first = t.partial(times(ESPIRITU, 40));
  var second = t.partial(times(ESPIRITU, 41));
  assert.equal(first.text, 'El Espíritu Santo ×40');
  assert.equal(first.resetAudio, true);
  assert.equal(first.translate, false);
  assert.equal(second.resetAudio, false);
  assert.match(second.text, /×41$/);
  assert.equal(t.lines().length, 0);
});

test('alabanza line repeated twice inside itself is not an intra-line loop', function () {
  assert.equal(S.detectLoop(ALABANZA), null);
});

test('twenty-two identical alabanza lines collapse to one ×22 marker, not 22 rows', function () {
  var t = S.createTranscript();
  var last;
  for (var i = 0; i < 22; i++) {
    last = t.add(ALABANZA, { serverId: 'a' + i });
  }
  assert.equal(last.lines.length, 1);
  assert.equal(last.lines[0].text, 'alabanza, bendición, alabanza, bendición ×22');
  assert.equal(last.translate, false);
  assert.ok(last.action === 'collapse');
});

test('three identical lines stay; the fourth collapses and is not silently deleted', function () {
  var t = S.createTranscript();
  var line = 'Amén.';
  var d3 = null;
  for (var i = 0; i < 3; i++) { d3 = t.add(line, { serverId: 'm' + i }); }
  assert.equal(d3.lines.length, 3);
  assert.equal(d3.action, 'keep');
  var d4 = t.add(line, { serverId: 'm3' });
  assert.equal(d4.action, 'collapse');
  assert.equal(d4.lines.length, 1);
  assert.equal(d4.lines[0].text, 'Amén. ×4'); // period kept; the count is the record of the other three
});

test('alternating Quién es Pablo / sentadito five times is kept as real speech', function () {
  var t = S.createTranscript();
  var d;
  for (var i = 0; i < 5; i++) {
    d = t.add(QUIEN, { serverId: 'q' + i });
    assert.equal(d.action, 'keep');
    d = t.add(SENTADITO, { serverId: 's' + i });
    assert.equal(d.action, 'keep');
  }
  assert.equal(d.lines.length, 10);
  assert.ok(d.lines.every(function (ln) { return ln.text.indexOf('×') < 0; }));
});

test('alternating Bendiga / Pablo lines are not collapsed', function () {
  var t = S.createTranscript();
  var d;
  for (var i = 0; i < 4; i++) {
    d = t.add(BENDIGA, { serverId: 'b' + i });
    d = t.add(PABLO, { serverId: 'p' + i });
  }
  assert.equal(d.lines.length, 8);
  assert.equal(d.lines.filter(function (ln) { return ln.base === PABLO; }).length, 4);
});

test('reconnect resend of the same server id does not add a row', function () {
  var t = S.createTranscript();
  t.add(BENDIGA, { serverId: 7 });
  t.add(PABLO, { serverId: 8 });
  var dup = t.add(PABLO, { serverId: 8 });
  assert.equal(dup.action, 'duplicate');
  assert.equal(dup.reason, 'id');
  assert.equal(dup.lines.length, 2);
});

test('replayed text during reconnect is not appended; the same words after reconnect are', function () {
  var t = S.createTranscript();
  t.add(BENDIGA, { serverId: 1 });
  t.add(PABLO, { serverId: 2 });
  t.beginReplay();
  var replayed = t.add(PABLO, { serverId: 99 });
  assert.equal(replayed.action, 'duplicate');
  assert.equal(replayed.reason, 'reconnect');
  assert.equal(replayed.lines.length, 2);
  t.endReplay();
  var later = t.add(PABLO, { serverId: 100 });
  assert.equal(later.action, 'keep');
  assert.equal(later.lines.length, 3);
});

test('a translation retry does not add a row', function () {
  var t = S.createTranscript();
  var d = t.add(PABLO, { serverId: 3, localId: 3 });
  var before = d.lines.length;
  var retried = t.retry(d.line.id);
  assert.equal(retried.ok, true);
  assert.equal(retried.added, false);
  assert.equal(retried.length, before);
  var q = [];
  q = S.enqueueTranslation(q, { id: 3, text: PABLO });
  q = S.enqueueTranslation(q, { id: 3, text: PABLO });
  assert.equal(q.length, 1);
});

function countWord(text, word) {
  var re = new RegExp('(^|[^\\p{L}\\p{N}])' + word + '(?=$|[^\\p{L}\\p{N}])', 'gu');
  return (text.match(re) || []).length;
}

test('sermon prompt lists Silas and Sila once and is not chained onto previous text', function () {
  var p = S.sermonPrompt();
  ['Pablo', 'Silas', 'Sila', 'Macedonia', 'calabozo'].forEach(function (word) {
    assert.equal(countWord(p, word), 1, word);
  });
  assert.equal(countWord(p, 'Espíritu'), 1);
  assert.equal(countWord(p, 'Silvia'), 0);
  var chained = S.chainPrompt(times(ESPIRITU, 10), p);
  assert.equal(chained, p);
  assert.ok(chained.indexOf('El Espíritu Santo, El') < 0);
  var opts = S.whisperDecodeOptions('spanish');
  assert.equal(opts.language, 'spanish');
  assert.equal(opts.prompt, undefined);
  assert.equal(opts.prompt_ids, undefined);
  assert.equal(opts.temperature, 0);
  assert.equal(opts.do_sample, false);
  assert.equal(opts.compression_ratio_threshold, S.COMPRESSION_RATIO_THRESHOLD);
  assert.equal(opts.condition_on_previous_text, false);
  var retryOpts = S.whisperDecodeOptions('spanish', 1);
  assert.equal(retryOpts.temperature, 0.2);
  assert.equal(retryOpts.do_sample, true);
  assert.equal(retryOpts.prompt, undefined);
  assert.equal(retryOpts.condition_on_previous_text, false);
});

test('uncertain words are flagged, not rewritten or glossed', function () {
  assert.match(S.UNCERTAIN_WORD_RULE, /\[\?\]/);
  assert.match(S.UNCERTAIN_WORD_RULE, /carnavozo/);
  assert.match(S.UNCERTAIN_WORD_RULE, /pasemonia/);
  assert.match(S.UNCERTAIN_WORD_RULE, /never “phantom”/);
  assert.doesNotMatch(S.UNCERTAIN_WORD_RULE, /calabozo/);
  assert.match(S.UNCERTAIN_WORD_RULE, /do not guess/i);
  assert.match(S.UNCERTAIN_WORD_RULE, /do not invent a gloss/i);
});

test('4:07 sermon: heard phrase versus the bad transcript', function () {
  var heard = 'adoro a pesar de que no entienda, adoro a pesar de que no sé lo que está pasando, eso es lo que hizo Pablo, adoró, cantaron Sila, vamos a cantar';
  var app = [
    'Eso es lo que dice Pablo.',
    'Vamos a cantar, Silvia.',
    'Vamos a cantar, Silvia.',
    'Vamos a cantar, Silvia.',
    'Vamos a cantar.'
  ];
  var report = S.compareHeard(heard, app);
  assert.ok(report.missing.indexOf('hizo') >= 0);
  assert.ok(report.missing.indexOf('adoró') >= 0);
  assert.ok(report.missing.indexOf('sila') >= 0);
  assert.equal(report.hasSilvia, true);
  assert.equal(report.hasDice, true);

  var joined = S.joinUtterance([
    'adoro a pesar de que no entienda',
    'adoro a pesar de que no sé lo que está pasando',
    'eso es lo que hizo Pablo',
    'adoró',
    'cantaron Sila',
    'vamos a cantar'
  ]);
  assert.match(joined, /hizo Pablo/);
  assert.match(joined, /adoró/);
  assert.match(joined, /cantaron Sila/);
  assert.doesNotMatch(joined, /Silvia/);
  assert.doesNotMatch(joined, /dice/);

  // Three identical lines are under the 4+ loop threshold, so a real
  // triple is kept. The Silvia line is a mishear, not something to delete.
  var t = S.createTranscript();
  var d;
  for (var i = 0; i < 3; i++) { d = t.add('Vamos a cantar, Silvia.', { serverId: 'v' + i }); }
  assert.equal(d.action, 'keep');
  assert.equal(d.lines.length, 3);
  assert.ok(d.lines.every(function (ln) { return ln.text.indexOf('×') < 0; }));
});

test('markdown keeps Spanish primary and the ×N marker', function () {
  var t = S.createTranscript();
  t.add(times(ESPIRITU, 8));
  t.add(QUIEN);
  var md = S.formatMarkdown(t.lines(), { transcriptOnly: true });
  assert.match(md, /^# Spanish transcript/);
  assert.match(md, /El Espíritu Santo ×8/);
  assert.match(md, /¿Quién es Pablo\?/);
  assert.doesNotMatch(md, /^EN:/m);
});

test('audio gate trims silence and resets at the segment cap', function () {
  var g = S.createAudioGate({ hangMs: 1000, maxMs: 3000 });
  assert.equal(g.noteFrame({ rms: 0, threshold: 0.01, frameMs: 500 }).send, false);
  var started = g.noteFrame({ rms: 0.05, threshold: 0.01, frameMs: 1000 });
  assert.equal(started.send, true);
  assert.equal(started.sendPreroll, true);
  var tail = g.noteFrame({ rms: 0, threshold: 0.01, frameMs: 1000 });
  assert.equal(tail.trimmed, true);
  assert.equal(tail.send, false);
  assert.equal(g.noteFrame({ rms: 0, threshold: 0.01, frameMs: 5000 }).send, false);
  g.noteFrame({ rms: 0.05, threshold: 0.01, frameMs: 2000 });
  var capped = g.noteFrame({ rms: 0.05, threshold: 0.01, frameMs: 2000 });
  assert.equal(capped.reset, true);
  assert.equal(capped.reason, 'max');
  g.forceReset();
  assert.equal(g.noteFrame({ rms: 0.2, threshold: 0.01, frameMs: 100 }).send, false);
});

test('a normal Spanish sentence is not a loop', function () {
  var s = 'Hoy leemos Hechos dieciséis, Pablo y Silas en el calabozo de Filipos.';
  assert.equal(S.detectLoop(s), null);
  assert.ok(S.compressionRatio(s) < S.COMPRESSION_RATIO_THRESHOLD);
});

var SUELDO = 'usted lo que necesita es un mejor sueldo, ';
var CORNELIO = 'El conocer a Dios no hace que tu vida cambie. Toda la humanidad conoce a Dios. No es eso lo que te va a cambiar, es aceptar a Cristo en tu corazón. Me llaman tanto la atención dos hombres, Cornelio y el carcelero. Totalmente diferentes, uno amaba a Dios y el otro no amaba a Dios. Uno buscaba de Dios, el otro ni sabía quién era. Uno ayudaba a los pobres, el otro no ayudaba a nadie. Uno veía ángeles, el otro se quería matar, veía demonios.';

// Maat's 4:17 PM capture, kept as the app wrote it. These are minor
// mishears of the room; the guard must not rewrite or collapse them.
var BASELINE_417 = [
  'Ayudaba a los...',
  'El conocer a Dios, que amabilice,',
  'Y es cuando esa paz te pasa todo'
];

test('4:12 salary hallucination collapses inside a row and in the live partial', function () {
  var row = ('no es un mejor sueldo, ' + times(SUELDO, 8)).trim();
  var loop = S.detectLoop(row);
  assert.ok(loop);
  assert.ok(loop.count >= 8);
  assert.match(loop.base, /usted lo que necesita es un mejor sueldo/);
  assert.match(loop.display, /usted lo que necesita es un mejor sueldo ×/);
  assert.ok(loop.ratio >= S.COMPRESSION_RATIO_THRESHOLD);
  var t = S.createTranscript();
  var d = t.add(row, { serverId: 'sueldo' });
  assert.equal(d.action, 'keep');
  assert.equal(d.collapsed, true);
  assert.equal(d.translate, false);
  assert.equal(d.lines.length, 1);
  assert.match(d.lines[0].text, /×/);
  assert.doesNotMatch(d.lines[0].text, /mejor sueldo, usted lo que necesita es un mejor sueldo/);

  var partial = S.createTranscript().partial('no es un mejor sueldo, ' + times(SUELDO, 30));
  assert.equal(partial.resetAudio, true);
  assert.equal(partial.translate, false);
  assert.match(partial.text, /×30$/);

  var cycle = times('no es un mejor sueldo, usted lo que necesita es un mejor sueldo, ', 8);
  var cycled = S.createTranscript().add(cycle);
  assert.equal(cycled.translate, false);
  assert.equal(cycled.lines.length, 1);
  assert.match(cycled.lines[0].text, /×8$/);

  var again = S.decodeDecision(row, 0);
  assert.equal(again.retry, true);
  assert.equal(again.temperature, 0.2);
  assert.equal(again.translate, false);
  var last = S.decodeDecision(row, S.TEMPERATURES.length - 1);
  assert.equal(last.retry, false);
  assert.equal(last.collapse, true);
});

test('4:17 good capture: a normal non-repetitive Spanish segment passes through untouched', function () {
  BASELINE_417.forEach(function (line) {
    assert.equal(S.detectLoop(line), null, line);
    assert.ok(S.compressionRatio(line) < S.COMPRESSION_RATIO_THRESHOLD, line);
    var decided = S.decodeDecision(line, 0);
    assert.equal(decided.retry, false, line);
    assert.equal(decided.collapse, false, line);
    assert.equal(decided.translate, true, line);
    assert.equal(decided.temperature, 0, line);
    var t = S.createTranscript();
    var d = t.add(line, { serverId: line });
    assert.equal(d.action, 'keep');
    assert.equal(d.collapsed, false);
    assert.equal(d.translate, true);
    assert.equal(d.lines.length, 1);
    assert.equal(d.lines[0].text, line);
    var shown = t.partial(line);
    assert.equal(shown.text, line);
    assert.equal(shown.resetAudio, false);
    assert.equal(shown.translate, true);
  });

  // The Cornelio / carcelero passage is real preaching, not the salary loop.
  // It is a plausibility sample: do not treat it as a correction of the
  // 4:17 lines above (those mishears stay as Maat wrote them).
  assert.equal(S.detectLoop(CORNELIO), null);
  assert.ok(S.compressionRatio(CORNELIO) < S.COMPRESSION_RATIO_THRESHOLD);
  var sermon = S.decodeDecision(CORNELIO, 0);
  assert.equal(sermon.retry, false);
  assert.equal(sermon.collapse, false);
  var book = S.createTranscript();
  var kept = [];
  BASELINE_417.forEach(function (line, i) {
    var d = book.add(line, { serverId: 'b' + i });
    assert.equal(d.action, 'keep');
    kept.push(d.lines[d.lines.length - 1].text);
  });
  var corn = book.add(CORNELIO, { serverId: 'corn' });
  assert.equal(corn.action, 'keep');
  assert.equal(corn.translate, true);
  assert.equal(corn.lines.length, 4);
  assert.deepEqual(kept, BASELINE_417);
  assert.equal(corn.lines[3].text, CORNELIO);
  assert.ok(corn.lines.every(function (ln) { return ln.text.indexOf('×') < 0; }));
  assert.equal(book.lines()[0].text, 'Ayudaba a los...');
  assert.ok(book.lines()[1].text.indexOf('amabilice') >= 0);
  assert.ok(book.lines()[1].text.indexOf('iglesia') < 0);

  // A later correction of the same segment keeps the words it was given.
  var corrected = book.add('Y es cuando esa paz te pasa todo', { serverId: 'b2' });
  assert.equal(corrected.action, 'duplicate');
  assert.equal(book.lines()[2].text, 'Y es cuando esa paz te pasa todo');
  var heardFix = book.add('Y es cuando esa paz que pasa todo entendimiento', { serverId: 'b2' });
  assert.equal(heardFix.action, 'update');
  assert.equal(heardFix.translate, true);
  assert.equal(book.lines()[2].text, 'Y es cuando esa paz que pasa todo entendimiento');
  assert.equal(book.lines().length, 4);
});
