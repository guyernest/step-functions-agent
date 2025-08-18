from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
from .base_tool_construct import MultiToolConstruct
from ..shared.tool_definitions import ToolDefinition, ToolLanguage


class EarthquakeMonitoringToolStack(Stack):
    """
    Earthquake Monitoring Tools Stack - Seismic data analysis and monitoring
    
    This stack deploys earthquake monitoring capabilities:
    - USGS Earthquake Catalog API integration
    - Location-based filtering and time range selection
    - Magnitude-based alert thresholds
    - Geographic coordinate processing
    - Real-time seismic data access
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Deploy TypeScript earthquake query tool
        self._create_earthquake_query_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_earthquake_query_tool(self):
        """Create TypeScript Lambda function for earthquake queries"""
        
        # Create execution role for earthquake Lambda
        earthquake_lambda_role = iam.Role(
            self,
            "EarthquakeQueryLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Create TypeScript Lambda function for earthquake queries
        self.earthquake_query_lambda = _lambda.Function(
            self,
            "EarthquakeQueryLambda",
            function_name=f"tool-earthquake-monitoring-{self.env_name}",
            description="Earthquake monitoring and analysis using USGS API with location and magnitude filtering",
            runtime=_lambda.Runtime.NODEJS_18_X,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/EarthQuakeQueryTS/dist"),
            handler="index.handler",
            timeout=Duration.seconds(60),
            memory_size=256,
            role=earthquake_lambda_role,
            environment={
                "NODE_ENV": "production"
            }
        )
        
        self.earthquake_query_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "EarthquakeQueryLambdaArn",
            value=self.earthquake_query_lambda.function_arn,
            export_name=f"EarthquakeQueryLambdaArn-{self.env_name}"
        )

    def _register_tools_using_base_construct(self):
        """Register all earthquake monitoring tools using the BaseToolConstruct pattern"""
        
        # Define tool locally instead of importing from shared definitions
        earthquake_tool = ToolDefinition(
            tool_name="query_earthquakes",
            description="Query earthquake data using USGS API with date range filtering",
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    },
                    "min_magnitude": {
                        "type": "number",
                        "description": "Minimum earthquake magnitude",
                        "default": 2.5
                    }
                },
                "required": ["start_date", "end_date"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["earthquake", "seismic", "usgs", "disaster"]
        )
        
        # Define earthquake monitoring tool specifications
        earthquake_tools = [
            {
                "tool_name": earthquake_tool.tool_name,
                "description": earthquake_tool.description,
                "input_schema": earthquake_tool.input_schema,
                "language": earthquake_tool.language.value,
                "tags": earthquake_tool.tags,
                "author": earthquake_tool.author
            }
        ]
        
        # Use MultiToolConstruct to register earthquake monitoring tools
        MultiToolConstruct(
            self,
            "EarthquakeMonitoringToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": earthquake_tools,
                    "lambda_function": self.earthquake_query_lambda
                }
            ],
            env_name=self.env_name
        )