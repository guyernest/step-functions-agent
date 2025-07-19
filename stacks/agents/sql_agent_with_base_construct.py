from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack


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
        
        # Define tool IDs
        tool_ids = [
            "get_db_schema",
            "execute_sql_query", 
            "execute_python"
        ]
        
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