# JuaKazi Development Makefile
# Docker-first approach for consistency and reproducibility

.PHONY: build build-fresh up down logs shell clean-docker \
	test eval train compare collect verify-week2 \
	dev-test dev-eval dev-ui format lint clean help

# Default target - show help
.DEFAULT_GOAL := help

# Help command
help:
	@echo "JuaKazi Gender Sensitization Engine - Make Commands"
	@echo ""
	@echo "Primary Commands (Docker - Recommended):"
	@echo "  make build            Build Docker image (with cache)"
	@echo "  make build-fresh      Build Docker image (no cache, clean build)"
	@echo "  make test             Run all tests (192 tests)"
	@echo "  make eval             Run F1 evaluation across all languages"
	@echo "  make up               Start API (:8000) + UI (:8501) services"
	@echo "  make down             Stop all services"
	@echo "  make logs             View service logs (follow mode)"
	@echo "  make shell            Open bash shell in container"
	@echo ""
	@echo "Week 2 ML Workflows (Docker):"
	@echo "  make train            Train ML model (all languages, 2 epochs)"
	@echo "  make compare          Compare models (rules vs ML vs hybrid)"
	@echo "  make collect          Show data collection sources"
	@echo "  make verify-week2     Verify complete Week 2 workflow"
	@echo ""
	@echo "Quick Local Dev (Optional - for fast iteration):"
	@echo "  make dev-test         Run tests locally (requires local setup)"
	@echo "  make dev-eval         Run evaluation locally"
	@echo "  make dev-ui           Launch testing UI (Streamlit)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Run flake8 linter"
	@echo "  make clean            Remove cache files"
	@echo "  make clean-docker     Clean up Docker resources"
	@echo ""

# ============================================================================
# PRIMARY COMMANDS (Docker-based - Recommended)
# ============================================================================

# Build Docker image
build:
	@echo "Building Docker image with cache..."
	docker-compose build

build-fresh:
	@echo "Building Docker image (no cache, clean build)..."
	docker-compose build --no-cache

# Run tests (192 tests)
test:
	@echo "Running all tests in Docker (192 tests)..."
	docker-compose run test

# Run evaluation
eval:
	@echo "Running F1 evaluation across all languages..."
	docker-compose run test python3 run_evaluation.py

# Service management
up:
	@echo "Starting API (:8000) and UI (:8501) services..."
	docker-compose up -d api ui

down:
	@echo "Stopping all services..."
	docker-compose down

logs:
	@echo "Showing logs (API + UI)..."
	docker-compose logs -f api ui

shell:
	@echo "Opening bash shell in container..."
	docker-compose run api bash

# ============================================================================
# WEEK 2 ML WORKFLOWS (Docker)
# ============================================================================

train:
	@echo "Training ML model (all languages, 2 epochs)..."
	docker-compose run train

train-custom:
	@echo "Training with custom parameters..."
	@echo "Usage: docker-compose run train python3 train_ml_model.py --language en --epochs 5 --evaluate"
	docker-compose run train python3 train_ml_model.py --help

compare:
	@echo "Comparing models (rules vs ML vs hybrid)..."
	docker-compose run compare

collect:
	@echo "Data collection sources..."
	docker-compose run collect

collect-ground-truth:
	@echo "Collecting ground truth data (English, 100 items)..."
	docker-compose run collect python3 scripts/data_collection/cli.py collect ground-truth --language en --max-items 100

verify-week2:
	@echo "Verifying complete Week 2 workflow..."
	@echo ""
	@echo "Step 1/6: Building Docker image..."
	docker-compose build
	@echo ""
	@echo "Step 2/6: Running tests..."
	docker-compose run test
	@echo ""
	@echo "Step 3/6: Listing data sources..."
	docker-compose run collect python3 scripts/data_collection/cli.py list-sources
	@echo ""
	@echo "Step 4/6: Collecting sample data (English, 20 items)..."
	docker-compose run collect python3 scripts/data_collection/cli.py collect ground-truth --language en --max-items 20
	@echo ""
	@echo "Step 5/6: Training model (English, 2 epochs)..."
	docker-compose run train python3 train_ml_model.py --language en --epochs 2 --evaluate
	@echo ""
	@echo "Step 6/6: Comparing models..."
	docker-compose run compare python3 compare_models.py --all-languages
	@echo ""
	@echo "✅ Week 2 verification complete!"

# ============================================================================
# QUICK LOCAL DEV (Optional - for fast iteration during development)
# ============================================================================

dev-test:
	@echo "Running tests locally (requires local Python setup)..."
	python3 -m pytest tests/ -v -k "not slow"

dev-eval:
	@echo "Running evaluation locally..."
	python3 run_evaluation.py

dev-ui:
	@echo "Launching JuaKazi Testing UI..."
	@echo "Opening browser at http://localhost:8501"
	./venv/bin/streamlit run ui/app.py

# ============================================================================
# CODE QUALITY & CLEANUP
# ============================================================================

clean:
	@echo "Cleaning cache files..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

clean-docker:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f

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