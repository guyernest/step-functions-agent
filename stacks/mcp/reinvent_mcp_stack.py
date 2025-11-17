"""
Reinvent MCP Server Stack

Demonstrates control plane integration for an MCP server deployed on AWS Lambda.
This stack shows how to use McpServerConstruct for automatic registration,
observability, and management integration.
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


class ReinventMcpStack(Stack):
    """
    CDK Stack for AWS re:Invent Conference Planner MCP Server

    This demonstrates:
    - Deploying Rust-based MCP server on Lambda
    - Automatic registration in control plane
    - CloudWatch observability integration
    - Optional tool delegation to remote Lambda functions
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

        # Create API Gateway (better than Function URL for MCP)
        self._create_api_gateway()

        # OPTIONAL: Register in control plane
        if self.enable_control_plane:
            self._register_in_control_plane()

        # Create outputs
        self._create_outputs()

    def _create_lambda_function(self):
        """Create Lambda function for Reinvent MCP Server"""

        # IAM role for Lambda
        self.lambda_role = iam.Role(
            self,
            "ReinventMcpLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # AWS Lambda Web Adapter layer (required for HTTP server on Lambda)
        # https://github.com/awslabs/aws-lambda-web-adapter
        web_adapter_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "LambdaAdapterLayer",
            # ARM64 version of Lambda Web Adapter
            f"arn:aws:lambda:{Stack.of(self).region}:753240598075:layer:LambdaAdapterLayerArm64:24"
        )

        # Lambda function (expects bootstrap binary at lambda/mcp-servers/reinvent/bootstrap)
        self.mcp_lambda = _lambda.Function(
            self,
            "ReinventMcpFunction",
            function_name=f"mcp-reinvent-{self.env_name}",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            handler="bootstrap",
            code=_lambda.Code.from_asset("lambda/mcp-servers/reinvent"),
            role=self.lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            architecture=_lambda.Architecture.ARM_64,
            layers=[web_adapter_layer],
            environment={
                "RUST_LOG": "info",
                "RUST_BACKTRACE": "1",
                # Lambda Web Adapter configuration (buffered mode for API Gateway)
                "AWS_LWA_PORT": "8080",
                # Tell Rust server to bind to port 8080 (Lambda Web Adapter expects this)
                "PORT": "8080",
            }
        )

    def _create_api_gateway(self):
        """Create API Gateway HTTP API for the MCP server"""

        # HTTP API Gateway with CORS
        self.api = apigw.HttpApi(
            self,
            "ReinventMcpApi",
            api_name=f"mcp-reinvent-api-{self.env_name}",
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
            "ReinventMcpIntegration",
            self.mcp_lambda,
        )

        # Add routes
        self.api.add_routes(
            path="/{proxy+}",
            methods=[apigw.HttpMethod.ANY],
            integration=integration,
        )

        # Root path route
        self.api.add_routes(
            path="/",
            methods=[apigw.HttpMethod.ANY],
            integration=integration,
        )

    def _register_in_control_plane(self):
        """Register MCP server in control plane (optional)"""

        # Get tool specifications from Rust server
        # These match what's in mcp-reinvent-core/src/lib.rs
        tools_spec = [
            {
                "name": "find_sessions",
                "description": "Find re:Invent sessions with flexible filtering. "
                              "Combine multiple filters to narrow down results.",
                "implementation": "local",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": ["string", "null"], "description": "Search query for title, abstract, or speaker names"},
                        "day": {"type": ["string", "null"], "description": "Filter by day (Monday-Friday)"},
                        "venue": {"type": ["string", "null"], "description": "Filter by venue (Venetian, MGM, etc.)"},
                        "level": {"type": ["integer", "null"], "description": "Filter by level (100, 200, 300, 400, 500)"},
                        "service": {"type": ["string", "null"], "description": "Filter by AWS service"},
                        "topic": {"type": ["string", "null"], "description": "Filter by topic"},
                        "session_type": {"type": ["string", "null"], "description": "Filter by session type"},
                        "area_of_interest": {"type": ["string", "null"], "description": "Filter by area of interest"},
                        "limit": {"type": "integer", "default": 20, "description": "Maximum number of results"}
                    }
                }
            },
            {
                "name": "get_session_details",
                "description": "Get comprehensive details about a specific session by its ID or short ID",
                "implementation": "local",
                "inputSchema": {
                    "type": "object",
                    "required": ["session_id"],
                    "properties": {
                        "session_id": {"type": "string", "description": "Session ID or short ID (e.g., 'DVT222-S')"}
                    }
                }
            }
        ]

        # Resource specifications
        resources_spec = [
            {
                "uri": "reinvent://guide/levels",
                "name": "Session Levels Guide",
                "description": "[PRIORITY: HIGH] Learn about session levels (100/200/300/400/500)",
                "mimeType": "text/markdown"
            },
            {
                "uri": "reinvent://guide/topics",
                "name": "Topics Guide",
                "description": "[PRIORITY: HIGH] Browse available session topics and categories",
                "mimeType": "text/markdown"
            },
            {
                "uri": "reinvent://guide/services",
                "name": "AWS Services Guide",
                "description": "Browse all AWS services covered in re:Invent sessions",
                "mimeType": "text/markdown"
            },
            {
                "uri": "reinvent://travel-times",
                "name": "Venue Travel Times",
                "description": "[PRIORITY: HIGH] Essential guide for planning conference schedule with travel times",
                "mimeType": "text/markdown"
            }
        ]

        # Prompt/workflow specifications
        prompts_spec = [
            {
                "name": "plan_day_agenda",
                "description": "Intelligently plan your re:Invent conference day with session recommendations and travel time optimization",
                "arguments": [
                    {"name": "day", "description": "The day to plan (Monday-Friday)", "required": True},
                    {"name": "query", "description": "Search terms for sessions", "required": False},
                    {"name": "level", "description": "Session level to focus on (100-500)", "required": False}
                ]
            }
        ]

        # Register using McpServerConstruct
        self.mcp_registration = McpServerConstruct(
            self,
            "McpServerRegistration",
            server_id=f"mcp-reinvent-{self.env_name}",
            version="1.0.0",
            server_name="AWS re:Invent Conference Planner",
            server_spec={
                "description": "MCP server for planning AWS re:Invent conference attendance with intelligent day planning workflow",
                "protocol_version": "2024-11-05",
                "protocol_type": "jsonrpc",
                "endpoint_url": self.api.url,
                "health_check_url": f"{self.api.url}health",
                "health_check_interval": 300,

                # MCP capabilities
                "tools": tools_spec,
                "resources": resources_spec,
                "prompts": prompts_spec,

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
                    "tags": ["production", "conference", "planning", "mcp"],
                    "repository": "https://github.com/.../mcp-reinvent-planner",
                    "documentation": "https://docs.../mcp-reinvent"
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
