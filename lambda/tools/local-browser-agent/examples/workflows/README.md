# Workflow Engine Examples

This directory contains production-ready workflow examples demonstrating the intelligent retry and conditional logic capabilities of the Browser Agent Workflow Engine.

## Overview

The workflow engine extends simple linear scripts with:
- **Conditional branching** (if/else, switch/case)
- **Intelligent retry** with multiple strategies
- **Progressive escalation** (cheap methods → expensive methods → vision LLM)
- **Graceful failure handling**
- **Authentication state checking**
- **Dynamic field lookup**

These capabilities make scripts resilient to common real-world problems like:
- Form structure changes
- Field ID/name changes
- Broken or moved links
- Empty search results
- A/B testing variants
- Login challenges

---

## Example Files

### 01_form_structure_changed.json
**Problem**: Form fields frequently change IDs during redesigns
**Solution**: Try multiple locator strategies in priority order

**Key Patterns**:
- Try new field ID first (fastest)
- Fallback to old field ID
- Use name attribute (more stable)
- Use placeholder text (universal)
- Final escalation to vision LLM

**When to Use**: Any form that undergoes frequent updates or redesigns

**Learnings for Developers**:
- Always include multiple fallback selectors
- Order strategies from most specific → most general
- Include vision LLM as final fallback
- Use `verify` conditions to confirm success

---

### 02_search_no_results.json
**Problem**: Search queries that return no results need graceful handling
**Solution**: Detect no-results state and try broader searches

**Key Patterns**:
- Detect no-results with multiple conditions (`or` operator)
- Try progressively broader search terms
- Extract available categories as alternative
- Different handling for results vs no-results

**When to Use**: Any search functionality, product catalogs, directory lookups

**Learnings for Developers**:
- Use `if/else` to branch on results presence
- Chain sequences for complex fallback logic
- Always capture state with screenshots
- Extract alternatives when primary goal fails

---

### 03_broken_link_fallback.json
**Problem**: Links move, break, or get removed during site updates
**Solution**: Try multiple navigation paths to reach destination

**Key Patterns**:
- Try direct link (fastest)
- Navigate through menu (more reliable)
- Direct URL navigation (bypass UI)
- Search for page
- Vision LLM navigation

**When to Use**: Navigation to specific pages, deep-linked content

**Learnings for Developers**:
- Navigation hierarchy: link → menu → URL → search → AI
- Verify URL AND absence of 404 errors
- Use `and`/`not` for complex conditions
- Extract navigation options on total failure

---

### 04_login_with_auth_check.json
**Problem**: Repeated logins waste time and can trigger rate limits
**Solution**: Check authentication state before attempting login

**Key Patterns**:
- Check for logged-in indicators (user menu, logout button)
- Skip login if already authenticated
- Use `goto` to jump to main workflow
- Multiple login strategies (password manager, manual, AI)

**When to Use**: Any authenticated application

**Learnings for Developers**:
- Always check auth state first
- Use named steps for goto targets
- Verify login success before proceeding
- Capture auth failures for debugging

**Critical Pattern**:
```json
{
  "type": "if",
  "name": "Check if already logged in",
  "condition": {
    "type": "or",
    "conditions": [
      {"type": "element_visible", "selector": "#user-menu"},
      {"type": "url_contains", "pattern": "/dashboard"}
    ]
  },
  "then": {"goto": "MainWorkflow"},
  "else": {"continue": true}
}
```

---

### 05_field_name_changed.json
**Problem**: Input field names change due to A/B tests, internationalization, etc.
**Solution**: Try multiple naming conventions and locator strategies

**Key Patterns**:
- Try all common field name variants
- Use semantic selectors (aria-label, type)
- Use switch/case for form variants
- Debug by listing all inputs on failure

**When to Use**: International sites, A/B tested forms, dynamic forms

**Learnings for Developers**:
- Combine multiple selector strategies in one (`#id1, #id2, #id3`)
- Use `switch` for detecting form variants
- Extract input metadata for debugging
- Vision LLM for truly dynamic content

**Debug Pattern**:
```json
{
  "action": "execute_js",
  "description": "Debug: List all input fields",
  "script": "return Array.from(document.querySelectorAll('input')).map(el => ({name: el.name, id: el.id, type: el.type, placeholder: el.placeholder}));"
}
```

