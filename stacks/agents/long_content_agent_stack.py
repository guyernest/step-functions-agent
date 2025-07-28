from aws_cdk import (
    Fn,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.naming_conventions import NamingConventions
from typing import List, Dict, Any


class LongContentAgentStack(BaseAgentStack):
    """
    Long Content Agent Stack - For agents handling large message contexts
    
    This specialized agent stack extends BaseAgentStack with:
    - DynamoDB table access for large content storage
    - Lambda Runtime API Proxy extension layer
    - Environment variables for content transformation
    - Automatic architecture detection for layer selection
    
    IMPORTANT: This is an optional stack for agents that need to handle large content.
    Most agents should use the standard BaseAgentStack instead.
    
    Use this stack when:
    - Agent deals with large web scraping results
    - Tool outputs exceed Step Functions message limits
    - Image analysis produces large responses
    - Document processing generates extensive content
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        agent_name: str,
        llm_arn: str, 
        tool_configs: List[Dict[str, Any]], 
        env_name: str = "prod",
        system_prompt: str = None,
        max_content_size: int = 5000,
        **kwargs
    ) -> None:
        """
        Initialize LongContentAgentStack
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this construct
            agent_name: Name of the agent (e.g., "WebScraper", "ImageAnalyzer")
            llm_arn: ARN of the LLM Lambda function to use
            tool_configs: List of tool configurations with lambda_arn, tool_name, etc.
            env_name: Environment name (dev, prod, etc.)
            system_prompt: Optional custom system prompt for the agent
            max_content_size: Maximum content size before storing in DynamoDB (default: 5000)
        """
        
        # Store long content specific configuration
        self.max_content_size = max_content_size
        
        # Call parent constructor first
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            agent_name=agent_name,
            llm_arn=llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            **kwargs
        )
        
        print(f"✅ Created long content agent stack: {agent_name} (max content size: {max_content_size} bytes)")

    def _import_shared_resources(self):
        """Import shared resources including long content infrastructure"""
        
        # Import standard shared resources
        super()._import_shared_resources()
        
        # Import long content infrastructure
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

    def _create_agent_execution_role(self):
        """Create IAM role with additional permissions for long content support"""
        
        # Call parent method to create base role
        super()._create_agent_execution_role()
        
        # Add permissions for DynamoDB content table
        self.agent_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.content_table_arn,
                    f"{self.content_table_arn}/index/*"
                ]
            )
        )
        
        print(f"🔐 Added DynamoDB content table permissions to agent execution role")

    def get_long_content_lambda_config(self, architecture: lambda_.Architecture = lambda_.Architecture.X86_64) -> Dict[str, Any]:
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
        
        # Reference the proxy extension layer
        proxy_extension_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            f"{self.agent_name}ProxyExtensionLayer{arch_name}",
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

    def create_long_content_lambda_function(
        self,
        function_id: str,
        function_name: str,
        runtime: lambda_.Runtime,
        code: lambda_.Code,
        handler: str,
        architecture: lambda_.Architecture = lambda_.Architecture.X86_64,
        additional_environment: Dict[str, str] = None,
        **kwargs
    ) -> lambda_.Function:
        """
        Create a Lambda function with long content support
        
        Args:
            function_id: CDK construct ID for the function
            function_name: Name of the Lambda function
            runtime: Lambda runtime
            code: Lambda code asset
            handler: Function handler
            architecture: Lambda architecture
            additional_environment: Additional environment variables
            **kwargs: Additional Lambda function properties
            
        Returns:
            Lambda function with long content support configured
        """
        
        # Get long content configuration
        long_content_config = self.get_long_content_lambda_config(architecture)
        
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
            **kwargs
        )
        
        # Grant the function access to the content table
        self._grant_content_table_access(function)
        
        print(f"⚡ Created long content Lambda function: {function_name}")
        return function

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