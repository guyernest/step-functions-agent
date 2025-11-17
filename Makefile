# Makefile for Step Functions AI Agent project
# ============================================

# Environment variables
PYTHON := python3
UV := uv
NPM := npm
CARGO := cargo
CARGO_LAMBDA := cargo lambda
MVN := mvn
GO := go
CDK := npx cdk

# AWS Configuration
AWS_PROFILE ?= default
AWS_REGION ?= us-west-2
ENV_NAME ?= prod

# Directories
LAMBDA_DIR := lambda
TOOLS_DIR := $(LAMBDA_DIR)/tools
CALL_LLM_DIR := $(LAMBDA_DIR)/call_llm
CALL_LLM_RUST_DIR := $(LAMBDA_DIR)/call_llm_rust
TEST_DIR := tests
UI_DIR := ui_amplify
AGENT_CORE_DIR := agent_core

# Python tools directories
PYTHON_TOOLS := $(TOOLS_DIR)/code-interpreter $(TOOLS_DIR)/db-interface $(TOOLS_DIR)/graphql-interface $(TOOLS_DIR)/cloudwatch-queries

# TypeScript tools directories
TS_TOOLS := $(TOOLS_DIR)/google-maps

# Rust tools directories
RUST_TOOLS := $(TOOLS_DIR)/rust-clustering $(TOOLS_DIR)/local-agent
RUST_LLM := $(CALL_LLM_RUST_DIR)

# Java tools directories
JAVA_TOOLS := $(TOOLS_DIR)/stock-analyzer

# Go tools directories
GO_TOOLS := $(TOOLS_DIR)/web-research $(TOOLS_DIR)/web-scraper

# Virtual environment
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(shell pwd)/$(VENV)/bin/python
VENV_PIP := $(VENV_BIN)/pip

# ============================================
# Default target
# ============================================
.PHONY: all
all: clean setup build test

# ============================================
# Help target - Display available commands
# ============================================
.PHONY: help
help:
	@echo "╔════════════════════════════════════════════════════════════════════╗"
	@echo "║     Step Functions AI Agent Framework - Makefile Commands         ║"
	@echo "╚════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🎯 Main Targets:"
	@echo "  make help              - Display this help message"
	@echo "  make all               - Run clean, setup, build, and test"
	@echo "  make deploy-prep       - Prepare for deployment (clean, setup, build, test)"
	@echo ""
	@echo "🚀 Unified Rust LLM Service:"
	@echo "  make build-llm-rust    - Build the unified Rust LLM service"
	@echo "  make test-llm-rust     - Run unit tests for Rust LLM service"
	@echo "  make test-llm-rust-integration - Run all provider integration tests"
	@echo "  make test-llm-rust-openai     - Test OpenAI tool calling"
	@echo "  make test-llm-rust-anthropic  - Test Anthropic tool calling"
	@echo "  make test-llm-rust-gemini     - Test Gemini tool calling"
	@echo "  make deploy-llm-rust   - Build and prepare Rust LLM for deployment"
	@echo "  make clean-llm-rust    - Clean Rust LLM build artifacts"
	@echo ""
	@echo "🛠️  Setup & Environment:"
	@echo "  make setup             - Set up all environments"
	@echo "  make venv              - Create Python virtual environment"
	@echo "  make setup-env         - Create .env file template"
	@echo "  make install-deps      - Install all dependencies"
	@echo ""
	@echo "🏗️  Build Commands:"
	@echo "  make build             - Build all Lambda functions"
	@echo "  make build-python      - Build Python Lambda functions"
	@echo "  make build-typescript  - Build TypeScript Lambda functions"
	@echo "  make build-rust        - Build all Rust Lambda functions"
	@echo "  make build-java        - Build Java Lambda functions"
	@echo "  make build-go          - Build Go Lambda functions"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test              - Run all tests"
	@echo "  make test-python       - Run Python tests"
	@echo "  make test-typescript   - Run TypeScript tests"
	@echo "  make test-rust         - Run Rust tests"
	@echo "  make test-java         - Run Java tests"
	@echo "  make test-go           - Run Go tests"
	@echo "  make test-call-llm     - Test Python LLM handlers"
	@echo "  make test-robustness   - Run robustness tests"
	@echo ""
	@echo "🔍 Validation:"
	@echo "  make validate-tools    - Check tool name alignment across stacks"
	@echo "  make validate-all      - Run all validation checks"
	@echo ""
	@echo "📊 Database Population:"
	@echo "  make populate-tables   - Populate all configuration tables"
	@echo "  make populate-llm-models - Populate LLM Models table"
	@echo "  make populate-tool-secrets - Populate Tool Secrets table"
	@echo ""
	@echo "🌐 MCP Registry Commands:"
	@echo "  make populate-mcp-registry - Manually populate MCP Registry table"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean             - Clean all build artifacts"
	@echo "  make clean-venv        - Clean and recreate virtual environment"
	@echo "  make clean-cache       - Clean Python cache files"
	@echo ""
	@echo "🚢 Deployment:"
	@echo "  make deploy-all        - Deploy all CDK stacks"
	@echo "  make deploy-tools      - Deploy all tool stacks"
	@echo "  make deploy-agents     - Deploy all agent stacks"
	@echo ""
	@echo "🤖 AgentCore Browser Commands (CDK-based):"
	@echo "  make create-agentcore-ecr-repos      - Create ECR repositories"
	@echo "  make build-agentcore-containers      - Build and push Docker containers to ECR"
	@echo "  make deploy-agentcore-full           - Full deployment (repos + images + CDK)"
	@echo "  make test-agentcore-browser          - Test browser tool invocation"
	@echo "  make logs-agentcore-browser          - View Lambda logs"
	@echo ""
	@echo "📱 UI Commands:"
	@echo "  make ui-build          - Build Amplify UI"
	@echo "  make ui-dev            - Start UI development server"
	@echo "  make ui-deploy         - Deploy UI to Amplify"
	@echo ""
	@echo "🔧 Utilities:"
	@echo "  make logs              - Tail CloudWatch logs for Lambda functions"
	@echo "  make check-deps        - Check if all required tools are installed"
	@echo "  make update-deps       - Update all dependencies to latest versions"
	@echo ""
	@echo "Environment Variables:"
	@echo "  AWS_PROFILE=$(AWS_PROFILE)"
	@echo "  AWS_REGION=$(AWS_REGION)"
	@echo "  ENV_NAME=$(ENV_NAME)"
	@echo ""
	@echo "Examples:"
	@echo "  AWS_PROFILE=prod make deploy-all"
	@echo "  ENV_NAME=dev make build-llm-rust"

# ============================================
# Unified Rust LLM Service Commands
# ============================================
.PHONY: build-llm-rust
build-llm-rust:
	@echo "🦀 Building Unified LLM Service (Rust) with ADOT Observability..."
	@if ! $(CARGO) lambda --version &> /dev/null; then \
		echo "📦 Installing cargo-lambda..."; \
		$(CARGO) install cargo-lambda; \
	fi
	@cd $(CALL_LLM_RUST_DIR) && \
		echo "🧹 Cleaning previous builds..." && \
		rm -rf target/lambda deployment && \
		echo "🔨 Building for Lambda (ARM64)..." && \
		$(CARGO_LAMBDA) build --release --arm64 && \
		echo "📋 Preparing clean deployment package..." && \
		mkdir -p deployment && \
		if [ -f target/lambda/bootstrap/bootstrap ]; then \
			cp target/lambda/bootstrap/bootstrap deployment/bootstrap; \
		elif [ -f target/lambda/bootstrap ]; then \
			cp target/lambda/bootstrap deployment/bootstrap; \
		fi && \
		cp collector.yaml deployment/ && \
		echo "📦 Deployment package size: $$(du -sh deployment | cut -f1)" && \
		echo "✅ Build complete! Clean deployment package at: lambda/call_llm_rust/deployment/"

.PHONY: test-llm-rust
test-llm-rust:
	@echo "🧪 Testing Unified LLM Service (Rust)..."
	@cd $(CALL_LLM_RUST_DIR) && \
		RUST_LOG=debug $(CARGO) test --lib -- --nocapture

.PHONY: verify-llm-rust
verify-llm-rust:
	@echo "🔍 Verifying Rust Lambda build with ADOT observability..."
	@cd $(CALL_LLM_RUST_DIR) && \
		if [ -d deployment ]; then \
			if [ -f deployment/bootstrap ]; then \
				echo "✅ deployment/bootstrap found (size: $$(ls -lh deployment/bootstrap | awk '{print $$5}'))"; \
			else \
				echo "❌ deployment/bootstrap NOT found"; \
				exit 1; \
			fi && \
			if [ -f deployment/collector.yaml ]; then \
				echo "✅ deployment/collector.yaml found for ADOT"; \
			else \
				echo "❌ deployment/collector.yaml NOT found"; \
				exit 1; \
			fi && \
			echo "📦 CDK deployment package:" && \
			ls -la deployment/ | sed 's/^/   /' && \
			echo "📏 Total size: $$(du -sh deployment | cut -f1)" && \
			echo "🚀 Ready for deployment: cdk deploy SharedLLMStack-prod"; \
		else \
			echo "❌ deployment directory NOT found - run: make build-llm-rust"; \
			exit 1; \
		fi
	
.PHONY: test-llm-rust-integration
test-llm-rust-integration:
	@echo "🧪 Running LLM Service Integration Tests..."
	@echo "Checking for API keys..."
	@if [ ! -f $(CALL_LLM_RUST_DIR)/.env ] && [ -z "$$OPENAI_API_KEY" ] && [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "❌ No API keys found. Please set environment variables or create .env file:"; \
		echo "   export OPENAI_API_KEY='sk-...'"; \
		echo "   export ANTHROPIC_API_KEY='sk-ant-...'"; \
		echo "   Or copy lambda/call_llm_rust/.env.example to .env and add keys"; \
		exit 1; \
	fi
	@cd $(CALL_LLM_RUST_DIR) && \
		$(CARGO) test --test service_integration_test test_all_providers -- --ignored --nocapture

.PHONY: test-llm-rust-openai
test-llm-rust-openai:
	@echo "🧪 Testing OpenAI through UnifiedLLMService..."
	@cd $(CALL_LLM_RUST_DIR) && \
		$(CARGO) test --test service_integration_test test_openai_service -- --ignored --nocapture

.PHONY: test-llm-rust-anthropic
test-llm-rust-anthropic:
	@echo "🧪 Testing Anthropic through UnifiedLLMService..."
	@cd $(CALL_LLM_RUST_DIR) && \
		$(CARGO) test --test service_integration_test test_anthropic_service -- --ignored --nocapture

.PHONY: test-llm-rust-gemini
test-llm-rust-gemini:
	@echo "🧪 Testing Gemini through UnifiedLLMService..."
	@cd $(CALL_LLM_RUST_DIR) && \
		$(CARGO) test --test service_integration_test test_gemini_service -- --ignored --nocapture

.PHONY: deploy-llm-rust
deploy-llm-rust: build-llm-rust
	@echo "📦 Preparing Rust LLM service for deployment..."
	@cd $(CALL_LLM_RUST_DIR) && \
		mkdir -p deployment && \
		cp -r target/lambda/unified-llm-service/* deployment/
	@echo "✅ Ready for deployment at $(CALL_LLM_RUST_DIR)/deployment/"
	@echo "Run: make deploy-stack STACK=UnifiedLLMServiceStack-$(ENV_NAME)"

.PHONY: clean-llm-rust
clean-llm-rust:
	@echo "🧹 Cleaning Rust LLM build artifacts..."
	@cd $(CALL_LLM_RUST_DIR) && \
		$(CARGO) clean && \
		rm -rf deployment

# ============================================
# MCP Server Build Commands
# ============================================

MCP_TEMPLATE_DIR := $(HOME)/Development/Xecutive-AI/general-mcp-examples/mcp-template
MCP_SERVERS_DIR := lambda/mcp-servers

.PHONY: build-mcp-reinvent
build-mcp-reinvent:
	@echo "🦀 Building re:Invent MCP server..."
	@cd $(MCP_TEMPLATE_DIR) && \
		$(CARGO_LAMBDA) build --release --arm64 -p reinvent-server
	@echo "📦 Copying bootstrap to lambda directory..."
	@mkdir -p $(MCP_SERVERS_DIR)/reinvent
	@cp $(MCP_TEMPLATE_DIR)/target/lambda/reinvent-server/bootstrap $(MCP_SERVERS_DIR)/reinvent/
	@echo "✅ re:Invent MCP server built and ready for deployment"
	@echo "Deploy with: cdk deploy ReinventMcpStack-prod"

.PHONY: clean-mcp-reinvent
clean-mcp-reinvent:
	@echo "🧹 Cleaning re:Invent MCP server build artifacts..."
	@rm -rf $(MCP_SERVERS_DIR)/reinvent
	@cd $(MCP_TEMPLATE_DIR) && \
		$(CARGO) clean -p reinvent-server

.PHONY: build-mcp-all
build-mcp-all: build-mcp-reinvent
	@echo "✅ All MCP servers built"

.PHONY: clean-mcp-all
clean-mcp-all: clean-mcp-reinvent
	@echo "✅ All MCP server artifacts cleaned"

# ============================================
# Setup Commands
# ============================================
.PHONY: setup
setup: check-deps setup-env setup-python setup-node setup-rust setup-java setup-go

.PHONY: check-deps
check-deps:
	@echo "🔍 Checking required dependencies..."
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "❌ Python not found"; exit 1; }
	@command -v $(UV) >/dev/null 2>&1 || { echo "❌ uv not found. Install with: pip install uv"; exit 1; }
	@command -v $(NPM) >/dev/null 2>&1 || { echo "❌ npm not found"; exit 1; }
	@command -v $(CARGO) >/dev/null 2>&1 || { echo "❌ cargo not found"; exit 1; }
	@command -v $(GO) >/dev/null 2>&1 || { echo "❌ go not found"; exit 1; }
	@echo "✅ All dependencies found!"

.PHONY: setup-env
setup-env:
	@echo "📝 Setting up .env file..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file template..."; \
		echo "# LLM Provider API Keys" > .env; \
		echo "ANTHROPIC_API_KEY=your_anthropic_api_key" >> .env; \
		echo "OPENAI_API_KEY=your_openai_api_key" >> .env; \
		echo "AI21_API_KEY=your_ai21_api_key" >> .env; \
		echo "GEMINI_API_KEY=your_gemini_api_key" >> .env; \
		echo "" >> .env; \
		echo "# AWS Configuration" >> .env; \
		echo "AWS_PROFILE=$(AWS_PROFILE)" >> .env; \
		echo "AWS_REGION=$(AWS_REGION)" >> .env; \
		echo "" >> .env; \
		echo "⚠️  Please update .env with your actual API keys"; \
	else \
		echo "✅ .env file already exists"; \
	fi

.PHONY: setup-python
setup-python:
	@echo "🐍 Setting up Python environment..."
	@$(UV) venv
	@. $(VENV_BIN)/activate && \
	for dir in $(PYTHON_TOOLS); do \
		if [ -f $$dir/requirements.in ]; then \
			echo "  📦 Building requirements for $$dir..."; \
			$(UV) pip compile $$dir/requirements.in --output-file $$dir/requirements.txt; \
		fi \
	done

.PHONY: setup-node
setup-node:
	@echo "📦 Setting up Node.js environment..."
	@for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			echo "  📦 Installing dependencies for $$dir..."; \
			cd $$dir && $(NPM) install && cd -; \
		fi \
	done

.PHONY: setup-rust
setup-rust:
	@echo "🦀 Setting up Rust environment..."
	@for dir in $(RUST_TOOLS) $(RUST_LLM); do \
		if [ -f $$dir/Cargo.toml ]; then \
			echo "  📦 Building Rust project in $$dir..."; \
			cd $$dir && $(CARGO) build && cd -; \
		fi \
	done

.PHONY: setup-java
setup-java:
	@echo "☕ Setting up Java environment..."
	@for dir in $(JAVA_TOOLS); do \
		if [ -f $$dir/pom.xml ]; then \
			echo "  📦 Building Java project in $$dir..."; \
			cd $$dir && $(MVN) install && cd -; \
		fi \
	done

.PHONY: setup-go
setup-go:
	@echo "🐹 Setting up Go environment..."
	@for dir in $(GO_TOOLS); do \
		if [ -f $$dir/go.mod ]; then \
			echo "  📦 Building Go project in $$dir..."; \
			cd $$dir && $(GO) mod tidy && $(GO) build -o bootstrap . && cd -; \
		fi \
	done

# ============================================
# Build Commands
# ============================================
.PHONY: build
build: build-python build-typescript build-rust build-java build-go

.PHONY: build-python
build-python:
	@echo "🐍 Building Python Lambda functions..."
	@for dir in $(PYTHON_TOOLS); do \
		echo "  🔨 Building $$dir..."; \
		cd $$dir && $(UV) pip install -r requirements.txt && cd -; \
	done

.PHONY: build-typescript
build-typescript:
	@echo "📦 Building TypeScript Lambda functions..."
	@for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			echo "  🔨 Building $$dir..."; \
			cd $$dir && $(NPM) run build && cd -; \
		fi \
	done

.PHONY: build-rust
build-rust: build-llm-rust
	@echo "🦀 Building Rust Lambda functions..."
	@for dir in $(RUST_TOOLS); do \
		if [ -f $$dir/Cargo.toml ]; then \
			echo "  🔨 Building $$dir..."; \
			if [ "$$dir" = "$(TOOLS_DIR)/local-agent" ]; then \
				echo "    Using special build for local-agent (Lambda deployment)"; \
				cd $$dir && $(MAKE) all && cd -; \
			else \
				cd $$dir && $(CARGO) build --release && cd -; \
			fi \
		fi \
	done

.PHONY: build-java
build-java:
	@echo "☕ Building Java Lambda functions..."
	@for dir in $(JAVA_TOOLS); do \
		if [ -f $$dir/pom.xml ]; then \
			echo "  🔨 Building $$dir..."; \
			cd $$dir && $(MVN) package && cd -; \
		fi \
	done

.PHONY: build-go
build-go:
	@echo "🐹 Building Go Lambda functions..."
	@for dir in $(GO_TOOLS); do \
		if [ -f $$dir/go.mod ]; then \
			echo "  🔨 Building $$dir..."; \
			cd $$dir && $(GO) build -o bootstrap . && cd -; \
		fi \
	done

# ============================================
# Test Commands
# ============================================
.PHONY: test
test: test-python test-typescript test-rust test-java test-go test-call-llm

.PHONY: test-python
test-python:
	@echo "🧪 Running Python tests..."
	@for dir in $(PYTHON_TOOLS); do \
		if [ -d $$dir/tests ]; then \
			echo "  Testing $$dir..."; \
			cd $$dir && python -m pytest tests/ && cd -; \
		fi \
	done

.PHONY: test-typescript
test-typescript:
	@echo "🧪 Running TypeScript tests..."
	@for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			echo "  Testing $$dir..."; \
			cd $$dir && $(NPM) test && cd -; \
		fi \
	done

.PHONY: test-rust
test-rust: test-llm-rust
	@echo "🧪 Running Rust tests..."
	@for dir in $(RUST_TOOLS); do \
		if [ -f $$dir/Cargo.toml ]; then \
			echo "  Testing $$dir..."; \
			cd $$dir && $(CARGO) test && cd -; \
		fi \
	done

.PHONY: test-java
test-java:
	@echo "🧪 Running Java tests..."
	@for dir in $(JAVA_TOOLS); do \
		if [ -f $$dir/pom.xml ]; then \
			echo "  Testing $$dir..."; \
			cd $$dir && $(MVN) test && cd -; \
		fi \
	done

.PHONY: test-go
test-go:
	@echo "🧪 Running Go tests..."
	@for dir in $(GO_TOOLS); do \
		if [ -f $$dir/go.mod ]; then \
			echo "  Testing $$dir..."; \
			cd $$dir && $(GO) test ./... && cd -; \
		fi \
	done

# ============================================
# Virtual Environment Management
# ============================================
.PHONY: venv
venv:
	@echo "🐍 Creating Python virtual environment with uv..."
	@$(UV) venv $(VENV) --python 3.12
	@echo "✅ Virtual environment created. Activate with: source venv/bin/activate"

.PHONY: install-deps
install-deps: venv
	@echo "📦 Installing all dependencies..."
	@make install-call-llm

.PHONY: install-call-llm
install-call-llm: venv
	@echo "📦 Installing call_llm dependencies with uv..."
	@cd $(CALL_LLM_DIR) && \
		$(UV) pip compile --python $(VENV_PYTHON) requirements.in -o requirements.txt && \
		$(UV) pip compile --python $(VENV_PYTHON) requirements-dev.in -o requirements-dev.txt && \
		$(UV) pip sync --python $(VENV_PYTHON) requirements-dev.txt

.PHONY: test-call-llm
test-call-llm: install-call-llm
	@echo "🧪 Running call_llm tests..."
	@. $(VENV_BIN)/activate && \
		export AWS_PROFILE=$(AWS_PROFILE) && \
		export USE_ENV_KEYS=true && \
		cd $(CALL_LLM_DIR) && \
		python -m pytest tests/ --ignore=tests/test_gemini_handler.py -v

.PHONY: test-robustness
test-robustness: install-call-llm
	@echo "🧪 Running robustness improvement tests..."
	@. $(VENV_BIN)/activate && \
		export AWS_PROFILE=$(AWS_PROFILE) && \
		export USE_ENV_KEYS=true && \
		cd $(CALL_LLM_DIR) && \
		python -m pytest tests/test_robustness_improvements.py -v

# ============================================
# Clean Commands
# ============================================
.PHONY: clean
clean: clean-cache clean-llm-rust
	@echo "🧹 Cleaning build artifacts..."
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "target" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

.PHONY: clean-cache
clean-cache:
	@echo "🧹 Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

.PHONY: clean-venv
clean-venv:
	@echo "🧹 Cleaning virtual environment..."
	@rm -rf $(VENV)
	@make venv

# ============================================
# Validation Commands
# ============================================
.PHONY: validate-tools
validate-tools:
	@echo "🔍 Validating tool name alignment across stacks..."
	@$(PYTHON) scripts/validate_tool_alignment.py

.PHONY: validate-all
validate-all: validate-tools
	@echo "✅ All validations completed"

# ============================================
# Deployment Commands
# ============================================
.PHONY: deploy-prep
deploy-prep: clean setup build test validate-all
	@echo "✅ Ready for deployment!"
	@echo "Run 'make deploy-all' to deploy all stacks"

.PHONY: deploy-all
deploy-all:
	@echo "🚀 Deploying all CDK stacks..."
	@$(CDK) deploy --all --require-approval never --profile $(AWS_PROFILE)

.PHONY: deploy-stack
deploy-stack:
	@if [ -z "$(STACK)" ]; then \
		echo "❌ Please specify STACK=<stack-name>"; \
		exit 1; \
	fi
	@echo "🚀 Deploying $(STACK)..."
	@$(CDK) deploy $(STACK) --require-approval never --profile $(AWS_PROFILE)

.PHONY: deploy-tools
deploy-tools:
	@echo "🚀 Deploying all tool stacks..."
	@$(CDK) deploy "*ToolStack-$(ENV_NAME)" --require-approval never --profile $(AWS_PROFILE)

.PHONY: deploy-agents
deploy-agents:
	@echo "🚀 Deploying all agent stacks..."
	@$(CDK) deploy "*AgentStack-$(ENV_NAME)" --require-approval never --profile $(AWS_PROFILE)

# ============================================
# Database Population Commands
# ============================================
.PHONY: populate-tables
populate-tables: populate-llm-models populate-tool-secrets
	@echo "✅ All tables populated successfully!"

.PHONY: populate-llm-models
populate-llm-models:
	@echo "📊 Populating LLM Models table..."
	@$(PYTHON) scripts/populate_llm_models.py

.PHONY: populate-tool-secrets
populate-tool-secrets:
	@echo "🔐 Populating Tool Secrets table..."
	@$(PYTHON) scripts/populate_tool_secrets.py $(AWS_PROFILE) $(AWS_REGION)

# ============================================
# MCP Registry Commands
# ============================================
.PHONY: populate-mcp-registry
populate-mcp-registry:
	@echo "📊 Populating MCP Registry table..."
	@$(PYTHON) scripts/populate_mcp_registry.py

# ============================================
# Template Registry Commands
# ============================================
TEMPLATE_FILE ?= templates/broadband_availability_bt_wholesale_v1.0.0.json

.PHONY: register-template
register-template:
	@if [ -z "$(TEMPLATE)" ]; then \
		echo "❌ Please specify TEMPLATE=<template-file>"; \
		echo "Example: make register-template TEMPLATE=templates/broadband_availability_bt_wholesale_v1.0.0.json"; \
		exit 1; \
	fi
	@echo "📝 Registering template: $(TEMPLATE)"
	@$(PYTHON) scripts/register_template.py $(TEMPLATE) --env $(ENV_NAME) --profile $(AWS_PROFILE)

.PHONY: update-broadband-template
update-broadband-template:
	@echo "📝 Updating BT Wholesale broadband availability template..."
	@$(PYTHON) scripts/register_template.py \
		templates/broadband_availability_bt_wholesale_v1.0.0.json \
		--env $(ENV_NAME) \
		--profile $(AWS_PROFILE)

.PHONY: deploy-broadband-agent
deploy-broadband-agent: update-broadband-template
	@echo "🚀 Deploying broadband availability agent stack..."
	@$(CDK) deploy BroadbandAvailabilityBtWholesaleStack-$(ENV_NAME) \
		--require-approval never \
		--profile $(AWS_PROFILE)
	@echo "✅ Broadband agent deployed with updated schema!"

# ============================================
# UI Commands
# ============================================
.PHONY: ui-build
ui-build:
	@echo "🎨 Building Amplify UI..."
	@cd $(UI_DIR) && npm run build

.PHONY: ui-dev
ui-dev:
	@echo "🎨 Starting UI development server..."
	@cd $(UI_DIR) && npm run dev

.PHONY: ui-deploy
ui-deploy: ui-build
	@echo "🚀 Deploying UI to Amplify..."
	@cd $(UI_DIR) && npx amplify push --yes

# ============================================
# Utility Commands
# ============================================
.PHONY: logs
logs:
	@if [ -z "$(FUNCTION)" ]; then \
		echo "❌ Please specify FUNCTION=<function-name>"; \
		echo "Example: make logs FUNCTION=unified-llm-service-prod"; \
		exit 1; \
	fi
	@echo "📋 Tailing logs for $(FUNCTION)..."
	@aws logs tail /aws/lambda/$(FUNCTION) --follow --profile $(AWS_PROFILE)

.PHONY: update-deps
update-deps:
	@echo "🔄 Updating all dependencies..."
	@echo "  Updating Python dependencies..."
	@for dir in $(PYTHON_TOOLS); do \
		if [ -f $$dir/requirements.in ]; then \
			cd $$dir && $(UV) pip compile --upgrade requirements.in -o requirements.txt && cd -; \
		fi \
	done
	@echo "  Updating Node.js dependencies..."
	@for dir in $(TS_TOOLS); do \
		if [ -f $$dir/package.json ]; then \
			cd $$dir && $(NPM) update && cd -; \
		fi \
	done
	@echo "  Updating Rust dependencies..."
	@for dir in $(RUST_TOOLS) $(RUST_LLM); do \
		if [ -f $$dir/Cargo.toml ]; then \
			cd $$dir && $(CARGO) update && cd -; \
		fi \
	done
	@echo "✅ All dependencies updated!"

# Keep backward compatibility
.PHONY: install
install: install-deps

.PHONY: format
format:
	@echo "🎨 Formatting code..."
	@echo "  Formatting Python code..."
	@find . -name "*.py" -type f -exec black {} \;
	@echo "  Formatting Rust code..."
	@for dir in $(RUST_TOOLS) $(RUST_LLM); do \
		if [ -f $$dir/Cargo.toml ]; then \
			cd $$dir && $(CARGO) fmt && cd -; \
		fi \
	done
	@echo "✅ Code formatted!"

# ============================================
# Agent Core Commands (NEW Service - Bedrock Agent Core)
# ============================================
AGENTCORE_DIR := agent_core
AGENTCORE_NAME ?= web-search-agent

# Legacy Agent Commands (OLD Service - Bedrock Agents)
# ============================================
# Agent Core deployment has been moved to a separate project
# See ~/projects/nova-act for Agent Core agent implementations
AGENT_NAME ?= web-search-agent

# ============================================
# Agent Core targets have been moved to ~/projects/nova-act
# The Lambda tools that call Agent Core runtime remain in this project
# ============================================

# Commented out Agent Core deployment targets - now in ~/projects/nova-act
# All the Agent Core deployment, testing, and management targets have been removed
# from this Makefile as they are now in the dedicated nova-act project.
# 
# The following targets have been removed:
#   - deploy-agent-core
#   - deploy-agent-wrapper  
#   - agentcore-broadband-*
#   - deploy-agent-full
#   - list-agent-core
#   - delete-agent-core
#   - clean-agent-core
#   - test-agent-core
#
# This project still maintains:
#   - Lambda tools that call Agent Core runtime (agentcore_browser)
#   - CDK stacks for those tools
#   - Agent stacks that use those tools

: <<'AGENT_CORE_REMOVED'
	@echo "🚀 Deploying Agent Core agent from $(CONFIG)..."
	@echo "📍 Using AWS Profile: $(AWS_PROFILE), Region: $(AWS_REGION)"
	@NOVA_ACT_ARN=$$(aws cloudformation describe-stacks \
		--stack-name "NovaActBrowserToolStack-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		$${AWS_PROFILE:+--profile "$$AWS_PROFILE"} \
		--query "Stacks[0].Outputs[?OutputKey=='NovaActBrowserFunctionArn'].OutputValue" \
		--output text 2>/dev/null); \
	if [ -z "$$NOVA_ACT_ARN" ]; then \
		echo "❌ Nova Act Browser stack not found. Deploy it first:"; \
		echo "  make deploy-stack STACK=NovaActBrowserToolStack-$(ENV_NAME)"; \
		exit 1; \
	fi; \
	echo "✅ Found Nova Act Browser Lambda: $$NOVA_ACT_ARN"; \
	sed "s|\$${NOVA_ACT_BROWSER_LAMBDA_ARN}|$$NOVA_ACT_ARN|g" \
		"$(AGENT_CORE_CONFIGS)/$(CONFIG)" > "/tmp/agent-config-temp.yaml"; \
	if $(PYTHON) $(AGENT_CORE_DIR)/deploy_agent.py \
		"/tmp/agent-config-temp.yaml" \
		--region $(AWS_REGION) \
		$${AWS_PROFILE:+--profile "$$AWS_PROFILE"}; then \
		rm -f "/tmp/agent-config-temp.yaml"; \
		echo "✅ Agent Core deployment complete!"; \
	else \
		rm -f "/tmp/agent-config-temp.yaml"; \
		echo "❌ Agent Core deployment failed!"; \
		exit 1; \
	fi

.PHONY: deploy-agent-wrapper
deploy-agent-wrapper:
	@if [ -z "$(AGENT)" ]; then \
		echo "❌ Please specify AGENT=<agent-name>"; \
		echo "Example: make deploy-agent-wrapper AGENT=web-search-agent"; \
		exit 1; \
	fi
	@echo "🚀 Deploying Step Functions wrapper for $(AGENT)..."
	@if [ ! -f "agent-core-output-$(AGENT).json" ]; then \
		echo "❌ Agent Core output file not found: agent-core-output-$(AGENT).json"; \
		echo "Run 'make deploy-agent-core CONFIG=<config>' first"; \
		exit 1; \
	fi; \
	echo "#!/usr/bin/env python3" > /tmp/agent-wrapper-app.py; \
	echo "import os" >> /tmp/agent-wrapper-app.py; \
	echo "import aws_cdk as cdk" >> /tmp/agent-wrapper-app.py; \
	echo "from stacks.agents.agent_core_wrapper_stack import AgentCoreWrapperStack" >> /tmp/agent-wrapper-app.py; \
	echo "" >> /tmp/agent-wrapper-app.py; \
	echo "app = cdk.App()" >> /tmp/agent-wrapper-app.py; \
	echo "env = cdk.Environment(" >> /tmp/agent-wrapper-app.py; \
	echo "    account=os.environ.get('CDK_DEFAULT_ACCOUNT')," >> /tmp/agent-wrapper-app.py; \
	echo "    region='$(AWS_REGION)'" >> /tmp/agent-wrapper-app.py; \
	echo ")" >> /tmp/agent-wrapper-app.py; \
	echo "" >> /tmp/agent-wrapper-app.py; \
	echo "wrapper_stack = AgentCoreWrapperStack.from_deployment_output(" >> /tmp/agent-wrapper-app.py; \
	echo "    app," >> /tmp/agent-wrapper-app.py; \
	echo "    'AgentCoreWrapper-$(AGENT)-$(ENV_NAME)'," >> /tmp/agent-wrapper-app.py; \
	echo "    output_file='agent-core-output-$(AGENT).json'," >> /tmp/agent-wrapper-app.py; \
	echo "    env_name='$(ENV_NAME)'," >> /tmp/agent-wrapper-app.py; \
	echo "    env=env" >> /tmp/agent-wrapper-app.py; \
	echo ")" >> /tmp/agent-wrapper-app.py; \
	echo "app.synth()" >> /tmp/agent-wrapper-app.py; \
	CDK_APP="python3 /tmp/agent-wrapper-app.py" $(CDK) deploy \
		"AgentCoreWrapper-$(AGENT)-$(ENV_NAME)" \
		--require-approval never \
		--profile $(AWS_PROFILE); \
	rm -f /tmp/agent-wrapper-app.py; \
	echo "✅ Wrapper deployment complete!"

# ============================================
# Agent Core - Broadband Checker Deployment
# ============================================
.PHONY: agentcore-broadband-build
agentcore-broadband-build:
	@echo "🔨 Building Broadband Checker Agent Docker image..."
	@docker build -f $(AGENT_CORE_DIR)/Dockerfile.broadband \
		-t broadband-checker-agent:latest \
		$(AGENT_CORE_DIR) && \
		echo "✅ Docker image built: broadband-checker-agent:latest"

.PHONY: agentcore-broadband-test-local
agentcore-broadband-test-local: agentcore-broadband-build
	@echo "🧪 Testing Broadband Checker Agent locally..."
	@docker run --rm \
		-e AWS_REGION=$(AWS_REGION) \
		-e BYPASS_TOOL_CONSENT=true \
		broadband-checker-agent:latest \
		python -c "import json; from broadband_checker_agent import handler; \
		result = handler({'test': True}, {}); \
		print('Test Result:'); print(json.dumps(result, indent=2)[:500])"

.PHONY: agentcore-broadband-deploy-lambda
agentcore-broadband-deploy-lambda:
	@echo "🚀 Deploying Broadband Checker as Lambda function..."
	@cd $(AGENT_CORE_DIR) && \
		python3 deploy_broadband_agent.py \
			--agent-name broadband-checker \
			--region $(AWS_REGION) \
			--deployment-type lambda \
			--test

.PHONY: agentcore-broadband-configure
agentcore-broadband-configure:
	@echo "⚙️  Configuring Broadband Checker Agent..."
	@cd $(AGENT_CORE_DIR) && \
		source ../venv/bin/activate && \
		agentcore configure -e broadband_checker_agent.py && \
		echo "✅ Agent configured successfully"

.PHONY: agentcore-broadband-deploy-agentcore
agentcore-broadband-deploy-agentcore: agentcore-broadband-configure
	@echo "🚀 Deploying Broadband Checker to Agent Core runtime using agentcore CLI..."
	@cd $(AGENT_CORE_DIR) && \
		source ../venv/bin/activate && \
		agentcore launch --agent broadband_checker_agent && \
		echo "✅ Agent deployed successfully"

.PHONY: agentcore-broadband-test-deployed
agentcore-broadband-test-deployed:
	@echo "🧪 Testing deployed Broadband Checker Agent..."
	@cd $(AGENT_CORE_DIR) && \
		source ../venv/bin/activate && \
		agentcore invoke broadband_checker_agent '{"test": true}' && \
		echo "✅ Test completed"

.PHONY: agentcore-broadband-logs
agentcore-broadband-logs:
	@echo "📋 Viewing Broadband Checker Agent logs (full)..."
	@aws logs tail /aws/agentcore/runtimes/broadband_checker_agent-KcXxkNFCkG-DEFAULT \
		--profile $(AWS_PROFILE) \
		--region $(AWS_REGION) \
		--follow

.PHONY: agentcore-broadband-logs-body
agentcore-broadband-logs-body:
	@echo "📋 Viewing Broadband Checker Agent logs (body field only with timestamp)..."
	@echo "📍 Log group: /aws/agentcore/runtimes/broadband_checker_agent-KcXxkNFCkG-DEFAULT"
	@echo "⏰ Following new logs as they arrive..."
	@echo "----------------------------------------"
	@aws logs tail /aws/agentcore/runtimes/broadband_checker_agent-KcXxkNFCkG-DEFAULT --follow | \
	awk '{ts=$$1; $$1=""; stream=$$2; $$2=""; sub(/^  */,""); print ts "|" $$0}' | \
	while IFS="|" read -r ts json; do \
		body=$$(printf "%s\n" "$$json" | jq -r 'try .body // empty' 2>/dev/null); \
		if [ -n "$$body" ]; then printf "%s %s\n" "$$ts" "$$body"; fi; \
	done

.PHONY: agentcore-broadband-batch-test
agentcore-broadband-batch-test:
	@echo "🧪 Testing batch processing..."
	@aws lambda invoke \
		--function-name broadband-checker-agent-$(AWS_REGION) \
		--payload '{"addresses":[{"postcode":"E8 4LX","building_number":"13"},{"postcode":"SW1A 1AA","building_number":"10"}],"parallel":false}' \
		--profile $(AWS_PROFILE) \
		--region $(AWS_REGION) \
		/tmp/broadband-batch-response.json && \
		echo "Batch Response:" && \
		cat /tmp/broadband-batch-response.json | python3 -m json.tool

.PHONY: agentcore-broadband-clean
agentcore-broadband-clean:
	@echo "🧹 Cleaning Broadband Checker build artifacts..."
	@cd $(AGENT_CORE_DIR) && \
		rm -f deployment-broadband-checker-*.json && \
		docker rmi broadband-checker-agent:latest 2>/dev/null || true

.PHONY: deploy-agent-full
deploy-agent-full:
	@if [ -z "$(CONFIG)" ]; then \
		echo "❌ Please specify CONFIG=<config-file>"; \
		echo "Example: make deploy-agent-full CONFIG=web_search_agent.yaml"; \
		exit 1; \
	fi
	@# Extract agent name from config
	@AGENT_NAME=$$(python3 -c "import yaml; f=open('$(AGENT_CORE_CONFIGS)/$(CONFIG)', 'r'); print(yaml.safe_load(f).get('agent_name', 'unknown')); f.close()") && \
	echo "🚀 Full deployment for agent: $$AGENT_NAME" && \
	$(MAKE) deploy-agent-core CONFIG=$(CONFIG) && \
	$(MAKE) deploy-agent-wrapper AGENT=$$AGENT_NAME && \
	WRAPPER_ARN=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreWrapper-$$AGENT_NAME-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--profile "$(AWS_PROFILE)" \
		--query "Stacks[0].Outputs[?contains(OutputKey, 'StateMachineArn')].OutputValue" \
		--output text) && \
	echo "" && \
	echo "✅ Full deployment complete!" && \
	echo "" && \
	echo "Integration details:" && \
	echo "  Agent: $$AGENT_NAME" && \
	echo "  Wrapper State Machine: $$WRAPPER_ARN" && \
	echo "" && \
	echo "Add to hybrid supervisor agent_configs:" && \
	echo "  \"$$AGENT_NAME\": {" && \
	echo "    \"arn\": \"$$WRAPPER_ARN\"," && \
	echo "    \"description\": \"Agent Core $$AGENT_NAME\"" && \
	echo "  }"

