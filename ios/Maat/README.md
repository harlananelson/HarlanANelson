# Maat iPad shell — on-device ASR

Thin native wrapper around live Maat (`https://harlananelson.com/maat.html`).
The only native job is **speech recognition on the M1 Neural Engine** so a CRS
podcast keeps transcribing when the iPad loses its iPhone / Tailscale path.

This Linux workstation **cannot install the app**. Open the project on a Mac.

## What runs where

| Piece | Where |
|---|---|
| Maat UI (Listen, Practice, Tools) | WKWebView, live Netlify page |
| Mic + ASR | Native `Speech` framework, `requiresOnDeviceRecognition` → ANE |
| Home GPU Whisper large-v3 | Unchanged fallback when this shell is not present |
| WhisperKit | Not in v1. Swap `OnDeviceASR` later for better WER |

Safari / the PWA **cannot** call the Neural Engine. This app can.

## Install (Mac + iPad Air 5)

1. Open `ios/Maat.xcodeproj` in Xcode 16+.
2. Signing: your Personal Team (free) is enough for a development install.
   Set `DEVELOPMENT_TEAM` on the Maat target.
3. Target the physical iPad (iPadOS 18+). First build asks for Mic + Speech.
4. Apple may download an on-device speech model the first time you are online.
   After that, English (and Spanish) work with the radio off.

## How Listen uses it

`live-translator.html` feature-detects `webkit.messageHandlers.maatAsr`.
If present, Start does **not** open the Home GPU WebSocket for ASR. Final
utterances paint in the page and queue a POST to tesla-bridge
`/api/transcript/append` when the network is back.

## WhisperKit later

Add the WhisperKit Swift package, download `openai_whisper-small` or
`large-v3-turbo` Core ML, and point `OnDeviceASR` at it. Same JS contract.
Do not rewrite Maat in Swift.
