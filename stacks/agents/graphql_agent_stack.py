from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import AllTools
from ..shared.base_agent_construct import BaseAgentConstruct


class GraphQLAgentStack(BaseAgentStack):
    """
    GraphQL Agent Stack - Uses BaseAgentStack for simplified deployment
    
    This stack demonstrates the clean new architecture using the base stack:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses BaseAgentStack for common patterns
    - Configurable tool list per agent
    - Uses Claude LLM for GraphQL tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Import Claude LLM ARN from shared stack
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
        # Import GraphQL interface Lambda ARN
        graphql_lambda_arn = Fn.import_value(f"GraphQLInterfaceLambdaArn-{env_name}")
        
        # Define tool configurations
        tool_configs = [
            {
                "tool_name": "execute_graphql_query",
                "lambda_arn": graphql_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "generate_query_prompt",
                "lambda_arn": graphql_lambda_arn,
                "requires_approval": False
            }
        ]
        
        # Validate tool names exist in centralized definitions
        tool_names = [config["tool_name"] for config in tool_configs]
        invalid_tools = AllTools.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"GraphQL Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
        # Call BaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="graphql-agent",
            llm_arn=claude_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="You are an expert GraphQL assistant with deep knowledge of GraphQL schemas, queries, mutations, and subscriptions. Help users interact with GraphQL APIs by analyzing schemas, generating queries, and executing GraphQL operations. Always use the execute_graphql_query tool to execute queries against GraphQL endpoints and generate_query_prompt tool to help construct complex queries.",
            **kwargs
        )
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define GraphQL agent specification
        agent_spec = {
            "agent_name": "graphql-agent",
            "version": "v1.0",
            "status": "active",
            "system_prompt": """You are an expert GraphQL assistant with comprehensive knowledge of GraphQL ecosystems and best practices.

Your primary responsibilities:
- Analyze GraphQL schemas and understand type relationships
- Generate efficient GraphQL queries, mutations, and subscriptions
- Help with query optimization and performance tuning
- Execute GraphQL operations against various endpoints
- Explain GraphQL concepts and schema designs
- Handle complex nested queries and fragments
- Work with AWS AppSync and other GraphQL services

Always use proper GraphQL syntax and follow best practices for query construction. Use the execute_graphql_query tool to execute queries and the generate_query_prompt tool to help users construct complex operations.""",
            "description": "GraphQL query generation, schema analysis, and API integration agent",
            "llm_provider": "claude",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": [
                {"tool_name": "execute_graphql_query", "enabled": True, "version": "latest"},
                {"tool_name": "generate_query_prompt", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/graphql-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/GraphQL",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 5,
                "temperature": 0.2,
                "timeout_seconds": 300,
                "max_tokens": 4096
            },
            "metadata": {
                "created_by": "system",
                "tags": ["graphql", "api", "schema", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "GraphQLAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )