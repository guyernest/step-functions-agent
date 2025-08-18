from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    Fn,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import os


class SharedLongContentInfrastructureStack(Stack):
    """
    Shared infrastructure for long content support
    
    This stack provides:
    - DynamoDB table for content storage with TTL
    - Lambda layer for Runtime API Proxy extension
    - Shared configuration and exports
    
    IMPORTANT: This is an optional stack for agents that need to handle large content.
    Most agents should use the standard infrastructure stack instead.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create DynamoDB table for content storage
        self._create_content_storage_table()
        
        # Create Lambda Runtime API Proxy layers
        self._create_proxy_extension_layers()
        
        # Export key values for other stacks
        self._create_outputs()
        
        print(f"✅ Created shared long content infrastructure for {env_name} environment")
    
    def _create_content_storage_table(self):
        """Create DynamoDB table for storing large content"""
        
        self.content_table = dynamodb.Table(
            self,
            "AgentContentTable",
            table_name=f"AgentContext-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            # Enable TTL for automatic cleanup of old content
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  # For monitoring/debugging
            point_in_time_recovery=True  # For production safety
        )
        
        # Add global secondary index for querying by timestamp (optional, for debugging)
        self.content_table.add_global_secondary_index(
            index_name="timestamp-index",
            partition_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.KEYS_ONLY
        )
        
        print(f"📊 Created DynamoDB table: {self.content_table.table_name}")
    
    def _create_proxy_extension_layers(self):
        """Create Lambda Runtime API Proxy layers"""
        
        # Check if pre-built extension zip files exist
        extension_dir = "lambda/extensions/long-content"
        x86_zip_path = os.path.join(extension_dir, "extension-x86.zip")
        arm_zip_path = os.path.join(extension_dir, "extension-arm.zip")
        
        # Create x86_64 layer if zip exists
        if os.path.exists(x86_zip_path):
            self.proxy_layer_x86 = _lambda.LayerVersion(
                self,
                "ProxyLayerX86",
                code=_lambda.Code.from_asset(x86_zip_path),
                compatible_architectures=[_lambda.Architecture.X86_64],
                description="Lambda Runtime API Proxy extension for x86_64",
                layer_version_name=f"lambda-runtime-api-proxy-x86-{self.env_name}",
                removal_policy=RemovalPolicy.DESTROY
            )
            self.proxy_layer_x86_arn = self.proxy_layer_x86.layer_version_arn
            print(f"🔧 Created x86_64 Lambda Runtime API Proxy layer")
        else:
            print(f"⚠️  Warning: x86_64 extension zip not found at {x86_zip_path}")
            self.proxy_layer_x86_arn = ""
        
        # Create ARM64 layer if zip exists  
        if os.path.exists(arm_zip_path):
            self.proxy_layer_arm = _lambda.LayerVersion(
                self,
                "ProxyLayerArm",
                code=_lambda.Code.from_asset(arm_zip_path),
                compatible_architectures=[_lambda.Architecture.ARM_64],
                description="Lambda Runtime API Proxy extension for ARM64",
                layer_version_name=f"lambda-runtime-api-proxy-arm-{self.env_name}",
                removal_policy=RemovalPolicy.DESTROY
            )
            self.proxy_layer_arm_arn = self.proxy_layer_arm.layer_version_arn
            print(f"🔧 Created ARM64 Lambda Runtime API Proxy layer")
        else:
            print(f"⚠️  Warning: ARM64 extension zip not found at {arm_zip_path}")
            self.proxy_layer_arm_arn = ""
        
        print(f"✅ Created Lambda Runtime API Proxy layers for {self.env_name}")
    
    def _create_outputs(self):
        """Create CloudFormation outputs for other stacks to use"""
        
        # Export content table name
        CfnOutput(
            self,
            "ContentTableName",
            value=self.content_table.table_name,
            export_name=NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name),
            description="DynamoDB table name for long content storage"
        )
        
        # Export content table ARN
        CfnOutput(
            self,
            "ContentTableArn",
            value=self.content_table.table_arn,
            export_name=NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name),
            description="DynamoDB table ARN for long content storage"
        )
        
        # Export proxy layer ARNs if they exist
        if hasattr(self, 'proxy_layer_x86_arn') and self.proxy_layer_x86_arn:
            CfnOutput(
                self,
                "ProxyLayerX86Arn",
                value=self.proxy_layer_x86_arn,
                export_name=NamingConventions.stack_export_name("ProxyLayerX86", "LongContent", self.env_name),
                description="Lambda Runtime API Proxy layer ARN for x86_64"
            )
        
        if hasattr(self, 'proxy_layer_arm_arn') and self.proxy_layer_arm_arn:
            CfnOutput(
                self,
                "ProxyLayerArmArn", 
                value=self.proxy_layer_arm_arn,
                export_name=NamingConventions.stack_export_name("ProxyLayerArm", "LongContent", self.env_name),
                description="Lambda Runtime API Proxy layer ARN for ARM64"
            )