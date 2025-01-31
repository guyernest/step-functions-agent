#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Tags

from step_functions_agent.step_functions_sql_agent_stack import SQLAgentStack
from step_functions_agent.step_functions_financial_agent_stack import FinancialAgentStack
from step_functions_agent.step_functions_googlemap_agent_stack import GoogleMapAgentStack
from step_functions_agent.step_functions_clustering_agent_stack import ClusteringAgentStack
from step_functions_agent.step_functions_analysis_agent_stack import AnalysisAgentStack
from step_functions_agent.step_functions_research_agent_stack import ResearchAgentStack
from step_functions_agent.step_functions_supervisor_agent_stack import SupervisorAgentStack
from step_functions_agent.agent_ui_stack import AgentUIStack
from step_functions_agent.agent_monitoring_stack import AgentMonitoringStack
from step_functions_agent.step_functions_graphql_agent_stack import GraphQLAgentStack

app = cdk.App()
sqlAgentStack = SQLAgentStack(app, "SQLAgentStack")
financialAgentStack = FinancialAgentStack(app, "FinancialAgentStack")
googlemapAgentStack = GoogleMapAgentStack(app, "GoogleMapAgentStack")
clusteringAgentStack = ClusteringAgentStack(app, "ClusteringAgentStack")
analyzerAgentStack = AnalysisAgentStack(app, "AnalyzerAgentStack")
researchAgentStack = ResearchAgentStack(app, "ResearchAgentStack")
graphqlAgentStack = GraphQLAgentStack(app, "GraphQLAgentStack")

superviserAgentStack = SupervisorAgentStack(app, "SuperviserAgentStack")

uiStack = AgentUIStack(app, "AgentUIStack")

monitoringStack = AgentMonitoringStack(app, "AgentMonitoringStack")

Tags.of(app).add("application", "ai-agents")

Tags.of(sqlAgentStack).add("project", "sql-ai-agent")
Tags.of(financialAgentStack).add("project", "financial-ai-agent")
Tags.of(googlemapAgentStack).add("project", "googlemap-ai-agent")
Tags.of(clusteringAgentStack).add("project", "clustering-ai-agent")
Tags.of(analyzerAgentStack).add("project", "analysis-ai-agent")
Tags.of(researchAgentStack).add("project", "research-ai-agent")

Tags.of(graphqlAgentStack).add("project", "graphql-ai-agent")

Tags.of(superviserAgentStack).add("project", "supervisor-ai-agent")

app.synth()
