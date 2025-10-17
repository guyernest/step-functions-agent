# AgentCore Browser Tool - Migration to Simplified Deployment

## Summary

We've migrated from CDK-managed AgentCore runtimes to manual deployment using the AgentCore starter toolkit CLI. This change improves stability and simplifies operations.

## What Changed

### Before (CDK-Managed Runtimes)
```
❌ Problematic approach:
- AgentCore runtimes managed via CDK (AWS::BedrockAgentCore::Runtime)
- CloudFormation stuck states during updates
- Architecture mismatch issues (ARM64 vs AMD64)
- Difficult recovery from failed deployments
```

### After (Manual Runtime Deployment)
```
✅ Simplified approach:
- AgentCore runtimes deployed via bedrock-agentcore CLI
- CodeBuild managed by CDK (stable, works well)
- Lambda function managed by CDK (stable, works well)
- Runtime ARNs passed via Lambda environment variables
```

## Architecture Changes

```
┌─────────────────────────────────────────────┐
│ What We Kept in CDK (Stable)               │
├─────────────────────────────────────────────┤
│ ✅ CodeBuild project for building containers│
│ ✅ Lambda function for routing requests     │
│ ✅ Tool registration with Step Functions    │
│ ✅ Secrets management                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ What We Moved to Manual (More Stable)      │
├─────────────────────────────────────────────┤
│ 🔧 AgentCore Runtime deployment             │
│ 🔧 Runtime updates and lifecycle mgmt       │
│ 🔧 Runtime ARN management                   │
└─────────────────────────────────────────────┘
```

## Code Changes

### 1. app.py
- **Commented out** `AgentCoreBrowserRuntimeStack` instantiation
- Added explanation and migration guide
- Changed `agent_arns` to `None` (ARNs now set via environment variables)

### 2. Makefile
- **Added new targets:**
  - `deploy-agentcore-runtimes-manual` - Deploy runtimes using starter toolkit
  - `list-agentcore-runtimes` - List all deployed runtimes
  - `get-agentcore-runtime-arns` - Get runtime ARNs
  - `update-agentcore-runtimes-manual` - Update runtimes to latest image
  - `delete-agentcore-runtimes-manual` - Delete runtimes
  - `update-agentcore-lambda-arns` - Auto-discover ARNs and update Lambda
  - `deploy-agentcore-full-manual` - Complete workflow in one command

### 3. Documentation
- **Created:**
  - `docs/AGENTCORE_BROWSER_SIMPLIFIED_DEPLOYMENT.md` - Complete guide
  - `docs/AGENTCORE_BROWSER_QUICK_START.md` - Quick reference
  - `docs/AGENTCORE_BROWSER_MIGRATION_SUMMARY.md` - This file

## New Deployment Workflow

```bash
# One-time full deployment
make deploy-agentcore-full-manual ENV_NAME=prod AWS_REGION=us-west-2

# Or step-by-step:
# 1. Build containers
make build-agentcore-containers-codebuild ENV_NAME=prod AWS_REGION=us-west-2

# 2. Deploy runtimes
make deploy-agentcore-runtimes-manual ENV_NAME=prod AWS_REGION=us-west-2

# 3. Update Lambda ARNs
make update-agentcore-lambda-arns ENV_NAME=prod AWS_REGION=us-west-2
```

## Modifying Browser Instructions

```bash
# 1. Edit instructions
vim lambda/tools/agentcore_browser/agents/instructions/broadband/bt_checker.yaml

# 2. Rebuild containers
make build-agentcore-containers-codebuild ENV_NAME=prod AWS_REGION=us-west-2

# 3. Runtimes auto-update on next cold start (or force update)
make update-agentcore-runtimes-manual ENV_NAME=prod AWS_REGION=us-west-2
```

## Benefits of This Approach

| Aspect | Before (CDK) | After (Manual) |
|--------|--------------|----------------|
| **Stability** | ❌ CloudFormation stuck states | ✅ No CF issues |
| **Recovery** | ❌ Difficult to recover from failures | ✅ Easy deletion/recreation |
| **Architecture** | ❌ AMD64 vs ARM64 confusion | ✅ Clear ARM64 requirement |
| **Updates** | ❌ Full stack redeploy needed | ✅ Quick runtime updates |
| **Debugging** | ❌ Opaque CF errors | ✅ Clear CLI output |
| **Complexity** | ❌ High (CDK + CF + Runtime) | ✅ Low (just CLI) |

## What Stays the Same

- ✅ Container code (`simple_nova_agent.py`, Dockerfile)
- ✅ Nova Act integration and browser automation
- ✅ Lambda function invocation and routing
- ✅ Secrets management
- ✅ Tool registration and Step Functions integration

## Files to Keep vs Remove

### Keep (Still Used)
```
lambda/tools/agentcore_browser/
├── agents/
│   ├── instructions/           ✅ Browser automation YAML
│   ├── nova_act_agent/         ✅ Nova Act integration
│   ├── simple_nova_agent.py    ✅ Agent handler
│   ├── Dockerfile              ✅ Container definition
│   ├── requirements.txt        ✅ Dependencies
│   └── buildspec.yml           ✅ CodeBuild config
├── lambda_function.py          ✅ Lambda handler
└── requirements.in             ✅ Lambda dependencies

stacks/tools/
└── agentcore_browser_tool_stack.py  ✅ Lambda + tools (no runtime)
```

### Deprecated (Not Removed, But Not Used)
```
stacks/mcp/
└── agentcore_browser_runtime_stack.py  ⚠️ Kept for reference, not deployed
```

## Future Migration Path

When AWS CDK support for `AWS::BedrockAgentCore::Runtime` becomes more mature and stable:

1. **Test in dev environment** - Try deploying runtimes via CDK in a non-prod environment
2. **Verify no stuck states** - Ensure updates complete successfully
3. **Uncomment code in app.py** - Re-enable `AgentCoreBrowserRuntimeStack`
4. **Update Makefile** - Point to CDK-based deployment
5. **Migrate environments gradually** - Dev → Staging → Prod

The code is preserved and ready for easy migration back to CDK when the service matures.

## Troubleshooting Common Issues

### Issue: bedrock-agentcore command not found
```bash
pip install bedrock-agentcore
```

### Issue: Runtime ARN not found
```bash
# List all runtimes
bedrock-agentcore list-runtimes --region us-west-2

# Check specific runtime
bedrock-agentcore describe-runtime \
  --runtime-name cdk_broadband_checker_agent \
  --region us-west-2
```

### Issue: Lambda still uses old ARNs
```bash
# Auto-discover and update
make update-agentcore-lambda-arns ENV_NAME=prod AWS_REGION=us-west-2
```

### Issue: Container architecture mismatch
```bash
# Verify ARM64 in buildspec
grep "platform" lambda/tools/agentcore_browser/agents/buildspec.yml
# Should show: --platform linux/arm64
```

## Getting Help

- **Quick Start**: See `docs/AGENTCORE_BROWSER_QUICK_START.md`
- **Full Guide**: See `docs/AGENTCORE_BROWSER_SIMPLIFIED_DEPLOYMENT.md`
- **Issues**: Check CloudWatch logs or GitHub issues

## Conclusion

This migration simplifies AgentCore browser tool deployment by using the proven starter toolkit CLI for runtime management while keeping CDK for stable components. This provides a more reliable and maintainable solution until AWS CDK support matures.
