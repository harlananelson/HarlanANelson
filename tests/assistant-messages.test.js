// Run: node tests/assistant-messages.test.js
// W1 (R3-03, R3-02, R8-F5) for assistant.html (Converse).
"use strict";
var assert = require("assert");
var page = require("./lib/assistant-page.js");
var HOST = "harlan-b550-aorus-pro-ac.taila21a91.ts.net";
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}
var GOOD = { tb_token: "REAL", tb_bridge: "https://" + HOST };

test("sanity: page script loads with a stored token", function () {
  var h = page.load({ store: Object.assign({}, GOOD), search: "?mode=mic" });
  assert.ok(!h.threw, h.threw && h.threw.message);
});

test("R3-03: token is offered to the parent with an explicit origin, never *", function () {
  var h = page.load({ store: Object.assign({}, GOOD) });
  var offers = h.posts.filter(function (p) { return p.type === "maat-auth-offer"; });
  assert.ok(offers.length > 0, "offer posted");
  offers.forEach(function (p) { assert.notStrictEqual(p.origin, "*"); });
  h.posts.forEach(function (p) { assert.notStrictEqual(p.origin, "*", p.type); });
});

test("R3-03: no token goes to an unexpected parent origin", function () {
  var h = page.load({ store: Object.assign({}, GOOD), ancestorOrigins: ["https://evil.example"], referrer: "https://evil.example/x" });
  h.posts.filter(function (p) { return p.token; }).forEach(function (p) {
    assert.ok(/^https:\/\/(www\.)?harlananelson\.com$|^https:\/\/harlan-b550/.test(p.origin), "posted token to " + p.origin);
  });
});

test("R3-03: maat-auth from a foreign window/origin is ignored", function () {
  var h = page.load({ store: Object.assign({}, GOOD) });
  h.send(false, "https://evil.example", { type: "maat-auth", token: "ATTACKER", bridge: "https://evil.example" });
  assert.strictEqual(h.store.tb_token, "REAL");
  assert.strictEqual(h.store.tb_bridge, "https://" + HOST);
});

test("R3-03: right origin but not the parent window is ignored", function () {
  var h = page.load({ store: Object.assign({}, GOOD) });
  h.send(false, "https://harlananelson.com", { type: "maat-auth", token: "ATTACKER" });
  assert.strictEqual(h.store.tb_token, "REAL");
});

test("R3-03: maat-auth from the real parent on an allowed origin is accepted", function () {
  var h = page.load({ store: Object.assign({}, GOOD) });
  h.send(true, "https://harlananelson.com", { type: "maat-auth", token: "NEW", bridge: "https://" + HOST });
  assert.strictEqual(h.store.tb_token, "NEW");
});

test("R3-03: a parent on a foreign origin is refused even if it is the parent window", function () {
  var h = page.load({ store: Object.assign({}, GOOD) });
  h.send(true, "https://evil.example", { type: "maat-auth", token: "NEW" });
  assert.strictEqual(h.store.tb_token, "REAL");
});

test("R3-02: ?bridge= to a foreign host is ignored; the stored token is never sent there", function () {
  var h = page.load({ store: Object.assign({}, GOOD), search: "?bridge=https://evil.example.com" });
  assert.strictEqual(h.store.tb_bridge, "https://" + HOST);
  h.fetches.forEach(function (f) { assert.ok(f.url.indexOf("evil.example.com") < 0, f.url + " " + f.auth); });
});

test("R3-02: ?bridge= naming the tailnet host is accepted", function () {
  var h = page.load({ store: { tb_token: "REAL" }, search: "?bridge=https://" + HOST });
  assert.strictEqual(h.store.tb_bridge, "https://" + HOST);
});

test("R3-02: ?bridge= that fails Save's validity check is ignored", function () {
  var h = page.load({ store: { tb_token: "REAL" }, search: "?bridge=http://" + HOST });
  assert.ok(h.store.tb_bridge === undefined || h.store.tb_bridge === "https://" + HOST, h.store.tb_bridge);
});

// ---- follow-up: parents are Maat only, never another service on the tailnet host ----
["https://" + HOST + ":8444", "https://" + HOST + ":9443", "https://" + HOST + ":8443"].forEach(function (o) {
  test("HIGH-1: maat-auth from a parent on " + o + " is refused", function () {
    var h = page.load({ store: Object.assign({}, GOOD) });
    h.send(true, o, { type: "maat-auth", token: "ATTACKER", bridge: "https://evil.example" });
    assert.strictEqual(h.store.tb_token, "REAL");
    assert.strictEqual(h.store.tb_bridge, "https://" + HOST);
  });
  test("HIGH-1: no token is posted to a parent framed from " + o, function () {
    var h = page.load({ store: Object.assign({}, GOOD), ancestorOrigins: [o], referrer: o + "/" });
    h.posts.filter(function (p) { return p.token; }).forEach(function (p) {
      assert.notStrictEqual(p.origin, o, "token posted to " + p.origin);
      assert.ok(!/:\d+$/.test(p.origin), "token posted to a port-qualified origin " + p.origin);
    });
  });
});

test("HIGH-1: parents on harlananelson.com, www, and the tailnet host with no port are accepted", function () {
  ["https://harlananelson.com", "https://www.harlananelson.com", "https://" + HOST].forEach(function (o) {
    var h = page.load({ store: Object.assign({}, GOOD) });
    h.send(true, o, { type: "maat-auth", token: "NEW" });
    assert.strictEqual(h.store.tb_token, "NEW", o);
  });
});

test("HIGH-1: a configured (stored) bridge host is a parent on its empty port only", function () {
  var st = { tb_token: "REAL", tb_bridge: "https://other.example.ts.net" };
  var h = page.load({ store: Object.assign({}, st) });
  h.send(true, "https://other.example.ts.net:8444", { type: "maat-auth", token: "ATTACKER" });
  assert.strictEqual(h.store.tb_token, "REAL");
  h.send(true, "https://other.example.ts.net", { type: "maat-auth", token: "NEW" });
  assert.strictEqual(h.store.tb_token, "NEW");
});

test("HIGH-1: maat-auth.bridge is stored only for the default host or the already-stored host", function () {
  var h = page.load({ store: Object.assign({}, GOOD) });
  h.send(true, "https://harlananelson.com", { type: "maat-auth", token: "T", bridge: "https://evil.example" });
  assert.strictEqual(h.store.tb_bridge, "https://" + HOST);
  var h2 = page.load({ store: { tb_token: "REAL", tb_bridge: "https://other.example.ts.net" } });
  h2.send(true, "https://harlananelson.com", { type: "maat-auth", token: "T", bridge: "https://other.example.ts.net/" });
  assert.strictEqual(h2.store.tb_bridge, "https://other.example.ts.net");
  h2.send(true, "https://harlananelson.com", { type: "maat-auth", token: "T", bridge: "https://" + HOST });
  assert.strictEqual(h2.store.tb_bridge, "https://" + HOST);
});

test("MEDIUM: the visible first-run hint no longer says ?bridge= sets a new machine", function () {
  var fs = require("fs"), path = require("path");
  var html = fs.readFileSync(path.join(__dirname, "..", "assistant.html"), "utf8");
  var m = html.match(/<p class="hint">Tip:[\s\S]*?<\/p>/);
  assert.ok(m, "hint present");
  assert.ok(!/bridge=URL/.test(m[0]), m[0]);
  assert.ok(/Settings/.test(m[0]), "hint points at Settings");
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
