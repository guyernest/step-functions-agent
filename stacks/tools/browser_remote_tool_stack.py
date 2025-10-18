"""
CDK Stack for Browser Remote Tool

Creates a Step Functions Activity for remote browser automation.
The Activity is polled by a local agent running on the user's desktop,
which executes Nova Act commands in a real browser environment.

This avoids bot detection by running in the user's actual browser with
their cookies, extensions, and authentic environment.
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_s3 as s3,
    CfnOutput,
    Duration,
    RemovalPolicy,
)
from constructs import Construct
from .base_tool_construct import BaseToolConstruct


class BrowserRemoteToolStack(Stack):
    """
    Browser Remote Tool - Activity-based browser automation

    This stack creates:
    1. Step Functions Activity ARN for local agent polling
    2. Lambda tool that returns the Activity ARN
    3. S3 bucket for browser session recordings
    4. Tool registration in DynamoDB
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

        # Create S3 bucket for browser session recordings
        self.recordings_bucket = s3.Bucket(
            self, "BrowserRecordingsBucket",
            bucket_name=f"browser-agent-recordings-{env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldRecordings",
                    enabled=True,
                    expiration=Duration.days(90)  # Auto-delete after 90 days
                )
            ]
        )

        # Create Step Functions Activity for browser automation
        self.browser_activity = sfn.Activity(
            self, "BrowserRemoteActivity",
            activity_name=f"browser-remote-{env_name}"
        )

        # Create passthrough Lambda that returns Activity ARN
        # This Lambda is registered as a tool but doesn't execute browser automation
        self.browser_remote_lambda = lambda_.Function(
            self, "BrowserRemoteLambda",
            function_name=f"browser-remote-tool-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json

def handler(event, context):
    '''
    Browser Remote Tool - Returns Activity ARN for local agent polling

    This is a passthrough tool that tells Step Functions to use an Activity
    instead of executing browser automation in Lambda.
    '''

    # Extract tool input
    tool_input = event.get('input', {})

    # Return activity configuration
    return {
        "success": True,
        "activity_arn": context.invoked_function_arn.replace(
            ':lambda:function:', ':states:activity:'
        ).replace(
            f'browser-remote-tool-{env_name}',
            f'browser-remote-{env_name}'
        ),
        "s3_bucket": context.invoked_function_arn.split(':')[4],
        "tool_input": tool_input,
        "message": "Browser remote task posted to Activity. Local agent will execute.",
    }
"""),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "ACTIVITY_ARN": self.browser_activity.activity_arn,
                "S3_BUCKET": self.recordings_bucket.bucket_name,
                "ENV_NAME": env_name,
            },
            description=f"Browser remote tool passthrough for {env_name}"
        )

        # Grant Lambda permission to describe the activity (for validation)
        self.browser_remote_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["states:DescribeActivity"],
                resources=[self.browser_activity.activity_arn]
            )
        )

        # Store references
        self.function_name = self.browser_remote_lambda.function_name
        self.function_arn = self.browser_remote_lambda.function_arn
        self.activity_arn = self.browser_activity.activity_arn

        # Register tool in DynamoDB using BaseToolConstruct
        self._register_tool_in_registry()

        # Outputs
        CfnOutput(
            self, "ActivityArn",
            value=self.browser_activity.activity_arn,
            description=f"Browser Remote Activity ARN for {env_name}",
            export_name=f"BrowserRemoteActivityArn-{env_name}"
        )

        CfnOutput(
            self, "LambdaFunctionArn",
            value=self.browser_remote_lambda.function_arn,
            description=f"Browser Remote Lambda ARN for {env_name}",
            export_name=f"BrowserRemoteLambdaArn-{env_name}"
        )

        CfnOutput(
            self, "RecordingsBucketName",
            value=self.recordings_bucket.bucket_name,
            description=f"S3 bucket for browser recordings in {env_name}",
            export_name=f"BrowserRecordingsBucket-{env_name}"
        )

        CfnOutput(
            self, "LocalAgentInstructions",
            value=f"Configure local agent: activity_arn={self.browser_activity.activity_arn}, s3_bucket={self.recordings_bucket.bucket_name}",
            description="Instructions for local agent setup"
        )

    def _register_tool_in_registry(self):
        """Register browser_remote tool in DynamoDB tool registry"""

        # Define tool specification
        tool_spec = {
            "tool_name": "browser_remote",
            "description": "Execute browser automation on a remote machine using Nova Act. Supports two modes: (1) Template mode - use pre-built browser automation templates with variables for consistent execution, (2) Legacy mode - provide natural language prompts for ad-hoc automation. Template mode is preferred for schema-driven agents.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "Template ID from TemplateRegistry (e.g., 'broadband_availability_bt_wholesale'). Use this for schema-driven automation with pre-built templates."
                    },
                    "template_version": {
                        "type": "string",
                        "description": "Template version (default: '1.0.0'). Specifies which version of the template to use."
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to populate the template (e.g., {'building_number': '23', 'street': 'High Street', 'postcode': 'SW1A 1AA'}). Required when using template_id."
                    },
                    "prompt": {
                        "type": "string",
                        "description": "[LEGACY] Natural language instruction for browser automation (e.g., 'Navigate to BT broadband checker and search for address'). Use template_id instead when available."
                    },
                    "starting_page": {
                        "type": "string",
                        "description": "[LEGACY] Initial URL to navigate to (optional if continuing existing session or using template)"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to reuse existing browser session (optional, for session persistence)"
                    },
                    "user_data_dir": {
                        "type": "string",
                        "description": "Path to Chrome profile directory for authenticated sessions (optional, overrides template default)"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "Maximum number of browser steps to take (default: 30)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds for the entire operation (default: 300)"
                    },
                    "schema": {
                        "type": "object",
                        "description": "JSON schema for structured output extraction (optional, overrides template schema)"
                    },
                    "headless": {
                        "type": "boolean",
                        "description": "Run browser in headless mode (default: false, recommended false for bot detection avoidance)"
                    },
                    "record_video": {
                        "type": "boolean",
                        "description": "Record video of browser session (default: true)"
                    }
                },
                "oneOf": [
                    {
                        "required": ["template_id", "variables"],
                        "description": "Template mode - use pre-built automation template"
                    },
                    {
                        "required": ["prompt"],
                        "description": "Legacy mode - use natural language prompt"
                    }
                ]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "Whether the automation succeeded"
                    },
                    "response": {
                        "type": "string",
                        "description": "Text response from Nova Act"
                    },
                    "parsed_response": {
                        "description": "Structured data if schema was provided"
                    },
                    "matches_schema": {
                        "type": "boolean",
                        "description": "Whether response matched provided schema"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for reusing this browser session"
                    },
                    "recording_s3_uri": {
                        "type": "string",
                        "description": "S3 URI for session recordings and screenshots"
                    },
                    "error": {
                        "type": "string",
                        "description": "Error message if automation failed"
                    }
                }
            },
            "language": "python",
            "tags": ["browser", "automation", "remote", "nova-act", "activity", "bot-avoidance"],
            "author": "system",
            "human_approval_required": False,  # Activity pattern handles this differently
            "lambda_arn": self.browser_remote_lambda.function_arn,
            "lambda_function_name": self.browser_remote_lambda.function_name,
            "activity_arn": self.browser_activity.activity_arn,  # Additional metadata
            "execution_pattern": "activity",  # Mark as activity-based tool
        }

        # Use BaseToolConstruct for registration
        BaseToolConstruct(
            self,
            "BrowserRemoteToolRegistry",
            tool_specs=[tool_spec],  # Pass as list
            lambda_function=self.browser_remote_lambda,
            env_name=self.env_name
        )
