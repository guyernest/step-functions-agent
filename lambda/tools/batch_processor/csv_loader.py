"""
CSV Loader Lambda
Loads CSV from S3 and returns as array for INLINE Map processing
"""

import json
import boto3
import csv
import io
from typing import Dict, Any, List

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Load CSV from S3 and return as list of dictionaries
    """
    # Parse S3 URI
    csv_s3_uri = event.get('csv_s3_uri')
    if csv_s3_uri:
        # Parse from URI format
        parts = csv_s3_uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''
    else:
        # Use bucket/key format
        bucket = event['input_bucket']
        key = event['input_key']

    # Read CSV from S3
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8-sig')  # Handle BOM

    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(content))
    rows = []

    for i, row in enumerate(csv_reader):
        # Add row metadata
        row['_row_number'] = i + 1
        row['_row_id'] = f"row_{i+1}"
        rows.append(row)

    return {
        'rows': rows,
        'total_rows': len(rows),
        'columns': list(csv_reader.fieldnames or [])
    }