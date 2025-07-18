from aws_cdk import (
    Duration,
    Stack,
    Fn,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions, generate_tool_lambda_arns


class RefactoredSQLAgentStack(Stack):
    """
    Refactored SQL Agent Stack - Example of new architecture
    
    This is a simplified agent that demonstrates:
    - References shared LLM Lambda functions
    - Uses only two tools: get_db_schema and execute_sql_query
    - No external dependencies (uses SQLite)
    - Clean separation of concerns
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Define tools this agent will use (just IDs from registry)
        self.agent_tools = [
            "db-interface",  # This Lambda contains both get_db_schema and execute_sql_query
        ]
        
        # Import shared resources
        self._import_shared_resources()
        
        # Create agent-specific resources
        self._create_agent_resources()
        
        # Create Step Functions workflow
        self._create_step_functions_workflow()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import shared LLM Lambda function ARNs
        self.claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{self.env_name}")
        
        # Import tool registry table
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )

    def _create_agent_resources(self):
        """Create agent-specific resources"""
        
        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            "SQLAgentLogGroup",
            log_group_name=f"/aws/stepfunctions/sql-agent-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK
        )
        
        # Create agent execution role
        self.agent_execution_role = self._create_agent_execution_role()

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution"""
        
        role_name = NamingConventions.agent_execution_role_name("sql", self.env_name)
        
        role = iam.Role(
            self,
            "SQLAgentExecutionRole",
            role_name=role_name,
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
        
        # Grant access to shared LLM Lambda functions
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
        tool_lambda_arns = generate_tool_lambda_arns(
            self.agent_tools,
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
                resources=tool_lambda_arns
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
        """Create Step Functions workflow with dynamic tool loading"""
        
        # Create input processing task
        input_processing = sfn.Pass(
            self,
            "ProcessInput",
            comment="Process input and prepare for tool loading",
            parameters={
                "tool_ids": self.agent_tools,
                "messages.$": "$.messages",
                "system.$": "$.system",
                "model.$": "$.model"
            }
        )
        
        # Create tool loading Map state
        load_tool_spec = sfn_tasks.DynamoGetItem(
            self,
            "GetToolSpec",
            table=dynamodb.Table.from_table_name(
                self,
                "ToolRegistryTable",
                table_name=self.tool_registry_table_name
            ),
            key={
                "tool_name": sfn_tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$.tool_id")
                ),
                "version": sfn_tasks.DynamoAttributeValue.from_string("latest")
            },
            result_selector={
                "name.$": "$.Item.tool_name.S",
                "description.$": "$.Item.description.S",
                "input_schema.$": "States.StringToJson($.Item.input_schema.S)",
                "lambda_arn.$": "$.Item.lambda_arn.S"
            }
        )
        
        load_tools = sfn.Map(
            self,
            "LoadToolSpecs",
            comment="Load tool specifications from registry",
            items_path="$.tool_ids",
            parameters={
                "tool_id.$": "$"
            }
        )
        load_tools.iterator(load_tool_spec)
        
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
                "system.$": "$.system",
                "messages.$": "$.messages",
                "tools.$": "$.tools",
                "model.$": "$.model"
            }),
            result_path="$.llm_response"
        )
        
        # Create tool execution choice
        tool_execution_choice = sfn.Choice(
            self,
            "ProcessLLMResponse",
            comment="Check if LLM wants to use a tool"
        )
        
        # Create tool execution task
        find_tool_lambda = sfn.Pass(
            self,
            "FindToolLambda",
            comment="Find the Lambda ARN for the requested tool",
            parameters={
                "tool_lambda_arn.$": "$.tools[?(@.name == $.llm_response.Payload.body.function_calls[0].name)].lambda_arn | [0]",
                "tool_input.$": "$.llm_response.Payload.body.function_calls[0]",
                "messages.$": "$.llm_response.Payload.body.messages",
                "tools.$": "$.tools",
                "system.$": "$.system",
                "model.$": "$.model"
            }
        )
        
        # For now, we'll use a Choice state to handle tool routing
        # In the future, this can be enhanced with dynamic Lambda invocation
        # Both tools are handled by the same Lambda (db-interface)
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
                "id.$": "$.tool_input.id",
                "name.$": "$.tool_input.name",
                "input.$": "$.tool_input.input",
                "type": "tool_use"
            }),
            result_path="$.tool_result"
        )
        
        
        # Create tool result processing
        process_tool_result = sfn.Pass(
            self,
            "ProcessToolResult",
            comment="Add tool result to messages",
            parameters={
                "messages.$": "States.ArrayConcat($.messages, [$.tool_result.Payload])",
                "tools.$": "$.tools",
                "system.$": "$.system",
                "model.$": "$.model"
            }
        )
        
        # Create success state
        success = sfn.Succeed(
            self,
            "Success",
            comment="SQL agent workflow completed successfully"
        )
        
        # Create failure state
        failure = sfn.Fail(
            self,
            "Failure",
            comment="SQL agent workflow failed"
        )
        
        # Connect the states
        definition = (
            input_processing
            .next(load_tools)
            .next(sfn.Pass(
                self,
                "PrepareForLLM",
                parameters={
                    "tools.$": "$",
                    "messages.$": "$.messages",
                    "system.$": "$.system",
                    "model.$": "$.model"
                }
            ))
            .next(call_llm)
            .next(tool_execution_choice)
        )
        
        # Add choice conditions
        tool_execution_choice.when(
            sfn.Condition.is_present("$.llm_response.Payload.body.function_calls[0]"),
            find_tool_lambda
            .next(execute_db_tool)
            .next(process_tool_result)
            .next(call_llm)
        ).otherwise(success)
        
        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self,
            "SQLAgentStateMachine",
            state_machine_name=f"sql-agent-{self.env_name}",
            definition=definition,
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )