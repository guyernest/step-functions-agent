"""
Generate Batch Config Tool
Creates configuration for the batch processor
"""

import json
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Generate configuration for batch processor

    Tool input:
    {
        "name": "generate_batch_config",
        "input": {
            "csv_columns": ["col1", "col2"],
            "agent_name": "company-enrichment-agent",
            "input_mapping": {...},
            "output_mapping": {...}
        }
    }
    """
    try:
        tool_input = event.get('input', {})

        # Get required fields - be flexible about parameter names
        csv_columns = tool_input.get('csv_columns', [])
        agent_name = tool_input['agent_name']

        # Handle input and output mappings
        input_mapping = tool_input.get('input_mapping', {})
        output_mapping = tool_input.get('output_mapping', {})

        # Extract legacy parameters if present
        column_mappings = input_mapping if isinstance(input_mapping, dict) else {}
        output_fields = list(output_mapping.keys()) if isinstance(output_mapping, dict) else []
        max_concurrency = tool_input.get('max_concurrency', 10)
        include_original = tool_input.get('include_original', True)
        add_metadata = tool_input.get('add_metadata', True)

        # Generate the batch processor configuration
        # Note: This tool generates config structure but doesn't need the CSV URI
        config = {
            "target": {
                "type": "agent",
                "name": agent_name
            },
            "input_mapping": {
                "column_mappings": column_mappings,
                "prompt_template": tool_input.get(
                    'prompt_template',
                    "Process this data and return structured output"
                )
            },
            "output_mapping": {
                "structured_output_fields": output_fields,
                "include_original": include_original,
                "add_metadata": add_metadata
            },
            "execution_config": {
                "max_concurrency": max_concurrency,
                "timeout_seconds": tool_input.get('timeout_seconds', 300)
            }
        }

        # Add any static values if provided
        if tool_input.get('static_values'):
            config['input_mapping']['static_values'] = tool_input['static_values']

        # Add transformations if provided
        if tool_input.get('transformations'):
            config['input_mapping']['transformations'] = tool_input['transformations']

        result = {
            "config": config,
            "summary": {
                "target_agent": agent_name,
                "mapped_columns": len(column_mappings),
                "output_fields": len(output_fields),
                "max_concurrency": max_concurrency,
                "include_original_data": include_original
            },
            "message": "Batch processor configuration generated successfully"
        }

        return {
            "type": "tool_result",
            "name": event.get('name', 'generate_batch_config'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error generating config: {e}")
        return {
            "type": "tool_result",
            "name": event.get('name', 'generate_batch_config'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps({
                "error": str(e),
                "message": f"Failed to generate configuration: {e}"
            })
        }