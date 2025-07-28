# Long Content Feature - Developer Guide

## Overview

The long content feature enables Step Functions agents to handle messages that exceed the 256KB limit by storing large content in DynamoDB and using Lambda Runtime API Proxy extensions.

## Architecture Patterns

### 1. Standalone Deployment (Default)

Use `long_content_app.py` - creates everything fresh:

```python
# Everything is created new
python long_content_app.py
cdk deploy --app "python long_content_app.py" --all
```

### 2. Extending Existing Infrastructure

When you want to reuse existing resources, modify the stack files directly:

#### Example: Reusing Existing Agent Registry

```python
# In stacks/agents/your_long_content_agent_stack.py

class YourLongContentAgentStack(FlexibleLongContentAgentStack):
    def __init__(self, ...):
        # Option 1: Import by ARN (when you know the exact ARN)
        agent_config = {
            "use_agent_registry": True,
            "agent_registry_arn": "arn:aws:dynamodb:us-east-1:123456789:table/tool-registry-prod"
        }
        
        # Option 2: Import by CloudFormation export
        agent_config = {
            "use_agent_registry": True,
            "import_registry_from": "SharedTableAgentRegistry-prod"  # Export name
        }
        
        super().__init__(..., agent_config=agent_config)
```

#### Example: Reusing Existing Tools

```python
# In stacks/agents/web_scraper_with_long_content_agent_stack.py

def _get_tool_configs(self) -> List[Dict[str, Any]]:
    """Override to use existing tools"""
    
    # Import existing tool Lambda functions
    return [
        {
            "tool_name": "web_scraper",
            "lambda_arn": "arn:aws:lambda:us-east-1:123456789:function:tool-web-scraper-prod",
            "requires_approval": False,
            "supports_long_content": True
        },
        {
            "tool_name": "google_maps",
            # Import from CloudFormation export
            "lambda_arn": Fn.import_value("GoogleMapsLambdaArn-prod"),
            "requires_approval": False
        }
    ]
```

#### Example: Reusing Existing LLM Functions

```python
# In stacks/shared/shared_llm_with_long_content_stack.py

class SharedLLMWithLongContentStack(Stack):
    def __init__(self, ...):
        super().__init__(...)
        
        # Instead of creating new LLM functions, import existing ones
        self.claude_function = lambda_.Function.from_function_arn(
            self,
            "ImportedClaudeFunction",
            "arn:aws:lambda:us-east-1:123456789:function:claude-llm-prod"
        )
        
        # Add long content layer to existing function
        self.claude_function.add_layers(
            lambda_.LayerVersion.from_layer_version_arn(
                self,
                "ProxyLayer",
                self.proxy_layer_arn
            )
        )
```

## Common Reuse Patterns

### Pattern 1: Reuse Everything Except Content Table

```python
# In your app file
class MyLongContentApp:
    def __init__(self):
        # Import existing infrastructure
        self.tool_registry_table = "tool-registry-prod"
        self.agent_registry_table = "agent-registry-prod"
        self.claude_llm_arn = "arn:aws:lambda:region:account:function:claude-llm-prod"
        
        # Create only what's needed for long content
        self.content_table = self._create_content_table()
        self.proxy_layers = self._create_proxy_layers()
```

### Pattern 2: Import Specific Tools

```python
# In stacks/shared/flexible_long_content_infrastructure_stack.py

def _import_existing_tools(self):
    """Import tools we want to reuse"""
    
    # Direct imports
    self.existing_tools = {
        "db_interface": {
            "arn": "arn:aws:lambda:us-east-1:123456789:function:db-interface-prod",
            "name": "db_interface"
        },
        "google_maps": {
            "arn": Fn.import_value("GoogleMapsToolArn-prod"),
            "name": "google_maps"
        }
    }
```

### Pattern 3: Selective Layer Reuse

```python
# If you already have the extension layers deployed elsewhere
class MyInfrastructureStack(Stack):
    def __init__(self, ...):
        # Import existing layers
        self.proxy_layer_x86_arn = "arn:aws:lambda:region:account:layer:proxy-x86:1"
        self.proxy_layer_arm_arn = "arn:aws:lambda:region:account:layer:proxy-arm:1"
        
        # Skip layer creation
        self._create_content_table()  # Only create what's new
```

## Step-by-Step Extension Guide

### Step 1: Identify What to Reuse

List existing resources:
```bash
# List existing Lambda functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'tool-')].[FunctionName, FunctionArn]"

# List DynamoDB tables  
aws dynamodb list-tables

# List CloudFormation exports
aws cloudformation list-exports --query "Exports[?contains(Name, 'Tool')]"
```

### Step 2: Modify Stack Files

Example modifications:

