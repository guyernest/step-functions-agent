from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .base_tool_construct import BaseToolConstruct
import json
from pathlib import Path


class FinancialToolStack(Stack):
    """
    Financial Tools Stack - Provides comprehensive financial data analysis capabilities
    
    This stack creates:
    - Lambda function for Yahoo Finance data access
    - IAM roles with appropriate permissions
    - Tool registration in the Tool Registry
    - Support for stock data, industry analysis, and company rankings
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create IAM role for financial tools Lambda
        financial_lambda_role = iam.Role(
            self, "FinancialToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant X-Ray permissions
        financial_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )

        # Grant S3 permissions for data caching (if needed)
        financial_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                resources=["arn:aws:s3:::*/*"]
            )
        )

        # Create the financial tools Lambda function
        financial_lambda = _lambda_python.PythonFunction(
            self, "FinancialToolsLambda",
            function_name=f"financial-tools-{env_name}",
            description="Financial data tools for stock analysis, industry research, and market data",
            entry="lambda/tools/yfinance",
            runtime=_lambda.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(90),
            memory_size=512,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=financial_lambda_role,
        )

        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'yfinance' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ FinancialToolStack: Loaded {len(tool_names)} tool names from tool-names.json: {tool_names}")
        
        # Register all financial tools using BaseToolConstruct with self-contained definitions
        tool_specs = [
            {
                "tool_name": "get_ticker_data",
                "description": "Get stock price data for a ticker symbol within a date range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                    },
                    "required": ["ticker", "start_date", "end_date"]
                },
                "language": "python",
                "tags": ["finance", "stocks", "yfinance", "historical"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            },
            {
                "tool_name": "get_ticker_recent_history",
                "description": "Get recent stock price history for a ticker",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                        "period": {"type": "string", "description": "Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)", "default": "1mo"}
                    },
                    "required": ["ticker"]
                },
                "language": "python",
                "tags": ["finance", "stocks", "yfinance", "recent"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            },
            {
                "tool_name": "list_industries",
                "description": "List all industries within a specific sector",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector_key": {"type": "string", "description": "Sector key (e.g., technology, healthcare, financial-services)"}
                    },
                    "required": ["sector_key"]
                },
                "language": "python",
                "tags": ["finance", "sectors", "industries", "yfinance"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            },
            {
                "tool_name": "top_sector_companies",
                "description": "Get top companies within a specific sector",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector_key": {"type": "string", "description": "Sector key to get top companies for"}
                    },
                    "required": ["sector_key"]
                },
                "language": "python",
                "tags": ["finance", "sectors", "companies", "rankings"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            },
            {
                "tool_name": "top_industry_companies",
                "description": "Get top companies within a specific industry",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry_key": {"type": "string", "description": "Industry key to get top companies for"}
                    },
                    "required": ["industry_key"]
                },
                "language": "python",
                "tags": ["finance", "industries", "companies", "rankings"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            },
            {
                "tool_name": "download_tickers_data",
                "description": "Download data for multiple tickers at once",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tickers": {"type": "array", "items": {"type": "string"}, "description": "List of ticker symbols"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                    },
                    "required": ["tickers", "start_date", "end_date"]
                },
                "language": "python",
                "tags": ["finance", "stocks", "yfinance", "bulk"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            }
        ]
        
        # Validate that all tool specs match declared names
        spec_names = {spec["tool_name"] for spec in tool_specs}
        declared_names = set(tool_names)
        
        if spec_names != declared_names:
            raise ValueError(f"Tool name mismatch! Specs: {spec_names}, Declared: {declared_names}")
        
        BaseToolConstruct(
            self,
            "FinancialTools",
            tool_specs=tool_specs,
            lambda_function=financial_lambda,
            env_name=env_name
        )

        # Store Lambda function reference for monitoring
        self.financial_lambda_function = financial_lambda
        
        # Create CloudFormation exports
        self._create_stack_exports(financial_lambda)
    
    def _create_stack_exports(self, financial_lambda):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export YFinance Lambda ARN (using the import name expected by research agent)
        CfnOutput(
            self,
            "YFinanceLambdaArn",
            value=financial_lambda.function_arn,
            export_name=f"YFinanceLambdaArn-{self.env_name}",
            description="ARN of the YFinance Lambda function"
        )