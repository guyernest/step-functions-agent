# Broadband Availability Checker Agent

## Overview

The Broadband Availability Checker Agent is an AWS Bedrock Agent Core implementation that automates broadband availability checks through the BT Wholesale portal. It uses Nova Act for browser automation with S3 recording capabilities for human verification.

## Key Features

- **Flexible Address Input**: Accepts both simple strings ("13 Albion Dr, London E8 4LX") and structured objects
- **Automated Browser Navigation**: Uses Nova Act to navigate BT Wholesale portal
- **Health Check Support**: Implements `/ping` endpoint for Agent Core runtime monitoring  
- **S3 Recording Storage**: Automatically uploads browser session recordings
- **Concurrent Request Prevention**: Tracks active tasks to prevent duplicate checks

## Architecture

### Components

1. **broadband_checker_agent.py** - Main agent implementation using Nova Act
2. **broadband_extraction_config.json** - Flexible configuration for data extraction rules
3. **broadband_spreadsheet_processor.py** - Step Functions integration for batch processing

### Technology Stack

- **AWS Bedrock Agent Core** - Agent runtime framework
- **Nova Act** - Browser automation with recording
- **Nova Pro Model** - LLM for intelligent navigation
- **Python 3.11+** - Runtime environment

## Features

### Core Capabilities

- ✅ Automated address entry and search
- ✅ Intelligent address matching from selection lists
- ✅ Structured data extraction (speeds, availability, restrictions)
- ✅ Session recording for human verification
- ✅ Batch processing from spreadsheets
- ✅ Parallel execution support
- ✅ Flexible extraction rules via JSON configuration
- ✅ Conditional data extraction logic

### Extracted Data Fields

- VDSL Range A/B speeds (downstream/upstream)
- G.fast availability status
- FTTP availability and installation process
- Exchange and cabinet information
- WLR withdrawal status
- SOADSL restrictions
- Downstream handback thresholds

## Installation

### Prerequisites

- AWS Account with Bedrock Agent Core access
- Python 3.10+
- Nova Act API key stored in AWS Parameter Store at `/agentcore/nova-act-api-key`
- AWS profile configured (`CGI-PoC`)

### Setup

1. **Configure the agent:**
   ```bash
   make agentcore-broadband-configure
   ```

2. **Deploy to Agent Core:**
   ```bash
   make agentcore-broadband-deploy-agentcore
   ```

3. **View logs:**
   ```bash
   make agentcore-broadband-logs-body
   ```

## Usage

### API Formats

The agent accepts multiple payload formats:

#### 1. Simple Address String
```json
{
  "address": "13C Albion Dr, London E8 4LX, UK"
}
```

#### 2. Structured Address
```json
{
  "address": {
    "building_number": "13",
    "street": "ALBION DRIVE",
    "town": "HACKNEY, LONDON",
    "postcode": "E8 4LX"
  }
}
```

#### 3. Test Mode
```json
{
  "test": true
}
```

#### 4. Natural Language (via Strands Agent)
```json
{
  "prompt": "Check broadband for 10 Downing Street, London SW1A 2AA"
}
```

### Batch Processing from Spreadsheet

```python
# Step Functions event
{
    "input_bucket": "my-bucket",
    "input_key": "addresses/input.xlsx",
    "output_bucket": "my-bucket",
    "parallel_workers": 5,
    "batch_size": 10,
    "save_recordings": true
}
```

### Spreadsheet Format

Expected columns in input spreadsheet:
- Building Number
- Building Name
- Street
- Town
- Postcode
- Customer Reference (optional)

## Customization

### Modifying Extraction Rules

Edit `broadband_extraction_config.json` to:

1. **Add new fields to extract:**

```json
{
  "field_name": "new_field",
  "selector_path": "Field Label -> Value",
  "data_type": "string",
  "required": false
}
```

2. **Add conditional extraction:**

```json
{
  "field_name": "conditional_field",
  "condition_field": "gfast_available",
  "condition_value": "true",
  "selector_path": "G.fast Speed -> Downstream"
}
```

3. **Modify address matching rules:**

