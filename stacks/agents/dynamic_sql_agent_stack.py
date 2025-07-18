from aws_cdk import (
    Duration,
    Stack,
    Fn,
    RemovalPolicy,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import json


class DynamicSQLAgentStack(Stack):
    """
    Dynamic SQL Agent Stack - Uses DynamoDB tool registry for dynamic tool loading
    
    This stack demonstrates the complete new architecture:
    - Uses JSON template with dynamic tool loading from DynamoDB
    - References shared LLM Lambda functions
    - Configurable tool list per agent
    - Full end-to-end dynamic flow
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Define which tools this agent uses
        self.agent_tools = [
            "get_db_schema",
            "execute_sql_query"
        ]
        
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
        
        # Import tool registry table name and ARN
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution"""
        
        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            "DynamicSQLAgentLogGroup",
            log_group_name=f"/aws/stepfunctions/dynamic-sql-agent-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        role = iam.Role(
            self,
            "DynamicSQLAgentExecutionRole",
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
        
        # Grant access to shared LLM Lambda function
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    self.claude_lambda_arn
                ]
            )
        )
        
        # Grant access to tool Lambda functions (using naming convention)
        # For SQL tools, both use the same db-interface Lambda
        db_interface_arn = NamingConventions.tool_lambda_arn(
            "db-interface",
            self.region,
            self.account,
            self.env_name
        )
        
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[db_interface_arn]
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
        """Create Step Functions workflow from dynamic template"""
        
        # Read the template file
        template_path = "step-functions/dynamic-sql-agent-template.json"
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholders with actual values
        
        # 1. Replace tool registry table name
        template_content = template_content.replace(
            "TOOL_REGISTRY_TABLE_NAME", 
            self.tool_registry_table_name
        )
        
        # 2. Replace shared Claude Lambda ARN
        template_content = template_content.replace(
            "SHARED_CLAUDE_LAMBDA_ARN",
            self.claude_lambda_arn
        )
        
        # 3. Replace db-interface Lambda ARN
        db_interface_arn = NamingConventions.tool_lambda_arn(
            "db-interface",
            self.region,
            self.account,
            self.env_name
        )
        template_content = template_content.replace(
            "DB_INTERFACE_LAMBDA_ARN",
            db_interface_arn
        )
        
        # 4. Replace agent tool list
        agent_tool_list_json = json.dumps(self.agent_tools)
        template_content = template_content.replace(
            '"AGENT_TOOL_LIST"',
            agent_tool_list_json
        )
        
        # Create the state machine using the processed template
        self.state_machine = sfn.StateMachine(
            self,
            "DynamicSQLAgentStateMachine",
            state_machine_name=f"dynamic-sql-agent-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(template_content),
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )