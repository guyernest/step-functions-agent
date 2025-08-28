"""
MCP Registry GraphQL Resolver Lambda Function

This Lambda function provides GraphQL resolvers for the MCP Registry,
allowing queries and mutations for MCP server management.
"""

import json
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
app = AppSyncResolver()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

def get_table_name():
    """Get the MCP Registry table name from environment variables"""
    import os
    env_name = os.environ.get('ENVIRONMENT', 'prod')
    return f"MCPServerRegistry-{env_name}"

def decimal_default(obj):
    """JSON serializer for Decimal types"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def parse_dynamodb_item(item: Dict) -> Dict:
    """Parse DynamoDB item and convert types for GraphQL"""
    if not item:
        return None
    
    # Convert Decimal to float for numeric fields
    for key in ['health_check_interval']:
        if key in item and isinstance(item[key], Decimal):
            item[key] = float(item[key])
    
    # Parse JSON fields
    for key in ['available_tools', 'configuration', 'metadata']:
        if key in item and isinstance(item[key], str):
            try:
                item[key] = json.loads(item[key])
            except json.JSONDecodeError:
                pass
    
    return item

# Query Resolvers

@app.resolver(type_name="Query", field_name="listMCPServersFromRegistry")
@tracer.capture_method
def list_mcp_servers(**kwargs) -> List[Dict]:
    """List all MCP servers from the registry"""
    try:
        table = dynamodb.Table(get_table_name())
        response = table.scan()
        
        servers = []
        for item in response.get('Items', []):
            servers.append(parse_dynamodb_item(item))
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            for item in response.get('Items', []):
                servers.append(parse_dynamodb_item(item))
        
        logger.info(f"Retrieved {len(servers)} MCP servers")
        return servers
        
    except Exception as e:
        logger.error(f"Error listing MCP servers: {str(e)}")
        raise

@app.resolver(type_name="Query", field_name="getMCPServer")
@tracer.capture_method
def get_mcp_server(server_id: str, version: Optional[str] = None) -> Dict:
    """Get specific MCP server details"""
    try:
        table = dynamodb.Table(get_table_name())
        
        if version:
            # Get specific version
            response = table.get_item(
                Key={
                    'server_id': server_id,
                    'version': version
                }
            )
            item = response.get('Item')
        else:
            # Get latest version
            response = table.query(
                KeyConditionExpression='server_id = :sid',
                ExpressionAttributeValues={
                    ':sid': server_id
                },
                ScanIndexForward=False,  # Sort descending by version
                Limit=1
            )
            items = response.get('Items', [])
            item = items[0] if items else None
        
        return parse_dynamodb_item(item)
        
    except Exception as e:
        logger.error(f"Error getting MCP server {server_id}: {str(e)}")
        raise

@app.resolver(type_name="Query", field_name="listMCPServersByStatus")
@tracer.capture_method
def list_mcp_servers_by_status(status: str) -> List[Dict]:
    """Find MCP servers by status using GSI"""
    try:
        table = dynamodb.Table(get_table_name())
        
        response = table.query(
            IndexName='MCPServersByStatus',
            KeyConditionExpression='status = :status',
            ExpressionAttributeValues={
                ':status': status
            }
        )
        
        servers = []
        for item in response.get('Items', []):
            servers.append(parse_dynamodb_item(item))
        
        logger.info(f"Found {len(servers)} servers with status {status}")
        return servers
        
    except Exception as e:
        logger.error(f"Error querying servers by status: {str(e)}")
        raise

@app.resolver(type_name="Query", field_name="listMCPServersByProtocol")
@tracer.capture_method
def list_mcp_servers_by_protocol(protocol_type: str) -> List[Dict]:
    """Find MCP servers by protocol type using GSI"""
    try:
        table = dynamodb.Table(get_table_name())
        
        response = table.query(
            IndexName='MCPServersByProtocol',
            KeyConditionExpression='protocol_type = :protocol',
            ExpressionAttributeValues={
                ':protocol': protocol_type
            }
        )
        
        servers = []
        for item in response.get('Items', []):
            servers.append(parse_dynamodb_item(item))
        
        logger.info(f"Found {len(servers)} servers with protocol {protocol_type}")
        return servers
        
    except Exception as e:
        logger.error(f"Error querying servers by protocol: {str(e)}")
        raise

@app.resolver(type_name="Query", field_name="testMCPServerConnection")
@tracer.capture_method
def test_mcp_server_connection(server_id: str) -> Dict:
    """Test MCP server connection"""
    import requests
    import time
    
    try:
        # Get server details
        server = get_mcp_server(server_id)
        if not server:
            return {
                'success': False,
                'message': f'Server {server_id} not found',
                'response_time': 0
            }
        
        endpoint_url = server.get('endpoint_url')
        protocol_type = server.get('protocol_type', 'jsonrpc')
        auth_type = server.get('authentication_type', 'none')
        
        # Prepare request based on protocol
        start_time = time.time()
        
        if protocol_type == 'jsonrpc':
            # Test JSON-RPC ping
            headers = {'Content-Type': 'application/json'}
            
            # Add authentication if needed
            if auth_type == 'api_key':
                api_key_header = server.get('api_key_header', 'x-api-key')
                # In production, fetch from Secrets Manager
                headers[api_key_header] = 'test-api-key'
            
            payload = {
                'jsonrpc': '2.0',
                'method': 'ping',
                'id': 1
            }
            
            response = requests.post(
                endpoint_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            success = response.status_code == 200
            message = 'Connection successful' if success else f'HTTP {response.status_code}'
            
        elif protocol_type == 'rest':
            # Test REST health check
            health_url = server.get('health_check_url', endpoint_url + '/health')
            response = requests.get(health_url, timeout=5)
            success = response.status_code == 200
            message = 'Health check passed' if success else f'HTTP {response.status_code}'
            
        else:
            success = False
            message = f'Protocol {protocol_type} not supported for testing'
        
        response_time = int((time.time() - start_time) * 1000)  # ms
        
        return {
            'success': success,
            'message': message,
            'response_time': response_time,
            'server_id': server_id,
            'endpoint_url': endpoint_url
        }
        
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Connection timeout',
            'response_time': 5000,
            'server_id': server_id
        }
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'response_time': 0,
            'server_id': server_id
        }

# Mutation Resolvers

@app.resolver(type_name="Mutation", field_name="registerMCPServer")
@tracer.capture_method
def register_mcp_server(input: Dict) -> Dict:
    """Register a new MCP server"""
    try:
        table = dynamodb.Table(get_table_name())
        
        # Generate server_id if not provided
        server_id = input.get('server_id')
        if not server_id:
            import hashlib
            endpoint = input.get('endpoint_url', '')
            server_id = f"mcp-{hashlib.md5(endpoint.encode()).hexdigest()[:8]}"
        
        # Set defaults
        version = input.get('version', '1.0.0')
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare item
        item = {
            'server_id': server_id,
            'version': version,
            'server_name': input['server_name'],
            'description': input.get('description', ''),
            'endpoint_url': input['endpoint_url'],
            'protocol_type': input.get('protocol_type', 'jsonrpc'),
            'authentication_type': input.get('authentication_type', 'none'),
            'available_tools': json.dumps(input.get('available_tools', [])),
            'status': 'pending',  # New registrations start as pending
            'configuration': json.dumps(input.get('configuration', {})),
            'metadata': json.dumps(input.get('metadata', {})),
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': input.get('created_by', 'api')
        }
        
        # Add optional fields
        if 'api_key_header' in input:
            item['api_key_header'] = input['api_key_header']
        if 'health_check_url' in input:
            item['health_check_url'] = input['health_check_url']
        if 'health_check_interval' in input:
            item['health_check_interval'] = input['health_check_interval']
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        logger.info(f"Registered MCP server: {server_id}")
        
        return {
            'success': True,
            'server_id': server_id,
            'version': version,
            'message': 'Server registered successfully (pending approval)'
        }
        
    except Exception as e:
        logger.error(f"Error registering MCP server: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

@app.resolver(type_name="Mutation", field_name="updateMCPServerStatus")
@tracer.capture_method
def update_mcp_server_status(server_id: str, version: str, status: str) -> Dict:
    """Update MCP server status"""
    try:
        table = dynamodb.Table(get_table_name())
        
        # Validate status
        valid_statuses = ['active', 'inactive', 'maintenance', 'unhealthy', 'pending']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        # Update item
        response = table.update_item(
            Key={
                'server_id': server_id,
                'version': version
            },
            UpdateExpression='SET #status = :status, updated_at = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':updated': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        logger.info(f"Updated status for {server_id} to {status}")
        
        return {
            'success': True,
            'server_id': server_id,
            'version': version,
            'status': status,
            'message': f'Status updated to {status}'
        }
        
    except Exception as e:
        logger.error(f"Error updating server status: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

@app.resolver(type_name="Mutation", field_name="approveMCPServer")
@tracer.capture_method
def approve_mcp_server(server_id: str) -> Dict:
    """Approve a pending MCP server"""
    try:
        # Get latest version
        server = get_mcp_server(server_id)
        if not server:
            return {
                'success': False,
                'message': f'Server {server_id} not found'
            }
        
        # Update status to active
        result = update_mcp_server_status(
            server_id,
            server['version'],
            'active'
        )
        
        if result['success']:
            logger.info(f"Approved MCP server: {server_id}")
            # TODO: Send notification to server owner
        
        return result
        
    except Exception as e:
        logger.error(f"Error approving server: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

# Lambda handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event: Dict, context: LambdaContext) -> Dict:
    """Main Lambda handler for AppSync GraphQL resolver"""
    return app.resolve(event, context)