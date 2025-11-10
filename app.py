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
from stacks.shared.mcp_registry_stack import MCPRegistryStack
from stacks.shared.test_events_stack import TestEventsStack
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
from stacks.tools.nova_act_browser_tool_stack import NovaActBrowserToolStack
from stacks.tools.agentcore_browser_tool_stack import AgentCoreBrowserToolStack
from stacks.tools.browser_remote_tool_stack import BrowserRemoteToolStack
from stacks.tools.address_search_batch_tool_stack import AddressSearchBatchToolStack
from stacks.mcp.agentcore_browser_runtime_stack import AgentCoreBrowserRuntimeStack
from stacks.tools.batch_processor_tool_stack import BatchProcessorToolStack
from stacks.agents.sql_agent_with_base_construct import SQLAgentStack
from stacks.agents.batch_orchestrator_agent_stack import BatchOrchestratorAgentStack
from stacks.agents.google_maps_agent_stack import GoogleMapsAgentStack
from stacks.agents.research_agent_stack import ResearchAgentStack
from stacks.agents.cloudwatch_agent_stack import CloudWatchAgentStack
from stacks.agents.graphql_agent_stack import GraphQLAgentStack
from stacks.agents.image_analysis_agent_stack import ImageAnalysisAgentStack
from stacks.agents.test_sql_approval_agent_stack import TestSQLApprovalAgentStack
from stacks.agents.test_automation_remote_agent_stack import TestAutomationRemoteAgentStack
from stacks.agents.sql_agent_unified_llm_stack import SQLAgentUnifiedLLMStack
from stacks.agents.web_research_agent_unified_llm_stack import WebResearchAgentUnifiedLLMStack
from stacks.agents.web_search_agent_unified_llm_stack import WebSearchAgentUnifiedLLMStack
from stacks.agents.google_maps_agent_unified_llm_stack import GoogleMapsAgentUnifiedLLMStack
from stacks.agents.test_automation_remote_agent_unified_llm_stack import TestAutomationRemoteAgentUnifiedLLMStack
from stacks.agents.browser_automation_agent_unified_llm_stack import BrowserAutomationAgentUnifiedLLMStack
from stacks.agents.broadband_agent_unified_llm_stack import BroadbandAgentUnifiedLLMStack
from stacks.agents.broadband_checker_structured_stack import BroadbandCheckerStructuredStack
from stacks.agents.broadband_availability_bt_wholesale_stack import BroadbandAvailabilityBtWholesaleStack
from stacks.agents.travel_time_checker_structured_stack import TravelTimeCheckerStructuredStack
from stacks.agents.browser_automation_structured_stack import BrowserAutomationStructuredStack
from stacks.shared.structured_output_infrastructure_stack import StructuredOutputInfrastructureStack
# from legacy.step_functions_agent.agent_monitoring_stack import AgentMonitoringStack  # Commented out due to missing dependency

# Long content support imports
from stacks.shared.shared_long_content_infrastructure_stack import SharedLongContentInfrastructureStack
from stacks.shared.shared_unified_rust_llm_long_content_stack import SharedUnifiedRustLLMWithLongContentStack
from stacks.tools.microsoft_graph_long_content_tool_stack import MicrosoftGraphLongContentToolStack
from stacks.agents.test_automation_remote_agent_rust_long_content_stack import TestAutomationRemoteAgentRustLongContentStack

# MCP Server stacks
from stacks.mcp.reinvent_mcp_stack import ReinventMcpStack
from stacks.mcp.wikipedia_mcp_stack import WikipediaMcpStack


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

    # Deploy Structured Output Infrastructure stack
    # This creates Lambda functions for structured output handling
    structured_output_infrastructure = StructuredOutputInfrastructureStack(
        app,
        f"StructuredOutputInfrastructureStack-{environment}",
        agent_registry_table=agent_registry_stack.agent_registry_table,
        env=env,
        description=f"Structured output infrastructure for {environment} environment"
    )
    structured_output_infrastructure.add_dependency(agent_registry_stack)

    # Get MCP endpoint URL from context or environment
    # This will be set by the UI Amplify deployment
    mcp_endpoint_url = os.environ.get('MCP_ENDPOINT_URL', 'https://api.example.com/mcp')
    if environment == "prod":
        # Use the production MCP endpoint from our deployment
        mcp_endpoint_url = "https://fkg9gkvzxk.execute-api.us-west-2.amazonaws.com/mcp"
    
    # Deploy MCP Registry stack
    # This creates DynamoDB table for MCP Server Registry
    mcp_registry_stack = MCPRegistryStack(
        app,
        f"MCPRegistryStack-{environment}",
        env_name=environment,
        mcp_endpoint_url=mcp_endpoint_url,
        env=env,
        description=f"MCP Server Registry for {environment} environment"
    )
    
    # Deploy Test Events stack
    # This creates DynamoDB tables for test events and results
    test_events_stack = TestEventsStack(
        app,
        f"TestEventsStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Test Events Registry for health testing in {environment} environment"
    )
    
    # Deploy MCP GraphQL API stack
    # This creates AppSync GraphQL API for MCP Registry
    from stacks.shared.mcp_graphql_stack import MCPGraphQLStack
    
    mcp_graphql_stack = MCPGraphQLStack(
        app,
        f"MCPGraphQLStack-{environment}",
        mcp_registry_table_name=mcp_registry_stack.mcp_registry_table.table_name,
        mcp_registry_table_arn=mcp_registry_stack.mcp_registry_table.table_arn,
        env_name=environment,
        env=env,
        description=f"MCP Registry GraphQL API for {environment} environment"
    )
    mcp_graphql_stack.add_dependency(mcp_registry_stack)
    
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
    db_interface_tool.add_dependency(shared_infrastructure_stack)
    
    # E2B Tool - provides Python code execution capabilities
    e2b_tool = E2BToolStack(
        app,
        f"E2BToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"E2B code execution tool for {environment} environment"
    )
    e2b_tool.add_dependency(shared_infrastructure_stack)
    e2b_tool.add_dependency(shared_llm_stack)

    # Google Maps Tool - provides location-based services
    google_maps_tool = GoogleMapsToolStack(
        app,
        f"GoogleMapsToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Google Maps tool for {environment} environment"
    )
    google_maps_tool.add_dependency(shared_infrastructure_stack)
    
    # Financial Tools - provides Yahoo Finance data analysis
    financial_tools = FinancialToolStack(
        app,
        f"FinancialToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Financial data tools for {environment} environment"
    )
    financial_tools.add_dependency(shared_infrastructure_stack)
    
    # Web Research Tools - provides AI-powered company research
    web_research_tools = WebResearchToolStack(
        app,
        f"WebResearchToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Web research tools for {environment} environment"
    )
    web_research_tools.add_dependency(shared_infrastructure_stack)
    
    # CloudWatch Tools - provides monitoring and log analysis capabilities
    cloudwatch_tools = CloudWatchToolStack(
        app,
        f"CloudWatchToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"CloudWatch monitoring tools for {environment} environment"
    )
    cloudwatch_tools.add_dependency(shared_infrastructure_stack)
    
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
    microsoft_graph_tools.add_dependency(shared_infrastructure_stack)
    
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
    
    # Nova Act Browser Tools - browser automation for web portal searches
    nova_act_browser_tools = NovaActBrowserToolStack(
        app,
        f"NovaActBrowserToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Nova Act browser automation tools for {environment} environment"
    )
    nova_act_browser_tools.add_dependency(shared_infrastructure_stack)

    # Agent Core Browser Runtime - DEPRECATED: Use manual deployment instead
    # CDK support for AWS::BedrockAgentCore::Runtime is immature and causes CloudFormation stuck states
    # Use the AgentCore starter toolkit CLI for runtime management instead
    # See docs/AGENTCORE_BROWSER_SIMPLIFIED_DEPLOYMENT.md for details
    #
    # Deployment workflow:
    # 1. Build containers: make build-agentcore-containers-codebuild
    # 2. Deploy runtimes manually: make deploy-agentcore-runtimes-manual
    # 3. Update Lambda ARNs: make update-agentcore-lambda-arns
    #
    # agentcore_browser_runtime = AgentCoreBrowserRuntimeStack(
    #     app,
    #     f"AgentCoreBrowserRuntimeStack-{environment}",
    #     env_name=environment,
    #     env=env,
    #     description=f"AgentCore runtimes for browser automation agents in {environment} environment"
    # )

    # Agent Core Browser Tools - Lambda that routes to AgentCore runtime agents
    # Runtime ARNs are now set via environment variables (updated by make update-agentcore-lambda-arns)
    # Not passed from CDK stack since runtimes are deployed manually
    agent_arns = None  # ARNs are set via Lambda environment variables

    agentcore_browser_tools = AgentCoreBrowserToolStack(
        app,
        f"AgentCoreBrowserToolStack-{environment}",
        env_name=environment,
        agent_arns=agent_arns,  # Pass agent ARNs from runtime stack
        env=env,
        description=f"Agent Core browser automation tool for {environment} environment"
    )
    agentcore_browser_tools.add_dependency(shared_infrastructure_stack)
    # Note: AgentCore runtimes are deployed separately via agentcore CLI (see Makefile)

    # Browser Remote Tool - Activity-based browser automation on local machine
    browser_remote_tool = BrowserRemoteToolStack(
        app,
        f"BrowserRemoteToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Browser remote tool (Activity pattern) for {environment} environment"
    )
    browser_remote_tool.add_dependency(shared_infrastructure_stack)

    # Address Search Batch Tool - First Step Functions-based tool for batch processing
    address_search_batch = AddressSearchBatchToolStack(
        app,
        f"AddressSearchBatchToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Address search batch processor (Step Functions tool) for {environment} environment"
    )
    address_search_batch.add_dependency(shared_infrastructure_stack)

    # Generic Batch Processor Tool - Processes CSV files through agents with structured output
    batch_processor_tool = BatchProcessorToolStack(
        app,
        f"BatchProcessorToolStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Generic batch processor for CSV files with structured output agents for {environment} environment"
    )
    batch_processor_tool.add_dependency(shared_infrastructure_stack)
    batch_processor_tool.add_dependency(agent_registry_stack)
    
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
    
    # SQL Agent with Unified Rust LLM - for side-by-side testing
    sql_agent_rust = SQLAgentUnifiedLLMStack(
        app,
        f"SQLAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"SQL agent using unified Rust LLM for {environment} environment"
    )
    
    # Web Research Agent with Unified Rust LLM - high-performance research
    web_research_agent_rust = WebResearchAgentUnifiedLLMStack(
        app,
        f"WebResearchAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Web research agent using unified Rust LLM for {environment} environment"
    )
    
    # Web Search Agent with Unified Rust LLM - Agent Core browser automation
    web_search_agent_rust = WebSearchAgentUnifiedLLMStack(
        app,
        f"WebSearchAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Web search agent using Agent Core browser automation for {environment} environment"
    )
    web_search_agent_rust.add_dependency(agentcore_browser_tools)  # Depends on Agent Core browser tool
    
    # Broadband Agent with Unified Rust LLM - UK broadband availability checking
    broadband_agent_rust = BroadbandAgentUnifiedLLMStack(
        app,
        f"BroadbandAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"UK broadband availability agent using Agent Core browser automation for {environment} environment"
    )
    broadband_agent_rust.add_dependency(agentcore_browser_tools)  # Depends on Agent Core browser tool

    # Broadband Checker with Structured Output - using unified LLM generator pattern
    broadband_checker = BroadbandCheckerStructuredStack(
        app,
        f"BroadbandCheckerStructuredStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Broadband checker with structured output using unified LLM generator for {environment} environment"
    )
    broadband_checker.add_dependency(shared_llm_stack)
    broadband_checker.add_dependency(agent_registry_stack)
    broadband_checker.add_dependency(shared_infrastructure_stack)  # For ToolRegistry
    broadband_checker.add_dependency(agentcore_browser_tools)  # For browser tool

    # BT Wholesale Broadband Availability Agent - Schema-driven with template support
    bt_wholesale_agent = BroadbandAvailabilityBtWholesaleStack(
        app,
        f"BroadbandAvailabilityBtWholesaleStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Schema-driven BT Wholesale broadband availability checker with template support for {environment} environment"
    )
    bt_wholesale_agent.add_dependency(shared_llm_stack)
    bt_wholesale_agent.add_dependency(agent_registry_stack)
    bt_wholesale_agent.add_dependency(shared_infrastructure_stack)  # For TemplateRegistry and ToolRegistry
    bt_wholesale_agent.add_dependency(browser_remote_tool)  # For browser_remote tool

    # Travel Time Checker with Structured Output - using unified LLM generator pattern
    travel_time_checker = TravelTimeCheckerStructuredStack(
        app,
        f"TravelTimeCheckerStructuredStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Travel time checker with structured output using unified LLM generator for {environment} environment"
    )
    travel_time_checker.add_dependency(shared_llm_stack)
    travel_time_checker.add_dependency(agent_registry_stack)
    travel_time_checker.add_dependency(shared_infrastructure_stack)  # For ToolRegistry
    travel_time_checker.add_dependency(google_maps_tool)  # For maps_directions tool

    # Google Maps Agent with Unified Rust LLM - location services
    google_maps_agent_rust = GoogleMapsAgentUnifiedLLMStack(
        app,
        f"GoogleMapsAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Google Maps agent using unified Rust LLM for {environment} environment"
    )
    
    # Test Automation Remote Agent with Unified Rust LLM - automation and integration
    test_automation_agent_rust = TestAutomationRemoteAgentUnifiedLLMStack(
        app,
        f"TestAutomationRemoteAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Test automation agent with remote execution using unified Rust LLM for {environment} environment"
    )

    # Browser Automation Agent with Unified Rust LLM - Nova Act browser automation
    browser_automation_agent_rust = BrowserAutomationAgentUnifiedLLMStack(
        app,
        f"BrowserAutomationAgentUnifiedLLMStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Browser automation agent with Nova Act remote execution using unified Rust LLM for {environment} environment"
    )
    browser_automation_agent_rust.add_dependency(browser_remote_tool)  # Depends on browser remote tool

    # Browser Automation Agent with Structured Output - using unified LLM generator pattern
    browser_automation_structured = BrowserAutomationStructuredStack(
        app,
        f"BrowserAutomationStructuredStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Browser automation agent with structured output using unified LLM generator for {environment} environment"
    )
    browser_automation_structured.add_dependency(shared_llm_stack)
    browser_automation_structured.add_dependency(agent_registry_stack)
    browser_automation_structured.add_dependency(shared_infrastructure_stack)  # For ToolRegistry
    browser_automation_structured.add_dependency(browser_remote_tool)  # For browser remote tool

    # ==========================
    # Long Content Support Stacks
    # ==========================
    
    # Deploy long content infrastructure first (if not already deployed)
    long_content_infrastructure = SharedLongContentInfrastructureStack(
        app,
        f"SharedLongContentInfrastructureStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Shared long content infrastructure for {environment} environment"
    )
    
    # Create Unified Rust LLM with long content support as a construct within shared LLM stack
    # Note: This needs to be added to the shared LLM stack after long content infrastructure is deployed
    unified_rust_llm_long_content = SharedUnifiedRustLLMWithLongContentStack(
        shared_llm_stack,
        f"UnifiedRustLLMWithLongContent",
        env_name=environment,
        max_content_size=10000  # 10KB threshold for long content
    )
    
    # Microsoft Graph tool with long content support
    microsoft_graph_long_content = MicrosoftGraphLongContentToolStack(
        app,
        f"MicrosoftGraphLongContentToolStack-{environment}",
        env_name=environment,
        env=env,
        max_content_size=10000,
        description=f"Microsoft Graph tool with long content support for {environment} environment"
    )
    microsoft_graph_long_content.add_dependency(shared_infrastructure_stack)
    
    # Test Automation Remote Agent with Rust LLM and Long Content Support
    test_automation_remote_agent_rust_long = TestAutomationRemoteAgentRustLongContentStack(
        app,
        f"TestAutomationRemoteAgentRustLongContentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Test automation agent with Rust LLM and long content support for {environment} environment"
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
    
    # GraphQL Agent - uses Claude LLM for GraphQL schema analysis and query generation
    graphql_agent = GraphQLAgentStack(
        app,
        f"GraphQLAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"GraphQL integration and query generation agent for {environment} environment"
    )

    # Batch Orchestrator Agent - Manages batch CSV processing with structured output agents
    batch_orchestrator_agent = BatchOrchestratorAgentStack(
        app,
        f"BatchOrchestratorAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Batch processing orchestrator agent for {environment} environment"
    )
    batch_orchestrator_agent.add_dependency(batch_processor_tool)
    batch_orchestrator_agent.add_dependency(agent_registry_stack)

    # ======================================================================
    # MCP SERVERS
    # ======================================================================

    # Reinvent MCP Server - AWS re:Invent conference planning
    reinvent_mcp = ReinventMcpStack(
        app,
        f"ReinventMcpStack-{environment}",
        env_name=environment,
        enable_control_plane=True,  # Set to False for standalone deployment
        env=env,
        description=f"AWS re:Invent Conference Planner MCP Server for {environment}"
    )
    # Depends on MCP Registry for control plane integration
    reinvent_mcp.add_dependency(mcp_registry_stack)

    # Wikipedia MCP Server - Wikipedia search and reference
    wikipedia_mcp = WikipediaMcpStack(
        app,
        f"WikipediaMcpStack-{environment}",
        env_name=environment,
        enable_control_plane=True,
        env=env,
        description=f"Wikipedia Search & Reference MCP Server for {environment}"
    )
    wikipedia_mcp.add_dependency(mcp_registry_stack)

    # Image Analysis Agent - uses Gemini LLM for multimodal image analysis
    image_analysis_agent = ImageAnalysisAgentStack(
        app,
        f"ImageAnalysisAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"AI-powered image analysis and computer vision agent for {environment} environment"
    )
    
    # Test SQL Approval Agent - demonstrates human approval workflow for SQL operations
    test_sql_approval_agent = TestSQLApprovalAgentStack(
        app,
        f"TestSQLApprovalAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Test SQL agent with human approval workflow for {environment} environment"
    )
    
    # Test Automation Remote Agent - demonstrates remote execution workflow for local automation
    test_automation_remote_agent = TestAutomationRemoteAgentStack(
        app,
        f"TestAutomationRemoteAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Test automation agent with remote execution workflow for {environment} environment"
    )
    
    # Deploy monitoring stack for comprehensive observability
    # This monitors all agents, LLM functions, and tool functions
    # COMMENTED OUT due to missing dependency: cdk_monitoring_constructs
    # agent_monitoring = AgentMonitoringStack(
    #     app,
    #     f"AgentMonitoringStack-{environment}",
    #     agents=[
    #         sql_agent.state_machine_name,
    #         google_maps_agent.state_machine_name,
    #         research_agent.state_machine_name,
    #         cloudwatch_agent.state_machine_name,
    #         graphql_agent.state_machine_name,
    #         image_analysis_agent.state_machine_name,
    #         test_sql_approval_agent.state_machine_name,
    #         test_automation_remote_agent.state_machine_name,
    #         web_search_agent_rust.state_machine_name
    #     ],
    #     llm_functions=[
    #         shared_llm_stack.claude_function_name,
    #         shared_llm_stack.openai_function_name,
    #         shared_llm_stack.gemini_function_name,
    #         shared_llm_stack.bedrock_function_name
    #     ],
    #     tool_functions=[
    #         db_interface_tool.function_name,
    #         e2b_tool.execute_code_lambda.function_name,
    #         google_maps_tool.google_maps_lambda.function_name,
    #         financial_tools.financial_lambda_function.function_name,
    #         web_research_tools.go_research_lambda.function_name,
    #         cloudwatch_tools.cloudwatch_lambda_function.function_name,
    #         clustering_tools.hdbscan_clustering_lambda.function_name,
    #         stock_analysis_tools.stock_analysis_lambda.function_name,
    #         earthquake_monitoring_tools.earthquake_query_lambda.function_name,
    #         book_recommendation_tools.book_recommendation_lambda.function_name,
    #         local_automation_tools.local_automation_lambda.function_name,
    #         microsoft_graph_tools.microsoft_graph_lambda.function_name,
    #         web_automation_tools.web_scraper_lambda.function_name,
    #         graphql_interface_tools.graphql_interface_lambda.function_name,
    #         image_analysis_tools.image_analysis_lambda.function_name,
    #         nova_act_browser_tools.nova_act_browser_lambda.function_name,
    #         agentcore_browser_tools.agentcore_browser_lambda.function_name
    #     ],
    #     log_group_name=sql_agent.log_group.log_group_name,
    #     env=env,
    #     description=f"Comprehensive monitoring dashboard for AI agents in {environment} environment"
    # )
    
    # Add explicit dependencies to ensure proper deployment order
    
    # Agent stacks need Agent Registry to be deployed first
    sql_agent.add_dependency(agent_registry_stack)
    google_maps_agent.add_dependency(agent_registry_stack)
    research_agent.add_dependency(agent_registry_stack)
    cloudwatch_agent.add_dependency(agent_registry_stack)
    graphql_agent.add_dependency(agent_registry_stack)
    image_analysis_agent.add_dependency(agent_registry_stack)
    web_search_agent_rust.add_dependency(agent_registry_stack)
    
    # Research agent needs financial and web research tools
    research_agent.add_dependency(financial_tools)
    research_agent.add_dependency(web_research_tools)
    
    # CloudWatch agent needs CloudWatch tools
    cloudwatch_agent.add_dependency(cloudwatch_tools)
    
    # GraphQL agent needs GraphQL interface tools
    graphql_agent.add_dependency(graphql_interface_tools)
    
    # Image analysis agent needs image analysis tools
    image_analysis_agent.add_dependency(image_analysis_tools)
    
    # Test SQL approval agent needs Agent Registry and DB Interface tools
    test_sql_approval_agent.add_dependency(agent_registry_stack)
    test_sql_approval_agent.add_dependency(db_interface_tool)
    test_sql_approval_agent.add_dependency(e2b_tool)
    
    # Test automation remote agent needs Agent Registry and Local Automation tools
    test_automation_remote_agent.add_dependency(agent_registry_stack)
    test_automation_remote_agent.add_dependency(local_automation_tools)
    
    # Long content stacks dependencies
    # Unified Rust LLM with long content needs long content infrastructure
    unified_rust_llm_long_content.node.add_dependency(long_content_infrastructure)
    
    # Microsoft Graph with long content needs long content infrastructure
    microsoft_graph_long_content.add_dependency(long_content_infrastructure)
    
    # Test automation agent with long content needs all its dependencies
    test_automation_remote_agent_rust_long.add_dependency(long_content_infrastructure)
    test_automation_remote_agent_rust_long.add_dependency(shared_llm_stack)  # For the unified Rust LLM construct
    test_automation_remote_agent_rust_long.add_dependency(microsoft_graph_long_content)
    test_automation_remote_agent_rust_long.add_dependency(local_automation_tools)
    test_automation_remote_agent_rust_long.add_dependency(agent_registry_stack)
    
    # Monitoring stack needs all agents and tools to be deployed first
    # COMMENTED OUT due to monitoring stack being disabled
    # agent_monitoring.add_dependency(sql_agent)
    # agent_monitoring.add_dependency(google_maps_agent)
    # agent_monitoring.add_dependency(research_agent)
    # agent_monitoring.add_dependency(cloudwatch_agent)
    # agent_monitoring.add_dependency(graphql_agent)
    # agent_monitoring.add_dependency(image_analysis_agent)
    # agent_monitoring.add_dependency(test_sql_approval_agent)
    # agent_monitoring.add_dependency(test_automation_remote_agent)
    # agent_monitoring.add_dependency(shared_llm_stack)
    
    # Add tags to all stacks
    tags = {
        "Environment": environment,
        "Project": "StepFunctionsAgent",
        "Architecture": "Refactored"
    }
    
    for stack in [shared_infrastructure_stack, shared_llm_stack, agent_registry_stack,
                  structured_output_infrastructure, db_interface_tool, e2b_tool, google_maps_tool, financial_tools,
                  web_research_tools, cloudwatch_tools, clustering_tools, stock_analysis_tools,
                  earthquake_monitoring_tools, book_recommendation_tools, local_automation_tools,
                  microsoft_graph_tools, web_automation_tools, graphql_interface_tools,
                  image_analysis_tools, nova_act_browser_tools, agentcore_browser_tools,
                  browser_remote_tool,
                  sql_agent, google_maps_agent, research_agent,
                  cloudwatch_agent, graphql_agent, image_analysis_agent,
                  test_sql_approval_agent, test_automation_remote_agent, web_search_agent_rust,
                  broadband_checker, browser_automation_structured,
                  long_content_infrastructure, microsoft_graph_long_content,
                  test_automation_remote_agent_rust_long, reinvent_mcp, wikipedia_mcp]:
        for key, value in tags.items():
            cdk.Tags.of(stack).add(key, value)
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()