.PHONY: list-agent-core
list-agent-core:
	@echo "📋 Listing Agent Core agents..."
	@echo "📍 Using AWS Profile: $(AWS_PROFILE), Region: $(AWS_REGION)"
	@aws bedrock-agent list-agents \
		--region $(AWS_REGION) \
		$${AWS_PROFILE:+--profile "$$AWS_PROFILE"} \
		--output table

.PHONY: delete-agent-core
delete-agent-core:
	@if [ -z "$(AGENT_ID)" ] && [ -z "$(AGENT_NAME)" ]; then \
		echo "❌ Please specify AGENT_ID=<agent-id> or AGENT_NAME=<agent-name>"; \
		echo "Run 'make list-agent-core' to see available agents"; \
		exit 1; \
	fi
	@echo "🗑️  Deleting Agent Core agent..."
	@echo "📍 Using AWS Profile: $(AWS_PROFILE), Region: $(AWS_REGION)"
	@if [ -n "$(AGENT_ID)" ]; then \
		$(PYTHON) $(AGENT_CORE_DIR)/clean_agent.py \
			--agent-id $(AGENT_ID) \
			--region $(AWS_REGION) \
			$${AWS_PROFILE:+--profile "$$AWS_PROFILE"}; \
	else \
		$(PYTHON) $(AGENT_CORE_DIR)/clean_agent.py \
			--agent-name $(AGENT_NAME) \
			--region $(AWS_REGION) \
			$${AWS_PROFILE:+--profile "$$AWS_PROFILE"}; \
	fi

