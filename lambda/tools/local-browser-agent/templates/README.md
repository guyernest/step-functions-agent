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

## Performance Optimization

The templates include several optimizations:

1. **Fast Path**: Skips login if already authenticated (~20-30 second savings)
2. **DOM-First**: Tries fast DOM detection before expensive Vision LLM calls
3. **Named Phases**: Clear workflow structure for easy debugging
4. **3-Second Timeouts**: Quick decisions to avoid unnecessary waits
5. **Progressive Escalation**: Cheapest/fastest methods first, escalate only when needed

## Troubleshooting

**Problem:** Variables not being replaced
- **Solution:** Ensure exact match including curly braces: `{{postcode}}` not `{{ postcode }}`

**Problem:** Workflow fails at login step
- **Solution:** Check that `{{username}}` is valid and password manager has saved credentials

**Problem:** Address not found in list
- **Solution:** Verify `{{full_address}}` matches the exact format shown on the BT website

**Problem:** Template treats `{{variable}}` as literal text
- **Solution:** Perform string replacement BEFORE parsing JSON, not after
