# Generic Batch Processor Architecture

## Design Principles
1. **Agent/Tool Agnostic**: Should work with any agent or tool without code changes
2. **Scalable**: Handle unlimited batch sizes using DynamoDB
3. **Configuration-Driven**: All mappings defined in configuration, not code
4. **Schema-Aware**: Agents can register their output schemas for automatic mapping
5. **Template-Driven**: Browser automation uses templates for consistent schema extraction

## Architecture Overview

```
CSV Input → Input Mapper → Agent/Tool → Output Mapper → Result Aggregator → CSV Output
```

### Current Implementation (In-Memory Processing)

The current batch processor uses Step Functions INLINE Map with structured output:

```
CSV (S3)
  ↓
ValidateInput (Lambda)
  ↓
LoadCSVData (Lambda - input_mapper)
  ↓
ProcessCSV (Map State - Max Concurrency: 10)
  ├─ TransformInput (Lambda - input_mapper)
  ├─ InvokeAgent (Step Functions - synchronous)
  └─ ExtractStructuredOutput (Lambda - output_mapper)
  ↓
AggregateResults (Lambda - result_aggregator)
  ↓
CSV Output (S3)
```

## Schema-Driven Flow for Browser Automation Agents

### Complete Schema Propagation Pipeline

For agents using browser automation with templates (e.g., `broadband-availability-bt-wholesale`):

```
1. Canonical Schema Definition
   Location: schemas/broadband_availability_bt_wholesale.json
   Contains: input_schema, output_schema, browser_config, metadata
   ↓
2. Schema Factory (Rust CLI)
   Tool: lambda/tools/local-browser-agent/schema-factory
   Generates:
   - CDK Stack (stacks/agents/{agent_name}_stack.py)
   - Browser Script Template
   - Tool Specifications
   - Batch Mapping Configuration
   ↓
3. Template Registry (DynamoDB)
   Table: TemplateRegistry-{env}
   Keys: template_id (partition), version (sort)
   Contains:
   - template: JSON with steps including act_with_schema
   - variables: Input parameter definitions
   - metadata: Profile, starting URL, tags
   ↓
4. Agent Registration (DynamoDB)
   Table: AgentRegistry-{env}
   Keys: agent_name (partition), version (sort)
   Contains:
   - structured_output.enabled: true
   - structured_output.schemas: {schema definitions}
   - structured_output.output_fields: [field list]
   - template_config: {template_id, version, rendering_engine}
   ↓
5. Batch Orchestrator Agent
   Agent: batch-orchestrator-agent
   Tools:
   - analyze_csv_structure
   - validate_agent_compatibility (checks structured_output.enabled)
   - generate_batch_config
   - execute_batch_processor
   - monitor_batch_execution
   - get_batch_results
   ↓
6. Batch Processor State Machine
   State Machine: batch-processor-{env}
   Uses JSONata for transformations

   Flow:
   a. ValidateInput
      - Validates CSV S3 URI
      - Checks agent has structured_output enabled

   b. LoadCSVData (input_mapper Lambda)
      - Reads CSV from S3
      - Returns rows as array

   c. ProcessCSV (Map State)

      c1. TransformInput (input_mapper Lambda)
          - Maps CSV columns to agent input fields
          - Creates prompt and data payload
          Input: {row: {...}, mapping_config: {...}, target: {...}}
          Output: {prompt: "...", data: {...}}

      c2. InvokeAgent (Step Functions StartSyncExecution)
          - Invokes agent state machine synchronously
          - Agent uses template_id to load template from registry
          - Template renderer (Mustache) fills variables
          - Local browser agent executes steps
          - act_with_schema step extracts structured data
          Output: {structured_output: {...}, messages: [...]}

      c3. ExtractStructuredOutput (output_mapper Lambda)
          - Extracts structured_output field from agent response
          - Maps to CSV column fields
          Input: {agent_output: {...}, output_mapping: {...}, original_row: {...}}
          Output: {original_row_fields..., extracted_fields..., _status, _timestamp}

   d. AggregateResults (result_aggregator Lambda)
      - Combines all processed rows
      - Writes CSV to S3
      - Returns statistics
```

### Schema Consistency Enforcement

