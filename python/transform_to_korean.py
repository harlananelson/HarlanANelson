#!/usr/bin/env python3
"""Transform a copy of english-speech-drill.html into korean-speech-drill.html.

The UI text stays in English (an English speaker learning Korean); only the
language-learning content is swapped: the exercise corpus, the verb definitions,
the form system (TENSE_*), recognition/TTS language (ko-KR), and the title.

Korean, like Japanese, has no spaces inside a word, so the scorer strips
whitespace and Hangul punctuation and matches accepted forms as substrings.

Usage:
    cp english-speech-drill.html korean-speech-drill.html
    python3 python/generate_korean_exercises.py
    python3 python/transform_to_korean.py
"""
import json
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent
HTML_FILE = PROJECT / "korean-speech-drill.html"
EXERCISES_FILE = PROJECT / "python" / "output" / "korean_exercises.json"
DEFINITIONS_FILE = PROJECT / "python" / "output" / "korean_definitions.json"


def fmt_defs(defs):
    return "{\n" + ",\n".join(f'  "{k}":"{v}"' for k, v in defs.items()) + "\n}"


def sub_block(html, pattern, replacement, label, flags=re.DOTALL):
    new, n = re.subn(pattern, lambda m: replacement, html, count=1, flags=flags)
    print(f"  {'replaced' if n else 'WARNING: NOT FOUND -'} {label}")
    return new


def main():
    if not HTML_FILE.exists():
        raise SystemExit("Run first:  cp english-speech-drill.html korean-speech-drill.html")

    exercises = json.loads(EXERCISES_FILE.read_text())
    definitions = json.loads(DEFINITIONS_FILE.read_text())
    html = HTML_FILE.read_text()

    n_title = html.count("English Speech Drill")
    html = html.replace("English Speech Drill", "Korean Speech Drill")
    print(f"  replaced title/heading ({n_title})")

    ex_js = json.dumps(exercises, indent=2, ensure_ascii=False)
    html = sub_block(html, r"const exercises = \[.*?\n\];",
                     f"const exercises = {ex_js};", "exercise corpus")

    html = sub_block(html, r"const definitions = \{.*?\n\};",
                     f"const definitions = {fmt_defs(definitions)};", "definitions")

    tense_names = """const TENSE_NAMES = {
  yo:       'Polite present (–요)',
  an_yo:    'Polite negative (안 –요)',
  ss_yo:    'Polite past (–었어요)',
  an_ss_yo: 'Polite past neg. (안 –었어요)',
  da:       'Dictionary (–다)',
  nida:     'Formal present (–습니다)',
  seyo:     'Honourific (–세요)',
  go:       'Connective (–고)'
};"""
    html = sub_block(html, r"const TENSE_NAMES = \{.*?\n\};", tense_names, "TENSE_NAMES")

    html = sub_block(
        html, r"const ALL_TENSES = \[.*?\];",
        "const ALL_TENSES = ['yo','an_yo','ss_yo','an_ss_yo','da','nida','seyo','go'];",
        "ALL_TENSES", flags=0)

    tense_descs = """const TENSE_DESCRIPTIONS = {
  yo:       {nombre:'Polite present (–요)', regla:'Polite 해요체: "I go / I eat."', conjugacion:'가다→가요, 먹다→먹어요, 하다→해요. ㅏ/ㅗ take 아; otherwise 어. 하→해.'},
  an_yo:    {nombre:'Polite negative (안 –요)', regla:'Polite negative: "I do not go."', conjugacion:'안 + 해요체 (안 가요, 안 먹어요, 안 해요).'},
  ss_yo:    {nombre:'Polite past (–었어요)', regla:'Polite past: "I went / I ate."', conjugacion:'았/었 + 어요 (갔어요, 먹었어요, 했어요).'},
  an_ss_yo: {nombre:'Polite past negative', regla:'Polite past negative: "I did not go."', conjugacion:'안 + past (안 갔어요).'},
  da:       {nombre:'Dictionary (–다)', regla:'Citation form: "to go."', conjugacion:'The verb as listed (가다, 먹다, 하다).'},
  nida:     {nombre:'Formal present (–습니다)', regla:'Formal 합니다체: "I go."', conjugacion:'No batchim → ㅂ니다 (갑니다). Batchim → 습니다 (먹습니다). ㄹ drops (살다→삽니다).'},
  seyo:     {nombre:'Honourific (–세요)', regla:'Request / honourific: "please go."', conjugacion:'Stem + 세요; batchim takes 으세요 (가세요, 먹으세요). ㄹ drops (사세요).'},
  go:       {nombre:'Connective (–고)', regla:'Links clauses: "go and …"', conjugacion:'Stem + 고 (가고, 먹고, 하고).'}
};"""
    html = sub_block(html, r"const TENSE_DESCRIPTIONS = \{.*?\n\};", tense_descs,
                     "TENSE_DESCRIPTIONS")

    feedback = """function feedbackPorTiempo(tense, item, u){
  const notas = [];
  switch(tense){
    case 'yo':
      notas.push('Polite present: 가요, 먹어요, 해요 (하→해).');
      break;
    case 'an_yo':
      notas.push('Polite negative: 안 + 해요체 (안 가요).');
      break;
    case 'ss_yo':
      notas.push('Polite past: 았/었 + 어요 (갔어요, 먹었어요, 했어요).');
      break;
    case 'an_ss_yo':
      notas.push('Polite past negative: 안 + past (안 갔어요).');
      break;
    case 'da':
      notas.push('Dictionary form: 가다, 먹다, 하다.');
      break;
    case 'nida':
      notas.push('Formal present: no batchim → ㅂ니다; batchim → 습니다; ㄹ drops.');
      break;
    case 'seyo':
      notas.push('Honourific: stem + 세요 (batchim 으세요). ㄹ drops (사세요).');
      break;
    case 'go':
      notas.push('Connective: stem + 고 (가고, 먹고, 하고).');
      break;
  }
  return notas;
}"""
    html = sub_block(html, r"function feedbackPorTiempo\(tense, item, u\)\{.*?\n\}",
                     feedback, "feedbackPorTiempo")

    pills = """<div class="tense-filter" id="tenseFilter">
      <button class="tense-pill active" data-tense="all">All</button>
      <button class="tense-pill" data-tense="yo">–요</button>
      <button class="tense-pill" data-tense="an_yo">안 –요</button>
      <button class="tense-pill" data-tense="ss_yo">–었어요</button>
      <button class="tense-pill" data-tense="an_ss_yo">안 –었어요</button>
      <button class="tense-pill" data-tense="da">–다</button>
      <button class="tense-pill" data-tense="nida">–습니다</button>
      <button class="tense-pill" data-tense="seyo">–세요</button>
      <button class="tense-pill" data-tense="go">–고</button>
    </div>"""
    html = sub_block(html, r'<div class="tense-filter" id="tenseFilter">.*?</div>',
                     pills, "form filter pills")

    new_norm = """function normalizar(t){
  return (t || '')
    .toLowerCase()
    .normalize('NFKC')
    .replace(/[\\u3000\\s]+/g,'')
    .replace(/[.,;?!…·・、。「」『』？！]/g,'')
    .trim();
}"""
    html = sub_block(html, r"function normalizar\(t\)\{.*?\n\}", new_norm, "normalizar")

    new_incl = """function incluyeAlguna(texto, opciones){
  // Korean eojeol may arrive with or without spaces; match each accepted
  // form as a contiguous substring after space-stripping.
  return opciones.some(op => texto.includes(textoPlano(op)));
}"""
    html = sub_block(html, r"function incluyeAlguna\(texto, opciones\)\{.*?\n\}",
                     new_incl, "incluyeAlguna")

    n_lang = html.count("'en-US'")
    html = html.replace("'en-US'", "'ko-KR'")
    print(f"  replaced language code 'en-US' -> 'ko-KR' ({n_lang})")

    html = html.replace("/^en[-_]/i", "/^ko[-_]/i")
    html = html.replace("/en[-_]US/i", "/ko[-_]KR/i")
    html = html.replace("/en[-_]GB/i", "/ko[-_]KR/i")

    html = html.replace("one complete sentence in English", "one complete sentence in Korean")
    html = html.replace("Find English voices at elevenlabs.io/voices",
                        "Find a Korean voice at elevenlabs.io/voices")
    html = html.replace("'practice-log-english.json'", "'practice-log-korean.json'")

    old_err = """    } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed')) {
      $('vozPill').textContent = 'Mic: blocked';
      $('feedbackBox').innerHTML = '<span class="bad">Microphone access was blocked.</span> Check your browser permissions.';
    } else {"""
    new_err = """    } else if (event && (event.error === 'not-allowed' || event.error === 'service-not-allowed' || event.error === 'language-not-supported')) {
      $('vozPill').textContent = 'Mic: unavailable';
      $('feedbackBox').innerHTML = '<span class="bad">Korean speech recognition could not start.</span> This browser most likely does not support Korean recognition. Try this drill in Chrome on a computer, or switch the engine to on-device Whisper.';
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

    if "drill-recognition-engines-en.js" in html:
        html = html.replace("drill-recognition-engines-en.js",
                            "drill-recognition-engines-ko.js")
        print("  pointed recognition-engines script at -ko variant")
    else:
        print("  WARNING: recognition-engines script tag not found")

    HTML_FILE.write_text(html)
    print(f"\nWrote {HTML_FILE.name}: {len(exercises)} exercises, {len(definitions)} verbs.")


if __name__ == "__main__":
    main()
