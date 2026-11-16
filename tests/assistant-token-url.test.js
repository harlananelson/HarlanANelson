// Run: node tests/assistant-token-url.test.js
// W2 / R3-01: `var history = []` shadowed window.history, so ?token= crashed
// the page and left the token in the URL.
"use strict";
var assert = require("assert");
var page = require("./lib/assistant-page.js");
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}

test("?token=...&mode=mic loads without throwing (R3-01 probe)", function () {
  var h = page.load({ search: "?token=DUMMY&mode=mic" });
  assert.ok(!h.threw, "threw: " + (h.threw && h.threw.message));
});

test("the token is stored and scrubbed from the visible URL, keeping mode=mic", function () {
  var h = page.load({ search: "?token=DUMMY&mode=mic" });
  assert.strictEqual(h.store.tb_token, "DUMMY");
  assert.deepStrictEqual(h.replaced, ["/assistant.html?mode=mic"]);
});

test("?token= alone scrubs to the bare path", function () {
  var h = page.load({ search: "?token=DUMMY" });
  assert.deepStrictEqual(h.replaced, ["/assistant.html"]);
});

test("without ?token= nothing is scrubbed", function () {
  var h = page.load({ search: "?mode=mic" });
  assert.ok(!h.threw);
  assert.deepStrictEqual(h.replaced, []);
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
