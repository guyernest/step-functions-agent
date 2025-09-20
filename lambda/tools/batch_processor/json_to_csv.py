"""
JSON to CSV Converter Lambda
Converts JSON Lines output from ResultWriter directly to CSV
Much simpler than using Athena!
"""

import json
import csv
import boto3
import io
from typing import List, Dict, Any
from urllib.parse import urlparse

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Convert JSON results to CSV

    Event (INLINE mode):
    {
        "rows": [...],
        "output_bucket": "bucket-name",
        "execution_name": "execution-id"
    }

    Event (DISTRIBUTED mode - legacy):
    {
        "input_location": "s3://bucket/batch-results/xxx/raw/",
        "output_location": "s3://bucket/batch-results/xxx/final/output.csv"
    }
    """
    # Check if we're in INLINE mode (rows provided directly)
    if 'rows' in event:
        json_data = event['rows']
        output_bucket = event['output_bucket']
        execution_name = event.get('execution_name', 'output')
        output_location = f"s3://{output_bucket}/batch-results/{execution_name}/final/output.csv"
    else:
        # DISTRIBUTED mode - read from S3
        input_location = event['input_location']
        output_location = event['output_location']
        json_data = read_json_lines_from_s3(input_location)
    
    if not json_data:
        return {
            "status": "NO_DATA",
            "message": "No results to convert"
        }
    
    # Convert to CSV
    csv_content = convert_to_csv(json_data)
    
    # Write CSV to S3
    write_csv_to_s3(csv_content, output_location)
    
    return {
        "status": "SUCCESS",
        "csv_location": output_location,
        "row_count": len(json_data)
    }

def read_json_lines_from_s3(location: str) -> List[Dict[str, Any]]:
    """Read JSON Lines files from S3 location"""
    # Parse S3 location
    parsed = urlparse(location)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip('/')
    
    # List all objects in the prefix
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix
    )
    
    all_data = []
    
    if 'Contents' in response:
        for obj in response['Contents']:
            # Read each file
            file_response = s3_client.get_object(
                Bucket=bucket,
                Key=obj['Key']
            )
            
            # Parse JSON Lines
            content = file_response['Body'].read().decode('utf-8')
            for line in content.strip().split('\n'):
                if line:
                    try:
                        all_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # Skip malformed lines
    
    return all_data

def convert_to_csv(data: List[Dict[str, Any]]) -> str:
    """Convert list of dicts to CSV string"""
    if not data:
        return ""
    
    # Get all unique keys across all records
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())
    
    # Sort keys to ensure consistent column order
    # Put metadata columns at the end
    metadata_cols = [k for k in all_keys if k.startswith('_')]
    data_cols = [k for k in all_keys if not k.startswith('_')]
    
    fieldnames = sorted(data_cols) + sorted(metadata_cols)
    
    # Write CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()

def write_csv_to_s3(csv_content: str, location: str):
    """Write CSV content to S3"""
    # Parse S3 location
    parsed = urlparse(location)
    bucket = parsed.netloc
    key = parsed.path.lstrip('/')
    
    # Upload to S3
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_content.encode('utf-8'),
        ContentType='text/csv'
    )

# Test case
if __name__ == "__main__":
    test_data = [
        {
            "customer_id": "123",
            "query": "Help with billing",
            "category": "Billing",
            "priority": "High",
            "_status": "SUCCESS",
            "_execution_time_ms": 1250
        },
        {
            "customer_id": "124",
            "query": "Password reset",
            "category": "Authentication",
            "priority": "Medium",
            "_status": "SUCCESS",
            "_execution_time_ms": 980
        }
    ]
    
    print("Sample CSV output:")
    print(convert_to_csv(test_data))