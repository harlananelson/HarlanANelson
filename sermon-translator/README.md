# Sermon translator — fine-tuning

Make real-time **Spanish→English** of **Pr. Jean Petit / Iglesia de Fe** sermons work well on an
**iPad Air 5 (Apple M1, 8 GB)**.

## Pipeline

```
iPad mic → fine-tuned Whisper (Spanish ASR, on-device via WhisperKit) → cloud LLM → English caption
```

- **On-device:** Spanish speech → Spanish text (this is what we fine-tune — his voice, accent,
  names, theological vocabulary). RAM-light, real-time on M1.
- **Cloud:** Spanish text → English (internet is available; `../live-translator.html` already does this).

## Data: Pr. Jean Petit's sermons

The biblestudy repo (`github.com/harlananelson/biblestudy`) is **private**, so the notebook does
**not** clone it — the sermon YouTube URLs are listed directly in the notebook's config (one
channel, *Pr. Jean Petit*: the `jean-petit` talks + the Iglesia de Fe `servicio-*` services).
`disciplina-iglesia` is a different preacher and is omitted.

- **The existing transcripts are YouTube auto-captions** (the weakest source — confirmed across all
  the target sermons; chopped into ~2 s fragments). So the notebook **downloads the audio and
  re-transcribes it with faster-whisper large-v3 on the GPU** (batched), then distills those much
  better labels into the small model (teacher→student). The ceiling is large-v3's accuracy on this
  speaker; it still mishears rare names (*Betsabé*, *sabuesos*) — hand-correct a subset for gold.
- **Cleanest signal is the `jean-petit` talks** (single speaker). The `servicio-*` services include
  worship/announcements/multiple voices (VAD drops silence/music, not other speakers) — drop them
  from `SERMONS` for the tightest single-speaker fit.

## Running large-v3 locally (biblestudy)

The biblestudy flake now provides the toolchain (`pkgs.ffmpeg`, `pkgs.yt-dlp`, and `faster-whisper`
in `requirements.txt`), so `scripts/transcribe_audio.py` works in `nix develop`. The bulk large-v3
run is meant for the Colab GPU (this notebook); local CPU transcription works but is slow.

## Files

| File | What |
|------|------|
| `finetune_whisper_sermons.ipynb` | The notebook — run on a **GPU** (Colab/Kaggle/HF), not the iPad. |
| `build_notebook.py` | Generator. **Edit this and re-run `python build_notebook.py`** — don't hand-edit the `.ipynb`. |

## How to use

1. Open the notebook in Colab/Kaggle with a GPU runtime. (You have a Hugging Face account — Step 9
   can push the result to the Hub.)
2. Check the **Configuration** cell: the `SERMONS` URL list, `HELD_OUT` (default `no-saltes-solo`), `BASE_MODEL`.
3. Run top to bottom: download audio per sermon → re-transcribe with large-v3 (batched, GPU) →
   LoRA-fine-tune `whisper-small` → WER on the held-out sermon → save/merge.
4. **Convert for the iPad** (on a Mac) with `whisperkittools` → CoreML, bundle in a WhisperKit app.
5. Translate Spanish → English with the cloud LLM (Live Translator).

## Notes

- 8 sermons with URLs (~13 h) are listed in `SERMONS`; two (`el-ascensor-correcto`, `casa-2026-05-29`)
  had no source URL in the repo, so they're omitted.
- Default base `whisper-small` (converts well, real-time on M1). Try `whisper-large-v3-turbo` for
  more accuracy if it stays fast enough.
- More data: everything is on the one channel **"Pr. Jean Petit"** — extend biblestudy and re-run.
- Rights: fine for personal/ministry use; mind the source's terms if you redistribute.
