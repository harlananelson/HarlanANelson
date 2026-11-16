// Run: node tests/maat-settings.test.js
// W5: R1-04 (Save must not destroy a live Listen recording) and
//     R1-08 (Save must not freeze URLs / cache-busters / the Listen host).
"use strict";
var assert = require("assert");
var page = require("./lib/maat-page.js");

var HOST = "harlan-b550-aorus-pro-ac.taila21a91.ts.net";
var CURRENT = (function () {
  var m = /var CACHE_V = \{ listen: "(\d+)", converse: "(\d+)" \};/.exec(page.script);
  return { listen: m[1], converse: m[2] };
})();
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}
function vOf(u) { var m = /[?&]v=([^&]+)/.exec(u || ""); return m ? m[1] : null; }
function saveWith(h, edits) {
  h.openSettings();
  Object.keys(edits).forEach(function (id) { h.get(id).value = edits[id]; });
  h.get("saveModes").onclick();
}
function startRecording(h) {
  h.post("view-sermon", "https://" + HOST + ":8443", { type: "maat-recording", on: true });
}

test("sanity: the page loads and opens Converse and Listen frames", function () {
  var h = page.load({ hash: "#sermon" });
  assert.ok(!h.threw, h.threw && h.threw.message);
  assert.ok(h.frames()["view-sermon"]);
});

test("R1-04: Save with only a token/key change does not touch a recording Listen frame", function () {
  var h = page.load({ hash: "#sermon" });
  var before = h.iframeCount();
  var logBefore = h.srcLog.length;
  var frame = h.frames()["view-sermon"];
  startRecording(h);
  saveWith(h, { maatToken: "NEW-TOKEN", maatTranslationKey: "sk-ant-x" });
  assert.strictEqual(h.store.tb_token, "NEW-TOKEN");
  assert.strictEqual(h.frames()["view-sermon"], frame, "same iframe node");
  assert.strictEqual(h.iframeCount(), before, "no frames rebuilt");
  assert.strictEqual(h.srcLog.length, logBefore, "no frame navigated");
  assert.strictEqual(h.confirms.length, 0, "nothing to confirm");
});

test("R1-04: changing the host while recording asks first, and Cancel keeps Listen", function () {
  var h = page.load({ hash: "#sermon", confirm: false });
  startRecording(h);
  var logBefore = h.srcLog.length;
  saveWith(h, { maatBridge: "https://other-box.example-tailnet.ts.net" });
  assert.ok(h.confirms.length >= 1, "a confirm was shown");
  assert.strictEqual(h.srcLog.length, logBefore, "Listen was not reloaded");
});

