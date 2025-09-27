"""
Broadband Checker Agent with Structured Output

This agent checks broadband availability using the browser_broadband tool
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


class BroadbandCheckerStructuredStack(Stack):
    """CDK Stack for Broadband Checker Agent with Structured Output using unified generator"""

    def __init__(self, scope: Construct, id: str, env_name: str = "dev", **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get environment
        self.env_name = env_name

        # Agent name
        self.agent_name = "broadband-checker-structured"

        # Import shared resources
        self.agent_registry_table_name = self.node.try_get_context("agent_registry_table") or f"AgentRegistry-{self.env_name}"
        self.tool_registry_table_name = self.node.try_get_context("tool_registry_table") or f"ToolRegistry-{self.env_name}"
        self.llm_models_table_name = self.node.try_get_context("llm_models_table") or f"LLMModels-{self.env_name}"

        # Import unified LLM ARN
        self.unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{self.env_name}")

        # Import browser_broadband tool ARN
        self.broadband_tool_arn = Fn.import_value(f"AgentCoreBrowserLambdaArn-{self.env_name}")

        # System prompt for the agent
        self.system_prompt = """You are a broadband availability checker agent that helps users find broadband services for UK addresses.

When given an address and postcode, you will:
1. Parse the address to extract building number, street, town, and postcode
2. Use the browser_broadband tool to check availability
3. Return the results in a structured format

Important:
- Always use the browser_broadband tool first to get the actual data
- After receiving the tool results, call the return_broadband_data function with the structured information
- Extract the exchange station, download speed range, and upload speed range from the tool results
- Include any browser recording URLs provided

For the structured output:
- exchange_station: The name of the telephone exchange serving the address
- download_speed: The maximum download speed in Mbps (extract the higher number from the range)
- upload_speed: The maximum upload speed in Mbps (extract the higher number from the range)
- screenshot_url: The first browser recording URL from the results (if available)

Be precise with the data extraction and ensure all required fields are populated."""

        # Define structured output schema for broadband data
        self.structured_output_schema = {
            "type": "object",
            "properties": {
                "exchange_station": {
                    "type": "string",
                    "description": "Name of the telephone exchange"
                },
                "download_speed": {
                    "type": "number",
                    "description": "Maximum download speed in Mbps"
                },
                "upload_speed": {
                    "type": "number",
                    "description": "Maximum upload speed in Mbps"
                },
                "screenshot_url": {
                    "type": "string",
                    "description": "URL of the browser recording"
                }
            },
            "required": ["exchange_station", "download_speed", "upload_speed"]
        }

        # Tool configurations
        self.tool_configs = [
            {
                "tool_name": "browser_broadband",
                "lambda_arn": self.broadband_tool_arn,
                "requires_approval": False
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
                    self.broadband_tool_arn
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

        # Create the state machine
        self.state_machine = sfn.CfnStateMachine(
            self, "BroadbandCheckerStructuredStateMachine",
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