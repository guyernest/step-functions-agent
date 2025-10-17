"""
Browser Automation Agent with Structured Output

This agent performs browser automation tasks using the browser_remote tool
and returns data in a structured format using the unified generator pattern.
"""

import json
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Fn,
    aws_stepfunctions as sfn,
    aws_iam as iam,
    Tags
)
from constructs import Construct
from pathlib import Path
import os
from .step_functions_generator_unified_llm import UnifiedLLMStepFunctionsGenerator
from ..shared.base_agent_construct import BaseAgentConstruct


class BrowserAutomationStructuredStack(Stack):
    """CDK Stack for Browser Automation Agent with Structured Output using unified generator"""

    def __init__(self, scope: Construct, id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get environment
        self.env_name = env_name

        # Agent name
        self.agent_name = "browser-automation-structured"

        # Import shared resources
        self.agent_registry_table_name = self.node.try_get_context("agent_registry_table") or f"AgentRegistry-{self.env_name}"
        self.tool_registry_table_name = self.node.try_get_context("tool_registry_table") or f"ToolRegistry-{self.env_name}"
        self.llm_models_table_name = self.node.try_get_context("llm_models_table") or f"LLMModels-{self.env_name}"

        # Import unified LLM ARN
        self.unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{self.env_name}")

        # Import browser remote tool Lambda ARN and Activity ARN
        self.browser_remote_lambda_arn = Fn.import_value(f"BrowserRemoteLambdaArn-{self.env_name}")
        self.browser_remote_activity_arn = Fn.import_value(f"BrowserRemoteActivityArn-{self.env_name}")

        # System prompt for the agent
        self.system_prompt = """You are a BT Broadband Availability Checker assistant that uses browser automation to check broadband availability for UK addresses.

IMPORTANT REMOTE EXECUTION NOTICE:
- Your browser automation tasks are executed on a remote local browser via Step Functions Activities
- The local agent uses Nova Act for intelligent browser interactions
- Browser sessions run in a real user environment to avoid bot detection
- Scripts are executed as JSON files that define declarative browser automation steps

YOUR PRIMARY TASK:
Check broadband availability for UK addresses using the BT Wholesale Broadband Checker website.

BROWSER AUTOMATION SCRIPT FORMAT:
You must provide browser automation instructions as a JSON script with this structure:
{
  "name": "BT Broadband Check",
  "description": "Checking broadband availability in BT portal",
  "starting_page": "https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome",
  "abort_on_error": false,
  "steps": [
    {
      "action": "act",
      "prompt": "Fill in the address form with these details: - Building Number field: <NUMBER> - Street/Road field: '<STREET>' - PostCode field: '<POSTCODE>'. Then click the Submit button.",
      "description": "Search by address"
    },
    {
      "action": "act",
      "prompt": "If an address list appears, select the closest match to <FULL ADDRESS>.",
      "description": "Select from options"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract the broadband availability information from the results page: Exchange name, Cabinet number, VDSL Range A downstream and upstream rates, Availability status",
      "schema": {
        "type": "object",
        "properties": {
          "exchange": { "type": "string" },
          "cabinet": { "type": "string" },
          "downstream": { "type": "number" },
          "upstream": { "type": "number" },
          "availability": { "type": "boolean" }
        },
        "required": ["exchange", "cabinet", "downstream", "upstream"]
      },
      "description": "Extract broadband information"
    }
  ]
}

SCRIPT ACTIONS:
1. "act" - Use natural language prompts to interact with the page (click, fill forms, navigate)
2. "act_with_schema" - Extract structured data using JSON schemas
3. "screenshot" - Capture the current page state

IMPORTANT GUIDELINES:
- Always start at: https://www.broadbandchecker.btwholesale.com/#/ADSL/AddressHome
- Use the address format: Building Number, Street, Postcode
- Handle address selection when multiple matches appear
- Extract: exchange name, cabinet number, download speed, upload speed, availability status
- Set abort_on_error to false to handle edge cases gracefully

When performing browser automation with structured output:
1. Use the browser_remote tool with your JSON script
2. After receiving the tool results, analyze the extracted data
3. Call the return_browser_automation_data function with the structured information
4. Include any screenshot URLs or recording URLs provided

For the structured output:
- Extract the exchange station name, download speed, and upload speed
- Ensure all required fields are populated with accurate data
- Include metadata like screenshots and recordings when available
- Provide clear, structured responses that match the expected schema

Be precise with data extraction and ensure all required fields are populated."""

        # Define structured output schema for browser automation data
        # This is a flexible schema that can be customized per use case
        self.structured_output_schema = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the browser automation task succeeded"
                },
                "data": {
                    "type": "object",
                    "description": "Extracted structured data from the web page"
                },
                "screenshot_url": {
                    "type": "string",
                    "description": "URL of the browser recording or screenshot"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata about the automation task"
                }
            },
            "required": ["success", "data"]
        }

        # Tool configurations
        self.tool_configs = [
            {
                "tool_name": "browser_remote",
                "lambda_arn": self.browser_remote_lambda_arn,
                "requires_activity": True,
                "activity_type": "remote_execution",
                "activity_arn": self.browser_remote_activity_arn
            }
        ]

        # Generate state machine definition using unified generator
        state_machine_definition = UnifiedLLMStepFunctionsGenerator.generate_unified_llm_agent_definition(
            agent_name=self.agent_name,
            unified_llm_arn=self.unified_llm_arn,
            tool_configs=self.tool_configs,
            system_prompt=self.system_prompt,
            structured_output_schema=self.structured_output_schema,
            default_provider="anthropic",
            default_model="claude-3-5-sonnet-20241022",
            llm_models_table_name=self.llm_models_table_name,
            agent_registry_table_name=self.agent_registry_table_name,
            tool_registry_table_name=self.tool_registry_table_name
        )

        # Create IAM role for the state machine
        state_machine_role = iam.Role(
            self, "StateMachineRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description=f"Role for {self.agent_name} state machine"
        )

        # Grant permissions to invoke Lambda functions
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[
                    self.unified_llm_arn,
                    self.browser_remote_lambda_arn
                ]
            )
        )

        # Grant DynamoDB permissions
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.agent_registry_table_name}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.tool_registry_table_name}",
                    f"arn:aws:dynamodb:{self.region}:{self.account}:table/{self.llm_models_table_name}"
                ]
            )
        )

        # Grant CloudWatch metrics permissions
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # Grant permissions for remote execution activity
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "states:SendTaskSuccess",
                    "states:SendTaskFailure",
                    "states:SendTaskHeartbeat"
                ],
                resources=[self.browser_remote_activity_arn]
            )
        )

        # Create the state machine
        self.state_machine = sfn.CfnStateMachine(
            self, "BrowserAutomationStructuredStateMachine",
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_string=state_machine_definition,
            role_arn=state_machine_role.role_arn,
            tracing_configuration={
                "enabled": True
            }
        )

        # Tag the resources
        Tags.of(self).add("Agent", self.agent_name)
        Tags.of(self).add("Environment", self.env_name)
        Tags.of(self).add("Type", "structured-output")
        Tags.of(self).add("Generator", "unified-llm")

        # Register agent in registry with structured output configuration
        agent_spec = {
            "agent_name": self.agent_name,
            "version": "v1.0",
            "status": "active",
            "system_prompt": self.system_prompt,
            "description": "Browser automation agent with structured output for web scraping and data extraction",
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": json.dumps([
                {"tool_name": "browser_remote", "enabled": True}
            ]),
            "structured_output": json.dumps({
                "enabled": True,
                "schemas": {
                    "browser_automation_data": {
                        "schema": self.structured_output_schema
                    }
                },
                "output_fields": ["success", "data", "screenshot_url", "metadata"]
            }),
            "state_machine_arn": self.state_machine.attr_arn,
            "environment": self.env_name,
            "metadata": {
                "supports_batch_processing": True,
                "structured_output_enabled": True,
                "execution_type": "remote_activity"
            }
        }

        BaseAgentConstruct(
            self,
            f"{self.agent_name.replace('-', '')}Registration",
            agent_spec=agent_spec,
            env_name=self.env_name
        )

        # Outputs
        CfnOutput(
            self, "StateMachineArn",
            value=self.state_machine.attr_arn,
            export_name=f"{self.agent_name}-state-machine-arn-{self.env_name}",
            description=f"ARN of the {self.agent_name} state machine"
        )

        CfnOutput(
            self, "StateMachineName",
            value=self.state_machine.state_machine_name,
            export_name=f"{self.agent_name}-state-machine-name-{self.env_name}",
            description=f"Name of the {self.agent_name} state machine"
        )
