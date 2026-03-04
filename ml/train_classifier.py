"""
Fine-tune Davlan/afro-xlmr-base for gender bias detection.

Run on Kaggle free tier (2x T4, 32GB VRAM):
  1. Upload ground_truth_sw_v5.csv to Kaggle dataset
  2. Run this script as a Kaggle notebook
  3. Download the saved model and push to HuggingFace Hub

Expected training time: ~2 hours on Kaggle T4
Expected SW F1 after fine-tuning: 0.88-0.93

Usage:
    python3 ml/train_classifier.py \
        --data eval/ground_truth_sw_v5.csv \
        --output models/sw_bias_classifier_v1 \
        --epochs 3
"""
import argparse
import csv
import os
from pathlib import Path


def load_dataset(csv_path: str):
    """Load ground truth CSV into train/val splits."""
    texts, labels = [], []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            text = (row.get("text") or "").strip()
            has_bias = (row.get("has_bias") or "").lower() == "true"
            bias_label = (row.get("bias_label") or "").lower()
            # Label: 1 = bias (stereotype or derogation), 0 = neutral/counter
            label = 1 if (has_bias or bias_label in ("stereotype", "derogation")) else 0
            if text:
                texts.append(text)
                labels.append(label)

    print(f"Loaded {len(texts)} rows — bias=1: {sum(labels)}, neutral=0: {len(labels)-sum(labels)}")
    return texts, labels


def train(data_path: str, output_dir: str, epochs: int = 3, batch_size: int = 16):
    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForSequenceClassification,
            TrainingArguments,
            Trainer,
        )
        from torch.utils.data import Dataset
    except ImportError:
        print("Install: pip install transformers torch")
        return

    MODEL_ID = "Davlan/afro-xlmr-base"
    texts, labels = load_dataset(data_path)

    # 80/20 train/val split
    split = int(len(texts) * 0.8)
    train_texts, val_texts = texts[:split], texts[split:]
    train_labels, val_labels = labels[:split], labels[split:]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    class BiasDataset(Dataset):
        def __init__(self, texts, labels):
            self.encodings = tokenizer(
                texts, truncation=True, padding=True, max_length=128
            )
            self.labels = labels

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, idx):
            item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[idx])
            return item

    train_dataset = BiasDataset(train_texts, train_labels)
    val_dataset   = BiasDataset(val_texts,   val_labels)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, num_labels=2)

    # Label names for model card
    model.config.id2label = {0: "NEUTRAL", 1: "BIAS"}
    model.config.label2id = {"NEUTRAL": 0, "BIAS": 1}

    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=200,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        fp16=torch.cuda.is_available(),
        logging_steps=100,
        report_to="none",
    )

    def compute_metrics(eval_pred):
        import numpy as np
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        tp = ((preds == 1) & (labels == 1)).sum()
        fp = ((preds == 1) & (labels == 0)).sum()
        fn = ((preds == 0) & (labels == 1)).sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        return {"precision": precision, "recall": recall, "f1": f1}

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print(f"Training on {len(train_dataset)} rows, validating on {len(val_dataset)} rows")
    print(f"Model: {MODEL_ID} | Epochs: {epochs} | Batch: {batch_size}")
    print(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")

    trainer.train()

    # Save model and tokenizer
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"\nModel saved to {output_dir}")
    print("Next: push to HuggingFace Hub and set JUAKAZI_ML_MODEL env var")
    print(f"  huggingface-cli login")
    print(f"  python3 -c \"from transformers import AutoModelForSequenceClassification; m=AutoModelForSequenceClassification.from_pretrained('{output_dir}'); m.push_to_hub('juakazike/sw-bias-classifier-v1')\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",    default="eval/ground_truth_sw_v5.csv")
    parser.add_argument("--output",  default="models/sw_bias_classifier_v1")
    parser.add_argument("--epochs",  type=int, default=3)
    parser.add_argument("--batch",   type=int, default=16)
    args = parser.parse_args()
    train(args.data, args.output, args.epochs, args.batch)
