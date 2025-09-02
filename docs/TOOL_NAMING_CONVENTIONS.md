# Tool Naming Conventions and Registration Guidelines

## Purpose
This document establishes naming conventions for tools to ensure consistency between:
1. Tool Lambda implementations
2. Tool registry registrations
3. Agent tool references

## Critical Requirements

### 1. Tool Name Consistency
- **Tool names MUST be identical** across all three components:
  - Lambda handler (the `case` statement in the switch)
  - Tool registry registration (in the tool stack)
  - Agent tool references (in agent stacks)

### 2. Naming Format
- Use **snake_case** for tool names
- Include a **namespace prefix** when tools belong to a service family:
  - `maps_*` for Google Maps tools
  - `db_*` for database tools
  - `web_*` for web research tools
  - `aws_*` for AWS service tools

### 3. Tool Registry Validation
Before deploying:
1. Check Lambda implementation for exact tool names
2. Verify tool stack registers the same names
3. Confirm agents reference the correct names

## Examples

### Google Maps Tools (Correct)
```python
# Tool Stack Registration
tool_specs = [
    {"tool_name": "maps_geocode", ...},
    {"tool_name": "maps_directions", ...},
    {"tool_name": "maps_elevation", ...}
]

# Agent Reference
tool_configs = [
    {"tool_name": "maps_geocode", ...},
    {"tool_name": "maps_directions", ...},
    {"tool_name": "maps_elevation", ...}
]

# Lambda Implementation
switch (tool_name) {
    case "maps_geocode": ...
    case "maps_directions": ...
    case "maps_elevation": ...
}
```

## Common Pitfalls to Avoid

### ❌ Inconsistent Naming
- Tool Stack: `"geocode"`
- Agent: `"maps_geocode"`
- Lambda: `"maps_geocode"`

### ❌ Missing Tools
- Lambda implements 7 tools
- Tool Stack registers only 5 tools
- Agent expects all 7 tools

### ❌ Different Naming Styles
- Tool Stack: `"places_search"`
- Agent: `"maps_search_places"`

## Verification Checklist

When adding or modifying tools:

1. [ ] Lambda implementation defines the tool name
2. [ ] Tool stack registration uses exact same name
3. [ ] All agents referencing the tool use exact same name
4. [ ] Input schemas match between registration and implementation
5. [ ] All tools implemented in Lambda are registered
6. [ ] No extra tools are referenced that don't exist

## Tool Discovery Pattern

For self-registering tools:
1. Tools should register themselves on deployment
2. Use consistent metadata tags for discovery
3. Agents should query registry for available tools
4. Consider implementing a validation Lambda that checks name alignment

## Migration Guide

If you discover misaligned tool names:
1. Check the Lambda implementation for the authoritative name
2. Update tool registration to match
3. Update all agent references
4. Test the complete flow before deployment

## Testing

Always test tool invocation:
1. Deploy the tool stack
2. Deploy the agent stack
3. Test via the UI tool test page
4. Verify the tool name appears correctly in both registries
5. Execute a test to confirm the Lambda responds correctly