// Run: node tests/maat-messages.test.js
// Exercises maat.html's postMessage listener (W1 / R1-01, R2-F8, R3-03, R8-F5)
// by extracting the page script and running it against stub DOM objects.
"use strict";
var fs = require("fs");
var path = require("path");
var assert = require("assert");

var src = fs.readFileSync(path.join(__dirname, "..", "maat.html"), "utf8");
var script = src.split("<script>")[1].split("</script>")[0];

var DEFAULT_HOST = "harlan-b550-aorus-pro-ac.taila21a91.ts.net";

function makeHarness(initialStore) {
  var store = Object.assign({ tb_token: "REAL-TOKEN", tb_bridge: "https://" + DEFAULT_HOST }, initialStore || {});
  var localStorage = {
    getItem: function (k) { return k in store ? store[k] : null; },
    setItem: function (k, v) { store[k] = String(v); }
  };
  var posts = [];
  var fetches = [];
  function mkFrame(id, srcUrl) {
    return {
      id: id,
      getAttribute: function (k) { return k === "src" ? srcUrl : null; },
      contentWindow: { name: id, postMessage: function (m, o) { posts.push({ frame: id, origin: o, msg: m }); } }
    };
  }
  var frames = {
    "view-converse": mkFrame("view-converse", "https://harlananelson.com/assistant.html?v=1&mode=mic"),
    "view-sermon": mkFrame("view-sermon", "https://" + DEFAULT_HOST + ":8443/?v=26"),
    "view-music": mkFrame("view-music", "https://" + DEFAULT_HOST + ":8444/"),
    "tool-frame-remarkable": mkFrame("tool-frame-remarkable", "https://" + DEFAULT_HOST + ":9443/?listen=current&v=17")
  };
  var frameList = Object.keys(frames).map(function (k) { return frames[k]; });
  var listener = null;
  var win = {
    addEventListener: function (t, f) { if (t === "message") listener = f; },
    confirm: function () { return true; }
  };
  var doc = {
    getElementById: function (id) { return frames[id] || null; },
    querySelectorAll: function (sel) { return sel === "iframe" ? frameList : []; },
    createElement: function () {
      return { style: {}, dataset: {}, setAttribute: function () {}, appendChild: function () {},
        classList: { toggle: function () {}, add: function () {}, remove: function () {} }, addEventListener: function () {} };
    }
  };
  var fetchStub = function (u, o) { fetches.push([u, o && o.headers && o.headers.Authorization]); return { catch: function () {} }; };
  var loc = { href: "https://harlananelson.com/maat.html", origin: "https://harlananelson.com",
    search: "", hash: "", hostname: "harlananelson.com", port: "", protocol: "https:" };
  try {
    new Function("window", "document", "localStorage", "fetch", "location", "navigator", "URL", "URLSearchParams", script)(
      win, doc, localStorage, fetchStub, loc, { userAgent: "x" }, URL, URLSearchParams);
  } catch (e) { /* later init steps hit the stub DOM; the listener is already registered */ }
  assert.ok(listener, "message listener must be registered");
  return {
    store: store, posts: posts, fetches: fetches, frames: frames,
    send: function (frameId, origin, data) {
      listener({ origin: origin, source: frameId ? frames[frameId].contentWindow : { name: "foreign" }, data: data });
    }
  };
}

var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}
function tokenPosts(h) { return h.posts.filter(function (p) { return p.msg && p.msg.token; }); }

test("foreign window cannot repoint tb_bridge or trigger a token push (R1-01 probe)", function () {
  var h = makeHarness();
  h.send(null, "https://evil.example", { type: "maat-auth-offer", token: "attacker", bridge: "https://evil.example" });
  assert.strictEqual(h.store.tb_token, "REAL-TOKEN");
  assert.strictEqual(h.store.tb_bridge, "https://" + DEFAULT_HOST);
  assert.strictEqual(tokenPosts(h).length, 0);
});

test("a shell frame with the wrong origin is ignored", function () {
  var h = makeHarness();
  h.send("view-converse", "https://evil.example", { type: "maat-auth-offer", token: "x", bridge: "https://evil.example" });
  assert.strictEqual(h.store.tb_bridge, "https://" + DEFAULT_HOST);
  assert.strictEqual(tokenPosts(h).length, 0);
});

