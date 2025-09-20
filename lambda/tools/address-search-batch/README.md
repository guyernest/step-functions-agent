# Address Search Batch Tool

## Overview

The Address Search Batch Tool is a Step Functions-based tool that processes CSV files containing UK addresses and enriches them with property information using the web-search-agent-unified. This is the **first Step Functions tool** in our framework, demonstrating how to create long-running batch processing tools that exceed Lambda's 15-minute timeout.

## Architecture

This tool is unique because:
1. **It's a Step Functions state machine, not a Lambda function**
2. **Registered in the tool registry with `tool_type: "state_machine"`**
3. **Invoked by agents using `states:startExecution.sync:2`**
4. **Can run for hours processing thousands of addresses**

## How It Works

```
CSV with Addresses → Distributed Map → Web Search Agent → Enriched CSV
```

1. **Input**: CSV file in S3 with UK addresses
2. **Processing**: Each address is searched using web-search-agent-unified
3. **Output**: Enriched CSV with property information (type, bedrooms, value, etc.)

## Configuration

The tool configuration is defined in `config.json`:

```json
{
  "tool_name": "address_search_batch",
  "target_agent": {
    "name": "web-search-agent-unified",
    "type": "agent"
  },
  "default_mappings": {
    "input_mapping": {
      "column_mappings": {
        "address": "query"
      }
    },
    "output_mapping": {
      "columns": [
        {"name": "property_type", "source": "$.property_info.type"},
        {"name": "bedrooms", "source": "$.property_info.bedrooms"},
        {"name": "estimated_value", "source": "$.property_info.estimated_value"}
      ]
    }
  }
}
```

## Deployment

### 1. Deploy the Stack

```bash
# Deploy the address search batch tool
cdk deploy AddressSearchBatchToolStack-prod
```

This creates:
- Step Functions state machine: `address-search-batch-prod`
- Lambda functions for mapping: `address-search-mapper-prod`, etc.
- S3 bucket for results: `address-search-batch-results-prod-{account}`
- Tool registry entry with `tool_type: "state_machine"`

### 2. Integration with Agents

To use this tool in an agent, the agent's Step Functions definition must handle state machine tools:

```json
{
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.tool.tool_type",
      "StringEquals": "state_machine",
      "Next": "InvokeStateMachineTool"
    },
    {
      "Variable": "$.tool.tool_type",
      "StringEquals": "lambda",
      "Next": "InvokeLambdaTool"
    }
  ]
},
"InvokeStateMachineTool": {
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution.sync:2",
  "Parameters": {
    "StateMachineArn.$": "$.tool.resource_arn",
    "Input": {
      "csv_s3_uri.$": "$.input.csv_s3_uri",
      "output_bucket.$": "$.input.output_bucket"
    }
  },
  "End": true
}
```

## Usage Example

### 1. Upload Test CSV to S3

```bash
# Upload the test addresses
aws s3 cp test_addresses.csv s3://my-bucket/test/addresses.csv
```

### 2. Invoke via Agent

When an agent calls this tool:

```json
{
  "name": "address_search_batch",
  "input": {
    "csv_s3_uri": "s3://my-bucket/test/addresses.csv",
    "output_bucket": "address-search-batch-results-prod-123456789012"
  }
}
```

### 3. Monitor Execution

The state machine execution can be monitored in the Step Functions console. Unlike Lambda tools, this can run for hours.

### 4. Get Results

The enriched CSV will be available at:
```
s3://address-search-batch-results-prod-123456789012/batch-results/{execution-id}/final/output.csv
```

## Sample Output

Input CSV:
```csv
address,postcode
"10 Downing Street, Westminster, London",SW1A 2AA
"221B Baker Street, London",NW1 6XE
```

Output CSV:
```csv
address,postcode,property_type,bedrooms,estimated_value,council_tax_band,_status
"10 Downing Street, Westminster, London",SW1A 2AA,Terraced,4,£2,000,000,Band H,SUCCESS
"221B Baker Street, London",NW1 6XE,Flat,2,£850,000,Band F,SUCCESS
```

## Key Integration Points

### Tool Registry Changes

This tool introduces a new field in the tool registry:
- **`tool_type`**: Either `"lambda"` (default) or `"state_machine"`
- **`resource_arn`**: Generic ARN field that works for both Lambda and Step Functions

### Agent Generator Changes

The Step Functions generator (`step_functions_generator.py`) needs to handle routing:

```python
def generate_tool_routing():
    for tool in tools:
        if tool.get('tool_type') == 'state_machine':
            # Use StepFunctions:StartExecution.sync:2
            task = {
                "Type": "Task",
                "Resource": "arn:aws:states:::states:startExecution.sync:2",
                "Parameters": {
                    "StateMachineArn": tool['resource_arn'],
                    "Input": {"$": "$.tool_input"}
                }
            }
        else:
            # Existing Lambda invoke
            task = {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": tool['resource_arn'],
                    "Payload": {"$": "$"}
                }
            }
```

## Advantages of Step Functions Tools

1. **No Lambda Timeout**: Can run for days if needed
2. **Cost Efficient**: No idle Lambda time charges
3. **Better Observability**: Visual workflow in Step Functions console
4. **Native CSV Processing**: Distributed Map reads CSV directly
5. **Automatic Parallelization**: Process multiple rows concurrently

## Customization

### Custom Address Mapping

Override the default mapping when invoking:

```json
{
  "csv_s3_uri": "s3://bucket/addresses.csv",
  "custom_mappings": {
    "input_mapping": {
      "transformations": {
        "query": {
          "type": "template",
          "config": {
            "template": "Property details for {address} {postcode} UK market value",
            "variables": {
              "address": "address",
              "postcode": "postcode"
            }
          }
        }
      }
    }
  }
}
```

### Execution Configuration

Control concurrency and timeouts:

```json
{
  "execution_config": {
    "max_concurrency": 10,  // Process 10 addresses in parallel
    "timeout_seconds": 120,  // 2 minutes per address
    "continue_on_error": true
  }
}
```

## Testing

### Unit Tests

```bash
# Test the address mapper
python address_mapper.py
```

### Integration Test

```bash
# Start execution directly
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:eu-west-1:123456789012:stateMachine:address-search-batch-prod \
  --input '{"csv_s3_uri":"s3://bucket/test_addresses.csv"}'
```

## Troubleshooting

### Common Issues

1. **"Access Denied" on S3**: Check IAM permissions for the state machine role
2. **Target agent not found**: Verify web-search-agent-unified is deployed
3. **CSV parse errors**: Ensure CSV has proper headers and encoding
4. **Timeout errors**: Increase timeout_seconds in execution_config

### Monitoring

- **Step Functions Console**: Visual execution tracking
- **CloudWatch Logs**: Detailed Lambda execution logs
- **X-Ray**: End-to-end tracing if enabled

## Future Enhancements

1. **Multiple Agent Support**: Route different address types to specialized agents
2. **Caching**: Store previous search results to avoid duplicate searches
3. **Enrichment Sources**: Add multiple data sources (council tax, sold prices, etc.)
4. **International Support**: Extend beyond UK addresses

## Summary

The Address Search Batch Tool demonstrates how to create sophisticated batch processing tools that:
- Are registered as Step Functions state machines in the tool registry
- Can be invoked by agents just like Lambda tools
- Run without timeout constraints
- Process CSV data at scale

This pattern can be applied to any batch processing scenario that needs to run longer than Lambda's 15-minute limit.