"""Generate finetune_whisper_sermons.ipynb.

Edit the CELLS list below and re-run `python build_notebook.py` to regenerate the
notebook — this is the maintainable source, so we never hand-edit .ipynb JSON.

Fine-tunes Whisper for Pr. Jean Petit's Spanish sermons (Iglesia de Fe) so
real-time Spanish->English runs on an iPad Air 5 (M1, 8GB) via WhisperKit:
download audio from YouTube, re-transcribe with faster-whisper large-v3 on the
GPU (much better labels than the YouTube auto-captions), distill into a small
Whisper. English is produced by a separate cloud translation step.
"""
import json

# Each cell is (kind, source) where kind is "md" or "code".
CELLS = [
("md", r"""# Fine-tune Whisper for Pr. Jean Petit's Spanish sermons

**Goal:** better real-time Spanish→English of Pr. Jean Petit / Iglesia de Fe sermons on an **iPad Air 5 (Apple M1, 8 GB)**.

**Pipeline (this notebook does the ASR fine-tune):**
1. **Spanish audio → Spanish text** — fine-tuned Whisper, on the iPad via WhisperKit. ← *this notebook*
2. **Spanish text → English** — a cloud LLM (internet available; your Live Translator already does this).

**Data:** the sermon YouTube URLs are listed below (one channel, *Pr. Jean Petit* — the biblestudy repo is private, so we don't clone it). We download each sermon's audio and **re-transcribe it with faster-whisper large-v3 on the GPU** — the existing YouTube auto-captions are the weakest labels, and large-v3 gives full, well-segmented sentences. Then we distill those labels into a small Whisper. Teacher→student adapted to *his voice*; the ceiling is large-v3's accuracy on this speaker.

**Run on a GPU** (Colab/Kaggle/HF), not the iPad. ~13 h of audio at large-v3 takes a while even on a GPU — batched inference (below) keeps it reasonable."""),

("code", r"""%pip install -q "transformers>=4.44" "datasets>=2.20" "accelerate>=0.33" "peft>=0.12" evaluate jiwer soundfile librosa yt-dlp faster-whisper"""),

("md", r"""## Configuration

Pr. Jean Petit's sermons (jean-petit talks + Iglesia de Fe services), one channel. Two sermons in the repo had no source URL and are omitted. Hold one out for evaluation."""),

("code", r"""# --- EDIT THIS ---  (Pr. Jean Petit / Iglesia de Fe — one YouTube channel)
SERMONS = [
    # (name,                  YouTube URL)
    ("estilo-vida-alejando",  "https://www.youtube.com/watch?v=1BIa-AWgG7Y"),
    ("no-saltes-solo",        "https://www.youtube.com/watch?v=QKr-XXnYktA"),   # <- held out for eval
    ("servicio-2026-05-24",   "https://www.youtube.com/live/-tTKmdUaqGI"),
    ("servicio-2026-05-31",   "https://www.youtube.com/watch?v=WRbaoILFH-Q"),
    ("servicio-2026-06-08",   "https://www.youtube.com/watch?v=emcQv9S0cFA"),
    ("servicio-2026-06-09",   "https://www.youtube.com/watch?v=FxSXSvp2M0M"),
    ("servicio-2026-06-16",   "https://www.youtube.com/watch?v=ftc7SkA7DFc"),
    ("servicio-2026-06-23",   "https://www.youtube.com/watch?v=yBZFAQRGKcU"),
]
HELD_OUT      = "no-saltes-solo"        # kept ENTIRELY for evaluation

BASE_MODEL    = "openai/whisper-small"  # student: converts to CoreML; real-time on M1
TEACHER_MODEL = "large-v3"              # faster-whisper teacher (GPU); far better labels than auto-captions
LANGUAGE      = "spanish"
TASK          = "transcribe"            # keep Spanish; English is cloud-side
MAX_SEG_SEC   = 28
MIN_SEG_SEC   = 1.0
SAMPLE_RATE   = 16000
BATCH_SIZE    = 16                      # batched large-v3 inference on the GPU
AUDIO_DIR     = "audio_cache"
OUTPUT_DIR    = "whisper-small-jeanpetit-es"

import os
os.makedirs(AUDIO_DIR, exist_ok=True)
sermons = [{"name": n, "url": u, "split": "eval" if n == HELD_OUT else "train"} for n, u in SERMONS]
print(f"{sum(s['split']=='train' for s in sermons)} train, {sum(s['split']=='eval' for s in sermons)} eval sermons")"""),

("md", r"""## Step 1 — Download audio (16 kHz mono) for each sermon

Colab has `ffmpeg` preinstalled, so `yt-dlp -x` can extract WAV directly. Cached, so re-runs skip."""),

("code", r"""import subprocess

def fetch_audio(url, name):
    out = os.path.join(AUDIO_DIR, name + ".wav")
    if os.path.exists(out):
        return out
    subprocess.run(["yt-dlp", "-f", "bestaudio", "-x", "--audio-format", "wav",
                    "--postprocessor-args", f"-ar {SAMPLE_RATE} -ac 1",
                    "-o", os.path.join(AUDIO_DIR, name + ".%(ext)s"), url], check=True)
    return out

for s in sermons:
    s["wav"] = fetch_audio(s["url"], s["name"])
    print("audio:", s["wav"])"""),

("md", r"""## Step 2 — Make labels: transcribe each sermon with large-v3 (batched, GPU)

`BatchedInferencePipeline` runs large-v3 several windows at a time — much faster than sequential on a GPU. VAD filtering skips music/silence (helps the casa-de-fe services). Each returned segment becomes one `(audio_clip, spanish_text)` training pair."""),

("code", r"""import torch, librosa, numpy as np
from faster_whisper import WhisperModel, BatchedInferencePipeline

on_gpu = torch.cuda.is_available()
teacher = WhisperModel(TEACHER_MODEL,
                       device="cuda" if on_gpu else "cpu",
                       compute_type="float16" if on_gpu else "int8")
pipe = BatchedInferencePipeline(model=teacher)
print("teacher on", "GPU" if on_gpu else "CPU (slow — use a GPU runtime)")

def label_sermon(s):
    audio, _ = librosa.load(s["wav"], sr=SAMPLE_RATE, mono=True)
    segments, _ = pipe.transcribe(s["wav"], language="es", batch_size=BATCH_SIZE, vad_filter=True)
    rows = []
    for seg in segments:
        txt = (seg.text or "").strip()
        dur = seg.end - seg.start
        if not txt or dur < MIN_SEG_SEC or dur > MAX_SEG_SEC:
            continue
        clip = audio[int(seg.start*SAMPLE_RATE):int(seg.end*SAMPLE_RATE)]
        if len(clip) >= MIN_SEG_SEC*SAMPLE_RATE:
            rows.append({"audio": clip.astype(np.float32), "sentence": txt, "split": s["split"]})
    print(f"  {s['name']}: {len(rows)} segments")
    return rows

all_rows = [r for s in sermons for r in label_sermon(s)]
train_rows = [r for r in all_rows if r["split"] == "train"]
eval_rows  = [r for r in all_rows if r["split"] == "eval"]
print(f"segments — train: {len(train_rows)}  eval: {len(eval_rows)}")"""),

("md", r"""## Step 3 — Build Hugging Face datasets"""),

("code", r"""from datasets import Dataset, Audio

def to_ds(rows):
    return Dataset.from_dict({
        "audio": [{"array": r["audio"], "sampling_rate": SAMPLE_RATE} for r in rows],
        "sentence": [r["sentence"] for r in rows],
    }).cast_column("audio", Audio(sampling_rate=SAMPLE_RATE))

train_ds = to_ds(train_rows)
eval_ds  = to_ds(eval_rows) if eval_rows else None
train_ds"""),

("md", r"""## Step 4 — Processor, feature extraction, collator, WER metric"""),

("code", r"""from dataclasses import dataclass
from typing import Any, Dict, List, Union
from transformers import WhisperProcessor

processor = WhisperProcessor.from_pretrained(BASE_MODEL, language=LANGUAGE, task=TASK)

def prepare(batch):
    a = batch["audio"]
    batch["input_features"] = processor.feature_extractor(
        a["array"], sampling_rate=a["sampling_rate"]).input_features[0]
    batch["labels"] = processor.tokenizer(batch["sentence"]).input_ids
    return batch

train_ds = train_ds.map(prepare, remove_columns=train_ds.column_names, num_proc=1)
if eval_ds is not None:
    eval_ds = eval_ds.map(prepare, remove_columns=eval_ds.column_names, num_proc=1)

@dataclass
class Collator:
    processor: Any
    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]):
        inp = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(inp, return_tensors="pt")
        labels = self.processor.tokenizer.pad(
            [{"input_ids": f["labels"]} for f in features], return_tensors="pt")
        lab = labels["input_ids"].masked_fill(labels.attention_mask.ne(1), -100)
        if (lab[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            lab = lab[:, 1:]
        batch["labels"] = lab
        return batch

collator = Collator(processor)

import evaluate
wer_metric = evaluate.load("wer")
norm = processor.tokenizer.normalize if hasattr(processor.tokenizer, "normalize") else (lambda x: x.lower())

def compute_metrics(pred):
    pred_ids, label_ids = pred.predictions, pred.label_ids
    label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
    pred_str  = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
    return {"wer": 100 * wer_metric.compute(
        predictions=[norm(p) for p in pred_str], references=[norm(l) for l in label_str])}"""),

("md", r"""## Step 5 — Load the model, attach LoRA, train"""),

("code", r"""from transformers import WhisperForConditionalGeneration
from peft import LoraConfig, get_peft_model

model = WhisperForConditionalGeneration.from_pretrained(BASE_MODEL)
model.config.forced_decoder_ids = None
model.config.suppress_tokens = []
model.generation_config.language = LANGUAGE
model.generation_config.task = TASK

lora = LoraConfig(r=32, lora_alpha=64, target_modules=["q_proj", "v_proj"],
                  lora_dropout=0.05, bias="none")
model = get_peft_model(model, lora)
model.print_trainable_parameters()"""),

("code", r"""from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

args = Seq2SeqTrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    learning_rate=1e-3,            # LoRA likes a higher LR; ~1e-5 for a full fine-tune
    warmup_steps=50,
    num_train_epochs=3,
    fp16=torch.cuda.is_available(),
    eval_strategy="epoch" if eval_ds is not None else "no",
    save_strategy="epoch",
    predict_with_generate=True,
    generation_max_length=225,
    logging_steps=25,
    report_to="none",
    remove_unused_columns=False,   # required for PEFT + Whisper
    label_names=["labels"],
)

trainer = Seq2SeqTrainer(
    model=model, args=args,
    train_dataset=train_ds, eval_dataset=eval_ds,
    data_collator=collator, compute_metrics=compute_metrics,
    processing_class=processor,
)
trainer.train()"""),

("md", r"""## Step 6 — Evaluate WER on the held-out sermon

Note: this measures WER against the **large-v3 labels**, i.e. how well the small model matches the teacher — not ground truth. For a true number, evaluate against a hand-checked transcript."""),

("code", r"""print(trainer.evaluate() if eval_ds is not None else "No eval set — set HELD_OUT to a sermon name.")"""),

("md", r"""## Step 7 — Save (merge LoRA) and push to the Hub

You have a Hugging Face account — uncomment to push (`huggingface-cli login` first, or use a token)."""),

("code", r"""merged = model.merge_and_unload()       # fold LoRA into base -> standard Whisper checkpoint
merged.save_pretrained(OUTPUT_DIR)
processor.save_pretrained(OUTPUT_DIR)
print("saved to", OUTPUT_DIR)

# from huggingface_hub import login; login()
# merged.push_to_hub("harlananelson/whisper-small-jeanpetit-es")
# processor.push_to_hub("harlananelson/whisper-small-jeanpetit-es")"""),

("md", r"""## Step 8 — Convert to CoreML for WhisperKit (run on a Mac)

```bash
pip install whisperkittools
whisperkit-generate-model --model-version OUTPUT_DIR_OR_HF_REPO \
    --output-dir ./CompressedModels --quantize
```

Bundle the `.mlmodelc` in a WhisperKit app on the iPad Air 5. Start with `small`; if accuracy needs a bump and it stays real-time, re-run with `BASE_MODEL = "openai/whisper-large-v3-turbo"`. Docs: <https://github.com/argmaxinc/WhisperKit>"""),

("md", r"""## Step 9 — The English side, and notes

On the iPad the fine-tuned Whisper emits **Spanish** in real time; send each finished sentence to a cloud LLM for **English** — exactly what your `live-translator.html` already does.

**End to end:** iPad mic → fine-tuned Whisper (Spanish, on-device) → cloud LLM → English caption.

### Notes
- **Labels:** large-v3 transcription beats the YouTube auto-captions (full sentences, clean segments), but it still mishears rare names (e.g. *Betsabé*, *sabuesos*). Hand-correct a subset if you need gold references.
- **casa-de-fe services contain non-sermon audio** (worship, announcements, multiple voices). VAD drops silence/music but not other speakers — for the cleanest single-speaker result, train on the `jean-petit` talks alone (drop the `servicio-*` rows from `SERMONS`).
- **Speed:** ~13 h of audio at large-v3 is the slow part; batched inference helps. To go faster, set `TEACHER_MODEL = "large-v3-turbo"` (slightly lower quality).
- **8 GB iPad:** keep ASR to `small`/`turbo`; translation is cloud, so RAM isn't the bottleneck."""),
]


def cell(kind, src):
    base = {"metadata": {}, "source": src.splitlines(keepends=True)}
    if kind == "md":
        return {"cell_type": "markdown", **base}
    return {"cell_type": "code", "execution_count": None, "outputs": [], **base}


nb = {
    "cells": [cell(k, s) for k, s in CELLS],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with open("finetune_whisper_sermons.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("wrote finetune_whisper_sermons.ipynb with", len(CELLS), "cells")
