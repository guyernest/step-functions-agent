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
from ..shared.tool_definitions import JavaTools
import os


class StockAnalysisToolStack(Stack):
    """
    Stock Analysis Tools Stack - High-performance financial time series analysis
    
    This stack deploys Java-based stock analysis capabilities:
    - Moving average calculations using Fork/Join framework
    - Historical volatility analysis with statistical methods
    - S3 data processing for large datasets
    - Optimized for parallel processing and performance
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Deploy Java stock analysis tool
        self._create_stock_analysis_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_stock_analysis_tool(self):
        """Create Java Lambda function for stock analysis"""
        
        # Create execution role for Java Lambda
        stock_analysis_lambda_role = iam.Role(
            self,
            "StockAnalysisLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to S3 for reading stock data
        stock_analysis_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    "arn:aws:s3:::*/*",  # Allow access to all S3 objects
                    "arn:aws:s3:::*"     # Allow bucket listing
                ]
            )
        )
        
        # Create Java Lambda function for stock analysis
        self.stock_analysis_lambda = _lambda.Function(
            self,
            "StockAnalysisLambda",
            function_name=f"tool-stock-analysis-{self.env_name}",
            description="High-performance stock analysis using Java Fork/Join framework for time series computation",
            runtime=_lambda.Runtime.JAVA_17,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/stock-analyzer/"),
            handler="tools.StockAnalyzerLambda::handleRequest",
            timeout=Duration.minutes(15),  # Stock analysis can take time for large datasets
            memory_size=1024,  # More memory for parallel processing
            role=stock_analysis_lambda_role,
            environment={
                # Java-specific optimizations for Lambda
                "JAVA_TOOL_OPTIONS": "-XX:+TieredCompilation -XX:TieredStopAtLevel=1 -XX:+UseSerialGC"
            }
        )
        
        self.stock_analysis_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "StockAnalysisLambdaArn",
            value=self.stock_analysis_lambda.function_arn,
            export_name=f"StockAnalysisLambdaArn-{self.env_name}"
        )

    def _register_tools_using_base_construct(self):
        """Register all stock analysis tools using the BaseToolConstruct pattern"""
        
        # Get tool definitions from centralized definitions
        moving_average_tool = JavaTools.STOCK_ANALYZER
        volatility_tool = JavaTools.VOLATILITY_ANALYZER
        
        # Define stock analysis tool specifications
        stock_analysis_tools = [
            {
                "tool_name": moving_average_tool.tool_name,
                "description": moving_average_tool.description,
                "input_schema": moving_average_tool.input_schema,
                "language": moving_average_tool.language.value,
                "tags": moving_average_tool.tags,
                "author": moving_average_tool.author
            },
            {
                "tool_name": volatility_tool.tool_name,
                "description": volatility_tool.description,
                "input_schema": volatility_tool.input_schema,
                "language": volatility_tool.language.value,
                "tags": volatility_tool.tags,
                "author": volatility_tool.author
            }
        ]
        
        # Use MultiToolConstruct to register all Java tools
        MultiToolConstruct(
            self,
            "StockAnalysisToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": stock_analysis_tools,
                    "lambda_function": self.stock_analysis_lambda
                }
            ],
            env_name=self.env_name
        )