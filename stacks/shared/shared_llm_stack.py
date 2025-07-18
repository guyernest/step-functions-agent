from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    SecretValue,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    RemovalPolicy
)
from constructs import Construct
import json
import os
from pathlib import Path
from dotenv import load_dotenv


class SharedLLMStack(Stack):
    """
    Shared LLM Stack - Centralized LLM provider integrations
    
    This stack creates and manages all LLM Lambda functions that can be reused
    across multiple agent stacks. It provides:
    - Centralized LLM API key management
    - Shared Lambda functions for each LLM provider
    - Stack exports for agent stacks to reference
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create centralized LLM secrets
        self._create_llm_secrets()
        
        # Create shared LLM Lambda layer
        self._create_llm_layer()
        
        # Create shared log group
        self._create_log_group()
        
        # Create shared IAM role
        self._create_llm_execution_role()
        
        # Create LLM Lambda functions
        self._create_llm_functions()
        
        # Create stack exports
        self._create_stack_exports()

    def _create_llm_secrets(self):
        """Create centralized LLM secrets using Lambda Powertools pattern"""
        # Load API keys from .env file if it exists
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Create secret with JSON structure for all LLM API keys
        # Use environment variables if available, otherwise use placeholders
        secret_value = {
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"), 
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here"),
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key-here")
        }
        
        # Check if we have real API keys or just placeholders
        has_real_keys = any(key in secret_value["ANTHROPIC_API_KEY"] for key in ["sk-ant-", "claude-"])
        
        if has_real_keys:
            # Use the real API keys from .env file
            # Convert string values to SecretValue objects
            secret_object_value = {
                key: SecretValue.unsafe_plain_text(value)
                for key, value in secret_value.items()
            }
            
            self.llm_secret = secretsmanager.Secret(
                self, 
                "LLMSecrets",
                secret_name=f"/ai-agent/llm-secrets/{self.env_name}",
                description=f"Centralized LLM API keys for {self.env_name} environment",
                secret_object_value=secret_object_value,
                removal_policy=RemovalPolicy.DESTROY  # TODO: Change for production
            )
        else:
            # Use the template with placeholders
            self.llm_secret = secretsmanager.Secret(
                self, 
                "LLMSecrets",
                secret_name=f"/ai-agent/llm-secrets/{self.env_name}",
                description=f"Centralized LLM API keys for {self.env_name} environment",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template=json.dumps(secret_value),
                    generate_string_key="placeholder",
                    exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\^"
                ),
                removal_policy=RemovalPolicy.DESTROY  # TODO: Change for production
            )

    def _create_llm_layer(self):
        """Create shared LLM Lambda layer"""
        self.llm_layer = _lambda_python.PythonLayerVersion(
            self, 
            "SharedLLMLayerV9",  # Fix pydantic_core ARM64 compatibility
            entry="lambda/call_llm/lambda_layer/python",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            description="Shared layer for LLM Lambda functions with common utilities - ARM64 V4",
        )

    def _create_log_group(self):
        """Create shared log group for all LLM functions"""
        self.log_group = logs.LogGroup(
            self, 
            "SharedLLMLogGroup",
            log_group_name=f"/aws/lambda/shared-llm-refactored-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_llm_execution_role(self):
        """Create shared IAM role for all LLM Lambda functions"""
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

        # Grant access to the centralized LLM secrets
        self.llm_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.llm_secret.secret_arn
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

    def _create_llm_functions(self):
        """Create Lambda functions for each LLM provider"""
        
        # Common Lambda function configuration
        common_config = {
            "runtime": _lambda.Runtime.PYTHON_3_11,
            "timeout": Duration.seconds(90),
            "memory_size": 256,
            "layers": [self.llm_layer],
            "architecture": _lambda.Architecture.ARM_64,
            "log_group": self.log_group,
            "role": self.llm_execution_role,
            "tracing": _lambda.Tracing.ACTIVE,
            "environment": {
                "ENVIRONMENT": self.env_name,
                # The functions will use Lambda Powertools to access secrets
                "POWERTOOLS_SERVICE_NAME": "shared-llm",
                "POWERTOOLS_LOG_LEVEL": "INFO"
            }
        }

        # Claude (Anthropic) Lambda function
        self.claude_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedClaudeLambda",
            function_name=f"shared-claude-llm-{self.env_name}",
            description="Shared Claude (Anthropic) LLM function",
            entry="lambda/call_llm/functions/anthropic_llm",
            index="claude_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # OpenAI Lambda function
        self.openai_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedOpenAILambda",
            function_name=f"shared-openai-llm-{self.env_name}",
            description="Shared OpenAI LLM function",
            entry="lambda/call_llm/functions/openai_llm",
            index="openai_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # Gemini Lambda function
        self.gemini_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedGeminiLambda",
            function_name=f"shared-gemini-llm-{self.env_name}",
            description="Shared Gemini LLM function",
            entry="lambda/call_llm/functions/gemini_llm",
            index="gemini_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # Bedrock Lambda function
        self.bedrock_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedBedrockLambda",
            function_name=f"shared-bedrock-llm-{self.env_name}",
            description="Shared Bedrock LLM function",
            entry="lambda/call_llm/functions/bedrock_llm",
            index="bedrock_lambda.py",
            handler="lambda_handler",
            **common_config
        )

        # DeepSeek Lambda function
        self.deepseek_lambda = _lambda_python.PythonFunction(
            self, 
            "SharedDeepSeekLambda",
            function_name=f"shared-deepseek-llm-{self.env_name}",
            description="Shared DeepSeek LLM function",
            entry="lambda/call_llm/functions/openai_llm",
            index="deepseek_lambda.py",
            handler="lambda_handler",
            **common_config
        )

    def _create_stack_exports(self):
        """Create CloudFormation outputs for agent stacks to import"""
        
        # Export Lambda function ARNs
        CfnOutput(
            self, 
            "ClaudeLambdaArn",
            value=self.claude_lambda.function_arn,
            export_name=f"SharedClaudeLambdaArn-{self.env_name}",
            description="ARN of the shared Claude Lambda function"
        )

        CfnOutput(
            self, 
            "OpenAILambdaArn",
            value=self.openai_lambda.function_arn,
            export_name=f"SharedOpenAILambdaArn-{self.env_name}",
            description="ARN of the shared OpenAI Lambda function"
        )

        CfnOutput(
            self, 
            "GeminiLambdaArn",
            value=self.gemini_lambda.function_arn,
            export_name=f"SharedGeminiLambdaArn-{self.env_name}",
            description="ARN of the shared Gemini Lambda function"
        )

        CfnOutput(
            self, 
            "BedrockLambdaArn",
            value=self.bedrock_lambda.function_arn,
            export_name=f"SharedBedrockLambdaArn-{self.env_name}",
            description="ARN of the shared Bedrock Lambda function"
        )

        CfnOutput(
            self, 
            "DeepSeekLambdaArn",
            value=self.deepseek_lambda.function_arn,
            export_name=f"SharedDeepSeekLambdaArn-{self.env_name}",
            description="ARN of the shared DeepSeek Lambda function"
        )

        # Export LLM secret ARN for tools that need LLM access
        CfnOutput(
            self, 
            "LLMSecretArn",
            value=self.llm_secret.secret_arn,
            export_name=f"SharedLLMSecretArn-{self.env_name}",
            description="ARN of the shared LLM secrets"
        )

        # Export layer ARN for tools that need LLM utilities
        CfnOutput(
            self, 
            "LLMLayerArn",
            value=self.llm_layer.layer_version_arn,
            export_name=f"SharedLLMLayerArn-{self.env_name}",
            description="ARN of the shared LLM layer"
        )

        # Export log group name and ARN for centralized logging
        CfnOutput(
            self, 
            "LLMLogGroupName",
            value=self.log_group.log_group_name,
            export_name=f"SharedLLMLogGroupName-{self.env_name}",
            description="Name of the shared LLM log group"
        )
        
        CfnOutput(
            self, 
            "LLMLogGroupArn",
            value=self.log_group.log_group_arn,
            export_name=f"SharedLLMLogGroupArn-{self.env_name}",
            description="ARN of the shared LLM log group for agent stacks"
        )