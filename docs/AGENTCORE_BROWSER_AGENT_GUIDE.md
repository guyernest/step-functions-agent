# AgentCore Browser Agent - Quick Guide

## How to Create or Modify a Browser Agent

### Overview

Browser agents run on AWS Bedrock AgentCore and use Nova Act for browser automation. Each agent is a containerized Python application that handles specific browser tasks.

---

## 🚀 Quick Start: Modify Existing Agent (e.g., Broadband Checker)

### Step 1: Update Agent Code

The agent code is now integrated into the step-functions-agent project:

```bash
cd /Users/guy/projects/step-functions-agent/lambda/tools/agentcore_browser/agents
```

**Key files:**
- `simple_nova_agent.py` - Main agent handler (shared by all 3 agents)
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `README.md` - Agent documentation

**Modify the agent:**
```python
# Edit simple_nova_agent.py
def handler(event, context):
    # Your custom logic here
    # For login flow, add authentication handling

    if event.get("action") == "broadband_check_with_login":
        # 1. Navigate to login page
        # 2. Fill credentials
        # 3. Submit
        # 4. Navigate to broadband checker
        # 5. Fill address form
        # 6. Extract results
        pass

    return {"statusCode": 200, "body": json.dumps(result)}
```

### Step 2: Build and Push Updated Container

```bash
# From step-functions-agent project
make build-agentcore-containers ENV_NAME=prod
```

This will:
1. Build ARM64 Docker image from `lambda/tools/agentcore_browser/agents`
2. Push to all 3 ECR repositories
3. AgentCore runtimes automatically pick up the new image

**That's it!** The runtime will use the new image on the next invocation.

---

## 🆕 Create a NEW Browser Agent

### Step 1: Add Agent Configuration to CDK

Edit `stacks/mcp/agentcore_browser_runtime_stack.py`:

```python
agent_configs = [
    # ... existing agents ...
    {
        "id": "LoginBroadbandAgent",  # Unique construct ID
        "runtime_name": "cdk_login_broadband_agent",  # Must match [a-zA-Z][a-zA-Z0-9_]{0,47}
        "description": "Broadband checker with login authentication",
        "env_vars": {
            "AWS_REGION": self.region,
            "AGENT_TYPE": "login_broadband",  # Custom identifier
            "LOG_LEVEL": "INFO"
        }
    }
]
```

### Step 2: Update app.py to Export Agent ARN

Edit `app.py`:

```python
agent_arns = {
    "browser_broadband": agentcore_browser_runtime.agent_runtimes["cdk_broadband_checker_agent"].runtime_arn,
    "browser_shopping": agentcore_browser_runtime.agent_runtimes["cdk_shopping_agent"].runtime_arn,
    "browser_search": agentcore_browser_runtime.agent_runtimes["cdk_web_search_agent"].runtime_arn,
    "browser_login_broadband": agentcore_browser_runtime.agent_runtimes["cdk_login_broadband_agent"].runtime_arn,  # NEW
}
```

### Step 3: Update Tool Stack to Register New Tool

Edit `stacks/tools/agentcore_browser_tool_stack.py`:

Add to `tool_specs` array:

```python
{
    "tool_name": "browser_login_broadband",
    "description": "Check UK broadband with authenticated login",
    "input_schema": {
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "Login username"},
            "password": {"type": "string", "description": "Login password"},
            "postcode": {"type": "string", "description": "UK postcode"}
        },
        "required": ["username", "password", "postcode"]
    },
    "language": "python",
    "tags": ["browser", "automation", "broadband", "auth"],
    "author": "system",
    "human_approval_required": False,
    "lambda_arn": self.agentcore_browser_lambda.function_arn,
    "lambda_function_name": self.agentcore_browser_lambda.function_name
}
```

Update `tool-names.json`:

```bash
# Edit lambda/tools/agentcore_browser/tool-names.json
[
  "browser_broadband",
  "browser_shopping",
  "browser_search",
  "browser_login_broadband"
]
```

### Step 4: Create ECR Repository for New Agent

Edit `Makefile` - add to `create-agentcore-ecr-repos` target:

