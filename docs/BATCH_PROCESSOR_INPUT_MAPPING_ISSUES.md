# Batch Processor Input Mapping Issues - Ultrathink Analysis

## Executive Summary

There are **TWO CRITICAL ISSUES** causing inconsistent agent inputs from CSV batch processing:

1. **BOM Handling Mismatch**: Analysis tool doesn't strip BOM, but loader does → mapping keys don't match actual columns
2. **Schema Transformation Gap**: CSV has `address` field, but agent needs `building_number`, `street`, `postcode` → missing intelligent transformation

---

## Problem 1: BOM (Byte Order Mark) Handling Mismatch

### The Issue

**UTF-8 BOM** (`\ufeff`) appears at the start of CSV files created by Excel/Windows applications. Different Lambda functions handle it inconsistently.

### Evidence

**CSV Analyzer** (`lambda/agents/batch_orchestrator/analyze_csv.py` line 49):
```python
content = response['Body'].read().decode('utf-8')  # ❌ Does NOT strip BOM
```

**CSV Loader** (`lambda/tools/batch_processor/csv_loader.py` line 32):
```python
content = response['Body'].read().decode('utf-8-sig')  # ✅ DOES strip BOM
```

### Impact

```
CSV file uploaded
  └─> Header: "\ufeffaddress,postcode"

Step 1: Batch Orchestrator analyzes CSV
  └─> analyze_csv_structure returns:
      columns: ["\ufeffaddress", "postcode"]  ❌ BOM NOT stripped
  └─> LLM generates mapping:
      input_mapping: {
        "\ufeffaddress": "address",  ❌ Key has BOM
        "postcode": "postcode"
      }

Step 2: Batch Processor loads CSV
  └─> csv_loader reads with utf-8-sig:
      columns: ["address", "postcode"]  ✅ BOM stripped
  └─> Row data: {"address": "1 Church view", "postcode": "DN12 1RH"}

Step 3: Input Mapper tries to apply mapping
  └─> Looking for column "\ufeffaddress" in row
  └─> Row has "address" (no BOM)
  └─> ❌ MAPPING FAILS - Key not found!
  └─> Result: Agent gets EMPTY or PARTIAL input
```

### Fix Required

**File:** `lambda/agents/batch_orchestrator/analyze_csv.py` line 49

**Change:**
```python
# BEFORE
content = response['Body'].read().decode('utf-8')

# AFTER
content = response['Body'].read().decode('utf-8-sig')  # Strip BOM
```

---

## Problem 2: Schema Transformation Gap

### The Issue

CSV columns don't match agent input schema - requires **intelligent parsing/transformation**.

### Schema Mismatch

**CSV Columns:**
```
address, postcode
```

**Agent Input Schema** (`schemas/broadband_availability_bt_wholesale.json`):
```json
{
  "building_number": "REQUIRED - Building number (e.g., '1', '23A')",
  "street": "REQUIRED - Street name (e.g., 'High Street')",
  "postcode": "REQUIRED - UK postcode (e.g., 'SW1A 1AA')",
  "full_address": "OPTIONAL - Full address for disambiguation"
}
```

### Current Behavior

**When LLM generates "smart" mapping:**
```json
{
  "input_mapping": {
    "address": "address",
    "postcode": "postcode"
  }
}
```

Result:
```json
{
  "input": {
    "address": "1 Church view, London",
    "postcode": "DN12 1RH"
  }
}
```

**Agent receives `address` field but schema has NO `address` field** → Agent ignores it or errors out.

**When LLM generates "literal" mapping:**
```json
{
  "input_mapping": {
    "address": null,
    "postcode": "postcode"
  }
}
```

