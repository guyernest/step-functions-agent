# Workflow Engine Design

## Overview

The Workflow Engine extends the sequential browser automation executor with **conditional logic**, **intelligent retry strategies**, and **escalation patterns**. It enables complex flows like adaptive login handling, state validation, and progressive problem-solving.

## Design Principles

1. **Backward Compatible** - Linear scripts continue to work without modification
2. **Easy to Author** - Simple JSON syntax for common patterns
3. **Powerful** - Handles complex real-world workflows (multi-strategy login, conditional navigation)
4. **Progressive Enhancement** - Start simple, add complexity only where needed
5. **Intelligent Failure Handling** - Try alternatives before giving up

## Core Workflow Step Types

### 1. `if` - Conditional Branching

Skip or branch execution based on runtime conditions.

```json
{
  "type": "if",
  "name": "CheckIfAlreadyLoggedIn",
  "description": "Skip login if session cookie valid",
  "condition": {
    "type": "element_exists",
    "selector": ".user-menu, [data-testid='user-profile']",
    "timeout": 3000
  },
  "then": {"goto": "SearchAddress"},
  "else": {"continue": true}
}
```

**Fields:**
- `condition` - Condition to evaluate (see Condition Types below)
- `then` - Action if condition is true: `{"goto": "StepName"}` or `{"continue": true}`
- `else` - Action if condition is false (optional)

**Use Cases:**
- Skip login if already authenticated
- Check if modal appeared and close it
- Verify expected page loaded, else retry navigation
- Conditional form fields based on page state

---

### 2. `try` - Intelligent Retry with Strategies

Attempt an operation with multiple strategies, fallbacks, and escalation.

```json
{
  "type": "try",
  "name": "AttemptPasswordManagerLogin",
  "description": "Try multiple strategies to trigger password manager",
  "strategies": [
    {
      "name": "PasswordManagerAutofill",
      "description": "Click password field with real mouse to trigger autofill",
      "steps": [
        {
          "action": "click",
          "selector": "input[type='password']",
          "trigger_autofill": true,
          "description": "Click password field with real mouse"
        },
        {
          "action": "wait",
          "duration": 800,
          "description": "Wait for password manager dropdown"
        },
        {
          "action": "press",
          "keys": ["ArrowDown", "Enter"],
          "delay": 500,
          "description": "Select saved password"
        }
      ],
      "verify": {
        "type": "js_eval",
        "expression": "document.querySelector('input[type=password]').value.length > 0",
        "description": "Check if password field is filled"
      }
    },
    {
      "name": "DirectPasswordManagerClick",
      "description": "Try clicking password field without username first",
      "steps": [
        {
          "action": "click",
          "selector": "input[type='password']",
          "trigger_autofill": true,
          "force": true
        },
        {
          "action": "wait",
          "duration": 1000
        },
        {
          "action": "press",
          "keys": ["Enter"]
        }
      ],
      "verify": {
        "type": "js_eval",
        "expression": "document.querySelector('input[type=password]').value.length > 0"
      }
    },
    {
      "name": "EscalateToVisionLLM",
      "description": "Use AI vision to analyze and complete login",
      "escalate": {
        "type": "vision_llm",
        "prompt": "The password manager did not fill the password field. Please examine the page and complete the login process. Look for the password field and any autofill options.",
        "max_actions": 10,
        "timeout": 60000
      }
    }
  ],
  "on_all_strategies_failed": {
    "action": "screenshot",
    "description": "Capture failure state",
    "then": {"goto": "ManualLoginFallback"}
  }
}
```

**Fields:**
- `strategies` - Array of strategies to try in order
- `max_attempts_per_strategy` - Optional, default 1 (can retry same strategy)
- `backoff` - Optional backoff config for retries within same strategy
- `on_all_strategies_failed` - Action when all strategies exhausted

**Strategy Types:**

#### A. **Step-based Strategy**
Execute a sequence of steps and verify success.

```json
{
  "name": "StrategyName",
  "description": "What this strategy does",
  "steps": [...],
  "verify": {
    "type": "element_exists",
    "selector": ".success-indicator"
  }
}
```

