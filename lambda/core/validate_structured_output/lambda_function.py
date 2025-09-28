"""
ValidateStructuredOutput Lambda function.
Validates extracted structured output against the defined schema.
"""

import json
import jsonschema
from jsonschema import Draft7Validator
from typing import Dict, Any, List, Tuple, Optional

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates data against a JSON schema.

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, []
    except jsonschema.exceptions.ValidationError:
        # Collect all validation errors for better debugging
        validator = Draft7Validator(schema)
        errors = []
        for error in validator.iter_errors(data):
            error_path = '.'.join(str(p) for p in error.path) if error.path else 'root'
            errors.append(f"{error_path}: {error.message}")
        return False, errors

def extract_structured_data(tool_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract structured data from tool call arguments."""

    # Handle different formats of tool call arguments
    arguments = tool_call.get('arguments', {})

    # If arguments is a string, parse it
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return None

    return arguments

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler - validates structured output from agent response.

    Input event structure:
    {
        "tool_call": {
            "name": "return_structured",
            "arguments": {...structured data...}
        },
        "schema": {...json schema...},
        "messages": [...conversation history...]
    }
    """

    # Extract parameters
    tool_call = event.get('tool_call', {})
    schema = event.get('schema', {})
    messages = event.get('messages', [])

    # Extract structured data from tool call
    structured_data = extract_structured_data(tool_call)

    if structured_data is None:
        return {
            'valid': False,
            'validated_output': None,
            'errors': ['Failed to extract structured data from tool call'],
            'messages': messages
        }

    # Validate against schema
    is_valid, errors = validate_against_schema(structured_data, schema)

    if not is_valid:
        return {
            'valid': False,
            'validated_output': None,
            'errors': errors,
            'messages': messages
        }

    # Add structured output to messages for conversation continuity
    messages_with_output = messages.copy()
    messages_with_output.append({
        'role': 'assistant',
        'content': f"Successfully extracted structured data",
        'structured_output': structured_data
    })

    return {
        'valid': True,
        'validated_output': structured_data,
        'errors': [],
        'messages': messages_with_output
    }