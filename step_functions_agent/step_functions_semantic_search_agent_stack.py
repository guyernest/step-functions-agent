from aws_cdk import (
    Stack,
    RemovalPolicy,
    SecretValue,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_lambda as _lambda,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class SemanticSearchAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Create the secret for the API keys from the local .env file

        # Reading the API KEYs for the LLM and related services for each line in the .env file
        with open("lambda/tools/SemanticSearchRust/.env", "r") as f:
            secret_values = {}
            for line in f:
                if line.startswith("#") or line.strip() == "":
                    continue
                key, value = line.strip().split("=", 1)
                secret_values[key] = SecretValue.unsafe_plain_text(value)
                # Decide if you add a secret or as a parameter
                if key.endswith("_KEY"):
                    api_key_secret = secretsmanager.Secret(self, "SemanticSearchToolAPIKeysSecret", 
                        secret_name="/ai-agent/semantic_search",
                        secret_object_value=secret_values,
                        removal_policy=RemovalPolicy.DESTROY
                    )
                else:
                    endpoint_parameter = ssm.StringParameter(self, "SemanticSearchEndpointParameter",
                        parameter_name="/ai-agent/qdrant/qdrant_endpoint",
                        string_value=value,
                        tier=ssm.ParameterTier.STANDARD,
                        description="Qdrant Semantic Search endpoint for the AI Agent",
                    )


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

        # The execution role for the lambda
        tools_lambda_role = iam.Role(
            self,
            "SemanticSearchToolsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        api_key_secret.grant_read(tools_lambda_role)
        endpoint_parameter.grant_read(tools_lambda_role)

        # Add the policy to allow the lambda to access the secrets manager for the API keys
        # TODO: make it more robust as the name of the secret is hardcoded
        tools_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/api-keys*"
                ]
            )
        )
        # Add the policy to allow the lambda to access the parameter store for the endpoint

        ## Forecasting Tools in Rust
        # Rust Lambda
        tools_lambda = _lambda.Function(
            self, 
            "SemanticSearchToolsLambda",
            function_name="SemanticSearchTools",
            description="Semantic Search to Qdrant Vector Database tools using Rust.",
            code=_lambda.Code.from_asset("lambda/tools/SemanticSearchRust/target/lambda/SemanticSearchRust"), 
            handler="main",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            role=tools_lambda_role
        )


        # Define the Step Functions state machine

        # Create semantic search tools
        tools = [
            Tool(
                "semantic_search_rust",
                "Search for relevant documents that can answer the user's query.",
                tools_lambda,
                input_schema={
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "The search query to use for the semantic search."
                        }
                    },
                    "required": [
                        "search_query"
                    ]
                }
            ),

        ] # end of tools list

        system_prompt="""
        You are an expert document analyst, with specialization in answer questions based on retrieved documents. 
        Your job is to help users with their questions from the documents you have access to. 
        You have access to a set of tools, please use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        """

        semantic_search_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "SemanticSearchAgentStateMachine",
            state_machine_name="SemanticSearchAgentWithToolsAndNova",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=tools,
            system_prompt=system_prompt,
        )

        self.tool_functions = [
            tools_lambda.function_name,
        ]

        self.agent_flows = [
            semantic_search_agent_flow.state_machine_name,
        ]
