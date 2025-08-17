# Makefile for web-research Lambda function
# This builds a Go Lambda function for ARM64 architecture

# Variables
BINARY_NAME=bootstrap
GO_FILES=main.go perplexity.go toolsecrets.go
ARTIFACTS_DIR?=.

# Default target
.PHONY: all
all: build

# Build for Lambda deployment (via CDK)
.PHONY: build-WebResearchFunction
build-WebResearchFunction:
	GOOS=linux GOARCH=arm64 go build -tags lambda.norpc -o $(BINARY_NAME) $(GO_FILES)
	cp ./$(BINARY_NAME) $(ARTIFACTS_DIR)/.

# Build for local development/testing
.PHONY: build
build:
	GOOS=linux GOARCH=arm64 go build -tags lambda.norpc -o $(BINARY_NAME) $(GO_FILES)
	@echo "✅ Built $(BINARY_NAME) for Lambda (linux/arm64)"

# Build and deploy (requires CDK)
.PHONY: deploy
deploy: build
	@echo "📦 Deploying web-research Lambda..."
	cd ../../../ && npx cdk deploy WebResearchToolStack-prod --require-approval never

# Clean build artifacts
.PHONY: clean
clean:
	rm -f $(BINARY_NAME)
	@echo "🧹 Cleaned build artifacts"

# Run tests
.PHONY: test
test:
	go test -v ./...

# Format code
.PHONY: fmt
fmt:
	go fmt ./...
	@echo "✨ Code formatted"

# Run linter
.PHONY: lint
lint:
	golangci-lint run ./...

# Check for vulnerabilities
.PHONY: vuln
vuln:
	go list -json -m all | nancy sleuth

# Build for multiple architectures (useful for testing)
.PHONY: build-all
build-all:
	@echo "Building for Linux AMD64..."
	GOOS=linux GOARCH=amd64 go build -tags lambda.norpc -o $(BINARY_NAME)-amd64 $(GO_FILES)
	@echo "Building for Linux ARM64..."
	GOOS=linux GOARCH=arm64 go build -tags lambda.norpc -o $(BINARY_NAME)-arm64 $(GO_FILES)
	@echo "Building for Darwin AMD64..."
	GOOS=darwin GOARCH=amd64 go build -o $(BINARY_NAME)-darwin-amd64 $(GO_FILES)
	@echo "Building for Darwin ARM64..."
	GOOS=darwin GOARCH=arm64 go build -o $(BINARY_NAME)-darwin-arm64 $(GO_FILES)
	@echo "✅ Built for all architectures"

# Local testing with environment variables
.PHONY: run-local
run-local:
	@echo "Running locally (requires PPLX_API_KEY environment variable)..."
	go run $(GO_FILES)

# Get dependencies
.PHONY: deps
deps:
	go mod download
	go mod tidy
	@echo "📦 Dependencies updated"

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make build              - Build Lambda binary for deployment"
	@echo "  make build-WebResearchFunction - Build for CDK (used by CDK)"
	@echo "  make deploy            - Build and deploy via CDK"
	@echo "  make clean             - Remove build artifacts"
	@echo "  make test              - Run tests"
	@echo "  make fmt               - Format code"
	@echo "  make lint              - Run linter (requires golangci-lint)"
	@echo "  make vuln              - Check for vulnerabilities (requires nancy)"
	@echo "  make build-all         - Build for multiple architectures"
	@echo "  make run-local         - Run locally for testing"
	@echo "  make deps              - Update dependencies"
	@echo "  make help              - Show this help message"