# Script Format v2 Specification

## Overview

Script Format v2 is a declarative, human-readable format for browser automation scripts. It prioritizes simplicity and readability while supporting the full power of progressive escalation.

## Design Goals

1. **Human Readable** - Domain experts can read and understand scripts
2. **Concise** - ~75% reduction from v1 format
3. **Auto-Escalation** - Locators automatically escalate, no manual chain definition
4. **Flexible** - Support simple and complex workflows
5. **Type Safe** - Clear schema for validation and tooling

## Format Comparison

### Before (v1) - 722 lines for BT script

```json
{
  "name": "BT Broadband Checker",
  "version": "1.0.0",
  "steps": [
    {
      "type": "click",
      "description": "Click Next button",
      "escalation_chain": [
        {
          "method": "playwright_locator",
          "locator": {
            "strategy": "selector",
            "value": "button[type='submit']"
          },
          "confidence_threshold": 0.9
        },
        {
          "method": "playwright_locator",
          "locator": {
            "strategy": "text",
            "value": "Next"
          },
          "confidence_threshold": 0.9
        },
        {
          "method": "vision_find_element",
          "prompt": "Find the Next button",
          "prefer": "selector",
          "confidence_threshold": 0.7
        }
      ]
    }
  ]
}
```

### After (v2) - ~180 lines for BT script

```yaml
name: BT Broadband Checker
version: 2.0.0
start_url: https://bt.com/broadband

inputs:
  postcode:
    type: string
    description: UK postcode to check

steps:
  - click: Next button
    locators:
      - selector: "button[type='submit']"
      - text: Next
```

## Complete Schema

### Root Structure

```yaml
# Required fields
name: string                    # Script name
version: string                 # Semantic version (e.g., "2.0.0")
start_url: string               # Initial URL to navigate to

# Optional fields
description: string             # What this script does
author: string                  # Who created it
created: datetime               # ISO 8601 timestamp
tags: string[]                  # Categorization tags

# Input variables
inputs:
  variable_name:
    type: string | number | boolean | select
    description: string
    required: boolean           # Default: true
    default: any                # Default value
    options: string[]           # For select type only

# Session configuration
session:
  profile: string               # Browser profile name
  persist_cookies: boolean      # Keep cookies between runs
  timeout_minutes: number       # Session timeout

# Main workflow
steps: Step[]                   # Array of step definitions
```

### Step Types

#### 1. Navigate

```yaml
- navigate: https://example.com/page
  description: Go to login page    # Optional
```

#### 2. Click

```yaml
- click: Button description
  locators:                        # Optional - auto-generated if omitted
    - test_id: submit-btn          # data-testid attribute
    - text: Submit                 # Text content
    - selector: "button.primary"   # CSS selector
    - aria_label: Submit form      # aria-label attribute
    - role: button                 # ARIA role
```

#### 3. Fill

```yaml
- fill: Email field
  value: "{{email}}"               # Variable reference
  locators:
    - form_field: email            # Smart form field finder
    - name: email
    - placeholder: "Enter email"
```

#### 4. Select (Dropdown)

```yaml
- select: Country dropdown
  value: "United Kingdom"          # Option text
  locators:
    - name: country
    - test_id: country-select
```

#### 5. Wait

```yaml
# Wait for page state
- wait: networkidle               # or: load, domcontentloaded

# Wait for duration
- wait: 2000                      # milliseconds

# Wait for element
- wait:
    visible: ".success-message"
    timeout: 10000
```

#### 6. Screenshot

```yaml
- screenshot: After login
  path: screenshots/login.png     # Optional path
```

#### 7. Press (Keyboard)

```yaml
- press: Enter
# or
- press: [Tab, Tab, Enter]        # Multiple keys
```

#### 8. Extract (Vision)

```yaml
- extract: Get package details
  method: vision                   # Use vision AI
  prompt: "Extract all broadband packages with prices and speeds"
  schema:
    type: object
    properties:
      packages:
        type: array
        items:
          type: object
          properties:
            name: { type: string }
            price: { type: number }
            speed_mbps: { type: number }
```

#### 9. Sequence (Named Group)

```yaml
- sequence: Login Flow
  steps:
    - fill: Username
      value: "{{username}}"
    - fill: Password
      value: "{{password}}"
    - click: Sign In
```

### Conditional Steps

#### If Statement

