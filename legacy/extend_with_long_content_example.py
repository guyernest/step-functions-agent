#!/usr/bin/env python3
"""
Example: Extending Existing Infrastructure with Long Content Support

This example shows the simplest way to add long content support to an existing
Step Functions Agent deployment by directly specifying what to import.

For developers: Simply edit the resource ARNs/names below to match your environment.
"""

import os
import aws_cdk as cdk
from stacks.shared.lambda_extension_layer_stack import LambdaExtensionLayerStack
from stacks.shared.shared_long_content_infrastructure_stack import SharedLongContentInfrastructureStack
from stacks.agents.test_extended_long_content_agent_stack import TestExtendedLongContentAgentStack

# === CONFIGURATION - Edit these values for your environment ===

# What environment are we extending?
SOURCE_ENV = "prod"  # The existing environment we're importing from
TARGET_ENV = "dev"   # The new environment we're creating

# Existing resources to import (replace with your actual values)
EXISTING_RESOURCES = {
    # Existing LLM function to reuse
    "llm_arn": "arn:aws:lambda:eu-west-1:145023107515:function:shared-claude-prod",
    
    # Existing agent registry table
    "agent_registry_table": "tool-registry-prod",
    
    # Existing tools to reuse
    "tools": {
        "web_scraper": "arn:aws:lambda:eu-west-1:145023107515:function:tool-web-scraper-prod",
        "google_maps": "GoogleMapsLambdaArn-prod",  # CloudFormation export name
    },
    
    # Existing approval activity (optional)
    "approval_activity": "arn:aws:states:eu-west-1:145023107515:activity:sql-approval-prod"
}

# === END CONFIGURATION ===


def main():
    """Deploy long content support extending existing infrastructure"""
    
    # Create CDK app
    app = cdk.App()
    
    # AWS environment
    env = cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "eu-west-1")
    )
    
    print(f"🚀 Extending {SOURCE_ENV} infrastructure with long content support")
    print(f"📍 Target environment: {TARGET_ENV}")
    print(f"☁️  AWS: {env.account or 'default'}/{env.region or 'default'}")
    
    # Step 1: Create Lambda extension layers (always needed for long content)
    extension_stack = LambdaExtensionLayerStack(
        app,
        f"LambdaExtensionLayer-{TARGET_ENV}",
        env_name=TARGET_ENV,
        env=env,
        description=f"Lambda Runtime API Proxy layers for {TARGET_ENV}"
    )
    
    # Step 2: Create long content infrastructure (DynamoDB table)
    # This is always new - we don't share content tables between environments
    infra_stack = SharedLongContentInfrastructureStack(
        app,
        f"SharedLongContentInfrastructure-{TARGET_ENV}",
        env_name=TARGET_ENV,
        env=env,
        description=f"Long content storage infrastructure for {TARGET_ENV}"
    )
    infra_stack.add_dependency(extension_stack)
    
    # Step 3: Create agent that uses both existing and new resources
    test_agent = TestExtendedLongContentAgentStack(
        app,
        f"TestExtendedAgent-{TARGET_ENV}",
        env_name=TARGET_ENV,
        env=env,
        description=f"Test agent demonstrating extension pattern - {TARGET_ENV}"
    )
    test_agent.add_dependency(infra_stack)
    
    # Add tags
    tags = {
        "Environment": TARGET_ENV,
        "ExtendedFrom": SOURCE_ENV,
        "Project": "StepFunctionsAgent",
        "Feature": "LongContent"
    }
    
    for stack in [extension_stack, infra_stack, test_agent]:
        for key, value in tags.items():
            cdk.Tags.of(stack).add(key, value)
    
    # Print summary
    print("\n📋 Extension Summary:")
    print(f"✅ New resources:")
    print(f"   - Lambda extension layers")
    print(f"   - DynamoDB content table: AgentContext-{TARGET_ENV}")
    print(f"   - Test agent: TestLongContentExtension-{TARGET_ENV}")
    print(f"\n♻️  Reused resources from {SOURCE_ENV}:")
    print(f"   - LLM function: {EXISTING_RESOURCES['llm_arn'].split(':')[-1]}")
    print(f"   - Agent registry: {EXISTING_RESOURCES['agent_registry_table']}")
    print(f"   - Tools: {', '.join(EXISTING_RESOURCES['tools'].keys())}")
    
    print(f"\n🚀 Deploy with:")
    print(f"   cdk deploy --app 'python extend_with_long_content_example.py' --all")
    
    # Synthesize
    app.synth()


if __name__ == "__main__":
    main()