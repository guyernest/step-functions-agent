"""
CDK Stack for Broadband Checker Agent with Structured Output Support.
Uses the same pattern as other unified LLM agents but with structured output tool injection.
"""

from aws_cdk import (
    Stack,
    aws_stepfunctions as sfn,
    aws_iam as iam,
    aws_logs as logs,
    Duration,
    custom_resources as cr,
    CfnOutput,
    Fn,
    RemovalPolicy,
    Tags,
    Aws
)
from constructs import Construct
import json
from datetime import datetime, timezone


class BroadbandCheckerStructuredV2Stack(Stack):
    """
    Stack for the Broadband Checker agent with structured output capability.
    Uses the same pattern as unified LLM agents with minimal changes.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "prod",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.agent_name = "broadband-checker-structured-v2"

        # Import shared resources from other stacks
        self._import_shared_resources()

        # Create agent execution role
        self._create_agent_execution_role()

        # Create the Step Functions state machine
        self.state_machine = self._create_state_machine()

        # Register the agent in the registry
        self._register_agent()

        # Add tags for UI filtering
        Tags.of(self.state_machine).add("Application", "StepFunctionsAgent")
        Tags.of(self.state_machine).add("Type", "Agent")
        Tags.of(self.state_machine).add("AgentName", self.agent_name)
        Tags.of(self.state_machine).add("Environment", self.env_name)
        Tags.of(self.state_machine).add("ManagedBy", "StepFunctionsAgentUI")

        # Outputs
        CfnOutput(
            self, "StateMachineArn",
            value=self.state_machine.state_machine_arn,
            export_name=f"BroadbandCheckerStructuredV2StateMachineArn-{env_name}",
            description="Broadband Checker Agent V2 State Machine ARN"
        )

    def _import_shared_resources(self):
        """Import ARNs and resources from shared stacks."""

        # Import Unified LLM Lambda ARN
        self.unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{self.env_name}")

        # Import Agent Core browser tool Lambda ARN
        self.broadband_tool_arn = Fn.import_value(f"AgentCoreBrowserLambdaArn-{self.env_name}")

        # Import ValidateStructuredOutput Lambda ARN (if we want validation)
        self.validate_output_arn = Fn.import_value(f"ValidateStructuredOutputLambdaArn-{self.env_name}")

        # Agent Registry table
        self.agent_registry_table_name = f"AgentRegistry-{self.env_name}"
        self.agent_registry_table_arn = f"arn:aws:dynamodb:{Aws.REGION}:{Aws.ACCOUNT_ID}:table/AgentRegistry-{self.env_name}"

        # Tool Registry table
        self.tool_registry_table_name = f"ToolRegistry-{self.env_name}"
        self.tool_registry_table_arn = f"arn:aws:dynamodb:{Aws.REGION}:{Aws.ACCOUNT_ID}:table/ToolRegistry-{self.env_name}"

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution."""

        # Create agent-specific log group
        self.log_group = logs.LogGroup(
            self,
            f"{self.agent_name}LogGroup",
            log_group_name=f"/aws/stepfunctions/{self.agent_name}-{self.env_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.execution_role = iam.Role(
            self,
            f"{self.agent_name}ExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )

        # Grant Step Functions logging permissions
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                resources=[
                    self.log_group.log_group_arn,
                    f"{self.log_group.log_group_arn}:*"
                ]
            )
        )

        # Grant Lambda invoke permissions
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["lambda:InvokeFunction"],
                resources=[
                    self.unified_llm_arn,
                    self.broadband_tool_arn,
                    self.validate_output_arn
                ]
            )
        )

        # Grant DynamoDB access
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["dynamodb:GetItem", "dynamodb:Query"],
                resources=[
                    self.agent_registry_table_arn,
                    self.tool_registry_table_arn,
                    f"{self.tool_registry_table_arn}/index/*"
                ]
            )
        )

        # Grant CloudWatch metrics permissions
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # Grant X-Ray permissions
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )

    def _create_state_machine(self) -> sfn.StateMachine:
        """Create the Step Functions state machine using the unified LLM pattern."""

        # System prompt for broadband checking
        system_prompt = """You are a UK broadband availability checker with structured output capability.

When checking broadband:
1. Use the browser_broadband tool to check availability at the given address
2. After checking, use the return_broadband_data tool to provide structured output with:
   - exchange_station: The telephone exchange name
   - download_speed: Maximum download speed in Mbps
   - upload_speed: Maximum upload speed in Mbps
   - screenshot_url: URL of the browser recording (if available)

Always provide structured output using return_broadband_data after checking availability."""

        # Define the structured output tool
        structured_output_tool = {
            "name": "return_broadband_data",
            "description": "Return structured broadband availability data",
            "input_schema": {
                "type": "object",
                "properties": {
                    "exchange_station": {
                        "type": "string",
                        "description": "The telephone exchange serving this address"
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
        }

        # Define the state machine using the unified LLM pattern
        definition = {
            "Comment": "Broadband Checker with Structured Output - Unified LLM Pattern",
            "QueryLanguage": "JSONata",
            "StartAt": "Load Tools",
            "States": {
                "Load Tools": {
                    "Type": "Map",
                    "Items": "{% ['browser_broadband'] %}",
                    "ItemProcessor": {
                        "ProcessorConfig": {
                            "Mode": "INLINE"
                        },
                        "StartAt": "GetToolDefinition",
                        "States": {
                            "GetToolDefinition": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::dynamodb:getItem",
                                "Arguments": {
                                    "TableName": self.tool_registry_table_name,
                                    "Key": {
                                        "tool_name": {
                                            "S": "{% $states.input %}"
                                        }
                                    }
                                },
                                "End": True,
                                "Output": {
                                    "name": "{% $states.result.Item.tool_name.S %}",
                                    "description": "{% $states.result.Item.description.S %}",
                                    "input_schema": "{% $parse($states.result.Item.input_schema.S) %}"
                                }
                            }
                        }
                    },
                    "Next": "Call Unified LLM",
                    "Assign": {
                        "tools": "{% $append($states.result, " + json.dumps(structured_output_tool) + ") %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    }
                },

                "Call Unified LLM": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Arguments": {
                        "FunctionName": self.unified_llm_arn,
                        "Payload": {
                            "name": self.agent_name,
                            "provider_config": {
                                "provider_id": "{% $exists($states.input.provider) ? $states.input.provider : 'anthropic' %}",
                                "model_id": "{% $exists($states.input.model) ? $states.input.model : 'claude-3-5-sonnet-20241022' %}",
                                "endpoint": "https://api.anthropic.com/v1/messages",
                                "auth_header_name": "x-api-key",
                                "secret_path": "/ai-agent/llm-secrets/prod",
                                "secret_key_name": "ANTHROPIC_API_KEY",
                                "request_transformer": "anthropic_v1",
                                "response_transformer": "anthropic_v1",
                                "timeout": 30
                            },
                            "messages": "{% ($messages := $states.input.messages; $hasSystemMessage := $messages[0].role = 'system'; $hasSystemMessage ? $messages : $append([{'role': 'system', 'content': " + json.dumps(system_prompt) + "}], $messages)) %}",
                            "tools": "{% $tools %}",
                            "temperature": "{% $exists($states.input.temperature) ? $states.input.temperature : 0.7 %}",
                            "max_tokens": "{% $exists($states.input.max_tokens) ? $states.input.max_tokens : 4096 %}",
                            "stream": False
                        }
                    },
                    "Output": {
                        "messages": "{% $append($states.input.messages, [$states.result.Payload.message]) %}",
                        "metadata": "{% $states.result.Payload.metadata %}",
                        "function_calls": "{% $exists($states.result.Payload.function_calls) ? $states.result.Payload.function_calls : [] %}"
                    },
                    "Next": "Check for Tool Calls"
                },

                "Check for Tool Calls": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Condition": "{% $exists($states.input.function_calls) and $count($states.input.function_calls) > 0 %}",
                            "Next": "Map Tool Calls"
                        }
                    ],
                    "Default": "Success"
                },

                "Map Tool Calls": {
                    "Type": "Map",
                    "Items": "{% $states.input.function_calls %}",
                    "MaxConcurrency": 5,
                    "Next": "Prepare Tool Results",
                    "ItemProcessor": {
                        "ProcessorConfig": {
                            "Mode": "INLINE"
                        },
                        "StartAt": "Route Tool Call",
                        "States": {
                            "Route Tool Call": {
                                "Type": "Choice",
                                "Choices": [
                                    {
                                        "Condition": "{% $states.input.name = 'browser_broadband' %}",
                                        "Next": "Execute browser_broadband"
                                    },
                                    {
                                        "Condition": "{% $states.input.name = 'return_broadband_data' %}",
                                        "Next": "Process Structured Output"
                                    }
                                ],
                                "Default": "Unknown Tool"
                            },
                            "Execute browser_broadband": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::lambda:invoke",
                                "Arguments": {
                                    "FunctionName": self.broadband_tool_arn,
                                    "Payload": {
                                        "name": "{% $states.input.name %}",
                                        "id": "{% $states.input.id %}",
                                        "input": "{% $states.input.input %}"
                                    }
                                },
                                "End": True,
                                "Output": "{% $states.result.Payload %}"
                            },
                            "Process Structured Output": {
                                "Type": "Pass",
                                "End": True,
                                "Output": {
                                    "type": "structured_output",
                                    "tool_use_id": "{% $states.input.id %}",
                                    "name": "return_broadband_data",
                                    "content": {
                                        "exchange_station": "{% $states.input.input.exchange_station %}",
                                        "download_speed": "{% $states.input.input.download_speed %}",
                                        "upload_speed": "{% $states.input.input.upload_speed %}",
                                        "screenshot_url": "{% $states.input.input.screenshot_url %}"
                                    }
                                }
                            },
                            "Unknown Tool": {
                                "Type": "Pass",
                                "Output": {
                                    "error": "Unknown tool requested"
                                },
                                "End": True
                            }
                        }
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}",
                        "tool_results": "{% $states.result %}"
                    }
                },

                "Prepare Tool Results": {
                    "Type": "Pass",
                    "Next": "Check for Structured Output",
                    "Output": {
                        "messages": "{% $append($states.input.messages, [{'role': 'user', 'content': $states.input.tool_results}]) %}",
                        "structured_output": "{% ($filtered := $states.input.tool_results[$.type = 'structured_output']; $count($filtered) > 0 ? $filtered[0] : null) %}"
                    }
                },

                "Check for Structured Output": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Condition": "{% $states.input.structured_output != null %}",
                            "Next": "Success with Structured Output"
                        }
                    ],
                    "Default": "Call Unified LLM"
                },

                "Success with Structured Output": {
                    "Type": "Pass",
                    "Output": {
                        "messages": "{% $states.input.messages %}",
                        "structured_output": "{% $states.input.structured_output.content %}",
                        "success": "{% true %}"
                    },
                    "Next": "Success"
                },

                "Success": {
                    "Type": "Succeed"
                }
            }
        }

        # Create state machine
        return sfn.StateMachine(
            self, "BroadbandCheckerStateMachine",
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            role=self.execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )

    def _register_agent(self):
        """Register the agent in DynamoDB using AWS Custom Resource."""

        # Generate current timestamp
        current_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Create the agent item for DynamoDB
        agent_item = {
            "TableName": self.agent_registry_table_name,
            "Item": {
                "agentId": {"S": self.agent_name},
                "agentArn": {"S": self.state_machine.state_machine_arn},
                "agent_name": {"S": self.agent_name},
                "name": {"S": "Broadband Checker V2 (Structured Output)"},
                "description": {"S": "Broadband checker with structured output using unified LLM pattern"},
                "category": {"S": "utilities"},
                "stateMachineType": {"S": "STANDARD"},
                "status": {"S": "active"},
                "version": {"S": "v2.0"},
                "deployment_env": {"S": self.env_name},
                "created_at": {"S": current_timestamp},
                "updated_at": {"S": current_timestamp},
                "tools": {"S": json.dumps(["browser_broadband", "return_broadband_data"])},
                "llm_provider": {"S": "anthropic"},
                "llm_model": {"S": "claude-3-5-sonnet-20241022"},
                "metadata": {"S": json.dumps({
                    "stack": self.stack_name,
                    "type": "structured-output-agent",
                    "llm_type": "unified-rust"
                })}
            }
        }

        # Use AwsCustomResource to register the agent
        cr.AwsCustomResource(
            self,
            "RegisterAgent",
            on_create=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters=agent_item,
                physical_resource_id=cr.PhysicalResourceId.of(f"{self.agent_name}-{self.env_name}")
            ),
            on_update=cr.AwsSdkCall(
                service="dynamodb",
                action="putItem",
                parameters=agent_item,
                physical_resource_id=cr.PhysicalResourceId.of(f"{self.agent_name}-{self.env_name}")
            ),
            on_delete=cr.AwsSdkCall(
                service="dynamodb",
                action="deleteItem",
                parameters={
                    "TableName": self.agent_registry_table_name,
                    "Key": {
                        "agentId": {"S": self.agent_name}
                    }
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["dynamodb:PutItem", "dynamodb:DeleteItem"],
                    resources=[self.agent_registry_table_arn]
                )
            ])
        )