"""
Agent Core Wrapper Stack - Creates Step Functions state machines that wrap Agent Core agents
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_stepfunctions as sfn,
    aws_iam as iam,
    aws_lambda as _lambda,
    RemovalPolicy
)
from constructs import Construct
import json
from typing import Dict, Any, Optional
from pathlib import Path


class AgentCoreWrapperStack(Stack):
    """
    Stack for creating Step Functions wrappers around Agent Core agents
    These wrappers allow Agent Core agents to be invoked via Step Functions .sync pattern
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        agent_configs: Dict[str, Dict[str, Any]],
        env_name: str = "prod", 
        **kwargs
    ) -> None:
        """
        Initialize Agent Core Wrapper Stack
        
        Args:
            scope: CDK scope
            construct_id: Stack ID
            agent_configs: Dictionary of agent configurations
                          Keys are agent names, values are config dicts with:
                          - agent_id: Agent Core agent ID
                          - alias_id: Agent alias ID
                          - description: Agent description
            env_name: Environment name
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        self.agent_configs = agent_configs
        self.state_machines = {}
        
        # Create wrapper state machines for each agent
        for agent_name, config in agent_configs.items():
            self.state_machines[agent_name] = self._create_agent_wrapper(
                agent_name, config
            )
        
        # Create outputs
        self._create_outputs()
    
    def _create_agent_wrapper(
        self, 
        agent_name: str, 
        config: Dict[str, Any]
    ) -> sfn.StateMachine:
        """Create a Step Functions wrapper for an Agent Core agent"""
        
        # Create the state machine definition
        definition = {
            "Comment": f"Wrapper for Agent Core agent: {agent_name}",
            "StartAt": "ValidateInput",
            "States": {
                "ValidateInput": {
                    "Type": "Pass",
                    "Parameters": {
                        "agent_id": config["agent_id"],
                        "alias_id": config["alias_id"],
                        "session_id.$": "States.Default($.session_id, $$.Execution.Name)",
                        "input_text.$": "$.agent_config.input_text",
                        "enable_trace.$": "States.Default($.agent_config.enable_trace, true)",
                        "end_session.$": "States.Default($.agent_config.end_session, false)",
                        "session_attributes.$": "$.agent_config.session_attributes",
                        "prompt_session_attributes.$": "$.agent_config.prompt_session_attributes"
                    },
                    "ResultPath": "$.validated_input",
                    "Next": "InvokeAgentCore"
                },
                
                "InvokeAgentCore": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::bedrock:invokeAgent",
                    "Parameters": {
                        "AgentId.$": "$.validated_input.agent_id",
                        "AgentAliasId.$": "$.validated_input.alias_id",
                        "SessionId.$": "$.validated_input.session_id",
                        "InputText.$": "$.validated_input.input_text",
                        "EnableTrace.$": "$.validated_input.enable_trace",
                        "EndSession.$": "$.validated_input.end_session",
                        "SessionState": {
                            "SessionAttributes.$": "$.validated_input.session_attributes",
                            "PromptSessionAttributes.$": "$.validated_input.prompt_session_attributes"
                        }
                    },
                    "ResultPath": "$.agent_response",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ServiceUnavailable"],
                            "IntervalSeconds": 2,
                            "MaxAttempts": 3,
                            "BackoffRate": 2.0
                        }
                    ],
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "HandleError",
                            "ResultPath": "$.error_info"
                        }
                    ],
                    "Next": "ProcessResponse"
                },
                
                "ProcessResponse": {
                    "Type": "Pass",
                    "Parameters": {
                        "agent_messages": [
                            {
                                "role": "assistant",
                                "content.$": "$.agent_response.completion",
                                "metadata": {
                                    "agent_id": config["agent_id"],
                                    "agent_name": agent_name,
                                    "session_id.$": "$.validated_input.session_id",
                                    "trace_id.$": "$.agent_response.responseMetadata.traceId"
                                }
                            }
                        ],
                        "citations.$": "$.agent_response.citations",
                        "trace.$": "$.agent_response.trace",
                        "session_attributes.$": "$.agent_response.sessionState.sessionAttributes",
                        "prompt_session_attributes.$": "$.agent_response.sessionState.promptSessionAttributes",
                        "metadata": {
                            "status": "success",
                            "agent_name": agent_name,
                            "execution_time.$": "$$.State.EnteredTime"
                        }
                    },
                    "End": True
                },
                
                "HandleError": {
                    "Type": "Pass",
                    "Parameters": {
                        "agent_messages": [
                            {
                                "role": "assistant",
                                "content.$": "States.Format('I encountered an error while processing your request: {}', $.error_info.Cause)",
                                "metadata": {
                                    "agent_id": config["agent_id"],
                                    "agent_name": agent_name,
                                    "error": True
                                }
                            }
                        ],
                        "metadata": {
                            "status": "error",
                            "agent_name": agent_name,
                            "error_message.$": "$.error_info.Cause",
                            "error_type.$": "$.error_info.Error"
                        }
                    },
                    "End": True
                }
            }
        }
        
        # Create IAM role for the state machine
        role = iam.Role(
            self, f"{agent_name}WrapperRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                f"{agent_name}Policy": iam.PolicyDocument(
                    statements=[
                        # Bedrock Agent invocation permissions
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeAgent",
                                "bedrock:Retrieve"
                            ],
                            resources=[
                                f"arn:aws:bedrock:{self.region}:{self.account}:agent/{config['agent_id']}",
                                f"arn:aws:bedrock:{self.region}:{self.account}:agent-alias/{config['agent_id']}/{config['alias_id']}"
                            ]
                        ),
                        # CloudWatch Logs permissions for tracing
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            resources=["*"]
                        ),
                        # X-Ray tracing permissions
                        iam.PolicyStatement(
                            actions=[
                                "xray:PutTraceSegments",
                                "xray:PutTelemetryRecords"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        # Create the state machine
        state_machine = sfn.StateMachine(
            self, f"{agent_name}Wrapper",
            state_machine_name=f"agent-core-{agent_name}-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            role=role,
            tracing_enabled=True,
            comment=config.get("description", f"Agent Core wrapper for {agent_name}")
        )
        
        return state_machine
    
    @classmethod
    def from_deployment_output(
        cls,
        scope: Construct,
        construct_id: str,
        output_file: str,
        env_name: str = "prod",
        **kwargs
    ) -> "AgentCoreWrapperStack":
        """
        Create stack from Agent Core deployment output file
        
        Args:
            scope: CDK scope
            construct_id: Stack ID
            output_file: Path to deployment output JSON file
            env_name: Environment name
            
        Returns:
            AgentCoreWrapperStack instance
        """
        # Load deployment output
        with open(output_file, "r") as f:
            output = json.load(f)
        
        # Convert to agent config format
        agent_config = {
            output["agent_name"]: {
                "agent_id": output["agent_id"],
                "alias_id": output["alias_id"],
                "description": f"Agent Core agent: {output['agent_name']}"
            }
        }
        
        return cls(scope, construct_id, agent_config, env_name, **kwargs)
    
    def _create_outputs(self):
        """Create stack outputs"""
        
        for agent_name, state_machine in self.state_machines.items():
            # Export state machine ARN
            CfnOutput(
                self, f"{agent_name}StateMachineArn",
                value=state_machine.state_machine_arn,
                description=f"ARN of {agent_name} wrapper state machine",
                export_name=f"AgentCore-{agent_name}-StateMachineArn-{self.env_name}"
            )
            
            # Export state machine name
            CfnOutput(
                self, f"{agent_name}StateMachineName",
                value=state_machine.state_machine_name,
                description=f"Name of {agent_name} wrapper state machine"
            )


class AgentCoreIntegrationConstruct(Construct):
    """
    Construct for integrating Agent Core agents into the hybrid architecture
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_name: str,
        agent_id: str,
        alias_id: str,
        description: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Create an Agent Core integration
        
        Args:
            scope: CDK scope
            construct_id: Construct ID
            agent_name: Name of the agent
            agent_id: Agent Core agent ID
            alias_id: Agent alias ID
            description: Optional description
        """
        super().__init__(scope, construct_id, **kwargs)
        
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.alias_id = alias_id
        
        # Create the wrapper state machine
        self.state_machine = self._create_wrapper_state_machine(description)
        
    def _create_wrapper_state_machine(self, description: Optional[str]) -> sfn.StateMachine:
        """Create the wrapper state machine"""
        
        # Use simplified definition for construct
        definition = {
            "Comment": f"Agent Core wrapper: {self.agent_name}",
            "StartAt": "InvokeAgent",
            "States": {
                "InvokeAgent": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::bedrock:invokeAgent",
                    "Parameters": {
                        "AgentId": self.agent_id,
                        "AgentAliasId": self.alias_id,
                        "SessionId.$": "$.session_id",
                        "InputText.$": "$.agent_config.input_text",
                        "EnableTrace": True
                    },
                    "ResultPath": "$.agent_response",
                    "Next": "FormatResponse"
                },
                "FormatResponse": {
                    "Type": "Pass",
                    "Parameters": {
                        "agent_messages": [{
                            "role": "assistant",
                            "content.$": "$.agent_response.completion"
                        }],
                        "metadata": {
                            "agent_name": self.agent_name,
                            "session_id.$": "$.session_id"
                        }
                    },
                    "End": True
                }
            }
        }
        
        # Create minimal IAM role
        role = iam.Role(
            self, "Role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "BedrockPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["bedrock:InvokeAgent"],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        return sfn.StateMachine(
            self, "StateMachine",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            role=role,
            tracing_enabled=True
        )