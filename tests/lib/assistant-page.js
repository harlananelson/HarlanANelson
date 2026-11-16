// Loads assistant.html's inline script against a recording stub DOM.
"use strict";
var fs = require("fs");
var path = require("path");
var src = fs.readFileSync(path.join(__dirname, "..", "..", "assistant.html"), "utf8");
var script = src.split("<script>")[1].split("</script>")[0];
exports.script = script;

exports.load = function (opts) {
  opts = opts || {};
  var store = opts.store || {};
  var fetches = [];
  var posts = [];
  var replaced = [];
  var listeners = {};
  function el() {
    return new Proxy({ style: {}, classList: { add: function () {}, remove: function () {}, toggle: function () {} },
      appendChild: function () {}, addEventListener: function () {}, children: [], options: [], dataset: {} }, {
      get: function (t, k) { return k in t ? t[k] : undefined; },
      set: function (t, k, v) { t[k] = v; return true; }
    });
  }
  var parentWin = { postMessage: function (m, o) { posts.push({ type: m.type, token: m.token, bridge: m.bridge, origin: o }); } };
  var ctx = {
    location: { search: opts.search || "", pathname: "/assistant.html", hash: "", href: "https://harlananelson.com/assistant.html" + (opts.search || ""),
      origin: "https://harlananelson.com", hostname: "harlananelson.com", port: "", protocol: "https:",
      ancestorOrigins: opts.ancestorOrigins || ["https://harlananelson.com"] },
    localStorage: { getItem: function (k) { return k in store ? store[k] : null; }, setItem: function (k, v) { store[k] = String(v); } },
    URLSearchParams: URLSearchParams, URL: URL, JSON: JSON, Math: Math, Date: Date, String: String, Array: Array, Promise: Promise,
    setTimeout: function () { return 0; }, setInterval: function () { return 0; }, clearTimeout: function () {},
    navigator: { userAgent: "x", mediaDevices: {} }, Audio: function () { return { setAttribute: function () {}, addEventListener: function () {} }; },
    document: { getElementById: function () { return el(); }, createElement: el, addEventListener: function () {},
      documentElement: el(), body: el(), createTextNode: function () { return {}; }, referrer: opts.referrer === undefined ? "https://harlananelson.com/maat.html" : opts.referrer },
    fetch: function (u, o) { fetches.push({ url: String(u).split("?")[0], auth: (o && o.headers && o.headers.Authorization) || "none" }); return new Promise(function () {}); }
  };
  ctx.window = ctx;
  ctx.window.history = { replaceState: function (a, b, url) { replaced.push(url); } };
  ctx.window.parent = opts.noParent ? ctx : parentWin;
  ctx.window.addEventListener = function (t, f) { (listeners[t] = listeners[t] || []).push(f); };
  ctx.window.self = ctx; ctx.window.top = ctx;
  var threw = null;
  try { new Function(Object.keys(ctx).join(","), script).apply(null, Object.keys(ctx).map(function (k) { return ctx[k]; })); }
  catch (e) { threw = e; }
  return {
    store: store, fetches: fetches, posts: posts, replaced: replaced, threw: threw, parentWin: parentWin,
    send: function (fromParent, origin, data) {
      (listeners.message || []).forEach(function (f) { f({ origin: origin, source: fromParent ? parentWin : { name: "other" }, data: data }); });
    }
  };
};
