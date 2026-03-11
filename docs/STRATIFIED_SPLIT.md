# Stratified split and oversampling for classifier training

For reproducible ML classifier training (bias detection), use the stratified split and BIAS oversampling produced by `scripts/stratified_split.py`. This addresses class imbalance and gives stable validation metrics.

## Quick start

```bash
# From repo root. Requires ground truth CSV in eval/ (e.g. eval/ground_truth_sw_v5.csv).
python scripts/stratified_split.py --language sw
```

Output (default):

- `eval/results/splits/sw_train.csv` — training set (stratified, BIAS oversampled to ~25%)
- `eval/results/splits/sw_val.csv` — validation set (stratified, no oversampling)
- `eval/results/splits/sw_split_summary.json` — counts, ratios, paths

## Why stratified split?

- **Stratified by `has_bias`** so train and val have similar bias/neutral proportions.
- **80/20** train/val by default (`--val-ratio 0.2`).

## Why oversample BIAS in train?

- Ground truth is often imbalanced (e.g. &lt;20% biased). Oversampling biased samples in the **train** set to ~**25%** improves classifier recall on the minority class without touching the validation set.
- Use `--bias-ratio 0.25` (default). The script duplicates biased rows in train until the biased fraction reaches the target.

## Recommended training settings

After generating the split:

- **Epochs:** 5 (plan: *5 epochs recommended*; 3 often underfits).
- **Class weighting:** Use `WeightedTrainer` or equivalent so the loss reflects class imbalance in the **original** distribution if desired; oversampling already helps.
- **Model:** e.g. `Davlan/afro-xlmr-base` for Swahili.
- **Reproducibility:** Use the same `--seed` (default 42) when re-running the split.

## Using the splits in training

- **Option A:** Point your trainer at `eval/results/splits/{lang}_train.csv` and `eval/results/splits/{lang}_val.csv` (same columns as the original ground truth).
- **Option B:** Load full ground truth and filter by indices; the summary JSON records sizes and ratios for sanity checks.

## References

- MASTER_PLAN Phase C: `data/stratified-split-and-docs`, `ml/classifier-retrain`.
- CLAUDE.md: classifier val F1 target 0.82–0.88 with stratified split and 5 epochs.
