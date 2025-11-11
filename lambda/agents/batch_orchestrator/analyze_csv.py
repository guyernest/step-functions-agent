"""
Analyze CSV Structure Tool
Analyzes CSV file structure and content for batch processing
"""

import json
import boto3
import csv
import io
from typing import Dict, Any, List
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Analyze CSV file structure and return metadata

    Tool input:
    {
        "name": "analyze_csv_structure",
        "input": {
            "s3_uri": "s3://bucket/path/file.csv",
            "sample_rows": 5
        }
    }
    """
    try:
        tool_input = event.get('input', {})
        s3_uri = tool_input['s3_uri']
        sample_rows = tool_input.get('sample_rows', 5)

        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")

        parts = s3_uri[5:].split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")

        bucket, key = parts

        # Get the CSV file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8-sig')  # Strip BOM to match csv_loader

        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(content))

        # Get column names
        columns = csv_reader.fieldnames if csv_reader.fieldnames else []

        # Collect sample data and analyze types
        sample_data = []
        row_count = 0
        data_types = {col: set() for col in columns}

        for row in csv_reader:
            row_count += 1

            # Collect sample rows
            if row_count <= sample_rows:
                sample_data.append(row)

            # Analyze data types
            for col, value in row.items():
                if value:
                    # Try to infer type
                    try:
                        float(value)
                        data_types[col].add('number')
                    except:
                        data_types[col].add('string')

        # Simplify data types
        column_types = {}
        for col, types in data_types.items():
            if 'number' in types and len(types) == 1:
                column_types[col] = 'number'
            else:
                column_types[col] = 'string'

        # Generate analysis result
        result = {
            "columns": columns,
            "column_count": len(columns),
            "row_count": row_count,
            "sample_data": sample_data,
            "data_types": column_types,
            "file_info": {
                "bucket": bucket,
                "key": key,
                "size_bytes": response['ContentLength'],
                "last_modified": response['LastModified'].isoformat()
            },
            "analysis_summary": f"CSV file contains {row_count} rows and {len(columns)} columns"
        }

        return {
            "type": "tool_result",
            "name": event.get('name', 'analyze_csv_structure'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error analyzing CSV: {e}")
        return {
            "type": "tool_result",
            "name": event.get('name', 'analyze_csv_structure'),
            "tool_use_id": str(event.get('id', '')) if event.get('id') else None,
            "content": json.dumps({
                "error": str(e),
                "message": f"Failed to analyze CSV: {e}"
            })
        }