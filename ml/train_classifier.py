"""
Fine-tune Davlan/afro-xlmr-base for gender bias detection.

Uses stratified train/val splits and BIAS oversampling when available
(see scripts/stratified_split.py and docs/STRATIFIED_SPLIT.md). Default 5 epochs
for better val F1 (target 0.82–0.88 per MASTER_PLAN).

Usage:
  # With stratified splits (run scripts/stratified_split.py --language sw first)
  python3 ml/train_classifier.py --use-splits --language sw --epochs 5

  # Single CSV (legacy 80/20 split)
  python3 ml/train_classifier.py --data eval/ground_truth_sw_v5.csv --epochs 5
"""
import argparse
import csv
import json
from pathlib import Path


def _label_from_row(row: dict) -> int:
    has_bias = (row.get("has_bias") or "").lower() == "true"
    bias_label = (row.get("bias_label") or "").lower()
    return 1 if (has_bias or bias_label in ("stereotype", "derogation")) else 0


def load_dataset(csv_path: str):
    """Load single CSV into (texts, labels)."""
    texts, labels = [], []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = (row.get("text") or "").strip()
            if text:
                texts.append(text)
                labels.append(_label_from_row(row))
    print(f"Loaded {len(texts)} rows — bias=1: {sum(labels)}, neutral=0: {len(labels)-sum(labels)}")
    return texts, labels


def load_train_val_splits(train_path: str, val_path: str):
    """Load train and val CSVs; return (train_texts, train_labels, val_texts, val_labels)."""
    train_texts, train_labels = [], []
    with open(train_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = (row.get("text") or "").strip()
            if text:
                train_texts.append(text)
                train_labels.append(_label_from_row(row))
    val_texts, val_labels = [], []
    with open(val_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = (row.get("text") or "").strip()
            if text:
                val_texts.append(text)
                val_labels.append(_label_from_row(row))
    print(f"Train: {len(train_texts)} rows (bias=1: {sum(train_labels)})")
    print(f"Val:   {len(val_texts)} rows (bias=1: {sum(val_labels)})")
    return train_texts, train_labels, val_texts, val_labels


def train(
    data_path: str | None,
    output_dir: str,
    epochs: int = 5,
    batch_size: int = 16,
    train_path: str | None = None,
    val_path: str | None = None,
):
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

    if train_path and val_path:
        train_texts, train_labels, val_texts, val_labels = load_train_val_splits(train_path, val_path)
    else:
        texts, labels = load_dataset(data_path or "eval/ground_truth_sw_v5.csv")
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
        metric_for_best_model="eval_f1",
        greater_is_better=True,
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

    # Val metrics for Model Card / CLAUDE
    val_metrics = trainer.evaluate()
    val_f1 = val_metrics.get("eval_f1", 0.0)
    val_precision = val_metrics.get("eval_precision", 0.0)
    val_recall = val_metrics.get("eval_recall", 0.0)
    print(f"\nVal F1: {val_f1:.4f} | P: {val_precision:.4f} | R: {val_recall:.4f}")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    metrics_file = out_path / "val_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(
            {"eval_f1": val_f1, "eval_precision": val_precision, "eval_recall": val_recall},
            f,
            indent=2,
        )
    print(f"Val metrics saved to {metrics_file}")
    print(f"\nModel saved to {output_dir}")
    print("Next: push to HuggingFace Hub and set JUAKAZI_ML_MODEL env var")
    print(f"  huggingface-cli login")
    print(f"  python3 -c \"from transformers import AutoModelForSequenceClassification; m=AutoModelForSequenceClassification.from_pretrained('{output_dir}'); m.push_to_hub('juakazike/sw-bias-classifier-v1')\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train afro-xlmr-base for bias detection. Use --use-splits with stratified splits (see docs/STRATIFIED_SPLIT.md)."
    )
    parser.add_argument("--data", default="eval/ground_truth_sw_v5.csv", help="Single CSV (used if --use-splits not set)")
    parser.add_argument("--output", default="models/sw_bias_classifier_v1")
    parser.add_argument("--epochs", type=int, default=5, help="Default 5 for better val F1 (MASTER_PLAN)")
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument(
        "--use-splits",
        action="store_true",
        help="Use eval/results/splits/{lang}_train.csv and _val.csv (run scripts/stratified_split.py first)",
    )
    parser.add_argument("--language", "-l", default="sw", choices=("en", "sw", "fr", "ki"))
    parser.add_argument("--splits-dir", default="eval/results/splits", help="Dir with {lang}_train.csv, {lang}_val.csv")
    args = parser.parse_args()

    train_path = val_path = None
    if args.use_splits:
        splits_dir = Path(args.splits_dir)
        train_path = str(splits_dir / f"{args.language}_train.csv")
        val_path = str(splits_dir / f"{args.language}_val.csv")
        if not Path(train_path).exists() or not Path(val_path).exists():
            raise SystemExit(
                f"Split files not found. Run: python3 scripts/stratified_split.py --language {args.language}"
            )

    train(
        data_path=args.data if not args.use_splits else None,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch,
        train_path=train_path,
        val_path=val_path,
    )
