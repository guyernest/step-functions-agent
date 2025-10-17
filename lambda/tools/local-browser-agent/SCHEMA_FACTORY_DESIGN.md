# Schema-Based Factory Design for Browser Automation

## Overview

This document describes the schema-based factory pattern for creating consistent, testable, and maintainable browser automation extraction agents. The pattern ensures schema consistency across the entire data extraction pipeline, from CSV input to browser automation to structured output.

## Problem Statement

Currently, browser automation extraction flows suffer from:

1. **Schema Drift**: Multiple schemas maintained separately across the pipeline
2. **Inconsistency**: Field names and types differ between components
3. **Manual Maintenance**: Each new extraction agent requires manual coordination
4. **Limited Testability**: Difficult to validate components independently
5. **LLM Freedom**: Too much flexibility leads to errors and inconsistency

## Core Philosophy

**Single Source of Truth**: One canonical schema defines the entire extraction pipeline.

```
[Canonical Schema: extraction_task.json]
           ↓
     ┌─────┴─────┬─────────┬──────────┬─────────────┐
     ↓           ↓         ↓          ↓             ↓
[Tool Input] [Print Out] [act_with] [Batch Out] [CSV Cols]
  Schema      Schema      _schema    Mapping
```

**Declarative Over Imperative**: Pre-build and test scripts offline, let LLM only fill in parameters.

**MCP Philosophy Applied**: Treat browser automation like MCP servers - strict interfaces, verifiable behavior, real-time data.

## Architecture

### 1. Canonical Schema Format

A canonical schema defines everything needed for an extraction task:

```json
{
  "extraction_name": "broadband_availability_check",
  "version": "1.0.0",
  "description": "Check broadband availability for UK addresses using BT Wholesale",

  "input_schema": {
    "type": "object",
    "properties": {
      "address": {
        "type": "string",
        "description": "Full street address",
        "required": true
      },
      "postcode": {
        "type": "string",
        "pattern": "^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$",
        "description": "UK postcode",
        "required": true
      },
      "building_number": {
        "type": "string",
        "description": "Building number or name",
        "required": false
      }
    }
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "available": {
        "type": "boolean",
        "description": "Whether broadband service is available",
        "required": true
      },
      "service_type": {
        "type": "string",
        "enum": ["fibre", "copper", "fttc", "fttp"],
        "description": "Type of broadband service available"
      },
      "max_download_speed": {
        "type": "string",
        "description": "Maximum download speed (e.g., '80 Mbps')"
      },
      "max_upload_speed": {
        "type": "string",
        "description": "Maximum upload speed (e.g., '20 Mbps')"
      },
      "installation_cost": {
        "type": "string",
        "description": "Installation cost if available"
      },
      "availability_date": {
        "type": "string",
        "description": "Expected availability date if not currently available"
      }
    }
  },

  "browser_config": {
    "profile_name": "Bt_broadband",
    "starting_url": "https://my.btwholesale.com/",
    "timeout": 300,
    "requires_login": false,
    "clone_for_parallel": false
  },

  "metadata": {
    "author": "system",
    "created_at": "2025-10-17",
    "tags": ["broadband", "availability", "uk", "bt-wholesale"],
    "use_cases": ["batch-processing", "api-integration"]
  }
}
```

### 2. Generated Artifacts

From this canonical schema, the factory generates:

#### A. Agent CDK Stack
```
generated/broadband_availability_v1/
├── stack.py                          # CDK stack definition
├── agent_config.py                   # Agent configuration
└── tests/
    ├── test_agent.py                 # Unit tests
    └── test_integration.py           # Integration tests
```

#### B. Tool Specifications
```json
{
  "tool_name": "check_broadband_availability",
  "description": "Check broadband availability for UK addresses using BT Wholesale",
  "input_schema": {
    // Derived from canonical input_schema + browser_config
    "address": "string",
    "postcode": "string",
    "building_number": "string (optional)",
    "profile_name": "Bt_broadband (fixed)",
    "starting_url": "https://my.btwholesale.com/ (fixed)",
    "timeout": "300 (fixed)"
  }
}
```

#### C. Output Tool (print_output)
```json
{
  "tool_name": "print_output",
  "description": "Output structured broadband availability results",
  "input_schema": {
    // Exactly matches canonical output_schema
    "available": "boolean",
    "service_type": "string",
    "max_download_speed": "string",
    // ... etc
  }
}
```

