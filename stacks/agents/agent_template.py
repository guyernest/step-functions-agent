"""
Agent Template - Copy this file to create new agents

This template provides the standard structure for creating new AI agents
using the refactored architecture with self-registration.

To create a new agent:
1. Copy this file to `{agent_name}_agent_stack.py`
2. Replace all TEMPLATE_* placeholders with your agent-specific values
3. Update the tool_ids list to match your agent's required tools
4. Customize the system prompt for your agent's specific role
5. Update the agent specification in _register_agent_in_registry()

Example replacements:
- TEMPLATE_AGENT_NAME -> "my-new-agent"
- TEMPLATE_CLASS_NAME -> "MyNewAgentStack"
- TEMPLATE_LLM_PROVIDER -> "claude" (or "openai", "gemini")
- TEMPLATE_DESCRIPTION -> "My new agent description"
"""

from aws_cdk import Stack, Fn
from constructs import Construct
from .base_agent_stack import BaseAgentStack
from ..shared.tool_definitions import AllTools
from ..shared.base_agent_construct import BaseAgentConstruct
import json


class TEMPLATE_CLASS_NAME(Stack):
    """
    TEMPLATE Agent Stack - Uses base agent stack for simplified deployment
    
    This agent demonstrates:
    - [DESCRIBE YOUR AGENT'S CAPABILITIES]
    - [LIST KEY FEATURES]
    - [MENTION TOOLS USED]
    - [MENTION LLM PROVIDER]
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import LLM ARN from shared stack
        # OPTIONS: SharedClaudeLambdaArn, SharedOpenAILambdaArn, SharedGeminiLambdaArn
        llm_lambda_arn = Fn.import_value(f"SharedTEMPLATE_LLM_PROVIDERLambdaArn-{env_name}")
        
        # Define tool IDs that this agent will use
        tool_ids = [
            "TEMPLATE_TOOL_1",  # Description of what this tool does
            "TEMPLATE_TOOL_2",  # Description of what this tool does
            "TEMPLATE_TOOL_3"   # Description of what this tool does
        ]
        
        # Validate tool names exist in centralized definitions
        invalid_tools = AllTools.validate_tool_names(tool_ids)
        if invalid_tools:
            raise ValueError(f"TEMPLATE Agent uses invalid tools: {invalid_tools}. Available tools: {AllTools.get_all_tool_names()}")
        
        # Define system prompt for this agent
        system_prompt = """You are a TEMPLATE_ROLE with expertise in TEMPLATE_DOMAIN.

