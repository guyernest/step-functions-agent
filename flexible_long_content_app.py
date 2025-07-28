#!/usr/bin/env python3
"""
Flexible Long Content Step Functions Agent App

This app supports multiple deployment scenarios:
1. STANDALONE - Deploy complete long content infrastructure from scratch
2. EXTEND - Add long content support to existing environment
3. HYBRID - Mix of creating new and importing existing resources

Configuration via context:
    cdk deploy --context mode=extend --context share_tools=true

Or via cdk.json:
{
    "context": {
        "long_content": {
            "mode": "extend",
            "share_resources": {
                "agent_registry": true,
                "tools": ["db_interface", "google_maps"]
            },
            "import_values": {
                "agent_registry_table": "tool-registry-prod"
            }
        }
    }
}
"""

import os
import aws_cdk as cdk
from typing import Dict, Any, Optional
from stacks.shared.lambda_extension_layer_stack import LambdaExtensionLayerStack
from stacks.shared.flexible_long_content_infrastructure_stack import FlexibleLongContentInfrastructureStack
from stacks.shared.shared_llm_with_long_content_stack import SharedLLMWithLongContentStack
from stacks.tools.web_scraper_with_long_content_tool_stack import WebScraperWithLongContentToolStack
from stacks.tools.sql_with_long_content_tool_stack import SqlWithLongContentToolStack
from stacks.agents.flexible_long_content_agent_stack import FlexibleLongContentAgentStack


def get_deployment_config(app: cdk.App) -> Dict[str, Any]:
    """
    Get deployment configuration from context or environment
    
    Priority order:
    1. Command line context (--context)
    2. cdk.json context
    3. Environment variables
    4. Default values
    """
    
    # Start with defaults
    config = {
        "mode": "standalone",  # standalone, extend, hybrid
        "environment": "dev",
        "share_resources": {
            "agent_registry": False,
            "tools": [],
            "llm": False
        },
        "import_values": {},
        "create_examples": True
    }
    
    # Check for long_content configuration in context
    long_content_config = app.node.try_get_context("long_content")
    if long_content_config:
        config.update(long_content_config)
    
    # Override with individual context values
    mode = app.node.try_get_context("mode")
    if mode:
        config["mode"] = mode
    
    # Override with environment variables
    if os.environ.get("LONG_CONTENT_MODE"):
        config["mode"] = os.environ["LONG_CONTENT_MODE"]
    
    if os.environ.get("LONG_CONTENT_ENV"):
        config["environment"] = os.environ["LONG_CONTENT_ENV"]
    
    return config


def create_infrastructure_config(mode: str, share_resources: Dict[str, Any]) -> Dict[str, Any]:
    """Create infrastructure stack configuration based on deployment mode"""
    
    if mode == "standalone":
        return {
            "mode": "create",
            "resources": {
                "content_table": "create",
                "proxy_layers": "create"
            }
        }
    elif mode == "extend":
        return {
            "mode": "hybrid",
            "resources": {
                "content_table": "create",  # Always create new content table
                "proxy_layers": "create",   # Always create new layers
                "agent_registry": "import" if share_resources.get("agent_registry") else "none"
            }
        }
    else:  # hybrid
        return {
            "mode": "hybrid",
            "resources": share_resources.get("resources", {})
        }