#### D. Browser Script Template
```json
{
  "session": {
    "profile_name": "{{schema.browser_config.profile_name}}",
    "mode": "use_profile",
    "clone_for_parallel": "{{schema.browser_config.clone_for_parallel}}"
  },
  "steps": [
    {
      "type": "navigate",
      "url": "{{schema.browser_config.starting_url}}",
      "description": "Navigate to BT Wholesale portal"
    },
    {
      "type": "act",
      "goal": "Search for broadband availability at address: {{input.address}}, postcode: {{input.postcode}}",
      "description": "Perform availability search"
    },
    {
      "type": "act_with_schema",
      "goal": "Extract all broadband availability information from the results page",
      "schema": "{{schema.output_schema}}",
      "description": "Extract structured results"
    }
  ],
  "placeholders": {
    "input.address": "string - from input_schema.address",
    "input.postcode": "string - from input_schema.postcode",
    "input.building_number": "string - from input_schema.building_number (optional)"
  }
}
```

#### E. Batch Processor Mapping
```json
{
  "input_mapping": {
    "csv_columns_to_agent_input": {
      "Address": "address",
      "Postcode": "postcode",
      "Building": "building_number"
    }
  },
  "output_mapping": {
    "structured_output_fields": [
      "available",
      "service_type",
      "max_download_speed",
      "max_upload_speed",
      "installation_cost",
      "availability_date"
    ],
    "csv_column_mapping": {
      "available": "Broadband_Available",
      "service_type": "Service_Type",
      "max_download_speed": "Max_Download_Speed",
      "max_upload_speed": "Max_Upload_Speed",
      "installation_cost": "Installation_Cost",
      "availability_date": "Availability_Date"
    }
  }
}
```

#### F. Validation and Testing
```python
# generated/broadband_availability_v1/validator.py

from jsonschema import validate
from typing import Dict, Any

class BroadbandAvailabilityValidator:
    """Auto-generated validator for broadband_availability_v1"""

    def __init__(self, schema_path: str):
        self.schema = self._load_schema(schema_path)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate agent input against canonical schema"""
        validate(instance=input_data, schema=self.schema['input_schema'])
        return True

    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate agent output against canonical schema"""
        validate(instance=output_data, schema=self.schema['output_schema'])
        return True

    def validate_browser_script(self, script: Dict[str, Any]) -> bool:
        """Validate browser script has correct placeholders"""
        # Check session config matches browser_config
        # Check all input placeholders are defined
        # Check output schema matches
        pass

    def validate_batch_mapping(self, mapping: Dict[str, Any]) -> bool:
        """Validate batch processor mapping is complete"""
        # Check all input fields are mapped
        # Check all output fields are mapped
        pass
```

### 3. Schema Registry

Store canonical schemas with versioning:

```python
# DynamoDB Schema:
{
  "schema_id": "broadband_availability_v1",  # PK
  "version": "1.0.0",                         # SK
  "canonical_schema": {...},                  # Full schema JSON
  "agent_arn": "arn:aws:states:...",         # Generated agent
  "tool_name": "check_broadband_availability",
  "browser_script_s3": "s3://schemas/broadband_v1/script.json",
  "status": "active",                         # active, deprecated, testing
  "created_at": "2025-10-17T10:00:00Z",
  "created_by": "guy@example.com",
  "tags": ["broadband", "availability"],
  "dependencies": {
    "profile": "Bt_broadband",
    "requires_login": false
  }
}
```

### 4. Schema Generator CLI

Command-line tool to generate all artifacts:

```bash
# Create new extraction agent from schema
python schema_factory.py generate \
  --schema schemas/broadband_availability.json \
  --output-dir generated/broadband_availability_v1/ \
  --deploy

# Validate existing agent against schema
python schema_factory.py validate \
  --schema schemas/broadband_availability.json \
  --agent-arn arn:aws:states:...

# Update agent when schema changes
python schema_factory.py update \
  --schema schemas/broadband_availability_v2.json \
  --previous-version v1 \
  --migration-strategy recreate

# List all registered schemas
python schema_factory.py list

# Test schema locally before deployment
python schema_factory.py test \
  --schema schemas/broadband_availability.json \
  --test-data test_inputs.json
```

## Implementation Phases

### Phase 1: Schema Generator Tool (Week 1)

**Deliverables:**
- Canonical schema format specification
- Python CLI tool (`schema_factory.py`)
- Template engine for artifact generation
- Validation framework

**Files to Create:**
```
lambda/tools/local-browser-agent/
├── schema_factory/
│   ├── __init__.py
│   ├── cli.py                        # Main CLI entry point
│   ├── schema_validator.py           # Schema validation
│   ├── generator.py                  # Artifact generator
│   ├── templates/
│   │   ├── agent_stack.py.j2         # CDK stack template
│   │   ├── browser_script.json.j2    # Browser script template
│   │   ├── tool_spec.json.j2         # Tool specification template
│   │   ├── batch_mapping.json.j2     # Batch mapping template
│   │   └── validator.py.j2           # Validator template
│   └── utils/
│       ├── template_renderer.py
│       └── schema_loader.py
```

