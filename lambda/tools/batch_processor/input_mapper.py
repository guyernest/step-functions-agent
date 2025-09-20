"""
Input Mapper Lambda
Transforms CSV row data into agent/tool input format
Used within Distributed Map iterator
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Map CSV row to agent/tool input format
    
    Event structure:
    {
        "row": {
            "column1": "value1",
            "column2": "value2",
            ...
        },
        "mapping_config": {
            "column_mappings": {...},
            "static_values": {...},
            "transformations": {...}
        },
        "target": {
            "type": "agent | tool",
            "name": "...",
            "arn": "..."
        }
    }
    """
    try:
        row = event['row']
        mapping = event.get('mapping_config', {})
        target = event.get('target', {})
        
        # Build the input for the agent/tool
        result = {}
        
        # Apply column mappings
        column_mappings = mapping.get('column_mappings', {})
        for csv_col, target_field in column_mappings.items():
            if csv_col in row:
                result[target_field] = row[csv_col]
        
        # Add static values
        static_values = mapping.get('static_values', {})
        result.update(static_values)
        
        # Apply transformations
        transformations = mapping.get('transformations', {})
        for field_name, transform_config in transformations.items():
            transform_type = transform_config.get('type')
            config = transform_config.get('config', {})
            
            if transform_type == 'concat':
                result[field_name] = apply_concat(row, config)
            elif transform_type == 'template':
                result[field_name] = apply_template(row, config)
            elif transform_type == 'jsonpath':
                result[field_name] = apply_jsonpath(row, config)
        
        # Format based on target type
        if target.get('type') == 'tool':
            # Wrap in tool invocation format
            return {
                "name": target.get('name'),
                "input": result,
                "id": f"batch_{context.request_id}"
            }
        else:
            # Direct format for agents
            return result
            
    except Exception as e:
        logger.error(f"Error mapping input: {str(e)}")
        raise

def apply_concat(row: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Concatenate multiple columns"""
    columns = config.get('columns', [])
    separator = config.get('separator', ' ')
    
    values = []
    for col in columns:
        if col in row and row[col]:
            values.append(str(row[col]))
    
    return separator.join(values)

def apply_template(row: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Apply template transformation"""
    template = config.get('template', '')
    variables = config.get('variables', {})
    
    result = template
    for var_name, col_name in variables.items():
        if col_name in row:
            placeholder = f"{{{var_name}}}"
            result = result.replace(placeholder, str(row.get(col_name, '')))
    
    return result

def apply_jsonpath(row: Dict[str, Any], config: Dict[str, Any]) -> Any:
    """Extract value from JSON column"""
    column = config.get('column', '')
    path = config.get('path', '$')
    
    if column not in row:
        return None
    
    try:
        data = row[column]
        if isinstance(data, str):
            data = json.loads(data)
        
        # Simple path extraction (could be enhanced with jsonpath-ng)
        if path == '$':
            return data
        
        # Basic dot notation support
        parts = path.lstrip('$.').split('.')
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
        
    except Exception as e:
        logger.warning(f"JSONPath extraction failed: {str(e)}")
        return None

# Test case
if __name__ == "__main__":
    test_event = {
        "row": {
            "customer_id": "123",
            "first_name": "John",
            "last_name": "Doe",
            "query": "Help with billing"
        },
        "mapping_config": {
            "column_mappings": {
                "customer_id": "customerId",
                "query": "userQuery"
            },
            "transformations": {
                "fullName": {
                    "type": "concat",
                    "config": {
                        "columns": ["first_name", "last_name"],
                        "separator": " "
                    }
                }
            }
        },
        "target": {
            "type": "agent",
            "name": "support_agent"
        }
    }
    
    print("Test input:")
    print(json.dumps(test_event, indent=2))
    print("\nWould produce:")
    print(json.dumps(lambda_handler(test_event, type('Context', (), {'request_id': 'test123'})), indent=2))