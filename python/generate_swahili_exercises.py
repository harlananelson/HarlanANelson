#!/usr/bin/env python3
"""Generate Swahili verb-marker drill exercises for swahili-speech-drill.html.

Covers the AFFIRMATIVE forms of regular polysyllabic Bantu verbs across the five
core verb markers (-na- -li- -ta- -me- -nge-). For these verbs the conjugated
form is simply  subject-prefix + marker + verb-stem, which is fully regular.

Monosyllabic verbs (kula, kunywa, kuja, kwenda ...) are deliberately EXCLUDED:
they have special ku- retention behaviour and are deferred to a later pass.
"""

import json
import random
from pathlib import Path

random.seed(42)

# ── Subjects: (pronoun, subject prefix) ──────────────────────────────────
SUBJECTS = [
    ("mimi", "ni"), ("wewe", "u"), ("yeye", "a"),
    ("sisi", "tu"), ("ninyi", "m"), ("wao", "wa"),
]

# ── Verb markers: key -> (English name, learner hint) ────────────────────
MARKERS = {
    "na":  ("Present", "Present tense: subject prefix + -na- + verb stem. ni-na-soma gives ninasoma."),
    "li":  ("Past", "Past tense: subject prefix + -li- + verb stem. ni-li-soma gives nilisoma."),
    "ta":  ("Future", "Future tense: subject prefix + -ta- + verb stem. ni-ta-soma gives nitasoma."),
    "me":  ("Perfect", "Perfect: subject prefix + -me- + verb stem (completed, still relevant). ni-me-soma gives nimesoma."),
    "nge": ("Conditional", "Conditional: subject prefix + -nge- + verb stem ('would'). ni-nge-soma gives ningesoma."),
}
ALL_MARKERS = ["na", "li", "ta", "me", "nge"]

# ── Verbs: stem -> (English gloss, [complements]) ────────────────────────
# All polysyllabic and regular: conjugated form = prefix + marker + stem.
VERBS = {
    "soma":     ("read / study", ["kitabu", "barua", "gazeti", "somo"]),
    "andika":   ("write", ["barua", "jina", "hadithi", "insha"]),
    "fanya":    ("do / make", ["kazi", "mazoezi", "biashara"]),
    "ona":      ("see", ["gari", "ndege", "mlima", "rafiki"]),
    "penda":    ("like / love", ["chakula", "muziki", "kusoma"]),
    "taka":     ("want", ["maji", "msaada", "chai"]),
    "sema":     ("say / speak", ["ukweli", "Kiswahili", "habari"]),
    "fika":     ("arrive", ["nyumbani", "shuleni", "kazini"]),
    "nunua":    ("buy", ["chakula", "nguo", "matunda", "gari"]),
    "saidia":   ("help", ["rafiki", "mama", "mwalimu"]),
    "pika":     ("cook", ["chakula", "wali", "ugali"]),
    "cheza":    ("play", ["mpira", "muziki", "michezo"]),
    "imba":     ("sing", ["wimbo", "nyimbo"]),
    "jua":      ("know", ["jibu", "njia", "Kiswahili"]),
    "ngoja":    ("wait for", ["basi", "rafiki", "mvua"]),
    "fungua":   ("open", ["mlango", "dirisha", "duka"]),
    "funga":    ("close / tie", ["mlango", "dirisha", "duka"]),
    "safisha":  ("clean", ["nyumba", "chumba", "gari"]),
    "osha":     ("wash", ["sahani", "nguo", "mikono"]),
    "sikia":    ("hear / feel", ["habari", "sauti", "muziki"]),
    "elewa":    ("understand", ["somo", "Kiswahili", "swali"]),
    "rudi":     ("return", ["nyumbani", "shuleni", "mjini"]),
    "kumbuka":  ("remember", ["jina", "siku", "namba"]),
    "panda":    ("climb / board / plant", ["basi", "mlima", "mti"]),
    "anza":     ("begin", ["kazi", "somo", "safari"]),
    "maliza":   ("finish", ["kazi", "chakula", "somo"]),
    "weka":     ("put / keep", ["kitabu", "pesa", "chakula"]),
    "leta":     ("bring", ["chakula", "maji", "kitabu"]),
    "pata":     ("get / obtain", ["pesa", "kazi", "barua"]),
    "piga":     ("hit / strike", ["simu", "picha", "ngoma"]),
    "tafuta":   ("look for", ["kazi", "rafiki", "njia"]),
    "lipa":     ("pay", ["pesa", "deni", "kodi"]),
    "fundisha": ("teach", ["Kiswahili", "watoto", "somo"]),
}

# ── Time words per marker ────────────────────────────────────────────────
TIME = {
    "na":  ["sasa", "kila siku", "leo", "asubuhi"],
    "li":  ["jana", "juzi", "wiki iliyopita", "asubuhi"],
    "ta":  ["kesho", "wiki ijayo", "baadaye", "mwakani"],
    "me":  ["tayari", "leo", "sasa hivi"],
    "nge": [""],   # the conditional pairs awkwardly with a bare time word
}


def conjugate(prefix, marker, stem):
    """Affirmative regular conjugation: prefix + marker + stem."""
    return prefix + marker + stem


def generate_exercises():
    exercises = []
    counter = 0
    for stem, (gloss, complements) in VERBS.items():
        for marker in ALL_MARKERS:
            seen = set()
            for _ in range(3):
                pron, prefix = random.choice(SUBJECTS)
                comp = random.choice(complements)
                time = random.choice(TIME[marker])
                combo = (prefix, comp, time)
                tries = 0
                while combo in seen and tries < 15:
                    pron, prefix = random.choice(SUBJECTS)
                    comp = random.choice(complements)
                    time = random.choice(TIME[marker])
                    combo = (prefix, comp, time)
                    tries += 1
                seen.add(combo)

                verb = conjugate(prefix, marker, stem)
                if time:
                    sentence = f"{verb} {comp} {time}."
                    grupos = [[verb], [comp], [time]]
                    context = f"{pron}, ku{stem}, {comp}, {time}"
                else:
                    sentence = f"{verb} {comp}."
                    grupos = [[verb], [comp]]
                    context = f"{pron}, ku{stem}, {comp}"

                exercises.append({
                    "id": f"{stem}-{marker}-{counter}",
                    "verbo": stem,
                    "contexto": context,
                    "respuesta": sentence,
                    "pista": MARKERS[marker][1],
                    "grupos": grupos,
                })
                counter += 1
    return exercises


def main():
    exercises = generate_exercises()
    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)

    (out / "swahili_exercises.json").write_text(
        json.dumps(exercises, indent=2, ensure_ascii=False))
    print(f"Generated {len(exercises)} exercises -> python/output/swahili_exercises.json")

    definitions = {stem: gloss for stem, (gloss, _comp) in VERBS.items()}
    (out / "swahili_definitions.json").write_text(
        json.dumps(definitions, indent=2, ensure_ascii=False))
    print(f"Generated {len(definitions)} definitions -> python/output/swahili_definitions.json")


if __name__ == "__main__":
    main()
