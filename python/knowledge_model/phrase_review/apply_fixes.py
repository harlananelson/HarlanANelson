#!/usr/bin/env python3
"""Apply the mechanical subset of the 2026-08-01 phrase-review fixes.

Reads findings/<lang>.json, patches the exercise arrays embedded in the
drill HTML files, keeps `grupos` in sync, and re-verifies the invariant
that every grupos element appears in the accent-stripped lowercased
respuesta.

Mechanical policy (deliberately conservative):
  - pista / contexto fields: apply every finding's fix (no grupos
    constraint; TTS-facing text only).
  - respuesta:
      * Spanish: apply ONLY diacritic-restoration fixes (text == fix after
        accent stripping). Rewording waits for regeneration.
      * English/Swahili: apply all respuesta fixes, then repair grupos
        tokens that stopped matching; if a token can't be repaired, revert
        that fix and log it.
  - Never touch an exercise whose finding text no longer matches (already
    edited, or reviewer paraphrased) — log and skip.

Usage: python apply_fixes.py [--dry-run]
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parents[2]

DRILLS = {
    "spanish": ("spanish-speech-drill.html", "const actividades = "),
    "english": ("english-speech-drill.html", "const exercises = "),
    "japanese": ("japanese-speech-drill.html", "const exercises = "),
    "swahili": ("swahili-speech-drill.html", "const exercises = "),
}

SPANISH_TENSES = ["presente", "futuro", "condicional", "subjuntivo",
                  "subj_imperfecto", "subj_pluscuam", "puntual", "habitual",
                  "fondo", "anterior"]


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def norm(s):
    return strip_accents((s or "").lower())


def load_exercises(lang):
    fn, marker = DRILLS[lang]
    src = (SITE / fn).read_text(encoding="utf-8")
    i = src.index(marker + "[")
    j = src.index("];", i)
    arr = json.loads(src[i + len(marker):j + 1])
    return src, arr, i + len(marker), j + 1


def save_exercises(lang, src, arr, a, b, dry):
    fn, _ = DRILLS[lang]
    blob = json.dumps(arr, ensure_ascii=False, indent=2)
    if not dry:
        (SITE / fn).write_text(src[:a] + blob + src[b:], encoding="utf-8")


def findings_for(lang):
    if lang == "spanish":
        out = []
        for t in SPANISH_TENSES:
            p = HERE / "findings" / f"{t}.json"
            if p.exists():
                out += json.loads(p.read_text())
        return out
    p = HERE / "findings" / f"{lang}.json"
    return json.loads(p.read_text()) if p.exists() else []


def grupos_ok(ex):
    """Return list of grupos tokens that do NOT appear in the respuesta."""
    resp = norm(ex.get("respuesta", ""))
    bad = []
    for g in ex.get("grupos", []):
        # a group matches if ANY of its variant tokens appears
        if not any(norm(tok) in resp for tok in g):
            bad.append(g)
    return bad


def repair_grupos(ex, old_resp, new_resp):
    """After a respuesta edit, replace changed words inside grupos tokens.
    Word-level pairing between old and new respuesta; returns False if a
    group can't be made to match the new respuesta."""
    ow, nw = norm(old_resp).replace(".", " ").split(), norm(new_resp).replace(".", " ").split()
    # crude alignment: words removed vs added
    removed = [w for w in ow if w not in nw]
    added = [w for w in nw if w not in ow]
    if len(removed) == len(added):
        mapping = dict(zip(removed, added))
    elif not added:
        mapping = {w: "" for w in removed}   # pure deletion ("was being" -> "was")
    else:
        mapping = {}
    for g in ex.get("grupos", []):
        for k, tok in enumerate(g):
            if norm(tok) in norm(new_resp):
                continue
            words = tok.split()
            fixed = " ".join(w2 for w2 in
                             (mapping.get(norm(w), w) for w in words) if w2)
            if norm(fixed) in norm(new_resp):
                g[k] = fixed
            else:
                # keep variants that still match; drop this token if another does
                if any(norm(t2) in norm(new_resp) for t2 in g if t2 is not tok):
                    continue
                return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    report = {}
    for lang in DRILLS:
        src, arr, a, b, = load_exercises(lang)
        by_id = {ex["id"]: ex for ex in arr}
        applied = skipped = reverted = 0
        skipped_log = []
        pre_bad = sum(1 for ex in arr if grupos_ok(ex))

        for f in findings_for(lang):
            ex = by_id.get(f.get("id"))
            field, text, fix = f.get("field"), f.get("text"), f.get("fix")
            if not ex or field not in ("respuesta", "contexto", "pista") \
               or not text or not fix or fix == text:
                skipped += 1
                continue
            cur = ex.get(field, "")
            if text not in cur:
                skipped += 1
                skipped_log.append((f.get("id"), field, "text-not-found"))
                continue

            if field == "respuesta":
                if lang == "spanish" and norm(text) != norm(fix):
                    skipped += 1   # rewording — regeneration phase, not mechanical
                    continue
                old = cur
                new = cur.replace(text, fix)
                ex[field] = new
                if grupos_ok(ex) and not repair_grupos(ex, old, new):
                    ex[field] = old   # revert unrepairable
                    reverted += 1
                    skipped_log.append((f.get("id"), field, "grupos-unrepairable"))
                    continue
                applied += 1
            else:
                ex[field] = cur.replace(text, fix)
                applied += 1

        post_bad = sum(1 for ex in arr if grupos_ok(ex))
        report[lang] = dict(applied=applied, skipped=skipped, reverted=reverted,
                            grupos_bad_before=pre_bad, grupos_bad_after=post_bad,
                            examples_skipped=skipped_log[:5])
        if post_bad > pre_bad:
            print(f"!! {lang}: grupos invariant regressed ({pre_bad} -> {post_bad}); NOT saving")
            continue
        save_exercises(lang, src, arr, a, b, args.dry_run)

    for lang, r in report.items():
        print(f"{lang:9s} applied {r['applied']:4d}  skipped {r['skipped']:4d}  "
              f"reverted {r['reverted']:3d}  grupos-bad {r['grupos_bad_before']}->{r['grupos_bad_after']}")
        for e in r["examples_skipped"]:
            print(f"    skip: {e}")


if __name__ == "__main__":
    main()