---

### 06_bt_wholesale_workflow.json
**Problem**: Production BT Wholesale login with password manager issues
**Solution**: Complete production workflow combining all patterns

**Key Patterns**:
- Authentication state check (skip login if already logged in)
- Real mouse click for password manager (`trigger_autofill: true`)
- Multiple login strategies with progressive escalation
- Postcode field lookup with fallbacks
- No-results vs results handling
- Comprehensive error capture

**When to Use**: Template for production workflows with authentication

**Learnings for Developers**:
- Real mouse clicks needed for password managers
- Always verify credentials were filled
- Use `execute_js` to check form state
- Separate concerns: auth → navigation → action → extraction

**Password Manager Pattern**:
```json
{
  "action": "click",
  "description": "Click with real mouse for autofill",
  "locator": {"strategy": "selector", "value": "#username"},
  "trigger_autofill": true
},
{
  "action": "wait",
  "description": "Wait for dropdown",
  "duration": 1500
},
{
  "action": "press",
  "keys": "ArrowDown"
},
{
  "action": "press",
  "keys": "Enter"
}
```

---

## Common Patterns

### 1. Progressive Escalation
Start with cheap/fast methods, escalate to expensive/slow methods:

```
Try 1: Simple selector (milliseconds, free)
Try 2: Alternative selector (milliseconds, free)
Try 3: Progressive escalation (seconds, free)
Try 4: Vision LLM (seconds, costs $)
```

### 2. Multi-Condition Verification
Use logical operators for robust conditions:

```json
{
  "type": "and",
  "conditions": [
    {"type": "url_contains", "pattern": "/success"},
    {"type": "element_visible", "selector": ".confirmation"},
    {"type": "not", "condition": {"type": "element_visible", "selector": ".error"}}
  ]
}
```

### 3. Named Steps with Goto
Skip unnecessary steps or handle different flows:

```json
[
  {
    "type": "if",
    "condition": {"type": "element_visible", "selector": ".logged-in"},
    "then": {"goto": "MainWorkflow"}
  },
  {"name": "Login", "action": "fill", ...},
  {"name": "MainWorkflow", "action": "extract", ...}
]
```

### 4. Failure Capture
Always capture state on failure for debugging:

```json
{
  "on_all_strategies_failed": {
    "type": "sequence",
    "steps": [
      {"action": "screenshot"},
      {"action": "execute_js", "script": "return {debug: ...}"}
    ],
    "then": {"action": "error", "message": "Descriptive error"}
  }
}
```

---

## Advanced Features

### Step-Level Retry
In addition to strategy-level retry (trying different approaches), individual steps support transient failure retry:

```json
{
  "action": "click",
  "locator": {"strategy": "selector", "value": "#submit-button"},
  "retry": {
    "attempts": 3,
    "delay_ms": 500
  }
}
```

**When to use**:
- **Step-level retry**: For transient failures (network delays, slow page loads, race conditions)
- **Strategy-level retry**: For trying fundamentally different approaches (different selectors, escalation)

**Example**:
```json
{
  "type": "try",
  "strategies": [
    {
      "name": "Click with short timeout",
      "steps": [
        {
          "action": "click",
          "locator": {"strategy": "selector", "value": "#button"},
          "retry": {
            "attempts": 3,
            "delay_ms": 500
          }
        }
      ]
    },
    {
      "name": "Progressive escalation",
      "escalate": {"type": "progressive_escalation", "target": "#button"}
    }
  ]
}
```

### Password Manager Autofill Heuristics

The executor automatically detects login fields and triggers password manager UI with real mouse interactions:

**Auto-detection triggers**:
- Input fields with `type="password"`
- Inputs with `autocomplete="username"` or `autocomplete="email"`
- Inputs with name/id matching: `username`, `email`, `user`, `login`, `userid`
- Inputs with name/id matching: `password`, `pass`, `pwd`

**Behavior**:
1. Brings page to front
2. Focuses the input field
3. Performs human-like mouse sequence:
   - Move to center of field
   - Hover for 500ms (allows password manager dropdown to appear)
   - Mouse down
   - Hold for 100ms
   - Mouse up

