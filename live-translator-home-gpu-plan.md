# Live Translator — Home-GPU Engine Plan

> Status: planned 2026-06-10. Owner: Harlan. Implements the multi-engine
> upgrade discussed after the RTX 3090 install. The app this extends is
> `live-translator.html` (deployed at harlananelson.com/live-translator.html);
> the quality standard and gold corpus live in the private `biblestudy` repo
> (`defe/translation-app-handoff.md`); the on-device fine-tuning track lives in
> `sermon-translator/`.

## Goal

Live Spanish→English transcription + translation of sermons, fast, on an iPad
in church — with the heavy models running at home on the RTX 3090 (24 GB),
reached privately over Tailscale. Cloud and in-browser engines remain as
fallbacks.

## Engine lineup (after this plan)

| Engine | ASR | Translation | When to use |
|---|---|---|---|
| **Home GPU** (new) | faster-whisper **large-v3**, streaming, on the 3090 | Local LLM (8–12B, quantized) with rolling context | Primary — best quality, no per-token cost |
| Cloud | OpenAI `gpt-4o-transcribe` | Anthropic/OpenAI per segment | Fallback when the home box is unreachable |
| On-device | transformers.js Whisper (tiny/small); later the fine-tuned WhisperKit model from `sermon-translator/` | Cloud LLM | Offline / no-network fallback |

## Architecture (Home GPU engine)

```
iPad mic (live-translator.html)
  → 16 kHz mono Opus chunks over WebSocket
  → wss://<machine>.<tailnet>.ts.net  (Tailscale; TLS via `tailscale serve`)
  → server: VAD + streaming faster-whisper large-v3  → Spanish sentences
  → translation worker: local LLM, rolling ~5-sentence context (R1–R3 below)
  → ES + EN caption events back over the same WebSocket
  → app renders panes + exports <root>-YYYYMMDD-HHMM.md (root now configurable)
```

Notes:

- **TLS / mixed content**: harlananelson.com is HTTPS, so the page cannot open
  `ws://`. `tailscale serve` fronts the local service with a valid cert on the
  tailnet hostname → connect via `wss://`. iPad needs the Tailscale app
  connected. No port forwarding; the GPU box is never publicly exposed.
- **Bandwidth**: ~24 kbps Opus — works on church Wi-Fi or cellular.
- **VRAM budget**: large-v3 ≈ 4–5 GB (fp16/int8) + 8–12B LLM quantized ≈
  6–10 GB. Comfortable on 24 GB.
- **Availability**: the workstation must be on Sunday mornings — leave on, or
  Wake-on-LAN over Tailscale before service.

## Translation contract (from biblestudy `translation-app-handoff.md` — binding)

- **R1 — sentence granularity**: reflow ASR segments into sentences before
  translating; keep timestamp offsets for mapping back.
- **R2 — rolling context**: translate each sentence with the preceding ~3–10
  sentences visible as read-only context.
- **R3 — never emit meta-text**: output is a translation or exactly
  `[inaudible]` / `[unclear audio]`. Short max_tokens; validate every output
  and reject refusal-shaped lines. (The old app leaked 18 chat-style refusals
  into one transcript — hard failure, top priority.)

## Build order (eval-first — the gold corpus is the rubric)

1. **ASR bake-off on the 3090.** Batch faster-whisper large-v3 over the
   May 17 Iglesia de Fe service audio; WER vs the gold Spanish
   (`biblestudy/defe/sermon.bilingual.tsv`, 2,038 sentences). Retests the
   "YouTube es-orig beats Whisper" verdict (made on a 6 GB 2060, ≤ medium).
   Side product: the large-v3 labels `sermon-translator/`'s distillation
   notebook wanted from Colab — Colab no longer required.
2. **Translation server.** Local LLM bake-off (e.g., Qwen2.5-7B/14B,
   Gemma-2-9B via Ollama) with the R1–R3 prompt, scored against the gold
   English (chrF + refusal-leak scan must be zero).
3. **Streaming endpoint.** FastAPI/WebSocket service wrapping 1+2
   (whisper-streaming/WhisperLive-style chunking; LocalAgreement commit).
   `tailscale serve` in front. Target: committed captions ≤ ~3 s behind speech.
4. **Third engine in the app.** Add "Home GPU (Tailscale)" to the engine
   picker in `live-translator.html` + a server-URL field (localStorage, like
   other settings). Cloud/on-device paths unchanged.
5. **Live trial** during a service with cloud engine ready as instant fallback.
6. **Fine-tune only if measurements demand it** (LoRA on the 3090: Whisper on
   sermon audio; translation on the parallel corpus). Vocabulary gaps may be
   fixable with `initial_prompt` / glossary first — measure before tuning.

## Already done (2026-06-10)

- Configurable export filename root in `live-translator.html` (settings field,
  persisted; sanitized; default `transcript` so existing `biblestudy`
  `parse_app_export.py` workflows keep working).

## Step 4 in progress (paused 2026-06-10 ~6:30pm, resume after usage reset)

Server (steps 1-3) is DONE and pushed (biblestudy `defe-transcripts`,
`server/`). App integration mapped, not yet edited:

- Add `<option value="homegpu">` to `#engine` (line ~167) + a `homegpuOpts`
  div with `homeGpuUrl` input (state default '', persist like `vocab`).
- **Fix first**: the `fileRoot` field (lines ~196-199) sits INSIDE `cloudOpts`
  so it's hidden unless engine=cloud — move it after cloudOpts' closing div.
- `applyEngine()` (~line 1029): 3-way toggle (localOpts/cloudOpts/homegpuOpts).
- `start()` (~1281) / `updateControls()` (~1322): homegpu needs NO API keys —
  gate on homeGpuUrl instead; open WebSocket, then `startCapture()`.
- `onAudio()` (~1215): when homegpu, send each frame downsampled to 16 kHz
  Float32 over the WS (linear-interp downsampler; skip client VAD machinery,
  keep `setLevel`); server does VAD/reflow/translation.
- WS `es` event -> new segment (es done, enState 'translating', dir es-en,
  map server id -> seg); `en` event -> fill seg.en, state done, paintRow.
  Diarization won't cover homegpu segments (no client audio copy) — fine v1.
- stop(): send {"type":"stop"}, close WS after drain.

## Open decisions

- Translation direction(s): ES→EN confirmed; EN→ES later? (UI + prompt only.)
- Which LLM wins the bake-off (step 2 decides, not preference).
- Whether step 3 serves the page itself on the tailnet (an alternative to
  mixed-content care: open the app from the tailnet origin instead of
  harlananelson.com when using the home engine).
