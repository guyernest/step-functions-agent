# Debugging Browser Automation Workflows

This document describes a systematic debugging methodology for diagnosing and fixing browser automation workflow failures. The approach was developed while debugging the BT Broadband workflow template and can be applied to any browser automation workflow.

## Overview

When a workflow fails, the debugging process follows these steps:

1. **Analyze test logs** - Identify which steps are failing
2. **Collect HTML examples** - Get real page HTML from successful loads
3. **Identify DOM patterns** - Find consistent element structures
4. **Compare selectors** - Understand why current selectors fail
5. **Write fixes** - Create robust selectors with fallbacks
6. **Validate changes** - Ensure JSON validity and selector syntax

---

## Step 1: Analyze Test Logs for Failure Patterns

### What to do

Review log files containing multiple task executions and identify:
- Which steps fail consistently
- Success/failure rates per step
- Error messages or timeouts

### Example analysis

| Step | Success Rate | Issue |
|------|-------------|-------|
| WaitForResults | 0% (34/34 failed) | Selector never matched |
| extract_dom | 0% (silent failures) | All extractions returned null |
| Address selection | ~80% | Some addresses not found |

### Key takeaway

Focus debugging efforts on steps with the lowest success rates first. A 0% success rate indicates a fundamental selector or syntax issue.

---

## Step 2: Collect Real HTML Examples

### What to do

Request actual HTML from successful page loads:
1. Navigate to the page manually in a browser
2. Right-click > "Save As" or copy `document.documentElement.outerHTML`
3. Save multiple examples (3-5 minimum)

### Why multiple examples matter

- Single example can miss edge cases
- Variations reveal which elements are always present vs conditional
- Helps create robust selectors that work across all scenarios

### Example variations to capture

| Example | Characteristics |
|---------|-----------------|
| Address 1 | Has existing ONT, VDSL available |
| Address 2 | No existing ONT, FTTP only |
| Address 3 | Different exchange, with cabinet |
| Address 4 | Business premises, no cabinet |
| Address 5 | Different region/exchange code format |

---

## Step 3: Identify Common DOM Patterns

### Analysis approach

For each HTML file:
1. Search for the target data (e.g., "Exchange Code", "L2SID")
2. Document the exact HTML structure around it
3. Note CSS classes, element hierarchy, and text patterns
4. Compare across all files to find consistent patterns

### Example: Exchange Code structure

```html
<!-- Found in ALL 5 example pages -->
<span class="ExhangeCodeSetup">
  <span class="ExhangeCodeSetupTwo"><strong>Exchange Code:</strong></span>
  <span>STSTHBN</span>  <!-- Value is in sibling span, NOT same element -->
</span>
```

### Pattern summary table

Create a table documenting which elements appear in which pages:

| Element | Selector | Present In |
|---------|----------|------------|
| Exchange Code container | `.ExhangeCodeSetup` | All pages |
| Featured Products header | `th:has-text('Featured Products')` | All pages |
| L2SID (New ONT) row | `tr:has(th:has-text('L2SID'))` | All FTTP pages |
| ONT Details table | `th:has-text('ONT Details')` | Only 2/5 pages |

---

## Step 4: Compare Expected vs Actual Selectors

### Common issues discovered

#### Issue 1: Invalid selector syntax

| Aspect | Expected Behavior | Actual Behavior |
|--------|-------------------|-----------------|
| Selector | `text=/Exchange Code/i, text=/FEATURED PRODUCTS/i` | Match any of these |
| Reality | Comma syntax not valid for OR in Playwright | Fails completely |

**Fix:** Use single selector or Playwright's `:is()` pseudo-class.

#### Issue 2: Value in sibling element

| Aspect | Expected | Actual HTML |
|--------|----------|-------------|
| Exchange Code | Value in same element as label | Value in **sibling** span |
| Regex | `el.textContent.match(/Exchange Code[:\s]*([A-Z0-9]+)/i)` | Fails - label and value are separate |

**Fix:** Navigate to sibling element in selector or JavaScript.

### Testing selectors

Use browser DevTools console to test:

```javascript
// Test CSS selector
document.querySelector('.ExhangeCodeSetup > span:last-child')

// Test if element exists
document.querySelector('th:has-text("Featured Products")') !== null

// Test fallback JS extraction
(() => {
  const wrapper = document.querySelector('.ExhangeCodeSetup');
  if (wrapper) {
    const spans = wrapper.querySelectorAll('span');
    for (const s of spans) {
      if (!s.classList.contains('ExhangeCodeSetupTwo')) {
        return s.textContent.trim();
      }
    }
  }
  return null;
})()
```

---

## Step 5: Write Corrected Selectors

### Selector writing principles

1. **Use CSS classes when available** - More stable than text matching
2. **Handle sibling/parent relationships** - Value may not be in same element as label
3. **Provide fallback_js** - For complex extractions CSS selectors can't handle
4. **Test against all HTML variants** - Ensure selector works on all examples

### Before (broken)

```json
{
  "name": "exchange_code",
  "selector": "text=/Exchange Code/i/../following-sibling::*",
  "fallback_js": "(() => { const el = [...document.querySelectorAll('*')].find(e => e.textContent.includes('Exchange Code')); return el ? el.textContent.match(/Exchange Code[:\\s]*([A-Z0-9]+)/i)?.[1] : null; })()"
}
```

