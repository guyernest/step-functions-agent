"""
Step Functions Template Generator for Unified Rust LLM Service

This module generates Step Functions definitions that work with the unified Rust LLM service,
passing provider configurations dynamically based on the selected model.
"""

import json
from typing import List, Dict, Any


class UnifiedLLMStepFunctionsGenerator:
    """Generates Step Functions definitions for agents using the unified Rust LLM service"""
    
    @staticmethod
    def generate_unified_llm_agent_definition(
        agent_name: str,
        unified_llm_arn: str,
        tool_configs: List[Dict[str, Any]],
        system_prompt: str,
        default_provider: str = "anthropic",
        default_model: str = "claude-3-5-sonnet-20241022",
        structured_output_schema: Dict[str, Any] = None,
        llm_models_table_name: str = None,
        agent_registry_table_name: str = None,
        tool_registry_table_name: str = None,
        approval_activity_arn: str = None
    ) -> str:
        """
        Generate a Step Functions definition for the unified Rust LLM service

        Args:
            agent_name: Name of the agent
            unified_llm_arn: ARN of the unified Rust LLM Lambda function
            tool_configs: List of tool configurations with tool_name, lambda_arn, etc.
            system_prompt: System prompt for the agent
            default_provider: Default LLM provider (openai, anthropic, gemini)
            default_model: Default model ID for the provider
            structured_output_schema: Optional schema for structured output
            llm_models_table_name: Name of LLM models DynamoDB table
            agent_registry_table_name: Name of agent registry DynamoDB table
            tool_registry_table_name: Name of tool registry DynamoDB table
            approval_activity_arn: ARN of approval activity for human approval tools

        Returns:
            JSON string of the Step Functions definition
        """
        
        # Tool definitions will be resolved dynamically from DynamoDB at runtime
        # This generator creates static definitions based on tool configs
        tool_definitions = []
        tool_names = []

        for config in tool_configs:
            tool_name = config["tool_name"]
            tool_names.append(tool_name)

            # Create basic tool definition from config
            # Full schema will be resolved from DynamoDB at runtime
            tool_definitions.append({
                "name": tool_name,
                "description": f"Tool: {tool_name}",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            })

        # Create structured output tool if schema provided
        structured_output_tool = None
        if structured_output_schema:
            structured_output_tool = {
                "name": f"return_{agent_name}_data",
                "description": f"Return structured {agent_name} data in the required format",
                "input_schema": structured_output_schema
            }
        
        # Generate tool routing choices
        tool_choices = UnifiedLLMStepFunctionsGenerator._generate_tool_choices(
            tool_configs,
            agent_name=agent_name,
            structured_output_schema=structured_output_schema,
            approval_activity_arn=approval_activity_arn
        )
        
        # Build the complete state machine definition
        definition = {
            "Comment": f"{agent_name} - Unified Rust LLM Service with Dynamic Provider Configuration",
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
                    "Next": "Load LLM Provider Config",
                    "Assign": {
                        "agent_config": "{% $states.result.Item %}",
                        "system_prompt": "{% $states.result.Item.system_prompt.S %}",
                        "llm_provider": "{% $states.result.Item.llm_provider.S ? $states.result.Item.llm_provider.S : '" + default_provider + "' %}",
                        "llm_model": "{% $states.result.Item.llm_model.S ? $states.result.Item.llm_model.S : '" + default_model + "' %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    },
                    "Comment": "Load agent configuration including system prompt from Agent Registry"
                },
                "Load LLM Provider Config": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::dynamodb:getItem",
                    "Arguments": {
                        "TableName": llm_models_table_name or "LLMModels-prod",
                        "Key": {
                            "pk": {
                                "S": "{% $llm_provider & '#' & $llm_model %}"
                            }
                        }
                    },
                    "Next": "Build Provider Config",
                    "Assign": {
                        "llm_config": "{% $states.result.Item %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    },
                    "Comment": "Load LLM provider configuration from LLMModels table"
                },
                "Build Provider Config": {
                    "Type": "Pass",
                    "Next": "Load Tool Definitions",
                    "Assign": {
                        "provider_config": "{% ($provider := $split($llm_config.pk.S, '#')[0]; $model := $split($llm_config.pk.S, '#')[1]; $providerMappings := {'anthropic': {'endpoint': 'https://api.anthropic.com/v1/messages', 'auth_header_name': 'x-api-key', 'secret_key_name': 'ANTHROPIC_API_KEY', 'request_transformer': 'anthropic_v1', 'response_transformer': 'anthropic_v1'}, 'openai': {'endpoint': 'https://api.openai.com/v1/chat/completions', 'auth_header_name': 'Authorization', 'auth_header_prefix': 'Bearer ', 'secret_key_name': 'OPENAI_API_KEY', 'request_transformer': 'openai_v1', 'response_transformer': 'openai_v1'}, 'google': {'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/' & $model & ':generateContent', 'auth_header_name': 'x-goog-api-key', 'secret_key_name': 'GEMINI_API_KEY', 'request_transformer': 'gemini_v1', 'response_transformer': 'gemini_v1'}, 'bedrock': {'endpoint': 'https://bedrock-runtime.eu-west-1.amazonaws.com/model/' & $model & '/converse', 'auth_header_name': 'Authorization', 'auth_header_prefix': 'Bearer ', 'secret_key_name': 'AWS_BEARER_TOKEN_BEDROCK', 'request_transformer': 'bedrock_v1', 'response_transformer': 'bedrock_v1'}, 'amazon': {'endpoint': 'https://bedrock-runtime.eu-west-1.amazonaws.com/model/' & $model & '/converse', 'auth_header_name': 'Authorization', 'auth_header_prefix': 'Bearer ', 'secret_key_name': 'AWS_BEARER_TOKEN_BEDROCK', 'request_transformer': 'bedrock_v1', 'response_transformer': 'bedrock_v1'}}; $mapping := $providerMappings.$lookup($provider); {'provider_id': $provider, 'model_id': $model, 'endpoint': $mapping.endpoint, 'auth_header_name': $mapping.auth_header_name, 'auth_header_prefix': $mapping.auth_header_prefix, 'secret_path': '/ai-agent/llm-secrets/prod', 'secret_key_name': $mapping.secret_key_name, 'request_transformer': $mapping.request_transformer, 'response_transformer': $mapping.response_transformer, 'timeout': 30}) %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    },
                    "Comment": "Build provider configuration for unified LLM service"
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
                    "Next": "Call Unified LLM",
                    "Assign": {
                        "tools": "{% " + (
                            f"($toolNames := $states.result.name; $structuredToolName := '{structured_output_tool['name']}'; $structuredToolName in $toolNames ? $states.result : $append($states.result, {json.dumps(structured_output_tool)}))"
                            if structured_output_tool else "$states.result"
                        ) + " %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    },
                    "Comment": "Load tool definitions from Tool Registry for enabled tools"
                },
                "Call Unified LLM": {
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
                            "provider_config": "{% $provider_config %}",
                            "messages": "{% ($messages := $states.input.messages; $hasSystemMessage := $messages[0].role = 'system'; $hasSystemMessage ? $messages : $append([{'role': 'system', 'content': $system_prompt}], $messages)) %}",
                            "tools": "{% $tools %}",
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": False
                        },
                        "FunctionName": unified_llm_arn
                    },
                    "Output": {
                        "messages": "{% $append($states.input.messages, [ $states.result.Payload.message ]) %}",
                        "metadata": "{% $states.result.Payload.metadata %}",
                        "function_calls": "{% $exists($states.result.Payload.function_calls) ? $states.result.Payload.function_calls : [] %}"
                    },
                    "Comment": "Call the unified Rust LLM service with provider configuration"
                },
                "Update Token Metrics": {
                    "Type": "Task",
                    "Arguments": {
                        "Namespace": "AI-Agents",
                        "MetricData": [
                            {
                                "MetricName": "InputTokens",
                                "Value": "{% $states.input.metadata.tokens_used.input_tokens %}",
                                "Unit": "Count",
                                "Dimensions": [
                                    {
                                        "Name": "agent",
                                        "Value": agent_name
                                    },
                                    {
                                        "Name": "state_machine_name",
                                        "Value": "{% $states.context.StateMachine.Name %}"
                                    },
                                    {
                                        "Name": "provider",
                                        "Value": "{% $states.input.metadata.provider_id %}"
                                    },
                                    {
                                        "Name": "model",
                                        "Value": "{% $states.input.metadata.model_id %}"
                                    }
                                ]
                            },
                            {
                                "MetricName": "OutputTokens",
                                "Value": "{% $states.input.metadata.tokens_used.output_tokens %}",
                                "Unit": "Count",
                                "Dimensions": [
                                    {
                                        "Name": "agent",
                                        "Value": agent_name
                                    },
                                    {
                                        "Name": "state_machine_name",
                                        "Value": "{% $states.context.StateMachine.Name %}"
                                    },
                                    {
                                        "Name": "provider",
                                        "Value": "{% $states.input.metadata.provider_id %}"
                                    },
                                    {
                                        "Name": "model",
                                        "Value": "{% $states.input.metadata.model_id %}"
                                    }
                                ]
                            }
                        ]
                    },
                    "Resource": "arn:aws:states:::aws-sdk:cloudwatch:putMetricData",
                    "Next": "Check for Tool Calls",
                    "Output": "{% $states.input %}",
                    "Comment": "Send token usage metrics to CloudWatch"
                },
                "Check for Tool Calls": {
                    "Type": "Choice",
                    "Comment": "Check if the LLM wants to call any tools",
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
                    "Comment": "Process each tool call in parallel",
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
                                "Comment": "Route to the appropriate tool handler",
                                "Choices": tool_choices,
                                "Default": "Unknown Tool"
                            },
                            **UnifiedLLMStepFunctionsGenerator._generate_tool_states(
                                tool_configs,
                                agent_name=agent_name,
                                structured_output_schema=structured_output_schema,
                                approval_activity_arn=approval_activity_arn
                            ),
                            "Unknown Tool": {
                                "Type": "Pass",
                                "Output": {
                                    "error": "Unknown tool requested"
                                },
                                "End": True
                            }
                        }
                    },
                    "Assign": {
                        "tool_results": "{% $type($states.result) = 'array' ? $states.result : [$states.result] %}"
                    },
                    "Output": {
                        "messages": "{% $states.input.messages %}"
                    }
                },
                "Prepare Tool Results": {
                    "Type": "Pass",
                    "Comment": "Format tool results for the next LLM call",
                    "Next": "Check for Structured Output" if structured_output_schema else "Call Unified LLM",
                    "Output": {
                        "messages": "{% $append($states.input.messages, [ { \"role\": \"user\", \"content\": [$filter($tool_results, function($v) { $v != {} })] } ]) %}"
                    } if not structured_output_schema else {
                        "messages": "{% $append($states.input.messages, [ { \"role\": \"user\", \"content\": [$filter($tool_results, function($v) { $v != {} })] } ]) %}",
                        "structured_output": "{% ($filtered := $tool_results[$.type = 'structured_output']; $count($filtered) > 0 ? $filtered[0] : null) %}"
                    }
                },
                "Success": {
                    "Type": "Succeed",
                    "Comment": "Agent completed successfully"
                }
            }
        }

        # Add structured output check state if schema provided
        if structured_output_schema:
            definition["States"]["Check for Structured Output"] = {
                "Type": "Choice",
                "Choices": [
                    {
                        "Condition": "{% $states.input.structured_output != null %}",
                        "Next": "Success with Structured Output"
                    }
                ],
                "Default": "Call Unified LLM"
            }

            definition["States"]["Success with Structured Output"] = {
                "Type": "Pass",
                "Output": {
                    "messages": "{% $states.input.messages %}",
                    "structured_output": "{% $states.input.structured_output.content %}",
                    "success": "{% true %}"
                },
                "End": True
            }
        
        return json.dumps(definition, indent=2)
    
    @staticmethod
    def _generate_tool_choices(tool_configs: List[Dict[str, Any]], agent_name: str = None,
                              structured_output_schema: Dict[str, Any] = None,
                              approval_activity_arn: str = None) -> List[Dict[str, Any]]:
        """Generate the Choice conditions for tool routing"""
        choices = []
        for config in tool_configs:
            tool_name = config["tool_name"]
            choices.append({
                "Condition": "{% $states.input.name = '" + tool_name + "' %}",
                "Next": f"Execute {tool_name}"
            })

        # Add structured output tool routing if schema provided
        if structured_output_schema:
            structured_output_tool_name = f"return_{agent_name}_data"
            choices.append({
                "Condition": "{% $states.input.name = '" + structured_output_tool_name + "' %}",
                "Next": "Process Structured Output"
            })

        return choices
    
    @staticmethod
    def _generate_tool_states(tool_configs: List[Dict[str, Any]],
                             agent_name: str = None,
                             structured_output_schema: Dict[str, Any] = None,
                             approval_activity_arn: str = None) -> Dict[str, Any]:
        """Generate the tool execution states"""
        states = {}
        
        for config in tool_configs:
            tool_name = config["tool_name"]
            lambda_arn = config.get("lambda_arn")
            requires_activity = config.get("requires_activity", False)
            activity_type = config.get("activity_type")
            
            if requires_activity and activity_type == "human_approval" and approval_activity_arn:
                # Tool requires human approval
                states[f"Execute {tool_name}"] = {
                    "Type": "Parallel",
                    "Comment": f"Execute {tool_name} with human approval",
                    "Branches": [
                        {
                            "StartAt": f"Request Approval for {tool_name}",
                            "States": {
                                f"Request Approval for {tool_name}": {
                                    "Type": "Task",
                                    "Resource": "arn:aws:states:::activity:send",
                                    "Arguments": {
                                        "ActivityArn": approval_activity_arn,
                                        "Input": {
                                            "tool_name": tool_name,
                                            "tool_input": "{% $states.input.input %}",
                                            "message": f"Approval required for {tool_name}"
                                        }
                                    },
                                    "TimeoutSeconds": 300,
                                    "HeartbeatSeconds": 30,
                                    "Next": f"Approval Decision for {tool_name}"
                                },
                                f"Approval Decision for {tool_name}": {
                                    "Type": "Choice",
                                    "Choices": [
                                        {
                                            "Condition": "{% $states.input.approved %}",
                                            "Next": f"Invoke {tool_name}"
                                        }
                                    ],
                                    "Default": f"Rejected {tool_name}"
                                },
                                f"Invoke {tool_name}": {
                                    "Type": "Task",
                                    "Resource": "arn:aws:states:::lambda:invoke",
                                    "Arguments": {
                                        "FunctionName": lambda_arn,
                                        "Payload": {
                                            "name": "{% $states.input.tool_request.name %}",
                                            "id": "{% $states.input.tool_request.id %}",
                                            "input": "{% $states.input.tool_request.input %}"
                                        }
                                    },
                                    "End": True,
                                    "Output": "{% $states.result.Payload %}"
                                },
                                f"Rejected {tool_name}": {
                                    "Type": "Pass",
                                    "Output": {
                                        "type": "tool_result",
                                        "tool_use_id": "{% $states.input.tool_request.id %}",
                                        "name": tool_name,
                                        "content": {
                                            "status": "rejected",
                                            "message": f"Tool execution rejected by user: {tool_name}"
                                        }
                                    },
                                    "End": True
                                }
                            }
                        }
                    ],
                    "End": True,
                    "Output": "{% $states.result[0] %}"
                }
            elif requires_activity and activity_type == "remote_execution":
                # Remote execution workflow: Activity → Check Response → Return Result
                remote_activity_arn = config.get("activity_arn")
                if remote_activity_arn:
                    states[f"Execute {tool_name}"] = {
                        "Type": "Parallel",
                        "Comment": f"Execute {tool_name} via remote activity",
                        "Branches": [
                            {
                                "StartAt": f"Wait for Remote {tool_name}",
                                "States": {
                                    f"Wait for Remote {tool_name}": {
                                        "Type": "Task",
                                        "Resource": remote_activity_arn,
                                        "TimeoutSeconds": 300,  # 5 minute timeout
                                        "Arguments": {
                                            "tool_name": tool_name,
                                            "tool_use_id": "{% $states.input.id %}",
                                            "tool_input": "{% $states.input.input %}",
                                            "timestamp": "{% $states.context.Execution.StartTime %}",
                                            "context": {
                                                "execution_name": "{% $states.context.Execution.Name %}",
                                                "state_machine": "{% $states.context.StateMachine.Name %}"
                                            }
                                        },
                                        "Catch": [{
                                            "ErrorEquals": ["States.Timeout"],
                                            "Next": f"Remote Timeout {tool_name}"
                                        }],
                                        "Next": f"Process Remote Response {tool_name}",
                                        "Comment": f"Wait for remote system to process {tool_name}"
                                    },
                                    f"Process Remote Response {tool_name}": {
                                        "Type": "Choice",
                                        "Choices": [{
                                            "Condition": "{% $states.input.approved %}",
                                            "Next": f"Remote Approved {tool_name}"
                                        }],
                                        "Default": f"Remote Rejected {tool_name}",
                                        "Comment": f"Check if remote execution was approved"
                                    },
                                    f"Remote Approved {tool_name}": {
                                        "Type": "Pass",
                                        "End": True,
                                        "Output": {
                                            "type": "tool_result",
                                            "tool_use_id": "{% $states.input.tool_use_id %}",
                                            "name": tool_name,
                                            "content": "{% $type($states.input.tool_input) = 'object' ? $string($states.input.tool_input) : $states.input.tool_input %}"
                                        },
                                        "Comment": f"Return approved remote execution result"
                                    },
                                    f"Remote Rejected {tool_name}": {
                                        "Type": "Pass",
                                        "End": True,
                                        "Output": {
                                            "type": "tool_result",
                                            "tool_use_id": "{% $states.input.tool_use_id %}",
                                            "name": tool_name,
                                            "content": {
                                                "status": "rejected",
                                                "message": "{% $states.input.rejection_reason ? $states.input.rejection_reason : 'Remote execution was rejected' %}"
                                            }
                                        },
                                        "Comment": f"Return rejection from remote system"
                                    },
                                    f"Remote Timeout {tool_name}": {
                                        "Type": "Pass",
                                        "End": True,
                                        "Output": {
                                            "type": "tool_result",
                                            "tool_use_id": "{% $states.input.id %}",
                                            "name": tool_name,
                                            "content": {
                                                "status": "timeout",
                                                "message": f"Remote execution of {tool_name} timed out after 5 minutes"
                                            }
                                        },
                                        "Comment": f"Handle timeout for remote execution"
                                    }
                                }
                            }
                        ],
                        "End": True,
                        "Output": "{% $states.result[0] %}"
                    }
                else:
                    print(f"Warning: Remote execution tool '{tool_name}' missing activity_arn, falling back to standard execution")
                    # Fallback to standard execution
                    states[f"Execute {tool_name}"] = {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::lambda:invoke",
                        "Comment": f"Execute {tool_name}",
                        "Arguments": {
                            "FunctionName": lambda_arn,
                            "Payload": {
                                "name": "{% $states.input.name %}",
                                "id": "{% $states.input.id %}",
                                "input": "{% $states.input.input %}"
                            }
                        },
                        "End": True,
                        "Output": "{% $states.result.Payload %}"
                    }
            else:
                # Check if tool requires polling interval
                polling_interval = config.get('polling_interval')
                if polling_interval:
                    # Add wait state before tool execution for polling
                    states[f"Execute {tool_name}"] = {
                        "Type": "Wait",
                        "Comment": f"Wait {polling_interval} seconds before {tool_name}",
                        "Seconds": polling_interval,
                        "Next": f"Invoke {tool_name} After Wait"
                    }
                    states[f"Invoke {tool_name} After Wait"] = {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::lambda:invoke",
                        "Comment": f"Execute {tool_name} after polling interval",
                        "Arguments": {
                            "FunctionName": lambda_arn,
                            "Payload": {
                                "name": "{% $states.input.name %}",
                                "id": "{% $states.input.id %}",
                                "input": "{% $states.input.input %}",
                                "polling_metadata": {
                                    "interval": polling_interval,
                                    "max_attempts": config.get('max_polling_attempts', 20)
                                }
                            }
                        },
                        "End": True,
                        "Output": "{% $states.result.Payload %}"
                    }
                else:
                    # Direct tool execution without approval or wait
                    states[f"Execute {tool_name}"] = {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::lambda:invoke",
                        "Comment": f"Execute {tool_name}",
                        "Arguments": {
                            "FunctionName": lambda_arn,
                            "Payload": {
                                "name": "{% $states.input.name %}",
                                "id": "{% $states.input.id %}",
                                "input": "{% $states.input.input %}"
                            }
                        },
                        "End": True,
                        "Output": "{% $states.result.Payload %}"
                    }

        # Add structured output processing state if schema provided
        if structured_output_schema:
            states["Process Structured Output"] = {
                "Type": "Pass",
                "End": True,
                "Output": {
                    "type": "structured_output",
                    "tool_use_id": "{% $states.input.id %}",
                    "name": f"return_{agent_name}_data",
                    "content": "{% $states.input.input %}"
                }
            }

        return states