# Modular Architecture Design

This document explains the modular architecture approach that eliminates centralized code dependencies when adding new tools and agents.

## Problem with Centralized Approach

### Before: Centralized Tool Registry
```python
# Bad: Every new tool requires updating centralized code
class AllTools:
    TOOL_REGISTRY = {
        "get_db_schema": ToolDefinition(...),
        "execute_sql_query": ToolDefinition(...),
        "new_tool": ToolDefinition(...)  # ← Must update this for every new tool
    }
```

### Issues:
1. **Breaks Modularity**: Adding a new tool requires modifying central files
2. **Deployment Dependencies**: All agents depend on centralized tool definitions
3. **Version Conflicts**: Updates to central registry affect all agents
4. **Team Conflicts**: Multiple teams can't independently deploy tools

## Solution: Modular Architecture

### Dynamic Tool Resolution
```python
# Good: Tools resolved dynamically from DynamoDB at runtime
tool_configs = [
    {
        "tool_name": "any_tool_name",  # Must exist in DynamoDB registry
        "lambda_arn": "arn:aws:lambda:...",
        "requires_activity": True,
        "activity_type": "human_approval"
    }
]
```

### Key Components

#### 1. ModularBaseAgentStack
```python
class ModularBaseAgentStack(Stack):
    """
    Truly modular agent deployment without centralized dependencies
    - No centralized tool registry dependencies at deploy time
    - Tools are resolved dynamically from DynamoDB at runtime
    - Agents can be deployed independently without updating central code
    """
    
    def __init__(self, ..., validate_tools: bool = False):
        # validate_tools=False by default for full modularity
        # Tools are validated at runtime from DynamoDB
```

#### 2. Tool Stack Self-Registration
```python
# Each tool stack registers itself in DynamoDB
MultiToolConstruct(
    self,
    "LocalAutomationToolsRegistry",
    tool_groups=[{
        "tool_specs": [
            {
                "tool_name": "local_agent_execute",
                "description": "Execute automation scripts on remote local systems",
                "requires_activity": True,
                "activity_type": "remote_execution",
                "activity_arn": self.remote_execution_activity_arn
            }
        ],
        "lambda_function": self.local_automation_lambda
    }],
    env_name=self.env_name
)
```

#### 3. Runtime Tool Discovery
{% raw %}
```python
# Step Functions loads tools dynamically from DynamoDB
"Load Tool Definitions": {
    "Type": "Map",
    "Items": "{% $parse($agent_config.tools.S) %}",
    "ItemProcessor": {
        "StartAt": "Get Tool Details",
        "States": {
            "Get Tool Details": {
                "Type": "Task",
                "Resource": "arn:aws:states:::dynamodb:getItem",
                "Arguments": {
                    "TableName": tool_registry_table_name,
                    "Key": {
                        "tool_name": {"S": "{% $states.input.tool_name %}"}
                    }
                }
            }
        }
    }
}
```
{% endraw %}

## Benefits of Modular Architecture

### 1. **True Independence**
- Deploy tools without updating any central code
- Deploy agents without dependency conflicts
- Teams can work independently

### 2. **Runtime Flexibility**
- Tools are discovered dynamically at execution time
- No compile-time dependencies on tool definitions
- Support for any tool registered in DynamoDB

### 3. **Scalable Team Development**
```bash
# Team A deploys their tool
cdk deploy CustomAnalyticsToolStack-prod

# Team B deploys their agent using Team A's tool
# (without needing to coordinate code changes)
cdk deploy CustomAgentStack-prod
```

### 4. **Version Independence**
- Tool updates don't affect agent deployments
- Agent updates don't require tool redeployments
- Independent versioning and rollback capabilities

## Migration Guide

### From Centralized to Modular

#### Before (Centralized)
```python
class SQLAgentStack(BaseAgentStack):
    def __init__(self, ...):
        # Validates against centralized AllTools registry
        tool_names = [config["tool_name"] for config in tool_configs]
        invalid_tools = AllTools.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"Invalid tools: {invalid_tools}")
```

#### After (Modular)
```python
class SQLAgentStack(ModularBaseAgentStack):
    def __init__(self, ...):
        # No centralized validation - tools resolved from DynamoDB
        print(f"Using tools: {[config['tool_name'] for config in tool_configs]}")
        
        super().__init__(
            # ... other parameters
            validate_tools=False  # Disable centralized validation
        )
```

### Tool Registration Pattern
```python
# Each tool stack registers itself
class CustomToolStack(Stack):
    def __init__(self, ...):
        # 1. Create Lambda function
        self.custom_lambda = lambda_.Function(...)
        
        # 2. Create activity if needed
        if self.requires_remote_execution:
            self.remote_activity = sfn.Activity(...)
        
        # 3. Self-register in DynamoDB
        MultiToolConstruct(
            self,
            "CustomToolsRegistry",
            tool_groups=[{
                "tool_specs": [{
                    "tool_name": "custom_tool",
                    "description": "Custom tool functionality",
                    "input_schema": {...},
                    "requires_activity": True,
                    "activity_type": "remote_execution",
                    "activity_arn": self.remote_activity.activity_arn
                }],
                "lambda_function": self.custom_lambda
            }]
        )
```

## Best Practices

### 1. **Tool Naming Conventions**
```python
# Use descriptive, unique tool names
"tool_name": "financial_stock_analysis"  # Good
"tool_name": "analyze"                   # Bad - too generic
```

### 2. **Activity Management**
```python
# Human approval: Agent-owned (one per agent)
approval_activity = sfn.Activity(
    self, f"{agent_name}ApprovalActivity",
    activity_name=f"{agent_name}-approval-activity-{env_name}"
)

# Remote execution: Tool-owned (one per remote tool)
remote_activity = sfn.Activity(
    self, f"{tool_name}RemoteActivity", 
    activity_name=f"{tool_name}-remote-activity-{env_name}"
)
```

### 3. **Error Handling**
```python
# Graceful handling of missing tools
try:
    # Tool execution
except ToolNotFoundError:
    return {
        "error": "Tool not available in registry",
        "available_tools": "Check DynamoDB registry"
    }
```

### 4. **Testing Strategy**
```python
# Optional validation for development
class TestAgentStack(ModularBaseAgentStack):
    def __init__(self, ...):
        super().__init__(
            # ... other parameters
            validate_tools=True  # Enable for testing/development
        )
```

## Future Enhancements

### 1. **Tool Versioning**
```python
# Support for tool versions
"tool_name": "analyze_data",
"tool_version": "v2.1.0",
"compatibility": ["v2.x", "v1.5+"]
```

### 2. **Dynamic Tool Discovery**
```python
# Runtime tool discovery and registration
"Discover Available Tools": {
    "Type": "Task",
    "Resource": "arn:aws:states:::dynamodb:scan",
    "Arguments": {
        "TableName": tool_registry_table_name,
        "FilterExpression": "attribute_exists(tool_name)"
    }
}
```

### 3. **Tool Capability Matching**
{% raw %}
```python
# Automatic tool selection based on capabilities
"Select Best Tool": {
    "Type": "Choice",
    "Choices": [
        {
            "Condition": "{% $states.input.requires_database %}",
            "Next": "Use Database Tool"
        },
        {
            "Condition": "{% $states.input.requires_computation %}",
            "Next": "Use Compute Tool"
        }
    ]
}
```
{% endraw %}

This modular architecture provides the foundation for truly independent tool and agent development while maintaining the flexibility and power of the approval workflow system.