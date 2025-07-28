from aws_cdk import (
    Fn,
)
from constructs import Construct
from .flexible_long_content_agent_stack import FlexibleLongContentAgentStack
from typing import Dict, Any, List


class SqlWithLongContentAgentStack(FlexibleLongContentAgentStack):
    """
    SQL Agent with Long Content Support
    
    Specialized agent for SQL database operations that can handle large query results
    and comprehensive database analysis outputs.
    
    This agent demonstrates:
    - Using FlexibleLongContentAgentStack for large SQL result sets
    - Integration with SQL tools that have human approval requirements
    - Automatic content transformation for database operations
    - DynamoDB storage for extensive query results and schema analysis
    
    Use cases:
    - Executing queries that return large result sets
    - Database schema analysis and documentation
    - Data analysis workflows with substantial outputs
    - Database migration and assessment tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", agent_config: Dict[str, Any] = None, **kwargs) -> None:
        
        # Enhanced system prompt for SQL operations
        system_prompt = """You are a specialized SQL database AI assistant with access to powerful database tools that can handle large result sets and comprehensive analysis outputs.

Your capabilities include:
- Executing SQL queries against various database systems (PostgreSQL, MySQL, SQLite)
- Analyzing database schemas and generating comprehensive documentation
- Processing large query results and datasets without size limitations
- Providing detailed database analysis and optimization recommendations

The SQL tools you have access to automatically handle large outputs by storing them in DynamoDB when they exceed Step Functions limits. This allows you to work with extensive query results and comprehensive schema analysis without size restrictions.

IMPORTANT NOTES:
- Both SQL query execution and schema analysis use long content support
- Be cautious with DELETE, UPDATE, and DROP operations
- Results exceeding 500 characters will be automatically stored in DynamoDB
- Use LIMIT clauses to control result set sizes for testing
- All operations are now available without approval for testing purposes

When working with databases:
1. For query execution: Explain the query purpose and potential impact
2. Use appropriate LIMIT clauses to manage result set sizes
3. Include metadata to help understand query performance
4. For schema analysis: Provide comprehensive documentation
5. Suggest optimizations when analyzing database structures

You can confidently work with large database results as the infrastructure automatically handles content storage and retrieval for both query results and schema analysis."""

        # Initialize with flexible configuration
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="SqlLongContent",
            env_name=env_name,
            agent_config=agent_config,
            system_prompt=system_prompt,
            max_content_size=500,  # 500 characters threshold for testing
            **kwargs
        )
        
        print(f"✅ Created SQL agent with long content support for {env_name} environment")
    
    def _get_tool_configs(self) -> List[Dict[str, Any]]:
        """Get tool configurations for SQL operations"""
        
        # Check if tools are provided in agent_config
        if self.agent_config and "tool_configs" in self.agent_config:
            return self.agent_config["tool_configs"]
        
        # Default tool configuration - using simplified SQL tools
        sql_lambda_arn = Fn.import_value(f"SqlToolsLongContentLambdaArn-{self.env_name}")
        return [
            {
                "tool_name": "get_db_schema",
                "lambda_arn": sql_lambda_arn,
                "requires_activity": False,
                "supports_long_content": True
            },
            {
                "tool_name": "execute_sql_query", 
                "lambda_arn": sql_lambda_arn,
                "requires_activity": False,
                "supports_long_content": True
            }
        ]