```yaml
- if:
    visible: ".error-message"      # Condition
  then:
    - screenshot: Error state
    - goto: HandleError
  else:
    - click: Continue
```

#### Condition Types

```yaml
# Element visibility
visible: ".element"
not_visible: ".element"

# Element existence (in DOM)
exists: ".element"
not_exists: ".element"

# URL conditions
url_contains: "/dashboard"
url_matches: "^https://.*\\.com/login"

# Text content
text_contains:
  selector: ".status"
  text: "Success"

# JavaScript evaluation
js_eval: "document.querySelector('.count').textContent > '0'"

# Logical operators
any:                              # OR
  - visible: ".success"
  - url_contains: "/complete"

all:                              # AND
  - visible: ".form"
  - not_visible: ".loading"
```

#### Switch Statement

```yaml
- switch:
    cases:
      - when:
          url_contains: "/login"
        then: goto LoginFlow

      - when:
          url_contains: "/dashboard"
        then: goto MainFlow

      - when:
          visible: ".modal"
        then:
          - click: Close modal
            locators:
              - selector: ".modal-close"

    default:
      - screenshot: Unknown state
      - goto: ErrorHandler
```

#### Goto

```yaml
- goto: StepName                  # Jump to named sequence
```

### Locator Types

| Type | Attribute | Stability | Example |
|------|-----------|-----------|---------|
| `test_id` | data-testid, data-cy, data-test | HIGH | `test_id: submit-btn` |
| `aria_label` | aria-label | HIGH | `aria_label: Submit form` |
| `name` | name | HIGH | `name: email` |
| `role` | role + accessible name | HIGH | `role: button` |
| `id` | id | MEDIUM | `id: login-form` |
| `text` | Text content | MEDIUM | `text: Sign In` |
| `placeholder` | placeholder | MEDIUM | `placeholder: Enter email` |
| `selector` | CSS selector | LOW-HIGH | `selector: form > button` |
| `xpath` | XPath | LOW | `xpath: //button[@type='submit']` |
| `form_field` | Smart field detection | HIGH | `form_field: email` |

### Locator Metadata

```yaml
locators:
  - test_id: submit-btn
    confidence: 0.95              # How confident we are (0-1)
    stability: high               # high | medium | low
    note: "Added by developer"    # Optional note
```

### Variables

#### Input Variables

```yaml
inputs:
  username:
    type: string
    description: Login username
    required: true

  remember_me:
    type: boolean
    description: Stay signed in
    default: false

  plan_type:
    type: select
    description: Subscription plan
    options: [basic, premium, enterprise]
    default: basic
```

#### Using Variables

```yaml
steps:
  - fill: Username field
    value: "{{username}}"

  - click: "{{plan_type}} plan"   # Dynamic text

  - if:
      js_eval: "{{remember_me}} === true"
    then:
      - click: Remember me checkbox
```

#### Extracted Variables

```yaml
- extract: Get order number
  store_as: order_id              # Save result to variable
  method: vision
  prompt: "Find the order confirmation number"

- fill: Reference field
  value: "{{order_id}}"           # Use extracted value
```

## Auto-Escalation

When executing steps, the engine automatically tries locators in order:

```
1. Try each explicit locator in order
2. If all fail, auto-generate additional locators from description
3. If still failing, use vision AI to find element
4. If vision fails, use vision AI with coordinates
5. Report failure with diagnosis
```

### Escalation Configuration

```yaml
# Global settings
settings:
  escalation:
    enable_vision: true           # Allow vision AI fallback
    vision_confidence: 0.7        # Min confidence for vision
    max_attempts: 3               # Retries per locator
    timeout: 30000                # Per-step timeout (ms)
```

### Per-Step Override

```yaml
- click: Complex button
  locators:
    - text: Submit
  escalation:
    enable_vision: false          # Don't use vision for this step
    timeout: 60000                # Longer timeout
```

## Complete Example

