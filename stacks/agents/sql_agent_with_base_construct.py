from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
import json


class SQLAgentStack(ModularBaseAgentStack):
    """
    SQL Agent Stack - Uses base agent stack for simplified deployment
    
    This stack demonstrates the clean new architecture using the base stack:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses BaseAgentStack for common patterns
    - Configurable tool list per agent
    - Uses Claude LLM for SQL tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "SQL assistant with database query and Python code execution capabilities"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['sql', 'database', 'data-analysis', 'python', 'queries']
        }
        
        # Import Claude LLM ARN from shared stack
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
        # Import tool Lambda ARNs
        db_interface_lambda_arn = Fn.import_value(f"DBInterfaceLambdaArn-{env_name}")
        execute_code_lambda_arn = Fn.import_value(f"ExecuteCodeLambdaArn-{env_name}")
        
        # Define tool configurations with activity support
        tool_configs = [
            {
                "tool_name": "get_db_schema",
                "lambda_arn": db_interface_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "execute_sql_query", 
                "lambda_arn": db_interface_lambda_arn,
                "requires_activity": True,
                "activity_type": "human_approval"  # SQL queries require human approval for safety
            },
            {
                "tool_name": "execute_python",
                "lambda_arn": execute_code_lambda_arn,
                "requires_activity": True,
                "activity_type": "human_approval"  # Code execution requires human approval for security
            }
        ]
        
                
        # Call ModularBaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="sql-agent",
            llm_arn=claude_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="You are a helpful SQL assistant with access to a SQLite database and Python code execution. Help users query and understand their data. Please don't assume to know the schema of the database, and use the get_db_schema tool to learn table and column names and types before using it. You can also execute Python code for data analysis, visualization, or calculations using the execute_python tool.",
            **kwargs
        )
        