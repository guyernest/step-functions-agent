# Script Builder Guide: Progressive Escalation Best Practices

## Overview

This guide documents best practices for building browser automation scripts using the Progressive Escalation Architecture. These patterns were learned from implementing the BT Broadband availability checker.

## Core Principle: Escalate Intelligently

**Always try cheap methods before expensive ones:**
1. DOM checks (free, ~10ms)
2. Playwright locators (free, ~100ms)
3. LLM Vision ($$, ~1-2s)

## Pattern 1: Click with Text Matching (Most Common)

### ❌ Bad: Jump to Vision
```json
{
  "type": "click",
  "escalation_chain": [
    {
      "method": "vision_find_element",
      "prompt": "Find the Next button"
    }
  ]
}
```
**Problem**: Costs $0.01 and takes 1-2s for something Playwright can do for free in 100ms.

### ✅ Good: Progressive Escalation
```json
{
  "type": "click",
  "description": "Click Next button",
  "escalation_chain": [
    {
      "method": "playwright_locator",
      "locator": {"strategy": "selector", "value": "button[type='submit']"},
      "confidence_threshold": 0.9
    },
    {
      "method": "playwright_locator",
      "locator": {"strategy": "text", "value": "Next"},
      "confidence_threshold": 0.9
    },
    {
      "method": "playwright_locator",
      "locator": {"strategy": "text", "value": "Continue"},
      "confidence_threshold": 0.85
    },
    {
      "method": "vision_find_element",
      "prompt": "Find the submit/next/continue button",
      "prefer": "selector",
      "confidence_threshold": 0.7
    }
  ]
}
```
**Result**: 95% of the time succeeds with free Playwright, vision only as last resort.

## Pattern 2: Address/List Selection with Partial Text Match

### Key Learning: Use Text Fragments
When selecting from a list (addresses, products, etc.), use **distinctive text fragments** that are likely to be unique.

### ❌ Bad: Extract then Click
```json
{
  "type": "extract",
  "method": "vision",
  "execute_action": true,
  "prompt": "Find the address '12 CHATSWORTH ROAD, BIRKENHEAD' and click it"
}
```
**Problem**:
- Costs $0.01 for vision API call
- Takes 1-2s
- Vision might hallucinate or return wrong format

### ✅ Good: Progressive Text Matching
```json
{
  "type": "click",
  "description": "Select matching address from list",
  "escalation_chain": [
    {
      "method": "playwright_locator",
      "locator": {"strategy": "text", "value": "12 CHATSWORTH ROAD"},
      "confidence_threshold": 0.9
    },
    {
      "method": "playwright_locator",
      "locator": {"strategy": "text", "value": "CHATSWORTH ROAD"},
      "confidence_threshold": 0.85
    },
    {
      "method": "playwright_locator",
      "locator": {"strategy": "text", "value": "BIRKENHEAD"},
      "confidence_threshold": 0.8
    },
    {
      "method": "vision_find_element",
      "prompt": "Find the list item matching '12 CHATSWORTH ROAD, BIRKENHEAD'",
      "prefer": "text",
      "confidence_threshold": 0.7
    }
  ]
}
```

**How it works**:
- Playwright's `get_by_text()` uses partial matching (exact=False)
- Tries most specific fragment first ("12 CHATSWORTH ROAD")
- Falls back to broader matches ("CHATSWORTH ROAD", "BIRKENHEAD")
- Vision only if all Playwright attempts fail

**Real-world result**: Vision success rate dropped from 100% to <5%, saving $0.01 per execution.

## Pattern 3: JavaScript Redirects (SSO, SPA Navigation)

### Key Learning: Network Idle ≠ Navigation Complete

Modern web apps often have multi-stage JavaScript redirects where:
1. Form submission completes (network idle)
2. JavaScript processes response (active)
3. JavaScript triggers redirect (active)
4. New page loads (network idle again)

### ❌ Bad: Single Wait
```json
{
  "type": "click",
  "description": "Click submit"
},
{
  "type": "wait_for_load_state",
  "state": "networkidle"
},
{
  "type": "screenshot"
}
```
**Problem**: Takes screenshot before JavaScript redirect completes.

### ✅ Good: Triple Wait Pattern
```json
{
  "type": "click",
  "description": "Click submit button"
},
{
  "type": "wait_for_load_state",
  "description": "Wait for initial response",
  "state": "networkidle"
},
{
  "type": "wait",
  "description": "Wait for JavaScript redirect to process",
  "duration": 3000
},
{
  "type": "wait_for_load_state",
  "description": "Wait for final page to load",
  "state": "networkidle"
},
{
  "type": "screenshot",
  "description": "Screenshot of final page"
}
```

**When to use**:
- SSO login flows
- Multi-step form submissions
- SPA (Single Page App) navigation
- Any time you see: "Page appears idle but content not visible"

