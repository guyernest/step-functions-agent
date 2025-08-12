from aws_cdk import (
    Duration,
    Stack,
    Fn,
    CfnOutput,
    RemovalPolicy,
    SecretValue,
    CustomResource,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_nodejs as _lambda_nodejs,
    custom_resources as cr,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
from ..shared.tool_definitions import GoogleMapsTools
from .base_tool_construct import BaseToolConstruct
import os
import json
from pathlib import Path
from dotenv import load_dotenv


class GoogleMapsToolStack(Stack):
    """
    Google Maps Tool Stack - Deploys the Google Maps Lambda and registers all 7 tools
    
    This stack demonstrates TypeScript tool integration:
    - Deploys TypeScript Lambda with multiple tool endpoints
    - Creates tool-specific secrets from .env.google-maps
    - Registers 7 Google Maps tools in DynamoDB registry using BaseToolConstruct
    - Shows how one Lambda can provide multiple tools
    
    Now refactored to use BaseToolConstruct for consistency with other tool stacks.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared infrastructure
        self._import_shared_resources()
        
        # Create tool-specific secrets
        self._create_google_maps_secrets()
        
        # Create tool Lambda
        self._create_google_maps_lambda()
        
        # Register tools in DynamoDB registry using BaseToolConstruct
        self._register_tools_using_base_construct()
        
        # Create stack exports
        self._create_stack_exports()

    def _import_shared_resources(self):
        """Import shared DynamoDB tool registry resources"""
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )

    def _create_google_maps_secrets(self):
        """Create or update Google Maps API key secret from .env file"""
        
        # Define env file path - check both possible locations
        # First try the root level with underscore (as user mentioned)
        env_file = Path(__file__).parent.parent.parent / '.env.google_maps'
        # If not found, try the lambda directory with hyphen
        if not env_file.exists():
            env_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'google-maps' / '.env.google-maps'
        
        # Load environment variables from .env file if it exists
        if env_file.exists():
            # Clear any existing GOOGLE_MAPS_API_KEY from environment
            if 'GOOGLE_MAPS_API_KEY' in os.environ:
                del os.environ['GOOGLE_MAPS_API_KEY']
            # Load from .env file with override
            load_dotenv(env_file, override=True)
            google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            
            if google_maps_api_key:
                print(f"✅ Google Maps API key loaded for {self.env_name} environment")
                # Create secret with actual API key
                self.google_maps_secret = secretsmanager.Secret(
                    self,
                    "GoogleMapsApiKey",
                    secret_name=NamingConventions.tool_secret_path("google-maps", self.env_name),
                    description="Google Maps API key for geocoding, places, and directions services",
                    secret_string_value=SecretValue.unsafe_plain_text(
                        json.dumps({"GOOGLE_MAPS_API_KEY": google_maps_api_key})
                    )
                )
            else:
                # Create placeholder secret
                self.google_maps_secret = secretsmanager.Secret(
                    self,
                    "GoogleMapsApiKey",
                    secret_name=NamingConventions.tool_secret_path("google-maps", self.env_name),
                    description="Google Maps API key for geocoding, places, and directions services - UPDATE THIS VALUE",
                    generate_secret_string=secretsmanager.SecretStringGenerator(
                        secret_string_template='{"api_key": "PLACEHOLDER_GOOGLE_MAPS_API_KEY"}',
                        generate_string_key="api_key"
                    )
                )
        else:
            # Create placeholder secret if no .env file
            self.google_maps_secret = secretsmanager.Secret(
                self,
                "GoogleMapsApiKey",
                secret_name=NamingConventions.tool_secret_path("google-maps", self.env_name),
                description="Google Maps API key - UPDATE THIS VALUE in Secrets Manager",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template='{"GOOGLE_MAPS_API_KEY": "PLACEHOLDER_GOOGLE_MAPS_API_KEY"}',
                    generate_string_key="GOOGLE_MAPS_API_KEY"
                )
            )
        
        # Apply removal policy
        self.google_maps_secret.apply_removal_policy(RemovalPolicy.DESTROY)

    def _create_google_maps_lambda(self):
        """Create the Google Maps Lambda function for TypeScript tools"""
        
        # Create Lambda execution role
        lambda_role = iam.Role(
            self,
            "GoogleMapsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant access to both legacy and consolidated secrets
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.google_maps_secret.secret_arn,  # Legacy secret
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/tool-secrets/{self.env_name}*"  # Consolidated secret
                ]
            )
        )
        
        # Grant X-Ray permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        # Create the Lambda function using NodejsFunction for TypeScript
        self.google_maps_lambda = _lambda_nodejs.NodejsFunction(
            self,
            "GoogleMapsLambda",
            function_name=f"tool-google-maps-{self.env_name}",
            description="Google Maps tools - provides geocoding, places search, directions, and more",
            entry="lambda/tools/google-maps/src/index.ts",
            handler="handler",
            runtime=_lambda.Runtime.NODEJS_18_X,
            timeout=Duration.seconds(30),
            memory_size=256,
            architecture=_lambda.Architecture.ARM_64,
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "ENVIRONMENT": self.env_name,
                "GOOGLE_MAPS_SECRET_NAME": self.google_maps_secret.secret_name,  # For backward compatibility
                "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}",
                "LOG_LEVEL": "INFO"
            },
            bundling={
                "minify": True,
                "source_map": True,
                "external_modules": [
                    "aws-sdk",  # Available in Lambda runtime
                ]
            }
        )
        
        # Apply removal policy to help with stack destruction
        self.google_maps_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

    def _register_tools_using_base_construct(self):
        """Register all Google Maps tools using BaseToolConstruct with centralized definitions"""
        
        # Get tool specifications from centralized definitions
        tool_definitions = GoogleMapsTools.get_all_tools()
        tool_specs = [
            tool_def.to_registry_item(
                lambda_arn=self.google_maps_lambda.function_arn,
                lambda_function_name=self.google_maps_lambda.function_name
            )
            for tool_def in tool_definitions
        ]
        
        # Use BaseToolConstruct for registration with secret requirements
        BaseToolConstruct(
            self,
            "GoogleMapsTools",
            tool_specs=tool_specs,
            lambda_function=self.google_maps_lambda,
            env_name=self.env_name,
            secret_requirements={
                "google-maps": ["GOOGLE_MAPS_API_KEY"]
            }
        )

    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export Google Maps Lambda ARN
        CfnOutput(
            self,
            "GoogleMapsLambdaArn",
            value=self.google_maps_lambda.function_arn,
            export_name=f"GoogleMapsLambdaArn-{self.env_name}",
            description="ARN of the Google Maps Lambda function"
        )
        
        # Export Google Maps secret ARN (still needed for other tools that might reference it)
        CfnOutput(
            self, 
            "GoogleMapsSecretArn",
            value=self.google_maps_secret.secret_arn,
            export_name=f"GoogleMapsSecretArn-{self.env_name}",
            description="ARN of the Google Maps secrets"
        )