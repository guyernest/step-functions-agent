"""
Step Functions Template Generator for Static Tool Definitions

This module generates static Step Functions definitions with explicit tool routing
for better observability and debugging in production environments.
"""

import json
from typing import List, Dict, Any
from ..shared.tool_definitions import AllTools


class StepFunctionsGenerator:
    """Generates static Step Functions definitions for agents"""
    
    @staticmethod
    def generate_static_agent_definition(
        agent_name: str,
        llm_arn: str,
        tool_configs: List[Dict[str, Any]],
        system_prompt: str,
        agent_registry_table_name: str = None,
        tool_registry_table_name: str = None
    ) -> str:
        """
        Generate a complete Step Functions definition with static tool routing
        
        Args:
            agent_name: Name of the agent
            llm_arn: ARN of the LLM Lambda function
            tool_configs: List of tool configurations with tool_name, lambda_arn, etc.
            system_prompt: System prompt for the agent
            agent_registry_table_name: Name of agent registry DynamoDB table
            tool_registry_table_name: Name of tool registry DynamoDB table
            
        Returns:
            JSON string of the Step Functions definition
        """
        
        # Get tool definitions from centralized registry
        all_tool_definitions = AllTools.get_all_tool_definitions()
        tool_definitions = []
        tool_names = []
        
        for config in tool_configs:
            tool_name = config["tool_name"]
            tool_names.append(tool_name)
            
            if tool_name in all_tool_definitions:
                tool_def = all_tool_definitions[tool_name]
                tool_definitions.append({
                    "name": tool_def.tool_name,
                    "description": tool_def.description,
                    "input_schema": tool_def.input_schema
                })
            else:
                print(f"Warning: Tool definition not found for '{tool_name}'")
        
        # Generate tool routing choices
        tool_choices = StepFunctionsGenerator._generate_tool_choices(tool_configs)
        
        # Build the complete state machine definition
        definition = {
            "Comment": f"{agent_name} - Static Tool Definitions for Production Observability with Dynamic Loading",
            "QueryLanguage": "JSONata",
            "StartAt": "Load Agent Configuration",
            "States": {
                "Load Agent Configuration": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::dynamodb:getItem",
                    "Arguments": {
                        "TableName": agent_registry_table_name or "AgentRegistry",
                        "Key": {
                            "agent_name": {
                                "S": agent_name
                            },
                            "version": {
                                "S": "v1.0"
                            }
                        }
                    },
                    "Next": "Load Tool Definitions",
                    "Assign": {
                        "agent_config": "{% $states.result.Item %}",
                        "system_prompt": "{% $states.result.Item.system_prompt.S %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    },
                    "Comment": "Load agent configuration including system prompt from Agent Registry"
                },
                "Load Tool Definitions": {
                    "Type": "Map", 
                    "Items": "{% $parse($agent_config.tools.S) %}",
                    "ItemProcessor": {
                        "ProcessorConfig": {
                            "Mode": "INLINE"
                        },
                        "StartAt": "Get Tool Details",
                        "States": {
                            "Get Tool Details": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::dynamodb:getItem",
                                "Arguments": {
                                    "TableName": tool_registry_table_name or "ToolRegistry",
                                    "Key": {
                                        "tool_name": {
                                            "S": "{% $states.input.tool_name %}"
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
                    "Next": "Call LLM",
                    "Assign": {
                        "tools": "{% $states.result %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    },
                    "Comment": "Load tool definitions from Tool Registry for enabled tools"
                },
                "Call LLM": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Retry": [
                        {
                            "ErrorEquals": [
                                "Lambda.ServiceException",
                                "Lambda.AWSLambdaException", 
                                "Lambda.SdkClientException",
                                "Lambda.TooManyRequestsException"
                            ],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                            "JitterStrategy": "FULL"
                        }
                    ],
                    "Next": "Update Token Metrics",
                    "Arguments": {
                        "Payload": {
                            "system": "{% $system_prompt %}",
                            "messages": "{% $states.input.messages %}",
                            "tools": "{% $tools %}"
                        },
                        "FunctionName": llm_arn
                    },
                    "Output": {
                        "messages": "{% $append($states.input.messages, [ { \"role\": \"assistant\", \"content\": $states.result.Payload.body.messages[-1].content } ]) %}",
                        "metadata": "{% $states.result.Payload.body.metadata %}",
                        "function_calls": "{% $states.result.Payload.body.function_calls %}"
                    },
                    "Comment": "Call the LLM with conversation history and available tools"
                },
                "Update Token Metrics": {
                    "Type": "Task",
                    "Arguments": {
                        "Namespace": "AI-Agents",
                        "MetricData": [
                            {
                                "MetricName": "InputTokens",
                                "Value": "{% $states.input.metadata.usage.input_tokens %}",
                                "Unit": "Count",
                                "Dimensions": [
                                    {
                                        "Name": "agent",
                                        "Value": agent_name
                                    },
                                    {
                                        "Name": "state_machine_name",
                                        "Value": "{% $states.context.StateMachine.Name %}"
                                    }
                                ]
                            },
                            {
                                "MetricName": "OutputTokens",
                                "Value": "{% $states.input.metadata.usage.output_tokens %}",
                                "Unit": "Count",
                                "Dimensions": [
                                    {
                                        "Name": "agent",
                                        "Value": agent_name
                                    },
                                    {
                                        "Name": "state_machine_name",
                                        "Value": "{% $states.context.StateMachine.Name %}"
                                    }
                                ]
                            }
                        ]
                    },
                    "Resource": "arn:aws:states:::aws-sdk:cloudwatch:putMetricData",
                    "Next": "Is done?",
                    "Output": "{% $states.input %}",
                    "Comment": "Record token usage metrics in CloudWatch"
                },
                "Is done?": {
                    "Type": "Choice",
                    "Default": "For each tool use",
                    "Choices": [
                        {
                            "Condition": "{% $exists($states.input.function_calls) and $count($states.input.function_calls) > 0 ? false : true %}",
                            "Next": "Prepare Output"
                        }
                    ],
                    "Comment": "Check if LLM is done or wants to use tools"
                },
                "Prepare Output": {
                    "Type": "Pass",
                    "End": True,
                    "Output": {
                        "messages": "{% $states.input.messages %}",
                        "output": {
                            "answer": "{% $states.input.messages[-1].content %}"
                        }
                    },
                    "Comment": "Extract final response"
                },
                "For each tool use": {
                    "Type": "Map",
                    "Items": "{% $states.input.function_calls %}",
                    "ItemProcessor": {
                        "ProcessorConfig": {
                            "Mode": "INLINE"
                        },
                        "StartAt": "Which Tool to Use?",
                        "States": tool_choices
                    },
                    "Next": "Call LLM",
                    "Output": {
                        "messages": "{% $append($states.input.messages, [ { \"role\": \"user\", \"content\": [$filter($states.result, function($v) { $v != {} })] } ]) %}"
                    },
                    "Comment": "Execute each tool call in parallel with static routing, filtering out empty results"
                }
            }
        }
        
        return json.dumps(definition, indent=2)
    
    @staticmethod
    def _generate_tool_choices(tool_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate the Choice state and tool execution states"""
        
        states = {
            "Which Tool to Use?": {
                "Type": "Choice",
                "Choices": [],
                "Default": "Tool Not Found",
                "Comment": "Static routing to specific tool Lambda functions"
            }
        }
        
        # Add a choice and execution state for each tool
        for config in tool_configs:
            tool_name = config["tool_name"]
            lambda_arn = config["lambda_arn"]
            requires_approval = config.get("requires_approval", False)
            
            # Add choice condition (JSONata syntax)
            states["Which Tool to Use?"]["Choices"].append({
                "Condition": "{% $states.input.name = '" + tool_name + "' %}",
                "Next": f"Execute {tool_name}"
            })
            
            # Add execution state
            states[f"Execute {tool_name}"] = {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Arguments": {
                        "FunctionName": lambda_arn,
                        "Payload": {
                            "name": "{% $states.input.name %}",
                            "id": "{% $states.input.id %}",
                            "input": "{% $states.input.input %}"
                        }
                    },
                    "Retry": [
                        {
                            "ErrorEquals": [
                                "Lambda.ServiceException",
                                "Lambda.AWSLambdaException",
                                "Lambda.SdkClientException",
                                "Lambda.TooManyRequestsException"
                            ],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 3,
                            "BackoffRate": 2,
                            "JitterStrategy": "FULL"
                        }
                    ],
                    "End": True,
                    "Output": "{% $states.result.Payload %}",
                    "Comment": f"Execute {tool_name} Lambda function"
            }
            
            # Add human approval state if needed
            if requires_approval:
                # Modify the choice to go to approval first
                states["Which Tool to Use?"]["Choices"][-1]["Next"] = f"Request Approval for {tool_name}"
                
                # Add approval state
                states[f"Request Approval for {tool_name}"] = {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
                    "Arguments": {
                        "QueueUrl": "HUMAN_APPROVAL_QUEUE_URL",  # Will be replaced
                        "MessageBody": {
                            "TaskToken.$": "$$.Task.Token",
                            "Tool": tool_name,
                            "Input": "{% $states.input %}"
                        }
                    },
                    "Next": f"Execute {tool_name}",
                    "Comment": f"Wait for human approval before executing {tool_name}"
                }
        
        # Add Tool Not Found state
        states["Tool Not Found"] = {
            "Type": "Pass",
            "End": True,
            "Output": {
                "error": "Tool not found",
                "tool_name": "{% $states.input.name %}"
            },
            "Comment": "Handle unknown tools"
        }
        
        return states