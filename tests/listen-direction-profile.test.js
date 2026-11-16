// Run: node tests/listen-direction-profile.test.js [path-to-live-translator.html]
// W4 / R2-F7: Home GPU used to ignore Direction "English -> Spanish" and
// "Bidirectional ES <-> EN" (no matching profile was sent, so the server ran its
// es->en default on English speech).
"use strict";
var fs = require("fs");
var os = require("os");
var path = require("path");
var assert = require("assert");
var file = process.argv[2] || path.join(__dirname, "..", "live-translator.html");
var src = fs.readFileSync(file, "utf8");

function fnSource(name) {
  var a = src.indexOf("    function " + name + "(");
  if (a < 0) return "";
  var i = src.indexOf("{", src.indexOf(")", a)), depth = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}" && --depth === 0) return src.slice(a, j + 1);
  }
  throw new Error("unbalanced " + name);
}
function env(state) {
  var els = { speakerProfile: { value: "" }, direction: { value: "" } };
  var code = ["profileForDirection", "directionForProfile", "isKoreanProfile", "isPairProfile",
    "syncPairFromDirection", "syncPairFromProfile"].map(fnSource).join("\n");
  return new Function("state", "els", code + "\nreturn { profileForDirection: profileForDirection, directionForProfile: directionForProfile," +
    " syncPairFromDirection: syncPairFromDirection, syncPairFromProfile: syncPairFromProfile };")(state, els);
}
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   - " + name); }
  catch (e) { failures++; console.log("FAIL - " + name + "\n       " + e.message); }
}

test("each direction maps to a profile whose language pair matches the direction (R2-F7 table)", function () {
  var f = env({});
  assert.strictEqual(f.profileForDirection("es-en"), null, "es-en is the server default");
  assert.strictEqual(f.profileForDirection("en-es"), "english-to-spanish");
  assert.strictEqual(f.profileForDirection("auto"), "bilingual");
  assert.strictEqual(f.profileForDirection("ko-en"), "korean");
  assert.strictEqual(f.profileForDirection("en-ko"), "english-to-korean");
  assert.strictEqual(f.profileForDirection("auto-ko"), "korean-en");
});

test("profiles named by the page exist on the server with the matching pair (if biblestudy is checked out)", function () {
  var dir = path.join(os.homedir(), "projects", "biblestudy", "server", "profiles");
  if (!fs.existsSync(dir)) { console.log("       (skipped: " + dir + " not present)"); return; }
  var f = env({});
  var want = { "en-es": { language: "en", translate_to: "es" }, "ko-en": { language: "ko", translate_to: "en" },
    "en-ko": { language: "en", translate_to: "ko" } };
  Object.keys(want).forEach(function (d) {
    var p = JSON.parse(fs.readFileSync(path.join(dir, f.profileForDirection(d) + ".json"), "utf8"));
    assert.strictEqual(p.language, want[d].language, d);
    assert.strictEqual(p.translate_to, want[d].translate_to, d);
  });
  var b = JSON.parse(fs.readFileSync(path.join(dir, f.profileForDirection("auto") + ".json"), "utf8"));
  assert.deepStrictEqual(b.bilingual, ["en", "es"]);
});

test("choosing a direction in the dropdown sets the profile; es-en clears a pair profile", function () {
  var st = { direction: "en-es", speakerProfile: "" };
  var f = env(st);
  f.syncPairFromDirection(true);
  assert.strictEqual(st.speakerProfile, "english-to-spanish");
  st.direction = "es-en"; f.syncPairFromDirection(true);
  assert.strictEqual(st.speakerProfile, "");
});

test("choosing the profile sets the direction (both new profiles round-trip)", function () {
  var st = { direction: "es-en", speakerProfile: "bilingual" };
  var f = env(st);
  f.syncPairFromProfile();
  assert.strictEqual(st.direction, "auto");
  st.speakerProfile = "english-to-spanish"; f.syncPairFromProfile();
  assert.strictEqual(st.direction, "en-es");
});

test("at load, a stored direction fills an empty profile, but never overwrites an unrelated one (medical)", function () {
  var st = { direction: "auto", speakerProfile: "medical" };
  var f = env(st);
  f.syncPairFromDirection();
  assert.strictEqual(st.speakerProfile, "medical");
  st.speakerProfile = ""; f.syncPairFromDirection();
  assert.strictEqual(st.speakerProfile, "bilingual");
});

test("the profile dropdown offers both new profiles", function () {
  assert.ok(/<option value="english-to-spanish">/.test(src));
  assert.ok(/<option value="bilingual">/.test(src));
});

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
