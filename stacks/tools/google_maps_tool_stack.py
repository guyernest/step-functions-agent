from aws_cdk import (
    Duration,
    Stack,
    Fn,
    CfnOutput,
    CustomResource,
    RemovalPolicy,
    SecretValue,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_nodejs as _lambda_nodejs,
    custom_resources as cr,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import json
import os
from pathlib import Path
from dotenv import load_dotenv


class GoogleMapsToolStack(Stack):
    """
    Google Maps Tool Stack - Deploys the Google Maps Lambda and registers all 7 tools
    
    This stack demonstrates TypeScript tool integration:
    - Deploys TypeScript Lambda with multiple tool endpoints
    - Creates tool-specific secrets from .env.google-maps
    - Registers 7 Google Maps tools in DynamoDB registry
    - Shows how one Lambda can provide multiple tools
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared infrastructure
        self._import_shared_resources()
        
        # Create tool-specific secrets
        self._create_google_maps_secrets()
        
        # Create tool Lambda
        self._create_google_maps_lambda()
        
        # Register tools in DynamoDB registry
        self._register_tools_in_registry()
        
        # Create stack exports
        self._create_stack_exports()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import tool registry table name and ARN
        self.tool_registry_table_name = Fn.import_value(
            NamingConventions.stack_export_name("Table", "ToolRegistry", self.env_name)
        )
        
        self.tool_registry_table_arn = Fn.import_value(
            NamingConventions.stack_export_name("TableArn", "ToolRegistry", self.env_name)
        )

    def _create_google_maps_secrets(self):
        """Create Google Maps tool secrets from .env.google-maps file"""
        # Load API keys from .env.google-maps file if it exists
        env_path = Path(__file__).parent.parent.parent / '.env.google-maps'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Create secret with JSON structure for Google Maps API key
        secret_value = {
            "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", "your-google-maps-api-key-here")
        }
        
        # Check if we have real API keys or just placeholders
        has_real_keys = not secret_value["GOOGLE_MAPS_API_KEY"].startswith("your-")
        
        if has_real_keys:
            # Use the real API keys from .env.google-maps file
            secret_object_value = {
                key: SecretValue.unsafe_plain_text(value)
                for key, value in secret_value.items()
            }
            
            self.google_maps_secret = secretsmanager.Secret(
                self, 
                "GoogleMapsSecrets",
                secret_name=NamingConventions.tool_secret_path("google-maps", self.env_name),
                description=f"Google Maps tool API keys for {self.env_name} environment",
                secret_object_value=secret_object_value,
                removal_policy=RemovalPolicy.DESTROY
            )
        else:
            # Use the template with placeholders
            self.google_maps_secret = secretsmanager.Secret(
                self, 
                "GoogleMapsSecrets",
                secret_name=NamingConventions.tool_secret_path("google-maps", self.env_name),
                description=f"Google Maps tool API keys for {self.env_name} environment",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template=json.dumps(secret_value),
                    generate_string_key="placeholder",
                    exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\\\^\""
                ),
                removal_policy=RemovalPolicy.DESTROY
            )

    def _create_google_maps_lambda(self):
        """Create Google Maps Lambda function with TypeScript"""
        
        # Generate consistent function name
        function_name = NamingConventions.tool_lambda_name("google-maps", self.env_name)
        
        # Create execution role
        lambda_role = iam.Role(
            self,
            "GoogleMapsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant access to Google Maps secrets
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.google_maps_secret.secret_arn
                ]
            )
        )
        
        # Grant X-Ray permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        # Create the Lambda function using NodejsFunction for TypeScript
        self.google_maps_lambda = _lambda_nodejs.NodejsFunction(
            self,
            "GoogleMapsLambda",
            function_name=function_name,
            description="Google Maps tools - provides geocoding, places search, directions, and more",
            entry="lambda/tools/google-maps/src/index.ts",
            handler="handler",
            runtime=_lambda.Runtime.NODEJS_20_X,
            timeout=Duration.seconds(30),
            memory_size=256,
            architecture=_lambda.Architecture.ARM_64,
            role=lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "ENVIRONMENT": self.env_name,
                "NODE_OPTIONS": "--enable-source-maps",
                "POWERTOOLS_SERVICE_NAME": "google-maps-tool",
                "POWERTOOLS_LOG_LEVEL": "INFO"
            },
            bundling={
                "minify": False,  # Disable minify to avoid issues with powertools
                "source_map": True
            }
        )
        
        # Apply removal policy to help with stack destruction
        self.google_maps_lambda.apply_removal_policy(RemovalPolicy.DESTROY)

    def _register_tools_in_registry(self):
        """Register all Google Maps tools in the DynamoDB registry"""
        
        # Tool specifications for all 7 Google Maps tools
        tools_specs = [
            {
                "tool_name": "maps_geocode",
                "description": "Convert an address into geographic coordinates",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "The address to geocode"
                        }
                    },
                    "required": ["address"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "geocoding", "location"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "maps_reverse_geocode",
                "description": "Convert coordinates into an address",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude coordinate"
                        }
                    },
                    "required": ["latitude", "longitude"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "geocoding", "location"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "maps_search_places",
                "description": "Search for places using Google Places API",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "location": {
                            "type": "object",
                            "properties": {
                                "latitude": {"type": "number"},
                                "longitude": {"type": "number"}
                            },
                            "description": "Optional center point for the search"
                        },
                        "radius": {
                            "type": "number",
                            "description": "Search radius in meters (max 50000)"
                        }
                    },
                    "required": ["query"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "places", "search", "location"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "maps_place_details",
                "description": "Get detailed information about a specific place",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "place_id": {
                            "type": "string",
                            "description": "The place ID to get details for"
                        }
                    },
                    "required": ["place_id"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "places", "details"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "maps_distance_matrix",
                "description": "Calculate travel distance and time for multiple origins and destinations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "origins": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of origin addresses or coordinates"
                        },
                        "destinations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of destination addresses or coordinates"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Travel mode (driving, walking, bicycling, transit)",
                            "enum": ["driving", "walking", "bicycling", "transit"]
                        }
                    },
                    "required": ["origins", "destinations"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "distance", "travel", "routing"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "maps_elevation",
                "description": "Get elevation data for locations on the earth",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "locations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number"},
                                    "longitude": {"type": "number"}
                                },
                                "required": ["latitude", "longitude"]
                            },
                            "description": "Array of locations to get elevation for"
                        }
                    },
                    "required": ["locations"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "elevation", "geography"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "tool_name": "maps_directions",
                "description": "Get directions between two points",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting point address or coordinates"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Ending point address or coordinates"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Travel mode (driving, walking, bicycling, transit)",
                            "enum": ["driving", "walking", "bicycling", "transit"]
                        }
                    },
                    "required": ["origin", "destination"]
                },
                "lambda_arn": self.google_maps_lambda.function_arn,
                "lambda_function_name": self.google_maps_lambda.function_name,
                "language": "typescript",
                "tags": ["maps", "directions", "navigation", "routing"],
                "status": "active",
                "author": "system",
                "human_approval_required": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        # Create custom resources to register each tool
        for i, tool_spec in enumerate(tools_specs):
            self._create_tool_registration(i, tool_spec)

    def _create_tool_registration(self, index: int, tool_spec: dict):
        """Create a custom resource to register a tool in DynamoDB"""
        
        # Create role for the custom resource
        custom_resource_role = iam.Role(
            self,
            f"ToolRegistrationRole{index}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant DynamoDB permissions
        custom_resource_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem"
                ],
                resources=[self.tool_registry_table_arn]
            )
        )
        
        # Convert input_schema and tags to JSON strings for DynamoDB
        tool_spec_for_dynamo = tool_spec.copy()
        tool_spec_for_dynamo["input_schema"] = json.dumps(tool_spec["input_schema"])
        tool_spec_for_dynamo["tags"] = json.dumps(tool_spec["tags"])
        
        # Create the custom resource
        cr.AwsCustomResource(
            self,
            f"RegisterTool{index}",
            on_create=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in tool_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"tool-{tool_spec['tool_name']}-{self.env_name}")
            ),
            on_update=cr.AwsSdkCall(
                service="dynamodb", 
                action="putItem",
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Item": {
                        key: {"S": str(value)} if not isinstance(value, bool) else {"BOOL": value}
                        for key, value in tool_spec_for_dynamo.items()
                    }
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"tool-{tool_spec['tool_name']}-{self.env_name}")
            ),
            on_delete=cr.AwsSdkCall(
                service="dynamodb",
                action="deleteItem", 
                parameters={
                    "TableName": self.tool_registry_table_name,
                    "Key": {
                        "tool_name": {"S": tool_spec["tool_name"]}
                    }
                }
            ),
            role=custom_resource_role
        )

    def _create_stack_exports(self):
        """Create CloudFormation outputs for other stacks to import"""
        
        # Export Google Maps Lambda function ARN
        CfnOutput(
            self, 
            "GoogleMapsLambdaArn",
            value=self.google_maps_lambda.function_arn,
            export_name=f"GoogleMapsLambdaArn-{self.env_name}",
            description="ARN of the Google Maps Lambda function"
        )
        
        # Export Google Maps secret ARN
        CfnOutput(
            self, 
            "GoogleMapsSecretArn",
            value=self.google_maps_secret.secret_arn,
            export_name=f"GoogleMapsSecretArn-{self.env_name}",
            description="ARN of the Google Maps secrets"
        )