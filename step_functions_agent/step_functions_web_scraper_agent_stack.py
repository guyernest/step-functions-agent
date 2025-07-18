from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_lambda_nodejs as nodejs_lambda,
    BundlingOptions,
    DockerImage
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class WebScraperAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## Create the DynamoDB table for the long content extension
        dynamodb_long_content_table = dynamodb.Table(
            self, 
            "LongContentDynamoDBTable",
            table_name=f"LongContentDynamoDBTable-{self.account}-{self.region}",
            partition_key=dynamodb.Attribute(
                name="id", 
                type=dynamodb.AttributeType.STRING
            ),
            # Adding TTL for the records to be deleted after 1 hour
            time_to_live_attribute="ttl",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        ## Call LLM Lambda with long content extension  ######

        ### Create Log Group to be used by the lambdas and step functions
        log_group = logs.LogGroup(
            self, 
            "WebScraperAgentLogGroup", 
            retention=logs.RetentionDays.ONE_WEEK
        )

        # The default execution role for the lambda
        call_llm_lambda_role = iam.Role(
            self,
            "CallLLMLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant the lambda access to the secrets with the API keys for the LLM
        call_llm_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/ai-agent/*",
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/api-keys*"
                ]
            )
        )

        dynamodb_long_content_table.grant_read_write_data(call_llm_lambda_role)

        call_llm_function_name = "CallClaudeLLMwithExtension"

        llm_layer = _lambda_python.PythonLayerVersion(
            self, "LLMLayer",
            entry="lambda/call_llm/lambda_layer/python",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            description="A layer for the LLM Lambda functions",
        )

        ### Get the extension layer from its name (we will create it here later)
        # TODO: Create the extension layer in the CDK stacks

        extension_layer_arm_version = 17

        extension_layer_arm = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ExtensionLayerArm",
            layer_version_arn=f"arn:aws:lambda:{self.region}:{self.account}:layer:lambda-runtime-api-proxy-arm-dev:{extension_layer_arm_version}"
        )

        ### Define the Lambda function
        call_llm_lambda_function = _lambda_python.PythonFunction(
            self, 
            "CallLLMLambdaClaude",
            # Name of the Lambda function that will be used by the agents to find the function.
            function_name=call_llm_function_name,
            description="Lambda function to Call LLM (Anthropic) with messages history, tools, and long content extension.",
            entry="lambda/call_llm/functions/anthropic_llm",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="claude_lambda.py",
            handler="lambda_handler",
            layers=[
                llm_layer,
                extension_layer_arm
            ],
            environment={
                "AGENT_CONTEXT_TABLE": dynamodb_long_content_table.table_name,
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
            },
            architecture=_lambda.Architecture.ARM_64,
            log_group=log_group,
            role=call_llm_lambda_role,
            tracing= _lambda.Tracing.ACTIVE,
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

        dynamodb_long_content_table.grant_read_write_data(web_scraper_lambda_role)

        extension_layer_x86_version = 8
        extension_layer_x86 = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ExtensionLayerX86",
            layer_version_arn=f"arn:aws:lambda:{self.region}:{self.account}:layer:lambda-runtime-api-proxy-x86-dev:{extension_layer_x86_version}"
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
            layers=[
                chromium_layer,
                extension_layer_x86
            ],
            environment={
                "AGENT_CONTEXT_TABLE": dynamodb_long_content_table.table_name,
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
            },
            runtime=_lambda.Runtime.NODEJS_18_X,
            memory_size=512,            
            # Optional: Bundle settings
            bundling=nodejs_lambda.BundlingOptions(
                minify=True,
                source_map=True,
            ),
            log_group=log_group,
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
                            "description": "The URL of the webpage to scrape"
                        },
                        "actions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["search", "click", "hover", "select", "type", "wait", "waitForSelector", "clickAndWaitForSelector"],
                                        "description": "The type of action to perform"
                                    }
                                },
                            },
                            "description": "Array of actions to perform on the webpage"
                        },
                        "extractSelectors": {
                            "type": "object",
                            "properties": {
                                "containers": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "CSS selectors for container elements"
                                },
                                "text": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "CSS selectors for text elements"
                                },
                                "links": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "CSS selectors for link elements"
                                },
                                "images": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "CSS selectors for image elements"
                                }
                            },
                            "description": "Selectors for elements to extract"
                        },
                        "screenshotSelector": {
                            "type": "string",
                            "description": "CSS selector for element to screenshot"
                        },
                        "fullPageScreenshot": {
                            "type": "boolean",
                            "description": "Whether to take a screenshot of the full page"
                        }
                    },
                    "required": [
                        "url"
                    ]
                }
            )
        ]

        system_prompt="""
        You are an expert navigation agent with deep knowledge of HTML and CSS. 
        Your job is to help users navigate, search and extract information from websites. 
        You have access to a set of tools, but only use them when needed.
        Here are some instructions about the tools you have access to:
        - web_scrape: This tool allows you to navigate a website and extract information from it. It takes a JSON object as input with the following fields:
            - url: The URL of the website to navigate.
            - actions: A list of actions to perform on the website. Each action is a JSON object with the following fields:
                - type: The type of action to perform. Can be one of the following: search, click, hover, select, type, wait, waitForSelector, clickAndWaitForSelector.
                - selector: The CSS selector of the element to perform the action on.
                - value: The value to type or search for. Only used for type and search actions.
                - waitTime: The time to wait in milliseconds. Only used for wait action.
                - waitForSelector: The CSS selector of the element to wait for. Only used for waitForSelector and clickAndWaitForSelector actions.
            - extractSelectors: A JSON object with the following fields:
                - containers: A list of CSS selectors of the containers to extract.
                - text: A list of CSS selectors of the text elements to extract.
                - links: A list of CSS selectors of the links to extract.
                - images: A list of CSS selectors of the images to extract.
            - screenshotSelector: The CSS selector of the element to take a screenshot of.
            - fullPageScreenshot: A boolean indicating whether to take a full page screenshot or not.

        Let's see some examples for actions:
        // Click a link or button
        { "type": "click", "selector": "#submit-button", "waitForNavigation": true }

        // Search using a form
        { "type": "search", "searchInput": "#search-box", "searchButton": "#search-submit", "searchTerm": "query" }

        // Click and wait for a specific element to appear
        { "type": "clickAndWaitForSelector", "clickSelector": ".load-more", "waitForSelector": ".results-item" }

        // Hover over an element (useful for dropdown menus)
        { "type": "hover", "selector": ".dropdown-menu" }

        // Select an option from a dropdown
        { "type": "select", "selector": "#country-select", "value": "USA" }

        // Type text into an input field
        { "type": "type", "selector": "#username", "text": "johndoe" }

        // Wait for a specific amount of time (in milliseconds)
        { "type": "wait", "timeMs": 2000 }

        // Wait for a specific element to appear
        { "type": "waitForSelector", "selector": ".lazy-loaded-content" }

        Let's see some examples for extractSelectors:
        "extractSelectors": {
            // Extract text content from container elements
            "containers": [".article-header", ".article-body", ".footer"],
            
            // Extract text from elements (returns an array of text content for each matching element)
            "text": [".news-item h3", ".product-price"],
            
            // Extract links with their href and text
            "links": ["nav a", ".pagination a"],
            
            // Extract images with their src and alt attributes
            "images": [".gallery img", ".product-image"]
        }

        ### Direct URL Navigation

        For sites with complex forms or search functionality, it's often better to navigate directly to the target URL rather than trying to fill out forms. For example, to get weather for New York:

        ```json
        // Instead of this (which might not work due to form behavior):
        "actions": [
        { "type": "type", "selector": "#searchbox", "text": "New York, NY" },
        { "type": "click", "selector": "#submit" }
        ]

        // Use direct URL navigation instead:
        "url": "https://forecast.weather.gov/MapClick.php?lat=40.7142&lon=-74.0059"
        ```

        ### Guidelines for Using This Tool

        #### Exploration Phase

        * Start with a basic request to understand the site structure
        * Request a full page screenshot to see the visual layout
        * Examine HTML content to identify key selectors and elements
        * Look for forms, navigation elements, and content containers

        #### Refinement Phase

        * Create more targeted requests with specific selectors
        * Use navigation actions to reach deeper content
        * Extract only the relevant information
        * Create a reusable script for similar future tasks

        ####Documentation Phase

        * Document the selectors and navigation steps that worked
        * Create a template for similar websites
        * Note any challenges or anti-bot measures encountered

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

        self.log_group_name = log_group.log_group_name