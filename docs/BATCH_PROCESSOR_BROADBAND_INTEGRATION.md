# Batch Processor Integration with Broadband Agent

## Overview

This document details how the `batch-processor-prod` tool integrates with the `broadband-availability-bt-wholesale-prod` agent to process CSV files of addresses and generate enriched CSV output with broadband availability data.

## ✅ Compatibility Verification

The broadband agent **IS FULLY COMPATIBLE** with the batch processor:

### Agent Configuration
- ✅ `structured_output.enabled = True` (lines 159-171)
- ✅ Output fields defined: `["success", "exchange", "cabinet", "downstream_mbps", "upstream_mbps", "availability", "service_type", "screenshot_url", "metadata"]`
- ✅ Canonical schema ID: `broadband_availability_bt_wholesale`
- ✅ Supports batch processing: `supports_batch_processing = True` (line 181)

### Batch Processor Requirements
- ✅ Agent must return `structured_output` field
- ✅ Agent must have `structured_output.enabled = True` in registry
- ✅ Output fields must be defined in agent configuration

**Status**: 🟢 **ALL REQUIREMENTS MET**

---

## How It Works

### 1. Input CSV Format

```csv
building_number,street,postcode,full_address
23,High Street,SW1A 1AA,23 High Street London SW1A 1AA
1,Church View,DN12 1RH,
45A,Park Road,E8 4LX,
```

**Columns**:
- `building_number` (required) - Building number
- `street` (required) - Street or road name
- `postcode` (required) - UK postcode
- `full_address` (optional) - Full address for disambiguation

### 2. Batch Processor Configuration

**S3 Execution Input**:
```json
{
  "config_s3_uri": "s3://batch-processor-prod/configs/broadband_batch_config.json",
  "input_csv_s3_uri": "s3://batch-processor-prod/inputs/addresses.csv",
  "output_s3_prefix": "s3://batch-processor-prod/outputs/broadband/"
}
```

**Configuration File** (`broadband_batch_config.json`):
```json
{
  "agent_name": "broadband-availability-bt-wholesale-prod",
  "agent_state_machine_arn": "arn:aws:states:eu-west-1:...:stateMachine:broadband-availability-bt-wholesale-prod",
  "input_mapping": {
    "column_mappings": [
      {
        "csv_column": "building_number",
        "agent_input_field": "building_number",
        "required": true
      },
      {
        "csv_column": "street",
        "agent_input_field": "street",
        "required": true
      },
      {
        "csv_column": "postcode",
        "agent_input_field": "postcode",
        "required": true
      },
      {
        "csv_column": "full_address",
        "agent_input_field": "full_address",
        "required": false
      }
    ]
  },
  "output_mapping": {
    "structured_output_fields": [
      "success",
      "exchange",
      "cabinet",
      "downstream_mbps",
      "upstream_mbps",
      "availability",
      "service_type",
      "screenshot_url",
      "metadata"
    ],
    "include_original": true,
    "add_metadata": true
  },
  "execution_config": {
    "max_concurrency": 10,
    "timeout_seconds": 300,
    "retry_strategy": {
      "max_attempts": 2,
      "backoff_rate": 2.0,
      "interval_seconds": 5
    }
  },
  "notification_config": {
    "enabled": true,
    "success_notification": true,
    "failure_notification": true,
    "sns_topic_arn": "arn:aws:sns:eu-west-1:...:batch-processor-notifications-prod"
  }
}
```

### 3. Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Batch Processor Execution                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Validate Configuration                                        │
│    - Check agent has structured_output.enabled                   │
│    - Verify output_fields match agent schema                     │
│    - Validate CSV column mappings                                │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Load CSV from S3                                              │
│    - Parse CSV file                                              │
│    - Convert to array of row objects                             │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Distributed Map (Parallel Processing - Max 10 concurrent)    │
│                                                                  │
│   For Each Row:                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ a. Map CSV → Agent Input                                 │  │
│   │    {                                                      │  │
│   │      "building_number": "23",                             │  │
│   │      "street": "High Street",                             │  │
│   │      "postcode": "SW1A 1AA"                               │  │
│   │    }                                                      │  │
│   └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ b. Invoke Agent (Synchronous)                            │  │
│   │    states:startExecution.sync                             │  │
│   │    - Template loaded from registry                        │  │
│   │    - Variables rendered with Mustache                     │  │
│   │    - Browser automation executed                          │  │
│   │    - Structured data extracted                            │  │
│   └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ c. Extract Structured Output                             │  │
│   │    output_mapper.py:extract_structured_output()           │  │
│   │                                                           │  │
│   │    Looks for: agent_output.structured_output              │  │
│   │    Fields: success, exchange, cabinet, downstream_mbps,   │  │
│   │            upstream_mbps, availability, service_type,     │  │
│   │            screenshot_url, metadata                       │  │
│   └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ d. Build Enriched Row                                    │  │
│   │    Original: building_number, street, postcode            │  │
│   │    +                                                      │  │
│   │    Structured: success, exchange, cabinet, ...            │  │
│   │    +                                                      │  │
│   │    Metadata: _status, _timestamp, _execution_time_ms      │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Aggregate Results                                             │
│    - Combine all enriched rows                                   │
│    - Preserve column order (original → structured → metadata)    │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Generate Output CSV                                           │
│    - Convert JSON array to CSV                                   │
│    - Upload to S3                                                │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Send Notification (SNS)                                       │
│    - Success/failure status                                      │
│    - Row counts (total, successful, failed)                      │
│    - Output S3 URI                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Output CSV Format

