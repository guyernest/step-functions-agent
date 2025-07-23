from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
from ..shared.base_agent_construct import BaseAgentConstruct
import json


class TestSQLApprovalAgentStack(ModularBaseAgentStack):
    """
    Test SQL Agent Stack - Demonstrates human approval workflow for SQL operations
    
    This stack creates a SQL agent that requires human approval for:
    - execute_sql_query: Requires approval for data safety
    - execute_python: Requires approval for code execution security
    
    Safe operations like get_db_schema run without approval.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        # Import Claude LLM ARN from shared stack
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
        # Import tool Lambda ARNs
        db_interface_lambda_arn = Fn.import_value(f"DBInterfaceLambdaArn-{env_name}")
        execute_code_lambda_arn = Fn.import_value(f"ExecuteCodeLambdaArn-{env_name}")
        
        # Define tool configurations with human approval for sensitive operations
        tool_configs = [
            {
                "tool_name": "get_db_schema",
                "lambda_arn": db_interface_lambda_arn,
                "requires_activity": False  # Safe read-only operation
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
        
        # Skip centralized validation for modular tool deployment
        # Tools are validated dynamically from DynamoDB registry at runtime
        print(f"Using tools: {[config['tool_name'] for config in tool_configs]}")
        
        # Call BaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="test-sql-approval-agent",
            llm_arn=claude_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="""You are a helpful SQL assistant with access to a SQLite database and Python code execution. 

IMPORTANT SECURITY NOTICE: 
- SQL queries and Python code execution require human approval for safety
- Always use get_db_schema first to understand the database structure
- When your SQL query or Python code is rejected, carefully review the feedback and revise your approach
- Be patient during approval processes - a human reviewer will evaluate your request

Your capabilities:
1. get_db_schema: Examine database structure (no approval needed)
2. execute_sql_query: Run SQL queries (requires human approval)  
3. execute_python: Execute Python code for analysis/visualization (requires human approval)

Always explain what you're trying to do before requesting approval-required operations.""",
            **kwargs
        )
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this test SQL approval agent in the Agent Registry"""
        
        # Define SQL approval agent specification
        agent_spec = {
            "agent_name": "test-sql-approval-agent",
            "version": "v1.0",
            "status": "active",
            "system_prompt": """You are a SQL assistant with human approval workflow for secure database operations.

Your responsibilities:
- Analyze database schemas safely (no approval needed)
- Request human approval for SQL queries and code execution
- Handle approval rejections gracefully by revising your approach
- Explain your intentions clearly when requesting approvals

Security features:
- Human approval required for execute_sql_query
- Human approval required for execute_python  
- Safe schema exploration with get_db_schema

Always be patient and respectful during the approval process.""",
            "description": "Test SQL agent demonstrating human approval workflow for database operations",
            "llm_provider": "claude",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": [
                {"tool_name": "get_db_schema", "enabled": True, "version": "latest", "requires_approval": False},
                {"tool_name": "execute_sql_query", "enabled": True, "version": "latest", "requires_approval": True},
                {"tool_name": "execute_python", "enabled": True, "version": "latest", "requires_approval": True}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/test-sql-approval-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/TestSQLApproval",
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
                "tags": ["sql", "database", "approval", "test", "security"],
                "deployment_env": self.env_name,
                "test_scenario": "human_approval_workflow"
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "TestSQLApprovalAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )