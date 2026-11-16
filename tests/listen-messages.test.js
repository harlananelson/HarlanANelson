// Run: node tests/listen-messages.test.js [path-to-live-translator.html]
// W1 (R2-F8, R8-F5) for live-translator.html (Listen): extracts the
// /* maat-parent-messaging */ block and exercises it against stubs.
"use strict";
var fs = require("fs");
var path = require("path");
var assert = require("assert");
var file = process.argv[2] || path.join(__dirname, "..", "live-translator.html");
var src = fs.readFileSync(file, "utf8");
var HOST = "harlan-b550-aorus-pro-ac.taila21a91.ts.net";
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}

// The pre-fix page has no markers; fall back to its bare listener so the test
// runs (and fails) against the old code for the right reason.
function extract() {
  var a = src.indexOf("/* maat-parent-messaging:start */");
  if (a >= 0) return src.slice(a, src.indexOf("/* maat-parent-messaging:end */"));
  var b = src.indexOf("window.addEventListener('message', function (ev) {");
  return src.slice(b, src.indexOf("});", b) + 3);
}

function makeEnv(store, opts) {
  opts = opts || {};
  var listeners = [], posts = [], applied = [];
  var parentWin = { postMessage: function (m, o) { posts.push({ type: m.type, origin: o }); } };
  var win = { parent: parentWin, addEventListener: function (t, f) { if (t === "message") listeners.push(f); } };
  var localStorage = { getItem: function (k) { return k in store ? store[k] : null; }, setItem: function (k, v) { store[k] = String(v); } };
  var loc = { ancestorOrigins: opts.ancestorOrigins || ["https://harlananelson.com"] };
  var doc = { referrer: opts.referrer === undefined ? "https://harlananelson.com/maat.html" : opts.referrer };
  var code = extract() + "\n return { post: typeof postToMaatParent === 'function' ? postToMaatParent : null };";
  var api = new Function("window", "document", "location", "localStorage", "URL", "DEFAULT_TS_HOST",
    "tailscaleBridge", "applyMaatAuthKeys", "paintGpuUrlHint", code)(
    win, doc, loc, localStorage, URL, HOST,
    function () { return (store.tb_bridge || "").replace(/\/+$/, ""); },
    function (d) { applied.push(d); }, function () {});
  return {
    posts: posts, applied: applied, parentWin: parentWin, api: api,
    send: function (fromParent, origin, data) {
      listeners.forEach(function (f) { f({ origin: origin, source: fromParent ? parentWin : { name: "other" }, data: data }); });
    }
  };
}

test("foreign origin / window cannot set keys or the bridge (R2-F8)", function () {
  var store = { tb_bridge: "https://" + HOST };
  var e = makeEnv(store);
  e.send(false, "https://evil.example", { type: "maat-auth", bridge: "https://evil.example", translationKey: "k", clearKeys: true });
  assert.strictEqual(store.tb_bridge, "https://" + HOST);
  assert.strictEqual(e.applied.length, 0);
});

test("right origin but not the parent window is ignored", function () {
  var store = { tb_bridge: "https://" + HOST };
  var e = makeEnv(store);
  e.send(false, "https://harlananelson.com", { type: "maat-auth", translationKey: "k" });
  assert.strictEqual(e.applied.length, 0);
});

test("the parent on a foreign origin is refused", function () {
  var store = { tb_bridge: "https://" + HOST };
  var e = makeEnv(store);
  e.send(true, "https://evil.example", { type: "maat-auth", translationKey: "k" });
  assert.strictEqual(e.applied.length, 0);
});

test("the real parent (harlananelson.com, www, or the tailnet origin with no port) is accepted", function () {
  ["https://harlananelson.com", "https://www.harlananelson.com", "https://" + HOST].forEach(function (o) {
    var store = { tb_bridge: "https://" + HOST };
    var e = makeEnv(store);
    e.send(true, o, { type: "maat-auth", bridge: "https://" + HOST, translationKey: "k" });
    assert.strictEqual(e.applied.length, 1, o);
  });
});

test("a bridge from the parent that is not https is not stored", function () {
  var store = { tb_bridge: "https://" + HOST };
  var e = makeEnv(store);
  e.send(true, "https://harlananelson.com", { type: "maat-auth", bridge: "javascript:alert(1)" });
  assert.strictEqual(store.tb_bridge, "https://" + HOST);
});

test("messages to the parent never use targetOrigin * (R8-F5)", function () {
  var e = makeEnv({});
  assert.ok(e.api.post, "postToMaatParent exists");
  e.api.post({ type: "maat-recording", on: true });
  assert.ok(e.posts.length > 0);
  e.posts.forEach(function (p) { assert.notStrictEqual(p.origin, "*"); });
});

test("an unexpected framing origin gets nothing", function () {
  var e = makeEnv({}, { ancestorOrigins: ["https://evil.example"], referrer: "https://evil.example/" });
  e.api.post({ type: "maat-listen", session: "s" });
  e.posts.forEach(function (p) { assert.ok(/harlananelson\.com$|ts\.net(:8443)?$/.test(p.origin), p.origin); });
});

// ---- follow-up HIGH-1: only Maat is a parent, not another service on the tailnet host ----
["https://" + HOST + ":8443", "https://" + HOST + ":8444", "https://" + HOST + ":9443"].forEach(function (o) {
  test("HIGH-1: a parent on " + o + " cannot set keys or the bridge", function () {
    var store = { tb_bridge: "https://" + HOST };
    var e = makeEnv(store);
    e.send(true, o, { type: "maat-auth", bridge: "https://evil.example", translationKey: "k", clearKeys: true });
    assert.strictEqual(e.applied.length, 0);
    assert.strictEqual(store.tb_bridge, "https://" + HOST);
  });
  test("HIGH-1: nothing is posted to a port-qualified origin when framed from " + o, function () {
    var e = makeEnv({}, { ancestorOrigins: [o], referrer: o + "/" });
    e.api.post({ type: "maat-listen", session: "s" });
    e.posts.forEach(function (p) { assert.ok(!/:\d+$/.test(p.origin), p.origin); });
  });
});

test("HIGH-1: a configured (stored) bridge host is a parent on its empty port only", function () {
  var store = { tb_bridge: "https://other.example.ts.net" };
  var e = makeEnv(store);
  e.send(true, "https://other.example.ts.net:8444", { type: "maat-auth", translationKey: "k" });
  assert.strictEqual(e.applied.length, 0);
  e.send(true, "https://other.example.ts.net", { type: "maat-auth", translationKey: "k" });
  assert.strictEqual(e.applied.length, 1);
});

test("HIGH-1: maat-auth.bridge is stored only for the default host or the already-stored host", function () {
  var store = { tb_bridge: "https://" + HOST };
  var e = makeEnv(store);
  e.send(true, "https://harlananelson.com", { type: "maat-auth", bridge: "https://evil.example", translationKey: "k" });
  assert.strictEqual(store.tb_bridge, "https://" + HOST);
  var s2 = { tb_bridge: "https://other.example.ts.net" };
  var e2 = makeEnv(s2);
  e2.send(true, "https://harlananelson.com", { type: "maat-auth", bridge: "https://other.example.ts.net/", translationKey: "k" });
  assert.strictEqual(s2.tb_bridge, "https://other.example.ts.net");
  e2.send(true, "https://harlananelson.com", { type: "maat-auth", bridge: "https://" + HOST, translationKey: "k" });
  assert.strictEqual(s2.tb_bridge, "https://" + HOST);
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
