# Knowledge model prototype — Spanish drill

A graph-theoretic model of (a) what the drill teaches and (b) what the
learner knows, plus a recommender that targets the transition between them.
Theory: Knowledge Space Theory's outer fringe (Doignon & Falmagne) with a
Bayesian Knowledge Tracing student model and exponential forgetting.

## Files

| File | Role |
|---|---|
| `spanish_morph.py` | Regular conjugator for the drill's 10 tense categories |
| `extract_graph.py` | Parses the 9,100 exercises out of `spanish-speech-drill.html`, infers each (verb, tense) cell's regularity by comparing expected answers against the regular conjugator, emits `graph.json` |
| `estimator.py` | BKT mastery over cells + transfer through rule/lemma nodes + forgetting; prints per-tense mastery and the ranked frontier |
| `pull_tracking.py` | Downloads tracked drill sessions from Netlify Blobs (`drill-tracking` store) to `data/tracking.jsonl` |

## Graph structure

- `lemma:<verb>` — vocabulary knowledge (260 verbs)
- `rule:<family>:<tense>` — a regular conjugation rule (e.g. `rule:ar:puntual`);
  evidence on any member cell transfers to all others via this node
- `cell:<verb>:<tense>` — the drilled skill (2,624 cells)
- Edges: lemma→cell, rule→cell (regular cells only), and tense-progression
  cell→cell (presente → pasts/futuro/subjuntivo → compounds).

Regularity is **inferred, not authored**: a cell is regular iff every
exercise answer matches the regular conjugator (accent-insensitive; any
person). Validation: the inferred futuro irregulars are exactly the
textbook set (decir, hacer, poder, poner, querer, saber, salir, tener,
valer, venir, haber + tener-compounds) and the imperfecto irregulars are
exactly ir/ser/ver.

## Usage

```bash
python extract_graph.py            # -> graph.json (rerun when exercises change)
python pull_tracking.py            # -> data/tracking.jsonl from Netlify Blobs
python estimator.py                # mastery + frontier from real sessions
python estimator.py --demo         # synthetic learner, end-to-end check
```

Requires tracked sessions: turn the drill's 📊 Tracking pill ON while
practicing. The estimator scores `feedback` events ("Correcto." vs "Revisa
esta idea.") against the exercise snapshot (verb + tense).

## Knobs / next steps

- BKT params (`P_L0`, `P_T`, slip/guess) and `HALF_LIFE_DAYS` are priors,
  not fits — fit them once a few hundred real attempts accumulate.
- Person-level cells (verb × tense × person) are a straightforward
  refinement; the extractor already infers person where a subject pronoun
  is present.
- The frontier score (mastery gap × unblock count × urgency) is the greedy
  policy; wiring it back into the drill's scheduler replaces the current
  SRS queue.
