from aws_cdk import (
    Stack,
    Fn,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_logs as logs,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
from .step_functions_generator import StepFunctionsGenerator
from .agent_registry_mixin import AgentRegistryMixin
from typing import List, Dict, Any, Optional


class FlexibleLongContentAgentStack(Stack, AgentRegistryMixin):
    """
    Flexible Long Content Agent Stack
    
    This agent stack can operate in multiple modes:
    1. With Agent Registry - Integrates with existing agent registry
    2. Without Agent Registry - Operates independently
    3. With Custom Registry - Uses a different registry table
    
    Configuration example:
    {
        "use_agent_registry": true,
        "import_registry_from": "AgentRegistry-prod",  # Optional custom export name
        "create_approval_activity": true,
        "share_llm": true,
        "llm_arn": "arn:aws:lambda:..."  # When sharing existing LLM
    }
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        agent_name: str,
        env_name: str = "prod",
        agent_config: Optional[Dict[str, Any]] = None,
        system_prompt: str = None,
        max_content_size: int = 5000,
        **kwargs
    ) -> None:
        """
        Initialize FlexibleLongContentAgentStack
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this construct
            agent_name: Name of the agent
            env_name: Environment name
            agent_config: Configuration for flexible deployment
            system_prompt: Custom system prompt
            max_content_size: Maximum content size before using DynamoDB
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.agent_name = agent_name
        self.env_name = env_name
        self.agent_config = agent_config or {}
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.max_content_size = max_content_size
        
        # Import resources based on configuration
        self._import_resources()
        
        # Create IAM role for the agent
        self._create_agent_role()
        
        # Create CloudWatch log group
        self._create_log_group()
        
        # Handle approval activity if needed
        self._handle_approval_activity()
        
        # Create the Step Functions state machine
        self._create_state_machine()
        
        # Add permissions based on configuration
        self._add_permissions()
        
        # Create stack outputs
        self._create_outputs()
        
        print(f"✅ Created flexible long content agent: {agent_name}")

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for the agent"""
        return f"""You are {self.agent_name}, an AI assistant with access to various tools that can handle large content outputs.

Your responses may contain references to content stored in DynamoDB when the output exceeds Step Functions limits.
The infrastructure automatically handles storing and retrieving this content."""

    def _import_resources(self):
        """Import necessary resources based on configuration"""
        
        # Import long content infrastructure
        self.content_table_name = Fn.import_value(
            NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name)
        )
        self.content_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name)
        )
        
        # Import or set LLM ARN
        if self.agent_config.get("llm_arn"):
            self.llm_arn = self.agent_config["llm_arn"]
        else:
            self.llm_arn = Fn.import_value(f"SharedClaudeLambdaWithLongContentArn-{self.env_name}")
        
        # Import tool configurations
        self.tool_configs = self._get_tool_configs()
        
        # Import tool registry (always needed for agents to look up tools)
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        
        # Optionally import agent registry
        if self.agent_config.get("use_agent_registry", False):
            self._import_agent_registry()
        else:
            self.agent_registry_table_name = None
            self.agent_registry_table_arn = None

    def _import_agent_registry(self):
        """Import agent registry table if configured"""
        
        if self.agent_config.get("import_registry_from"):
            # Custom export name
            export_base = self.agent_config["import_registry_from"]
            self.agent_registry_table_name = Fn.import_value(f"{export_base}-TableName")
            self.agent_registry_table_arn = Fn.import_value(f"{export_base}-TableArn")
        else:
            # Standard export names
            self.agent_registry_table_name = Fn.import_value(
                NamingConventions.stack_export_name("Table", "AgentRegistry", self.env_name)
            )
            self.agent_registry_table_arn = Fn.import_value(
                NamingConventions.stack_export_name("TableArn", "AgentRegistry", self.env_name)
            )

    def _get_tool_configs(self) -> List[Dict[str, Any]]:
        """Get tool configurations - can be customized by subclasses"""
        # Default implementation - subclasses should override
        return self.agent_config.get("tool_configs", [])

    def _create_agent_role(self):
        """Create IAM role for the Step Functions state machine"""
        
        self.agent_role = iam.Role(
            self,
            f"{self.agent_name}Role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description=f"Execution role for {self.agent_name} agent"
        )
        
        # Add basic Step Functions permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogDelivery",
                    "logs:GetLogDelivery",
                    "logs:UpdateLogDelivery",
                    "logs:DeleteLogDelivery",
                    "logs:ListLogDeliveries",
                    "logs:PutResourcePolicy",
                    "logs:DescribeResourcePolicies",
                    "logs:DescribeLogGroups"
                ],
                resources=["*"]
            )
        )
        
        # Add Lambda invoke permissions
        lambda_resources = [self.llm_arn]
        for config in self.tool_configs:
            if "lambda_arn" in config:
                lambda_resources.append(config["lambda_arn"])
        
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=lambda_resources
            )
        )
        
        # Add X-Ray permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                resources=["*"]
            )
        )
        
        # Add CloudWatch metrics permissions
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )

    def _create_log_group(self):
        """Create CloudWatch log group"""
        
        self.log_group = logs.LogGroup(
            self,
            f"{self.agent_name}LogGroup",
            log_group_name=f"/aws/stepfunctions/{self.agent_name}-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

    def _handle_approval_activity(self):
        """Create or import approval activity if needed"""
        
        # Check if we should use existing approval activity
        if self.agent_config.get("existing_approval_activity_arn"):
            self.approval_activity = sfn.Activity.from_activity_arn(
                self,
                "ImportedApprovalActivity",
                self.agent_config["existing_approval_activity_arn"]
            )
            print(f"Imported existing approval activity")
            return
        
        if not self.agent_config.get("create_approval_activity", True):
            self.approval_activity = None
            return
        
        approval_tools = [
            config for config in self.tool_configs 
            if config.get("requires_activity") and config.get("activity_type") == "human_approval"
        ]
        
        if approval_tools:
            self.approval_activity = sfn.Activity(
                self,
                f"{self.agent_name}ApprovalActivity",
                activity_name=f"{self.agent_name}-approval-activity-{self.env_name}"
            )
            
            # Grant activity permissions
            self.approval_activity.grant(self.agent_role, "states:SendTaskSuccess", "states:SendTaskFailure")
            
            print(f"Created approval activity: {self.approval_activity.activity_name}")
        else:
            self.approval_activity = None

    def _create_state_machine(self):
        """Create the Step Functions state machine"""
        
        # Generate the state machine definition
        definition = StepFunctionsGenerator.generate_static_agent_definition(
            agent_name=self.agent_name,
            llm_arn=self.llm_arn,
            tool_configs=self.tool_configs,
            system_prompt=self.system_prompt,
            approval_activity_arn=self.approval_activity.activity_arn if self.approval_activity else None,
            agent_registry_table_name=self.agent_registry_table_name,
            tool_registry_table_name=self.tool_registry_table_name,
        )
        
        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self,
            f"{self.agent_name}StateMachine",
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(definition),
            role=self.agent_role,
            tracing_enabled=True,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            )
        )
        
        self.state_machine_name = self.state_machine.state_machine_name
        
        # Register agent if configured to use registry
        if self.agent_config.get("use_agent_registry", False):
            self.register_agent_in_registry()

    def _add_permissions(self):
        """Add permissions based on configuration"""
        
        # Always add content table permissions for long content
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem"
                ],
                resources=[self.content_table_arn]
            )
        )
        
        # Add agent registry permissions if using it
        if self.agent_registry_table_arn:
            self.agent_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    resources=[
                        self.agent_registry_table_arn,
                        f"{self.agent_registry_table_arn}/index/*"
                    ]
                )
            )
        
        # Add tool registry permissions - agents need to read tool information
        if hasattr(self, 'tool_registry_table_arn') and self.tool_registry_table_arn:
            self.agent_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    resources=[
                        self.tool_registry_table_arn,
                        f"{self.tool_registry_table_arn}/index/*"
                    ]
                )
            )

    def _create_outputs(self):
        """Create CloudFormation outputs"""
        
        # Export state machine ARN
        CfnOutput(
            self,
            "StateMachineArn",
            value=self.state_machine.state_machine_arn,
            export_name=NamingConventions.stack_export_name("StateMachine", self.agent_name, self.env_name),
            description=f"ARN of the {self.agent_name} state machine"
        )
        
        # Export state machine name
        CfnOutput(
            self,
            "StateMachineName",
            value=self.state_machine_name,
            export_name=NamingConventions.stack_export_name("StateMachineName", self.agent_name, self.env_name),
            description=f"Name of the {self.agent_name} state machine"
        )
        
        # Export activity ARN if created
        if self.approval_activity:
            CfnOutput(
                self,
                "ApprovalActivityArn",
                value=self.approval_activity.activity_arn,
                export_name=NamingConventions.stack_export_name("ApprovalActivity", self.agent_name, self.env_name),
                description=f"ARN of the {self.agent_name} approval activity"
            )