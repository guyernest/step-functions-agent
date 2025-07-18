from aws_cdk import (
    Duration,
    Stack,
    Fn,
    CustomResource,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_stepfunctions_tasks as tasks,
    custom_resources as cr,
)
from constructs import Construct
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
        
        # Register tools in DynamoDB registry
        self._register_tools_in_registry()

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

    def _register_tools_in_registry(self):
        """Register both SQL tools in the DynamoDB registry"""
        
        # Tool specifications for both tools that use the same Lambda
        tools_specs = [
            {
                "tool_name": "get_db_schema",
                "version": "latest",
                "description": "Describe the schema of the SQLite database, including table names, and column names and types.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                },
                "lambda_arn": self.db_interface_lambda.function_arn,
                "lambda_function_name": self.db_interface_lambda.function_name,
                "language": "python",
                "tags": ["sql", "database", "schema"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "execute_sql_query", 
                "version": "latest",
                "description": "Return the query results of any valid sqlite SQL query. If the SQL query result has many rows then return only the first 5 rows.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "The sql query to execute. If the SQL query result has many rows then return only the first 5 rows."
                        }
                    },
                    "required": ["sql_query"]
                },
                "lambda_arn": self.db_interface_lambda.function_arn,
                "lambda_function_name": self.db_interface_lambda.function_name,
                "language": "python",
                "tags": ["sql", "database", "query"],
                "status": "active", 
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        # Create custom resources to register each tool
        for i, tool_spec in enumerate(tools_specs):
            self._create_tool_registration(i, tool_spec)

    def _create_tool_registration(self, index: int, tool_spec: dict):
        """Create a custom resource to register a tool in DynamoDB"""
        
        # Create role for the custom resource
        custom_resource_role = iam.Role(
            self,
            f"ToolRegistrationRole{index}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant DynamoDB permissions
        custom_resource_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem"
                ],
                resources=[self.tool_registry_table_arn]
            )
        )
        
        # Convert input_schema to JSON string for DynamoDB
        tool_spec_for_dynamo = tool_spec.copy()
        tool_spec_for_dynamo["input_schema"] = json.dumps(tool_spec["input_schema"])
        tool_spec_for_dynamo["tags"] = json.dumps(tool_spec["tags"])
        
        # Create the custom resource
        cr.AwsCustomResource(
            self,
            f"RegisterTool{index}",
            on_create=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in tool_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"tool-{tool_spec['tool_name']}-{self.env_name}")
            ),
            on_update=cr.AwsSdkCall(
                service="dynamodb", 
                action="putItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in tool_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"tool-{tool_spec['tool_name']}-{self.env_name}")
            ),
            on_delete=cr.AwsSdkCall(
                service="dynamodb",
                action="deleteItem", 
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Key": {
                        "tool_name": {"S": tool_spec["tool_name"]},
                        "version": {"S": tool_spec["version"]}
                    }
                }
            ),
            role=custom_resource_role
        )