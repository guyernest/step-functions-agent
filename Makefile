# Makefile for Step Functions AI Agent project

# Environment variables
PYTHON := python3
UV := uv
NPM := npm
CARGO := cargo
MVN := mvn
GO := go

# Directories
LAMBDA_DIR := lambda
TOOLS_DIR := $(LAMBDA_DIR)/tools
CALL_LLM_DIR := $(LAMBDA_DIR)/call_llm
TEST_DIR := tests

# Python tools directories
PYTHON_TOOLS := $(TOOLS_DIR)/code-interpreter $(TOOLS_DIR)/db-interface $(TOOLS_DIR)/graphql-interface $(TOOLS_DIR)/cloudwatch-queries

# TypeScript tools directories
TS_TOOLS := $(TOOLS_DIR)/google-maps

# Rust tools directories
RUST_TOOLS := $(TOOLS_DIR)/rust-clustering

# Java tools directories
JAVA_TOOLS := $(TOOLS_DIR)/stock-analyzer

# Go tools directories
GO_TOOLS := $(TOOLS_DIR)/web-research $(TOOLS_DIR)/web-scraper

.PHONY: all clean setup test build deploy-prep help

# Default target
all: clean setup build test

# Help target
help:
	@echo "Step Functions AI Agent Framework - Makefile Help"
	@echo "================================================="
	@echo ""
	@echo "Main targets:"
	@echo "  help           - Display this help message"
	@echo "  all            - Run all steps (clean, setup, build, test)"
	@echo "  setup          - Set up all environments and create .env file"
	@echo "  build          - Build all lambda functions"
	@echo "  test           - Run tests for all components"
	@echo "  venv           - Create Python virtual environment with uv"
	@echo "  install-call-llm - Install call_llm dependencies with uv"
	@echo "  test-call-llm  - Run call_llm tests with proper environment (uses .env file)"
	@echo "  test-robustness- Run only the robustness improvement tests"
	@echo "  clean          - Clean build artifacts and temporary files"
	@echo "  clean-venv     - Clean and recreate virtual environment"
	@echo "  deploy-prep    - Prepare for deployment (clean, setup, build, test)"
	@echo "  populate-llm-models - Populate LLM Models DynamoDB table with provider data"
	@echo ""
	@echo "Language-specific targets:"
	@echo "  setup-python      - Set up Python environment"
	@echo "  setup-node        - Set up Node.js environment"
	@echo "  setup-rust        - Set up Rust environment"
	@echo "  setup-java        - Set up Java environment"
	@echo "  setup-go          - Set up Go environment"
	@echo ""
	@echo "  build-python      - Build Python lambda functions"
	@echo "  build-typescript  - Build TypeScript lambda functions"
	@echo "  build-rust        - Build Rust lambda functions"
	@echo "  build-java        - Build Java lambda functions"
	@echo "  build-go          - Build Go lambda functions"
	@echo ""
	@echo "  test-python       - Run Python tests"
	@echo "  test-typescript   - Run TypeScript tests"
	@echo "  test-rust         - Run Rust tests"
	@echo "  test-java         - Run Java tests"
	@echo "  test-go           - Run Go tests"
	@echo ""
	@echo "After running deploy-prep, use 'cdk deploy' to deploy the stacks"

# Setup virtual environment and dependencies
setup: setup-env setup-python setup-node setup-rust setup-java setup-go

setup-env:
	@echo "Setting up .env file..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "ANTHROPIC_API_KEY=your_anthropic_api_key" > .env; \
		echo "OPENAI_API_KEY=your_openai_api_key" >> .env; \
		echo "AI21_API_KEY=your_ai21_api_key" >> .env; \
		echo "GEMINI_API_KEY=your_gemini_api_key" >> .env; \
		echo "Please update .env with your actual API keys"; \
	fi

setup-python:
	@echo "Setting up Python environment..."
	$(UV) venv
	. .venv/bin/activate && \
	for dir in $(PYTHON_TOOLS); do \
		if [ -f $$dir/requirements.in ]; then \
			echo "Building requirements for $$dir..."; \
			$(UV) pip compile $$dir/requirements.in --output-file $$dir/requirements.txt; \
		fi \
	done

setup-node:
	@echo "Setting up Node.js environment..."
	for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Installing dependencies for $$dir..."; \
			cd $$dir && $(NPM) install && cd -; \
		fi \
	done

setup-rust:
	@echo "Setting up Rust environment..."
	for dir in $(RUST_TOOLS); do \
		if [ -f $$dir/Cargo.toml ]; then \
			echo "Building Rust project in $$dir..."; \
			cd $$dir && $(CARGO) build && cd -; \
		fi \
	done

setup-java:
	@echo "Setting up Java environment..."
	for dir in $(JAVA_TOOLS); do \
		if [ -f $$dir/pom.xml ]; then \
			echo "Building Java project in $$dir..."; \
			cd $$dir && $(MVN) install && cd -; \
		fi \
	done

