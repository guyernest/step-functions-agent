"""
MCP Registry Stack - DynamoDB table for MCP Server Registry
Similar to AgentRegistryStack but for MCP servers
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_iam as iam,
    custom_resources as cr,
    CustomResource,
    Duration
)
from constructs import Construct
import json
from datetime import datetime


class MCPRegistryStack(Stack):
    """
    Stack for MCP Server Registry
    Creates DynamoDB table and seeds initial MCP server entries
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", mcp_endpoint_url: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.mcp_endpoint_url = mcp_endpoint_url or "https://api.example.com/mcp"
        
        # Create DynamoDB table for MCP Server Registry
        self.mcp_registry_table = dynamodb.Table(
            self,
            "MCPServerRegistryTable",
            table_name=f"MCPServerRegistry-{env_name}",
            partition_key=dynamodb.Attribute(
                name="server_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  # For future event-driven updates
        )
        
        # Add Global Secondary Index for querying by status
        self.mcp_registry_table.add_global_secondary_index(
            index_name="MCPServersByStatus",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by protocol type
        self.mcp_registry_table.add_global_secondary_index(
            index_name="MCPServersByProtocol",
            partition_key=dynamodb.Attribute(
                name="protocol_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="server_name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by deployment stack (for CDK tracking)
        self.mcp_registry_table.add_global_secondary_index(
            index_name="MCPServersByStack",
            partition_key=dynamodb.Attribute(
                name="deployment_stack",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Note: Amplify build role permissions should be granted using:
        #   make grant-amplify-mcp-permissions
        # This is because the Amplify role is managed outside of CDK
        
        # Create Lambda for seeding initial data
        seed_lambda = _lambda.Function(
            self,
            "MCPRegistrySeedFunction",
            function_name=f"mcp-registry-seed-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            timeout=Duration.seconds(60),
            code=_lambda.Code.from_inline(self.get_seed_lambda_code()),
            environment={
                "TABLE_NAME": self.mcp_registry_table.table_name,
                "ENVIRONMENT": env_name
            }
        )
        
        # Grant permissions to seed lambda
        self.mcp_registry_table.grant_write_data(seed_lambda)
        
        # Create custom resource provider
        provider = cr.Provider(
            self,
            "MCPRegistrySeedProvider",
            on_event_handler=seed_lambda
        )
        
        # Create custom resource to seed data
        CustomResource(
            self,
            "MCPRegistrySeedResource",
            service_token=provider.service_token,
            properties={
                "TableName": self.mcp_registry_table.table_name,
                "Environment": env_name,
                "MCPEndpoint": self.mcp_endpoint_url,
                "Timestamp": datetime.now().isoformat()  # Force update on each deployment
            }
        )
        
        # Outputs
        CfnOutput(
            self,
            "MCPRegistryTableName",
            value=self.mcp_registry_table.table_name,
            export_name=f"MCPRegistryTableName-{env_name}",
            description="Name of the MCP Server Registry DynamoDB table"
        )
        
        CfnOutput(
            self,
            "MCPRegistryTableArn",
            value=self.mcp_registry_table.table_arn,
            export_name=f"MCPRegistryTableArn-{env_name}",
            description="ARN of the MCP Server Registry DynamoDB table"
        )
    
    def get_seed_lambda_code(self) -> str:
        """Return the Lambda function code for seeding initial MCP servers"""
        return '''
import boto3
import json
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """Seed initial MCP server entries"""
    
    request_type = event.get('RequestType', 'Create')
    properties = event.get('ResourceProperties', {})
    
    if request_type in ['Create', 'Update']:
        table_name = properties['TableName']
        environment = properties['Environment']
        mcp_endpoint = properties['MCPEndpoint']
        
        table = dynamodb.Table(table_name)
        
        # Initial MCP server entry - Step Functions Agent Management MCP
        initial_servers = [
            {
                'server_id': f'step-functions-agent-mcp-{environment}',
                'version': '1.0.0',
                'server_name': 'Step Functions Agent MCP Server',
                'description': 'MCP server for managing Step Functions agents, providing tools for agent execution and monitoring',
                'endpoint_url': mcp_endpoint,
                'protocol_type': 'jsonrpc',
                'authentication_type': 'api_key',
                'api_key_header': 'x-api-key',
                'available_tools': [
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
                ],
                'status': 'active',
                'health_check_url': mcp_endpoint.replace('/mcp', '/health'),
                'health_check_interval': 300,
                'configuration': json.dumps({
                    'timeout_seconds': 30,
                    'max_retries': 3,
                    'supports_batch': False
                }),
                'metadata': json.dumps({
                    'managed_by': 'cdk',
                    'team': 'platform',
                    'cost_center': 'engineering',
                    'tags': ['production', 'critical', 'agent-management']
                }),
                'deployment_stack': f'step-functions-agents-{environment}',
                'deployment_region': os.environ.get('AWS_REGION', 'us-east-1'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'created_by': 'system'
            }
        ]
        
        # Add example/demo MCP server for development
        if environment == 'dev':
            initial_servers.append({
                'server_id': 'example-echo-mcp-dev',
                'version': '1.0.0',
                'server_name': 'Example Echo MCP Server',
                'description': 'Simple echo server for testing MCP protocol implementation',
                'endpoint_url': 'https://echo.example.com/mcp',
                'protocol_type': 'jsonrpc',
                'authentication_type': 'none',
                'available_tools': [
                    {
                        'name': 'echo',
                        'description': 'Echoes back the input message',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'message': {
                                    'type': 'string',
                                    'description': 'Message to echo back'
                                }
                            },
                            'required': ['message']
                        }
                    }
                ],
                'status': 'inactive',
                'configuration': json.dumps({}),
                'metadata': json.dumps({
                    'purpose': 'testing',
                    'tags': ['example', 'development']
                }),
                'deployment_stack': 'manual',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'created_by': 'system'
            })
        
        # Write items to DynamoDB
        for server in initial_servers:
            try:
                # Check if server already exists
                existing = table.get_item(
                    Key={
                        'server_id': server['server_id'],
                        'version': server['version']
                    }
                )
                
                if 'Item' not in existing:
                    # Create new entry
                    table.put_item(Item=server)
                    print(f"Created MCP server: {server['server_id']}")
                else:
                    # Update existing entry (preserve created_at)
                    server['created_at'] = existing['Item'].get('created_at', server['created_at'])
                    table.put_item(Item=server)
                    print(f"Updated MCP server: {server['server_id']}")
                    
            except Exception as e:
                print(f"Error seeding server {server['server_id']}: {str(e)}")
        
        return {
            'PhysicalResourceId': f"mcp-registry-seed-{environment}",
            'Data': {
                'Message': f'Seeded {len(initial_servers)} MCP servers'
            }
        }
    
    elif request_type == 'Delete':
        # Optionally clean up on stack deletion
        # For now, we'll keep the data
        return {
            'PhysicalResourceId': f"mcp-registry-seed-{properties.get('Environment', 'unknown')}"
        }
    
    return {
        'PhysicalResourceId': 'mcp-registry-seed'
    }
'''