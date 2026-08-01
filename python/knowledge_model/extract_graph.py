#!/usr/bin/env python3
"""Extract the Spanish drill's domain knowledge graph.

Parses the 9,100 exercises embedded in spanish-speech-drill.html and builds
a prerequisite graph over three node types:

  lemma:<verb>          knowing the verb's meaning (vocabulary)
  rule:<family>:<tense> the regular conjugation rule (e.g. rule:ar:puntual)
  cell:<verb>:<tense>   producing this verb in this tense (the drilled skill)

Edges (prerequisite -> dependent):
  lemma:<v>            -> cell:<v>:<t>      (must know the word)
  rule:<f>:<t>         -> cell:<v>:<t>      (regular cells only — transfer)
  cell:<v>:<t_pre>     -> cell:<v>:<t>      (tense progression, same verb)

Whether a cell is regular is INFERRED: every exercise's expected answer is
compared against a regular conjugator (spanish_morph.py). If any observed
person-form differs from the regular generation, the cell is irregular and
does not share the family rule node.

Usage:
  python extract_graph.py [--html ../../spanish-speech-drill.html] [--out graph.json]
"""

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import spanish_morph as morph

ALL_TENSES = ["presente", "futuro", "condicional", "subjuntivo",
              "subj_imperfecto", "subj_pluscuam", "puntual", "habitual",
              "fondo", "anterior"]

# Tense progression prerequisites (pedagogical order encoded in the drill's
# own curriculum: indicative present first, then pasts, then compound pasts,
# then subjunctive chain).
TENSE_PREREQS = {
    "presente": [],
    "puntual": ["presente"],
    "habitual": ["presente"],
    "fondo": ["habitual"],
    "futuro": ["presente"],
    "condicional": ["futuro"],
    "anterior": ["puntual", "habitual"],
    "subjuntivo": ["presente"],
    "subj_imperfecto": ["subjuntivo", "puntual"],
    "subj_pluscuam": ["subj_imperfecto", "anterior"],
}


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def load_exercises(html_path):
    src = Path(html_path).read_text(encoding="utf-8")
    i = src.index("const actividades = [")
    j = src.index("];", i)
    return json.loads(src[i + len("const actividades = "):j + 1])


def tense_of(ex_id):
    for t in ALL_TENSES:
        if f"-{t}-" in ex_id:
            return t
    return None


PRON_STRIPPED = {strip_accents(p): per for p, per in morph.PRONOUNS.items()}
# unambiguous when scanned inside the accented respuesta text
PRON_IN_TEXT = {p: per for p, per in morph.PRONOUNS.items()
                if p not in ("el", "tu", "uno", "vos")}


def person_of(exercise):
    """Infer grammatical person: a lone-pronoun group, else scan respuesta."""
    for g in exercise.get("grupos") or []:
        joined = strip_accents(" ".join(g).strip().lower())
        if joined in PRON_STRIPPED:
            return PRON_STRIPPED[joined]
    resp = " " + (exercise.get("respuesta") or "").lower() + " "
    best = None
    for pron, per in PRON_IN_TEXT.items():
        k = resp.find(" " + pron + " ")
        if k >= 0 and (best is None or k < best[0]):
            best = (k, per)
    return best[1] if best else None


def form_candidates(exercise):
    """Candidate verb-form strings: each group, each group token (variant
    lists like ['abandonara','abandonase']), and adjacent-group joins (for
    compound tenses whose aux and participle sit in separate groups)."""
    groups = [[t.strip().lower() for t in g] for g in (exercise.get("grupos") or [])]
    cand = set()
    joined = [" ".join(g) for g in groups]
    for g in groups:
        cand.update(g)
    cand.update(joined)
    for a, b in zip(joined, joined[1:]):
        cand.add(a + " " + b)
        # variant aux group followed by participle: pair each token with next
    for g, nxt in zip(groups, joined[1:]):
        for tok in g:
            cand.add(tok + " " + nxt)
    return {strip_accents(c) for c in cand if c}


