# Test Fixtures

This directory contains test input and response fixtures for testing agents and tools.

## Test Input Files

### Agent Test Events
- `test_claude_event.json` - Basic Claude agent test event
- `test_claude_downgrade.json` - Testing model downgrade scenarios
- `test_dynamic_agent_with_code.json` - Dynamic agent with code execution

### Tool-Specific Tests

#### Google Maps Tool
- `test_google_maps_directions.json` - Directions API test
- `test_google_maps_geocode.json` - Geocoding test
- `test_google_maps_places_search.json` - Places search test
- `test_google_maps_reverse_geocode.json` - Reverse geocoding test

#### Code Execution Tool
- `test_execute_code.json` - Code execution test event

#### Batch Processing
- `test_batch_processor_input.json` - Batch processor test input
- `test_travel_time_batch_input.json` - Travel time batch processing test

#### LLM Provider Tests
- `test_gemini_llm.json` - Gemini LLM integration test
- `test_gemini_simple.json` - Simple Gemini test

#### Monitoring
- `test_monitor_execution_event.json` - Execution monitoring test

## Response Files

- `response.json` - Generic response fixture
- `response_execute_code.json` - Code execution response example

## Usage

These fixtures can be used with:

```bash
# Test a Lambda function locally
aws lambda invoke \
  --function-name MyFunction \
  --payload file://tests/fixtures/test_claude_event.json \
  output.json

# Or with SAM CLI
sam local invoke MyFunction -e tests/fixtures/test_claude_event.json

# Or with the test scripts
python tests/test_config_locally.py
```

## Adding New Fixtures

When adding new test fixtures:

1. **Name clearly** - Use descriptive names that indicate what is being tested
2. **Document** - Add entry to this README
3. **Minimal** - Keep test data minimal but realistic
4. **Sanitize** - Remove any sensitive data (API keys, credentials, PII)

## File Format

All fixtures follow the Lambda event format:

```json
{
  "name": "tool_name",
  "id": "unique_id",
  "input": {
    // Tool-specific parameters
  }
}
```
