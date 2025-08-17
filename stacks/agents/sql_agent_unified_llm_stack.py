from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json


class SQLAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    SQL Agent Stack with Unified Rust LLM Service
    
    This stack demonstrates the new architecture using the unified Rust LLM service:
    - Uses the unified Rust LLM Lambda that supports multiple providers
    - Dynamically configures provider based on agent settings
    - Maintains compatibility with existing tool definitions
    - Allows side-by-side testing with the Python-based SQL agent
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "SQL assistant with database query and Python code execution capabilities (Rust LLM)"
        self.llm_provider = "openai"  # Changed to OpenAI
        self.llm_model = "gpt-4o-mini"  # Using GPT-4o-mini model
        self.agent_metadata = {
            "tags": ['sql', 'database', 'data-analysis', 'python', 'queries', 'rust-llm'],
            "llm_type": "unified-rust"
        }
        
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import tool Lambda ARNs
        db_interface_lambda_arn = Fn.import_value(f"DBInterfaceLambdaArn-{env_name}")
        execute_code_lambda_arn = Fn.import_value(f"ExecuteCodeLambdaArn-{env_name}")
        
        # Define tool configurations without approval for testing
        tool_configs = [
            {
                "tool_name": "get_db_schema",
                "lambda_arn": db_interface_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "execute_sql_query", 
                "lambda_arn": db_interface_lambda_arn,
                "requires_activity": False  # Removed approval for testing
            },
            {
                "tool_name": "execute_python",
                "lambda_arn": execute_code_lambda_arn,
                "requires_activity": False  # Removed approval for testing
            }
        ]
        
                
        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="sql-agent-rust",  # Different name to avoid conflicts
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="You are a helpful SQL assistant with access to a SQLite database and Python code execution. Help users query and understand their data. Please don't assume to know the schema of the database, and use the get_db_schema tool to learn table and column names and types before using it. You can also execute Python code for data analysis, visualization, or calculations using the execute_python tool.",
            default_provider=self.llm_provider,
            default_model=self.llm_model,
            **kwargs
        )