Your capabilities include:
- [LIST YOUR AGENT'S MAIN CAPABILITIES]
- [INCLUDE SPECIFIC SKILLS OR KNOWLEDGE AREAS]
- [MENTION AVAILABLE TOOLS AND THEIR PURPOSE]

Available tools:
- TEMPLATE_TOOL_1: [Describe what this tool does]
- TEMPLATE_TOOL_2: [Describe what this tool does]
- TEMPLATE_TOOL_3: [Describe what this tool does]

When helping users:
1. [SPECIFIC INSTRUCTION FOR YOUR AGENT]
2. [ANOTHER SPECIFIC INSTRUCTION]
3. [BEST PRACTICES FOR YOUR DOMAIN]
4. [HOW TO USE TOOLS EFFECTIVELY]
5. [OUTPUT FORMAT REQUIREMENTS]

Always [SPECIFIC REQUIREMENTS FOR YOUR AGENT'S BEHAVIOR]."""

        # Create agent using base stack
        self.TEMPLATE_agent = BaseAgentStack(
            self,
            "TEMPLATEAgent",
            agent_name="TEMPLATE_AGENT_NAME",
            llm_arn=llm_lambda_arn,
            tool_ids=tool_ids,
            env_name=env_name,
            system_prompt=system_prompt
        )
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this agent in the Agent Registry using BaseAgentConstruct"""
        
        # Define agent specification
        agent_spec = {
            "agent_name": "TEMPLATE_AGENT_NAME",
            "version": "v1.0",
            "status": "active",
            "system_prompt": """You are a TEMPLATE_ROLE with expertise in TEMPLATE_DOMAIN.

Your capabilities include:
- [LIST YOUR AGENT'S MAIN CAPABILITIES]
- [INCLUDE SPECIFIC SKILLS OR KNOWLEDGE AREAS]
- [MENTION AVAILABLE TOOLS AND THEIR PURPOSE]

When helping users:
1. [SPECIFIC INSTRUCTION FOR YOUR AGENT]
2. [ANOTHER SPECIFIC INSTRUCTION]
3. [BEST PRACTICES FOR YOUR DOMAIN]
4. [HOW TO USE TOOLS EFFECTIVELY]
5. [OUTPUT FORMAT REQUIREMENTS]

Always [SPECIFIC REQUIREMENTS FOR YOUR AGENT'S BEHAVIOR].""",
            "description": "TEMPLATE_DESCRIPTION",
            "llm_provider": "TEMPLATE_LLM_PROVIDER",  # claude, openai, gemini
            "llm_model": "TEMPLATE_LLM_MODEL",        # claude-3-5-sonnet-20241022, gpt-4o, gemini-1.5-pro-latest
            "tools": [
                {"tool_id": "TEMPLATE_TOOL_1", "enabled": True, "version": "latest"},
                {"tool_id": "TEMPLATE_TOOL_2", "enabled": True, "version": "latest"},
                {"tool_id": "TEMPLATE_TOOL_3", "enabled": True, "version": "latest"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/TEMPLATE_AGENT_NAME-{self.env_name}",
                "metrics_namespace": "AIAgents/TEMPLATE_NAMESPACE",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 5,           # Adjust based on your agent's needs
                "temperature": 0.3,            # Adjust for creativity vs accuracy
                "timeout_seconds": 300,        # Adjust for expected response time
                "max_tokens": 4096            # Adjust for response length
            },
            "metadata": {
                "created_by": "system",
                "tags": ["TEMPLATE_TAG_1", "TEMPLATE_TAG_2", "production"],
                "deployment_env": self.env_name
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "TEMPLATEAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )


"""
CHECKLIST FOR CREATING A NEW AGENT:

□ 1. Replace TEMPLATE_CLASS_NAME with your agent's class name (e.g., EmailAgentStack)
□ 2. Replace TEMPLATE_AGENT_NAME with kebab-case agent name (e.g., "email-agent")
□ 3. Replace TEMPLATE_LLM_PROVIDER with your chosen LLM (claude/openai/gemini)
□ 4. Replace TEMPLATE_LLM_MODEL with the specific model name
□ 5. Replace TEMPLATE_TOOL_* with actual tool names from your tool registry
□ 6. Replace TEMPLATE_ROLE with the agent's role (e.g., "email assistant")
□ 7. Replace TEMPLATE_DOMAIN with the agent's domain (e.g., "email management")
□ 8. Replace TEMPLATE_DESCRIPTION with a clear description
□ 9. Replace TEMPLATE_NAMESPACE with metrics namespace (e.g., "Email")
□ 10. Replace TEMPLATE_TAG_* with relevant tags
□ 11. Update system prompt with specific instructions for your agent
□ 12. Adjust parameters (temperature, max_tokens, etc.) for your use case
□ 13. Test tool validation by running locally
□ 14. Update the class docstring with agent-specific information
□ 15. Add the new stack to your main CDK app file (refactored_app.py)

NOTE: created_at and updated_at timestamps are automatically generated at deployment time.

AVAILABLE LLM PROVIDERS:
- claude: SharedClaudeLambdaArn (claude-3-5-sonnet-20241022)
- openai: SharedOpenAILambdaArn (gpt-4o)
- gemini: SharedGeminiLambdaArn (gemini-1.5-pro-latest)

TOOL VALIDATION:
Run `AllTools.get_all_tool_names()` to see available tools.
All tools are defined in ../shared/tool_definitions.py

DEPLOYMENT:
1. Add your new stack to refactored_app.py
2. Deploy with: cdk deploy YourNewAgentStack-prod --profile YOUR_PROFILE
"""