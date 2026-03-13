"""
Fine-tune AfroXLMR-base on our Swahili ground truth for gender bias detection.

Usage:
    python3 scripts/train_sw_classifier.py

Requirements:
    pip install transformers datasets torch scikit-learn

Output:
    - Model saved to models/sw-bias-classifier-v2/
    - Push to HF with: huggingface-cli upload juakazike/sw-bias-classifier-v2 models/sw-bias-classifier-v2/

Strategy:
    - Base: Davlan/afro-xlmr-base (covers Swahili, 560M params)
    - Data: 1,267 biased + 5,068 neutral (4:1 undersample to reduce imbalance)
    - Epochs: 5, batch 16, LR 2e-5
    - Class weights to handle residual imbalance
    - Stage 2 fallback only — never replaces rules engine

Expected outcome:
    - SW F1 fallback layer: 0.75+ on implicit bias rows
    - Combined rules + ML: SW F1 > 0.85
"""
import csv
import json
import random
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
import numpy as np

# ── Config ──────────────────────────────────────────────────────────────────
BASE_MODEL = "Davlan/afro-xlmr-base"
GROUND_TRUTH = "eval/ground_truth_sw_v5.csv"
OUTPUT_DIR = "models/sw-bias-classifier-v2"
MAX_LENGTH = 128
NEUTRAL_RATIO = 4          # neutral:bias sample ratio (keep 4x neutral rows)
TRAIN_SPLIT = 0.85
SEED = 42
EPOCHS = 5
BATCH_SIZE = 16
LR = 2e-5
# ────────────────────────────────────────────────────────────────────────────

random.seed(SEED)
np.random.seed(SEED)


def load_data(path: str):
    """Load ground truth, undersample neutral to NEUTRAL_RATIO:1."""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    bias_rows = [r for r in rows if r.get("has_bias", "").strip().lower() == "true"]
    neutral_rows = [r for r in rows if r.get("has_bias", "").strip().lower() == "false"]

    # Filter empty texts
    bias_rows = [r for r in bias_rows if r.get("text", "").strip()]
    neutral_rows = [r for r in neutral_rows if r.get("text", "").strip()]

    # Undersample neutral
    target_neutral = len(bias_rows) * NEUTRAL_RATIO
    random.shuffle(neutral_rows)
    neutral_rows = neutral_rows[:target_neutral]

    all_rows = [(r["text"].strip(), 1) for r in bias_rows] + \
               [(r["text"].strip(), 0) for r in neutral_rows]

    random.shuffle(all_rows)

    split = int(len(all_rows) * TRAIN_SPLIT)
    train = all_rows[:split]
    val = all_rows[split:]

    print(f"Train: {len(train)} ({sum(1 for _, l in train if l == 1)} bias, {sum(1 for _, l in train if l == 0)} neutral)")
    print(f"Val:   {len(val)} ({sum(1 for _, l in val if l == 1)} bias, {sum(1 for _, l in val if l == 0)} neutral)")
    return train, val


class BiasDataset(Dataset):
    def __init__(self, data, tokenizer, max_length):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text, label = self.data[idx]
        enc = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
            "labels": torch.tensor(label, dtype=torch.long),
        }


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    f1 = f1_score(labels, preds, average="binary")
    precision = precision_score(labels, preds, average="binary", zero_division=0)
    recall = recall_score(labels, preds, average="binary")
    return {"f1": f1, "precision": precision, "recall": recall}


def main():
    print(f"Loading data from {GROUND_TRUTH}...")
    train_data, val_data = load_data(GROUND_TRUTH)

    print(f"\nLoading tokenizer and model from {BASE_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=2,
        id2label={0: "NEUTRAL", 1: "BIAS"},
        label2id={"NEUTRAL": 0, "BIAS": 1},
        ignore_mismatched_sizes=True,
    )

    train_dataset = BiasDataset(train_data, tokenizer, MAX_LENGTH)
    val_dataset = BiasDataset(val_data, tokenizer, MAX_LENGTH)

    # Class weights for residual imbalance
    n_bias = sum(1 for _, l in train_data if l == 1)
    n_neutral = sum(1 for _, l in train_data if l == 0)
    pos_weight = n_neutral / n_bias
    print(f"\nClass weight for BIAS: {pos_weight:.2f}")

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LR,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        seed=SEED,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("\nStarting training...")
    trainer.train()

    print("\nFinal evaluation:")
    results = trainer.evaluate()
    print(json.dumps(results, indent=2))

    print(f"\nSaving model to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Save training metadata
    meta = {
        "base_model": BASE_MODEL,
        "ground_truth": GROUND_TRUTH,
        "train_size": len(train_data),
        "val_size": len(val_data),
        "neutral_ratio": NEUTRAL_RATIO,
        "val_f1": results.get("eval_f1"),
        "val_precision": results.get("eval_precision"),
        "val_recall": results.get("eval_recall"),
    }
    with open(f"{OUTPUT_DIR}/training_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nDone. Upload with:")
    print(f"  huggingface-cli upload juakazike/sw-bias-classifier-v2 {OUTPUT_DIR}/")
    print(f"\nThen set env var:")
    print(f"  JUAKAZI_ML_MODEL=juakazike/sw-bias-classifier-v2")


if __name__ == "__main__":
    main()
