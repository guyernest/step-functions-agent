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
import os
import json


class ClusteringToolStack(Stack):
    """
    Clustering Tools Stack - High-performance data analysis tools
    
    This stack deploys clustering and semantic search capabilities:
    - HDBSCAN clustering tool using Rust for performance
    - Semantic search with Qdrant vector database
    - Cohere embeddings integration
    - S3 data processing capabilities
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create tool-specific secrets for semantic search
        self._create_semantic_search_secret()
        
        # Deploy HDBSCAN clustering tool
        self._create_hdbscan_clustering_tool()
        
        # Deploy semantic search tool
        self._create_semantic_search_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_semantic_search_secret(self):
        """Create secret for semantic search tool (Qdrant and Cohere API)"""
        
        env_file_path = ".env.semantic-search"
        secret_value = {
            "QDRANT_API_KEY": "REPLACE_WITH_ACTUAL_API_KEY",
            "QDRANT_URL": "https://your-cluster.qdrant.tech",
            "COHERE_API_KEY": "REPLACE_WITH_ACTUAL_API_KEY"
        }
        
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
        
        self.semantic_search_secret = secretsmanager.Secret(
            self, 
            "SemanticSearchSecrets",
            secret_name=f"/ai-agent/tools/semantic-search/{self.env_name}",
            description=f"Semantic search tool secrets (Qdrant and Cohere API) for {self.env_name} environment",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_value),
                generate_string_key="placeholder",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\^"
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_hdbscan_clustering_tool(self):
        """Create Rust Lambda function for HDBSCAN clustering"""
        
        # Create execution role for clustering Lambda
        clustering_lambda_role = iam.Role(
            self,
            "HDBSCANClusteringLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to S3 for reading vector data
        clustering_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    "arn:aws:s3:::*/*",  # Allow access to all S3 objects
                    "arn:aws:s3:::*"     # Allow bucket listing
                ]
            )
        )
        
        # Create Rust Lambda function for clustering
        self.hdbscan_clustering_lambda = _lambda.Function(
            self,
            "HDBSCANClusteringLambda",
            function_name=f"tool-hdbscan-clustering-{self.env_name}",
            description="High-performance HDBSCAN clustering using Rust implementation",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/rust-clustering/"),
            handler="main",
            timeout=Duration.minutes(15),  # Clustering can take time
            memory_size=1024,  # More memory for data processing
            role=clustering_lambda_role,
            environment={
                "RUST_LOG": "info"
            }
        )
        
        self.hdbscan_clustering_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "HDBSCANClusteringLambdaArn",
            value=self.hdbscan_clustering_lambda.function_arn,
            export_name=f"HDBSCANClusteringLambdaArn-{self.env_name}"
        )

    def _create_semantic_search_tool(self):
        """Create Rust Lambda function for semantic search"""
        
        # Create execution role for semantic search Lambda
        semantic_search_lambda_role = iam.Role(
            self,
            "SemanticSearchLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant access to semantic search secrets
        semantic_search_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[self.semantic_search_secret.secret_arn]
            )
        )
        
        # Create Rust Lambda function for semantic search
        self.semantic_search_lambda = _lambda.Function(
            self,
            "SemanticSearchLambda",
            function_name=f"tool-semantic-search-{self.env_name}",
            description="Semantic search using Rust, Qdrant vector database, and Cohere embeddings",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/SemanticSearchRust/"),
            handler="main",
            timeout=Duration.seconds(120),
            memory_size=512,
            role=semantic_search_lambda_role,
            environment={
                "RUST_LOG": "info"
            }
        )
        
        self.semantic_search_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "SemanticSearchLambdaArn",
            value=self.semantic_search_lambda.function_arn,
            export_name=f"SemanticSearchLambdaArn-{self.env_name}"
        )
        
        CfnOutput(
            self,
            "SemanticSearchSecretArn",
            value=self.semantic_search_secret.secret_arn,
            description="ARN of the semantic search secret - update with actual Qdrant and Cohere API keys"
        )

    def _register_tools_using_base_construct(self):
        """Register all clustering tools using the BaseToolConstruct pattern"""
        
        # Define clustering tool specifications with self-contained definitions
        clustering_tools = [
            {
                "tool_name": "hdbscan_clustering",
                "description": "Perform high-performance HDBSCAN clustering on data using Rust implementation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data_source": {"type": "string", "description": "S3 path to data file"},
                        "min_cluster_size": {"type": "integer", "description": "Minimum cluster size", "default": 5},
                        "min_samples": {"type": "integer", "description": "Minimum samples parameter", "default": 1},
                        "metric": {"type": "string", "description": "Distance metric", "default": "euclidean"}
                    },
                    "required": ["data_source"]
                },
                "language": "rust",
                "tags": ["clustering", "hdbscan", "rust"],
                "author": "system"
            }
        ]
        
        # Define semantic search tool specifications with self-contained definitions
        semantic_search_tools = [
            {
                "tool_name": "semantic_search",
                "description": "Perform semantic search using Qdrant vector database and Cohere embeddings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "collection_name": {"type": "string", "description": "Qdrant collection name"},
                        "limit": {"type": "integer", "description": "Number of results to return", "default": 10}
                    },
                    "required": ["query", "collection_name"]
                },
                "language": "rust",
                "tags": ["search", "semantic", "qdrant", "cohere"],
                "author": "system"
            }
        ]
        
        # Use MultiToolConstruct to register both tool groups
        MultiToolConstruct(
            self,
            "ClusteringToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": clustering_tools,
                    "lambda_function": self.hdbscan_clustering_lambda
                },
                {
                    "tool_specs": semantic_search_tools,
                    "lambda_function": self.semantic_search_lambda
                }
            ],
            env_name=self.env_name
        )