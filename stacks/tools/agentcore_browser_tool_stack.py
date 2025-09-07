"""
CDK Stack for Agent Core Browser Tool
Creates a Lambda function that routes to multiple Agent Core browser agents
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_iam as iam,
    CfnOutput,
    Duration
)
from constructs import Construct
from .base_tool_construct_batched import BatchedToolConstruct
import json
import os


class AgentCoreBrowserToolStack(Stack):
    """
    Agent Core Browser Tool - Lambda function that routes to multiple browser agents
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        # Get account ID from env if provided, otherwise use default
        env = kwargs.get('env')
        self.aws_account_id = env.account if env and hasattr(env, 'account') else '672915487120'
        
        # Get the path to the Lambda function code
        lambda_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "lambda", "tools", "agentcore_browser"
        )
        
        # Create Lambda function using PythonLambda to handle dependencies
        self.agentcore_browser_lambda = lambda_python.PythonFunction(
            self, "AgentCoreBrowserLambda",
            function_name=f"agentcore-browser-tool-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            entry=lambda_path,
            index="lambda_function.py",
            handler="handler",
            timeout=Duration.seconds(300),  # 5 minutes for long-running browser tasks
            memory_size=256,  # Reduced memory for cost optimization
            environment={
                "AWS_ACCOUNT_ID": str(self.aws_account_id),
                "ENV_NAME": env_name
            },
            description=f"Agent Core browser tool router for {env_name}"
        )
        
        # Grant permissions to invoke Agent Core
        self.agentcore_browser_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock-agent-runtime:InvokeAgent",
                    "bedrock-agent-runtime:*",
                    "bedrock-agentcore:*",
                    "bedrock:InvokeModel"
                ],
                resources=["*"]
            )
        )
        
        # Grant permissions to access S3 for browser recordings
        self.agentcore_browser_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket",
                    "s3:GetObject"
                ],
                resources=[
                    "arn:aws:s3:::nova-act-browser-results-prod-672915487120",
                    "arn:aws:s3:::nova-act-browser-results-prod-672915487120/*"
                ]
            )
        )
        
        # Store the function name and ARN for use by agents
        self.function_name = self.agentcore_browser_lambda.function_name
        self.function_arn = self.agentcore_browser_lambda.function_arn
        
        # Register the tool in DynamoDB using BaseToolConstruct
        self._register_tool_in_registry()
    
    def _register_tool_in_registry(self):
        """Register all browser tool variants in DynamoDB using BatchedToolConstruct"""
        
        # Define all three tool variants that route to different agents
        tool_specs = [
            {
                "tool_name": "browser_broadband",
                "description": "Check UK broadband availability and speeds for a given address using BT Wholesale portal",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "object",
                            "properties": {
                                "building_number": {
                                    "type": "string",
                                    "description": "Building number or name"
                                },
                                "street": {
                                    "type": "string",
                                    "description": "Street name"
                                },
                                "town": {
                                    "type": "string",
                                    "description": "Town or city"
                                },
                                "postcode": {
                                    "type": "string",
                                    "description": "UK postcode (required)"
                                }
                            },
                            "required": ["postcode"],
                            "description": "UK address to check broadband availability"
                        }
                    },
                    "required": ["address"]
                },
                "language": "python",
                "tags": ["browser", "automation", "broadband", "uk", "telecom"],
                "author": "system",
                "human_approval_required": False,
                "lambda_arn": self.agentcore_browser_lambda.function_arn,
                "lambda_function_name": self.agentcore_browser_lambda.function_name
            },
            {
                "tool_name": "browser_shopping",
                "description": "Search for products and compare prices on e-commerce websites like Amazon and eBay",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Product search query"
                        },
                        "site": {
                            "type": "string",
                            "enum": ["amazon", "ebay", "all"],
                            "description": "Shopping site to search (default: amazon)"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)"
                        }
                    },
                    "required": ["query"]
                },
                "language": "python",
                "tags": ["browser", "automation", "shopping", "e-commerce", "prices"],
                "author": "system",
                "human_approval_required": False,
                "lambda_arn": self.agentcore_browser_lambda.function_arn,
                "lambda_function_name": self.agentcore_browser_lambda.function_name
            },
            {
                "tool_name": "browser_search",
                "description": "General web search and information extraction from any website",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or extraction task"
                        },
                        "url": {
                            "type": "string",
                            "description": "Specific URL to search or extract from (optional)"
                        },
                        "extract_fields": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Specific fields to extract from results (optional)"
                        }
                    },
                    "required": ["query"]
                },
                "language": "python",
                "tags": ["browser", "automation", "search", "web", "extraction"],
                "author": "system",
                "human_approval_required": False,
                "lambda_arn": self.agentcore_browser_lambda.function_arn,
                "lambda_function_name": self.agentcore_browser_lambda.function_name
            }
        ]
        
        # Use BatchedToolConstruct for registration
        BatchedToolConstruct(
            self,
            "AgentCoreBrowserToolRegistry",
            tool_specs=tool_specs,
            lambda_function=self.agentcore_browser_lambda,
            env_name=self.env_name
        )
        
        # Outputs
        CfnOutput(
            self, "LambdaFunctionArn",
            value=self.agentcore_browser_lambda.function_arn,
            description=f"Agent Core Browser Lambda ARN for {self.env_name}",
            export_name=f"AgentCoreBrowserLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self, "LambdaFunctionName",
            value=self.agentcore_browser_lambda.function_name,
            description=f"Agent Core Browser Lambda name for {self.env_name}",
            export_name=f"AgentCoreBrowserLambdaName-{self.env_name}"
        )
        
        CfnOutput(
            self, "RegisteredTools",
            value=json.dumps([
                "browser_broadband",
                "browser_shopping",
                "browser_search"
            ]),
            description="List of registered browser tool variants"
        )
        
        CfnOutput(
            self, "ToolConfiguration",
            value=json.dumps({
                "description": "Multi-tool browser automation using Agent Core",
                "lambda_arn": self.agentcore_browser_lambda.function_arn,
                "lambda_name": self.agentcore_browser_lambda.function_name,
                "tools": {
                    "browser_broadband": "UK broadband availability checker",
                    "browser_shopping": "E-commerce product search and price comparison",
                    "browser_search": "General web search and information extraction"
                }
            }),
            description="Tool configuration for Agent Core browser tools"
        )