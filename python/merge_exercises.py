#!/usr/bin/env python3
"""Merge generated exercises into spanish-speech-drill.html.

Reads all batch JSON files from python/output/, assigns sequential IDs starting
from the next available number, and appends to the actividades array in the HTML file.

Usage:
    python merge_exercises.py                 # merge all generated exercises
    python merge_exercises.py --dry-run       # show counts without modifying
    python merge_exercises.py --stats         # show exercise statistics
    python merge_exercises.py --json-only     # export exercises.json + definitions.json from HTML
"""

import argparse
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
HTML_FILE = PROJECT_DIR / "spanish-speech-drill.html"
OUTPUT_DIR = SCRIPT_DIR / "output"

TENSE_ORDER = [
    "presente", "futuro", "condicional",
    "subjuntivo", "subj_imperfecto", "subj_pluscuam",
    "puntual", "habitual", "fondo", "anterior",
]


def load_all_generated() -> list:
    """Load all generated exercises from output directory."""
    exercises = []
    for tense in TENSE_ORDER:
        tense_dir = OUTPUT_DIR / tense
        if not tense_dir.exists():
            continue
        for batch_file in sorted(tense_dir.glob("batch_*.json")):
            data = json.loads(batch_file.read_text())
            exercises.extend(data)
    return exercises


def find_max_id(html: str) -> int:
    """Find the highest numeric ID in existing exercises."""
    ids = re.findall(r'"id":\s*"[^"]*-(\d+)"', html)
    if not ids:
        return -1
    return max(int(i) for i in ids)


def reassign_ids(exercises: list, start_id: int) -> list:
    """Assign sequential IDs to exercises."""
    current_id = start_id
    for ex in exercises:
        # Extract verb and tense from existing id pattern
        verb = ex["verbo"]
        # Extract tense from the id
        tense = None
        for t in TENSE_ORDER:
            if f"-{t}-" in ex["id"] or ex["id"].endswith(f"-{t}-0"):
                tense = t
                break
        if not tense:
            # Fallback: try to parse from id
            parts = ex["id"].rsplit("-", 1)
            if len(parts) >= 2:
                prefix = parts[0]
                for t in TENSE_ORDER:
                    if prefix.endswith(f"-{t}"):
                        tense = t
                        break
        if not tense:
            tense = "unknown"

        ex["id"] = f"{verb}-{tense}-{current_id}"
        current_id += 1
    return exercises


def format_exercise_json(ex: dict) -> str:
    """Format a single exercise as indented JSON matching existing style."""
    lines = []
    lines.append("  {")
    lines.append(f'    "id": {json.dumps(ex["id"])},')
    lines.append(f'    "verbo": {json.dumps(ex["verbo"])},')
    lines.append(f'    "contexto": {json.dumps(ex["contexto"], ensure_ascii=False)},')
    lines.append(f'    "respuesta": {json.dumps(ex["respuesta"], ensure_ascii=False)},')
    lines.append(f'    "pista": {json.dumps(ex["pista"], ensure_ascii=False)},')
    lines.append(f'    "grupos": {json.dumps(ex["grupos"], ensure_ascii=False)}')
    lines.append("  }")
    return "\n".join(lines)