```makefile
for repo in bedrock-agentcore-cdk_broadband_checker_agent \
            bedrock-agentcore-cdk_shopping_agent \
            bedrock-agentcore-cdk_web_search_agent \
            bedrock-agentcore-cdk_login_broadband_agent; do  # NEW
```

### Step 5: Update Container Build Script

Edit `Makefile` - update `build-agentcore-containers` to handle new agent:

```makefile
# Add variable for new agent repo
LOGIN_BROADBAND_REPO=$$(aws cloudformation describe-stacks \
    --stack-name "AgentCoreBrowserRuntimeStack-$(ENV_NAME)" \
    --region "$(AWS_REGION)" \
    --query "Stacks[0].Outputs[?OutputKey=='LoginBroadbandRepositoryUri'].OutputValue" \
    --output text 2>/dev/null || echo "$$ACCOUNT_ID.dkr.ecr.$(AWS_REGION).amazonaws.com/bedrock-agentcore-cdk_login_broadband_agent") && \

# Add push command
docker tag $$BROADBAND_REPO:latest $$LOGIN_BROADBAND_REPO:latest && \
docker push $$LOGIN_BROADBAND_REPO:latest && \
```

### Step 6: Add Output for New Repository

Edit `stacks/mcp/agentcore_browser_runtime_stack.py` in `_create_outputs()`:

```python
CfnOutput(
    self,
    "LoginBroadbandRepositoryUri",
    value=self.agent_runtimes["cdk_login_broadband_agent"].container_uri.rsplit(':', 1)[0],
    description="ECR repository for login broadband agent container"
)
```

### Step 7: Create Agent-Specific Code

Add specialized handler in `lambda/tools/agentcore_browser/agents/simple_nova_agent.py`:

```python
def handle_login_broadband(body: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Handler specifically for login-based broadband checks"""

    # Extract input parameters
    input_data = body.get("input", {})
    postcode = input_data.get("postcode")

    # Extract credentials (injected by Lambda)
    username = credentials.get("username")
    password = credentials.get("password")

    # 1. Login flow using credentials
    # 2. Navigate to broadband checker
    # 3. Perform check
    # 4. Logout

    return {
        "success": True,
        "data": {...}
    }
```

Then route in main handler:
```python
if agent_type == "login_broadband":
    result = handle_login_broadband(body, credentials)
```

### Step 8: Deploy

```bash
# 1. Create ECR repo for new agent
make create-agentcore-ecr-repos ENV_NAME=prod

# 2. Build and push container
make build-agentcore-containers ENV_NAME=prod

# 3. Deploy runtime stack (creates new AgentCore runtime)
cdk deploy AgentCoreBrowserRuntimeStack-prod

# 4. Deploy tool stack (registers new tool in DynamoDB)
cdk deploy AgentCoreBrowserToolStack-prod
```

---

## 📋 Complete Deployment Workflow

### Fresh Deployment (All Agents)

```bash
make deploy-agentcore-full ENV_NAME=prod
```

Or step-by-step with CDK:

```bash
# 1. Create ECR repos
make create-agentcore-ecr-repos ENV_NAME=prod

# 2. Build and push images
make build-agentcore-containers ENV_NAME=prod

# 3. Deploy with CDK
cdk deploy AgentCoreBrowserRuntimeStack-prod
cdk deploy AgentCoreBrowserToolStack-prod
```

### Update Existing Agent Code

```bash
# Just rebuild and push - runtimes auto-update
make build-agentcore-containers ENV_NAME=prod
```

---

## 🎯 Agent Specialization Patterns

### Option 1: Shared Handler with Routing

**Current approach** - One handler routes based on `AGENT_TYPE`:

```python
# simple_nova_agent.py
agent_type = os.environ.get("AGENT_TYPE")

if agent_type == "broadband":
    return handle_broadband(event)
elif agent_type == "shopping":
    return handle_shopping(event)
elif agent_type == "search":
    return handle_search(event)
```

**Pros:** Simple, single codebase
**Cons:** All agents share same code, harder to customize

### Option 2: Separate Entry Points

**Recommended for specialized agents** - Each agent has its own handler function:

```bash
lambda/tools/agentcore_browser/agents/
├── simple_nova_agent.py  # Contains all handler functions
├── Dockerfile
└── requirements.txt
```

