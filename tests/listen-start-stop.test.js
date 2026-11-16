// Run: node tests/listen-start-stop.test.js [path-to-live-translator.html]
// W3 / R2-F1: Stop pressed while Start is still connecting (Home GPU) or
// waiting on the mic permission prompt must not leave an orphan capture.
"use strict";
var fs = require("fs");
var path = require("path");
var assert = require("assert");
var file = process.argv[2] || path.join(__dirname, "..", "live-translator.html");
var src = fs.readFileSync(file, "utf8");

function fnSource(name) {
  var a = src.indexOf("    function " + name + "(");
  assert.ok(a >= 0, "function " + name + " not found");
  var i = src.indexOf("{", src.indexOf(")", a)), depth = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}" && --depth === 0) return src.slice(a, j + 1);
  }
  throw new Error("unbalanced " + name);
}
var gen = (/^\s*var startGen = 0;.*$/m.exec(src) || [""])[0];
var code = ["startCapture", "stopCapture", "start", "stop"].map(fnSource).join("\n");

function makeEnv() {
  var ctxs = [], streams = [], gumResolvers = [], hgResolvers = [], statuses = [];
  function mkStream() {
    var s = { live: true, getTracks: function () { return [{ stop: function () { s.live = false; } }]; } };
    streams.push(s);
    return s;
  }
  function AudioContextStub() {
    var c = this;
    ctxs.push(c); c.closed = false; c.sampleRate = 48000;
    c.createMediaStreamSource = function () { return { connect: function () {}, disconnect: function () {} }; };
    c.createScriptProcessor = function () { return { connect: function () {}, disconnect: function () {} }; };
    c.createGain = function () { return { gain: {}, connect: function () {}, disconnect: function () {} }; };
    c.destination = {};
    c.resume = function () {}; c.close = function () { c.closed = true; };
  }
  var env = {
    window: { AudioContext: AudioContextStub },
    navigator: { mediaDevices: { getUserMedia: function () {
      return new Promise(function (res) { gumResolvers.push(function () { res(mkStream()); }); }); } } },
    state: { transcribeEngine: "homegpu", whisperModel: "m" },
    els: {},
    hgWs: null
  };
  var body = [
    "var listening = false, capturing = false, audioCtx = null, micStream = null, micSource = null, processor = null, muteGain = null, srcRate = 48000;",
    "var hgWs = env.hgWs, hgHold = [], hgHoldSamples = 0, whisper = null;",
    gen,
    "var FRAME = 4096;",
    "function captureConstraints() { return {}; } function onAudio() {} function resetVad() {} function setLevel() {}",
    "function pushLog() {} function setStatus(k, t) { env.statuses.push(k + ':' + t); } function updateControls() {} function pushConfig() {}",
    "function announceListenToMaat() {} function hasNativeAsr() { return false; } function resolvedHomeGpuUrl() { return 'wss://x/ws'; }",
    "function hasKey() { return true; } function isMonolingual() { return false; } function whisperDevice() { return 'cpu'; }",
    "function hgCancelReconnect() {} function hgConnect() { return new Promise(function (res) { env.hgResolvers.push(res); }); }",
    code,
    "return { start: start, stop: stop, startCapture: startCapture, state: function () { return { listening: listening, capturing: capturing, audioCtx: audioCtx }; }, setWs: function (w) { hgWs = w; } };"
  ].join("\n");
  env.statuses = statuses; env.hgResolvers = hgResolvers;
  var api = new Function("env", "window", "navigator", "state", "els", "Promise", body)(
    env, env.window, env.navigator, env.state, env.els, Promise);
  return { api: api, ctxs: ctxs, streams: streams, gum: gumResolvers, hg: hgResolvers, env: env };
}
function tick() { return new Promise(function (r) { setTimeout(r, 0); }); }

var failures = 0;
function test(name, fn) {
  return Promise.resolve().then(fn).then(function () { console.log("ok   - " + name); },
    function (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); });
}

(function main() {
  var chain = Promise.resolve();
  chain = chain.then(function () { return test("Stop while Home GPU is connecting: no mic is ever opened", function () {
    var e = makeEnv();
    e.api.start();
    e.api.stop();
    e.hg[0](true);
    return tick().then(function () {
      assert.strictEqual(e.gum.length, 0, "getUserMedia must not be called after Stop");
      assert.strictEqual(e.api.state().capturing, false);
      assert.strictEqual(e.ctxs.length, 0);
    });
  }); });
  chain = chain.then(function () { return test("Stop during the mic prompt: the late stream is released, no capture starts", function () {
    var e = makeEnv();
    e.api.setWs({ readyState: 1, send: function () {} });   // session already open: Start goes straight to the mic
    e.api.start();
    return tick().then(function () {
      assert.strictEqual(e.gum.length, 1);
      e.api.stop();
      e.gum[0]();
      return tick();
    }).then(function () {
      assert.strictEqual(e.api.state().capturing, false, "capturing must stay false");
      assert.strictEqual(e.api.state().listening, false);
      assert.ok(e.streams.every(function (s) { return !s.live; }), "every mic track stopped");
      assert.ok(e.ctxs.every(function (c) { return c.closed; }), "every AudioContext closed");
    });
  }); });
  chain = chain.then(function () { return test("Start, Stop, Start with a slow first prompt leaves exactly one live capture", function () {
    var e = makeEnv();
    e.api.setWs({ readyState: 1, send: function () {} });
    e.api.start();            // prompt 1 pending
    return tick().then(function () {
      e.api.stop();
      e.api.start();          // prompt 2 pending
      return tick();
    }).then(function () {
      assert.strictEqual(e.gum.length, 2);
      e.gum[0]();             // stale one resolves first
      return tick();
    }).then(function () { e.gum[1](); return tick(); }).then(function () {
      var live = e.ctxs.filter(function (c) { return !c.closed; });
      assert.strictEqual(live.length, 1, "live AudioContexts: " + live.length);
      assert.strictEqual(e.streams.filter(function (s) { return s.live; }).length, 1, "live mic streams");
      assert.strictEqual(e.api.state().capturing, true);
      assert.strictEqual(e.api.state().listening, true, "the stale callback must not clear listening");
    });
  }); });
  chain = chain.then(function () { return test("startCapture closes an existing capture before opening another", function () {
    var e = makeEnv();
    e.api.startCapture(); e.gum[0]();
    return tick().then(function () {
      e.api.startCapture(); e.gum[1](); return tick();
    }).then(function () {
      var live = e.ctxs.filter(function (c) { return !c.closed; });
      assert.strictEqual(live.length, 1, "live AudioContexts: " + live.length);
      assert.strictEqual(e.streams.filter(function (s) { return s.live; }).length, 1);
    });
  }); });
  chain.then(function () {
    console.log(failures ? failures + " failure(s)" : "all passed");
    process.exit(failures ? 1 : 0);
  });
})();
