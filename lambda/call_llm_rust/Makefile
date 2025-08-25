.PHONY: build clean test deploy check

# Build the Rust Lambda for ARM64 with ADOT observability
build:
	@echo "Building Rust Lambda for ARM64 architecture..."
	cargo lambda build --release --arm64
	@echo "Copying collector.yaml to build output..."
	@cp collector.yaml target/lambda/bootstrap/ 2>/dev/null || cp collector.yaml target/lambda/ 2>/dev/null || true
	@echo "Build complete! Output: target/lambda/"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	cargo clean
	rm -rf target/lambda

# Run tests
test:
	@echo "Running tests..."
	cargo test

# Check code (compile without building)
check:
	@echo "Checking code..."
	cargo check

# Install dependencies (cargo-lambda)
install-deps:
	@echo "Checking for cargo-lambda..."
	@command -v cargo-lambda >/dev/null 2>&1 || { \
		echo "Installing cargo-lambda..."; \
		brew tap cargo-lambda/cargo-lambda; \
		brew install cargo-lambda; \
	}

# Full deploy preparation
deploy: install-deps clean build
	@echo "Ready for deployment!"
	@echo "Lambda package location: target/lambda/"
	@ls -la target/lambda/ 2>/dev/null || ls -la target/lambda/bootstrap/ 2>/dev/null

# Local development build
dev:
	cargo build
	cargo check

# Format code
fmt:
	cargo fmt

# Run clippy linter
lint:
	cargo clippy -- -D warnings