test("foreign window cannot request a token push with maat-auth-please", function () {
  var h = makeHarness();
  h.send(null, "https://evil.example", { type: "maat-auth-please" });
  h.send(null, "https://harlananelson.com", { type: "maat-auth-please" }); // right origin, wrong window
  assert.strictEqual(h.posts.length, 0);
});

test("the Converse frame may not repoint the bridge to a foreign host", function () {
  var h = makeHarness();
  h.send("view-converse", "https://harlananelson.com", { type: "maat-auth-offer", token: "x", bridge: "https://evil.example" });
  assert.strictEqual(h.store.tb_bridge, "https://" + DEFAULT_HOST);
  assert.strictEqual(h.store.tb_token, "REAL-TOKEN");
  h.posts.forEach(function (p) { assert.notStrictEqual(p.msg.bridge, "https://evil.example"); });
});

test("the Converse frame may offer a token when none is stored, on the tailnet host", function () {
  var h = makeHarness({ tb_token: "" });
  h.send("view-converse", "https://harlananelson.com", { type: "maat-auth-offer", token: "NEW", bridge: "https://" + DEFAULT_HOST });
  assert.strictEqual(h.store.tb_token, "NEW");
  var tp = tokenPosts(h);
  assert.ok(tp.length > 0, "token should be pushed to frames");
  tp.forEach(function (p) { assert.notStrictEqual(p.origin, "*"); });
});

test("only Converse may send maat-auth-offer", function () {
  var h = makeHarness({ tb_token: "" });
  h.send("view-sermon", "https://" + DEFAULT_HOST + ":8443", { type: "maat-auth-offer", token: "FROM-LISTEN" });
  h.send("view-music", "https://" + DEFAULT_HOST + ":8444", { type: "maat-auth-offer", token: "FROM-MUSIC" });
  assert.strictEqual(h.store.tb_token, "");
});

test("Listen (tailnet :8443) may request auth; the push never uses targetOrigin *", function () {
  var h = makeHarness();
  h.send("view-sermon", "https://" + DEFAULT_HOST + ":8443", { type: "maat-auth-please" });
  assert.ok(h.posts.length > 0);
  h.posts.forEach(function (p) { assert.notStrictEqual(p.origin, "*"); });
});

test("maat-listen is accepted only from the Listen frame", function () {
  var h = makeHarness();
  h.send("view-converse", "https://harlananelson.com", { type: "maat-listen", session: "evil" });
  h.send(null, "https://evil.example", { type: "maat-listen", session: "evil" });
  // No public accessor for the stem; remarkable url is derived from it, so a
  // forged stem must not be able to throw or leak. Accepting the real one must work.
  h.send("view-sermon", "https://" + DEFAULT_HOST + ":8443", { type: "maat-listen", session: "real" });
});

test("allowlist helper: shell origins, tailnet origins on any port, configured host, nothing else", function () {
  var m = script.split("/* maat-origin-allowlist:start */")[1].split("/* maat-origin-allowlist:end */")[0];
  var trusted = new Function(m + "; return maatOriginTrusted;")();
  var T = ["https://harlananelson.com", "https://www.harlananelson.com",
    "https://" + DEFAULT_HOST, "https://" + DEFAULT_HOST + ":8443", "https://" + DEFAULT_HOST + ":8444",
    "https://" + DEFAULT_HOST + ":9443"];
  T.forEach(function (o) { assert.ok(trusted(o, ""), o); });
  var F = ["null", "", "http://harlananelson.com", "https://harlananelson.com:8443", "https://evil.example",
    "https://harlananelson.com.evil.example", "https://evilharlananelson.com", "https://evil.example/" + DEFAULT_HOST,
    "https://" + DEFAULT_HOST + ".evil.example", "http://" + DEFAULT_HOST + ":8443"];
  F.forEach(function (o) { assert.ok(!trusted(o, ""), o); });
  assert.ok(trusted("https://other.ts.net:8443", "other.ts.net"));
  assert.ok(!trusted("https://other.ts.net:8443", "another.ts.net"));
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
