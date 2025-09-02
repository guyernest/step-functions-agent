from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
import json
from pathlib import Path


class ResearchAgentStack(ModularBaseAgentStack):
    """
    Research Agent Stack - Uses base agent stack for simplified deployment
    
    This stack demonstrates the multi-language architecture:
    - Go tool for web research (Perplexity API)
    - Python tools for financial data (yfinance)
    - Uses OpenAI GPT LLM for research tasks (expanding LLM coverage)
    - Reduced from ~177 lines to ~25 lines (85% reduction)
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Financial analyst and research assistant with market analysis expertise"
        self.llm_provider = "openai"
        self.llm_model = "gpt-4o"
        self.agent_metadata = {
            "tags": ['research', 'finance', 'markets', 'analysis', 'web-search']
        }
        # Import OpenAI GPT LLM ARN from shared stack for LLM coverage diversity
        openai_lambda_arn = Fn.import_value(f"SharedOpenAILambdaArn-{env_name}")
        
        # Import tool Lambda ARNs
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
        
        print(f"✅ ResearchAgent: Using tools: {research_tools_needed}")
        
        # Define tool configurations (mix of Go and Python tools)
        tool_configs = [
            {
                "tool_name": "research_company",  # Go tool - Perplexity web research
                "lambda_arn": web_research_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "list_industries",  # Python tool - yfinance sectors
                "lambda_arn": yfinance_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "top_industry_companies",  # Python tool - yfinance industry rankings
                "lambda_arn": yfinance_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "top_sector_companies",  # Python tool - yfinance sector rankings
                "lambda_arn": yfinance_lambda_arn,
                "requires_approval": False
            }
        ]
        
                
        # Call ModularBaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="research-agent",
            llm_arn=openai_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="""You are an expert financial analyst and research assistant with specialization in comprehensive market analysis.

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

Always explain your research methodology and cite the specific tools used for transparency.""",
            **kwargs
        )
        