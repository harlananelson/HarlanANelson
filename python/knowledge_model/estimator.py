#!/usr/bin/env python3
"""Mastery estimator + frontier recommender over the drill knowledge graph.

Student model: mastery m_i in [0,1] for every graph node.
  - cell nodes updated by Bayesian Knowledge Tracing from drill attempts
  - rule nodes = shrunken average of their observed member cells (transfer:
    evidence about hablé raises the prior for canté)
  - lemma nodes = shrunken accuracy across the verb's observed cells
  - unseen cells get a model-based prior from their rule + lemma parents
  - exponential forgetting decays observed mastery toward the prior

Frontier (Knowledge Space Theory "outer fringe"): unmastered cells whose
prerequisites are satisfied, ranked by how much downstream skill each one
unblocks and how urgent (decayed) it is.

Input: tracking JSONL produced by pull_tracking.py (one JSON object per
line: the stored blob batches). Falls back to --demo (synthetic session).

Usage:
  python estimator.py --data data/tracking.jsonl
  python estimator.py --demo
"""

import argparse
import json
import math
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

# BKT parameters (sensible defaults; fit later when data accumulates)
P_L0 = 0.30      # baseline prior mastery
P_T = 0.15       # learning transit per attempt
P_SLIP = 0.10
P_GUESS = 0.15
HALF_LIFE_DAYS = 7.0
TAU_MASTERED = 0.85
TAU_PREREQ = 0.60
SHRINK = 3.0     # pseudo-observations pulling small-sample averages to prior

TENSE_NAMES_INV = {
    "presente": "presente", "futuro": "futuro", "condicional": "condicional",
    "subjuntivo": "subjuntivo", "subj. imperf.": "subj_imperfecto",
    "subj. plusc.": "subj_pluscuam", "puntual": "puntual",
    "habitual": "habitual", "fondo": "fondo", "anterior": "anterior",
}


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def load_graph(path):
    g = json.loads(Path(path).read_text())
    parents = defaultdict(list)
    children = defaultdict(list)
    for a, b in g["edges"]:
        parents[b].append(a)
        children[a].append(b)
    return g["nodes"], parents, children


# ── observations from tracking data ─────────────────────────────────────────

def parse_tracking(jsonl_path):
    """Yield (ts_ms, verb, tense, correct) from tracked feedback events."""
    out = []
    for line in Path(jsonl_path).read_text().splitlines():
        if not line.strip():
            continue
        batch = json.loads(line)
        base_ts = time.mktime(time.strptime(
            batch.get("received", "1970-01-01T00:00:00")[:19], "%Y-%m-%dT%H:%M:%S"))
        for ev in batch.get("events", []):
            if ev.get("type") != "feedback":
                continue
            text = (ev.get("data") or {}).get("text", "")
            ex = (ev.get("data") or {}).get("ex") or {}
            low = strip_accents(text.lower())
            if low.startswith("correcto"):
                correct = True
            elif low.startswith("revisa esta idea"):
                correct = False
            else:
                continue  # status messages, mic errors, etc.
            verb = (ex.get("verb") or "").split(" ")[0].strip().lower()
            tense = TENSE_NAMES_INV.get((ex.get("tense") or "").strip().lower())
            if verb and tense:
                out.append((base_ts * 1000 + ev.get("t", 0), verb, tense, correct))
    out.sort()
    return out


# ── the estimator ───────────────────────────────────────────────────────────

def bkt_update(p, correct):
    if correct:
        num = p * (1 - P_SLIP)
        den = num + (1 - p) * P_GUESS
    else:
        num = p * P_SLIP
        den = num + (1 - p) * (1 - P_GUESS)
    post = num / den if den > 0 else p
    return post + (1 - post) * P_T


def estimate(nodes, parents, observations, now_ms=None):
    """Return mastery dict node_id -> [0,1]."""
    now_ms = now_ms or (time.time() * 1000)

    # 1. BKT over observed cells
    obs_p = {}          # cell -> posterior
    last_ts = {}
    hits = defaultdict(lambda: [0, 0])   # verb -> [correct, total] for lemmas
    for ts, verb, tense, correct in observations:
        nid = f"cell:{verb}:{tense}"
        if nid not in nodes:
            continue
        obs_p[nid] = bkt_update(obs_p.get(nid, P_L0), correct)
        last_ts[nid] = ts
        hits[verb][0] += 1 if correct else 0
        hits[verb][1] += 1

    # 2. rule + lemma mastery from their observed members
    rule_m, lemma_m = {}, {}
    members = defaultdict(list)
    for nid, p in obs_p.items():
        for par in parents.get(nid, []):
            members[par].append(p)
    for nid, d in nodes.items():
        if d["type"] == "rule":
            xs = members.get(nid, [])
            rule_m[nid] = ((sum(xs) + P_L0 * SHRINK) / (len(xs) + SHRINK))
        elif d["type"] == "lemma":
            c, n = hits.get(d["verb"], [0, 0])
            lemma_m[nid] = (c + P_L0 * SHRINK) / (n + SHRINK)

    # 3. priors for every cell from parents; forgetting decay for observed
    mastery = {}
    mastery.update(rule_m)
    mastery.update(lemma_m)
    for nid, d in nodes.items():
        if d["type"] != "cell":
            continue
        rule_par = [p for p in parents.get(nid, []) if p.startswith("rule:")]
        lemma_par = [p for p in parents.get(nid, []) if p.startswith("lemma:")]
        prior = P_L0
        if rule_par:                       # regular cell: rule transfer
            prior = 0.55 * rule_m.get(rule_par[0], P_L0) + 0.45 * P_L0
        if lemma_par:
            prior = 0.75 * prior + 0.25 * lemma_m.get(lemma_par[0], P_L0)
        if nid in obs_p:
            age_days = max(0.0, (now_ms - last_ts[nid]) / 86_400_000)
            w = 0.5 ** (age_days / HALF_LIFE_DAYS)
            mastery[nid] = w * obs_p[nid] + (1 - w) * prior
        else:
            mastery[nid] = prior
    return mastery


