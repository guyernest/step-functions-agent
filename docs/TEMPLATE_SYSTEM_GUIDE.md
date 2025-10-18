# Browser Automation Template System Guide

## Overview

The Template System provides a robust, schema-driven approach to browser automation by separating automation logic from execution. Instead of LLMs generating browser automation scripts on-the-fly, they select pre-built, tested templates and fill in variables.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Step Functions Agent                         │
│  ┌────────────┐      ┌──────────────┐      ┌─────────────────┐ │
│  │    LLM     │─────▶│  Template    │─────▶│  Local Browser  │ │
│  │ (Claude)   │      │  Renderer    │      │     Agent       │ │
│  └────────────┘      └──────────────┘      └─────────────────┘ │
│         │                    │                       │           │
│         │                    │                       │           │
│         ▼                    ▼                       ▼           │
│  ┌────────────┐      ┌──────────────┐      ┌─────────────────┐ │
│  │  Agent     │      │  Template    │      │   Nova Act      │ │
│  │  Registry  │      │  Registry    │      │   Executor      │ │
│  └────────────┘      └──────────────┘      └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Template Registry (DynamoDB)

**Table**: `TemplateRegistry-{env}`

**Schema**:
- **Partition Key**: `template_id` (e.g., "broadband_availability_bt_wholesale")
- **Sort Key**: `version` (e.g., "1.0.0")

**Attributes**:
- `extraction_name`: Links to canonical schema
- `status`: "active" | "deprecated" | "archived"
- `template`: JSON string containing full template structure
- `variables`: JSON schema defining required variables
- `metadata`: Author, tags, canonical schema info
- `created_at`: ISO timestamp
- `updated_at`: ISO timestamp

**GSI Indexes**:
- `TemplatesByExtractionName`: Query templates by extraction_name
- `TemplatesByStatus`: Filter by status

### 2. Template Renderer Lambda

**Function**: `template-renderer-{env}`

**Technology**: Python 3.11 with `chevron` library (Mustache rendering)

**Input**:
```json
{
  "template": { ... },
  "variables": {
    "building_number": "23",
    "street": "High Street",
    "postcode": "SW1A 1AA"
  }
}
```

**Output**:
```json
{
  "rendered_script": { ... }
}
```

**Supported Mustache Syntax**:
- `{{variable}}` - Simple substitution
- `{{#condition}}...{{/condition}}` - Conditional sections
- `{{^condition}}...{{/condition}}` - Inverted sections
- `{{#list}}...{{/list}}` - List iteration

### 3. Step Functions Integration

**New States** (in Remote Execution workflow):

1. **Check Template Enabled**: Detects if `template_id` exists in input
2. **Load Template**: DynamoDB GetItem from TemplateRegistry
3. **Render Template**: Lambda invocation with Mustache rendering
4. **Wait for Remote**: Sends rendered script to Activity
5. **Wait for Remote Direct**: Legacy path for raw prompts

**State Machine Flow**:
```
Check Template Enabled
  ├─ Has template_id? ──▶ Load Template ──▶ Render Template ──▶ Wait for Remote
  └─ No template_id?  ──▶ Wait for Remote Direct (legacy)
```

### 4. Local Browser Agent Updates

**Rust Agent** (`nova_act_executor.rs`):
- Auto-detects execution mode based on input structure
- `steps` array present → `command_type: "script"`
- No steps → `command_type: "act"`

**Python Wrapper** (`nova_act_wrapper.py`):
- New `execute_script()` function for script mode
- Delegates to `ScriptExecutor` for multi-step automation
- Maintains backward compatibility with `act` mode

**UI Display**:
- Shows `name` field from template (e.g., "BT Wholesale Broadband Availability Check")
- Fallback priority: name → description → prompt → "Unknown task"

## Template Format

Templates follow the same format as local examples in `lambda/tools/local-browser-agent/examples/`:

```json
{
  "name": "BT Wholesale Broadband Availability Check",
  "description": "Check broadband availability for UK addresses",
  "starting_page": "https://my.btwholesale.com/portalzone/...",
  "abort_on_error": true,
  "session": {
    "profile_name": "Bt_broadband",
    "clone_for_parallel": false,
    "requires_human_login": false,
    "session_timeout_hours": 24
  },
  "steps": [
    {
      "action": "act",
      "prompt": "Navigate to {{building_number}} {{street}}, {{postcode}}",
      "description": "Search by address"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract broadband availability data",
      "schema": { ... },
      "description": "Extract structured data"
    },
    {
      "action": "screenshot",
      "description": "Capture results"
    }
  ]
}
```

### Required Fields

- `name`: Human-readable template name
- `description`: What this template does
- `starting_page`: Initial URL (required by Nova Act)
- `steps`: Array of automation steps

### Optional Fields

- `abort_on_error`: Stop on first error (default: false)
- `session`: Browser session configuration
  - `profile_name`: Chrome profile to use
  - `clone_for_parallel`: Clone profile for parallel execution
  - `requires_human_login`: Needs manual authentication
  - `session_timeout_hours`: Session validity duration

