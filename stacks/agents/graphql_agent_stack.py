from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
import json
from pathlib import Path


class GraphQLAgentStack(ModularBaseAgentStack):
    """
    GraphQL Agent Stack - Uses BaseAgentStack for simplified deployment
    
    This stack demonstrates the clean new architecture using the base stack:
    - Minimal code (~20 lines vs ~340 lines)
    - Uses BaseAgentStack for common patterns
    - Configurable tool list per agent
    - Uses Amazon Nova (Bedrock) LLM for GraphQL tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "GraphQL API specialist for schema analysis and query generation"
        self.llm_provider = "bedrock"
        self.llm_model = "amazon.nova-pro"
        self.agent_metadata = {
            "tags": ['graphql', 'api', 'queries', 'mutations', 'schemas']
        }
        # Import Bedrock (Nova) LLM ARN from shared stack
        bedrock_lambda_arn = Fn.import_value(f"SharedBedrockLambdaArn-{env_name}")
        
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
        
                
        # Call ModularBaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="graphql-agent",
            llm_arn=bedrock_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="You are an expert GraphQL assistant with deep knowledge of GraphQL schemas, queries, mutations, and subscriptions. Help users interact with GraphQL APIs by analyzing schemas, generating queries, and executing GraphQL operations. Always use the execute_graphql_query tool to execute queries against GraphQL endpoints and generate_query_prompt tool to help construct complex queries.",
            **kwargs
        )
        
        
        
        # Set agent-specific properties for registry
        self.agent_description = "GraphQL API specialist for schema analysis and query generation"
        self.llm_provider = "bedrock"
        self.llm_model = "amazon.nova-pro"
        self.agent_metadata = {
            "tags": ['graphql', 'api', 'queries', 'mutations', 'schemas']
        }# Store env_name for registration
        self.env_name = env_name