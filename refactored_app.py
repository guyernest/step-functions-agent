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
from stacks.tools.db_interface_tool_stack import DBInterfaceToolStack
from stacks.tools.e2b_tool_stack import E2BToolStack
from stacks.tools.google_maps_tool_stack import GoogleMapsToolStack
from stacks.agents.sql_agent_with_base_construct import SQLAgentStack
from stacks.agents.google_maps_agent_stack import GoogleMapsAgentStack


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
    
    # CDK automatically handles dependency order through stack references
    # No need for explicit dependencies - they're handled by imports in agent stacks
    
    # Add tags to all stacks
    tags = {
        "Environment": environment,
        "Project": "StepFunctionsAgent",
        "Architecture": "Refactored"
    }
    
    for stack in [shared_infrastructure_stack, shared_llm_stack, db_interface_tool, e2b_tool, sql_agent, google_maps_tool, google_maps_agent]:
        for key, value in tags.items():
            cdk.Tags.of(stack).add(key, value)
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()