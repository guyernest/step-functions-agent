"""
Validate Agent Compatibility Tool
Checks if an agent has structured output capability
"""

import json
import boto3
import os
from typing import Dict, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Validate that an agent has structured output capability

    Tool input:
    {
        "name": "validate_agent_compatibility",
        "input": {
            "agent_name": "company-enrichment-agent"
        }
    }
    """
    try:
        tool_input = event.get('input', {})
        agent_name = tool_input['agent_name']

        # Get agent registry table
        table_name = os.environ.get('AGENT_REGISTRY_TABLE')
        if not table_name:
            raise ValueError("Agent registry table not configured")

        table = dynamodb.Table(table_name)

        # Look up agent - need to query since we don't have the version
        # Query for the latest version of the agent
        response = table.query(
            KeyConditionExpression='agent_name = :name',
            ExpressionAttributeValues={
                ':name': agent_name
            },
            ScanIndexForward=False,  # Sort descending to get latest version first
            Limit=1
        )

        if 'Items' not in response or len(response['Items']) == 0:
            return {
                "type": "tool_result",
                "name": event.get('name', 'validate_agent_compatibility'),
                "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
                "content": json.dumps({
                    "compatible": False,
                    "error": f"Agent '{agent_name}' not found in registry",
                    "suggestion": "Please check the agent name and try again"
                })
            }

        agent = response['Items'][0]

        # Check for structured output capability - be flexible about how it's stored
        # Try different field names and formats
        structured_output = None
        is_enabled = False

        # Option 1: Check structured_output field (snake_case)
        if 'structured_output' in agent:
            structured_output = agent['structured_output']
            if isinstance(structured_output, str):
                try:
                    structured_output = json.loads(structured_output)
                except:
                    pass
            is_enabled = structured_output.get('enabled', False) if isinstance(structured_output, dict) else False

        # Option 2: Check structuredOutput field (camelCase)
        if not is_enabled and 'structuredOutput' in agent:
            structured_output = agent['structuredOutput']
            if isinstance(structured_output, str):
                try:
                    structured_output = json.loads(structured_output)
                except:
                    pass
            is_enabled = structured_output.get('enabled', False) if isinstance(structured_output, dict) else False

        # Option 3: Check if agent has any return_*_data tool (indicates structured output)
        if not is_enabled and 'tools' in agent:
            tools = agent['tools']
            if isinstance(tools, str):
                try:
                    tools = json.loads(tools)
                except:
                    tools = []

            # Check for any tool that starts with 'return_' and ends with '_data'
            if isinstance(tools, list):
                for tool in tools:
                    # Handle both string tool names and dict tool configs
                    tool_name = tool if isinstance(tool, str) else tool.get('tool_name', '') if isinstance(tool, dict) else ''
                    if isinstance(tool_name, str) and tool_name.startswith('return_') and tool_name.endswith('_data'):
                        is_enabled = True
                        if not structured_output:
                            structured_output = {'enabled': True, 'toolName': tool_name}
                        break

        # Option 4: Check metadata for type indicating structured output
        if not is_enabled and 'metadata' in agent:
            metadata = agent['metadata']
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                    if metadata.get('type') == 'structured-output-agent':
                        is_enabled = True
                        if not structured_output:
                            structured_output = {'enabled': True}
                except:
                    pass

        if not is_enabled:
            return {
                "type": "tool_result",
                "name": event.get('name', 'validate_agent_compatibility'),
                "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
                "content": json.dumps({
                    "compatible": False,
                    "agent_name": agent_name,
                    "structured_output_enabled": False,
                    "error": f"Agent '{agent_name}' does not have structured output enabled",
                    "message": "This agent cannot be used with batch processor. All agents must implement structured output.",
                    "suggestion": "Please choose an agent that implements the 'return_structured_data' tool"
                })
            }

        # Agent is compatible - return details
        result = {
            "compatible": True,
            "agent_name": agent_name,
            "structured_output_enabled": True,
            "message": f"Agent '{agent_name}' is compatible with batch processing"
        }

        # Add state machine ARN - check different possible fields
        state_machine_arn = agent.get('state_machine_arn') or agent.get('agentArn', '')
        if state_machine_arn:
            result['state_machine_arn'] = state_machine_arn

        # Add description
        description = agent.get('description', '')
        if description:
            result['description'] = description

        # Add structured output details if available
        if structured_output and isinstance(structured_output, dict):
            # Tool name
            if 'toolName' in structured_output:
                result['structured_output_tool'] = structured_output['toolName']

            # Schema information
            if 'schemas' in structured_output:
                result['schemas'] = structured_output['schemas']
                # Extract field names from schemas
                output_fields = []
                for schema_name, schema_def in structured_output.get('schemas', {}).items():
                    if 'schema' in schema_def and 'properties' in schema_def['schema']:
                        output_fields.extend(schema_def['schema']['properties'].keys())
                if output_fields:
                    result['output_fields'] = list(set(output_fields))
            elif 'schema' in structured_output:
                result['output_schema'] = structured_output['schema']
                # Extract fields from schema
                if 'properties' in structured_output['schema']:
                    result['output_fields'] = list(structured_output['schema']['properties'].keys())
            elif 'output_fields' in structured_output:
                result['output_fields'] = structured_output['output_fields']

            # Default schema if specified
            if 'defaultSchema' in structured_output:
                result['default_schema'] = structured_output['defaultSchema']

            # Schema version
            if 'schema_version' in structured_output:
                result['schema_version'] = structured_output['schema_version']

            # Field descriptions if available
            if 'field_descriptions' in structured_output:
                result['field_descriptions'] = structured_output['field_descriptions']

        return {
            "type": "tool_result",
            "name": event.get('name', 'validate_agent_compatibility'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error validating agent: {e}")
        return {
            "type": "tool_result",
            "name": event.get('name', 'validate_agent_compatibility'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps({
                "compatible": False,
                "error": str(e),
                "message": f"Failed to validate agent: {e}"
            })
        }