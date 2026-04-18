#!/usr/bin/env python3
"""Generate English tense drill exercises for english-speech-drill.html."""

import json
import random
import re
from pathlib import Path

random.seed(42)

# ── Verb conjugation tables ──────────────────────────────────────────────
# (base, 3rd_present, past, past_participle, present_participle)
VERB_FORMS = {
    "be":    ("be", "is", "was", "been", "being"),
    "have":  ("have", "has", "had", "had", "having"),
    "do":    ("do", "does", "did", "done", "doing"),
    "go":    ("go", "goes", "went", "gone", "going"),
    "say":   ("say", "says", "said", "said", "saying"),
    "get":   ("get", "gets", "got", "gotten", "getting"),
    "make":  ("make", "makes", "made", "made", "making"),
    "know":  ("know", "knows", "knew", "known", "knowing"),
    "think": ("think", "thinks", "thought", "thought", "thinking"),
    "take":  ("take", "takes", "took", "taken", "taking"),
    "see":   ("see", "sees", "saw", "seen", "seeing"),
    "come":  ("come", "comes", "came", "come", "coming"),
    "want":  ("want", "wants", "wanted", "wanted", "wanting"),
    "give":  ("give", "gives", "gave", "given", "giving"),
    "tell":  ("tell", "tells", "told", "told", "telling"),
    "work":  ("work", "works", "worked", "worked", "working"),
    "find":  ("find", "finds", "found", "found", "finding"),
    "leave": ("leave", "leaves", "left", "left", "leaving"),
    "run":   ("run", "runs", "ran", "run", "running"),
    "walk":  ("walk", "walks", "walked", "walked", "walking"),
}

# "be" needs special conjugation per subject
BE_FORMS = {
    "simple_present": {"I": "am", "you": "are", "he": "is", "she": "is", "we": "are", "they": "are"},
    "simple_past":    {"I": "was", "you": "were", "he": "was", "she": "was", "we": "were", "they": "were"},
    "past_continuous": {"I": "was", "you": "were", "he": "was", "she": "was", "we": "were", "they": "were"},
}

# ── Subject pools ────────────────────────────────────────────────────────
SUBJECTS_3RD = ["he", "she"]
SUBJECTS_NON3RD = ["I", "you", "we", "they"]
ALL_SUBJECTS = SUBJECTS_3RD + SUBJECTS_NON3RD

# ── Time adverbs per tense ──────────────────────────────────────────────
TIME_ADVERBS = {
    "simple_present":       ["every day", "every morning", "usually", "always", "often", "sometimes"],
    "present_continuous":   ["right now", "at the moment", "currently", "today"],
    "simple_past":          ["yesterday", "last week", "last night", "two days ago", "last month"],
    "past_continuous":      ["at that moment", "at 5 pm yesterday", "when the phone rang", "all morning yesterday"],
    "present_perfect":      ["already", "recently", "many times", "before", "just", "twice"],
    "past_perfect":         ["before the meeting", "before she arrived", "by that time", "already"],
    "simple_future":        ["tomorrow", "next week", "next month", "soon", "later today"],
    "future_continuous":    ["at 8 am tomorrow", "this time next week", "all day tomorrow", "at noon tomorrow"],
    "conditional":          ["if it were possible", "if she had time", "if the weather were nice", "in that situation"],
    "used_to":              ["when I was young", "years ago", "as a child", "in the past", "back then"],
    "present_perfect_cont": ["for an hour", "for two weeks", "since morning", "since last year", "all day"],
    "past_perfect_cont":    ["for an hour", "for two weeks", "since morning", "all day", "for a long time"],
}

# ── Complements per verb ─────────────────────────────────────────────────
COMPLEMENTS = {
    "be":    ["happy", "tired", "ready", "at home", "busy"],
    "have":  ["breakfast", "a meeting", "a good time", "a problem", "lunch"],
    "do":    ["the homework", "the dishes", "the laundry", "the work", "exercise"],
    "go":    ["to school", "to work", "to the park", "home", "to the store"],
    "say":   ["hello", "goodbye", "the truth", "something important", "thank you"],
    "get":   ["a new job", "the answer", "a good grade", "ready", "home"],
    "make":  ["dinner", "a cake", "a decision", "a plan", "coffee"],
    "know":  ["the answer", "the truth", "her name", "the way", "the rules"],
    "think": ["about the problem", "about the future", "carefully", "about it", "about the plan"],
    "take":  ["the bus", "a walk", "a break", "the test", "a photo"],
    "see":   ["the movie", "the doctor", "her friends", "the results", "the sunset"],
    "come":  ["to the party", "home early", "to class", "to the office", "back"],
    "want":  ["a new car", "to help", "some water", "to learn", "the job"],
    "give":  ["a present", "the answer", "advice", "a speech", "directions"],
    "tell":  ["the truth", "a story", "her the news", "him the answer", "a joke"],
    "work":  ["at the office", "on the project", "hard", "from home", "overtime"],
    "find":  ["the keys", "a solution", "the right answer", "a new apartment", "the book"],
    "leave": ["the house", "early", "the office", "for work", "the country"],
    "run":   ["in the park", "every morning", "a marathon", "to the store", "five miles"],
    "walk":  ["to school", "in the park", "home", "to work", "down the street"],
}

