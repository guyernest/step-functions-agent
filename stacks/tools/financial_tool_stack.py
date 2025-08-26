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

        # Register all financial tools using BaseToolConstruct with self-contained definitions
        tool_specs = [
            {
                "tool_name": "get_stock_data",
                "description": "Get stock price data and financial information using Yahoo Finance",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"},
                        "period": {"type": "string", "description": "Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"},
                        "interval": {"type": "string", "description": "Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)"}
                    },
                    "required": ["symbol"]
                },
                "language": "python",
                "tags": ["finance", "stocks", "yfinance"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            },
            {
                "tool_name": "get_company_info",
                "description": "Get detailed company information and fundamentals",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"}
                    },
                    "required": ["symbol"]
                },
                "language": "python",
                "tags": ["finance", "company", "fundamentals"],
                "author": "system",
                "lambda_arn": financial_lambda.function_arn,
                "lambda_function_name": financial_lambda.function_name
            }
        ]
        
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