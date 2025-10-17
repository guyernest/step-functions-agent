"""
CDK Stack for Agent Core Browser Tool
Creates a Lambda function that routes to multiple Agent Core browser agents
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_iam as iam,
    aws_ssm as ssm,
    CfnOutput,
    Duration,
    BundlingOptions
)
from constructs import Construct
from .base_tool_construct_batched import BatchedToolConstruct
import json
import os
from pathlib import Path


class AgentCoreBrowserToolStack(Stack):
    """
    Agent Core Browser Tool - Lambda function that routes to multiple browser agents

    This stack can work in two modes:
    1. With agent_arns parameter: Uses CDK-deployed AgentCore runtimes (recommended)
    2. Without agent_arns: Uses hardcoded agent ARNs from agent_config.py (legacy)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "prod",
        agent_arns: dict = None,  # Optional: Map of tool_name -> agent_arn
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.agent_arns = agent_arns or {}

        # Get account ID from env if provided, otherwise use default
        env = kwargs.get('env')
        self.aws_account_id = env.account if env and hasattr(env, 'account') else '672915487120'
        
        # Get the path to the Lambda function code
        lambda_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "lambda", "tools", "agentcore_browser"
        )
        
        # Build environment variables for Lambda
        lambda_env = {
            "AWS_ACCOUNT_ID": str(self.aws_account_id),
            "ENV_NAME": env_name,
            "ENVIRONMENT": env_name,  # For tool_secrets.py compatibility
            "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{env_name}",
            "POWERTOOLS_SERVICE_NAME": "agentcore-browser",
            "POWERTOOLS_LOG_LEVEL": "INFO"
        }

        # Determine which mode to use for agent ARN resolution
        # Priority: Parameter Store > Environment Variables > Hardcoded
        use_parameter_store = os.environ.get('USE_PARAMETER_STORE_ARNS', 'false').lower() == 'true'

        if use_parameter_store:
            # Use Parameter Store for agent ARNs (recommended for multi-region/account)
            lambda_env["USE_PARAMETER_STORE_ARNS"] = "true"
        elif self.agent_arns:
            # Pass agent ARNs to Lambda for dynamic routing via environment variables
            lambda_env["AGENT_ARN_BROADBAND"] = self.agent_arns.get("browser_broadband", "")
            lambda_env["AGENT_ARN_SHOPPING"] = self.agent_arns.get("browser_shopping", "")
            lambda_env["AGENT_ARN_SEARCH"] = self.agent_arns.get("browser_search", "")
            lambda_env["AGENT_ARN_APARTMENTS"] = self.agent_arns.get("browser_apartments", "")
            lambda_env["USE_DYNAMIC_AGENT_ARNS"] = "true"

        # Create Lambda function using PythonLambda to handle dependencies
        # Exclude agents/ directory to reduce package size
        self.agentcore_browser_lambda = lambda_python.PythonFunction(
            self, "AgentCoreBrowserLambda",
            function_name=f"agentcore-browser-tool-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            entry=lambda_path,
            index="lambda_function.py",
            handler="handler",
            timeout=Duration.seconds(300),  # 5 minutes for long-running browser tasks
            memory_size=256,  # Reduced memory for cost optimization
            environment=lambda_env,
            tracing=lambda_.Tracing.ACTIVE,  # Enable X-Ray tracing
            description=f"Agent Core browser tool router for {env_name}",
            bundling=lambda_python.BundlingOptions(
                asset_excludes=[
                    "agents",
                    "agents/*",
                    "test_events",
                    "test_events/*",
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                    "*.md",
                    ".dockerignore",
                    ".lambdaignore"
                ]
            )
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
        # Supports both us-west-2 and eu-west-1 recording buckets
        self.agentcore_browser_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket",
                    "s3:GetObject"
                ],
                resources=[
                    "arn:aws:s3:::nova-act-browser-results-prod-672915487120",
                    "arn:aws:s3:::nova-act-browser-results-prod-672915487120/*",
                    "arn:aws:s3:::nova-act-browser-results-prod-145023107515",
                    "arn:aws:s3:::nova-act-browser-results-prod-145023107515/*"
                ]
            )
        )

        # Grant permissions to retrieve secrets from consolidated tool secrets
        self.agentcore_browser_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/tool-secrets/{env_name}*"
                ]
            )
        )

        # Grant X-Ray tracing permissions
        self.agentcore_browser_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )

        # If using Parameter Store mode, create parameters and grant permissions
        if use_parameter_store:
            # Define the tool names and their default ARNs (can be overridden via context)
            tool_params = {
                "browser_broadband": self.node.try_get_context("browser_broadband_agent_arn") or "",
                "browser_shopping": self.node.try_get_context("browser_shopping_agent_arn") or "",
                "browser_search": self.node.try_get_context("browser_search_agent_arn") or "",
                "browser_apartments": self.node.try_get_context("browser_apartments_agent_arn") or ""
            }

            # Create SSM parameters for each tool
            for tool_name, arn in tool_params.items():
                if arn:  # Only create parameter if ARN is provided
                    ssm.StringParameter(
                        self, f"AgentArn{tool_name.replace('_', '').title()}",
                        parameter_name=f"/agentcore/tools/{tool_name}/agent_arn",
                        string_value=arn,
                        description=f"AgentCore ARN for {tool_name}",
                        tier=ssm.ParameterTier.STANDARD
                    )

            # Grant Lambda permission to read SSM parameters
            self.agentcore_browser_lambda.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath"
                    ],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/agentcore/tools/*"
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
        
        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'agentcore_browser' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ Loaded {len(tool_names)} tool names from {tool_names_file.name}: {tool_names}")
        
        # Validate that we have the expected tools
        expected_tools = ["browser_broadband", "browser_shopping", "browser_search"]
        if set(tool_names) != set(expected_tools):
            raise ValueError(f"Tool names mismatch! Expected {expected_tools}, got {tool_names}")
        
        # Define all three tool variants that route to different agents
        tool_specs = [
            {
                "tool_name": "browser_broadband",
                "description": "Check UK broadband availability and speeds for a given address using BT Wholesale portal",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "building_number": {
                            "type": "string",
                            "description": "Building number or name (e.g., '10', 'Flat 3A', 'The Manor House')"
                        },
                        "street": {
                            "type": "string", 
                            "description": "Street name without building number (e.g., 'Downing Street', 'High Street')"
                        },
                        "town": {
                            "type": "string",
                            "description": "Town or city name (e.g., 'London', 'Manchester', 'Birmingham')"
                        },
                        "postcode": {
                            "type": "string",
                            "description": "UK postcode in standard format (e.g., 'SW1A 2AA', 'E8 1GQ', 'M1 1AA')"
                        }
                    },
                    "required": ["postcode"]
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