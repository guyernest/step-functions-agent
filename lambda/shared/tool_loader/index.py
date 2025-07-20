"""
Tool Loader Lambda Function

This function dynamically loads tool definitions from DynamoDB registry
at Step Functions execution time based on a list of tool names.
"""
import json
import os
import boto3
from typing import List, Dict, Any

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Load tool definitions from DynamoDB registry
    
    Args:
        event: Contains 'tool_names' - list of tool names to load
        
    Returns:
        Dict with 'tools' containing the full tool definitions with schemas
    """
    try:
        tool_names = event.get('tool_names', [])
        
        if not tool_names:
            return {
                'statusCode': 200,
                'tools': []
            }
        
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('TOOL_REGISTRY_TABLE_NAME')
        table = dynamodb.Table(table_name)
        
        tools = []
        
        # Load each tool definition from DynamoDB
        for tool_name in tool_names:
            try:
                # Use correct DynamoDB key schema: tool_name (partition) + version (sort)
                response = table.get_item(
                    Key={
                        'tool_name': tool_name,
                        'version': '1.0.0'  # Default version for all tools
                    }
                )
                
                if 'Item' in response:
                    item = response['Item']
                    
                    # Convert DynamoDB item to tool definition format expected by LLM
                    tool_def = {
                        'name': item['tool_name'],
                        'description': item['description'],
                        'input_schema': item['input_schema']
                    }
                    
                    tools.append(tool_def)
                    print(f"Loaded tool: {tool_name}")
                else:
                    print(f"Warning: Tool '{tool_name}' not found in registry")
                    
            except Exception as e:
                print(f"Error loading tool '{tool_name}': {str(e)}")
                # Continue with other tools even if one fails
                continue
        
        print(f"Successfully loaded {len(tools)} tools: {[t['name'] for t in tools]}")
        
        return {
            'statusCode': 200,
            'tools': tools
        }
        
    except Exception as e:
        print(f"Error in tool loader: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'tools': []
        }