test("R1-04: ... and OK reloads Listen on the new host", function () {
  var h = page.load({ hash: "#sermon", confirm: true });
  startRecording(h);
  saveWith(h, { maatBridge: "https://other-box.example-tailnet.ts.net" });
  var last = h.srcLog.filter(function (x) { return x[0] === "view-sermon"; }).pop();
  assert.ok(/^https:\/\/other-box\.example-tailnet\.ts\.net:8443\//.test(last[1]), last[1]);
});

test("R1-08: Save does not persist derived URLs", function () {
  var h = page.load({});
  saveWith(h, { maatToken: "T" });
  var saved = JSON.parse(h.store.maat_urls || "{}");
  assert.strictEqual(saved.sermon, undefined, "sermon stored: " + saved.sermon);
  assert.strictEqual(saved.converse, undefined, "converse stored: " + saved.converse);
});

test("R1-08: a URL the user edited IS persisted", function () {
  var h = page.load({});
  saveWith(h, { "url-practice": "https://example.org/drills.html" });
  var saved = JSON.parse(h.store.maat_urls || "{}");
  assert.strictEqual(saved.practice, "https://example.org/drills.html");
});

test("R1-08: legacy frozen entries (v=26 Listen, v=83 Converse) no longer pin the cache-buster", function () {
  var frozen = { sermon: "https://" + HOST + ":8443/?v=26", converse: "./assistant.html?v=83&mode=mic" };
  var h = page.load({ hash: "#sermon", store: { maat_urls: JSON.stringify(frozen) } });
  var frames = h.frames();
  var listenSrc = frames["view-sermon"].src;
  assert.strictEqual(vOf(listenSrc), CURRENT.listen, listenSrc);   // current constant, not the old 22
  h = page.load({ store: { maat_urls: JSON.stringify(frozen) } });
  assert.strictEqual(vOf(h.frames()["view-converse"].src), CURRENT.converse, h.frames()["view-converse"].src);
});

test("R1-08: the Tailscale machine field changes Listen even after an earlier Save", function () {
  var frozen = { sermon: "https://" + HOST + ":8443/?v=26" };
  var h = page.load({ hash: "#sermon", store: { maat_urls: JSON.stringify(frozen) } });
  saveWith(h, { maatBridge: "https://other-box.example-tailnet.ts.net" });
  var last = h.srcLog.filter(function (x) { return x[0] === "view-sermon"; }).pop();
  assert.ok(/^https:\/\/other-box\.example-tailnet\.ts\.net:8443\//.test(last[1]), last && last[1]);
});

test("R1-04: a token-only Save after a deep link (#practice?lang=es, #converse?input=type) reloads nothing", function () {
  ["#practice?lang=es", "#converse?input=type", "#converse?input=mic"].forEach(function (hash) {
    var h = page.load({ hash: hash });
    var logBefore = h.srcLog.length;
    saveWith(h, { maatToken: "NEW-TOKEN" });
    assert.strictEqual(h.srcLog.length, logBefore, hash + ": frames navigated: " + JSON.stringify(h.srcLog.slice(logBefore)));
  });
});

test("MEDIUM-a: a same-origin override in another directory is kept, not collapsed to the default", function () {
  var h = page.load({ store: { maat_urls: JSON.stringify({ converse: "https://harlananelson.com/maat/assistant.html" }) } });
  var src = h.frames()["view-converse"].src;
  assert.ok(/\/maat\/assistant\.html/.test(src), "Converse src lost the typed path: " + src);
  saveWith(h, { maatToken: "T2" });
  var saved = JSON.parse(h.store.maat_urls || "{}");
  assert.strictEqual(saved.converse, "https://harlananelson.com/maat/assistant.html", "override dropped: " + saved.converse);
});

test("MEDIUM-a: the default with other v=/mode= is still not an override", function () {
  var h = page.load({ store: { maat_urls: JSON.stringify({ converse: "https://harlananelson.com/assistant.html?v=83&mode=mic" }) } });
  var src = h.frames()["view-converse"].src;
  assert.ok(/^\.\/assistant\.html/.test(src) && vOf(src) !== "83", src);
});

test("MEDIUM-b: a bare :8443 Listen URL on another tailnet machine is an override, not derived", function () {
  var h = page.load({ hash: "#sermon", store: { maat_urls: JSON.stringify({ sermon: "https://other-box.example-tailnet.ts.net:8443/" }) } });
  var src = h.frames()["view-sermon"].src;
  assert.ok(/^https:\/\/other-box\.example-tailnet\.ts\.net:8443\//.test(src), "Listen host replaced: " + src);
});

test("MEDIUM-b: a bare :8443 URL on the configured machine is still derived (follows the Tailscale field)", function () {
  var h = page.load({ hash: "#sermon", store: { tb_bridge: "https://cfg-box.example-tailnet.ts.net",
    maat_urls: JSON.stringify({ sermon: "https://cfg-box.example-tailnet.ts.net:8443/?v=20" }) } });
  var src = h.frames()["view-sermon"].src;
  assert.ok(/^https:\/\/cfg-box\.example-tailnet\.ts\.net:8443\//.test(src), src);
  assert.notStrictEqual(vOf(src), "20", "frozen v= still pinned: " + src);
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
