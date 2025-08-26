"""
Web Search Agent Stack using Unified Rust LLM
Integrates Agent Core browser tool for web searches
"""

from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json


class WebSearchAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    Web Search Agent using unified Rust LLM with Agent Core browser integration
    
    This stack provides web search and information extraction capabilities:
    - Uses Agent Core browser automation for real-time web searches
    - Extracts product information, prices, availability
    - Supports multiple websites and search scenarios
    - Powered by unified Rust LLM for high performance
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Set agent-specific properties for registry
        self.agent_description = "Web search agent with Agent Core browser automation and Microsoft 365 integration (Rust LLM)"
        self.llm_provider = "anthropic"  # Using Anthropic for web search tasks
        self.llm_model = "claude-3-5-sonnet-20241022"  # Using Claude 3.5 Sonnet
        self.agent_metadata = {
            "tags": ['web-search', 'browser-automation', 'agent-core', 'product-search', 'microsoft-365', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["web_search", "price_extraction", "product_comparison", "availability_check", "email", "teams", "sharepoint"]
        }
        
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import Agent Core browser tool Lambda ARN
        agentcore_browser_lambda_arn = Fn.import_value(f"AgentCoreBrowserLambdaArn-{env_name}")
        
        # Import Microsoft Graph Lambda ARN
        microsoft_graph_lambda_arn = Fn.import_value(f"MicrosoftGraphLambdaArn-{env_name}")
        
        # Define tool configurations for web search
        tool_configs = [
            {
                "tool_name": "agentcore_browser_search",
                "lambda_arn": agentcore_browser_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "MicrosoftGraphAPI",
                "lambda_arn": microsoft_graph_lambda_arn,
                "requires_activity": False
            }
        ]
        
        # System prompt for the web search agent
        system_prompt = """You are a helpful AI assistant specializing in web searches, information extraction, and enterprise integration.

You have access to two powerful tools:

1. **agentcore_browser_search**: Advanced browser automation through Agent Core that can:
   - Search for products and information on various websites
   - Extract prices, availability, ratings, and other details
   - Compare products across different sources
   - Navigate complex web interfaces

2. **MicrosoftGraphAPI**: Integration with Microsoft 365 services for:
   - Sending emails and managing calendars
   - Accessing Teams messages and channels
   - Working with SharePoint documents
   - Managing OneDrive files

When users ask for information that requires web search:
- Use agentcore_browser_search with a clear, specific query
- The tool will use browser automation to search and extract the information
- Provide clear, concise summaries of the findings
- Include specific details like prices, availability, ratings when found

When users need Microsoft 365 integration:
- Use MicrosoftGraphAPI to interact with Office services
- You can combine web search results with Office actions (e.g., search for products then email the results)

Always be factual and cite sources. Browser automation may take 10-30 seconds to complete."""
        
        # Initialize with base class
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="web-search-agent-unified",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            default_provider="anthropic",
            default_model="claude-3-5-sonnet-20241022",
            validate_tools=False,  # Don't validate since Lambda may not exist yet
            **kwargs
        )