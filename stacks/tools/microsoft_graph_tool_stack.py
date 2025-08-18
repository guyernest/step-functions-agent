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
from ..shared.tool_definitions import ToolDefinition, ToolLanguage
import os
import json


class MicrosoftGraphToolStack(Stack):
    """
    Microsoft Graph Tools Stack - Office 365 enterprise integration
    
    This stack deploys Microsoft Graph API capabilities:
    - Email management and automation
    - Teams messages and collaboration
    - SharePoint document access
    - User and group management
    - Calendar and scheduling integration
    - Enterprise security and compliance
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create tool-specific secrets
        self._create_microsoft_graph_secret()
        
        # Deploy Python Microsoft Graph tool
        self._create_microsoft_graph_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

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
            "MicrosoftGraphSecrets",
            secret_name=f"/ai-agent/tools/microsoft-graph/{self.env_name}",
            description=f"Microsoft Graph API secrets for {self.env_name} environment - UPDATE WITH ACTUAL CREDENTIALS",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_value),
                generate_string_key="placeholder",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/@\""
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_microsoft_graph_tool(self):
        """Create Python Lambda function for Microsoft Graph API"""
        
        # Create execution role
        graph_lambda_role = iam.Role(
            self,
            "MicrosoftGraphLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to both legacy and consolidated secrets
        graph_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    self.microsoft_graph_secret.secret_arn,  # Legacy secret
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/tool-secrets/{self.env_name}*",  # Consolidated secret
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/MicrosoftGraphAPISecrets*"  # Another legacy path
                ]
            )
        )
        
        # Create Lambda function
        if _lambda_python is not None:
            self.microsoft_graph_lambda = _lambda_python.PythonFunction(
                self,
                "MicrosoftGraphLambda",
                function_name=f"tool-microsoft-graph-{self.env_name}",
                description="Microsoft Graph API integration for comprehensive Office 365 enterprise services",
                entry="lambda/tools/MicrosoftGraphAPI",
                index="index.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.minutes(5),
                memory_size=512,
                role=graph_lambda_role,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}"
                }
            )
        else:
            self.microsoft_graph_lambda = _lambda.Function(
                self,
                "MicrosoftGraphLambda",
                function_name=f"tool-microsoft-graph-{self.env_name}",
                description="Microsoft Graph API integration for comprehensive Office 365 enterprise services",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/MicrosoftGraphAPI"),
                handler="index.lambda_handler",
                timeout=Duration.minutes(5),
                memory_size=512,
                role=graph_lambda_role,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}"
                }
            )
        
        self.microsoft_graph_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "MicrosoftGraphLambdaArn",
            value=self.microsoft_graph_lambda.function_arn,
            export_name=f"MicrosoftGraphLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self,
            "MicrosoftGraphSecretArn",
            value=self.microsoft_graph_secret.secret_arn,
            description="ARN of Microsoft Graph API secret - update with actual credentials"
        )

    def _register_tools_using_base_construct(self):
        """Register all Microsoft Graph tools using the BaseToolConstruct pattern"""
        
        # Define tool locally instead of importing from shared definitions
        graph_tool = ToolDefinition(
            tool_name="MicrosoftGraphAPI",
            description="Access Microsoft Graph API including emails, Teams messages, SharePoint, and user management",
            input_schema={
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
            language=ToolLanguage.PYTHON,
            lambda_handler="lambda_handler",
            tags=["microsoft", "graph", "email", "teams", "sharepoint", "enterprise"],
            human_approval_required=True
        )
        
        # Define Microsoft Graph tool specifications
        microsoft_tools = [
            {
                "tool_name": graph_tool.tool_name,
                "description": graph_tool.description,
                "input_schema": graph_tool.input_schema,
                "language": graph_tool.language.value,
                "tags": graph_tool.tags,
                "author": graph_tool.author,
                "human_approval_required": graph_tool.human_approval_required
            }
        ]
        
        # Use BaseToolConstruct directly to register Microsoft Graph tools with secret requirements
        from .base_tool_construct import BaseToolConstruct
        
        BaseToolConstruct(
            self,
            "MicrosoftGraphToolsRegistry",
            tool_specs=microsoft_tools,
            lambda_function=self.microsoft_graph_lambda,
            env_name=self.env_name,
            secret_requirements={
                "microsoft-graph": ["TENANT_ID", "CLIENT_ID", "CLIENT_SECRET"]
            }
        )