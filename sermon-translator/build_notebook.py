"""Generate finetune_whisper_sermons.ipynb.

Edit the CELLS list below and re-run `python build_notebook.py` to regenerate the
notebook — this is the maintainable source, so we never hand-edit .ipynb JSON.

The notebook fine-tunes OpenAI Whisper for SPANISH transcription of one speaker
(a pastor) from his YouTube sermons, for on-device ASR on an iPad Air 5 (M1, 8GB)
via WhisperKit. English is produced by a separate cloud translation step
(internet is available), so only the Spanish ASR is fine-tuned here.
"""
import json

# Each cell is (kind, source) where kind is "md" or "code".
CELLS = [
("md", r"""# Fine-tune Whisper for Spanish sermon transcription

**Goal:** better real-time Spanish→English of a specific pastor's live sermons on an **iPad Air 5 (Apple M1, 8 GB)**.

**Pipeline (this notebook does step 1 only):**
1. **Spanish audio → Spanish text** — fine-tuned Whisper, runs *on the iPad* via WhisperKit. ← *this notebook*
2. **Spanish text → English** — a cloud LLM (internet is available; your Live Translator already does this).

We fine-tune **Spanish transcription** (not translation) because that's where speaker-specific tuning pays off — his accent, cadence, proper names, and theological vocabulary — and the training data is easy: *Spanish audio + Spanish text*.

**Run this on a GPU** (Colab/Kaggle/HF), **not** on the iPad. The iPad only runs the *converted* model later.

**Prereqs:** a GPU runtime; optionally a Hugging Face token (to push the model); the URLs of several of the pastor's sermons. Aim for **~5–10 hours** of his audio for a solid result."""),

("code", r"""%pip install -q "transformers>=4.44" "datasets>=2.20" "accelerate>=0.33" "peft>=0.12" evaluate jiwer soundfile librosa webvtt-py yt-dlp"""),

("md", r"""## Configuration

Put the pastor's sermon URLs here. Keep **one whole sermon** aside as the held-out evaluation set (never train on it)."""),

("code", r"""# --- EDIT THIS ---
SERMON_URLS = [
    # "https://www.youtube.com/watch?v=XXXXXXXXXXX",
    # "https://www.youtube.com/watch?v=YYYYYYYYYYY",
]
HELD_OUT_URL = ""   # one sermon URL kept ENTIRELY for evaluation (not in SERMON_URLS)

BASE_MODEL  = "openai/whisper-small"   # small converts well to CoreML and runs real-time on M1.
                                       # Options: openai/whisper-medium, openai/whisper-large-v3-turbo
LANGUAGE    = "spanish"
TASK        = "transcribe"             # NOT "translate" — we keep Spanish; English is done in the cloud.
MAX_SEG_SEC = 28                       # Whisper's window is 30s; keep segments under it.
SAMPLE_RATE = 16000
WORKDIR     = "sermon_data"
OUTPUT_DIR  = "whisper-small-sermon-es"

import os
os.makedirs(WORKDIR, exist_ok=True)
assert SERMON_URLS, "Add at least one sermon URL to SERMON_URLS."
print(f"{len(SERMON_URLS)} training sermon(s); held-out: {HELD_OUT_URL or 'NONE — set one!'}")"""),

("md", r"""## Step 1 — Download audio + Spanish subtitles (yt-dlp)

We grab 16 kHz mono audio and the **Spanish** subtitle track. Human/official subs are best; auto-generated subs are a usable fallback **but should be spot-corrected** — fine-tuning on wrong text teaches wrong text. If a sermon has no subs at all, you'll need to transcribe it once with a large Whisper and correct it before training."""),

("code", r"""import subprocess

def fetch(url, idx, folder=WORKDIR):
    base = f"{folder}/sermon_{idx:02d}"
    # audio -> 16k mono wav
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "wav",
        "--postprocessor-args", f"-ar {SAMPLE_RATE} -ac 1",
        "-o", base + ".%(ext)s", url], check=True)
    # spanish subtitles (human first; auto as fallback), as vtt
    subprocess.run([
        "yt-dlp", "--skip-download",
        "--write-subs", "--write-auto-subs", "--sub-langs", "es.*",
        "--convert-subs", "vtt", "-o", base + ".%(ext)s", url], check=False)
    return base

train_bases = [fetch(u, i) for i, u in enumerate(SERMON_URLS)]
heldout_base = fetch(HELD_OUT_URL, 99) if HELD_OUT_URL else None
print("downloaded:", train_bases, heldout_base)"""),

("md", r"""## Step 2 — Slice audio into ≤28 s segments aligned to subtitle cues

We read the VTT, merge consecutive cues up to `MAX_SEG_SEC`, and cut the matching audio. Each segment becomes one `(audio, sentence)` training example."""),

("code", r"""import glob, re, webvtt, soundfile as sf, librosa, numpy as np

def clean(t):
    t = re.sub(r"<[^>]+>", " ", t)          # strip vtt inline tags
    t = re.sub(r"\s+", " ", t).strip()
    return t

def vtt_for(base):
    cands = sorted(glob.glob(base + "*.vtt"))
    return cands[0] if cands else None

def segments_from(base):
    vtt = vtt_for(base)
    wav = base + ".wav"
    if not vtt or not os.path.exists(wav):
        print("  skip (missing subs or audio):", base); return []
    audio, sr = librosa.load(wav, sr=SAMPLE_RATE, mono=True)
    cues = [(c.start_in_seconds, c.end_in_seconds, clean(c.text)) for c in webvtt.read(vtt) if clean(c.text)]
    rows, cur_s, cur_e, cur_t = [], None, None, []
    def flush():
        if cur_t:
            a = audio[int(cur_s*sr):int(cur_e*sr)]
            if len(a) > 0.5*sr:
                rows.append({"audio": a.astype(np.float32), "sentence": " ".join(cur_t)})
    for s, e, t in cues:
        if cur_s is None:
            cur_s, cur_e, cur_t = s, e, [t]
        elif e - cur_s <= MAX_SEG_SEC:
            cur_e, cur_t = e, cur_t + [t]
        else:
            flush(); cur_s, cur_e, cur_t = s, e, [t]
    flush()
    print(f"  {base}: {len(rows)} segments")
    return rows

train_rows = [r for b in train_bases for r in segments_from(b)]
eval_rows  = segments_from(heldout_base) if heldout_base else []
print(f"train segments: {len(train_rows)} | eval segments: {len(eval_rows)}")"""),

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

("md", r"""## Step 4 — Processor, feature extraction, collator, metric"""),

("code", r"""import torch
from dataclasses import dataclass
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

("md", r"""## Step 5 — Load the model and attach LoRA, then train

LoRA keeps fine-tuning feasible on a single GPU and produces a tiny adapter. For maximum quality with enough GPU you can skip PEFT and train all weights."""),

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
    learning_rate=1e-3,            # LoRA likes a higher LR; use ~1e-5 for full fine-tune
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

("md", r"""## Step 6 — Evaluate WER on the held-out sermon"""),

("code", r"""if eval_ds is not None:
    print(trainer.evaluate())
else:
    print("No held-out sermon set — set HELD_OUT_URL and re-run to measure WER.")"""),

("md", r"""## Step 7 — Save (merge the LoRA adapter) and optionally push to the Hub"""),

("code", r"""merged = model.merge_and_unload()       # fold LoRA into base weights -> standard Whisper checkpoint
merged.save_pretrained(OUTPUT_DIR)
processor.save_pretrained(OUTPUT_DIR)
print("saved to", OUTPUT_DIR)

# from huggingface_hub import login; login()
# merged.push_to_hub("your-username/whisper-small-sermon-es")
# processor.push_to_hub("your-username/whisper-small-sermon-es")"""),

("md", r"""## Step 8 — Convert to CoreML for WhisperKit (do this on a Mac)

WhisperKit runs Whisper on the iPad's Neural Engine. Convert the fine-tuned checkpoint with Argmax's tools (run on macOS):

```bash
pip install whisperkittools
# point it at the merged checkpoint from Step 7 (local path or your HF repo id)
whisperkit-generate-model --model-version OUTPUT_DIR_OR_HF_REPO \
    --output-dir ./CompressedModels --quantize
```

Then bundle the resulting `.mlmodelc` in a small WhisperKit app (Swift) and load it on the iPad Air 5. Start with the `small` model; if it's too slow, try `whisper-large-v3-turbo` as the base and re-convert. Docs: <https://github.com/argmaxinc/WhisperKit>"""),

("md", r"""## Step 9 — The English side (cloud)

On the iPad, fine-tuned Whisper emits **Spanish** text in real time. Send each finished sentence to a cloud LLM for the **English** translation — exactly what your **Live Translator** (`live-translator.html`) already does (Anthropic/OpenAI, context-aware, 5 concurrent). So the device only runs ASR; the network handles translation.

**End to end:** iPad mic → fine-tuned Whisper (Spanish, on-device, WhisperKit) → cloud LLM → English caption.

### Caveats
- **Data quality:** correct auto-generated subtitles before training; bad references teach bad output.
- **Amount:** ~5–10 h of his audio gives a meaningful WER drop; more helps for names/terms.
- **Rights:** fine for personal/ministry use; mind the source's terms if you redistribute.
- **8 GB iPad:** keep ASR to `small`/`turbo`; translation is cloud, so RAM isn't the bottleneck here."""),
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
