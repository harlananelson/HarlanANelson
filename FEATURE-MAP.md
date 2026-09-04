# Maat feature map

Lauren Tan / PStack style: teach an agent **what each feature is, how a user reaches it, how to drive it, and which DOM ids to click**. This is not a heatmap. It is the map you read *before* operating the GUI or reproducing a screenshot.

**Open this file first.** Per-feature YAML lives in `.features/` (same fields, machine-lookup).

Verified against `maat.html` in this repo (shell ~1125 lines). Cold open: **Converse**. Last destination is **not** restored.

| Live URL | File |
|---|---|
| https://harlananelson.com/maat.html | `maat.html` |
| iframe apps | `live-translator.html`, `languages.html`, `assistant.html`, tailnet `:8443` / `:8444` / `:9443` |

---

## How an agent should use this

1. Identify the destination from the screenshot or report (thumb bar labels, or a deep link).
2. Open the **entry URL** below (prefer hash deep links — they survive Add to Home Screen).
3. Click the **selectors** (ids are stable; labels are not).
4. If a private iframe is blank, check Tailscale before debugging the JS.
5. Do **not** guess navigation by reading `maat.html` from scratch — the mode **id** is not the label (`Listen` = `sermon`).

Hands (browser) still required. This map only tells the hands where to go.

---

## Shell (the PWA)

**Purpose.** One installable chrome. Five destinations in the thumb bar + gear. Each destination (except Tools) is an iframe; Tools is a chip bar + stacked iframes.

**Reach.** `https://harlananelson.com/maat.html` (standalone PWA). No service worker — Safari HTTP cache is real; cache-bust query `v=` on iframes.

**Selectors (shell, not inside iframes)**

| Control | id | Notes |
|---|---|---|
| Error banner | `#banner` | Failure-driven only; click to dismiss. Appears after ~8s iframe timeout |
| View stack | `#views` | Contains `#view-sermon`, `#view-practice`, `#view-converse`, `#view-music`, `#view-tools` |
| Thumb bar | `#tabs` | `aria-label="Maat modes"` |
| Listen tab | `#tab-sermon` | Label **Listen**, id **sermon** |
| Practice tab | `#tab-practice` | |
| Converse tab | `#tab-converse` | Default on cold open |
| Music tab | `#tab-music` | Promoted out of Tools |
| Tools tab | `#tab-tools` | Tap = last tool; **long-press** = picker |
| Gear | `#tabs button.gear` | `aria-label="Settings"` — not a destination tab |
| Settings overlay | `#settings` | `.open` when visible |
| Tool picker | `#toolPicker` | `role="dialog"`; `#toolPickerClose` |

**Deep links** (allowlisted; unknown values dropped)

| Intent | URL |
|---|---|
| Listen | `?mode=sermon` or `#listen` (alias → `sermon`) |
| Practice | `#practice` / `#practice?lang=es` |
| Converse type | `#converse` |
| Converse mic | `#converse?input=mic` (default iframe already `mode=mic`) |
| Music | `#music` |
| Tools / reMarkable | `#tools?tool=remarkable` or `#remarkable` |
| Settings | `#about` (opens gear; not a tab) |
| Legacy | `?mode=voice` → Converse+mic; `assistant` → Converse; `languages` → Practice |

**Traps**

- Mode **id** `sermon` is the Listen tab. Searching the DOM for `#tab-listen` finds nothing.
- Cold open is always Converse. Do not expect last-tab restore.
- Practice iframe is sandboxed (`allow-scripts allow-same-origin allow-forms allow-popups allow-downloads`) — it cannot navigate the shell.
- `#tools?tool=music` is rewritten to the **Music** tab, not Tools.
- Empty Settings key fields are a no-op on save (do not clear framed Listen keys). **Clear keys** is the only wipe.
- Native iPad shell is **sketched** in `ios/Maat/` (`webkit.messageHandlers.maatAsr`, Apple on-device Speech / ANE). Not installed until a Mac signs it. Safari PWA still uses `getUserMedia` + Home GPU.

**Related:** `.features/shell.yaml`, `.features/settings.yaml`

---

## Listen

**User name.** Listen. **Internal id.** `sermon`.

**Purpose.** Transcribe / translate / analyze a live room (sermon, meeting, podcast). Writes sessions the `listen-session` skill can read.

**Reach**

1. Maat → thumb **Listen** (`#tab-sermon`).
2. Or `maat.html?mode=sermon`.
3. Iframe `#view-sermon`. Default URL `./live-translator.html?v=26`. If Maat is on the tailnet host with no port, or Settings points Listen at `:8443`, the GPU page is `https://<tailscale-host>:8443/?v=25` (WebSocket same-origin). Native iPad shell (`ios/Maat`) uses Apple on-device ASR (Neural Engine) when `webkit.messageHandlers.maatAsr` is present.

**Needs.** Tailscale + home GPU (`:8443`) for the reliable path. Public `live-translator.html` on Netlify can fail the WebSocket on iPad.

**Inside the iframe (`live-translator.html`)**

| Control | id |
|---|---|
| Start / stop | `#startBtn` (label starts as `● Start listening`) |
| Direction | `#direction` |
| Provider / model | `#provider`, `#model` |
| Speaker profile | `#speakerProfile` |
| Session prefix | `#fileRoot` (file is `prefix-YYYY-MM-DD-HHMM.md`) |
| Home GPU URL | `#homeGpuUrl` |
| Clear / copy / save | `#clearBtn`, `#copyBtn`, `#saveBtn` |
| Keys note when framed | `#maatKeysNote` — “API keys are set in Maat ⚙ Settings.” |

Auth is `postMessage` type `maat-auth` from the shell. Listen posts `maat-listen` with `{session}` so Tools can pass `listen=` to reMarkable.