def classify_cells(exercises):
    """For each (verb, tense): compare observed forms vs regular conjugation."""
    obs = defaultdict(list)      # (verb, tense) -> [(person, candidates, ex_id)]
    for ex in exercises:
        t = tense_of(ex["id"])
        v = ex.get("verbo")
        if not t or not v:
            continue
        obs[(v, t)].append((person_of(ex), form_candidates(ex), ex["id"]))

    cells = {}
    for (v, t), rows in obs.items():
        reg = morph.regular_forms(v, t)
        matches, mismatches, unchecked = 0, [], 0
        for p, cands, exid in rows:
            if not cands or not reg:
                unchecked += 1
                continue
            # Regularity test: does ANY regular person-form appear in the
            # answer? Person attribution is irrelevant here (and unreliable
            # for dative gustar-type constructions); it matters only later,
            # in the per-person estimator. Accent-insensitive because the
            # grupos chunks are accent-stripped — real irregulars differ in
            # the letters, not the accents.
            expects = {strip_accents(f.lower()) for f in reg.values()}
            if any(e == c or
                   re.search(r"(?:^|\s)" + re.escape(e) + r"(?:\s|$)", c)
                   for e in expects for c in cands):
                matches += 1
            else:
                mismatches.append((p, sorted(cands, key=len)[-1],
                                   strip_accents(reg.get(p or "3s", "?").lower()), exid))
        cells[(v, t)] = {
            "n_exercises": len(rows),
            "checked": matches + len(mismatches),
            "matches": matches,
            "mismatches": mismatches[:6],
            "n_mismatch": len(mismatches),
            "regular": bool(matches + len(mismatches)) and not mismatches,
        }
    return cells


def build_graph(cells):
    nodes, edges = {}, []
    verbs = sorted({v for v, _ in cells})
    tenses_present = sorted({t for _, t in cells}, key=ALL_TENSES.index)

    for v in verbs:
        nodes[f"lemma:{v}"] = {"type": "lemma", "verb": v}
    for t in tenses_present:
        for fam in ("ar", "er", "ir"):
            nodes[f"rule:{fam}:{t}"] = {"type": "rule", "family": fam, "tense": t}

    for (v, t), info in cells.items():
        nid = f"cell:{v}:{t}"
        fam = morph.family(v)
        nodes[nid] = {
            "type": "cell", "verb": v, "tense": t, "family": fam,
            "regular": info["regular"], "n_exercises": info["n_exercises"],
        }
        edges.append([f"lemma:{v}", nid])
        if info["regular"] and fam:
            edges.append([f"rule:{fam}:{t}", nid])
        for pre in TENSE_PREREQS.get(t, []):
            if (v, pre) in cells:
                edges.append([f"cell:{v}:{pre}", nid])

    # drop rule nodes with no dependents
    used = {a for a, _ in edges}
    for nid in [n for n, d in nodes.items() if d["type"] == "rule" and n not in used]:
        del nodes[nid]
    return {"nodes": nodes, "edges": edges}


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).parent
    ap.add_argument("--html", default=str(here / "../../spanish-speech-drill.html"))
    ap.add_argument("--out", default=str(here / "graph.json"))
    args = ap.parse_args()

    exercises = load_exercises(args.html)
    cells = classify_cells(exercises)
    graph = build_graph(cells)

    n_reg = sum(1 for d in graph["nodes"].values()
                if d["type"] == "cell" and d["regular"])
    n_cell = sum(1 for d in graph["nodes"].values() if d["type"] == "cell")
    Path(args.out).write_text(json.dumps(graph, ensure_ascii=False, indent=1))
    print(f"exercises: {len(exercises)}")
    print(f"nodes: {len(graph['nodes'])}  edges: {len(graph['edges'])}")
    print(f"cells: {n_cell}  regular: {n_reg}  irregular: {n_cell - n_reg}")

    # sanity: famously irregular verbs should be irregular in the preterite
    for v in ("ser", "ir", "estar", "tener", "hacer", "hablar", "comer"):
        c = cells.get((v, "puntual"))
        if c:
            print(f"  puntual {v}: regular={c['regular']} "
                  f"(checked {c['checked']}, mism {c['n_mismatch']})"
                  + (f" e.g. {c['mismatches'][0][:3]}" if c["mismatches"] else ""))


if __name__ == "__main__":
    main()