# ── Hints per tense ──────────────────────────────────────────────────────
HINTS = {
    "simple_present":       "Think about a habitual action or general truth — use the simple present.",
    "present_continuous":   "This is happening right now — use am/is/are + verb-ing.",
    "simple_past":          "This action is finished — use the simple past form.",
    "past_continuous":      "An action was in progress at a past moment — use was/were + verb-ing.",
    "present_perfect":      "This connects past to present — use have/has + past participle.",
    "past_perfect":         "One past action happened before another — use had + past participle.",
    "simple_future":        "This will happen later — use will + base form.",
    "future_continuous":    "An action will be in progress at a future time — use will be + verb-ing.",
    "conditional":          "This is hypothetical — use would + base form.",
    "used_to":              "This was a past habit that is no longer true — use used to + base form.",
    "present_perfect_cont": "This action started in the past and continues now — use have/has been + verb-ing.",
    "past_perfect_cont":    "This action was ongoing before another past event — use had been + verb-ing.",
}


def conjugate(verb, tense, subject):
    """Return the conjugated verb phrase for a given tense and subject."""
    base, s3, past, pp, ing = VERB_FORMS[verb]
    subj_lower = subject.lower()
    is_3rd = subj_lower in ("he", "she", "it")

    # Special handling for "be"
    if verb == "be":
        return _conjugate_be(tense, subject, subj_lower, is_3rd)

    if tense == "simple_present":
        return s3 if is_3rd else base
    elif tense == "present_continuous":
        aux = "is" if is_3rd else ("am" if subj_lower == "i" else "are")
        return f"{aux} {ing}"
    elif tense == "simple_past":
        return past
    elif tense == "past_continuous":
        aux = "was" if (is_3rd or subj_lower == "i") else "were"
        return f"{aux} {ing}"
    elif tense == "present_perfect":
        aux = "has" if is_3rd else "have"
        return f"{aux} {pp}"
    elif tense == "past_perfect":
        return f"had {pp}"
    elif tense == "simple_future":
        return f"will {base}"
    elif tense == "future_continuous":
        return f"will be {ing}"
    elif tense == "conditional":
        return f"would {base}"
    elif tense == "used_to":
        return f"used to {base}"
    elif tense == "present_perfect_cont":
        aux = "has" if is_3rd else "have"
        return f"{aux} been {ing}"
    elif tense == "past_perfect_cont":
        return f"had been {ing}"
    return base


def _conjugate_be(tense, subject, subj_lower, is_3rd):
    """Special conjugation for 'be'."""
    if tense == "simple_present":
        return BE_FORMS["simple_present"].get(subject, BE_FORMS["simple_present"].get(subj_lower.capitalize(), "is"))
    elif tense == "present_continuous":
        aux = BE_FORMS["simple_present"].get(subject, "is")
        return f"{aux} being"
    elif tense == "simple_past":
        return BE_FORMS["simple_past"].get(subject, BE_FORMS["simple_past"].get(subj_lower.capitalize(), "was"))
    elif tense == "past_continuous":
        aux = BE_FORMS["past_continuous"].get(subject, "was")
        return f"{aux} being"
    elif tense == "present_perfect":
        aux = "has" if is_3rd else "have"
        return f"{aux} been"
    elif tense == "past_perfect":
        return "had been"
    elif tense == "simple_future":
        return "will be"
    elif tense == "future_continuous":
        return "will be being"
    elif tense == "conditional":
        return "would be"
    elif tense == "used_to":
        return "used to be"
    elif tense == "present_perfect_cont":
        # "be" doesn't naturally form present perfect continuous — skip
        aux = "has" if is_3rd else "have"
        return f"{aux} been being"
    elif tense == "past_perfect_cont":
        return "had been being"
    return "be"


# Skip awkward combinations
SKIP_COMBOS = {
    ("be", "present_continuous"),      # "is being happy" is awkward
    ("be", "present_perfect_cont"),    # "has been being" is very rare
    ("be", "past_perfect_cont"),       # "had been being" is very rare
    ("be", "future_continuous"),       # "will be being" is very rare
    ("know", "present_continuous"),    # "is knowing" — stative verb
    ("know", "past_continuous"),
    ("know", "future_continuous"),
    ("know", "present_perfect_cont"),
    ("know", "past_perfect_cont"),
    ("want", "present_continuous"),    # "is wanting" — stative verb
    ("want", "past_continuous"),
    ("want", "future_continuous"),
    ("want", "present_perfect_cont"),
    ("want", "past_perfect_cont"),
}


