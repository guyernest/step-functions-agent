from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
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
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_graphql_secret(self):
        """Create secret for GraphQL interface"""
        
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
            description=f"GraphQL API secrets and configuration for {self.env_name} environment",
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
        
        # Grant access to GraphQL secrets
        graphql_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[self.graphql_secret.secret_arn]
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
                role=graphql_lambda_role
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
                role=graphql_lambda_role
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
                "tool_name": "execute_graphql_query",
                "description": "Execute GraphQL queries against any endpoint with dynamic schema support",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "GraphQL query to execute"},
                        "variables": {"type": "object", "description": "Query variables (optional)"}
                    },
                    "required": ["query"]
                },
                "language": "python",
                "tags": ["graphql", "api", "query", "execution"],
                "author": "system"
            },
            {
                "tool_name": "generate_query_prompt",
                "description": "Generate a prompt template for creating GraphQL queries based on schema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Description of what you want to query"}
                    },
                    "required": ["description"]
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
        MultiToolConstruct(
            self,
            "GraphQLInterfaceToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": graphql_tools,
                    "lambda_function": self.graphql_interface_lambda
                }
            ],
            env_name=self.env_name
        )