# Tool Definition Migration Guide

## Problem Statement

The current architecture has tool definitions centralized in `stacks/shared/tool_definitions.py` while Lambda implementations are scattered across tool directories. This separation causes:

1. **Parameter Mismatches**: Tool schema and Lambda parameters easily get out of sync
2. **Development Friction**: Tool teams must touch shared files for any changes
3. **Maintenance Burden**: Manual synchronization between schema and implementation
4. **Risk of Bugs**: Runtime failures when tool calls don't match Lambda expectations

## Solution: Decentralized Tool Ownership

Move tool definitions from the centralized file into individual tool stacks alongside their Lambda implementations.

### Benefits

1. **Single Source of Truth**: Each tool stack owns both Lambda and schema
2. **Automatic Sync**: Schema changes require Lambda changes in the same PR
3. **Independent Development**: Tool teams work in isolation
4. **Type Safety**: Compile-time validation of schema-implementation alignment
5. **Better Testing**: Tool tests validate both Lambda and schema together

## Migration Steps

### 1. Create Self-Contained Tool Stack

Replace the current pattern:

```python
# OLD: Separate files
# stacks/shared/tool_definitions.py - Contains schema
# stacks/tools/my_tool_stack.py - Contains Lambda
# lambda/tools/my-tool/ - Contains implementation
```

With the new pattern:

```python
# NEW: Single stack owns everything
from stacks.shared.base_tool_construct import BaseToolConstruct

class MyToolStackV2(BaseToolConstruct):
    def _create_tools(self):
        # 1. Create Lambda function
        self.my_lambda = _lambda.Function(...)
        
        # 2. Define schema that matches Lambda exactly
        tool_def = ToolDefinition(
            tool_name="my_tool",
            input_schema={
                # Schema MUST match Lambda parameter expectations
                "properties": {
                    "param1": {"type": "string"},  # Lambda uses input["param1"]
                    "param2": {"type": "number"}   # Lambda uses input["param2"]
                }
            }
        )
        
        # 3. Register tool (creates exports automatically)
        self._register_tool(tool_def, self.my_lambda)
```

### 2. Update Agent Stacks

Replace manual tool configuration:

```python
# OLD: Manual configuration with hard-coded ARNs
tool_configs = [
    {
        "tool_name": "my_tool",
        "lambda_arn": Fn.import_value("MyToolLambdaArn-prod"),
        "requires_approval": False
    }
]
```

With automatic discovery:

```python
# NEW: Automatic configuration from tool stack
my_tool_stack = MyToolStackV2(app, "MyToolStack", env_name="prod")
tool_configs = my_tool_stack.get_tool_configs_for_agent()
```

### 3. Update Tool Registration

Replace centralized registration:

```python
# OLD: Manual collection from centralized definitions
from stacks.shared.tool_definitions import AllTools
all_tools = AllTools.get_all_tool_definitions()
```

With distributed collection:

```python
# NEW: Automatic collection from tool stacks
from stacks.shared.base_tool_construct import ToolRegistrationMixin

tool_stacks = [google_maps_stack, db_stack, financial_stack]
all_tools = ToolRegistrationMixin.collect_tools_from_stacks(tool_stacks)
```

## Migration Example: Google Maps Tools

### Before Migration

```python
# stacks/shared/tool_definitions.py
class GoogleMapsTools:
    GEOCODE = ToolDefinition(
        tool_name="maps_geocode",
        input_schema={"properties": {"address": {"type": "string"}}},
        # ... separated from Lambda implementation
    )

# stacks/tools/google_maps_tool_stack.py  
class GoogleMapsToolStack(Stack):
    def __init__(self):
        self.lambda = _lambda.Function(...)  # Implementation separate from schema
```

### After Migration

```python
# stacks/tools/google_maps_tool_stack_v2.py
class GoogleMapsToolStackV2(BaseToolConstruct):
    def _create_tools(self):
        # Lambda and schema in same file - always in sync
        self.lambda = _lambda.Function(...)
        
        geocode_tool = ToolDefinition(
            tool_name="maps_geocode", 
            input_schema={
                "properties": {
                    "address": {"type": "string"}  # Matches Lambda exactly
                }
            }
        )
        self._register_tool(geocode_tool, self.lambda)
```

## Rollout Strategy

### Phase 1: Create New Pattern Infrastructure
- ✅ `BaseToolConstruct` base class
- ✅ Example implementation (`GoogleMapsToolStackV2`)
- ✅ Migration guide and documentation

### Phase 2: Migrate High-Risk Tools (Parameter Mismatches)
- Fix EarthQuake tool (start_date/end_date vs latitude/longitude mismatch)
- Fix Book Recommendation tool (category vs genre mismatch)  
- Fix any other identified mismatches

### Phase 3: Migrate Remaining Tools
- Convert all tool stacks to use `BaseToolConstruct`
- Update all agent stacks to use automatic discovery
- Update registration scripts

### Phase 4: Cleanup
- Remove centralized `tool_definitions.py`
- Update documentation
- Add linting rules to prevent regression

## Validation

Each migrated tool must pass:

1. **Schema Validation**: Tool schema matches Lambda parameter usage
2. **Integration Testing**: End-to-end agent test with actual tool calls
3. **Registration Testing**: Tool appears correctly in registry
4. **Discovery Testing**: Agent can discover and use tool automatically

## Benefits Achieved

After migration:

- ❌ **No more parameter mismatches** - schema and Lambda are co-located
- ✅ **Independent tool development** - no shared file modifications
- ✅ **Type safety** - compile-time validation of tool configurations
- ✅ **Automatic tool discovery** - agents find tools without manual configuration
- ✅ **Better testing** - tool tests validate complete integration
- ✅ **Cleaner architecture** - clear ownership boundaries

## Tool Stack Migration Checklist

For each tool being migrated:

- [ ] Create new tool stack inheriting from `BaseToolConstruct`
- [ ] Move Lambda creation into `_create_tools()` method
- [ ] Define tool schemas matching Lambda parameters exactly
- [ ] Register tools using `_register_tool()`
- [ ] Update agent stacks to use automatic discovery
- [ ] Add integration tests validating schema-Lambda alignment
- [ ] Remove tool from centralized definitions file
- [ ] Update documentation

## Best Practices

1. **Always validate schema matches Lambda**: Test actual tool calls in integration tests
2. **Use descriptive schemas**: Include examples, constraints, and clear descriptions
3. **Version tool schemas**: Use semantic versioning for breaking changes
4. **Test tool discovery**: Ensure agents can find and use tools automatically
5. **Document parameter changes**: Any Lambda parameter changes must update schema in same PR