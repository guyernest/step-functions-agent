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
from ..shared.tool_definitions import FinancialTools


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

        # Register all financial tools using BaseToolConstruct
        tool_definitions = FinancialTools.get_all_tools()
        tool_specs = [
            tool_def.to_registry_item(
                lambda_arn=financial_lambda.function_arn,
                lambda_function_name=financial_lambda.function_name
            )
            for tool_def in tool_definitions
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