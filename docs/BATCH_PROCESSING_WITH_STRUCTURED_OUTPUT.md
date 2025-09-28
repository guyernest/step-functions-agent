# Batch Processing with Structured Output - Implementation Guide

## Overview

This guide explains how to build agents and tools that are compatible with the batch processor, focusing on the **required structured output pattern** that enables reliable CSV generation and data processing at scale.

## Core Principle: Structured Output is Mandatory

**All agents and tools used with the batch processor MUST implement structured output.**

This is not optional - it's a fundamental requirement that ensures:
- Predictable CSV column structure
- Direct field-to-column mapping
- Type safety and validation
- Consistent error handling
- Simplified implementation

## Architecture

```
┌─────────────┐     ┌────────────────┐     ┌─────────────────────┐     ┌──────────────┐
│   CSV Input │────▶│ Batch Processor│────▶│ Agent with         │────▶│ Structured   │
│     (S3)    │     │ (Step Functions)│     │ Structured Output  │     │ Output (JSON)│
└─────────────┘     └────────────────┘     └─────────────────────┘     └──────────────┘
                                                      │                          │
                                                      ▼                          ▼
                                            ┌─────────────────────┐     ┌──────────────┐
                                            │ return_structured   │     │  CSV Output  │
                                            │ _data tool         │     │    (S3)      │
                                            └─────────────────────┘     └──────────────┘
```

## Building a Batch-Compatible Agent

### Step 1: Define Your Output Schema

Create a clear JSON Schema for your agent's output:

```python
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "company_name": {
            "type": "string",
            "description": "Official company name"
        },
        "industry": {
            "type": "string",
            "description": "Primary industry classification"
        },
        "employee_count": {
            "type": "integer",
            "description": "Number of employees"
        },
        "revenue_estimate": {
            "type": "string",
            "description": "Annual revenue range"
        },
        "confidence_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence in the data accuracy"
        }
    },
    "required": ["company_name", "industry"],
    "additionalProperties": false
}
```

### Step 2: Implement the Structured Output Tool

Create a tool that validates and returns structured data:

```python
# Lambda function for the structured output tool
import json
from jsonschema import validate, ValidationError

def lambda_handler(event, context):
    """
    Tool: return_structured_data
    Returns validated structured output for batch processing
    """
    tool_input = event.get('input', {})

    try:
        # Validate against schema
        validate(instance=tool_input, schema=OUTPUT_SCHEMA)

        return {
            "type": "structured_output",
            "content": tool_input,
            "schema_version": "1.0",
            "validated": True
        }
    except ValidationError as e:
        return {
            "type": "error",
            "error_message": f"Validation failed: {str(e)}",
            "content": None
        }
```

### Step 3: Configure Your Agent's State Machine

Add the structured output tool to your agent's workflow:

```json
{
  "CollectData": {
    "Type": "Task",
    "Comment": "Gather data from various sources",
    "Next": "ReturnStructuredOutput"
  },

  "ReturnStructuredOutput": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "return_structured_data",
      "Payload": {
        "input": {
          "company_name.$": "$.extracted_data.company",
          "industry.$": "$.extracted_data.industry",
          "employee_count.$": "$.extracted_data.employees",
          "revenue_estimate.$": "$.extracted_data.revenue",
          "confidence_score.$": "$.analysis.confidence"
        }
      }
    },
    "ResultPath": "$.structured_output",
    "Next": "Success"
  },

  "Success": {
    "Type": "Succeed",
    "OutputPath": "$"
  }
}
```

### Step 4: Register Your Agent's Schema

Add schema information to your agent's metadata:

```python
# In your agent's CDK stack
agent_metadata = {
    "name": "company-enrichment-agent",
    "structured_output": {
        "enabled": True,
        "schema_version": "1.0",
        "tool_name": "return_structured_data",
        "output_fields": [
            "company_name",
            "industry",
            "employee_count",
            "revenue_estimate",
            "confidence_score"
        ]
    }
}
```

## Batch Processor Integration

