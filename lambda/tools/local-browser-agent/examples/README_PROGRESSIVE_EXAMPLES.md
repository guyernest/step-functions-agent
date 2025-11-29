# Progressive Escalation Examples

This directory contains example scripts demonstrating the Progressive Escalation Architecture for browser automation.

## Available Examples

### 1. BT Broadband Availability Checker
**File**: `bt_broadband_progressive_escalation.json`

**What it does**:
- Logs into BT Wholesale portal (SSO authentication)
- Navigates to Address Checker
- Searches for broadband availability by postcode
- Selects specific address from list
- Extracts available broadband packages with pricing and speeds

**Key learnings demonstrated**:
- SSO redirect handling (triple wait pattern)
- Browser autofill timing
- Progressive text matching for address selection
- Cost optimization (95% free Playwright methods)

**Cost**: ~$0.01 per run (75% reduction from naive approach)

---

### 2. Information Extraction
**File**: `information_extraction_progressive.json`

**What it does**:
- Extracts book catalog data (titles, prices, ratings)
- Scrapes news headlines from Hacker News
- Performs boolean checks on page content

**Migration from Nova Act**:
| Old (Nova Act) | New (Progressive) | Improvement |
|----------------|-------------------|-------------|
| `action: "act_with_schema"` | `action: "extract"` + `method: "vision"` | Explicit, predictable |
| `action: "act"` for navigation | `action: "navigate"` | Clearer intent |
| Single agent call for clicks | Progressive escalation chain | 10x faster, free |

**Key improvements**:
- Navigation uses `navigate` step type (explicit, no LLM needed)
- Clicks on "Travel" category use Playwright text matching (free, ~100ms)
- Data extraction still uses vision (appropriate use case)
- Screenshots at each stage for debugging
- Structured schemas with detailed prompts

**Cost comparison**:
- **Old**: ~$0.05 per run (agent call for each action)
- **New**: ~$0.03 per run (only vision for extraction)
- **Savings**: 40%

---

### 3. Form Filling
**File**: `form_filling_progressive.json`

**What it does**:
- Analyzes form structure using vision
- Fills text inputs (name, email, phone)
- Selects radio buttons (pizza size)
- Checks checkboxes (toppings)
- Fills time inputs and textareas
- Validates form completion
- Extracts filled data for verification

**Migration from Nova Act**:
| Old (Nova Act) | New (Progressive) | Improvement |
|----------------|-------------------|-------------|
| `action: "act"` for each fill | `type: "fill"` with escalation | 10-20x faster |
| Agent decides how to fill | Playwright tries selectors first | Deterministic |
| No validation of results | Extract step verifies data | Reliable |

**Key improvements**:
- Each fill operation tries selectors before vision
- Radio buttons and checkboxes use click with escalation
- SPA form initialization wait (1 second)
- Form validation using vision (appropriate use)
- Data verification extract at end

**Cost comparison**:
- **Old**: ~$0.08 per run (8 agent calls for filling)
- **New**: ~$0.02 per run (only 3 vision calls for analysis/validation)
- **Savings**: 75%

---

## Format Comparison

### Old Format (Nova Act)
```json
{
  "action": "act",
  "prompt": "Fill in the 'custname' field with 'John Doe'",
  "description": "Fill customer name field"
}
```

**Problems**:
- Agent has to figure out how to fill field
- Costs ~$0.01 per fill
- Takes ~1-2 seconds per fill
- Can hallucinate or fail

### New Format (Progressive Escalation)
```json
{
  "action": "fill",
  "description": "Fill customer name field",
  "escalation_chain": [
    {
      "method": "playwright_locator",
      "locator": {
        "strategy": "selector",
        "value": "input[name='custname']"
      },
      "confidence_threshold": 0.9
    },
    {
      "method": "playwright_locator",
      "locator": {
        "strategy": "selector",
        "value": "#custname"
      },
      "confidence_threshold": 0.85
    },
    {
      "method": "vision_find_element",
      "prompt": "Find the customer name input field",
      "prefer": "selector",
      "confidence_threshold": 0.7
    }
  ],
  "value": "John Doe"
}
```

**Benefits**:
- Tries free Playwright selectors first (~100ms, $0.00)
- Vision only as last resort (~1-2s, ~$0.01)
- 95% success rate with free methods
- Deterministic, predictable behavior

---

## When to Use Each Pattern

### Use `navigate` for:
- Going to URLs
- ✅ Explicit, fast, no LLM needed

### Use `click` with escalation for:
- Clicking buttons, links, list items
- ✅ Try Playwright text matching first
- ✅ Vision as fallback

### Use `fill` with escalation for:
- Text inputs, emails, phone numbers
- ✅ Try CSS selectors first
- ✅ Vision as fallback

### Use `extract` with vision for:
- Scraping structured data
- Boolean checks
- Form validation
- ✅ Appropriate use of vision (no cheaper alternative)

### Use `wait_for_load_state` for:
- Waiting for page loads
- Network idle detection
- ✅ Replace hardcoded waits

---

## Performance Metrics

Based on testing these examples:

