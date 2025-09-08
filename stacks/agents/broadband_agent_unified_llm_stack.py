from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json


class BroadbandAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    Broadband Availability Agent Stack with Unified Rust LLM Service
    
    This agent specializes in checking UK broadband availability using the Agent Core browser tool.
    It can:
    - Check ADSL, VDSL, and FTTP availability at UK addresses
    - Provide exchange and cabinet information
    - Show available speeds and technologies
    - Return browser recording URLs for verification
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "UK broadband availability checker using Agent Core browser automation (Rust LLM)"
        self.llm_provider = "claude"  # Using Claude for better UK address parsing
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['broadband', 'uk', 'telecom', 'adsl', 'vdsl', 'fttp', 'browser-automation', 'agent-core', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["broadband_check", "address_parsing", "speed_analysis", "technology_availability"]
        }
        
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import Agent Core browser tool Lambda ARN
        agentcore_browser_lambda_arn = Fn.import_value(f"AgentCoreBrowserLambdaArn-{env_name}")
        
        # Define tool configurations - initially just browser_broadband
        tool_configs = [
            {
                "tool_name": "browser_broadband",
                "lambda_arn": agentcore_browser_lambda_arn,
                "requires_activity": False,
                "description": "Check UK broadband availability at an address"
            }
        ]
        
        # System prompt for the broadband agent
        system_prompt = """You are a specialized UK broadband availability checker assistant.

Your primary function is to help users check broadband availability at UK addresses using the browser_broadband tool.

When a user provides an address, you should:
1. Parse the address to identify the components:
   - Building number or name (e.g., "10", "Flat 3", "The Manor")
   - Street name (without the building number)
   - Town or city
   - Postcode (REQUIRED - in format like "SW1A 2AA", "E8 1GQ")

2. Use the browser_broadband tool with the address components as separate parameters:
   - building_number: The building number or name
   - street: The street name (without building number)
   - town: The town or city name
   - postcode: The UK postcode (required)

3. Present the results clearly, including:
   - Exchange name and cabinet number
   - Available technologies (ADSL, VDSL, FTTP)
   - Download and upload speeds
   - WLR3 availability
   - Links to the browser recording for verification

Important guidelines:
- UK postcodes are required for broadband checks
- If the user provides an incomplete address, politely ask for the missing information (especially the postcode)
- Always include the presigned URLs in your response so users can verify the browser automation
- If the check fails, suggest the user check the recording URLs to see what happened
- Be helpful in explaining technical terms:
  - ADSL: Standard broadband (up to 24 Mbps)
  - VDSL/FTTC: Fiber to the cabinet (up to 80 Mbps)
  - FTTP: Fiber to the premises (up to 1000 Mbps)
  - WLR3: Wholesale Line Rental (traditional phone line)

Example interaction:
User: "Can you check broadband for 10 Downing Street, London SW1A 2AA?"
You: I'll check the broadband availability for 10 Downing Street, London SW1A 2AA.
[Use browser_broadband tool with: building_number="10", street="Downing Street", town="London", postcode="SW1A 2AA"]
Then provide comprehensive results with all technical details and recording URLs."""
        
        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="broadband-agent-rust",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            default_provider=self.llm_provider,
            default_model=self.llm_model,
            **kwargs
        )