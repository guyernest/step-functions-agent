"""
Shared infrastructure stack for structured output support.
Provides Lambda functions and layers used by all structured output agents.
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct
import os


class StructuredOutputInfrastructureStack(Stack):
    """
    Shared infrastructure for structured output functionality.
    Creates Lambda functions that are reused across all agents with structured output.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_registry_table: dynamodb.Table,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.agent_registry_table = agent_registry_table

        # Create Lambda layer for jsonschema
        self.jsonschema_layer = self._create_jsonschema_layer()

        # Create PrepareAgentContext Lambda
        self.prepare_agent_context_fn = self._create_prepare_context_lambda()

        # Create ValidateStructuredOutput Lambda
        self.validate_structured_output_fn = self._create_validate_output_lambda()

        # Create ExecuteTool Lambda (placeholder for tool execution)
        self.execute_tool_fn = self._create_execute_tool_lambda()

        # Create CallLLM Lambda (placeholder - would integrate with Bedrock)
        self.call_llm_fn = self._create_call_llm_lambda()

        # Export Lambda ARNs for use by other stacks
        # Get env_name from stack name (format: StructuredOutputInfrastructureStack-{env_name})
        env_name = self.stack_name.split('-')[-1] if '-' in self.stack_name else 'prod'

        CfnOutput(
            self, "PrepareAgentContextArn",
            value=self.prepare_agent_context_fn.function_arn,
            export_name=f"PrepareAgentContextLambdaArn-{env_name}",
            description="ARN of the PrepareAgentContext Lambda function"
        )

        CfnOutput(
            self, "ValidateStructuredOutputArn",
            value=self.validate_structured_output_fn.function_arn,
            export_name=f"ValidateStructuredOutputLambdaArn-{env_name}",
            description="ARN of the ValidateStructuredOutput Lambda function"
        )

    def _create_jsonschema_layer(self) -> lambda_.LayerVersion:
        """Create a Lambda layer with jsonschema library."""

        return lambda_python.PythonLayerVersion(
            self, "JsonSchemaLayer",
            entry="lambda/layers/jsonschema",
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_12
            ],
            description="Layer containing jsonschema library for validation",
            layer_version_name="structured-output-jsonschema"
        )

    def _create_prepare_context_lambda(self) -> lambda_.Function:
        """Create the PrepareAgentContext Lambda function."""

        function = lambda_.Function(
            self, "PrepareAgentContextFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda/core/prepare_agent_context"),
            environment={
                "AGENT_REGISTRY_TABLE": self.agent_registry_table.table_name,
                "LOG_LEVEL": "INFO"
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Prepares agent context with structured output tools"
        )

        # Grant read access to agent registry
        self.agent_registry_table.grant_read_data(function)

        return function

    def _create_validate_output_lambda(self) -> lambda_.Function:
        """Create the ValidateStructuredOutput Lambda function."""

        function = lambda_.Function(
            self, "ValidateStructuredOutputFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda/core/validate_structured_output"),
            layers=[self.jsonschema_layer],
            environment={
                "LOG_LEVEL": "INFO"
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Validates structured output against JSON schemas"
        )

        return function

    def _create_execute_tool_lambda(self) -> lambda_.Function:
        """Create the ExecuteTool Lambda function (placeholder)."""

        function = lambda_.Function(
            self, "ExecuteToolFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_inline("""
import json

def lambda_handler(event, context):
    '''Placeholder for tool execution.'''
    tool_name = event.get('tool_name')
    arguments = event.get('arguments', {})

    # In real implementation, this would route to actual tool implementations
    return {
        'tool_name': tool_name,
        'result': f"Executed {tool_name} with args: {arguments}",
        'success': True
    }
            """),
            timeout=Duration.seconds(300),
            memory_size=512,
            description="Executes tools called by agents"
        )

        return function

    def _create_call_llm_lambda(self) -> lambda_.Function:
        """Create the CallLLM Lambda function (placeholder for Bedrock integration)."""

        function = lambda_.Function(
            self, "CallLLMFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_inline("""
import json
import os

def lambda_handler(event, context):
    '''Placeholder for LLM calls - would integrate with Bedrock.'''

    messages = event.get('messages', [])
    tools = event.get('tools', [])
    system = event.get('system', '')

    # Check if this is an enforcement call
    if any(tool.get('function', {}).get('name') == 'return_broadband_data' for tool in tools):
        # Simulate structured output response
        return {
            'messages': messages + [
                {'role': 'assistant', 'content': 'Extracting broadband data...'}
            ],
            'tool_calls': [{
                'name': 'return_broadband_data',
                'arguments': {
                    'exchange_station': 'Westminster Exchange',
                    'download_speed': 150.0,
                    'upload_speed': 30.0,
                    'screenshot_url': 'https://example.com/screenshot.png'
                }
            }]
        }

    # Default response
    return {
        'messages': messages + [
            {'role': 'assistant', 'content': 'I can help you check broadband availability.'}
        ],
        'tool_calls': []
    }
            """),
            environment={
                "BEDROCK_MODEL": "claude-3-sonnet-20240229",
                "LOG_LEVEL": "INFO"
            },
            timeout=Duration.seconds(300),
            memory_size=1024,
            description="Calls LLM models via Bedrock"
        )

        # Add Bedrock permissions
        function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        return function