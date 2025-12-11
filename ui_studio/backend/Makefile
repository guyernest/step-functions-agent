# Navigation Studio Backend Makefile

.PHONY: setup install dev run test clean lint

# Python settings
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# Default port
PORT ?= 8765
HOST ?= 127.0.0.1

# Setup virtual environment and install dependencies
setup: $(VENV)/bin/activate

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PYTHON_VENV) -m playwright install chromium
	@echo "Virtual environment created at $(VENV)"
	@echo "Run 'source $(VENV)/bin/activate' to activate"

# Install dependencies (assumes venv is active)
install:
	pip install -r requirements.txt
	python -m playwright install chromium

# Run development server with hot reload
dev: setup
	$(PYTHON_VENV) -m uvicorn main:app --reload --host $(HOST) --port $(PORT)

# Run production server
run: setup
	$(PYTHON_VENV) -m uvicorn main:app --host $(HOST) --port $(PORT)

# Run tests
test: setup
	$(PYTHON_VENV) -m pytest tests/ -v

# Clean up
clean:
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Lint code
lint: setup
	$(PYTHON_VENV) -m flake8 *.py --max-line-length=100

# Show help
help:
	@echo "Navigation Studio Backend"
	@echo ""
	@echo "Available targets:"
	@echo "  setup   - Create virtual environment and install dependencies"
	@echo "  install - Install dependencies (when venv is active)"
	@echo "  dev     - Run development server with hot reload"
	@echo "  run     - Run production server"
	@echo "  test    - Run tests"
	@echo "  clean   - Remove virtual environment and cache files"
	@echo "  lint    - Lint code with flake8"
	@echo ""
	@echo "Environment variables:"
	@echo "  PORT    - Server port (default: 8765)"
	@echo "  HOST    - Server host (default: 127.0.0.1)"
