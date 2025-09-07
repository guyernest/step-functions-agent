# Agent Core Browser Tool

## Overview

This Lambda function provides browser automation capabilities using AWS Bedrock Agent Core with the Nova Act browser automation tool. It implements a **multi-tool registration pattern** where multiple specialized browser tools share a single Lambda function, with routing based on the tool name.

## Design Pattern: Single Lambda, Multiple Tools

Instead of a single generic tool with dynamic schemas, this implementation registers multiple specific tools that all point to the same Lambda function:

- **`browser_broadband`**: UK broadband availability checking via BT Wholesale portal
- **`browser_shopping`**: E-commerce product search and price comparison
- **`browser_search`**: General web search and information extraction

Each tool has its own specific input schema, making it easier for calling agents to construct proper tool calls without ambiguous "agent-specific parameters".

## Architecture

- **Service**: AWS Bedrock Agent Core (container-based runtime)
- **Framework**: Strands multi-agent orchestration
- **Browser**: Nova Act automation tool
- **Timeout**: 300 seconds (5 minutes) for long-running browser tasks

## Configuration

### Agent Routing

The Lambda function routes to different Agent Core agents based on the tool name:

| Tool Name | Agent ID | Purpose |
|-----------|----------|---------|
| `browser_broadband` | `broadband_checker_agent-KcXxkNFCkG` | UK broadband availability checks |
| `browser_shopping` | `shopping_agent-aw6O6r7uk5` | E-commerce product searches |
| `browser_search` | `web_search_agent-3dH6uJ84DT` | General web searches |

### Environment Variables

- `AGENT_CONFIG`: JSON string with agent mappings
- `ENV_NAME`: Environment name (prod/dev)
- `AWS_REGION`: AWS region for Agent Core

## Input Schemas

### browser_broadband

```json
{
  "name": "browser_broadband",
  "input": {
    "address": {
      "building_number": "string - Building number or name",
      "street": "string - Street name",
      "town": "string - Town or city",
      "postcode": "string - UK postcode (required)"
    }
  }
}
```

### browser_shopping

```json
{
  "name": "browser_shopping",
  "input": {
    "query": "string - Product search query",
    "site": "string (optional) - amazon/ebay/all, defaults to amazon",
    "max_results": "integer (optional) - Maximum results to return, defaults to 10"
  }
}
```

### browser_search

```json
{
  "name": "browser_search",
  "input": {
    "query": "string - Search query",
    "url": "string (optional) - Specific URL to search",
    "extract_fields": "array (optional) - Fields to extract from results"
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

### Broadband Availability Check

```json
{
  "name": "browser_broadband",
  "input": {
    "address": {
      "building_number": "13",
      "street": "Albion Drive",
      "town": "London",
      "postcode": "E8 4LX"
    }
  }
}
```

### Product Search

```json
{
  "name": "browser_shopping",
  "input": {
    "query": "gaming laptops with RTX 4060",
    "site": "amazon",
    "max_results": 5
  }
}
```

### General Web Search

```json
{
  "name": "browser_search",
  "input": {
    "query": "latest AI research papers",
    "extract_fields": ["title", "authors", "publication_date"]
  }
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

Multiple tools are registered in DynamoDB, all pointing to the same Lambda:

| Tool Name | Tags | Description |
|-----------|------|-------------|
| `browser_broadband` | `["browser", "automation", "broadband", "uk", "telecom"]` | UK broadband availability |
| `browser_shopping` | `["browser", "automation", "shopping", "e-commerce", "prices"]` | Product search and pricing |
| `browser_search` | `["browser", "automation", "search", "web", "extraction"]` | General web search |

All tools:
- Human approval: Not required
- Lambda ARN: Same function handles all variants

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
