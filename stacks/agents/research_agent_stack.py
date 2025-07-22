from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.base_agent_construct import BaseAgentConstruct
from ..shared.tool_definitions import AllTools
import json


class ResearchAgentStack(BaseAgentStack):
    """
    Research Agent Stack - Uses base agent stack for simplified deployment
    
    This stack demonstrates the multi-language architecture:
    - Go tool for web research (Perplexity API)
    - Python tools for financial data (yfinance)
    - Uses OpenAI GPT LLM for research tasks (expanding LLM coverage)
    - Reduced from ~177 lines to ~25 lines (85% reduction)
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Import OpenAI GPT LLM ARN from shared stack for LLM coverage diversity
        openai_lambda_arn = Fn.import_value(f"SharedOpenAILambdaArn-{env_name}")
        
        # Import tool Lambda ARNs
        web_research_lambda_arn = Fn.import_value(f"WebResearchLambdaArn-{env_name}")
        yfinance_lambda_arn = Fn.import_value(f"YFinanceLambdaArn-{env_name}")
        
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
        
        # Validate tool names exist in centralized definitions
        tool_names = [config["tool_name"] for config in tool_configs]
        invalid_tools = AllTools.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"Research Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
        # Call BaseAgentStack constructor
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
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define Research agent specification
        agent_spec = {
            "agent_name": "research-agent",
            "version": "v1.0",
            "status": "active", 
            "system_prompt": """You are a comprehensive research assistant specializing in business intelligence and financial analysis.

Your capabilities include:
- Company research and competitive analysis
- Financial data analysis using market APIs
- Industry trends and sector analysis  
- Web research for current information
- Data synthesis and insight generation

When conducting research:
1. Start with specific company or topic research using available tools
2. Gather financial data when analyzing companies
3. Look for recent developments and news
4. Provide context and analysis, not just raw data
5. Cite your sources and explain your methodology
6. Offer actionable insights and recommendations

Always be thorough but concise, and prioritize accuracy and relevance.""",
            "description": "Business research and financial analysis agent",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "tools": [
                {"tool_name": "research_company", "enabled": True, "version": "latest"},
                {"tool_name": "top_sector_companies", "enabled": True, "version": "latest"},
                {"tool_name": "top_industry_companies", "enabled": True, "version": "latest"},
                {"tool_name": "list_industries", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/research-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/Research",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 8,
                "temperature": 0.4,
                "timeout_seconds": 600,
                "max_tokens": 8192
            },
            "metadata": {
                "created_by": "system", 
                "tags": ["research", "business", "financial", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "ResearchAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )