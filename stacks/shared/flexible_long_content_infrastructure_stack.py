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
from typing import Optional, Dict, Any


class FlexibleLongContentInfrastructureStack(Stack):
    """
    Flexible Long Content Infrastructure Stack
    
    This stack can operate in multiple modes:
    1. CREATE mode - Creates all resources from scratch
    2. IMPORT mode - Imports existing resources by name/ARN
    3. HYBRID mode - Creates some resources, imports others
    
    Configuration example:
    {
        "mode": "hybrid",
        "resources": {
            "content_table": "import",  # Use existing table
            "proxy_layers": "create",   # Create new layers
            "agent_registry": "import"  # Share existing registry
        },
        "import_values": {
            "content_table_name": "AgentContext-prod",
            "agent_registry_table_name": "tool-registry-prod"
        }
    }
    
    This pattern enables:
    - Adding long content support to existing environments
    - Sharing resources between multiple deployments
    - Gradual migration strategies
    - Testing new features without affecting production
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        env_name: str = "prod",
        deployment_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.deployment_config = deployment_config or {"mode": "create"}
        self.mode = self.deployment_config.get("mode", "create")
        self.resources = self.deployment_config.get("resources", {})
        self.import_values = self.deployment_config.get("import_values", {})
        
        print(f"🚀 Deploying long content infrastructure in {self.mode} mode for {env_name}")
        
        # Handle content storage table
        self._handle_content_storage_table()
        
        # Handle proxy extension layers
        self._handle_proxy_extension_layers()
        
        # Handle agent registry (if needed)
        self._handle_agent_registry()
        
        # Export key values for other stacks
        self._create_outputs()
        
        print(f"✅ Created flexible long content infrastructure for {env_name} environment")
    
    def _handle_content_storage_table(self):
        """Create or import DynamoDB table for content storage"""
        
        resource_mode = self.resources.get("content_table", "create" if self.mode == "create" else "import")
        
        if resource_mode == "create":
            self._create_content_storage_table()
        else:
            self._import_content_storage_table()
    
    def _create_content_storage_table(self):
        """Create new DynamoDB table for storing large content"""
        
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
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            point_in_time_recovery=True
        )
        
        # Add GSI for debugging
        self.content_table.add_global_secondary_index(
            index_name="timestamp-index",
            partition_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.KEYS_ONLY
        )
        
        self.content_table_name = self.content_table.table_name
        self.content_table_arn = self.content_table.table_arn
        
        print(f"📊 Created DynamoDB table: {self.content_table_name}")
    
    def _import_content_storage_table(self):
        """Import existing DynamoDB table"""
        
        if "content_table_name" in self.import_values:
            # Import by name
            table_name = self.import_values["content_table_name"]
            self.content_table = dynamodb.Table.from_table_name(
                self,
                "ImportedContentTable",
                table_name=table_name
            )
            self.content_table_name = table_name
            self.content_table_arn = self.content_table.table_arn
        else:
            # Import from CloudFormation export
            self.content_table_name = Fn.import_value(
                self.import_values.get("content_table_name_export", 
                    NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name))
            )
            self.content_table_arn = Fn.import_value(
                self.import_values.get("content_table_arn_export",
                    NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name))
            )
        
        print(f"📊 Imported existing DynamoDB table for content storage")
    
    def _handle_proxy_extension_layers(self):
        """Create or import Lambda Runtime API Proxy layers"""
        
        resource_mode = self.resources.get("proxy_layers", "create" if self.mode == "create" else "import")
        
        if resource_mode == "create":
            # Expect the LambdaExtensionLayerStack to create these
            print(f"🔧 Proxy layers will be created by LambdaExtensionLayerStack")
        else:
            self._import_proxy_extension_layers()
    
    def _import_proxy_extension_layers(self):
        """Import Lambda Runtime API Proxy layers from existing deployment"""
        
        if "proxy_layer_x86_arn" in self.import_values:
            # Direct ARN import
            self.proxy_layer_x86_arn = self.import_values["proxy_layer_x86_arn"]
            self.proxy_layer_arm_arn = self.import_values["proxy_layer_arm_arn"]
        else:
            # Import from CloudFormation exports
            self.proxy_layer_x86_arn = Fn.import_value(
                self.import_values.get("proxy_layer_x86_export",
                    NamingConventions.stack_export_name("ProxyLayerX86", "ExtensionBuild", self.env_name))
            )
            self.proxy_layer_arm_arn = Fn.import_value(
                self.import_values.get("proxy_layer_arm_export",
                    NamingConventions.stack_export_name("ProxyLayerArm", "ExtensionBuild", self.env_name))
            )
        
        print(f"🔧 Imported Lambda Runtime API Proxy layers")
    
    def _handle_agent_registry(self):
        """Optionally handle agent registry sharing"""
        
        if "agent_registry" not in self.resources:
            return
        
        resource_mode = self.resources.get("agent_registry", "none")
        
        if resource_mode == "import":
            self._import_agent_registry()
    
    def _import_agent_registry(self):
        """Import existing agent registry table"""
        
        if "agent_registry_table_name" in self.import_values:
            # Import by name
            self.agent_registry_table_name = self.import_values["agent_registry_table_name"]
            self.agent_registry_table = dynamodb.Table.from_table_name(
                self,
                "ImportedAgentRegistry",
                table_name=self.agent_registry_table_name
            )
            self.agent_registry_table_arn = self.agent_registry_table.table_arn
        else:
            # Import from CloudFormation exports
            self.agent_registry_table_name = Fn.import_value(
                NamingConventions.stack_export_name("Table", "AgentRegistry", self.env_name)
            )
            self.agent_registry_table_arn = Fn.import_value(
                NamingConventions.stack_export_name("TableArn", "AgentRegistry", self.env_name)
            )
        
        print(f"📋 Imported existing agent registry table")
    
    def _create_outputs(self):
        """Create CloudFormation outputs for other stacks to use"""
        
        # Always export content table info
        CfnOutput(
            self,
            "ContentTableName",
            value=self.content_table_name,
            export_name=NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name),
            description="DynamoDB table name for long content storage"
        )
        
        CfnOutput(
            self,
            "ContentTableArn",
            value=self.content_table_arn,
            export_name=NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name),
            description="DynamoDB table ARN for long content storage"
        )
        
        # Export proxy layer ARNs if we have them
        if hasattr(self, 'proxy_layer_x86_arn'):
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
        
        # Export agent registry info if imported
        if hasattr(self, 'agent_registry_table_name'):
            CfnOutput(
                self,
                "AgentRegistryTableName",
                value=self.agent_registry_table_name,
                export_name=NamingConventions.stack_export_name("AgentRegistryTable", "LongContent", self.env_name),
                description="Shared agent registry table name"
            )