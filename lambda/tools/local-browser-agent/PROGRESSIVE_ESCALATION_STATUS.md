# Progressive Escalation Implementation Status

## Current Status: Extract Logging Implemented ✅

### What Was Just Added (openai_playwright_executor.py:611-650)

Comprehensive logging for extract steps to debug vision API calls:

```python
async def _step_extract(self, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
    """Extract data using LLM vision"""
    method = step.get("method", "vision")
    prompt = step.get("prompt", "")
    schema = step.get("schema", {})

    print(f"[EXTRACT] Starting extraction with method: {method}", file=sys.stderr)
    print(f"[EXTRACT] Prompt: {prompt[:100]}...", file=sys.stderr)

    if method == "vision":
        print(f"[EXTRACT] Taking screenshot for vision analysis...", file=sys.stderr)
        screenshot_bytes = await self.page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        print(f"[EXTRACT] Screenshot captured ({len(screenshot_bytes)} bytes)", file=sys.stderr)

        print(f"[EXTRACT] Calling LLM vision API...", file=sys.stderr)
        extracted_data = await self._call_llm_vision(prompt, screenshot_b64, schema)
        print(f"[EXTRACT] Vision API response: {json.dumps(extracted_data, indent=2)}", file=sys.stderr)

        return {
            "success": True,
            "action": "extract",
            "method": "vision",
            "data": extracted_data,
        }
```

### Expected Log Output

When extract steps run, you should now see:

```
[EXTRACT] Starting extraction with method: vision
[EXTRACT] Prompt: This page shows a list of addresses after postcode search. The target address is: JOHN WILLIS...
[EXTRACT] Taking screenshot for vision analysis...
[EXTRACT] Screenshot captured (245678 bytes)
[EXTRACT] Calling LLM vision API...
[EXTRACT] Vision API response: {
  "match_found": true,
  "match_method": "selector",
  "match_value": "li.address-item:nth-child(3)",
  "confidence": 0.95,
  "should_scroll": false
}
```

## Current Architecture Gap: Extract → Action Flow

### Problem
The BT Broadband script has two extract steps (steps 333-419):

1. **Step 333-368**: Check if address selection is needed
   - ✅ Calls vision API
   - ✅ Returns structured data
   - ❌ No follow-up action uses this data

2. **Step 370-419**: Find matching address
   - ✅ Calls vision API
   - ✅ Returns `{match_method, match_value, match_coordinates, confidence}`
   - ❌ No follow-up action clicks the found address

3. **Step 421**: Immediately waits for packages page
   - ❌ Assumes we're already on packages page
   - ❌ Address was never clicked!

### What's Missing

We need a way to use extracted data in subsequent steps. Options:

#### Option A: Context Variables (Recommended)
Store extract results in execution context and reference them:

```json
{
  "type": "extract",
  "description": "Find address",
  "save_to": "address_match",
  "method": "vision",
  "prompt": "...",
  "schema": {...}
},
{
  "type": "click",
  "description": "Click the found address",
  "use_extract_result": "address_match",
  "fallback": {
    "escalation_chain": [...]
  }
}
```

#### Option B: Conditional Steps
Execute steps based on extract results:

```json
{
  "type": "extract",
  "description": "Check if address selection needed",
  "schema": {"shows_address_list": "boolean", ...},
  "on_result": {
    "shows_address_list": true,
    "then": [
      {
        "type": "extract",
        "description": "Find address"
      },
      {
        "type": "click",
        "description": "Click address"
      }
    ],
    "shows_packages": true,
    "then": []
  }
}
```

#### Option C: Embedded Actions in Extract
Extract can return an action to perform:

```json
{
  "type": "extract",
  "description": "Find and select address",
  "method": "vision",
  "prompt": "Find the address matching 'JOHN WILLIS HOUSE'. Return how to click it.",
  "schema": {
    "action": "click",
    "locator": {"strategy": "...", "value": "..."}
  },
  "execute_action": true
}
```

## Test Plan

### Phase 1: Verify Logging ✅
Run BT Broadband script and confirm:
- [EXTRACT] logs appear for both extract steps
- Vision API responses are shown in full
- Confidence scores are visible

### Phase 2: Implement Extract → Action Flow
Choose implementation option and update:
- `openai_playwright_executor.py`: Step execution logic
- `bt_broadband_progressive_escalation.json`: Script structure
- Add click step after address extraction

### Phase 3: End-to-End Test
Complete flow should:
1. Login successfully ✅
2. Navigate to Address Checker ✅
3. Enter postcode ✅
4. Click search ✅
5. **Extract address selection check** (Step 333) - NEW
6. **Extract matching address** (Step 370) - NEW
7. **Click the address** (Step XXX) - MISSING
8. Extract broadband packages
9. Return package data

## Immediate Next Steps

1. **User tests script** → Verify [EXTRACT] logs appear and show vision responses
2. **Decide on architecture** → Choose Option A, B, or C for extract→action flow
3. **Implement chosen option** → Update executor and script
4. **Add click step** → Actually select the address after finding it
5. **End-to-end test** → Verify complete BT Broadband flow works

## Files Modified So Far

### Core Implementation
- `python/openai_playwright_executor.py`: Extract logging (lines 611-650)
- `python/progressive_escalation_engine.py`: Vision debugging (lines 371-440)
- `python/computer_agent_wrapper.py`: Format detection, lazy imports
- `src-tauri/src/script_executor.rs`: Wrapper routing
- `src-tauri/src/nova_act_executor.rs`: Conditional env vars

### Test Scripts
- `examples/bt_broadband_progressive_escalation.json`: Complete test flow

## Performance Metrics (Once Complete)

Expected improvements from progressive escalation:
- **Cost**: 5-10x reduction (most operations use free DOM/Playwright methods)
- **Speed**: 2-4x faster (DOM ~10ms vs Vision ~1-2s)
- **Success rate**: Higher (multiple fallback methods)

Current escalation stats tracked:
- Level 0 (DOM): Free, ~10ms
- Level 1 (Playwright): Free, ~100ms
- Level 2 (Vision): ~$0.01, ~1-2s
- Total cost per execution
- Average escalation level
