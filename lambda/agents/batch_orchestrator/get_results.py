"""
Get Results Tool
Retrieves batch processing results
"""

import json
import boto3
import os
from typing import Dict, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn_client = boto3.client('stepfunctions')
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Get batch processing results

    Tool input:
    {
        "name": "get_batch_results",
        "input": {
            "execution_arn": "arn:aws:states:..."  // Full ARN
            OR
            "execution_id": "batch-20250925-..."    // Just the execution ID
        }
    }
    """
    try:
        tool_input = event.get('input', {})

        # Support both execution_arn and execution_id
        execution_arn = tool_input.get('execution_arn')
        if not execution_arn:
            execution_id = tool_input.get('execution_id')
            if execution_id:
                # Construct ARN from execution_id
                state_machine_arn = os.environ.get('BATCH_PROCESSOR_ARN',
                    'arn:aws:states:us-west-2:672915487120:stateMachine:batch-processor-prod')
                execution_arn = f"{state_machine_arn.replace(':stateMachine:', ':execution:')}:{execution_id}"
            else:
                raise ValueError("Either execution_arn or execution_id must be provided")

        # Get execution details
        response = sfn_client.describe_execution(
            executionArn=execution_arn
        )

        status = response['status']

        if status != 'SUCCEEDED':
            return {
                "type": "tool_result",
                "name": event.get('name', 'get_batch_results'),
                "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
                "content": json.dumps({
                    "error": f"Execution status is {status}, not SUCCEEDED",
                    "message": f"Cannot retrieve results. Execution status: {status}",
                    "suggestion": "Wait for execution to complete successfully before retrieving results"
                })
            }

        # Parse output to get result details
        output = json.loads(response['output'])

        # Get the output location
        output_location = output.get('output_location', '')
        if not output_location:
            # Try to construct it from execution ID
            results_bucket = os.environ.get('RESULTS_BUCKET')
            if results_bucket and 'execution_id' in output:
                output_location = f"s3://{results_bucket}/results/{output['execution_id']}/output.csv"

        result = {
            "execution_arn": execution_arn,
            "status": "SUCCESS",
            "output_csv_uri": output_location,
            "summary": {
                "total_rows": output.get('total_rows', 0),
                "successful_rows": output.get('successful_rows', 0),
                "failed_rows": output.get('failed_rows', 0),
                "success_rate": output.get('success_rate', 'N/A'),
                "processing_time": f"{response['stopDate'] - response['startDate']}"
            },
            "columns": output.get('column_names', []),
            "execution_details": {
                "start_time": response['startDate'].isoformat(),
                "end_time": response['stopDate'].isoformat(),
                "execution_id": output.get('execution_id', execution_arn.split(':')[-1])
            }
        }

        # Generate download instructions
        result['download_instructions'] = (
            f"You can download the results from: {output_location}\n"
            f"Use AWS CLI: aws s3 cp {output_location} ./results.csv"
        )

        # Check if there were any failures
        if output.get('failed_rows', 0) > 0:
            result['failure_info'] = (
                f"{output['failed_rows']} rows failed processing. "
                "Check the _status and _error_message columns in the output CSV for details."
            )

        result['message'] = f"Successfully retrieved results. Output saved to: {output_location}"

        return {
            "type": "tool_result",
            "name": event.get('name', 'get_batch_results'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return {
            "type": "tool_result",
            "name": event.get('name', 'get_batch_results'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps({
                "error": str(e),
                "message": f"Failed to retrieve results: {e}"
            })
        }