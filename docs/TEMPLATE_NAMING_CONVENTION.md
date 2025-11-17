# Template Naming Convention

## Overview

Templates in the TemplateRegistry table follow a specific naming convention to maintain consistency and enable automatic matching with agents.

## Naming Rules

### Template IDs
- Use **snake_case** (underscores)
- Match the extraction name or canonical schema name
- Examples:
  - `broadband_availability_bt_wholesale`
  - `shopping_cart_amazon`
  - `login_microsoft_graph`

### Agent Names
- Use **kebab-case** (hyphens) for CDK stack compatibility
- Examples:
  - `broadband-availability-bt-wholesale`
  - `shopping-cart-amazon`
  - `login-microsoft-graph`

## Automatic Matching

The UI automatically normalizes agent names when looking for templates:

```typescript
// Agent name (kebab-case)
"broadband-availability-bt-wholesale"

// Normalized to template_id (snake_case)
"broadband_availability_bt_wholesale"
```

## Template Configuration in Agent Metadata

### New Approach (Recommended)
Agents should include `template_config` in their metadata:

```python
agent_spec = {
    "template_config": json.dumps({
        "enabled": True,
        "template_id": "broadband_availability_bt_wholesale",
        "template_version": "1.0.0",
        "rendering_engine": "mustache"
    })
}
```

### Legacy Approach (Backward Compatible)
For agents without `template_config`, the UI will:
1. Check if agent uses the `browser_remote` tool
2. Normalize the agent name (hyphens → underscores)
3. Try to fetch template directly with normalized name
4. Fall back to searching templates by normalized name

## Registration Guidelines

When registering a new template:

1. **Template Filename**:
   ```
   {template_id}_v{version}.json
   ```
   Example: `broadband_availability_bt_wholesale_v1.0.0.json`

2. **Template ID** (in DynamoDB):
   - Use snake_case
   - Should match the `extraction_name` for schema-driven agents

3. **Agent Name** (in CDK):
   - Use kebab-case
   - Convert template_id: replace underscores with hyphens

## Examples

| Template ID | Template File | Agent Name | Extraction Name |
|-------------|---------------|------------|-----------------|
| `broadband_availability_bt_wholesale` | `broadband_availability_bt_wholesale_v1.0.0.json` | `broadband-availability-bt-wholesale` | `broadband_availability_bt_wholesale` |
| `contact_lookup_microsoft` | `contact_lookup_microsoft_v1.0.0.json` | `contact-lookup-microsoft` | `contact_lookup_microsoft` |
| `price_check_amazon` | `price_check_amazon_v2.1.0.json` | `price-check-amazon` | `price_check_amazon` |

## Troubleshooting

### Template Not Found
If the UI shows "No template configured for this agent":

1. **Check naming**:
   ```bash
   aws dynamodb scan --table-name TemplateRegistry-prod \
     --filter-expression "template_id = :tid" \
     --expression-attribute-values '{":tid":{"S":"your_template_id"}}'
   ```

2. **Verify agent uses browser_remote tool**:
   - Check agent's tools array includes `browser_remote`

3. **Check template status**:
   - Ensure template status is `"active"` in DynamoDB

4. **Normalize agent name manually**:
   ```python
   # Agent name with hyphens
   agent_name = "broadband-availability-bt-wholesale"

   # Template ID with underscores
   template_id = agent_name.replace("-", "_")
   # Result: "broadband_availability_bt_wholesale"
   ```

## Migration Path

For existing agents without `template_config`:

1. **Option 1: Update Agent Stack** (Recommended)
   - Add `template_config` to agent_spec in CDK stack
   - Redeploy agent to update DynamoDB

2. **Option 2: Use Naming Convention** (Automatic)
   - UI automatically handles this
   - No code changes needed
   - Template ID must match normalized agent name

## Best Practices

1. **Always use consistent naming**:
   - Template IDs: snake_case
   - Agent names: kebab-case
   - Extraction names: snake_case (match template_id)

2. **Include template_config in new agents**:
   - Makes template association explicit
   - Avoids reliance on naming conventions
   - Supports versioning

3. **Document template variables**:
   - Include clear descriptions in template metadata
   - Mark required vs optional variables
   - Provide example values

4. **Test locally before registration**:
   - Use `script_executor.py` to test templates
   - Verify all variables render correctly
   - Check extracted data matches schema
