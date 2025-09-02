from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json
from pathlib import Path


class WebResearchAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    Web Research Agent Stack with Unified Rust LLM Service
    
    This stack demonstrates web research capabilities using the unified Rust LLM service:
    - Uses the unified Rust LLM Lambda that supports multiple providers
    - Includes tools for web search, content analysis, and company research
    - Dynamically configures provider based on agent settings
    - Optimized for research and analysis tasks
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Web research agent with search, analysis, and company research capabilities (Rust LLM)"
        self.llm_provider = "openai"  # Using OpenAI for web research
        self.llm_model = "gpt-4o"  # Using GPT-4o for better research capabilities
        self.agent_metadata = {
            "tags": ['research', 'web-search', 'analysis', 'company-research', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["web_search", "content_analysis", "company_research", "market_analysis"]
        }
        
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import research tool Lambda ARNs
        web_research_lambda_arn = Fn.import_value(f"WebResearchLambdaArn-{env_name}")
        yfinance_lambda_arn = Fn.import_value(f"YFinanceLambdaArn-{env_name}")
        
        # Load tool names from Lambda's single source of truth
        web_research_tools_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'web-research' / 'tool-names.json'
        with open(web_research_tools_file, 'r') as f:
            web_research_tools = json.load(f)
        
        yfinance_tools_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'yfinance' / 'tool-names.json'
        with open(yfinance_tools_file, 'r') as f:
            yfinance_tools = json.load(f)
        
        # Only use the tools we need for research
        research_tools_needed = ["research_company", "list_industries", "top_industry_companies", "top_sector_companies"]
        
        print(f"✅ WebResearchAgentUnifiedLLM: Using tools: {research_tools_needed}")
        
        # Define tool configurations for web research (same as research_agent_stack)
        tool_configs = [
            {
                "tool_name": "research_company",  # Go tool - Perplexity web research
                "lambda_arn": web_research_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "list_industries",  # Python tool - yfinance sectors
                "lambda_arn": yfinance_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "top_industry_companies",  # Python tool - yfinance industry rankings
                "lambda_arn": yfinance_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "top_sector_companies",  # Python tool - yfinance sector rankings
                "lambda_arn": yfinance_lambda_arn,
                "requires_activity": False
            }
        ]
        
        # System prompt optimized for research tasks
        system_prompt = """You are an expert financial analyst and research assistant with specialization in comprehensive market analysis.

Your capabilities include:
- Deep company research using AI-powered web search
- Financial sector and industry analysis
- Competitive intelligence and market positioning
- Recent performance and market trends analysis

Available tools:
- research_company: Perform comprehensive web research on any company using AI search
- list_industries: Get all industries within a specific sector
- top_industry_companies: Find leading companies in specific industries  
- top_sector_companies: Identify top companies in market sectors

When conducting research:
1. Start with broad sector/industry analysis when appropriate
2. Use web research for current, qualitative insights
3. Combine multiple data sources for comprehensive analysis
4. Focus on recent developments and market positioning
5. Provide actionable insights and clear summaries

Always explain your research methodology and cite the specific tools used for transparency."""
        
        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="web-research-agent-rust",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            default_provider=self.llm_provider,
            default_model=self.llm_model,
            **kwargs
        )