def main():
    """Main deployment function"""
    
    # Create CDK app
    app = cdk.App()
    
    # Get deployment configuration
    config = get_deployment_config(app)
    environment = config["environment"]
    mode = config["mode"]
    
    # AWS environment configuration
    env = cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
    )
    
    print(f"🚀 Deploying long content infrastructure")
    print(f"📍 Mode: {mode}")
    print(f"🌍 Environment: {environment}")
    print(f"☁️  Target: {env.account or 'default'}/{env.region or 'default'}")
    
    # Stack references for dependencies
    stacks = {}
    
    # 1. Deploy Lambda Extension Layers (always needed for long content)
    if mode == "extend" and config.get("import_values", {}).get("proxy_layers"):
        print("📥 Using existing Lambda extension layers")
        # Skip creating extension stack
        extension_layer_stack = None
    else:
        extension_layer_stack = LambdaExtensionLayerStack(
            app,
            f"LambdaExtensionLayer-{environment}",
            env_name=environment,
            env=env,
            description=f"Lambda extension layers - {environment}"
        )
        stacks["extension"] = extension_layer_stack
    
    # 2. Deploy Flexible Long Content Infrastructure
    infra_config = create_infrastructure_config(mode, config.get("share_resources", {}))
    infra_config["import_values"] = config.get("import_values", {})
    
    shared_infrastructure = FlexibleLongContentInfrastructureStack(
        app,
        f"FlexibleLongContentInfra-{environment}",
        env_name=environment,
        deployment_config=infra_config,
        env=env,
        description=f"Flexible long content infrastructure - {environment}"
    )
    if extension_layer_stack:
        shared_infrastructure.add_dependency(extension_layer_stack)
    stacks["infrastructure"] = shared_infrastructure
    
    # 3. Deploy Shared LLM with Long Content (optional)
    if not config.get("share_resources", {}).get("llm"):
        shared_llm = SharedLLMWithLongContentStack(
            app,
            f"SharedLLMWithLongContent-{environment}",
            env_name=environment,
            env=env,
            description=f"Shared LLM functions with long content support - {environment}",
            max_content_size=10000
        )
        shared_llm.add_dependency(shared_infrastructure)
        stacks["llm"] = shared_llm
    else:
        print("📥 Using existing LLM functions")
        shared_llm = None
    
    # 4. Deploy Example Tool and Agent Stacks (optional)
    if config.get("create_examples", True):
        print("\n📦 Creating example tool and agent stacks...")
        
        # Web Scraper Tools
        web_scraper_tools = WebScraperWithLongContentToolStack(
            app,
            f"WebScraperLongContentTools-{environment}",
            env_name=environment,
            env=env,
            description=f"Web scraper tools with long content support - {environment}"
        )
        web_scraper_tools.add_dependency(shared_infrastructure)
        stacks["web_scraper_tools"] = web_scraper_tools
        
        # SQL Tools
        sql_tools = SqlWithLongContentToolStack(
            app,
            f"SqlLongContentTools-{environment}",
            env_name=environment,
            env=env,
            description=f"SQL tools with long content support - {environment}"
        )
        sql_tools.add_dependency(shared_infrastructure)
        stacks["sql_tools"] = sql_tools
        
        # Example Agent using flexible configuration
        if shared_llm:
            agent_config = {
                "use_agent_registry": config.get("share_resources", {}).get("agent_registry", False),
                "import_registry_from": config.get("import_values", {}).get("agent_registry_export")
            }
            
            example_agent = FlexibleLongContentAgentStack(
                app,
                f"ExampleLongContentAgent-{environment}",
                env_name=environment,
                env=env,
                agent_name="WebScraperExample",
                agent_config=agent_config,
                description=f"Example agent with flexible long content support - {environment}"
            )
            example_agent.add_dependency(shared_llm)
            example_agent.add_dependency(web_scraper_tools)
            stacks["example_agent"] = example_agent
    
    # Add tags to all stacks
    tags = {
        "Environment": environment,
        "Project": "StepFunctionsAgent",
        "Architecture": "LongContent",
        "DeploymentMode": mode
    }
    
    for stack in stacks.values():
        if stack:
            for key, value in tags.items():
                cdk.Tags.of(stack).add(key, value)
    
    # Print deployment summary
    print("\n📋 Deployment Summary:")
    print(f"   Mode: {mode}")
    print(f"   Environment: {environment}")
    print(f"   Stacks to deploy: {len(stacks)}")
    for name, stack in stacks.items():
        if stack:
            print(f"   - {name}: {stack.stack_name}")
    
    print(f"\n🚀 Deploy with: cdk deploy --app 'python flexible_long_content_app.py' --all")
    print(f"   Or specific stack: cdk deploy --app 'python flexible_long_content_app.py' StackName")
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()