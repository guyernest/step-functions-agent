from aws_cdk import (
    Stack,
    Fn,
)
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
import json


class GoogleMapsAgentStack(ModularBaseAgentStack):
    """
    Google Maps Agent Stack - Location and mapping assistant using Gemini LLM
    
    This agent demonstrates:
    - Use of base agent construct for simplified creation
    - Gemini LLM integration (different from Claude)
    - Google Maps tools integration
    - TypeScript tool usage from Python agent
    
    The agent provides location-based services including:
    - Address geocoding and reverse geocoding
    - Place search and details
    - Directions and routing
    - Distance calculations
    - Elevation data
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Location and mapping assistant with Google Maps integration"
        self.llm_provider = "gemini"
        self.llm_model = "gemini-2.0-flash-exp"
        self.agent_metadata = {
            "tags": ['maps', 'location', 'geocoding', 'directions', 'google-maps']
        }
                # Import Gemini Lambda ARN from shared LLM stack
        gemini_lambda_arn = Fn.import_value(f"SharedGeminiLambdaArn-{env_name}")
        
        # Import Google Maps Lambda ARN
        google_maps_lambda_arn = Fn.import_value(f"GoogleMapsLambdaArn-{env_name}")
        
        # Define tool configurations for all Google Maps tools
        tool_configs = [
            {
                "tool_name": "maps_geocode",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "maps_reverse_geocode",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "maps_search_places",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "maps_place_details",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "maps_distance_matrix",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "maps_elevation",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            },
            {
                "tool_name": "maps_directions",
                "lambda_arn": google_maps_lambda_arn,
                "requires_approval": False
            }
        ]
        
                
        # Define system prompt for this agent
        system_prompt = """You are a helpful location and mapping assistant powered by Google Maps services. 

You have access to comprehensive Google Maps tools that allow you to:
- Find and geocode addresses
- Search for places, businesses, and points of interest
- Get detailed information about locations including ratings, reviews, and contact details
- Calculate distances, travel times, and routes between locations
- Provide turn-by-turn directions for driving, walking, cycling, or public transit
- Get elevation data for geographic locations

When helping users:
1. Be specific about locations - ask for clarification if addresses are ambiguous
2. Provide multiple options when searching for places
3. Include relevant details like travel time, distance, and ratings when available
4. Consider the user's travel mode (driving, walking, etc.) when providing directions
5. Format location information clearly and helpfully

You work best with Google's ecosystem and can provide rich, detailed location-based information."""

        # Call ModularBaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="google-maps-agent",
            llm_arn=gemini_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Set agent-specific properties for registry
        self.agent_description = "Location and mapping assistant with Google Maps integration"
        self.llm_provider = "gemini"
        self.llm_model = "gemini-2.0-flash-exp"
        self.agent_metadata = {
            "tags": ['location', 'maps', 'navigation', 'geocoding', 'places']
        }