All handlers in one file with routing:

```python
# simple_nova_agent.py
def handle_broadband(body, credentials):
    # Broadband-specific logic
    pass

def handle_shopping(body, credentials):
    # Shopping-specific logic
    pass

def handle_search(body, credentials):
    # Search-specific logic
    pass

# Main handler routes based on AGENT_TYPE
agent_type = os.environ.get("AGENT_TYPE")
if agent_type == "broadband":
    result = handle_broadband(body, credentials)
elif agent_type == "shopping":
    result = handle_shopping(body, credentials)
# ... etc
```

**Pros:** Single codebase, easy to maintain, shared dependencies
**Cons:** All agents share same container (but different runtimes)

---

## 🔧 Key Files Reference

### CDK Infrastructure
- `stacks/mcp/agentcore_browser_runtime_stack.py` - Defines agents and runtimes
- `stacks/tools/agentcore_browser_tool_stack.py` - Registers tools in DynamoDB
- `stacks/shared/agentcore_runtime_construct.py` - Reusable runtime construct
- `app.py` - Wires runtime ARNs to tool stack

### Lambda Tool
- `lambda/tools/agentcore_browser/lambda_function.py` - Routes tool calls to agents
- `lambda/tools/agentcore_browser/agent_config.py` - Maps tool names to agent ARNs
- `lambda/tools/agentcore_browser/tool-names.json` - List of registered tools

### Agent Code
- `lambda/tools/agentcore_browser/agents/simple_nova_agent.py` - Main agent handler
- `lambda/tools/agentcore_browser/agents/Dockerfile` - Container definition
- `lambda/tools/agentcore_browser/agents/requirements.txt` - Python dependencies
- `lambda/tools/agentcore_browser/agents/README.md` - Agent documentation

### Deployment
- `Makefile` - Deployment commands
- `docs/AGENTCORE_CDK_MIGRATION.md` - Architecture documentation

---

## 🐛 Troubleshooting

### Agent not picking up new code
- **Issue:** Changed code but agent still uses old version
- **Solution:** Push new image, runtimes auto-update: `make build-agentcore-containers`

### Image validation failed
- **Issue:** `The specified image identifier does not exist`
- **Solution:** Build and push image BEFORE deploying runtime stack

### Runtime name validation error
- **Issue:** `failed to satisfy constraint: Member must satisfy regular expression pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}`
- **Solution:** Runtime names can only contain letters, numbers, and underscores (no hyphens!)

### ECR repository not found
- **Issue:** `The repository does not exist`
- **Solution:** Run `make create-agentcore-ecr-repos` first

---

## 📊 Current Setup

**Deployed Agents:**
1. `cdk_broadband_checker_agent` - UK broadband availability (no auth)
2. `cdk_shopping_agent` - E-commerce product search
3. `cdk_web_search_agent` - General web extraction

**Tool Names (as seen by Step Functions agents):**
- `browser_broadband`
- `browser_shopping`
- `browser_search`

**ECR Repositories:**
- `bedrock-agentcore-cdk_broadband_checker_agent`
- `bedrock-agentcore-cdk_shopping_agent`
- `bedrock-agentcore-cdk_web_search_agent`

---

## 💡 Next Steps

To create a broadband checker **with login**:

1. **Decide:** New agent or modify existing?
   - **New agent:** Follow "Create a NEW Browser Agent" section above
   - **Modify existing:** Just update `simple_nova_agent.py` and rebuild

2. **Recommended:** Create a new agent `cdk_login_broadband_agent`
   - Keeps original broadband agent for non-authenticated checks
   - Clean separation of concerns
   - Can have different input schema (requires username/password)

3. **Implementation:** Add login flow to agent handler
   ```python
   # 1. Navigate to BT Wholesale login page
   # 2. Fill username/password fields
   # 3. Submit login form
   # 4. Wait for redirect to authenticated area
   # 5. Navigate to broadband checker
   # 6. Perform normal broadband check
   # 7. Extract results
   # 8. Logout (cleanup)
   ```

4. **Deploy:** Follow Step 1-8 in "Create a NEW Browser Agent" section

Happy agent building! 🚀
