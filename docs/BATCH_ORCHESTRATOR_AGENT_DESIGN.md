# Batch Orchestrator Agent - Design Document

## Overview

The Batch Orchestrator Agent is a high-level agent that manages batch CSV processing workflows. It acts as an intelligent coordinator between users, the batch processor tool, and agents with structured output capabilities.

## Purpose

Provide a conversational interface for batch processing operations while enforcing the structured output requirement for reliable CSV generation.

## Architecture

```
User Request
     │
     ▼
┌─────────────────────────┐
│  Batch Orchestrator     │
│       Agent             │
├─────────────────────────┤
│ - Validates CSV input   │
│ - Selects target agent  │
│ - Configures mapping    │
│ - Monitors execution    │
│ - Returns results       │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│   Batch Processor       │
│   (Step Functions)      │
└─────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│  Target Agent with      │
│  Structured Output      │
└─────────────────────────┘
```

## Key Features

### 1. Intelligent Agent Selection

The orchestrator can recommend or select appropriate agents based on:
- CSV column analysis
- User's processing goals
- Agent capabilities registry
- Structured output compatibility

### 2. Automatic Mapping Configuration

Analyzes CSV headers and generates input/output mappings:
- Column name matching
- Data type inference
- Required field validation
- Output schema alignment

### 3. Execution Management

- Starts batch processor execution
- Monitors progress
- Handles errors gracefully
- Provides status updates

### 4. Results Handling

- Returns S3 URLs for processed files
- Provides summary statistics
- Offers download links
- Suggests next steps

## Agent Tools

### 1. analyze_csv_structure
Analyzes CSV file structure and content:

```python
def analyze_csv_structure(s3_uri):
    """
    Analyzes a CSV file to understand its structure.
    Returns column names, data types, and sample data.
    """
    return {
        "columns": ["name", "email", "company"],
        "row_count": 1000,
        "sample_data": [...],
        "data_types": {"name": "string", "email": "string", "company": "string"}
    }
```

### 2. validate_agent_compatibility
Checks if an agent supports structured output:

```python
def validate_agent_compatibility(agent_name):
    """
    Validates that an agent has structured output capability.
    Returns compatibility status and output schema.
    """
    return {
        "compatible": true,
        "structured_output_enabled": true,
        "output_schema": {...},
        "available_fields": ["industry", "employee_count", "revenue"]
    }
```

### 3. generate_batch_config
Creates batch processor configuration:

```python
def generate_batch_config(csv_uri, agent_name, mappings):
    """
    Generates configuration for the batch processor.
    """
    return {
        "csv_s3_uri": csv_uri,
        "target": {
            "type": "agent",
            "name": agent_name
        },
        "input_mapping": mappings,
        "output_mapping": {
            "structured_output_fields": [...]
        }
    }
```

### 4. execute_batch_processor
Starts the batch processing job:

```python
def execute_batch_processor(config):
    """
    Executes the batch processor Step Functions state machine.
    Returns execution ARN for monitoring.
    """
    return {
        "execution_arn": "arn:aws:states:...",
        "status": "RUNNING",
        "start_time": "2024-01-20T10:00:00Z"
    }
```

### 5. monitor_batch_execution
Monitors execution progress:

```python
def monitor_batch_execution(execution_arn):
    """
    Checks the status of a batch processing execution.
    """
    return {
        "status": "RUNNING",
        "rows_processed": 450,
        "total_rows": 1000,
        "percent_complete": 45,
        "estimated_completion": "2024-01-20T10:15:00Z"
    }
```

### 6. get_batch_results
Retrieves processing results:

```python
def get_batch_results(execution_arn):
    """
    Gets the results of a completed batch processing job.
    """
    return {
        "status": "SUCCEEDED",
        "output_csv_uri": "s3://bucket/results/output.csv",
        "rows_processed": 1000,
        "rows_succeeded": 980,
        "rows_failed": 20,
        "processing_time_seconds": 300
    }
```

## Conversation Flow

### Example 1: Basic Batch Processing

```
User: I need to enrich this company CSV file with industry and employee data
      File: s3://my-data/companies.csv

Agent: I'll help you enrich your company data. Let me analyze the CSV file first.

      [Calls analyze_csv_structure]

      I found a CSV with 500 companies containing columns: company_name, website, location.

      I'll use the company-enrichment-agent which provides:
      - Industry classification
      - Employee count estimates
      - Revenue estimates
      - Data confidence scores

      [Calls validate_agent_compatibility]

      ✓ The agent supports structured output for reliable CSV generation.

      Starting batch processing with these settings:
      - Concurrency: 10 parallel executions
      - Timeout: 60 seconds per company
      - Output: Original columns + enrichment data

      [Calls execute_batch_processor]

      Processing started. I'll monitor the progress...

      [Calls monitor_batch_execution periodically]

      Progress: 250/500 companies processed (50%)
      Estimated completion: 5 minutes

      [After completion, calls get_batch_results]

      ✅ Batch processing complete!

      Results:
      - Successfully enriched: 485 companies (97%)
      - Failed: 15 companies (3%)
      - Output file: s3://my-data/results/companies_enriched.csv
      - Processing time: 4 minutes 32 seconds

      The enriched CSV includes:
      - All original columns
      - industry
      - employee_count
      - revenue_estimate
      - confidence_score
      - processing metadata

      You can download the results from the S3 link above.

User: Why did 15 companies fail?

Agent: Let me check the error details for the failed rows.

      The 15 failures were due to:
      - 8 companies: Website no longer active (404 errors)
      - 5 companies: Unable to identify company from provided name
      - 2 companies: Timeout during data gathering

      These failed rows are marked in the output CSV with error details in the
      _error_message column, so you can review and potentially reprocess them.
```