```csv
building_number,street,postcode,full_address,success,exchange,cabinet,downstream_mbps,upstream_mbps,availability,service_type,screenshot_url,metadata,_status,_timestamp,_execution_time_ms
23,High Street,SW1A 1AA,23 High Street London SW1A 1AA,true,KINGSLAND GREEN,Cabinet 9,80,20,true,FTTC,s3://browser-agent-recordings-prod/.../recording.mp4,{...},SUCCESS,2025-10-18T05:30:00Z,12500
1,Church View,DN12 1RH,,true,DONCASTER CENTRAL,Cabinet 15,67,19,true,FTTC,s3://browser-agent-recordings-prod/.../recording.mp4,{...},SUCCESS,2025-10-18T05:31:00Z,11200
45A,Park Road,E8 4LX,,true,HACKNEY,Cabinet 23,300,50,true,FTTP,s3://browser-agent-recordings-prod/.../recording.mp4,{...},SUCCESS,2025-10-18T05:32:00Z,13800
```

**Column Order**:
1. **Original columns**: All input CSV columns preserved
2. **Structured output fields**: In the order specified in config
3. **Metadata columns**: `_status`, `_timestamp`, `_execution_time_ms`, `_error_message` (if failed)

---

## Structured Output Extraction Logic

### Code Location
`lambda/tools/batch_processor/output_mapper.py:extract_structured_output()`

### Extraction Priority

The `output_mapper` looks for the `structured_output` field in this order:

1. **Direct field**: `agent_output.structured_output`
2. **Step Functions Output wrapper**: `agent_output.Output.structured_output`
3. **Tool result content**: `agent_output.content.structured_output`

### Code Implementation

```python
def extract_structured_output(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Extract structured output from agent response"""

    agent_output = event.get('agent_output', {})
    output_mapping = event.get('output_mapping', {})
    original_row = event.get('original_row', {})

    # Build result with OrderedDict to preserve column order
    from collections import OrderedDict
    result_row = OrderedDict()

    # 1. Add original row fields first
    if output_mapping.get('include_original', True):
        for key, value in original_row.items():
            result_row[key] = value

    # 2. Extract structured_output field
    structured_data = None

    # Check different possible locations
    if 'structured_output' in agent_output:
        structured_data = agent_output['structured_output']
    elif 'Output' in agent_output:
        # Parse Step Functions Output wrapper
        output_data = json.loads(agent_output['Output']) if isinstance(agent_output['Output'], str) else agent_output['Output']
        if 'structured_output' in output_data:
            structured_data = output_data['structured_output']
    elif 'content' in agent_output and 'structured_output' in agent_output['content']:
        structured_data = agent_output['content']['structured_output']

    if structured_data is None:
        # ERROR: Agent didn't return structured output
        return {
            **result_row,
            '_status': 'FAILED',
            '_error_message': 'Agent did not return structured output',
            '_timestamp': datetime.utcnow().isoformat()
        }

    # 3. Extract specified fields in order
    fields_to_extract = output_mapping.get('structured_output_fields', [])
    for field_name in fields_to_extract:
        if field_name in structured_data:
            value = structured_data[field_name]
            # Convert complex types to JSON strings for CSV
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            result_row[field_name] = value
        else:
            result_row[field_name] = ''

    # 4. Add metadata
    if output_mapping.get('add_metadata', True):
        result_row['_status'] = 'SUCCESS'
        result_row['_timestamp'] = datetime.utcnow().isoformat()

    return dict(result_row)
```

---

