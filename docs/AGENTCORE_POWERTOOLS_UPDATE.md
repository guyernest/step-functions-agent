# AgentCore Browser Tool - AWS Lambda Powertools Integration

## Summary

Updated the AgentCore browser tool to use **AWS Lambda Powertools** for logging and tracing, matching the pattern used by other tools in the framework (MicrosoftGraphAPI, google-maps, execute-code, etc.).

## Changes Made

### 1. Updated Lambda Function Code

**File:** `lambda/tools/agentcore_browser/lambda_function.py`

**Before:**
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
```

**After:**
```python
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize AWS Lambda Powertools
logger = Logger(service="agentcore-browser")
tracer = Tracer()

@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Received tool invocation", extra={"event": event})
```

**Benefits:**
- ✅ **Structured logging** - JSON formatted logs
- ✅ **Correlation IDs** - Automatic request tracking
- ✅ **X-Ray tracing** - Performance insights
- ✅ **Consistent with other tools** - Same pattern across framework

### 2. Updated CDK Stack Configuration

**File:** `stacks/tools/agentcore_browser_tool_stack.py`

**Added Environment Variables:**
```python
lambda_env = {
    "AWS_ACCOUNT_ID": str(self.aws_account_id),
    "ENV_NAME": env_name,
    "ENVIRONMENT": env_name,  # For tool_secrets.py compatibility
    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{env_name}",
    "POWERTOOLS_SERVICE_NAME": "agentcore-browser",  # NEW
    "POWERTOOLS_LOG_LEVEL": "INFO"  # NEW
}
```

**Enabled X-Ray Tracing:**
```python
self.agentcore_browser_lambda = lambda_python.PythonFunction(
    self, "AgentCoreBrowserLambda",
    # ... other params ...
    tracing=lambda_.Tracing.ACTIVE,  # NEW
)
```

**Added X-Ray Permissions:**
```python
self.agentcore_browser_lambda.add_to_role_policy(
    iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "xray:PutTraceSegments",
            "xray:PutTelemetryRecords"
        ],
        resources=["*"]
    )
)
```

### 3. Tool Secrets Integration (Already Correct)

The `tool_secrets.py` file is already in place and matches the shared pattern used by other tools.

**File:** `lambda/tools/agentcore_browser/tool_secrets.py`

✅ Matches `lambda/shared/tool-secrets-helper/tool_secrets.py`
✅ Already used by MicrosoftGraphAPI and execute-code tools
✅ LRU caching for performance
✅ Supports both ENVIRONMENT and ENV_NAME for compatibility

## Pattern Comparison

### Other Tools (MicrosoftGraphAPI)
```python
from aws_lambda_powertools import Logger, Tracer
from tool_secrets import get_tool_secrets

logger = Logger(service="MicrosoftGraphAPI")
tracer = Tracer()

keys = get_tool_secrets('microsoft-graph')
```

### AgentCore Browser Tool (Now)
```python
from aws_lambda_powertools import Logger, Tracer
from tool_secrets import get_tool_secrets

logger = Logger(service="agentcore-browser")
tracer = Tracer()

