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

# Stage 2: Install Python deps
FROM python:3.11-slim AS python-builder
RUN pip install uv
WORKDIR /build
COPY requirements.txt .
# Install without the torch CPU extra-index-url (use standard torch for container)
RUN grep -v "extra-index-url" requirements.txt > requirements_docker.txt && \
    sed -i 's/torch==2\.2\.2+cpu/torch==2.2.2/g' requirements_docker.txt && \
    uv pip install --target /venv -r requirements_docker.txt \
      --extra-index-url https://download.pytorch.org/whl/cpu || \
    pip install --target /venv -r requirements_docker.txt

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
