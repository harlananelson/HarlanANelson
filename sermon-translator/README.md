# Sermon translator — fine-tuning

Make real-time **Spanish→English** of a specific pastor's live sermons work well on an
**iPad Air 5 (Apple M1, 8 GB)**.

## Pipeline

```
iPad mic → fine-tuned Whisper (Spanish ASR, on-device via WhisperKit) → cloud LLM → English caption
```

- **On-device:** Spanish speech → Spanish text. This is what we fine-tune (the pastor's voice,
  accent, names, theological vocabulary). RAM-light, real-time on M1.
- **Cloud:** Spanish text → English. Internet is available, so translation is handled by a cloud
  LLM — your existing `../live-translator.html` already does exactly this (context-aware, 5 concurrent).
  No translation fine-tuning needed.

Whisper *can* translate Spanish→English in one pass, but we keep two stages: ASR fine-tuning has
easy training data (Spanish audio + Spanish text) and the cloud LLM translates better than Whisper.

## Files

| File | What |
|------|------|
| `finetune_whisper_sermons.ipynb` | The fine-tuning notebook — run on a **GPU** (Colab/Kaggle/HF), not the iPad. |
| `build_notebook.py` | Generator for the notebook. **Edit this and re-run `python build_notebook.py`** — don't hand-edit the `.ipynb`. |

## How to use

1. Open `finetune_whisper_sermons.ipynb` in Colab/Kaggle with a GPU runtime.
2. In the **Configuration** cell, paste the pastor's sermon YouTube URLs and set one `HELD_OUT_URL`.
3. Run top to bottom: it downloads audio + Spanish subtitles, slices into ≤28 s segments,
   fine-tunes `whisper-small` with LoRA, reports WER on the held-out sermon, and saves the model.
4. **Convert for the iPad** (on a Mac) with `whisperkittools` → CoreML, bundle in a WhisperKit app.
5. Translate the Spanish text → English with the cloud LLM (Live Translator).

## Notes

- Aim for **~5–10 h** of his audio. Correct auto-generated subtitles before training — bad
  references teach bad output.
- Default base model is `whisper-small` (converts well, real-time on M1). Try
  `whisper-large-v3-turbo` if you want more accuracy and it stays fast enough.
- 8 GB iPad: keep ASR to `small`/`turbo`; translation is cloud, so RAM isn't the bottleneck.
- Rights: fine for personal/ministry use; mind the source's terms if you redistribute.
