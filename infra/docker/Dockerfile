# syntax=docker/dockerfile:1
# Stage 1: Build Next.js static export
FROM node:20-alpine AS node-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=/
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Install Python deps with uv
FROM python:3.11-slim AS python-builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /build
COPY requirements_docker.txt .
RUN uv pip install --system --no-cache -r requirements_docker.txt

# Stage 3: Download model weights into image so startup is instant
FROM python:3.11-slim AS model-downloader
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin
RUN python3 -c "from transformers import pipeline; pipeline('text-classification', model='juakazike/multilingual-bias-classifier-v1', device=-1, truncation=True, max_length=128)"

# Stage 4: Runtime (non-root)
FROM python:3.11-slim
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin
COPY --from=model-downloader /root/.cache/huggingface /root/.cache/huggingface
WORKDIR /app
COPY api/ api/
COPY eval/ eval/
COPY core/ core/
COPY rules/ rules/
COPY config.py .
COPY --from=node-builder /frontend/out ./static
RUN useradd -m juakazi && chown -R juakazi /app && chown -R juakazi /root/.cache/huggingface
USER juakazi
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
