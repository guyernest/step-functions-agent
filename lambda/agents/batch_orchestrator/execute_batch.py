"""
Execute Batch Processor Tool
Starts batch processing execution
"""

import json
import boto3
import os
from typing import Dict, Any
import logging
from datetime import datetime
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn_client = boto3.client('stepfunctions')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Start batch processor execution

    Tool input:
    {
        "name": "execute_batch_processor",
        "input": {
            "csv_s3_uri": "s3://bucket/file.csv",
            "agent_name": "agent-name",
            "input_mapping": {...},
            "output_mapping": {...},
            "max_concurrency": 10  # optional
        }
    }
    """
    try:
        tool_input = event.get('input', {})

        # Build the batch processor configuration
        csv_s3_uri = tool_input['csv_s3_uri']
        agent_name = tool_input['agent_name']

        # Build the target configuration
        target = {
            "type": "agent",
            "name": agent_name
        }

        # Handle output_mapping - if it's a dict of field mappings, extract the keys as structured_output_fields
        output_mapping = tool_input.get('output_mapping', {})
        if output_mapping and 'structured_output_fields' not in output_mapping:
            # If output_mapping is a dict of field mappings, convert to expected format
            structured_fields = list(output_mapping.keys()) if isinstance(output_mapping, dict) else []
            output_mapping = {
                "structured_output_fields": structured_fields,
                "include_original": True,
                "add_metadata": True
            }
        elif not output_mapping:
            # Default output mapping
            output_mapping = {
                "structured_output_fields": [],
                "include_original": True,
                "add_metadata": True
            }

        # Build the complete config for the batch processor
        config = {
            "csv_s3_uri": csv_s3_uri,
            "target": target,
            "input_mapping": tool_input.get('input_mapping', {}),
            "output_mapping": output_mapping,
            "execution_config": {
                "max_concurrency": tool_input.get('max_concurrency', 10)
            }
        }

        # For broadband-checker-structured, provide the known fields if none specified
        if agent_name == "broadband-checker-structured" and not output_mapping.get('structured_output_fields'):
            output_mapping['structured_output_fields'] = [
                "exchange_station",
                "download_speed",
                "upload_speed",
                "screenshot_url"
            ]

        # Get batch processor state machine ARN
        state_machine_arn = os.environ.get('BATCH_PROCESSOR_ARN')
        if not state_machine_arn:
            raise ValueError("Batch processor ARN not configured")

        # Generate execution name
        execution_name = f"batch-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Start the execution
        response = sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json.dumps(config)
        )

        execution_arn = response['executionArn']

        # Get initial status
        status_response = sfn_client.describe_execution(
            executionArn=execution_arn
        )

        result = {
            "execution_arn": execution_arn,
            "execution_name": execution_name,
            "status": status_response['status'],
            "start_time": response['startDate'].isoformat(),
            "state_machine_arn": state_machine_arn,
            "input_config": config,
            "message": f"Batch processing started successfully. Execution ID: {execution_name}",
            "monitor_command": f"Use 'monitor_batch_execution' with execution_arn: {execution_arn}"
        }

        return {
            "type": "tool_result",
            "name": event.get('name', 'execute_batch_processor'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error starting batch processor: {e}")
        return {
            "type": "tool_result",
            "name": event.get('name', 'execute_batch_processor'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps({
                "error": str(e),
                "message": f"Failed to start batch processor: {e}"
            })
        }