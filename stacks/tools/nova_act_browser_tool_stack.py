"""
Nova Act Browser Tool Stack - Web portal search and browser automation
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput
)
from constructs import Construct
from .base_tool_construct import BaseToolConstruct


class NovaActBrowserToolStack(Stack):
    """
    Nova Act Browser Tool Stack - Browser automation for web portal searches
    
    This stack deploys the Nova Act browser automation tool that provides:
    - Web portal search capabilities
    - Data extraction from web pages
    - Authentication handling for protected portals
    - Screenshot capture and result storage
    - Integration with Bedrock Agent Core (when available)
    - Support for hybrid agent architectures
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create S3 bucket for search results and screenshots
        self._create_results_bucket()
        
        # Create Nova Act browser Lambda function
        self._create_nova_act_browser_lambda()
        
        # Register tool in DynamoDB using base construct
        self._register_tool()
        
        # Create outputs
        self._create_outputs()
    
    def _create_results_bucket(self):
        """Create S3 bucket for storing search results and screenshots"""
        
        self.results_bucket = s3.Bucket(
            self, "NovaActBrowserResultsBucket",
            bucket_name=f"nova-act-browser-results-{self.env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldResults",
                    expiration=Duration.days(7),
                    prefix="results/"
                ),
                s3.LifecycleRule(
                    id="DeleteOldScreenshots",
                    expiration=Duration.days(1),
                    prefix="screenshots/"
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
    
    def _create_nova_act_browser_lambda(self):
        """Create the Nova Act browser automation Lambda function"""
        
        # Create IAM role with necessary permissions
        self.nova_act_role = iam.Role(
            self, "NovaActBrowserRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant S3 permissions for results storage
        self.results_bucket.grant_read_write(self.nova_act_role)
        
        # Create Lambda function
        self.nova_act_browser_lambda = _lambda_python.PythonFunction(
            self, "NovaActBrowserFunction",
            function_name=f"nova-act-browser-{self.env_name}",
            description="Nova Act browser automation for web portal searches",
            entry="lambda/tools/nova_act_browser",
            index="handler.py",
            handler="lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(60),
            memory_size=512,
            role=self.nova_act_role,
            environment={
                "RESULTS_BUCKET": self.results_bucket.bucket_name,
                "ENVIRONMENT": self.env_name,
                "LOG_LEVEL": "INFO"
            }
        )
        
        # Store function name for monitoring
        self.function_name = self.nova_act_browser_lambda.function_name
    
    def _register_tool(self):
        """Register the Nova Act browser tool in DynamoDB"""
        
        import json
        
        input_schema = {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["search", "extract", "authenticate"],
                            "description": "The action to perform"
                        },
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query (for search action)"
                        },
                        "selectors": {
                            "type": "object",
                            "description": "CSS selectors for data extraction (for extract action)"
                        },
                        "credentials": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"}
                            },
                            "description": "Credentials for authentication (for authenticate action)"
                        },
                        "config": {
                            "type": "object",
                            "properties": {
                                "max_results": {"type": "integer"},
                                "timeout": {"type": "integer"},
                                "capture_screenshot": {"type": "boolean"},
                                "search_selector": {"type": "string"},
                                "results_selector": {"type": "string"}
                            },
                            "description": "Additional configuration options"
                        }
                    },
                    "required": ["action"]
                }
        
        tool_specs = [{
            "tool_name": "nova_act_browser",
            "description": "Browser automation tool for web portal searches, data extraction, and authentication",
            "input_schema": json.dumps(input_schema),
            "lambda_arn": self.nova_act_browser_lambda.function_arn,
            "lambda_function_name": self.nova_act_browser_lambda.function_name,
            "language": "python",
            "tags": json.dumps(["web", "browser", "automation", "search", "scraping", "nova-act"]),
            "status": "active",
            "author": "StepFunctionsAgent",
            "human_approval_required": False,
            "version": "1.0.0",
            "created_at": "2025-08-24T00:00:00Z",
            "updated_at": "2025-08-24T00:00:00Z",
            "response_schema": json.dumps({
                    "type": "object",
                    "properties": {
                        "statusCode": {"type": "integer"},
                        "session_id": {"type": "string"},
                        "action": {"type": "string"},
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "url": {"type": "string"}
                                }
                            }
                        },
                        "extracted_data": {"type": "object"},
                        "authenticated": {"type": "boolean"},
                        "s3_key": {"type": "string"},
                        "error": {"type": "string"}
                    }
                })
        }]
        
        tool_construct = BaseToolConstruct(
            self, "NovaActBrowserTool",
            tool_specs=tool_specs,
            lambda_function=self.nova_act_browser_lambda,
            env_name=self.env_name
        )
    
    def _create_outputs(self):
        """Create stack outputs"""
        
        CfnOutput(
            self, "NovaActBrowserFunctionArn",
            value=self.nova_act_browser_lambda.function_arn,
            description="ARN of the Nova Act browser Lambda function",
            export_name=f"NovaActBrowserFunctionArn-{self.env_name}"
        )
        
        CfnOutput(
            self, "NovaActBrowserFunctionName",
            value=self.nova_act_browser_lambda.function_name,
            description="Name of the Nova Act browser Lambda function"
        )
        
        CfnOutput(
            self, "ResultsBucketName",
            value=self.results_bucket.bucket_name,
            description="Name of the S3 bucket for search results"
        )