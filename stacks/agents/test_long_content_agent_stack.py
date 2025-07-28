from aws_cdk import (
    Fn,
)
from constructs import Construct
from .long_content_agent_stack import LongContentAgentStack


class TestLongContentAgentStack(LongContentAgentStack):
    """
    Test Long Content Agent Stack
    
    Simple test agent for validating long content functionality.
    This agent uses a basic echo tool that can generate large outputs
    for testing the content transformation pipeline.
    
    Use this agent to:
    - Validate that long content infrastructure is working
    - Test content transformation thresholds
    - Debug proxy extension functionality
    - Verify DynamoDB storage and retrieval
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Import LLM ARN for long content support
        llm_arn = Fn.import_value(f"SharedClaudeLambdaWithLongContentArn-{env_name}")
        
        # Define tool configurations for testing
        tool_configs = [
            {
                "tool_name": "echo_large_content",
                "lambda_arn": Fn.import_value(f"EchoLargeContentLambdaArn-{env_name}"),
                "requires_approval": False,
                "supports_long_content": True
            }
        ]
        
        # Simple system prompt for testing
        system_prompt = """You are a test AI assistant for validating long content functionality.

You have access to an echo tool that can generate large content outputs for testing purposes. Use this tool to:

1. Test content transformation by requesting outputs of various sizes
2. Validate that large content is properly stored and retrieved
3. Verify that the Lambda Runtime API Proxy is working correctly

The echo tool accepts:
- content_size: Size in bytes of content to generate (up to 50KB)
- pattern: Pattern to repeat in the generated content
- include_metadata: Whether to include test metadata

Example usage:
- Generate 10KB of test content: echo_large_content(content_size=10000, pattern="TEST_DATA")
- Generate content above threshold: echo_large_content(content_size=8000, pattern="LARGE_CONTENT_TEST")

This tool helps validate that the long content infrastructure is functioning properly."""

        # Initialize with long content support (low threshold for testing)
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name="TestLongContent",
            llm_arn=llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            max_content_size=3000,  # Low threshold for easy testing
            **kwargs
        )
        
        print(f"✅ Created test long content agent for {env_name} environment")