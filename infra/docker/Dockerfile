# syntax=docker/dockerfile:1
# Stage 1: Build Next.js static export
FROM node:20-alpine AS node-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Install Python deps + pre-download HF models
FROM python:3.11-slim AS python-builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --target /venv -r requirements.txt
# Pre-download SW classifier so cold start is fast
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
AutoTokenizer.from_pretrained('juakazike/sw-bias-classifier-v3'); \
AutoModelForSequenceClassification.from_pretrained('juakazike/sw-bias-classifier-v3')" \
  || echo "Model pre-download skipped (will download on first request)"

# Stage 3: Runtime (non-root)
FROM python:3.11-slim
COPY --from=python-builder /venv /venv
ENV PYTHONPATH=/venv
WORKDIR /app
COPY api/ api/
COPY eval/ eval/
COPY rules/ rules/
COPY config.py .
COPY --from=node-builder /frontend/out ./static
RUN useradd -m juakazi && chown -R juakazi /app
USER juakazi
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
