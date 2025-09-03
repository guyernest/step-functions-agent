from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    SecretValue,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
)

try:
    from aws_cdk import aws_lambda_go_alpha as lambda_go
except ImportError:
    lambda_go = None

from constructs import Construct
from .base_tool_construct import BaseToolConstruct
from .base_tool_construct_batched import BatchedToolConstruct
from ..shared.naming_conventions import NamingConventions
import os
import json
from pathlib import Path
from dotenv import load_dotenv


class WebResearchToolStack(Stack):
    """
    Web Research Tool Stack - Provides AI-powered company research capabilities
    
    This stack creates:
    - Go Lambda function for Perplexity API integration
    - IAM roles with appropriate secrets access
    - Tool registration in the Tool Registry
    - Support for comprehensive company research using AI
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Don't import shared resources here - BaseToolConstruct will do it
        # self._import_shared_resources()
        
        # Create tool-specific secrets
        self._create_web_research_secret()
        
        # Create Go research tool Lambda
        self._create_go_research_lambda()
        
        # Register tools in DynamoDB registry using BaseToolConstruct
        self._register_tools_using_base_construct()

    def _create_web_research_secret(self):
        """Create secret for web research tool (Perplexity API)"""
        
        # Try to load from .env.web-research file
        env_file_path = Path(__file__).parent.parent.parent / ".env.web-research"
        secret_value = {"PPLX_API_KEY": "REPLACE_WITH_ACTUAL_API_KEY"}
        
        if env_file_path.exists():
            try:
                load_dotenv(env_file_path)
                pplx_key = os.getenv("PPLX_API_KEY")
                if pplx_key and pplx_key != "your_perplexity_api_key_here":
                    secret_value["PPLX_API_KEY"] = pplx_key
            except Exception as e:
                print(f"Warning: Could not read {env_file_path}: {e}")
        
        # Check if we have actual API key (not placeholder)
        if secret_value.get("PPLX_API_KEY") and secret_value["PPLX_API_KEY"] != "REPLACE_WITH_ACTUAL_API_KEY":
            # Create secret with actual value
            self.web_research_secret = secretsmanager.Secret(
                self, 
                "WebResearchSecrets",
                secret_name=NamingConventions.tool_secret_path("web-research", self.env_name),
                description="Web research tool secrets (Perplexity API)",
                secret_string_value=SecretValue.unsafe_plain_text(
                    json.dumps(secret_value)
                ),
                removal_policy=RemovalPolicy.DESTROY
            )
        else:
            # Create placeholder secret
            self.web_research_secret = secretsmanager.Secret(
                self, 
                "WebResearchSecrets",
                secret_name=NamingConventions.tool_secret_path("web-research", self.env_name),
                description="Web research tool secrets - UPDATE WITH ACTUAL PERPLEXITY API KEY",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template=json.dumps(secret_value),
                    generate_string_key="PPLX_API_KEY"
                ),
                removal_policy=RemovalPolicy.DESTROY
            )

    def _create_go_research_lambda(self):
        """Create Go Lambda function for web research"""
        
        # Create execution role for Go Lambda
        go_lambda_role = iam.Role(
            self,
            "GoResearchLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to both individual and consolidated secrets
        go_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    self.web_research_secret.secret_arn,
                    f"arn:aws:secretsmanager:*:*:secret:/ai-agent/tool-secrets/{self.env_name}*"
                ]
            )
        )
        
        # Grant X-Ray permissions
        go_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        # Create Go Lambda function
        if lambda_go is not None:
            self.go_research_lambda = lambda_go.GoFunction(
                self,
                "WebResearchLambda",
                function_name=f"web-research-{self.env_name}",
                description="Web research tool using Go and Perplexity API",
                entry="lambda/tools/web-research/",
                runtime=_lambda.Runtime.PROVIDED_AL2023,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.seconds(120),
                role=go_lambda_role,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "WEB_RESEARCH_SECRET_NAME": self.web_research_secret.secret_name,
                    "LOG_LEVEL": "DEBUG"  # Set to DEBUG for detailed logging
                }
            )
        else:
            # Fallback to regular Lambda with Go runtime
            self.go_research_lambda = _lambda.Function(
                self,
                "WebResearchLambda",
                function_name=f"web-research-{self.env_name}",
                description="Web research tool using Go and Perplexity API",
                runtime=_lambda.Runtime.PROVIDED_AL2023,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/web-research/"),
                handler="main",
                timeout=Duration.seconds(120),
                role=go_lambda_role,
                environment={
                    "ENVIRONMENT": self.env_name,
                    "WEB_RESEARCH_SECRET_NAME": self.web_research_secret.secret_name,
                    "LOG_LEVEL": "DEBUG"  # Set to DEBUG for detailed logging
                }
            )
        
        # Apply removal policy
        self.go_research_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

    def _register_tools_using_base_construct(self):
        """Register web research tools using BaseToolConstruct with self-contained definitions"""
        
        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'web-research' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ WebResearchToolStack: Loaded {len(tool_names)} tool names from tool-names.json: {tool_names}")
        
        # Define tool specifications with self-contained definitions
        tool_specs = [
            {
                "tool_name": "research_company",  # Now using the correct name from Lambda
                "description": "Research companies and topics using AI-powered web search with Perplexity API",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name to research"},
                        "topics": {"type": "array", "items": {"type": "string"}, "description": "Optional specific topics to research"}
                    },
                    "required": ["company"]
                },
                "language": "go",
                "tags": ["research", "perplexity", "web", "ai"],
                "author": "system",
                "lambda_arn": self.go_research_lambda.function_arn,
                "lambda_function_name": self.go_research_lambda.function_name
            }
        ]
        
        # Validate that all tool specs match declared names
        spec_names = {spec["tool_name"] for spec in tool_specs}
        declared_names = set(tool_names)
        
        if spec_names != declared_names:
            raise ValueError(f"Tool name mismatch! Specs: {spec_names}, Declared: {declared_names}")
        
        # Use BatchedToolConstruct for registration with secret requirements
        BatchedToolConstruct(
            self,
            "WebResearchTools",
            tool_specs=tool_specs,
            lambda_function=self.go_research_lambda,
            env_name=self.env_name,
            secret_requirements={
                "web-research": ["PPLX_API_KEY"]
            }
        )

        # Store Lambda function reference for monitoring
        self.web_research_lambda_function = self.go_research_lambda
        
        # Create export for other stacks
        CfnOutput(
            self,
            "WebResearchLambdaArnExport",
            value=self.go_research_lambda.function_arn,
            export_name=f"WebResearchLambdaArn-{self.env_name}",
            description="ARN of the web research Lambda function"
        )