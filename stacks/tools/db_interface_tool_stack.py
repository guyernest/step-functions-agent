from aws_cdk import (
    Duration,
    Stack,
    Fn,
    CfnOutput,
    CustomResource,
    RemovalPolicy,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_stepfunctions_tasks as tasks,
    custom_resources as cr,
)
from constructs import Construct
from .base_tool_construct import BaseToolConstruct
from ..shared.naming_conventions import NamingConventions
import json


class DBInterfaceToolStack(Stack):
    """
    DB Interface Tool Stack - Deploys the db-interface Lambda and registers both SQL tools
    
    This stack demonstrates the tool deployment pattern:
    - Deploys single Lambda with consistent naming
    - Registers multiple tools that use the same Lambda
    - Populates DynamoDB tool registry
    - Uses tool-specific secrets if needed
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared infrastructure
        self._import_shared_resources()
        
        # Create tool Lambda
        self._create_db_interface_lambda()
        
        # Register tools in DynamoDB registry using BaseToolConstruct
        self._register_tools_using_base_construct()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import tool registry table name and ARN
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        
        # Note: Removed shared LLM layer import as db-interface doesn't use it

    def _create_db_interface_lambda(self):
        """Create the db-interface Lambda function with consistent naming"""
        
        # Generate consistent function name
        function_name = NamingConventions.tool_lambda_name("db-interface", self.env_name)
        
        # Create execution role
        lambda_role = iam.Role(
            self,
            "DBInterfaceLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant X-Ray permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        # Store function name for external reference (e.g., monitoring)
        self.function_name = function_name
        
        # Create the Lambda function
        self.db_interface_lambda = _lambda_python.PythonFunction(
            self,
            "DBInterfaceLambda",
            function_name=function_name,
            description="Database interface tool - provides get_db_schema and execute_sql_query",
            entry="lambda/tools/db-interface",
            index="index.py",
            handler="lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(30),
            memory_size=256,
            architecture=_lambda.Architecture.ARM_64,
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "ENVIRONMENT": self.env_name,
                "POWERTOOLS_SERVICE_NAME": "db-interface-tool",
                "POWERTOOLS_LOG_LEVEL": "INFO"
            }
        )
        
        # Apply removal policy to help with stack destruction
        self.db_interface_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

    def _register_tools_using_base_construct(self):
        """Register database tools using BaseToolConstruct with self-contained definitions"""
        
        # Define tool specifications with self-contained definitions
        tool_specs = [
            {
                "tool_name": "get_db_schema",
                "description": "Get the database schema including table structures and column information",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "language": "python",
                "tags": ["database", "schema", "sql"],
                "author": "system",
                "human_approval_required": False,
                "lambda_arn": self.db_interface_lambda.function_arn,
                "lambda_function_name": self.db_interface_lambda.function_name
            },
            {
                "tool_name": "execute_sql_query",
                "description": "Execute SQL queries against the database and return results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute"
                        }
                    },
                    "required": ["query"]
                },
                "language": "python",
                "tags": ["database", "sql", "query"],
                "author": "system",
                "human_approval_required": False,
                "lambda_arn": self.db_interface_lambda.function_arn,
                "lambda_function_name": self.db_interface_lambda.function_name
            }
        ]
        
        # Use BaseToolConstruct for registration
        BaseToolConstruct(
            self,
            "DatabaseTools",
            tool_specs=tool_specs,
            lambda_function=self.db_interface_lambda,
            env_name=self.env_name
        )

        # Store Lambda function reference for monitoring
        self.database_lambda_function = self.db_interface_lambda
        
        # Create CloudFormation exports
        self._create_stack_exports()
    
    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export DB Interface Lambda ARN
        CfnOutput(
            self,
            "DBInterfaceLambdaArn",
            value=self.db_interface_lambda.function_arn,
            export_name=f"DBInterfaceLambdaArn-{self.env_name}",
            description="ARN of the DB Interface Lambda function"
        )