"""
Travel Time Checker Agent with Structured Output

This agent calculates travel times between locations using different transport modes
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


class TravelTimeCheckerStructuredStack(Stack):
    """CDK Stack for Travel Time Checker Agent with Structured Output using unified generator"""

    def __init__(self, scope: Construct, id: str, env_name: str = "dev", **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get environment
        self.env_name = env_name

        # Agent name
        self.agent_name = "travel-time-checker-structured"

        # Import shared resources
        self.agent_registry_table_name = self.node.try_get_context("agent_registry_table") or f"AgentRegistry-{self.env_name}"
        self.tool_registry_table_name = self.node.try_get_context("tool_registry_table") or f"ToolRegistry-{self.env_name}"
        self.llm_models_table_name = self.node.try_get_context("llm_models_table") or f"LLMModels-{self.env_name}"

        # Import unified LLM ARN
        self.unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{self.env_name}")

        # Import Google Maps tool ARN
        self.google_maps_tool_arn = Fn.import_value(f"GoogleMapsLambdaArn-{self.env_name}")

        # System prompt for the agent
        self.system_prompt = """You are a travel time calculation agent that helps users determine travel times between locations using different modes of transport.

When given a starting location (from_address) and destination (to_address), you will:
1. Use the maps_directions tool THREE times to get travel times for:
   - Driving mode
   - Walking mode
   - Bicycling mode
2. Extract the duration from each result
3. Return the results in a structured format

Important:
- Always call the maps_directions tool exactly THREE times with different modes
- Extract the total duration in minutes from each response
- The duration is typically provided in the format "X mins" or "X hours Y mins"
- Convert all durations to minutes (integer values)
- After getting all three results, call the return_travel_times function with the structured data

For the structured output:
- driving_time: Travel time by car in minutes
- walking_time: Travel time on foot in minutes
- cycling_time: Travel time by bicycle in minutes

Be precise with the data extraction and ensure all required fields are populated with integer values representing minutes."""

        # Define structured output schema for travel time data
        self.structured_output_schema = {
            "type": "object",
            "properties": {
                "driving_time": {
                    "type": "integer",
                    "description": "Travel time by car in minutes"
                },
                "walking_time": {
                    "type": "integer",
                    "description": "Travel time on foot in minutes"
                },
                "cycling_time": {
                    "type": "integer",
                    "description": "Travel time by bicycle in minutes"
                }
            },
            "required": ["driving_time", "walking_time", "cycling_time"]
        }

        # Tool configurations - only need maps_directions
        self.tool_configs = [
            {
                "tool_name": "maps_directions",
                "lambda_arn": self.google_maps_tool_arn,
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
                    self.google_maps_tool_arn
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
            self, "TravelTimeCheckerStructuredStateMachine",
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
            "description": "Travel time calculation agent with structured output",
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
            "tools": json.dumps([
                {"tool_name": "maps_directions", "enabled": True}
            ]),
            "structured_output": json.dumps({
                "enabled": True,
                "schemas": {
                    "travel_times": {
                        "schema": self.structured_output_schema
                    }
                },
                "output_fields": ["driving_time", "walking_time", "cycling_time"]
            }),
            "state_machine_arn": self.state_machine.attr_arn,
            "environment": self.env_name,
            "metadata": {
                "supports_batch_processing": True,
                "structured_output_enabled": True
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