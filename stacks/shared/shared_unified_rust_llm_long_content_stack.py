from aws_cdk import (
    Duration,
    Fn,
    aws_iam as iam,
    aws_lambda as _lambda,
    CfnOutput,
)
from constructs import Construct
from .naming_conventions import NamingConventions


class SharedUnifiedRustLLMWithLongContentStack(Construct):
    """
    Shared Unified Rust LLM Stack with Long Content Support
    
    Creates a Rust-based unified LLM Lambda function with long content capabilities.
    
    This stack creates a Rust LLM Lambda function that includes:
    - Lambda Runtime API Proxy extension layer
    - DynamoDB content table access for large context storage
    - Environment variables for content transformation
    - Architecture-specific layer selection
    
    Use this stack when:
    - Agents need unified LLM support across multiple providers
    - Processing large documents that exceed Step Functions limits
    - LLM context includes extensive web scraping results
    - Tools generate datasets that may be too large for Step Functions
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", max_content_size: int = 5000, **kwargs) -> None:
        """
        Initialize SharedUnifiedRustLLMWithLongContentStack
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this construct  
            env_name: Environment name (dev, prod, etc.)
            max_content_size: Maximum content size before storing in DynamoDB (default: 5000)
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.max_content_size = max_content_size
        
        # Import resources
        self._import_long_content_infrastructure(env_name)
        self._import_llm_resources(env_name)
        
        # Create the Rust LLM with long content support
        self._create_unified_rust_llm_with_long_content()
        
        # Create stack exports
        self._create_stack_exports()
        
        print(f"✅ Created Unified Rust LLM with long content support (max content size: {max_content_size} bytes)")

    def _import_long_content_infrastructure(self, env_name: str):
        """Import shared long content infrastructure resources"""
        
        # Import DynamoDB content table
        self.content_table_name = Fn.import_value(
            NamingConventions.stack_export_name("ContentTable", "LongContent", env_name)
        )
        
        self.content_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("ContentTableArn", "LongContent", env_name)
        )
        
        # Import proxy extension layer ARNs
        self.proxy_layer_x86_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerX86", "LongContent", env_name)
        )
        
        self.proxy_layer_arm_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerArm", "LongContent", env_name)
        )
        
        print(f"📊 Imported long content infrastructure for {env_name}")

    def _import_llm_resources(self, env_name: str):
        """Import LLM resources from shared infrastructure"""
        from aws_cdk import aws_secretsmanager as secretsmanager, aws_logs as logs, RemovalPolicy
        
        # Import the existing secret
        self.llm_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "ImportedLLMSecrets",
            secret_name=f"/ai-agent/llm-secrets/{env_name}"
        )
        
        # Create a dedicated log group for Rust LLM with long content
        self.log_group = logs.LogGroup(
            self, 
            "UnifiedRustLLMLongContentLogGroup",
            log_group_name=f"/aws/lambda/unified-rust-llm-long-content-{env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        print(f"🔑 Imported LLM secrets and created log group")

    def _create_unified_rust_llm_with_long_content(self):
        """Create the Unified Rust LLM Lambda with long content support"""
        
        # Import the ARM64 proxy layer
        arm_proxy_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ProxyExtensionLayerARM64",
            layer_version_arn=self.proxy_layer_arm_arn
        )
        
        # Create execution role with necessary permissions
        self.llm_execution_role = iam.Role(
            self,
            "UnifiedRustLLMExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        
        # Grant access to the imported LLM secrets
        self.llm_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:secretsmanager:*:*:secret:/ai-agent/llm-secrets/{self.env_name}*"
                ]
            )
        )
        
        # Grant access to X-Ray tracing
        self.llm_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for DynamoDB content table
        self.llm_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.content_table_arn,
                    f"{self.content_table_arn}/index/*"
                ]
            )
        )
        
        # Create the Unified Rust LLM Lambda with long content support
        self.unified_rust_llm = _lambda.Function(
            self,
            "UnifiedRustLLMWithLongContent",
            function_name=f"unified-rust-llm-long-content-{self.env_name}",
            description="Unified Rust LLM service with long content support",
            code=_lambda.Code.from_asset("lambda/call_llm_rust/target/lambda/bootstrap"),
            handler="main",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            timeout=Duration.seconds(120),  # Increased timeout for content processing
            memory_size=768,  # Increased memory for content processing
            architecture=_lambda.Architecture.ARM_64,
            layers=[arm_proxy_layer],  # Add proxy extension layer
            log_group=self.log_group,
            role=self.llm_execution_role,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "ENVIRONMENT": self.env_name,
                "POWERTOOLS_SERVICE_NAME": "unified-rust-llm-long-content",
                "POWERTOOLS_LOG_LEVEL": "INFO",
                "RUST_LOG": "info",
                # Required for Lambda Runtime API Proxy to work
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
                # Configuration for content transformation
                "AGENT_CONTEXT_TABLE": self.content_table_name,
                "MAX_CONTENT_SIZE": str(self.max_content_size),
                # Optional: Enable debug logging
                "LRAP_DEBUG": "false"  # Set to "true" for debugging
            }
        )
        
        print(f"🚀 Created Unified Rust LLM Lambda with long content support")

    def _create_stack_exports(self):
        """Create CloudFormation outputs"""
        
        # Export Lambda function ARN
        CfnOutput(
            self, 
            "UnifiedRustLLMWithLongContentArn",
            value=self.unified_rust_llm.function_arn,
            export_name=f"UnifiedRustLLMWithLongContentArn-{self.env_name}",
            description="ARN of the Unified Rust LLM Lambda with long content support"
        )
        
        # Export function name
        CfnOutput(
            self, 
            "UnifiedRustLLMWithLongContentName",
            value=self.unified_rust_llm.function_name,
            export_name=f"UnifiedRustLLMWithLongContentName-{self.env_name}",
            description="Name of the Unified Rust LLM Lambda with long content support"
        )