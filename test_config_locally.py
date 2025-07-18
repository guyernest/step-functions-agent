#!/usr/bin/env python3
"""
Test the config.py locally to debug the aws_account_id issue
"""
import os
import sys

# Add the lambda layer to the path
sys.path.insert(0, 'lambda/call_llm/lambda_layer/python')

# Set environment variable
os.environ['ENVIRONMENT'] = 'prod'

# Test the get_api_keys function
try:
    from common.config import get_api_keys
    print("Successfully imported get_api_keys")
    
    # Try to call it
    keys = get_api_keys()
    print(f"Successfully retrieved keys: {list(keys.keys())}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()