**Manual trigger**:
```json
{
  "action": "click",
  "locator": {"strategy": "selector", "value": "#username"},
  "trigger_autofill": true
}
```

**Why this matters**:
- Programmatic clicks (`locator.click()`) don't trigger password managers
- Browser automation flags can block password manager UI
- Real mouse events bypass these restrictions

**Best practice**:
```json
{
  "type": "try",
  "name": "Login",
  "strategies": [
    {
      "name": "Password manager autofill",
      "steps": [
        {
          "action": "click",
          "locator": {"strategy": "selector", "value": "#username"},
          "trigger_autofill": true
        },
        {
          "action": "wait",
          "duration": 1500
        },
        {
          "action": "press",
          "keys": "ArrowDown"
        },
        {
          "action": "press",
          "keys": "Enter"
        }
      ],
      "verify": {
        "type": "js_eval",
        "expression": "document.querySelector('#password')?.value?.length > 0"
      }
    }
  ]
}
```

### Browser Launch Optimization

The executor automatically configures browser launch to allow password managers and other browser features:

**What's removed**:
- `--enable-automation` flag (blocks password managers in some browsers)
- `--disable-component-extensions-with-background-pages` (blocks browser extensions)

**What this enables**:
- Password manager dropdowns in Edge/Chrome
- Browser extension functionality
- More native browser behavior

**Profile support**:
```json
{
  "session": {
    "profile_name": "my-work-profile",
    "clone_for_parallel": false
  }
}
```

Profiles preserve:
- Saved passwords
- Cookies/sessions
- Browser extensions
- Bookmarks
- History

---

## Testing Workflows Locally

### Using the Test UI

1. Open the Browser Agent application
2. Go to Test tab
3. Load one of these workflow JSON files
4. Click "Run Test"
5. Watch the execution logs for:
   - Which strategies succeed/fail
   - How long each strategy takes
   - What conditions evaluate to
   - When escalation occurs

### Using the CLI

```bash
cd /Users/guy/projects/step-functions-agent/lambda/tools/local-browser-agent

# Test with real BT Wholesale
python3 python/openai_playwright_executor.py \
  examples/workflows/06_bt_wholesale_workflow.json

# Test form handling
python3 python/openai_playwright_executor.py \
  examples/workflows/01_form_structure_changed.json
```

### Debugging Failed Workflows

When a workflow fails:

1. **Check the screenshot** captured on failure
2. **Review the execute_js output** showing page state
3. **Check the condition evaluation logs** in stderr
4. **Look at which strategy failed** and why
5. **Try the next cheaper strategy** before adding expensive ones

---

## Best Practices for Creating New Workflows

### 1. Start Simple, Add Complexity
Don't start with complex workflows. Build progressively:

1. Write linear script (no workflow features)
2. Test it manually
3. Identify points of failure
4. Add `try` blocks for those points
5. Add `if` checks for conditional logic
6. Add vision LLM as last resort

### 2. Order Strategies by Cost
Always order retry strategies from cheapest to most expensive:

```
Fast + Free:
- Simple selectors
- Alternative selectors
- Name/ID variants

Medium Speed + Free:
- Progressive escalation
- JavaScript evaluation

Slow + Costs Money:
- Vision LLM
```

### 3. Verify Everything
Add `verify` conditions to every strategy:

```json
{
  "name": "Fill email field",
  "steps": [{...}],
  "verify": {
    "type": "element_exists",
    "selector": "input[name='email'][value='user@example.com']"
  }
}
```

### 4. Capture Failure State
Always include failure handlers:

```json
{
  "on_all_strategies_failed": {
    "action": "screenshot",
    "then": {
      "action": "execute_js",
      "script": "return {pageState: ...}",
      "then": {
        "action": "error",
        "message": "Clear description of what failed"
      }
    }
  }
}
```

### 5. Use Descriptive Names
Every step should have clear name and description:

```json
{
  "name": "Login with Password Manager",
  "description": "Use saved credentials via real mouse click",
  "type": "try",
  "strategies": [...]
}
```

### 6. Test Each Strategy Independently
Before combining strategies in `try` block, test each one individually in a linear script.

### 7. Document Your Assumptions
Add comments (in description fields) about why certain strategies exist:

