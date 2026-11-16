// Loads maat.html's inline script against a recording stub DOM.
"use strict";
var fs = require("fs");
var path = require("path");
var src = fs.readFileSync(path.join(__dirname, "..", "..", "maat.html"), "utf8");
var script = src.split("<script>")[1].split("</script>")[0];

exports.script = script;

exports.load = function (opts) {
  opts = opts || {};
  var store = opts.store || {};
  var localStorage = {
    getItem: function (k) { return k in store ? store[k] : null; },
    setItem: function (k, v) { store[k] = String(v); }
  };
  var made = [];
  var srcLog = [];
  var messageListener = null;
  function el(tag) {
    var e = { tag: tag, tagName: String(tag).toUpperCase(), style: {}, dataset: {}, children: [], attrs: {},
      className: "", innerHTML: "", _src: "",
      setAttribute: function (k, v) { e.attrs[k] = v; },
      getAttribute: function (k) { return k === "src" ? (e._src || null) : (e.attrs[k] || null); },
      appendChild: function (c) { e.children.push(c); return c; },
      classList: { toggle: function () {}, add: function () {}, remove: function () {} },
      addEventListener: function () {}, querySelectorAll: function () { return []; } };
    if (tag === "iframe") {
      e.contentWindow = { postMessage: function () {} };
      Object.defineProperty(e, "src", {
        get: function () { return e._src; },
        set: function (v) { e._src = v; srcLog.push([e.id, v]); }
      });
    }
    made.push(e);
    return e;
  }
  var fallback = {};
  var doc = {
    getElementById: function (id) {
      for (var i = made.length - 1; i >= 0; i--) if (made[i].id === id) return made[i];
      return fallback[id] || (fallback[id] = el("div"));
    },
    querySelectorAll: function (sel) {
      return sel === "iframe" ? made.filter(function (e) { return e.tag === "iframe"; }) : [];
    },
    createElement: el
  };
  var loc = { href: "https://harlananelson.com/maat.html", origin: "https://harlananelson.com",
    search: opts.search || "", hash: opts.hash || "", hostname: "harlananelson.com", port: "", protocol: "https:" };
  var confirms = [];
  var win = {
    addEventListener: function (t, f) { if (t === "message") messageListener = f; },
    confirm: function (m) { confirms.push(m); return opts.confirm === undefined ? true : !!opts.confirm; }
  };
  var threw = null;
  try {
    new Function("window", "document", "localStorage", "fetch", "location", "navigator", "URL", "URLSearchParams",
      "setTimeout", "clearTimeout", script)(win, doc, localStorage,
      function () { return { catch: function () {} }; }, loc, { userAgent: "x" }, URL, URLSearchParams,
      function () { return 0; }, function () {});
  } catch (e) { threw = e; }
  return {
    store: store, threw: threw, srcLog: srcLog, confirms: confirms,
    get: function (id) { return doc.getElementById(id); },
    frames: function () {
      var f = {};
      made.forEach(function (e) { if (e.tag === "iframe") f[e.id] = e; });
      return f;
    },
    iframeCount: function () { return made.filter(function (e) { return e.tag === "iframe"; }).length; },
    // open the gear panel, as a tap would
    openSettings: function () {
      var gear = made.filter(function (e) { return e.className === "gear"; })[0];
      gear.onclick();
    },
    post: function (frameId, origin, data) {
      var f = this.frames()[frameId];
      messageListener({ origin: origin, source: f ? f.contentWindow : {}, data: data });
    }
  };
};
