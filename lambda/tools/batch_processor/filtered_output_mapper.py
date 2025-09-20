"""
Filtered Output Mapper Lambda
Reduces payload size by extracting only essential fields from agent execution results
Supports both structured output and text extraction patterns
"""

import json
import re
from typing import Dict, Any, List, Optional

def lambda_handler(event, context):
    """
    Map agent execution results to structured output with minimal payload

    Event structure:
    {
        "original_row": {...},
        "execution_result": {
            "Output": {...} or direct result
        },
        "output_mapping": {
            "extract_fields": [...],  # Fields to extract
            "structured_output_tool": "print_output"  # Optional tool name
        },
        "execution_metadata": {
            "status": "SUCCESS/FAILED",
            "error_message": "..."  # If failed
        }
    }
    """
    original_row = event.get('original_row', {})
    execution_result = event.get('execution_result', {})
    output_mapping = event.get('output_mapping', {})
    execution_metadata = event.get('execution_metadata', {})

    # Extract the actual result
    if isinstance(execution_result, dict):
        if 'Output' in execution_result:
            actual_result = execution_result['Output']
        else:
            actual_result = execution_result
    else:
        actual_result = {}

    # Start with minimal original row data
    output = {
        k: v for k, v in original_row.items()
        if not k.startswith('_') or k in ['_row_number', '_row_id']
    }

    # Check if agent used structured output tool
    structured_data = extract_structured_output(actual_result,
                                                output_mapping.get('structured_output_tool'))

    if structured_data:
        # Use structured output if available
        output.update(structured_data)
    else:
        # Fall back to pattern extraction
        extracted_data = extract_with_patterns(actual_result,
                                              output_mapping.get('extract_fields', []))
        output.update(extracted_data)

    # Add minimal metadata
    output['_status'] = execution_metadata.get('status', 'UNKNOWN')
    if execution_metadata.get('status') == 'FAILED':
        output['_error'] = execution_metadata.get('error_message', 'Unknown error')[:200]

    # Add execution time if available
    if 'StartDate' in execution_result and 'StopDate' in execution_result:
        duration = execution_result['StopDate'] - execution_result['StartDate']
        output['_execution_time_ms'] = duration

    return output

def extract_structured_output(result: Dict[str, Any],
                             tool_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured output from agent tool use
    """
    if not tool_name or 'messages' not in result:
        return {}

    # Look for tool use with the specified name
    for message in result.get('messages', []):
        if message.get('role') == 'assistant':
            tool_calls = message.get('tool_calls', [])
            for call in tool_calls:
                if call.get('name') == tool_name:
                    # Return the tool input as structured data
                    return call.get('input', {})

    # Also check function_calls for newer format
    for call in result.get('function_calls', []):
        if call.get('name') == tool_name:
            return call.get('arguments', {})

    return {}

def extract_with_patterns(result: Dict[str, Any],
                          field_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract fields using regex patterns or JSONPath
    """
    output = {}

    # Get text content to search
    text_content = extract_text_content(result)

    for config in field_configs:
        field_name = config.get('name')
        if not field_name:
            continue

        # Try regex extraction first
        if 'pattern' in config:
            match = re.search(config['pattern'], text_content, re.IGNORECASE | re.MULTILINE)
            if match:
                if 'group' in config:
                    output[field_name] = match.group(config['group'])
                else:
                    output[field_name] = match.group(1) if match.groups() else match.group(0)

        # Try JSONPath extraction (simplified)
        elif 'path' in config:
            value = extract_by_path(result, config['path'])
            if value is not None:
                output[field_name] = value

        # Apply default if no value found
        if field_name not in output and 'default' in config:
            output[field_name] = config['default']

    return output

def extract_text_content(result: Dict[str, Any]) -> str:
    """
    Extract all text content from agent response
    """
    texts = []

    # Extract from messages format
    if 'messages' in result:
        for message in result['messages']:
            if message.get('role') == 'user':
                # Check for tool results
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_result':
                            texts.append(item.get('content', ''))
            elif message.get('role') == 'assistant':
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            texts.append(item.get('text', ''))
                elif isinstance(content, str):
                    texts.append(content)

    # Extract from results format (web search)
    if 'results' in result:
        for res in result.get('results', []):
            if isinstance(res, dict):
                texts.append(res.get('title', ''))
                texts.append(res.get('snippet', ''))
                texts.append(res.get('description', ''))

    return '\n'.join(filter(None, texts))

def extract_by_path(data: Dict[str, Any], path: str) -> Any:
    """
    Simple JSONPath-like extraction
    Supports paths like "messages[0].content" or "Output.status"
    """
    current = data

    # Split path by dots, handling array notation
    parts = re.split(r'\.(?![^\[]*\])', path)

    for part in parts:
        if not current:
            return None

        # Handle array index notation
        array_match = re.match(r'(\w+)\[(-?\d+)\]', part)
        if array_match:
            key, index = array_match.groups()
            index = int(index)

            if isinstance(current, dict) and key in current:
                array = current[key]
                if isinstance(array, list) and -len(array) <= index < len(array):
                    current = array[index]
                else:
                    return None
            else:
                return None
        else:
            # Regular key access
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

    return current

# Test the function
if __name__ == "__main__":
    # Test with broadband agent output
    test_event = {
        "original_row": {
            "address": "10 Downing Street",
            "postcode": "SW1A 2AA",
            "_row_number": 1
        },
        "execution_result": {
            "Output": {
                "messages": [
                    {"role": "user", "content": "Check broadband"},
                    {"role": "assistant", "content": [{"type": "text", "text": "Checking..."}]},
                    {"role": "user", "content": [
                        {"type": "tool_result", "content": "Exchange: WHITEHALL\nCabinet: Not found\nDownload Speed: 50.0-330.0 Mbps"}
                    ]}
                ]
            }
        },
        "output_mapping": {
            "extract_fields": [
                {"name": "exchange", "pattern": r"Exchange:\s+([A-Z\s]+)", "default": "N/A"},
                {"name": "download_speed", "pattern": r"Download Speed:\s+([\d.-]+\s*Mbps)", "default": "N/A"}
            ]
        },
        "execution_metadata": {"status": "SUCCESS"}
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))