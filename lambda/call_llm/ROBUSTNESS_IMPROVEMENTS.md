# LLM Call Robustness Improvements

## Overview

This document describes the robustness improvements implemented to handle LLM provider format changes, ensuring the system remains stable when providers like OpenAI release new models (e.g., GPT-5) or modify their API response formats.

## Key Improvements Implemented

### 1. Dynamic Model Configuration

**Previous Issue:** Model IDs were hardcoded, preventing flexibility across different agents.

**Solution:** Model IDs are now passed through the event payload from the Step Functions flow:
- Each agent can specify its preferred model in the agent registry
- The model ID is extracted from the event and passed to handlers
- Defaults are maintained for backward compatibility

**Example Usage:**
```python
# In Step Functions payload
{
    "model_id": "gpt-4o-mini",  # Or "claude-3-opus", "gpt-5", etc.
    "system": "...",
    "messages": [...],
    "tools": [...]
}
```

### 2. Defensive Field Access Utilities

**Location:** `/lambda/call_llm/lambda_layer/python/common/base_llm.py`

New utilities added to BaseLLM class:

#### `safe_get_nested(data, path, default=None)`
Safely navigates nested data structures using dot notation:
```python
# Instead of: completion.choices[0].message.content
# Use: self.safe_get_nested(completion, "choices.0.message.content", "")

# Handles missing fields gracefully
content = self.safe_get_nested(response, "choices.0.message.content", default="")
```

#### `validate_required_fields(data, required_fields, context="")`
Validates presence of required fields before processing:
```python
required = ["choices.0.message", "usage.prompt_tokens"]
validation = self.validate_required_fields(response, required, "OpenAI response")
if not all(validation.values()):
    # Handle missing fields
```

#### `safe_extract_field(data, field_paths, default=None)`
Tries multiple possible field paths (for version compatibility):
```python
# Handle different token field names across versions
input_tokens = self.safe_extract_field(
    response, 
    ["usage.prompt_tokens", "usage.input_tokens", "tokens.input"],
    default=0
)
```

#### `detect_response_format(response)`
Automatically detects response format characteristics:
```python
format_info = self.detect_response_format(response)
# Returns: {'has_choices': True, 'model_info': 'gpt-4o', ...}
```

#### `create_error_response(error_msg, context=None)`
Creates standardized error responses for graceful degradation:
```python
if not valid_response:
    return self.create_error_response(
        "Invalid response format", 
        {"model": self.model_id, "format": format_info}
    )
```

### 3. Enhanced OpenAI Handler Robustness

**Location:** `/lambda/call_llm/functions/openai_llm/openai_handler.py`

**Improvements:**
- Defensive field access throughout response parsing
- Graceful handling of incomplete tool calls
- JSON parsing error recovery with fallback to empty dict
- Support for alternative field names (GPT-5 compatibility)
- Comprehensive error logging with context

**Example:**
```python
# Old vulnerable code:
choice = completion.choices[0]
message = choice.message

# New robust code:
choice = self.safe_extract_field(completion, ['choices.0', 'results.0'])
if not choice:
    return self.create_error_response("No valid choice found", format_info)
```

### 4. Error Recovery Mechanisms

All handlers now include:
- Try-catch blocks around API calls
- Graceful degradation for malformed responses
- Detailed error logging with model context
- Standardized error response format

### 5. Comprehensive Test Coverage

**Location:** `/lambda/call_llm/tests/test_robustness_improvements.py`

New test suite covering:
- Defensive programming utilities
- Malformed response handling
- Incomplete tool call recovery
- JSON parsing failure recovery
- Alternative field name support
- Future format compatibility

## Provider-Specific Considerations

### OpenAI (GPT-4, GPT-5, and beyond)
- Supports both `prompt_tokens`/`completion_tokens` and `input_tokens`/`output_tokens`
- Handles changes from `choices` to potential `results` array
- Robust tool call parsing with incomplete data handling

### Anthropic (Claude)
- Dynamic model selection (Claude 3 Opus, Sonnet, etc.)
- Safe content block type handling
- Cache control compatibility

### AWS Bedrock
- Model-specific format variations handled
- Support for different tool specification formats

## Best Practices for Future Development

1. **Always use defensive field access**
   - Never use direct array/dict access without checks
   - Use `safe_get_nested()` for all external API responses

2. **Implement format detection**
   - Call `detect_response_format()` to understand response structure
   - Log format changes for monitoring

3. **Provide fallbacks**
   - Use `safe_extract_field()` with multiple possible paths
   - Always provide sensible defaults

4. **Create detailed error responses**
   - Include model ID and context in errors
   - Log sufficient detail for debugging

5. **Test with malformed data**
   - Include tests for missing fields
   - Test partial/incomplete responses
   - Verify graceful degradation

## Monitoring Recommendations

To detect format changes early:

1. **Log format detection results**
   - Monitor `detect_response_format()` output
   - Alert on unexpected format characteristics

2. **Track error rates by provider**
   - Monitor error responses by model ID
   - Identify patterns in failures

3. **Version tracking**
   - Log model versions/IDs with responses
   - Track when new models are introduced

## Migration Guide for New Providers

When adding a new LLM provider:

1. Extend `BaseLLM` class
2. Use defensive utilities for all field access
3. Implement comprehensive error handling
4. Add format detection logging
5. Create tests with malformed responses
6. Document provider-specific quirks

## Example: Handling Future Format Changes

```python
# Hypothetical GPT-5 format change handling
def convert_to_json(self, completion):
    try:
        # Detect format version
        format_info = self.detect_response_format(completion)
        
        # Try multiple extraction patterns
        message = self.safe_extract_field(
            completion,
            [
                'choices.0.message',      # GPT-4 format
                'results.0.message',       # Hypothetical GPT-5
                'completions.0.response'   # Alternative future format
            ]
        )
        
        if not message:
            return self.create_error_response(
                "Unrecognized response format",
                format_info
            )
        
        # Continue processing...
        
    except Exception as e:
        logger.error(f"Failed to parse response: {e}")
        return self.create_error_response(str(e))
```

## Testing the Improvements

Run the robustness test suite:
```bash
cd /lambda/call_llm
python -m pytest tests/test_robustness_improvements.py -v
```

## Conclusion

These robustness improvements significantly enhance the system's ability to handle:
- Provider API format changes
- New model releases
- Unexpected response structures
- Partial or malformed responses

The defensive programming patterns and comprehensive error handling ensure the system degrades gracefully rather than failing completely when encountering unexpected formats.