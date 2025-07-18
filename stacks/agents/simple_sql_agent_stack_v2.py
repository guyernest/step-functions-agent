from aws_cdk import (
    Duration,
    Stack,
    Fn,
    aws_logs as logs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from ..shared.naming_conventions import NamingConventions
import json


class SimpleSQLAgentStackV2(Stack):
    """
    Simple SQL Agent Stack V2 - Using raw Step Functions definition
    
    This stack demonstrates:
    - References shared LLM Lambda functions
    - Uses raw Step Functions definition with JSONata
    - Minimal complexity for testing
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        
        # Import shared resources
        self._import_shared_resources()
        
        # Create agent-specific resources
        self._create_agent_resources()
        
        # Create Step Functions workflow
        self._create_step_functions_workflow()

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""
        
        # Import shared LLM Lambda function ARN
        self.claude_lambda_arn = Fn.import_value(f"SharedClaudeLambdaArn-{self.env_name}")
        
        # Import shared log group ARN
        self.shared_log_group_arn = Fn.import_value(f"SharedLLMLogGroupArn-{self.env_name}")

    def _create_agent_resources(self):
        """Create agent-specific resources"""
        
        # Use the shared log group from SharedLLMStack
        self.log_group = logs.LogGroup.from_log_group_arn(
            self,
            "SharedLogGroup",
            log_group_arn=self.shared_log_group_arn
        )
        
        # Create agent execution role
        self.agent_execution_role = self._create_agent_execution_role()

    def _create_agent_execution_role(self):
        """Create IAM role for Step Functions execution"""
        
        role = iam.Role(
            self,
            "SimpleSQLAgentExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )
        
        # Grant basic Step Functions permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                resources=[
                    f"{self.shared_log_group_arn}:*"
                ]
            )
        )
        
        # Grant access to Lambda functions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    self.claude_lambda_arn,
                    # db-interface Lambda ARN
                    NamingConventions.tool_lambda_arn(
                        "db-interface",
                        self.region,
                        self.account,
                        self.env_name
                    )
                ]
            )
        )
        
        # Grant X-Ray permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )
        
        return role

    def _create_step_functions_workflow(self):
        """Create Step Functions workflow using raw definition"""
        
        # Create the state machine definition with JSONata
        definition = {
            "Comment": "Simple SQL Agent with Shared LLM",
            "QueryLanguage": "JSONata",
            "StartAt": "Call LLM",
            "States": {
                "Call LLM": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Arguments": {
                        "FunctionName": self.claude_lambda_arn,
                        "Payload": {
                            "system": "You are a helpful SQL assistant with access to a SQLite database. Help users query and understand their data.",
                            "messages": "{% $states.input.messages %}",
                            "tools": [
                                {
                                    "name": "get_db_schema",
                                    "description": "Describe the schema of the SQLite database, including table names, and column names and types.",
                                    "input_schema": {
                                        "type": "object",
                                        "properties": {}
                                    }
                                },
                                {
                                    "name": "execute_sql_query",
                                    "description": "Return the query results of any valid sqlite SQL query. If the SQL query result has many rows then return only the first 5 rows.",
                                    "input_schema": {
                                        "type": "object",
                                        "properties": {
                                            "sql_query": {
                                                "type": "string",
                                                "description": "The sql query to execute. If the SQL query result has many rows then return only the first 5 rows."
                                            }
                                        },
                                        "required": ["sql_query"]
                                    }
                                }
                            ]
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
                    "Next": "Is done?",
                    "Output": {
                        "messages": "{% $append($states.input.messages, $states.result.Payload.body.message) %}",
                        "llm_response": "{% $states.result %}"
                    }
                },
                "Is done?": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Condition": "{% $exists($states.input.llm_response.Payload.body.function_calls[0]) %}",
                            "Next": "Execute Tool"
                        }
                    ],
                    "Default": "Done"
                },
                "Execute Tool": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Arguments": {
                        "FunctionName": NamingConventions.tool_lambda_arn(
                            "db-interface",
                            self.region,
                            self.account,
                            self.env_name
                        ),
                        "Payload": "{% $states.input.llm_response.Payload.body.function_calls[0] %}"
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
                    "Next": "Call LLM",
                    "Output": {
                        "messages": "{% $append($states.input.messages, $states.result.Payload) %}"
                    }
                },
                "Done": {
                    "Type": "Succeed",
                    "Comment": "Agent workflow completed"
                }
            }
        }
        
        # Create the state machine using raw definition
        self.state_machine = sfn.StateMachine(
            self,
            "SimpleSQLAgentStateMachine",
            state_machine_name=f"simple-sql-agent-v2-fixed-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )