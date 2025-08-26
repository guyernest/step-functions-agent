from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    CfnOutput
)
from constructs import Construct
from .base_tool_construct import MultiToolConstruct
import os


class WebAutomationToolStack(Stack):
    """
    Web Automation Tools Stack - Browser automation and intelligent web scraping
    
    This stack deploys comprehensive web automation capabilities:
    - Advanced browser automation with Playwright/Chromium
    - Intelligent website memory and learning system
    - Extraction script storage and reuse
    - Complex navigation and interaction support
    - Screenshot and content capture capabilities
    - Site schema analysis and adaptation
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create DynamoDB table for WebScraper Memory
        self._create_webscraper_memory_table()
        
        # Deploy TypeScript web scraper tool
        self._create_web_scraper_tool()
        
        # Deploy Rust WebScraper Memory tool
        self._create_webscraper_memory_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_webscraper_memory_table(self):
        """Create DynamoDB table for WebScraper Memory tool"""
        
        self.webscraper_memory_table = dynamodb.Table(
            self,
            "WebScraperMemoryTable",
            table_name=f"webscraper-memory-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="site_url",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="record_type",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            )
        )

    def _create_web_scraper_tool(self):
        """Create TypeScript Lambda function for web scraping"""
        
        # Create execution role for web scraper Lambda
        scraper_lambda_role = iam.Role(
            self,
            "WebScraperLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to S3 for screenshots and file downloads
        scraper_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject"
                ],
                resources=["arn:aws:s3:::*/*"]
            )
        )
        
        # Create TypeScript Lambda function for web scraping
        self.web_scraper_lambda = _lambda.Function(
            self,
            "WebScraperLambda",
            function_name=f"tool-web-scraper-{self.env_name}",
            description="Advanced web scraping with headless browser automation, navigation, and content extraction",
            runtime=_lambda.Runtime.NODEJS_18_X,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/web-scraper/dist"),
            handler="index.handler",
            timeout=Duration.minutes(5),
            memory_size=2048,  # More memory for Chromium
            role=scraper_lambda_role,
            environment={
                "NODE_ENV": "production",
                "PLAYWRIGHT_BROWSERS_PATH": "/tmp"
            }
        )
        
        self.web_scraper_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "WebScraperLambdaArn",
            value=self.web_scraper_lambda.function_arn,
            export_name=f"WebScraperLambdaArn-{self.env_name}"
        )

    def _create_webscraper_memory_tool(self):
        """Create Rust Lambda function for WebScraper Memory"""
        
        # Create execution role for WebScraper Memory Lambda
        memory_lambda_role = iam.Role(
            self,
            "WebScraperMemoryLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to DynamoDB for memory operations
        memory_lambda_role.add_to_policy(
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
                resources=[self.webscraper_memory_table.table_arn]
            )
        )
        
        # Create Rust Lambda function for WebScraper Memory
        self.webscraper_memory_lambda = _lambda.Function(
            self,
            "WebScraperMemoryLambda",
            function_name=f"tool-webscraper-memory-{self.env_name}",
            description="Intelligent website schema and extraction script memory storage for adaptive web scraping",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/WebScraperMemory/"),
            handler="main",
            timeout=Duration.seconds(120),
            memory_size=512,
            role=memory_lambda_role,
            environment={
                "WEBSCRAPER_MEMORY_TABLE": self.webscraper_memory_table.table_name,
                "RUST_LOG": "info"
            }
        )
        
        self.webscraper_memory_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "WebScraperMemoryLambdaArn",
            value=self.webscraper_memory_lambda.function_arn,
            export_name=f"WebScraperMemoryLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self,
            "WebScraperMemoryTableName",
            value=self.webscraper_memory_table.table_name,
            description="DynamoDB table name for WebScraper Memory storage"
        )

    def _register_tools_using_base_construct(self):
        """Register all web automation tools using the BaseToolConstruct pattern"""
        
        # Define web scraper tool specifications with self-contained definitions
        web_scraper_tools = [
            {
                "tool_name": "web_scraper",
                "description": "Advanced web scraping with headless browser automation and intelligent content extraction",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to scrape"},
                        "selectors": {"type": "object", "description": "CSS selectors for specific elements to extract"},
                        "wait_for": {"type": "string", "description": "CSS selector to wait for before scraping"},
                        "screenshot": {"type": "boolean", "description": "Take screenshot of page", "default": False}
                    },
                    "required": ["url"]
                },
                "language": "typescript",
                "tags": ["web", "scraping", "playwright", "automation"],
                "author": "system"
            }
        ]
        
        # Define memory tool specifications with self-contained definitions
        memory_tools = [
            {
                "tool_name": "webscraper_memory",
                "description": "Retrieve stored extraction scripts and site schemas for adaptive web scraping",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "site_url": {"type": "string", "description": "Website URL to get memory for"},
                        "record_type": {"type": "string", "description": "Type of record to retrieve", "enum": ["schema", "script"]}
                    },
                    "required": ["site_url", "record_type"]
                },
                "language": "rust",
                "tags": ["web", "memory", "schema", "rust"],
                "author": "system"
            },
            {
                "tool_name": "save_extraction_script",
                "description": "Store extraction scripts and site schemas for future use",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "site_url": {"type": "string", "description": "Website URL"},
                        "record_type": {"type": "string", "description": "Type of record to save", "enum": ["schema", "script"]},
                        "content": {"type": "object", "description": "Content to store (schema or script)"}
                    },
                    "required": ["site_url", "record_type", "content"]
                },
                "language": "rust",
                "tags": ["web", "memory", "storage", "rust"],
                "author": "system"
            }
        ]
        
        # Use MultiToolConstruct to register all web automation tools
        MultiToolConstruct(
            self,
            "WebAutomationToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": web_scraper_tools,
                    "lambda_function": self.web_scraper_lambda
                },
                {
                    "tool_specs": memory_tools,
                    "lambda_function": self.webscraper_memory_lambda
                }
            ],
            env_name=self.env_name
        )