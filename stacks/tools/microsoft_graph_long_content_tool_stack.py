from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Fn,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
)

try:
    from aws_cdk import aws_lambda_python_alpha as _lambda_python
except ImportError:
    _lambda_python = None

from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import os
import json


class MicrosoftGraphLongContentToolStack(Stack):
    """
    Microsoft Graph Tools Stack with Long Content Support
    
    This stack deploys Microsoft Graph API capabilities with long content handling:
    - Email management and automation with large attachments
    - Teams messages and collaboration with extensive threads
    - SharePoint document access for large files
    - User and group management with bulk operations
    - Calendar and scheduling integration with detailed events
    - Enterprise security and compliance reports
    - Long content support via Lambda Runtime API Proxy
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", max_content_size: int = 5000, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.max_content_size = max_content_size
        
        # Import long content infrastructure
        self._import_long_content_infrastructure()
        
        # Create tool-specific secrets
        self._create_microsoft_graph_secret()
        
        # Deploy Python Microsoft Graph tool with long content support
        self._create_microsoft_graph_tool_with_long_content()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()
        
        # Create stack exports
        self._create_stack_exports()
        
        print(f"✅ Created Microsoft Graph tool with long content support")

    def _import_long_content_infrastructure(self):
        """Import shared long content infrastructure resources"""
        
        # Import DynamoDB content table
        self.content_table_name = Fn.import_value(
            NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name)
        )
        
        self.content_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name)
        )
        
        # Import proxy extension layer ARNs
        self.proxy_layer_x86_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerX86", "LongContent", self.env_name)
        )
        
        self.proxy_layer_arm_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerArm", "LongContent", self.env_name)
        )
        
        print(f"📊 Imported long content infrastructure for {self.env_name}")

    def _create_microsoft_graph_secret(self):
        """Create secret for Microsoft Graph API"""
        
        env_file_path = ".env.microsoft"
        secret_value = {
            "TENANT_ID": "REPLACE_WITH_ACTUAL_TENANT_ID",
            "CLIENT_ID": "REPLACE_WITH_ACTUAL_CLIENT_ID",
            "CLIENT_SECRET": "REPLACE_WITH_ACTUAL_CLIENT_SECRET"
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
        
        self.microsoft_graph_secret = secretsmanager.Secret(
            self, 
            "MicrosoftGraphSecretsLongContent",
            secret_name=f"/ai-agent/tools/microsoft-graph-long-content/{self.env_name}",
            description=f"Microsoft Graph API secrets for {self.env_name} environment with long content - UPDATE WITH ACTUAL CREDENTIALS",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_value),
                generate_string_key="placeholder",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/@\""
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_microsoft_graph_tool_with_long_content(self):
        """Create Python Lambda function for Microsoft Graph API with long content support"""
        
        # Import the ARM64 proxy layer
        arm_proxy_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ProxyExtensionLayerARM64",
            layer_version_arn=self.proxy_layer_arm_arn
        )
        
        # Create execution role
        graph_lambda_role = iam.Role(
            self,
            "MicrosoftGraphLongContentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to secrets
        graph_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    self.microsoft_graph_secret.secret_arn,
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/tool-secrets/{self.env_name}*",
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/MicrosoftGraphAPISecrets*"
                ]
            )
        )
        
        # Add permissions for DynamoDB content table
        graph_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.content_table_arn,
                    f"{self.content_table_arn}/index/*"
                ]
            )
        )
        
        # Add X-Ray tracing permissions
        graph_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        # Create Lambda function with long content support
        if _lambda_python is not None:
            self.microsoft_graph_lambda = _lambda_python.PythonFunction(
                self,
                "MicrosoftGraphLongContentLambda",
                function_name=f"tool-microsoft-graph-long-content-{self.env_name}",
                description="Microsoft Graph API integration with long content support for Office 365 enterprise services",
                entry="lambda/tools/MicrosoftGraphAPI",
                index="index.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.minutes(10),  # Increased timeout for large content
                memory_size=1024,  # Increased memory for processing large content
                layers=[arm_proxy_layer],  # Add proxy extension layer
                role=graph_lambda_role,
                tracing=_lambda.Tracing.ACTIVE,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}",
                    # Required for Lambda Runtime API Proxy to work
                    "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
                    # Configuration for content transformation
                    "AGENT_CONTEXT_TABLE": self.content_table_name,
                    "MAX_CONTENT_SIZE": str(self.max_content_size),
                    # Optional: Enable debug logging
                    "LRAP_DEBUG": "false",  # Set to "true" for debugging
                    "POWERTOOLS_SERVICE_NAME": "microsoft-graph-long-content",
                    "POWERTOOLS_LOG_LEVEL": "INFO"
                }
            )
        else:
            self.microsoft_graph_lambda = _lambda.Function(
                self,
                "MicrosoftGraphLongContentLambda",
                function_name=f"tool-microsoft-graph-long-content-{self.env_name}",
                description="Microsoft Graph API integration with long content support for Office 365 enterprise services",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/MicrosoftGraphAPI"),
                handler="index.lambda_handler",
                timeout=Duration.minutes(10),  # Increased timeout for large content
                memory_size=1024,  # Increased memory for processing large content
                layers=[arm_proxy_layer],  # Add proxy extension layer
                role=graph_lambda_role,
                tracing=_lambda.Tracing.ACTIVE,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}",
                    # Required for Lambda Runtime API Proxy to work
                    "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
                    # Configuration for content transformation
                    "AGENT_CONTEXT_TABLE": self.content_table_name,
                    "MAX_CONTENT_SIZE": str(self.max_content_size),
                    # Optional: Enable debug logging
                    "LRAP_DEBUG": "false",  # Set to "true" for debugging
                    "POWERTOOLS_SERVICE_NAME": "microsoft-graph-long-content",
                    "POWERTOOLS_LOG_LEVEL": "INFO"
                }
            )
        
        self.microsoft_graph_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        print(f"🔧 Created Microsoft Graph Lambda with long content support")

    def _register_tools_using_base_construct(self):
        """Register tools in DynamoDB using the base tool construct"""
        from .base_tool_construct_batched import BatchedToolConstruct
        
        # Define tool specifications
        tool_specs = [{
            "tool_name": "MicrosoftGraphAPI",
            "description": "Access Microsoft Graph API including emails, Teams messages, SharePoint, and user management",
            "input_schema": {
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "Microsoft Graph API endpoint (e.g., 'users', 'me/messages', 'sites')"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                        "description": "HTTP method for the API call",
                        "default": "GET"
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body data for POST/PUT/PATCH operations"
                    }
                },
                "required": ["endpoint"]
            },
            "language": "python",
            "tags": ["microsoft", "graph", "email", "teams", "sharepoint", "enterprise"],
            "human_approval_required": True,
            "lambda_arn": self.microsoft_graph_lambda.function_arn,
            "lambda_function_name": self.microsoft_graph_lambda.function_name
        }]
        
        # Use BatchedToolConstruct for registration
        BatchedToolConstruct(
            self,
            "MicrosoftGraphLongContentToolRegistry",
            tool_specs=tool_specs,
            lambda_function=self.microsoft_graph_lambda,
            env_name=self.env_name
        )
        
        print(f"📝 Registered Microsoft Graph tool with long content")

    def _create_stack_exports(self):
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self,
            "MicrosoftGraphLongContentLambdaArn",
            value=self.microsoft_graph_lambda.function_arn,
            export_name=f"MicrosoftGraphLongContentLambdaArn-{self.env_name}",
            description="ARN of the Microsoft Graph Lambda with long content support"
        )
        
        CfnOutput(
            self,
            "MicrosoftGraphLongContentLambdaName",
            value=self.microsoft_graph_lambda.function_name,
            export_name=f"MicrosoftGraphLongContentLambdaName-{self.env_name}",
            description="Name of the Microsoft Graph Lambda with long content support"
        )