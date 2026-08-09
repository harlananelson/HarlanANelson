# The second column: from translation to the help lane

Design for the next step of the Listen tab (formerly Interpret). Written
2026-08-09, to be built after Sunday's service so today's transcripts can serve
as test material.

---

## 1. The idea in one line

The second column is not the *translation* column — it is the **help-me-follow**
column. Translation is only what "help" means when the source is a language you
do not speak. When the source is your own language, help means **context**: what
that name referred to, and above all **what has changed since it was last said**.

Which makes the column profile-defined, exactly like the analysis lens:

| Profile | Column 1 | Column 2 | Latency | Density |
|---|---|---|---|---|
| jean-petit, bible-study, medical, immigration, criminal-defense | source speech | target language | must keep pace | every line |
| **meeting (new)** | source speech | **annotations** | may trail 60–120s | **sparse — most lines empty** |

An empty cell in meeting mode is not a gap. It is the honest signal that nothing
needed saying, and it is the common case.

---

## 2. What "fact check" means here — and what it does not

It does **not** mean the internet's version: adjudicating public truth, rating
claims, or appending opinion in the voice of authority. The system has no
standing to do that and a local model attempting it will invent confidently —
the same failure that turned a garbled line into fluent nonsense during QC.

It means **tracking what the room committed to, and flagging when it moves.**

Worth flagging:

- **A deliverable changes.** "Sarah is writing the migration script" → later
  "Tom will do the migration."
- **A date moves.** "We ship the 14th" → later "end of the month".
- **A requirement changes.** "It must run on the cluster" → later "local is
  fine for now".
- **A number changes.** A count, a budget, a threshold, a sample size.
- **An owner changes**, or a task quietly acquires no owner at all.
- **A question was asked and never answered** — tracked, and raised at the end.
- **A decision is revisited** that was already settled earlier in the same
  session.

Never flagged:

- Whether a claim about the world is *true*.
- Whether a decision was *wise*.
- Anything requiring knowledge from outside the transcript, unless the profile
  explicitly enables external checking (§6) — and even then, phrased as a
  question, never as a verdict.

The test for whether an annotation belongs: **can it cite two moments in this
transcript?** If not, it is an opinion wearing a fact's clothes.

---

## 3. The architecture that makes it safe

**The model extracts; the code compares.**

This is the load-bearing decision. Asking an LLM "has anything changed?" is an
open-ended judgement, which is where invention lives. Instead:

1. **Extract (LLM, narrow task).** For each batch of trailing lines, pull any
   commitments into a fixed shape. Nothing else is asked of it.

   ```json
   {"kind": "date|deliverable|requirement|owner|number|question|decision",
    "subject": "migration script",
    "value": "September 14",
    "line": 412}
   ```

2. **Compare (plain code, deterministic).** Hold a **ledger** of commitments for
   the session, keyed by `kind` + normalised `subject`. A new extraction whose
   value differs from the stored one *is* a change — no judgement involved. The
   diff is arithmetic, not opinion.

3. **Emit (grounded).** The annotation must carry **both line ids** and quote
   both statements verbatim from the transcript. An annotation that cannot cite
   its earlier line is dropped before it reaches the screen — the same shape as
   the QC similarity gate: a deterministic guard that holds regardless of which
   model is behind it.

The ledger is also the reason this gets *better* over a long meeting rather than
noisier: it is accumulating state, not re-reading everything each pass.

---

## 4. What the user sees

Aligned to the line that triggered it, in the second column:

```
10:42  We'll have the migration script by the 14th.
                                 ⚠ CHANGED — at 09:58 this was "end of August"
                                   ("the migration lands end of August")

10:44  Tom, can you own the rollback plan?
                                 (nothing — no change, no note)

10:51  What's our fallback if the cluster is down?
                                 ? OPEN — asked at 10:51, not yet answered
```

Markers, deliberately few:

- **⚠ CHANGED** — a tracked commitment now differs. Both versions shown.
- **↩ REFERS TO** — an acronym or name defined earlier in this session.
- **? OPEN** — a question asked and not answered (resolved silently if answered
  later; surfaced in the summary if never).

No marker for agreement, no marker for "verified". Silence means nothing needed
saying.

---

## 5. Artifacts

Beyond the live column, a meeting produces two things worth keeping:

- **`<session>-<date>.txt`** — as today, with annotations saved as `[note]`
  lines so they interleave with the speech.
- **`<session>-ledger-<date>.json`** — the commitment ledger: every deliverable,
  date, owner and requirement with its history of changes and the line ids. This
  is the artifact a meeting actually owes you, and it is a by-product of the
  column rather than extra work.

The Analyze lens for the meeting profile then reads the ledger rather than
re-deriving it: decisions made, commitments with their current value, what
changed during the meeting, questions never answered.

---

## 6. Model choice, and the one place external checking is allowed

Extraction is narrow and local gemma is adequate for it. Annotation *phrasing*
is also fine locally.

External checking — "is this figure plausible", "does this contradict something
outside the room" — is off by default and, where a profile enables it, must:

- be routed to a stronger model (the profile names it, as the assistant already
  does for its backends),
- be phrased as a question, never a verdict,
- be visually distinct from internal CHANGED annotations, which are grounded.

The internal/external line is the same one that separates this from internet
fact-checking, and it should stay visible in the UI, not just in the code.

---

## 7. Build order

Each step ships working, per the transition-matrix approach:

1. **Move Meeting into Listen** as a monolingual profile: no translation,
   column 2 empty. Pure relocation — proves the tab boundary before adding
   anything.
2. **Ledger extraction + storage**, no UI. Run it over today's real transcripts
   and read the ledger by hand. This is where the extraction prompt gets tuned,
   with no risk to a live session.
3. **CHANGED annotations** in column 2, with the two-citation guard. The most
   valuable marker, and the safest.
4. **OPEN questions**, which need the resolve-when-answered logic.
5. **REFERS TO**, lowest value, easiest to get noisy — do it last and be willing
   to drop it.
6. **Analyze reads the ledger.**

Step 2 is where the real risk lives, and it is deliberately placed where it can
be evaluated offline against transcripts we already have.

---

## 8. Open questions for the owner

- ~~Should the meeting profile default to no saved audio?~~ **Decided
  2026-08-09: yes, text-only.** Meetings are more sensitive than sermons and
  the room has not consented to being recorded merely because one participant
  wanted a transcript. Consequences to build with:
  * the profile carries `save_audio: false`, and `save_line` skips the clip;
  * **the large-v3 refine tier cannot run** on a meeting — there is no audio to
    re-read. Rolling QC still works (it reasons over text), but the acoustic
    second pass is gone, so the first pass is the only hearing. That is the
    price of the privacy posture and it should be stated in the UI, not
    discovered later when a refined file never appears;
  * **diarization cannot run either** — speaker labelling embeds the audio.
    Meeting mode therefore has no speaker attribution unless the manual
    🗣/📻 tag is used;
  * the audio directory should not be created at all for these sessions, so
    "no audio" is visible on disk rather than a claim.
- Should CHANGED annotations be **spoken** in a driving context, or is this a
  screen-only feature? (Leaning screen-only: interrupting to say "that date
  moved" during a live meeting is worse than useless.)
- Is a monolingual **English** meeting the primary case, or should the profile
  handle a monolingual Spanish meeting equally? The pipeline is language-blind;
  only the prompts assume.
