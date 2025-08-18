from aws_cdk import (
    Stack,
    Duration,
    Fn,
    Aws,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct
from typing import Dict, Any, List
from ..shared.tool_definitions import AdvancedTools
from .step_functions_generator_unified_llm import UnifiedLLMStepFunctionsGenerator
from .agent_registry_mixin import AgentRegistryMixin
import json


class TestAutomationRemoteAgentRustLongContentStack(Stack, AgentRegistryMixin):
    """
    Test Automation Remote Agent Stack with Rust LLM and Long Content Support
    
    This stack creates an agent that provides enterprise test automation capabilities
    with long content support for handling extensive test results and reports.
    
    Features:
    - Unified Rust LLM with long content support for multi-provider flexibility
    - Microsoft Graph API with long content for enterprise Office 365 integration
    - Local agent execution for running automation scripts
    - Handles large test reports and bulk operations
    - Dynamic provider switching via DynamoDB configuration
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        """
        Initialize the Test Automation Remote Agent with Rust LLM and Long Content
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this stack
            env_name: Environment name (dev, prod, etc.)
        """
        # Initialize Stack class
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import required resources
        self._import_resources()
        
        # Create the agent
        self._create_agent()
        
        # Create stack exports
        self._create_stack_exports()
        
        print(f"✅ Created Test Automation Remote Agent with Rust LLM and Long Content for {env_name}")

    def _import_resources(self):
        """Import required resources from other stacks"""
        
        # Import unified Rust LLM with long content
        self.unified_rust_llm_arn = Fn.import_value(
            f"UnifiedRustLLMWithLongContentArn-{self.env_name}"
        )
        
        # Import Microsoft Graph tool with long content
        self.microsoft_graph_arn = Fn.import_value(
            f"MicrosoftGraphLongContentLambdaArn-{self.env_name}"
        )
        
        # Import local agent execution activity ARN
        self.local_execution_activity_arn = Fn.import_value(
            f"LocalAutomationRemoteActivityArn-{self.env_name}"
        )
        
        # Import shared infrastructure
        self.agent_registry_table_name = Fn.import_value(
            f"SharedTableAgentRegistry-{self.env_name}"
        )
        
        # LLM Models table is optional - not all deployments have it
        # For now, use a placeholder since it's not used in this environment
        self.llm_models_table_name = "LLMModels-placeholder"
        
        self.tool_registry_table_name = Fn.import_value(
            f"SharedTableToolRegistry-{self.env_name}"
        )
        
        print(f"📦 Imported required resources for {self.env_name}")

    def _create_agent(self):
        """Create the Test Automation Remote Agent with long content support"""
        
        self.agent_name = f"test-automation-remote-agent-rust-long-content"
        self.system_prompt = "You are an enterprise test automation assistant with Office 365 integration."
        
        # Define tool configurations  
        self.tool_configs = [
            {
                "tool_name": "local_agent_execute",
                "lambda_arn": self.local_execution_activity_arn,  # Activity ARN for compatibility
                "is_activity": True  # Flag to indicate this is an activity
            },
            {
                "tool_name": "MicrosoftGraphAPI",
                "lambda_arn": self.microsoft_graph_arn
            }
        ]
        
        # Create Step Functions state machine using unified LLM generator
        state_machine_definition = UnifiedLLMStepFunctionsGenerator.generate_unified_llm_agent_definition(
            agent_name=self.agent_name,
            unified_llm_arn=self.unified_rust_llm_arn,
            tool_configs=self.tool_configs,
            system_prompt=self.system_prompt,
            default_provider="anthropic",  # Default provider
            default_model="claude-3-5-sonnet-20241022",  # Default model
            agent_registry_table_name=self.agent_registry_table_name,
            llm_models_table_name=self.llm_models_table_name,
            tool_registry_table_name=self.tool_registry_table_name
        )
        
        # Create CloudWatch log group for the agent
        self.log_group = logs.LogGroup(
            self,
            "TestAutomationRemoteAgentLogGroup",
            log_group_name=f"/aws/vendedlogs/states/{self.agent_name}-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create IAM role for Step Functions
        sfn_role = iam.Role(
            self,
            "TestAutomationRemoteAgentRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )
        
        # Add permissions for Lambda invocations
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[
                    self.unified_rust_llm_arn,
                    self.microsoft_graph_arn,
                    f"{self.unified_rust_llm_arn}:*",
                    f"{self.microsoft_graph_arn}:*"
                ]
            )
        )
        
        # Add permissions for DynamoDB
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.agent_registry_table_name}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.llm_models_table_name}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.tool_registry_table_name}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.agent_registry_table_name}/index/*",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.llm_models_table_name}/index/*",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.tool_registry_table_name}/index/*"
                ]
            )
        )
        
        # Add permissions for CloudWatch Metrics
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )
        
        # Add permissions for Step Functions activities
        sfn_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "states:SendTaskSuccess",
                    "states:SendTaskFailure",
                    "states:SendTaskHeartbeat",
                    "states:GetActivityTask"
                ],
                resources=[self.local_execution_activity_arn]
            )
        )
        
        # Create Step Functions state machine
        self.state_machine = sfn.CfnStateMachine(
            self,
            "TestAutomationRemoteAgentStateMachine",
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_string=state_machine_definition,  # Already a JSON string
            role_arn=sfn_role.role_arn,
            logging_configuration=sfn.CfnStateMachine.LoggingConfigurationProperty(
                destinations=[
                    sfn.CfnStateMachine.LogDestinationProperty(
                        cloud_watch_logs_log_group=sfn.CfnStateMachine.CloudWatchLogsLogGroupProperty(
                            log_group_arn=self.log_group.log_group_arn
                        )
                    )
                ],
                include_execution_data=True,
                level="ALL"
            ),
            tracing_configuration=sfn.CfnStateMachine.TracingConfigurationProperty(
                enabled=True
            )
        )
        
        # Set additional metadata for the agent registry
        self.agent_description = "Enterprise test automation agent with Office 365 integration and long content support"
        self.llm_provider = "anthropic"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "llm_type": "unified-rust",
            "long_content_enabled": True,
            "default_provider": "anthropic",
            "default_model": "claude-3-5-sonnet-20241022",
            "capabilities": [
                "test_automation",
                "remote_execution",
                "office365_integration",
                "email_automation",
                "teams_integration",
                "sharepoint_access",
                "long_content_support"
            ],
            "tools": ["local_agent_execute", "MicrosoftGraphAPI"],
            "supports_long_content": True,
            "content_table": Fn.import_value(f"SharedContentTableLongContent-{self.env_name}")
        }
        
        # Register agent in DynamoDB using the mixin
        self.register_agent_in_registry()
        
        print(f"✅ Created unified LLM agent: {self.agent_name}-{self.env_name}")
        print(f"   Using unified Rust LLM with long content support")
        print(f"   Tools: local_agent_execute, MicrosoftGraphAPI")


    def _create_stack_exports(self):
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self,
            "TestAutomationRemoteAgentRustLongContentArn",
            value=self.state_machine.attr_arn,
            export_name=f"TestAutomationRemoteAgentRustLongContentArn-{self.env_name}",
            description="ARN of the Test Automation Remote Agent with Rust LLM and Long Content"
        )
        
        CfnOutput(
            self,
            "TestAutomationRemoteAgentRustLongContentName",
            value=self.state_machine.state_machine_name,
            export_name=f"TestAutomationRemoteAgentRustLongContentName-{self.env_name}",
            description="Name of the Test Automation Remote Agent with Rust LLM and Long Content"
        )