Result:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "1 Church view, London, DN12 1RH"
    }
  ]
}
```

**Agent gets free-form text** → Must parse address itself (unreliable).

### The Root Cause

The batch orchestrator agent (LLM) **doesn't know the agent's actual input schema**. It only sees:
- ✅ CSV columns: `["address", "postcode"]`
- ❌ Agent input schema: **NOT PROVIDED**

So it makes a **guess**:
- Sometimes maps `address` → `address` (which doesn't exist in schema)
- Sometimes puts everything in `messages[].content` as free text

### What SHOULD Happen

The batch orchestrator should:

1. **Fetch the agent's input schema** from AgentRegistry or canonical schema
2. **Recognize schema mismatch**: CSV has `address`, agent needs `building_number` + `street`
3. **Generate intelligent transformation**:
   ```json
   {
     "input_mapping": {
       "transformations": {
         "building_number": {
           "type": "extract_regex",
           "source_column": "address",
           "pattern": "^(\\d+[A-Z]?)\\s+"
         },
         "street": {
           "type": "extract_regex",
           "source_column": "address",
           "pattern": "^\\d+[A-Z]?\\s+(.+)$"
         },
         "postcode": "postcode",
         "full_address": {
           "type": "concat",
           "columns": ["address", "postcode"],
           "separator": ", "
         }
       }
     }
   }
   ```

4. **OR fallback to simpler approach**:
   ```json
   {
     "input_mapping": {
       "full_address": {
         "type": "concat",
         "columns": ["address", "postcode"],
         "separator": ", "
       },
       "postcode": "postcode"
     }
   }
   ```

   Then rely on the agent or template to parse `full_address`.

---

## Current System Flow (with Issues)

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. CSV Upload                                                   │
│    File: test_addresses_two.csv                                │
│    Headers: "\ufeffaddress,postcode"  ← BOM present            │
│    Row 1: "1 Church view, London","DN12 1RH"                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. Batch Orchestrator Agent                                     │
│    Tool: analyze_csv_structure                                  │
│    ❌ decode('utf-8') - BOM NOT stripped                        │
│    Returns: columns = ["\ufeffaddress", "postcode"]            │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. LLM Generates Input Mapping                                  │
│    ❌ Doesn't know agent input schema                           │
│    ❌ Uses BOM-prefixed column names                            │
│    Output:                                                       │
│    {                                                             │
│      "input_mapping": {                                          │
│        "\ufeffaddress": "address",  ← Wrong key                 │
│        "postcode": "postcode"                                    │
│      }                                                           │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. Batch Processor Loads CSV                                    │
│    csv_loader.py                                                 │
│    ✅ decode('utf-8-sig') - BOM IS stripped                     │
│    Actual columns: ["address", "postcode"]                      │
│    Row: {"address": "1 Church view", "postcode": "DN12 1RH"}   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. Input Mapper Applies Mapping                                 │
│    Looking for: row["\ufeffaddress"]                            │
│    Row has: row["address"]                                       │
│    ❌ KEY NOT FOUND - Mapping fails!                            │
│    Result: Partial or empty input to agent                      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. Agent Receives Invalid Input                                 │
│    Expected: {building_number, street, postcode}                │
│    Received: {address: "...", postcode: "..."}                  │
│    OR: {messages: [{content: "full string"}]}                   │
│    ❌ Schema mismatch - Agent can't process correctly           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Solutions

### Solution 1: Fix BOM Handling (Immediate - 5 minutes)

**File:** `lambda/agents/batch_orchestrator/analyze_csv.py`

**Change Line 49:**
```python
# BEFORE
content = response['Body'].read().decode('utf-8')