#### B. **Escalation Strategy**
Delegate to a higher-level problem solver (Vision LLM, progressive escalation).

```json
{
  "name": "EscalateToVision",
  "escalate": {
    "type": "vision_llm",
    "prompt": "Please complete the task that automated steps could not accomplish",
    "max_actions": 10,
    "timeout": 60000
  }
}
```

#### C. **Alternative Approach Strategy**
Try completely different method (e.g., API call instead of UI).

```json
{
  "name": "UseAPIFallback",
  "alternative": {
    "type": "api_call",
    "method": "POST",
    "url": "https://api.example.com/login",
    "body": {
      "username": "${USERNAME}",
      "password": "${PASSWORD}"
    }
  }
}
```

**Escalation Types:**

| Type | Description | When to Use |
|------|-------------|-------------|
| `vision_llm` | Use multimodal LLM to solve visually | Element location unclear, CAPTCHA, complex UI |
| `progressive_escalation` | Use existing progressive escalation engine | Find element with vision assistance |
| `human_intervention` | Pause and request human help | Security verification, MFA |
| `api_fallback` | Switch to API instead of UI | UI automation too brittle |

---

### 3. `sequence` - Named Step Group

Group related steps with a label for readability and goto targets.

```json
{
  "name": "LoginFlow",
  "type": "sequence",
  "description": "Complete login process",
  "steps": [
    {"action": "fill", "selector": "#username", "value": "user@example.com"},
    {"action": "fill", "selector": "#password", "value": "password123"},
    {"action": "click", "selector": "button[type='submit']"}
  ]
}
```

**Use Cases:**
- Organize complex scripts into logical sections
- Create reusable goto targets
- Add descriptive names to multi-step operations

---

### 4. `goto` - Explicit Jump

Jump to a named step.

```json
{
  "type": "goto",
  "target": "SearchAddress"
}
```

**Use Cases:**
- Skip sections conditionally
- Jump to error handlers
- Loop back for retries (with loop protection)

---

### 5. `switch` - Multi-way Branch

Choose from multiple branches based on state (like switch/case).

```json
{
  "type": "switch",
  "name": "HandlePageType",
  "description": "Different actions based on which page appeared",
  "cases": [
    {
      "condition": {"type": "url_contains", "pattern": "/login"},
      "goto": "LoginFlow"
    },
    {
      "condition": {"type": "url_contains", "pattern": "/dashboard"},
      "goto": "SearchAddress"
    },
    {
      "condition": {"type": "element_exists", "selector": ".modal-overlay"},
      "steps": [
        {"action": "click", "selector": ".modal-close"},
        {"action": "wait", "duration": 500}
      ],
      "then": {"continue": true}
    }
  ],
  "default": {
    "action": "screenshot",
    "description": "Unknown page state",
    "then": {"goto": "ErrorHandler"}
  }
}
```

---

## Condition Types

All condition types support timeout and return boolean.

### Element-Based Conditions

#### `element_exists`
Check if element exists in DOM (may not be visible).

```json
{
  "type": "element_exists",
  "selector": ".user-menu",
  "timeout": 5000
}
```

#### `element_visible`
Check if element exists AND is visible.

```json
{
  "type": "element_visible",
  "selector": "button#submit",
  "timeout": 3000
}
```

#### `element_text`
Check element text content.

```json
{
  "type": "element_text",
  "selector": ".status-message",
  "contains": "Success"
}
```

```json
{
  "type": "element_text",
  "selector": "h1",
  "equals": "Welcome"
}
```

#### `element_count`
Count matching elements.

```json
{
  "type": "element_count",
  "selector": ".error-message",
  "min": 0,
  "max": 0
}
```

### URL-Based Conditions

#### `url_contains`
Check if URL contains substring.

```json
{
  "type": "url_contains",
  "pattern": "/dashboard"
}
```

#### `url_matches`
Check if URL matches regex pattern.

```json
{
  "type": "url_matches",
  "pattern": "^https://example\\.com/(dashboard|home)"
}
```

#### `url_equals`
Exact URL match.

```json
{
  "type": "url_equals",
  "url": "https://example.com/success"
}
```

