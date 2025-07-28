from aws_cdk import (
    Stack,
    Fn,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    Duration,
)
from constructs import Construct
from ..shared.long_content_tool_construct import LongContentToolConstruct
from ..shared.naming_conventions import NamingConventions
from stacks.shared.tool_definitions import ToolDefinition, ToolLanguage, ToolStatus
from typing import Dict, Any, Optional


class WebScraperWithLongContentToolStack(Stack):
    """
    Web Scraper Tool Stack with Long Content Support
    
    Implements advanced web scraping tools that can handle large outputs
    using the Lambda Runtime API Proxy extension for content transformation.
    
    This stack demonstrates:
    - Using LongContentToolConstruct for tools with large outputs
    - Integration with Lambda Runtime API Proxy extension
    - Automatic content transformation via DynamoDB storage
    - Environment configuration for content size thresholds
    - Integration with existing tool registry
    
    Tools provided:
    - web_scraper_large: Advanced web scraper for large content extraction
    - batch_web_scraper: Tool for scraping multiple URLs with consolidated output
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
        
        # Create the long content tool construct
        self.web_scraper_tools = LongContentToolConstruct(
            self,
            "WebScraperLongContentTools",
            env_name=env_name,
            max_content_size=8000  # 8KB threshold for web content
        )
        
        # Create the tools within the construct
        self._create_tools()
        
        print(f"🕷️ Created web scraper tools with long content support for {env_name} environment")

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
        
        # Option 2: Import from CloudFormation export (default)
        else:
            self.tool_registry_table_name = Fn.import_value(
                NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
            )
            self.tool_registry_table_arn = Fn.import_value(
                NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
            )
            print(f"📋 Imported tool registry from CloudFormation exports")
    
    def _create_tools(self) -> None:
        """Create web scraping tools with long content support"""
        
        # 1. Large Content Web Scraper Tool
        web_scraper_large_tool = ToolDefinition(
            tool_name="web_scraper_large",
            description="Advanced web scraper capable of handling large content outputs from complex websites",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to scrape"
                    },
                    "extract_type": {
                        "type": "string", 
                        "description": "Type of content to extract: 'full', 'text_only', 'structured', 'tables'",
                        "enum": ["full", "text_only", "structured", "tables"],
                        "default": "full"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include page metadata (title, description, etc.)",
                        "default": True
                    },
                    "follow_links": {
                        "type": "boolean",
                        "description": "Follow and scrape linked pages (up to 5 levels)",
                        "default": False
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to scrape when following links",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["url"]
            },
            language=ToolLanguage.PYTHON,
            lambda_handler="handler",
            tags=["web-scraping", "content", "long-content"],
            status=ToolStatus.ACTIVE,
            human_approval_required=False
        )

        # Create Lambda function with long content support (using inline code for testing)
        # Store reference to the Lambda function for exports
        web_scraper_code = """
import json

def handler(event, context):
    # Simple test implementation for web scraper
    url = event.get('url', 'https://example.com')
    extract_type = event.get('extract_type', 'full')
    include_metadata = event.get('include_metadata', True)
    
    # Generate large test content that exceeds the long content threshold
    large_content = {
        'url': url,
        'title': f'Test Page for {url}',
        'content': f'This is comprehensive test content from {url}. ' * 200,  # Large content
        'metadata': {
            'title': f'Test Page - {url}',
            'description': f'Test description for {url} with extensive metadata',
            'keywords': ['test', 'web-scraping', 'long-content'] * 50,
            'links': [f'https://example.com/page-{i}' for i in range(100)],
            'images': [f'https://example.com/image-{i}.jpg' for i in range(50)]
        },
        'extracted_data': {
            'paragraphs': [f'Test paragraph {i} with substantial content for testing long content functionality. ' * 20 for i in range(25)],
            'headers': [f'Header {i}' for i in range(20)],
            'tables': [{'column1': f'value{i}', 'column2': f'data{i}'} for i in range(100)]
        },
        'analysis': {
            'word_count': 15000,
            'page_size': '250KB',
            'load_time': '2.5s',
            'performance_score': 85
        }
    }
    
    return {
        'statusCode': 200,
        'scraped_data': large_content,
        'summary': 'Successfully scraped large content from web page for testing long content functionality.',
        'message': 'This is a test web scraper response with large content that should exceed Step Functions limits.'
    }
