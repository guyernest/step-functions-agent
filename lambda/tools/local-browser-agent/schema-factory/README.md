# Schema Factory CLI

A Rust-based CLI tool for generating browser automation extraction agents from canonical schemas.

## Overview

Schema Factory implements the schema-based factory pattern for creating consistent, testable, and maintainable browser automation extraction agents. It ensures schema consistency across the entire data extraction pipeline, from CSV input to browser automation to structured output.

See [SCHEMA_FACTORY_DESIGN.md](../SCHEMA_FACTORY_DESIGN.md) for the complete design documentation.

## Installation

### Build from Source

```bash
cd lambda/tools/local-browser-agent/schema-factory
cargo build --release
```

The binary will be available at `target/release/schema-factory`.

### Add to PATH (Optional)

```bash
# macOS/Linux
export PATH="$PATH:$(pwd)/target/release"

# Or install globally
cargo install --path .
```

## Usage

### Generate Agent from Schema

```bash
schema-factory generate \
  --schema examples/broadband_availability.json \
  --output-dir generated/broadband_availability_v1
```

This generates:
- `stack.py` - CDK stack definition
- `browser_script_template.json` - Browser automation script
- `tool_spec.json` - Tool specification
- `output_tool_spec.json` - Output tool (print_output) spec
- `batch_mapping.json` - Batch processor mapping
- `validator.py` - Python validator
- `canonical_schema.json` - Copy of canonical schema
- `README.md` - Documentation

### Validate Schema

```bash
schema-factory validate \
  --schema examples/broadband_availability.json
```

### Validate Deployed Agent

```bash
schema-factory validate \
  --schema examples/broadband_availability.json \
  --agent-arn arn:aws:states:... \
  --check-tools \
  --check-output-mapping
```

### Generate and Deploy

```bash
schema-factory generate \
  --schema examples/broadband_availability.json \
  --output-dir generated/broadband_availability_v1 \
  --deploy \
  --env prod
```

### List Registered Schemas

```bash
schema-factory list --verbose
```

### Test Schema Locally

```bash
schema-factory test \
  --schema examples/broadband_availability.json \
  --test-data examples/test_input.json \
  --run-browser
```

### Migrate Schema Versions

```bash
schema-factory migrate \
  --from schemas/broadband_availability_v1.json \
  --to schemas/broadband_availability_v2.json \
  --strategy blue-green
```

## Canonical Schema Format

A canonical schema defines everything needed for an extraction task:

```json
{
  "extraction_name": "broadband_availability_check",
  "version": "1.0.0",
  "description": "Check broadband availability for UK addresses",

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
        "required": true
      }
    }
  },

  "output_schema": {
    "type": "object",
    "properties": {
      "available": {
        "type": "boolean",
        "required": true
      },
      "service_type": {
        "type": "string",
        "enum": ["fibre", "copper", "fttc", "fttp"]
      },
      "max_download_speed": {
        "type": "string"
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
    "tags": ["broadband", "availability", "uk"],
    "use_cases": ["batch-processing", "api-integration"]
  }
}
```

## Examples

See the `examples/` directory for:
- `broadband_availability.json` - Complete schema for BT broadband availability checking
- `property_valuation.json` - Property valuation extraction schema
- `test_input.json` - Example test data

## Development

### Run Tests

```bash
cargo test
```

### Run with Verbose Output

```bash
cargo run -- generate --schema examples/broadband_availability.json --output-dir /tmp/test
```

### Format Code

```bash
cargo fmt
```

### Lint

```bash
cargo clippy
```

## Architecture

The CLI is structured as:

```
src/
├── main.rs           # CLI entry point and command routing
├── schema.rs         # Canonical schema types and validation
├── generator.rs      # Artifact generation logic
├── validator.rs      # Schema validation logic
├── templates.rs      # Template rendering engine
└── commands/         # Command implementations
    ├── generate.rs
    ├── validate.rs
    ├── deploy.rs
    ├── list.rs
    ├── test.rs
    └── migrate.rs

templates/            # Handlebars templates
├── browser_script.json.hbs
├── tool_spec.json.hbs
├── output_tool_spec.json.hbs
├── batch_mapping.json.hbs
├── cdk_stack.py.hbs
└── validator.py.hbs
```

## Dependencies

- **clap** - Command-line parsing
- **serde/serde_json** - JSON serialization
- **handlebars** - Template rendering
- **tokio** - Async runtime
- **anyhow** - Error handling
- **colored** - Terminal colors

## Roadmap

- [x] Basic CLI structure
- [x] Canonical schema types
- [x] Schema validation
- [x] Template generation engine
- [x] Generate command
- [ ] Deploy command (CDK integration)
- [ ] List command (DynamoDB registry integration)
- [ ] Test command (local validation)
- [ ] Migrate command (version migration)
- [ ] Schema registry (DynamoDB)
- [ ] Visual schema builder (web UI)
- [ ] AI-assisted schema generation

## Contributing

This tool is part of the browser automation extraction agent system. See [SCHEMA_FACTORY_DESIGN.md](../SCHEMA_FACTORY_DESIGN.md) for the complete design philosophy and usage patterns.

## License

Internal tool for browser automation agent development.