def build_grupos(subject, verb_phrase, complement, time_adverb):
    """Build key-phrase groups for scoring."""
    groups = []
    groups.append([subject.lower()])
    # Split multi-word verb phrases into one group
    groups.append([verb_phrase.lower()])
    groups.append([complement.lower()])
    groups.append([time_adverb.lower()])
    return groups


def generate_exercises():
    """Generate all exercises."""
    exercises = []
    tenses = list(TIME_ADVERBS.keys())
    counter = 0

    for verb in VERB_FORMS:
        for tense in tenses:
            if (verb, tense) in SKIP_COMBOS:
                continue

            complements = COMPLEMENTS[verb]
            adverbs = TIME_ADVERBS[tense]

            # Generate 2-3 exercises per verb-tense
            num_exercises = random.choice([2, 2, 3])
            used_combos = set()

            for _ in range(num_exercises):
                # Pick a subject
                subject = random.choice(ALL_SUBJECTS)
                complement = random.choice(complements)
                adverb = random.choice(adverbs)

                combo = (subject, complement, adverb)
                attempts = 0
                while combo in used_combos and attempts < 10:
                    subject = random.choice(ALL_SUBJECTS)
                    complement = random.choice(complements)
                    adverb = random.choice(adverbs)
                    combo = (subject, complement, adverb)
                    attempts += 1
                used_combos.add(combo)

                verb_phrase = conjugate(verb, tense, subject)

                # Build the sentence based on tense patterns
                # Time adverb position varies by tense
                if tense in ("present_perfect", "past_perfect") and adverb in ("already", "just"):
                    # "She has already found the keys"
                    parts = verb_phrase.split(" ", 1)
                    sentence = f"{subject} {parts[0]} {adverb} {parts[1]} {complement}."
                    grupos = build_grupos(subject, verb_phrase, complement, adverb)
                elif tense == "used_to":
                    sentence = f"{subject} {verb_phrase} {complement} {adverb}."
                    grupos = build_grupos(subject, verb_phrase, complement, adverb)
                else:
                    sentence = f"{subject} {verb_phrase} {complement} {adverb}."
                    grupos = build_grupos(subject, verb_phrase, complement, adverb)

                # Build context prompt (fragments for the user)
                context = f"{subject.lower()}, {adverb}, {complement}"

                exercise = {
                    "id": f"{verb}-{tense}-{counter}",
                    "verbo": verb,
                    "contexto": context,
                    "respuesta": sentence,
                    "pista": HINTS[tense],
                    "grupos": grupos,
                }
                exercises.append(exercise)
                counter += 1

    return exercises


def main():
    exercises = generate_exercises()
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "english_exercises.json"
    with open(output_file, "w") as f:
        json.dump(exercises, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(exercises)} exercises → {output_file}")

    # Also output definitions
    definitions = {}
    for verb, (base, s3, past, pp, ing) in VERB_FORMS.items():
        if verb == "be":
            definitions[verb] = "exist, identity, state — am/is/are, was/were, been"
        elif verb == "have":
            definitions[verb] = "possess, auxiliary — has, had"
        elif verb == "do":
            definitions[verb] = "perform an action — does, did, done"
        elif verb == "go":
            definitions[verb] = "move, travel — goes, went, gone"
        elif verb == "say":
            definitions[verb] = "speak words — says, said"
        elif verb == "get":
            definitions[verb] = "obtain, become — gets, got, gotten"
        elif verb == "make":
            definitions[verb] = "create, produce — makes, made"
        elif verb == "know":
            definitions[verb] = "be aware of — knows, knew, known"
        elif verb == "think":
            definitions[verb] = "believe, consider — thinks, thought"
        elif verb == "take":
            definitions[verb] = "grab, carry — takes, took, taken"
        elif verb == "see":
            definitions[verb] = "perceive with eyes — sees, saw, seen"
        elif verb == "come":
            definitions[verb] = "move toward, arrive — comes, came"
        elif verb == "want":
            definitions[verb] = "desire, wish for — wants, wanted"
        elif verb == "give":
            definitions[verb] = "transfer, provide — gives, gave, given"
        elif verb == "tell":
            definitions[verb] = "communicate, inform — tells, told"
        elif verb == "work":
            definitions[verb] = "labor, function — works, worked"
        elif verb == "find":
            definitions[verb] = "discover, locate — finds, found"
        elif verb == "leave":
            definitions[verb] = "depart, go away — leaves, left"
        elif verb == "run":
            definitions[verb] = "move quickly — runs, ran"
        elif verb == "walk":
            definitions[verb] = "move on foot — walks, walked"

    defs_file = output_dir / "english_definitions.json"
    with open(defs_file, "w") as f:
        json.dump(definitions, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(definitions)} definitions → {defs_file}")


if __name__ == "__main__":
    main()
