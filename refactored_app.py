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
from stacks.agents.dynamic_sql_agent_stack import DynamicSQLAgentStack


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
    
    # Deploy agent stacks that reference shared resources
    # These are lightweight and focus only on Step Functions workflows
    
    # Dynamic SQL Agent - uses DynamoDB tool registry for dynamic tool loading
    dynamic_sql_agent = DynamicSQLAgentStack(
        app,
        f"DynamicSQLAgentStack-{environment}",
        env_name=environment,
        env=env,
        description=f"Dynamic SQL agent with tool registry for {environment} environment"
    )
    
    # CDK automatically handles dependency order through stack references
    # No need for explicit dependencies - they're handled by imports in agent stacks
    
    # Add tags to all stacks
    tags = {
        "Environment": environment,
        "Project": "StepFunctionsAgent",
        "Architecture": "Refactored"
    }
    
    for stack in [shared_infrastructure_stack, shared_llm_stack, db_interface_tool, dynamic_sql_agent]:
        for key, value in tags.items():
            cdk.Tags.of(stack).add(key, value)
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()