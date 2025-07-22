from aws_cdk import (
    Duration,
    Stack,
    Fn,
    RemovalPolicy,
    CfnOutput,
    aws_logs as logs,
    aws_iam as iam,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
from .step_functions_generator import StepFunctionsGenerator
from typing import List, Dict, Any
import json


class BaseAgentStack(Stack):
    """
    Base Agent Stack - Common patterns for all agents
    
    This base class provides:
    - Agent execution role with standard permissions
    - Log group creation with consistent naming
    - Tool permission generation based on tool IDs
    - Step Functions template processing
    - State machine creation with standard settings
    
    Derived agent stacks just need to specify:
    - LLM ARN to use
    - List of tool IDs from registry
    - Agent-specific configuration
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
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.agent_name = agent_name
        self.llm_arn = llm_arn
        self.tool_configs = tool_configs
        self.tool_names = [config["tool_name"] for config in tool_configs]
        self.system_prompt = system_prompt or f"You are a helpful AI assistant with access to various tools."
        
        # Import shared resources
        self._import_shared_resources()
        
        # Create agent execution role
        self._create_agent_execution_role()
        
        # Create Step Functions workflow from template
        self._create_step_functions_from_template()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import tool registry table name and ARN
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )
        
        # Import agent registry table name and ARN
        self.agent_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "AgentRegistry", self.env_name)
        )
        
        self.agent_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "AgentRegistry", self.env_name)
        )


    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution with tool permissions"""
        
        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            f"{self.agent_name}AgentLogGroup",
            log_group_name=f"/aws/stepfunctions/{self.agent_name}-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        role = iam.Role(
            self,
            f"{self.agent_name}AgentExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )
        
        # Grant Step Functions logging permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream", 
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams",
                    "logs:DescribeLogGroups"
                ],
                resources=[
                    self.log_group.log_group_arn,
                    f"{self.log_group.log_group_arn}:*"
                ]
            )
        )
        
        # Grant CloudWatch metrics permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"]
            )
        )
        
        # Grant access to DynamoDB tool registry
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.tool_registry_table_arn,
                    f"{self.tool_registry_table_arn}/index/*"
                ]
            )
        )
        
        # Grant access to DynamoDB agent registry
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ],
                resources=[
                    self.agent_registry_table_arn,
                    f"{self.agent_registry_table_arn}/index/*"
                ]
            )
        )
        
        # Grant access to LLM Lambda function
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    self.llm_arn
                ]
            )
        )
        
        # Grant access to invoke specific tool Lambda functions
        # Get unique Lambda ARNs from tool configs
        lambda_arns = list(set(config["lambda_arn"] for config in self.tool_configs))
        
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=lambda_arns
            )
        )
        
        # Grant X-Ray permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        self.agent_execution_role = role

    def _create_step_functions_from_template(self):
        """Create Step Functions workflow with static tool definitions"""
        
        # Generate static Step Functions definition with explicit tool routing
        definition_json = StepFunctionsGenerator.generate_static_agent_definition(
            agent_name=self.agent_name,
            llm_arn=self.llm_arn,
            tool_configs=self.tool_configs,
            system_prompt=self.system_prompt,
            agent_registry_table_name=self.agent_registry_table_name,
            tool_registry_table_name=self.tool_registry_table_name
        )
        
        # Create the state machine using the generated definition
        self.state_machine = sfn.StateMachine(
            self,
            f"{self.agent_name}AgentStateMachine",
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(definition_json),
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )