from aws_cdk import (
    Duration,
    Stack,
    Fn,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import json


class TemplateBasedSQLAgentStack(Stack):
    """
    Template-Based SQL Agent Stack - Uses JSON template with JSONata
    
    This stack demonstrates the template approach:
    - Uses JSON template file with JSONata
    - References shared LLM Lambda functions
    - Simple placeholder replacement
    - Follows your existing proven pattern
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared resources
        self._import_shared_resources()
        
        # Create agent execution role
        self._create_agent_execution_role()
        
        # Create Step Functions workflow from template
        self._create_step_functions_from_template()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import shared LLM Lambda function ARN
        self.claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{self.env_name}")

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution"""
        
        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            "TemplateBasedSQLAgentLogGroup",
            log_group_name=f"/aws/stepfunctions/template-sql-agent-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK
        )
        
        role = iam.Role(
            self,
            "TemplateBasedSQLAgentExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )
        
        # Grant Step Functions logging permissions to its own log group
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
        
        # Grant access to Lambda functions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    self.claude_lambda_arn,
                    # db-interface Lambda ARN
                    NamingConventions.tool_lambda_arn(
                        "db-interface",
                        self.region,
                        self.account,
                        self.env_name
                    )
                ]
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
        """Create Step Functions workflow from JSON template"""
        
        # Read the template file
        template_path = "step-functions/refactored-sql-agent-template.json"
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholders with actual ARNs
        template_content = template_content.replace(
            "SHARED_CLAUDE_LAMBDA_ARN", 
            self.claude_lambda_arn
        )
        
        template_content = template_content.replace(
            "DB_INTERFACE_LAMBDA_ARN",
            NamingConventions.tool_lambda_arn(
                "db-interface",
                self.region,
                self.account,
                self.env_name
            )
        )
        
        # Create the state machine using the processed template
        self.state_machine = sfn.StateMachine(
            self,
            "TemplateBasedSQLAgentStateMachine",
            state_machine_name=f"template-sql-agent-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(template_content),
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )