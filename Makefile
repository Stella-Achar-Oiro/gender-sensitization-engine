# JuaKazi Development Makefile

.PHONY: setup install test run clean docker-build docker-run

# Setup development environment
setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

# Install dependencies
install:
	./venv/bin/pip install -r requirements.txt

# Run tests
test:
	/home/achar/juakazi/gender-sensitization-engine/venv/bin/python test_system.py

# Run API server
run-api:
	/home/achar/juakazi/gender-sensitization-engine/venv/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run review UI
run-ui:
	/home/achar/juakazi/gender-sensitization-engine/venv/bin/streamlit run review_ui/app.py --server.port 8501

# Run both services
run: 
	@echo "Starting API on :8000 and UI on :8501"
	./venv/bin/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
	./venv/bin/streamlit run review_ui/app.py --server.port 8501 &

# Clean up
clean:
	rm -rf venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete

# Docker commands
docker-build:
	docker build -t juakazi-engine .

docker-run:
	docker run -p 8000:8000 -p 8501:8501 juakazi-engine

# Development helpers
format:
	./venv/bin/black . --line-length 88
	./venv/bin/isort .

lint:
	./venv/bin/flake8 .

# Quick evaluation
eval:
	./venv/bin/python scripts/compute_metrics.py