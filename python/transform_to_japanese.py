#!/usr/bin/env python3
"""Transform a copy of english-speech-drill.html into japanese-speech-drill.html.

The UI text stays in English (an English speaker learning Japanese); only the
language-learning content is swapped: the exercise corpus, the verb definitions,
the form/marker system (the "TENSE_*" objects, reused as Japanese verb forms),
the recognition/TTS language (ja-JP), and the title.

Japanese needs one thing the Spanish/Swahili/English versions do not: a
space-insensitive scorer. Japanese has no spaces and ja-JP recognition returns
kana or kanji, so `normalizar` strips whitespace + Japanese punctuation and
`incluyeAlguna` does a plain substring match (each answer group already lists
both the kana and kanji form).

Usage:
    cp english-speech-drill.html japanese-speech-drill.html
    python3 python/generate_japanese_exercises.py
    python3 python/transform_to_japanese.py
"""

import json
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent
HTML_FILE = PROJECT / "japanese-speech-drill.html"
EXERCISES_FILE = PROJECT / "python" / "output" / "japanese_exercises.json"
DEFINITIONS_FILE = PROJECT / "python" / "output" / "japanese_definitions.json"


def fmt_defs(defs):
    return "{\n" + ",\n".join(f'  "{k}":"{v}"' for k, v in defs.items()) + "\n}"


def sub_block(html, pattern, replacement, label, flags=re.DOTALL):
    new, n = re.subn(pattern, lambda m: replacement, html, count=1, flags=flags)
    print(f"  {'replaced' if n else 'WARNING: NOT FOUND -'} {label}")
    return new


