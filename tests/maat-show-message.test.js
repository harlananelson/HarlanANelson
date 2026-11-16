// Run: node tests/maat-show-message.test.js
// DECISION NEEDED PR (R3-05, shell side): show() tells the Converse frame which
// tab is showing, with an explicit targetOrigin, so it can close its mic.
"use strict";
var assert = require("assert");
var harness = require("./lib/maat-show-harness.js");
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}
function showMsgs(h) {
  return h.frames()["view-converse"].posted.filter(function (p) { return p.msg && p.msg.type === "maat-show"; });
}

test("switching to Listen tells the Converse frame (explicit origin)", function () {
  var h = harness.load({});
  assert.ok(!h.threw, h.threw && h.threw.message);
  h.clickTab("sermon");
  var m = showMsgs(h);
  assert.ok(m.length >= 1, "a maat-show message was posted to Converse");
  assert.strictEqual(m[m.length - 1].msg.id, "sermon");
  m.forEach(function (p) { assert.notStrictEqual(p.origin, "*"); assert.strictEqual(p.origin, "https://harlananelson.com"); });
});

test("returning to Converse says so", function () {
  var h = harness.load({});
  h.clickTab("sermon"); h.clickTab("converse");
  var m = showMsgs(h);
  assert.strictEqual(m[m.length - 1].msg.id, "converse");
});

test("a declined 'leave Listen while recording' confirm does not tell Converse anything new", function () {
  var h = harness.load({ hash: "#sermon", confirm: false });
  h.post("view-sermon", "https://harlan-b550-aorus-pro-ac.taila21a91.ts.net:8443", { type: "maat-recording", on: true });
  var before = showMsgs(h).length;
  h.clickTab("converse");
  assert.strictEqual(showMsgs(h).length, before);
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
