# AgentCore Chain Architecture

## Overview

This document defines the clean configuration and permission flow for the complete browser automation chain in the step-functions-agent framework.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: CSV Batch Processing Agent (Step Functions)           │
│ - Reads CSV from S3                                             │
│ - Iterates rows using Map state                                 │
│ - Aggregates results into output CSV                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: Row Processing Agent (Step Functions)                 │
│ - Receives single row data                                      │
│ - Calls Lambda tool with structured input                       │
│ - Returns structured output                                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: AgentCore Browser Lambda Tool                         │
│ - Validates input against tool schema                           │
│ - Retrieves secrets from Secrets Manager                        │
│ - Invokes AgentCore runtime with enriched input                 │
│ - Returns structured response                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: AgentCore Runtime                                      │
│ - Executes containerized browser agent                          │
│ - Uses Nova Act model for browser automation                    │
│ - Returns extraction results                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Browser Tool (Nova Act)                               │
│ - Performs web navigation and interaction                       │
│ - Extracts structured data from websites                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration Flow

### Layer 1: Batch Agent Configuration

**Input Configuration:**
```json
{
  "input_csv_path": "s3://bucket/input.csv",
  "output_csv_path": "s3://bucket/output.csv",
  "row_processing_agent_arn": "arn:aws:states:region:account:stateMachine:RowProcessingAgent",
  "tool_name": "browser_broadband",
  "extraction_fields": ["speed", "availability", "provider"]
}
```

**Permissions Required:**
- `s3:GetObject` on input CSV bucket
- `s3:PutObject` on output CSV bucket
- `states:StartExecution` on Row Processing Agent state machine
- `states:DescribeExecution` for monitoring

### Layer 2: Row Processing Agent Configuration

**Input Configuration:**
```json
{
  "tool_name": "browser_broadband",
  "tool_input": {
    "postcode": "SW1A 1AA",
    "address_line1": "10 Downing Street"
  },
  "extraction_fields": ["speed", "availability", "provider"]
}
```

**Environment Variables:**
- `TOOL_REGISTRY_TABLE`: DynamoDB table for tool discovery
- `AWS_REGION`: Region for Lambda invocation

**Permissions Required:**
- `dynamodb:Query` on tool registry table
- `lambda:InvokeFunction` on AgentCore browser Lambda
- `logs:CreateLogStream`, `logs:PutLogEvents`

### Layer 3: Lambda Tool Configuration

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "postcode": {"type": "string"},
    "address_line1": {"type": "string"}
  },
  "required": ["postcode"]
}
```

**Environment Variables:**
```python
{
    "AWS_ACCOUNT_ID": "672915487120",
    "ENV_NAME": "prod",
    "AGENT_ARN_BROADBAND": "arn:aws:bedrock-agentcore:...",
    "AGENT_ARN_SHOPPING": "arn:aws:bedrock-agentcore:...",
    "AGENT_ARN_SEARCH": "arn:aws:bedrock-agentcore:...",
    "USE_DYNAMIC_AGENT_ARNS": "true",
    "CONSOLIDATED_SECRET_NAME": "/ai-agent/tool-secrets/prod"  # Consolidated tool secrets
}
```

**Consolidated Tool Secrets Structure:**
```json
{
  "browser_broadband": {
    "username": "user@example.com",
    "password": "encrypted_password",
    "api_key": "optional_api_key"
  },
  "browser_shopping": {
    "api_key": "shopping_api_key"
  },
  "browser_search": {
    "api_key": "search_api_key"
  }
}
```

**Note:** Uses the same consolidated secret pattern as other tools (google-maps, MicrosoftGraphAPI).
**Manageable via UI:** Tool Secrets Management interface.

**Permissions Required:**
- `bedrock-agentcore:InvokeAgent` on agent runtime ARN
- `secretsmanager:GetSecretValue` on `/ai-agent/tool-secrets/{env_name}*`
- `logs:CreateLogStream`, `logs:PutLogEvents`

### Layer 4: AgentCore Runtime Configuration

**Environment Variables (set by CDK):**
```python
{
    "AWS_REGION": "us-west-2",
    "AGENT_TYPE": "broadband",  # or "shopping", "search"
    "LOG_LEVEL": "INFO"
}
```

**Input Payload (from Lambda):**
```json
{
  "tool_name": "browser_broadband",
  "input": {
    "postcode": "SW1A 1AA",
    "address_line1": "10 Downing Street",
    "credentials": {
      "username": "user@example.com",
      "password": "decrypted_password"
    }
  }
}
```

**Permissions Required (IAM Role):**
- `bedrock:InvokeModel` for Nova Act
- `bedrock:InvokeModelWithResponseStream`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

### Layer 5: Browser Tool (Nova Act)

**No direct configuration** - invoked by AgentCore runtime through Bedrock service

---

## Secrets Management Strategy

### Option 1: Lambda-Level Secrets (RECOMMENDED)

**Approach:**
- Lambda tool retrieves secrets from **consolidated tool secrets**
- Uses standard tool secrets pattern: `/ai-agent/tool-secrets/{env_name}`
- Injects credentials into AgentCore invocation payload
- AgentCore runtime receives credentials as part of input

**Advantages:**
- Single point of secrets retrieval
- **Consistent with other tools** (google-maps, MicrosoftGraphAPI, etc.)
- **Manageable via UI** - Tool Secrets Management
- Lambda has fine-grained IAM permissions
- Easy to audit and rotate secrets
- No changes needed to AgentCore runtime code

**Implementation:**
```python
# In lambda/tools/agentcore_browser/lambda_function.py
from tool_secrets import get_tool_secrets