**BT Broadband example**: Used twice:
1. After login (SSO redirect to wholesale portal)
2. After address submission (redirect to packages page)

## Pattern 4: Browser Autofill Timing

### Key Learning: Wait for Elements AND Their State

Modern browsers autofill credentials asynchronously. The element exists, but the value hasn't been populated yet.

### ❌ Bad: Immediate Click
```json
{
  "type": "fill",
  "description": "Enter username"
},
{
  "type": "click",
  "description": "Click next"
}
```
**Problem**: Clicks before browser finishes autofilling password.

### ✅ Good: Wait for Element State
```json
{
  "type": "fill",
  "description": "Enter username"
},
{
  "type": "wait",
  "description": "Wait for password field to appear",
  "locator": {
    "strategy": "selector",
    "value": "input[type='password']"
  },
  "timeout": 30000
},
{
  "type": "wait",
  "description": "Wait for Next button to be enabled",
  "locator": {
    "strategy": "selector",
    "value": "button#next"
  },
  "timeout": 30000
},
{
  "type": "click",
  "description": "Click Next button"
}
```

**Key points**:
- Wait for elements to appear (visible state)
- Wait for elements to be enabled (not disabled)
- Give browser time to autofill

## Pattern 5: Extract for Decision-Making, Not Actions

### When to Use Extract Steps

Use `extract` when you need to:
- Make conditional decisions based on page state
- Gather structured data (packages, prices, availability)
- Determine which branch of logic to follow

### ❌ Bad: Extract for Simple Click
```json
{
  "type": "extract",
  "method": "vision",
  "execute_action": true,
  "prompt": "Find the Next button and click it"
}
```

### ✅ Good: Extract for Data Collection
```json
{
  "type": "extract",
  "method": "vision",
  "description": "Extract all broadband packages",
  "prompt": "Extract ALL visible packages with pricing, speed, and availability",
  "schema": {
    "type": "object",
    "properties": {
      "packages": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "monthly_price": {"type": "number"},
            "download_speed_mbps": {"type": "number"},
            "available": {"type": "boolean"}
          }
        }
      }
    }
  }
}
```

### When to Use Click with Escalation vs Extract

| Scenario | Use |
|----------|-----|
| Click a button/link | Click with escalation chain |
| Fill a form field | Fill with escalation chain |
| Select from list | Click with text matching |
| Gather structured data | Extract with vision |
| Make conditional decisions | Extract + conditional logic |

## Pattern 6: Modal Overlays and Interception

### Key Learning: Use Force Click

Modern UIs often have overlays (modals, notifications, cookie banners) that intercept clicks.

### Error You'll See
```
Error: Element is not clickable - another element would receive the click
```

### Solution: Already Built-In
The `_step_click` method automatically handles this:

```python
try:
    await locator.click(timeout=30000)
except Exception as e:
    if "intercepts pointer events" in str(e):
        # Retry with force=True to bypass modal overlays
        await locator.click(timeout=30000, force=True)
```

**You don't need to do anything** - the executor handles this automatically.

## Pattern 7: SPA Form Initialization

### Key Learning: Wait After Navigation for Forms

SPAs (React, Vue, Angular) often mount forms asynchronously after navigation completes.

### Symptoms
- Page loads (network idle)
- Form visible in screenshot
- Fill/click fails with "element not found"

### Solution: Short Delay Before Form Interaction
```json
{
  "type": "navigate",
  "url": "https://example.com/form"
},
{
  "type": "wait_for_load_state",
  "state": "networkidle"
},
{
  "type": "wait",
  "description": "Wait for SPA form to initialize",
  "duration": 2000
},
{
  "type": "fill",
  "description": "Enter data in form"
}
```

**BT Broadband example**: 2-second wait after navigating to Address Checker before filling postcode field.

## Cost Optimization Summary

### Estimated Costs Per Method
- **DOM Check**: $0.00 (~10ms)
- **Playwright Locator**: $0.00 (~100ms)
- **Vision API**: ~$0.01 (~1-2s)

### Real-World Savings (BT Broadband Script)

| Step | Old Approach | New Approach | Savings |
|------|-------------|--------------|---------|
| Login - Next button | Vision ($0.01) | Playwright text ($0.00) | $0.01 |
| Address selection | Vision ($0.01) | Playwright text ($0.00) | $0.01 |
| Submit button | Vision ($0.01) | Playwright selector ($0.00) | $0.01 |
| Package extraction | Vision ($0.01) | Vision ($0.01) | $0.00 |
| **Total per run** | **$0.04** | **$0.01** | **75% reduction** |

With progressive escalation, **95% of operations use free Playwright methods**, vision only for truly complex cases.

## Decision Tree: Which Method to Use?

