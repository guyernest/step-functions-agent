from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class AnalysisAgentStack(Stack):

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

        # Clustering lambda from function name
        clustering_lambda_function = _lambda.Function.from_function_name(
            self,
            "ClusteringLambda",
            "ClusteringTools"
        )

        # Create the code interpreter lambda function from the name of the function
        code_interpreter_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CodeInterpreter", 
            "CodeInterpreter"
        )

        # The execution role for the lambda
        analysis_lambda_role = iam.Role(
            self,
            "AnalysisLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant the lambda access to the yfinance output bucket
        yfinance_output_bucket.grant_read(analysis_lambda_role)

        ## Analysis Tools in Java
        # Java Lambda
        analysis_lambda = _lambda.Function(
            self, 
            "AnalysisLambda",
            function_name="AnalysisTools",
            description="Time series analysis tools using Java.",
            code=_lambda.Code.from_asset("lambda/tools/stock-analyzer/target/stock-analyzer-lambda-1.0-SNAPSHOT.jar"), 
            handler="tools.StockAnalyzerLambda::handleRequest",
            runtime=_lambda.Runtime.JAVA_17,
            architecture=_lambda.Architecture.ARM_64,
            timeout=Duration.seconds(30), 
            memory_size=512,
            role=analysis_lambda_role
        )


        # Define the Step Functions state machine

        # Create yfinance tools
        stock_analysis_tools = [
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
                name="calculate_moving_average",
                description="Use this tool to calculate moving average for a given time series set. The input is a file in S3 with the time series data",
                lambda_function=analysis_lambda,
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
            ),
            Tool(
                "execute_python", 
                "Execute python code in a Jupyter notebook cell and return the URL of the image that was created.",
                code_interpreter_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The python code to execute in a single cell."
                        }
                    },
                    "required": [
                        "code"
                    ]
                }
            ),
            Tool(
                name="calculate_hdbscan_clusters",
                description="Use this tool to calculate clustering for a given time series. The input is a file in S3 with the time series data",
                lambda_function=clustering_lambda_function,
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
        You are an expert financial analyst, with specialization in the stock market. 
        Your job is to help users with their questions about the stock market. 
        You have access to a set of tools, but only use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        """

        analysis_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "AnalysisStateMachine",
            state_machine_name="AnalysisAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=stock_analysis_tools,
            system_prompt=system_prompt,
            output_schema={
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The answer to the question"
                    },
                    "chart": {
                        "type": "string",
                        "description": "The URL of the chart"
                    }
                },
                "required": [
                    "answer",
                    "chart"
                ]
            }
        )