```yaml
name: BT Broadband Availability Checker
version: 2.0.0
description: Check broadband availability at a UK address
author: Domain Expert
start_url: https://my.btwholesale.com/portalzone/spa/#/myApps

inputs:
  building_number:
    type: string
    description: Building/house number
    required: true

  street:
    type: string
    description: Street name

  postcode:
    type: string
    description: UK postcode
    required: true

session:
  profile: BT_Wholesale
  persist_cookies: true
  timeout_minutes: 30

steps:
  # Initial page load
  - wait: networkidle
  - screenshot: Initial state

  # Check if already logged in
  - if:
      any:
        - visible: ".user-menu"
        - url_contains: "/myApps"
    then:
      - goto: NavigateToChecker

  # Login flow
  - sequence: Login
    steps:
      - wait: 1000
      - fill: Username
        value: "{{BT_USERNAME}}"
        locators:
          - form_field: username
          - selector: "input[type='text']"

      - click: Next button
        locators:
          - selector: "button[type='submit']"
          - text: Next

      - wait: networkidle

      - fill: Password
        value: "{{BT_PASSWORD}}"
        locators:
          - form_field: password

      - click: Sign In
        locators:
          - selector: "button#next"
          - text: Sign In

      - wait: networkidle
      - wait: 3000                # Wait for redirect
      - wait: networkidle

  # Navigate to broadband checker
  - sequence: NavigateToChecker
    steps:
      - click: Broadband Availability Checker
        locators:
          - text: Enhanced Broadband Availability
          - text: Broadband Availability

      - wait: networkidle
      - wait: 2000                # SPA initialization

  # Fill address form
  - sequence: SearchAddress
    steps:
      - click: Address Checker tab
        locators:
          - text: Address Checker
          - role: tab

      - fill: Building number
        value: "{{building_number}}"
        locators:
          - form_field: building
          - placeholder: "Building"

      - fill: Street name
        value: "{{street}}"
        locators:
          - form_field: street

      - fill: Postcode
        value: "{{postcode}}"
        locators:
          - form_field: postcode

      - click: Submit
        locators:
          - selector: "button[type='submit']"
          - text: Submit

      - wait: networkidle

  # Handle address selection if shown
  - if:
      visible: ".address-list"
    then:
      - click: Select matching address
        locators:
          - text: "{{building_number}}"
          - text: "{{postcode}}"

      - wait: networkidle

  # Extract results
  - screenshot: Results page

  - extract: Broadband packages
    method: vision
    store_as: packages
    prompt: |
      Extract ALL visible broadband packages with:
      - Package name
      - Monthly price (number only)
      - Download speed in Mbps
      - Upload speed in Mbps
      - Availability status (available/not available)

      Return as JSON array.
    schema:
      type: object
      properties:
        packages:
          type: array
          items:
            type: object
            properties:
              name: { type: string }
              monthly_price: { type: number }
              download_mbps: { type: number }
              upload_mbps: { type: number }
              available: { type: boolean }
            required: [name, available]
```

## Migration from v1

### Automatic Conversion

```python
def migrate_v1_to_v2(v1_script: dict) -> dict:
    """Convert v1 script to v2 format"""

    v2 = {
        "name": v1_script.get("name"),
        "version": "2.0.0",
        "start_url": v1_script.get("starting_page"),
        "steps": []
    }

    for step in v1_script.get("steps", []):
        v2_step = convert_step(step)
        v2["steps"].append(v2_step)

    return v2
```

### Key Conversions

| v1 | v2 |
|----|-----|
| `{"type": "click", "description": "..."}` | `click: "..."` |
| `{"type": "fill", "value": "..."}` | `fill: "..." + value: "..."` |
| `{"type": "wait_for_load_state", "state": "networkidle"}` | `wait: networkidle` |
| `{"type": "screenshot"}` | `screenshot: Description` |
| `escalation_chain: [...]` | `locators: [...]` |
| `{"method": "playwright_locator", "locator": {"strategy": "text", "value": "X"}}` | `text: X` |

## Validation

### Schema Validation

```python
from jsonschema import validate

SCRIPT_V2_SCHEMA = {
    "type": "object",
    "required": ["name", "version", "start_url", "steps"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "start_url": {"type": "string", "format": "uri"},
        "steps": {"type": "array", "minItems": 1}
    }
}

def validate_script(script: dict) -> list[str]:
    """Validate script and return list of errors"""
    errors = []
    try:
        validate(script, SCRIPT_V2_SCHEMA)
    except ValidationError as e:
        errors.append(str(e.message))
    return errors
```

### Semantic Validation

- All `goto` targets must exist
- Variables must be defined before use
- Locators should have at least one high-stability option
- Extracted variables should be used somewhere

## File Extension

- `.nav.yaml` - Navigation Studio script (YAML)
- `.nav.json` - Navigation Studio script (JSON)

Both are valid; YAML preferred for human editing.

---

**Version**: 2.0
**Created**: 2025-01-16
**Status**: Specification Complete
