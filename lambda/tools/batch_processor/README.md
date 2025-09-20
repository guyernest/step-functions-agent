# Batch Processor Tool

## Overview

The Batch Processor Tool is a Step Functions state machine that processes large CSV datasets through agents or other tools in parallel, handling operations that exceed Lambda's 15-minute timeout limit. Unlike traditional Lambda-based tools, this tool is invoked directly via `states:startExecution.sync:2` from the calling agent, allowing it to run for hours or days while the caller waits for completion. It reads input data from CSV files in S3, processes each row through a specified agent or tool, and generates an output CSV with the original data plus new columns containing the processing results.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   S3 CSV    │────▶│ Distributed Map  │────▶│  Agent/Tool     │────▶│ JSON Results │
│    Input    │     │ (Native Reader)  │     │  Execution      │     │  (S3)        │
└─────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
                                                                              │
                                                                              ▼
                                                                     ┌──────────────┐
                                                                     │ JSON to CSV  │
                                                                     │   Lambda     │
                                                                     └──────────────┘
                                                                              │
                                                                              ▼
                                                                     ┌──────────────┐
                                                                     │  Final CSV   │
                                                                     │    Output    │
                                                                     └──────────────┘
```

### Key Components

1. **Distributed Map State**: Native CSV reading from S3, no parsing Lambda needed
2. **Input Mapper Lambda**: Transforms each CSV row to agent/tool input format  
3. **Tool/Agent Router**: Routes each row to the specified tool or agent
4. **Output Mapper Lambda**: Transforms results back to enriched row format
5. **JSON to CSV Converter**: Simple Lambda that converts final JSON results to CSV

### Architecture Decision: Why Simple JSON-to-CSV Conversion

During design, we evaluated three approaches for generating the final CSV output:

#### Option 1: Simple JSON-to-CSV Lambda (Chosen)
- **Approach**: ResultWriter outputs JSON → Single Lambda converts to CSV
- **Pros**: Simplest implementation, fast, no external dependencies
- **Cons**: Lambda reads all JSON files (but typically just 1-2 files)
- **Best for**: Most use cases with up to 100K rows

#### Option 2: Athena with SQL Builder
- **Approach**: ResultWriter → Lambda builds SQL → Multiple Athena queries
- **Pros**: Can handle very large datasets, complex aggregations possible
- **Cons**: More complex, higher cost, slower execution
- **Best for**: Millions of rows or complex SQL transformations needed

#### Option 3: Pure Athena (No Lambda)
- **Approach**: Hardcoded Athena queries in Step Functions
- **Pros**: No Lambda for SQL generation
- **Cons**: Complex string manipulation in Step Functions, inflexible
- **Best for**: Fixed schema with no dynamic columns

We chose **Option 1** because ResultWriter typically outputs just 1-2 JSON files even for thousands of rows, making direct conversion the fastest and most cost-effective approach.

## Input Parameters

```json
{
  "csv_s3_uri": "s3://bucket/path/to/input.csv",
  "target": {
    "type": "agent | tool",
    "name": "agent_name_or_tool_name",
    "arn": "arn:aws:states:region:account:stateMachine:name"
  },
  "input_mapping": {
    "column_mappings": {
      "csv_column_name": "agent_input_field"
    },
    "static_values": {
      "field_name": "static_value"
    },
    "transformations": {
      "field_name": {
        "type": "concat | template | jsonpath",
        "config": {}
      }
    }
  },
  "output_mapping": {
    "columns": [
      {
        "name": "result_column",
        "source": "$.agent_output.field_path",
        "default": "N/A"
      }
    ],
    "include_original": true,
    "add_metadata": true
  },
  "execution_config": {
    "max_concurrency": 10,
    "timeout_seconds": 300,
    "retry_policy": {
      "max_attempts": 3,
      "backoff_rate": 2.0
    },
    "continue_on_error": true
  }
}
```

## Parameter Details

### `target` Configuration

Specifies which agent or tool to invoke for each row:

- **`type`**: Either "agent" (Step Functions state machine) or "tool" (Lambda function)
- **`name`**: The registered name in the tool registry
- **`arn`**: (Optional) Direct ARN if not using registry lookup

### `input_mapping` Configuration

Defines how CSV columns map to agent/tool inputs:

#### Column Mappings
Direct mapping from CSV columns to input fields:
```json
{
  "column_mappings": {
    "customer_id": "customerId",
    "email": "contactEmail",
    "query": "userQuery"
  }
}
```

#### Static Values
Add constant values to every invocation:
```json
{
  "static_values": {
    "environment": "production",
    "source": "batch_processor"
  }
}
```

#### Transformations
Apply transformations to values:

**Concatenation:**
```json
{
  "transformations": {
    "fullName": {
      "type": "concat",
      "config": {
        "columns": ["first_name", "last_name"],
        "separator": " "
      }
    }
  }
}
```

**Template:**
```json
{
  "transformations": {
    "prompt": {
      "type": "template",
      "config": {
        "template": "Process order {order_id} for customer {customer_name}",
        "variables": {
          "order_id": "order_number",
          "customer_name": "name"
        }
      }
    }
  }
}
```

**JSONPath:**
```json
{
  "transformations": {
    "nestedValue": {
      "type": "jsonpath",
      "config": {
        "column": "json_data",
        "path": "$.details.important_field"
      }
    }
  }
}
```

### `output_mapping` Configuration

Controls the structure of the output CSV:

#### Column Definitions
```json
{
  "columns": [
    {
      "name": "processing_result",
      "source": "$.result",
      "default": "ERROR"
    },
    {
      "name": "confidence_score",
      "source": "$.metadata.confidence",
      "type": "number",
      "format": "%.2f"
    },
    {
      "name": "extracted_entities",
      "source": "$.entities",
      "type": "json_string"
    }
  ]
}
```

#### Options
- **`include_original`**: (default: true) Include all original CSV columns
- **`add_metadata`**: (default: true) Add execution metadata columns:
  - `_execution_id`: Unique identifier for this batch
  - `_row_id`: Original row number
  - `_status`: SUCCESS | FAILED | TIMEOUT
  - `_error_message`: Error details if failed
  - `_execution_time_ms`: Processing time per row
  - `_timestamp`: ISO 8601 completion time

### `execution_config` Configuration

Controls execution behavior:

- **`max_concurrency`**: (default: 1) Number of parallel executions
- **`timeout_seconds`**: (default: 300) Per-row timeout
- **`retry_policy`**: Retry configuration for transient failures
- **`continue_on_error`**: (default: true) Continue processing remaining rows on failure

## Usage Examples

### Example 1: Customer Support Ticket Classification

Input CSV:
```csv
ticket_id,customer_email,description
1001,john@example.com,"Cannot login to account"
1002,jane@example.com,"Billing discrepancy last month"
```

Configuration:
```json
{
  "csv_s3_uri": "s3://support-data/tickets.csv",
  "target": {
    "type": "agent",
    "name": "ticket_classifier_agent"
  },
  "input_mapping": {
    "column_mappings": {
      "description": "ticketText",
      "customer_email": "customerEmail"
    }
  },
  "output_mapping": {
    "columns": [
      {
        "name": "category",
        "source": "$.classification.category"
      },
      {
        "name": "priority",
        "source": "$.classification.priority"
      },
      {
        "name": "suggested_response",
        "source": "$.suggestedResponse"
      }
    ],
    "include_original": true
  },
  "execution_config": {
    "max_concurrency": 5
  }
}
```

Output CSV:
```csv
ticket_id,customer_email,description,category,priority,suggested_response,_status,_execution_time_ms
1001,john@example.com,"Cannot login to account",Authentication,High,"Please reset your password...",SUCCESS,1250
1002,jane@example.com,"Billing discrepancy last month",Billing,Medium,"We'll review your billing...",SUCCESS,980
```

### Example 2: Product Description Generation

Input CSV:
```csv
product_id,title,features
P001,"Wireless Headphones","Noise canceling, 30hr battery"
P002,"Smart Watch","Heart rate monitor, GPS"
```

Configuration:
```json
{
  "csv_s3_uri": "s3://catalog/products.csv",
  "target": {
    "type": "tool",
    "name": "generate_description"
  },
  "input_mapping": {
    "transformations": {
      "prompt": {
        "type": "template",
        "config": {
          "template": "Write a compelling product description for {title} with features: {features}",
          "variables": {
            "title": "title",
            "features": "features"
          }
        }
      }
    }
  },
  "output_mapping": {
    "columns": [
      {
        "name": "marketing_description",
        "source": "$.description"
      },
      {
        "name": "seo_keywords",
        "source": "$.keywords",
        "type": "json_string"
      }
    ]
  }
}
```

### Example 3: Data Enrichment with Multiple Sources

Input CSV:
```csv
company_name,website
Acme Corp,acme.com
TechStart,techstart.io
```

Configuration:
```json
{
  "csv_s3_uri": "s3://enrichment/companies.csv",
  "target": {
    "type": "agent",
    "name": "company_enrichment_agent"
  },
  "input_mapping": {
    "column_mappings": {
      "company_name": "name",
      "website": "domain"
    },
    "static_values": {
      "enrichment_level": "full",
      "include_social": true
    }
  },
  "output_mapping": {
    "columns": [
      {
        "name": "industry",
        "source": "$.enrichment.industry"
      },
      {
        "name": "employee_count",
        "source": "$.enrichment.employees",
        "type": "number"
      },
      {
        "name": "revenue_estimate",
        "source": "$.enrichment.revenue"
      },
      {
        "name": "linkedin_url",
        "source": "$.social.linkedin"
      },
      {
        "name": "description",
        "source": "$.enrichment.description"
      }
    ]
  },
  "execution_config": {
    "max_concurrency": 3,
    "timeout_seconds": 60
  }
}
```

## Integration with Agents

### For Agent Developers

Your agent will receive input in the format:
```json
{
  "batchContext": {
    "executionId": "batch-123",
    "rowId": "5",
    "totalRows": 100
  },
  "input": {
    // Mapped fields from CSV based on input_mapping
  }
}
```

Your agent should return:
```json
{
  "result": "Success",
  "data": {
    // Your agent's output
  },
  "metadata": {
    // Optional metadata
  }
}
```

### For Tool Developers

Tools receive the standard tool invocation format:
```json
{
  "name": "tool_name",
  "input": {
    // Mapped fields from CSV
  },
  "id": "unique_invocation_id"
}
```

Return format:
```json
{
  "type": "tool_result",
  "tool_use_id": "unique_invocation_id",
  "content": {
    // Tool output
  }
}
```

## Error Handling

The batch processor implements several error handling strategies:

1. **Row-Level Errors**: Failed rows are marked in the output with error details
2. **Retries**: Configurable exponential backoff for transient failures
3. **Partial Success**: By default, continues processing remaining rows after failures
4. **Dead Letter Queue**: Failed rows after all retries are sent to DLQ for manual review
5. **Timeout Protection**: Per-row timeouts prevent single row from blocking entire batch

## Performance Considerations

### Concurrency Settings

- **Low (1-5)**: For rate-limited APIs or heavy processing
- **Medium (10-20)**: For moderate workloads with good API limits
- **High (50-100)**: For lightweight operations or internal tools

### Batch Size Recommendations

- **Small batches (<1000 rows)**: Can use higher concurrency
- **Medium batches (1000-10000 rows)**: Balance concurrency with monitoring
- **Large batches (>10000 rows)**: Consider splitting or use lower concurrency

### Cost Optimization

1. **Athena costs**: Minimize by using columnar formats and partitioning
2. **Step Functions costs**: State transitions are charged per state
3. **S3 costs**: Use lifecycle policies for temporary data
4. **Lambda/Agent costs**: Optimize timeout settings to avoid unnecessary charges

## Monitoring and Observability

### CloudWatch Metrics

- `BatchProcessor.RowsProcessed`: Total rows processed
- `BatchProcessor.RowsFailed`: Failed row count
- `BatchProcessor.ProcessingTime`: Per-row processing time
- `BatchProcessor.ConcurrentExecutions`: Current parallel executions

### CloudWatch Logs

Log groups:
- `/aws/stepfunctions/batch-processor`: Main orchestration logs
- `/aws/lambda/batch-processor-*`: Component function logs

### X-Ray Tracing

Enable tracing for detailed execution flow:
```json
{
  "execution_config": {
    "enable_xray": true
  }
}
```

## Limitations

1. **CSV Size**: Maximum 5GB per input file (S3 Select limitation)
2. **Row Size**: Individual rows must fit in Step Functions payload (256KB)
3. **Execution Time**: Maximum 1 year (Step Functions limit)
4. **Concurrency**: Limited by account-level Step Functions quotas
5. **Output Columns**: Maximum 1000 columns in output CSV

## Deployment

### Prerequisites

1. Deploy shared infrastructure stack:
```bash
make deploy-shared
```

2. Deploy the batch processor tool:
```bash
make deploy-tool TOOL_NAME=batch_processor
```

### IAM Permissions

The batch processor requires:
- S3: Read input bucket, write output bucket
- Athena: Create/query tables, UNLOAD operations
- Glue: Catalog access for Athena tables
- Step Functions: StartExecution for agents
- Lambda: Invoke for tools
- CloudWatch: Logs and metrics

### Testing

Run integration tests:
```bash
make test-batch-processor
```

Test with sample data:
```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:region:account:stateMachine:batch-processor \
  --input file://test/sample-batch-config.json
