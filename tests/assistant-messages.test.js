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

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
