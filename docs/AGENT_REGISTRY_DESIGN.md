# Agent Registry Design

## Overview

The Agent Registry provides a centralized, dynamic configuration system for AI agents, enabling runtime updates to system prompts, tool configurations, and observability settings without redeployment.

## DynamoDB Schema

### Primary Table: AgentRegistry

```json
{
  "agent_name": "research-agent",              // Partition Key
  "version": "v1.0",                          // Sort Key (allows versioning)
  "status": "active",                         // active | deprecated | testing
  "system_prompt": "You are an expert financial analyst...",
  "description": "Financial research agent with web and market data capabilities",
  "llm_provider": "openai",                   // claude | openai | gemini | bedrock
  "llm_model": "gpt-4o",                      // Model identifier
  "tools": [                                   // Tool configuration
    {
      "tool_id": "research_company",
      "enabled": true,
      "version": "latest"
    },
    {
      "tool_id": "list_industries", 
      "enabled": true,
      "version": "latest"
    }
  ],
  "observability": {                          // Monitoring configuration
    "log_group": "/aws/lambda/research-agent-prod",
    "metrics_namespace": "AIAgents/Research",
    "trace_enabled": true,
    "log_level": "INFO"
  },
  "parameters": {                             // Agent-specific parameters
    "max_iterations": 5,
    "temperature": 0.7,
    "timeout_seconds": 300,
    "max_tokens": 4096
  },
  "metadata": {
    "created_at": "2025-07-19T00:00:00Z",
    "updated_at": "2025-07-19T00:00:00Z", 
    "created_by": "team@company.com",
    "tags": ["research", "financial", "production"],
    "deployment_env": "prod"
  }
}
```

### Global Secondary Indexes

1. **AgentsByStatus**: `status` (PK), `updated_at` (SK)
   - Find all active agents
   - Track deprecated agents

2. **AgentsByLLM**: `llm_provider` (PK), `agent_name` (SK)
   - Find agents by LLM provider
   - Useful for provider migration

3. **AgentsByEnvironment**: `deployment_env` (PK), `agent_name` (SK)
   - Separate dev/staging/prod agents
   - Environment-specific queries

## Step Functions Integration

### Dynamic Agent Loading Pattern

```json
{
  "Comment": "Dynamic Agent with Registry",
  "StartAt": "LoadAgentConfig",
  "States": {
    "LoadAgentConfig": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:getItem",
      "Parameters": {
        "TableName": "AgentRegistry",
        "Key": {
          "agent_name": {"S.$": "$.agent_name"},
          "version": {"S.$": "$.agent_version"}
        }
      },
      "ResultPath": "$.agent_config",
      "OutputPath": "$",
      "Next": "ParseAgentConfig"
    },
    "ParseAgentConfig": {
      "Type": "Pass",
      "Parameters": {
        "agent_name.$": "$.agent_name",
        "messages.$": "$.messages",
        "system_prompt.$": "$.agent_config.Item.system_prompt.S",
        "llm_provider.$": "$.agent_config.Item.llm_provider.S",
        "llm_model.$": "$.agent_config.Item.llm_model.S",
        "tools.$": "States.StringToJson($.agent_config.Item.tools.S)",
        "parameters.$": "States.StringToJson($.agent_config.Item.parameters.S)"
      },
      "Next": "LoadToolSpecs"
    }
  }
}
```

## API Design

### Agent Configuration API (Future Lambda/API Gateway)

```python
# Get current agent configuration
GET /agents/{agent_name}
GET /agents/{agent_name}/versions/{version}

# Update agent configuration
PUT /agents/{agent_name}
{
  "system_prompt": "Updated prompt...",
  "parameters": {
    "temperature": 0.8
  }
}

# Create new version
POST /agents/{agent_name}/versions
{
  "base_version": "v1.0",
  "changes": {
    "system_prompt": "New prompt..."
  }
}

# List all agents
GET /agents?status=active&llm_provider=openai
```

## Implementation Benefits

### 1. **Dynamic Updates**
- Change prompts without redeployment
- A/B test different configurations
- Quick rollback capabilities

### 2. **Centralized Management**
- Single source of truth for agent configs
- Consistent configuration patterns
- Audit trail of changes

### 3. **Enhanced Observability**
- Standardized logging configuration
- Metrics namespace management
- Trace configuration per agent

### 4. **Version Control**
- Track prompt evolution
- Compare agent versions
- Gradual rollout support

## Migration Strategy

### Phase 1: Registry Creation
1. Create DynamoDB table with indexes
2. Create utility functions for CRUD operations
3. Add IAM permissions for Step Functions

### Phase 2: Agent Migration
1. Start with research-agent as pilot
2. Update Step Functions to load from registry
3. Maintain backward compatibility

### Phase 3: Management Tools
1. Create CLI for agent management
2. Build simple UI for prompt editing
3. Add version comparison tools

## Security Considerations

1. **Access Control**
   - IAM policies for registry access
   - Separate read/write permissions
   - Environment isolation

2. **Audit Trail**
   - Track all configuration changes
   - Store user identity in metadata
   - Enable DynamoDB streams for history

3. **Validation**
   - Schema validation for updates
   - Tool ID verification
   - LLM model validation

## Future Enhancements

1. **Prompt Templates**
   - Reusable prompt components
   - Variable substitution
   - Template inheritance

2. **Performance Metrics**
   - Track agent performance by version
   - A/B test results storage
   - Cost tracking per configuration

3. **Integration Features**
   - Webhook notifications on changes
   - GitOps integration
   - Approval workflows for production