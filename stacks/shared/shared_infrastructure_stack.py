from aws_cdk import (
    Stack,
    CfnOutput,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct
from .naming_conventions import NamingConventions


class SharedInfrastructureStack(Stack):
    """
    Shared Infrastructure Stack - Core infrastructure components
    
    This stack creates and manages shared infrastructure components that are
    used across multiple stacks:
    - DynamoDB Tool Registry
    - Common IAM policies and roles
    - Shared monitoring and logging resources
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Create DynamoDB tool registry
        self._create_tool_registry()
        
        # Create stack exports
        self._create_stack_exports()

    def _create_tool_registry(self):
        """Create DynamoDB table for tool registry"""
        table_name = NamingConventions.tool_registry_table_name(self.env_name)
        
        self.tool_registry_table = dynamodb.Table(
            self,
            "ToolRegistry",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="tool_name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # TODO: Change for production
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Global Secondary Index: Tools by Language
        self.tool_registry_table.add_global_secondary_index(
            index_name="ToolsByLanguage",
            partition_key=dynamodb.Attribute(
                name="language",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="tool_name",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Global Secondary Index: Tools by Status
        self.tool_registry_table.add_global_secondary_index(
            index_name="ToolsByStatus",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Global Secondary Index: Tools by Author
        self.tool_registry_table.add_global_secondary_index(
            index_name="ToolsByAuthor",
            partition_key=dynamodb.Attribute(
                name="author",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export tool registry table name
        CfnOutput(
            self,
            "ToolRegistryTableName",
            value=self.tool_registry_table.table_name,
            export_name=NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name),
            description="Name of the tool registry DynamoDB table"
        )

        # Export tool registry table ARN
        CfnOutput(
            self,
            "ToolRegistryTableArn",
            value=self.tool_registry_table.table_arn,
            export_name=NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name),
            description="ARN of the tool registry DynamoDB table"
        )

        # Export tool registry table stream ARN
        CfnOutput(
            self,
            "ToolRegistryTableStreamArn",
            value=self.tool_registry_table.table_stream_arn,
            export_name=NamingConventions.stack_export_name("TableStreamArn", "ToolRegistry", self.env_name),
            description="Stream ARN of the tool registry DynamoDB table"
        )

    def get_tool_registry_table(self) -> dynamodb.Table:
        """Get the tool registry table for use in other stacks"""
        return self.tool_registry_table