### JavaScript-Based Conditions

#### `js_eval`
Evaluate arbitrary JavaScript expression.

```json
{
  "type": "js_eval",
  "expression": "document.querySelector('input[type=password]').value.length > 0"
}
```

```json
{
  "type": "js_eval",
  "expression": "localStorage.getItem('auth_token') !== null",
  "expected": true
}
```

### Logical Operators

#### `and`
All conditions must be true.

```json
{
  "type": "and",
  "conditions": [
    {"type": "element_exists", "selector": ".user-menu"},
    {"type": "url_contains", "pattern": "/dashboard"}
  ]
}
```

#### `or`
At least one condition must be true.

```json
{
  "type": "or",
  "conditions": [
    {"type": "element_exists", "selector": ".user-menu"},
    {"type": "element_exists", "selector": "#user-profile"},
    {"type": "url_contains", "pattern": "/logged-in"}
  ]
}
```

#### `not`
Invert condition result.

```json
{
  "type": "not",
  "condition": {
    "type": "element_exists",
    "selector": ".error-message"
  }
}
```

---

## Complete Example: BT Wholesale Login

```json
{
  "name": "BT Wholesale Broadband Availability",
  "version": "2.0.0",
  "workflow_version": "1.0",
  "description": "Extract broadband availability using adaptive login",

  "session": {
    "profile_name": "Bt_broadband",
    "clone_for_parallel": false,
    "requires_human_login": false,
    "session_timeout_hours": 24
  },

  "starting_page": "https://my.btwholesale.com/portalzone/portalzone/spa/#/portalzone/myApps",
  "abort_on_error": false,

  "steps": [
    {
      "type": "wait_for_load_state",
      "state": "networkidle",
      "timeout": 30000
    },

    {
      "type": "screenshot",
      "description": "Capture initial page state"
    },

    {
      "type": "if",
      "name": "CheckIfAlreadyLoggedIn",
      "description": "Skip login if session cookie is still valid",
      "condition": {
        "type": "or",
        "conditions": [
          {
            "type": "element_visible",
            "selector": ".user-menu",
            "timeout": 2000
          },
          {
            "type": "element_visible",
            "selector": "[data-testid='user-profile']",
            "timeout": 2000
          },
          {
            "type": "and",
            "conditions": [
              {"type": "url_contains", "pattern": "/myApps"},
              {
                "type": "not",
                "condition": {"type": "url_contains", "pattern": "/login"}
              }
            ]
          }
        ]
      },
      "then": {
        "action": "screenshot",
        "description": "Already logged in, skipping login flow",
        "then": {"goto": "SearchAddress"}
      }
    },

    {
      "name": "BeginLogin",
      "type": "sequence",
      "description": "Start login process with username",
      "steps": [
        {
          "action": "wait",
          "duration": 1000,
          "description": "Wait for login page to stabilize"
        },
        {
          "action": "fill",
          "selector": "input[type='text'][name*='user'], input[type='text'][name*='username'], input[type='email']",
          "value": "nterizakis",
          "description": "Fill username"
        },
        {
          "action": "click",
          "selector": "button[type='submit']",
          "description": "Click Next/Continue button"
        },
        {
          "action": "wait_for_load_state",
          "state": "networkidle",
          "timeout": 60000
        },
        {
          "action": "screenshot",
          "description": "Password page"
        }
      ]
    },

    {
      "type": "try",
      "name": "AttemptPasswordEntry",
      "description": "Try multiple strategies to enter password",
      "strategies": [
        {
          "name": "AutofillWithBrowserPasswordManager",
          "description": "Wait for browser autofill (passive)",
          "steps": [
            {
              "action": "wait",
              "duration": 2000,
              "description": "Wait for browser autofill to trigger"
            }
          ],
          "verify": {
            "type": "js_eval",
            "expression": "document.querySelector('input[type=password]').value.length > 0",
            "description": "Check if password was auto-filled"
          }
        },
        {
          "name": "TriggerPasswordManagerWithClick",
          "description": "Click password field with real mouse to open password manager",
          "steps": [
            {
              "action": "click",
              "selector": "input[type='password']",
              "trigger_autofill": true,
              "description": "Click with real mouse to trigger password manager"
            },
            {
              "action": "wait",
              "duration": 800,
              "description": "Wait for password manager dropdown"
            },
            {
              "action": "press",
              "keys": ["ArrowDown", "Enter"],
              "delay": 500,
              "description": "Select password from dropdown"
            }
          ],
          "verify": {
            "type": "js_eval",
            "expression": "document.querySelector('input[type=password]').value.length > 0"
          }
        },
        {
          "name": "TriggerPasswordManagerWithFocus",
          "description": "Try focusing field instead of clicking",
          "steps": [
            {
              "action": "execute_js",
              "code": "document.querySelector('input[type=password]').focus()",
              "description": "Focus password field programmatically"
            },
            {
              "action": "wait",
              "duration": 1000
            },
            {
              "action": "press",
              "keys": ["ArrowDown", "ArrowDown", "Enter"],
              "delay": 300
            }
          ],
          "verify": {
            "type": "js_eval",
            "expression": "document.querySelector('input[type=password]').value.length > 0"
          }
        },
        {
          "name": "DoubleClickPasswordField",
          "description": "Some password managers respond to double-click",
          "steps": [
            {
              "action": "click",
              "selector": "input[type='password']",
              "click_count": 2,
              "trigger_autofill": true,
              "description": "Double-click password field"
            },
            {
              "action": "wait",
              "duration": 1000
            },
            {
              "action": "press",
              "keys": ["Enter"]
            }
          ],
          "verify": {
            "type": "js_eval",
            "expression": "document.querySelector('input[type=password]').value.length > 0"
          }
        },
        {
          "name": "EscalateToVisionLLM",
          "description": "Use AI vision to analyze page and complete login",
          "escalate": {
            "type": "vision_llm",
            "prompt": "The automated password entry failed. Please examine the page and complete the login. The username 'nterizakis' has been entered. Look for the password field, check if there's a password manager dropdown, or if the password needs to be entered manually. If you see saved credentials, select them. Complete the login process.",
            "max_actions": 15,
            "timeout": 60000
          }
        }
      ],
      "on_all_strategies_failed": {
        "action": "screenshot",
        "description": "All password strategies failed",
        "then": {"goto": "LoginFailed"}
      }
    },

    {
      "action": "click",
      "selector": "button#next, button[type='submit']",
      "description": "Submit password"
    },

    {
      "action": "wait_for_load_state",
      "state": "networkidle",
      "timeout": 60000
    },

    {
      "type": "if",
      "name": "VerifyLoginSuccess",
      "description": "Check if login succeeded",
      "condition": {
        "type": "or",
        "conditions": [
          {"type": "element_exists", "selector": ".user-menu"},
          {"type": "url_contains", "pattern": "/dashboard"},
          {"type": "url_contains", "pattern": "/myApps"},
          {
            "type": "and",
            "conditions": [
              {
                "type": "not",
                "condition": {"type": "url_contains", "pattern": "/login"}
              },
              {
                "type": "not",
                "condition": {"type": "element_exists", "selector": ".error-message, .login-error"}
              }
            ]
          }
        ]
      },
      "then": {
        "action": "screenshot",
        "description": "Login successful",
        "then": {"goto": "SearchAddress"}
      },
      "else": {"goto": "LoginFailed"}
    },

    {
      "name": "LoginFailed",
      "type": "sequence",
      "description": "Handle login failure",
      "steps": [
        {
          "action": "screenshot",
          "description": "Capture failed login state"
        },
        {
          "action": "execute_js",
          "code": "console.error('Login failed after all strategies'); return {error: 'Login failed', url: window.location.href};",
          "description": "Log failure details"
        }
      ],
      "then": {
        "type": "error",
        "message": "Login failed after trying all strategies"
      }
    },

    {
      "name": "SearchAddress",
      "type": "sequence",
      "description": "Main workflow - search for broadband availability",
      "steps": [
        {
          "action": "act",
          "prompt": "Click on the 'Enhanced Broadband Availability Checker' or 'Open App' button for the broadband availability tool. It's usually on the bottom right of the screen.",
          "description": "Navigate to broadband checker"
        },
        {
          "action": "wait_for_load_state",
          "state": "networkidle"
        },
        {
          "action": "screenshot",
          "description": "Broadband checker page"
        },
        {
          "action": "act",
          "prompt": "Click on the 'Address Checker' tab if not already selected, then fill in the form: Building Number = '1', Street/Road = 'Church View', PostCode = 'DN12 1RH'. Click the Submit button.",
          "description": "Search by address"
        },
        {
          "action": "wait_for_load_state",
          "state": "networkidle",
          "timeout": 30000
        },
        {
          "action": "screenshot",
          "description": "Search results"
        },
        {
          "type": "if",
          "description": "Check if address selection list appeared",
          "condition": {
            "type": "or",
            "conditions": [
              {"type": "element_exists", "selector": ".address-list, .address-selection"},
              {"type": "element_text", "selector": "body", "contains": "Select address"}
            ]
          },
          "then": {
            "action": "act",
            "prompt": "Select the address that matches '1 Church View, DN12 1RH' from the list and click submit.",
            "description": "Select from address options"
          }
        },
        {
          "action": "wait_for_load_state",
          "state": "networkidle",
          "timeout": 30000
        },
        {
          "action": "screenshot",
          "description": "Final availability results"
        },
        {
          "action": "act_with_schema",
          "prompt": "Extract the broadband availability information from the current page. Look for maximum download speed, technology type (FTTC, FTTP, etc.), and whether broadband is available at this address.",
          "schema": {
            "type": "object",
            "properties": {
              "address": {
                "type": "string",
                "description": "The full address searched"
              },
              "available": {
                "type": "boolean",
                "description": "Whether broadband is available"
              },
              "technology": {
                "type": "string",
                "description": "Technology type (FTTC, FTTP, ADSL, etc.)"
              },
              "max_download_speed_mbps": {
                "type": "number",
                "description": "Maximum download speed in Mbps"
              },
              "max_upload_speed_mbps": {
                "type": "number",
                "description": "Maximum upload speed in Mbps"
              },
              "estimated_speed_range": {
                "type": "string",
                "description": "Speed range if provided (e.g., '50-80 Mbps')"
              }
            },
            "required": ["address", "available"]
          },
          "description": "Extract structured availability data"
        }
      ]
    }
  ]
}
```

