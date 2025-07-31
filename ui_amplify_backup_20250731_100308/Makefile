# Makefile for Step Functions Agent UI

# Default target
.PHONY: all
all: setup

# Setup the development environment
.PHONY: setup
setup: copy-amplify-outputs install

# Install dependencies
.PHONY: install
install:
	npm install

# Copy amplify_outputs.json to src directory
.PHONY: copy-amplify-outputs
copy-amplify-outputs:
	@echo "Copying amplify_outputs.json to src directory..."
	@cp amplify_outputs.json src/amplify_outputs.json 2>/dev/null || echo "Warning: amplify_outputs.json not found. Run 'npx amplify sandbox' first."

# Start development server
.PHONY: start
start: copy-amplify-outputs
	npm start

# Start Amplify sandbox
.PHONY: sandbox
sandbox:
	npx amplify sandbox

# Build the application
.PHONY: build
build: copy-amplify-outputs
	npm run build

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf build
	rm -rf node_modules
	rm -f src/amplify_outputs.json

# Full development setup
.PHONY: dev
dev:
	@echo "Starting full development environment..."
	@echo "1. Starting Amplify sandbox in background..."
	@npx amplify sandbox &
	@echo "2. Waiting for sandbox to initialize..."
	@sleep 10
	@echo "3. Copying configuration..."
	@make copy-amplify-outputs
	@echo "4. Starting development server..."
	@make start

# Help
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make setup              - Initial setup (install deps and copy config)"
	@echo "  make start              - Start development server"
	@echo "  make sandbox            - Start Amplify sandbox"
	@echo "  make build              - Build the application"
	@echo "  make clean              - Clean build artifacts"
	@echo "  make dev                - Start full dev environment"
	@echo "  make copy-amplify-outputs - Copy amplify_outputs.json to src/"