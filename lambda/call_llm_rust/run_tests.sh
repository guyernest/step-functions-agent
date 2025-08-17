#!/bin/bash

# Script to run the Rust LLM service tests
# This script helps run integration tests with proper API key configuration

set -e

echo "🧪 Rust LLM Service Test Runner"
echo "================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Checking environment variables..."
    
    # Check for API keys in environment
    if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ No API keys found in environment or .env file"
        echo ""
        echo "To run integration tests, you need to provide API keys:"
        echo "1. Copy .env.example to .env and add your keys, OR"
        echo "2. Export them as environment variables:"
        echo "   export OPENAI_API_KEY='sk-...'"
        echo "   export ANTHROPIC_API_KEY='sk-ant-...'"
        exit 1
    fi
else
    echo "✅ Found .env file"
fi

# Menu for test selection
echo ""
echo "Select test to run:"
echo "1. Unit tests only"
echo "2. OpenAI tool calling test"
echo "3. Anthropic tool calling test"
echo "4. All provider tests"
echo "5. Build only (no tests)"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo "Running unit tests..."
        cargo test --lib
        ;;
    2)
        echo "Running OpenAI tool calling test..."
        cargo test --test tool_calling_test test_openai -- --ignored --nocapture
        ;;
    3)
        echo "Running Anthropic tool calling test..."
        cargo test --test tool_calling_test test_anthropic -- --ignored --nocapture
        ;;
    4)
        echo "Running all provider tests..."
        cargo test --test tool_calling_test test_all_providers -- --ignored --nocapture
        ;;
    5)
        echo "Building project..."
        cargo build --release
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"