from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
from .base_tool_construct import MultiToolConstruct
from ..shared.tool_definitions import SpecializedTools


class LocalAutomationToolStack(Stack):
    """
    Local Automation Tools Stack - Secure local command execution and RPA
    
    This stack deploys local automation capabilities:
    - Secure local command execution through Rust-based agent
    - Remote process automation (RPA) capabilities
    - Step Functions activity-based security model
    - Windows and macOS application automation
    - File system operations and data transfer
    - Network-isolated execution environment
    - Automatic DynamoDB registry registration
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Deploy Rust local automation tool
        self._create_local_automation_tool()
        
        # Register all tools in DynamoDB using the base construct
        self._register_tools_using_base_construct()

    def _create_local_automation_tool(self):
        """Create Rust Lambda function for local automation"""
        
        # Create execution role for local automation Lambda
        local_automation_lambda_role = iam.Role(
            self,
            "LocalAutomationLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant additional permissions for local automation operations
        local_automation_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "states:SendTaskSuccess",
                    "states:SendTaskFailure",
                    "states:SendTaskHeartbeat",
                    "states:GetActivityTask"
                ],
                resources=["*"]
            )
        )
        
        # Grant SSM permissions for secure command execution
        local_automation_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:SendCommand",
                    "ssm:GetCommandInvocation",
                    "ssm:DescribeInstanceInformation",
                    "ssm:ListCommandInvocations"
                ],
                resources=["*"]
            )
        )
        
        # Grant EC2 permissions for instance management
        local_automation_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceStatus"
                ],
                resources=["*"]
            )
        )
        
        # Create Rust Lambda function for local automation
        self.local_automation_lambda = _lambda.Function(
            self,
            "LocalAutomationLambda",
            function_name=f"tool-local-automation-{self.env_name}",
            description="Secure local command execution and RPA through Rust-based agent with activity-based security",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda/tools/local-agent/"),
            handler="main",
            timeout=Duration.minutes(5),  # Local commands may take time
            memory_size=512,
            role=local_automation_lambda_role,
            environment={
                "RUST_LOG": "info",
                "HUMAN_APPROVAL_REQUIRED": "true",  # Security feature
                "EXECUTION_TIMEOUT": "300"  # 5 minutes max execution
            }
        )
        
        self.local_automation_lambda.apply_removal_policy(RemovalPolicy.DESTROY)
        
        CfnOutput(
            self,
            "LocalAutomationLambdaArn",
            value=self.local_automation_lambda.function_arn,
            export_name=f"LocalAutomationLambdaArn-{self.env_name}"
        )

    def _register_tools_using_base_construct(self):
        """Register all local automation tools using the BaseToolConstruct pattern"""
        
        # Get tool definition from centralized definitions
        local_agent_tool = SpecializedTools.LOCAL_AGENT
        
        # Define local automation tool specifications
        local_automation_tools = [
            {
                "tool_name": local_agent_tool.tool_name,
                "description": local_agent_tool.description,
                "input_schema": local_agent_tool.input_schema,
                "language": local_agent_tool.language.value,
                "tags": local_agent_tool.tags,
                "author": local_agent_tool.author,
                "human_approval_required": local_agent_tool.human_approval_required
            }
        ]
        
        # Use MultiToolConstruct to register local automation tools
        MultiToolConstruct(
            self,
            "LocalAutomationToolsRegistry",
            tool_groups=[
                {
                    "tool_specs": local_automation_tools,
                    "lambda_function": self.local_automation_lambda
                }
            ],
            env_name=self.env_name
        )