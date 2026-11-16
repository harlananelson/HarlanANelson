// Run: node tests/maat-deeplink.test.js
// W6 / R1-09: deep-link allowlists must not accept Object.prototype names.
"use strict";
var assert = require("assert");
var page = require("./lib/maat-page.js");
function load(hash, search, initial) {
  var h = page.load({ hash: hash, search: search, store: initial });
  return { store: h.store, frames: h.frames(), threw: h.threw };
}

var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}

test("harness builds the page (sanity)", function () {
  var h = load("#practice?lang=es");
  assert.ok(!h.threw, h.threw && h.threw.message);
  assert.ok(/lang=es/.test(h.frames["view-practice"].dataset.src), h.frames["view-practice"].dataset.src);
});

["constructor", "__proto__", "toString", "hasOwnProperty", "valueOf"].forEach(function (name) {
  test("tool=" + name + " is dropped and not remembered", function () {
    var h = load("#tools?tool=" + name);
    assert.ok(!h.threw, h.threw && h.threw.message);
    var lt = h.store["maat.tools.lastTool"];
    assert.ok(lt === undefined || lt === "remarkable", "stored lastTool=" + lt);
  });
  test("lang=" + name + " is dropped (not passed to Practice)", function () {
    var h = load("#practice?lang=" + name);
    assert.ok(!h.threw, h.threw && h.threw.message);
    assert.ok(!/lang=/.test(h.frames["view-practice"].dataset.src), h.frames["view-practice"].dataset.src);
  });
  test("mode=" + name + " falls back to Converse", function () {
    var h = load("#" + name);
    assert.ok(!h.threw, h.threw && h.threw.message);
    assert.ok(h.frames["view-converse"].src, "Converse is the active view");
    assert.ok(!h.frames["view-sermon"].src, "Listen must not be opened");
  });
});

test("a lastTool poisoned by an earlier build is ignored", function () {
  var h = load("#tools", "", { "maat.tools.lastTool": "constructor" });
  assert.ok(!h.threw, h.threw && h.threw.message);
  assert.ok(h.frames["tool-frame-remarkable"], "Tools still builds its frame");
  // The poisoned id must not become the active tool: the real tool is selected
  // and its frame loaded, and the bad value is not written back.
  assert.ok(h.frames["tool-frame-remarkable"].src, "reMarkable frame was loaded (active tool fell back to remarkable)");
  assert.notStrictEqual(h.store["maat.tools.lastTool"], "constructor");
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
