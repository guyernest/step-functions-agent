"""
Input Mapper Lambda
Transforms CSV row data into agent/tool input format
Validates agents have structured output capability
Used within Distributed Map iterator
"""

import json
import logging
import os
import boto3
import csv
import io
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Map CSV row to agent/tool input format or validate configuration

    Event structure for mapping:
    {
        "action": "transform",  # or "validate"
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

    Event structure for validation:
    {
        "action": "validate",
        "csv_s3_uri": "s3://bucket/key",
        "target": {
            "type": "agent",
            "name": "agent_name"
        },
        "output_mapping": {
            "structured_output_fields": [...]
        }
    }
    """
    action = event.get('action', 'transform')

    if action == 'validate':
        return validate_configuration(event, context)
    elif action == 'load_csv':
        return load_csv_data(event, context)

    # Default to transform action
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
            # For agents, create a simple prompt if mapping is simple
            # Check if we have a simple address/postcode mapping
            if 'address' in mapping and isinstance(mapping['address'], str):
                # Simple string mapping - concatenate the field values
                prompt_parts = []
                for field in ['address', 'postcode']:
                    if field in mapping and mapping[field] in row:
                        prompt_parts.append(row[mapping[field]])

                prompt = ', '.join(prompt_parts) if prompt_parts else str(row)
            elif result:
                # Use the mapped result
                prompt = json.dumps(result) if isinstance(result, dict) else str(result)
            else:
                # Fallback: use the raw row data
                prompt = json.dumps(row) if isinstance(row, dict) else str(row)

            return {
                "prompt": prompt,
                "data": result if result else row
            }
            
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

def validate_configuration(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Validate batch processing configuration

    Checks:
    - CSV file exists and is accessible
    - Target agent exists and has structured output capability
    - Output mapping specifies structured fields
    """
    try:
        csv_s3_uri = event['csv_s3_uri']
        target = event['target']
        output_mapping = event.get('output_mapping', {})

        # Log target type for debugging
        logger.info(f"Target value: {target}, type: {type(target)}")

        # Handle case where target is a string (agent name) instead of a dict
        if isinstance(target, str):
            target = {
                'type': 'agent',
                'name': target
            }
            logger.info(f"Converted string target to dict: {target}")

        # Parse S3 URI
        if not csv_s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {csv_s3_uri}")

        parts = csv_s3_uri[5:].split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {csv_s3_uri}")

        bucket, key = parts

        # Verify CSV file exists
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
        except Exception as e:
            raise ValueError(f"Cannot access CSV file: {e}")

        # For agents, validate structured output capability
        if target['type'] == 'agent':
            agent_name = target['name']

            # Get agent registry table name
            table_name = os.environ.get('AGENT_REGISTRY_TABLE')
            if not table_name:
                # Try to get from SSM if not in env
                ssm = boto3.client('ssm')
                try:
                    param = ssm.get_parameter(Name='/ai-agent/agent-registry-table')
                    table_name = param['Parameter']['Value']
                except:
                    logger.warning("Could not get agent registry table name")

            if table_name:
                table = dynamodb.Table(table_name)

                # Look up agent in registry - query for latest version
                response = table.query(
                    KeyConditionExpression='agent_name = :name',
                    ExpressionAttributeValues={
                        ':name': agent_name
                    },
                    ScanIndexForward=False,  # Sort descending to get latest version first
                    Limit=1
                )

                if 'Items' not in response or len(response['Items']) == 0:
                    raise ValueError(f"Agent not found: {agent_name}")

                agent = response['Items'][0]

                # CRITICAL: Check for structured output capability - be flexible
                has_structured_output = False
                structured_fields = []

                # Check structured_output field (snake_case)
                if 'structured_output' in agent:
                    so = agent['structured_output']
                    if isinstance(so, str):
                        try:
                            so = json.loads(so)
                        except:
                            pass
                    if isinstance(so, dict) and so.get('enabled'):
                        has_structured_output = True
                        structured_fields = so.get('output_fields', [])

                        # Try to extract fields from schemas
                        if not structured_fields and 'schemas' in so:
                            for schema_name, schema_def in so.get('schemas', {}).items():
                                if 'schema' in schema_def:
                                    schema_str = schema_def['schema']
                                    if isinstance(schema_str, str):
                                        try:
                                            schema_obj = json.loads(schema_str)
                                            if 'properties' in schema_obj:
                                                structured_fields.extend(schema_obj['properties'].keys())
                                        except:
                                            pass

                # Check structuredOutput field (camelCase)
                if not has_structured_output and 'structuredOutput' in agent:
                    so = agent['structuredOutput']
                    if isinstance(so, str):
                        try:
                            so = json.loads(so)
                        except:
                            pass
                    if isinstance(so, dict) and so.get('enabled'):
                        has_structured_output = True
                        # Extract fields from schemas
                        if 'schemas' in so:
                            for schema_def in so.get('schemas', {}).values():
                                if 'schema' in schema_def and 'properties' in schema_def['schema']:
                                    structured_fields.extend(schema_def['schema']['properties'].keys())

                # Check for return_*_data tools
                if not has_structured_output and 'tools' in agent:
                    tools = agent['tools']
                    if isinstance(tools, str):
                        try:
                            tools = json.loads(tools)
                        except:
                            tools = []

                    if isinstance(tools, list):
                        for tool in tools:
                            # Handle both string tool names and dict tool configs
                            tool_name = tool if isinstance(tool, str) else tool.get('tool_name', '') if isinstance(tool, dict) else ''
                            if isinstance(tool_name, str) and tool_name.startswith('return_') and tool_name.endswith('_data'):
                                has_structured_output = True
                                break

                if not has_structured_output:
                    raise ValueError(
                        f"Agent '{agent_name}' does not have structured output enabled. "
                        f"All agents used with batch processor MUST implement structured output. "
                        f"Please use an agent that implements a 'return_*_data' tool."
                    )

                # Get the agent's state machine ARN - check different fields
                target['arn'] = agent.get('state_machine_arn') or agent.get('agentArn', '')
                if not target['arn']:
                    raise ValueError(f"Agent {agent_name} does not have a state machine ARN")

                # Store structured output fields for later use
                output_mapping['available_fields'] = list(set(structured_fields)) if structured_fields else []

        # Validate output mapping has structured fields defined
        if not output_mapping.get('structured_output_fields'):
            available = output_mapping.get('available_fields', [])
            if available:
                # Auto-populate if not specified
                output_mapping['structured_output_fields'] = available
                logger.info(f"Auto-populated structured_output_fields with: {available}")
            else:
                # Try to provide a helpful error with what we know about the agent
                error_msg = (
                    "output_mapping.structured_output_fields is required. "
                    "Specify which fields from the agent's structured output to include in the CSV."
                )
                if target.get('type') == 'agent':
                    error_msg += f"\nAgent '{target.get('name', '')}' has structured output enabled but no fields were found in registry."
                raise ValueError(error_msg)

        return {
            'valid': True,
            'csv_bucket': bucket,
            'csv_key': key,
            'target': target,
            'output_mapping': output_mapping,
            'message': 'Validation successful - agent has structured output'
        }

    except Exception as e:
        import traceback
        logger.error(f"Validation failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"Event structure: {json.dumps(event)[:500]}")
        return {
            'valid': False,
            'error': str(e),
            'message': f'Validation failed: {e}'
        }

def load_csv_data(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Load CSV data from S3 for inline processing

    Reads the CSV file and returns it as an array of row objects
    suitable for Step Functions Map state processing.
    """
    import csv
    import io

    try:
        csv_bucket = event['csv_bucket']
        csv_key = event['csv_key']

        # Read CSV from S3
        response = s3_client.get_object(Bucket=csv_bucket, Key=csv_key)
        content = response['Body'].read().decode('utf-8')

        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        logger.info(f"Loaded {len(rows)} rows from s3://{csv_bucket}/{csv_key}")

        return {
            'rows': rows,
            'row_count': len(rows),
            'columns': csv_reader.fieldnames if csv_reader.fieldnames else []
        }

    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return {
            'error': str(e),
            'message': f'Failed to load CSV: {e}'
        }

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