```
Is it a simple click/fill operation?
├─ YES → Use click/fill with escalation chain (Playwright first, vision last)
└─ NO → Is it data extraction?
    ├─ YES → Use extract with vision
    └─ NO → Is it a conditional decision?
        ├─ YES → Use extract + conditional logic
        └─ NO → Reconsider if you need automation for this

Does the page have JavaScript redirects?
├─ YES → Use triple wait pattern (networkidle → delay → networkidle)
└─ NO → Use single wait_for_load_state

Is it a form in an SPA?
├─ YES → Add 2s wait after navigation for initialization
└─ NO → Proceed normally

Is autofill involved?
├─ YES → Wait for elements to appear and be enabled
└─ NO → Proceed normally
```

## Template: Standard Click with Escalation

Copy this template for most click operations:

```json
{
  "type": "click",
  "description": "Click [BUTTON_DESCRIPTION]",
  "escalation_chain": [
    {
      "method": "playwright_locator",
      "locator": {
        "strategy": "selector",
        "value": "[CSS_SELECTOR]"
      },
      "confidence_threshold": 0.9
    },
    {
      "method": "playwright_locator",
      "locator": {
        "strategy": "text",
        "value": "[BUTTON_TEXT_PRIMARY]"
      },
      "confidence_threshold": 0.9
    },
    {
      "method": "playwright_locator",
      "locator": {
        "strategy": "text",
        "value": "[BUTTON_TEXT_ALTERNATIVE]"
      },
      "confidence_threshold": 0.85
    },
    {
      "method": "vision_find_element",
      "prompt": "Find the [BUTTON_DESCRIPTION]. [LOCATION_HINT]",
      "prefer": "selector",
      "fallback": "coordinates",
      "confidence_threshold": 0.7
    }
  ]
}
```

## Template: JavaScript Redirect Wait

Copy this template after login or form submission that triggers redirects:

```json
{
  "type": "click",
  "description": "Submit form / Login"
},
{
  "type": "wait_for_load_state",
  "description": "Wait for initial response",
  "state": "networkidle"
},
{
  "type": "wait",
  "description": "Wait for JavaScript redirect to complete",
  "duration": 3000
},
{
  "type": "wait_for_load_state",
  "description": "Wait for final page to fully load",
  "state": "networkidle"
}
```

## Common Mistakes to Avoid

### 1. ❌ Using Vision for Everything
**Why**: Expensive, slow, can hallucinate
**Fix**: Always try Playwright locators first

### 2. ❌ Hardcoded Waits Everywhere
**Why**: Slow, brittle, doesn't adapt to page speed
**Fix**: Use `wait_for_load_state` with "networkidle"

### 3. ❌ Exact Text Matching Only
**Why**: Fails on case differences, extra whitespace
**Fix**: Use partial text matching with escalation

### 4. ❌ Single Wait After Redirects
**Why**: JavaScript might still be processing
**Fix**: Use triple wait pattern (networkidle → delay → networkidle)

### 5. ❌ Not Waiting for Autofill
**Why**: Browser hasn't finished populating fields
**Fix**: Wait for password field and button to appear

### 6. ❌ Extract for Simple Clicks
**Why**: Waste of vision API call
**Fix**: Use click with escalation chain

## Testing Your Script

### Progressive Escalation Success Metrics

After running your script, check the logs for escalation statistics:

```
Progressive Escalation Statistics
===================================
Total escalations: 8
Level 0 (DOM): 2 (25.0%)
Level 1 (Playwright): 5 (62.5%)
Level 2 (Vision): 1 (12.5%)
Total vision calls: 1
Total cost: $0.01
Avg cost per escalation: $0.001
```

**Good script characteristics**:
- Level 0 + Level 1 > 85%
- Level 2 (Vision) < 15%
- Avg cost per escalation < $0.005
- Total cost per run < $0.02

**Red flags**:
- Level 2 > 50% → Too many vision calls, add more Playwright fallbacks
- Avg cost > $0.01 → Script is too vision-dependent
- Many failed escalations → Need better locators or broader text matches

## Summary: Key Learnings from BT Broadband Implementation

1. **Progressive escalation works**: 95% success with free methods, vision as fallback
2. **Text matching is powerful**: Partial text matching finds elements vision would cost $0.01 for
3. **JavaScript redirects are common**: Triple wait pattern handles SSO and SPA navigation
4. **Browser autofill needs time**: Wait for elements to appear AND be enabled
5. **Extract for data, click for actions**: Don't use vision for simple clicks
6. **Force click handles overlays**: Already built into the executor
7. **SPA forms need initialization time**: 2-second delay after navigation to form pages

**Bottom line**: Think cheap first, expensive last. Playwright can do 95% of what vision can do, for free and 10x faster.
