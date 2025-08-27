.PHONY: build clean install-deps local test package check help

# Variables
BUILD_DIR ?= .build
LAMBDA_TARGET = x86_64-unknown-linux-gnu

# Default target  
.DEFAULT_GOAL := help

# Install dependencies
install-deps:
	@echo "🦀 Installing Rust dependencies..."
	@which cargo-lambda > /dev/null || cargo install cargo-lambda
	@echo "✅ Dependencies installed!"

# Build Rust Lambda function following reference pattern
build: install-deps
	@echo "🔨 Building Rust MCP server for Lambda..."
	@mkdir -p $(BUILD_DIR)
	cargo lambda build --release --target $(LAMBDA_TARGET)
	@mkdir -p "$(BUILD_DIR)/rust-mcp-server"
	@if [ -f "target/lambda/step-functions-agents-mcp-server/bootstrap" ]; then \
		cp "target/lambda/step-functions-agents-mcp-server/bootstrap" "$(BUILD_DIR)/rust-mcp-server/bootstrap"; \
	elif [ -f "target/lambda/bootstrap/bootstrap" ]; then \
		cp "target/lambda/bootstrap/bootstrap" "$(BUILD_DIR)/rust-mcp-server/bootstrap"; \
	else \
		echo "❌ Error: Could not find bootstrap binary"; \
		exit 1; \
	fi
	@echo "✅ Built Lambda bootstrap at: $(BUILD_DIR)/rust-mcp-server/bootstrap"

# Local development build
local:
	@echo "🏠 Building for local development..."
	cargo build --release
	@echo "✅ Local build complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	cargo test

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	cargo clean
	rm -rf $(BUILD_DIR)
	@echo "✅ Clean complete!"

# Check if bootstrap exists and is executable
check:
	@if [ -f "$(BUILD_DIR)/rust-mcp-server/bootstrap" ]; then \
		echo "✅ Bootstrap exists: $(BUILD_DIR)/rust-mcp-server/bootstrap"; \
		ls -la "$(BUILD_DIR)/rust-mcp-server/bootstrap"; \
		file "$(BUILD_DIR)/rust-mcp-server/bootstrap"; \
	else \
		echo "❌ Bootstrap not found: $(BUILD_DIR)/rust-mcp-server/bootstrap"; \
		echo "Run 'make build' first"; \
		exit 1; \
	fi

# Package for deployment (create zip)
package: build
	@echo "📦 Creating deployment package..."
	@cd "$(BUILD_DIR)/rust-mcp-server" && zip -r ../../mcp-server-lambda.zip bootstrap
	@echo "✅ Package created: mcp-server-lambda.zip"

# Development server (run locally)
dev: local
	@echo "🚀 Starting local development server..."
	@echo "Set environment variables if needed:"
	@echo "  export AWS_REGION=us-east-1"
	@echo "  export API_KEY_TABLE_NAME=your-table-name"
	./target/release/step-functions-agents-mcp-server

# CI/CD helper
ci-build: build
	@echo "✅ CI build complete!"

# Show help
help:
	@echo "Step Functions Agents MCP Server - Rust Build"
	@echo ""
	@echo "Available commands:"
	@echo "  build          Build Rust Lambda function using cargo-lambda"
	@echo "  local          Build for local development"
	@echo "  test           Run tests"
	@echo "  clean          Clean build artifacts"
	@echo "  package        Create deployment zip package"
	@echo "  check          Check if bootstrap binary exists"
	@echo "  dev            Run local development server"
	@echo "  install-deps   Install required Rust tools"
	@echo "  ci-build       Build for CI/CD"
	@echo "  help           Show this help message"
	@echo ""
	@echo "Environment variables:"
	@echo "  BUILD_DIR      Build output directory (default: .build)"
	@echo ""
	@echo "Examples:"
	@echo "  make build              # Build for Lambda deployment"
	@echo "  make dev                # Run locally for development"
	@echo "  make clean build        # Clean and rebuild"