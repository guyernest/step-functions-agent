"""
Output Mapper Lambda
Transforms agent/tool output back to enriched row format
Used within Distributed Map iterator
"""

import json
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Extract structured output from agent response and map to CSV columns

    Event structure:
    {
        "action": "extract",  # Main action
        "agent_output": {
            # Full agent output including structured_output field
        },
        "output_mapping": {
            "structured_output_fields": [...],  # Required fields to extract
            "include_original": true,
            "add_metadata": true
        },
        "original_row": {
            # Original CSV row data
        }
    }
    """
    action = event.get('action', 'extract')

    if action == 'extract':
        return extract_structured_output(event, context)

    # Legacy behavior for backward compatibility
    try:
        original_row = event.get('original_row', {})
        result = event.get('execution_result', {})
        mapping = event.get('output_mapping', {})
        metadata = event.get('execution_metadata', {})
        
        # Start with original row if requested
        output_row = {}
        if mapping.get('include_original', True):
            output_row = original_row.copy()
        
        # Extract tool result if wrapped
        if isinstance(result, dict) and result.get('type') == 'tool_result':
            actual_result = result.get('content', {})
        else:
            actual_result = result
        
        # Map specified columns from the result
        columns = mapping.get('columns', [])
        for column_config in columns:
            col_name = column_config['name']
            source_path = column_config.get('source', '')
            default_value = column_config.get('default', '')
            col_type = column_config.get('type', 'string')
            
            try:
                value = extract_value(actual_result, source_path)
                
                # Format based on type
                if col_type == 'number' and value is not None:
                    format_spec = column_config.get('format')
                    if format_spec:
                        value = format_spec % float(value)
                elif col_type == 'json_string' and value is not None:
                    value = json.dumps(value)
                elif col_type == 'boolean' and value is not None:
                    value = str(value).lower()
                
                output_row[col_name] = value if value is not None else default_value
                
            except Exception as e:
                logger.warning(f"Error extracting {source_path}: {str(e)}")
                output_row[col_name] = default_value
        
        # Add metadata if requested
        if mapping.get('add_metadata', True):
            output_row['_status'] = metadata.get('status', 'SUCCESS')
            output_row['_execution_time_ms'] = calculate_execution_time(
                metadata.get('start_time'),
                metadata.get('end_time')
            )
            output_row['_timestamp'] = datetime.utcnow().isoformat()
            
            if metadata.get('status') == 'FAILED':
                output_row['_error_message'] = metadata.get('error_message', '')
        
        return output_row
        
    except Exception as e:
        logger.error(f"Error mapping output: {str(e)}")
        # Return original row with error metadata
        return {
            **original_row,
            '_status': 'FAILED',
            '_error_message': str(e),
            '_timestamp': datetime.utcnow().isoformat()
        }

def extract_value(data: Any, path: str) -> Any:
    """
    Extract value from nested data using JSONPath-like notation
    Examples:
    - $.result → data['result']
    - $.result.data.field → data['result']['data']['field']
    - $.items[0].name → data['items'][0]['name']
    """
    if not path or path == '$':
        return data
    
    # Remove leading $. if present
    if path.startswith('$.'):
        path = path[2:]
    
    # Split path and traverse
    parts = path.split('.')
    current = data
    
    for part in parts:
        if current is None:
            return None
        
        # Handle array indices like items[0]
        match = re.match(r'(\w+)\[(\d+)\]', part)
        if match:
            field, index = match.groups()
            if isinstance(current, dict) and field in current:
                current = current[field]
                if isinstance(current, list) and len(current) > int(index):
                    current = current[int(index)]
                else:
                    return None
            else:
                return None
        else:
            # Handle regular field access
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
    
    return current

def extract_structured_output(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Extract structured output from agent response

    This function specifically looks for the 'structured_output' field
    in the agent's response, which is REQUIRED for batch processing.
    """
    try:
        agent_output = event.get('agent_output', {})
        output_mapping = event.get('output_mapping', {})
        original_row = event.get('original_row', {})

        # Start with an ordered dictionary to control column order
        from collections import OrderedDict
        result_row = OrderedDict()

        # First add original row fields if requested (preserves input column order)
        if output_mapping.get('include_original', True):
            for key, value in original_row.items():
                result_row[key] = value

        # CRITICAL: Extract structured output from agent response
        # The agent MUST return a 'structured_output' field
        structured_data = None

        # First check if agent_output itself is a string that needs parsing
        if isinstance(agent_output, str):
            logger.info("Agent output is a string, attempting to parse as JSON")
            try:
                agent_output = json.loads(agent_output)
                logger.info(f"Successfully parsed agent_output string to dict with keys: {list(agent_output.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse agent_output string as JSON: {e}")
                logger.error(f"Agent output string (first 500 chars): {agent_output[:500]}")
                agent_output = {}

        # Check different possible locations for structured output
        if isinstance(agent_output, dict):
            logger.info(f"Agent output keys: {list(agent_output.keys())}")

            # Direct structured output field
            if 'structured_output' in agent_output:
                structured_data = agent_output['structured_output']
                logger.info("Found structured_output directly in agent_output")
            # Check if it's wrapped in Output field (from Step Functions)
            elif 'Output' in agent_output:
                # Output field might be a JSON string from Step Functions execution
                output_data = agent_output['Output']
                logger.info(f"Found Output field, type: {type(output_data)}")

                if isinstance(output_data, str):
                    try:
                        output_data = json.loads(output_data)
                        logger.info(f"Parsed Output JSON, keys: {list(output_data.keys()) if isinstance(output_data, dict) else 'not a dict'}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Output as JSON: {e}")
                        logger.error(f"Output string (first 500 chars): {output_data[:500]}")
                        output_data = {}

                if isinstance(output_data, dict) and 'structured_output' in output_data:
                    structured_data = output_data['structured_output']
                    logger.info(f"Found structured_output in parsed Output, data: {structured_data}")
                else:
                    logger.warning(f"No structured_output in Output. Keys available: {list(output_data.keys()) if isinstance(output_data, dict) else 'not a dict'}")
            # Check for content field (tool result format)
            elif 'content' in agent_output and isinstance(agent_output['content'], dict):
                if 'structured_output' in agent_output['content']:
                    structured_data = agent_output['content']['structured_output']
                    logger.info("Found structured_output in content field")

        if structured_data is None:
            # Agent didn't return structured output - this is an error
            logger.error(f"Agent did not return structured output. Response keys: {list(agent_output.keys()) if isinstance(agent_output, dict) else 'not a dict'}")
            logger.error(f"Full agent_output (first 2000 chars): {json.dumps(agent_output)[:2000]}")
            return {
                **result_row,
                '_status': 'FAILED',
                '_error_message': 'Agent did not return structured output. Ensure agent implements return_structured_data tool.',
                '_timestamp': datetime.utcnow().isoformat()
            }

        # Extract specified fields from structured output in the order they're specified
        fields_to_extract = output_mapping.get('structured_output_fields', [])

        # Add fields in the exact order specified in structured_output_fields
        for field_name in fields_to_extract:
            if field_name in structured_data:
                value = structured_data[field_name]
                # Convert complex types to JSON strings for CSV
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                elif value is None:
                    value = ''
                result_row[field_name] = value
            else:
                # Field not found in structured output
                result_row[field_name] = ''
                logger.warning(f"Field '{field_name}' not found in structured output")

        # Add metadata if requested
        if output_mapping.get('add_metadata', True):
            result_row['_status'] = 'SUCCESS'
            result_row['_timestamp'] = datetime.utcnow().isoformat()

            # Add execution time if available
            if 'execution_metadata' in event:
                metadata = event['execution_metadata']
                result_row['_execution_time_ms'] = calculate_execution_time(
                    metadata.get('start_time'),
                    metadata.get('end_time')
                )

        # Return as regular dict (but order is preserved)
        return dict(result_row)

    except Exception as e:
        logger.error(f"Error extracting structured output: {str(e)}")
        return {
            **original_row,
            '_status': 'FAILED',
            '_error_message': str(e),
            '_timestamp': datetime.utcnow().isoformat()
        }

