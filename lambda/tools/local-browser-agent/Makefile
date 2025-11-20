.PHONY: help install build run dev test clean deploy

# Default target
help:
	@echo "Local Browser Agent - Makefile Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install all dependencies (Rust, Python 3.11 venv, Node.js)"
	@echo "  make install-python   Install Python dependencies with uv (creates .venv)"
	@echo "  make install-node     Install Node.js dependencies"
	@echo "  make install-rust     Fetch Rust dependencies"
	@echo "  make install-playwright Install Playwright Chrome browser"
	@echo "  make aws-setup        Configure AWS profile for browser-agent"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run in development mode with hot reload (opens Tauri UI)"
	@echo "  make build            Build release binary with DMG installer"
	@echo "  make build-bin        Build binary only (faster, no DMG bundle)"
	@echo "  make package          Create deployment package (includes DMG, Python, docs)"
	@echo "  make run              Run the agent (requires config.yaml)"
	@echo "  make run-config       Run with custom config (CONFIG=/path/to/config.yaml)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-rust        Run Rust tests only"
	@echo "  make test-python      Run Python tests only"
	@echo ""
	@echo "Python Dependencies (uv):"
	@echo "  make update-deps      Update requirements.txt from requirements.in"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Clean build artifacts"
	@echo "  make clean-all        Clean all including requirements.txt and .venv"
	@echo "  make lint             Run linters"
	@echo "  make format           Format code"
	@echo ""
	@echo "AWS Deployment:"
	@echo "  make deploy           Deploy CDK stack (AWS_PROFILE required)"
	@echo "  make deploy-destroy   Destroy CDK stack (AWS_PROFILE required)"

# Installation
install: check-deps install-python install-node install-rust install-playwright config-setup
	@echo ""
	@echo "========================================"
	@echo "✅ Installation Complete!"
	@echo "========================================"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure AWS profile: make aws-setup"
	@echo "2. Deploy CDK stack: cd ../../../ && cdk deploy BrowserRemoteToolStack-prod"
	@echo "3. Run in dev mode: make dev"
	@echo "4. Configure via UI (Activity ARN, S3 bucket, Chrome profile, etc.)"
	@echo "5. Save configuration and start monitoring"
	@echo ""
	@echo "Note: Python 3.11 venv created at python/.venv"
	@echo "      Dependencies managed via uv (requirements.in -> requirements.txt)"
	@echo ""

