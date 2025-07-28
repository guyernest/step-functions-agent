from aws_cdk import (
    Stack,
    Fn,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct
from typing import Dict, Any, List, Optional
from ..shared.long_content_tool_construct import LongContentToolConstruct
from ..shared.naming_conventions import NamingConventions
from stacks.shared.tool_definitions import ToolDefinition, ToolLanguage, ToolStatus


class FlexibleLongContentToolStack(Stack):
    """
    Flexible Long Content Tool Stack
    
    Base class for tool stacks that need long content support and can
    optionally integrate with existing tool registry.
    
    Configuration options:
    - use_tool_registry: Whether to register tools in existing registry
    - tool_registry_table_name: Name of existing tool registry table
    - import_from_exports: Import registry from CloudFormation exports
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        env_name: str = "prod",
        tool_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.tool_config = tool_config or {}
        
        # Import tool registry if configured
        self._import_tool_registry()
        
        # Create the tool construct (to be used by subclasses)
        self.tool_construct = None
        
        print(f"✅ Created flexible long content tool stack for {env_name}")
    
    def _import_tool_registry(self):
        """Import tool registry if configured"""
        
        if not self.tool_config.get("use_tool_registry", True):
            self.tool_registry_table = None
            return
        
        # Option 1: Import by table name
        if self.tool_config.get("tool_registry_table_name"):
            self.tool_registry_table = dynamodb.Table.from_table_name(
                self,
                "ImportedToolRegistry",
                self.tool_config["tool_registry_table_name"]
            )
            print(f"📋 Imported tool registry table: {self.tool_config['tool_registry_table_name']}")
        
        # Option 2: Import from CloudFormation export
        elif self.tool_config.get("import_from_exports", True):
            self.tool_registry_table_name = Fn.import_value(
                NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
            )
            self.tool_registry_table_arn = Fn.import_value(
                NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
            )
            # Note: We can't create a Table object from CloudFormation imports,
            # but we have the name and ARN for permissions
            self.tool_registry_table = None
            print(f"📋 Imported tool registry from CloudFormation exports")
        else:
            self.tool_registry_table = None
    
    def _register_tool_with_registry(
        self, 
        tool_definition: ToolDefinition, 
        lambda_function: lambda_.Function
    ):
        """
        Register tool with the tool registry if available
        
        Note: This would typically be done via a custom resource or 
        post-deployment script since we can't write to DynamoDB during synthesis
        """
        if hasattr(self, 'tool_registry_table_arn'):
            # Grant permissions to a hypothetical registration Lambda
            # that would run post-deployment
            print(f"🔧 Tool {tool_definition.tool_name} ready for registry")
    
    def _grant_tool_registry_permissions(self, role: iam.Role):
        """Grant permissions to read from tool registry"""
        
        if hasattr(self, 'tool_registry_table_arn'):
            role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    resources=[
                        self.tool_registry_table_arn,
                        f"{self.tool_registry_table_arn}/index/*"
                    ]
                )
            )


class WebScraperFlexibleLongContentToolStack(FlexibleLongContentToolStack):
    """
    Web Scraper Tools with Flexible Long Content Support
    
    Can integrate with existing tool registry while providing
    long content capabilities.
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        
        # Configure to use existing tool registry
        tool_config = {
            "use_tool_registry": True,
            "import_from_exports": True
        }
        
        super().__init__(
            scope=scope,
            construct_id=construct_id,
            env_name=env_name,
            tool_config=tool_config,
            **kwargs
        )
        
        # Create the long content tool construct
        self.tool_construct = LongContentToolConstruct(
            self,
            "WebScraperLongContentTools",
            env_name=env_name,
            max_content_size=8000  # 8KB threshold
        )
        
        # Create tools
        self._create_tools()
        
        print(f"🕷️ Created web scraper tools with registry integration")
    
    def _create_tools(self):
        """Create web scraping tools"""
        
        # Define web scraper tool
        web_scraper_def = ToolDefinition(
            tool_name="web_scraper_large",
            description="Advanced web scraper for large content",
            language=ToolLanguage.PYTHON,
            status=ToolStatus.STABLE,
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},
                    "max_content_size": {"type": "number", "description": "Maximum content size"}
                },
                "required": ["url"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "metadata": {"type": "object"}
                }
            }
        )
        
        # Create Lambda function
        web_scraper_lambda = self.tool_construct.create_long_content_lambda(
            id="WebScraperLarge",
            function_name=f"web-scraper-large-{self.env_name}",
            description="Web scraper with long content support",
            code=lambda_.Code.from_inline("""
import json
import urllib.request

def lambda_handler(event, context):
    url = event.get('url')
    
    # Simple web scraping logic (in real implementation, use BeautifulSoup etc.)
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'content': content,
                'metadata': {
                    'url': url,
                    'length': len(content),
                    'content_type': response.headers.get('Content-Type', 'text/html')
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
"""),
            handler="index.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            timeout=Duration.minutes(5),
            memory_size=1024
        )
        
        # Register tool
        self.tool_construct._register_tool(web_scraper_def, web_scraper_lambda)
        
        # Optionally register with tool registry
        self._register_tool_with_registry(web_scraper_def, web_scraper_lambda)