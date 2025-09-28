"""
CDK Stack for Broadband Checker Agent with Structured Output Support.
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    Duration,
    CfnOutput
)
from constructs import Construct
import json
import os
import sys

# Import structured output config
sys.path.append(os.path.join(os.path.dirname(__file__), '../../lambda/agents/broadband_checker'))
from structured_output_config import STRUCTURED_OUTPUT_CONFIG


class BroadbandCheckerAgentStack(Stack):
    """
    Stack for the Broadband Checker agent with structured output capability.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_registry_table: dynamodb.Table,
        shared_lambdas: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Reference shared Lambda functions
        self.prepare_context_fn = shared_lambdas['prepare_agent_context']
        self.validate_output_fn = shared_lambdas['validate_structured_output']
        self.call_llm_fn = shared_lambdas['call_llm']

        # Create the Step Functions state machine
        self.state_machine = self._create_state_machine()

        # Register agent in the registry
        self._register_agent(agent_registry_table)

        # Outputs
        CfnOutput(
            self, "StateMachineArn",
            value=self.state_machine.state_machine_arn,
            description="Broadband Checker Agent State Machine ARN"
        )

    def _create_state_machine(self) -> sfn.StateMachine:
        """Create the Step Functions state machine with structured output support."""

        # Define the state machine using the JSON definition
        definition = {
            "Comment": "Broadband Checker Agent with Structured Output",
            "StartAt": "PrepareAgentContext",
            "States": {
                "PrepareAgentContext": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": self.prepare_context_fn.function_arn,
                        "Payload": {
                            "agent": "broadband-checker",
                            "messages.$": "$.messages",
                            "tools.$": "$.tools",
                            "system.$": "$.system",
                            "output_format.$": "$.output_format"
                        }
                    },
                    "ResultSelector": {
                        "tools.$": "$.Payload.tools",
                        "system.$": "$.Payload.system",
                        "messages.$": "$.Payload.messages",
                        "structured_output_config.$": "$.Payload.structured_output_config"
                    },
                    "ResultPath": "$.agent_context",
                    "Next": "CallLLM"
                },

                "CallLLM": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": self.call_llm_fn.function_arn,
                        "Payload": {
                            "model.$": "$.model",
                            "messages.$": "$.agent_context.messages",
                            "tools.$": "$.agent_context.tools",
                            "system.$": "$.agent_context.system",
                            "temperature.$": "$.temperature",
                            "max_tokens.$": "$.max_tokens"
                        }
                    },
                    "ResultPath": "$.llm_response",
                    "Next": "CheckToolCalls"
                },

                "CheckToolCalls": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.llm_response.tool_calls[0].name",
                            "StringEquals": "return_broadband_data",
                            "Next": "ValidateStructuredOutput"
                        },
                        {
                            "Variable": "$.llm_response.tool_calls",
                            "IsPresent": true,
                            "Next": "ExecuteTools"
                        },
                        {
                            "And": [
                                {
                                    "Variable": "$.agent_context.structured_output_config.enforced",
                                    "BooleanEquals": True
                                },
                                {
                                    "Variable": "$.structured_output",
                                    "IsPresent": False
                                }
                            ],
                            "Next": "EnforceStructuredOutput"
                        }
                    ],
                    "Default": "PrepareResponse"
                },

                "ValidateStructuredOutput": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": self.validate_output_fn.function_arn,
                        "Payload": {
                            "tool_call.$": "$.llm_response.tool_calls[0]",
                            "schema.$": "$.agent_context.structured_output_config.schema",
                            "messages.$": "$.llm_response.messages"
                        }
                    },
                    "ResultSelector": {
                        "valid.$": "$.Payload.valid",
                        "validated_output.$": "$.Payload.validated_output",
                        "errors.$": "$.Payload.errors",
                        "messages.$": "$.Payload.messages"
                    },
                    "ResultPath": "$.validation_result",
                    "Next": "CheckValidation"
                },

                "CheckValidation": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.validation_result.valid",
                            "BooleanEquals": True,
                            "Next": "SuccessWithStructuredOutput"
                        }
                    ],
                    "Default": "ValidationFailed"
                },

                "EnforceStructuredOutput": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": self.call_llm_fn.function_arn,
                        "Payload": {
                            "model.$": "$.model",
                            "messages": [{
                                "role": "user",
                                "content": "Please extract the broadband information and use the return_broadband_data tool with the following fields: exchange_station, download_speed, upload_speed, and screenshot_url if available."
                            }],
                            "tools.$": "States.Array($.agent_context.structured_output_config.tool)",
                            "system": "You MUST use the return_broadband_data tool. Extract the information from our previous conversation.",
                            "temperature": 0.3,
                            "max_tokens": 1024
                        }
                    },
                    "ResultPath": "$.enforcement_response",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "MaxAttempts": 2,
                            "IntervalSeconds": 1
                        }
                    ],
                    "Next": "ValidateEnforcedOutput"
                },

                "ValidateEnforcedOutput": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": self.validate_output_fn.function_arn,
                        "Payload": {
                            "tool_call.$": "$.enforcement_response.tool_calls[0]",
                            "schema.$": "$.agent_context.structured_output_config.schema",
                            "messages.$": "$.llm_response.messages"
                        }
                    },
                    "ResultPath": "$.enforced_validation",
                    "Next": "CheckEnforcedValidation"
                },

                "CheckEnforcedValidation": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.enforced_validation.valid",
                            "BooleanEquals": True,
                            "Next": "SuccessWithStructuredOutput"
                        }
                    ],
                    "Default": "StructuredOutputFailed"
                },

                "ExecuteTools": {
                    "Type": "Pass",
                    "Comment": "Tool execution would happen here",
                    "Next": "CallLLM"
                },

                "PrepareResponse": {
                    "Type": "Pass",
                    "Parameters": {
                        "messages.$": "$.llm_response.messages",
                        "final_answer.$": "$.llm_response.messages[-1].content",
                        "structured_output": null
                    },
                    "Next": "Success"
                },

                "SuccessWithStructuredOutput": {
                    "Type": "Pass",
                    "Parameters": {
                        "messages.$": "$.validation_result.messages",
                        "structured_output.$": "$.validation_result.validated_output",
                        "success": true
                    },
                    "Next": "Success"
                },

                "ValidationFailed": {
                    "Type": "Fail",
                    "Error": "ValidationFailed",
                    "Cause": "Structured output validation failed"
                },

                "StructuredOutputFailed": {
                    "Type": "Fail",
                    "Error": "StructuredOutputEnforcementFailed",
                    "Cause": "Could not extract structured output after enforcement"
                },

                "Success": {
                    "Type": "Succeed"
                }
            }
        }

        # Create state machine
        return sfn.StateMachine(
            self, "BroadbandCheckerStateMachine",
            state_machine_name="broadband-checker-agent",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            state_machine_type=sfn.StateMachineType.EXPRESS,
            timeout=Duration.minutes(5),
            tracing_enabled=True
        )

    def _register_agent(self, agent_registry_table: dynamodb.Table):
        """Register the agent in the agent registry with structured output config."""

        agent_entry = {
            "agentId": "broadband-checker",
            "agentArn": self.state_machine.state_machine_arn,
            "description": "Checks broadband availability for UK addresses",
            "category": "utilities",
            "structuredOutput": STRUCTURED_OUTPUT_CONFIG
        }

        # In a real implementation, this would write to DynamoDB
        # For now, we'll output it for manual registration
        print(f"Agent registration entry: {json.dumps(agent_entry, indent=2)}")