from aws_cdk import (
    Fn,
)
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import GoogleMapsTools
from ..shared.base_agent_construct import BaseAgentConstruct
import json


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
        
        # Define the tools this agent will use (validated from centralized definitions)
        google_maps_tools = GoogleMapsTools.get_tool_names()
        
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
            agent_name="google-maps-agent",
            llm_arn=gemini_lambda_arn,
            tool_ids=google_maps_tools,
            env_name=env_name,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define Google Maps agent specification
        agent_spec = {
            "agent_name": "google-maps-agent",
            "version": "v1.0", 
            "status": "active",
            "system_prompt": """You are a helpful location and mapping assistant powered by Google Maps services. 

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
5. Use the most appropriate tool for each request

Always format responses clearly and provide actionable information.""",
            "description": "Location services and mapping agent using Google Maps API",
            "llm_provider": "gemini",
            "llm_model": "gemini-1.5-pro-latest",
            "tools": [
                {"tool_id": "maps_geocode", "enabled": True, "version": "latest"},
                {"tool_id": "maps_reverse_geocode", "enabled": True, "version": "latest"},
                {"tool_id": "maps_search_places", "enabled": True, "version": "latest"},
                {"tool_id": "maps_place_details", "enabled": True, "version": "latest"},
                {"tool_id": "maps_directions", "enabled": True, "version": "latest"},
                {"tool_id": "maps_distance_matrix", "enabled": True, "version": "latest"},
                {"tool_id": "maps_elevation", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/google-maps-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/GoogleMaps", 
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 5,
                "temperature": 0.7,
                "timeout_seconds": 300,
                "max_tokens": 4096
            },
            "metadata": {
                "created_by": "system",
                "tags": ["maps", "location", "google", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "GoogleMapsAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )