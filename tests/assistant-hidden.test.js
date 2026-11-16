// Run: node tests/assistant-hidden.test.js
// DECISION NEEDED PR (R3-05, subset): Converse must stop its open channel
// (dictate loop) and Grok voice when its Maat tab is hidden or the page is.
"use strict";
var assert = require("assert");
var fs = require("fs");
var path = require("path");
var page = require("./lib/assistant-page.js");
var src = page.script;
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}

// Block under test, run against stubs for the page's channel state.
function blockEnv(state) {
  var a = src.indexOf("/* maat-hidden-stop:start */");
  assert.ok(a >= 0, "maat-hidden-stop block missing");
  var block = src.slice(a, src.indexOf("/* maat-hidden-stop:end */"));
  var calls = [];
  var f = new Function("voice", "dictateLoop", "voiceStop", "endDictateLoop", "hushMic",
    block + "\nreturn { onMaatShow: onMaatShow, stopOpenChannelWhenHidden: stopOpenChannelWhenHidden };")(
    state.voice, state.dictateLoop,
    function (why) { calls.push("voiceStop"); }, function (why) { calls.push("endDictateLoop"); }, function () { calls.push("hush"); });
  return { f: f, calls: calls };
}

test("maat-show for another tab stops an open channel and Grok voice", function () {
  var e = blockEnv({ voice: {}, dictateLoop: true });
  e.f.onMaatShow({ type: "maat-show", id: "sermon" });
  assert.deepStrictEqual(e.calls.slice().sort(), ["endDictateLoop", "voiceStop"]);
});

test("maat-show for Converse itself changes nothing", function () {
  var e = blockEnv({ voice: {}, dictateLoop: true });
  e.f.onMaatShow({ type: "maat-show", id: "converse" });
  assert.deepStrictEqual(e.calls, []);
});

test("nothing is stopped when nothing is open", function () {
  var e = blockEnv({ voice: null, dictateLoop: false });
  e.f.onMaatShow({ type: "maat-show", id: "music" });
  assert.deepStrictEqual(e.calls, []);
});

test("the page routes maat-show only from the trusted parent, and hides on visibilitychange", function () {
  assert.ok(/d\.type === "maat-show"[\s\S]{0,120}fromTrustedParent\(ev\)/.test(src), "listener checks the parent");
  assert.ok(/visibilityState === "hidden"[\s\S]{0,80}stopOpenChannelWhenHidden/.test(src), "visibilitychange stops the channel");
});

test("a foreign window's maat-show does not reach the page (listener level)", function () {
  var h = page.load({ store: { tb_token: "T", tb_bridge: "https://harlan-b550-aorus-pro-ac.taila21a91.ts.net" } });
  assert.ok(!h.threw, h.threw && h.threw.message);
  h.send(false, "https://evil.example", { type: "maat-show", id: "sermon" });   // must not throw
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
