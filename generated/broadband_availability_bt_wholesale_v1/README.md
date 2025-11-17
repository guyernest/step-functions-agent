# broadband_availability_bt_wholesale Agent

Auto-generated extraction agent from canonical schema.

## Schema Information

- **Extraction Name**: broadband_availability_bt_wholesale
- **Version**: 1.0.0
- **Description**: Check broadband availability for UK addresses using BT Wholesale Broadband Checker portal
- **Tool Name**: broadband-availability-bt-wholesale
- **Agent Name**: broadband-availability-bt-wholesale-structured

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "postcode": {
      "type": "string",
      "description": "UK postcode in format like SW1A 1AA",
      "required": true,
      "pattern": "^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$"
    },
    "building_number": {
      "type": "string",
      "description": "Building number (e.g., '1', '23A')",
      "required": true
    },
    "full_address": {
      "type": "string",
      "description": "Full address for disambiguation when multiple matches exist",
      "required": false
    },
    "street": {
      "type": "string",
      "description": "Street or road name (e.g., 'High Street', 'Park Road')",
      "required": true
    }
  }
}
```

## Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the broadband availability check succeeded",
      "required": true
    },
    "cabinet": {
      "type": "string",
      "description": "Street cabinet number"
    },
    "service_type": {
      "type": "string",
      "description": "Type of broadband service available",
      "enum": [
        "ADSL",
        "VDSL",
        "FTTC",
        "FTTP",
        "unknown"
      ]
    },
    "exchange": {
      "type": "string",
      "description": "BT exchange station name"
    },
    "upstream_mbps": {
      "type": "number",
      "description": "Maximum upload speed in Mbps"
    },
    "availability": {
      "type": "boolean",
      "description": "Whether broadband service is available"
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata from the extraction"
    },
    "downstream_mbps": {
      "type": "number",
      "description": "Maximum download speed in Mbps"
    },
    "screenshot_url": {
      "type": "string",
      "description": "URL of browser recording or screenshot"
    }
  }
}
```

## Browser Configuration

- **Profile**: Bt_broadband
- **Starting URL**: https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome
- **Timeout**: 300 seconds
- **Requires Login**: false

## Generated Artifacts

- `stack.py` - CDK stack definition
- `browser_script_template.json` - Browser automation script template
- `tool_spec.json` - Tool specification for agent
- `output_tool_spec.json` - Output tool (print_output) specification
- `batch_mapping.json` - Batch processor mapping configuration
- `validator.py` - Schema validator
- `canonical_schema.json` - Original canonical schema

## Usage

### Deploy the Agent

```bash
cd ../../../../generated/broadband_availability_bt_wholesale_v1
cdk deploy
```

### Test Locally

```bash
python validator.py --input test_input.json --output test_output.json
```

### Use in Batch Processing

Configure the batch processor with `batch_mapping.json`:

```bash
aws stepfunctions start-execution \
  --state-machine-arn <batch-processor-arn> \
  --input file://batch_input.json
```

## Metadata

- **Author**: system
- **Created**: 2025-10-17
- **Tags**: broadband, availability, uk, bt-wholesale, infrastructure, vdsl, fttc
- **Use Cases**: batch-processing, api-integration, address-validation, infrastructure-planning
