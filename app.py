#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Tags

from step_functions_sql_agent.step_functions_sql_agent_stack import SQLAgentStack
from step_functions_sql_agent.step_functions_financial_agent_stack import FinancialAgentStack

app = cdk.App()
sqlAgentStack = SQLAgentStack(app, "SQLAgentStack")
financialAgentStack = FinancialAgentStack(app, "FinancialAgentStack")

Tags.of(sqlAgentStack).add("project", "sql-ai-agent")
Tags.of(sqlAgentStack).add("application", "ai-agents")
Tags.of(financialAgentStack).add("project", "financial-ai-agent")
Tags.of(financialAgentStack).add("application", "ai-agents")

app.synth()