**Problems:**
- XPath-style `/../following-sibling::*` doesn't work in Playwright CSS selectors
- Fallback JS searches entire textContent, but value is in separate element

### After (fixed)

```json
{
  "name": "exchange_code",
  "selector": ".ExhangeCodeSetup > span:last-child",
  "fallback_js": "(() => { const wrapper = document.querySelector('.ExhangeCodeSetup'); if (wrapper) { const spans = wrapper.querySelectorAll('span'); for (const s of spans) { if (!s.classList.contains('ExhangeCodeSetupTwo') && !s.textContent.includes('Exchange Code')) { return s.textContent.trim(); } } } return null; })()"
}
```

**Improvements:**
- Uses stable CSS class selector
- Directly targets the value span (last child)
- Fallback JS explicitly navigates sibling structure

---

## Step 6: Validate Changes

### Validation checklist

```bash
# 1. Validate JSON syntax
python3 -c "import json; json.load(open('templates/workflow.json')); print('JSON valid')"

# 2. Check for common JSON issues
# - Unescaped quotes in fallback_js strings
# - Missing commas between array elements
# - Trailing commas (not allowed in JSON)
```

### Selector syntax verification

| Selector Type | Valid Syntax | Invalid Syntax |
|---------------|--------------|----------------|
| Class | `.ExhangeCodeSetup` | `ExhangeCodeSetup` |
| Has-text | `th:has-text('Featured')` | `th:text('Featured')` |
| Child combinator | `span > span:last-child` | `span/span:last-child` |
| Multiple selectors (OR) | `:is(.a, .b)` or separate strategies | `.a, .b` (comma doesn't mean OR) |

---

## Common Selector Issues Reference

| Issue | Symptom | Fix |
|-------|---------|-----|
| Comma-separated selectors | 100% failure | Use single selector or `:is()` pseudo-class |
| Value in sibling element | Returns label text or null | Use `> span:last-child` or sibling navigation in JS |
| Element only sometimes present | Partial failures | Make extraction optional, check for null |
| Angular/React dynamic content | Intermittent failures | Wait for specific element, not just `networkidle` |
| Text with special characters | Selector parse error | Escape regex special chars or use CSS class |
| XPath syntax in CSS selector | Selector not found | Use CSS equivalents (`:has()`, `>`, `+`) |

---

## Debugging Checklist

Use this checklist when debugging workflow failures:

```
□ 1. GET LOGS
   - Request test logs with multiple executions
   - Calculate success rate per step
   - Identify the failing step(s)

□ 2. GET HTML SAMPLES
   - Request 3-5 HTML examples from successful page loads
   - Ensure variety (different data, edge cases)
   - Save as local files for analysis

□ 3. ANALYZE PATTERNS
   - Find target data in each HTML file
   - Document exact element structure
   - Identify CSS classes, IDs, attributes
   - Note which elements are always vs sometimes present

□ 4. COMPARE SELECTORS
   - Test current selector against HTML samples
   - Use browser DevTools: document.querySelector('...')
   - Identify why selector fails

□ 5. WRITE FIXES
   - Prefer CSS class selectors over text
   - Handle sibling/parent relationships
   - Always provide fallback_js
   - Test against ALL HTML samples

□ 6. VALIDATE
   - JSON syntax check
   - Playwright selector syntax check
   - Verify fallback_js executes correctly in browser console
```

---

## Real-World Example: BT Broadband Workflow

### Initial failures

- **WaitForResults**: 0% success - selector `text=/Exchange Code/i, text=/FEATURED PRODUCTS/i` never matched
- **extract_dom**: 0% success - all extractions returned null

### Root causes identified

1. Comma-separated text selectors don't work as OR logic
2. Exchange Code value is in a sibling span, not the same element as the label
3. ONT Details table only exists on some pages (2 of 5 examples)

### Fixes applied

| Extraction | Old Selector | New Selector |
|------------|--------------|--------------|
| Wait for results | `text=/Exchange Code/i, ...` | `.ExhangeCodeSetup` |
| Exchange Code | `text=/Exchange Code/i/../following-sibling::*` | `.ExhangeCodeSetup > span:last-child` |
| L2SID | (not extracted) | `tr:has(th:has-text('L2SID (New ONT)')) td` |
| ONT Details | `table:has(th:text-matches('ONT', 'i'))` | `table:has(th:has-text('ONT Details'))` |

### Results

After fixes, the workflow should correctly extract:
- Exchange codes: `STSTHBN`, `STBOSMB`, `STWINTN`, `LCBOL`, `SDPCHVN`
- L2SID values: `BAAOEA`, `BAAOFE`, `BAAMRT`, `BAAMUH`, `BAANTY`
- ONT details (when present): reference, serial number, port service ID

---

## Conclusion

This systematic approach transforms debugging from guesswork into a reliable process:

1. **Quantify the problem** - Use logs to identify exactly which steps fail
2. **Ground truth** - Collect real HTML to understand actual DOM structure
3. **Pattern analysis** - Find what's consistent across variations
4. **Targeted fixes** - Write selectors based on real structure, not assumptions
5. **Validation** - Verify fixes work before deployment

Following this methodology ensures efficient debugging and robust fixes that handle edge cases.
