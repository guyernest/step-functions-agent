#!/usr/bin/env python3
"""
Minimal app just for testing SharedLLMStack changes
"""

import aws_cdk as cdk
from stacks.shared.shared_llm_stack import SharedLLMStack

app = cdk.App()

# Create SharedLLMStack for testing
shared_llm_stack = SharedLLMStack(
    app, 
    "SharedLLMStack-prod",
    env_name="prod",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or "123456789012",
        region=app.node.try_get_context("region") or "us-east-1"
    )
)

app.synth()