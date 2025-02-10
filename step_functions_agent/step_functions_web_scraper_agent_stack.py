from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_nodejs as nodejs_lambda,
    BundlingOptions,
    DockerImage
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class WebScraperAgentStack(Stack):

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

        # Chromium Lambda Layer
        chromium_layer = _lambda.LayerVersion(
            self,
            "ChromiumLayer",
            code=_lambda.Code.from_asset(
                path=".",  # Path where the bundling will occur
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("node:18"),
                    command=[
                        "bash", "-c",
                        """
                        # Create working directory
                        mkdir -p /asset-output/nodejs
                        cd /asset-output/nodejs
                        
                        # Create package.json
                        echo '{"dependencies":{"@sparticuz/chromium":"132.0.0"}}' > package.json
                        
                        # Install dependencies
                        npm install --arch=x86_64 --platform=linux
                        
                        # Clean up unnecessary files to reduce layer size
                        find . -type d -name "test" -exec rm -rf {} +
                        find . -type f -name "*.md" -delete
                        find . -type f -name "*.ts" -delete
                        find . -type f -name "*.map" -delete
                        """
                    ],
                    user="root"
                )
            ),
            compatible_runtimes=[_lambda.Runtime.NODEJS_18_X],
            description="Layer containing Chromium binary for web scraping"
        )

        # The execution role for the lambda
        web_scraper_lambda_role = iam.Role(
            self,
            "WebScraperLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        ## Web Scraper Tools in Typescript
        # TypeScript Lambda
        web_scraper_lambda = nodejs_lambda.NodejsFunction(
            self, 
            "WebScraperLambda",
            function_name="WebScraperLambda",
            description="Lambda function to operate headless browser to scrape web pages.",
            timeout=Duration.seconds(30),
            code=_lambda.Code.from_asset("lambda/tools/web-scraper/dist"),
            # entry="lambda/tools/web-scraper/src/index.ts", 
            handler="index.handler",  # Name of the exported function
            layers=[chromium_layer],
            runtime=_lambda.Runtime.NODEJS_18_X,
            memory_size=512,            
            # Optional: Bundle settings
            bundling=nodejs_lambda.BundlingOptions(
                minify=True,
                source_map=True,
            ),
            role=web_scraper_lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
        )

        # Define the Step Functions state machine

        # Create Web Scraper tools
        web_scraper_tools = [
            Tool(
                "web_scrape",
                "Search a website and return the results.",
                web_scraper_lambda,
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                        },
                        "selectors": {
                           "type": "object",
                           "properties": {
                              "searchInput": {
                                "type": "string"
                                },
                                "searchButton": {
                                    "type": "string"
                                },
                                "resultContainer": {
                                    "type": "string"
                                }
                           }
                                
                        },
                        "searchTerm": {
                            "type": "string",
                            "description": "The address to geocode."
                        }
                    },
                    "required": [
                        "url"
                    ]
                }
            )
        ]

        system_prompt="""
        You are an expert navigation agent with deep knowledge of Google Maps. 
        Your job is to help users navigate and find interesting places using Google Maps. 
        You have access to a set of tools, but only use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        """

        web_scraper_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "WebScraperAIStateMachine",
            state_machine_name="WebScraperAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=web_scraper_tools,
            system_prompt=system_prompt,
        )

        self.tool_functions = [
            web_scraper_lambda.function_name,
        ]

        self.agent_flows = [
            web_scraper_agent_flow.state_machine_name,
        ]