---

## Workflow Execution Model

### Execution Flow

```
1. Parse workflow script
2. Build step index (map names to positions)
3. Validate workflow structure
4. Execute from step 0:

   For each step:
     - Check step type
     - If regular action → execute → next step
     - If conditional → evaluate → branch
     - If try → iterate strategies → execute → verify → next or escalate
     - If sequence → execute substeps → next step
     - If goto → jump to target step

5. Continue until:
   - All steps complete (success)
   - Error thrown (failure)
   - Abort condition met
```

### State Management

The workflow executor maintains:

```python
{
  "current_step_index": 0,
  "step_history": [0, 1, 2, 5],  # For debugging
  "loop_detection": {
    "5": 2,  # Step 5 visited 2 times
    "8": 1
  },
  "variables": {  # Future: store extracted data
    "login_status": "success",
    "search_results": {...}
  }
}
```

### Loop Protection

To prevent infinite loops:

```python
MAX_VISITS_PER_STEP = 10  # Configurable

if step_visits[step_index] > MAX_VISITS_PER_STEP:
    raise WorkflowError(f"Step {step_index} visited too many times - possible infinite loop")
```

---

## Strategy Selection Logic

For `try` blocks with multiple strategies:

```python
async def execute_try_block(self, step):
    strategies = step["strategies"]

    for strategy_index, strategy in enumerate(strategies):
        strategy_name = strategy.get("name", f"Strategy {strategy_index + 1}")

        print(f"  Attempting: {strategy_name}")

        try:
            # Execute strategy based on type
            if "steps" in strategy:
                # Step-based strategy
                await self._execute_strategy_steps(strategy)

            elif "escalate" in strategy:
                # Escalation strategy
                await self._execute_escalation(strategy["escalate"])

            elif "alternative" in strategy:
                # Alternative approach
                await self._execute_alternative(strategy["alternative"])

            # Verify success if verification specified
            if "verify" in strategy:
                success = await self.condition_evaluator.evaluate(
                    strategy["verify"],
                    self.executor.page
                )

                if not success:
                    print(f"  ✗ {strategy_name} failed verification")
                    continue  # Try next strategy

            # Success!
            print(f"  ✓ {strategy_name} succeeded")
            self.current_index += 1
            return

        except Exception as e:
            print(f"  ✗ {strategy_name} failed: {e}")
            # Continue to next strategy

    # All strategies failed
    print(f"  ✗ All {len(strategies)} strategies failed")

    if "on_all_strategies_failed" in step:
        await self._handle_failure_action(step["on_all_strategies_failed"])
    else:
        raise WorkflowError(f"Try block '{step.get('name', 'unnamed')}' exhausted all strategies")
```