### Step Types

1. **`act`**: Natural language browser action
   ```json
   {
     "action": "act",
     "prompt": "Click the submit button",
     "description": "Submit form"
   }
   ```

2. **`act_with_schema`**: Action with structured data extraction
   ```json
   {
     "action": "act_with_schema",
     "prompt": "Extract the table data",
     "schema": { "type": "object", "properties": {...} },
     "description": "Extract pricing table"
   }
   ```

3. **`screenshot`**: Capture page screenshot
   ```json
   {
     "action": "screenshot",
     "description": "Capture confirmation page"
   }
   ```

## Variable Substitution

Variables use Mustache syntax:

### Simple Variables
```json
"prompt": "Enter {{postcode}} in the search field"
```

### Conditional Sections
```json
"prompt": "Select {{building_number}} {{street}}{{#full_address}}, matching '{{full_address}}'{{/full_address}}"
```

If `full_address` is provided:
```
Select 23 High Street, matching '23 High Street, London SW1A 1AA'
```

If `full_address` is empty:
```
Select 23 High Street
```

### Inverted Sections
```json
"prompt": "{{^logged_in}}Please login first. {{/logged_in}}Navigate to dashboard"
```

## Registration Script

**Script**: `scripts/register_template.py`

**Usage**:
```bash
# Dry run (preview without saving)
python scripts/register_template.py templates/my_template_v1.0.0.json --dry-run

# Register to prod
python scripts/register_template.py templates/my_template_v1.0.0.json --env prod

# Register to dev with specific profile
python scripts/register_template.py templates/my_template_v1.0.0.json --env dev --profile CGI-Dev
```

**Features**:
- Automatic variable extraction from Mustache placeholders
- Metadata extraction from filename (e.g., `broadband_availability_bt_wholesale_v1.0.0.json`)
- Version management
- Validation before registration

**Naming Convention**:
```
{template_id}_v{version}.json

Examples:
- broadband_availability_bt_wholesale_v1.0.0.json
- shopping_cart_amazon_v2.1.0.json
- login_bt_portal_v1.0.0.json
```

## Agent Configuration

Agents that use templates must include in their system prompt:

```python
system_prompt = """
TEMPLATE-BASED AUTOMATION (PREFERRED):
Use the browser_remote tool in TEMPLATE MODE by providing:
{
  "template_id": "broadband_availability_bt_wholesale",
  "template_version": "1.0.0",
  "variables": {
    "building_number": "<value from input>",
    "street": "<value from input>",
    "postcode": "<value from input>"
  }
}

IMPORTANT GUIDELINES:
- ALWAYS use template_id when available
- Map input parameters to template variables
- The template handles all browser navigation and data extraction
"""
```

**Agent Registration**:
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

## Tool Schema Update

The `browser_remote` tool now supports two modes:

### Template Mode (Preferred)
```json
{
  "template_id": "broadband_availability_bt_wholesale",
  "template_version": "1.0.0",
  "variables": {
    "building_number": "23",
    "street": "High Street",
    "postcode": "SW1A 1AA"
  }
}
```

### Legacy Mode (Ad-hoc)
```json
{
  "prompt": "Navigate to BT broadband checker and search for address",
  "starting_page": "https://..."
}
```

**Schema Validation**:
```json
{
  "oneOf": [
    {
      "required": ["template_id", "variables"],
      "description": "Template mode - use pre-built automation template"
    },
    {
      "required": ["prompt"],
      "description": "Legacy mode - use natural language prompt"
    }
  ]
}
```

## End-to-End Flow

### 1. LLM Execution
User triggers agent with input:
```json
{
  "building_number": "23",
  "street": "High Street",
  "postcode": "SW1A 1AA"
}
```

### 2. LLM Tool Call
```json
{
  "tool_name": "browser_remote",
  "template_id": "broadband_availability_bt_wholesale",
  "template_version": "1.0.0",
  "variables": {
    "building_number": "23",
    "street": "High Street",
    "postcode": "SW1A 1AA"
  }
}
```

### 3. Step Functions Processing
```
Check Template Enabled
  └─ template_id exists ✓

Load Template
  └─ DynamoDB GetItem(template_id="broadband_availability_bt_wholesale", version="1.0.0")

Render Template
  └─ Lambda(template, variables) → rendered_script

Wait for Remote
  └─ Activity.sendTask(rendered_script)
```

### 4. Local Browser Agent
```
Activity Poller receives task
  ├─ UI shows: "BT Wholesale Broadband Availability Check"
  └─ Rust agent detects steps array → command_type="script"

Python Wrapper
  └─ execute_script() → ScriptExecutor

Nova Act Execution
  ├─ Step 1: Login/Navigate
  ├─ Step 2: Fill address form
  ├─ Step 3: Select address
  ├─ Step 4: Extract data with schema
  └─ Step 5: Screenshot

Return Results
  └─ S3 recording + structured data
```

## Benefits

### 1. Consistency
- Pre-tested templates ensure reliable execution
- No LLM hallucination in automation logic
- Versioned templates for change management

