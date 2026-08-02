#!/usr/bin/env python3
"""Validate and apply regenerated Spanish exercises (regen-out-*.json).

Every regenerated item must pass a mechanical gate before replacing its
original in spanish-speech-drill.html:

  1. shape: all six fields present, id exists in the drill
  2. grupos invariant: every group has a token appearing verbatim in the
     accent-stripped lowercased respuesta
  3. banned patterns: 'ya yo', 'a nadie' without a preceding negative,
     personal-subject haber ('yo|tú|él|ella|nosotros|ellos... había/hubo/habrá'),
     accent-stripped tell-tales in respuesta (tenia/anos/ninos/jardin as words)
  4. tense form present: some regular OR known conjugated form of the verb
     for the drilled tense appears in the respuesta (via spanish_morph); if
     the verb is irregular/replaced this check is advisory-only (warn).

Items failing 1-3 are rejected (kept as-is in the drill) and logged to
regen-rejects.json for a second pass.

Usage: python apply_regen.py [--dry-run]
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import spanish_morph as morph  # noqa: E402

TENSES = ["presente", "futuro", "condicional", "subjuntivo", "subj_imperfecto",
          "subj_pluscuam", "puntual", "habitual", "fondo", "anterior"]

PRONS = r"(?:yo|tú|tu|él|ella|usted|nosotros|nosotras|vosotros|ellos|ellas|ustedes)"
BANNED = [
    (re.compile(r"\bya yo\b", re.I), "ya-yo order"),
    (re.compile(PRONS + r"\s+(?:había|hubo|habrá|habría|haya|hubiera|habían|hubieron)\s+(?!\w+do\b|\w+to\b|\w+cho\b)", re.I | re.U),
     "personal haber (non-auxiliary)"),
    (re.compile(r"\b(tenia|anos|ninos|jardin|pasabamos|habia)\b"), "stripped accent"),
]
NEG = re.compile(r"\b(no|nunca|jamás|nadie|tampoco|ni)\b.{0,60}\ba nadie\b", re.I)
ANADIE = re.compile(r"\ba nadie\b", re.I)


def sa(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn")


def norm(s):
    return sa((s or "").lower())


def tense_of(ex_id):
    for t in TENSES:
        if f"-{t}-" in ex_id:
            return t
    return None


def grupos_ok(ex):
    resp = norm(ex.get("respuesta", ""))
    return all(any(norm(t) in resp for t in g) for g in ex.get("grupos", []))


def banned_hits(ex):
    r = ex.get("respuesta", "")
    hits = [name for rx, name in BANNED if rx.search(r)]
    if ANADIE.search(r) and not NEG.search(r):
        hits.append("a nadie without negation")
    return hits


def tense_form_warn(ex):
    t = tense_of(ex["id"])
    reg = morph.regular_forms(ex.get("verbo", "").replace("se", "") or "", t) \
        if t else None
    if not reg:
        return False
    resp = norm(ex.get("respuesta", ""))
    return not any(norm(f) in resp for f in reg.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    regen = {}
    for p in sorted(HERE.glob("regen-out-*.json")):
        try:
            for ex in json.loads(p.read_text()):
                regen[ex["id"]] = ex
        except Exception as e:
            print(f"!! unparseable {p.name}: {e}")
    print(f"regenerated items loaded: {len(regen)}")

    src = (SITE / "spanish-speech-drill.html").read_text(encoding="utf-8")
    marker = "const actividades = "
    a = src.index(marker + "[")
    b = src.index("];", a) + 1
    arr = json.loads(src[a + len(marker):b])
    by_id = {ex["id"]: ex for ex in arr}

    applied, rejects, warns = 0, [], 0
    for eid, new in regen.items():
        if eid not in by_id:
            rejects.append({"id": eid, "why": "unknown id"})
            continue
        if not all(k in new and new[k] for k in
                   ("id", "verbo", "contexto", "respuesta", "pista", "grupos")):
            rejects.append({"id": eid, "why": "missing fields"})
            continue
        if not grupos_ok(new):
            rejects.append({"id": eid, "why": "grupos mismatch",
                            "respuesta": new["respuesta"], "grupos": new["grupos"]})
            continue
        hits = banned_hits(new)
        if hits:
            rejects.append({"id": eid, "why": "banned: " + ", ".join(hits),
                            "respuesta": new["respuesta"]})
            continue
        if tense_form_warn(new):
            warns += 1
        by_id[eid].update({k: new[k] for k in
                           ("verbo", "contexto", "respuesta", "pista", "grupos")})
        applied += 1

    (HERE / "regen-rejects.json").write_text(
        json.dumps(rejects, ensure_ascii=False, indent=1))
    print(f"applied {applied}, rejected {len(rejects)}, tense-form warnings {warns}")
    for r in rejects[:8]:
        print("  reject:", r["id"], "—", r["why"])

    if not args.dry_run and applied:
        blob = json.dumps(arr, ensure_ascii=False, indent=2)
        (SITE / "spanish-speech-drill.html").write_text(
            src[:a + len(marker)] + blob + src[b:], encoding="utf-8")
        print("drill updated")


if __name__ == "__main__":
    main()
