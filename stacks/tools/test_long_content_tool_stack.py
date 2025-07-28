from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
)
from constructs import Construct
from ..shared.long_content_tool_construct import LongContentToolConstruct
from stacks.shared.tool_definitions import ToolDefinition, ToolLanguage, ToolStatus


class TestLongContentToolStack(LongContentToolConstruct):
    """
    Test Long Content Tool Stack
    
    Simple test tools for validating long content functionality.
    These tools generate controlled large outputs for testing the
    content transformation pipeline.
    
    Tools provided:
    - echo_large_content: Generates content of specified size for testing
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Initialize with long content support (low threshold for testing)
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            env_name=env_name,
            max_content_size=3000,  # Low threshold for easy testing
            **kwargs
        )

    def _create_tools(self) -> None:
        """Create test tools for long content validation"""
        
        # Echo Large Content Tool
        echo_large_content_tool = ToolDefinition(
            tool_name="echo_large_content",
            description="Test tool that generates large content outputs for validating long content functionality",
            language=ToolLanguage.PYTHON,
            status=ToolStatus.ACTIVE,
            human_approval_required=False,
            parameters={
                "content_size": {
                    "type": "integer",
                    "description": "Size in bytes of content to generate",
                    "required": True,
                    "minimum": 100,
                    "maximum": 51200,  # 50KB maximum for testing
                    "default": 5000
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern to repeat in the generated content",
                    "default": "TEST_CONTENT_",
                    "maxLength": 100
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Include test metadata in the response",
                    "default": True
                },
                "format": {
                    "type": "string",
                    "description": "Output format for the generated content",
                    "enum": ["text", "json", "structured"],
                    "default": "structured"
                }
            },
            expected_output="Generated content of specified size. Large outputs are automatically stored in DynamoDB for testing."
        )

        # Create Lambda function with long content support
        self.create_long_content_lambda_function(
            function_id="EchoLargeContentFunction",
            function_name=f"echo-large-content-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("lambda/tools/echo-large-content"),
            handler="index.handler",
            tool_definition=echo_large_content_tool,
            timeout_seconds=60,   # 1 minute should be enough for testing
            memory_size=256,      # Minimal memory for test tool
            additional_environment={
                "TEST_MODE": "true",
                "MAX_CONTENT_SIZE_OVERRIDE": str(self.max_content_size)
            }
        )

        print(f"🧪 Created test long content tools for {env_name} environment")