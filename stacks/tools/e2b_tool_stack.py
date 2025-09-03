from aws_cdk import (
    Duration,
    Stack,
    Fn,
    CfnOutput,
    SecretValue,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_s3 as s3,
    RemovalPolicy
)
from constructs import Construct
from .base_tool_construct_batched import BatchedToolConstruct
from ..shared.naming_conventions import NamingConventions
import json
import os
from pathlib import Path
from dotenv import load_dotenv


class E2BToolStack(Stack):
    """
    E2B Tool Stack - Deploys the execute_code Lambda and registers the tool
    
    This stack demonstrates the tool deployment pattern with tool-specific secrets:
    - Deploys single Lambda with execute_code functionality
    - Creates tool-specific secrets from .env.execute_code
    - Registers execute_python tool in DynamoDB registry
    - Uses tool-specific IAM permissions
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared infrastructure
        self._import_shared_resources()
        
        # Create S3 bucket for code execution data
        self._create_s3_bucket()
        
        # Create tool-specific secrets
        self._create_execute_code_secrets()
        
        # Create tool Lambda
        self._create_execute_code_lambda()
        
        # Register tools in DynamoDB registry using BaseToolConstruct
        self._register_tools_using_base_construct()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import tool registry table name and ARN
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        
        # Import shared LLM layer ARN
        self.shared_llm_layer_arn = Fn.import_value(
            f"SharedLLMLayerArn-{self.env_name}"
        )

    def _create_s3_bucket(self):
        """Create S3 bucket for storing code execution outputs (charts, images, etc.)"""
        
        # Get AWS account ID and region for bucket naming
        account_id = self.account
        region = self.region
        
        # Create bucket with the specified naming template: execute-code-data-{account-id}-{region}
        bucket_name = f"execute-code-data-{account_id}-{region}"
        
        self.execute_code_bucket = s3.Bucket(
            self,
            "ExecuteCodeDataBucket",
            bucket_name=bucket_name,
            # Security settings
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            
            # Lifecycle management
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="delete-old-objects",
                    enabled=True,
                    expiration=Duration.days(30)  # Delete objects after 30 days
                )
            ],
            
            # Versioning and encryption
            versioned=False,  # No versioning needed for temporary charts
            encryption=s3.BucketEncryption.S3_MANAGED,
            
            # CORS for presigned URLs
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                    max_age=3600
                )
            ],
            
            # Cleanup policy
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

    def _create_execute_code_secrets(self):
        """Create execute_code tool secrets from .env.execute_code file"""
        # Load API keys from .env.execute_code file if it exists
        env_path = Path(__file__).parent.parent.parent / '.env.execute_code'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Create secret with JSON structure for execute_code tool API keys
        secret_value = {
            "E2B_API_KEY": os.getenv("E2B_API_KEY", "your-e2b-api-key-here")
        }
        
        # Check if we have real API keys or just placeholders
        has_real_keys = "e2b_" in secret_value["E2B_API_KEY"]
        
        if has_real_keys:
            # Use the real API keys from .env.execute_code file
            secret_object_value = {
                key: SecretValue.unsafe_plain_text(value)
                for key, value in secret_value.items()
            }
            
            self.execute_code_secret = secretsmanager.Secret(
                self, 
                "ExecuteCodeSecrets",
                secret_name=NamingConventions.tool_secret_path("execute-code", self.env_name),
                description=f"Execute code tool API keys for {self.env_name} environment",
                secret_object_value=secret_object_value,
                removal_policy=RemovalPolicy.DESTROY
            )
        else:
            # Use the template with placeholders
            self.execute_code_secret = secretsmanager.Secret(
                self, 
                "ExecuteCodeSecrets",
                secret_name=NamingConventions.tool_secret_path("execute-code", self.env_name),
                description=f"Execute code tool API keys for {self.env_name} environment",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template=json.dumps(secret_value),
                    generate_string_key="placeholder",
                    exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\^"
                ),
                removal_policy=RemovalPolicy.DESTROY
            )

    def _create_execute_code_lambda(self):
        """Create execute_code Lambda function"""
        
        # Create IAM role for execute_code Lambda
        self.execute_code_role = iam.Role(
            self,
            "ExecuteCodeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant access to both legacy and consolidated secrets
        self.execute_code_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.execute_code_secret.secret_arn,  # Legacy secret
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/tool-secrets/{self.env_name}*"  # Consolidated secret
                ]
            )
        )

        # Grant access to X-Ray tracing
        self.execute_code_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )

        # Grant access to the specific S3 bucket for code execution outputs
        self.execute_code_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:PutObjectAcl"
                ],
                resources=[
                    f"{self.execute_code_bucket.bucket_arn}/*"
                ]
            )
        )

        # Create Lambda function
        self.execute_code_lambda = _lambda_python.PythonFunction(
            self,
            "ExecuteCodeLambda",
            function_name=f"execute-code-tool-{self.env_name}",
            description="Execute code tool using E2B sandbox",
            entry="lambda/tools/execute-code",
            index="index.py",
            handler="lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(300),  # 5 minutes for code execution
            memory_size=512,
            architecture=_lambda.Architecture.ARM_64,
            role=self.execute_code_role,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "ENVIRONMENT": self.env_name,
                "POWERTOOLS_SERVICE_NAME": "execute-code-tool",
                "POWERTOOLS_LOG_LEVEL": "INFO",
                "IMAGE_BUCKET_NAME": self.execute_code_bucket.bucket_name,
                "CONSOLIDATED_SECRET_NAME": f"/ai-agent/tool-secrets/{self.env_name}"
            },
            layers=[
                _lambda.LayerVersion.from_layer_version_arn(
                    self, "SharedLLMLayer", self.shared_llm_layer_arn
                )
            ]
        )
        
        # Apply removal policy to help with stack destruction
        self.execute_code_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

    def _register_tools_using_base_construct(self):
        """Register code execution tools using BaseToolConstruct with self-contained definitions"""
        
        # Define tool specifications with self-contained definitions
        tool_specs = [
            {
                "tool_name": "execute_python",
                "description": "Execute Python code in a secure E2B sandbox environment",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"},
                        "timeout": {"type": "integer", "description": "Execution timeout in seconds", "default": 30}
                    },
                    "required": ["code"]
                },
                "language": "python",
                "tags": ["code", "execution", "e2b", "sandbox"],
                "author": "system",
                "lambda_arn": self.execute_code_lambda.function_arn,
                "lambda_function_name": self.execute_code_lambda.function_name
            }
        ]
        
        # Use BatchedToolConstruct for registration with secret requirements
        BatchedToolConstruct(
            self,
            "CodeExecutionTools",
            tool_specs=tool_specs,
            lambda_function=self.execute_code_lambda,
            env_name=self.env_name,
            secret_requirements={
                "execute-code": ["E2B_API_KEY"]
            }
        )

        # Store Lambda function reference for monitoring
        self.code_execution_lambda_function = self.execute_code_lambda
        
        # Create CloudFormation exports
        self._create_stack_exports()
    
    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export Execute Code Lambda ARN
        CfnOutput(
            self,
            "ExecuteCodeLambdaArn",
            value=self.execute_code_lambda.function_arn,
            export_name=f"ExecuteCodeLambdaArn-{self.env_name}",
            description="ARN of the Execute Code Lambda function"
        )
        
        # Export Execute Code S3 Bucket Name
        CfnOutput(
            self,
            "ExecuteCodeBucketName",
            value=self.execute_code_bucket.bucket_name,
            export_name=f"ExecuteCodeBucketName-{self.env_name}",
            description="Name of the S3 bucket for code execution outputs"
        )