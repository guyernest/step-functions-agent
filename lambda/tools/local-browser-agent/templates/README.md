# Workflow Templates

This directory contains parameterized workflow templates that can be reused with different input variables.

## Available Templates

### bt_broadband_workflow_template.json

**Description:** Optimized workflow for checking BT Wholesale broadband availability with smart login detection and password manager support.

**Required Variables:**
- `{{username}}` - BT Wholesale username for login
- `{{postcode}}` - UK postcode to search (e.g., "CB7 5LG")
- `{{building_number}}` - Building/house number (e.g., "40")
- `{{street}}` - Street name (e.g., "Withers Place")
- `{{full_address}}` - Complete address for exact matching (e.g., "40 Withers Place, Fordham, Ely, Cambridgeshire, CB7 5LG")

**Key Features:**
- ✅ **Smart Login Detection**: Automatically detects if login is required and skips login steps if already authenticated
- ✅ **Password Manager Support**: Multiple strategies for password autofill (Tab+Enter, Vision LLM, manual fallback)
- ✅ **Progressive Escalation**: Tries fast DOM methods first, escalates to Vision LLM if needed
- ✅ **Robust Address Matching**: Case-insensitive regex matching handles format variations
- ✅ **Scroll-Aware Vision**: Vision LLM can scroll through long address lists to find matches
- ✅ **Robust Error Handling**: Verifies each step with fallback strategies

**Flow:**
```
1. CheckAuthenticationStatus
   ├─ If login page → PerformLogin → PerformSearch
   └─ If authenticated → PerformSearch
2. PerformSearch (fill postcode and search)
3. SelectAddress (with DOM detection for address list)
4. ExtractResults (broadband package data)
```

## Usage

### Method 1: Template Variable Replacement (Recommended for State Machines)

Load the template JSON and replace variables programmatically:

```python
import json

# Load template
with open('templates/bt_broadband_workflow_template.json', 'r') as f:
    template = f.read()

# Replace variables
workflow = template.replace('{{username}}', 'nterizakis')
workflow = workflow.replace('{{postcode}}', 'CB7 5LG')
workflow = workflow.replace('{{building_number}}', '40')
workflow = workflow.replace('{{street}}', 'Withers Place')
workflow = workflow.replace('{{full_address}}', '40 Withers Place, Fordham, Ely, Cambridgeshire, CB7 5LG')

# Parse and use
workflow_json = json.loads(workflow)
```

### Method 2: Manual Substitution

1. Copy the template file
2. Search and replace all `{{variable}}` placeholders with actual values
3. Save as a new workflow file

### Example: AWS Step Functions Integration

```python
import json
import boto3

def lambda_handler(event, context):
    # Extract input variables
    username = event['username']
    postcode = event['postcode']
    building_number = event['building_number']
    street = event['street']
    full_address = event['full_address']

    # Load and populate template
    with open('templates/bt_broadband_workflow_template.json', 'r') as f:
        template = f.read()

    # Replace all variables
    workflow = (template
        .replace('{{username}}', username)
        .replace('{{postcode}}', postcode)
        .replace('{{building_number}}', building_number)
        .replace('{{street}}', street)
        .replace('{{full_address}}', full_address)
    )

    # Send to browser agent
    browser_agent = boto3.client('lambda')
    response = browser_agent.invoke(
        FunctionName='browser-agent',
        Payload=json.dumps({
            'tool_name': 'browser_remote',
            'tool_input': json.loads(workflow)
        })
    )

    return json.loads(response['Payload'].read())
```

## Template Variables Best Practices

1. **Always use double curly braces**: `{{variable}}` not `{variable}`
2. **Use descriptive names**: Makes template easier to understand and maintain
3. **Document required variables**: List all variables in template description
4. **Validate before execution**: Ensure all variables are replaced (no `{{` remaining)
5. **Escape special characters**: If values contain quotes, escape them properly

## Creating New Templates

1. Start with a working workflow from the `examples/` directory
2. Identify values that should be parameterized
3. Replace hardcoded values with `{{variable_name}}` placeholders
4. Update the workflow name and description to indicate it's a template
5. Document all required variables in this README
6. Test the template with sample data to verify variable replacement works

## Security Notes

⚠️ **Never store passwords in templates or workflow files**

The templates use password manager integration to maintain security:
- Password is never stored in the workflow
- Browser's native password manager is used
- Multiple fallback strategies ensure reliability
- Manual intervention option as final fallback

## Address Selection Strategies

The workflow uses 5 progressive strategies to handle address format variations:

### Strategy 1: Minimal Regex Pattern (Fastest)
- Pattern: `/^\s*{building_number}\s+\w+/i`
- Matches: "1 Church", "40 Withers" (case-insensitive)
- Handles: Leading spaces, any first word of street

