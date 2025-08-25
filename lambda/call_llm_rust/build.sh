#!/bin/bash

# Build script for Rust Lambda with ADOT observability
# Uses cargo-lambda for cross-compilation

set -e

echo "Building Rust Lambda for ARM64 architecture..."

# Check if cargo-lambda is installed
if ! command -v cargo-lambda &> /dev/null; then
    echo "cargo-lambda is not installed. Installing..."
    brew tap cargo-lambda/cargo-lambda
    brew install cargo-lambda
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf target/lambda

# Build the Lambda function
echo "Building Lambda function..."
cargo lambda build --release --arm64

# Copy collector.yaml to the output directory
echo "Copying collector.yaml to build output..."
cp collector.yaml target/lambda/bootstrap/

echo "Build complete!"
echo "Output directory: target/lambda/bootstrap/"
echo ""
echo "Files in output:"
ls -la target/lambda/bootstrap/

echo ""
echo "To deploy, the CDK will use this directory for the Lambda code asset."