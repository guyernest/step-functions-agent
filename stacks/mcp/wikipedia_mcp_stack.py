"""
Wikipedia MCP Server Stack

Demonstrates control plane integration for a Wikipedia search MCP server on AWS Lambda.
Shows how to use McpServerConstruct for automatic registration and observability.
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigatewayv2 as apigw,
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct
from ..shared.mcp_server_construct import McpServerConstruct


class WikipediaMcpStack(Stack):
    """
    CDK Stack for Wikipedia MCP Server

    This demonstrates:
    - Deploying Rust-based Wikipedia MCP server on Lambda
    - Automatic registration in control plane
    - CloudWatch observability integration
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "prod",
        enable_control_plane: bool = True,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.enable_control_plane = enable_control_plane

        # Deploy Lambda function for MCP server
        self._create_lambda_function()

        # Create API Gateway
        self._create_api_gateway()

        # OPTIONAL: Register in control plane
        if self.enable_control_plane:
            self._register_in_control_plane()

        # Create outputs
        self._create_outputs()

    def _create_lambda_function(self):
        """Create Lambda function for Wikipedia MCP Server"""

        # IAM role for Lambda
        self.lambda_role = iam.Role(
            self,
            "WikipediaMcpLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # AWS Lambda Web Adapter layer (ARM64)
        web_adapter_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "LambdaAdapterLayer",
            f"arn:aws:lambda:{Stack.of(self).region}:753240598075:layer:LambdaAdapterLayerArm64:24"
        )

        # Lambda function
        self.mcp_lambda = _lambda.Function(
            self,
            "WikipediaMcpFunction",
            function_name=f"mcp-wikipedia-{self.env_name}",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            handler="bootstrap",
            code=_lambda.Code.from_asset("lambda/mcp-servers/wikipedia"),
            role=self.lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            architecture=_lambda.Architecture.ARM_64,
            layers=[web_adapter_layer],
            environment={
                "RUST_LOG": "info",
                "RUST_BACKTRACE": "1",
                # Lambda Web Adapter configuration
                "AWS_LWA_PORT": "8080",
                # Tell Rust server to bind to port 8080
                "PORT": "8080",
            }
        )

    def _create_api_gateway(self):
        """Create API Gateway HTTP API for the MCP server"""

        # HTTP API Gateway with CORS
        self.api = apigw.HttpApi(
            self,
            "WikipediaMcpApi",
            api_name=f"mcp-wikipedia-api-{self.env_name}",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[
                    apigw.CorsHttpMethod.GET,
                    apigw.CorsHttpMethod.POST,
                    apigw.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=["*"],
                max_age=Duration.days(1),
            )
        )

        # Lambda integration
        integration = HttpLambdaIntegration(
            "WikipediaMcpIntegration",
            self.mcp_lambda,
        )

        # Add routes
        self.api.add_routes(
            path="/{proxy+}",
            methods=[apigw.HttpMethod.ANY],
            integration=integration,
        )

        self.api.add_routes(
            path="/",
            methods=[apigw.HttpMethod.ANY],
            integration=integration,
        )

    def _register_in_control_plane(self):
        """Register MCP server in control plane"""

        # Tool specifications
        tools_spec = [
            {
                "name": "search_articles",
                "description": "Search Wikipedia articles by query",
                "implementation": "local",
                "inputSchema": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "lang": {"type": "string", "default": "en", "description": "Wikipedia language code (e.g., 'en', 'es', 'fr')"},
                        "limit": {"type": "integer", "default": 5, "description": "Maximum number of results"}
                    }
                }
            },
            {
                "name": "get_summary",
                "description": "Get article summary",
                "implementation": "local",
                "inputSchema": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string", "description": "Article title"},
                        "lang": {"type": "string", "default": "en", "description": "Wikipedia language code"}
                    }
                }
            },
            {
                "name": "get_page_html",
                "description": "Get full page HTML",
                "implementation": "local",
                "inputSchema": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string", "description": "Article title"},
                        "lang": {"type": "string", "default": "en", "description": "Wikipedia language code"}
                    }
                }
            }
        ]

        # Register using McpServerConstruct
        self.mcp_registration = McpServerConstruct(
            self,
            "McpServerRegistration",
            server_id=f"mcp-wikipedia-{self.env_name}",
            version="1.0.0",
            server_name="Wikipedia Search & Reference",
            server_spec={
                "description": "MCP server for searching Wikipedia articles and retrieving content",
                "protocol_version": "2024-11-05",
                "protocol_type": "jsonrpc",
                "endpoint_url": self.api.url,
                "health_check_url": f"{self.api.url}health",
                "health_check_interval": 300,

                # MCP capabilities
                "tools": tools_spec,
                "resources": [],
                "prompts": [],

                # Observability
                "traces_enabled": True,
                "log_level": "INFO",

                # Authentication
                "authentication_type": "none",

                # Configuration
                "configuration": {
                    "timeout_seconds": 30,
                    "max_retries": 3,
                    "supports_batch": False
                },

                # Metadata
                "metadata": {
                    "team": "platform",
                    "cost_center": "engineering",
                    "tags": ["production", "wikipedia", "reference", "mcp"],
                    "repository": "https://github.com/.../mcp-wikipedia",
                    "documentation": "https://docs.../mcp-wikipedia"
                }
            },
            lambda_function=self.mcp_lambda,
            env_name=self.env_name,
            enable_observability=True,
            enable_health_monitoring=True
        )

    def _create_outputs(self):
        """Create CloudFormation outputs"""

        CfnOutput(
            self,
            "ApiUrl",
            value=self.api.url or "",
            description="MCP Server API Gateway URL"
        )

        CfnOutput(
            self,
            "ApiId",
            value=self.api.api_id,
            description="API Gateway ID"
        )

        CfnOutput(
            self,
            "FunctionArn",
            value=self.mcp_lambda.function_arn,
            description="Lambda Function ARN"
        )

        CfnOutput(
            self,
            "LogGroup",
            value=self.mcp_lambda.log_group.log_group_name,
            description="CloudWatch Log Group"
        )