.PHONY: clean-agent-core
clean-agent-core:
	@if [ -z "$(CONFIG)" ]; then \
		echo "❌ Please specify CONFIG=<config-file>"; \
		echo "Example: make clean-agent-core CONFIG=web_search_agent.yaml"; \
		exit 1; \
	fi
	@AGENT_NAME=$$(python3 -c "import yaml; f=open('$(AGENT_CORE_CONFIGS)/$(CONFIG)', 'r'); print(yaml.safe_load(f).get('agent_name', 'unknown')); f.close()") && \
	echo "🧹 Cleaning up agent: $$AGENT_NAME" && \
	$(MAKE) delete-agent-core AGENT_NAME=$$AGENT_NAME

.PHONY: test-agent-core
test-agent-core:
	@if [ -z "$(AGENT)" ]; then \
		echo "❌ Please specify AGENT=<agent-name>"; \
		echo "Example: make test-agent-core AGENT=web-search-agent"; \
		exit 1; \
	fi
	@echo "🧪 Testing Agent Core agent: $(AGENT)..."
	@# Get wrapper state machine ARN
	@WRAPPER_ARN=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreWrapper-$(AGENT)-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--profile "$(AWS_PROFILE)" \
		--query "Stacks[0].Outputs[?contains(OutputKey, 'StateMachineArn')].OutputValue" \
		--output text 2>/dev/null) && \
	if [ -z "$$WRAPPER_ARN" ]; then \
		echo "❌ Wrapper state machine not found for $(AGENT)"; \
		exit 1; \
	fi && \
	# Start execution
	aws stepfunctions start-execution \
		--state-machine-arn "$$WRAPPER_ARN" \
		--input '{"session_id": "test-'$$(date +%s)'", "agent_config": {"input_text": "Hello, can you help me search for information?"}}' \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--output json | jq .

