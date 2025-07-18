import json
import os
import boto3
from botocore.exceptions import ClientError

def log_library_versions():
    """Log versions of key libraries for debugging"""
    try:
        import boto3
        print(f"DEBUG: boto3 version: {boto3.__version__}")
    except Exception as e:
        print(f"DEBUG: Error getting boto3 version: {e}")
    
    try:
        import botocore
        print(f"DEBUG: botocore version: {botocore.__version__}")
    except Exception as e:
        print(f"DEBUG: Error getting botocore version: {e}")
    
    try:
        import sys
        print(f"DEBUG: Python version: {sys.version}")
        print(f"DEBUG: Python executable: {sys.executable}")
        print(f"DEBUG: Python path: {sys.path[:5]}...")  # First 5 entries
    except Exception as e:
        print(f"DEBUG: Error getting Python info: {e}")
    
    try:
        import aws_lambda_powertools
        print(f"DEBUG: aws-lambda-powertools version: {aws_lambda_powertools.__version__}")
    except Exception as e:
        print(f"DEBUG: aws-lambda-powertools not available or error: {e}")
    
    try:
        import pydantic
        print(f"DEBUG: pydantic version: {pydantic.__version__}")
    except Exception as e:
        print(f"DEBUG: pydantic not available or error: {e}")
    
    try:
        import pydantic_core
        print(f"DEBUG: pydantic_core version: {pydantic_core.__version__}")
    except Exception as e:
        print(f"DEBUG: pydantic_core not available or error: {e}")

def get_api_keys():
    """
    Get LLM API keys from the centralized secrets manager.
    Uses environment-specific secret path for better isolation.
    """
    try:
        # Log library versions for debugging
        log_library_versions()
        
        # Get environment from Lambda environment variable, default to 'prod'
        environment = os.environ.get("ENVIRONMENT", "prod")
        
        # Use the new centralized LLM secrets path
        secret_path = f"/ai-agent/llm-secrets/{environment}"
        
        print(f"DEBUG: About to create boto3 client for secrets manager")
        print(f"DEBUG: Environment: {environment}")
        print(f"DEBUG: Secret path: {secret_path}")
        
        # Create Secrets Manager client with minimal configuration
        print(f"DEBUG: Environment variables related to AWS:")
        aws_env_vars = {k: v for k, v in os.environ.items() if 'AWS' in k}
        for k, v in aws_env_vars.items():
            print(f"DEBUG: {k} = {v[:50]}..." if len(v) > 50 else f"DEBUG: {k} = {v}")
        
        print(f"DEBUG: Creating boto3 session first...")
        # Create session first to avoid aws_account_id parameter issues
        session = boto3.Session(
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
        print(f"DEBUG: Session created, now creating secretsmanager client...")
        client = session.client('secretsmanager')
        print(f"DEBUG: Client created successfully")
        
        # Get the secret value
        print(f"DEBUG: About to call get_secret_value...")
        response = client.get_secret_value(SecretId=secret_path)
        print(f"DEBUG: get_secret_value call successful")
        
        # Parse the JSON secret value
        secret_string = response['SecretString']
        keys = json.loads(secret_string)
        
        print(f"DEBUG: Successfully retrieved and parsed {len(keys)} keys")
        return keys
    except ClientError as e:
        print(f"DEBUG: ClientError occurred: {str(e)}")
        raise ValueError(f"LLM API keys not found in Secrets Manager at {secret_path}: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSONDecodeError occurred: {str(e)}")
        raise ValueError(f"Invalid JSON in secret at {secret_path}: {str(e)}")
    except Exception as e:
        print(f"DEBUG: Exception occurred: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        raise ValueError(f"Error retrieving LLM API keys from {secret_path}: {str(e)}")