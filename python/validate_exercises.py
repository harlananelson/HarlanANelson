#!/usr/bin/env python3
"""Validate generated Spanish speech drill exercises.

Checks:
1. All 6 required fields present
2. Every grupo element appears in respuesta (after normalization)
3. No accented characters in grupos
4. Time phrase / trigger phrase repetition (flag if >3 per tense)
5. Correct verb in exercise ID
6. Expected exercise count per verb per tense

Usage:
    python validate_exercises.py                    # validate all
    python validate_exercises.py --tense presente   # validate one tense
    python validate_exercises.py --fix              # auto-fix accent issues in grupos
"""

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

REQUIRED_FIELDS = {"id", "verbo", "contexto", "respuesta", "pista", "grupos"}

TENSE_EXPECTED_PER_VERB = {
    "presente": 3, "futuro": 3, "condicional": 3,
    "subjuntivo": 3, "subj_imperfecto": 3, "subj_pluscuam": 3,
    "puntual": 2, "habitual": 2, "fondo": 1, "anterior": 1,
}


def strip_accents(text: str) -> str:
    """Remove accent marks from text."""
    nfkd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def normalize(text: str) -> str:
    """Normalize text for comparison (lowercase, no accents, no punctuation)."""
    t = text.lower()
    t = strip_accents(t)
    t = re.sub(r'[¿?¡!.,;:\'"()]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def has_accents(text: str) -> bool:
    """Check if text contains accented characters."""
    return text != strip_accents(text)


def load_tense_exercises(tense: str) -> list:
    """Load all exercises for a tense from batch files."""
    tense_dir = OUTPUT_DIR / tense
    if not tense_dir.exists():
        return []
    exercises = []
    for batch_file in sorted(tense_dir.glob("batch_*.json")):
        data = json.loads(batch_file.read_text())
        exercises.extend(data)
    return exercises


def validate_exercise(ex: dict, tense: str) -> list:
    """Validate a single exercise. Returns list of issue strings."""
    issues = []

    # 1. Required fields
    missing = REQUIRED_FIELDS - set(ex.keys())
    if missing:
        issues.append(f"MISSING_FIELDS: {missing}")
        return issues  # can't validate further

    # 2. ID format
    if tense not in ex["id"]:
        issues.append(f"ID_TENSE_MISMATCH: id={ex['id']} doesn't contain tense={tense}")

    verb_in_id = ex["id"].rsplit(f"-{tense}", 1)[0] if f"-{tense}" in ex["id"] else ""
    if verb_in_id and verb_in_id != ex["verbo"]:
        issues.append(f"ID_VERB_MISMATCH: id has '{verb_in_id}' but verbo is '{ex['verbo']}'")

    # 3. grupos validation
    if not isinstance(ex["grupos"], list):
        issues.append("GRUPOS_NOT_LIST")
        return issues

    resp_norm = normalize(ex["respuesta"])

    for gi, grupo in enumerate(ex["grupos"]):
        if not isinstance(grupo, list):
            issues.append(f"GRUPO_{gi}_NOT_LIST: {grupo}")
            continue

        # Check accents in grupo elements
        for alt in grupo:
            if has_accents(alt):
                issues.append(f"GRUPO_HAS_ACCENT: grupo[{gi}] '{alt}' has accents")

        # Check that at least one alternative appears in respuesta
        found = any(normalize(alt) in resp_norm for alt in grupo)
        if not found:
            issues.append(f"GRUPO_NOT_IN_RESPUESTA: grupo[{gi}] {grupo} not found in '{ex['respuesta']}'")

    # 4. Empty fields
    for field in ["verbo", "contexto", "respuesta", "pista"]:
        if not ex[field].strip():
            issues.append(f"EMPTY_FIELD: {field}")

    return issues


def fix_accents_in_grupos(exercises: list) -> int:
    """Remove accents from all grupo elements. Returns count of fixes."""
    fixes = 0
    for ex in exercises:
        for grupo in ex.get("grupos", []):
            for i, alt in enumerate(grupo):
                stripped = strip_accents(alt)
                if stripped != alt:
                    grupo[i] = stripped
                    fixes += 1
    return fixes


def main():
    parser = argparse.ArgumentParser(description="Validate generated exercises")
    parser.add_argument("--tense", help="Validate only this tense")
    parser.add_argument("--fix", action="store_true", help="Auto-fix accent issues in grupos")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    tenses = [args.tense] if args.tense else list(TENSE_EXPECTED_PER_VERB.keys())
    total_exercises = 0
    total_issues = 0
    summary = {}

    for tense in tenses:
        exercises = load_tense_exercises(tense)
        if not exercises:
            print(f"\n{tense}: NO FILES FOUND")
            continue

        # Fix accents if requested
        if args.fix:
            fixes = fix_accents_in_grupos(exercises)
            if fixes:
                print(f"  Fixed {fixes} accent issues in {tense}")
                # Re-save
                tense_dir = OUTPUT_DIR / tense
                for batch_file in sorted(tense_dir.glob("batch_*.json")):
                    data = json.loads(batch_file.read_text())
                    fix_accents_in_grupos(data)
                    batch_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

        # Validate
        issues_by_type = Counter()
        verb_counts = Counter()
        time_phrases = Counter()
        issue_count = 0

        for ex in exercises:
            verb_counts[ex.get("verbo", "?")] += 1
            # Track time phrase usage
            contexto = ex.get("contexto", "")
            time_phrases[contexto] += 1

            ex_issues = validate_exercise(ex, tense)
            if ex_issues:
                issue_count += len(ex_issues)
                for issue in ex_issues:
                    issue_type = issue.split(":")[0]
                    issues_by_type[issue_type] += 1
                    if args.verbose:
                        print(f"  [{tense}] {ex.get('id','?')}: {issue}")

        # Check verb coverage
        expected_per = TENSE_EXPECTED_PER_VERB.get(tense, 3)
        under = sum(1 for v, c in verb_counts.items() if c < expected_per)
        over = sum(1 for v, c in verb_counts.items() if c > expected_per)

        # Check time phrase repetition
        repeated_phrases = {p: c for p, c in time_phrases.items() if c > 3}

        total_exercises += len(exercises)
        total_issues += issue_count

        status = "OK" if issue_count == 0 else "ISSUES"
        print(f"\n{tense}: {len(exercises)} exercises, {issue_count} issues [{status}]")
        if issues_by_type:
            for itype, count in issues_by_type.most_common():
                print(f"  {itype}: {count}")
        if under:
            print(f"  UNDER_COUNT: {under} verbs have <{expected_per} exercises")
        if over:
            print(f"  OVER_COUNT: {over} verbs have >{expected_per} exercises")
        if repeated_phrases and args.verbose:
            print(f"  REPEATED_CONTEXTS: {len(repeated_phrases)} contexts used >3 times")

        summary[tense] = {"count": len(exercises), "issues": issue_count}

    print(f"\n{'='*50}")
    print(f"TOTAL: {total_exercises} exercises, {total_issues} issues")
    if total_issues == 0:
        print("All exercises passed validation.")
    else:
        print("Run with --verbose for details, --fix to auto-fix accents.")


if __name__ == "__main__":
    main()
