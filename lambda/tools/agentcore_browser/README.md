# Agent Core Browser Tool

## Overview
This Lambda function provides browser automation capabilities using AWS Bedrock Agent Core with the Nova Act browser automation tool. It enables web searches, data extraction, and portal interactions through the Strands framework.

## Architecture
- **Service**: AWS Bedrock Agent Core (container-based runtime)
- **Framework**: Strands multi-agent orchestration
- **Browser**: Nova Act automation tool
- **Timeout**: 300 seconds (5 minutes) for long-running browser tasks

## Configuration

### Agent Runtime ARN
The Agent Core runtime ARN is configured in the stack:
```python
agent_runtime_arn = "arn:aws:bedrock-agentcore:us-west-2:672915487120:runtime/shopping_agent-aw6O6r7uk5"
```

### Environment Variables
- `AGENT_RUNTIME_ARN`: The Agent Core runtime ARN
- `ENV_NAME`: Environment name (prod/dev)

## Input Schema
```json
{
  "name": "agentcore_browser_search",
  "input": {
    "query": "string - Search query or task description",
    "url": "string (optional) - Target URL, defaults to https://www.amazon.com",
    "action": "string (optional) - Action type: search/extract/authenticate",
    "test_mode": "boolean (optional) - Use test mode, defaults to true"
  }
}
```

## Response Format
```json
{
  "success": true,
  "result": {
    "status": "COMPLETED",
    "responseText": "Search results or extracted data",
    "error": null
  },
  "executionTime": 15000,
  "metadata": {
    "sessionId": "agentcore-session-xxx",
    "agentRuntimeArn": "arn:aws:bedrock-agentcore:..."
  }
}
```

## Error Handling
The function handles several error conditions:
- Invalid input format
- Session ID validation (must be 33+ characters)
- Agent Core invocation failures
- Streaming response parsing errors
- Timeouts (Lambda has 300s timeout)

## Testing

### Direct Lambda Invocation
```bash
aws lambda invoke \
  --function-name agentcore-browser-tool-prod \
  --payload '{"name":"agentcore_browser_search","input":{"query":"find laptops under $1000"}}' \
  response.json
```

### Via Step Functions
The tool is integrated with Step Functions agents through the tool registry.

### UI Testing Limitations
⚠️ **Note**: The UI has a 30-second timeout due to AWS AppSync limitations. For longer searches:
1. Test directly via AWS Console or CLI
2. Use Step Functions for production workloads
3. Consider implementing async pattern for UI testing

## Common Use Cases

### Product Search
```json
{
  "query": "find gaming laptops with RTX 4060",
  "action": "search"
}
```

### Price Extraction
```json
{
  "query": "get price and availability for iPhone 15 Pro",
  "action": "extract"
}
```

### Custom Portal Search
```json
{
  "query": "search for enterprise software licenses",
  "url": "https://portal.example.com",
  "action": "search"
}
```

## Deployment

### CDK Stack
The tool is deployed via `AgentCoreBrowserToolStack`:
- Lambda function with Python 3.11 runtime
- 300-second timeout for long-running searches
- 1024 MB memory allocation
- Automatic DynamoDB tool registry registration

### Tool Registration
The tool self-registers in DynamoDB with:
- Tool name: `agentcore_browser_search`
- Tags: `["browser", "automation", "search", "agent-core", "nova-act"]`
- Human approval: Not required

## Monitoring
- CloudWatch Logs: `/aws/lambda/agentcore-browser-tool-{env}`
- Metrics: Lambda invocation metrics
- Tracing: X-Ray tracing enabled through agents

## Troubleshooting

### Session ID Error
If you see "Invalid length for parameter runtimeSessionId":
- Ensure session ID is at least 33 characters
- The Lambda automatically generates valid session IDs

### Timeout Issues
If searches timeout:
- Check if the search is complex (may take 30-60s)
- Verify Lambda timeout is set to 300s
- For UI testing, use direct Lambda invocation instead

### Empty Results
If results are empty:
- Check Agent Core runtime is deployed and active
- Verify the query is specific enough
- Check CloudWatch logs for detailed error messages

## Future Improvements
- [ ] Implement async pattern for UI testing
- [ ] Add caching for repeated searches
- [ ] Support batch operations
- [ ] Add more action types (login, form fill, etc.)
- [ ] Implement retry logic for transient failures

## Related Documentation
- [AWS Bedrock Agent Core](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Nova Act Browser Automation](https://docs.aws.amazon.com/bedrock/latest/userguide/nova-act.html)
- [Strands Framework](https://github.com/aws/strands)