---

## Escalation Patterns

### Vision LLM Escalation

When automated steps fail, delegate to multimodal LLM:

```json
{
  "escalate": {
    "type": "vision_llm",
    "prompt": "The automated login failed. Please examine the page and complete the login process.",
    "max_actions": 10,
    "timeout": 60000,
    "screenshot_interval": 5,
    "allow_keyboard": true,
    "allow_mouse": true
  }
}
```

**Implementation:**
```python
async def _execute_vision_escalation(self, config):
    prompt = config["prompt"]
    max_actions = config.get("max_actions", 10)
    timeout = config.get("timeout", 60000)

    # Take screenshot
    screenshot = await self.executor.page.screenshot()

    # Call vision LLM
    response = await self.vision_llm.analyze_and_act(
        screenshot=screenshot,
        prompt=prompt,
        max_actions=max_actions,
        page=self.executor.page
    )

    # Vision LLM executes actions and returns when done
    return response
```

### Progressive Escalation

Use existing progressive escalation engine:

```json
{
  "escalate": {
    "type": "progressive_escalation",
    "target": "Click the submit button",
    "max_attempts": 3
  }
}
```

### Human Intervention

Pause and request human help:

```json
{
  "escalate": {
    "type": "human_intervention",
    "message": "Please complete the two-factor authentication",
    "timeout": 300000,
    "resume_condition": {
      "type": "element_exists",
      "selector": ".dashboard"
    }
  }
}
```

