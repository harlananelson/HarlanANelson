// "⟲ Last reply" chip in assistant.html: shown only for tmux targets, and a
// tap reads the session (followPane with sent="") without sending anything.
// Run: node --test tests/assistant-last-reply.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const html = fs.readFileSync(path.join(__dirname, "..", "assistant.html"), "utf8");

function block(re, what) {
  const m = html.match(re);
  assert.ok(m, what + " not found in assistant.html");
  return m[0];
}

function el() {
  return { style: { display: "none" }, textContent: "", className: "", attrs: {},
    setAttribute(k, v) { this.attrs[k] = v; } };
}

test("the chip exists, hidden by default, in the context row", () => {
  const bar = block(/<div id="barContext">[\s\S]*?<\/div>/, "barContext");
  assert.match(bar, /<button id="lastReplyBtn" class="chip" style="display:none"[^>]*>⟲ Last reply<\/button>/);
});

test("context row counts the chip when deciding whether to show itself", () => {
  assert.match(html, /\["speakerToggle", "analyzeBtn", "termToggle", "lastReplyBtn"\]\.forEach/);
});

test("visible for a tmux target, hidden for an AI target", () => {
  const src = block(/function paintTermToggle\(\) \{[\s\S]*?\n  \}/, "paintTermToggle");
  const els = { termToggle: el(), lastReplyBtn: el() };
  const run = (target) => new Function("$", "target", "termView",
    src + "; paintTermToggle();")((id) => els[id], target, true);
  run({ kind: "tmux", name: "maat" });
  assert.strictEqual(els.lastReplyBtn.style.display, "");
  run({ kind: "ai", name: "grok" });
  assert.strictEqual(els.lastReplyBtn.style.display, "none");
});

test("tap reads the selected session and sends nothing", () => {
  const src = block(/if \(\$\("lastReplyBtn"\)\) \$\("lastReplyBtn"\)\.onclick = function \(\) \{[\s\S]*?\n  \};/, "lastReplyBtn handler");
  const calls = [], status = [], btn = {};
  const run = (target) => new Function("$", "target", "followPane", "setStatus", "api",
    src + "; $(\"lastReplyBtn\").onclick();")(
    (id) => (id === "lastReplyBtn" ? btn : null),
    target,
    (...a) => calls.push(a),
    (s) => status.push(s),
    () => { throw new Error("handler must not call the API directly (no send)"); });
  run({ kind: "tmux", name: "maat" });
  assert.strictEqual(calls.length, 1);
  assert.strictEqual(calls[0][0], "maat");
  assert.strictEqual(calls[0][1], "", "sent must be empty: read the latest turn, type nothing");
  assert.match(calls[0][2], /latest reply from maat/);
  run({ kind: "ai", name: "grok" });
  assert.strictEqual(calls.length, 1, "no capture for an AI target");
  assert.match(status[status.length - 1], /Pick a shell session/);
});

test("followPane takes the placeholder text and still defaults to the old one", () => {
  assert.match(html, /function followPane\(name, sent, waitText\)/);
  assert.match(html, /waitText \|\| \("Waiting for a reply from " \+ name \+ "…"\)/);
});
