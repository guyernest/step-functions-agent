# Batch Processing Testing Guide

## Overview
The batch processing system allows you to process CSV files through structured-output agents in parallel, with automatic result aggregation.

## Prerequisites
1. Deploy the batch processor infrastructure:
   ```bash
   cdk deploy batch-processor-tool-prod
   ```

2. Deploy the batch orchestrator agent:
   ```bash
   cdk deploy batch-orchestrator-agent-prod
   ```

3. Ensure your target agent has structured output enabled (implements `return_structured_data` tool)

## Testing via Batch Orchestrator Agent

### Method 1: Conversational Approach
Simply tell the agent what you want to process:
```
Process the CSV file at s3://batch-processor-results-prod-672915487120/test_addresses_short.csv
using the broadband-checker-structured agent to check broadband speeds
```

### Method 2: Explicit Configuration
Use the orchestrator tools directly:

1. **Analyze CSV structure**:
   ```json
   {
     "name": "analyze_csv_structure",
     "input": {
       "csv_s3_uri": "s3://batch-processor-results-prod-672915487120/test_addresses_short.csv"
     }
   }
   ```

2. **Validate agent compatibility**:
   ```json
   {
     "name": "validate_agent_compatibility",
     "input": {
       "agent_name": "broadband-checker-structured"
     }
   }
   ```

3. **Execute batch processing**:
   ```json
   {
     "name": "execute_batch_processor",
     "input": {
       "csv_s3_uri": "s3://batch-processor-results-prod-672915487120/test_addresses_short.csv",
       "agent_name": "broadband-checker-structured",
       "input_mapping": {
         "address": "address",
         "postcode": "postcode"
       },
       "output_mapping": {
         "structured_output_fields": ["download_speed", "upload_speed", "exchange_station", "screenshot_url"],
         "include_original": true,
         "add_metadata": true
       },
       "max_concurrency": 10
     }
   }
   ```

4. **Monitor execution**:
   ```json
   {
     "name": "monitor_batch_execution",
     "input": {
       "execution_arn": "arn:aws:states:us-west-2:672915487120:execution:..."
     }
   }
   ```

## Direct Step Functions Testing

Use the Step Functions console with this test input:
```json
{
  "csv_s3_uri": "s3://batch-processor-results-prod-672915487120/test_addresses_short.csv",
  "target": {
    "type": "agent",
    "name": "broadband-checker-structured"
  },
  "input_mapping": {
    "address": "address",
    "postcode": "postcode"
  },
  "output_mapping": {
    "structured_output_fields": [
      "download_speed",
      "upload_speed",
      "exchange_station",
      "screenshot_url"
    ],
    "include_original": true,
    "add_metadata": true
  },
  "execution_config": {
    "max_concurrency": 10
  }
}
```

## Expected Output Format
The batch processor will generate a new CSV with:
- All original columns (if `include_original: true`)
- New columns for each structured output field
- Metadata columns (if `add_metadata: true`):
  - `_processing_time`: Time taken to process each row
  - `_agent_used`: Name of the agent that processed the row
  - `_timestamp`: When the row was processed

## Troubleshooting

### Common Issues

1. **Agent not found error**:
   - Verify agent name matches exactly (case-sensitive)
   - Check agent is registered in DynamoDB agent registry

2. **Agent not compatible error**:
   - Ensure agent has `structured_output` enabled
   - Agent must implement `return_structured_data` tool

3. **CSV access error**:
   - Verify S3 URI is correct
   - Check Lambda functions have S3 read permissions for the bucket

4. **Map state failures**:
   - Check CloudWatch logs for individual Lambda invocations
   - Reduce `max_concurrency` if hitting Lambda limits

### Monitoring
- **Step Functions Console**: View execution graph and status
- **CloudWatch Logs**: Check Lambda function logs for detailed errors
- **S3 Results Bucket**: Find output CSV in `s3://batch-processor-results-prod-672915487120/results/`

## Performance Tuning

- **max_concurrency**: Controls parallel processing (default: 10)
  - Increase for faster processing with more Lambda capacity
  - Decrease if hitting Lambda throttling limits

- **timeout_seconds**: Per-row processing timeout (default: 300)
  - Increase for complex agent processing
  - Decrease for simple transformations

## Example Agents Compatible with Batch Processing
- `broadband-checker-structured-v2`: Checks broadband availability (unified LLM pattern)
- `company-enrichment-structured`: Enriches company data
- Any agent with `structured_output.enabled: true` in registry

## Note on Agent Versions
The original `broadband-checker-structured` agent has been replaced with `broadband-checker-structured-v2` which uses the unified LLM pattern with JSONata for better maintainability.