```

## Troubleshooting

### Common Issues

1. **"Access Denied" errors**: Check IAM permissions for S3 buckets and target agents/tools
2. **"Timeout" errors**: Increase `timeout_seconds` or optimize agent/tool performance
3. **"CSV Parse Error"**: Ensure CSV is properly formatted (RFC 4180 compliant)
4. **"Output Missing Columns"**: Verify `output_mapping.source` paths match agent output

### Debug Mode

Enable detailed logging:
```json
{
  "execution_config": {
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

## Best Practices

1. **Start Small**: Test with 10-row sample before full dataset
2. **Monitor Progress**: Use Step Functions console to track execution
3. **Validate Mappings**: Ensure input/output mappings match agent expectations
4. **Handle Nulls**: Provide defaults for optional fields
5. **Version Control**: Tag S3 outputs with execution IDs for traceability
6. **Cost Management**: Set up CloudWatch alarms for unexpected costs
7. **Data Privacy**: Use encryption for sensitive data in S3

## Support

For issues or questions:
1. Check CloudWatch Logs for detailed error messages
2. Review X-Ray traces for performance bottlenecks
3. Contact the platform team with execution ARN and error details

---

## Scalable Architecture (Future)

> **Note**: This section describes the planned DynamoDB-based architecture for handling unlimited batch sizes. The current implementation uses Step Functions payload passing, which works well for batches up to ~250 rows with filtered output.

### Design Goals

1. **Unlimited Scale**: Handle millions of rows without payload size limitations
2. **Generic & Configurable**: Work with any agent/tool through configuration, not code
3. **Progressive Enhancement**: Support both simple text extraction and structured output tools
4. **Cost Effective**: Use DynamoDB on-demand pricing with automatic TTL cleanup

### Architecture Overview

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  S3 CSV  │────▶│ Input Mapper │────▶│ Agent/Tool  │────▶│ DynamoDB     │────▶│ Aggregator │
│  Input   │     │   (Lambda)   │     │  Execution  │     │   Writer     │     │  (Lambda)  │
└──────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └────────────┘
                                                                   │                     │
                                                                   ▼                     ▼
                                                            ┌──────────────┐    ┌────────────┐
                                                            │   DynamoDB   │    │  S3 CSV    │
                                                            │   Results    │    │   Output   │
                                                            └──────────────┘    └────────────┘
```

### Key Improvements

1. **DynamoDB Storage**: Each row result stored separately, no payload accumulation
2. **Configuration-Driven Extraction**: Define extraction rules in YAML/JSON, not code
3. **Multiple Extraction Methods**: Support tool results, structured output, JMESPath, regex
4. **Schema Registry**: Agents can register output schemas for automatic mapping

### DynamoDB Schema

**Table**: `batch_processor_results`

```python
{
    "batch_id": "address-search#exec-123",  # Partition Key
    "row_id": "row_001",                    # Sort Key
    "status": "SUCCESS",
    "input_data": {...},                    # Original CSV row
    "output_data": {...},                   # Extracted results
    "execution_time_ms": 1250,
    "timestamp": "2025-01-18T10:00:00Z",
    "ttl": 1758171551                       # Auto-cleanup after 7 days
}
```

### Generic Output Configuration

Instead of hardcoded mappers per agent, use configuration:

```yaml
output_mappings:
  broadband-agent-rust:
    extraction_methods:
      # Try structured output first (if agent supports it)
      - method: "structured_output"
        tool_name: "print_output"
        field_mappings:
          exchange: "$.exchange"
          download_speed: "$.speeds.download"

      # Fall back to text extraction from tool results
      - method: "tool_result"
        tool_name: "browser_broadband"
        field_mappings:
          exchange: "$.content | parse('Exchange: (.+)')"
          download_speed: "$.content | parse('Download Speed: (.+)')"

      # Or use JMESPath for complex extraction
      - method: "jmespath"
        paths:
          exchange: "messages[-1].content[0].text"
          transform: "parse_text"

  web-search-agent:
    extraction_methods:
      - method: "results_array"
        field_mappings:
          title: "results[0].title"
          url: "results[0].url"
          snippet: "results[0].snippet"
```

### Extraction Methods

#### 1. Structured Output (Recommended for new agents)
Agents call a `print_output` tool with structured data:
```python
print_output({
    "exchange": "WHITEHALL",
    "download_speed": "50-330 Mbps"
})
```

#### 2. Tool Result Parsing
Extract from existing tool result messages using patterns:
```yaml
method: "tool_result"
tool_name: "browser_broadband"
field_mappings:
  exchange: "$.content | parse('Exchange: ([A-Z\\s]+)')"
```

#### 3. JMESPath Extraction
Flexible path-based extraction with transformations:
```yaml
method: "jmespath"
paths:
  exchange:
    path: "messages[-1].content[0].text"
    transform: "extract_exchange"
```

#### 4. Direct Mapping
For simple tool outputs:
```yaml
method: "direct"
field_mappings:
  category: "$.category"
  confidence: "$.confidence_score"
```

### Agent Output Schema Registry

Agents can register their output format for automatic compatibility:

```yaml
# schemas/broadband-agent-rust.yaml
agent: broadband-agent-rust
version: "1.0"
output_format: "messages"
fields:
  - name: exchange
    type: string
    extraction:
      - type: tool_result
        tool: browser_broadband
        pattern: "Exchange: ([A-Z\\s]+)"
      - type: structured
        path: "$.exchange"

  - name: download_speed
    type: string
    extraction:
      - type: tool_result
        pattern: "Download Speed: ([\\d.-]+\\s*Mbps)"
      - type: structured
        path: "$.speeds.download"
```

### State Machine Modifications

The INLINE Map would be updated to write results to DynamoDB:

```json
{
  "ProcessRows": {
    "Type": "Map",
    "ItemProcessor": {
      "States": {
        "TransformInput": { /* ... */ },
        "InvokeAgent": { /* ... */ },
        "ExtractOutput": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "Parameters": {
            "FunctionName": "${GenericMapperArn}",
            "Payload": {
              "execution_result.$": "$.execution_result",
              "agent_name.$": "$$.Execution.Input.target.name",
              "mapping_config.$": "$$.Execution.Input.output_mapping"
            }
          },
          "ResultPath": "$.extracted_output",
          "Next": "WriteResult"
        },
        "WriteResult": {
          "Type": "Task",
          "Resource": "arn:aws:states:::dynamodb:putItem",
          "Parameters": {
            "TableName": "batch_processor_results",
            "Item": {
              "batch_id": {"S.$": "$$.Execution.Name"},
              "row_id": {"S.$": "$._row_id"},
              "status": {"S": "SUCCESS"},
              "input_data": {"S.$": "States.JsonToString($)"},
              "output_data": {"S.$": "States.JsonToString($.extracted_output)"},
              "execution_time_ms": {"N.$": "$.execution_time"},
              "timestamp": {"S.$": "$$.State.EnteredTime"}
            }
          },
          "End": true
        }
      }
    }
  },
  "AggregateResults": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "${ResultAggregatorArn}",
      "Payload": {
        "batch_id.$": "$$.Execution.Name",
        "output_bucket.$": "$.output_bucket",
        "output_key.$": "States.Format('results/{}.csv', $$.Execution.Name)"
      }
    },
    "End": true
  }
}
```

### Size Comparison

**Current Implementation (Payload Passing)**:
- Full agent response: ~5-10 KB per row
- Filtered output: ~0.5-1 KB per row
- Maximum batch: ~250 rows (with filtering)

**DynamoDB Architecture**:
- Payload per row: ~0.1 KB (just status reference)
- Maximum batch: Unlimited
- Query cost: Minimal (single partition key query)

### Migration Path

1. **Phase 1**: Current implementation with filtered output (✅ Complete)
   - Handles most use cases up to ~250 rows
   - Simple, fast, no external dependencies

2. **Phase 2**: Add DynamoDB storage option (When needed)
   - Add flag to choose storage mode
   - Implement DynamoDB writer and aggregator
   - Keep backward compatibility

3. **Phase 3**: Generic mapper with configuration (Future)
   - Implement configuration-driven extraction
   - Support multiple extraction methods
   - Add schema registry

4. **Phase 4**: Structured output adoption (Long term)
   - Encourage agents to support `print_output` tool
   - Provide migration guide for existing agents
   - Achieve maximum efficiency

### Benefits of Scalable Architecture

1. **Unlimited Scale**: No Step Functions payload limitations
2. **Cost Effective**: Pay only for what you use with DynamoDB
3. **Debugging**: Query individual row results in DynamoDB
4. **Flexibility**: Add new agents without code changes
5. **Performance**: Parallel writes, efficient aggregation
6. **Reliability**: Built-in retry and error handling

### When to Use Each Approach

**Use Current Implementation When**:
- Batch size < 250 rows
- Need simple, fast processing
- Output data is not sensitive
- Don't need result persistence

**Use DynamoDB Architecture When**:
- Batch size > 250 rows
- Need result persistence/auditing
- Complex output transformations
- Multiple retry attempts needed
- Want to query results by various criteria

### Configuration Example (Future)

```yaml
# batch-processor-config.yaml
storage_mode: dynamodb  # or "inline" for current implementation

agents:
  broadband-agent-rust:
    extraction: schemas/broadband-agent.yaml

  property-search-agent:
    extraction: schemas/property-agent.yaml

defaults:
  ttl_days: 7
  max_concurrency: 10
  enable_compression: true
```

This scalable architecture provides a clear path forward while maintaining the simplicity of the current implementation for most use cases.