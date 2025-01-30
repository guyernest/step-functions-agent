from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool, LLMProviderEnum

class ClusteringAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallClaudeLLM"

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

        ## yfinance output bucket
        yfinance_output_bucket = s3.Bucket.from_bucket_name(
            self,
            "YFinanceOutputBucket",
            f"yfinance-data-{self.account}-{self.region}"
        )

        # The execution role for the lambda
        clustering_lambda_role = iam.Role(
            self,
            "ClusteringLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant the lambda access to the yfinance output bucket
        yfinance_output_bucket.grant_read(clustering_lambda_role)

        ## Forecasting Tools in Rust
        # Rust Lambda
        clustering_lambda = _lambda.Function(
            self, 
            "ClusteringLambda",
            function_name="ClusteringTools",
            description="Time Series Clustering tools using Rust.",
            code=_lambda.Code.from_asset("lambda/tools/rust-clustering/target/lambda/rust-clustering"), 
            handler="main",
            runtime=_lambda.Runtime.PROVIDED_AL2023,
            architecture=_lambda.Architecture.ARM_64,
            role=clustering_lambda_role
        )


        # Define the Step Functions state machine

        provider = LLMProviderEnum.ANTHROPIC

        # Create yfinance tools
        clustering_tools = [
            Tool(
                "download_tickers_data",
                "Download the data for a list of tickers for the last number of days, put them in S3 bucket for further processing",
                yfinance_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "tickers": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "The ticker symbol of the stock."
                            },
                            "description": "The list of tickers to download data for."
                        },
                        "days": {
                            "type": "number",
                            "description": "The number of days to download data for."
                        }
                    },
                    "required": [
                        "tickers",
                        "days"
                    ]
                }
            ),
            Tool(
                "list_industries",
                "List the industries for a given sector key.",
                yfinance_lambda_function,
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
                name="calculate_hdbscan_clusters",
                description="Use this tool to calculate clustering for a given time series. The input is a file in S3 with the time series data",
                lambda_function=clustering_lambda,
                input_schema={
                    "type": "object",
                    "properties": {
                        "bucket": {
                            "type": "string",
                            "description": "The bucket where the time series data is stored."
                        },
                        "key": {
                            "type": "string",
                            "description": "The key of the file object where the time series data is stored."
                        }
                    },
                    "required": [
                        "bucket",
                        "key",
                    ]
                }
            )

        ]

        system_prompt="""
        You are an expert financial analyst, with specialization in forecasting. 
        Your job is to help users with their forecasting needs on the stock market. 
        You have access to a set of tools, but only use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        """

        clustering_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "ClusteringStateMachine",
            state_machine_name="ClusteringAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            provider=provider,
            tools=clustering_tools,
            system_prompt=system_prompt,
        )