# ============================================
# NEW Bedrock Agent Core Commands (2024)
# ============================================

.PHONY: agentcore-deploy
agentcore-deploy:
	@echo "🚀 Deploying Web Search Agent to Bedrock Agent Core..."
	@echo "📍 Using AWS Region: $(AWS_REGION)"
	@cd $(AGENTCORE_DIR) && \
	$(PYTHON) deploy_agentcore.py \
		--agent-name $(AGENTCORE_NAME) \
		--region $(AWS_REGION)

.PHONY: agentcore-test
agentcore-test:
	@if [ ! -f "$(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json" ]; then \
		echo "❌ Deployment info not found. Deploy first with: make agentcore-deploy"; \
		exit 1; \
	fi
	@echo "🧪 Testing Agent Core agent: $(AGENTCORE_NAME)..."
	@cd $(AGENTCORE_DIR) && \
	AGENT_ARN=$$(cat agentcore-deployment-$(AGENTCORE_NAME).json | jq -r '.agent_arn') && \
	$(PYTHON) deploy_agentcore.py \
		--agent-name $(AGENTCORE_NAME) \
		--region $(AWS_REGION) \
		--test

.PHONY: agentcore-status
agentcore-status:
	@if [ ! -f "$(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json" ]; then \
		echo "❌ No deployment found for $(AGENTCORE_NAME)"; \
		exit 1; \
	fi
	@echo "📊 Agent Core Status for: $(AGENTCORE_NAME)"
	@cat $(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json | jq .

.PHONY: agentcore-invoke
agentcore-invoke:
	@if [ ! -f "$(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json" ]; then \
		echo "❌ Deployment info not found. Deploy first with: make agentcore-deploy"; \
		exit 1; \
	fi
	@echo "🔄 Invoking Agent Core agent: $(AGENTCORE_NAME)"
	@AGENT_ARN=$$(cat $(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json | jq -r '.agent_arn') && \
	aws agentcore invoke-agent-runtime \
		--agent-runtime-arn "$$AGENT_ARN" \
		--qualifier "DEFAULT" \
		--payload '{"prompt": "$(PROMPT)", "test": true}' \
		--region $(AWS_REGION) \
		--output json | jq .

.PHONY: agentcore-logs
agentcore-logs:
	@echo "📜 Viewing Agent Core logs for: $(AGENTCORE_NAME)"
	@aws logs tail /aws/agentcore/$(AGENTCORE_NAME) \
		--region $(AWS_REGION) \
		--follow

.PHONY: agentcore-clean
agentcore-clean:
	@echo "🧹 Cleaning up Agent Core deployment: $(AGENTCORE_NAME)"
	@if [ -f "$(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json" ]; then \
		AGENT_ID=$$(cat $(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json | jq -r '.agent_id'); \
		ECR_URI=$$(cat $(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json | jq -r '.ecr_uri'); \
		ROLE_NAME="AgentCoreRuntime-$(AGENTCORE_NAME)"; \
		echo "Deleting Agent Core runtime..."; \
		aws agentcore-control delete-agent-runtime \
			--agent-runtime-id "$$AGENT_ID" \
			--region $(AWS_REGION) 2>/dev/null || true; \
		echo "Deleting ECR repository..."; \
		aws ecr delete-repository \
			--repository-name "$$(echo $$ECR_URI | cut -d'/' -f2)" \
			--force \
			--region $(AWS_REGION) 2>/dev/null || true; \
		echo "Deleting IAM role..."; \
		aws iam delete-role-policy \
			--role-name "$$ROLE_NAME" \
			--policy-name "AgentCoreExecutionPolicy" 2>/dev/null || true; \
		aws iam delete-role \
			--role-name "$$ROLE_NAME" 2>/dev/null || true; \
		rm -f $(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json; \
		echo "✅ Cleanup complete"; \
	else \
		echo "No deployment found to clean"; \
	fi

.PHONY: agentcore-help
agentcore-help:
	@echo "╔════════════════════════════════════════════════════════════════════╗"
	@echo "║           Bedrock Agent Core Commands (NEW Service)               ║"
	@echo "╚════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  agentcore-deploy    - Deploy agent to Bedrock Agent Core"
	@echo "  agentcore-test      - Test deployed agent"
	@echo "  agentcore-status    - Show deployment status"
	@echo "  agentcore-invoke    - Invoke agent with a prompt"
	@echo "                        Usage: make agentcore-invoke PROMPT='your question'"
	@echo "  agentcore-logs      - View agent logs"
	@echo "  agentcore-clean     - Clean up agent deployment"
	@echo "  agentcore-wrapper   - Deploy Step Functions wrapper for Agent Core"
	@echo "  agentcore-full      - Deploy agent and wrapper together"
	@echo ""
	@echo "Environment Variables:"
	@echo "  AGENTCORE_NAME      - Agent name (default: web-search-agent)"
	@echo "  AWS_REGION          - AWS region (default: us-west-2)"
	@echo ""

.PHONY: agentcore-wrapper
agentcore-wrapper:
	@echo "🚀 Deploying Step Functions wrapper for Agent Core..."
	@if [ ! -f "$(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json" ]; then \
		echo "❌ Agent not deployed. Deploy first with: make agentcore-deploy"; \
		exit 1; \
	fi
	@AGENT_ARN=$$(cat $(AGENTCORE_DIR)/agentcore-deployment-$(AGENTCORE_NAME).json | jq -r '.agent_arn') && \
	$(CDK) deploy AgentCoreWrapperSimpleStack-$(ENV_NAME) \
		--context agent_runtime_arn="$$AGENT_ARN" \
		--require-approval never
	@echo "✅ Agent Core wrapper deployed!"

.PHONY: agentcore-full
agentcore-full: agentcore-deploy agentcore-wrapper
	@echo "✅ Full Agent Core deployment complete!"
	@echo "State Machine ARN:"
	@aws cloudformation describe-stacks \
		--stack-name AgentCoreWrapperSimpleStack-$(ENV_NAME) \
		--query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" \
		--output text \
		--region $(AWS_REGION)

# ============================================
# AgentCore Browser Deployment Commands (CDK-based)
# ============================================

.PHONY: create-agentcore-ecr-repos
create-agentcore-ecr-repos:
	@echo "📦 Creating AgentCore ECR repositories..."
	@echo ""
	@for repo in agentcore-cdk_broadband_checker_agent agentcore-cdk_shopping_agent agentcore-cdk_web_search_agent; do \
		echo "Creating repository: $$repo" && \
		aws ecr create-repository \
			--repository-name $$repo \
			--region $(AWS_REGION) \
			--image-scanning-configuration scanOnPush=true \
			--encryption-configuration encryptionType=AES256 2>/dev/null || echo "  (already exists, skipping)"; \
	done && \
	echo "" && \
	echo "✅ ECR repositories created!" && \
	echo "" && \
	echo "Next step: make build-agentcore-containers ENV_NAME=prod"

.PHONY: build-agentcore-containers
build-agentcore-containers:
	@echo "🐳 Building AgentCore browser agent containers..."
	@echo ""
	@echo "This will build Docker containers for each browser agent and push to ECR"
	@echo "Agents: broadband_checker_agent, shopping_agent, web_search_agent"
	@echo ""
	@# Get ECR repository URIs - try from CloudFormation first, fallback to direct repo names
	@ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text) && \
	BROADBAND_REPO=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreBrowserRuntimeStack-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--query "Stacks[0].Outputs[?OutputKey=='BroadbandRepositoryUri'].OutputValue" \
		--output text 2>/dev/null || echo "$$ACCOUNT_ID.dkr.ecr.$(AWS_REGION).amazonaws.com/agentcore-cdk_broadband_checker_agent") && \
	SHOPPING_REPO=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreBrowserRuntimeStack-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--query "Stacks[0].Outputs[?OutputKey=='ShoppingRepositoryUri'].OutputValue" \
		--output text 2>/dev/null || echo "$$ACCOUNT_ID.dkr.ecr.$(AWS_REGION).amazonaws.com/agentcore-cdk_shopping_agent") && \
	SEARCH_REPO=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreBrowserRuntimeStack-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--query "Stacks[0].Outputs[?OutputKey=='SearchRepositoryUri'].OutputValue" \
		--output text 2>/dev/null || echo "$$ACCOUNT_ID.dkr.ecr.$(AWS_REGION).amazonaws.com/agentcore-cdk_web_search_agent") && \
	echo "📦 ECR Repositories:" && \
	echo "  Broadband: $$BROADBAND_REPO" && \
	echo "  Shopping: $$SHOPPING_REPO" && \
	echo "  Search: $$SEARCH_REPO" && \
	echo "" && \
	echo "🔑 Logging in to ECR..." && \
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $$(echo $$BROADBAND_REPO | cut -d'/' -f1) && \
	echo "" && \
	echo "🔨 Building and pushing containers..." && \
	echo "  Source: lambda/tools/agentcore_browser/agents" && \
	cd lambda/tools/agentcore_browser/agents && \
	docker build --platform linux/amd64 -t $$BROADBAND_REPO:latest -f Dockerfile . && \
	docker push $$BROADBAND_REPO:latest && \
	docker tag $$BROADBAND_REPO:latest $$SHOPPING_REPO:latest && \
	docker push $$SHOPPING_REPO:latest && \
	docker tag $$BROADBAND_REPO:latest $$SEARCH_REPO:latest && \
	docker push $$SEARCH_REPO:latest && \
	echo "" && \
	echo "✅ All AgentCore containers built and pushed to ECR!"

.PHONY: deploy-agentcore-runtime
deploy-agentcore-runtime:
	@echo "🚀 Deploying AgentCore Browser Runtime Stack..."
	@echo "This creates ECR repositories and AgentCore runtimes"
	$(CDK) deploy AgentCoreBrowserRuntimeStack-$(ENV_NAME) \
		--require-approval never --profile $(AWS_PROFILE)
	@echo "✅ AgentCore runtimes deployed!"
	@echo ""
	@echo "⚠️  Next steps:"
	@echo "  1. Build and push containers: make build-agentcore-containers"
	@echo "  2. Deploy Lambda tool: make deploy-agentcore-tool"

.PHONY: deploy-agentcore-tool
deploy-agentcore-tool:
	@echo "🚀 Deploying Agent Core Browser Tool Stack..."
	@echo "This deploys the Lambda that routes to AgentCore runtimes"
	$(CDK) deploy AgentCoreBrowserToolStack-$(ENV_NAME) \
		--require-approval never --profile $(AWS_PROFILE)
	@echo "✅ Agent Core Browser Tool deployed!"

.PHONY: deploy-agentcore-full
deploy-agentcore-full: create-agentcore-ecr-repos build-agentcore-containers deploy-agentcore-runtime deploy-agentcore-tool
	@echo ""
	@echo "✅ Full AgentCore Browser deployment complete!"
	@echo ""
	@echo "Deployed components:"
	@echo "  ✓ ECR repositories (created manually)"
	@echo "  ✓ Docker containers (real images)"
	@echo "  ✓ AgentCore runtimes"
	@echo "  ✓ Lambda routing tool"
	@echo ""
	@echo "The browser tools are now registered in DynamoDB:"
	@echo "  - browser_broadband"
	@echo "  - browser_shopping"
	@echo "  - browser_search"


.PHONY: test-agentcore-browser
test-agentcore-browser:
	@echo "🧪 Testing AgentCore browser tool..."
	@FUNCTION_NAME=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreBrowserToolStack-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
		--output text 2>/dev/null) && \
	if [ -z "$$FUNCTION_NAME" ]; then \
		echo "❌ AgentCoreBrowserToolStack not found"; \
		exit 1; \
	fi && \
	echo "Invoking $$FUNCTION_NAME with test payload..." && \
	aws lambda invoke \
		--function-name $$FUNCTION_NAME \
		--payload '{"name":"browser_search","input":{"query":"test query"}}' \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		/tmp/agentcore-test-response.json && \
	echo "Response:" && \
	cat /tmp/agentcore-test-response.json | python3 -m json.tool

