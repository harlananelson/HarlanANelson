#!/usr/bin/env python3
"""Transform a copy of english-speech-drill.html into swahili-speech-drill.html.

The UI text stays in English (the user is an English speaker learning Swahili);
only the language-learning content is swapped: the exercise corpus, the verb
definitions, the verb-marker system (TENSE_*), recognition/TTS language, and
the title.

Usage:
    cp english-speech-drill.html swahili-speech-drill.html
    python3 python/generate_swahili_exercises.py
    python3 python/transform_to_swahili.py
"""

import json
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent
HTML_FILE = PROJECT / "swahili-speech-drill.html"
EXERCISES_FILE = PROJECT / "python" / "output" / "swahili_exercises.json"
DEFINITIONS_FILE = PROJECT / "python" / "output" / "swahili_definitions.json"


def fmt_defs(defs):
    """Format verb definitions as a JavaScript object literal."""
    return "{\n" + ",\n".join(f'  {k}:"{v}"' for k, v in defs.items()) + "\n}"


def sub_block(html, pattern, replacement, label, flags=re.DOTALL):
    """Regex-replace one block; warn (don't crash) if it isn't found."""
    new, n = re.subn(pattern, lambda m: replacement, html, count=1, flags=flags)
    print(f"  {'replaced' if n else 'WARNING: NOT FOUND -'} {label}")
    return new


