from aws_cdk import (
    Stack,
    Fn,
)
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import GoogleMapsTools, AllTools
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
        
        # Validate tool names exist in centralized definitions
        tool_names = [config["tool_name"] for config in tool_configs]
        invalid_tools = AllTools.validate_tool_names(tool_names)
        if invalid_tools:
            raise ValueError(f"Google Maps Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
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

        # Call BaseAgentStack constructor
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
        
        # Store env_name for registration
        self.env_name = env_name
        
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
                {"tool_name": "maps_geocode", "enabled": True, "version": "latest"},
                {"tool_name": "maps_reverse_geocode", "enabled": True, "version": "latest"},
                {"tool_name": "maps_search_places", "enabled": True, "version": "latest"},
                {"tool_name": "maps_place_details", "enabled": True, "version": "latest"},
                {"tool_name": "maps_directions", "enabled": True, "version": "latest"},
                {"tool_name": "maps_distance_matrix", "enabled": True, "version": "latest"},
                {"tool_name": "maps_elevation", "enabled": True, "version": "latest"}
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