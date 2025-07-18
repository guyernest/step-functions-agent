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
        
        # Define which tools this agent uses (manual configuration)
        self.agent_config = {
            "tools": [
                {
                    "name": "get_db_schema",
                    "lambda_arn_key": "DB_INTERFACE_LAMBDA_ARN"
                },
                {
                    "name": "execute_sql_query", 
                    "lambda_arn_key": "DB_INTERFACE_LAMBDA_ARN"
                },
                {
                    "name": "execute_python",
                    "lambda_arn_key": "EXECUTE_CODE_LAMBDA_ARN"
                }
            ],
            "llm_arn_key": "SHARED_CLAUDE_LAMBDA_ARN"
        }
        
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
        
        # Import execute code Lambda function ARN
        self.execute_code_lambda_arn = Fn.import_value(f"ExecuteCodeLambdaArn-{self.env_name}")
        
        
        # Import DB interface Lambda function ARN
        self.db_interface_lambda_arn = Fn.import_value(f"DBInterfaceLambdaArn-{self.env_name}")
        
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
        
        # Grant access to execute code Lambda function
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    self.execute_code_lambda_arn
                ]
            )
        )
        
        
        # Grant access to DB interface Lambda function
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[self.db_interface_lambda_arn]
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
        template_path = "step-functions/dynamic-agent-template.json"
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholders with actual values
        
        
        # 1. Replace tool registry table name
        template_content = template_content.replace(
            "TOOL_REGISTRY_TABLE_NAME",
            self.tool_registry_table_name
        )
        
        # 2. Replace tool names list for dynamic loading
        tool_names = [tool["name"] for tool in self.agent_config["tools"]]
        tool_names_json = json.dumps(tool_names)
        template_content = template_content.replace(
            '"TOOL_NAMES_LIST"',
            tool_names_json
        )
        
        # 3. Replace shared Claude Lambda ARN
        template_content = template_content.replace(
            "SHARED_CLAUDE_LAMBDA_ARN",
            self.claude_lambda_arn
        )
        
        # 4. Replace db-interface Lambda ARN
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
        
        # 5. Replace execute code Lambda ARN
        template_content = template_content.replace(
            "EXECUTE_CODE_LAMBDA_ARN",
            self.execute_code_lambda_arn
        )
        
        # 6. Generate dynamic routing choices and execution states
        routing_choices = []
        execution_states = {}
        
        # Create mapping of placeholder keys to actual ARNs
        arn_mapping = {
            "DB_INTERFACE_LAMBDA_ARN": self.db_interface_lambda_arn,
            "EXECUTE_CODE_LAMBDA_ARN": self.execute_code_lambda_arn,
            "SHARED_CLAUDE_LAMBDA_ARN": self.claude_lambda_arn
        }
        
        # Create one execution state per TOOL (not per Lambda function)
        for tool in self.agent_config["tools"]:
            tool_name = tool['name']
            lambda_key = tool['lambda_arn_key']
            
            # Get the actual ARN for this Lambda function
            actual_lambda_arn = arn_mapping.get(lambda_key, lambda_key)
            
            # Create state name based on tool name
            state_name = f"Execute {tool_name.replace('_', ' ').title()} Tool"
            
            # Add routing choice
            choice = {
                "Next": state_name,
                "Condition": "{% $states.input.name = \"" + tool_name + "\" %}"
            }
            routing_choices.append(choice)
            
            # Create execution state for this specific tool
            execution_states[state_name] = {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Arguments": {
                    "FunctionName": actual_lambda_arn,
                    "Payload": {
                        "name": "{% $states.input.**.name %}",
                        "id": "{% $states.input.id %}",
                        "input": "{% $states.input.input %}"
                    }
                },
                "Retry": [
                    {
                        "ErrorEquals": [
                            "Lambda.ServiceException",
                            "Lambda.AWSLambdaException", 
                            "Lambda.SdkClientException",
                            "Lambda.TooManyRequestsException"
                        ],
                        "IntervalSeconds": 1,
                        "MaxAttempts": 3,
                        "BackoffRate": 2,
                        "JitterStrategy": "FULL"
                    }
                ],
                "End": True,
                "Comment": f"Execute {tool_name} tool",
                "Output": "{% $states.result.Payload %}"
            }
        
        # Replace routing choices
        routing_choices_json = json.dumps(routing_choices, indent=6)
        template_content = template_content.replace(
            '"DYNAMIC_ROUTING_CHOICES"',
            routing_choices_json
        )
        
        # Replace execution states by merging them into the JSON structure
        # Parse the template as JSON to properly merge states
        template_json = json.loads(template_content)
        
        # Add execution states to the ItemProcessor states
        item_processor_states = template_json["States"]["For each tool use"]["ItemProcessor"]["States"]
        
        # Add each execution state
        for state_name, state_def in execution_states.items():
            item_processor_states[state_name] = state_def
        
        # Convert back to JSON string
        template_content = json.dumps(template_json, indent=2)
        
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