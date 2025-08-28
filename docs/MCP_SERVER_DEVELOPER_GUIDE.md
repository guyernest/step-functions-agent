# MCP Server Developer Integration Guide

## Quick Start

This guide shows you how to integrate your MCP server with the Step Functions Agent Framework's MCP Registry using AWS CDK, similar to how agents and tools are registered.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [CDK Integration Pattern](#cdk-integration-pattern)
3. [Registration Methods](#registration-methods)
4. [Implementation Examples](#implementation-examples)
5. [Testing Your Integration](#testing-your-integration)
6. [Best Practices](#best-practices)

## Prerequisites

- AWS CDK v2 installed
- Python 3.9+ for CDK stacks
- Access to Step Functions Agent Framework infrastructure
- MCP server endpoint deployed and accessible

## CDK Integration Pattern

### Option 1: Direct Registration in CDK Stack (Recommended)

Similar to how agents register in `AgentRegistryStack`, you can register your MCP server during stack deployment:

```python
# your_mcp_server_stack.py
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    CustomResource,
    custom_resources as cr,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct
import json
from datetime import datetime

class YourMCPServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Your MCP server Lambda or container
        mcp_server_function = _lambda.Function(
            self,
            "MCPServerFunction",
            # ... your function configuration
        )
        
        # Register with MCP Registry
        self.register_mcp_server(
            server_id=f"your-mcp-server-{env_name}",
            server_name="Your MCP Server",
            endpoint_url=mcp_server_function.function_url.url,  # or API Gateway URL
            protocol_type="jsonrpc",
            authentication_type="api_key",  # or "none", "oauth", "iam"
            available_tools=self.get_tool_definitions(),
            env_name=env_name
        )
    
    def register_mcp_server(
        self,
        server_id: str,
        server_name: str,
        endpoint_url: str,
        protocol_type: str,
        authentication_type: str,
        available_tools: list,
        env_name: str
    ):
        """Register MCP server in the registry during deployment"""
        
        # Reference the MCP Registry table
        registry_table = dynamodb.Table.from_table_name(
            self,
            "MCPRegistryTable",
            f"MCPServerRegistry-{env_name}"
        )
        
        # Create custom resource for registration
        register_provider = cr.Provider(
            self,
            "MCPRegistrationProvider",
            on_event_handler=self.create_registration_lambda()
        )
        
        CustomResource(
            self,
            "MCPServerRegistration",
            service_token=register_provider.service_token,
            properties={
                "TableName": registry_table.table_name,
                "ServerId": server_id,
                "ServerName": server_name,
                "EndpointUrl": endpoint_url,
                "ProtocolType": protocol_type,
                "AuthenticationType": authentication_type,
                "AvailableTools": json.dumps(available_tools),
                "Status": "active",
                "DeploymentStack": self.stack_name,
                "DeploymentRegion": self.region,
                "Version": "1.0.0"
            }
        )
        
        # Output registration details
        CfnOutput(
            self,
            "MCPServerRegistrationInfo",
            value=json.dumps({
                "server_id": server_id,
                "endpoint_url": endpoint_url,
                "status": "registered"
            }),
            description="MCP Server registration information"
        )
    
    def get_tool_definitions(self) -> list:
        """Define available tools for this MCP server"""
        return [
            {
                "name": "your_tool_1",
                "description": "Description of what this tool does",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "First parameter"
                        },
                        "param2": {
                            "type": "number",
                            "description": "Second parameter"
                        }
                    },
                    "required": ["param1"]
                }
            },
            {
                "name": "your_tool_2",
                "description": "Another tool description",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Input data"
                        }
                    },
                    "required": ["data"]
                }
            }
        ]
    
    def create_registration_lambda(self) -> _lambda.Function:
        """Create Lambda function for custom resource registration"""
        return _lambda.Function(
            self,
            "RegistrationHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_inline("""
import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    request_type = event['RequestType']
    properties = event['ResourceProperties']
    
    table = dynamodb.Table(properties['TableName'])
    
    if request_type in ['Create', 'Update']:
        # Register or update MCP server
        item = {
            'server_id': properties['ServerId'],
            'version': properties['Version'],
            'server_name': properties['ServerName'],
            'endpoint_url': properties['EndpointUrl'],
            'protocol_type': properties['ProtocolType'],
            'authentication_type': properties['AuthenticationType'],
            'available_tools': json.loads(properties['AvailableTools']),
            'status': properties['Status'],
            'deployment_stack': properties.get('DeploymentStack', ''),
            'deployment_region': properties.get('DeploymentRegion', ''),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
        
        return {
            'PhysicalResourceId': properties['ServerId'],
            'Data': {
                'ServerID': properties['ServerId'],
                'Status': 'Registered'
            }
        }
    
    elif request_type == 'Delete':
        # Optionally remove from registry on stack deletion
        # You might want to keep the registration for historical purposes
        try:
            table.update_item(
                Key={
                    'server_id': properties['ServerId'],
                    'version': properties['Version']
                },
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'decommissioned',
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
        except:
            pass  # Ignore errors during deletion
        
        return {
            'PhysicalResourceId': properties['ServerId']
        }
            """)
        )
```

### Option 2: Using a Construct Pattern

Create a reusable construct for MCP server registration:

```python
# constructs/mcp_server_construct.py
from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    CustomResource,
    custom_resources as cr,
    CfnOutput
)
import json

class MCPServerConstruct(Construct):
    """Construct for creating and registering an MCP server"""
    
    def __init__(
        self,
        scope: Construct,
        id: str,
        server_name: str,
        server_function: _lambda.Function,
        tools: list,
        authentication_type: str = "api_key",
        protocol_type: str = "jsonrpc",
        env_name: str = "prod",
        **kwargs
    ) -> None:
        super().__init__(scope, id)
        
        self.server_function = server_function
        self.env_name = env_name
        
        # Create API Gateway for the MCP server
        self.api = self.create_api_gateway()
        
        # Register with MCP Registry
        self.registration = self.register_server(
            server_name=server_name,
            tools=tools,
            authentication_type=authentication_type,
            protocol_type=protocol_type
        )
        
        # Grant necessary permissions
        self.setup_permissions()
        
    def create_api_gateway(self) -> apigw.RestApi:
        """Create API Gateway endpoint for MCP server"""
        api = apigw.RestApi(
            self,
            "MCPServerAPI",
            rest_api_name=f"{self.node.id}-api",
            description="MCP Server API Gateway",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],
                allow_methods=["POST", "OPTIONS"],
                allow_headers=["Content-Type", "X-Api-Key"]
            )
        )
        
        # Add Lambda integration
        integration = apigw.LambdaIntegration(self.server_function)
        
        # Add /mcp endpoint
        mcp_resource = api.root.add_resource("mcp")
        mcp_resource.add_method("POST", integration)
        
        # Add /health endpoint (no auth)
        health_resource = api.root.add_resource("health")
        health_resource.add_method("GET", integration)
        
        return api
    
    def register_server(
        self,
        server_name: str,
        tools: list,
        authentication_type: str,
        protocol_type: str
    ) -> CustomResource:
        """Register the MCP server in the registry"""
        
        # Registration Lambda inline code
        registration_code = """
import boto3
import json
from datetime import datetime

def handler(event, context):
    # Registration logic here (similar to Option 1)
    pass
        """
        
        registration_handler = _lambda.Function(
            self,
            "RegistrationHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_inline(registration_code)
        )
        
        provider = cr.Provider(
            self,
            "RegistrationProvider",
            on_event_handler=registration_handler
        )
        
        return CustomResource(
            self,
            "ServerRegistration",
            service_token=provider.service_token,
            properties={
                "ServerName": server_name,
                "EndpointUrl": self.api.url,
                "Tools": json.dumps(tools),
                "AuthenticationType": authentication_type,
                "ProtocolType": protocol_type
            }
        )
    
    def setup_permissions(self):
        """Setup necessary IAM permissions"""
        # Grant Lambda permission to read from registry
        registry_policy = iam.PolicyStatement(
            actions=["dynamodb:Query", "dynamodb:GetItem"],
            resources=[f"arn:aws:dynamodb:*:*:table/MCPServerRegistry-{self.env_name}"]
        )
        self.server_function.add_to_role_policy(registry_policy)
```

## Registration Methods

### Method 1: CDK Deployment (Automatic)

Your MCP server is automatically registered when you deploy your CDK stack:

```bash
cdk deploy YourMCPServerStack
```

### Method 2: Self-Registration API

For dynamic registration, use the self-registration endpoint:

```python
import requests
import json

def self_register_mcp_server():
    """Self-register MCP server with the registry"""
    
    registration_endpoint = "https://api.your-domain.com/mcp/register"
    registration_token = "your-registration-token"  # From AWS Secrets Manager
    
    payload = {
        "server_name": "My Custom MCP Server",
        "description": "Provides specialized tools for X",
        "endpoint_url": "https://my-server.example.com/mcp",
        "protocol_type": "jsonrpc",
        "authentication_type": "none",  # No auth required
        "available_tools": [
            {
                "name": "custom_tool",
                "description": "Does something custom",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"}
                    },
                    "required": ["input"]
                }
            }
        ],
        "health_check_url": "https://my-server.example.com/health",
        "metadata": {
            "team": "platform-team",
            "cost_center": "12345"
        }
    }
    
    response = requests.post(
        registration_endpoint,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Registration-Token": registration_token
        }
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"Server registered: {result['server_id']}")
        print(f"Status: {result['status']}")
    else:
        print(f"Registration failed: {response.text}")

if __name__ == "__main__":
    self_register_mcp_server()
```

### Method 3: Manual Registration via UI

For development/testing, use the Management Console:

1. Navigate to "MCP Servers" tab
2. Click "Register New Server"
3. Fill in the registration form
4. Submit for approval (if required)

## Implementation Examples

### Example 1: Simple MCP Server with No Authentication

```python
# stacks/simple_mcp_server_stack.py
class SimpleMCPServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda function for MCP server
        mcp_function = _lambda.Function(
            self,
            "SimpleMCPFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=_lambda.Code.from_asset("lambda/simple_mcp"),
            environment={
                "LOG_LEVEL": "INFO"
            }
        )
        
        # Create Function URL (no auth)
        function_url = mcp_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )
        
        # Register with MCP Registry
        self.register_mcp_server(
            server_id="simple-mcp-server",
            server_name="Simple MCP Server",
            endpoint_url=function_url.url,
            protocol_type="jsonrpc",
            authentication_type="none",  # No authentication
            available_tools=[
                {
                    "name": "echo",
                    "description": "Echoes back the input",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        },
                        "required": ["message"]
                    }
                }
            ],
            env_name="prod"
        )
```

### Example 2: GraphQL MCP Server with API Key

```python
# stacks/graphql_mcp_server_stack.py
class GraphQLMCPServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # AppSync GraphQL API
        graphql_api = appsync.GraphqlApi(
            self,
            "MCPGraphQLAPI",
            name="mcp-graphql-api",
            schema=appsync.SchemaFile.from_asset("schema.graphql"),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY
                )
            )
        )
        
        # Register with MCP Registry
        self.register_mcp_server(
            server_id="graphql-mcp-server",
            server_name="GraphQL MCP Server",
            endpoint_url=graphql_api.graphql_url,
            protocol_type="graphql",
            authentication_type="api_key",
            available_tools=[
                {
                    "name": "query_data",
                    "description": "Query data via GraphQL",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "variables": {"type": "object"}
                        },
                        "required": ["query"]
                    }
                }
            ],
            env_name="prod"
        )
```

### Example 3: Multi-Tool MCP Server

```python
# lambda/multi_tool_mcp/handler.py
import json
from typing import Dict, Any

def handle_mcp_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP protocol requests"""
    
    body = json.loads(event.get('body', '{}'))
    method = body.get('method')
    params = body.get('params', {})
    request_id = body.get('id')
    
    if method == 'initialize':
        return {
            'jsonrpc': '2.0',
            'result': {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'multi-tool-mcp-server',
                    'version': '1.0.0'
                }
            },
            'id': request_id
        }
    
    elif method == 'tools/list':
        return {
            'jsonrpc': '2.0',
            'result': {
                'tools': [
                    {
                        'name': 'process_data',
                        'description': 'Process input data',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'data': {'type': 'string'},
                                'format': {'type': 'string'}
                            },
                            'required': ['data']
                        }
                    },
                    {
                        'name': 'generate_report',
                        'description': 'Generate a report',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'report_type': {'type': 'string'},
                                'parameters': {'type': 'object'}
                            },
                            'required': ['report_type']
                        }
                    }
                ]
            },
            'id': request_id
        }
    
    elif method == 'tools/call':
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name == 'process_data':
            result = process_data(arguments)
        elif tool_name == 'generate_report':
            result = generate_report(arguments)
        else:
            return {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32601,
                    'message': f'Tool not found: {tool_name}'
                },
                'id': request_id
            }
        
        return {
            'jsonrpc': '2.0',
            'result': result,
            'id': request_id
        }
    
    return {
        'jsonrpc': '2.0',
        'error': {
            'code': -32601,
            'message': f'Method not found: {method}'
        },
        'id': request_id
    }

def process_data(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Process data tool implementation"""
    data = arguments.get('data', '')
    format_type = arguments.get('format', 'json')
    
    # Your data processing logic here
    return {
        'processed': True,
        'format': format_type,
        'length': len(data)
    }

def generate_report(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Generate report tool implementation"""
    report_type = arguments['report_type']
    parameters = arguments.get('parameters', {})
    
    # Your report generation logic here
    return {
        'report_id': 'rpt-12345',
        'type': report_type,
        'status': 'generated'
    }

def lambda_handler(event, context):
    """Lambda entry point"""
    try:
        response = handle_mcp_request(event)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'jsonrpc': '2.0',
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            })
        }
```

## Testing Your Integration

### 1. Local Testing

Test your MCP server locally before registration:

```python
# test_mcp_server.py
import requests
import json

def test_mcp_server(endpoint_url: str, api_key: str = None):
    """Test MCP server endpoints"""
    
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['x-api-key'] = api_key
    
    # Test initialize
    init_request = {
        'jsonrpc': '2.0',
        'method': 'initialize',
        'params': {},
        'id': 1
    }
    
    response = requests.post(endpoint_url, json=init_request, headers=headers)
    print(f"Initialize: {response.json()}")
    
    # Test tools/list
    list_request = {
        'jsonrpc': '2.0',
        'method': 'tools/list',
        'params': {},
        'id': 2
    }
    
    response = requests.post(endpoint_url, json=list_request, headers=headers)
    tools = response.json().get('result', {}).get('tools', [])
    print(f"Available tools: {[t['name'] for t in tools]}")
    
    # Test tools/call
    for tool in tools:
        call_request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': tool['name'],
                'arguments': {}  # Add test arguments
            },
            'id': 3
        }
        
        response = requests.post(endpoint_url, json=call_request, headers=headers)
        print(f"Tool {tool['name']}: {response.json()}")

if __name__ == "__main__":
    # Test your server
    test_mcp_server("http://localhost:3000/mcp")
```

### 2. Integration Testing

Test registration and discovery:

```python
# test_registration.py
import boto3
from datetime import datetime

def test_registration(server_id: str, env_name: str = "prod"):
    """Test if server is properly registered"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(f'MCPServerRegistry-{env_name}')
    
    # Query for your server
    response = table.get_item(
        Key={
            'server_id': server_id,
            'version': '1.0.0'
        }
    )
    
    if 'Item' in response:
        server = response['Item']
        print(f"✅ Server found: {server['server_name']}")
        print(f"   Status: {server['status']}")
        print(f"   Endpoint: {server['endpoint_url']}")
        print(f"   Tools: {[t['name'] for t in server.get('available_tools', [])]}")
    else:
        print(f"❌ Server not found: {server_id}")

if __name__ == "__main__":
    test_registration("your-mcp-server-prod")
```

### 3. Health Check Testing

Verify your health endpoint:

```bash
# Test health endpoint
curl https://your-server.example.com/health

# Expected response
{"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

## Best Practices

### 1. Tool Design

✅ **DO:**
- Keep tool names descriptive and unique
- Provide comprehensive input schemas
- Include helpful descriptions
- Version your tools appropriately

❌ **DON'T:**
- Use generic tool names like "process" or "execute"
- Skip input validation
- Change tool signatures without versioning

### 2. Error Handling

```python
def handle_error(error: Exception, request_id: Any = None) -> Dict:
    """Proper error handling for MCP requests"""
    
    error_codes = {
        ValueError: -32602,  # Invalid params
        KeyError: -32602,    # Invalid params
        NotImplementedError: -32601,  # Method not found
        Exception: -32603    # Internal error
    }
    
    code = error_codes.get(type(error), -32603)
    
    return {
        'jsonrpc': '2.0',
        'error': {
            'code': code,
            'message': str(error),
            'data': {
                'type': type(error).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
        },
        'id': request_id
    }
```

### 3. Authentication Patterns

#### No Authentication (Public Data)
```python
# Suitable for read-only, public data
authentication_type = "none"
```

#### API Key (Most Common)
```python
# Validate API key in your handler
def validate_api_key(event):
    api_key = event.get('headers', {}).get('x-api-key')
    if not api_key or api_key != EXPECTED_API_KEY:
        raise ValueError("Invalid API key")
```

#### AWS IAM (Internal Services)
```python
# Use IAM role-based authentication
from aws_requests_auth.aws_auth import AWSRequestsAuth

auth = AWSRequestsAuth(
    aws_access_key=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_host='your-api.execute-api.region.amazonaws.com',
    aws_region='us-east-1',
    aws_service='execute-api'
)
```

### 4. Health Check Implementation

```python
def health_check_handler(event, context):
    """Health check endpoint handler"""
    
    checks = {
        'database': check_database_connection(),
        'dependencies': check_external_dependencies(),
        'memory': check_memory_usage()
    }
    
    all_healthy = all(checks.values())
    
    return {
        'statusCode': 200 if all_healthy else 503,
        'body': json.dumps({
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': checks,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
```

### 5. Monitoring and Logging

```python
import logging
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()

@tracer.capture_method
def process_mcp_request(method: str, params: Dict):
    """Process MCP request with monitoring"""
    
    # Log the request
    logger.info(f"Processing {method}", extra={"params": params})
    
    # Add custom metric
    metrics.add_metric(name="MCPRequestCount", unit=MetricUnit.Count, value=1)
    metrics.add_metadata(key="method", value=method)
    
    # Process request
    result = handle_method(method, params)
    
    # Log success
    logger.info(f"Successfully processed {method}")
    
    return result
```

## Troubleshooting

### Common Issues

1. **Registration Failed**
   - Check DynamoDB table exists: `MCPServerRegistry-{env}`
   - Verify IAM permissions for DynamoDB write
   - Ensure unique server_id

2. **Health Check Failing**
   - Verify endpoint URL is accessible
   - Check security groups and network ACLs
   - Ensure health endpoint returns within 5 seconds

3. **Tools Not Appearing**
   - Validate tool schema JSON format
   - Check available_tools array is properly formatted
   - Verify GraphQL schema updates are deployed

### Debug Commands

```bash
# Check if server is registered
aws dynamodb get-item \
  --table-name MCPServerRegistry-prod \
  --key '{"server_id":{"S":"your-server-id"},"version":{"S":"1.0.0"}}'

# List all registered servers
aws dynamodb scan \
  --table-name MCPServerRegistry-prod \
  --filter-expression "#status = :status" \
  --expression-attribute-names '{"#status":"status"}' \
  --expression-attribute-values '{":status":{"S":"active"}}'

# Test MCP endpoint
curl -X POST https://your-server.example.com/mcp \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

## Support

- **Documentation**: [MCP Registry Design](./MCP_REGISTRY_DESIGN.md)
- **Examples**: [/examples/mcp-servers](../examples/mcp-servers)
- **Issues**: [GitHub Issues](https://github.com/your-org/step-functions-agent/issues)
- **Slack**: #mcp-registry-support

## Next Steps

1. Review the [MCP Protocol Specification](https://github.com/anthropics/mcp)
2. Check out [example implementations](../examples/mcp-servers)
3. Deploy your first MCP server
4. Register with the MCP Registry
5. Test integration with AI agents

Happy coding! 🚀