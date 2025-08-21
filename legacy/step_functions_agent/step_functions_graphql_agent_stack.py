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
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class GraphQLAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Create the secret for the API keys from the local .env file

        # Reading the API KEYs for the LLM and related services for each line in the .env file
        with open("lambda/tools/graphql-interface/.env", "r") as f:
            secret_values = {}
            for line in f:
                if line.startswith("#") or line.strip() == "":
                    continue
                key, value = line.strip().split("=", 1)
                secret_values[key] = SecretValue.unsafe_plain_text(value)
                # Decide if you add a secret or as a parameter
                if key.endswith("_API_KEY") or key.endswith("_KEY"):
                    api_key_secret = secretsmanager.Secret(self, "GraphQLToolAPIKeysSecret", 
                        secret_name="/ai-agent/graphql-tool/keys",
                        secret_object_value=secret_values,
                        removal_policy=RemovalPolicy.DESTROY
                    )
                else:
                    endpoint_parameter = ssm.StringParameter(self, "GraphQLEndpointParameter",
                        parameter_name="/ai-agent/graphql-tool/graphql-endpoint",
                        string_value=value,
                        tier=ssm.ParameterTier.STANDARD,
                        description="GraphQL endpoint for the AI Agent",
                    )


        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallOpenAILLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLM", 
            call_llm_function_name
        )

        ### Tools Lambda Functions

        #### GraphQL Tools

        graphql_lambda_role = iam.Role(
            self, "GraphQLToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "GraphQLToolLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        api_key_secret.grant_read(graphql_lambda_role)
        endpoint_parameter.grant_read(graphql_lambda_role)

        # Define the Lambda function
        graphql_lambda_function = _lambda_python.PythonFunction(
            self, 
            "GraphQLToolLambdaFunction",
            function_name="GraphQLToolLambdaFunction",
            description="Explore and query a GraphQL API.",
            entry="lambda/tools/graphql-interface",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=128,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=graphql_lambda_role,
        )

        # Adding test event to the lambda function in EventBridge
        graphql_function_test_event = events.Rule(
            self,
            "GraphQLFunctionTestEvent",
            rule_name="GraphQLFunctionTestEvent",
            description="Test event for the GraphQL Lambda function",
            schedule=events.Schedule.rate(Duration.days(1)),
            targets=[
                targets.LambdaFunction(
                    handler=graphql_lambda_function,
                    event=events.RuleTargetInput.from_object(
                        {
                            "id": "uniquetooluseid",
                            "input": {
                                "graphql_query": "query test { organization { name } }"
                            },
                            "name": "execute_graphql_query",
                            "type": "tool_use"
                        }
                    )
                )
            ]
        )

        # Define the Step Functions state machine

        # Create graphql tools
        graphql_tools = [
            Tool(
                "generate_query_prompt",
                "Generate the prompt for a GraphQL query, including the API schema and query examples.",
                graphql_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "The question of the user to be answered."
                        }
                    },
                    "required": [
                        "description",
                    ]
                }
            ),
            Tool(
                "execute_graphql_query",
                "Execute a GraphQL query to allow retrival of relevant policies from the GraphQL API.",
                graphql_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "graphql_query": {
                            "type": "string",
                            "description": "The GraphQL query to execute."
                        }
                    },
                    "required": [
                        "gql_query"
                    ]
                }
            )
        ]  # type: list[Tool]

        system_prompt="""
        You are an expert business analyst with deep knowledge policies and regulations.
         
        Your job is to help users understand what are the policies in the domain of alcohol shipping. 
        The policies are defined only on the destination country. 
        For example, when shipping from Atlanta to Seattle, the policies are relevant only for Washington state.
        You have access to a set of tools, and please use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        Please use the generate_query_prompt tool to generate the prompt for a GraphQL query, including the API schema and query examples.
        Please use the execute_graphql_query tool to retrieve relevant policies from the GraphQL API.
        Answer only based on the retrived policies. Please remember that the policies are built on a hierarchy.
        """

        graphql_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "GraphQLAIStateMachine",
            state_machine_name="GraphQLAIAgentStateMachine",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=graphql_tools,
            system_prompt=system_prompt,
            output_schema={
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The answer to the question"
                    }
                },
                "required": [
                    "answer",
                ]
            }
        )