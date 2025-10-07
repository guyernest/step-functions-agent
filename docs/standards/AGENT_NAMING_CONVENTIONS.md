# Agent Naming Conventions

## Overview
This document establishes clear naming conventions for agents to ensure consistency between agent definitions and registry entries.

## Agent Name Requirements

### Format
- Use **kebab-case** (lowercase with hyphens)
- Be descriptive but concise
- **ALWAYS use "-agent" suffix** for clarity and consistency

### Examples
- ✅ `sql-agent` - Good: clear and descriptive
- ✅ `google-maps-agent` - Good: describes functionality clearly
- ✅ `research-agent` - Good: clear purpose
- ❌ `sql` - Bad: too generic, unclear what type of component
- ❌ `google-maps` - Bad: could be confused with tools or other components
- ❌ `SQLAgent` - Bad: wrong case format
- ❌ `sql_agent` - Bad: should use hyphens, not underscores

## Implementation Requirements

### 1. Agent Stack Definition
In the agent stack file (e.g., `google_maps_agent_stack.py`):

```python
super().__init__(
    scope,
    construct_id,
    agent_name="google-maps-agent",  # Must match registry exactly
    llm_arn=gemini_lambda_arn,
    tool_ids=google_maps_tools,
    env_name=env_name,
    system_prompt=system_prompt,
    **kwargs
)
```

### 2. Agent Registry Entry
In `agent_registry_stack.py`, the agent name must match exactly:

```python
{
    "agent_name": "google-maps-agent",  # Must match agent stack exactly
    "version": "v1.0",
    "status": "active",
    # ... rest of configuration
}
```

### 3. Step Functions Template
The template will use the agent name from the agent stack to look up the registry:

```json
"Key": {
    "agent_name": {"S": "google-maps-agent"},  # Must match both stack and registry
    "version": {"S": "v1.0"}
}
```

## Validation Checklist

Before deploying a new agent, verify:

- [ ] Agent name uses kebab-case format
- [ ] Agent name in stack matches registry exactly (case-sensitive)
- [ ] No redundant suffixes like "-agent"
- [ ] Name is descriptive of the agent's purpose
- [ ] Step Functions template uses correct agent name placeholder

## Current Agents

| Agent Name | Purpose | LLM Provider | Status |
|------------|---------|--------------|---------|
| `sql-agent` | Database queries and analysis | Claude | ✅ Active |
| `google-maps-agent` | Location and mapping services | Gemini | ✅ Active |
| `research-agent` | Web research and company analysis | OpenAI GPT | ✅ Active |

## Troubleshooting

### "Item not found" errors
This usually indicates a mismatch between:
- Agent stack `agent_name` parameter
- Registry entry `agent_name` field
- Step Functions lookup key

**Solution**: Ensure all three use the exact same string (case-sensitive).

### Registry updates
If you need to update an existing agent name:
1. Update the registry entry in `agent_registry_stack.py`
2. Redeploy the registry stack: `cdk deploy AgentRegistryStack-{env}`
3. Verify the agent stack uses the same name
4. Redeploy the agent stack

## Resource Naming Patterns

With agent name `my-new-agent`, resources will be named:

| Resource Type | Naming Pattern | Example |
|---------------|----------------|---------|
| Agent Name | `{purpose}-agent` | `my-new-agent` |
| Step Function | `{agent-name}-{env}` | `my-new-agent-prod` |
| Log Group | `/aws/stepfunctions/{agent-name}-{env}` | `/aws/stepfunctions/my-new-agent-prod` |
| IAM Role | `{AgentName}AgentExecutionRole` | `MyNewAgentExecutionRole` |

## Future Development

When creating new agents:
1. Choose a descriptive kebab-case name with "-agent" suffix
2. Add entry to this documentation  
3. Ensure consistency across all three components
4. Verify resource names follow the patterns above
5. Test the agent before marking as active