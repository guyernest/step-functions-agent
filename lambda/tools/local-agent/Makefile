.PHONY: build deploy clean install help

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "Local Automation Tool - Rust Lambda Build"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install cargo-lambda"
	@echo "  make build       - Build the Rust Lambda function"
	@echo "  make deploy      - Prepare deployment directory"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make all         - Build and prepare for deployment"
	@echo ""
	@echo "Note: This builds only the Lambda function, not the desktop app"

# Install cargo-lambda if not already installed
install:
	@echo "Installing cargo-lambda..."
	@cargo install cargo-lambda || echo "cargo-lambda already installed"

# Build the Rust Lambda function for ARM64
build: install
	@echo "Building Rust Lambda function..."
	@cargo lambda build --release --arm64
	@echo "Build complete! Binary at: target/lambda/local_sfn_agent/bootstrap"

# Prepare deployment directory with only the bootstrap binary
deploy: build
	@echo "Preparing deployment directory..."
	@mkdir -p deployment
	@cp target/lambda/local_sfn_agent/bootstrap deployment/
	@echo "Deployment ready! Size: $$(du -h deployment/bootstrap | cut -f1)"
	@echo "Directory contents:"
	@ls -lah deployment/

# Clean build artifacts but keep source
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf deployment/
	@cargo clean
	@echo "Clean complete!"

# Build and deploy in one step
all: build deploy
	@echo "Ready for CDK deployment!"