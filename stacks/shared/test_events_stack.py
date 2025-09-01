"""
Test Events Registry Stack

This stack creates the DynamoDB table for storing test events
for agents, tools, and MCP servers.
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
    Tags
)
from constructs import Construct
from .naming_conventions import NamingConventions


class TestEventsStack(Stack):
    """
    Creates DynamoDB table for test events storage
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "prod",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        # Create Test Events table
        self.test_events_table = dynamodb.Table(
            self,
            "TestEventsTable",
            table_name=f"TestEvents-{env_name}",
            partition_key=dynamodb.Attribute(
                name="resource_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="id",  # Format: resource_id#test_name
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # Add GSI for querying by resource_id
        self.test_events_table.add_global_secondary_index(
            index_name="resource-index",
            partition_key=dynamodb.Attribute(
                name="resource_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="test_name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Add GSI for querying by tags
        self.test_events_table.add_global_secondary_index(
            index_name="tag-index",
            partition_key=dynamodb.Attribute(
                name="tag",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Create Test Results table for storing execution history
        self.test_results_table = dynamodb.Table(
            self,
            "TestResultsTable",
            table_name=f"TestResults-{env_name}",
            partition_key=dynamodb.Attribute(
                name="test_event_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="executed_at",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl"  # Auto-delete old results after 30 days
        )

        # Add GSI for querying by resource
        self.test_results_table.add_global_secondary_index(
            index_name="resource-results-index",
            partition_key=dynamodb.Attribute(
                name="resource_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="executed_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Tag all resources
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("Stack", "TestEvents")
        Tags.of(self).add("Purpose", "Health Testing and Monitoring")

        # Export table names and ARNs
        CfnOutput(
            self,
            "TestEventsTableName",
            value=self.test_events_table.table_name,
            export_name=NamingConventions.stack_export_name(
                "Table", "TestEvents", env_name
            )
        )

        CfnOutput(
            self,
            "TestEventsTableArn",
            value=self.test_events_table.table_arn,
            export_name=NamingConventions.stack_export_name(
                "TableArn", "TestEvents", env_name
            )
        )

        CfnOutput(
            self,
            "TestResultsTableName",
            value=self.test_results_table.table_name,
            export_name=NamingConventions.stack_export_name(
                "Table", "TestResults", env_name
            )
        )

        CfnOutput(
            self,
            "TestResultsTableArn",
            value=self.test_results_table.table_arn,
            export_name=NamingConventions.stack_export_name(
                "TableArn", "TestResults", env_name
            )
        )