"""
        
        self.web_scraper_lambda = self.web_scraper_tools.create_long_content_lambda_function(
            function_id="WebScraperLargeFunction",
            function_name=f"web-scraper-large-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_inline(web_scraper_code),
            handler="index.handler",
            tool_definition=web_scraper_large_tool,
            timeout_seconds=300,  # 5 minutes for large scraping operations
            memory_size=1024,     # More memory for processing large content
            additional_environment={
                "USER_AGENT": "StepFunctionsAgent/1.0 WebScraper",
                "RESPECT_ROBOTS_TXT": "true",
                "REQUEST_DELAY_MS": "1000"  # 1 second delay between requests
            }
        )

        # 2. Batch Web Scraper Tool
        batch_web_scraper_tool = ToolDefinition(
            tool_name="batch_web_scraper",
            description="Batch web scraper for processing multiple URLs with consolidated output",
            input_schema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "description": "List of URLs to scrape",
                        "items": {"type": "string"},
                        "maxItems": 20
                    },
                    "extract_type": {
                        "type": "string",
                        "description": "Type of content to extract from each URL",
                        "enum": ["full", "text_only", "structured", "summary"],
                        "default": "structured"
                    },
                    "consolidate_results": {
                        "type": "boolean",
                        "description": "Consolidate all results into a single report",
                        "default": True
                    },
                    "parallel_processing": {
                        "type": "boolean", 
                        "description": "Process URLs in parallel for faster execution",
                        "default": True
                    }
                },
                "required": ["urls"]
            },
            language=ToolLanguage.PYTHON,
            lambda_handler="handler",
            tags=["web-scraping", "batch", "content", "long-content"],
            status=ToolStatus.ACTIVE,
            human_approval_required=False
        )

        # Create Lambda function with long content support (using inline code for testing)
        batch_scraper_code = """
import json

def handler(event, context):
    # Simple test implementation for batch web scraper
    urls = event.get('urls', ['https://example.com'])
    extract_type = event.get('extract_type', 'structured')
    consolidate_results = event.get('consolidate_results', True)
    
    # Generate large batch content that exceeds the long content threshold
    batch_results = []
    for i, url in enumerate(urls[:10]):  # Limit to 10 URLs for testing
        batch_results.append({
            'url': url,
            'title': f'Batch Result {i+1} for {url}',
            'content': f'Comprehensive content from {url} in batch operation. ' * 100,
            'extracted_data': {
                'summary': f'Summary of content from {url} with extensive details. ' * 50,
                'key_points': [f'Key point {j} from {url}' for j in range(20)],
                'entities': [f'Entity {j}' for j in range(30)],
                'sentiment': 'positive',
                'topics': [f'Topic {j}' for j in range(15)]
            },
            'metadata': {
                'processing_time': f'{i+1}.5s',
                'word_count': (i+1) * 1000,
                'quality_score': 85 + i
            }
        })
    
    consolidated_report = {
        'total_urls_processed': len(batch_results),
        'successful_extractions': len(batch_results),
        'failed_extractions': 0,
        'individual_results': batch_results,
        'aggregate_analysis': {
            'total_content_size': '1.5MB',
            'average_processing_time': '2.3s',
            'common_topics': ['technology', 'innovation', 'testing'],
            'overall_sentiment': 'positive',
            'quality_metrics': {
                'average_word_count': 5000,
                'content_diversity': 'high',
                'information_density': 'excellent'
            }
        },
        'recommendations': [f'Recommendation {i}: Process optimization suggestions for better performance. ' * 15 for i in range(10)]
    }
    
    return {
        'statusCode': 200,
        'batch_results': consolidated_report,
        'summary': f'Successfully processed {len(urls)} URLs in batch operation with comprehensive analysis.',
        'message': 'This is a test batch web scraper response with large consolidated content that should exceed Step Functions limits.'
    }
"""
        
        self.batch_web_scraper_lambda = self.web_scraper_tools.create_long_content_lambda_function(
            function_id="BatchWebScraperFunction",
            function_name=f"batch-web-scraper-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_inline(batch_scraper_code),
            handler="index.handler",
            tool_definition=batch_web_scraper_tool,
            timeout_seconds=600,  # 10 minutes for batch operations
            memory_size=2048,     # High memory for batch processing
            additional_environment={
                "USER_AGENT": "StepFunctionsAgent/1.0 BatchWebScraper",
                "RESPECT_ROBOTS_TXT": "true",
                "REQUEST_DELAY_MS": "2000",  # 2 second delay for batch operations
                "MAX_CONCURRENT_REQUESTS": "5"
            }
        )

        # Create exports for the tools
        self._create_tool_exports()
        
        print(f"🕷️ Created web scraper tools with long content support for {self.env_name} environment")
    
    def _create_tool_exports(self):
        """Create CloudFormation exports for tool Lambda functions"""
        from aws_cdk import CfnOutput
        
        # Export web scraper large Lambda ARN
        CfnOutput(
            self,
            "WebScraperLargeLambdaArnExport",
            value=self.web_scraper_lambda.function_arn,
            export_name=f"WebScraperLargeLambdaArn-{self.env_name}",
            description="ARN of the web_scraper_large Lambda function"
        )
        
        # Export batch web scraper Lambda ARN
        CfnOutput(
            self,
            "BatchWebScraperLambdaArnExport",
            value=self.batch_web_scraper_lambda.function_arn,
            export_name=f"BatchWebScraperLambdaArn-{self.env_name}",
            description="ARN of the batch_web_scraper Lambda function"
        )