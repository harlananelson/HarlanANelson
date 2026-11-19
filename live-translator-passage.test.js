var test = require('node:test');
var assert = require('node:assert/strict');
var P = require('./live-translator-passage.js');

var RANT = 'Biblica, Inc. me prohibió usar la traducción NIV; han elegido las riquezas injustas en lugar de la libre difusión del Evangelio.';
var WEB = 'But the fruit of the Spirit is love, joy, peace, patience, kindness, goodness, faith, gentleness, and self-control. Against such things there is no law.';
var RV = 'Mas el fruto del Espíritu es: caridad, gozo, paz, tolerancia, benignidad, bondad, fe, Mansedumbre, templanza: contra tales cosas no hay ley.';

function webPayload() {
  return {
    web_48_5: {
      translation: 'World English Bible',
      abbreviation: 'web',
      book_nr: 48,
      book_name: 'Galatians',
      chapter: 5,
      verses: [
        { chapter: 5, verse: 22, text: '  But the fruit of the Spirit is love, joy, peace, patience, kindness, goodness, faith,' },
        { chapter: 5, verse: 23, text: 'gentleness, and self-control. Against such things there is no law.' }
      ]
    }
  };
}

test('the verse card ignores model text, including a Biblica/NIV rant', function () {
  var ev = {
    type: 'passage',
    ref_es: 'Gálatas 5:22-23',
    ref_en: 'Galatians 5:22-23',
    es: RANT,
    en: 'But the fruit of the Spirit is love, joy, peace, forbearance, kindness, goodness, faithfulness, gentleness and self-control.'
  };
  var card = P.cardFromEvent(ev);
  assert.equal(card.es, '📖 Gálatas 5:22-23');
  assert.equal(card.en, '📖 Galatians 5:22-23');
  assert.ok(card.es.indexOf('Biblica') < 0);
  assert.ok(card.en.indexOf('forbearance') < 0);
  assert.equal(P.isRefusal(RANT), true);
});

test('defaults are WEB and Reina-Valera 1909, and NIV is not a source', function () {
  assert.deepEqual(P.translations(), { en: 'web', es: 'rv1909' });
  assert.equal(P.sourceFor('niv'), null);
  assert.equal(P.lookupUrl('niv', 'Galatians 5:22-23'), '');
  assert.match(P.lookupUrl('web', 'Galatians 5:22-23'), /\/v2\/web\/Galatians/);
  assert.match(P.lookupUrl('rv1909', 'Gálatas 5:22-23'), /\/v2\/valera\/G/);
  assert.match(P.lookupUrl('kjv', 'Galatians 5:22'), /\/v2\/kjv\//);
  assert.equal(P.PASSAGE_SOURCES.web.name, 'World English Bible');
  assert.equal(P.PASSAGE_SOURCES.rv1909.name, 'Reina-Valera 1909');
});

test('fill uses the lookup and never the model strings', function () {
  var calls = [];
  function fakeFetch(url) {
    calls.push(url);
    var body = /\/valera\//.test(url)
      ? { valera_48_5: { book_nr: 48, chapter: 5, verses: [
          { verse: 22, text: 'Mas el fruto del Espíritu es: caridad, gozo, paz, tolerancia, benignidad, bondad, fe,' },
          { verse: 23, text: 'Mansedumbre, templanza: contra tales cosas no hay ley.' }
        ] } }
      : webPayload();
    return Promise.resolve({ ok: true, json: function () { return Promise.resolve(body); } });
  }
  var ev = {
    ref_es: 'Gálatas 5:22-23',
    ref_en: 'Galatians 5:22-23',
    es: RANT,
    en: 'NIV fruit of the Spirit'
  };
  return P.fill(ev, { fetch: fakeFetch }).then(function (card) {
    assert.equal(calls.length, 2);
    assert.ok(calls.some(function (u) { return u.indexOf('/web/') >= 0; }));
    assert.ok(calls.some(function (u) { return u.indexOf('/valera/') >= 0; }));
    assert.ok(calls.every(function (u) { return u.indexOf('/niv/') < 0; }));
    assert.equal(card.es, '📖 Gálatas 5:22-23 — ' + RV);
    assert.equal(card.en, '📖 Galatians 5:22-23 — ' + WEB);
    assert.ok(card.es.indexOf('Biblica') < 0);
  });
});

test('a lookup that returns a refusal leaves the reference only', function () {
  function fakeFetch() {
    return Promise.resolve({
      ok: true,
      json: function () {
        return Promise.resolve({ web_1_1: { book_nr: 1, chapter: 1, verses: [{ verse: 1, text: RANT }] } });
      }
    });
  }
  return P.fill(
    { ref_es: 'Génesis 1:1', ref_en: 'Genesis 1:1', es: RANT, en: RANT },
    { fetch: fakeFetch, translations: { en: 'web', es: 'rv1909' } }
  ).then(function (card) {
    assert.equal(card.en, '📖 Genesis 1:1');
    assert.ok(card.en.indexOf('Biblica') < 0);
  });
});

test('switching the config to KJV changes only the English request', function () {
  var calls = [];
  function fakeFetch(url) {
    calls.push(url);
    return Promise.resolve({ ok: false, json: function () { return Promise.resolve({}); } });
  }
  return P.fill(
    { ref_en: 'John 3:16', ref_es: 'Juan 3:16' },
    { fetch: fakeFetch, translations: { en: 'kjv', es: 'rv1909' } }
  ).then(function (card) {
    assert.ok(calls.some(function (u) { return u.indexOf('/kjv/') >= 0; }));
    assert.ok(!calls.some(function (u) { return u.indexOf('/web/') >= 0; }));
    assert.equal(card.en, '📖 John 3:16');
    assert.equal(card.es, '📖 Juan 3:16');
  });
});