def merge(dry_run: bool = False):
    html = HTML_FILE.read_text(encoding="utf-8")

    # Find the end of the actividades array: the "];" on its own line after the data
    # The pattern is: line with just "];" after the exercise data
    # We know from the file that line 64878 has "];"
    match = re.search(r'(const actividades = \[)(.*?)(^\];)', html, re.DOTALL | re.MULTILINE)
    if not match:
        print("ERROR: Could not find 'const actividades = [...]' in HTML file")
        return

    array_start = match.start(1)
    array_end = match.end(3)
    existing_content = match.group(2)

    # Find max existing ID
    max_id = find_max_id(html)
    next_id = max_id + 1
    print(f"Existing max ID: {max_id}, new exercises start at: {next_id}")

    # Load generated exercises
    generated = load_all_generated()
    if not generated:
        print("No generated exercises found in python/output/")
        return

    print(f"Generated exercises to merge: {len(generated)}")

    # Show stats by tense
    from collections import Counter
    tense_counts = Counter()
    for ex in generated:
        for t in TENSE_ORDER:
            if f"-{t}-" in ex["id"] or ex["id"].endswith(f"-{t}-0"):
                tense_counts[t] += 1
                break

    for t in TENSE_ORDER:
        if tense_counts[t]:
            print(f"  {t}: {tense_counts[t]}")

    if dry_run:
        print("\nDry run — no files modified.")
        return

    # Reassign IDs
    generated = reassign_ids(generated, next_id)

    # Format new exercises
    new_json_parts = []
    for ex in generated:
        new_json_parts.append(format_exercise_json(ex))

    new_exercises_text = ",\n".join(new_json_parts)

    # Insert before the closing "];"
    # Remove trailing whitespace/newline from existing content, add comma, then new exercises
    existing_trimmed = existing_content.rstrip()
    if existing_trimmed.endswith(","):
        separator = "\n"
    else:
        separator = ",\n"

    new_html = (
        html[:array_start]
        + "const actividades = ["
        + existing_trimmed
        + separator
        + new_exercises_text
        + "\n];"
        + html[array_end:]
    )

    HTML_FILE.write_text(new_html, encoding="utf-8")

    # Verify
    new_count = len(re.findall(r'"id":', new_html))
    print(f"\nMerge complete. Total exercises in file: {new_count}")


def export_json_only():
    """Extract exercises and definitions from HTML as standalone JSON files."""
    html = HTML_FILE.read_text(encoding="utf-8")

    # Extract actividades array
    match = re.search(r'const actividades = (\[.*?^\]);', html, re.DOTALL | re.MULTILINE)
    if not match:
        print("ERROR: Could not find actividades array in HTML")
        return
    exercises = json.loads(match.group(1))
    print(f"Extracted {len(exercises)} exercises")

    # Extract definiciones object
    def_match = re.search(r'const definiciones = (\{.*?\});', html, re.DOTALL)
    if not def_match:
        print("ERROR: Could not find definiciones object in HTML")
        return
    # definiciones is JS object — keys aren't quoted. Parse manually.
    def_text = def_match.group(1)
    # Add quotes around unquoted keys: word:"value" -> "word":"value"
    def_text = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r'"\1":', def_text)
    definitions = json.loads(def_text)
    print(f"Extracted {len(definitions)} definitions")

    # Write output
    out_dir = PROJECT_DIR / "ios" / "SpanishDrill" / "Resources"
    out_dir.mkdir(parents=True, exist_ok=True)

    exercises_path = out_dir / "exercises.json"
    exercises_path.write_text(json.dumps(exercises, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {exercises_path}")

    definitions_path = out_dir / "definitions.json"
    definitions_path.write_text(json.dumps(definitions, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {definitions_path}")


def stats():
    """Show statistics about generated exercises."""
    from collections import Counter
    for tense in TENSE_ORDER:
        tense_dir = OUTPUT_DIR / tense
        if not tense_dir.exists():
            print(f"{tense}: no files")
            continue
        count = 0
        verbs = set()
        for batch_file in sorted(tense_dir.glob("batch_*.json")):
            data = json.loads(batch_file.read_text())
            count += len(data)
            for ex in data:
                verbs.add(ex.get("verbo", "?"))
        print(f"{tense}: {count} exercises, {len(verbs)} verbs, {len(list(tense_dir.glob('batch_*.json')))} batches")


def main():
    parser = argparse.ArgumentParser(description="Merge generated exercises into HTML")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--json-only", action="store_true",
                        help="Export exercises.json + definitions.json from HTML")
    args = parser.parse_args()

    if args.json_only:
        export_json_only()
    elif args.stats:
        stats()
    else:
        merge(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
