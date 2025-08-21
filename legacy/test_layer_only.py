#!/usr/bin/env python3
"""
Simple Lambda test that only uses the layer (not anthropic dependencies)
"""

def lambda_handler(event, context):
    """Test the layer imports and boto3 client creation"""
    try:
        import sys
        print(f"Python path: {sys.path}")
        
        # Test the layer imports
        from common.config import get_api_keys
        print("Successfully imported from layer")
        
        # Test boto3 client creation (should not have aws_account_id error anymore)
        import boto3
        client = boto3.client('secretsmanager', region_name='us-west-2')
        print("Successfully created boto3 client")
        
        return {
            "statusCode": 200,
            "body": {
                "message": "Layer test successful - no aws_account_id error",
                "boto3_working": True
            }
        }
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        }