**Transcript store (not in the GUI):** `~/.config/tesla-bridge/transcripts/<session>-<date>.jsonl`. Use the `listen-session` skill; do not `find -newermt today`. Session **name** is what was typed in `#fileRoot`, not the meeting topic.

**Related:** `.features/listen.yaml`, `listen-session` skill

---

## Practice

**Purpose.** Speech drills. Public. No Tailscale.

**Reach.** `#tab-practice` or `#practice?lang=es|en|ja|sw`. Iframe `#view-practice` → `languages.html`.

**Inside `languages.html`**

| Language | tab id | iframe | drill file |
|---|---|---|---|
| Español | `#tab-es` | `#view-es` | `spanish-speech-drill.html` |
| English | `#tab-en` | `#view-en` | `english-speech-drill.html` |
| 日本語 | `#tab-ja` | `#view-ja` | `japanese-speech-drill.html` |
| Kiswahili | `#tab-sw` | `#view-sw` | `swahili-speech-drill.html` |

Last language: `localStorage.languages_last`. Allowlist only: `es en ja sw`.

**Related:** `.features/practice.yaml`

---

## Converse

**Purpose.** Talk to a model or a workstation shell. Type or speak. Default cold-open destination.

**Reach.** `#tab-converse` or `#converse` / `#converse?input=mic`. Iframe `#view-converse` → `assistant.html?v=88&mode=mic`. Needs Tailscale + tesla-bridge.

**Inside `assistant.html`**

| Control | id |
|---|---|
| Connection dot | `#connDot` |
| Sound | `#soundBtn` |
| Who you talk to | `#targetBtn` (“Talk to…”) |
| Overflow | `#overflowBtn` (“⋯ More”) |
| Status line | `#status` (Tesla browser has no console — errors land here) |
| Transcript | `#transcript` |
| Talk | `#talkBtn` (“Tap to talk”) — hidden if no mic |
| Type | `#barInput`, `#barSend` |
| Pause chip | `#modeChip` |
| Bridge / token / session | `#cfgBridge`, `#cfgToken`, `#cfgSession` (in `#settings`) |

`input=mic` sets `mode=mic` on the iframe URL **without** replacing a Settings host.

**Related:** `.features/converse.yaml`

---

## Music

**Purpose.** Record or upload audio and pick a lens (sound engineering, bass, drums, marimba, choir). Full-rate capture — **not** the 16 kHz speech path.

**Reach.** `#tab-music` or `#music`. Iframe `#view-music` → tailnet `:8444/`. Needs Tailscale.

Old `#tools?tool=music` lands here, not in Tools.

**Related:** `.features/music.yaml`

---

## Tools → reMarkable

**Purpose.** Phone → tablet jobs. Typical: current Listen session → study guide → reMarkable.

**Reach.** `#tab-tools` (opens **last** tool) or long-press Tools → picker. Deep link `#tools?tool=remarkable` / `#remarkable`. Frame `#tool-frame-remarkable` → `:9443/?listen=current&v=17` (`listen` becomes the live stem from Listen’s `maat-listen` message).

**Needs.** Tailscale + phone-bridge. Same workstation token as Converse (`localStorage.tb_token`). Status in `#toolsNote`.

**Inside phone-bridge (`:9443/`)**

| Control | id |
|---|---|
| Settings gear | `#gear-btn` |
| Gold action | `#go-btn` (“Make study guide → tablet”) |
| Preview first | `#preview-first` |
| Source line | `#source-line` |
| Change source | `#src-change` |
| Listen picker | `#listen-select` |
| Destination | `#dest-choose` |
| Advanced | `#adv-toggle` (`✎`) |

OCR on the 3090: Ollama `gemma4:12b-it-q8_0` (`call-gemmi.sh`).

**Related:** `.features/tools-remarkable.yaml`, `~/projects/remarkable/phone-bridge/`

---

## Settings (gear)

**Reach.** Gear button or `#about`. Overlay `#settings`.

| Field | id |
|---|---|
| Workstation token | `#maatToken` |
| Tailscale machine | `#maatBridge` |
| Translation API key | `#maatTranslationKey` |
| Transcription API key | `#maatTranscriptionKey` |
| Show / Clear keys | `#showMaatKeys`, `#clearMaatKeys` |
| Provider / model | `#maatProvider`, `#maatModel` |
| Per-mode URL | `#url-<mode-id>` (`sermon`, `practice`, `converse`, `music`, `remarkable`) |
| Save / Cancel | `#saveModes`, `#closeSettings` |

localStorage keys: `tb_token`, `tb_bridge`, `maat_translation_key`, `maat_transcription_key`, `maat_provider`, `maat_model`, `maat_urls`, `maat.tools.lastTool`.

**Related:** `.features/settings.yaml`

---

## Screenshot → destination cheat sheet

| You see | Go to |
|---|---|
| Thumb bar, gold selected **Converse**, “Tap to talk” | Converse / `assistant.html` |
| “Start listening”, translator settings | Listen / `live-translator.html` or `:8443` |
| Language chips ES/EN/JA/SW | Practice / `languages.html` |
| Music lens / `:8444` | Music tab |
| “Make study guide → tablet” | Tools → reMarkable / `:9443` |
| “Maat” heading, token/Tailscale fields | Gear / `#settings` |
| Red banner “did not load — is Tailscale on” | Environment, not a code bug until Tailscale is up |

---

## What this is not

- Not a visual heatmap or Figma overlay.
- Native iPad shell sketched (`ios/Maat/`, plan: `~/projects/grok/usage/maat-native-ipad-shell-plan.md`). Needs Xcode on a Mac to install.
- Not a substitute for the `listen-session` skill when the question is “what did I just record?”