def calculate_execution_time(start_time: Optional[str], end_time: Optional[str]) -> int:
    """Calculate execution time in milliseconds"""
    if not start_time or not end_time:
        return 0
    
    try:
        # Parse ISO format timestamps
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        delta = end - start
        return int(delta.total_seconds() * 1000)
    except Exception:
        return 0

# Test case
if __name__ == "__main__":
    test_event = {
        "original_row": {
            "customer_id": "123",
            "query": "Help with billing"
        },
        "execution_result": {
            "classification": {
                "category": "Billing",
                "priority": "High"
            },
            "suggested_response": "I'll help you review your billing...",
            "confidence": 0.95
        },
        "output_mapping": {
            "columns": [
                {
                    "name": "category",
                    "source": "$.classification.category"
                },
                {
                    "name": "priority", 
                    "source": "$.classification.priority"
                },
                {
                    "name": "response",
                    "source": "$.suggested_response"
                },
                {
                    "name": "confidence",
                    "source": "$.confidence",
                    "type": "number",
                    "format": "%.2f"
                }
            ],
            "include_original": True,
            "add_metadata": True
        },
        "execution_metadata": {
            "status": "SUCCESS",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T10:00:01.500Z"
        }
    }
    
    print("Test input:")
    print(json.dumps(test_event, indent=2))
    print("\nWould produce enriched row:")
    print(json.dumps(lambda_handler(test_event, None), indent=2))