# AFTER
content = response['Body'].read().decode('utf-8-sig')  # Strip BOM to match loader
```

**Impact:**
- ✅ Column names in analysis match actual CSV columns
- ✅ Input mapping keys will be correct
- ✅ Fixes inconsistent behavior between analysis and loading

---

### Solution 2A: Provide Agent Schema to Batch Orchestrator (Medium - 2 hours)

**Enhance the batch orchestrator agent's tools:**

1. **Add tool: `get_agent_input_schema`**
   ```python
   def get_agent_input_schema(agent_name):
       # Read from schemas/{extraction_name}.json
       # OR query AgentRegistry metadata
       return {
           "input_schema": {...},
           "output_schema": {...}
       }
   ```

2. **Update `execute_batch_processor` tool spec:**
   ```json
   {
     "description": "Before calling this, use get_agent_input_schema to understand what fields the agent expects. Generate transformations to map CSV columns to agent input fields."
   }
   ```

3. **Agent system prompt enhancement:**
   ```
   When generating input_mapping:
   1. Call get_agent_input_schema(agent_name) first
   2. Compare CSV columns with agent input schema
   3. If mismatch, generate appropriate transformations
   4. For address parsing, use these transformation types:
      - extract_regex: Extract part of string
      - concat: Combine multiple columns
      - split: Split string into parts
      - passthrough: Direct mapping
   ```

**Impact:**
- ✅ LLM knows agent's actual schema
- ✅ Can generate intelligent transformations
- ✅ Handles address parsing correctly
- ⚠️ Requires updating batch orchestrator agent

---

### Solution 2B: Add Address Parsing to Agent (Quick - 30 minutes)

**Make the agent more flexible by accepting either format:**

**Option 1: Add `address` field to agent input schema**
```json
{
  "input_schema": {
    "properties": {
      "building_number": {"type": "string"},
      "street": {"type": "string"},
      "postcode": {"type": "string", "required": true},
      "full_address": {"type": "string"},
      "address": {"type": "string"}  // ← ADD THIS
    }
  }
}
```

**Agent system prompt update:**
```
If you receive:
- building_number + street + postcode: Use directly
- address + postcode: Parse address to extract building_number and street
- full_address: Parse to extract all components
```

**Impact:**
- ✅ Works with both CSV formats
- ✅ No changes to batch orchestrator needed
- ⚠️ Agent must handle parsing (less reliable)

---

### Solution 2C: Use `full_address` Field (Simplest - 10 minutes)

**Have batch orchestrator always map to `full_address`:**

1. **Update batch orchestrator prompt:**
   ```
   When CSV has 'address' and 'postcode' columns:
   - Map 'postcode' → 'postcode'
   - Create 'full_address' by concatenating address + postcode
   - Do NOT try to parse into building_number/street
   ```

2. **Rely on template to handle parsing:**
   The BT Wholesale template step 3 already handles address selection:
   ```json
   {
     "prompt": "If an address list appears, select the closest match to {{building_number}} {{street}}, {{postcode}}{{#full_address}} (matching '{{full_address}}'){{/full_address}}"
   }
   ```

**Impact:**
- ✅ Simplest solution
- ✅ Template can handle full address
- ✅ Works with current architecture
- ⚠️ Relies on BT Wholesale portal's address search

---

## Recommended Implementation Plan

### Phase 1: Immediate Fix (Today)
1. ✅ Fix BOM handling in `analyze_csv.py`
2. ✅ Deploy updated Lambda

### Phase 2: Quick Improvement (This Week)
1. Update batch orchestrator system prompt to use `full_address` approach
2. Test with both CSV formats

### Phase 3: Proper Solution (Next Sprint)
1. Implement `get_agent_input_schema` tool
2. Add transformation logic to input_mapper
3. Update batch orchestrator to generate intelligent mappings

---

## Testing Plan

### Test Case 1: CSV with BOM
```csv
\ufeffaddress,postcode
"1 Church view, London","DN12 1RH"
```

**Expected:**
- ✅ Columns analyzed as: `["address", "postcode"]` (BOM stripped)
- ✅ Mapping: `{"address": "full_address", "postcode": "postcode"}`
- ✅ Agent input: `{"full_address": "1 Church view, London, DN12 1RH", "postcode": "DN12 1RH"}`

### Test Case 2: CSV with Correct Headers
```csv
building_number,street,postcode
1,"Church view, London","DN12 1RH"
```

**Expected:**
- ✅ Columns: `["building_number", "street", "postcode"]`
- ✅ Direct mapping to agent schema
- ✅ Agent input: `{"building_number": "1", "street": "Church view, London", "postcode": "DN12 1RH"}`

### Test Case 3: CSV with Upper Case Headers
```csv
ADDRESS,POSTCODE
"1 Church view, London","DN12 1RH"
```

**Expected:**
- ✅ Columns normalized to lowercase
- ✅ Mapping: case-insensitive match
- ✅ Agent input: correct values

---

## Summary

| Issue | Severity | Fix Complexity | Impact |
|-------|----------|----------------|--------|
| BOM not stripped in analyzer | HIGH | LOW (5 min) | Breaks input mapping completely |
| Schema mismatch (address vs building_number+street) | HIGH | MEDIUM (varies by solution) | Agent gets wrong input format |
| No intelligent transformation | MEDIUM | HIGH (2 hours) | Limits CSV flexibility |

**Immediate Action Required:**
Fix the BOM handling - this is a 1-line change that fixes a critical bug.

**Next Steps:**
Choose solution 2B or 2C based on your preference for where parsing logic lives.
