#!/usr/bin/env python3
"""
Refactored Step Functions Agent App

This file demonstrates the new architecture with:
- Shared LLM stack deployed once
- Shared infrastructure stack with tool registry
- Agent stacks that reference shared resources
- Consistent naming conventions
- Environment-specific deployments
"""

import os
import aws_cdk as cdk
from stacks.shared.shared_llm_stack import SharedLLMStack
from stacks.shared.shared_infrastructure_stack import SharedInfrastructureStack
from stacks.shared.agent_registry_stack import AgentRegistryStack
from stacks.tools.db_interface_tool_stack import DBInterfaceToolStack
from stacks.tools.e2b_tool_stack import E2BToolStack
from stacks.tools.google_maps_tool_stack import GoogleMapsToolStack
from stacks.tools.financial_tool_stack import FinancialToolStack
from stacks.tools.web_research_tool_stack import WebResearchToolStack
from stacks.tools.cloudwatch_tool_stack import CloudWatchToolStack
from stacks.tools.clustering_tool_stack import ClusteringToolStack
from stacks.tools.stock_analysis_tool_stack import StockAnalysisToolStack
from stacks.tools.earthquake_monitoring_tool_stack import EarthquakeMonitoringToolStack
from stacks.tools.book_recommendation_tool_stack import BookRecommendationToolStack
from stacks.tools.local_automation_tool_stack import LocalAutomationToolStack
from stacks.tools.microsoft_graph_tool_stack import MicrosoftGraphToolStack
from stacks.tools.web_automation_tool_stack import WebAutomationToolStack
from stacks.tools.graphql_interface_tool_stack import GraphQLInterfaceToolStack
from stacks.tools.image_analysis_tool_stack import ImageAnalysisToolStack
from stacks.agents.sql_agent_with_base_construct import SQLAgentStack
from stacks.agents.google_maps_agent_stack import GoogleMapsAgentStack
from stacks.agents.research_agent_stack import ResearchAgentStack
from stacks.agents.cloudwatch_agent_stack import CloudWatchAgentStack


