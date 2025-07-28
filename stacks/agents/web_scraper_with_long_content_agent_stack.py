from aws_cdk import (
    Fn,
)
from constructs import Construct
from .flexible_long_content_agent_stack import FlexibleLongContentAgentStack
from ..shared.naming_conventions import NamingConventions
from typing import Dict, Any, List


class WebScraperWithLongContentAgentStack(FlexibleLongContentAgentStack):
    """
    Web Scraper Agent with Long Content Support
    
    Specialized agent for web scraping tasks that typically produce large outputs
    exceeding Step Functions message size limits.
    
    This agent demonstrates:
    - Using FlexibleLongContentAgentStack for large web scraping results
    - Integration with specialized web scraping tools
    - Automatic content transformation via Lambda Runtime API Proxy
    - DynamoDB storage for large scraped content
    
    Use cases:
    - Scraping large web pages with extensive content
    - Processing multiple pages in a single operation
    - Extracting large datasets from web sources
    - Document processing workflows with substantial output
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", agent_config: Dict[str, Any] = None, **kwargs) -> None:
        
        # Enhanced system prompt for web scraping tasks
        system_prompt = """You are a specialized web scraping AI assistant with access to advanced web scraping tools that can handle large content outputs.

Your capabilities include:
- Scraping large web pages and extracting comprehensive content
- Processing multiple pages in a single operation
- Handling extensive datasets from web sources
- Extracting structured data from complex web layouts

The web scraping tools you have access to automatically handle large outputs by storing them in DynamoDB when they exceed Step Functions limits. This allows you to process websites with extensive content without size restrictions.

When scraping websites:
1. Be respectful of robots.txt and website terms of service
2. Use appropriate delays between requests to avoid overwhelming servers
3. Extract relevant structured data when possible
4. Provide summaries of large content when appropriate for the user

You can confidently work with large web scraping results as the infrastructure automatically handles content storage and retrieval."""

        # Initialize with flexible configuration
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="WebScraperLongContent",
            env_name=env_name,
            agent_config=agent_config,
            system_prompt=system_prompt,
            max_content_size=10000,  # 10KB threshold for web content
            **kwargs
        )
        
        print(f"✅ Created web scraper agent with long content support for {env_name} environment")
    
    def _get_tool_configs(self) -> List[Dict[str, Any]]:
        """Get tool configurations for web scraping"""
        
        # Check if tools are provided in agent_config
        if self.agent_config and "tool_configs" in self.agent_config:
            return self.agent_config["tool_configs"]
        
        # Default tool configuration
        return [
            {
                "tool_name": "web_scraper_large",
                "lambda_arn": Fn.import_value(f"WebScraperLargeLambdaArn-{self.env_name}"),
                "requires_approval": False,
                "supports_long_content": True
            }
        ]