"""
Google Maps Tool Stack V2 - Self-Contained Tool Definitions

This is an example of the new architectural pattern where tool stacks own their
tool definitions alongside Lambda implementations, preventing parameter mismatches.

Migration Benefits:
1. Tool schema and Lambda parameters are always in sync
2. No more parameter mismatches between registry and implementation
3. Independent development without touching shared files
4. Type safety enforced at the tool level
"""

from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct

from stacks.shared.base_tool_construct import BaseToolConstruct
from stacks.shared.tool_definitions import ToolDefinition, ToolLanguage


class GoogleMapsToolStackV2(BaseToolConstruct):
    """
    Google Maps tools with self-contained definitions.
    
    This stack demonstrates the new pattern where tool definitions
    are co-located with Lambda implementations.
    """
    
    def _create_tools(self) -> None:
        """Create Lambda functions and their matching tool definitions"""
        
        # Create the Google Maps Lambda function
        self.google_maps_lambda = _lambda.Function(
            self,
            "GoogleMapsLambda",
            runtime=_lambda.Runtime.NODEJS_18_X,
            handler="handler",
            code=_lambda.Code.from_asset("lambda/tools/google-maps"),
            timeout=Duration.seconds(30),
            environment={
                # Environment variables for the Lambda
            },
        )
        
        # Grant necessary permissions
        self.google_maps_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=["*"]
            )
        )
        
        # Define tool schemas that match the Lambda implementation exactly
        self._define_geocoding_tools()
        self._define_places_tools()
        self._define_directions_tools()
        self._define_utility_tools()
    
    def _define_geocoding_tools(self) -> None:
        """Define geocoding tool definitions"""
        
        # Geocode tool - matches Lambda parameter expectations exactly
        geocode_tool = ToolDefinition(
            tool_name="maps_geocode",
            description="Convert an address into geographic coordinates using Google Maps Geocoding API",
            input_schema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The address to geocode (e.g., '1600 Amphitheatre Parkway, Mountain View, CA')"
                    }
                },
                "required": ["address"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "geocoding", "location", "google"]
        )
        self._register_tool(geocode_tool, self.google_maps_lambda)
        
        # Reverse geocode tool
        reverse_geocode_tool = ToolDefinition(
            tool_name="maps_reverse_geocode", 
            description="Convert coordinates into a human-readable address using Google Maps Reverse Geocoding API",
            input_schema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude coordinate (-90 to 90)",
                        "minimum": -90,
                        "maximum": 90
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude coordinate (-180 to 180)",
                        "minimum": -180,
                        "maximum": 180
                    }
                },
                "required": ["latitude", "longitude"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "geocoding", "location", "google", "reverse"]
        )
        self._register_tool(reverse_geocode_tool, self.google_maps_lambda)
    
    def _define_places_tools(self) -> None:
        """Define Places API tool definitions"""
        
        # Places search tool
        search_places_tool = ToolDefinition(
            tool_name="maps_search_places",
            description="Search for places using Google Places API with optional location bias",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'coffee shops', 'restaurants near Times Square')"
                    },
                    "location": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "number",
                                "minimum": -90,
                                "maximum": 90
                            },
                            "longitude": {
                                "type": "number", 
                                "minimum": -180,
                                "maximum": 180
                            }
                        },
                        "description": "Optional center point to bias the search results",
                        "required": ["latitude", "longitude"]
                    },
                    "radius": {
                        "type": "number",
                        "description": "Search radius in meters (max 50000)",
                        "minimum": 1,
                        "maximum": 50000,
                        "default": 5000
                    }
                },
                "required": ["query"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "places", "search", "google", "location"]
        )
        self._register_tool(search_places_tool, self.google_maps_lambda)
        
        # Place details tool
        place_details_tool = ToolDefinition(
            tool_name="maps_place_details",
            description="Get detailed information about a specific place using its Place ID",
            input_schema={
                "type": "object",
                "properties": {
                    "place_id": {
                        "type": "string",
                        "description": "The Google Place ID to get details for (obtained from places search)"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific fields to return (e.g., ['name', 'rating', 'formatted_phone_number'])",
                        "default": ["name", "formatted_address", "rating", "opening_hours"]
                    }
                },
                "required": ["place_id"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "places", "details", "google", "poi"]
        )
        self._register_tool(place_details_tool, self.google_maps_lambda)
    
    def _define_directions_tools(self) -> None:
        """Define directions and routing tool definitions"""
        
        # Directions tool
        directions_tool = ToolDefinition(
            tool_name="maps_directions",
            description="Get turn-by-turn directions between locations using Google Directions API",
            input_schema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Starting location (address, place name, or coordinates like '37.7749,-122.4194')"
                    },
                    "destination": {
                        "type": "string", 
                        "description": "Ending location (address, place name, or coordinates)"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "bicycling", "transit"],
                        "description": "Travel mode for directions",
                        "default": "driving"
                    },
                    "waypoints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional intermediate waypoints to visit",
                        "maxItems": 25
                    },
                    "avoid": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["tolls", "highways", "ferries", "indoor"]
                        },
                        "description": "Route restrictions to avoid"
                    }
                },
                "required": ["origin", "destination"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "directions", "routing", "google", "navigation"]
        )
        self._register_tool(directions_tool, self.google_maps_lambda)
        
        # Distance Matrix tool
        distance_matrix_tool = ToolDefinition(
            tool_name="maps_distance_matrix",
            description="Calculate distances and travel times between multiple origins and destinations",
            input_schema={
                "type": "object",
                "properties": {
                    "origins": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of origin locations (addresses or coordinates)",
                        "minItems": 1,
                        "maxItems": 25
                    },
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of destination locations (addresses or coordinates)",
                        "minItems": 1,
                        "maxItems": 25
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["driving", "walking", "bicycling", "transit"],
                        "description": "Travel mode for calculations",
                        "default": "driving"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "Unit system for distances",
                        "default": "metric"
                    }
                },
                "required": ["origins", "destinations"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "distance", "matrix", "google", "travel-time"]
        )
        self._register_tool(distance_matrix_tool, self.google_maps_lambda)
    
    def _define_utility_tools(self) -> None:
        """Define utility and additional tool definitions"""
        
        # Elevation tool
        elevation_tool = ToolDefinition(
            tool_name="maps_elevation",
            description="Get elevation data for specified coordinates using Google Elevation API",
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
                                    "minimum": -90,
                                    "maximum": 90
                                },
                                "longitude": {
                                    "type": "number",
                                    "minimum": -180,
                                    "maximum": 180
                                }
                            },
                            "required": ["latitude", "longitude"]
                        },
                        "description": "List of coordinates to get elevation for",
                        "minItems": 1,
                        "maxItems": 512
                    }
                },
                "required": ["locations"]
            },
            language=ToolLanguage.TYPESCRIPT,
            lambda_handler="handler",
            tags=["maps", "elevation", "geography", "google", "terrain"]
        )
        self._register_tool(elevation_tool, self.google_maps_lambda)


# Migration helper function for existing agent stacks
def get_google_maps_tool_configs_v2(stack: GoogleMapsToolStackV2, requires_approval: bool = False) -> list:
    """
    Helper function for agent stacks to get Google Maps tool configurations.
    
    This replaces the need to manually maintain tool lists in agent stacks.
    """
    return stack.get_tool_configs_for_agent(requires_approval=requires_approval)