The system enforces schema consistency at multiple layers:

1. **Canonical Schema** (Source of Truth)
   - Defines input and output structure
   - Validated by schema-factory

2. **Template Schema** (Browser Extraction)
   - `act_with_schema` step contains schema for browser data extraction
   - Must match canonical output_schema

3. **Agent Stack Schema** (Agent Definition)
   - `structured_output_schema` in CDK stack
   - Used by Unified LLM to validate output
   - Registered in AgentRegistry

4. **Output Mapper** (Batch Processing)
   - Reads `structured_output_fields` from configuration
   - Extracts only specified fields from agent response
   - Validates REQUIRED fields are present

### Key Files in Schema Flow

| File | Purpose | Schema Elements |
|------|---------|-----------------|
| `schemas/{extraction_name}.json` | Canonical schema definition | input_schema, output_schema |
| `templates/{extraction_name}_v{version}.json` | Template with act_with_schema | steps[].schema (embedded) |
| `stacks/agents/{agent_name}_stack.py` | CDK agent definition | structured_output_schema, output_fields |
| `lambda/tools/batch_processor/input_mapper.py` | CSV → Agent input | Validates structured_output.enabled |
| `lambda/tools/batch_processor/output_mapper.py` | Agent output → CSV | Extracts structured_output fields |

### Output Mapper Implementation Details

The `output_mapper.py` Lambda (`extract_structured_output` function) performs:

1. **Locate structured output** in agent response:
   ```python
   # Check multiple possible locations
   agent_output['structured_output']  # Direct
   agent_output['Output']['structured_output']  # Step Functions wrapped
   agent_output['content']['structured_output']  # Tool result format
   ```

2. **Extract specified fields**:
   ```python
   fields_to_extract = output_mapping['structured_output_fields']
   for field_name in fields_to_extract:
       if field_name in structured_data:
           result_row[field_name] = structured_data[field_name]
   ```

3. **Add metadata**:
   ```python
   result_row['_status'] = 'SUCCESS'
   result_row['_timestamp'] = datetime.utcnow().isoformat()
   ```

4. **Handle errors**:
   - Missing structured_output → Return error with _status: 'FAILED'
   - Missing fields → Return empty string for field
   - Complex types (dict, list) → JSON stringify for CSV

## DynamoDB Schema

### Table: `batch_processor_results`

**Keys:**
- **Partition Key**: `batch_id` (String) - Format: `{tool_name}#{execution_id}`
- **Sort Key**: `row_id` (String) - Format: `row_{number}`

**Attributes:**
```json
{
  "batch_id": "address-search-batch#exec-123",
  "row_id": "row_001",
  "status": "SUCCESS",
  "input_data": {
    "address": "10 Downing Street",
    "postcode": "SW1A 2AA"
  },
  "output_data": {
    "exchange": "WHITEHALL",
    "cabinet": "Direct Exchange",
    "download_speed": "50.0-330.0 Mbps",
    "upload_speed": "3.0-50.0 Mbps"
  },
  "execution_time_ms": 1250,
  "timestamp": "2025-01-18T10:00:00Z",
  "ttl": 1758171551  // 7 days retention
}
```

**Indexes:**
- **GSI1**: `timestamp` - For time-based queries
- **GSI2**: `status` - For error analysis

## Generic Output Mapper

### Configuration Schema
```yaml
output_mappings:
  broadband-agent-rust:
    type: "agent"
    extraction_methods:
      - method: "tool_result"
        tool_name: "browser_broadband"
        field_mappings:
          exchange: "$.content | parse('Exchange: (.+)')"
          cabinet: "$.content | parse('Cabinet: (.+)')"

      - method: "structured_output"
        tool_name: "print_output"
        field_mappings:
          exchange: "$.exchange"
          cabinet: "$.cabinet"

      - method: "jmespath"
        paths:
          exchange: "messages[-1].content[0].text"
          transform: "parse_text"

  web-search-agent:
    type: "agent"
    extraction_methods:
      - method: "results_array"
        field_mappings:
          title: "results[0].title"
          url: "results[0].url"
          snippet: "results[0].snippet"

  classification-tool:
    type: "tool"
    extraction_methods:
      - method: "direct"
        field_mappings:
          category: "$.category"
          confidence: "$.confidence_score"
```

