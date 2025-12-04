# JuaKazi Development Makefile

.PHONY: setup install install-minimal install-core test validate-lexicons eval eval-correction demo run-api run-ui run clean docker-build docker-run format lint test-api test-demo help

# Default target - show help
.DEFAULT_GOAL := help

# Help command
help:
	@echo "JuaKazi Gender Sensitization Engine - Make Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup            Auto-install poetry (if needed) and all dependencies"
	@echo "  make install          Install all dependencies (API, UI, ML, dev tools)"
	@echo "  make install-minimal  Install API + UI only (no ML dependencies)"
	@echo "  make install-core     Install core only (no optional dependencies)"
	@echo ""
	@echo "Evaluation (No Dependencies Required):"
	@echo "  make validate-lexicons  Validate lexicons for AI BRIDGE compliance"
	@echo "  make eval               Run full F1 evaluation across all languages"
	@echo "  make eval-correction    Run correction effectiveness evaluation"
	@echo "  make demo               Run live demo"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run system tests"
	@echo "  make test-api         Test API endpoints (requires FastAPI)"
	@echo "  make test-demo        Run complete system demo"
	@echo ""
	@echo "Services (Requires Optional Dependencies):"
	@echo "  make run-api          Start FastAPI server on port 8000"
	@echo "  make run-ui           Start Streamlit UI on port 8501"
	@echo "  make run              Start both API and UI services"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run Docker container"
	@echo ""
	@echo "Development:"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Run flake8 linter"
	@echo "  make clean            Remove venv and cache files"
	@echo ""

# Setup development environment
setup:
	@command -v poetry >/dev/null 2>&1 || { echo "Installing poetry..."; pip install poetry; }
	poetry install --with dev --all-extras

# Install dependencies (API, UI, ML, dev tools)
install:
	poetry install --with dev --all-extras

# Install minimal (API + UI only, no ML)
install-minimal:
	poetry install --extras "api ui" --with dev

# Install core only (no optional dependencies)
install-core:
	poetry install --with dev

# Run tests
test:
	poetry run python tests/test_system.py

# Validate lexicons (AI BRIDGE compliance check)
validate-lexicons:
	@echo "Validating lexicons for AI BRIDGE compliance..."
	poetry run python -m eval.lexicon_validator

# Run evaluation
eval:
	poetry run python run_evaluation.py

# Run correction evaluation
eval-correction:
	poetry run python eval/correction_evaluator.py

# Run live demo
demo:
	poetry run python demo_live.py

# Run API server
run-api:
	poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run review UI
run-ui:
	poetry run streamlit run review_ui/app.py --server.port 8501

# Run both services
run:
	@echo "Starting API on :8000 and UI on :8501"
	poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
	poetry run streamlit run review_ui/app.py --server.port 8501 &

# Clean up
clean:
	rm -rf venv/
	rm -rf .venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Docker commands
docker-build:
	docker build -t juakazi-engine .

docker-run:
	docker run -p 8000:8000 -p 8501:8501 juakazi-engine

# Development helpers
format:
	black . --line-length 88
	isort .

lint:
	flake8 .

# Test utilities
test-api:
	poetry run python tests/test_api.py

test-demo:
	poetry run python tests/test_demo.py