"""
Secret Structure Manager Lambda
Manages the structure of consolidated tool secrets dynamically
"""

import json
import boto3
import os
from typing import Dict, Any
from datetime import datetime

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')

# Environment variables
CONSOLIDATED_SECRET_NAME = os.environ['CONSOLIDATED_SECRET_NAME']
TOOL_SECRETS_TABLE_NAME = os.environ['TOOL_SECRETS_TABLE_NAME']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'prod')

# DynamoDB table
tool_secrets_table = dynamodb.Table(TOOL_SECRETS_TABLE_NAME)


def handler(event, context):
    """
    Lambda handler for managing tool secret structure
    
    Supported operations:
    - register_tool: Register a new tool's secret requirements
    - update_secret: Update a specific tool's secret values
    - get_tool_secrets: Get secrets for a specific tool
    - list_tools: List all registered tools
    """
    
    operation = event.get('operation')
    
    if operation == 'register_tool':
        return register_tool(event)
    elif operation == 'update_secret':
        return update_secret(event)
    elif operation == 'get_tool_secrets':
        return get_tool_secrets(event)
    elif operation == 'list_tools':
        return list_tools()
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unsupported operation: {operation}'})
        }


def register_tool(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a new tool's secret requirements in DynamoDB
    
    Expected event structure:
    {
        "operation": "register_tool",
        "tool_name": "google-maps",
        "secret_keys": ["GOOGLE_MAPS_API_KEY"],
        "description": "Google Maps API key for geocoding and places"
    }
    """
    
    tool_name = event.get('tool_name')
    secret_keys = event.get('secret_keys', [])
    description = event.get('description', '')
    
    if not tool_name or not secret_keys:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'tool_name and secret_keys are required'})
        }
    
    # Register in DynamoDB
    try:
        tool_secrets_table.put_item(
            Item={
                'tool_name': tool_name,
                'secret_keys': secret_keys,
                'description': description,
                'registered_at': datetime.utcnow().isoformat(),
                'environment': ENVIRONMENT
            }
        )
        
        # Update the consolidated secret structure
        update_consolidated_secret_structure()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Tool {tool_name} registered successfully',
                'tool_name': tool_name,
                'secret_keys': secret_keys
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def update_secret(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a specific tool's secret values
    
    Expected event structure:
    {
        "operation": "update_secret",
        "tool_name": "google-maps",
        "secrets": {
            "GOOGLE_MAPS_API_KEY": "actual-api-key-value"
        }
    }
    """
    
    tool_name = event.get('tool_name')
    secrets = event.get('secrets', {})
    
    if not tool_name or not secrets:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'tool_name and secrets are required'})
        }
    
    try:
        # Get current consolidated secret
        response = secretsmanager.get_secret_value(SecretId=CONSOLIDATED_SECRET_NAME)
        current_secrets = json.loads(response['SecretString'])
        
        # Update with new values
        if tool_name not in current_secrets:
            current_secrets[tool_name] = {}
        
        current_secrets[tool_name].update(secrets)
        
        # Save back to Secrets Manager
        secretsmanager.update_secret(
            SecretId=CONSOLIDATED_SECRET_NAME,
            SecretString=json.dumps(current_secrets)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Secrets for {tool_name} updated successfully',
                'tool_name': tool_name
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_tool_secrets(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get secrets for a specific tool
    
    Expected event structure:
    {
        "operation": "get_tool_secrets",
        "tool_name": "google-maps"
    }
    """
    
    tool_name = event.get('tool_name')
    
    if not tool_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'tool_name is required'})
        }
    
    try:
        # Get consolidated secret
        response = secretsmanager.get_secret_value(SecretId=CONSOLIDATED_SECRET_NAME)
        all_secrets = json.loads(response['SecretString'])
        
        tool_secrets = all_secrets.get(tool_name, {})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'tool_name': tool_name,
                'secrets': tool_secrets
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def list_tools() -> Dict[str, Any]:
    """
    List all registered tools
    """
    
    try:
        response = tool_secrets_table.scan()
        tools = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = tool_secrets_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            tools.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'tools': tools,
                'count': len(tools)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def update_consolidated_secret_structure():
    """
    Update the consolidated secret structure based on registered tools
    Ensures all registered tools have placeholder entries in the secret
    """
    
    try:
        # Get all registered tools
        response = tool_secrets_table.scan()
        tools = response.get('Items', [])
        
        # Get current consolidated secret
        secret_response = secretsmanager.get_secret_value(SecretId=CONSOLIDATED_SECRET_NAME)
        current_secrets = json.loads(secret_response['SecretString'])
        
        # Ensure each tool has an entry with placeholder values
        for tool in tools:
            tool_name = tool['tool_name']
            secret_keys = tool.get('secret_keys', [])
            
            if tool_name not in current_secrets:
                current_secrets[tool_name] = {}
            
            # Add placeholder for any missing keys
            for key in secret_keys:
                if key not in current_secrets[tool_name]:
                    current_secrets[tool_name][key] = f"PLACEHOLDER_{key}"
        
        # Update the secret
        secretsmanager.update_secret(
            SecretId=CONSOLIDATED_SECRET_NAME,
            SecretString=json.dumps(current_secrets)
        )
        
    except Exception as e:
        print(f"Error updating consolidated secret structure: {e}")
        raise