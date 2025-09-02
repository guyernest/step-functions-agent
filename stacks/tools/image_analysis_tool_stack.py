from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    SecretValue
)

try:
    from aws_cdk import aws_lambda_python_alpha as _lambda_python
except ImportError:
    _lambda_python = None

from constructs import Construct
from .base_tool_construct import MultiToolConstruct
import os
import json
from pathlib import Path


class ImageAnalysisToolStack(Stack):
    """
    Image Analysis Tools Stack - AI-powered vision and multimodal analysis
    
    This stack deploys advanced image analysis capabilities:
    - Google Gemini multimodal AI for natural language image queries
    - S3 image processing and retrieval
    - Batch image analysis and comparison
    - Computer vision and object detection
    - OCR and text extraction from images
    - Visual question answering
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create tool-specific secrets
        self._create_gemini_secret()
        
        # Deploy Python image analysis tool
        self._create_image_analysis_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_gemini_secret(self):
        """Create secret for Gemini API"""
        
        env_file_path = ".env.gemini"
        secret_value = {"GEMINI_API_KEY": "REPLACE_WITH_ACTUAL_API_KEY"}
        
        if os.path.exists(env_file_path):
            try:
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            secret_value[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not read {env_file_path}: {e}")
        
        self.gemini_secret = secretsmanager.Secret(
            self, 
            "GeminiApiSecrets",
            secret_name=f"/ai-agent/tools/image-analysis/{self.env_name}",
            description=f"Gemini API keys for image analysis in {self.env_name} environment",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_value),
                generate_string_key="placeholder",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/@\""
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_image_analysis_tool(self):
        """Create Python Lambda function for image analysis"""
        
        # Create execution role for image analysis Lambda
        image_lambda_role = iam.Role(
            self,
            "ImageAnalysisLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to S3 for image retrieval
        image_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    "arn:aws:s3:::*/*",
                    "arn:aws:s3:::*"
                ]
            )
        )
        
        # Grant access to Gemini API secrets
        image_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[self.gemini_secret.secret_arn]
            )
        )
        
        # Create Python Lambda function for image analysis
        if _lambda_python is not None:
            self.image_analysis_lambda = _lambda_python.PythonFunction(
                self,
                "ImageAnalysisLambda",
                function_name=f"tool-image-analysis-{self.env_name}",
                description="AI-powered image analysis using Google Gemini multimodal capabilities with natural language queries",
                entry="lambda/tools/image-analysis",
                index="index.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                timeout=Duration.minutes(5),
                memory_size=1024,  # More memory for image processing
                role=image_lambda_role
            )
        else:
            self.image_analysis_lambda = _lambda.Function(
                self,
                "ImageAnalysisLambda",
                function_name=f"tool-image-analysis-{self.env_name}",
                description="AI-powered image analysis using Google Gemini multimodal capabilities with natural language queries",
                runtime=_lambda.Runtime.PYTHON_3_11,
                architecture=_lambda.Architecture.ARM_64,
                code=_lambda.Code.from_asset("lambda/tools/image-analysis"),
                handler="index.lambda_handler",
                timeout=Duration.minutes(5),
                memory_size=1024,  # More memory for image processing
                role=image_lambda_role
            )
        
        self.image_analysis_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "ImageAnalysisLambdaArn",
            value=self.image_analysis_lambda.function_arn,
            export_name=f"ImageAnalysisLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self,
            "GeminiSecretArn",
            value=self.gemini_secret.secret_arn,
            description="ARN of Gemini API secret - update with actual API key"
        )

    def _register_tools_using_base_construct(self):
        """Register all image analysis tools using the BaseToolConstruct pattern"""
        
        # Load tool names from Lambda's single source of truth
        tool_names_file = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'image-analysis' / 'tool-names.json'
        with open(tool_names_file, 'r') as f:
            tool_names = json.load(f)
        
        print(f"✅ ImageAnalysisToolStack: Loaded {len(tool_names)} tool names from tool-names.json: {tool_names}")
        
        # Define image analysis tool specifications with self-contained definitions
        image_tools = [
            {
                "tool_name": "analyze_images",  # Corrected name to match Lambda
                "description": "Analyze images using AI with natural language queries and multimodal understanding",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image_locations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "bucket": {"type": "string", "description": "S3 bucket name"},
                                    "key": {"type": "string", "description": "S3 object key"}
                                },
                                "required": ["bucket", "key"]
                            },
                            "description": "List of S3 image locations"
                        },
                        "query": {"type": "string", "description": "Natural language query about the images"}
                    },
                    "required": ["image_locations", "query"]
                },
                "language": "python",
                "tags": ["ai", "vision", "gemini", "multimodal"],
                "author": "system"
            }
        ]
        
        # Validate that all tool specs match declared names
        spec_names = {spec["tool_name"] for spec in image_tools}
        declared_names = set(tool_names)
        
        if spec_names != declared_names:
            raise ValueError(f"Tool name mismatch! Specs: {spec_names}, Declared: {declared_names}")
        
        # Use MultiToolConstruct to register image analysis tools
        MultiToolConstruct(
            self,
            "ImageAnalysisToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": image_tools,
                    "lambda_function": self.image_analysis_lambda
                }
            ],
            env_name=self.env_name
        )