```json
{
  "description": "Click password field instead of username - works better on some Chrome versions",
  "steps": [...]
}
```

---

## Condition Types Reference

### Element Conditions
- `element_exists`: Element in DOM (may not be visible)
- `element_visible`: Element exists AND visible
- `element_text`: Check text content (contains or equals)
- `element_count`: Count matching elements (min, max, exact)

### URL Conditions
- `url_contains`: URL contains substring
- `url_matches`: URL matches regex pattern
- `url_equals`: URL exactly matches

### JavaScript Conditions
- `js_eval`: Evaluate JavaScript expression, compare result

### Logical Operators
- `and`: All conditions must be true
- `or`: At least one condition must be true
- `not`: Invert condition result

---

## Escalation Types Reference

### vision_llm
Use OpenAI Vision model to visually navigate page:

```json
{
  "escalate": {
    "type": "vision_llm",
    "prompt": "Find the email field and enter 'user@example.com'",
    "timeout": 30000,
    "max_actions": 10
  }
}
```

### progressive_escalation
Use existing progressive escalation engine for clicking:

```json
{
  "escalate": {
    "type": "progressive_escalation",
    "target": "button:has-text('Submit')"
  }
}
```

### human_intervention
Pause and wait for human to complete action:

```json
{
  "escalate": {
    "type": "human_intervention",
    "message": "Please solve the CAPTCHA",
    "timeout": 300000,
    "resume_condition": {
      "type": "element_visible",
      "selector": ".captcha-solved"
    }
  }
}
```

---

## Troubleshooting

### "Workflow not detected"
- Ensure at least one step has `"type"` field set to workflow type
- Workflow types: `if`, `try`, `sequence`, `goto`, `switch`
- Regular action steps don't need `"type"` field

### "Strategy verification failed"
- Check your `verify` condition is correct
- Add `timeout` to conditions if element might be slow to appear
- Use `execute_js` to debug what's actually on the page

### "All strategies exhausted"
- Review screenshot from `on_all_strategies_failed`
- Check if page structure changed
- Add more fallback strategies
- Consider if vision LLM is needed

### "goto target not found"
- Ensure target step has `"name"` field
- Step names are case-sensitive
- Use `goto` inside `then`, not as standalone step

### "Password manager not appearing"
- Use `trigger_autofill: true` on click action
- Increase wait duration after click (1000-1500ms)
- Check that profile has saved credentials
- Verify profile_name in session config

---

## Contributing

When creating new workflow examples:

1. **Test thoroughly** with real websites
2. **Document the problem** being solved
3. **Explain each strategy** and why it exists
4. **Include failure handling**
5. **Add to this README** with key learnings
6. **Follow naming convention**: `NN_descriptive_name.json`

---

## Additional Resources

- [Workflow Engine Design](../../WORKFLOW_ENGINE_DESIGN.md) - Complete technical specification
- [Condition Evaluator](../../python/condition_evaluator.py) - All condition types
- [Workflow Executor](../../python/workflow_executor.py) - Execution engine
- [OpenAI Executor Integration](../../python/openai_playwright_executor.py) - How workflows execute

---

## Future Suggestions & Improvements

### 1. Workflow Step Results Tracking
**Current State**: Workflow mode tracks execution counters but doesn't populate `step_results[]` array like linear mode does.

**Proposed Enhancement**:
Add optional result logging to WorkflowExecutor:

```python
class WorkflowExecutor:
    def __init__(self, script, executor):
        self.step_results = []  # Track individual step results

    async def execute_action_step(self, step):
        result = await self.executor.execute_step(step)
        self.step_results.append({
            "step_number": self.total_steps_executed,
            "step_name": step.get("name", "unnamed"),
            "step_type": step.get("type", step.get("action")),
            "success": result.get("success"),
            "error": result.get("error"),
            "duration_ms": result.get("duration_ms")
        })
```

**Benefits**:
- Detailed debugging of which steps succeeded/failed
- Performance profiling per step
- Better error reporting
- Audit trail for compliance

**Priority**: Medium - valuable for debugging complex workflows

---

### 2. Configurable Autofill Timing
**Current State**: Password manager autofill uses hardcoded timing (500ms hover, 100ms button hold).