.PHONY: logs-agentcore-browser
logs-agentcore-browser:
	@echo "📋 Tailing AgentCore browser Lambda logs..."
	@FUNCTION_NAME=$$(aws cloudformation describe-stacks \
		--stack-name "AgentCoreBrowserToolStack-$(ENV_NAME)" \
		--region "$(AWS_REGION)" \
		--query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
		--output text 2>/dev/null) && \
	aws logs tail /aws/lambda/$$FUNCTION_NAME --follow --region $(AWS_REGION) --profile $(AWS_PROFILE)

# AgentCore Browser Deployment using AgentCore CLI
# Uses the official agentcore CLI for simplified deployment

.PHONY: agentcore-configure-broadband
agentcore-configure-broadband:
	@echo "🔧 Configuring broadband checker agent..."
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && \
	AWS_REGION=$(AWS_REGION) agentcore configure \
		--entrypoint broadband_agent.py \
		--name cdk_broadband_checker_agent \
		--non-interactive

.PHONY: agentcore-configure-shopping
agentcore-configure-shopping:
	@echo "🔧 Configuring shopping agent..."
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore configure \
		--entrypoint shopping_agent.py \
		--name cdk_shopping_agent \
		--non-interactive

.PHONY: agentcore-configure-search
agentcore-configure-search:
	@echo "🔧 Configuring search agent..."
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore configure \
		--entrypoint search_agent.py \
		--name cdk_web_search_agent \
		--non-interactive

.PHONY: agentcore-configure-all
agentcore-configure-all: agentcore-configure-broadband agentcore-configure-shopping agentcore-configure-search
	@echo "✅ All agents configured!"

.PHONY: agentcore-launch-broadband
agentcore-launch-broadband:
	@echo "🚀 Launching broadband checker agent..."
	@echo "   (Uses CodeBuild - no Docker needed)"
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore launch \
		--agent cdk_broadband_checker_agent \
		--auto-update-on-conflict

.PHONY: agentcore-launch-shopping
agentcore-launch-shopping:
	@echo "🚀 Launching shopping agent..."
	@echo "   (Uses CodeBuild - no Docker needed)"
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore launch \
		--agent cdk_shopping_agent \
		--auto-update-on-conflict

