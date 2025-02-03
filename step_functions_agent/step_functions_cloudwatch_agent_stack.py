from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    SecretValue,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool, LLMProviderEnum

class CloudWatchAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallNovaLLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLM", 
            call_llm_function_name
        )

        ### Tools Lambda Functions

        #### CloudWatch Tools

        cloudwatch_lambda_role = iam.Role(
            self, "CloudWatchToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                "CloudWatchToolLambdaPolicy",
                managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            ]
        )

       # Grant the Lambda function permission to access CloudWatch Logs
        cloudwatch_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:DescribeLogGroups",
                    "logs:ListTagsLogGroup",
                    "logs:StartQuery",
                    "logs:StopQuery",
                    "logs:GetQueryResults",
                    "logs:DescribeQueries",
                ],
                resources=[
                    "*"
                ]
            )
        )
        # Define the Lambda function
        cloudwatch_lambda_function = _lambda_python.PythonFunction(
            self, 
            "CloudWatchToolLambdaFunction",
            function_name="CloudWatchToolLambdaFunction",
            description="Explore and query a CloudWatch Log Group.",
            entry="lambda/tools/cloudwatch-queries",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=128,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=cloudwatch_lambda_role,
        )

        # Define the Step Functions state machine

        # Create graphql tools
        cloudwatch_tools = [
            Tool(
                "find_log_groups_by_tag",
                "Finds the relevant log group to query based on a specific tag.",
                cloudwatch_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "tag_name": {
                            "type": "string",
                            "description": "The name of the tag, such as 'application' or 'environment'."
                        },
                        "tag_value": {
                            "type": "string",
                            "description": "The value of the tag, such as 'shipping' or 'production'."
                        }
                    },
                    "required": [
                        "tag_name",
                        "tag_value"
                    ]
                }
            ),
            Tool(
                "get_query_generation_prompt",
                "Get the prompt to generate a CloudWatch Insights query, including examples and instructions.",
                cloudwatch_lambda_function,
            ),
            Tool(
                "execute_query",
                "Execute a CloudWatch Insights query to allow retrival of relevant log data for an analysis.",
                cloudwatch_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "log_groups": {
                            "type": "list",
                            "description": "The list of log groups to query."
                        },
                        "query": {
                            "type": "string",
                            "description": "The CloudWatch Insights query to execute."
                        },
                        "time_range": {
                            "type": "string",
                            "description": "The time range to query, such as 'last_hour', 'last_day', 'last_week', 'last_month'."
                        }
                    },
                    "required": [
                        "log_groups",
                        "query",
                        "time_range"
                    ]
                }
            )
        ]  # type: list[Tool]

        system_prompt="""
        You are an expert software system analyst with deep knowledge root cause analysis.
        You are working with a user who is trying to understand the root cause of a problem in a software system
         
        Your job is to help users understand what is happening to their systems based on the log data.
        You have access to a set of tools, and please use them when needed. 
        One of the tools can give you examples and instructions on how to use CloudWatch Insights queries.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn.
        Please use the generate_query_prompt tool to generate the prompt for a CloudWatch Insights query, including the query examples.
        Please use the execute_query tool to retrieve relevant log data from CloudWatch Insights.
        Answer only based on the retrived log data.
        """  # type: str

        cloudwatch_insights_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "CloudWatchAIStateMachine",
            state_machine_name="CloudWatchAIStateMachine",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=cloudwatch_tools,
            system_prompt=system_prompt,
        )