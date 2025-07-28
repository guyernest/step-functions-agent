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
from typing import List, Dict, Any, Optional


class StandaloneLongContentAgentStack(Stack):
    """
    Standalone Long Content Agent Stack - For agents handling large message contexts
    
    This is a completely independent agent stack that doesn't require the main
    infrastructure (no Agent Registry dependency). It includes:
    - DynamoDB table access for large content storage
    - Lambda Runtime API Proxy extension layer
    - Environment variables for content transformation
    - Automatic architecture detection for layer selection
    
    IMPORTANT: This stack is designed to run independently from the main
    Step Functions Agent infrastructure.
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        agent_name: str,
        llm_arn: str, 
        tool_configs: List[Dict[str, Any]], 
        env_name: str = "prod",
        system_prompt: str = None,
        max_content_size: int = 5000,
        **kwargs
    ) -> None:
        """
        Initialize StandaloneLongContentAgentStack
        
        Args:
            scope: CDK construct scope
            construct_id: Unique identifier for this construct
            agent_name: Name of the agent (e.g., "WebScraper", "ImageAnalyzer")
            llm_arn: ARN of the LLM Lambda function to use
            tool_configs: List of tool configurations
            env_name: Environment name (dev, prod, etc.)
            system_prompt: Custom system prompt for the agent
            max_content_size: Maximum content size before storing in DynamoDB
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.agent_name = agent_name
        self.llm_arn = llm_arn
        self.tool_configs = tool_configs
        self.env_name = env_name
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.max_content_size = max_content_size
        
        # Import long content infrastructure
        self._import_long_content_infrastructure()
        
        # Create IAM role for the agent
        self._create_agent_role()
        
        # Create CloudWatch log group
        self._create_log_group()
        
        # Create approval activity if needed
        self._create_approval_activity_if_needed()
        
        # Create the Step Functions state machine
        self._create_state_machine()
        
        # Add DynamoDB permissions for long content
        self._add_content_table_permissions()
        
        # Create stack outputs
        self._create_outputs()
        
        print(f"✅ Created long content agent stack: {agent_name} (max content size: {max_content_size} bytes)")

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for the agent"""
        return f"""You are {self.agent_name}, an AI assistant with access to various tools that can handle large content outputs.

Your responses may contain references to content stored in DynamoDB when the output exceeds Step Functions limits. 
These references use the format: @content:dynamodb:table:record-{{uuid}}

The infrastructure automatically handles storing and retrieving this content, so you can work with large outputs seamlessly."""

    def _import_long_content_infrastructure(self):
        """Import shared long content infrastructure resources"""
        
        # Import DynamoDB content table
        self.content_table_name = Fn.import_value(
            NamingConventions.stack_export_name("ContentTable", "LongContent", self.env_name)
        )
        
        self.content_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("ContentTableArn", "LongContent", self.env_name)
        )
        
        print(f"📊 Imported long content infrastructure for {self.env_name}")

    def _create_agent_role(self):
        """Create IAM role for the Step Functions state machine"""
        
        self.agent_role = iam.Role(
            self,
            f"{self.agent_name}Role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description=f"Execution role for {self.agent_name} agent with long content support"
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
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[
                    self.llm_arn,
                    *[config["lambda_arn"] for config in self.tool_configs]
                ]
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

    def _create_log_group(self):
        """Create CloudWatch log group for the agent"""
        
        self.log_group = logs.LogGroup(
            self,
            f"{self.agent_name}LogGroup",
            log_group_name=f"/aws/stepfunctions/{self.agent_name}-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_approval_activity_if_needed(self):
        """Create single approval activity if any tools require human approval"""
        
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
            
            # Grant activity permissions to the agent role
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
            # No agent registry for standalone agents
            agent_registry_table_name=None,
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

    def _add_content_table_permissions(self):
        """Add DynamoDB content table permissions to the agent role"""
        
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
        
        print(f"🔐 Added DynamoDB content table permissions to agent execution role")

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