.PHONY: agentcore-launch-search
agentcore-launch-search:
	@echo "🚀 Launching search agent..."
	@echo "   (Uses CodeBuild - no Docker needed)"
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore launch \
		--agent cdk_web_search_agent \
		--auto-update-on-conflict

.PHONY: agentcore-launch-all
agentcore-launch-all: agentcore-launch-broadband agentcore-launch-shopping agentcore-launch-search
	@echo ""
	@echo "✅ All AgentCore browser agents launched!"

# Legacy manual deployment targets (DEPRECATED - use agentcore-launch-all instead)
# Kept for backward compatibility

.PHONY: deploy-agentcore-runtimes-manual-legacy
deploy-agentcore-runtimes-manual-legacy:
	@echo "🚀 Deploying AgentCore Runtimes Manually using starter toolkit"
	@echo ""
	@echo "⚠️  Prerequisite: agentcore CLI must be installed:"
	@echo "   pip install agentcore"
	@echo ""
	@ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text) && \
	AWS_REGION=$(AWS_REGION) && \
	RUNTIMES="cdk_broadband_checker_agent cdk_shopping_agent cdk_web_search_agent" && \
	echo "📦 Deploying runtimes: $$RUNTIMES" && \
	echo "" && \
	for RUNTIME in $$RUNTIMES; do \
		echo "Deploying $$RUNTIME..." && \
		CONTAINER_URI="$$ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com/agentcore-$$RUNTIME:latest" && \
		agentcore deploy-runtime \
			--runtime-name $$RUNTIME \
			--container-uri $$CONTAINER_URI \
			--network-mode PUBLIC \
			--protocol HTTP \
			--region $$AWS_REGION && \
		echo "  ✅ $$RUNTIME deployed successfully" && \
		echo ""; \
	done && \
	echo "✅ All AgentCore runtimes deployed!"

.PHONY: list-agentcore-runtimes
list-agentcore-runtimes:
	@echo "📋 Listing AgentCore Runtimes..."
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore list

.PHONY: agentcore-status
agentcore-status:
	@echo "📊 Checking AgentCore agent status..."
	@echo ""
	@echo "Broadband Agent:"
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore status --runtime-name cdk_broadband_checker_agent 2>/dev/null || echo "  Not deployed"
	@echo ""
	@echo "Shopping Agent:"
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore status --runtime-name cdk_shopping_agent 2>/dev/null || echo "  Not deployed"
	@echo ""
	@echo "Search Agent:"
	@cd lambda/tools/agentcore_browser/agents && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore status --runtime-name cdk_web_search_agent 2>/dev/null || echo "  Not deployed"

.PHONY: get-agentcore-runtime-arns
get-agentcore-runtime-arns:
	@echo "🔍 Getting AgentCore Runtime ARNs..."
	@echo ""
	@cd lambda/tools/agentcore_browser/agents && \
	echo "Broadband Agent:" && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore describe --runtime-name cdk_broadband_checker_agent 2>/dev/null | grep -i arn || echo "  Not deployed" && \
	echo "" && \
	echo "Shopping Agent:" && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore describe --runtime-name cdk_shopping_agent 2>/dev/null | grep -i arn || echo "  Not deployed" && \
	echo "" && \
	echo "Search Agent:" && \
	source ../../../../.venv/bin/activate && AWS_REGION=$(AWS_REGION) agentcore describe --runtime-name cdk_web_search_agent 2>/dev/null | grep -i arn || echo "  Not deployed"

.PHONY: update-agentcore-runtimes-manual
update-agentcore-runtimes-manual:
	@echo "🔄 Updating AgentCore Runtimes to latest container images..."
	@echo ""
	@ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text) && \
	AWS_REGION=$(AWS_REGION) && \
	RUNTIMES="cdk_broadband_checker_agent cdk_shopping_agent cdk_web_search_agent" && \
	for RUNTIME in $$RUNTIMES; do \
		echo "Updating $$RUNTIME..." && \
		CONTAINER_URI="$$ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com/agentcore-$$RUNTIME:latest" && \
		agentcore update-runtime \
			--runtime-name $$RUNTIME \
			--container-uri $$CONTAINER_URI \
			--region $$AWS_REGION && \
		echo "  ✅ $$RUNTIME updated" && \
		echo ""; \
	done && \
	echo "✅ All runtimes updated!"

.PHONY: delete-agentcore-runtimes-manual
delete-agentcore-runtimes-manual:
	@echo "🗑️  Deleting AgentCore Runtimes..."
	@echo ""
	@read -p "Are you sure you want to delete all AgentCore runtimes? (yes/no): " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		RUNTIMES="cdk_broadband_checker_agent cdk_shopping_agent cdk_web_search_agent" && \
		for RUNTIME in $$RUNTIMES; do \
			echo "Deleting $$RUNTIME..." && \
			agentcore delete-runtime \
				--runtime-name $$RUNTIME \
				--region $(AWS_REGION) 2>/dev/null && \
			echo "  ✅ $$RUNTIME deleted" || echo "  ⚠️  $$RUNTIME not found or already deleted"; \
			echo ""; \
		done && \
		echo "✅ Deletion complete!"; \
	else \
		echo "❌ Deletion cancelled"; \
	fi

.PHONY: update-agentcore-lambda-arns
update-agentcore-lambda-arns:
	@echo "🔄 Updating Lambda function with AgentCore runtime ARNs..."
	@echo ""
	@FUNCTION_NAME="agentcore-browser-tool-$(ENV_NAME)" && \
	BROADBAND_ARN=$$(agentcore describe-runtime --runtime-name cdk_broadband_checker_agent --region $(AWS_REGION) --query 'runtimeArn' --output text 2>/dev/null) && \
	SHOPPING_ARN=$$(agentcore describe-runtime --runtime-name cdk_shopping_agent --region $(AWS_REGION) --query 'runtimeArn' --output text 2>/dev/null) && \
	SEARCH_ARN=$$(agentcore describe-runtime --runtime-name cdk_web_search_agent --region $(AWS_REGION) --query 'runtimeArn' --output text 2>/dev/null) && \
	if [ -z "$$BROADBAND_ARN" ] || [ -z "$$SHOPPING_ARN" ] || [ -z "$$SEARCH_ARN" ]; then \
		echo "❌ Error: Could not find all runtime ARNs. Please deploy runtimes first."; \
		exit 1; \
	fi && \
	echo "Found ARNs:" && \
	echo "  Broadband: $$BROADBAND_ARN" && \
	echo "  Shopping:  $$SHOPPING_ARN" && \
	echo "  Search:    $$SEARCH_ARN" && \
	echo "" && \
	aws lambda update-function-configuration \
		--function-name $$FUNCTION_NAME \
		--environment Variables="{\"BROADBAND_AGENT_ARN\":\"$$BROADBAND_ARN\",\"SHOPPING_AGENT_ARN\":\"$$SHOPPING_ARN\",\"SEARCH_AGENT_ARN\":\"$$SEARCH_ARN\"}" \
		--region $(AWS_REGION) \
		--query 'Environment.Variables' \
		--output json && \
	echo "" && \
	echo "✅ Lambda environment variables updated!"

# Simplified full workflow using agentcore CLI (RECOMMENDED)
.PHONY: deploy-agentcore-browser-tools
deploy-agentcore-browser-tools: agentcore-configure-all agentcore-launch-all update-agentcore-lambda-arns
	@echo ""
	@echo "✅ Full AgentCore browser tool deployment complete!"
	@echo ""
	@echo "📝 Next steps:"
	@echo "  1. Test: make test-agentcore-broadband"
	@echo "  2. Check status: make agentcore-status"
	@echo "  3. View logs: make tail-agentcore-browser-logs"
	@echo "  4. Modify instructions in lambda/tools/agentcore_browser/agents/instructions/"
	@echo ""
	@echo "📚 Documentation: docs/AGENTCORE_BROWSER_QUICK_START.md"

# Test the broadband agent
.PHONY: test-agentcore-broadband
test-agentcore-broadband:
	@echo "🧪 Testing broadband agent..."
	@aws lambda invoke \
		--function-name agentcore-browser-tool-$(ENV_NAME) \
		--payload '{"id":"test1","name":"browser_broadband","input":{"postcode":"E8 4LX","building_number":"13"}}' \
		--region $(AWS_REGION) \
		/tmp/agentcore-test-response.json && \
	cat /tmp/agentcore-test-response.json | jq && \
	rm /tmp/agentcore-test-response.json
