#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Tags

from step_functions_agent.step_functions_sql_agent_stack import SQLAgentStack
from step_functions_agent.step_functions_test_agent_stack import TestAgentStack
from step_functions_agent.step_functions_financial_agent_stack import FinancialAgentStack
from step_functions_agent.step_functions_googlemap_agent_stack import GoogleMapAgentStack
from step_functions_agent.step_functions_clustering_agent_stack import ClusteringAgentStack
from step_functions_agent.step_functions_analysis_agent_stack import AnalysisAgentStack
from step_functions_agent.step_functions_research_agent_stack import ResearchAgentStack
from step_functions_agent.step_functions_supervisor_agent_stack import SupervisorAgentStack
from step_functions_agent.agent_ui_stack import AgentUIStack
from step_functions_agent.agent_monitoring_stack import AgentMonitoringStack
from step_functions_agent.agent_docs_stack import AgentDocsStack
from step_functions_agent.step_functions_graphql_agent_stack import GraphQLAgentStack
from step_functions_agent.step_functions_cloudwatch_agent_stack import CloudWatchAgentStack
from step_functions_agent.step_functions_books_agent_stack import BooksAgentStack
from step_functions_agent.step_functions_web_scraper_agent_stack import WebScraperAgentStack
from step_functions_agent.step_functions_image_analysis_agent_stack import ImageAnalysisAgentStack
from step_functions_agent.step_functions_earthqueke_agent_stack import EarthquakeAgentStack
from step_functions_agent.step_functions_semantic_search_agent_stack import SemanticSearchAgentStack

app = cdk.App()
sqlAgentStack = SQLAgentStack(app, "SQLAgentStack")
testAgentStack = TestAgentStack(app, "TestAgentStack")
financialAgentStack = FinancialAgentStack(app, "FinancialAgentStack")
googlemapAgentStack = GoogleMapAgentStack(app, "GoogleMapAgentStack")
clusteringAgentStack = ClusteringAgentStack(app, "ClusteringAgentStack")
analyzerAgentStack = AnalysisAgentStack(app, "AnalyzerAgentStack")
researchAgentStack = ResearchAgentStack(app, "ResearchAgentStack")
graphqlAgentStack = GraphQLAgentStack(app, "GraphQLAgentStack")
cloudWatchAgentStack = CloudWatchAgentStack(app, "CloudWatchAgentStack")
# booksAgentStack = BooksAgentStack(app, "BooksAgentStack")
webScraperAgentStack = WebScraperAgentStack(app, "WebScraperAgentStack")
imageAnalysisAgentStack = ImageAnalysisAgentStack(app, "ImageAnalysisAgentStack")
earthAgentStack = EarthquakeAgentStack(app, "EarthquakeAgentStack")
semanticSearchAgentStack = SemanticSearchAgentStack(app, "SemanticSearchAgentStack")

superviserAgentStack = SupervisorAgentStack(app, "SuperviserAgentStack")

uiStack = AgentUIStack(app, "AgentUIStack")

monitoringStack = AgentMonitoringStack(
    app, 
    "AgentMonitoringStack",
    agents= sqlAgentStack.agent_flows,
    llm_functions= sqlAgentStack.llm_functions,
    tool_functions= sqlAgentStack.tool_functions,
    log_group_name= sqlAgentStack.log_group_name
)

docsStack = AgentDocsStack(app, "AgentDocsStack")

Tags.of(app).add("application", "ai-agents")

Tags.of(sqlAgentStack).add("project", "sql-ai-agent")
Tags.of(testAgentStack).add("project", "test-ai-agent")
Tags.of(financialAgentStack).add("project", "financial-ai-agent")
Tags.of(googlemapAgentStack).add("project", "googlemap-ai-agent")
Tags.of(clusteringAgentStack).add("project", "clustering-ai-agent")
Tags.of(analyzerAgentStack).add("project", "analysis-ai-agent")
Tags.of(researchAgentStack).add("project", "research-ai-agent")
Tags.of(graphqlAgentStack).add("project", "graphql-ai-agent")
Tags.of(cloudWatchAgentStack).add("project", "cloudwatch-ai-agent")
# Tags.of(booksAgentStack).add("project", "books-ai-agent")
Tags.of(webScraperAgentStack).add("project", "web-scraper-ai-agent")
Tags.of(imageAnalysisAgentStack).add("project", "image-analysis-ai-agent")
Tags.of(earthAgentStack).add("project", "earthquake-ai-agent")
Tags.of(semanticSearchAgentStack).add("project", "semantic-search-ai-agent")

Tags.of(superviserAgentStack).add("project", "supervisor-ai-agent")

app.synth()