### 2. Performance
- Faster execution (no script generation)
- Reduced token usage (no need to include full scripts in prompts)
- Parallel execution with template versioning

### 3. Maintainability
- Templates can be updated independently of agents
- Clear separation of concerns
- Easy to test and validate templates

### 4. Security
- Templates are reviewed and approved
- No arbitrary code execution
- Audit trail through template registry

### 5. Reusability
- Same template used by multiple agents
- Template library grows over time
- Knowledge sharing across team

## Migration from Legacy Mode

### Before (Legacy)
```python
# LLM generates full script
tool_call = {
    "tool_name": "browser_remote",
    "prompt": "Navigate to BT broadband checker. Fill in building number: 23, street: High Street, postcode: SW1A 1AA. Extract availability data."
}
```

### After (Template)
```python
# LLM fills template variables
tool_call = {
    "tool_name": "browser_remote",
    "template_id": "broadband_availability_bt_wholesale",
    "variables": {
        "building_number": "23",
        "street": "High Street",
        "postcode": "SW1A 1AA"
    }
}
```

### Migration Steps

1. **Identify repetitive automation patterns** in your agents
2. **Create template** based on working examples
3. **Register template** using `register_template.py`
4. **Update agent system prompt** to use template mode
5. **Test with various inputs** to ensure variables work correctly
6. **Deploy updated agent** stack

## Best Practices

### Template Design
- ✅ Start with working local examples
- ✅ Use descriptive names and descriptions
- ✅ Keep templates focused (one workflow per template)
- ✅ Document required variables in template metadata
- ✅ Test locally before registration
- ❌ Don't include secrets or credentials
- ❌ Don't make templates too complex (split if needed)

### Variable Naming
- ✅ Use snake_case (e.g., `building_number`)
- ✅ Be descriptive (e.g., `postcode` not `pc`)
- ✅ Match input schema field names
- ❌ Avoid generic names (e.g., `value1`, `data`)

### Versioning
- Use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes to variable schema
- **MINOR**: New optional variables or steps
- **PATCH**: Bug fixes, prompt improvements

### Testing
1. Test locally with example inputs
2. Test template rendering (dry-run)
3. Test full flow in dev environment
4. Monitor first production runs closely

## Troubleshooting

### Template Not Found
**Error**: "Template not found in registry"

**Solutions**:
- Verify template_id matches registered name
- Check template version is correct
- Confirm template status is "active"
- Check DynamoDB table in correct environment

### Variable Rendering Issues
**Error**: Rendered script has `{{variable}}` placeholders

**Solutions**:
- Verify variable names match exactly (case-sensitive)
- Check variables are provided in LLM tool call
- Test rendering with `--dry-run` flag

### Command Type Detection
**Error**: "Unknown command type: script"

**Solutions**:
- Ensure local browser agent is updated
- Check template has `steps` array
- Verify Rust agent is auto-detecting correctly

### Script Execution Failures
**Error**: Script fails during execution

**Solutions**:
- Check template locally first
- Verify profile_name exists and is authenticated
- Review step prompts for clarity
- Check Nova Act API key is configured
- Monitor CloudWatch/local logs for detailed errors

## File Locations

```
step-functions-agent/
├── templates/                              # Template JSON files
│   └── broadband_availability_bt_wholesale_v1.0.0.json
├── scripts/
│   └── register_template.py               # Registration script
├── docs/
│   ├── TEMPLATE_SYSTEM_GUIDE.md          # This document
│   └── TEMPLATE_REGISTRY_SCHEMA.md       # DynamoDB schema
├── stacks/
│   ├── shared/
│   │   └── shared_infrastructure_stack.py # TemplateRegistry table
│   ├── agents/
│   │   ├── broadband_availability_bt_wholesale_stack.py
│   │   └── step_functions_generator_unified_llm.py
│   └── tools/
│       └── browser_remote_tool_stack.py   # Updated tool schema
├── lambda/
│   ├── shared/
│   │   └── template_renderer/
│   │       └── lambda_function.py         # Mustache rendering
│   └── tools/
│       └── local-browser-agent/
│           ├── src-tauri/src/
│           │   ├── nova_act_executor.rs   # Command type detection
│           │   └── activity_poller.rs     # UI display
│           └── python/
│               ├── nova_act_wrapper.py    # Script mode support
│               └── script_executor.py     # Multi-step execution
```

## Related Documentation

- [Template Registry Schema](TEMPLATE_REGISTRY_SCHEMA.md)
- [AgentCore Browser Agent Guide](AGENTCORE_BROWSER_AGENT_GUIDE.md)
- [Local Browser Agent README](../lambda/tools/local-browser-agent/README.md)
- [Schema Factory Design](../lambda/tools/local-browser-agent/SCHEMA_FACTORY_DESIGN.md)

## Support

For issues or questions:
1. Check logs: CloudWatch for Lambda, local logs for browser agent
2. Test locally with example scripts
3. Verify template registration with DynamoDB console
4. Review recent git commits for template system changes