---

## Error Handling

### Error Types

1. **Step Execution Error** - Individual step fails
2. **Strategy Exhaustion** - All strategies in try block fail
3. **Condition Evaluation Error** - Condition throws exception
4. **Timeout Error** - Operation exceeds time limit
5. **Infinite Loop Detected** - Same step visited too many times

### Error Recovery

```json
{
  "type": "try",
  "strategies": [...],
  "on_all_strategies_failed": {
    "type": "sequence",
    "steps": [
      {"action": "screenshot", "description": "Capture error state"},
      {
        "action": "execute_js",
        "code": "return {error: 'Strategy exhaustion', url: window.location.href, cookies: document.cookie};"
      }
    ],
    "then": {"goto": "ErrorHandler"}
  }
}
```

Global error handler:

```json
{
  "name": "ErrorHandler",
  "type": "sequence",
  "steps": [
    {"action": "screenshot"},
    {
      "action": "act",
      "prompt": "An error occurred. Please analyze the page state and determine if recovery is possible. If not, document the error clearly."
    }
  ]
}
```

---

## Migration Guide

### Converting Linear Scripts to Workflows

**Before (Linear):**
```json
{
  "steps": [
    {"action": "navigate", "url": "https://example.com/login"},
    {"action": "fill", "selector": "#username", "value": "user"},
    {"action": "fill", "selector": "#password", "value": "pass"},
    {"action": "click", "selector": "button[type='submit']"},
    {"action": "wait_for_load_state", "state": "networkidle"}
  ]
}
```