### Example 2: Guided Agent Selection

```
User: I have a CSV of customer support tickets that need processing

Agent: I'll help you process your support tickets. What would you like to do with them?

      Available options with structured output support:
      1. Classify tickets by category and priority
      2. Generate suggested responses
      3. Extract key information and entities
      4. Sentiment analysis and escalation routing
      5. All of the above (comprehensive analysis)

User: Let's classify them and generate responses

Agent: Perfect! I'll use the ticket-classifier-agent which will:
      - Categorize tickets (Technical, Billing, General, etc.)
      - Assign priority levels (Low, Medium, High)
      - Generate suggested responses
      - Provide confidence scores

      Let me analyze your CSV structure first...

      [Continues with processing flow]
```

## State Machine Definition

```yaml
StartAt: ValidateInput
States:
  ValidateInput:
    Type: Task
    Resource: validate_csv_and_agent
    Next: ConfigureMapping

  ConfigureMapping:
    Type: Task
    Resource: generate_batch_config
    Next: ExecuteBatch

  ExecuteBatch:
    Type: Task
    Resource: arn:aws:states:::states:startExecution.sync:2
    Parameters:
      StateMachineArn: ${BatchProcessorArn}
      Input: ${GeneratedConfig}
    Next: ProcessResults

  ProcessResults:
    Type: Task
    Resource: format_results_for_user
    Next: Success

  Success:
    Type: Succeed
```

## Error Handling

### Validation Errors

```python
if not agent_has_structured_output:
    return {
        "error": "INCOMPATIBLE_AGENT",
        "message": f"The agent '{agent_name}' doesn't support structured output. "
                   f"Please choose one of these compatible agents: {compatible_agents}",
        "suggestion": "Use 'company-enrichment-agent' for similar functionality"
    }
```

### Partial Failures

```python
if failed_rows > 0:
    return {
        "status": "COMPLETED_WITH_ERRORS",
        "message": f"Processed {success_rows} rows successfully, {failed_rows} failed",
        "error_details_location": f"{output_csv_uri} (see _error_message column)",
        "retry_suggestion": "You can reprocess failed rows by filtering the output CSV"
    }
```

## Configuration

### Agent Registration

```python
{
    "agent_name": "batch-orchestrator-agent",
    "description": "Orchestrates batch CSV processing with structured output agents",
    "tools": [
        "analyze_csv_structure",
        "validate_agent_compatibility",
        "generate_batch_config",
        "execute_batch_processor",
        "monitor_batch_execution",
        "get_batch_results"
    ],
    "capabilities": {
        "batch_processing": true,
        "structured_output_required": true,
        "max_csv_size": "5GB",
        "supported_agents": ["company-enrichment", "ticket-classifier", "address-validator"]
    }
}
```

### System Prompt

```
You are a Batch Processing Orchestrator that helps users process CSV files at scale.

Your responsibilities:
1. Guide users through batch processing workflows
2. Ensure target agents have structured output capability
3. Configure appropriate input/output mappings
4. Monitor executions and provide progress updates
5. Explain results and handle errors gracefully

Important requirements:
- Only use agents with structured output support
- Validate CSV structure before processing
- Provide clear status updates during execution
- Explain any failures with actionable suggestions

Available agents with structured output:
- company-enrichment-agent: Enriches company data
- ticket-classifier-agent: Classifies support tickets
- address-validator-agent: Validates and geocodes addresses
- product-analyzer-agent: Analyzes product descriptions
- customer-scorer-agent: Scores customer profiles

Always confirm the processing requirements with the user before starting large batches.
```

## Deployment

### Infrastructure Requirements

- Access to S3 for CSV files
- Permission to invoke Step Functions
- DynamoDB access for agent registry
- CloudWatch for monitoring

### IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:GetExecutionHistory"
      ],
      "Resource": ["arn:aws:states:*:*:stateMachine:batch-processor-*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": ["arn:aws:dynamodb:*:*:table/AgentRegistry"]
    }
  ]
}
```

## Monitoring and Metrics

### Key Metrics

- Batch jobs initiated per hour
- Average processing time per row
- Success/failure rates by agent
- CSV sizes processed
- User satisfaction (via feedback)

### CloudWatch Dashboard

```
┌─────────────────────────────────────┐
│  Batch Processing Overview          │
├─────────────────────────────────────┤
│ Active Jobs: 3                      │
│ Rows/Hour: 45,000                   │
│ Success Rate: 96.5%                 │
│ Avg Time/Row: 1.2s                  │
└─────────────────────────────────────┘
```

## Future Enhancements

### Phase 1 (Current)
- Basic orchestration with manual configuration
- Support for pre-defined agents
- Simple progress monitoring

### Phase 2 (Planned)
- Auto-discovery of compatible agents
- Intelligent mapping suggestions
- Cost estimation before execution
- Incremental processing support

### Phase 3 (Future)
- Multi-agent pipelines
- Custom transformation rules
- Real-time streaming support
- Advanced scheduling options

## Success Criteria

1. **Reliability**: 99% of valid batch jobs complete successfully
2. **Performance**: Process 10,000 rows in under 10 minutes
3. **Usability**: Users can start batch jobs with minimal configuration
4. **Accuracy**: Structured output validation catches 100% of schema violations
5. **Transparency**: Clear progress updates and error reporting

## Conclusion

The Batch Orchestrator Agent bridges the gap between conversational interfaces and large-scale data processing, ensuring all batch operations use structured output for reliable, predictable results. By enforcing structured output requirements and providing intelligent guidance, it makes batch processing accessible while maintaining data quality and system reliability.