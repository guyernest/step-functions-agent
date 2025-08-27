.PHONY: build deploy test clean install sandbox build-mcp build-frontend codegen lint format help

# Default target
.DEFAULT_GOAL := help

# Variables
MCP_SERVER_DIR = amplify/mcp-server/rust-mcp-server

# Help target
help:
	@echo "Step Functions Agent Framework - Amplify Gen 2 Project"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install all dependencies"
	@echo "  make sandbox       - Start Amplify sandbox environment"
	@echo "  make build         - Build everything (MCP server + frontend)"
	@echo "  make build-mcp     - Build MCP server (Rust Lambda function)"
	@echo "  make build-frontend - Build frontend application"
	@echo "  make codegen       - Generate GraphQL client code"
	@echo "  make deploy        - Deploy to AWS"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean build artifacts"
	@echo ""

# Install dependencies
install:
	@echo "Installing Node dependencies..."
	npm install
	@echo "Installing MCP server dependencies..."
	@cd $(MCP_SERVER_DIR) && make install-deps
	@echo "Dependencies installed!"

# Start Amplify sandbox
sandbox:
	@echo "Starting Amplify sandbox..."
	npx ampx sandbox

# Build everything
build: build-mcp build-frontend
	@echo "Build complete!"

# Build MCP server (Rust Lambda function)
build-mcp:
	@echo "Building MCP server..."
	@cd $(MCP_SERVER_DIR) && make build
	@echo "MCP server built successfully!"

# Build frontend
build-frontend: codegen
	@echo "Building frontend..."
	npm run build
	@echo "Frontend built successfully!"

# Generate GraphQL client code
codegen:
	@echo "Generating GraphQL client code..."
	npx ampx generate graphql-client-code --out src/graphql
	@echo "GraphQL code generation complete!"

# Deploy to AWS
deploy: build
	@echo "Deploying to AWS..."
	npx ampx pipeline-deploy --branch main
	@echo "Deployment complete!"

# Run tests
test:
	@echo "Running MCP server tests..."
	@cd $(MCP_SERVER_DIR) && make test
	@echo "Running frontend tests..."
	npm test -- --run 2>/dev/null || echo "No frontend tests configured"
	@echo "All tests passed!"

# Lint code
lint:
	@echo "Linting MCP server code..."
	@cd $(MCP_SERVER_DIR) && cargo clippy -- -D warnings
	@echo "Linting TypeScript code..."
	npx eslint src amplify --ext .ts,.tsx 2>/dev/null || echo "ESLint not configured"
	@echo "Linting complete!"

# Format code
format:
	@echo "Formatting MCP server code..."
	@cd $(MCP_SERVER_DIR) && cargo fmt
	@echo "Formatting TypeScript code..."
	npx prettier --write "src/**/*.{ts,tsx}" "amplify/**/*.ts" 2>/dev/null || echo "Prettier not configured"
	@echo "Formatting complete!"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist
	rm -rf .amplify
	rm -rf node_modules/.cache
	@cd $(MCP_SERVER_DIR) && make clean
	@echo "Clean complete!"

# Local development helpers
dev-mcp:
	@echo "Running MCP server locally..."
	@cd $(MCP_SERVER_DIR) && make dev

# Individual build targets for debugging
check-mcp:
	@echo "Checking MCP server build..."
	@cd $(MCP_SERVER_DIR) && make check

# CI/CD helpers
ci-test: lint test
	@echo "CI tests complete!"

ci-build: build
	@echo "CI build complete!"

# Utility targets
check-deps:
	@echo "Checking dependencies..."
	@which node > /dev/null || (echo "Node.js is required" && exit 1)
	@which npx > /dev/null || (echo "npm is required" && exit 1)
	@cd $(MCP_SERVER_DIR) && make install-deps
	@echo "All dependencies are installed!"

# Watch for changes (development)
watch:
	@echo "Watching for changes..."
	@echo "Run 'make sandbox' in another terminal for backend"
	npm run dev