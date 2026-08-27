# Maat API keys in Settings — task notes

Worktree branch: `grok-task/maat-keys-20260827-084633`

## Worktree was behind the code the task describes

This worktree was created from `bb29caf` (PR #71), 52 commits behind `origin/main`. The
task’s line numbers (`pushAuthToFrames` ~280, `saveModes` ~809, Listen `maat-auth`
~1310, `STORE_KEY` ~769) match **current main**, which already has
`getWorkstationToken` / `getTailscaleHost`, the `maat-auth` channel, and Listen on
the tailnet `:8443` origin.

Without that channel the requested payload extension cannot land as a small
patch. The first commit on this branch copies `maat.html` and
`live-translator.html` from `origin/main`. All key-ownership edits sit on top of
that. `git diff origin/main -- maat.html live-translator.html` is the feature.

`maat/listen-setup-in-gear` is a different (same-origin `liveTranslator.v2`)
approach and was not used. Listen is cross-origin from Maat, so keys have to
travel on `maat-auth`.

## Listen provider / model vs Maat gear

Listen’s own settings: `<select>` `anthropic` | `openai`, plus a model `<select>`
with suggestions and a Custom… text field. Defaults:

- provider `anthropic`
- models `{ anthropic: 'claude-haiku-4-5-20251001', openai: 'gpt-5-mini' }`

Maat gear follows the task’s “if in doubt”: the same two-option `<select>` and a
free-text model input. Placeholders match Listen’s defaults; stored `maat_model`
may be empty until the user types one.

An **empty** `model` in `maat-auth` does **not** overwrite Listen’s model. Only a
non-empty string is applied (via `state.models[state.provider]`, same slot as
Listen’s model control). Provider is always sent (`anthropic` if unset).

## Frame target origin

`pushAuthToFrames` no longer posts to `"*"`. Origin is `new URL(src, location.href).origin`
from `getAttribute("src")`, then `iframe.src`, then `dataset.src`. Non-http(s)
(`about:blank`, missing src) → skip that frame.

Relative URLs (`./assistant.html`, `./languages.html`) resolve to Maat’s origin.
Listen’s default `https://…ts.net:8443/?v=22` resolves to that host **including
port 8443**. Lazy frames with no src yet are skipped; they get a push on `load`
and via `maat-auth-please`.

The previous `if (!token && !bridge) return` was dropped. `bridge` already
fell back to `DEFAULT_TS_HOST`, so that return was dead; with keys in the
payload, Clear keys must still push empty strings.

## Empty keys vs the shared OpenAI slot

Listen stores translation keys as `state.apiKeys[provider]` and cloud
transcription as `state.apiKeys.openai`. When provider is `openai` those are
the same slot.

Apply order: empty-string **clears** first, then non-empty **sets**. A filled
OpenAI translation key is not wiped by a blank transcription field. Both empty
(Clear keys) still clears both slots. A non-empty `transcriptionKey` still
writes `state.apiKeys.openai`.

Maat always includes the four new fields (possibly empty). A framed Listen
session that receives empty keys will `saveState()` that emptiness into
`liveTranslator.v2` on the **Listen origin**. Standalone Listen at the same
tailnet URL shares that store, so opening Maat with no keys configured will
clear keys previously entered on standalone Listen at `:8443`. Standalone
Listen with **no** `maat-auth` message is unchanged.

## Framed vs standalone UI

`var framed = window.parent !== window` once, in try/catch (throw → framed).

Framed: hide `#apiKey` (its field), `#showKey`, and `#openaiKey` (its field);
show `#maatKeysNote` (“API keys are set in Maat ⚙ Settings.”). `#keyHint` still
runs; with no key it points at ⚙. Provider, model, Check key, and the existing
localStorage security callout stay. `hasKey()` / `checkBtn` gating are
untouched; they still read `state.apiKeys`.

Standalone: those hides never run. Key inputs, save path, and `state.apiKeys`
behave as before.

Framed start-hint copy (not gating) also points at ⚙ so it does not tell the
user to type “above” into a hidden field.
