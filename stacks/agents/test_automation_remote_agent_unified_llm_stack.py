from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
import json


class TestAutomationRemoteAgentUnifiedLLMStack(ModularBaseAgentUnifiedLLMStack):
    """
    Test Automation Remote Agent Stack with Unified Rust LLM Service
    
    This stack demonstrates remote execution workflow using the unified Rust LLM service:
    - Uses the unified Rust LLM Lambda that supports multiple providers
    - Includes remote execution via Step Functions Activities
    - Microsoft 365 integration capabilities
    - Optimized for automation and integration tasks
    
    Key features:
    - Remote execution on local systems via Activities
    - Microsoft Graph API integration
    - Secure remote task execution
    - Activity-based workflow for sensitive operations
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Test automation agent with remote execution workflow and Microsoft 365 integration (Rust LLM)"
        self.llm_provider = "anthropic"  # Using Claude for complex automation tasks
        self.llm_model = "claude-3-5-sonnet-20241022"  # Best for understanding complex automation requirements
        self.agent_metadata = {
            "tags": ['test-automation', 'remote-execution', 'approval-workflow', 'microsoft-365', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["remote_execution", "microsoft_365", "automation", "activity_workflow"]
        }
        
        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")
        
        # Import tool Lambda ARNs and Activity ARNs
        local_automation_lambda_arn = Fn.import_value(f"LocalAutomationLambdaArn-{env_name}")
        local_automation_remote_activity_arn = Fn.import_value(f"LocalAutomationRemoteActivityArn-{env_name}")
        microsoft_graph_lambda_arn = Fn.import_value(f"MicrosoftGraphLambdaArn-{env_name}")
        
        # Define tool configurations with remote execution for local automation and Microsoft Graph
        tool_configs = [
            {
                "tool_name": "local_agent_execute",  # Use correct tool name from registry
                "lambda_arn": local_automation_lambda_arn,
                "requires_activity": True,
                "activity_type": "remote_execution",  # Remote execution on local systems
                "activity_arn": local_automation_remote_activity_arn
            },
            {
                "tool_name": "MicrosoftGraphAPI",  # Microsoft Graph API tool
                "lambda_arn": microsoft_graph_lambda_arn,
                "requires_activity": False  # Direct Lambda execution, no activity needed
            }
        ]
        
        # System prompt optimized for automation tasks
        system_prompt = """You are a helpful automation assistant that can execute tasks on remote local systems and interact with Microsoft 365 services.

IMPORTANT REMOTE EXECUTION NOTICE:
- Your automation scripts are executed on remote systems via Step Functions Activities
- Remote workers poll for tasks and execute them on local machines

Your capabilities:
1. local_agent_execute: Execute automation scripts on remote local systems running on Windows
   - Supports file operations, application automation, and system commands
   - Uses PyAutoGUI format for UI automation
   - Executes securely on isolated remote systems

2. MicrosoftGraphAPI: Interact with Microsoft 365 services
   - Access emails, calendar, and contacts
   - Manage Teams messages and channels
   - Work with SharePoint documents
   - Handle OneDrive files
   - Manage user profiles and organizational data

When executing automation tasks:
1. Always explain what actions will be performed before execution
2. Use clear, structured automation scripts
3. Consider security implications of automated actions
4. Provide status updates during long-running operations
5. Handle errors gracefully and provide meaningful feedback

For Microsoft Graph operations:
- Use appropriate scopes and permissions
- Respect data privacy and organizational policies
- Provide clear summaries of retrieved information
- Handle pagination for large result sets

Remember: Remote execution tasks are performed on actual systems, so be careful and precise with your commands."""
        
        # Call ModularBaseAgentUnifiedLLMStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="test-automation-remote-agent-rust",
            unified_llm_arn=unified_llm_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt=system_prompt,
            default_provider=self.llm_provider,
            default_model=self.llm_model,
            **kwargs
        )