"""
Monitor Execution Tool
Monitors batch processing execution progress
"""

import json
import boto3
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn_client = boto3.client('stepfunctions')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Monitor batch processing execution

    Tool input:
    {
        "name": "monitor_batch_execution",
        "input": {
            "execution_arn": "arn:aws:states:..."
        }
    }
    """
    try:
        # Debug logging
        logger.info(f"Full event: {json.dumps(event)}")
        logger.info(f"Event id: {event.get('id')}, type: {type(event.get('id'))}")

        tool_input = event.get('input', {})
        execution_arn = tool_input['execution_arn']

        # Check for polling metadata from state machine
        polling_metadata = event.get('polling_metadata', {})

        # Get execution status
        response = sfn_client.describe_execution(
            executionArn=execution_arn
        )

        status = response['status']
        start_time = response['startDate']

        # Calculate duration
        if 'stopDate' in response:
            end_time = response['stopDate']
            duration = (end_time - start_time).total_seconds()
        else:
            duration = (datetime.utcnow().replace(tzinfo=start_time.tzinfo) - start_time).total_seconds()

        # Try to get execution history for more details
        progress_info = {}
        try:
            history = sfn_client.get_execution_history(
                executionArn=execution_arn,
                maxResults=100,
                reverseOrder=True
            )

            # Look for Map state progress events
            for hist_event in history.get('events', []):
                if hist_event.get('type') == 'MapStateStarted':
                    progress_info['map_state'] = 'Started'
                elif hist_event.get('type') == 'MapIterationStarted':
                    progress_info['iterations_started'] = progress_info.get('iterations_started', 0) + 1
                elif hist_event.get('type') == 'MapIterationSucceeded':
                    progress_info['iterations_succeeded'] = progress_info.get('iterations_succeeded', 0) + 1
                elif hist_event.get('type') == 'MapIterationFailed':
                    progress_info['iterations_failed'] = progress_info.get('iterations_failed', 0) + 1

        except Exception as e:
            logger.warning(f"Could not get execution history: {e}")

        # Build result
        result = {
            "execution_arn": execution_arn,
            "status": status,
            "start_time": start_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "is_running": status == 'RUNNING'
        }

        # Add end time if available
        if 'stopDate' in response:
            result['end_time'] = response['stopDate'].isoformat()

        # Add progress information
        if progress_info:
            total_iterations = progress_info.get('iterations_started', 0)
            completed_iterations = (progress_info.get('iterations_succeeded', 0) +
                                  progress_info.get('iterations_failed', 0))

            if total_iterations > 0:
                result['progress'] = {
                    'rows_started': total_iterations,
                    'rows_completed': completed_iterations,
                    'rows_succeeded': progress_info.get('iterations_succeeded', 0),
                    'rows_failed': progress_info.get('iterations_failed', 0),
                    'percent_complete': round((completed_iterations / total_iterations) * 100, 1)
                }

        # Add appropriate message based on status
        if status == 'RUNNING':
            if 'progress' in result:
                result['message'] = f"Processing in progress: {result['progress']['percent_complete']}% complete"
            else:
                result['message'] = "Batch processing is running..."

            # Add polling guidance for running executions
            result['polling_guidance'] = {
                'status': 'in_progress',
                'recommended_wait_seconds': polling_metadata.get('interval', 30),
                'message': f"The system will automatically wait {polling_metadata.get('interval', 30)} seconds before checking again. Please be patient.",
                'max_attempts': polling_metadata.get('max_attempts', 20)
            }
        elif status == 'SUCCEEDED':
            result['message'] = "Batch processing completed successfully!"
            result['next_step'] = "Use 'get_batch_results' to retrieve the output"
        elif status == 'FAILED':
            result['message'] = "Batch processing failed"
            if 'error' in response:
                result['error'] = response['error']
                result['cause'] = response.get('cause', 'Unknown error')
        elif status == 'TIMED_OUT':
            result['message'] = "Batch processing timed out"
        elif status == 'ABORTED':
            result['message'] = "Batch processing was aborted"

        # Add output if execution completed
        if status == 'SUCCEEDED' and 'output' in response:
            try:
                output_data = json.loads(response['output'])
                result['output_summary'] = output_data
            except:
                pass

        # Ensure tool_use_id is preserved as string
        tool_use_id = event.get('id', '')

        # More detailed debugging
        logger.info(f"Event keys: {list(event.keys())}")
        logger.info(f"Raw event.get('id'): {repr(event.get('id'))}")
        logger.info(f"Tool use id before conversion: {tool_use_id}, type: {type(tool_use_id)}")

        # Ensure we're getting the right value and converting properly
        if tool_use_id:
            tool_use_id_str = str(tool_use_id)
        else:
            tool_use_id_str = None

        logger.info(f"Final tool_use_id to return: {tool_use_id_str}")

        return {
            "type": "tool_result",
            "name": event.get('name', 'monitor_batch_execution'),
            "tool_use_id": tool_use_id_str,
            "content": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error monitoring execution: {e}")
        tool_use_id = event.get('id', '')
        tool_use_id_str = str(tool_use_id) if tool_use_id else None

        return {
            "type": "tool_result",
            "name": event.get('name', 'monitor_batch_execution'),
            "tool_use_id": tool_use_id_str,
            "content": json.dumps({
                "error": str(e),
                "message": f"Failed to monitor execution: {e}"
            })
        }