def main():
    """
    Main deployment function
    """
    
    # Get environment from environment variable or default to 'prod'
    environment = os.environ.get("ENVIRONMENT", "prod")
    
    # Create CDK app
    app = cdk.App()
    
    # Get AWS environment configuration
    env = cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
    )
    
    # Deploy shared infrastructure stack first
    # This creates the DynamoDB tool registry
    shared_infrastructure_stack = SharedInfrastructureStack(
        app,
        f"SharedInfrastructureStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Shared infrastructure components for {environment} environment"
    )
    
    # Deploy shared LLM stack
    # This creates centralized LLM Lambda functions
    shared_llm_stack = SharedLLMStack(
        app,
        f"SharedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Shared LLM functions for {environment} environment"
    )
    
    # Deploy Agent Registry stack
    # This creates DynamoDB table for dynamic agent configurations
    agent_registry_stack = AgentRegistryStack(
        app,
        f"AgentRegistryStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Agent Registry for dynamic configurations in {environment} environment"
    )
    
    # Deploy tool stacks
    # These deploy individual tool Lambda functions and register them in DynamoDB
    
    # DB Interface Tool - provides SQL schema and query tools
    db_interface_tool = DBInterfaceToolStack(
        app,
        f"DBInterfaceToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"DB interface tool for {environment} environment"
    )
    
    # E2B Tool - provides Python code execution capabilities
    e2b_tool = E2BToolStack(
        app,
        f"E2BToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"E2B code execution tool for {environment} environment"
    )
    
    # Google Maps Tool - provides location-based services
    google_maps_tool = GoogleMapsToolStack(
        app,
        f"GoogleMapsToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Google Maps tool for {environment} environment"
    )
    
    # Financial Tools - provides Yahoo Finance data analysis
    financial_tools = FinancialToolStack(
        app,
        f"FinancialToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Financial data tools for {environment} environment"
    )
    
    # Web Research Tools - provides AI-powered company research
    web_research_tools = WebResearchToolStack(
        app,
        f"WebResearchToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Web research tools for {environment} environment"
    )
    
    # CloudWatch Tools - provides monitoring and log analysis capabilities
    cloudwatch_tools = CloudWatchToolStack(
        app,
        f"CloudWatchToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"CloudWatch monitoring tools for {environment} environment"
    )
    
    # Clustering Tools - high-performance data analysis with HDBSCAN and semantic search
    clustering_tools = ClusteringToolStack(
        app,
        f"ClusteringToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"High-performance clustering and semantic search tools for {environment} environment"
    )
    
    # Stock Analysis Tools - financial time series analysis with Java Fork/Join
    stock_analysis_tools = StockAnalysisToolStack(
        app,
        f"StockAnalysisToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Stock analysis and financial time series tools for {environment} environment"
    )
    
    # Earthquake Monitoring Tools - seismic data analysis and USGS integration
    earthquake_monitoring_tools = EarthquakeMonitoringToolStack(
        app,
        f"EarthquakeMonitoringToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Earthquake monitoring and seismic data analysis tools for {environment} environment"
    )
    
    # Book Recommendation Tools - literary discovery with NYT Books API
    book_recommendation_tools = BookRecommendationToolStack(
        app,
        f"BookRecommendationToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Book recommendation and literary discovery tools for {environment} environment"
    )
    
    # Local Automation Tools - secure local command execution and RPA
    local_automation_tools = LocalAutomationToolStack(
        app,
        f"LocalAutomationToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Local automation and secure command execution tools for {environment} environment"
    )
    
    # Microsoft Graph Tools - Office 365 enterprise integration
    microsoft_graph_tools = MicrosoftGraphToolStack(
        app,
        f"MicrosoftGraphToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Microsoft Graph and Office 365 integration tools for {environment} environment"
    )
    
    # Web Automation Tools - browser automation and intelligent web scraping
    web_automation_tools = WebAutomationToolStack(
        app,
        f"WebAutomationToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Web automation and intelligent scraping tools for {environment} environment"
    )
    
    # GraphQL Interface Tools - dynamic GraphQL query execution and schema analysis
    graphql_interface_tools = GraphQLInterfaceToolStack(
        app,
        f"GraphQLInterfaceToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"GraphQL interface and dynamic query tools for {environment} environment"
    )
    
    # Image Analysis Tools - AI-powered vision and multimodal analysis
    image_analysis_tools = ImageAnalysisToolStack(
        app,
        f"ImageAnalysisToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Image analysis and AI vision tools for {environment} environment"
    )
    
    # Deploy agent stacks that reference shared resources
    # These are lightweight and focus only on Step Functions workflows
    
    # SQL Agent - uses base agent construct for simplified deployment
    sql_agent = SQLAgentStack(
        app,
        f"SQLAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"SQL agent using base construct for {environment} environment"
    )
    
    # Google Maps Agent - uses Gemini LLM with Google Maps tools
    google_maps_agent = GoogleMapsAgentStack(
        app,
        f"GoogleMapsAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Google Maps agent with Gemini LLM for {environment} environment"
    )
    
    # Research Agent - uses OpenAI LLM with Go + Python research tools
    research_agent = ResearchAgentStack(
        app,
        f"ResearchAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Research agent with multi-language tools for {environment} environment"
    )
    
    # CloudWatch Agent - uses Claude LLM for system analysis and monitoring
    cloudwatch_agent = CloudWatchAgentStack(
        app,
        f"CloudWatchAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"CloudWatch monitoring agent for {environment} environment"
    )
    
    # Add explicit dependencies to ensure proper deployment order
    
    # Agent stacks need Agent Registry to be deployed first
    sql_agent.add_dependency(agent_registry_stack)
    google_maps_agent.add_dependency(agent_registry_stack)
    research_agent.add_dependency(agent_registry_stack)
    cloudwatch_agent.add_dependency(agent_registry_stack)
    
    # Research agent needs financial and web research tools
    research_agent.add_dependency(financial_tools)
    research_agent.add_dependency(web_research_tools)
    
    # CloudWatch agent needs CloudWatch tools
    cloudwatch_agent.add_dependency(cloudwatch_tools)
    
    # Add tags to all stacks
    tags = {
        "Environment": environment,
        "Project": "StepFunctionsAgent",
        "Architecture": "Refactored"
    }
    
    for stack in [shared_infrastructure_stack, shared_llm_stack, agent_registry_stack, 
                  db_interface_tool, e2b_tool, google_maps_tool, financial_tools, 
                  web_research_tools, cloudwatch_tools, clustering_tools, stock_analysis_tools,
                  earthquake_monitoring_tools, book_recommendation_tools, local_automation_tools,
                  microsoft_graph_tools, web_automation_tools, graphql_interface_tools,
                  image_analysis_tools, sql_agent, google_maps_agent, research_agent, 
                  cloudwatch_agent]:
        for key, value in tags.items():
            cdk.Tags.of(stack).add(key, value)
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()