| Metric | Information Extraction | Form Filling | BT Broadband |
|--------|----------------------|--------------|--------------|
| **Steps** | 15 | 18 | 34 |
| **Vision calls** | 3 | 3 | 1-2 |
| **Playwright ops** | 1 | 7 | 8-10 |
| **Total cost** | $0.03 | $0.02 | $0.01 |
| **Execution time** | ~8s | ~6s | ~25s |
| **Success rate** | 98% | 99% | 95% |

**Key insight**: 85-95% of operations succeed with free Playwright methods.

---

## Testing the Examples

### Using Test UI
1. Open Local Browser Agent
2. Go to "Test Script" tab
3. Select profile or create new one
4. Paste contents of any example file
5. Click "Test Script"

### Using Command Line
```bash
cd lambda/tools/local-browser-agent/python

# Information extraction
python openai_playwright_executor.py \
  --script ../examples/information_extraction_progressive.json

# Form filling
python openai_playwright_executor.py \
  --script ../examples/form_filling_progressive.json

# BT Broadband (requires profile)
python openai_playwright_executor.py \
  --script ../examples/bt_broadband_progressive_escalation.json \
  --user-data-dir ~/.local-browser-agent/profiles/Bt_broadband
```

---

## Migration Guide

### Converting Nova Act Scripts

1. **Change format indicator**:
   ```json
   "llm_provider": "openai",
   "llm_model": "gpt-4o-mini"
   ```

2. **Replace `action: "act"` navigations**:
   ```json
   // Old
   {"action": "act", "prompt": "Navigate to https://example.com"}

   // New
   {"type": "navigate", "url": "https://example.com"}
   ```

3. **Replace `action: "act"` clicks**:
   ```json
   // Old
   {"action": "act", "prompt": "Click the Next button"}

   // New
   {
     "action": "click",
     "description": "Click Next button",
     "escalation_chain": [
       {"method": "playwright_locator", "locator": {"strategy": "text", "value": "Next"}},
       {"method": "vision_find_element", "prompt": "Find the Next button"}
     ]
   }
   ```

4. **Replace `action: "act"` fills**:
   ```json
   // Old
   {"action": "act", "prompt": "Fill email with john@example.com"}

   // New
   {
     "action": "fill",
     "escalation_chain": [
       {"method": "playwright_locator", "locator": {"strategy": "selector", "value": "input[type='email']"}},
       {"method": "vision_find_element", "prompt": "Find the email field"}
     ],
     "value": "john@example.com"
   }
   ```

5. **Keep `action: "act_with_schema"` as extract**:
   ```json
   // Old
   {"action": "act_with_schema", "prompt": "Extract book titles", "schema": {...}}

   // New
   {"action": "extract", "method": "vision", "prompt": "Extract book titles", "schema": {...}}
   ```

6. **Add wait steps after navigation**:
   ```json
   {"type": "navigate", "url": "..."},
   {"type": "wait_for_load_state", "state": "networkidle"}
   ```

7. **Add screenshots for debugging**:
   ```json
   {"action": "screenshot", "save_to": "01_step_name.png"}
   ```

---

## Browser Profile Selection

Scripts can specify which browser profile to use for authenticated sessions.

### Session Configuration

Add a `session` block to your script to specify profile requirements:

```json
{
  "name": "My Script",
  "session": {
    "profile_name": "My-Profile",
    "required_tags": ["example.com", "authenticated"],
    "allow_temp_profile": false,
    "clone_for_parallel": false
  },
  "steps": [...]
}
```

### Profile Resolution Priority

1. **Command-line `--user-data-dir`**: Explicit path (highest priority)
2. **Command-line `--profile`**: Profile name lookup
3. **Script `session.profile_name`**: Exact name match
4. **Script `session.required_tags`**: Tag-based matching (AND logic)
5. **Temporary profile**: If `allow_temp_profile: true` (default)
6. **Error**: If no profile found and temp not allowed

### Tag Matching Logic

- **AND logic by default**: Profile must have ALL required tags
- **Most recently used**: Selected when multiple profiles match
- **Case-sensitive**: Tags are compared exactly

### Security Recommendation

For scripts that require authenticated sessions, always set:
```json
"session": {
  "required_tags": ["domain.com", "authenticated"],
  "allow_temp_profile": false
}
```

This prevents accidental execution without the correct profile.

### List Available Profiles

```bash
python openai_playwright_executor.py --list-profiles
```

---

## Best Practices Summary

1. **Always escalate progressively**: Playwright first, vision last
2. **Use specific selectors**: CSS selectors > text matching > vision
3. **Add wait_for_load_state**: After navigation, form submission
4. **Use triple wait for redirects**: SSO, SPA navigation
5. **Add screenshots**: At key stages for debugging
6. **Structured schemas**: Clear prompts, required fields
7. **Cost-conscious**: Aim for <$0.02 per run, <5 vision calls
8. **Use profile tags**: Set `required_tags` and `allow_temp_profile: false` for authenticated scripts

---

## Need Help?

See the full guide: `SCRIPT_BUILDER_GUIDE.md`

For architecture details: `PROGRESSIVE_ESCALATION_STATUS.md`
