from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import AllTools
from ..shared.base_agent_construct import BaseAgentConstruct
import json


class SQLAgentStack(Stack):
    """
    SQL Agent Stack - Uses base agent stack for simplified deployment
    
    This stack demonstrates the clean new architecture using the base stack:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses BaseAgentStack for common patterns
    - Configurable tool list per agent
    - Uses Claude LLM for SQL tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import Claude LLM ARN from shared stack
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
        # Define tool IDs with validation
        tool_ids = [
            "get_db_schema",
            "execute_sql_query", 
            "execute_python"
        ]
        
        # Validate tool names exist in centralized definitions
        invalid_tools = AllTools.validate_tool_names(tool_ids)
        if invalid_tools:
            raise ValueError(f"SQL Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
        # Create agent using base stack
        self.sql_agent = BaseAgentStack(
            self,
            "SQLAgent",
            agent_name="sql-agent",
            llm_arn=claude_lambda_arn,
            tool_ids=tool_ids,
            env_name=env_name,
            system_prompt="You are a helpful SQL assistant with access to a SQLite database and Python code execution. Help users query and understand their data. Please don't assume to know the schema of the database, and use the get_db_schema tool to learn table and column names and types before using it. You can also execute Python code for data analysis, visualization, or calculations using the execute_python tool."
        )
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define SQL agent specification
        agent_spec = {
            "agent_name": "sql-agent",
            "version": "v1.0",
            "status": "active",
            "system_prompt": """You are an expert SQL assistant with deep knowledge of database systems and query optimization.
                
Your primary responsibilities:
- Analyze database schemas and understand table relationships
- Write efficient, optimized SQL queries
- Explain query results clearly
- Suggest performance improvements
- Handle complex joins and aggregations

Always ensure queries are safe and follow best practices. Use the get_db_schema tool to understand the database structure before writing queries. You can also execute Python code for data analysis, visualization, or calculations using the execute_python tool.""",
            "description": "SQL query generation and database analysis agent",
            "llm_provider": "claude",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": [
                {"tool_id": "get_db_schema", "enabled": True, "version": "latest"},
                {"tool_id": "execute_sql_query", "enabled": True, "version": "latest"},
                {"tool_id": "execute_python", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/sql-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/SQL",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 5,
                "temperature": 0.3,
                "timeout_seconds": 300,
                "max_tokens": 4096
            },
            "metadata": {
                "created_by": "system",
                "tags": ["sql", "database", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "SQLAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )