# Long Content Feature Documentation

This document describes the long content feature, an advanced capability for handling large message contexts that exceed AWS Step Functions size limits.

## Overview

AWS Step Functions has a maximum message size limit of approximately 256KB. When AI agents process large documents, scrape extensive web content, or analyze detailed images, the results can exceed this limit. The long content feature provides a solution by automatically storing large content in DynamoDB and replacing it with references in Step Functions messages.

## Architecture

The long content feature uses a **parallel architecture pattern** where specialized stacks run alongside standard stacks without affecting them:

```
Standard Architecture          Long Content Architecture
├── SharedInfrastructureStack  ├── SharedLongContentInfrastructureStack
├── SharedLLMStack             ├── SharedLLMWithLongContentStack  
├── BaseAgentStack             ├── LongContentAgentStack
├── BaseToolConstruct          ├── LongContentToolConstruct
└── Standard Agents            └── Long Content Agents
```

## Key Components

### 1. Lambda Runtime API Proxy Extension

The core of the long content feature is a Rust-based Lambda extension that intercepts Lambda Runtime API calls:

- **Location**: `lambda/extensions/long-content/`
- **Purpose**: Transparently handles content transformation
- **Languages**: Works with any Lambda runtime (Python, Node.js, Java, Rust, Go)
- **Operation**: 
  - Intercepts outgoing responses to store large content in DynamoDB
  - Intercepts incoming requests to retrieve content from DynamoDB references

### 2. Infrastructure Components

#### SharedLongContentInfrastructureStack
- **DynamoDB Table**: `AgentContext-{env_name}` with TTL for automatic cleanup
- **Lambda Layers**: Runtime API Proxy extension for x86_64 and ARM64 architectures
- **CloudFormation Exports**: For other stacks to reference

#### SharedLLMWithLongContentStack
- **Enhanced LLM Functions**: Standard LLM functions with proxy extension layer
- **Environment Variables**: Content transformation configuration
- **DynamoDB Access**: Permissions for content storage and retrieval

### 3. Agent and Tool Base Classes

#### LongContentAgentStack
- **Extends**: BaseAgentStack
- **Features**: DynamoDB access, proxy layer integration, content transformation config
- **Use Cases**: Agents that process large inputs or generate extensive outputs

#### LongContentToolConstruct  
- **Extends**: BaseToolConstruct
- **Features**: Automatic proxy layer attachment, content table permissions
- **Use Cases**: Tools that produce large outputs (web scrapers, image analyzers)

## Content Transformation Process

### Storage (Tool → Step Functions)
1. Tool Lambda function executes and generates large response
2. Runtime API Proxy intercepts the response
3. If content size > threshold, content is stored in DynamoDB with UUID
4. Response is replaced with reference: `@content:dynamodb:table:record-{uuid}`
5. Step Functions receives compact message with reference

### Retrieval (Step Functions → LLM)
1. Step Functions sends message with DynamoDB reference to LLM Lambda
2. Runtime API Proxy intercepts the request
3. Proxy retrieves actual content from DynamoDB using the UUID
4. LLM receives full content seamlessly
5. LLM processes complete context without size limitations

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `AWS_LAMBDA_EXEC_WRAPPER` | Yes | Must be `/opt/extensions/lrap-wrapper/wrapper` | - |
| `AGENT_CONTEXT_TABLE` | No | DynamoDB table name | `AgentContext` |
| `MAX_CONTENT_SIZE` | No | Size threshold in bytes | `5000` |
| `LRAP_DEBUG` | No | Enable debug logging | `false` |

### Content Size Thresholds

Different use cases require different thresholds:

- **Web Scraping**: 8-10KB (handles most web pages)
- **Image Analysis**: 15KB (detailed analysis results)
- **Document Processing**: 20KB (extensive text extraction)
- **LLM Functions**: 10KB (large context handling)

## Deployment

### Prerequisites

1. **Build Lambda Extension**:
   ```bash
   cd lambda/extensions/long-content
   make build
   make deploy
   ```

2. **Verify S3 Artifacts**: Extension ZIPs must be in artifacts bucket

### Standard Deployment

Use the provided deployment script:

```bash
# Deploy infrastructure and examples
python deploy_long_content.py --env dev

# Deploy only infrastructure
python deploy_long_content.py --env prod --no-examples

# Deploy only LLM components
python deploy_long_content.py --env dev --llm-only
```

### Manual CDK Deployment

```bash
# Deploy all long content stacks
cdk deploy --app "python deploy_long_content.py --env dev" --all

# Deploy specific stacks
cdk deploy SharedLongContentInfrastructure-dev
cdk deploy SharedLLMWithLongContent-dev
```

## Usage Examples

### Creating a Long Content Agent

```python
from stacks.agents.long_content_agent_stack import LongContentAgentStack

class CustomLongContentAgent(LongContentAgentStack):
    def __init__(self, scope, construct_id, env_name="prod", **kwargs):
        llm_arn = Fn.import_value(f"SharedClaudeLambdaWithLongContentArn-{env_name}")
        
        tool_configs = [
            {
                "tool_name": "large_data_processor",
                "lambda_arn": Fn.import_value(f"LargeDataProcessorLambdaArn-{env_name}"),
                "requires_approval": False,
                "supports_long_content": True
            }
        ]
        
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="CustomLongContentAgent",
            llm_arn=llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            max_content_size=15000,  # 15KB threshold
            **kwargs
        )
```

### Creating a Long Content Tool

```python
from stacks.shared.long_content_tool_construct import LongContentToolConstruct

class CustomLongContentTool(LongContentToolConstruct):
    def _create_tools(self):
        tool_definition = ToolDefinition(
            tool_name="large_data_processor",
            description="Processes large datasets with extensive output",
            # ... other fields
        )
        
        self.create_long_content_lambda_function(
            function_id="LargeDataProcessorFunction",
            function_name=f"large-data-processor-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("path/to/code"),
            handler="app.handler",
            tool_definition=tool_definition,
            timeout_seconds=300,
            memory_size=2048
        )
```

## Monitoring and Debugging

### CloudWatch Logs

Enable debug logging for detailed proxy operation logs:

```python
environment={
    "LRAP_DEBUG": "true"
}
```

Look for log entries with `[LRAP]` and `[TRANSFORM]` prefixes.

### DynamoDB Monitoring

Monitor the content table for:
- Item count (number of stored content pieces)
- Storage size (total content storage)
- TTL cleanup (automatic content expiration)

### Debug Markers

The proxy adds debug markers to processed messages:
- `proxy_in: true` - Input event processed by proxy
- `proxy_out: true` - Output response processed by proxy

## Best Practices

### When to Use Long Content Support

**Use long content support when**:
- Tool outputs regularly exceed 5KB
- Agent processes large documents or datasets
- Web scraping produces extensive content
- Image analysis generates detailed reports

**Don't use long content support when**:
- Tool outputs are consistently small (< 2KB)
- Simple question-answering scenarios
- Basic text processing tasks
- Performance is critical and content is manageable

### Performance Considerations

- **Latency**: Additional DynamoDB calls add ~10-50ms per large content operation
- **Cost**: DynamoDB storage and read/write operations
- **TTL**: Content automatically expires (default: 24 hours)
- **Concurrency**: DynamoDB supports high concurrent access

### Error Handling

- **DynamoDB Failures**: Proxy logs errors but passes through original content
- **Size Limits**: Configure appropriate thresholds for your use cases
- **Timeout**: Increase Lambda timeouts for content processing

## Troubleshooting

### Common Issues

1. **Extension not loading**:
   - Verify `AWS_LAMBDA_EXEC_WRAPPER` is set correctly
   - Check Lambda layer ARN is valid
   - Ensure extension binary is executable

2. **Content not transforming**:
   - Check `MAX_CONTENT_SIZE` threshold
   - Verify DynamoDB table permissions
   - Enable debug logging to see proxy operation

3. **Performance issues**:
   - Monitor DynamoDB throttling
   - Adjust Lambda memory allocation
   - Review content size thresholds

### Debug Steps

1. **Enable debug logging**: Set `LRAP_DEBUG=true`
2. **Check CloudWatch logs**: Look for proxy operation logs
3. **Verify DynamoDB**: Check content table for stored items
4. **Test without proxy**: Temporarily disable to isolate issues

## Security Considerations

- **DynamoDB Access**: Least privilege IAM permissions
- **Content Encryption**: DynamoDB encryption at rest
- **TTL Configuration**: Automatic content cleanup
- **Network Access**: Proxy operates within Lambda environment

## Migration from Standard Stacks

To migrate an existing agent to long content support:

1. **Deploy long content infrastructure**
2. **Create long content versions** of agent and tool stacks
3. **Test thoroughly** with representative data
4. **Update client applications** to use new stack exports
5. **Monitor performance** and adjust thresholds as needed

The migration is **non-breaking** - standard stacks continue to operate normally.

## Cost Analysis

Additional costs for long content support:

- **DynamoDB**: Storage and operations (minimal for TTL cleanup)
- **Lambda**: Extension processing overhead (~1-5% increase)
- **CloudWatch**: Additional logs (if debug enabled)

Cost scales with content size and frequency of large operations.

## Limitations

- **Content Size**: DynamoDB item limit is 400KB (adequate for most use cases)
- **Latency**: Additional DynamoDB operations add latency
- **Languages**: Extension works with all Lambda runtimes, but implementation is in Rust
- **Regions**: Must be deployed per region

## Support and Maintenance

- **Extension Updates**: Rebuild and redeploy layers for updates
- **Monitoring**: CloudWatch metrics and logs
- **Scaling**: DynamoDB auto-scaling handles load
- **Backup**: DynamoDB point-in-time recovery enabled