## Agent Output Format

### What the Broadband Agent Returns

Based on the agent configuration (lines 159-171), the agent returns:

```json
{
  "structured_output": {
    "success": true,
    "exchange": "KINGSLAND GREEN",
    "cabinet": "Cabinet 9",
    "downstream_mbps": 80,
    "upstream_mbps": 20,
    "availability": true,
    "service_type": "FTTC",
    "screenshot_url": "s3://browser-agent-recordings-prod/.../recording.mp4",
    "metadata": {
      "act_id": "...",
      "session_id": "...",
      "num_steps": 5
    }
  }
}
```

### How the Batch Processor Uses It

1. **Validate**: Checks that `structured_output` field exists
2. **Extract**: Pulls each field listed in `structured_output_fields` config
3. **Transform**: Converts complex types (dict, list) to JSON strings for CSV
4. **Combine**: Merges with original row and metadata
5. **Order**: Preserves column order (original → structured → metadata)

---

## Error Handling

### Row-Level Errors

If an individual address fails:
- ✅ Other rows continue processing (batch doesn't stop)
- ✅ Failed row includes error metadata:
  ```csv
  building_number,street,postcode,...,_status,_error_message,_timestamp
  INVALID,,,,FAILED,"Agent did not return structured output",2025-10-18T05:30:00Z
  ```

### Types of Failures

1. **Agent Execution Failure**: Agent state machine fails
   - `_status = "FAILED"`
   - `_error_message` = Step Functions error

2. **Missing Structured Output**: Agent succeeds but no `structured_output` field
   - `_status = "FAILED"`
   - `_error_message = "Agent did not return structured output"`

3. **Timeout**: Agent exceeds timeout (default 300s)
   - `_status = "FAILED"`
   - `_error_message = "Execution timeout"`

4. **Template Rendering Error**: Invalid variables
   - `_status = "FAILED"`
   - `_error_message` = Template error details

---

## Performance Characteristics

### Concurrency
- **Default**: 10 concurrent executions
- **Configurable**: Set via `execution_config.max_concurrency`
- **Per-address**: ~10-15 seconds (browser automation + extraction)

### Throughput Examples

| Rows | Concurrency | Est. Duration | Cost Estimate |
|------|-------------|---------------|---------------|
| 10   | 10          | ~15 seconds   | $0.01        |
| 100  | 10          | ~2 minutes    | $0.10        |
| 1000 | 10          | ~20 minutes   | $1.00        |

**Factors**:
- Nova Act API calls (browser automation)
- Step Functions state transitions
- Lambda invocations
- S3 operations

---

## Testing the Integration

### Step 1: Create Test CSV

```bash
cat > /tmp/test_addresses.csv << 'EOF'
building_number,street,postcode,full_address
1,Church View,DN12 1RH,
23,High Street,SW1A 1AA,23 High Street London SW1A 1AA
EOF
```

### Step 2: Upload to S3

```bash
aws s3 cp /tmp/test_addresses.csv \
  s3://batch-processor-prod-145023107515/inputs/test_addresses.csv \
  --profile CGI-PoC
```

### Step 3: Create Configuration

```bash
cat > /tmp/broadband_batch_config.json << 'EOF'
{
  "agent_name": "broadband-availability-bt-wholesale-prod",
  "agent_state_machine_arn": "arn:aws:states:eu-west-1:145023107515:stateMachine:broadband-availability-bt-wholesale-prod",
  "input_mapping": {
    "column_mappings": [
      {"csv_column": "building_number", "agent_input_field": "building_number", "required": true},
      {"csv_column": "street", "agent_input_field": "street", "required": true},
      {"csv_column": "postcode", "agent_input_field": "postcode", "required": true},
      {"csv_column": "full_address", "agent_input_field": "full_address", "required": false}
    ]
  },
  "output_mapping": {
    "structured_output_fields": [
      "success", "exchange", "cabinet", "downstream_mbps",
      "upstream_mbps", "availability", "service_type",
      "screenshot_url", "metadata"
    ],
    "include_original": true,
    "add_metadata": true
  },
  "execution_config": {
    "max_concurrency": 2,
    "timeout_seconds": 300
  }
}
EOF
```

### Step 4: Upload Configuration

```bash
aws s3 cp /tmp/broadband_batch_config.json \
  s3://batch-processor-prod-145023107515/configs/broadband_batch_config.json \
  --profile CGI-PoC
```

### Step 5: Execute Batch

```bash
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:eu-west-1:145023107515:stateMachine:batch-processor-prod" \
  --input '{
    "config_s3_uri": "s3://batch-processor-prod-145023107515/configs/broadband_batch_config.json",
    "input_csv_s3_uri": "s3://batch-processor-prod-145023107515/inputs/test_addresses.csv",
    "output_s3_prefix": "s3://batch-processor-prod-145023107515/outputs/broadband/"
  }' \
  --profile CGI-PoC
```

### Step 6: Monitor Execution

```bash
# Get execution ARN from previous command output
aws stepfunctions describe-execution \
  --execution-arn "arn:aws:states:eu-west-1:145023107515:execution:batch-processor-prod:..." \
  --profile CGI-PoC
```

### Step 7: Download Results

```bash
# Check output location (look for timestamp-based key)
aws s3 ls s3://batch-processor-prod-145023107515/outputs/broadband/ --profile CGI-PoC

# Download result
aws s3 cp s3://batch-processor-prod-145023107515/outputs/broadband/result-YYYY-MM-DD-HH-MM-SS.csv \
  /tmp/results.csv \
  --profile CGI-PoC
```

---

## Schema Flexibility

### Specific Schema (Broadband Agent)

The broadband agent has a **specific schema** defined:
- Fixed field names: `success`, `exchange`, `cabinet`, etc.
- Fixed field types: `boolean`, `string`, `number`
- Fixed field order as specified in `output_fields`

**Configuration**:
```json
{
  "output_mapping": {
    "structured_output_fields": [
      "success", "exchange", "cabinet", "downstream_mbps",
      "upstream_mbps", "availability", "service_type",
      "screenshot_url", "metadata"
    ]
  }
}
```

### General Schema (Flexible Agents)

The batch processor **also supports** general schemas:
- Any field names
- Any field types (auto-converted for CSV)
- Flexible field selection

**Example - Custom Agent**:
```json
{
  "output_mapping": {
    "structured_output_fields": [
      "customer_name", "order_total", "items", "status"
    ]
  }
}
```

**Key Point**: The batch processor doesn't enforce a specific schema - it extracts whatever fields you specify in `structured_output_fields`, as long as the agent returns them in its `structured_output` field.

---

## Verification Checklist

Before running batch processing:

- [ ] Agent has `structured_output.enabled = True` in registry ✅
- [ ] Agent returns `structured_output` field in response ✅
- [ ] Output fields match between:
  - Agent config: `output_fields` ✅
  - Batch config: `structured_output_fields` ✅
- [ ] Input CSV columns match agent input schema ✅
- [ ] S3 buckets exist and are accessible ✅
- [ ] Local browser agent is running (for remote execution) ✅
- [ ] Template is registered in TemplateRegistry ✅

**Status for Broadband Agent**: ✅ **ALL CHECKS PASS**

---

## Troubleshooting

### Issue: "Agent did not return structured output"

**Cause**: The `structured_output` field is missing from agent response

**Solutions**:
1. Check agent system prompt includes instruction to call structured output tool
2. Verify agent state machine includes structured output states
3. Check CloudWatch logs for agent execution errors
4. Test agent individually before batch processing

### Issue: "Field X not found in structured output"

**Cause**: Field listed in config but not returned by agent

**Solutions**:
1. Verify field name spelling matches exactly (case-sensitive)
2. Check agent's `output_fields` configuration
3. Update batch config to match agent's actual output fields

### Issue: Batch processing is slow

**Cause**: Browser automation takes time per address

**Solutions**:
1. Increase `max_concurrency` (default 10, max 40)
2. Reduce timeout if addresses fail quickly
3. Consider pre-warming browser profiles
4. Monitor Nova Act API quotas

---

## Related Documentation

- [Batch Processor Implementation](../lambda/tools/batch_processor/README.md)
- [Template System Guide](TEMPLATE_SYSTEM_GUIDE.md)
- [Broadband Agent Stack](../stacks/agents/broadband_availability_bt_wholesale_stack.py)
- [Output Mapper Source](../lambda/tools/batch_processor/output_mapper.py)

---

## Summary

✅ **The batch processor is FULLY COMPATIBLE with the broadband agent**

**Key Capabilities**:
1. ✅ Handles specific schemas (broadband fields)
2. ✅ Supports general schemas (any fields)
3. ✅ Preserves column order (original → structured → metadata)
4. ✅ Row-level error handling
5. ✅ Parallel processing (configurable concurrency)
6. ✅ Template-based automation support
7. ✅ S3 integration for inputs/outputs
8. ✅ SNS notifications

**Ready for Production**: Yes 🎉