def frontier(nodes, parents, children, mastery, top=15):
    """Outer fringe: unmastered cells whose cell-prerequisites are satisfied,
    ranked by unblocking power + urgency."""
    recs = []
    for nid, d in nodes.items():
        if d["type"] != "cell" or mastery[nid] >= TAU_MASTERED:
            continue
        prereqs = [p for p in parents.get(nid, []) if p.startswith("cell:")]
        if any(mastery[p] < TAU_PREREQ for p in prereqs):
            continue
        unblocks = sum(1 for c in children.get(nid, [])
                       if c.startswith("cell:") and mastery[c] < TAU_MASTERED)
        gap = TAU_MASTERED - mastery[nid]
        score = gap * (1 + unblocks)
        recs.append((score, nid, mastery[nid], unblocks, d))
    recs.sort(reverse=True)
    return recs[:top]


def summarize(nodes, mastery):
    by_t = defaultdict(list)
    for nid, d in nodes.items():
        if d["type"] == "cell":
            by_t[d["tense"]].append(mastery[nid])
    order = ["presente", "puntual", "habitual", "fondo", "futuro", "condicional",
             "subjuntivo", "subj_imperfecto", "anterior", "subj_pluscuam"]
    for t in order:
        xs = by_t.get(t, [])
        if xs:
            print(f"  {t:16s} mean mastery {sum(xs)/len(xs):.2f}   "
                  f"mastered {sum(1 for x in xs if x >= TAU_MASTERED):3d}/{len(xs)}")


def demo_observations(nodes):
    """Synthetic learner: solid regular presente, shaky irregular preterite,
    untouched subjunctive — to exercise the machinery end to end."""
    import random
    rng = random.Random(11)
    obs, now = [], time.time() * 1000
    cells = [(d["verb"], d["tense"], d["regular"]) for d in nodes.values()
             if d["type"] == "cell"]
    for verb, tense, regular in cells:
        if tense == "presente" and rng.random() < 0.5:
            for k in range(3):
                p_ok = 0.92 if regular else 0.75
                obs.append((now - 86.4e6 * rng.uniform(1, 10),
                            verb, tense, rng.random() < p_ok))
        elif tense == "puntual" and rng.random() < 0.3:
            for k in range(2):
                p_ok = 0.85 if regular else 0.45
                obs.append((now - 86.4e6 * rng.uniform(0, 5),
                            verb, tense, rng.random() < p_ok))
    obs.sort()
    return obs


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).parent
    ap.add_argument("--graph", default=str(here / "graph.json"))
    ap.add_argument("--data", default=str(here / "data/tracking.jsonl"))
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    nodes, parents, children = load_graph(args.graph)

    if args.demo:
        observations = demo_observations(nodes)
        print(f"[demo] synthetic observations: {len(observations)}")
    else:
        p = Path(args.data)
        if not p.exists():
            raise SystemExit(f"No tracking data at {p} — run pull_tracking.py "
                             f"first, or use --demo.")
        observations = parse_tracking(p)
        print(f"observations parsed from tracking: {len(observations)}")
        if not observations:
            raise SystemExit("Tracking data contained no scoreable feedback "
                             "events — drill with 📊 Tracking on first.")

    mastery = estimate(nodes, parents, observations)

    print("\nMastery by tense:")
    summarize(nodes, mastery)

    print(f"\nFrontier — what to teach next (top {args.top}):")
    for score, nid, m, unblocks, d in frontier(nodes, parents, children, mastery, args.top):
        tag = "regular" if d["regular"] else "IRREGULAR"
        print(f"  {d['verb']:14s} {d['tense']:16s} {tag:9s} "
              f"mastery {m:.2f}  unblocks {unblocks}  score {score:.2f}")


if __name__ == "__main__":
    main()
