from aws_cdk import Stack, Fn
from constructs import Construct
from .modular_base_agent_stack import ModularBaseAgentStack
from ..shared.base_agent_construct import BaseAgentConstruct
import json


class TestAutomationRemoteAgentStack(ModularBaseAgentStack):
    """
    Test Automation Remote Agent Stack - Demonstrates remote execution workflow
    
    This stack creates an automation agent that uses remote execution for:
    - local_agent: Remote execution on local systems via Step Functions Activity
    
    This demonstrates the remote execution pattern where tools are executed
    on external systems that poll Step Functions Activities.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        # Import Claude LLM ARN from shared stack
        claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{env_name}")
        
        # Import tool Lambda ARNs and Activity ARNs
        local_automation_lambda_arn = Fn.import_value(f"LocalAutomationLambdaArn-{env_name}")
        local_automation_remote_activity_arn = Fn.import_value(f"LocalAutomationRemoteActivityArn-{env_name}")
        
        # Define tool configurations with remote execution for local automation
        tool_configs = [
            {
                "tool_name": "local_agent_execute",  # Use correct tool name from registry
                "lambda_arn": local_automation_lambda_arn,
                "requires_activity": True,
                "activity_type": "remote_execution",  # Remote execution on local systems
                "activity_arn": local_automation_remote_activity_arn
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
            system_prompt="""You are a helpful automation assistant that can execute tasks on remote local systems through secure remote execution.

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

Guidelines:
- Design automation scripts that are robust and handle common failures
- Break complex tasks into smaller, manageable steps
- Provide clear instructions and context in your automation scripts
- Be patient during remote execution - processing may take time

Always explain what automation you're planning before execution.""",
            **kwargs
        )
        
        # Store env_name for registration
        self.env_name = env_name
        
        # Register this agent in the Agent Registry
        self._register_agent_in_registry()
    
    def _register_agent_in_registry(self):
        """Register this test automation remote agent in the Agent Registry"""
        
        # Define automation remote agent specification
        agent_spec = {
            "agent_name": "test-automation-remote-agent",
            "version": "v1.0", 
            "status": "active",
            "system_prompt": """You are an automation assistant with remote execution capabilities for local system automation.

Your responsibilities:
- Design automation scripts for remote execution on local systems using local_agent_execute
- Handle remote execution timeouts and failures gracefully
- Provide clear explanations of automation tasks
- Use PyAutoGUI format for UI automation scripts

Remote execution features:
- local_agent_execute tasks execute on remote systems via Step Functions Activities
- 5-minute timeout for remote operations
- Secure execution in isolated environments
- Real-time feedback from remote workers

Always design robust automation that handles common edge cases.""",
            "description": "Test automation agent demonstrating remote execution workflow for local system automation",
            "llm_provider": "claude",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": [
                {"tool_name": "local_agent_execute", "enabled": True, "version": "latest", "execution_type": "remote"}
            ],
            "observability": {
                "log_group": f"/aws/stepfunctions/test-automation-remote-agent-{self.env_name}",
                "metrics_namespace": "AIAgents/TestAutomationRemote",
                "trace_enabled": True,
                "log_level": "INFO"
            },
            "parameters": {
                "max_iterations": 3,
                "temperature": 0.2,
                "timeout_seconds": 600,  # Longer timeout for remote operations
                "max_tokens": 4096
            },
            "metadata": {
                "created_by": "system",
                "tags": ["automation", "remote", "rpa", "test", "local-execution"],
                "deployment_env": self.env_name,
                "test_scenario": "remote_execution_workflow"
            }
        }
        
        # Use BaseAgentConstruct for registration
        BaseAgentConstruct(
            self,
            "TestAutomationRemoteAgentRegistration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )