"""
MCP Server Construct - Generic CDK construct for MCP server registration

This construct provides automatic registration of MCP servers in the control plane.
It can be used by any MCP server deployment stack to integrate with centralized
observability, health monitoring, and management UI.

Usage:
    from stacks.shared.mcp_server_construct import McpServerConstruct

    McpServerConstruct(
        self, "McpServerRegistration",
        server_id="mcp-reinvent-prod",
        server_spec={...},
        lambda_function=my_lambda,
        env_name="prod",
        enable_observability=True
    )
"""

from aws_cdk import (
    Fn,
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    custom_resources as cr
)
from constructs import Construct
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class McpServerConstruct(Construct):
    """
    MCP Server Construct - Handles registration and observability integration

    This construct:
    - Registers MCP server in DynamoDB registry
    - Sets up CloudWatch logs, metrics, and alarms
    - Configures health check monitoring
    - Provides lifecycle management (create/update/delete)

    Makes control plane integration completely optional and pluggable.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        server_id: str,
        version: str,
        server_name: str,
        server_spec: Dict[str, Any],
        lambda_function: _lambda.Function,
        env_name: str = "prod",
        enable_observability: bool = True,
        enable_health_monitoring: bool = True,
        registry_table_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize McpServerConstruct

        Args:
            scope: CDK scope
            construct_id: Construct ID
            server_id: Unique server identifier (e.g., "mcp-reinvent-prod")
            version: Server version (e.g., "1.0.0")
            server_name: Human-readable server name
            server_spec: Server specification dict with tools, resources, prompts, etc.
            lambda_function: Lambda function for the MCP server
            env_name: Environment name (prod, dev, etc.)
            enable_observability: Enable CloudWatch logs, metrics, alarms
            enable_health_monitoring: Enable health check monitoring
            registry_table_name: Optional override for registry table name
        """
        super().__init__(scope, construct_id, **kwargs)

        self.server_id = server_id
        self.version = version
        self.server_name = server_name
        self.server_spec = server_spec
        self.lambda_function = lambda_function
        self.env_name = env_name
        self.enable_observability = enable_observability
        self.enable_health_monitoring = enable_health_monitoring

        # Import registry table
        self.registry_table_name = registry_table_name or f"MCPServerRegistry-{env_name}"
        self.registry_table_arn = self._get_registry_table_arn()

        # Set up observability if enabled
        if self.enable_observability:
            self._setup_observability()

        # Register server in DynamoDB
        self._register_server_in_registry()

        # Set up health monitoring if enabled
        if self.enable_health_monitoring:
            self._setup_health_monitoring()

    def _get_registry_table_arn(self) -> str:
        """Get the ARN of the registry table"""
        try:
            return Fn.import_value(f"MCPRegistryTableArn-{self.env_name}")
        except:
            # If import doesn't exist, construct ARN manually
            return Fn.sub(
                f"arn:aws:dynamodb:${{AWS::Region}}:${{AWS::AccountId}}:table/{self.registry_table_name}"
            )

    def _setup_observability(self):
        """Set up CloudWatch logs, metrics, and alarms"""

        # CloudWatch Log Group (if not already created by Lambda)
        self.log_group = logs.LogGroup(
            self,
            "McpServerLogGroup",
            log_group_name=f"/mcp-servers/{self.server_id}",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # Custom metrics namespace
        self.metrics_namespace = f"MCP/{self.server_name.replace(' ', '')}"

        # Create custom metric for tool invocations
        self.tool_invocation_metric = cloudwatch.Metric(
            namespace=self.metrics_namespace,
            metric_name="ToolInvocations",
            dimensions_map={"ServerName": self.server_name},
            statistic="Sum"
        )

        # Create alarm for high error rate
        self.error_alarm = cloudwatch.Alarm(
            self,
            "ErrorAlarm",
            alarm_name=f"{self.server_id}-high-error-rate",
            alarm_description=f"High error rate for {self.server_name}",
            metric=self.lambda_function.metric_errors(
                period=Duration.minutes(5),
                statistic="Sum"
            ),
            threshold=10,
            evaluation_periods=2,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # Enable X-Ray tracing if specified
        if self.server_spec.get('traces_enabled', False):
            self.lambda_function.add_environment(
                "AWS_XRAY_TRACING_ENABLED",
                "true"
            )

    def _register_server_in_registry(self):
        """Register MCP server in DynamoDB registry"""

        # Build registration item
        registration_item = {
            # Primary keys
            'server_id': {'S': self.server_id},
            'version': {'S': self.version},

            # Server metadata
            'server_name': {'S': self.server_name},
            'description': {'S': self.server_spec.get('description', '')},
            'protocol_version': {'S': self.server_spec.get('protocol_version', '2024-11-05')},
            'protocol_type': {'S': self.server_spec.get('protocol_type', 'jsonrpc')},

            # Deployment information
            'deployment_type': {'S': 'aws-lambda'},
            'deployment_stack': {'S': Stack.of(self).stack_name},
            'deployment_region': {'S': Stack.of(self).region},
            'lambda_arn': {'S': self.lambda_function.function_arn},
            'function_url': {'S': self.server_spec.get('endpoint_url', '')},
            'endpoint_url': {'S': self.server_spec.get('endpoint_url', '')},

            # MCP capabilities
            'available_tools': {'S': json.dumps(self.server_spec.get('tools', []))},
            'available_resources': {'S': json.dumps(self.server_spec.get('resources', []))},
            'available_prompts': {'S': json.dumps(self.server_spec.get('prompts', []))},

            # Status and health
            'status': {'S': 'active'},
            'health_status': {'S': 'unknown'},
            'health_check_url': {'S': self.server_spec.get('health_check_url', '')},
            'health_check_interval': {'N': str(self.server_spec.get('health_check_interval', 300))},
            'last_health_check': {'S': datetime.utcnow().isoformat()},

            # Observability
            'cloudwatch_log_group': {'S': f"/mcp-servers/{self.server_id}" if self.enable_observability else ''},
            'metrics_namespace': {'S': self.metrics_namespace if self.enable_observability else ''},
            'traces_enabled': {'BOOL': self.server_spec.get('traces_enabled', False)},
            'log_level': {'S': self.server_spec.get('log_level', 'INFO')},

            # Authentication
            'authentication_type': {'S': self.server_spec.get('authentication_type', 'none')},

            # Configuration
            'configuration': {'S': json.dumps(self.server_spec.get('configuration', {}))},
            'environment_variables': {'S': json.dumps(self.server_spec.get('environment_variables', {}))},

            # Metadata
            'metadata': {'S': json.dumps(self.server_spec.get('metadata', {}))},

            # Lifecycle
            'created_at': {'S': datetime.utcnow().isoformat()},
            'updated_at': {'S': datetime.utcnow().isoformat()},
            'created_by': {'S': 'cdk-deployment'}
        }

        # Create custom resource to register server
        self.registration_resource = cr.AwsCustomResource(
            self,
            "ServerRegistration",
            on_create=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.registry_table_name,
                    "Item": registration_item
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"mcp-server-{self.server_id}-{self.version}"
                )
            ),
            on_update=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.registry_table_name,
                    "Item": {
                        **registration_item,
                        'updated_at': {'S': datetime.utcnow().isoformat()}
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"mcp-server-{self.server_id}-{self.version}"
                )
            ),
            on_delete=cr.AwsSdkCall(
                service="dynamodb",
                action="deleteItem",
                parameters={
                    "TableName": self.registry_table_name,
                    "Key": {
                        "server_id": {"S": self.server_id},
                        "version": {"S": self.version}
                    }
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["dynamodb:PutItem", "dynamodb:DeleteItem"],
                    resources=[self.registry_table_arn]
                )
            ])
        )

    def _setup_health_monitoring(self):
        """Set up health check monitoring"""

        # Create EventBridge rule for periodic health checks (if needed)
        # This is optional - can be implemented later if we want automated health checks
        pass

    def add_tool_lambda_permission(self, tool_name: str, lambda_arn: str):
        """
        Add IAM permission for MCP server to invoke remote Lambda tool

        Args:
            tool_name: Name of the tool
            lambda_arn: ARN of the Lambda function to invoke
        """
        self.lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[lambda_arn]
            )
        )
