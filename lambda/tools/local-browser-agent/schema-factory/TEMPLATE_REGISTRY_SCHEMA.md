# TemplateRegistry DynamoDB Table Schema

## Overview
The TemplateRegistry table stores browser automation script templates that can be rendered with variables at runtime. Templates are pre-built, optimized scripts that the LLM fills in with minimal parameters, ensuring consistency and reducing errors.

## Table Structure

**Table Name**: `TemplateRegistry-{env}`
**Partition Key**: `template_id` (String) - Unique identifier for the template
**Sort Key**: `version` (String) - Semantic version (e.g., "1.0.0")
**Billing**: Pay-per-request

## Item Schema

```json
{
  "template_id": "broadband_availability_bt_wholesale",
  "version": "1.0.0",
  "extraction_name": "broadband_availability_bt_wholesale",
  "status": "active",
  "template": {
    "session": {
      "profile_name": "Bt_broadband",
      "mode": "use_profile"
    },
    "steps": [
      {
        "type": "navigate",
        "url": "https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome"
      },
      {
        "type": "act",
        "goal": "Fill in the address form with Building Number: {{building_number}}, Street: {{street}}, PostCode: {{postcode}}. Then click Submit.",
        "description": "Search by address"
      },
      {
        "type": "act_with_schema",
        "goal": "Extract broadband availability data from the results page",
        "schema": {
          "type": "object",
          "properties": {
            "exchange": {"type": "string"},
            "downstream_mbps": {"type": "number"}
          }
        }
      }
    ]
  },
  "variables": {
    "building_number": {
      "type": "string",
      "description": "Building number (e.g., '1', '23A')",
      "required": true
    },
    "street": {
      "type": "string",
      "description": "Street or road name",
      "required": true
    },
    "postcode": {
      "type": "string",
      "description": "UK postcode in format like SW1A 1AA",
      "required": true,
      "pattern": "^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$"
    },
    "full_address": {
      "type": "string",
      "description": "Full address for disambiguation",
      "required": false
    }
  },
  "metadata": {
    "author": "schema-factory",
    "canonical_schema_id": "broadband_availability_bt_wholesale",
    "canonical_schema_version": "1.0.0",
    "starting_url": "https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome",
    "profile_name": "Bt_broadband",
    "tags": ["broadband", "availability", "uk", "bt-wholesale"]
  },
  "created_at": "2025-10-17T17:00:00Z",
  "updated_at": "2025-10-17T17:00:00Z"
}
```

## Field Definitions

### Primary Keys
- **template_id** (String, required): Unique identifier, typically matches extraction_name
- **version** (String, required): Semantic version following semver (MAJOR.MINOR.PATCH)

### Core Fields
- **extraction_name** (String, required): Name of the extraction task (for GSI)
- **status** (String, required): `active`, `deprecated`, `draft`, `archived`
- **template** (Object, required): Browser automation script template with placeholders
  - Supports Mustache/Handlebars syntax: `{{variable_name}}`
  - Fixed structure from canonical schema
  - Placeholders only for user-provided values
- **variables** (Object, required): Schema defining template variables
  - Each variable includes: type, description, required, optional pattern/enum
  - Maps to canonical schema input_schema

### Metadata
- **metadata** (Object, optional): Additional information
  - `author`: Who created the template
  - `canonical_schema_id`: Reference to canonical schema
  - `canonical_schema_version`: Version of canonical schema
  - `starting_url`: Initial URL for the automation
  - `profile_name`: Browser profile to use
  - `tags`: Array of searchable tags
- **created_at** (String, auto): ISO 8601 timestamp
- **updated_at** (String, auto): ISO 8601 timestamp

## Global Secondary Indexes

### TemplatesByExtractionName
- **Partition Key**: `extraction_name`
- **Sort Key**: `created_at`
- **Use Case**: Find all templates for a specific extraction task

### TemplatesByStatus
- **Partition Key**: `status`
- **Sort Key**: `updated_at`
- **Use Case**: List all active/deprecated/draft templates

## Template Rendering Flow

```
LLM provides variables:
{
  "building_number": "23",
  "street": "High Street",
  "postcode": "SW1A 1AA"
}

State Machine:
1. Load template from TemplateRegistry
2. Render template with variables (server-side)
3. Send fully-rendered script to browser_remote Activity

Local Browser Agent receives:
{
  "session": {"profile_name": "Bt_broadband", "mode": "use_profile"},
  "steps": [
    {"type": "navigate", "url": "https://..."},
    {"type": "act", "goal": "Fill in Building Number: 23, Street: High Street, PostCode: SW1A 1AA..."}
  ]
}
```

## Access Patterns

### 1. Get Latest Template Version
```python
response = dynamodb.query(
    TableName='TemplateRegistry-prod',
    KeyConditionExpression='template_id = :id',
    ExpressionAttributeValues={':id': {'S': 'broadband_availability_bt_wholesale'}},
    ScanIndexForward=False,  # Descending order
    Limit=1
)
```

### 2. Get Specific Version
```python
response = dynamodb.get_item(
    TableName='TemplateRegistry-prod',
    Key={
        'template_id': {'S': 'broadband_availability_bt_wholesale'},
        'version': {'S': '1.0.0'}
    }
)
```

### 3. List All Active Templates
```python
response = dynamodb.query(
    TableName='TemplateRegistry-prod',
    IndexName='TemplatesByStatus',
    KeyConditionExpression='status = :status',
    ExpressionAttributeValues={':status': {'S': 'active'}}
)
```

## Version Management

- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

Example:
- `1.0.0` → Initial release
- `1.0.1` → Fix typo in template
- `1.1.0` → Add new optional variable
- `2.0.0` → Change required variables (breaking)

## Best Practices

1. **Immutability**: Never modify existing versions, create new versions instead
2. **Testing**: Test templates thoroughly before marking as `active`
3. **Deprecation**: Mark old versions as `deprecated`, don't delete
4. **Documentation**: Use clear variable descriptions
5. **Validation**: Include pattern/enum constraints where applicable
6. **Tagging**: Use consistent tags for discovery
