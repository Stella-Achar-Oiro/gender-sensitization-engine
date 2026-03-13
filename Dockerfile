FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and setup.py for installation
COPY pyproject.toml setup.py ./
COPY ml ./ml
COPY eval ./eval
COPY api ./api
COPY ui ./ui
COPY scripts ./scripts
COPY rules ./rules

# Install package in development mode
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir pytest pytest-cov black ruff

# Copy remaining application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV JUAKAZI_ML_MODEL=juakazike/sw-bias-classifier-v2
ENV JUAKAZI_ML_THRESHOLD=0.56
# Cache model at build time so first request is fast
ENV HF_HOME=/app/.hf_cache
RUN python3 -c "from transformers import pipeline; pipeline('text-classification', model='juakazike/sw-bias-classifier-v2', device=-1)"

# Create necessary directories
RUN mkdir -p audit_logs data/raw data/cache models/bias_detector reports

# Expose ports
EXPOSE 8000 8501

# Default command runs tests to verify installation
CMD ["pytest", "tests/", "-v", "-k", "not slow"]