**Proposed Enhancement**:
Make timing configurable per-site or globally:

```json
{
  "action": "click",
  "locator": {"strategy": "selector", "value": "#username"},
  "trigger_autofill": true,
  "autofill_timing": {
    "hover_ms": 750,
    "button_hold_ms": 150
  }
}
```

**Use cases**:
- Slow-loading sites need longer hover
- Some password managers are faster than others
- Different browsers have different timing sensitivities

**Priority**: Low - current defaults work for most cases

---

### 3. Strategy Cost Metrics
**Current State**: Strategies are tried in order, but no visibility into cost/duration.

**Proposed Enhancement**:
Track and report strategy costs:

```json
{
  "escalation_stats": {
    "strategies_attempted": 3,
    "strategy_costs": [
      {"name": "Simple selector", "duration_ms": 120, "llm_calls": 0, "cost_usd": 0},
      {"name": "Progressive escalation", "duration_ms": 2500, "llm_calls": 0, "cost_usd": 0},
      {"name": "Vision LLM", "duration_ms": 4200, "llm_calls": 2, "cost_usd": 0.008}
    ],
    "total_cost_usd": 0.008
  }
}
```

**Benefits**:
- Cost optimization insights
- Performance bottleneck identification
- Budget tracking for LLM usage

**Priority**: Medium - valuable for cost-conscious deployments

---

### 4. Human Intervention UI
**Current State**: Human intervention escalation exists but only waits for timeout or resume condition.

**Proposed Enhancement**:
Interactive UI for human intervention:
- Desktop notification when human help needed
- Visual indicator on page showing what needs to be done
- "Resume" button to continue workflow after human action
- Screen recording of human action for script generation

**Benefits**:
- CAPTCHA solving
- Complex multi-step processes
- Learning from human demonstrations

**Priority**: High - critical for handling CAPTCHAs and edge cases

---

### 5. Workflow Templates Library
**Current State**: Examples exist but no structured template system.

**Proposed Enhancement**:
Create a templates library with common patterns:

```
templates/
├── login/
│   ├── password-manager.json
│   ├── oauth.json
│   └── mfa.json
├── forms/
│   ├── multi-step-form.json
│   └── dynamic-fields.json
├── search/
│   ├── with-filters.json
│   └── no-results-fallback.json
└── navigation/
    ├── breadcrumb.json
    └── broken-link-recovery.json
```

**Benefits**:
- Faster workflow development
- Consistent patterns across team
- Best practices codified

**Priority**: Medium - improves developer productivity

---

### 6. Visual Workflow Editor
**Current State**: Workflows are hand-written JSON.

**Proposed Enhancement**:
Drag-and-drop workflow editor in the UI:
- Visual representation of if/else branches
- Strategy blocks with fallback arrows
- Condition builder (no JSON required)
- Test execution with step-by-step visualization

**Benefits**:
- Lower barrier to entry
- Faster iteration
- Visual debugging

**Priority**: Low - JSON works well for technical users, nice-to-have for less technical users

---

### 7. Workflow Composition & Reusability
**Current State**: Workflows are monolithic JSON files.

**Proposed Enhancement**:
Support workflow composition:

```json
{
  "type": "include",
  "workflow": "workflows/shared/login.json",
  "variables": {
    "USERNAME": "{{MY_USERNAME}}",
    "PASSWORD": "{{MY_PASSWORD}}"
  }
}
```

**Benefits**:
- DRY principle for common patterns
- Shared login flows across scripts
- Easier maintenance

**Priority**: Medium - valuable for large-scale deployments

---

### 8. Retry Budget System
**Current State**: Strategies retry until exhausted, could be expensive.

**Proposed Enhancement**:
Global retry budget to limit costs:

```json
{
  "retry_budget": {
    "max_total_llm_calls": 5,
    "max_total_duration_ms": 60000,
    "max_cost_usd": 0.10
  }
}
```

**Benefits**:
- Cost control
- Prevent runaway workflows
- Guaranteed upper bounds

**Priority**: High - critical for production deployments with LLM costs

---

**Remember**: The goal is to create workflows that are *resilient* to change, not perfect scripts that only work once. Real websites change constantly - your workflows should adapt automatically.
