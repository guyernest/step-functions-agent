from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    Fn,
    aws_dynamodb as dynamodb,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions


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
        
        # Import Lambda Runtime API Proxy layers from build stack
        self._import_proxy_extension_layers()
        
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
    
    def _import_proxy_extension_layers(self):
        """Import Lambda Runtime API Proxy layers from extension layer stack"""
        
        # Import proxy extension layer ARNs from layer stack
        self.proxy_layer_x86_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerX86", "ExtensionBuild", self.env_name)
        )
        
        self.proxy_layer_arm_arn = Fn.import_value(
            NamingConventions.stack_export_name("ProxyLayerArm", "ExtensionBuild", self.env_name)
        )
        
        print(f"🔧 Imported Lambda Runtime API Proxy layers for {self.env_name}")
    
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
        
        # Export proxy layer ARNs (re-export from build stack)
        CfnOutput(
            self,
            "ProxyLayerX86Arn",
            value=self.proxy_layer_x86_arn,
            export_name=NamingConventions.stack_export_name("ProxyLayerX86", "LongContent", self.env_name),
            description="Lambda Runtime API Proxy layer ARN for x86_64"
        )
        
        CfnOutput(
            self,
            "ProxyLayerArmArn", 
            value=self.proxy_layer_arm_arn,
            export_name=NamingConventions.stack_export_name("ProxyLayerArm", "LongContent", self.env_name),
            description="Lambda Runtime API Proxy layer ARN for ARM64"
        )