setup-go:
	@echo "Setting up Go environment..."
	for dir in $(GO_TOOLS); do \
		if [ -f $$dir/go.mod ]; then \
			echo "Building Go project in $$dir..."; \
			cd $$dir && $(GO) mod tidy && $(GO) build && cd -; \
		fi \
	done

# Build all lambda functions
build: build-python build-typescript build-rust build-java build-go

build-python:
	@echo "Building Python lambda functions..."
	for dir in $(PYTHON_TOOLS); do \
		echo "Building $$dir..."; \
		cd $$dir && $(UV) pip install -r requirements.txt && cd -; \
	done

build-typescript:
	@echo "Building TypeScript lambda functions..."
	for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Building $$dir..."; \
			cd $$dir && $(NPM) run build && cd -; \
		fi \
	done

build-rust:
	@echo "Building Rust lambda functions..."
	for dir in $(RUST_TOOLS); do \
		if [ -f $$dir/Cargo.toml ]; then \
			echo "Building $$dir..."; \
			cd $$dir && $(CARGO) build --release && cd -; \
		fi \
	done

build-java:
	@echo "Building Java lambda functions..."
	for dir in $(JAVA_TOOLS); do \
		if [ -f $$dir/pom.xml ]; then \
			echo "Building $$dir..."; \
			cd $$dir && $(MVN) package && cd -; \
		fi \
	done

build-go:
	@echo "Building Go lambda functions..."
	for dir in $(GO_TOOLS); do \
		if [ -f $$dir/go.mod ]; then \
			echo "Building $$dir..."; \
			cd $$dir && $(GO) build && cd -; \
		fi \
	done

# Run tests
test: test-python test-typescript test-rust test-java test-go test-call-llm

test-python:
	@echo "Running Python tests..."
	for dir in $(PYTHON_TOOLS); do \
		if [ -d $$dir/tests ]; then \
			echo "Testing $$dir..."; \
			cd $$dir && python -m pytest tests/ && cd -; \
		fi \
	done

# Virtual environment setup
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(shell pwd)/$(VENV)/bin/python
VENV_PIP := $(VENV_BIN)/pip
UV := uv

# Create and setup virtual environment with uv
venv:
	@echo "Creating Python virtual environment with uv..."
	@$(UV) venv $(VENV) --python 3.12
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Install call_llm dependencies
install-call-llm: venv
	@echo "Installing call_llm dependencies with uv..."
	@cd $(CALL_LLM_DIR) && \
		$(UV) pip compile --python $(VENV_PYTHON) requirements.in -o requirements.txt && \
		$(UV) pip compile --python $(VENV_PYTHON) requirements-dev.in -o requirements-dev.txt && \
		$(UV) pip sync --python $(VENV_PYTHON) requirements-dev.txt

# Test call_llm with proper environment setup
test-call-llm: install-call-llm
	@echo "Running call_llm tests with environment setup..."
	@. $(VENV_BIN)/activate && \
		export AWS_PROFILE=CGI-PoC && \
		export USE_ENV_KEYS=true && \
		echo "Python version: $$(python --version)" && \
		echo "AWS Profile: $$AWS_PROFILE" && \
		cd $(CALL_LLM_DIR) && \
		python -m pytest tests/ --ignore=tests/test_gemini_handler.py -v

# Test only the robustness improvements
test-robustness: install-call-llm
	@echo "Running robustness improvement tests..."
	@. $(VENV_BIN)/activate && \
		export AWS_PROFILE=CGI-PoC && \
		export USE_ENV_KEYS=true && \
		cd $(CALL_LLM_DIR) && \
		python -m pytest tests/test_robustness_improvements.py -v

test-typescript:
	@echo "Running TypeScript tests..."
	for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			echo "Testing $$dir..."; \
			cd $$dir && $(NPM) test && cd -; \
		fi \
	done

test-rust:
	@echo "Running Rust tests..."
	for dir in $(RUST_TOOLS); do \
		if [ -f $$dir/Cargo.toml ]; then \
			echo "Testing $$dir..."; \
			cd $$dir && $(CARGO) test && cd -; \
		fi \
	done

test-java:
	@echo "Running Java tests..."
	for dir in $(JAVA_TOOLS); do \
		if [ -f $$dir/pom.xml ]; then \
			echo "Testing $$dir..."; \
			cd $$dir && $(MVN) test && cd -; \
		fi \
	done

test-go:
	@echo "Running Go tests..."
	for dir in $(GO_TOOLS); do \
		if [ -f $$dir/go.mod ]; then \
			echo "Testing $$dir..."; \
			cd $$dir && $(GO) test ./... && cd -; \
		fi \
	done

# Clean build artifacts and temporary files
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "target" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".venv" -exec rm -rf {} +

# Clean and recreate virtual environment
clean-venv:
	@echo "Cleaning virtual environment..."
	@rm -rf $(VENV)
	@make venv

# Prepare for deployment
deploy-prep: clean setup build test
	@echo "Ready for deployment. Run 'cdk deploy' to deploy the stacks."

# Populate LLM Models table
populate-llm-models:
	@echo "Populating LLM Models table..."
	@$(PYTHON) scripts/populate_llm_models.py
