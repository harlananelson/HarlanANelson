// Run: node tests/maat-deeplink.test.js
// W6 / R1-09: deep-link allowlists must not accept Object.prototype names.
"use strict";
var fs = require("fs");
var path = require("path");
var assert = require("assert");
var src = fs.readFileSync(path.join(__dirname, "..", "maat.html"), "utf8");
var script = src.split("<script>")[1].split("</script>")[0];

function load(hash, search, initial) {
  var store = initial || {};
  var localStorage = {
    getItem: function (k) { return k in store ? store[k] : null; },
    setItem: function (k, v) { store[k] = String(v); }
  };
  var made = [];
  function el(tag) {
    var e = { tag: tag, tagName: String(tag).toUpperCase(), style: {}, dataset: {}, children: [], attrs: {}, className: "", innerHTML: "",
      setAttribute: function (k, v) { e.attrs[k] = v; }, getAttribute: function (k) { return e.attrs[k] || null; },
      appendChild: function (c) { e.children.push(c); return c; },
      classList: { toggle: function () {}, add: function () {}, remove: function () {} },
      addEventListener: function () {}, querySelectorAll: function () { return []; } };
    made.push(e);
    return e;
  }
  var byId = {};
  var doc = {
    getElementById: function (id) {
      for (var i = made.length - 1; i >= 0; i--) if (made[i].id === id) return made[i];
      return byId[id] || (byId[id] = el("div"));
    },
    querySelectorAll: function () { return []; },
    createElement: el
  };
  var loc = { href: "https://harlananelson.com/maat.html", origin: "https://harlananelson.com",
    search: search || "", hash: hash || "", hostname: "harlananelson.com", port: "", protocol: "https:" };
  var win = { addEventListener: function () {}, confirm: function () { return true; } };
  var threw = null;
  try {
    new Function("window", "document", "localStorage", "fetch", "location", "navigator", "URL", "URLSearchParams",
      "setTimeout", "clearTimeout", script)(win, doc, localStorage, function () { return { catch: function () {} }; },
      loc, { userAgent: "x" }, URL, URLSearchParams, function () { return 0; }, function () {});
  } catch (e) { threw = e; }
  var frames = {};
  made.forEach(function (e) { if (e.tag === "iframe") frames[e.id] = e; });
  return { store: store, frames: frames, threw: threw };
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
