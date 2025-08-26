#!/usr/bin/env python3
"""
CDK App for deploying Agent Core Wrapper Stack
"""

import os
import aws_cdk as cdk
from stacks.agents.agentcore_wrapper_simple import AgentCoreWrapperSimpleStack

app = cdk.App()

# Get environment from context
env_name = app.node.try_get_context("env_name") or os.environ.get("ENV_NAME", "prod")
aws_region = app.node.try_get_context("aws_region") or os.environ.get("AWS_REGION", "us-west-2")
aws_account = app.node.try_get_context("aws_account") or os.environ.get("CDK_DEFAULT_ACCOUNT")

# Create the stack
AgentCoreWrapperSimpleStack(
    app, 
    f"AgentCoreWrapperSimpleStack-{env_name}",
    env=cdk.Environment(
        account=aws_account,
        region=aws_region
    ),
    description=f"Agent Core Wrapper for Step Functions integration ({env_name})"
)

app.synth()