```python
# stacks/agents/my_custom_long_content_agent.py
from typing import Dict, Any, List
from aws_cdk import Fn
from .flexible_long_content_agent_stack import FlexibleLongContentAgentStack

class MyCustomLongContentAgent(FlexibleLongContentAgentStack):
    def __init__(self, scope, construct_id, **kwargs):
        
        # Configure what to import vs create
        agent_config = {
            "use_agent_registry": True,
            "llm_arn": "arn:aws:lambda:us-east-1:123456789:function:claude-llm-prod"
        }
        
        super().__init__(
            scope, 
            construct_id,
            agent_name="MyCustomAgent",
            agent_config=agent_config,
            **kwargs
        )
    
    def _get_tool_configs(self):
        """Mix of existing and new tools"""
        return [
            {
                # Reuse existing tool
                "tool_name": "web_scraper",
                "lambda_arn": "arn:aws:lambda:us-east-1:123456789:function:web-scraper-prod",
                "supports_long_content": True
            },
            {
                # Use new long content tool
                "tool_name": "document_processor",
                "lambda_arn": Fn.import_value("DocumentProcessorLongContentArn-dev"),
                "supports_long_content": True
            }
        ]
```

### Step 3: Create Custom App

```python
# my_extended_long_content_app.py
import aws_cdk as cdk
from stacks.shared.shared_long_content_infrastructure_stack import SharedLongContentInfrastructureStack

app = cdk.App()

# Only create what you need
infra = SharedLongContentInfrastructureStack(
    app,
    "MyLongContentInfra-prod",
    env_name="prod"
)

# Your custom agent that reuses existing resources
agent = MyCustomLongContentAgent(
    app,
    "MyCustomAgent-prod",
    env_name="prod"
)

app.synth()
```

## Resource Import Reference

### DynamoDB Tables

```python
# Import by name
table = dynamodb.Table.from_table_name(self, "ImportedTable", "table-name")

# Import by ARN
table = dynamodb.Table.from_table_arn(self, "ImportedTable", "arn:aws:dynamodb:...")
```

### Lambda Functions

```python
# Import by ARN
function = lambda_.Function.from_function_arn(self, "ImportedFunction", "arn:aws:lambda:...")

# Import by name (requires constructing ARN)
function_arn = f"arn:aws:lambda:{self.region}:{self.account}:function:function-name"
function = lambda_.Function.from_function_arn(self, "ImportedFunction", function_arn)
```

### Lambda Layers

```python
# Import by ARN
layer = lambda_.LayerVersion.from_layer_version_arn(
    self, "ImportedLayer", 
    "arn:aws:lambda:region:account:layer:layer-name:version"
)
```

### Step Functions Activities

```python
# Import by ARN
activity = sfn.Activity.from_activity_arn(
    self, "ImportedActivity",
    "arn:aws:states:region:account:activity:activity-name"
)
```

## Best Practices

1. **Document Your Imports**: Add comments explaining what you're importing and why
2. **Version Control**: Track which versions of resources you're importing
3. **Environment Separation**: Use different import sources for dev/staging/prod
4. **Validation**: Add checks to ensure imported resources exist
5. **Fallback Strategy**: Consider what happens if an import fails

## Example: Complete Extension Scenario

```python
# Scenario: Add long content support to existing SQL agent

# 1. Existing resources (in production):
# - Agent Registry: agent-registry-prod
# - SQL tools: sql-query-executor-prod, db-schema-analyzer-prod  
# - Claude LLM: claude-llm-prod

# 2. New resources needed:
# - Content table for long content
# - Proxy layers
# - Enhanced SQL tools with long content support

# 3. Implementation:
class ExtendedSqlLongContentStack(FlexibleLongContentAgentStack):
    def __init__(self, scope, construct_id, **kwargs):
        
        agent_config = {
            "use_agent_registry": True,
            "agent_registry_table_name": "agent-registry-prod",
            "llm_arn": "arn:aws:lambda:us-east-1:123456789:function:claude-llm-prod"
        }
        
        super().__init__(
            scope,
            construct_id, 
            agent_name="SqlExtended",
            agent_config=agent_config,
            **kwargs
        )
    
    def _get_tool_configs(self):
        # Mix existing tools with new long-content versions
        return [
            {
                "tool_name": "sql_query_executor_v2",
                "lambda_arn": Fn.import_value("SqlQueryExecutorLongContentArn-dev"),
                "requires_activity": True,
                "activity_type": "human_approval",
                "supports_long_content": True
            },
            {
                # Reuse existing tool that doesn't need long content
                "tool_name": "db_connection_test",
                "lambda_arn": "arn:aws:lambda:us-east-1:123456789:function:db-connection-test-prod",
                "supports_long_content": False
            }
        ]
```

This approach gives developers full control while keeping the code clean and maintainable.