## Generic Mapper Lambda

```python
# generic_output_mapper.py

import json
import re
import jmespath
from typing import Dict, Any, List, Optional
from decimal import Decimal

class GenericOutputMapper:
    """
    Generic mapper that uses configuration to extract fields
    from any agent or tool output
    """

    def __init__(self, mapping_config: Dict[str, Any]):
        self.config = mapping_config
        self.extraction_methods = self.config.get('extraction_methods', [])

    def extract(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try each extraction method until one succeeds
        """
        for method_config in self.extraction_methods:
            method = method_config.get('method')

            if method == 'tool_result':
                result = self.extract_from_tool_result(
                    execution_result,
                    method_config
                )
            elif method == 'structured_output':
                result = self.extract_structured_output(
                    execution_result,
                    method_config
                )
            elif method == 'jmespath':
                result = self.extract_with_jmespath(
                    execution_result,
                    method_config
                )
            elif method == 'results_array':
                result = self.extract_from_results(
                    execution_result,
                    method_config
                )
            elif method == 'direct':
                result = self.extract_direct(
                    execution_result,
                    method_config
                )
            else:
                continue

            if result:
                return result

        return {}

    def extract_from_tool_result(self, data: Dict, config: Dict) -> Dict[str, Any]:
        """Extract from agent tool_result messages"""
        tool_name = config.get('tool_name')
        field_mappings = config.get('field_mappings', {})

        # Find tool result in messages
        tool_content = self.find_tool_result(data, tool_name)
        if not tool_content:
            return {}

        # Apply field mappings
        result = {}
        for output_field, extraction in field_mappings.items():
            if '|' in extraction:
                # Handle parse expressions
                path, parse_expr = extraction.split('|', 1)
                value = jmespath.search(path.strip(), {'content': tool_content})
                if value and 'parse(' in parse_expr:
                    pattern = re.findall(r"parse\('(.+?)'\)", parse_expr)[0]
                    match = re.search(pattern, value)
                    if match:
                        result[output_field] = match.group(1)
            else:
                # Direct path
                result[output_field] = jmespath.search(extraction, {'content': tool_content})

        return result

    def find_tool_result(self, data: Dict, tool_name: Optional[str]) -> Optional[str]:
        """Find tool result content in agent messages"""
        messages = data.get('messages', [])

        for message in messages:
            if message.get('role') == 'user':
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if item.get('type') == 'tool_result':
                            if not tool_name or item.get('name') == tool_name:
                                return item.get('content', '')

        return None

    def extract_with_jmespath(self, data: Dict, config: Dict) -> Dict[str, Any]:
        """Use JMESPath for flexible extraction"""
        paths = config.get('paths', {})
        result = {}

        for field, path_config in paths.items():
            if isinstance(path_config, str):
                # Simple path
                result[field] = jmespath.search(path_config, data)
            elif isinstance(path_config, dict):
                # Path with transform
                path = path_config.get('path')
                transform = path_config.get('transform')
                value = jmespath.search(path, data)

                if value and transform:
                    result[field] = self.apply_transform(value, transform)
                else:
                    result[field] = value

        return result

    def apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to extracted value"""
        if transform == 'parse_text':
            # Extract structured data from text
            return self.parse_text_fields(str(value))
        elif transform == 'to_number':
            try:
                return Decimal(str(value))
            except:
                return None
        # Add more transforms as needed
        return value
```

## Output Writer Lambda

```python
# dynamo_output_writer.py

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('batch_processor_results')

def lambda_handler(event, context):
    """
    Write processed row result to DynamoDB

    Event:
    {
        "batch_id": "tool#execution",
        "row_id": "row_001",
        "input_data": {...},
        "output_data": {...},
        "status": "SUCCESS",
        "execution_time_ms": 1250
    }
    """

    # Prepare item
    item = {
        'batch_id': event['batch_id'],
        'row_id': event['row_id'],
        'status': event.get('status', 'UNKNOWN'),
        'input_data': event.get('input_data', {}),
        'output_data': event.get('output_data', {}),
        'execution_time_ms': event.get('execution_time_ms', 0),
        'timestamp': datetime.utcnow().isoformat(),
        'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())
    }

    # Write to DynamoDB
    table.put_item(Item=item)

    # Return minimal response to reduce payload
    return {
        'batch_id': item['batch_id'],
        'row_id': item['row_id'],
        'status': item['status']
    }
```

## Result Aggregator Lambda

```python
# result_aggregator.py

import json
import boto3
import csv
import io
from typing import List, Dict, Any

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table('batch_processor_results')

def lambda_handler(event, context):
    """
    Query all results for a batch and create CSV

    Event:
    {
        "batch_id": "tool#execution",
        "output_bucket": "results-bucket",
        "output_key": "results/output.csv"
    }
    """

    batch_id = event['batch_id']

    # Query all rows for this batch
    response = table.query(
        KeyConditionExpression='batch_id = :batch_id',
        ExpressionAttributeValues={
            ':batch_id': batch_id
        },
        ScanIndexForward=True  # Sort by row_id
    )

    items = response['Items']

    # Handle pagination if needed
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression='batch_id = :batch_id',
            ExpressionAttributeValues={
                ':batch_id': batch_id
            },
            ExclusiveStartKey=response['LastEvaluatedKey'],
            ScanIndexForward=True
        )
        items.extend(response['Items'])

    # Convert to CSV
    csv_content = create_csv(items)

    # Upload to S3
    s3.put_object(
        Bucket=event['output_bucket'],
        Key=event['output_key'],
        Body=csv_content.encode('utf-8'),
        ContentType='text/csv'
    )

    return {
        'status': 'SUCCESS',
        'row_count': len(items),
        'csv_location': f"s3://{event['output_bucket']}/{event['output_key']}"
    }

def create_csv(items: List[Dict[str, Any]]) -> str:
    """Convert DynamoDB items to CSV"""
    if not items:
        return ""

    # Flatten nested structures
    flattened = []
    for item in items:
        row = {}

        # Add input fields
        for key, value in item.get('input_data', {}).items():
            row[f'input_{key}'] = value

        # Add output fields
        for key, value in item.get('output_data', {}).items():
            row[f'output_{key}'] = value

        # Add metadata
        row['_status'] = item.get('status')
        row['_execution_time_ms'] = item.get('execution_time_ms')
        row['_timestamp'] = item.get('timestamp')

        flattened.append(row)

    # Create CSV
    output = io.StringIO()
    if flattened:
        fieldnames = sorted(set().union(*[d.keys() for d in flattened]))
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened)

    return output.getvalue()
```

## Agent Output Schema Registry

Agents can register their output schemas for automatic field detection:

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
        tool: browser_broadband
        pattern: "Download Speed: ([\\d.-]+\\s*Mbps)"
      - type: structured
        path: "$.speeds.download"
```

## Benefits of This Approach

1. **Scalability**: DynamoDB handles unlimited rows efficiently
2. **Flexibility**: Configuration-driven extraction works with any agent/tool
3. **Performance**: Parallel writes to DynamoDB, batch query for results
4. **Cost-Effective**: Pay per request, automatic cleanup with TTL
5. **Debugging**: All results stored and queryable
6. **Generic**: No code changes needed for new agents/tools

## Migration Path

1. **Phase 1**: Implement DynamoDB storage (keep existing mappers)
2. **Phase 2**: Add generic mapper with JMESPath
3. **Phase 3**: Create schema registry for agents
4. **Phase 4**: Optimize with structured output tools

## State Machine Changes

The INLINE Map state would be modified to:

```json
{
  "ProcessRows": {
    "Type": "Map",
    "ItemProcessor": {
      "States": {
        "TransformInput": { ... },
        "InvokeAgent": { ... },
        "WriteResult": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "Parameters": {
            "FunctionName": "${DynamoWriterArn}",
            "Payload": {
              "batch_id.$": "$$.Execution.Name",
              "row_id.$": "$._row_id",
              "input_data.$": "$",
              "output_data.$": "$.extracted_output",
              "status.$": "$.execution_status"
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
        "output_key.$": "$.output_key"
      }
    },
    "End": true
  }
}
```

This architecture provides a robust, scalable foundation for batch processing any agent or tool.