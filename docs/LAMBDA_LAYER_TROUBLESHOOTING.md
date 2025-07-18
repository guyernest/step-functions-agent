# Lambda Layer Troubleshooting Guide

This document captures the learnings from resolving Lambda layer compatibility issues in the Step Functions Agent project.

## Key Issues Encountered

### 1. AWS Lambda Powertools Compatibility Issue

**Error**: `Session.create_client() got an unexpected keyword argument 'aws_account_id'`

**Root Cause**: 
- AWS Lambda Powertools v3+ introduced a breaking change in how it initializes boto3 clients
- The `aws_account_id` parameter was added in newer versions of boto3/botocore
- Lambda runtime's built-in boto3/botocore versions (1.26.x) don't support this parameter

**Solutions**:
1. **Pin boto3/botocore versions** to 1.36.0 in ALL requirements files:
   ```python
   boto3==1.36.0
   botocore==1.36.0
   ```

2. **Use session-based client creation** in config.py:
   ```python
   session = boto3.Session(
       region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
   )
   client = session.client('secretsmanager')
   ```

3. **Include boto3/botocore in Lambda layer** to override the runtime versions

### 2. ARM64 Architecture Compatibility

**Error**: `No module named 'pydantic_core._pydantic_core'`

**Root Cause**:
- Binary wheels compiled for x86_64 don't work on ARM64 Lambda functions
- CDK's Python Lambda construct needs explicit platform targeting

**Solutions**:
1. **Use uv for dependency management** with platform targeting:
   ```bash
   uv pip compile --python-platform aarch64-unknown-linux-gnu requirements.in --output-file requirements.txt
   ```

2. **Configure Lambda functions for ARM64**:
   ```python
   architecture=_lambda.Architecture.ARM_64
   ```

3. **Downgrade problematic dependencies** if needed (e.g., anthropic 0.39.0 vs 0.57.1)

## Best Practices for Lambda Layers

### 1. Dependency Management

- Always use `uv` for compiling requirements with proper platform targeting
- Keep separate requirements.in files for:
  - Lambda layer (`lambda/call_llm/lambda_layer/python/requirements.in`)
  - Individual Lambda functions (`lambda/call_llm/functions/*/requirements.in`)
- Pin critical versions (boto3, botocore) to avoid runtime conflicts

### 2. Debugging Lambda Issues

Add comprehensive logging at module level:
```python
import sys
print(f"DEBUG: Lambda startup - Python path: {sys.path[:3]}...")

try:
    import boto3
    print(f"DEBUG: Module level - boto3 version: {boto3.__version__}")
except Exception as e:
    print(f"DEBUG: Module level - boto3 import error: {e}")
```

### 3. CDK Best Practices

- Update layer construct ID to force rebuilds when needed
- Clean CDK cache when dependencies change:
  ```bash
  rm -rf cdk.out/
  ```
- Use RemovalPolicy.DESTROY for log groups in development

### 4. Secret Management

Load API keys from .env file in CDK stack:
```python
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

secret_value = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "placeholder"),
    # ...
}
```

## Deployment Commands

```bash
# Activate virtual environment
source cpython-3.12.3-macos-aarch64-none/bin/activate

# Compile requirements with ARM64 platform
uv pip compile --python-platform aarch64-unknown-linux-gnu requirements.in --output-file requirements.txt

# Deploy with CDK
cdk deploy SharedLLMStack-prod --app "python refactored_app.py" --profile CGI-PoC

# Test Lambda function
aws lambda invoke --function-name shared-claude-llm-prod \
  --cli-binary-format raw-in-base64-out \
  --payload file://test_event.json \
  --profile CGI-PoC response.json
```

## Summary

The key to resolving Lambda layer issues is understanding the interplay between:
1. Lambda runtime environment (built-in libraries)
2. Lambda layer dependencies
3. Architecture compatibility (ARM64 vs x86_64)
4. CDK build and deployment process

Always test thoroughly after dependency updates and use version pinning for critical libraries.