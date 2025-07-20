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
from constructs import Construct
from .base_tool_construct import MultiToolConstruct
from ..shared.tool_definitions import SpecializedTools
import os
import json


class BookRecommendationToolStack(Stack):
    """
    Book Recommendation Tools Stack - Literary discovery and bestseller tracking
    
    This stack deploys book recommendation capabilities:
    - New York Times Books API integration
    - Bestseller list access and filtering
    - Category-based book discovery
    - Literary trend analysis
    - Publication metadata retrieval
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create tool-specific secrets
        self._create_books_api_secret()
        
        # Deploy TypeScript book recommendation tool
        self._create_book_recommendation_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_books_api_secret(self):
        """Create secret for NYT Books API"""
        
        env_file_path = ".env.books"
        secret_value = {"NYT_API_KEY": "REPLACE_WITH_ACTUAL_API_KEY"}
        
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
        
        self.books_api_secret = secretsmanager.Secret(
            self, 
            "BooksApiSecrets",
            secret_name=f"/ai-agent/tools/books-api/{self.env_name}",
            description=f"NYT Books API secrets for {self.env_name} environment",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_value),
                generate_string_key="placeholder",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\^"
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_book_recommendation_tool(self):
        """Create TypeScript Lambda function for book recommendations"""
        
        # Create execution role for books Lambda
        books_lambda_role = iam.Role(
            self,
            "BookRecommendationLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to books API secrets
        books_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[self.books_api_secret.secret_arn]
            )
        )
        
        # Create TypeScript Lambda function for book recommendations
        self.book_recommendation_lambda = _lambda.Function(
            self,
            "BookRecommendationLambda",
            function_name=f"tool-book-recommendations-{self.env_name}",
            description="Book discovery and recommendations using New York Times Books API with bestseller tracking",
            runtime=_lambda.Runtime.NODEJS_18_X,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/books-recommender/dist"),
            handler="index.handler",
            timeout=Duration.seconds(60),
            memory_size=256,
            role=books_lambda_role,
            environment={
                "NYT_API_SECRET_NAME": self.books_api_secret.secret_name,
                "NODE_ENV": "production"
            }
        )
        
        self.book_recommendation_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "BookRecommendationLambdaArn",
            value=self.book_recommendation_lambda.function_arn,
            export_name=f"BookRecommendationLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self,
            "BooksApiSecretArn",
            value=self.books_api_secret.secret_arn,
            description="ARN of the NYT Books API secret - update with actual API key"
        )

    def _register_tools_using_base_construct(self):
        """Register all book recommendation tools using the BaseToolConstruct pattern"""
        
        # Get tool definition from centralized definitions
        book_tool = SpecializedTools.BOOK_RECOMMENDATION
        
        # Define book recommendation tool specifications
        book_tools = [
            {
                "tool_name": book_tool.tool_name,
                "description": book_tool.description,
                "input_schema": book_tool.input_schema,
                "language": book_tool.language.value,
                "tags": book_tool.tags,
                "author": book_tool.author
            }
        ]
        
        # Use MultiToolConstruct to register book recommendation tools
        MultiToolConstruct(
            self,
            "BookRecommendationToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": book_tools,
                    "lambda_function": self.book_recommendation_lambda
                }
            ],
            env_name=self.env_name
        )