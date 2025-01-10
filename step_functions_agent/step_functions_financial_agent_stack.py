from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool, LLMProviderEnum

class FinancialAgentStack(Stack):

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

        #### Code Interpreter Tools

        # Create the code interpreter lambda function from the name of the function
        code_interpreter_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CodeInterpreter", 
            "CodeInterpreter"
        )

        # yfiance tools

        # Create the bucket for yfinance data
        yfinance_bucket = s3.Bucket(
            self, "YFinanceBucket",
            bucket_name=f"yfinance-data-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create the yfinance lambda function

        yfinance_lambda_role = iam.Role(
            self, "YFinanceLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "YFinanceLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        yfinance_bucket.grant_read_write(yfinance_lambda_role)

        yfinance_lambda_function = _lambda_python.PythonFunction(
            self, "YFinanceLambda",
            function_name="YFinance",
            description="Get stock data from Yahoo Finance, using Yfinance library.",
            entry="lambda/tools/yfinance",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=512,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "DATA_BUCKET_NAME": yfinance_bucket.bucket_name,
            },
            role=yfinance_lambda_role,
        )

        # Define the Step Functions state machine

        provider = LLMProviderEnum.ANTHROPIC

        # Create yfinance tools
        yfinance_tools = [
            Tool(
                "get_ticker_data",
                "Return the stock price of the given ticker symbol from Yahoo Finance.",
                yfinance_lambda_function,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The ticker symbol of the stock."
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The start date of the stock price."
                        },
                        "end_date": {
                            "type": "string",
                            "description": "The end date of the stock price."
                        }
                    },
                    "required": [
                        "ticker"
                    ]
                }
            ),
            Tool(
                "get_ticker_recent_history",
                "Get the recent history for a given ticker symbol over a given period and interval.",
                yfinance_lambda_function,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The ticker symbol of the stock."
                        },
                        "period": {
                            "type": "string",
                            "description": "The period to get the data for. Defaults to '1mo'. Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max Either Use period parameter or use start and end date."
                        },
                        "interval": {
                            "type": "string",
                            "description": "The interval to get the data for. Defaults to '1d'. Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days."
                        }
                    },
                    "required": [
                        "ticker"
                    ]
                }
            ),
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
                "execute_python", 
                "Execute python code in a Jupyter notebook cell and return the URL of the image that was created.",
                code_interpreter_lambda_function,
                provider=provider,
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
            )
        ]

        system_prompt="""
        You are an expert business analyst with deep knowledge financial data. 
        Your job is to help users understand and analyze stock prices. 
        You have access to a set of tools, but only use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        You also have access to a tool that allows execution of python code. 
        Use it to generate the visualizations in your analysis. 
        - the python code runs in jupyter notebook. 
        - every time you call `execute_python` tool, the python code is executed in a separate cell. 
        it's okay to multiple calls to `execute_python`. 
        - display visualizations using matplotlib directly in the notebook. don't worry about saving the visualizations to a file. 
        - you can run any python code you want, everything is running in a secure sandbox environment.
        """

        yfinance_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "YFinanceAIStateMachine",
            state_machine_name="FiancialAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            provider=provider,
            tools=yfinance_tools,
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