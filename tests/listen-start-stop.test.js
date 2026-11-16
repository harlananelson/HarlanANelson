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
var hgCode = fnSource("hgConnect");

function makeEnv(opts) {
  opts = opts || {};
  var ctxs = [], streams = [], gumResolvers = [], hgResolvers = [], statuses = [];
  // Real hgConnect against a stub WebSocket (opts.realHg) and recorded timers.
  var sockets = [], timers = [];
  function WebSocketStub(url) {
    var w = this;
    w.url = url; w.sent = []; w.closed = false; w.readyState = 0;
    w.send = function (m) { w.sent.push(JSON.parse(m).type); };
    // close() records the call but, like a slow network, does not stop events
    // the test fires afterwards: the page must not depend on close() winning.
    w.close = function () { w.closed = true; };
    sockets.push(w);
  }
  function setTimeoutStub(fn, ms) { var t = { fn: fn, ms: ms, cleared: false }; timers.push(t); return t; }
  function clearTimeoutStub(t) { if (t) { t.cleared = true; } }
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
    "var hgConnecting = false, hgConnectTimer = null; function hgCancelReconnect() {}",
    opts.realHg
      ? "function hgAbandonPending() {} function hgHandleEvent() {} function hgScheduleReconnect() {} " +
        "function sessionName() { return 'sess'; } function sendExportOnStop() {} \n" + hgCode
      : "function hgConnect() { return new Promise(function (res) { env.hgResolvers.push(res); }); }",
    code,
    "return { hgWsNow: function () { return hgWs; }, start: start, stop: stop, startCapture: startCapture, state: function () { return { listening: listening, capturing: capturing, audioCtx: audioCtx }; }, setWs: function (w) { hgWs = w; } };"
  ].join("\n");
  env.statuses = statuses; env.hgResolvers = hgResolvers;
  var api = new Function("env", "window", "navigator", "state", "els", "Promise", "WebSocket", "setTimeout", "clearTimeout", body)(
    env, env.window, env.navigator, env.state, env.els, Promise,
    opts.realHg ? WebSocketStub : undefined, opts.realHg ? setTimeoutStub : setTimeout, opts.realHg ? clearTimeoutStub : clearTimeout);
  return { sockets: sockets, timers: timers, api: api, ctxs: ctxs, streams: streams, gum: gumResolvers, hg: hgResolvers, env: env };
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

  // ---- follow-up MEDIUM: Stop during the REAL hgConnect ----
  function readyEvent(w) { w.readyState = 1; w.onmessage({ data: JSON.stringify({ type: "ready", asr: "a", llm: "l" }) }); }
  chain = chain.then(function () { return test("Stop during Home GPU connect: a socket that opens afterwards gets no session/profile and no status", function () {
    var e = makeEnv({ realHg: true });
    e.env.state.speakerProfile = "medical";
    e.api.start();
    assert.strictEqual(e.sockets.length, 1);
    e.api.stop();
    var after = e.env.statuses.length;
    readyEvent(e.sockets[0]);
    return tick().then(function () {
      assert.deepStrictEqual(e.sockets[0].sent, [], "frames sent to the server after Stop: " + e.sockets[0].sent);
      assert.strictEqual(e.env.statuses.length, after, "status written after Stop: " + e.env.statuses.slice(after));
      assert.strictEqual(e.gum.length, 0, "mic opened after Stop");
      assert.ok(e.sockets[0].closed, "the abandoned socket is closed");
    });
  }); });
  chain = chain.then(function () { return test("Stop during Home GPU connect: a later socket error does not overwrite the Stopped status", function () {
    var e = makeEnv({ realHg: true });
    e.api.start();
    e.api.stop();
    var after = e.env.statuses.length;
    e.sockets[0].onerror({});
    return tick().then(function () {
      assert.strictEqual(e.env.statuses.length, after, "status written after Stop: " + e.env.statuses.slice(after));
      assert.ok(/^idle:Stopped/.test(e.env.statuses[e.env.statuses.length - 1]), e.env.statuses[e.env.statuses.length - 1]);
    });
  }); });
  chain = chain.then(function () { return test("Stop clears the connect timer; a timer that still fires writes no status", function () {
    var e = makeEnv({ realHg: true });
    e.api.start();
    var t = e.timers[0];
    assert.ok(t && t.ms === 10000, "connect timer registered");
    e.api.stop();
    assert.ok(t.cleared, "connect timer cleared by Stop");
    var after = e.env.statuses.length;
    t.fn();
    return tick().then(function () {
      assert.strictEqual(e.env.statuses.length, after, "status written after Stop: " + e.env.statuses.slice(after));
    });
  }); });
  chain = chain.then(function () { return test("Start, Stop, Start: the abandoned socket's close does not disturb the new connection", function () {
    var e = makeEnv({ realHg: true });
    e.api.start();
    e.api.stop();
    e.api.start();
    assert.strictEqual(e.sockets.length, 2, "second Start opens its own socket");
    if (e.sockets[0].onclose) { e.sockets[0].onclose({}); }   // old socket finally closes
    assert.strictEqual(e.api.hgWsNow(), e.sockets[1], "hgWs still the new socket");
    readyEvent(e.sockets[1]);
    return tick().then(function () {
      assert.deepStrictEqual(e.sockets[1].sent.slice(0, 1), ["session"]);
      assert.strictEqual(e.gum.length, 1, "new Start reaches the mic prompt");
      assert.strictEqual(e.api.state().listening, true);
    });
  }); });
  chain.then(function () {
    console.log(failures ? failures + " failure(s)" : "all passed");
    process.exit(failures ? 1 : 0);
  });
})();
