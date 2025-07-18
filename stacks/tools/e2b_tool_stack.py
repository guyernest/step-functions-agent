from aws_cdk import (
    Duration,
    Stack,
    Fn,
    CfnOutput,
    SecretValue,
    CustomResource,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    custom_resources as cr,
    RemovalPolicy
)
from constructs import Construct
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
        
        # Create tool-specific secrets
        self._create_execute_code_secrets()
        
        # Create tool Lambda
        self._create_execute_code_lambda()
        
        # Register tools in DynamoDB registry
        self._register_tools_in_registry()
        
        # Create stack exports
        self.create_stack_exports()

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

        # Grant access to execute_code secrets
        self.execute_code_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.execute_code_secret.secret_arn
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

        # Grant access to S3 for image uploads (if needed)
        self.execute_code_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:PutObjectAcl"
                ],
                resources=["arn:aws:s3:::*/*"]
            )
        )

        # Create Lambda function
        self.execute_code_lambda = _lambda_python.PythonFunction(
            self,
            "ExecuteCodeLambda",
            function_name=f"execute-code-tool-{self.env_name}",
            description="Execute code tool using E2B sandbox",
            entry="lambda/tools/execute_code",
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
                "POWERTOOLS_LOG_LEVEL": "INFO"
            },
            layers=[
                _lambda.LayerVersion.from_layer_version_arn(
                    self, "SharedLLMLayer", self.shared_llm_layer_arn
                )
            ]
        )
        
        # Apply removal policy to help with stack destruction
        self.execute_code_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

    def _register_tools_in_registry(self):
        """Register tools in DynamoDB registry"""
        
        # Tool registration data
        tools_data = [
            {
                "tool_id": "execute_python",
                "tool_name": "execute_python",
                "description": "Execute Python code in a secure sandbox environment using E2B",
                "lambda_function_arn": self.execute_code_lambda.function_arn,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        }
                    },
                    "required": ["code"]
                },
                "category": "code_execution",
                "created_by": "E2BToolStack"
            }
        ]
        
        # Create custom resource handler for tool registration
        registry_handler = _lambda.Function(
            self,
            "ToolRegistryHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=_lambda.Code.from_inline(f"""
import boto3
import json

def handler(event, context):
    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('{self.tool_registry_table_name}')
            
            # Get tool data from properties
            tool_data = event['ResourceProperties']['tool_data']
            
            # Convert input_schema to JSON string if it's a dict
            if 'input_schema' in tool_data and isinstance(tool_data['input_schema'], dict):
                tool_data['input_schema'] = json.dumps(tool_data['input_schema'])
            
            table.put_item(Item=tool_data)
            
            return {{
                'PhysicalResourceId': tool_data['tool_id'],
                'Status': 'SUCCESS'
            }}
        elif event['RequestType'] == 'Delete':
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('{self.tool_registry_table_name}')
            
            # Get tool_data from properties
            tool_data = event['ResourceProperties']['tool_data']
            
            table.delete_item(Key={{'tool_name': tool_data['tool_name']}})
            
            return {{
                'PhysicalResourceId': tool_data['tool_name'],
                'Status': 'SUCCESS'
            }}
    except Exception as e:
        print(f"Error: {{e}}")
        return {{
            'PhysicalResourceId': 'error',
            'Status': 'FAILED',
            'Reason': str(e)
        }}
"""),
            initial_policy=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:DeleteItem"
                    ],
                    resources=[self.tool_registry_table_arn]
                )
            ]
        )
        
        # Create provider for custom resource
        provider = cr.Provider(
            self,
            "ToolRegistryProvider",
            on_event_handler=registry_handler
        )
        
        # Create custom resource to register tools
        for i, tool_data in enumerate(tools_data):
            CustomResource(
                self,
                f"RegisterTool{i}",
                service_token=provider.service_token,
                properties={
                    "tool_data": tool_data
                }
            )

    def create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export Lambda function ARN
        CfnOutput(
            self, 
            "ExecuteCodeLambdaArn",
            value=self.execute_code_lambda.function_arn,
            export_name=f"ExecuteCodeLambdaArn-{self.env_name}",
            description="ARN of the execute code Lambda function"
        )
        
        # Export execute_code secret ARN
        CfnOutput(
            self, 
            "ExecuteCodeSecretArn",
            value=self.execute_code_secret.secret_arn,
            export_name=f"ExecuteCodeSecretArn-{self.env_name}",
            description="ARN of the execute code secrets"
        )