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
        failed_count = 0
        success_count = 0

        # Process results from the Map state (already in memory)
        for result in processing_results:
            if isinstance(result, dict):
                process_result_item(result, all_results)
                if result.get('_status') == 'FAILED':
                    failed_count += 1
                else:
                    success_count += 1
            else:
                logger.warning(f"Unexpected result format: {type(result)}")
                failed_count += 1

        # If no results found
        if not all_results:
            return {
                'status': 'NO_RESULTS',
                'message': 'No results to aggregate',
                'files_processed': total_files
            }

        # Determine CSV columns with proper ordering
        # Use a list to preserve insertion order
        original_columns = []
        output_columns = []
        metadata_columns = []
        seen_columns = set()

        # First pass: get column order from first result (preserves input order)
        if all_results:
            first_result = all_results[0]
            for col in first_result.keys():
                if col not in seen_columns:
                    seen_columns.add(col)
                    if col.startswith('_'):
                        metadata_columns.append(col)
                    else:
                        # Columns from original input will appear first in the result
                        original_columns.append(col)

        # Second pass: collect any additional columns from other results
        for result in all_results[1:]:
            for col in result.keys():
                if col not in seen_columns:
                    seen_columns.add(col)
                    if col.startswith('_'):
                        if col not in metadata_columns:
                            metadata_columns.append(col)
                    else:
                        original_columns.append(col)

        # Order: original columns (in order they appear) + metadata columns
        final_columns = original_columns + sorted(metadata_columns)

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

    The item structure from the Map state is:
    {
        "row": { original CSV row data },
        "structured_result": {
            "Payload": { extracted structured data or error }
        }
    }
    """
    if isinstance(item, dict):
        result_row = {}

        # First, get the original row data if requested
        if 'row' in item:
            original_row = item['row']
            if isinstance(original_row, dict):
                result_row.update(original_row)

        # Then extract the structured result
        if 'structured_result' in item:
            structured_result = item['structured_result']

            # Handle Lambda response wrapper
            if isinstance(structured_result, dict) and 'Payload' in structured_result:
                payload = structured_result['Payload']

                # The payload should contain the extracted fields
                if isinstance(payload, dict):
                    # Add all fields from the payload (structured output + metadata)
                    result_row.update(payload)
            elif isinstance(structured_result, dict):
                # Direct structured result
                result_row.update(structured_result)

        # If we didn't get any data, at least record an error
        if not result_row:
            result_row = {
                '_status': 'FAILED',
                '_error': 'No data extracted',
                '_raw': str(item)[:500]  # Truncated for debugging
            }

        results_list.append(result_row)
    else:
        # Handle unexpected format
        logger.warning(f"Unexpected result format: {type(item)}")
        results_list.append({'_error': 'Invalid result format', '_data': str(item)})