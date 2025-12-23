from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Fn,
    CustomResource,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    custom_resources as cr,
    CfnOutput,
    SecretValue
)

try:
    from aws_cdk import aws_lambda_python_alpha as _lambda_python
except ImportError:
    _lambda_python = None

from constructs import Construct
from .base_tool_construct import MultiToolConstruct
import os
import json
from pathlib import Path


class GraphQLInterfaceToolStack(Stack):
    """
    GraphQL Interface Tools Stack - Dynamic GraphQL query execution and schema analysis
    
    This stack deploys GraphQL integration capabilities:
    - Dynamic GraphQL query execution against any endpoint
    - AWS AppSync integration with automatic schema discovery
    - Query generation assistance with AI-powered prompts
    - Variable binding and parameterized queries
    - Schema introspection and documentation
    - Error handling and query optimization
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create tool-specific secrets
        self._create_graphql_secret()
        
        # Deploy Python GraphQL interface tool
        self._create_graphql_interface_tool()

        # Configure GraphQL endpoints in consolidated secrets
        self._configure_graphql_endpoints_in_secrets()

        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_graphql_secret(self):
        """Create secret for GraphQL interface - for backward compatibility only"""

        # This is kept for backward compatibility
        # The actual GraphQL endpoints are configured in the consolidated tool secrets
        # managed by shared_infrastructure_stack

        env_file_path = ".env.graphql"
        secret_value = {
            "GRAPHQL_ENDPOINT": "https://your-appsync-endpoint.amazonaws.com/graphql",
            "API_KEY": "REPLACE_WITH_ACTUAL_API_KEY",
            "REGION": "us-east-1"
        }

        if os.path.exists(env_file_path):
            try:
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            secret_value[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not read {env_file_path}: {e}")

        self.graphql_secret = secretsmanager.Secret(
            self,
            "GraphQLSecrets",
            secret_name=f"/ai-agent/tools/graphql-interface/{self.env_name}",
            description=f"[DEPRECATED] GraphQL API secrets - use consolidated secrets instead",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_value),
                generate_string_key="placeholder",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/@\""
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_graphql_interface_tool(self):
        """Create Python Lambda function for GraphQL interface"""

        # Create execution role for GraphQL Lambda
        graphql_lambda_role = iam.Role(
            self,
            "GraphQLInterfaceLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Grant access to GraphQL secrets (both legacy and consolidated)
        graphql_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    self.graphql_secret.secret_arn,
                    f"arn:aws:secretsmanager:*:*:secret:/ai-agent/tool-secrets/{self.env_name}*"
                ]
            )
        )
        
        # Grant permissions for AppSync operations
        graphql_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "appsync:GraphQL",
                    "appsync:GetGraphqlApi",
                    "appsync:GetIntrospectionSchema"
                ],
                resources=["*"]
            )
        )
        
        # Create Python Lambda function for GraphQL interface
        if _lambda_python is not None:
            self.graphql_interface_lambda = _lambda_python.PythonFunction(
                self,
                "GraphQLInterfaceLambda",
                function_name=f"tool-graphql-interface-{self.env_name}",
                description="Dynamic GraphQL query execution and schema analysis with AppSync integration",
                entry="lambda/tools/graphql-interface",
                index="index.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.seconds(120),
                memory_size=512,
                role=graphql_lambda_role,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}"
                }
            )
        else:
            self.graphql_interface_lambda = _lambda.Function(
                self,
                "GraphQLInterfaceLambda",
                function_name=f"tool-graphql-interface-{self.env_name}",
                description="Dynamic GraphQL query execution and schema analysis with AppSync integration",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/graphql-interface"),
                handler="index.lambda_handler",
                timeout=Duration.seconds(120),
                memory_size=512,
                role=graphql_lambda_role,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}"
                }
            )
        
        self.graphql_interface_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "GraphQLInterfaceLambdaArn",
            value=self.graphql_interface_lambda.function_arn,
            export_name=f"GraphQLInterfaceLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self,
            "GraphQLSecretArn",
            value=self.graphql_secret.secret_arn,
            description="ARN of GraphQL API secret - update with actual endpoint and credentials"
        )

    def _configure_graphql_endpoints_in_secrets(self):
        """Configure GraphQL endpoints in the consolidated tool secrets."""

        # Default GraphQL endpoint configurations
        graphql_endpoints = {
            "LogisticZ": {
                "endpoint": os.environ.get("GRAPHQL_LOGISTICZ_ENDPOINT", "https://logisticz-api.example.com/graphql"),
                "api_key": os.environ.get("GRAPHQL_LOGISTICZ_API_KEY", "PLACEHOLDER_LOGISTICZ_API_KEY")
            },
            "CustomerService": {
                "endpoint": os.environ.get("GRAPHQL_CUSTOMER_ENDPOINT", "https://customer-api.example.com/graphql"),
                "api_key": os.environ.get("GRAPHQL_CUSTOMER_API_KEY", "PLACEHOLDER_CUSTOMER_API_KEY")
            }
        }

        # Check for .env.graphql-endpoints file for local configuration
        endpoints_file = ".env.graphql-endpoints"
        if os.path.exists(endpoints_file):
            try:
                with open(endpoints_file, 'r') as f:
                    custom_endpoints = json.load(f)
                    graphql_endpoints.update(custom_endpoints)
                    print(f"✅ Loaded custom GraphQL endpoints from {endpoints_file}")
            except Exception as e:
                print(f"⚠️  Could not load {endpoints_file}: {e}")

        # Convert endpoints to JSON strings as required by the Lambda
        formatted_endpoints = {}
        for endpoint_id, config in graphql_endpoints.items():
            formatted_endpoints[endpoint_id] = json.dumps(config)

        # Import the consolidated secret ARN
        try:
            consolidated_secret_arn = Fn.import_value(
                f"ConsolidatedToolSecretsArn-{self.env_name}"
            )
        except:
            print(f"⚠️  Consolidated secrets not available - skipping endpoint configuration")
            return

        # Create a Custom Resource to update the consolidated secret with GraphQL endpoints
        # We use a Lambda-backed Custom Resource to merge our endpoints into the existing secret
        update_secret_lambda = _lambda.Function(
            self,
            "UpdateGraphQLSecretsLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import cfnresponse

secretsmanager = boto3.client('secretsmanager')

def handler(event, context):
    try:
        request_type = event['RequestType']
        secret_arn = event['ResourceProperties']['SecretArn']
        tool_name = event['ResourceProperties']['ToolName']
        endpoints = json.loads(event['ResourceProperties']['Endpoints'])

        if request_type in ['Create', 'Update']:
            # Get current secret
            response = secretsmanager.get_secret_value(SecretId=secret_arn)
            current_secrets = json.loads(response['SecretString'])

            # Update with GraphQL endpoints
            current_secrets[tool_name] = endpoints

            # Save back
            secretsmanager.update_secret(
                SecretId=secret_arn,
                SecretString=json.dumps(current_secrets)
            )

            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Status': 'Updated'})
        elif request_type == 'Delete':
            # Optionally remove the tool from secrets on delete
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Status': 'Deleted'})
    except Exception as e:
        print(f"Error: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})
"""),
            timeout=Duration.seconds(60),
            memory_size=128
        )

        # Grant permission to update the secret
        update_secret_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:UpdateSecret"
                ],
                resources=[consolidated_secret_arn]
            )
        )

        # Create the Custom Resource
        CustomResource(
            self,
            "GraphQLEndpointsConfiguration",
            service_token=update_secret_lambda.function_arn,
            properties={
                "SecretArn": consolidated_secret_arn,
                "ToolName": "graphql-interface",
                "Endpoints": json.dumps(formatted_endpoints)
            }
        )

        print(f"✅ GraphQL endpoints will be configured in consolidated secrets")

    def _register_tools_using_base_construct(self):
        """Register all GraphQL interface tools using the BaseToolConstruct pattern"""
        
        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'graphql-interface' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ GraphQLInterfaceToolStack: Loaded {len(tool_names)} tool names from tool-names.json: {tool_names}")
        
        # Define GraphQL interface tool specifications with self-contained definitions
        graphql_tools = [
            {
                "tool_name": "get_graphql_schema",
                "description": "Fetch the GraphQL schema for a specific endpoint to understand available queries, mutations, and types",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "graphql_id": {"type": "string", "description": "Identifier for the GraphQL endpoint (e.g., 'LogisticZ', 'CustomerService')"}
                    },
                    "required": ["graphql_id"]
                },
                "language": "python",
                "tags": ["graphql", "schema", "introspection", "api"],
                "author": "system"
            },
            {
                "tool_name": "execute_graphql_query",
                "description": "Execute GraphQL queries against a specific endpoint with dynamic schema support",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "graphql_id": {"type": "string", "description": "Identifier for the GraphQL endpoint (e.g., 'LogisticZ', 'CustomerService')"},
                        "graphql_query": {"type": "string", "description": "GraphQL query to execute"},
                        "variables": {"type": "object", "description": "Query variables (optional)"}
                    },
                    "required": ["graphql_id", "graphql_query"]
                },
                "language": "python",
                "tags": ["graphql", "api", "query", "execution"],
                "author": "system"
            },
            {
                "tool_name": "generate_query_prompt",
                "description": "Generate a prompt template for creating GraphQL queries based on a specific endpoint's schema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "graphql_id": {"type": "string", "description": "Identifier for the GraphQL endpoint (e.g., 'LogisticZ', 'CustomerService')"},
                        "description": {"type": "string", "description": "Description of what you want to query"}
                    },
                    "required": ["graphql_id", "description"]
                },
                "language": "python",
                "tags": ["graphql", "prompt", "schema", "generation"],
                "author": "system"
            }
        ]
        
        # Validate that all tool specs match declared names
        spec_names = {spec["tool_name"] for spec in graphql_tools}
        declared_names = set(tool_names)
        
        if spec_names != declared_names:
            raise ValueError(f"Tool name mismatch! Specs: {spec_names}, Declared: {declared_names}")
        
        # Use MultiToolConstruct to register GraphQL interface tools
        # The secret_requirements registers "graphql-interface" in the ToolSecrets registry
        # with empty keys (dynamic discovery) since endpoints are nested objects
        MultiToolConstruct(
            self,
            "GraphQLInterfaceToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": graphql_tools,
                    "lambda_function": self.graphql_interface_lambda
                }
            ],
            env_name=self.env_name,
            secret_requirements={
                "graphql-interface": []  # Empty list = dynamic endpoint discovery
            }
        )