```json
"address_matching_rules": {
    "priority_order": ["exact", "fuzzy"],
    "fuzzy_threshold": 0.85,
    "handle_flats": true
}
```

### Extending the Agent

To add new extraction logic:

1. Update the extraction prompt in `_create_extraction_prompt()`
2. Enhance parsing in `_parse_nova_response()`
3. Add new fields to `BroadbandCheckResult` dataclass

## Integration with Step Functions

### State Machine Definition

```json
{
  "Comment": "Process broadband availability checks",
  "StartAt": "LoadSpreadsheet",
  "States": {
    "LoadSpreadsheet": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:broadband-spreadsheet-processor",
      "Next": "ProcessComplete"
    },
    "ProcessComplete": {
      "Type": "Succeed"
    }
  }
}
```

### Output Format

Results are saved as Excel with additional columns:
- Original address fields
- Extracted broadband data
- Recording URLs for verification
- Error messages for failed checks

## Monitoring and Debugging

### Viewing Logs

```bash
# View logs with timestamps and body fields only
make agentcore-broadband-logs-body
```

This displays clean output:
```
2025-09-06T03:46:09.042000+00:00 Nova Act API key configured
2025-09-06T03:46:10.123000+00:00 📝 Step 1: Filling and submitting form...
2025-09-06T03:46:15.456000+00:00 ✓ Form submitted
```

### S3 Recordings

Browser session recordings are automatically uploaded to:
```
s3://nova-act-browser-results-prod-672915487120/broadband-checker/{task_id}/
```

### Common Issues and Solutions

1. **Address not found:**
   - Check postcode format
   - Try with minimal fields (just postcode)
   - Review fuzzy matching threshold

2. **Extraction failures:**
   - Check if portal layout changed
   - Update extraction prompts
   - Review Nova Act recordings

3. **Rate limiting:**
   - Adjust `rate_limit_delay_ms` in config
   - Reduce parallel workers
   - Implement exponential backoff

## Performance Optimization

### Parallel Processing

```json
{
  "parallel_workers": 10,
  "batch_size": 20
}
```

### Caching

Results are cached in `/tmp` for the Lambda execution duration.

### Timeout Configuration

- Lambda timeout: 120 seconds
- Nova Act max_steps: 20
- Browser session timeout: 300 seconds

## Key Learnings

### Agent Core Integration

1. **Entry Point Pattern**: Must use `@app.entrypoint` decorator and call `app.run()` in main
2. **Health Check**: The `/ping` endpoint is critical for runtime monitoring
3. **No Context Parameter**: Entry point takes only `payload`, not `(payload, context)`

### Browser Automation

1. **SSL Certificates**: Use `ignore_https_errors=True` for sites with certificate issues
2. **Step-by-Step Execution**: Break interactions into multiple `nova_act.act()` calls
3. **Page Navigation**: URL changes from `#/ADSL/AddressHome` to `#/ADSL/AddressFeatureProduct`

### Logging

1. **OpenTelemetry Format**: Logs are in nested JSON format
2. **Body Field Extraction**: Use `awk` and `jq` to extract readable messages
3. **Buffering Issues**: Direct `aws logs tail` works better than complex pipelines

### Unit Tests

```python
def test_address_parsing():
    address = AddressInput(
        building_number="13",
        postcode="E8 4LX"
    )
    assert address.to_search_string() == "13, E8 4LX"
```

## Best Practices

1. **Always validate addresses** before processing
2. **Save recordings** for audit trail
3. **Handle errors gracefully** with partial results
4. **Monitor rate limits** to avoid blocking
5. **Update extraction rules** regularly as portal changes

## Future Enhancements

- [ ] Support for additional portals (Openreach, Virgin Media)
- [ ] ML-based address matching
- [ ] Real-time progress updates via WebSocket
- [ ] Automatic retry with different address formats
- [ ] Integration with CRM systems
- [ ] Historical data tracking and comparison

## Support

For issues or questions:
1. Check Nova Act recordings for browser behavior
2. Review Lambda logs in CloudWatch
3. Validate extraction configuration
4. Test with known good addresses first