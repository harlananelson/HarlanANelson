# Drill exercise phrase review — 2026-08-01

## All four languages at a glance

| Drill | Reviewed | Flagged | Dominant systemic issue |
|---|---|---|---|
| Spanish | 9,100 | 2,555 (28%) | see full analysis below |
| English | 531 | 43 (8%) | sentence-final "usually/always" (×18); "say the truth" for "tell the truth" (×9); stative verbs in continuous/daily frames ("she was being at home", "he knows the answer every day") |
| Japanese | 312 | 264 (85% of transitive items; kana itself flawless) | romaji fuses object+を into one word ("ringoo/pano/shigotoo" → should be "ringo o", "pan o", "shigoto o") in contexto+pista of all 264 transitive exercises |
| Swahili | 495 | 22 (4%) | missing obligatory object marker with definite human objects ("ninasaidia mama" → "ninamsaidia mama"); all other morphology flawless |

English/Japanese/Swahili are each ONE mechanical fix away from clean;
findings live in `findings/{english,japanese,swahili}.json`. The Spanish
set needs the deeper regeneration described below.

# Spanish exercise phrase review — 2026-08-01

Ten Sonnet reviewer agents (one per tense category) read all **9,100**
exercises embedded in `spanish-speech-drill.html` and flagged genuine
problems with spoken-Spanish usage. Full per-item detail (id, field, text,
category, fix, reason) is in `findings/<tense>.json`; the merged catalog is
`all_findings.json`.

## Headline

**3,148 findings across 2,555 distinct exercises (28% of the set).**
By category: gram 1,755 · unnat 642 · ctx 630 · sem 109 · calque 12.
By tense: habitual 905 · anterior 885 · fondo 809 · subjuntivo 158 ·
presente 150 · puntual 100 · condicional 56 · subj_imperfecto 48 ·
futuro 25 · subj_pluscuam 12.

The bulk is NOT 2,555 independently bad sentences — a handful of
**systematic generator bugs** account for most of it:

## Systemic failure patterns

1. **Accent/ñ stripping leaked into display text** (~1,200+ items;
   habitual/fondo/anterior worst). `tenia→tenía, ninos→niños, ano→año,
   jardin→jardín, pasabamos→pasábamos`. The grupos-must-be-accentless rule
   bled into `respuesta`/`contexto`, so the TTS speaks misspelled Spanish
   (and `anos` ≠ `años`).
2. **English `pista` fields** (~520 items in anterior + fondo) — the hint
   is read aloud by the Spanish TTS voice.
3. **Verb-class (valency) errors** — the generator conjugated every verb
   as a plain transitive with a personal subject:
   - impersonal **haber** personalized ("yo había mucho", "yo he terminado…"
     as presente, "que María hubiera más tiempo")
   - dative-experiencer verbs used transitively (**gustar, importar,
     preocupar, ocurrir, suceder, encantar, interesar, bastar, pesar**):
     "ellas gustaran la comida", "tú sucederías lo mismo"
   - reflexive-required **casar** without *se* ("ella casó mucho")
   - defective **soler** given a future ("yo soleré") — the form doesn't exist
   - **tranquilar** is not a Spanish verb (should be *tranquilizar(se)*) —
     it's in the 260-verb list itself, poisoning every tense (42 findings)
4. **Morphology slips**: participle errors ("habíamos **oír**", descubrido,
   suponido), naco→nazco, oíría→oiría, subjunctive-for-indicative in
   presente items, plural agreement ("Las plantas muere").
5. **Template artifacts**: dangling connectors ("Cada vez que, yo admito mi
   error.", "…cuando por fin." — ~110 items), unnatural "**ya yo había**"
   order (~524 items; natural: "yo ya había"), contradictory time markers
   ("en junio mañana"), and semantically absurd sentences ("nosotros
   asesinábamos mucho de niño", wedding-causes-weather counterfactuals,
   "a nadie" without negation).
6. **ctx mismatches** (~630): pista describing the wrong tense, contexto
   whose time expression contradicts the drilled aspect.

## What this means for generation v2

The fix is three-layered (see `../../prompts_v2/_spoken_spanish_preamble.txt`
and `verb_metadata.json`):

1. **Verb metadata, not a bare verb list** — valency class per verb
   (plain / dative-experiencer / reflexive / impersonal / defective), with
   per-class sentence patterns and per-class banned patterns. Remove
   `tranquilar` (replace with `calmar` or `tranquilizarse`).
2. **Prompt preamble** enforcing spoken-Spanish naturalness: full accents/ñ
   everywhere EXCEPT inside `grupos`; pista always in Spanish; complete
   clauses only; natural clitic/adverb order; negative-polarity rule;
   semantic plausibility ("would a person actually say this?").
3. **Mechanical validation before merge** (extend `validate_exercises.py`):
   - conjugation check against `spanish_morph.py` (+ participle table)
   - accent-integrity check on respuesta/contexto/pista (reject if a known
     accented form appears stripped)
   - banned-pattern lint: `ya yo`, `a nadie` without `no/nunca`, personal
     subject + haber, subject-conjugated gustar-class, dangling connectors
     (`cada vez que,`, terminal `mientras.`/`cuando por fin.`)
   - Spanish-language check on pista
   - LLM self-review pass: generated batch → reviewer model → only
     accepted items merged (same rubric as this review).

## Cost note

Review run: 10 Sonnet agents, ~1.4M tokens total, a few minutes wall-clock.
The same harness can re-certify any regenerated batch.