def get_tool_credentials(tool_name: str) -> Optional[dict]:
    """Retrieve credentials from consolidated tool secrets"""
    try:
        # Use the consolidated tool secrets helper
        tool_secrets = get_tool_secrets(tool_name)

        if tool_secrets:
            logger.info(f"Retrieved credentials for {tool_name}")
            return tool_secrets
        else:
            logger.info(f"No credentials for {tool_name}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving credentials: {e}")
        return None

def invoke_agentcore_agent(tool_name: str, tool_input: dict) -> dict:
    # Get credentials from consolidated secret
    credentials = get_tool_credentials(tool_name)

    # Build invocation payload
    payload = {
        "tool_name": tool_name,
        "input": tool_input
    }

    # Inject credentials if available
    if credentials:
        payload["input"]["credentials"] = credentials

    # Invoke AgentCore
    response = bedrock_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        inputText=json.dumps(payload)
    )
    return response
```

### Option 2: AgentCore-Level Secrets

**Approach:**
- AgentCore runtime retrieves secrets directly
- Lambda passes secret name/identifier
- AgentCore runtime IAM role has Secrets Manager permissions

**Advantages:**
- Secrets never pass through Lambda
- More secure for highly sensitive credentials

**Disadvantages:**
- More complex IAM setup
- Harder to audit
- Requires changes to agent code

**NOT RECOMMENDED** for this use case due to added complexity.

---

## IAM Permission Matrix

| Layer | Principal | Permissions | Resource |
|-------|-----------|-------------|----------|
| Batch Agent | State Machine Role | `s3:GetObject` | Input CSV bucket |
| Batch Agent | State Machine Role | `s3:PutObject` | Output CSV bucket |
| Batch Agent | State Machine Role | `states:StartExecution` | Row Processing Agent |
| Row Agent | State Machine Role | `dynamodb:Query` | Tool Registry Table |
| Row Agent | State Machine Role | `lambda:InvokeFunction` | AgentCore Browser Lambda |
| Lambda Tool | Lambda Execution Role | `bedrock-agentcore:InvokeAgent` | AgentCore Runtime ARNs |
| Lambda Tool | Lambda Execution Role | `secretsmanager:GetSecretValue` | `/agentcore/browser/*` |
| Lambda Tool | Lambda Execution Role | `logs:*` | CloudWatch Logs |
| AgentCore Runtime | Runtime Execution Role | `bedrock:InvokeModel*` | Nova Act Model |
| AgentCore Runtime | Runtime Execution Role | `logs:*` | CloudWatch Logs |
| AgentCore Runtime | Runtime Execution Role | `ecr:*` | Container Image |

---

## Configuration Wiring in CDK

### Step 1: Define Secrets in Secrets Manager

```python
# In stacks/tools/agentcore_browser_tool_stack.py

from aws_cdk import aws_secretsmanager as secretsmanager

class AgentCoreBrowserToolStack(Stack):
    def __init__(self, ...):
        # Create secret for broadband agent (optional - can be created manually)
        self.broadband_secret = secretsmanager.Secret(
            self, "BroadbandCredentials",
            secret_name=f"/agentcore/browser/browser_broadband/credentials-{env_name}",
            description="Credentials for broadband checker agent",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": ""}),
                generate_string_key="password"
            )
        )
```

### Step 2: Grant Lambda Permissions

```python
# Grant Secrets Manager read permissions
self.agentcore_browser_lambda.add_to_role_policy(
    iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["secretsmanager:GetSecretValue"],
        resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/agentcore/browser/*"]
    )
)
```

### Step 3: Update Lambda Environment

```python
lambda_env = {
    "AWS_ACCOUNT_ID": str(self.aws_account_id),
    "ENV_NAME": env_name,
    "USE_DYNAMIC_AGENT_ARNS": "true",
    "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{env_name}"
}
```

### Step 4: Wire State Machine to Lambda

```python
# In state machine definition
{
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
        "FunctionName": "${AgentCoreBrowserLambdaArn}",
        "Payload": {
            "tool_name": "browser_broadband",
            "tool_input.$": "$.row_data"
        }
    }
}
```

---

## Error Handling Strategy

### Lambda Tool Layer

```python
def lambda_handler(event, context):
    try:
        # Validate input
        tool_name = event.get("tool_name")
        tool_input = event.get("tool_input")

        if not tool_name or not tool_input:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields: tool_name or tool_input"
                })
            }

        # Get credentials (optional)
        credentials = get_tool_credentials(tool_name)

        # Invoke agent
        result = invoke_agentcore_agent(tool_name, tool_input, credentials)

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except ClientError as e:
        logger.error(f"AWS service error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "AWS service error",
                "details": str(e)
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal error",
                "details": str(e)
            })
        }
```

### State Machine Retry Policy

```json
{
  "Type": "Task",
  "Resource": "lambda:invoke",
  "Retry": [
    {
      "ErrorEquals": ["States.TaskFailed"],
      "IntervalSeconds": 2,
      "MaxAttempts": 3,
      "BackoffRate": 2
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "ResultPath": "$.error",
      "Next": "HandleError"
    }
  ]
}
```

---

## Deployment Order

1. **Configure Tool Secrets** (via UI or AWS CLI):

   **Option A: Via Tool Secrets Management UI (Recommended)**
   - Navigate to Tool Secrets Management in the web UI
   - Add credentials for `browser_broadband`, `browser_shopping`, or `browser_search`
   - Secrets are automatically stored in the consolidated secret

   **Option B: Via AWS CLI (for automation)**
   ```bash
   # Get existing consolidated secret
   EXISTING_SECRET=$(aws secretsmanager get-secret-value \
     --secret-id /ai-agent/tool-secrets/prod \
     --query SecretString --output text)

   # Add browser tool credentials
   echo "$EXISTING_SECRET" | jq '. + {
     "browser_broadband": {
       "username": "user@example.com",
       "password": "password123"
     }
   }' > /tmp/updated-secret.json

   # Update consolidated secret
   aws secretsmanager update-secret \
     --secret-id /ai-agent/tool-secrets/prod \
     --secret-string file:///tmp/updated-secret.json
   ```

2. **Create ECR Repositories**:
   ```bash
   make create-agentcore-ecr-repos ENV_NAME=prod
   ```

3. **Build and Push Container Images**:
   ```bash
   make build-agentcore-containers ENV_NAME=prod
   ```

4. **Deploy Runtime Stack** (AgentCore runtimes):
   ```bash
   cdk deploy AgentCoreBrowserRuntimeStack-prod
   ```

5. **Deploy Tool Stack** (Lambda + Secrets permissions):
   ```bash
   cdk deploy AgentCoreBrowserToolStack-prod
   ```

6. **Deploy State Machines** (if managed by CDK):
   ```bash
   cdk deploy BatchProcessingStack-prod
   cdk deploy RowProcessingStack-prod
   ```

---

## Testing Strategy

### Unit Tests

1. **Lambda Tool Tests**:
   - Mock Secrets Manager responses
   - Mock AgentCore invocations
   - Test credential injection logic

2. **AgentCore Runtime Tests**:
   - Test with and without credentials
   - Validate browser automation flows

### Integration Tests

1. **End-to-End Test**:
   ```json
   {
     "test_name": "broadband_check_e2e",
     "input_csv": "s3://test-bucket/test_addresses.csv",
     "expected_output_fields": ["speed", "availability", "provider"],
     "verify_secrets_used": true
   }
   ```

2. **Secrets Rotation Test**:
   - Update secret in Secrets Manager
   - Verify Lambda picks up new credentials on next invocation
   - No code changes or redeployment required

---

## Security Best Practices

1. **Secrets Management**:
   - Use Secrets Manager automatic rotation where possible
   - Never log credentials
   - Use IAM policies to restrict secret access to specific Lambda functions

2. **Least Privilege IAM**:
   - Each layer has only the permissions it needs
   - Use resource-based policies where possible
   - Regularly audit IAM roles

3. **Encryption**:
   - Secrets Manager encrypts at rest with KMS
   - Use HTTPS for all AWS service calls
   - Consider encrypting sensitive data in S3

4. **Monitoring**:
   - CloudWatch Logs for all layers
   - CloudWatch Alarms for error rates
   - X-Ray tracing for performance analysis

---

## Migration Path

### Current State (External nova-act)
- Agent code: `/Users/guy/projects/nova-act/agent_core/simple_nova_agent.py`
- Build process: External Docker build
- Deployment: Manual ECR push

### Target State (Integrated)
- Agent code: `/Users/guy/projects/step-functions-agent/lambda/tools/agentcore_browser/agents/`
- Build process: CDK Asset bundling or Makefile
- Deployment: Automated via CDK

### Migration Steps (Next Phase)
1. Copy agent code into step-functions-agent project
2. Update Makefile to build from local directory
3. Create separate agent handlers (broadband_agent.py, shopping_agent.py, etc.)
4. Update CDK to use local build context
5. Remove dependency on nova-act project

---

## Summary

**Key Design Decisions:**
1. **Secrets at Lambda Layer** - Single point of retrieval, simpler IAM
2. **Dynamic Agent ARNs** - CDK-managed, passed via environment variables
3. **Standardized Secret Naming** - `/agentcore/browser/{tool_name}/credentials`
4. **Clean Separation of Concerns** - Each layer has specific responsibilities
5. **Error Handling at Every Layer** - Graceful degradation and retry logic

**Benefits:**
- Easy to add new browser agents
- Simple credential rotation
- Clear audit trail
- Minimal code changes for configuration updates
- Testable at each layer
