var test = require('node:test');
var assert = require('node:assert/strict');
var fs = require('fs');
var path = require('path');
var A = require('../tools/transcript-align.js');
var S = require('../live-translator-stream.js');

var fixturePath = path.join(__dirname, 'fixtures', 'conocer-a-dios-417.json');
var fx = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));

test('normalization drops case and punctuation and keeps accents', function () {
  assert.equal(A.normalize('El conocer a Dios!'), 'el conocer a dios');
  assert.equal(A.normalize('  corazón,  llegará… '), 'corazón llegará');
  assert.deepEqual(A.tokenize('Abrís, Señor.'), ['abrís', 'señor']);
});

test('alignment starts at the anchor and ignores a preamble', function () {
  var report = A.align(
    'buenas tardes hermanos. El conocer a Dios es bueno.',
    'ruido de fondo. El conocer a Dios es bueno.',
    { anchor: 'El conocer a Dios' }
  );
  assert.equal(report.ok, true);
  assert.equal(report.anchor, 'el conocer a dios');
  assert.ok(report.refStart > 0);
  assert.ok(report.hypStart > 0);
  assert.equal(report.errors, 0);
  assert.equal(report.wer, 0);
});

test('a missing anchor is reported and nothing is scored', function () {
  var report = A.align('hoy hablamos de Pablo', 'hoy hablamos de Silas', { anchor: 'El conocer a Dios' });
  assert.equal(report.ok, false);
  assert.equal(report.reason, 'anchor-not-found');
  assert.equal(report.wer, undefined);
});

test('4:17 conocer a Dios: app text versus the reference, word for word from the anchor', function () {
  var report = A.align(fx.reference, fx.hypothesis, { anchor: fx.anchor });
  assert.equal(report.ok, true);
  assert.equal(report.anchor, 'el conocer a dios');
  assert.equal(report.refStart, 0);
  assert.equal(report.hypStart, 0);
  assert.equal(report.substitutions, 4);
  assert.equal(report.deletions, 16);
  assert.equal(report.insertions, 0);
  assert.equal(report.referenceLength, 90);
  assert.equal(report.errors, 20);
  assert.ok(Math.abs(report.wer - (20 / 90)) < 1e-12);

  assert.deepEqual(report.phrases, [
    { ref: 'mi amada iglesia', hyp: 'que amabilice' },
    { ref: 'perdones', hyp: 'perdonen' },
    { ref: 'toda la humanidad conoce a dios', hyp: '' },
    { ref: 'en tu corazón', hyp: '' },
    { ref: 'tu ser', hyp: '' },
    { ref: 'que', hyp: 'te' },
    { ref: 'entendimiento llegará a ti', hyp: '' }
  ]);

  // The same anchor found without being told the phrase.
  var shared = A.align(fx.reference, fx.hypothesis);
  assert.equal(shared.anchor, 'el conocer a dios');
  assert.equal(shared.errors, report.errors);

  // This capture is the good baseline. The loop guard, the compression
  // gate, and a re-decode decision must leave the app's words alone.
  assert.equal(S.detectLoop(fx.hypothesis), null);
  var decision = S.decodeDecision(fx.hypothesis, 0);
  assert.equal(decision.retry, false);
  assert.equal(decision.collapse, false);
  assert.equal(decision.temperature, 0);
  assert.ok(decision.ratio < S.COMPRESSION_RATIO_THRESHOLD);
  var kept = S.createTranscript().add(fx.hypothesis, { serverId: '417' });
  assert.equal(kept.action, 'keep');
  assert.equal(kept.collapsed, false);
  assert.equal(kept.translate, true);
  assert.equal(kept.lines.length, 1);
  assert.equal(kept.lines[0].text, fx.hypothesis);
  assert.ok(kept.lines[0].text.indexOf('amabilice') >= 0);
  assert.ok(kept.lines[0].text.indexOf('iglesia') < 0);
});