def main():
    if not HTML_FILE.exists():
        raise SystemExit("Run first:  cp english-speech-drill.html japanese-speech-drill.html")

    exercises = json.loads(EXERCISES_FILE.read_text())
    definitions = json.loads(DEFINITIONS_FILE.read_text())
    html = HTML_FILE.read_text()

    # ── Title / heading ──────────────────────────────────────────────
    n_title = html.count("English Speech Drill")
    html = html.replace("English Speech Drill", "Japanese Speech Drill")
    print(f"  replaced title/heading ({n_title})")

    # ── Exercise corpus ──────────────────────────────────────────────
    ex_js = json.dumps(exercises, indent=2, ensure_ascii=False)
    html = sub_block(html, r"const exercises = \[.*?\n\];",
                     f"const exercises = {ex_js};", "exercise corpus")

    # ── Verb definitions ─────────────────────────────────────────────
    html = sub_block(html, r"const definitions = \{.*?\n\};",
                     f"const definitions = {fmt_defs(definitions)};", "definitions")

    # ── TENSE_NAMES (reused as Japanese verb-form names) ─────────────
    tense_names = """const TENSE_NAMES = {
  masu:          'Polite present (–masu)',
  masen:         'Polite negative (–masen)',
  mashita:       'Polite past (–mashita)',
  masen_deshita: 'Polite past neg. (–masen deshita)',
  te:            'Te-form (–te)',
  plain:         'Plain / dictionary',
  nai:           'Plain negative (–nai)',
  ta:            'Plain past (–ta)'
};"""
    html = sub_block(html, r"const TENSE_NAMES = \{.*?\n\};", tense_names, "TENSE_NAMES")

    # ── ALL_TENSES ───────────────────────────────────────────────────
    html = sub_block(html, r"const ALL_TENSES = \[.*?\];",
                     "const ALL_TENSES = ['masu','masen','mashita','masen_deshita','te','plain','nai','ta'];",
                     "ALL_TENSES", flags=0)

    # ── TENSE_DESCRIPTIONS (field names nombre/regla/conjugacion kept) ─
    tense_descs = """const TENSE_DESCRIPTIONS = {
  masu:          {nombre:'Polite present (–masu)', regla:'Polite non-past: "I eat / I will eat."', conjugacion:'masu-stem + ます. Ichidan: drop る (食べ→食べます). Godan: final -u to -i row (飲む→飲みます).'},
  masen:         {nombre:'Polite negative (–masen)', regla:'Polite negative non-past: "I do not eat."', conjugacion:'masu-stem + ません (食べません, 飲みません).'},
  mashita:       {nombre:'Polite past (–mashita)', regla:'Polite past: "I ate."', conjugacion:'masu-stem + ました (食べました, 飲みました).'},
  masen_deshita: {nombre:'Polite past negative', regla:'Polite past negative: "I did not eat."', conjugacion:'masu-stem + ませんでした (食べませんでした).'},
  te:            {nombre:'Te-form (–て)', regla:'Connective / requests / continuous. Links clauses; ください for requests.', conjugacion:'Ichidan: 食べて. Godan onbin: う/つ/る→って, ぬ/ぶ/む→んで, く→いて, ぐ→いで, す→して. 行く→行って.'},
  plain:         {nombre:'Plain / dictionary', regla:'Casual non-past; the dictionary form: "eat."', conjugacion:'The verb as listed (食べる, 飲む, する, 来る).'},
  nai:           {nombre:'Plain negative (–ない)', regla:'Casual negative non-past: "do not eat."', conjugacion:'Ichidan: 食べない. Godan: final -u to -a row + ない (飲まない); う→わ (買わない). する→しない, 来る→来ない.'},
  ta:            {nombre:'Plain past (–た)', regla:'Casual past: "ate."', conjugacion:'The te-form with て→た / で→だ (食べた, 飲んだ, 買った, 書いた).'}
};"""
    html = sub_block(html, r"const TENSE_DESCRIPTIONS = \{.*?\n\};", tense_descs,
                     "TENSE_DESCRIPTIONS")

    # ── feedbackPorTiempo ────────────────────────────────────────────
    feedback = """function feedbackPorTiempo(tense, item, u){
  const notas = [];
  switch(tense){
    case 'masu':
      notas.push('Polite present: masu-stem + ます (食べます, 飲みます).');
      break;
    case 'masen':
      notas.push('Polite negative: masu-stem + ません (食べません).');
      break;
    case 'mashita':
      notas.push('Polite past: masu-stem + ました (食べました).');
      break;
    case 'masen_deshita':
      notas.push('Polite past negative: masu-stem + ませんでした.');
      break;
    case 'te':
      notas.push('Te-form: ichidan 食べて; godan onbin う/つ/る→って, ぬ/ぶ/む→んで, く→いて, ぐ→いで, す→して.');
      break;
    case 'plain':
      notas.push('Plain form: the dictionary form itself (食べる, 飲む, する, 来る).');
      break;
    case 'nai':
      notas.push('Plain negative: a-row + ない (飲まない); godan う→わ (買わない).');
      break;
    case 'ta':
      notas.push('Plain past: te-form with て→た / で→だ (食べた, 飲んだ, 買った).');
      break;
  }
  return notas;
}"""
    html = sub_block(html, r"function feedbackPorTiempo\(tense, item, u\)\{.*?\n\}",
                     feedback, "feedbackPorTiempo")

    # ── Form filter pills ────────────────────────────────────────────
    pills = """<div class="tense-filter" id="tenseFilter">
      <button class="tense-pill active" data-tense="all">All</button>
      <button class="tense-pill" data-tense="masu">–masu</button>
      <button class="tense-pill" data-tense="masen">–masen</button>
      <button class="tense-pill" data-tense="mashita">–mashita</button>
      <button class="tense-pill" data-tense="masen_deshita">–masen deshita</button>
      <button class="tense-pill" data-tense="te">te-form</button>
      <button class="tense-pill" data-tense="plain">plain</button>
      <button class="tense-pill" data-tense="nai">–nai</button>
      <button class="tense-pill" data-tense="ta">–ta</button>
    </div>"""
    html = sub_block(html, r'<div class="tense-filter" id="tenseFilter">.*?</div>',
                     pills, "form filter pills")

    # ── Japanese-aware normalizar (strip spaces + JP punctuation) ────
    new_norm = """function normalizar(t){
  return (t || '')
    .toLowerCase()
    .normalize('NFKC')
    .replace(/[\\u3000\\s]+/g,'')
    .replace(/[、。・「」『』？！,.;?!]/g,'')
    .trim();
}"""
    html = sub_block(html, r"function normalizar\(t\)\{.*?\n\}", new_norm, "normalizar")

    # ── Japanese-aware incluyeAlguna (spaceless substring match) ─────
    new_incl = """function incluyeAlguna(texto, opciones){
  // Japanese has no word boundaries, so match each accepted form as a plain
  // contiguous substring (kana and kanji variants are both listed per group).
  return opciones.some(op => texto.includes(textoPlano(op)));
}"""
    html = sub_block(html, r"function incluyeAlguna\(texto, opciones\)\{.*?\n\}",
                     new_incl, "incluyeAlguna")

    # ── Recognition + TTS language ───────────────────────────────────
    n_lang = html.count("'en-US'")
    html = html.replace("'en-US'", "'ja-JP'")
    print(f"  replaced language code 'en-US' -> 'ja-JP' ({n_lang})")

    # ── Browser voice selection regexes ──────────────────────────────
    html = html.replace("/^en[-_]/i", "/^ja[-_]/i")
    html = html.replace("/en[-_]US/i", "/ja[-_]JP/i")
    html = html.replace("/en[-_]GB/i", "/ja[-_]JP/i")

    # ── Misc text ────────────────────────────────────────────────────
    html = html.replace("one complete sentence in English", "one complete sentence in Japanese")
    html = html.replace("Find English voices at elevenlabs.io/voices",
                        "Find a Japanese voice at elevenlabs.io/voices")
    html = html.replace("'practice-log-english.json'", "'practice-log-japanese.json'")

    # ── Speech-recognition error message (Japanese may be unsupported) ─
    old_err = """    } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed')) {
      $('vozPill').textContent = 'Mic: blocked';
      $('feedbackBox').innerHTML = '<span class="bad">Microphone access was blocked.</span> Check your browser permissions.';
    } else {"""
    new_err = """    } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed' || event.error === 'language-not-supported')) {
      $('vozPill').textContent = 'Mic: unavailable';
      $('feedbackBox').innerHTML = '<span class="bad">Japanese speech recognition could not start.</span> This browser most likely does not support Japanese recognition. Try this drill in Chrome on a computer, where Japanese recognition works, or switch the engine to on-device Whisper.';
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

    # ── Recognition-engines script -> Japanese variant ───────────────
    if "drill-recognition-engines-en.js" in html:
        html = html.replace("drill-recognition-engines-en.js",
                            "drill-recognition-engines-ja.js")
        print("  pointed recognition-engines script at -ja variant")
    else:
        print("  WARNING: recognition-engines script tag not found")

    HTML_FILE.write_text(html)
    print(f"\nWrote {HTML_FILE.name}: {len(exercises)} exercises, {len(definitions)} verbs.")


if __name__ == "__main__":
    main()
