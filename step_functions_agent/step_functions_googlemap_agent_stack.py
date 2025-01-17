from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_nodejs as nodejs_lambda,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool, LLMProviderEnum

class GoogleMapAgentStack(Stack):

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

        # The execution role for the lambda
        google_maps_lambda_role = iam.Role(
            self,
            "GoogleMapsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant the lambda access to the secrets with the API keys for the LLM
        google_maps_lambda_role.add_to_policy(
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

        ## Google Maps Tools in Typescript
        # TypeScript Lambda
        google_maps_lambda = nodejs_lambda.NodejsFunction(
            self, 
            "GoogleMapsLambda",
            function_name="GoogleMaps",
            description="Lambda function to execute Google Maps API calls.",
            timeout=Duration.seconds(30),
            entry="lambda/tools/google-maps/src/index.ts", 
            handler="handler",  # Name of the exported function
            runtime=_lambda.Runtime.NODEJS_18_X,
            architecture=_lambda.Architecture.ARM_64,
            # Optional: Bundle settings
            bundling=nodejs_lambda.BundlingOptions(
                minify=True,
                source_map=True,
            ),
            role=google_maps_lambda_role
        )

        # Define the Step Functions state machine

        provider = LLMProviderEnum.ANTHROPIC

        # Create yfinance tools
        google_maps_tools = [
            Tool(
                "maps_geocode",
                "Convert an address into geographic coordinates.",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "The address to geocode."
                        }
                    },
                    "required": [
                        "address"
                    ]
                }
            ),
            Tool(
                "maps_reverse_geocode",
                "Convert coordinates into an address.",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude coordinate."
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude coordinate."
                        }
                    },
                    "required": [
                        "latitude",
                        "longitude"
                    ]
                }
            ),
            Tool(
                "maps_search_places",
                "Search for places using Google Places API",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for places."
                        },
                        "location": {
                            "type": "object",
                            "properties": {
                                "latitude": {
                                    "type": "number",
                                    "description": "The latitude coordinate of the center point."
                                },
                                "longitude": {
                                    "type": "number",
                                    "description": "The longitude coordinate of the center point."
                                }
                            },
                            "description": "Optional center point for the search"
                        },
                        "radius": {
                            "type": "number",
                            "description": "Optional radius in meters for the search (max 50000)."
                        }
                    },
                    "required": [
                        "query"
                    ]
                }
            ),
            Tool(
                "maps_place_details",
                "Get detailed information about a specific place",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "place_id": {
                            "type": "string",
                            "description": "The place ID of the place."
                        }
                    },
                    "required": [
                        "place_id"
                    ]
                }
            ),
            Tool(
                "maps_distance_matrix",
                "Calculate travel distance and time for multiple origins and destinations",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "origins": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Array of origin addresses or coordinates."
                        },
                        "destinations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Array of destination addresses or coordinates."
                        },
                        "mode": {
                            "type": "string",
                            "description": "Optional mode of travel (driving, walking, transit, or bicycling).",
                            "enum": ["driving", "walking", "transit", "bicycling"]
                        }
                    },
                    "required": [
                        "origins",
                        "destinations"
                    ]
                }
            ),
            Tool(
                "maps_elevation",
                "Get elevation data for locations on the earth",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "locations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "latitude": {
                                        "type": "number",
                                        "description": "The latitude coordinate."
                                    },
                                    "longitude": {
                                        "type": "number",
                                        "description": "The longitude coordinate."
                                    }
                                },
                                "required": [
                                    "latitude",
                                    "longitude"
                                ]
                            },
                            "description": "Array of locations to get elevation data for."
                        }
                    },
                    "required": [
                        "locations"
                    ]
                }
            ),
            Tool(
                "maps_directions",
                "Get directions between two points",
                google_maps_lambda,
                provider=provider,
                input_schema={
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "The origin address or coordinates."
                        },
                        "destination": {
                            "type": "string",
                            "description": "The destination address or coordinates."
                        },
                        "mode": {
                            "type": "string",
                            "description": "Optional mode of travel (driving, walking, transit, or bicycling).",
                            "enum": ["driving", "walking", "transit", "bicycling"]
                        }
                    },
                    "required": [
                        "origin",
                        "destination"
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

        google_maps_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "GoogleMapsAIStateMachine",
            state_machine_name="GoogleMapsAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            provider=provider,
            tools=google_maps_tools,
            system_prompt=system_prompt,
        )