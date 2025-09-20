"""
State Machine Invoker Lambda
This Lambda prepares the input for the batch processor state machine
with proper configuration including defaults
"""

import json
import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """
    Prepare and invoke the batch processor state machine
    This handles the tool invocation and prepares proper input
    """
    try:
        # Extract tool input
        tool_use = event
        tool_input = tool_use.get('input', {})

        # Parse S3 URI
        csv_s3_uri = tool_input['csv_s3_uri']
        parts = csv_s3_uri.replace('s3://', '').split('/', 1)
        input_bucket = parts[0]
        input_key = parts[1] if len(parts) > 1 else ''

        # Get output bucket
        output_bucket = tool_input.get('output_bucket', f'address-search-batch-results-prod-{context.invoked_function_arn.split(":")[4]}')

        # Get target agent configuration
        import os
        env_name = os.environ.get('ENV_NAME', 'prod')
        # AWS_REGION is automatically available in Lambda environment
        region = os.environ.get('AWS_REGION', 'eu-west-1')
        account_id = context.invoked_function_arn.split(":")[4]

        target_agent_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:web-search-agent-unified-{env_name}"

        # Default mappings for address search
        default_input_mapping = {
            "column_mappings": {
                "address": "query"
            },
            "transformations": {
                "query": {
                    "type": "template",
                    "config": {
                        "template": "UK property information for: {address}",
                        "variables": {
                            "address": "address"
                        }
                    }
                }
            },
            "static_values": {
                "search_type": "property",
                "region": "UK"
            }
        }

        default_output_mapping = {
            "columns": [
                {
                    "name": "property_type",
                    "source": "$.property_info.type",
                    "default": "N/A"
                },
                {
                    "name": "bedrooms",
                    "source": "$.property_info.bedrooms",
                    "type": "number",
                    "default": "0"
                },
                {
                    "name": "estimated_value",
                    "source": "$.property_info.estimated_value",
                    "default": "N/A"
                },
                {
                    "name": "council_tax_band",
                    "source": "$.property_info.council_tax_band",
                    "default": "N/A"
                }
            ],
            "include_original": True,
            "add_metadata": True
        }

        # Build state machine input
        state_machine_input = {
            "input_bucket": input_bucket,
            "input_key": input_key,
            "output_bucket": output_bucket,
            "input_mapping": tool_input.get('custom_mappings', {}).get('input_mapping', default_input_mapping),
            "output_mapping": tool_input.get('custom_mappings', {}).get('output_mapping', default_output_mapping),
            "target": {
                "type": "agent",
                "name": "web-search-agent-unified",
                "arn": target_agent_arn
            },
            "execution_config": tool_input.get('execution_config', {
                "max_concurrency": 5,
                "timeout_seconds": 60,
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff_rate": 2.0
                }
            })
        }

        # Get state machine ARN
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        if not state_machine_arn:
            state_machine_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:address-search-batch-{env_name}"

        # Start execution
        execution_response = stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(state_machine_input)
        )

        # Wait for completion (synchronous)
        import time
        execution_arn = execution_response['executionArn']

        while True:
            status_response = stepfunctions_client.describe_execution(
                executionArn=execution_arn
            )

            status = status_response['status']
            if status in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
                break

            time.sleep(5)  # Check every 5 seconds

        if status == 'SUCCEEDED':
            output = json.loads(status_response.get('output', '{}'))
            csv_location = f"s3://{output_bucket}/batch-results/{execution_arn.split(':')[-1]}/final/output.csv"

            return {
                "type": "tool_result",
                "name": "address_search_batch",
                "tool_use_id": tool_use.get('id'),
                "content": {
                    "status": "SUCCESS",
                    "csv_location": csv_location,
                    "message": f"Batch processing completed. Results available at {csv_location}",
                    "execution_arn": execution_arn
                }
            }
        else:
            return {
                "type": "tool_result",
                "name": "address_search_batch",
                "tool_use_id": tool_use.get('id'),
                "content": {
                    "status": "FAILED",
                    "error": status_response.get('cause', 'Unknown error'),
                    "execution_arn": execution_arn
                }
            }

    except Exception as e:
        logger.error(f"Error invoking batch processor: {str(e)}")
        return {
            "type": "tool_result",
            "name": "address_search_batch",
            "tool_use_id": tool_use.get('id'),
            "content": {
                "error": str(e),
                "status": "FAILED"
            }
        }