"""
CDK Stack for Agent Core Browser Tool Wrapper
This creates a Step Functions state machine that wraps the Agent Core shopping agent
to provide a consistent interface with other Lambda tools.
"""

from aws_cdk import (
    Stack,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_logs as logs,
    aws_iam as iam,
    CfnOutput,
    Duration,
    RemovalPolicy
)
from constructs import Construct
import json


class AgentCoreBrowserWrapperStack(Stack):
    """
    Creates a Step Functions wrapper around Agent Core agent for browser automation.
    This maintains compatibility with the Lambda tool interface used by the supervisor.
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get Agent Core deployment info from context or parameters
        agent_runtime_arn = self.node.try_get_context("agent_runtime_arn")
        if not agent_runtime_arn:
            # Default to the deployed shopping agent
            agent_runtime_arn = "arn:aws:bedrock-agentcore:us-west-2:672915487120:runtime/shopping_agent-aw6O6r7uk5"
        
        # Create log group for the state machine
        log_group = logs.LogGroup(
            self, "AgentCoreBrowserWrapperLogs",
            log_group_name=f"/aws/stepfunctions/agentcore-browser-wrapper-{self.stack_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create IAM role for Step Functions
        state_machine_role = iam.Role(
            self, "AgentCoreBrowserWrapperRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "AgentCoreInvokePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "bedrock-agentcore:InvokeAgentRuntime",
                                "bedrock-agentcore:GetAgentRuntime"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogDelivery",
                                "logs:GetLogDelivery",
                                "logs:UpdateLogDelivery",
                                "logs:DeleteLogDelivery",
                                "logs:ListLogDeliveries",
                                "logs:PutResourcePolicy",
                                "logs:DescribeResourcePolicies",
                                "logs:DescribeLogGroups"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        # Define the state machine using JSONata expressions
        state_machine_definition = {
            "Comment": "Wrapper for Agent Core Browser Tool to maintain Lambda tool interface",
            "StartAt": "ValidateInput",
            "States": {
                "ValidateInput": {
                    "Type": "Pass",
                    "Parameters": {
                        "action.$": "$.action",
                        "session_id.$": "$.session_id",
                        "url.$": "$.url",
                        "query.$": "$.query",
                        "selectors.$": "$.selectors",
                        "credentials.$": "$.credentials",
                        "config.$": "$.config"
                    },
                    "Next": "RouteAction"
                },
                
                "RouteAction": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.action",
                            "StringEquals": "search",
                            "Next": "PrepareSearchRequest"
                        },
                        {
                            "Variable": "$.action",
                            "StringEquals": "extract",
                            "Next": "PrepareExtractRequest"
                        },
                        {
                            "Variable": "$.action",
                            "StringEquals": "authenticate",
                            "Next": "PrepareAuthRequest"
                        }
                    ],
                    "Default": "InvalidAction"
                },
                
                "PrepareSearchRequest": {
                    "Type": "Pass",
                    "Parameters": {
                        "prompt.$": "States.Format('Search for {} on {}', $.query, $.url)",
                        "test": False,
                        "original_request.$": "$"
                    },
                    "Next": "InvokeAgentCore"
                },
                
                "PrepareExtractRequest": {
                    "Type": "Pass",
                    "Parameters": {
                        "prompt.$": "States.Format('Extract data from {} using selectors: {}', $.url, States.JsonToString($.selectors))",
                        "test": False,
                        "original_request.$": "$"
                    },
                    "Next": "InvokeAgentCore"
                },
                
                "PrepareAuthRequest": {
                    "Type": "Pass",
                    "Parameters": {
                        "prompt.$": "States.Format('Authenticate on {} portal', $.url)",
                        "test": False,
                        "original_request.$": "$"
                    },
                    "Next": "InvokeAgentCore"
                },
                
                "InvokeAgentCore": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::http:invoke",
                    "Parameters": {
                        "ApiEndpoint.$": "States.Format('https://bedrock-agentcore.us-west-2.amazonaws.com/runtime/{}/invoke', States.ArrayGetItem(States.StringSplit('" + agent_runtime_arn + "', '/'), 1))",
                        "Method": "POST",
                        "Headers": {
                            "Content-Type": "application/json"
                        },
                        "Authentication": {
                            "ConnectionArn": "arn:aws:events:us-west-2:672915487120:connection/bedrock-agentcore/default"
                        },
                        "RequestBody": {
                            "prompt.$": "$.prompt",
                            "test.$": "$.test"
                        }
                    },
                    "ResultSelector": {
                        "agent_response.$": "$.ResponseBody",
                        "status_code.$": "$.StatusCode",
                        "original_request.$": "$.original_request"
                    },
                    "Retry": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "IntervalSeconds": 2,
                            "MaxAttempts": 3,
                            "BackoffRate": 2
                        }
                    ],
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "HandleError",
                            "ResultPath": "$.error"
                        }
                    ],
                    "Next": "FormatResponse"
                },
                
                "FormatResponse": {
                    "Type": "Pass",
                    "Parameters": {
                        "statusCode": 200,
                        "session_id.$": "$.original_request.session_id",
                        "action.$": "$.original_request.action",
                        "status": "success",
                        "results.$": "$.agent_response.results",
                        "response.$": "$.agent_response.response",
                        "timestamp.$": "$$.State.EnteredTime"
                    },
                    "OutputPath": "$",
                    "End": True
                },
                
                "InvalidAction": {
                    "Type": "Pass",
                    "Parameters": {
                        "statusCode": 400,
                        "error.$": "States.Format('Invalid action: {}', $.action)",
                        "session_id.$": "$.session_id"
                    },
                    "End": True
                },
                
                "HandleError": {
                    "Type": "Pass",
                    "Parameters": {
                        "statusCode": 500,
                        "error.$": "$.error.Cause",
                        "session_id.$": "$.original_request.session_id",
                        "action.$": "$.original_request.action",
                        "status": "error"
                    },
                    "End": True
                }
            }
        }
        
        # Create the state machine
        state_machine = sfn.StateMachine(
            self, "AgentCoreBrowserWrapper",
            state_machine_name=f"AgentCoreBrowserWrapper-{self.stack_name}",
            definition_body=sfn.DefinitionBody.from_string(
                json.dumps(state_machine_definition)
            ),
            role=state_machine_role,
            logs=sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            ),
            tracing_enabled=True,
            timeout=Duration.minutes(5)
        )
        
        # Output the state machine ARN
        CfnOutput(
            self, "StateMachineArn",
            value=state_machine.state_machine_arn,
            description="ARN of the Agent Core Browser Wrapper State Machine"
        )
        
        # Output for integration with supervisor
        CfnOutput(
            self, "ToolIntegration",
            value=json.dumps({
                "tool_name": "agentcore-browser",
                "state_machine_arn": state_machine.state_machine_arn,
                "input_format": {
                    "action": "search|extract|authenticate",
                    "session_id": "string",
                    "url": "string",
                    "query": "string (for search)",
                    "selectors": "object (for extract)",
                    "credentials": "object (for authenticate)",
                    "config": "object (optional)"
                },
                "output_format": {
                    "statusCode": "number",
                    "session_id": "string",
                    "action": "string",
                    "status": "success|error",
                    "results": "object (from agent)",
                    "response": "string (from agent)",
                    "error": "string (if failed)"
                }
            }),
            description="Integration details for supervisor state machine"
        )