def main():
    if not HTML_FILE.exists():
        raise SystemExit("Run first:  cp english-speech-drill.html swahili-speech-drill.html")

    exercises = json.loads(EXERCISES_FILE.read_text())
    definitions = json.loads(DEFINITIONS_FILE.read_text())
    html = HTML_FILE.read_text()

    # ── Title / heading ──────────────────────────────────────────────
    n_title = html.count("English Speech Drill")
    html = html.replace("English Speech Drill", "Swahili Speech Drill")
    print(f"  replaced title/heading ({n_title})")

    # ── Exercise corpus ──────────────────────────────────────────────
    ex_js = json.dumps(exercises, indent=2, ensure_ascii=False)
    html = sub_block(html, r"const exercises = \[.*?\n\];",
                     f"const exercises = {ex_js};", "exercise corpus")

    # ── Verb definitions ─────────────────────────────────────────────
    html = sub_block(html, r"const definitions = \{.*?\n\};",
                     f"const definitions = {fmt_defs(definitions)};", "definitions")

    # ── TENSE_NAMES ──────────────────────────────────────────────────
    tense_names = """const TENSE_NAMES = {
  na:  'Present (-na-)',
  li:  'Past (-li-)',
  ta:  'Future (-ta-)',
  me:  'Perfect (-me-)',
  nge: 'Conditional (-nge-)'
};"""
    html = sub_block(html, r"const TENSE_NAMES = \{.*?\n\};", tense_names, "TENSE_NAMES")

    # ── ALL_TENSES ───────────────────────────────────────────────────
    html = sub_block(html, r"const ALL_TENSES = \[.*?\];",
                     "const ALL_TENSES = ['na','li','ta','me','nge'];",
                     "ALL_TENSES", flags=0)

    # ── TENSE_DESCRIPTIONS (field names nombre/regla/conjugacion kept) ─
    tense_descs = """const TENSE_DESCRIPTIONS = {
  na: {nombre:'Present (-na-)', regla:'Ongoing or habitual action: "I am reading / I read."', conjugacion:'subject prefix + -na- + verb stem. Prefixes: ni-, u-, a-, tu-, m-, wa-. Example: wanasoma.'},
  li: {nombre:'Past (-li-)', regla:'A completed action in the past: "I read."', conjugacion:'subject prefix + -li- + verb stem. Example: tulisoma, walifika.'},
  ta: {nombre:'Future (-ta-)', regla:'An action that will happen: "I will read."', conjugacion:'subject prefix + -ta- + verb stem. Example: nitasoma, mtaandika.'},
  me: {nombre:'Perfect (-me-)', regla:'A completed action still relevant now: "I have read."', conjugacion:'subject prefix + -me- + verb stem. Example: amesoma. Note: m + me = mme.'},
  nge: {nombre:'Conditional (-nge-)', regla:'A hypothetical action: "I would read."', conjugacion:'subject prefix + -nge- + verb stem. Example: ningesoma, wangefanya.'}
};"""
    html = sub_block(html, r"const TENSE_DESCRIPTIONS = \{.*?\n\};", tense_descs,
                     "TENSE_DESCRIPTIONS")

    # ── feedbackPorTiempo ────────────────────────────────────────────
    feedback = """function feedbackPorTiempo(tense, item, u){
  const notas = [];
  switch(tense){
    case 'na':
      notas.push('Present: subject prefix + -na- + verb stem (ninasoma, wanafanya).');
      break;
    case 'li':
      notas.push('Past: subject prefix + -li- + verb stem (nilisoma, tulifika).');
      break;
    case 'ta':
      notas.push('Future: subject prefix + -ta- + verb stem (nitasoma, mtaandika).');
      break;
    case 'me':
      notas.push('Perfect: subject prefix + -me- + verb stem (nimesoma). Remember m + me = mme.');
      break;
    case 'nge':
      notas.push('Conditional: subject prefix + -nge- + verb stem (ningesoma, angefanya).');
      break;
  }
  return notas;
}"""
    html = sub_block(html, r"function feedbackPorTiempo\(tense, item, u\)\{.*?\n\}",
                     feedback, "feedbackPorTiempo")

    # ── Tense filter pills ───────────────────────────────────────────
    pills = """<div class="tense-filter" id="tenseFilter">
      <button class="tense-pill active" data-tense="all">All</button>
      <button class="tense-pill" data-tense="na">Present (-na-)</button>
      <button class="tense-pill" data-tense="li">Past (-li-)</button>
      <button class="tense-pill" data-tense="ta">Future (-ta-)</button>
      <button class="tense-pill" data-tense="me">Perfect (-me-)</button>
      <button class="tense-pill" data-tense="nge">Conditional (-nge-)</button>
    </div>"""
    html = sub_block(html, r'<div class="tense-filter" id="tenseFilter">.*?</div>',
                     pills, "tense filter pills")

    # ── Recognition + TTS language ───────────────────────────────────
    n_lang = html.count("'en-US'")
    html = html.replace("'en-US'", "'sw-KE'")
    print(f"  replaced language code 'en-US' -> 'sw-KE' ({n_lang})")

    # ── Browser voice selection regexes ──────────────────────────────
    html = html.replace("/^en[-_]/i", "/^sw[-_]/i")
    html = html.replace("/en[-_]US/i", "/sw[-_]KE/i")
    html = html.replace("/en[-_]GB/i", "/sw[-_]TZ/i")

    # ── Misc text ────────────────────────────────────────────────────
    html = html.replace("one complete sentence in English", "one complete sentence in Swahili")
    html = html.replace("Find English voices at elevenlabs.io/voices",
                        "Find a multilingual voice at elevenlabs.io/voices")
    html = html.replace("'practice-log-english.json'", "'practice-log-swahili.json'")

    # ── Speech-recognition error message ─────────────────────────────
    # Not every browser supports Swahili recognition; a 'service-not-allowed'
    # there is a missing-language issue, not a blocked microphone. Reword it,
    # and confirm via the Permissions API before claiming the mic is blocked.
    old_err = """    } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed')) {
      $('vozPill').textContent = 'Mic: blocked';
      $('feedbackBox').innerHTML = '<span class="bad">Microphone access was blocked.</span> Check your browser permissions.';
    } else {"""
    new_err = """    } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed' || event.error === 'language-not-supported')) {
      $('vozPill').textContent = 'Mic: unavailable';
      $('feedbackBox').innerHTML = '<span class="bad">Swahili speech recognition could not start.</span> This browser most likely does not support Swahili recognition. Try this drill in Chrome on a computer, where Swahili recognition works.';
      if (navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({name:'microphone'}).then(function(p){
          if (p && p.state && p.state !== 'granted') {
            $('vozPill').textContent = 'Mic: blocked';
            $('feedbackBox').innerHTML = '<span class="bad">Microphone access was blocked.</span> Allow the microphone in your browser settings.';
          }
        }).catch(function(){});
      }
    } else {"""
    if old_err in html:
        html = html.replace(old_err, new_err, 1)
        print("  replaced speech-recognition error handler")
    else:
        print("  WARNING: speech-recognition error handler not found")

    # ── Pluggable recognition engines (browser / on-device Whisper / cloud) ──
    # Adds an external script that swaps in a choice of recognition engine.
    if "drill-recognition-engines.js" not in html:
        html = html.replace(
            "</body>",
            '  <script src="drill-recognition-engines.js"></script>\n</body>', 1)
        print("  injected recognition-engines script tag")
    else:
        print("  recognition-engines script tag already present")

    HTML_FILE.write_text(html)
    print(f"\nWrote {HTML_FILE.name}: {len(exercises)} exercises, {len(definitions)} verbs.")


if __name__ == "__main__":
    main()
