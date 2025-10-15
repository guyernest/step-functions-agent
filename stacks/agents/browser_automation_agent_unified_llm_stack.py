from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack


class BrowserAutomationAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    Browser Automation Agent Stack with Unified Rust LLM Service

    This stack demonstrates remote browser automation workflow using the unified Rust LLM service:
    - Uses the unified Rust LLM Lambda that supports multiple providers
    - Includes remote browser automation via Step Functions Activities
    - Nova Act integration for intelligent browser automation
    - Optimized for web scraping, form filling, and browser-based tasks

    Key features:
    - Remote execution on local browser via Activities
    - Bot detection avoidance using real browser sessions
    - Session persistence across multiple tasks
    - Activity-based workflow for secure browser operations
    - Video recording and screenshot capture
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Browser automation agent with remote execution workflow using Nova Act for intelligent web interactions (Rust LLM)"
        self.llm_provider = "anthropic"  # Using Claude for complex web navigation tasks
        self.llm_model = "claude-3-5-sonnet-20241022"  # Best for understanding web automation requirements
        self.agent_metadata = {
            "tags": ['browser-automation', 'remote-execution', 'nova-act', 'web-scraping', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["remote_execution", "browser_automation", "web_scraping", "activity_workflow"]
        }

        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")

        # Import browser remote tool Lambda ARN and Activity ARN
        browser_remote_lambda_arn = Fn.import_value(f"BrowserRemoteLambdaArn-{env_name}")
        browser_remote_activity_arn = Fn.import_value(f"BrowserRemoteActivityArn-{env_name}")

        # Define tool configurations with remote execution for browser automation
        tool_configs = [
            {
                "tool_name": "browser_remote",
                "lambda_arn": browser_remote_lambda_arn,
                "requires_activity": True,
                "activity_type": "remote_execution",  # Remote execution on local browser
                "activity_arn": browser_remote_activity_arn
            }
        ]

        # System prompt optimized for browser automation tasks
        system_prompt = """You are a helpful browser automation assistant that can execute web-based tasks on a remote local browser.

IMPORTANT REMOTE EXECUTION NOTICE:
- Your browser automation tasks are executed on a remote local browser via Step Functions Activities
- The local agent uses Nova Act for intelligent browser interactions
- Browser sessions run in a real user environment to avoid bot detection

Your capabilities:
1. browser_remote: Execute browser automation using natural language prompts
   - Navigate websites and interact with elements
   - Fill forms and submit data
   - Extract structured information using JSON schemas
   - Handle CAPTCHAs and authentication flows
   - Maintain session persistence across tasks
   - Capture screenshots and record videos
   - Uses Nova Act for high-level browser automation

Browser Automation Guidelines:
1. Write clear, specific prompts describing what you want to accomplish
2. Use JSON schemas when you need structured data extraction
3. Leverage session persistence for multi-step workflows
4. Be aware that automation runs in a real browser to avoid detection
5. Consider page load times and network latency
6. Handle common web scenarios (popups, cookie banners, etc.)

Example prompts:
- "Navigate to the BT broadband availability checker and check if broadband is available for postcode SW1A 1AA"
- "Go to Sweetgreen and add a Shroomami salad to the cart, but don't place the order"
- "Extract the top 5 news headlines from BBC News homepage"

When extracting structured data, always provide a JSON schema that matches your expected output format.

Remember: Browser automation tasks run on actual local systems with real browsers, so operations may take time to complete."""

        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="browser-automation-agent-rust",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            default_provider=self.llm_provider,
            default_model=self.llm_model,
            **kwargs
        )
