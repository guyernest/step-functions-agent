from aws_cdk import (
    Duration,
    Fn,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    CfnOutput,
)
from constructs import Construct
from .shared_llm_stack import SharedLLMStack
from .naming_conventions import NamingConventions


class SharedLLMWithLongContentStack(SharedLLMStack):
    """
    Shared LLM Stack with Long Content Support
    
    Extends SharedLLMStack to provide LLM functions with long content capabilities.
    
    This stack creates LLM Lambda functions that include:
    - Lambda Runtime API Proxy extension layer
    - DynamoDB content table access for large context storage
    - Environment variables for content transformation
    - Architecture-specific layer selection
    
    IMPORTANT: This is an optional stack for LLM functions that need to handle large content.
    Most deployments should use the standard SharedLLMStack instead.
    
    Use this stack when:
    - Agents process large documents that exceed Step Functions limits
    - LLM context includes extensive web scraping results
    - Image analysis produces large responses
    - Tools generate datasets that may be too large for Step Functions
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", max_content_size: int = 5000, **kwargs) -> None:
        """
        Initialize SharedLLMWithLongContentStack
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this construct  
            env_name: Environment name (dev, prod, etc.)
            max_content_size: Maximum content size before storing in DynamoDB (default: 5000)
        """
        self.max_content_size = max_content_size
        
        # Import long content infrastructure before calling parent
        self._import_long_content_infrastructure(env_name)
        
        # Call parent constructor
        super().__init__(scope, construct_id, env_name, **kwargs)
        
        print(f"✅ Created shared LLM stack with long content support (max content size: {max_content_size} bytes)")

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

    def _create_llm_secrets(self):
        """Import existing LLM secrets from main infrastructure"""
        from aws_cdk import aws_secretsmanager as secretsmanager
        
        # Import the existing secret instead of creating a new one
        self.llm_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "ImportedLLMSecrets",
            secret_name=f"/ai-agent/llm-secrets/{self.env_name}"
        )
        
        print(f"🔑 Imported existing LLM secrets: /ai-agent/llm-secrets/{self.env_name}")

    def _create_log_group(self):
        """Create CloudWatch log group with long content specific name"""
        from aws_cdk import aws_logs as logs, RemovalPolicy
        
        self.log_group = logs.LogGroup(
            self, 
            "SharedLLMLongContentLogGroup",
            log_group_name=f"/aws/lambda/shared-llm-long-content-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        print(f"📝 Created CloudWatch Log Group: {self.log_group.log_group_name}")

    def _create_llm_execution_role(self):
        """Create shared IAM role with additional permissions for long content support"""
        
        # Create the execution role directly since we need custom secret permissions
        self.llm_execution_role = iam.Role(
            self,
            "SharedLLMExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        
        # Grant access to the imported LLM secrets
        # When importing secrets, we need to use a wildcard for the version
        self.llm_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/llm-secrets/{self.env_name}*"
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
        
        print(f"🔐 Created LLM execution role with secrets and DynamoDB permissions")

    def _create_llm_functions(self):
        """Create Lambda functions for each LLM provider with long content support"""
        
        # Import the ARM64 proxy layer directly here to ensure correct layer is used
        arm_proxy_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "LLMProxyExtensionLayerARM64Direct",
            layer_version_arn=self.proxy_layer_arm_arn
        )
        
        # Common Lambda function configuration (extending parent config)
        common_config = {
            "runtime": _lambda.Runtime.PYTHON_3_11,
            "timeout": Duration.seconds(120),  # Increased timeout for content processing
            "memory_size": 512,  # Increased memory for content processing
            "layers": [self.llm_layer, arm_proxy_layer],  # Explicitly use ARM layer
            "architecture": _lambda.Architecture.ARM_64,
            "log_group": self.log_group,
            "role": self.llm_execution_role,
            "tracing": _lambda.Tracing.ACTIVE,
            "environment": {
                "ENVIRONMENT": self.env_name,
                "POWERTOOLS_SERVICE_NAME": "shared-llm-long-content",
                "POWERTOOLS_LOG_LEVEL": "INFO",
                # Required for Lambda Runtime API Proxy to work
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
                # Configuration for content transformation
                "AGENT_CONTEXT_TABLE": self.content_table_name,
                "MAX_CONTENT_SIZE": str(self.max_content_size),
                # Optional: Enable debug logging
                "LRAP_DEBUG": "false"  # Set to "true" for debugging
            }
        }

        # Claude (Anthropic) Lambda function with long content support
        self.claude_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedClaudeLambdaWithLongContent",
            function_name=f"shared-claude-llm-long-content-{self.env_name}",
            description="Shared Claude (Anthropic) LLM function with long content support",
            entry="lambda/call_llm/functions/anthropic_llm",
            index="claude_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # OpenAI Lambda function with long content support
        self.openai_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedOpenAILambdaWithLongContent",
            function_name=f"shared-openai-llm-long-content-{self.env_name}",
            description="Shared OpenAI LLM function with long content support",
            entry="lambda/call_llm/functions/openai_llm",
            index="openai_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # Gemini Lambda function with long content support
        self.gemini_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedGeminiLambdaWithLongContent",
            function_name=f"shared-gemini-llm-long-content-{self.env_name}",
            description="Shared Gemini LLM function with long content support",
            entry="lambda/call_llm/functions/gemini_llm",
            index="gemini_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # Bedrock Lambda function with long content support
        self.bedrock_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedBedrockLambdaWithLongContent",
            function_name=f"shared-bedrock-llm-long-content-{self.env_name}",
            description="Shared Bedrock LLM function with long content support",
            entry="lambda/call_llm/functions/bedrock_llm",
            index="bedrock_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # DeepSeek Lambda function with long content support
        self.deepseek_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedDeepSeekLambdaWithLongContent",
            function_name=f"shared-deepseek-llm-long-content-{self.env_name}",
            description="Shared DeepSeek LLM function with long content support",
            entry="lambda/call_llm/functions/openai_llm",
            index="deepseek_lambda.py",
            handler="lambda_handler",
            **common_config
        )
        
        # Store function names for external reference (e.g., monitoring)
        self.claude_function_name = f"shared-claude-llm-long-content-{self.env_name}"
        self.openai_function_name = f"shared-openai-llm-long-content-{self.env_name}"
        self.gemini_function_name = f"shared-gemini-llm-long-content-{self.env_name}"
        self.bedrock_function_name = f"shared-bedrock-llm-long-content-{self.env_name}"
        self.deepseek_function_name = f"shared-deepseek-llm-long-content-{self.env_name}"


    def _create_stack_exports(self):
        """Create CloudFormation outputs with long content naming convention"""
        
        # Export Lambda function ARNs with long content naming
        CfnOutput(
            self, 
            "ClaudeLambdaWithLongContentArn",
            value=self.claude_lambda.function_arn,
            export_name=f"SharedClaudeLambdaWithLongContentArn-{self.env_name}",
            description="ARN of the shared Claude Lambda function with long content support"
        )

        CfnOutput(
            self, 
            "OpenAILambdaWithLongContentArn",
            value=self.openai_lambda.function_arn,
            export_name=f"SharedOpenAILambdaWithLongContentArn-{self.env_name}",
            description="ARN of the shared OpenAI Lambda function with long content support"
        )

        CfnOutput(
            self, 
            "GeminiLambdaWithLongContentArn",
            value=self.gemini_lambda.function_arn,
            export_name=f"SharedGeminiLambdaWithLongContentArn-{self.env_name}",
            description="ARN of the shared Gemini Lambda function with long content support"
        )

        CfnOutput(
            self, 
            "BedrockLambdaWithLongContentArn",
            value=self.bedrock_lambda.function_arn,
            export_name=f"SharedBedrockLambdaWithLongContentArn-{self.env_name}",
            description="ARN of the shared Bedrock Lambda function with long content support"
        )

        CfnOutput(
            self, 
            "DeepSeekLambdaWithLongContentArn",
            value=self.deepseek_lambda.function_arn,
            export_name=f"SharedDeepSeekLambdaWithLongContentArn-{self.env_name}",
            description="ARN of the shared DeepSeek Lambda function with long content support"
        )

        # Export shared resources (same as parent)
        CfnOutput(
            self, 
            "LLMSecretArn",
            value=self.llm_secret.secret_arn,
            export_name=f"SharedLLMSecretWithLongContentArn-{self.env_name}",
            description="ARN of the shared LLM secrets for long content stack"
        )

        CfnOutput(
            self, 
            "LLMLayerArn",
            value=self.llm_layer.layer_version_arn,
            export_name=f"SharedLLMLayerWithLongContentArn-{self.env_name}",
            description="ARN of the shared LLM layer for long content stack"
        )

        CfnOutput(
            self, 
            "LLMLogGroupName",
            value=self.log_group.log_group_name,
            export_name=f"SharedLLMLogGroupWithLongContentName-{self.env_name}",
            description="Name of the shared LLM log group for long content stack"
        )
        
        CfnOutput(
            self, 
            "LLMLogGroupArn",
            value=self.log_group.log_group_arn,
            export_name=f"SharedLLMLogGroupWithLongContentArn-{self.env_name}",
            description="ARN of the shared LLM log group for long content agents"
        )

        # Export content table information for convenience
        CfnOutput(
            self, 
            "ContentTableName",
            value=self.content_table_name,
            export_name=f"LLMContentTableName-{self.env_name}",
            description="DynamoDB table name for LLM long content storage"
        )

        CfnOutput(
            self, 
            "ContentTableArn",
            value=self.content_table_arn,
            export_name=f"LLMContentTableArn-{self.env_name}",
            description="DynamoDB table ARN for LLM long content storage"
        )