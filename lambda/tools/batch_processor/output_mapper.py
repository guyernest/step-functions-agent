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
    Map agent/tool output to enriched row format
    
    Event structure:
    {
        "original_row": {
            "column1": "value1",
            "column2": "value2",
            ...
        },
        "execution_result": {
            ...agent/tool output...
        },
        "output_mapping": {
            "columns": [...],
            "include_original": true,
            "add_metadata": true
        },
        "execution_metadata": {
            "start_time": "...",
            "end_time": "...",
            "status": "SUCCESS | FAILED"
        }
    }
    """
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