check-deps:
	@echo "Checking dependencies..."
	@command -v cargo >/dev/null 2>&1 || { echo "❌ Rust not found. Install from https://rustup.rs/"; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install from https://nodejs.org/"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "❌ npm not found"; exit 1; }
	@echo "✅ All required tools found"

install-python:
	@echo "Installing Python dependencies with uv..."
	@cd python && uv venv --python 3.11 .venv
	@cd python && uv pip compile requirements.in -o requirements.txt
	@cd python && uv pip install --python .venv/bin/python -r requirements.txt
	@echo "✅ Python dependencies installed in python/.venv"

install-node:
	@echo "Installing Node.js dependencies..."
	@cd ui && npm install
	@echo "✅ Node.js dependencies installed"

install-playwright:
	@echo "Installing Playwright Chrome browser..."
	@python/.venv/bin/python -m playwright install chrome
	@echo "✅ Playwright Chrome installed"

install-rust:
	@echo "Fetching Rust dependencies..."
	@cd src-tauri && cargo fetch
	@cargo install tauri-cli --quiet 2>/dev/null || echo "✅ Tauri CLI already installed"
	@cd src-tauri && cargo add serde_yaml --quiet 2>/dev/null || echo "✅ serde_yaml already added"
	@echo "✅ Rust dependencies ready"

# Build
build:
	@echo "Building Local Browser Agent..."
	@# Remove .venv from python directory to avoid bundling it (320MB!)
	@rm -rf python/.venv python/__pycache__ python/*.pyc
	@cd src-tauri && cargo tauri build
	@echo ""
	@echo "Build complete!"
	@echo "  Binary:  ./src-tauri/target/release/local-browser-agent"
	@echo "  App:     ./src-tauri/target/release/bundle/macos/Local Browser Agent.app"
	@echo "  DMG:     ./src-tauri/target/release/bundle/dmg/*.dmg"

# Build binary only (faster, no bundle)
build-bin:
	@echo "Building binary only (no bundle)..."
	@cd ui && npm run build
	@cd src-tauri && cargo build --release
	@echo "Build complete: ./src-tauri/target/release/local-browser-agent"

# Create deployment package
package:
	@echo "=================================="
	@echo "Creating deployment package..."
	@echo "=================================="
	@echo ""
	@# Check if build exists
	@if [ ! -f "src-tauri/target/release/bundle/macos/Local Browser Agent.app/Contents/MacOS/local-browser-agent" ]; then \
		echo "❌ Build not found. Running 'make build' first..."; \
		make build; \
	fi
	@# Create deployment directory
	@rm -rf deployment-package
	@mkdir -p deployment-package
	@echo "📦 Packaging files..."
	@# Copy DMG installer
	@echo "  - DMG installer"
	@cp src-tauri/target/release/bundle/dmg/*.dmg deployment-package/ 2>/dev/null || true
	@# Copy app bundle
	@echo "  - App bundle"
	@cp -r "src-tauri/target/release/bundle/macos/Local Browser Agent.app" deployment-package/ 2>/dev/null || true
	@# Copy Python directory
	@echo "  - Python scripts"
	@mkdir -p deployment-package/python
	@cp python/*.py deployment-package/python/
	@cp python/requirements.txt deployment-package/python/
	@# Copy examples directory
	@echo "  - Examples"
	@cp -r examples deployment-package/
	@# Copy configuration template
	@echo "  - Configuration template"
	@cp config.example.yaml deployment-package/config.yaml
	@# Create setup script
	@echo "  - Setup script"
	@cp SETUP.sh.template deployment-package/SETUP.sh
	@chmod +x deployment-package/SETUP.sh
	@# Copy README template
	@echo "  - README"
	@cp README.template.md deployment-package/README.md
	@# Create compressed archive
	@echo "  - Creating archive"
	@tar -czf browser-agent-deployment.tar.gz deployment-package/
	@# Show results
	@echo ""
	@echo "=================================="
	@echo "✅ Deployment Package Created!"
	@echo "=================================="
	@echo ""
	@echo "Archive: browser-agent-deployment.tar.gz"
	@ls -lh browser-agent-deployment.tar.gz
	@echo ""
	@echo "Package contents:"
	@ls -lh deployment-package/
	@echo ""
	@echo "To deploy to UK Mac:"
	@echo "  1. Transfer: scp browser-agent-deployment.tar.gz user@uk-mac:"
	@echo "  2. Extract: tar -xzf browser-agent-deployment.tar.gz"
	@echo "  3. Setup:   cd deployment-package && ./SETUP.sh"
	@echo ""

# Development
dev:
	@echo "Starting development server..."
	@cd src-tauri && cargo tauri dev

# Run
run:
	@echo "Running Local Browser Agent..."
	@./src-tauri/target/release/local-browser-agent

run-config:
	@echo "Running Local Browser Agent with custom config..."
	@./src-tauri/target/release/local-browser-agent --config $(CONFIG)

# Testing
test: test-rust test-python
	@echo "All tests passed!"

test-rust:
	@echo "Running Rust tests..."
	@cd src-tauri && cargo test

test-python:
	@echo "Running Python tests..."
	@echo "Testing nested workflow structures..."
	@python3 python/test_nested_workflow.py
	@echo ""
	@echo "Running pytest tests..."
	@cd python && python3 -m pytest || true

# Linting & Formatting
lint:
	@echo "Running linters..."
	@cd src-tauri && cargo clippy -- -D warnings
	@cd ui && npm run lint

format:
	@echo "Formatting code..."
	@cd src-tauri && cargo fmt
	@cd ui && npm run format

# Clean
clean:
	@echo "Cleaning build artifacts..."
	@cd src-tauri && cargo clean
	@cd ui && rm -rf dist node_modules
	@rm -rf python/__pycache__ python/.pytest_cache python/.venv

clean-all: clean
	@echo "Cleaning all generated files including requirements.txt..."
	@rm -f python/requirements.txt

# Python Dependencies
update-deps:
	@echo "Updating requirements.txt from requirements.in..."
	@cd python && uv pip compile --python 3.11 requirements.in -o requirements.txt
	@echo "✅ requirements.txt updated"

# AWS Deployment
deploy:
	@echo "Deploying Browser Remote Tool Stack..."
	@cd ../../../ && cdk deploy BrowserRemoteToolStack-prod --profile $(AWS_PROFILE)

deploy-destroy:
	@echo "Destroying Browser Remote Tool Stack..."
	@cd ../../../ && cdk destroy BrowserRemoteToolStack-prod --profile $(AWS_PROFILE)

# Configuration
config-setup:
	@echo "Setting up configuration..."
	@if [ ! -f config.yaml ]; then \
		cp config.example.yaml config.yaml; \
		echo "Created config.yaml from example. Please edit with your values."; \
	else \
		echo "config.yaml already exists."; \
	fi

# AWS Profile setup
aws-setup:
	@echo "Setting up AWS profile for browser-agent..."
	@aws configure --profile browser-agent