### Strategy 2: Flexible Building + Street
- Pattern: `/{building_number}[\s,]+{street}/i`
- Matches: "1 Church View", "1, Church View"
- Handles: Space or comma separators

### Strategy 3: Fuzzy Match
- Pattern: `/{building_number}.*{street}/i`
- Matches: "1 anything Church View"
- Handles: Extra words between building and street

### Strategy 4: Exact Text Match
- Fallback for perfect HTML matches
- "40 Withers Place"

### Strategy 5: Vision LLM with Scroll (Last Resort)
- Searches visible addresses
- **Scrolls down if not found** (up to 3 scroll attempts)
- Handles: Long address lists, any format variation
- Max 8 actions (scrolls + clicks)

## Advanced Features

### Human-Like Timing (Delays)

Prevent bot detection by adding delays between actions. Delays mimic human reaction time.

**Script-level default delay:**
```json
{
  "name": "My Workflow",
  "default_delay": 300,
  "steps": [...]
}
```

**Per-step delay (overrides default):**
```json
{
  "action": "click",
  "delay": 500,
  "locator": {"strategy": "selector", "value": "button"}
}
```

**Random delay range (most human-like):**
```json
{
  "action": "click",
  "delay": {"min": 200, "max": 500},
  "locator": {"strategy": "selector", "value": "button"}
}
```

### Conditional Retry

Retry steps only when specific conditions are met. This is useful for temporary errors like "service unavailable" that may resolve on retry, while avoiding retries for permanent errors like "invalid credentials".

**Retry on visible error message:**
```json
{
  "action": "click",
  "locator": {"strategy": "selector", "value": "button[type='submit']"},
  "retry": {
    "attempts": 3,
    "delay_ms": 1000,
    "retry_if": {
      "text_visible": "service unavailable"
    }
  }
}
```

**Available retry conditions:**
- `text_visible`: Retry if text appears on page
- `text_not_visible`: Retry if text does NOT appear on page
- `element_visible`: Retry if element is visible
- `element_not_visible`: Retry if element is NOT visible

**Example - Retry until success indicator appears:**
```json
{
  "action": "click",
  "locator": {"strategy": "text", "value": "Submit"},
  "retry": {
    "attempts": 5,
    "delay_ms": 2000,
    "retry_if": {
      "element_not_visible": ".address-list"
    }
  }
}
```

### Smart Form Field Locator

The `form_field` strategy intelligently finds form fields in modern CSS frameworks (Angular Material, MUI, Bootstrap, etc.) that use complex nested DOM structures.

**Usage:**
```json
{
  "action": "fill",
  "locator": {
    "strategy": "form_field",
    "label": "PostCode",
    "field_type": "input"
  },
  "value": "CB7 5LG"
}
```

**How it works:**
The `form_field` strategy tries multiple patterns in order:
1. Direct ID match (`#postcode`)
2. Name attribute (`input[name='postcode']`)
3. Placeholder text (`input[placeholder*='PostCode']`)
4. Angular Material (`.mat-form-field:has-text('PostCode') input`)
5. MUI (`.MuiFormControl-root:has-text('PostCode') input`)
6. Generic label association (`label:has-text('PostCode') + input`)
7. Aria-label match (`input[aria-label*='PostCode']`)
8. Proximity search (`:has-text('PostCode') >> input`)

**Benefits:**
- ✅ Works with Angular Material, MUI, Bootstrap, and custom forms
- ✅ No need to inspect complex DOM structures
- ✅ Automatically handles label-to-input association
- ✅ Falls back gracefully through multiple strategies
- ✅ Logs which strategy succeeded for debugging

## Performance Optimization

The templates include several optimizations:

1. **Fast Path**: Skips login if already authenticated (~20-30 second savings)
2. **DOM-First**: Tries fast regex matching before expensive Vision LLM calls
3. **Progressive Matching**: Starts with minimal pattern, escalates as needed
4. **Named Phases**: Clear workflow structure for easy debugging
5. **3-Second Timeouts**: Quick decisions to avoid unnecessary waits
6. **Scroll-Aware Vision**: Vision LLM only used when DOM methods fail, with scroll capability
7. **Human-Like Timing**: Default delays prevent bot detection while maintaining speed
8. **Smart Retries**: Conditional retry avoids wasteful retries on permanent errors

## Troubleshooting

**Problem:** Variables not being replaced
- **Solution:** Ensure exact match including curly braces: `{{postcode}}` not `{{ postcode }}`

**Problem:** Workflow fails at login step
- **Solution:** Check that `{{username}}` is valid and password manager has saved credentials

**Problem:** Address not found in list
- **Solution:** Verify `{{full_address}}` matches the exact format shown on the BT website

**Problem:** Template treats `{{variable}}` as literal text
- **Solution:** Perform string replacement BEFORE parsing JSON, not after
