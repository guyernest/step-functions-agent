from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
import json


class TestAutomationRemoteAgentStack(ModularBaseAgentStack):
    """
    Test Automation Remote Agent Stack - Demonstrates remote execution workflow with Microsoft 365 integration
    
    This stack creates an automation agent that combines:
    - local_agent_execute: Remote execution on local systems via Step Functions Activity
    - MicrosoftGraphAPI: Direct integration with Microsoft 365 services (email, Teams, SharePoint, etc.)
    
    This demonstrates the hybrid execution pattern where some tools execute remotely
    on external systems via Activities, while others execute directly as Lambda functions.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:

        # Set agent-specific properties for registry
        self.agent_description = "Test automation agent with remote execution workflow and Microsoft 365 integration capabilities"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['test-automation', 'remote-execution', 'approval-workflow', 'microsoft-365', 'e2b']
        }
                # Import Claude LLM ARN from shared stack
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
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
        
        # Skip centralized validation for modular tool deployment
        # Tools are validated dynamically from DynamoDB registry at runtime
        print(f"Using tools: {[config['tool_name'] for config in tool_configs]}")
        
        # Call BaseAgentStack constructor
        super().__init__(
            scope,
            construct_id,
            agent_name="test-automation-remote-agent",
            llm_arn=claude_lambda_arn,
            tool_configs=tool_configs,
            env_name=env_name,
            system_prompt="""You are a helpful automation assistant that can execute tasks on remote local systems and interact with Microsoft 365 services.

IMPORTANT REMOTE EXECUTION NOTICE:
- Your automation scripts are executed on remote systems via Step Functions Activities
- Remote workers poll for tasks and execute them on local machines
- Tasks have a 5-minute timeout - plan accordingly
- If remote execution times out, the system may be unavailable

Your capabilities:
1. local_agent_execute: Execute automation scripts on remote local systems
   - Supports file operations, application automation, and system commands
   - Uses PyAutoGUI format for UI automation
   - Executes securely on isolated remote systems

2. MicrosoftGraphAPI: Interact with Microsoft 365 services
   - Access emails, calendar, and contacts
   - Manage Teams messages and channels
   - Work with SharePoint documents
   - Query user and group information
   - Use endpoints like 'users/guy.ernest@ai-on-cloud.com/messages', 'users/guy.ernest@ai-on-cloud.com/calendar/events', etc.
   - Supports GET, POST, PUT, PATCH, DELETE methods

Guidelines:
- Design automation scripts that are robust and handle common failures
- Break complex tasks into smaller, manageable steps
- Provide clear instructions and context in your automation scripts
- Be patient during remote execution - processing may take time
- When using Microsoft Graph, specify the correct endpoint and method
- For Microsoft Graph POST/PUT/PATCH requests, include the data payload

Always explain what automation you're planning before execution.""",
            **kwargs
        )
        
        # Set agent-specific properties for registry
        self.agent_description = "Test automation agent with remote execution workflow and Microsoft 365 integration capabilities"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ["automation", "remote", "rpa", "test", "local-execution"],
            "test_scenario": "remote_execution_workflow"
        }