#!/usr/bin/env python3
"""
Script to populate the MCP Registry with the current MCP server implementation
"""

import boto3
import json
from datetime import datetime
import sys

def populate_mcp_registry():
    """Populate the MCP Registry DynamoDB table with the current MCP server"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table_name = 'MCPServerRegistry-prod'
    
    try:
        table = dynamodb.Table(table_name)
        print(f"Connected to table: {table_name}")
    except Exception as e:
        print(f"Error connecting to table {table_name}: {e}")
        return False
    
    # MCP Server details from the implementation
    mcp_server = {
        'server_id': 'step-functions-agents-mcp-prod',
        'version': '1.0.0',
        'server_name': 'Step Functions Agents MCP Server',
        'description': 'MCP server providing access to AWS Step Functions agents for AI-powered task execution and automation',
        'endpoint_url': 'https://4w07f1jc72.execute-api.eu-west-1.amazonaws.com/mcp',
        'protocol_type': 'jsonrpc',
        'authentication_type': 'api_key',
        'api_key_header': 'x-api-key',
        'available_tools': json.dumps([
            {
                'name': 'start_agent',
                'description': 'Start execution of a Step Functions agent',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'agent_name': {
                            'type': 'string',
                            'description': 'Name of the agent to execute'
                        },
                        'input_message': {
                            'type': 'string',
                            'description': 'Input message for the agent'
                        },
                        'execution_name': {
                            'type': 'string',
                            'description': 'Optional execution name'
                        }
                    },
                    'required': ['agent_name', 'input_message']
                }
            },
            {
                'name': 'get_execution_status',
                'description': 'Get status of an agent execution',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'execution_arn': {
                            'type': 'string',
                            'description': 'ARN of the execution to check'
                        }
                    },
                    'required': ['execution_arn']
                }
            },
            {
                'name': 'list_available_agents',
                'description': 'List all available agents from the registry',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            }
        ]),
        'status': 'active',
        'health_check_url': 'https://4w07f1jc72.execute-api.eu-west-1.amazonaws.com/health',
        'health_check_interval': 300,
        'configuration': json.dumps({
            'timeout_seconds': 30,
            'max_retries': 3,
            'supports_batch': False,
            'protocol_version': '2024-11-05',
            'lambda_function': 'step-functions-agents-prod-mcp-server'
        }),
        'metadata': json.dumps({
            'managed_by': 'amplify',
            'team': 'platform',
            'environment': 'production',
            'cost_center': 'engineering',
            'tags': ['production', 'critical', 'agent-management', 'mcp'],
            'implementation': 'rust',
            'aws_region': 'eu-west-1',
            'api_gateway_id': '4w07f1jc72',
            'lambda_arn': 'arn:aws:lambda:eu-west-1:816069129666:function:step-functions-agents-prod-mcp-server'
        }),
        'deployment_stack': 'step-functions-agents-prod-mcp',
        'deployment_region': 'eu-west-1',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'created_by': 'system'
    }
    
    try:
        # Check if the item already exists
        response = table.get_item(
            Key={
                'server_id': mcp_server['server_id'],
                'version': mcp_server['version']
            }
        )
        
        if 'Item' in response:
            print(f"MCP server {mcp_server['server_id']} v{mcp_server['version']} already exists. Updating...")
            # Preserve created_at from existing item
            mcp_server['created_at'] = response['Item'].get('created_at', mcp_server['created_at'])
        else:
            print(f"Creating new MCP server entry: {mcp_server['server_id']} v{mcp_server['version']}")
        
        # Put the item
        table.put_item(Item=mcp_server)
        
        print("✅ Successfully populated MCP Registry!")
        print(f"   Server ID: {mcp_server['server_id']}")
        print(f"   Version: {mcp_server['version']}")
        print(f"   Endpoint: {mcp_server['endpoint_url']}")
        print(f"   Status: {mcp_server['status']}")
        print(f"   Tools: {len(json.loads(mcp_server['available_tools']))} available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating MCP Registry: {e}")
        return False

def verify_registry():
    """Verify that the MCP Registry was populated correctly"""
    
    dynamodb = boto3.resource('dynamodb')
    table_name = 'MCPServerRegistry-prod'
    
    try:
        table = dynamodb.Table(table_name)
        
        # Scan the table to get all items
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"\n📊 MCP Registry Status:")
        print(f"   Total servers: {len(items)}")
        
        for item in items:
            tools = json.loads(item.get('available_tools', '[]'))
            print(f"   • {item['server_name']} (v{item['version']})")
            print(f"     Status: {item['status']}")
            print(f"     Endpoint: {item['endpoint_url']}")
            print(f"     Tools: {len(tools)}")
            print(f"     Protocol: {item['protocol_type']}")
            print(f"     Auth: {item['authentication_type']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying MCP Registry: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Populating MCP Server Registry...")
    print()
    
    # Populate the registry
    if populate_mcp_registry():
        # Verify the population
        verify_registry()
        print("✅ MCP Registry setup complete!")
    else:
        print("❌ Failed to populate MCP Registry")
        sys.exit(1)