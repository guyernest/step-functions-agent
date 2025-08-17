# Test Events for Unified Rust LLM Service

This document provides test events you can use to test the deployed Rust LLM Lambda function in the AWS Console.

## Available Test Events

The `test_events.json` file contains several pre-configured test events:

### 1. Simple Text Generation Tests
- **`openai_simple_test`** - Basic text generation with OpenAI
- **`anthropic_simple_test`** - Basic text generation with Anthropic Claude  
- **`gemini_simple_test`** - Basic text generation with Google Gemini

### 2. Tool Calling Tests
- **`openai_tool_calling_test`** - Weather tool calling with OpenAI
- **`anthropic_tool_calling_test`** - Time tool calling with Anthropic
- **`gemini_tool_calling_test`** - Math tool calling with Gemini

### 3. Advanced Tests
- **`conversation_with_tool_result`** - Complete conversation flow with tool execution

## How to Use in Lambda Console

1. **Navigate to AWS Lambda Console**
   - Find your function: `shared-unified-rust-llm-prod`

2. **Create a Test Event**
   - Go to the "Test" tab
   - Click "Create new event"
   - Choose "Custom event"
   - Copy one of the test events from `test_events.json`
   - Give it a descriptive name (e.g., "OpenAI Simple Test")

3. **Run the Test**
   - Click "Test" to execute
   - Check the execution results and logs

## Expected Response Format

The Rust service returns a unified response format:

```json
{
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "text",
        "text": "The response text from the LLM"
      }
    ]
  },
  "function_calls": [
    {
      "id": "call_123",
      "name": "tool_name",
      "input": {"param": "value"}
    }
  ],
  "metadata": {
    "model_id": "gpt-4o-mini",
    "provider_id": "openai",
    "latency_ms": 1234,
    "tokens_used": {
      "input_tokens": 20,
      "output_tokens": 15,
      "total_tokens": 35
    },
    "stop_reason": "stop"
  }
}
```

## Troubleshooting

### Common Issues

1. **Secret Access Errors**
   - Ensure the Lambda has permission to access `/ai-agent/llm-secrets/prod`
   - Verify API keys are properly stored in AWS Secrets Manager

2. **Timeout Errors**
   - The function timeout is set to 90 seconds
   - Network issues may cause timeouts with external APIs

3. **Transform Errors**
   - Check that provider_id matches request_transformer and response_transformer
   - Supported transformers: `openai_v1`, `anthropic_v1`, `gemini_v1`

### Logs and Debugging

- Check CloudWatch logs at `/aws/lambda/shared-llm-refactored-prod`
- Enable RUST_LOG=debug for verbose logging
- Function includes X-Ray tracing for performance monitoring

## Provider-Specific Notes

### OpenAI
- Requires `auth_header_prefix: "Bearer "`
- Uses endpoint: `https://api.openai.com/v1/chat/completions`

### Anthropic
- No auth header prefix needed
- Uses endpoint: `https://api.anthropic.com/v1/messages`

### Gemini
- Uses API key authentication with `x-goog-api-key` header
- Endpoint includes model in URL path

## Testing Tool Calling Flow

To test the complete tool calling flow:

1. Start with a tool calling test (e.g., `openai_tool_calling_test`)
2. The response will include `function_calls` with tool invocations
3. Use `conversation_with_tool_result` to test providing tool results back
4. The final response should incorporate the tool result data

This tests the complete unified format transformation pipeline that Step Functions will use.