**After (Workflow with Validation):**
```json
{
  "workflow_version": "1.0",
  "steps": [
    {"action": "navigate", "url": "https://example.com/login"},

    {
      "type": "try",
      "strategies": [
        {
          "name": "StandardLogin",
          "steps": [
            {"action": "fill", "selector": "#username", "value": "user"},
            {"action": "fill", "selector": "#password", "value": "pass"},
            {"action": "click", "selector": "button[type='submit']"},
            {"action": "wait_for_load_state", "state": "networkidle"}
          ],
          "verify": {
            "type": "url_contains",
            "pattern": "/dashboard"
          }
        },
        {
          "name": "RetryWithDelay",
          "steps": [
            {"action": "wait", "duration": 2000},
            {"action": "fill", "selector": "#username", "value": "user"},
            {"action": "fill", "selector": "#password", "value": "pass"},
            {"action": "click", "selector": "button[type='submit']", "force": true},
            {"action": "wait_for_load_state", "state": "networkidle"}
          ],
          "verify": {
            "type": "url_contains",
            "pattern": "/dashboard"
          }
        }
      ]
    }
  ]
}
```

---

## Best Practices

### 1. Always Verify Success

Don't assume steps succeeded. Add verification:

```json
{
  "type": "try",
  "strategies": [{
    "steps": [...],
    "verify": {
      "type": "element_exists",
      "selector": ".success-message"
    }
  }]
}
```

### 2. Use Descriptive Names

Name all steps and strategies for debugging:

```json
{
  "name": "AttemptPasswordManagerLogin",
  "type": "try",
  "strategies": [
    {"name": "AutofillPassive"},
    {"name": "ClickWithRealMouse"},
    {"name": "EscalateToVision"}
  ]
}
```

### 3. Screenshot Before/After Critical Operations

```json
{
  "type": "sequence",
  "steps": [
    {"action": "screenshot", "description": "Before login"},
    {"action": "click", "selector": "button#login"},
    {"action": "wait_for_load_state", "state": "networkidle"},
    {"action": "screenshot", "description": "After login"}
  ]
}
```

### 4. Graceful Degradation

Order strategies from most efficient to most expensive:

```json
{
  "strategies": [
    {"name": "FastAutomatedMethod"},
    {"name": "SlowerAlternative"},
    {"name": "ExpensiveVisionLLM"},
    {"name": "ManualHumanIntervention"}
  ]
}
```

### 5. Set Realistic Timeouts

```json
{
  "condition": {
    "type": "element_exists",
    "selector": ".slow-loading-element",
    "timeout": 10000  // 10 seconds for slow elements
  }
}
```

### 6. Use Logical Operators for Robust Checks

```json
{
  "condition": {
    "type": "or",
    "conditions": [
      {"type": "element_exists", "selector": ".success-v1"},
      {"type": "element_exists", "selector": ".success-v2"},
      {"type": "url_contains", "pattern": "/success"}
    ]
  }
}
```

---

## Implementation Checklist

- [ ] `condition_evaluator.py` - All condition types
- [ ] `workflow_executor.py` - Main execution engine
- [ ] Step type handlers: `if`, `try`, `sequence`, `goto`, `switch`
- [ ] Strategy execution: step-based, escalation, alternative
- [ ] Loop detection and prevention
- [ ] Error handling and recovery
- [ ] Backward compatibility with linear scripts
- [ ] Integration tests for each workflow pattern
- [ ] Documentation and examples

---

## Future Enhancements

### Variables and Expressions

Store and reference values:

```json
{
  "action": "execute_js",
  "code": "return document.querySelector('.price').textContent",
  "store_as": "product_price"
},
{
  "action": "fill",
  "selector": "#budget",
  "value": "${product_price}"
}
```

### Parallel Execution

Run independent steps concurrently:

```json
{
  "type": "parallel",
  "branches": [
    {"action": "screenshot", "path": "page1.png"},
    {"action": "execute_js", "code": "return document.title", "store_as": "title"}
  ]
}
```

### Map/Iterate

Process arrays:

```json
{
  "type": "map",
  "items": "${product_urls}",
  "steps": [
    {"action": "navigate", "url": "${item}"},
    {"action": "screenshot"}
  ]
}
```

### External Step Functions Integration

Import full AWS Step Functions definitions:

```json
{
  "type": "step_functions",
  "definition_file": "complex_workflow.asl.json"
}
```