### Phase 2: Schema Validation Layer (Week 2)

**Deliverables:**
- Runtime validation at each boundary
- Error reporting and logging
- Schema version compatibility checks

**Integration Points:**
- Agent tool handler (validate input)
- Browser script executor (validate params + output)
- Batch processor (validate row mapping + agent output)

### Phase 3: Schema Registry (Week 3)

**Deliverables:**
- DynamoDB table for schema storage
- S3 bucket for browser scripts and artifacts
- API for schema CRUD operations
- Version management and migration tools

### Phase 4: Template Library (Week 4)

**Deliverables:**
- Common field type definitions
- Reusable extraction patterns
- Composition utilities
- Best practices documentation

## Usage Examples

### Example 1: Create New Extraction Agent

```bash
# 1. Define canonical schema
cat > schemas/property_valuation.json <<EOF
{
  "extraction_name": "property_valuation",
  "version": "1.0.0",
  "input_schema": {
    "properties": {
      "address": {"type": "string", "required": true},
      "postcode": {"type": "string", "required": true}
    }
  },
  "output_schema": {
    "properties": {
      "estimated_value": {"type": "number", "required": true},
      "value_range_low": {"type": "number"},
      "value_range_high": {"type": "number"},
      "last_sold_price": {"type": "number"},
      "last_sold_date": {"type": "string"}
    }
  },
  "browser_config": {
    "profile_name": "Zoopla",
    "starting_url": "https://www.zoopla.co.uk/",
    "timeout": 180
  }
}
EOF

# 2. Generate all artifacts
python schema_factory.py generate \
  --schema schemas/property_valuation.json \
  --output-dir generated/property_valuation_v1/

# 3. Test locally
python schema_factory.py test \
  --schema schemas/property_valuation.json \
  --test-data test_properties.json

# 4. Deploy to AWS
python schema_factory.py deploy \
  --schema schemas/property_valuation.json \
  --env prod
```

### Example 2: Validate Existing Agent

```bash
# Check if deployed agent matches schema
python schema_factory.py validate \
  --schema schemas/broadband_availability.json \
  --agent-arn arn:aws:states:eu-west-1:123456789012:stateMachine:broadband-checker-structured \
  --check-tools \
  --check-output-mapping

# Output:
# ✓ Input schema matches tool specification
# ✓ Output schema matches print_output tool
# ✗ Browser script missing field: building_number
# ✗ Batch mapping missing CSV column: availability_date
```

### Example 3: Update Schema (Version 2)

```bash
# Create new version with additional fields
cat > schemas/broadband_availability_v2.json <<EOF
{
  "extraction_name": "broadband_availability_check",
  "version": "2.0.0",
  "input_schema": {
    "properties": {
      "address": {"type": "string", "required": true},
      "postcode": {"type": "string", "required": true},
      "customer_type": {
        "type": "string",
        "enum": ["residential", "business"],
        "required": true
      }
    }
  },
  "output_schema": {
    "properties": {
      // ... existing fields ...
      "business_packages": {
        "type": "array",
        "items": {"type": "object"}
      }
    }
  }
}
EOF

# Generate migration plan
python schema_factory.py migrate \
  --from schemas/broadband_availability_v1.json \
  --to schemas/broadband_availability_v2.json \
  --strategy blue-green

# Deploy new version alongside v1
python schema_factory.py deploy \
  --schema schemas/broadband_availability_v2.json \
  --env prod \
  --keep-previous-version
```

## Benefits

### 1. Consistency by Design
- Single canonical schema eliminates drift
- All components guaranteed to match
- Type safety across boundaries

### 2. Rapid Development
- Generate new extraction agent in minutes
- No manual coordination needed
- Reuse patterns and templates

### 3. Testability
- Validate schema before deployment
- Unit test components independently
- Integration tests auto-generated

### 4. Maintainability
- Update schema, regenerate everything
- Version management built-in
- Clear migration paths

### 5. Observability
- Track schema versions
- Detect drift automatically
- Audit trail for changes

### 6. Documentation
- Schema serves as living documentation
- Self-documenting artifacts
- Clear interfaces

## Best Practices

### 1. Schema Design

**DO:**
- Keep schemas focused and specific
- Use descriptive field names
- Include validation rules (patterns, enums)
- Document each field
- Version schemas semantically

**DON'T:**
- Create overly complex schemas
- Use ambiguous field names
- Skip required/optional markers
- Forget to version

