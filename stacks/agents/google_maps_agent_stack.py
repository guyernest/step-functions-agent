from aws_cdk import (
    Fn,
)
from constructs import Construct
from .base_agent_stack import BaseAgentStack


class GoogleMapsAgentStack(BaseAgentStack):
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
        
        # Import Gemini Lambda ARN from shared LLM stack
        gemini_lambda_arn = Fn.import_value(f"SharedGeminiLambdaArn-{env_name}")
        
        # Define the tools this agent will use (all Google Maps tools)
        google_maps_tools = [
            "maps_geocode",           # Convert address to coordinates
            "maps_reverse_geocode",   # Convert coordinates to address
            "maps_search_places",     # Search for places
            "maps_place_details",     # Get detailed place information
            "maps_distance_matrix",   # Calculate distances and travel times
            "maps_elevation",         # Get elevation data
            "maps_directions"         # Get turn-by-turn directions
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

        super().__init__(
            scope,
            construct_id,
            agent_name="google-maps",
            llm_arn=gemini_lambda_arn,
            tool_ids=google_maps_tools,
            env_name=env_name,
            system_prompt=system_prompt,
            **kwargs
        )