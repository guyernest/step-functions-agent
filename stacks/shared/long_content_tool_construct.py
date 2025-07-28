"""
Long Content Tool Construct

Extends BaseToolConstruct to provide long content support for tools that handle
large input/output data that may exceed Step Functions message size limits.

This construct provides:
1. Lambda Runtime API Proxy extension layer integration
2. DynamoDB content table access for large content storage
3. Environment variables for content transformation
4. Architecture-specific layer selection (x86_64 vs ARM64)

Use this construct when your tools:
- Process large web scraping results
- Handle extensive image analysis outputs  
- Generate large document processing results
- Return datasets that may exceed Step Functions limits
"""

from abc import abstractmethod
from typing import Dict, List, Any, Optional
from aws_cdk import (
    Fn,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct

from .base_tool_construct import BaseToolConstruct, ToolExport
from .naming_conventions import NamingConventions
from stacks.shared.tool_definitions import ToolDefinition


class LongContentToolConstruct(BaseToolConstruct):
    """
    Base construct for tools that need to handle large content.
    
    IMPORTANT: This is an optional construct for tools that handle large content.
    Most tools should use the standard BaseToolConstruct instead.
    
    This construct automatically:
    - Imports long content infrastructure resources
    - Adds proxy extension layers to Lambda functions
    - Configures environment variables for content transformation
    - Grants DynamoDB access for content storage
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        env_name: str, 
        max_content_size: int = 5000,
        **kwargs
    ):
        """
        Initialize LongContentToolConstruct
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this construct
            env_name: Environment name (dev, prod, etc.)
            max_content_size: Maximum content size before storing in DynamoDB (default: 5000)
        """
        self.max_content_size = max_content_size
        self.env_name = env_name  # Set env_name before importing infrastructure
        
        # Import long content infrastructure before calling parent
        self._import_long_content_infrastructure()
        
        # Call parent constructor
        super().__init__(scope, construct_id, env_name, **kwargs)
        
        print(f"✅ Created long content tool construct (max content size: {max_content_size} bytes)")

    def _import_long_content_infrastructure(self):
        """Import shared long content infrastructure resources"""
        
        # Import DynamoDB content table
        self.content_table_name = Fn.import_value(
            NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name)
        )
        
        self.content_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name)
        )
        
        # Import proxy extension layer ARNs
        self.proxy_layer_x86_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerX86", "LongContent", self.env_name)
        )
        
        self.proxy_layer_arm_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerArm", "LongContent", self.env_name)
        )
        
        print(f"📊 Imported long content infrastructure for {self.env_name}")

    def create_long_content_lambda_function(
        self,
        function_id: str,
        function_name: str,
        runtime: lambda_.Runtime,
        code: lambda_.Code,
        handler: str,
        tool_definition: ToolDefinition,
        architecture: lambda_.Architecture = lambda_.Architecture.X86_64,
        timeout_seconds: int = 60,
        memory_size: int = 512,
        additional_environment: Dict[str, str] = None,
        **kwargs
    ) -> lambda_.Function:
        """
        Create a Lambda function with long content support and register it as a tool.
        
        Args:
            function_id: CDK construct ID for the function
            function_name: Name of the Lambda function
            runtime: Lambda runtime
            code: Lambda code asset
            handler: Function handler
            tool_definition: Tool definition for registry
            architecture: Lambda architecture (X86_64 or ARM_64)
            timeout_seconds: Function timeout in seconds
            memory_size: Function memory in MB
            additional_environment: Additional environment variables
            **kwargs: Additional Lambda function properties
            
        Returns:
            Lambda function with long content support configured
        """
        
        # Get long content configuration
        long_content_config = self._get_long_content_lambda_config(architecture, function_id)
        
        # Merge environment variables
        environment = long_content_config["environment"].copy()
        if additional_environment:
            environment.update(additional_environment)
        
        # Create the Lambda function
        function = lambda_.Function(
            self,
            function_id,
            function_name=function_name,
            runtime=runtime,
            code=code,
            handler=handler,
            architecture=architecture,
            layers=long_content_config["layers"],
            environment=environment,
            timeout=Duration.seconds(timeout_seconds),
            memory_size=memory_size,
            **kwargs
        )
        
        # Grant the function access to the content table
        self._grant_content_table_access(function)
        
        # Register the tool
        self._register_tool(tool_definition, function)
        
        print(f"⚡ Created long content Lambda function: {function_name}")
        return function

    def _get_long_content_lambda_config(self, architecture: lambda_.Architecture, function_id: str = None) -> Dict[str, Any]:
        """
        Get Lambda configuration for long content support
        
        Args:
            architecture: Lambda architecture (X86_64 or ARM_64)
            
        Returns:
            Dictionary with layers and environment variables for long content support
        """
        
        # Select appropriate proxy layer based on architecture
        if architecture == lambda_.Architecture.ARM_64:
            proxy_layer_arn = self.proxy_layer_arm_arn
            arch_name = "ARM64"
        else:
            proxy_layer_arn = self.proxy_layer_x86_arn
            arch_name = "x86_64"
        
        # Reference the proxy extension layer with function-specific ID
        layer_id = f"ProxyExtensionLayer{arch_name}"
        if function_id:
            layer_id += f"For{function_id}"
        proxy_extension_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            layer_id,
            layer_version_arn=proxy_layer_arn
        )
        
        config = {
            "layers": [proxy_extension_layer],
            "environment": {
                # Required for Lambda Runtime API Proxy to work
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
                
                # Configuration for content transformation
                "AGENT_CONTEXT_TABLE": self.content_table_name,
                "MAX_CONTENT_SIZE": str(self.max_content_size),
                
                # Optional: Enable debug logging
                "LRAP_DEBUG": "false"  # Set to "true" for debugging
            }
        }
        
        print(f"🔧 Generated long content Lambda config for {arch_name} architecture")
        return config

    def _grant_content_table_access(self, lambda_function: lambda_.Function):
        """Grant a Lambda function access to the content table"""
        
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem"
                ],
                resources=[self.content_table_arn]
            )
        )
        
        print(f"🔐 Granted content table access to Lambda function")

    def get_tool_configs_for_agent(self, requires_approval: bool = False) -> List[Dict[str, Any]]:
        """
        Get tool configurations for long content agent stacks.
        
        Extends the base method to include long content metadata.
        """
        configs = super().get_tool_configs_for_agent(requires_approval)
        
        # Add long content metadata to each tool config
        for config in configs:
            config.update({
                "supports_long_content": True,
                "max_content_size": self.max_content_size,
                "content_table_name": self.content_table_name
            })
        
        return configs

    @abstractmethod
    def _create_tools(self) -> None:
        """
        Create Lambda functions and define tool schemas.
        
        Subclasses must use create_long_content_lambda_function() instead of
        creating Lambda functions directly to get long content support.
        
        Example:
            def _create_tools(self):
                # Define tool schema
                web_scraper_tool = ToolDefinition(
                    tool_name="web_scraper",
                    description="Scrape web pages and extract content",
                    # ... other fields
                )
                
                # Create Lambda with long content support
                self.create_long_content_lambda_function(
                    function_id="WebScraperFunction",
                    function_name=f"web-scraper-{self.env_name}",
                    runtime=lambda_.Runtime.PYTHON_3_11,
                    code=lambda_.Code.from_asset("path/to/code"),
                    handler="app.handler",
                    tool_definition=web_scraper_tool
                )
        """
        pass