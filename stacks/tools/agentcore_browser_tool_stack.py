"""
CDK Stack for Agent Core Browser Tool
Creates a Lambda function that invokes Agent Core for browser automation
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
from .base_tool_construct import BaseToolConstruct
import json
import os


class AgentCoreBrowserToolStack(Stack):
    """
    Agent Core Browser Tool - Lambda function for browser automation
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Get Agent Core runtime from deployment
        agent_runtime_arn = "arn:aws:bedrock-agentcore:us-west-2:672915487120:runtime/shopping_agent-aw6O6r7uk5"
        
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
            memory_size=1024,  # More memory for processing streaming responses
            environment={
                "AGENT_RUNTIME_ARN": agent_runtime_arn,
                "ENV_NAME": env_name
            },
            description=f"Agent Core browser tool handler for {env_name}"
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
        
        # Store the function name and ARN for use by agents
        self.function_name = self.agentcore_browser_lambda.function_name
        self.function_arn = self.agentcore_browser_lambda.function_arn
        
        # Register the tool in DynamoDB using BaseToolConstruct
        self._register_tool_in_registry()
    
    def _register_tool_in_registry(self):
        """Register the Agent Core browser tool in DynamoDB using BaseToolConstruct"""
        
        tool_spec = {
            "tool_name": "agentcore_browser_search",
            "description": "Search and extract information from web portals using Agent Core browser automation with Nova Act",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or task description for browser automation"
                    },
                    "url": {
                        "type": "string",
                        "description": "Target URL to search (default: https://www.amazon.com)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["search", "extract", "authenticate"],
                        "description": "Action to perform (default: search)"
                    },
                    "test_mode": {
                        "type": "boolean",
                        "description": "Use test mode for immediate execution (default: true)"
                    }
                },
                "required": ["query"]
            },
            "language": "python",
            "tags": ["browser", "automation", "search", "agent-core", "nova-act"],
            "author": "system",
            "human_approval_required": False,
            "lambda_arn": self.agentcore_browser_lambda.function_arn,
            "lambda_function_name": self.agentcore_browser_lambda.function_name
        }
        
        # Use BaseToolConstruct for registration
        BaseToolConstruct(
            self,
            "AgentCoreBrowserToolRegistry",
            tool_specs=[tool_spec],
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
            self, "ToolConfiguration",
            value=json.dumps({
                "tool_name": "agentcore_browser_search",
                "description": "Search and extract information from web portals using Agent Core browser automation",
                "lambda_arn": self.agentcore_browser_lambda.function_arn,
                "lambda_name": self.agentcore_browser_lambda.function_name,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or task description"
                        },
                        "url": {
                            "type": "string",
                            "description": "Target URL (default: https://www.amazon.com)"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["search", "extract", "authenticate"],
                            "description": "Action to perform (default: search)"
                        },
                        "test_mode": {
                            "type": "boolean",
                            "description": "Use test mode for immediate execution (default: true)"
                        }
                    },
                    "required": ["query"]
                }
            }),
            description="Tool configuration for Agent Core browser"
        )