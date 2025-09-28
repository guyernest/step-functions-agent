"""
PrepareAgentContext Lambda function.
Injects structured output tools into agent context based on agent configuration.
"""

import json
import boto3
import os
from typing import Dict, Any, List, Optional

dynamodb = boto3.resource('dynamodb')
AGENT_REGISTRY_TABLE = os.environ.get('AGENT_REGISTRY_TABLE', 'AgentRegistry')

def get_agent_config(agent_id: str) -> Dict[str, Any]:
    """Retrieve agent configuration from DynamoDB registry."""
    table = dynamodb.Table(AGENT_REGISTRY_TABLE)

    try:
        response = table.get_item(Key={'agentId': agent_id})
        return response.get('Item', {})
    except Exception as e:
        print(f"Error fetching agent config: {str(e)}")
        return {}

def build_structured_output_tool(
    schema_config: Dict[str, Any],
    tool_name: str = "return_structured"
) -> Dict[str, Any]:
    """Build the structured output tool definition."""

    # Extract schema and metadata
    schema = schema_config.get('schema', {})
    description = schema_config.get('description', 'Return structured output')
    examples = schema_config.get('examples', [])

    # Build tool definition in OpenAI format
    tool = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": schema
        }
    }

    # Add examples as part of description if available
    if examples:
        example_text = json.dumps(examples[0], indent=2)
        tool["function"]["description"] += f"\n\nExample output:\n{example_text}"

    return tool

def enhance_system_prompt(
    current_prompt: str,
    tool_name: str,
    schema_name: str,
    examples: List[Dict]
) -> str:
    """Enhance system prompt to encourage structured output usage."""

    enhancement = f"""

STRUCTURED OUTPUT REQUIREMENT:
You MUST use the '{tool_name}' tool to provide your final answer after gathering all necessary information.
The output format is: {schema_name}

Instructions for using {tool_name}:
1. Gather all required information through the conversation
2. When you have all the data, call {tool_name} with the structured data
3. Ensure all required fields are populated
4. Use null for optional fields if data is unavailable"""

    if examples:
        enhancement += f"\n\nExample of expected output:\n{json.dumps(examples[0], indent=2)}"

    return current_prompt + enhancement

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler - prepares agent context with structured output tools.

    Input event structure:
    {
        "agent": "agent-id",
        "messages": [...],
        "tools": [...existing tools...],
        "system": "current system prompt",
        "output_format": "schema_name" (optional)
    }
    """

    # Extract input parameters
    agent_id = event.get('agent')
    messages = event.get('messages', [])
    existing_tools = event.get('tools', [])
    system_prompt = event.get('system', '')
    requested_format = event.get('output_format')

    # If no agent specified, return unchanged
    if not agent_id:
        return {
            'tools': existing_tools,
            'system': system_prompt,
            'messages': messages,
            'structured_output_config': None
        }

    # Get agent configuration
    agent_config = get_agent_config(agent_id)

    # Parse structuredOutput if it's a JSON string (standard for DynamoDB storage)
    structured_output_raw = agent_config.get('structuredOutput', {})
    if isinstance(structured_output_raw, str):
        try:
            structured_config = json.loads(structured_output_raw)
        except json.JSONDecodeError:
            print(f"Failed to parse structuredOutput JSON for agent {agent_id}")
            structured_config = {}
    else:
        structured_config = structured_output_raw

    # Check if structured output is enabled
    if not structured_config.get('enabled', False):
        return {
            'tools': existing_tools,
            'system': system_prompt,
            'messages': messages,
            'structured_output_config': None
        }

    # Determine which schema to use
    schemas = structured_config.get('schemas', {})
    default_schema = structured_config.get('defaultSchema', 'default')
    schema_name = requested_format or default_schema

    # Get the schema configuration
    if schema_name not in schemas:
        print(f"Schema '{schema_name}' not found, using default")
        schema_name = default_schema

    schema_config = schemas.get(schema_name, {})
    if not schema_config:
        print(f"No schema configuration found for {schema_name}")
        return {
            'tools': existing_tools,
            'system': system_prompt,
            'messages': messages,
            'structured_output_config': None
        }

    # Build the structured output tool
    tool_name = structured_config.get('toolName', 'return_structured')
    structured_tool = build_structured_output_tool(schema_config, tool_name)

    # Add tool to the tools list
    tools_with_structured = existing_tools.copy()
    tools_with_structured.append(structured_tool)

    # Enhance system prompt
    enhanced_system = enhance_system_prompt(
        system_prompt,
        tool_name,
        schema_name,
        schema_config.get('examples', [])
    )

    # Build structured output configuration for state machine
    structured_output_config = {
        'enabled': True,
        'enforced': structured_config.get('enforced', False),
        'tool_name': tool_name,
        'schema_name': schema_name,
        'schema': schema_config.get('schema', {}),
        'tool': structured_tool
    }

    return {
        'tools': tools_with_structured,
        'system': enhanced_system,
        'messages': messages,
        'structured_output_config': structured_output_config
    }