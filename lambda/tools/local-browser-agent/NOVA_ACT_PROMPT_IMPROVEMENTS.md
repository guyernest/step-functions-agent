# Nova Act Prompt Improvements

## Analysis of Current Issues

### 1. Video File Locking Error (Non-Critical)
```
[WinError 32] The process cannot access the file because it is being used by another process
```

**Root Cause**: Windows file locking issue in Nova Act's Playwright video recording. The video file is still being written when NovaAct attempts to rename it.

**Impact**: Low - videos are recorded successfully, just not renamed properly. This is a Nova Act SDK issue.

**Resolution**: This is a known issue in Nova Act and doesn't affect functionality. Videos are saved with temporary filenames. No action needed on our side.

### 2. Missing Required Input Data
```
AgentError("The postcode is required to check the address.")
```

**Root Cause**: The Step Functions workflow is not providing the required `postcode`, `building_number`, and `street` parameters in the tool input.

**Impact**: High - task cannot proceed without required data.

**Resolution**: This is correct behavior - the agent properly reports validation errors. The Step Functions orchestrator needs to ensure all required parameters are provided.

### 3. Poor Conditional Logic in Prompts (Critical)

**Old Approach** (v1.0.0):
```json
{
  "prompt": "If a login page appears, type 'nterizakis' as the username and click Next..."
}
```

**Problems**:
- ❌ Too many conditions in one prompt
- ❌ Not prescriptive enough
- ❌ Violates Nova Act best practices: "break up large acts into smaller ones"
- ❌ Combines multiple actions: check, type, click, wait, verify, click again

## Improvements in v1.0.1

Following Nova Act's documentation on "How to prompt act()", we've made these changes:

### 1. Prescriptive, Succinct Prompts

**Before**:
```
"If a login page appears, type 'nterizakis' as the username and click Next. In the next screen, click the 'Next' button, below the password that should be filled automatically. Otherwise (not login page), please continue to the next step to check the address."
```

**After**:
```
"Look at the current page. IF you see a login form with username and password fields, do these steps in order: (1) Type 'nterizakis' in the username field, (2) Click Next, (3) Wait for password page to load, (4) Verify password field has dots/asterisks, (5) Click Next button. IF you already see the Broadband Availability Checker form with Building Number, Street, PostCode fields, do nothing - you're already on the right page."
```

**Improvements**:
- ✅ Numbered steps for clarity
- ✅ Explicit conditional logic with IF/ELSE
- ✅ Clear success criteria ("do nothing - you're already on the right page")
- ✅ Prescriptive verification step ("Verify password field has dots/asterisks")

### 2. Separate Steps for Separate Actions

**Before** (1 step doing everything):
- Login conditional
- Fill form
- Select address conditional
- Extract data

**After** (4 focused steps):
1. Handle authentication (conditional logic built into prompt)
2. Fill address form
3. Handle address disambiguation (conditional logic built into prompt)
4. Extract structured data

### 3. Better Form Filling Instructions

**Before**:
```
"Fill in the address form with these details: - Building Number field: {{building_number}}..."
```

**After**:
```
"In the Building Number field, type: {{building_number}}
In the Street/Road field, type: {{street}}
In the PostCode field, type: {{postcode}}
After filling all three fields, click the Submit button."
```

**Improvements**:
- ✅ One field per line for clarity
- ✅ Uses "In the X field, type: Y" pattern (more prescriptive)
- ✅ Explicit confirmation step: "After filling all three fields"

### 4. Conditional Logic Handling Without Branching

Since our script executor doesn't support conditional step execution (skipping steps based on previous results), we embed the conditional logic WITHIN the prompt itself using IF/ELSE statements.

**Pattern**:
```
"Check X. IF condition A, do action 1. IF condition B, do action 2."
```

This leverages Nova Act's ability to understand and execute conditional instructions within a single act() call.

## Key Principles Applied

From Nova Act documentation:

1. **Be prescriptive and succinct**: Tell the agent exactly what to do, like instructing another person
2. **Break up large acts into smaller ones**: Each step has a single, clear purpose
3. **Use numbered steps**: When multiple actions are needed in sequence
4. **Provide clear success criteria**: "do nothing - you're already on X page"
5. **Explicit verification**: "Verify password field has dots/asterisks"

## Expected Outcomes

With these improvements:

1. **More Reliable Login Handling**: Agent clearly understands when to login vs when to skip
2. **Better Error Recovery**: Clear, numbered steps are easier for the agent to retry
3. **Reduced Step Failures**: Prescriptive instructions reduce ambiguity
4. **Improved Maintainability**: Each step has a single, clear responsibility

## Migration Path

To use the improved template:

1. Update Step Functions workflow to use `broadband_availability_bt_wholesale_v1.0.1.json`
2. Ensure all required parameters are provided: `building_number`, `street`, `postcode`
3. Optional: provide `full_address` for better address matching
4. Test with both "needs login" and "already authenticated" scenarios

## Future Enhancements

Potential improvements for future versions:

1. **Conditional Step Execution**: Add `condition` field to step schema to skip steps based on previous results
2. **Variable Capture**: Add `save_result_as` to capture boolean results from `act_with_schema` for use in conditions
3. **Retry Logic**: Add step-level retry configuration for transient failures
4. **Timeout Configuration**: Per-step timeout overrides
