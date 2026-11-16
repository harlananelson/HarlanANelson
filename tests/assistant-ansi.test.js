// Terminal view parser in assistant.html (the ansi-term:begin/end block).
// Run: node --test tests/assistant-ansi.test.js
"use strict";
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const html = fs.readFileSync(path.join(__dirname, "..", "assistant.html"), "utf8");
const m = html.match(/\/\* ansi-term:begin[\s\S]*?\*\/([\s\S]*?)\/\* ansi-term:end \*\//);
assert.ok(m, "ansi-term block not found in assistant.html");
const { ansiSegments, ansiPlain } = new Function(m[1] + "; return { ansiSegments, ansiPlain };")();

test("plain text passes through unchanged, box drawing intact", () => {
  const t = "┌────┬────┐\n│ #27 │ ok │\n└────┴────┘";
  assert.strictEqual(ansiPlain(t), t);
  assert.deepStrictEqual(ansiSegments(t).length, 1);
});

test("SGR colour, bold and reset become styled runs", () => {
  const segs = ansiSegments("\x1b[1mBold\x1b[0m \x1b[34mpath/x.py\x1b[39m done");
  assert.deepStrictEqual(segs.map((g) => g.text), ["Bold", " ", "path/x.py", " done"]);
  assert.strictEqual(segs[0].bold, true);
  assert.strictEqual(segs[1].bold, false);
  assert.ok(segs[2].fg);
  assert.strictEqual(segs[3].fg, null);
});

test("256-colour and truecolour", () => {
  const a = ansiSegments("\x1b[38;5;196mred\x1b[48;2;1;2;3mbg");
  assert.strictEqual(a[0].fg, "rgb(255,0,0)");
  assert.strictEqual(a[1].bg, "rgb(1,2,3)");
  assert.strictEqual(a[1].fg, "rgb(255,0,0)");
});

test("non-SGR escapes and control bytes are dropped", () => {
  const raw = "a\x1b[2Kb\x1b]8;;http://x\x07link\x1b]8;;\x07c\x07d\r\x00e";
  assert.strictEqual(ansiPlain(raw), "ablinkcde");
});

test("markup in pane text stays text (no HTML is produced)", () => {
  const raw = "<img src=x onerror=alert(1)> & </pre>";
  const segs = ansiSegments(raw);
  assert.strictEqual(segs.length, 1);
  assert.strictEqual(segs[0].text, raw);
  for (const g of ansiSegments("\x1b[38;2;999;-5;x;mX")) {
    if (g.fg) assert.match(g.fg, /^(#[0-9a-f]{6}|rgb\(\d{1,3},\d{1,3},\d{1,3}\))$/);
  }
});

test("inverse swaps foreground and background", () => {
  const [g] = ansiSegments("\x1b[7mprompt\x1b[27m");
  assert.ok(g.bg && g.fg);
});
