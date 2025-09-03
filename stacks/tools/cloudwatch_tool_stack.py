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
from .base_tool_construct_batched import BatchedToolConstruct
import json
from pathlib import Path


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

        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'cloudwatch-insights' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ CloudWatchToolStack: Loaded {len(tool_names)} tool names from tool-names.json: {tool_names}")
        
        # Register all CloudWatch tools using BaseToolConstruct with self-contained definitions
        tool_specs = [
            {
                "tool_name": "find_log_groups_by_tag",
                "description": "Find CloudWatch log groups by tag name and value",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tag_name": {"type": "string", "description": "Tag name to search for"},
                        "tag_value": {"type": "string", "description": "Tag value to search for"}
                    },
                    "required": ["tag_name", "tag_value"]
                },
                "language": "python",
                "tags": ["cloudwatch", "logs", "discovery"],
                "author": "system",
                "lambda_arn": cloudwatch_lambda.function_arn,
                "lambda_function_name": cloudwatch_lambda.function_name
            },
            {
                "tool_name": "execute_query",
                "description": "Execute CloudWatch Logs Insights queries to analyze log data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "log_groups": {"type": "array", "items": {"type": "string"}, "description": "List of log group names to query"},
                        "query": {"type": "string", "description": "CloudWatch Logs Insights query"},
                        "start_time": {"type": "string", "description": "Start time (ISO format or relative like '1h ago')"},
                        "end_time": {"type": "string", "description": "End time (ISO format or relative like 'now')"}
                    },
                    "required": ["log_groups", "query"]
                },
                "language": "python",
                "tags": ["cloudwatch", "logs", "monitoring", "query"],
                "author": "system",
                "lambda_arn": cloudwatch_lambda.function_arn,
                "lambda_function_name": cloudwatch_lambda.function_name
            },
            {
                "tool_name": "get_query_generation_prompt",
                "description": "Get the prompt template for generating CloudWatch Logs Insights queries",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                },
                "language": "python",
                "tags": ["cloudwatch", "logs", "prompt"],
                "author": "system",
                "lambda_arn": cloudwatch_lambda.function_arn,
                "lambda_function_name": cloudwatch_lambda.function_name
            },
            {
                "tool_name": "get_service_graph",
                "description": "Get X-Ray service graph to visualize application architecture and dependencies",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string", "description": "Start time for service graph"},
                        "end_time": {"type": "string", "description": "End time for service graph"}
                    },
                    "required": ["start_time", "end_time"]
                },
                "language": "python",
                "tags": ["xray", "service-graph", "monitoring"],
                "author": "system",
                "lambda_arn": cloudwatch_lambda.function_arn,
                "lambda_function_name": cloudwatch_lambda.function_name
            }
        ]
        
        # Validate that all tool specs match declared names
        spec_names = {spec["tool_name"] for spec in tool_specs}
        declared_names = set(tool_names)
        
        if spec_names != declared_names:
            raise ValueError(f"Tool name mismatch! Specs: {spec_names}, Declared: {declared_names}")
        
        # Use BatchedToolConstruct to avoid throttling with 4 tools
        BatchedToolConstruct(
            self,
            "CloudWatchTools",
            tool_specs=tool_specs,
            lambda_function=cloudwatch_lambda,
            env_name=env_name
        )

        # Store Lambda function reference for monitoring
        self.cloudwatch_lambda_function = cloudwatch_lambda
        
        # Create CloudFormation exports
        self._create_stack_exports(cloudwatch_lambda)
    
    def _create_stack_exports(self, cloudwatch_lambda):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export CloudWatch Lambda ARN
        CfnOutput(
            self,
            "CloudWatchInsightsLambdaArn",
            value=cloudwatch_lambda.function_arn,
            export_name=f"CloudWatchInsightsLambdaArn-{self.env_name}",
            description="ARN of the CloudWatch Insights Lambda function"
        )