### How the Batch Processor Uses Structured Output

1. **Invokes Agent**: Batch processor calls your agent for each CSV row
2. **Receives Structured Output**: Agent returns validated JSON structure
3. **Maps to Columns**: Each field in structured output becomes a CSV column
4. **Handles Errors**: Failed validations are tracked with error details

### Configuration Example

```json
{
  "csv_s3_uri": "s3://my-bucket/companies.csv",
  "target": {
    "type": "agent",
    "name": "company-enrichment-agent"
  },
  "input_mapping": {
    "column_mappings": {
      "company": "company_name",
      "website": "company_url"
    }
  },
  "output_mapping": {
    "structured_output_fields": [
      "company_name",
      "industry",
      "employee_count",
      "revenue_estimate",
      "confidence_score"
    ],
    "include_original": true,
    "add_metadata": true
  }
}
```

### Output CSV Structure

```csv
company,website,company_name,industry,employee_count,revenue_estimate,confidence_score,_status,_execution_time_ms
Acme Corp,acme.com,Acme Corporation,Manufacturing,5000,100M-500M,0.92,SUCCESS,1250
TechStart,techstart.io,TechStart Inc,Technology,50,1M-10M,0.88,SUCCESS,980
```

## Best Practices

### 1. Schema Design

- **Keep it flat**: Avoid deeply nested structures for CSV compatibility
- **Use consistent types**: Stick to string, number, boolean for CSV columns
- **Provide defaults**: Use sensible defaults for optional fields
- **Version your schema**: Include version info for backward compatibility

### 2. Error Handling

```python
def return_structured_data(data):
    try:
        # Validate and process
        validate(data, OUTPUT_SCHEMA)
        return {
            "type": "structured_output",
            "content": data,
            "success": true
        }
    except Exception as e:
        # Return structured error
        return {
            "type": "structured_output",
            "content": {
                "error": str(e),
                "partial_data": data.get("company_name", "Unknown")
            },
            "success": false
        }
```

### 3. Performance Optimization

- **Batch validation**: Validate schema once, not per row
- **Cache schemas**: Load schema once at Lambda cold start
- **Minimize output size**: Only include necessary fields
- **Use compression**: Enable S3 compression for large outputs

### 4. Testing

```python
# Test your structured output tool
def test_structured_output():
    test_data = {
        "company_name": "Test Corp",
        "industry": "Technology",
        "employee_count": 100
    }

    result = return_structured_data(test_data)
    assert result["type"] == "structured_output"
    assert result["content"]["company_name"] == "Test Corp"
    assert result["validated"] == True
```

## Common Patterns

### Pattern 1: Enrichment Agent

```python
# Agent that enriches company data
def process_company(input_data):
    company_name = input_data["company_name"]

    # Gather data from various sources
    industry = lookup_industry(company_name)
    employees = get_employee_count(company_name)
    revenue = estimate_revenue(company_name)

    # Return structured output
    return {
        "structured_output": {
            "company_name": company_name,
            "industry": industry,
            "employee_count": employees,
            "revenue_estimate": revenue,
            "data_source": "multiple",
            "timestamp": datetime.now().isoformat()
        }
    }
```

### Pattern 2: Classification Agent

```python
# Agent that classifies support tickets
def classify_ticket(input_data):
    ticket_text = input_data["description"]

    # Analyze ticket
    category = classify_text(ticket_text)
    priority = determine_priority(ticket_text)
    sentiment = analyze_sentiment(ticket_text)

    # Return structured output
    return {
        "structured_output": {
            "category": category,
            "priority": priority,
            "sentiment_score": sentiment,
            "requires_escalation": priority == "high",
            "auto_response_available": category in AUTO_RESPONSE_CATEGORIES
        }
    }
```

### Pattern 3: Validation Agent

```python
# Agent that validates and standardizes addresses
def validate_address(input_data):
    address = input_data["address"]

    # Validate and standardize
    validated = validate_with_service(address)

    # Return structured output
    return {
        "structured_output": {
            "original_address": address,
            "standardized_address": validated["formatted"],
            "is_valid": validated["valid"],
            "postal_code": validated["postal_code"],
            "country": validated["country"],
            "geocode_lat": validated["latitude"],
            "geocode_lng": validated["longitude"]
        }
    }
```

## Troubleshooting

### Common Issues and Solutions

1. **Schema Validation Failures**
   - Check that all required fields are present
   - Verify data types match schema
   - Use JSON Schema validators for testing

2. **Missing Structured Output**
   - Ensure agent includes `structured_output` field
   - Check that the structured output tool is called
   - Verify the tool returns correct format

3. **CSV Column Mismatch**
   - Confirm output_mapping matches schema fields
   - Check for typos in field names
   - Ensure consistent field naming

4. **Performance Issues**
   - Reduce structured output size
   - Optimize validation logic
   - Use appropriate concurrency settings

## Migration Guide

### Converting Existing Agents

If you have an existing agent without structured output:

1. **Identify Output Data**: List all data your agent produces
2. **Create Schema**: Define JSON Schema for the output
3. **Add Tool**: Implement `return_structured_data` tool
4. **Update Workflow**: Add tool invocation to state machine
5. **Test**: Validate with sample data
6. **Deploy**: Update agent registration with schema info

### Example Migration

**Before** (Unstructured):
```python
return {
    "message": f"Found company {name} in {industry} with {employees} employees"
}
```

**After** (Structured):
```python
return {
    "structured_output": {
        "company_name": name,
        "industry": industry,
        "employee_count": employees
    },
    "message": f"Found company {name} in {industry} with {employees} employees"
}
```

## Advanced Features

### Dynamic Schema Selection

Support multiple output schemas based on input:

```python
def get_schema_for_type(data_type):
    schemas = {
        "company": COMPANY_SCHEMA,
        "person": PERSON_SCHEMA,
        "product": PRODUCT_SCHEMA
    }
    return schemas.get(data_type, DEFAULT_SCHEMA)

def return_structured_data(data, data_type):
    schema = get_schema_for_type(data_type)
    validate(data, schema)
    return {
        "type": "structured_output",
        "content": data,
        "schema_type": data_type
    }
```

### Partial Success Handling

Return partial data when some fields fail:

```python
def return_structured_data_safe(data):
    result = {}
    errors = []

    for field, value in data.items():
        try:
            validate_field(field, value)
            result[field] = value
        except ValidationError as e:
            errors.append(f"{field}: {str(e)}")
            result[field] = None  # or default value

    return {
        "type": "structured_output",
        "content": result,
        "validation_errors": errors,
        "partial_success": len(errors) > 0
    }
```

## Future Enhancements

### Planned Features

1. **Schema Registry**: Centralized schema management
2. **Auto-mapping**: Automatic CSV-to-schema field mapping
3. **Schema Evolution**: Support for versioned schemas
4. **Validation Reports**: Detailed validation analytics
5. **Type Coercion**: Automatic type conversion

### Roadmap

- **Phase 1**: Current implementation with manual schema definition
- **Phase 2**: Schema registry with versioning
- **Phase 3**: Auto-discovery of agent schemas
- **Phase 4**: Advanced validation and transformation

## Support and Resources

### Documentation
- [Batch Processor README](../lambda/tools/batch_processor/README.md)
- [Structured Output Agent Example](../stacks/agents/broadband_checker_structured_v2_stack.py)
- [JSON Schema Specification](https://json-schema.org/)

### Examples
- Company enrichment agent with structured output
- Support ticket classifier with validation
- Address validator with geocoding

### Getting Help
1. Check agent logs for validation errors
2. Test schema with online validators
3. Use debug mode for detailed output
4. Contact platform team for assistance

## Conclusion

Structured output is not just a requirement - it's a design pattern that makes batch processing reliable, scalable, and maintainable. By following this guide, your agents will seamlessly integrate with the batch processor and provide consistent, validated data for CSV generation and beyond.