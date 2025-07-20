from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .base_tool_construct import BaseToolConstruct
from ..shared.tool_definitions import CloudWatchTools


class CloudWatchToolStack(Stack):
    """
    CloudWatch Tools Stack - Provides comprehensive monitoring and log analysis capabilities
    
    This stack creates:
    - Lambda function for CloudWatch Logs Insights queries
    - IAM roles with appropriate CloudWatch and X-Ray permissions
    - Tool registration in the Tool Registry
    - Support for log group discovery, query execution, and service graph analysis
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create IAM role for CloudWatch tools Lambda
        cloudwatch_lambda_role = iam.Role(
            self, "CloudWatchToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant the Lambda function permission to access CloudWatch Logs and X-Ray service graph
        cloudwatch_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:DescribeLogGroups",
                    "logs:ListTagsLogGroup", 
                    "logs:StartQuery",
                    "logs:StopQuery",
                    "logs:GetQueryResults",
                    "logs:DescribeQueries",
                    "xray:GetServiceGraph",
                ],
                resources=["*"]
            )
        )

        # Create the CloudWatch tools Lambda function
        cloudwatch_lambda = _lambda_python.PythonFunction(
            self, "CloudWatchToolsLambda",
            function_name=f"cloudwatch-tools-{env_name}",
            description="CloudWatch Logs Insights and X-Ray monitoring tools for log analysis and service graph visualization",
            entry="lambda/tools/cloudwatch-insights",
            runtime=_lambda.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=cloudwatch_lambda_role,
        )

        # Register all CloudWatch tools using BaseToolConstruct
        tool_definitions = CloudWatchTools.get_all_tools()
        tool_specs = [
            tool_def.to_registry_item(
                lambda_arn=cloudwatch_lambda.function_arn,
                lambda_function_name=cloudwatch_lambda.function_name
            )
            for tool_def in tool_definitions
        ]
        
        BaseToolConstruct(
            self,
            "CloudWatchTools",
            tool_specs=tool_specs,
            lambda_function=cloudwatch_lambda,
            env_name=env_name
        )

        # Store Lambda function reference for monitoring
        self.cloudwatch_lambda_function = cloudwatch_lambda
        
