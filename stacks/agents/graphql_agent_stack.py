from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json
from pathlib import Path


class GraphQLAgentStack(ModularBaseAgentUnifiedLLMStack):
    """
    GraphQL Agent Stack - Uses Unified Rust LLM for simplified deployment

    This stack demonstrates the clean new architecture using the unified LLM:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses ModularBaseAgentUnifiedLLMStack for common patterns
    - Configurable tool list per agent
    - Uses Unified Rust LLM for GraphQL tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "GraphQL API specialist for schema analysis and query generation (Rust LLM)"
        self.llm_provider = "anthropic"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['graphql', 'api', 'queries', 'mutations', 'schemas', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["schema_introspection", "query_generation", "dynamic_endpoints"]
        }
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import GraphQL interface Lambda ARN
        graphql_lambda_arn = Fn.import_value(f"GraphQLInterfaceLambdaArn-{env_name}")
        
        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'graphql-interface' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ GraphQLAgent: Loaded {len(tool_names)} tool names from tool-names.json: {tool_names}")
        
        # Define tool configurations
        tool_configs = [
            {
                "tool_name": tool_name,
                "lambda_arn": graphql_lambda_arn,
                "requires_approval": False
            }
            for tool_name in tool_names
        ]
        
                
        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="graphql-agent-rust",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            default_provider="anthropic",
            default_model="claude-3-5-sonnet-20241022",
            system_prompt="""You are an expert GraphQL assistant with deep knowledge of GraphQL schemas, queries, mutations, and subscriptions.

You have access to multiple GraphQL endpoints through dynamic endpoint selection. Each endpoint is identified by a unique ID (e.g., 'LogisticZ', 'CustomerService').

When working with GraphQL:
1. First use get_graphql_schema to fetch the schema for the specific GraphQL endpoint using its ID
2. Use generate_query_prompt to help construct complex queries based on the schema
3. Use execute_graphql_query to execute queries against the specific endpoint

Important: Always specify the graphql_id parameter to identify which GraphQL endpoint to connect to. Ask the user for the endpoint ID if not provided.

Available tools:
- get_graphql_schema: Fetch schema for a specific endpoint
- generate_query_prompt: Generate query prompts with schema awareness
- execute_graphql_query: Execute GraphQL queries on a specific endpoint""",
            **kwargs
        )
        

        # Store env_name for registration
        self.env_name = env_name