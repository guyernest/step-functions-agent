"""
CDK Stack for Address Search Batch Tool
Creates a Step Functions state machine for batch processing UK addresses
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput,
    Duration,
    RemovalPolicy
)
from constructs import Construct
from .base_tool_construct_batched import BatchedToolConstruct
import json
import os
from pathlib import Path


class AddressSearchBatchToolStack(Stack):
    """
    Address Search Batch Tool - Step Functions state machine for batch processing
    """
    
    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = env_name
        env = kwargs.get('env')
        self.aws_account_id = env.account if env and hasattr(env, 'account') else '672915487120'
        self.aws_region = env.region if env and hasattr(env, 'region') else 'eu-west-1'
        
        # Load configuration
        config_path = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'address-search-batch' / 'config.json'
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Create S3 bucket for batch results
        self.results_bucket = s3.Bucket(
            self, "AddressSearchBatchResults",
            bucket_name=f"address-search-batch-results-{env_name}-{self.aws_account_id}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldResults",
                    expiration=Duration.days(30)
                )
            ]
        )
        
        # Create Lambda functions for the batch processor
        self._create_lambda_functions()
        
        # Create the Step Functions state machine
        self._create_state_machine()
        
        # Register as a Step Functions tool in the registry
        self._register_tool_in_registry()
        
        # Outputs
        CfnOutput(self, "StateMachineArn",
                 value=self.state_machine_arn,
                 description="ARN of the address search batch processor")
        
        CfnOutput(self, "ResultsBucket",
                 value=self.results_bucket.bucket_name,
                 description="S3 bucket for batch processing results")
    
    def _create_lambda_functions(self):
        """Create the Lambda functions used by the state machine"""

        # Base path for batch processor Lambda functions
        batch_processor_path = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'batch_processor'
        address_search_path = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'address-search-batch'

        # State machine invoker Lambda (wrapper for tool invocation)
        self.invoker_lambda = lambda_.Function(
            self, "StateMachineInvokerLambda",
            function_name=f"address-search-batch-invoker-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset(str(address_search_path)),
            handler="state_machine_invoker.lambda_handler",
            timeout=Duration.minutes(15),  # Max Lambda timeout
            memory_size=256,
            environment={
                "ENV_NAME": self.env_name
            },
            description="Invoker for address search batch state machine"
        )

        # Address mapper function (specialized for address searches)
        self.address_mapper_lambda = lambda_.Function(
            self, "AddressMapperLambda",
            function_name=f"address-search-mapper-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset(str(address_search_path)),
            handler="address_mapper.lambda_handler",
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "ENV_NAME": self.env_name
            },
            description="Maps address CSV rows to/from web search agent format"
        )
        
        # Reuse generic output mapper from batch processor
        self.output_mapper_lambda = lambda_.Function(
            self, "OutputMapperLambda",
            function_name=f"address-search-output-mapper-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset(str(batch_processor_path)),
            handler="output_mapper.lambda_handler",
            timeout=Duration.seconds(60),
            memory_size=256,
            description="Maps agent outputs to CSV format"
        )
        
        # CSV Loader Lambda
        self.csv_loader_lambda = lambda_.Function(
            self, "CSVLoaderLambda",
            function_name=f"address-search-csv-loader-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset(str(batch_processor_path)),
            handler="csv_loader.lambda_handler",
            timeout=Duration.seconds(60),
            memory_size=256,
            description="Loads CSV from S3 for batch processing"
        )

        # JSON to CSV converter
        self.json_to_csv_lambda = lambda_.Function(
            self, "JsonToCsvLambda",
            function_name=f"address-search-json-to-csv-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset(str(batch_processor_path)),
            handler="json_to_csv.lambda_handler",
            timeout=Duration.seconds(120),
            memory_size=512,
            environment={
                "ENV_NAME": self.env_name
            },
            description="Converts JSON results to CSV"
        )
        
        # Grant S3 permissions
        self.results_bucket.grant_read_write(self.invoker_lambda)
        self.results_bucket.grant_read_write(self.csv_loader_lambda)
        self.results_bucket.grant_read_write(self.address_mapper_lambda)
        self.results_bucket.grant_read_write(self.output_mapper_lambda)
        self.results_bucket.grant_read_write(self.json_to_csv_lambda)

        # Grant read permission to CSV loader for any bucket (for input CSVs)
        self.csv_loader_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=["arn:aws:s3:::*/*"]
            )
        )
    
    def _create_state_machine(self):
        """Create the Step Functions state machine for batch processing"""
        
        # Get the target agent ARN from config
        target_agent_arn = self.config['target_agent']['arn_pattern'].format(
            region=self.aws_region,
            account=self.aws_account_id,
            env=self.env_name
        )
        
        # Read the state machine definition template (using INLINE version)
        batch_processor_path = Path(__file__).parent.parent.parent / 'lambda' / 'tools' / 'batch_processor'
        with open(batch_processor_path / 'state_machine_inline.json', 'r') as f:
            definition_template = f.read()

        # Substitute Lambda ARNs and configuration
        definition = definition_template.replace('${CSVLoaderFunctionArn}', self.csv_loader_lambda.function_arn)
        definition = definition.replace('${InputMapperFunctionArn}', self.address_mapper_lambda.function_arn)
        definition = definition.replace('${OutputMapperFunctionArn}', self.output_mapper_lambda.function_arn)
        definition = definition.replace('${JsonToCsvFunctionArn}', self.json_to_csv_lambda.function_arn)
        
        # Parse the definition
        definition_json = json.loads(definition)
        
        # Create IAM role for the state machine
        state_machine_role = iam.Role(
            self, "StateMachineRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description=f"Role for address search batch processor state machine {self.env_name}"
        )

        # Add permissions for Distributed Map
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "states:StartExecution",
                    "states:DescribeExecution",
                    "states:StopExecution"
                ],
                resources=["*"]  # Distributed Map needs broad permissions for child executions
            )
        )

        # Add permissions for EventBridge rules (needed for Distributed Map)
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "events:PutTargets",
                    "events:PutRule",
                    "events:DescribeRule"
                ],
                resources=[
                    f"arn:aws:events:{self.aws_region}:{self.aws_account_id}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule"
                ]
            )
        )

        # Add IAM PassRole permission for managed rules
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[state_machine_role.role_arn]
            )
        )
        
        # Grant permissions to invoke Lambda functions
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[
                    self.csv_loader_lambda.function_arn,
                    self.address_mapper_lambda.function_arn,
                    self.output_mapper_lambda.function_arn,
                    self.json_to_csv_lambda.function_arn
                ]
            )
        )
        
        # Grant permissions to invoke the target agent
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[target_agent_arn]
            )
        )
        
        # Grant S3 permissions for CSV input/output
        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject"
                ],
                resources=[
                    f"arn:aws:s3:::*",  # Allow reading from any bucket (for input CSVs)
                    f"arn:aws:s3:::*/*",
                    self.results_bucket.bucket_arn,
                    f"{self.results_bucket.bucket_arn}/*"
                ]
            )
        )
        
        # Create the state machine
        self.state_machine = sfn.CfnStateMachine(
            self, "AddressSearchBatchStateMachine",
            state_machine_name=f"address-search-batch-{self.env_name}",
            role_arn=state_machine_role.role_arn,
            definition_string=json.dumps(definition_json),
            state_machine_type="STANDARD"
        )
        
        # Store ARN for tool registration
        # Use the ref attribute which returns the ARN for CfnStateMachine
        self.state_machine_arn = self.state_machine.ref

        # Grant the invoker Lambda permission to start executions
        self.invoker_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[self.state_machine_arn]
            )
        )

        # Grant permission to describe executions (needs execution ARN pattern)
        self.invoker_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["states:DescribeExecution"],
                resources=[f"arn:aws:states:{self.aws_region}:{self.aws_account_id}:execution:address-search-batch-{self.env_name}:*"]
            )
        )

        # Add state machine ARN to invoker Lambda environment
        self.invoker_lambda.add_environment("STATE_MACHINE_ARN", self.state_machine_arn)
    
    def _register_tool_in_registry(self):
        """Register the state machine as a tool in DynamoDB"""
        
        tool_spec = {
            "tool_name": self.config['tool_name'],
            "description": self.config['description'],
            "input_schema": self.config['input_schema'],
            "language": "python",  # Back to python since we're using a Lambda wrapper
            "tags": self.config['tags'],
            "author": "system",
            "human_approval_required": False,
            "tool_type": "lambda",  # Back to lambda type since we're using the wrapper
            "resource_arn": self.invoker_lambda.function_arn,  # Invoker Lambda ARN
            "lambda_arn": self.invoker_lambda.function_arn,  # For compatibility
            "config": {
                "target_agent": self.config['target_agent']['name'],
                "default_mappings": self.config['default_mappings'],
                "execution_defaults": self.config['execution_defaults'],
                "results_bucket": self.results_bucket.bucket_name
            }
        }
        
        # Register using BatchedToolConstruct
        BatchedToolConstruct(
            self, "AddressSearchBatchToolRegistry",
            tool_specs=[tool_spec],
            lambda_function=self.invoker_lambda  # Use the invoker Lambda
        )
        
        print(f"✅ Registered address_search_batch as a Step Functions tool")
        print(f"   State Machine ARN: {self.state_machine_arn}")
        print(f"   Results Bucket: {self.results_bucket.bucket_name}")