credentials = get_tool_secrets('browser_broadband')
```

✅ **Identical pattern!**

## Requirements

**File:** `lambda/tools/agentcore_browser/requirements.txt`

Already includes:
```
aws-lambda-powertools==3.4.1
boto3==1.40.16
botocore==1.40.16
```

No changes needed to requirements.

## Environment Variables

### Lambda Environment
```python
{
  "AWS_ACCOUNT_ID": "672915487120",
  "ENV_NAME": "prod",
  "ENVIRONMENT": "prod",  # For tool_secrets.py
  "CONSOLIDATED_SECRET_NAME": "/ai-agent/tool-secrets/prod",
  "POWERTOOLS_SERVICE_NAME": "agentcore-browser",
  "POWERTOOLS_LOG_LEVEL": "INFO",
  "USE_DYNAMIC_AGENT_ARNS": "true",
  "AGENT_ARN_BROADBAND": "arn:aws:bedrock-agentcore:...",
  "AGENT_ARN_SHOPPING": "arn:aws:bedrock-agentcore:...",
  "AGENT_ARN_SEARCH": "arn:aws:bedrock-agentcore:..."
}
```

## Logging Improvements

### Before (Standard Python Logging)
```
[INFO] 2025-01-08T10:00:00.000Z Tool name: browser_broadband
[INFO] 2025-01-08T10:00:00.001Z Tool input: {"postcode": "SW1A 1AA"}
```

### After (AWS Lambda Powertools)
```json
{
  "level": "INFO",
  "location": "handler:180",
  "message": "Received tool invocation",
  "timestamp": "2025-01-08 10:00:00,000+0000",
  "service": "agentcore-browser",
  "cold_start": true,
  "function_name": "agentcore-browser-tool-prod",
  "function_memory_size": "256",
  "function_arn": "arn:aws:lambda:...",
  "function_request_id": "abc-123-def",
  "xray_trace_id": "1-abc-def",
  "event": {
    "name": "browser_broadband",
    "input": {"postcode": "SW1A 1AA"}
  }
}
```

**Benefits:**
- ✅ Structured JSON format
- ✅ Automatic metadata (request ID, function ARN, etc.)
- ✅ Easy filtering in CloudWatch Logs Insights
- ✅ X-Ray correlation
- ✅ Performance metrics

## X-Ray Tracing

With `@tracer.capture_lambda_handler` decorator:

- Automatic trace creation
- Sub-segment capture for AWS SDK calls
- Performance insights in X-Ray console
- Correlation with logs
- Error tracking and analysis

**Example X-Ray Trace:**
```
Lambda Function (250ms)
├─ Secrets Manager GetSecretValue (50ms)
├─ Bedrock AgentCore InvokeAgent (180ms)
└─ Response Processing (20ms)
```

## Deployment

### Deploy Updated Stack

```bash
cdk deploy AgentCoreBrowserToolStack-prod
```

**Changes Applied:**
- ✅ Powertools environment variables
- ✅ X-Ray tracing enabled
- ✅ X-Ray IAM permissions
- ✅ Lambda code with Powertools decorators

### Verify Deployment

```bash
# Check CloudWatch Logs
aws logs tail /aws/lambda/agentcore-browser-tool-prod --follow --format short

# Check X-Ray Traces
aws xray get-trace-summaries \
  --start-time $(date -u -d '5 minutes ago' +%s) \
  --end-time $(date -u +%s)
```

## Testing

### Test Lambda Invocation

```bash
aws lambda invoke \
  --function-name agentcore-browser-tool-prod \
  --payload '{"name":"browser_broadband","input":{"postcode":"SW1A 1AA"}}' \
  --log-type Tail \
  response.json

# View logs
base64 -d <<< $(jq -r '.LogResult' response.json)
```

**Expected Structured Log Output:**
```json
{
  "level": "INFO",
  "message": "Received tool invocation",
  "service": "agentcore-browser",
  "event": {
    "name": "browser_broadband",
    "input": {"postcode": "SW1A 1AA"}
  }
}
```

### Verify X-Ray Trace

1. Open AWS X-Ray Console
2. Find trace for the invocation
3. Verify sub-segments:
   - Secrets Manager call
   - Bedrock AgentCore call
   - Response processing

## CloudWatch Logs Insights Queries

With structured logging, you can now run powerful queries:

### Query 1: Find All Tool Invocations
```
fields @timestamp, message, event.name, event.input
| filter message = "Received tool invocation"
| sort @timestamp desc
```

### Query 2: Track Specific Tool
```
fields @timestamp, event.input.postcode, @duration
| filter event.name = "browser_broadband"
| stats count() by event.input.postcode
```

### Query 3: Error Analysis
```
fields @timestamp, message, error
| filter level = "ERROR"
| stats count() by error
```

## Consistency Across Tools

### Python Tools Using Powertools
- ✅ MicrosoftGraphAPI
- ✅ execute-code
- ✅ **agentcore_browser** (now!)

### Python Tools Using tool_secrets.py
- ✅ MicrosoftGraphAPI
- ✅ execute-code
- ✅ **agentcore_browser** (now!)

### TypeScript Tools
- ✅ google-maps (uses toolSecrets.ts)
- ✅ graphql-interface

**All tools now follow consistent patterns!**

## Benefits Summary

### 1. Better Observability
- ✅ Structured logs for easy parsing
- ✅ X-Ray traces for performance analysis
- ✅ Correlation between logs and traces
- ✅ CloudWatch Logs Insights queries

### 2. Easier Debugging
- ✅ Automatic request ID tracking
- ✅ Cold start detection
- ✅ Function metadata in every log
- ✅ Error context preservation

### 3. Performance Monitoring
- ✅ X-Ray service map
- ✅ Latency breakdown by service
- ✅ Identify bottlenecks
- ✅ Track trends over time

### 4. Consistency
- ✅ Same logging pattern across all Python tools
- ✅ Same tracing setup
- ✅ Same secret management
- ✅ Easier to maintain

## Migration Complete

✅ **AgentCore browser tool now uses AWS Lambda Powertools**
✅ **Structured logging enabled**
✅ **X-Ray tracing enabled**
✅ **Consistent with other tools**
✅ **No breaking changes**

The tool is production-ready with enterprise-grade observability!
