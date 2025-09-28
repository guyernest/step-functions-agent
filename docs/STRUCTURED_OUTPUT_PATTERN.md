# Structured Output Pattern for AI Agents

## Overview

The structured output pattern allows AI agents to return data in a predefined schema format, ensuring consistency and type safety for downstream processing. This is particularly useful for batch processing where all results must conform to the same structure.

## Architecture

The pattern is implemented in the `UnifiedLLMStepFunctionsGenerator` and provides:
- Automatic structured output tool generation
- Proper tool routing and state management
- Seamless integration with existing agent patterns

## How to Enable Structured Output

### 1. Define Your Schema

Create a JSON schema that describes your expected output structure:

```python
structured_output_schema = {
    "type": "object",
    "properties": {
        "field1": {
            "type": "string",
            "description": "Description of field1"
        },
        "field2": {
            "type": "number",
            "description": "Description of field2"
        },
        "field3": {
            "type": "boolean",
            "description": "Description of field3"
        }
    },
    "required": ["field1", "field2"]  # Specify required fields
}
```

### 2. Pass Schema to Generator

When creating your agent, pass the schema to the `UnifiedLLMStepFunctionsGenerator`:

```python
from stacks.agents.step_functions_generator_unified_llm import UnifiedLLMStepFunctionsGenerator

state_machine_definition = UnifiedLLMStepFunctionsGenerator.generate_unified_llm_agent_definition(
    agent_name="my-agent",
    unified_llm_arn=unified_llm_arn,
    tool_configs=tool_configs,
    system_prompt=system_prompt,
    structured_output_schema=structured_output_schema,  # Add this
    # ... other parameters
)
```

### 3. Update System Prompt

Include instructions in your system prompt about when and how to return structured output:

```python
system_prompt = """You are an agent that processes data and returns structured results.

After gathering all necessary information:
1. Use your tools to collect the required data
2. Call the return_<agent_name>_data function with the structured output
3. Ensure all required fields are populated

The structured output should include:
- field1: [explain what this field should contain]
- field2: [explain what this field should contain]
- field3: [explain what this field should contain]
"""
```

## What Happens Behind the Scenes

When you provide a `structured_output_schema`, the generator automatically:

1. **Creates a structured output tool** named `return_<agent_name>_data`
2. **Adds it to the tools list** alongside your regular tools
3. **Routes tool calls** to a special "Process Structured Output" state
4. **Detects structured output** in tool results
5. **Exits early** with the structured data when detected

## State Machine Flow

```
Load Agent Config
    ↓
Load Tools (includes structured output tool)
    ↓
Call LLM
    ↓
Check for Tool Calls
    ↓
Map Tool Calls → Route Tool Call
                    ├─ Regular Tool → Execute Tool
                    └─ Structured Output Tool → Process Structured Output
    ↓
Prepare Tool Results
    ↓
Check for Structured Output
    ├─ Yes → Success with Structured Output (exit)
    └─ No → Call LLM (loop)
```

## Example: Broadband Checker Agent

See `/stacks/agents/broadband_checker_structured_v2_refactored_stack.py` for a complete example:

```python
# Define the schema for broadband data
structured_output_schema = {
    "type": "object",
    "properties": {
        "exchange_station": {
            "type": "string",
            "description": "Name of the telephone exchange"
        },
        "download_speed": {
            "type": "number",
            "description": "Maximum download speed in Mbps"
        },
        "upload_speed": {
            "type": "number",
            "description": "Maximum upload speed in Mbps"
        }
    },
    "required": ["exchange_station", "download_speed", "upload_speed"]
}

# The agent will:
# 1. Call browser_broadband tool to get data
# 2. Parse the results
# 3. Call return_broadband_checker_structured_v2_data with structured output
# 4. Exit with the structured data
```

## Benefits

1. **Type Safety**: Ensures all outputs conform to the expected schema
2. **Consistency**: All agent invocations return the same structure
3. **Batch Processing**: Perfect for processing multiple items with uniform output
4. **Validation**: Schema validation can be added at the state machine level
5. **Reusability**: Single pattern works for all agents
6. **Maintainability**: Changes to the pattern benefit all agents

## Migration from Hardcoded State Machines

If you have an agent with a hardcoded state machine (like the original broadband-checker-v2):

1. Extract your structured output schema
2. Create a new stack using `UnifiedLLMStepFunctionsGenerator`
3. Pass the schema as `structured_output_schema`
4. Remove ~200+ lines of state machine definition code
5. Deploy and test

## Best Practices

1. **Keep schemas simple**: Complex nested structures can confuse the LLM
2. **Provide clear descriptions**: Help the LLM understand what each field should contain
3. **Use appropriate types**: string, number, boolean, array, object
4. **Document required fields**: Clearly mark which fields are mandatory
5. **Test with examples**: Ensure the LLM consistently returns valid structured output

## Troubleshooting

### Issue: Agent doesn't return structured output
- Check that the system prompt instructs the agent to call `return_<agent_name>_data`
- Verify the schema is being passed to the generator
- Ensure the agent name in the prompt matches the actual agent name

### Issue: Missing tools field error
- This should be automatically handled by the unified generator
- Ensure you're using the latest version of the generator
- Check that tools are passed through all state transitions

### Issue: Structured output not detected
- Verify the tool result has `type: "structured_output"`
- Check the "Check for Structured Output" state condition
- Ensure the tool result is properly formatted

## Future Enhancements

Potential improvements to the pattern:
- Schema validation in the state machine
- Automatic retry on validation failure
- Support for multiple structured outputs per invocation
- Integration with data validation libraries
- Automatic documentation generation from schemas