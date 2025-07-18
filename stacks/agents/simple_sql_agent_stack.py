from aws_cdk import (
    Duration,
    Stack,
    Fn,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions


class SimpleSQLAgentStack(Stack):
    """
    Simple SQL Agent Stack - Minimal example of new architecture
    
    This is a simplified agent that demonstrates:
    - References shared LLM Lambda functions
    - Uses a single Lambda that handles both SQL tools
    - No DynamoDB tool registry (for initial testing)
    - Clean separation of concerns
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared resources
        self._import_shared_resources()
        
        # Create agent-specific resources
        self._create_agent_resources()
        
        # Create Step Functions workflow
        self._create_step_functions_workflow()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import shared LLM Lambda function ARN
        self.claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{self.env_name}")

    def _create_agent_resources(self):
        """Create agent-specific resources"""
        
        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            "SimpleSQLAgentLogGroup",
            log_group_name=f"/aws/stepfunctions/simple-sql-agent-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create agent execution role
        self.agent_execution_role = self._create_agent_execution_role()

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution"""
        
        role = iam.Role(
            self,
            "SimpleSQLAgentExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )
        
        # Grant basic Step Functions permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:{self.log_group.log_group_name}:*"
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
                    self.claude_lambda_arn,
                    # Hardcode the db-interface Lambda ARN for now
                    NamingConventions.tool_lambda_arn(
                        "db-interface",
                        self.region,
                        self.account,
                        self.env_name
                    )
                ]
            )
        )
        
        # Grant X-Ray permissions for tracing
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
        
        return role

    def _create_step_functions_workflow(self):
        """Create Step Functions workflow"""
        
        # Define tool specifications statically for now
        prepare_tools = sfn.Pass(
            self,
            "PrepareTools",
            comment="Prepare tool specifications",
            parameters={
                "messages.$": "{% $states.input.messages %}",
                "system.$": "{% $states.input.system %}",
                "model.$": "{% $states.input.model %}",
                "tools": [
                    {
                        "name": "get_db_schema",
                        "description": "Describe the schema of the SQLite database, including table names, and column names and types.",
                        "input_schema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "execute_sql_query",
                        "description": "Return the query results of any valid sqlite SQL query. If the SQL query result has many rows then return only the first 5 rows.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "sql_query": {
                                    "type": "string",
                                    "description": "The sql query to execute. If the SQL query result has many rows then return only the first 5 rows."
                                }
                            },
                            "required": ["sql_query"]
                        }
                    }
                ]
            }
        )
        
        # Create LLM call task
        call_llm = sfn_tasks.LambdaInvoke(
            self,
            "CallLLM",
            lambda_function=_lambda.Function.from_function_arn(
                self,
                "SharedClaudeLambda",
                function_arn=self.claude_lambda_arn
            ),
            payload=sfn.TaskInput.from_object({
                "system.$": "{% $states.input.system %}",
                "messages.$": "{% $states.input.messages %}",
                "tools.$": "{% $states.input.tools %}",
                "model.$": "{% $states.input.model %}"
            }),
            result_path="$.llm_response"
        )
        
        # Create tool execution choice
        tool_execution_choice = sfn.Choice(
            self,
            "ProcessLLMResponse",
            comment="Check if LLM wants to use a tool"
        )
        
        # Extract tool call information
        extract_tool_call = sfn.Pass(
            self,
            "ExtractToolCall",
            comment="Extract tool call from LLM response",
            parameters={
                "tool_input.$": "{% $states.input.llm_response.Payload.body.function_calls[0] %}",
                "messages.$": "{% $states.input.llm_response.Payload.body.messages %}",
                "tools.$": "{% $states.input.tools %}",
                "system.$": "{% $states.input.system %}",
                "model.$": "{% $states.input.model %}"
            }
        )
        
        # Execute tool
        execute_db_tool = sfn_tasks.LambdaInvoke(
            self,
            "ExecuteDbTool",
            lambda_function=_lambda.Function.from_function_arn(
                self,
                "DbInterfaceLambda",
                function_arn=NamingConventions.tool_lambda_arn(
                    "db-interface",
                    self.region,
                    self.account,
                    self.env_name
                )
            ),
            payload=sfn.TaskInput.from_object({
                "id.$": "{% $states.input.tool_input.id %}",
                "name.$": "{% $states.input.tool_input.name %}",
                "input.$": "{% $states.input.tool_input.input %}",
                "type": "tool_use"
            }),
            result_path="$.tool_result"
        )
        
        # Process tool result
        process_tool_result = sfn.Pass(
            self,
            "ProcessToolResult",
            comment="Add tool result to messages",
            result_path="$.processed",
            parameters={
                "messages.$": "{% $append($states.input.messages, $states.input.tool_result.Payload) %}",
                "tools.$": "{% $states.input.tools %}",
                "system.$": "{% $states.input.system %}",
                "model.$": "{% $states.input.model %}"
            }
        )
        
        # Create final response formatting
        format_response = sfn.Pass(
            self,
            "FormatResponse",
            comment="Format final response",
            parameters={
                "messages.$": "{% $states.input.llm_response.Payload.body.messages %}",
                "final_answer.$": "{% $states.input.llm_response.Payload.body.messages[-1].content %}"
            }
        )
        
        # Create success state
        success = sfn.Succeed(
            self,
            "Success",
            comment="SQL agent workflow completed successfully"
        )
        
        # Connect the states
        definition = (
            prepare_tools
            .next(call_llm)
            .next(tool_execution_choice)
        )
        
        # Add choice conditions
        tool_execution_choice.when(
            sfn.Condition.is_present("{% $states.input.llm_response.Payload.body.function_calls[0] %}"),
            extract_tool_call
            .next(execute_db_tool)
            .next(process_tool_result)
            .next(call_llm)
        ).otherwise(
            format_response
            .next(success)
        )
        
        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self,
            "SimpleSQLAgentStateMachine",
            state_machine_name=f"simple-sql-agent-{self.env_name}",
            definition=definition,
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )