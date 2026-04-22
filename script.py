import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm

# Load model + tokenizer
model_name = "juakazike/sw-bias-classifier-v3"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


df = pd.read_csv("test.csv")

texts = df["text"].astype(str).tolist()


batch_size = 32
pred_labels = []
pred_scores = []

print("Prediction started...")

for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i+batch_size]

    inputs = tokenizer(
        batch,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)

    scores, labels = torch.max(probs, dim=1)

    pred_labels.extend(labels.cpu().numpy())
    pred_scores.extend(scores.cpu().numpy())

# Map label IDs to actual labels
id2label = model.config.id2label
df["predicted_bias"] = [id2label[int(x)] for x in pred_labels]
df["confidence"] = pred_scores


final_columns = [
    "id",
    "text",
    "bias_label",
    "has_bias",
    "bias_category",
    "predicted_bias",
    "confidence"
]
df = df[final_columns]
df.to_csv("predictions.csv", index=False)

print("Done!")