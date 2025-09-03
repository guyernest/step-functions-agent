from aws_cdk import (
    Stack,
    Fn,
    CfnOutput,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    Duration,
)
from constructs import Construct
from typing import Dict, Any, Optional
from ..shared.long_content_tool_construct import LongContentToolConstruct
from ..shared.naming_conventions import NamingConventions
from .base_tool_construct_batched import BatchedToolConstruct


class SqlWithLongContentToolStack(Stack):
    """
    SQL Tools with Long Content Support
    
    This stack creates SQL tools (get_db_schema and execute_sql_query) with
    long content support by using the actual db-interface Lambda code with
    the Lambda Runtime API Proxy extension.
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        env_name: str = "prod",
        tool_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.tool_config = tool_config or {}
        self.max_content_size = 500  # 500 characters threshold for testing
        
        # Import tool registry if configured
        self._import_tool_registry()
        
        # Create the long content tool construct
        self.sql_tools_construct = LongContentToolConstruct(
            self,
            "SqlLongContentTools",
            env_name=env_name,
            max_content_size=self.max_content_size
        )
        
        # Create the tools
        self._create_tools()
        
        print(f"🗄️ Created SQL tools with long content support for {env_name} environment")

    def _import_tool_registry(self):
        """Import tool registry if configured"""
        
        if not self.tool_config.get("use_tool_registry", True):
            self.tool_registry_table = None
            return
        
        # Import from CloudFormation export
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        print(f"📋 Imported tool registry from CloudFormation exports")
    
    def _create_tools(self) -> None:
        """Create SQL tools with long content support using the actual db-interface code"""
        
        # Tool definitions matching the simple SQL agent
        get_db_schema_tool = {
            "tool_name": "get_db_schema",
            "description": "Get database schema information including tables and columns",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Optional specific table name to get schema for"
                    }
                }
            },
            "language": "python",
            "lambda_handler": "lambda_handler",
            "tags": ["database", "schema", "sql", "metadata", "long-content"],
            "status": "active",
            "human_approval_required": False
        }
        
        # Create the SQL tools Lambda with long content support using PythonFunction
        # This will automatically handle requirements.txt for pandas and other dependencies
        
        # Get long content configuration for x86_64
        long_content_config = self.sql_tools_construct._get_long_content_lambda_config(
            lambda_.Architecture.X86_64, 
            "SqlToolsFunction"
        )
        
        # Create the Lambda function using PythonFunction for dependency management
        self.sql_tools_lambda = lambda_python.PythonFunction(
            self,
            "SqlToolsFunction",
            function_name=f"sql-tools-long-content-{self.env_name}",
            description="SQL tools with long content support",
            entry="lambda/tools/db-interface",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(30),
            memory_size=256,
            architecture=lambda_.Architecture.X86_64,
            layers=long_content_config["layers"],
            environment=dict({
                "ENVIRONMENT": self.env_name,
                "POWERTOOLS_SERVICE_NAME": "db-interface-long-content",
                "POWERTOOLS_LOG_LEVEL": "INFO"
            }, **long_content_config["environment"]),
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Grant the function access to the content table
        self.sql_tools_construct._grant_content_table_access(self.sql_tools_lambda)
        
        # Note: The db-interface tool doesn't require the shared LLM layer
        # It connects directly to the database
        
        # Store tool definitions for registration
        self.get_db_schema_tool = get_db_schema_tool
        
        execute_sql_query_tool = {
            "tool_name": "execute_sql_query",
            "description": "Execute SQL query against the database",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["query"]
            },
            "language": "python",
            "lambda_handler": "lambda_handler",
            "tags": ["database", "sql", "query", "execution", "long-content"],
            "status": "active",
            "human_approval_required": False
        }
        
        self.execute_sql_query_tool = execute_sql_query_tool
        
        # Register tools in tool registry and create exports
        self._register_tools_and_create_exports()
        
        print(f"🗄️ Created SQL tools Lambda with long content support for {self.env_name} environment")
    
    def _register_tools_and_create_exports(self):
        """Register tools in tool registry and create CloudFormation exports"""
        from aws_cdk import CfnOutput
        
        # Only register if tool registry is configured
        if self.tool_config.get("use_tool_registry", True):
            # Create tool specifications for registry
            tool_specs = [
                {
                    "tool_name": "get_db_schema",
                    "description": "Get database schema information including tables and columns",
                    "input_schema": self.get_db_schema_tool["input_schema"],
                    "lambda_arn": self.sql_tools_lambda.function_arn,
                    "lambda_function_name": self.sql_tools_lambda.function_name,
                    "language": "python",
                    "human_approval_required": False,
                    "tags": self.get_db_schema_tool.get("tags", []),
                    "supports_long_content": True,
                    "max_content_size": self.max_content_size,
                    "status": "active"
                },
                {
                    "tool_name": "execute_sql_query",
                    "description": "Execute SQL query against the database",
                    "input_schema": self.execute_sql_query_tool["input_schema"],
                    "lambda_arn": self.sql_tools_lambda.function_arn,
                    "lambda_function_name": self.sql_tools_lambda.function_name,
                    "language": "python",
                    "human_approval_required": False,
                    "tags": self.execute_sql_query_tool.get("tags", []),
                    "supports_long_content": True,
                    "max_content_size": self.max_content_size,
                    "status": "active"
                }
            ]
            
            # Use BaseToolConstruct for registration
            BatchedToolConstruct(
                self,
                "SqlLongContentToolsRegistration",
                tool_specs=tool_specs,
                lambda_function=self.sql_tools_lambda,
                env_name=self.env_name
            )
            
            print(f"📋 Registered SQL long content tools in tool registry")
        
        # Export SQL tools Lambda ARN
        CfnOutput(
            self,
            "SqlToolsLambdaArnExport",
            value=self.sql_tools_lambda.function_arn,
            export_name=f"SqlToolsLongContentLambdaArn-{self.env_name}",
            description="ARN of the SQL tools Lambda function with long content support"
        )