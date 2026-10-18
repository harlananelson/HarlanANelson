var test = require('node:test');
var assert = require('node:assert/strict');
var R = require('../tools/listen-review.js');

test('review defaults to the Home GPU and refuses a cloud host', function () {
  var gpu = R.reviewTarget({ homeGpuHttp: 'https://gpu.example:8443' });
  assert.equal(gpu.ok, true);
  assert.equal(gpu.cloud, false);
  assert.equal(gpu.engine, 'homegpu');
  assert.equal(gpu.url, 'https://gpu.example:8443/api/review');

  var blank = R.reviewTarget({});
  assert.equal(blank.ok, false);
  assert.equal(blank.reason, 'no-gpu');

  var cloud = R.reviewTarget({ reviewUrl: 'https://api.openai.com/v1/audio/transcriptions' });
  assert.equal(cloud.ok, false);
  assert.equal(cloud.reason, 'cloud-refused');
  assert.equal(cloud.cloud, true);

  var custom = R.reviewTarget({
    homeGpuHttp: 'https://gpu.example:8443',
    reviewUrl: 'https://gpu.example:8443/api/review'
  });
  assert.equal(custom.ok, true);
  assert.equal(custom.cloud, false);
});

test('suggestions are parsed and do not edit the transcript until accepted', function () {
  var lines = [
    { text: 'El conocer a Dios, que amabilice, no te hace que te perdonen los pecados.' }
  ];
  var suggestions = R.parseSuggestions({
    suggestions: [
      { line: 0, from: lines[0].text, to: 'El conocer a Dios, mi amada iglesia, no te hace que te perdones los pecados.', reason: 're-heard the name' },
      { line: 1, from: '', to: 'ignored' }
    ]
  });
  assert.equal(suggestions.length, 1);
  assert.equal(lines[0].text.indexOf('amabilice') >= 0, true);

  var stale = R.acceptSuggestion(lines, { line: 0, from: 'different text', to: 'nope' });
  assert.equal(stale.ok, false);
  assert.equal(stale.lines[0].text, lines[0].text);

  var applied = R.acceptSuggestion(lines, suggestions[0]);
  assert.equal(applied.ok, true);
  assert.equal(applied.line, 0);
  assert.match(applied.lines[0].text, /mi amada iglesia/);
  assert.equal(applied.lines[0].acceptedSuggestion, true);
  assert.match(lines[0].text, /amabilice/);

  var byText = R.acceptSuggestion(lines, {
    from: lines[0].text,
    to: 'El conocer a Dios, mi amada iglesia.'
  });
  assert.equal(byText.ok, true);
  assert.equal(byText.line, 0);
  assert.match(lines[0].text, /amabilice/);
});
