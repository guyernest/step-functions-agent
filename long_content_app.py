#!/usr/bin/env python3
"""
Long Content Step Functions Agent App

This app demonstrates the parallel architecture for long content support:
- Lambda extension build infrastructure
- Shared long content infrastructure (DynamoDB, Lambda layers)
- Shared LLM stack with long content support
- Tool stacks with long content capabilities
- Agent stacks that handle large message contexts

IMPORTANT: This is an optional deployment for agents that need to handle large content.
Most agents should use the standard refactored_app.py deployment instead.
"""

import os
import aws_cdk as cdk
from stacks.shared.lambda_extension_layer_stack import LambdaExtensionLayerStack
from stacks.shared.shared_long_content_infrastructure_stack import SharedLongContentInfrastructureStack
from stacks.shared.shared_llm_with_long_content_stack import SharedLLMWithLongContentStack
from stacks.tools.web_scraper_with_long_content_tool_stack import WebScraperWithLongContentToolStack
from stacks.tools.sql_with_long_content_tool_stack import SqlWithLongContentToolStack
from stacks.agents.web_scraper_with_long_content_agent_stack import WebScraperWithLongContentAgentStack
from stacks.agents.image_analysis_with_long_content_agent_stack import ImageAnalysisWithLongContentAgentStack
from stacks.agents.sql_with_long_content_agent_stack import SqlWithLongContentAgentStack


def main():
    """
    Main deployment function for long content infrastructure
    """
    
    # Get environment from environment variable or default to 'prod'
    # Using 'prod' to match the main infrastructure deployment
    environment = os.environ.get("LONG_CONTENT_ENV", "prod")
    
    # Create CDK app
    app = cdk.App()
    
    # Get AWS environment configuration
    env = cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
    )
    
    print(f"🚀 Deploying long content infrastructure for {environment} environment")
    print(f"📍 Target: {env.account or 'default'}/{env.region or 'default'}")
    
    # 1. Deploy Lambda Extension Layer Stack
    # This builds the Rust-based Lambda Runtime API Proxy extension as Lambda layers
    extension_layer_stack = LambdaExtensionLayerStack(
        app,
        f"LambdaExtensionLayer-{environment}",
        env_name=environment,
        env=env,
        description=f"Lambda extension layers - {environment}"
    )
    
    # 2. Deploy Shared Long Content Infrastructure Stack
    # This creates DynamoDB table and imports Lambda layers
    shared_long_content_infrastructure = SharedLongContentInfrastructureStack(
        app,
        f"SharedLongContentInfrastructure-{environment}",
        env_name=environment,
        env=env,
        description=f"Shared infrastructure for long content support - {environment}"
    )
    shared_long_content_infrastructure.add_dependency(extension_layer_stack)
    
    # 3. Deploy Shared LLM Stack with Long Content Support
    # This creates LLM Lambda functions with proxy extension
    shared_llm_with_long_content = SharedLLMWithLongContentStack(
        app,
        f"SharedLLMWithLongContent-{environment}",
        env_name=environment,
        env=env,
        description=f"Shared LLM functions with long content support - {environment}",
        max_content_size=500  # 500 characters threshold for testing
    )
    shared_llm_with_long_content.add_dependency(shared_long_content_infrastructure)
    
    # 4. Deploy Tool Stacks with Long Content Support
    # These deploy tools that can handle large input/output data
    # Configure tools to use existing tool registry
    tool_config = {
        "use_tool_registry": True,  # Use existing tool registry
        "import_from_exports": True  # Import from CloudFormation exports
    }
    
    # Web Scraper Tools - for extracting large web content
    web_scraper_tools = WebScraperWithLongContentToolStack(
        app,
        f"WebScraperLongContentTools-{environment}",
        env_name=environment,
        env=env,
        tool_config=tool_config,
        description=f"Web scraper tools with long content support - {environment}"
    )
    web_scraper_tools.add_dependency(shared_long_content_infrastructure)
    
    # SQL Tools - for handling large query results
    sql_tools = SqlWithLongContentToolStack(
        app,
        f"SqlLongContentTools-{environment}",
        env_name=environment,
        env=env,
        tool_config=tool_config,
        description=f"SQL tools with long content support - {environment}"
    )
    sql_tools.add_dependency(shared_long_content_infrastructure)
    
    # 5. Deploy Agent Stacks with Long Content Support
    # These are agents that leverage the long content infrastructure
    
    # Web Scraper Agent - uses long content for large web scraping results
    web_scraper_agent = WebScraperWithLongContentAgentStack(
        app,
        f"WebScraperLongContentAgent-{environment}",
        env_name=environment,
        env=env,
        agent_config={
            "use_agent_registry": True,  # Use existing agent registry
            "import_registry_from": None  # Will use standard export name
        },
        description=f"Web scraper agent with long content support - {environment}"
    )
    web_scraper_agent.add_dependency(shared_llm_with_long_content)
    web_scraper_agent.add_dependency(web_scraper_tools)
    
    # SQL Agent - handles large database query results
    sql_agent = SqlWithLongContentAgentStack(
        app,
        f"SqlLongContentAgent-{environment}",
        env_name=environment,
        env=env,
        agent_config={
            "use_agent_registry": True,  # Use existing agent registry
            "import_registry_from": None  # Will use standard export name
        },
        description=f"SQL agent with long content support - {environment}"
    )
    sql_agent.add_dependency(shared_llm_with_long_content)
    sql_agent.add_dependency(sql_tools)
    
    # Image Analysis Agent - processes large image analysis outputs
    image_analysis_agent = ImageAnalysisWithLongContentAgentStack(
        app,
        f"ImageAnalysisLongContentAgent-{environment}",
        env_name=environment,
        env=env,
        agent_config={
            "use_agent_registry": True,  # Use existing agent registry
            "import_registry_from": None  # Will use standard export name
        },
        description=f"Image analysis agent with long content support - {environment}"
    )
    image_analysis_agent.add_dependency(shared_llm_with_long_content)
    
    # Add tags to all stacks
    tags = {
        "Environment": environment,
        "Project": "StepFunctionsAgent",
        "Architecture": "LongContent",
        "ContentSupport": "Extended"
    }
    
    for stack in [extension_layer_stack, shared_long_content_infrastructure, 
                  shared_llm_with_long_content, web_scraper_tools, sql_tools,
                  web_scraper_agent, sql_agent, image_analysis_agent]:
        for key, value in tags.items():
            cdk.Tags.of(stack).add(key, value)
    
    # Print deployment summary
    print("\n📋 Long Content Stack Summary:")
    print(f"   - Extension Layers: LambdaExtensionLayer-{environment}")
    print(f"   - Infrastructure: SharedLongContentInfrastructure-{environment}")
    print(f"   - LLM Stack: SharedLLMWithLongContent-{environment}")
    print(f"   - Tool Stacks: WebScraperLongContentTools-{environment}, SqlLongContentTools-{environment}")
    print(f"   - Agent Stacks: WebScraperLongContentAgent-{environment}, SqlLongContentAgent-{environment}, ImageAnalysisLongContentAgent-{environment}")
    print("\nDeploy with: cdk deploy --app 'python long_content_app.py' --all")
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()