### 2. Browser Script Templates

**DO:**
- Pre-test scripts thoroughly
- Use minimal placeholders
- Add descriptions to steps
- Handle common errors
- Set appropriate timeouts

**DON'T:**
- Leave too much to LLM interpretation
- Use complex conditional logic
- Hardcode site-specific values that may change

### 3. Schema Evolution

**DO:**
- Use semantic versioning
- Provide migration paths
- Keep old versions temporarily
- Test backward compatibility

**DON'T:**
- Break existing agents
- Delete schemas in use
- Skip version testing

### 4. Validation

**DO:**
- Validate at every boundary
- Log validation errors clearly
- Fail fast on schema mismatches
- Include field-level error messages

**DON'T:**
- Silent failures
- Coerce types implicitly
- Skip validation in production

## Schema Library

Common reusable schema components:

### Address Fields (UK)
```json
{
  "address_line_1": {"type": "string", "required": true},
  "address_line_2": {"type": "string"},
  "city": {"type": "string"},
  "county": {"type": "string"},
  "postcode": {
    "type": "string",
    "pattern": "^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$"
  }
}
```

### Availability Check Pattern
```json
{
  "available": {"type": "boolean", "required": true},
  "service_type": {"type": "string"},
  "availability_date": {"type": "string"},
  "restrictions": {"type": "string"}
}
```

### Financial Information Pattern
```json
{
  "price": {"type": "number"},
  "currency": {"type": "string", "enum": ["GBP", "USD", "EUR"]},
  "payment_frequency": {"type": "string", "enum": ["one-time", "monthly", "annual"]}
}
```

### Contact Information Pattern
```json
{
  "phone": {"type": "string", "pattern": "^\\+?[0-9\\s-()]+$"},
  "email": {"type": "string", "format": "email"},
  "website": {"type": "string", "format": "uri"}
}
```

## Migration Strategy

When updating schemas:

### 1. Backward Compatible Changes (Patch/Minor)
- Add optional fields
- Add enum values
- Relax validation rules
- Add descriptions

**Strategy**: Deploy in-place, no migration needed

### 2. Breaking Changes (Major)
- Remove fields
- Change field types
- Make optional fields required
- Restrict enum values

**Strategy**: Blue-green deployment
1. Deploy v2 alongside v1
2. Migrate batch jobs to v2
3. Monitor for 1 week
4. Deprecate v1
5. Remove v1 after 1 month

## Error Handling

### Schema Validation Errors

```json
{
  "error_type": "SCHEMA_VALIDATION_ERROR",
  "schema_id": "broadband_availability_v1",
  "validation_errors": [
    {
      "field": "output.max_download_speed",
      "expected": "string",
      "actual": "number",
      "message": "Field type mismatch"
    }
  ],
  "context": {
    "agent_arn": "...",
    "execution_id": "...",
    "input": {...}
  }
}
```

### Missing Schema Errors

```json
{
  "error_type": "SCHEMA_NOT_FOUND",
  "schema_id": "unknown_extraction_v1",
  "message": "Canonical schema not found in registry",
  "available_schemas": [
    "broadband_availability_v1",
    "property_valuation_v1"
  ]
}
```

## Future Enhancements

### 1. Visual Schema Builder
Web UI to design schemas visually and generate JSON

### 2. Schema Marketplace
Share and reuse community schemas

### 3. AI-Assisted Schema Generation
LLM suggests schema based on website structure

### 4. Performance Optimization
Cache compiled templates and validators

### 5. Multi-Language Support
Generate artifacts for TypeScript, Python, Java

## Related Documentation

- [Session Management Guide](./SESSION_MANAGEMENT_GUIDE.md)
- [Build Guide](./BUILD_GUIDE.md)
- [Batch Processor Notifications](../../docs/BATCH_PROCESSOR_NOTIFICATIONS.md)
- [AgentCore Browser Guide](../../docs/AGENTCORE_BROWSER_AGENT_GUIDE.md)

## Conclusion

The schema-based factory pattern transforms browser automation from an error-prone, manual process into a repeatable, testable, and maintainable system. By treating schemas as the single source of truth and generating all artifacts from them, we ensure consistency across the entire extraction pipeline while dramatically reducing development time and maintenance burden.

This approach aligns with modern software engineering best practices:
- **Infrastructure as Code** (CDK stacks generated from schema)
- **Contract-First Development** (schema defines contracts)
- **Test-Driven Development** (tests generated from schema)
- **Documentation as Code** (schema is the documentation)

The result is a robust, scalable system for creating browser automation extraction agents that can be deployed, tested, and maintained with confidence.
