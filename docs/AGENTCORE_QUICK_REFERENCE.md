# AgentCore Browser - Quick Reference

## 🎯 Simple Workflows

### Update Existing Agent Code

```bash
# 1. Edit agent code (now in step-functions-agent project)
cd /Users/guy/projects/step-functions-agent
vim lambda/tools/agentcore_browser/agents/simple_nova_agent.py

# 2. Rebuild and push (auto-updates runtimes)
make build-agentcore-containers ENV_NAME=prod
```

**That's it!** AgentCore runtimes automatically use the new image.

---

### Fresh Deployment (First Time)

```bash
# One command does everything
make deploy-agentcore-full ENV_NAME=prod
```

Or with CDK:

```bash
# 1. Create repos and build images
make create-agentcore-ecr-repos ENV_NAME=prod
make build-agentcore-containers ENV_NAME=prod

# 2. Deploy stacks
cdk deploy AgentCoreBrowserRuntimeStack-prod
cdk deploy AgentCoreBrowserToolStack-prod
```

---

## 📁 Key Files

| Purpose | File Location |
|---------|--------------|
| **Agent Code** | `lambda/tools/agentcore_browser/agents/simple_nova_agent.py` |
| **Agent Dockerfile** | `lambda/tools/agentcore_browser/agents/Dockerfile` |
| **Agent README** | `lambda/tools/agentcore_browser/agents/README.md` |
| **Define Agents** | `stacks/mcp/agentcore_browser_runtime_stack.py` |
| **Register Tools** | `stacks/tools/agentcore_browser_tool_stack.py` |
| **Tool Names** | `lambda/tools/agentcore_browser/tool-names.json` |
| **Deployment** | `Makefile` |
| **Architecture** | `docs/AGENTCORE_CHAIN_ARCHITECTURE.md` |

---

## 🚀 Create New Agent (Checklist)

- [ ] Add agent config to `agentcore_browser_runtime_stack.py`
- [ ] Export ARN in `app.py`
- [ ] Add tool spec to `agentcore_browser_tool_stack.py`
- [ ] Update `tool-names.json`
- [ ] Add ECR repo to Makefile `create-agentcore-ecr-repos`
- [ ] Add build step to Makefile `build-agentcore-containers`
- [ ] Create agent handler in `lambda/tools/agentcore_browser/agents/simple_nova_agent.py`
- [ ] Run: `make deploy-agentcore-full ENV_NAME=prod`

---

## 🔍 Deployed Resources

**Agents:**
- `cdk_broadband_checker_agent` → `browser_broadband` tool
- `cdk_shopping_agent` → `browser_shopping` tool
- `cdk_web_search_agent` → `browser_search` tool

**Stacks:**
- `AgentCoreBrowserRuntimeStack-prod` - ECR + AgentCore runtimes
- `AgentCoreBrowserToolStack-prod` - Lambda routing + DynamoDB registry

---

## 🐛 Common Issues

| Error | Solution |
|-------|----------|
| Image validation failed | Build/push image before deploying runtime |
| Runtime name pattern error | Use only letters, numbers, underscores (no hyphens!) |
| Agent using old code | Rebuild: `make build-agentcore-containers` |
| ECR repo not found | Run: `make create-agentcore-ecr-repos` |

---

## 📚 Full Documentation

- **Creating/Modifying Agents:** `docs/AGENTCORE_BROWSER_AGENT_GUIDE.md`
- **Migration Details:** `docs/AGENTCORE_CDK_MIGRATION.md`
- **Deployment Summary:** `docs/AGENTCORE_DEPLOYMENT_SUMMARY.md`
