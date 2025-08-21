from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    SecretValue,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_lambda_nodejs as nodejs_lambda,
)
from constructs import Construct
from .ai_agent_construct_from_json import (
    ConfigurableStepFunctionsConstruct,
    Tool,
)


class BooksAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Create the secret for the API keys from the local .env file

        # Reading the API KEYs for the LLM and related services for each line in the .env file
        with open("lambda/tools/books-recommender/.env", "r") as f:
            secret_values = {}
            for line in f:
                if line.startswith("#") or line.strip() == "":
                    continue
                key, value = line.strip().split("=", 1)
                secret_values[key] = SecretValue.unsafe_plain_text(value)
                # Decide if you add a secret or as a parameter
                if key.endswith("_API_KEY") or key.endswith("_KEY"):
                    api_key_secret = secretsmanager.Secret(
                        self,
                        "BooksAPIKeysSecret",
                        secret_name="/ai-agent/book-tool/api-key",
                        secret_object_value=secret_values,
                        removal_policy=RemovalPolicy.DESTROY,
                    )

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallOpenAILLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, "CallLLM", call_llm_function_name
        )

        ### Tools Lambda Functions

        #### GraphQL Tools

        books_lambda_role = iam.Role(
            self,
            "BooksToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "BooksToolLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                )
            ],
        )

        api_key_secret.grant_read(books_lambda_role)

        # Define the Lambda function
        books_lambda_function = nodejs_lambda.NodejsFunction(
            self,
            "NYTBooksAPILambda",
            function_name="NYTBooksAPI",
            description="Lambda function to execute Books API calls.",
            timeout=Duration.seconds(30),
            entry="lambda/tools/books-recommender/src/index.ts",
            handler="handler",  # Name of the exported function
            runtime=_lambda.Runtime.NODEJS_18_X,
            architecture=_lambda.Architecture.ARM_64,
            # Optional: Bundle settings
            bundling=nodejs_lambda.BundlingOptions(
                minify=True,
                source_map=True,
            ),
            role=books_lambda_role,
        )

        # Define the Step Functions state machine

        # Create graphql tools
        books_tools = [
            Tool(
                "get_nyt_books",
                "Get the New York Times Best Sellers list for a specified genre.",
                books_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "genre": {
                            "type": "string",
                            "enum": [
                                "hardcover-fiction",
                                "hardcover-nonfiction",
                                "trade-fiction-paperback",
                                "paperback-nonfiction",
                                "combined-print-and-e-book-fiction",
                                "combined-print-and-e-book-nonfiction",
                                "e-book-fiction",
                                "e-book-nonfiction",
                                "advice-how-to-and-miscellaneous",
                                "childrens-middle-grade-hardcover",
                                "childrens-middle-grade-paperback",
                                "childrens-middle-grade-e-book",
                                "picture-books",
                                "series-books",
                                "audio-fiction",
                                "audio-nonfiction",
                                "business-books",
                                "graphic-books-and-manga",
                                "mass-market-monthly",
                                "middle-grade-paperback",
                                "young-adult-hardcover",
                                "young-adult-paperback",
                                "young-adult-e-book",
                            ],
                            "description": "The genre/category of books to retrieve (e.g., 'hardcover-fiction').",
                        }
                    },
                    "required": [
                        "genre",
                    ],
                },
            )
        ]  # type: list[Tool]

        system_prompt = """
        You are an expert in book recommendations.
         
        Your job is to help users to find interesting books to read.
        You have access to a set of tools, and please use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn.
        Please use the get_nyt_books tool to retrieve the New York Times Best Sellers list for a specified genre.
        Answer only based on the retrived books.
        """

        books_agent_flow = ConfigurableStepFunctionsConstruct(
            self,
            "BooksAIStateMachine",
            state_machine_name="BooksAIAgentStateMachine",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json",
            llm_caller=call_llm_lambda_function,
            tools=books_tools,
            system_prompt=system_prompt,
        )

        # Adding the generated lambda and step functions to self to allow monitoring stack to access them
        self.llm_functions = []

        self.tool_functions = [
            books_lambda_function.function_name,
        ]

        self.agent_flows = [
            books_agent_flow.state_machine_name,
        ]

        # self.log_group_name = log_group.log_group_name  