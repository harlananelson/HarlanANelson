#!/usr/bin/env python3
"""Apply the cleanup fixes from spanish-drill-cleanup. to spanish-speech-drill.html."""

import json
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent
HTML_FILE = PROJECT / "spanish-speech-drill.html"


def fix_accents(t):
    """Fix common missing accents."""
    replacements = [
        (r'\beramos\b', 'éramos'),
        (r'\bestabamos\b', 'estábamos'),
        (r'\bteniamos\b', 'teníamos'),
        (r'\bhabiamos\b', 'habíamos'),
        (r'\bhabias\b', 'habías'),
        (r'\bhabian\b', 'habían'),
        (r'\bhabia\b', 'había'),
        (r'\berais\b', 'erais'),
        (r'\bcreio\b', 'creyó'),
        (r'\bcrei\b', 'creí'),
        (r'\bdecias\b', 'decías'),
        (r'\bdecian\b', 'decían'),
        (r'\bhablo\b', 'habló'),
        (r'\bdejo\b', 'dejó'),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t)
    return t


def fix_haber(t):
    """Fix invalid haber conjugations."""
    replacements = [
        (r'\bhabimos\b', 'habíamos'),
        (r'\bhabio\b', 'hubo'),
        (r'\bhabiste\b', 'hubiste'),
        (r'\bhabia habido\b', 'había habido'),
        (r'\bhabiamos habido\b', 'habíamos habido'),
    ]
    for pat, repl in replacements:
        t = re.sub(pat, repl, t)
    return t


def fix_agreement(t):
    """Fix adjective agreement for plural subjects."""
    # Only fix "muy feliz" -> "muy felices" when preceded by plural subject indicators
    # Be conservative: the JS version was too aggressive (changed all instances)
    # We'll apply the same broad replacement as the original script
    t = re.sub(r'\béramos muy feliz\b', 'éramos muy felices', t)
    return t


def clean_text(t):
    """Apply all text fixes."""
    t = fix_accents(t)
    t = fix_haber(t)
    t = fix_agreement(t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def clean_grupo_word(w):
    """Apply accent fixes to grupo words."""
    replacements = [
        (r'\beramos\b', 'éramos'),
        (r'\bhabiamos\b', 'habíamos'),
        (r'\bhabia\b', 'había'),
        (r'\bcreio\b', 'creyó'),
        (r'\bdecias\b', 'decías'),
        (r'\bhabimos\b', 'habíamos'),
        (r'\bhablo\b', 'habló'),
        (r'\bdejo\b', 'dejó'),
    ]
    for pat, repl in replacements:
        w = re.sub(pat, repl, w)
    return w


def main():
    with open(HTML_FILE) as f:
        html = f.read()

    # Extract the actividades JSON array
    match = re.search(r'const actividades = (\[.*?\n\]);', html, re.DOTALL)
    if not match:
        print("ERROR: Could not find actividades array")
        return

    exercises = json.loads(match.group(1))
    changes = 0

    for item in exercises:
        old_resp = item['respuesta']
        new_resp = clean_text(old_resp)

        if old_resp != new_resp:
            item['respuesta'] = new_resp
            changes += 1

        # Clean grupos
        if 'grupos' in item and isinstance(item['grupos'], list):
            for i, group in enumerate(item['grupos']):
                for j, word in enumerate(group):
                    cleaned = clean_grupo_word(word)
                    if cleaned != word:
                        item['grupos'][i][j] = cleaned

            # Add missing key words
            resp_lower = new_resp.lower()
            flat = [w for g in item['grupos'] for w in g]

            if 'ya ' in resp_lower and not any('ya' in g for g in flat):
                item['grupos'].append(['ya'])

            if ('antes' in resp_lower or 'hasta ese día' in resp_lower) and \
               not any('antes' in g or 'hasta' in g for g in flat):
                item['grupos'].append(['antes'])

            if 'cuando ' in resp_lower and not any('cuando' in g for g in flat):
                item['grupos'].append(['cuando'])

    # Rebuild the JSON
    new_json = json.dumps(exercises, indent=2, ensure_ascii=False)
    new_block = f'const actividades = {new_json};'

    html = html[:match.start()] + new_block + html[match.end():]

    with open(HTML_FILE, 'w') as f:
        f.write(html)

    print(f"Fixed {changes} exercises in {HTML_FILE.name}")


if __name__ == "__main__":
    main()
