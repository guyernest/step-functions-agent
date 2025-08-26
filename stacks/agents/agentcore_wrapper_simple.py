"""
Simplified CDK Stack for Agent Core Wrapper
Uses Lambda to invoke Agent Core and maintains tool interface compatibility
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
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


class AgentCoreWrapperSimpleStack(Stack):
    """
    Simple wrapper for Agent Core using Lambda invocation
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get Agent Core runtime details from context
        agent_runtime_arn = self.node.try_get_context("agent_runtime_arn") or \
                           "arn:aws:bedrock-agentcore:us-west-2:672915487120:runtime/shopping_agent-aw6O6r7uk5"
        
        # Create Lambda function to invoke Agent Core
        agent_invoker = lambda_.Function(
            self, "AgentCoreInvoker",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_inline("""
import json
import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Bedrock Agent Core client
# Note: This assumes the bedrock-agentcore service is available
# In practice, might need to use custom SDK or HTTP calls

def handler(event, context):
    '''
    Lambda handler to invoke Agent Core and format response
    '''
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract action and parameters
        action = event.get('action', 'search')
        session_id = event.get('session_id', 'default')
        
        # Build prompt based on action
        if action == 'search':
            url = event.get('url', 'https://www.amazon.com')
            query = event.get('query', '')
            prompt = f"Search for {query} on {url}"
            
        elif action == 'extract':
            url = event.get('url', '')
            selectors = event.get('selectors', {})
            prompt = f"Extract data from {url} using selectors: {json.dumps(selectors)}"
            
        elif action == 'authenticate':
            url = event.get('url', '')
            prompt = f"Authenticate on {url} portal"
            
        else:
            return {
                'statusCode': 400,
                'error': f'Invalid action: {action}',
                'session_id': session_id
            }
        
        # Prepare Agent Core payload
        agent_payload = {
            'prompt': prompt,
            'test': False
        }
        
        # Invoke Agent Core (mock for now - replace with actual invocation)
        # In production, this would use the bedrock-agentcore SDK or HTTP API
        
        # Mock response for testing
        agent_response = {
            'status': True,
            'results': {
                'session_id': session_id,
                'prompt': prompt,
                'response': f'Mock results for: {prompt}'
            }
        }
        
        # Format response to match Lambda tool interface
        return {
            'statusCode': 200,
            'session_id': session_id,
            'action': action,
            'status': 'success',
            'results': agent_response.get('results', {}),
            'response': agent_response.get('results', {}).get('response', ''),
            'timestamp': context.aws_request_id
        }
        
    except Exception as e:
        logger.error(f"Error invoking Agent Core: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'session_id': event.get('session_id', 'default'),
            'action': event.get('action', 'unknown'),
            'status': 'error'
        }
"""),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "AGENT_RUNTIME_ARN": agent_runtime_arn,
                "AWS_REGION": self.region
            },
            description="Lambda function to invoke Agent Core and format responses"
        )
        
        # Grant permissions to invoke Agent Core
        agent_invoker.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:GetAgentRuntime"
                ],
                resources=["*"]
            )
        )
        
        # Create log group for state machine
        log_group = logs.LogGroup(
            self, "WrapperLogs",
            log_group_name=f"/aws/stepfunctions/agentcore-wrapper-{self.stack_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create Step Functions state machine
        invoke_task = tasks.LambdaInvoke(
            self, "InvokeAgentCore",
            lambda_function=agent_invoker,
            output_path="$.Payload",
            retry_on_service_exceptions=True
        )
        
        definition = invoke_task
        
        state_machine = sfn.StateMachine(
            self, "AgentCoreWrapper",
            state_machine_name=f"AgentCoreWrapper-{self.stack_name}",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            logs=sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            ),
            tracing_enabled=True,
            timeout=Duration.minutes(5)
        )
        
        # Outputs
        CfnOutput(
            self, "StateMachineArn",
            value=state_machine.state_machine_arn,
            description="ARN of the Agent Core Wrapper State Machine"
        )
        
        CfnOutput(
            self, "LambdaFunctionArn",
            value=agent_invoker.function_arn,
            description="ARN of the Lambda invoker function"
        )
        
        CfnOutput(
            self, "IntegrationConfig",
            value=json.dumps({
                "tool_name": "agentcore-browser",
                "type": "state_machine",
                "arn": state_machine.state_machine_arn,
                "description": "Browser automation using Agent Core"
            }),
            description="Configuration for supervisor integration"
        )