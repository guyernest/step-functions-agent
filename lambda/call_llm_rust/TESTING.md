# Testing the Unified LLM Service

This document explains how to test the Rust LLM service, which tests the actual Lambda code that Step Functions will call.

## Overview

The tests exercise the complete transformation pipeline:
1. **Input**: Unified format (from Step Functions)
2. **Transform**: Convert to provider-specific format
3. **API Call**: Send to LLM provider
4. **Transform Back**: Convert response to unified format
5. **Output**: Unified format (back to Step Functions)

## Prerequisites

### API Keys

Set your API keys using one of these methods:

#### Option 1: Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### Option 2: .env File
```bash
cd lambda/call_llm_rust
cp .env.example .env
# Edit .env with your actual API keys
```

## Running Tests

All test commands are available through the Makefile:

### Unit Tests
```bash
# Run unit tests (no API calls)
make test-llm-rust
```

### Integration Tests

These tests call actual LLM APIs through our service:

```bash
# Test all providers
make test-llm-rust-integration

# Test OpenAI transformer only
make test-llm-rust-openai

# Test Anthropic transformer only
make test-llm-rust-anthropic
```

## What the Tests Verify

### 1. Message Transformation
- Unified format → Provider format (request)
- Provider format → Unified format (response)

### 2. Tool Calling Flow
- Tool definition transformation
- Tool call detection and extraction
- Tool result handling

### 3. Metadata Tracking
- Token usage counting
- Latency measurement
- Model ID tracking

### 4. Secret Management
- API key retrieval (from env vars during tests)
- Proper authentication headers

## Test Structure

```rust
// Step 1: Create unified format request (what Step Functions sends)
let invocation = LLMInvocation {
    provider_config: { ... },        // Provider settings
    messages: [ UnifiedMessage ],    // Unified format
    tools: [ UnifiedTool ],         // Tool definitions
};

// Step 2: Process through our service
let response = service.process(invocation).await?;

// Step 3: Verify unified format response
assert!(response.function_calls.is_some());  // Tool was called
assert!(response.metadata.tokens_used > 0);  // Tokens tracked
```

## Example Test Flow

1. User: "What's the weather in Tokyo?"
2. Service transforms to provider format and sends to LLM
3. LLM calls: `get_weather(location="Tokyo, Japan")`
4. Service transforms tool call to unified format
5. Test provides: "Sunny, 22°C"
6. Service sends tool result back to LLM
7. LLM responds: "The weather in Tokyo is sunny..."
8. Service transforms final response to unified format

## Troubleshooting

### "No API keys found"
- Ensure environment variables are exported
- Or create `.env` file with your keys

### "Failed to fetch secret"
- Tests use environment variables, not AWS Secrets Manager
- Make sure the key name matches exactly (e.g., `OPENAI_API_KEY`)

### Test failures
- Check API key validity
- Ensure you have credits/quota with the provider
- Review the error message for specific issues

## CI/CD Considerations

For CI/CD pipelines:
1. Store API keys as secrets in your CI system
2. Export them as environment variables before running tests
3. Consider using test-specific API keys with limited quotas
4. Run integration tests only on main branch or release builds