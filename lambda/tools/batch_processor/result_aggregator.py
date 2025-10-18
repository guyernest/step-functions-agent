"""
Result Aggregator Lambda Function for Batch Processor
Combines individual processed results into final CSV output
"""

import json
import csv
import boto3
import io
import os
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Aggregate batch processing results into final CSV

    Event structure for INLINE mode:
    {
        "execution_id": "unique-execution-id",
        "processing_results": [...array of results from Map state...],
        "output_key": "results/execution-id/output.csv",
        "include_original": true,
        "add_metadata": true
    }
    """
    try:
        execution_id = event['execution_id']
        processing_results = event.get('processing_results', [])
        output_key = event['output_key']
        include_original = event.get('include_original', True)
        add_metadata = event.get('add_metadata', True)

        bucket = os.environ.get('RESULTS_BUCKET',
                                boto3.client('ssm').get_parameter(
                                    Name='/ai-agent/batch-processor-results-bucket'
                                )['Parameter']['Value'])

        all_results = []

        # Process results from the Map state (already in memory)
        for result in processing_results:
            process_result_item(result, all_results)

        # If no results found
        if not all_results:
            return {
                'status': 'NO_RESULTS',
                'message': 'No results to aggregate',
                'total_items': len(processing_results)
            }

        # Count successes and failures based on processed results
        failed_count = sum(1 for r in all_results if r.get('_status') == 'FAILED')
        success_count = len(all_results) - failed_count

        # Determine CSV columns with proper ordering
        # Collect all unique columns, separating regular fields from metadata
        regular_columns = []
        metadata_columns = []
        seen = set()

        for result in all_results:
            for col in result.keys():
                if col not in seen:
                    seen.add(col)
                    if col.startswith('_'):
                        metadata_columns.append(col)
                    else:
                        regular_columns.append(col)

        # Order: regular columns (in order they appear) + sorted metadata columns
        final_columns = regular_columns + sorted(metadata_columns)

        # Create CSV in memory
        output_buffer = io.StringIO()
        writer = csv.DictWriter(output_buffer, fieldnames=final_columns)
        writer.writeheader()

        for result in all_results:
            # Ensure all columns have values (empty string for missing)
            row = {col: result.get(col, '') for col in final_columns}
            writer.writerow(row)

        # Upload final CSV to S3
        csv_content = output_buffer.getvalue()
        s3_client.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=csv_content.encode('utf-8'),
            ContentType='text/csv'
        )

        # Generate summary
        summary = {
            'status': 'SUCCESS',
            'output_location': f's3://{bucket}/{output_key}',
            'total_rows': len(all_results),
            'successful_rows': success_count,
            'failed_rows': failed_count,
            'success_rate': f"{(success_count / len(all_results) * 100):.1f}%" if all_results else "0%",
            'columns': len(final_columns),
            'column_names': final_columns[:10],  # First 10 columns for preview
            'execution_id': execution_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"Aggregation complete: {json.dumps(summary)}")

        return summary

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return {
            'status': 'FAILED',
            'error': str(e),
            'execution_id': event.get('execution_id', 'unknown')
        }


def process_result_item(item: Dict[str, Any], results_list: List[Dict[str, Any]]):
    """
    Process a single result item and add to results list

    The item structure from the Map state (Lambda invocation response) is:
    {
        "ExecutedVersion": "$LATEST",
        "Payload": { extracted structured data with all fields },
        "SdkHttpMetadata": {...},
        "StatusCode": 200
    }
    """
    if not isinstance(item, dict):
        logger.warning(f"Unexpected result format: {type(item)}")
        results_list.append({'_error': 'Invalid result format', '_raw': str(item)[:500]})
        return

    # Extract the Payload which contains the actual result data
    if 'Payload' in item and isinstance(item['Payload'], dict):
        result_row = item['Payload'].copy()
        results_list.append(result_row)
    else:
        # Handle missing or invalid payload
        result_row = {
            '_status': 'FAILED',
            '_error': 'No Payload found in Lambda response',
            '_raw': str(item)[:500]  # Truncated for debugging
        }
        results_list.append(result_row)
