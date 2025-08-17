from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json


class GoogleMapsAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    Google Maps Agent Stack with Unified Rust LLM Service
    
    This stack provides location-based services using the unified Rust LLM service:
    - Uses the unified Rust LLM Lambda that supports multiple providers
    - Includes comprehensive Google Maps tools
    - Optimized for Gemini LLM (Google's own model)
    - Provides geocoding, directions, places, and mapping services
    
    The agent provides location-based services including:
    - Address geocoding and reverse geocoding
    - Place search and details
    - Directions and routing
    - Distance calculations
    - Elevation data
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Location and mapping assistant with Google Maps integration (Rust LLM)"
        self.llm_provider = "google"  # Using Google's Gemini
        self.llm_model = "gemini-2.0-flash-exp"  # Latest Gemini 2.0 Flash model
        self.agent_metadata = {
            "tags": ['maps', 'location', 'geocoding', 'directions', 'google-maps', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["geocoding", "place_search", "directions", "distance_matrix"]
        }
        
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import Google Maps Lambda ARN
        google_maps_lambda_arn = Fn.import_value(f"GoogleMapsLambdaArn-{env_name}")
        
        # Define tool configurations for all Google Maps tools
        tool_configs = [
            {
                "tool_name": "maps_geocode",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "maps_reverse_geocode",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "maps_search_places",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "maps_place_details",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "maps_distance_matrix",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "maps_elevation",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            },
            {
                "tool_name": "maps_directions",
                "lambda_arn": google_maps_lambda_arn,
                "requires_activity": False
            }
        ]
        
        # System prompt optimized for location services
        system_prompt = """You are a helpful location assistant specializing in Google Maps services.

Your capabilities include:
- **Geocoding**: Convert addresses to coordinates (maps_geocode)
- **Reverse Geocoding**: Convert coordinates to addresses (maps_reverse_geocode)
- **Place Search**: Find nearby places by type or keyword (maps_search_places)
- **Place Details**: Get detailed information about specific places (maps_place_details)
- **Directions**: Provide turn-by-turn navigation (maps_directions)
- **Distance Matrix**: Calculate travel times and distances (maps_distance_matrix)
- **Elevation**: Get elevation data for locations (maps_elevation)

When helping users:
1. Use appropriate tools based on the user's needs
2. Provide clear, structured responses with relevant details
3. Include practical information like travel times, distances, and ratings
4. Offer alternative options when available
5. Consider context (e.g., traffic conditions, business hours)

Always aim to provide accurate, helpful location-based information."""
        
        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="google-maps-agent-rust",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            default_provider=self.llm_provider,
            default_model=self.llm_model,
            **kwargs
        )