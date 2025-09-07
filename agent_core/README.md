# Bedrock Agent Core - Web Search Agent

This directory contains the implementation of a web search agent using the NEW Amazon Bedrock Agent Core service (not to be confused with the older Bedrock Agents service).

## Overview

Bedrock Agent Core is AWS's new container-based agent runtime service that provides:

- Docker-based agent deployment
- Built-in browser automation capabilities
- Async task management
- Multi-agent orchestration with Strands
- Direct integration with Nova Act for browser control

## Architecture

The web search agent uses:

- **Bedrock Agent Core Runtime**: Container-based agent hosting
- **Strands**: Multi-agent orchestration framework
- **Nova Act**: Browser automation tool
- **BedrockAgentCoreApp**: Python runtime for agents

## Files

- `web_search_agent.py` - Main agent implementation using Strands and Agent Core
- `requirements.txt` - Python dependencies
- `deploy_agentcore.py` - Deployment script for Agent Core
- `README.md` - This file

## Prerequisites

1. **AWS Account with Agent Core Access**
   - Bedrock Agent Core must be available in your region (us-west-2 recommended)
   - Appropriate IAM permissions for Agent Core, ECR, and Bedrock

2. **Python 3.10+**

   ```bash
   python3 --version
   ```

3. **Docker**
   - Required for building and pushing container images

   ```bash
   docker --version
   ```

4. **AWS CLI configured**

   ```bash
   aws configure
   ```

5. **Nova Act API Key** (if using browser automation)

   ```bash
   export NOVA_ACT_API_KEY="your-api-key"
   ```

## Installation

1. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Agent Core SDK**:

   ```bash
   python -c "import bedrock_agentcore; print(bedrock_agentcore.__version__)"
   ```

## Deployment

### Using Makefile (Recommended)

1. **Deploy the agent**:

   ```bash
   make agentcore-deploy
   ```

2. **Check deployment status**:

   ```bash
   make agentcore-status
   ```

3. **Test the agent**:

   ```bash
   make agentcore-test
   ```

4. **Invoke with a custom prompt**:

   ```bash
   make agentcore-invoke PROMPT="Search for Python programming books on Amazon"
   ```

5. **View logs**:

   ```bash
   make agentcore-logs
   ```

6. **Clean up resources**:

   ```bash
   make agentcore-clean
   ```

### Using Python Script Directly

1. **Deploy**:

   ```bash
   cd agent_core
   python deploy_agentcore.py --agent-name web-search-agent --region us-west-2
   ```

2. **Deploy and test**:

   ```bash
   python deploy_agentcore.py --agent-name web-search-agent --region us-west-2 --test
   ```

## Agent Capabilities

The web search agent can:

- Search web portals (default: Amazon.com)
- Extract structured data from web pages
- Handle authentication for protected portals
- Run searches asynchronously in the background
- Generate reports from search results

### Request Format

```json
{
  "prompt": "Search for wireless headphones under $100",
  "url": "https://www.amazon.com"  // Optional, defaults to Amazon
}
```

### Response Format

```json
{
  "status": "success",
  "response": "I found several wireless headphones under $100...",
  "task_info": {
    "active_tasks": 0,
    "completed_tasks": 1,
    "results_available": 1,
    "results": [...]
  }
}
```

## Multi-Agent Architecture

The agent uses Strands to coordinate three specialized agents:

1. **Fronting Agent** (`user_assistant`)
   - Handles user interaction
   - Routes requests to appropriate specialists
   - Manages conversation flow

2. **Search Agent** (`web_search_specialist`)
   - Performs web searches using Nova Act
   - Manages browser automation
   - Handles authentication

3. **Reporting Agent** (`report_generator`)
   - Processes search results
   - Generates structured reports
   - Summarizes findings

## Monitoring

### View Agent in AWS Console

1. Navigate to Amazon Bedrock in AWS Console
2. Go to "Agent Core" section
3. Find your deployed agent
4. View browser sessions under "Browser Tool" tab

### CloudWatch Logs

Logs are available in CloudWatch under:

```text
/aws/bedrock-agentcore/web-search-agent
```

## Troubleshooting

### Common Issues

1. **Module not found errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using Python 3.10+

2. **Docker not available**
   - Agent Core requires Docker for building container images
   - Ensure Docker daemon is running: `docker ps`

3. **Agent Core not available**
   - Service may not be available in all regions
   - Try us-west-2 or check AWS documentation for availability

4. **Authentication errors**
   - Verify AWS credentials: `aws sts get-caller-identity`
   - Check IAM permissions for Agent Core

5. **Nova Act errors**
   - Ensure NOVA_ACT_API_KEY is set
   - Check browser session limits in your account

### Debug Mode

Enable debug logging in the agent:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Local Testing

1. **Run agent locally**:

   ```bash
   cd agent_core
   python web_search_agent.py
   ```

2. **Test with sample payload**:

   ```python
   payload = {"prompt": "test query", "test": True}
   result = handler(payload, {})
   print(result)
   ```

### Modifying the Agent

1. Edit `web_search_agent.py`
2. Test locally
3. Redeploy: `make agentcore-deploy`

## Cost Considerations

- Agent Core charges per request and runtime duration
- Browser Tool sessions have time limits
- ECR storage for container images
- CloudWatch logs storage

## Security

- IAM roles are created automatically with minimal permissions
- Credentials are not stored in code
- Browser sessions are isolated and sandboxed
- All traffic is encrypted in transit

## Cleanup

To remove all resources:

```bash
make agentcore-clean
```

This will:

- Delete the Agent Core runtime
- Remove ECR repository
- Delete IAM role and policies
- Clean up local deployment files

## Differences from Legacy Bedrock Agents

| Feature | Bedrock Agents (Old) | Bedrock Agent Core (New) |
|---------|---------------------|------------------------|
| Deployment | API-based | Container-based |
| Runtime | Managed | Docker on Agent Core |
| Browser Tool | External Lambda | Built-in capability |
| Async Tasks | Not supported | Native support |
| Framework | Custom | Strands, LangChain, etc |
| Scaling | Limited | Auto-scaling |
| Local Testing | Difficult | Easy with Docker |

## Support

For issues or questions:

1. Check CloudWatch logs
2. Review deployment output
3. Verify prerequisites
4. Check AWS service health

## Next Steps

- Customize search behavior in `web_search_agent.py`
- Add more search providers beyond Amazon
- Implement caching for common searches
- Add user preference management
- Integrate with Step Functions for complex workflows
