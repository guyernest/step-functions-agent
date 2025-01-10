from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_lambda_go_alpha as _lambda_go,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool, LLMProviderEnum

class ResearchAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallLLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLM", 
            call_llm_function_name
        )

        ### Tools Lambda Functions

        ## yfinance Tool from function name
        yfinance_lambda_function = _lambda.Function.from_function_name(
            self,
            "YFinanceLambda",
            "YFinance"
        )

        # The execution role for the lambda
        research_lambda_role = iam.Role(
            self,
            "ResearchLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant the lambda access to the secrets with the API keys for Perplexity
        research_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/ai-agent/*",
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/*"
                ]
            )
        )

        ## Research Tools in Go
        # Rust Lambda
        research_lambda = _lambda_go.GoFunction(
            self, 
            "ResearchLambda",
            function_name="ResearchTools",
            description="Stock market stock research tools using Go and Perplexity.",
            entry="lambda/tools/web-research/", 
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(120),
            role=research_lambda_role
        )

        # Define the Step Functions state machine

        provider = LLMProviderEnum.ANTHROPIC

        # Create research tools
        research_tools = [
            Tool(
                "list_industries",
                "List the industries for a given sector key.",
                yfinance_lambda_function,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "sector_key": {
                            "type": "string",
                            "description": "The sector key of the industry. Valid sectors: real-estate, healthcare, financial-services, technology, consumer-cyclical, consumer-defensive, basic-materials, industrials, energy, utilities, communication-services"
                        }
                    },
                    "required": [
                        "sector_key"
                    ]
                }
            ),
            Tool(
                "top_industry_companies",
                "Get the top companies for a given industry key.",
                yfinance_lambda_function,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "industry_key": {
                            "type": "string",
                            "description": "The industry key of the industry."
                        }
                    },
                    "required": [
                        "industry_key"
                    ]
                }
            ),
            Tool(
                "top_sector_companies",
                "Get the top companies for a given sector key.",
                yfinance_lambda_function,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "sector_key": {
                            "type": "string",
                            "description": "The sector key of the industry."
                        }
                    },
                    "required": [
                        "sector_key"
                    ]
                }
            ),
            Tool(
                name="research_company",
                description="Perform stock market stock research on a given company.",
                lambda_function=research_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "The name of the company to research."
                        },
                        "topics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "The topics to research, such as recent financial performance, market position, etc."
                            }
                        }
                    },
                    "required": [
                        "company"
                    ]
                }
            )
        ]

        system_prompt="""
        You are an expert financial analyst, with specialization in web research. 
        Your job is to help users with their research needs on the stock market. 
        You have access to a set of tools, but only use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        """

        research_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "ResearchStateMachine",
            state_machine_name="ResearchAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            provider=provider,
            tools=research_tools,
            system_prompt=system_prompt,
        )