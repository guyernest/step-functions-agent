# Batch Processor Size Limits - Solutions

## The Problem
Step Functions has payload size limits:
- **Standard Workflows**: 256 KB max payload size
- **Express Workflows**: 256 KB max payload size
- **Distributed Map**: Can handle large datasets via S3

When processing batches, the full agent responses accumulate and can exceed these limits.

## Solution Options

### Option 1: Structured Output from Agent (Recommended for New Agents)
**Implementation**: Have agents use a `print_output` or `structured_output` tool

```python
# Agent would call:
print_output({
    "exchange": "WHITEHALL",
    "cabinet": "Cabinet 9",
    "download_speed": "74.0-80.0 Mbps",
    "upload_speed": "19.0-20.0 Mbps"
})
```

**Pros**:
- Minimal payload size (only essential data)
- Predictable output format
- Easy to parse
- No regex needed

**Cons**:
- Requires modifying agents
- Not backward compatible
- Extra tool call overhead

### Option 2: Output Filtering (Currently Implemented)
**Implementation**: Extract only essential fields in the output mapper

```python
# filtered_output_mapper.py extracts only what's needed
output_mapping = {
    "extract_fields": [
        {"name": "exchange", "pattern": r"Exchange:\s+([A-Z\s]+)"},
        {"name": "download_speed", "pattern": r"Download Speed:\s+([\d.-]+\s*Mbps)"}
    ]
}
```

**Pros**:
- Works with existing agents
- Configurable extraction patterns
- Reduces payload by 80-90%
- No agent modifications needed

**Cons**:
- Still has size limits (~1000-2000 rows max)
- Regex patterns can be fragile
- Loses full response data

### Option 3: External Storage (S3/DynamoDB)
**Implementation**: Store full results externally, pass only references

```python
# Store each result in S3
s3_key = f"results/{execution_id}/{row_id}.json"
s3_client.put_object(Bucket=bucket, Key=s3_key, Body=json.dumps(result))

# Pass only reference
output = {
    "result_location": f"s3://{bucket}/{s3_key}",
    "extracted_fields": {...}  # Minimal data
}
```

**Pros**:
- Unlimited batch size
- Preserves full responses
- Enables debugging/auditing
- Can process results async

**Cons**:
- Additional S3 costs
- More complex implementation
- Cleanup requirements
- Higher latency

### Option 4: Distributed Map with S3 (For Large Batches)
**Implementation**: Use Distributed Map's built-in S3 integration

```json
{
    "Type": "Map",
    "ItemProcessor": {
        "ProcessorConfig": {
            "Mode": "DISTRIBUTED",
            "ExecutionType": "EXPRESS"
        }
    },
    "ItemReader": {
        "Resource": "arn:aws:states:::s3:getObject",
        "ReaderConfig": {
            "InputType": "CSV",
            "CSVHeaderLocation": "FIRST_ROW"
        }
    },
    "ResultWriter": {
        "Resource": "arn:aws:states:::s3:putObject",
        "Parameters": {
            "Bucket": "results-bucket",
            "Prefix": "batch-results/"
        }
    }
}
```

**Pros**:
- Handles unlimited data
- Built-in S3 integration
- Parallel processing
- Automatic result writing

**Cons**:
- Express mode limitations
- More complex setup
- Higher costs
- No .sync support

## Recommended Approach

### For Small Batches (<100 rows):
Use **INLINE Map** with **Output Filtering**:
- Simple setup
- Synchronous execution
- Fast processing
- Current implementation

### For Medium Batches (100-1000 rows):
Use **Output Filtering** with **Compression**:
- Extract only essential fields
- Use brief field names
- Limit error messages
- Consider pagination

### For Large Batches (>1000 rows):
Use **External Storage** or **Distributed Map**:
- Store results in S3
- Process in chunks
- Use ResultWriter
- Consider async processing

## Implementation Guide

### 1. Configure Output Mapping
```json
{
  "output_mapping": {
    "extract_fields": [
      {
        "name": "field1",
        "pattern": "regex_pattern",
        "default": "N/A"
      }
    ],
    "structured_output_tool": "print_output",  // Optional
    "max_text_length": 1000  // Truncate long texts
  }
}
```

### 2. Use Filtered Output Mapper
Replace the standard output mapper with `filtered_output_mapper.py`:
- Reduces payload by 80-90%
- Supports both pattern extraction and structured output
- Configurable field extraction

### 3. Monitor Payload Size
Add CloudWatch metrics to track:
- Average payload size per row
- Maximum batch size processed
- Failed executions due to size limits

### 4. Implement Chunking (If Needed)
For very large batches, implement automatic chunking:
```python
def chunk_csv(input_file, chunk_size=100):
    """Split CSV into smaller chunks"""
    chunks = []
    current_chunk = []

    for row in csv_reader:
        current_chunk.append(row)
        if len(current_chunk) >= chunk_size:
            chunks.append(current_chunk)
            current_chunk = []

    return chunks
```

## Size Estimation

**Typical payload sizes**:
- Full agent response: 5-10 KB per row
- Filtered output: 0.5-1 KB per row
- Reference only: 0.1 KB per row

**Maximum batch sizes** (approximate):
- INLINE with full response: ~25 rows
- INLINE with filtering: ~250 rows
- External storage: Unlimited
- Distributed Map: Unlimited

## Migration Path

1. **Phase 1**: Implement output filtering (done)
2. **Phase 2**: Add structured output support to agents
3. **Phase 3**: Implement S3 storage for large batches
4. **Phase 4**: Add Distributed Map for massive batches

## Conclusion

The current implementation with output filtering handles most use cases. For larger batches, we can progressively add external storage or switch to Distributed Map as needed.