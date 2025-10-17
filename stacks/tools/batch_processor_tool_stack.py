"""
CDK Stack for Generic Batch Processor Tool
A Step Functions state machine that processes CSV files through agents with structured output
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_ssm as ssm,
    aws_sns as sns,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Fn
)
from constructs import Construct
from .base_tool_construct_batched import BatchedToolConstruct
import json
from pathlib import Path


class BatchProcessorToolStack(Stack):
    """
    Generic Batch Processor Tool - Step Functions for processing CSV files with structured output agents
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        env = kwargs.get('env')
        self.aws_account_id = env.account if env and hasattr(env, 'account') else '672915487120'
        self.aws_region = env.region if env and hasattr(env, 'region') else 'eu-west-1'

        # Import shared resources
        self._import_shared_resources()

        # Create S3 bucket for batch results
        self.results_bucket = s3.Bucket(
            self, "BatchProcessorResults",
            bucket_name=f"batch-processor-results-{env_name}-{self.aws_account_id}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldResults",
                    expiration=Duration.days(30)
                )
            ],
            versioned=True  # Enable versioning for data safety
        )

        # Create SNS topic for batch completion notifications
        self.notification_topic = sns.Topic(
            self, "BatchCompletionNotifications",
            topic_name=f"batch-processor-notifications-{env_name}",
            display_name="Batch Processor Completion Notifications",
            fifo=False
        )

        # Create SSM parameter for the results bucket name
        self.results_bucket_param = ssm.StringParameter(
            self, "ResultsBucketParameter",
            parameter_name="/ai-agent/batch-processor-results-bucket",
            string_value=self.results_bucket.bucket_name,
            description="S3 bucket name for batch processor results"
        )

        # Create Lambda functions for the batch processor
        self._create_lambda_functions()

        # Create the Step Functions state machine
        self._create_state_machine()

        # Register as a Step Functions tool in the registry
        self._register_tool_in_registry()

        # Outputs
        CfnOutput(self, "StateMachineArn",
                 value=self.state_machine.state_machine_arn,
                 export_name=f"BatchProcessorStateMachineArn-{env_name}",
                 description="ARN of the generic batch processor")

        CfnOutput(self, "ResultsBucket",
                 value=self.results_bucket.bucket_name,
                 export_name=f"BatchProcessorResultsBucket-{env_name}",
                 description="S3 bucket for batch processing results")

        CfnOutput(self, "NotificationTopicArn",
                 value=self.notification_topic.topic_arn,
                 export_name=f"BatchProcessorNotificationTopicArn-{env_name}",
                 description="SNS topic ARN for batch completion notifications")

        CfnOutput(self, "NotificationTopicName",
                 value=self.notification_topic.topic_name,
                 export_name=f"BatchProcessorNotificationTopicName-{env_name}",
                 description="SNS topic name for batch completion notifications")

    def _import_shared_resources(self):
        """Import shared resources from other stacks"""

        # Import agent registry for looking up agents
        self.agent_registry_table_name = Fn.import_value(
            f"SharedTableAgentRegistry-{self.env_name}"
        )
        self.agent_registry_table_arn = Fn.import_value(
            f"SharedTableArnAgentRegistry-{self.env_name}"
        )

        # Import tool registry for looking up tools
        self.tool_registry_table_name = Fn.import_value(
            f"SharedTableToolRegistry-{self.env_name}"
        )
        self.tool_registry_table_arn = Fn.import_value(
            f"SharedTableArnToolRegistry-{self.env_name}"
        )

    def _create_lambda_functions(self):
        """Create the Lambda functions used by the state machine"""

        # Base path for batch processor Lambda functions
        batch_processor_path = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'batch_processor'

        # Common Lambda environment
        lambda_env = {
            "RESULTS_BUCKET": self.results_bucket.bucket_name,
            "AGENT_REGISTRY_TABLE": self.agent_registry_table_name,
            "TOOL_REGISTRY_TABLE": self.tool_registry_table_name,
            "ENVIRONMENT": self.env_name
        }

        # 1. Input Mapper Lambda - Transforms CSV rows to agent input
        self.input_mapper = lambda_.Function(
            self, "InputMapper",
            function_name=f"batch-processor-input-mapper-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="input_mapper.lambda_handler",
            code=lambda_.Code.from_asset(str(batch_processor_path)),
            environment=lambda_env,
            timeout=Duration.seconds(60),
            memory_size=512,
            description="Maps CSV rows to agent input format"
        )

        # 2. Output Mapper Lambda - Transforms agent output to CSV columns
        self.output_mapper = lambda_.Function(
            self, "OutputMapper",
            function_name=f"batch-processor-output-mapper-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="output_mapper.lambda_handler",
            code=lambda_.Code.from_asset(str(batch_processor_path)),
            environment=lambda_env,
            timeout=Duration.seconds(60),
            memory_size=512,
            description="Maps agent structured output to CSV columns"
        )

        # 3. Result Aggregator Lambda - Combines results into final CSV
        self.result_aggregator = lambda_.Function(
            self, "ResultAggregator",
            function_name=f"batch-processor-result-aggregator-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="result_aggregator.lambda_handler",
            code=lambda_.Code.from_asset(str(batch_processor_path)),
            environment=lambda_env,
            timeout=Duration.minutes(5),
            memory_size=1024,
            description="Aggregates processed results into final CSV"
        )

        # Grant S3 permissions
        self.results_bucket.grant_read_write(self.input_mapper)
        self.results_bucket.grant_read_write(self.output_mapper)
        self.results_bucket.grant_read_write(self.result_aggregator)

        # Grant DynamoDB permissions for registry access
        for lambda_fn in [self.input_mapper, self.output_mapper]:
            lambda_fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["dynamodb:GetItem", "dynamodb:Query"],
                    resources=[
                        self.agent_registry_table_arn,
                        self.tool_registry_table_arn
                    ]
                )
            )

        # Grant SSM parameter read permission to result aggregator
        self.result_aggregator.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[self.results_bucket_param.parameter_arn]
            )
        )

    def _create_state_machine(self):
        """Create the Step Functions state machine for batch processing using JSONata"""

        # Load JSONata state machine definition from file
        jsonata_def_path = Path(__file__).parent / 'batch_processor_state_machine_jsonata.json'
        with open(jsonata_def_path, 'r') as f:
            definition = json.load(f)

        # Replace placeholders with actual ARNs
        definition_str = json.dumps(definition)
        definition_str = definition_str.replace(
            'FUNCTION_ARN_PLACEHOLDER_INPUT_MAPPER',
            self.input_mapper.function_arn
        )
        definition_str = definition_str.replace(
            'FUNCTION_ARN_PLACEHOLDER_OUTPUT_MAPPER',
            self.output_mapper.function_arn
        )
        definition_str = definition_str.replace(
            'FUNCTION_ARN_PLACEHOLDER_RESULT_AGGREGATOR',
            self.result_aggregator.function_arn
        )
        definition_str = definition_str.replace(
            'TOPIC_ARN_PLACEHOLDER',
            self.notification_topic.topic_arn
        )

        # Parse back to dict for validation
        definition = json.loads(definition_str)

        # Create execution role
        self.execution_role = iam.Role(
            self, "StateMachineRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "ExecutionPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "lambda:InvokeFunction"
                            ],
                            resources=[
                                self.input_mapper.function_arn,
                                self.output_mapper.function_arn,
                                self.result_aggregator.function_arn
                            ]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                f"{self.results_bucket.bucket_arn}/*",
                                self.results_bucket.bucket_arn,
                                "arn:aws:s3:::*"  # For reading input CSVs
                            ]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "states:StartExecution",
                                "states:DescribeExecution",
                                "states:StopExecution"
                            ],
                            resources=["*"]  # Will be restricted to specific agents
                        ),
                        # Permissions for synchronous execution (managed rules)
                        iam.PolicyStatement(
                            actions=[
                                "events:PutTargets",
                                "events:PutRule",
                                "events:DescribeRule"
                            ],
                            resources=["*"]  # Broad permission for managed rules
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:Query"
                            ],
                            resources=[
                                self.agent_registry_table_arn,
                                self.tool_registry_table_arn
                            ]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "sns:Publish"
                            ],
                            resources=[
                                self.notification_topic.topic_arn
                            ]
                        )
                    ]
                )
            }
        )

        # Create state machine using JSONata query language
        # The QueryLanguage is specified in the definition itself
        self.state_machine = sfn.StateMachine(
            self, "BatchProcessorStateMachine",
            state_machine_name=f"batch-processor-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(definition_str),
            role=self.execution_role,
            state_machine_type=sfn.StateMachineType.STANDARD
        )

        self.state_machine_arn = self.state_machine.state_machine_arn

    def _register_tool_in_registry(self):
        """Register the batch processor as a Step Functions tool"""

        tool_spec = {
            "tool_name": "batch_processor",
            "description": "Process CSV files through agents with structured output",
            "input_schema": {
                "type": "object",
                "properties": {
                    "csv_s3_uri": {
                        "type": "string",
                        "description": "S3 URI of input CSV file"
                    },
                    "target": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["agent", "tool"]},
                            "name": {"type": "string"},
                            "arn": {"type": "string"}
                        },
                        "required": ["type", "name"]
                    },
                    "input_mapping": {
                        "type": "object",
                        "description": "How to map CSV columns to agent input"
                    },
                    "output_mapping": {
                        "type": "object",
                        "description": "How to map structured output to CSV columns"
                    },
                    "execution_config": {
                        "type": "object",
                        "properties": {
                            "max_concurrency": {"type": "integer", "default": 10},
                            "timeout_seconds": {"type": "integer", "default": 300}
                        }
                    },
                    "notification_config": {
                        "type": "object",
                        "description": "Configuration for SNS notifications on completion",
                        "properties": {
                            "batch_name": {
                                "type": "string",
                                "description": "Identifier for this batch (used for SNS message filtering)"
                            },
                            "include_details": {
                                "type": "boolean",
                                "default": True,
                                "description": "Whether to include detailed statistics in notification"
                            }
                        },
                        "required": ["batch_name"]
                    }
                },
                "required": ["csv_s3_uri", "target"]
            },
            "tool_type": "step_functions",
            "resource_arn": self.state_machine_arn,
            "requires_activity": False,
            "human_approval_required": False,
            "tags": ["batch", "csv", "structured-output"],
            "author": "system"
        }

        # Register using BatchedToolConstruct
        BatchedToolConstruct(
            self,
            "BatchProcessorToolRegistry",
            tool_specs=[tool_spec],
            lambda_function=None,  # Step Functions tool, no Lambda
            env_name=self.env_name
        )