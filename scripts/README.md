# Scripts

Utility scripts for the Step Functions AI Agent Framework.

## Setup Scripts

### `setup_environment.sh`
Sets up the local development environment including:
- Python virtual environment
- CDK dependencies
- AWS configuration validation

Usage:
```bash
./scripts/setup_environment.sh
```

## Utility Scripts

### `utils/register_research_tools.py`
Manually registers research tools in the Tool Registry DynamoDB table.

This script is useful when:
- Tools were deployed but not automatically registered
- Testing tool registration logic
- Backfilling tool registry after infrastructure changes

Usage:
```bash
python scripts/utils/register_research_tools.py --env prod
```

## Example Scripts

### `examples/activity_worker.py`
Example implementation of a Step Functions activity worker for human-in-the-loop workflows.

This demonstrates:
- Polling for activity tasks
- Processing approval requests
- Sending task success/failure

Usage:
```bash
python scripts/examples/activity_worker.py --activity-arn <arn>
```

See [Activity Testing Guide](../docs/ACTIVITY_TESTING_GUIDE.md) for more details.

## CDK Helper Scripts

For CDK deployment helpers, see the main project README.

Common commands:
```bash
# Deploy all infrastructure
cdk deploy --all

# Deploy specific stack
cdk deploy SharedInfrastructureStack-prod

# Synthesize CloudFormation templates
cdk synth
```

## Testing Helpers

For testing scripts, see the [tests/](../tests/) directory.

## Contributing

When adding new scripts:

1. **Place in appropriate subdirectory**:
   - `utils/` - Utility scripts for operations
   - `examples/` - Example implementations
   - Root - Setup and common scripts

2. **Document**:
   - Add docstrings to Python scripts
   - Add comments to shell scripts
   - Update this README

3. **Make executable** (for shell scripts):
   ```bash
   chmod +x scripts/new_script.sh
   ```

4. **Use consistent style**:
   - Python: Follow PEP 8, use argparse for CLI
   - Shell: Use bash, include error handling
