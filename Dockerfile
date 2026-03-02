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

# Create necessary directories
RUN mkdir -p audit_logs data/raw data/cache models/bias_detector reports

# Expose ports
EXPOSE 8000 8501

# Default command runs tests to verify installation
CMD ["pytest", "tests/", "-v", "-k", "not slow"]