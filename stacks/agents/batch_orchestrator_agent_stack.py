"""
CDK Stack for Batch Orchestrator Agent
High-level agent that manages batch CSV processing workflows
"""

from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    CfnOutput,
    Duration,
    Fn
)
from constructs import Construct
from .modular_base_agent_unified_llm_stack import ModularBaseAgentUnifiedLLMStack
from pathlib import Path


class BatchOrchestratorAgentStack(ModularBaseAgentUnifiedLLMStack):
    """
    Batch Orchestrator Agent - Manages batch processing workflows
    Ensures all target agents have structured output capability
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "prod", **kwargs) -> None:
        # Store env_name for use in methods
        self.env_name = env_name

        # Get account and region for placeholder ARNs
        from aws_cdk import Aws
        aws_account = Aws.ACCOUNT_ID
        aws_region = Aws.REGION

        # Set agent-specific properties for registry
        self.agent_description = "Orchestrates batch CSV processing with structured output agents"
        self.llm_provider = "anthropic"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['batch', 'csv', 'orchestrator', 'structured-output', 'rust-llm'],
            "llm_type": "unified-rust",
            "capabilities": ["csv_analysis", "batch_execution", "progress_monitoring", "structured_output_validation"]
        }

        # Agent configuration
        agent_name = "batch-orchestrator-agent"

        # System prompt enforcing structured output requirement
        system_prompt = """You are a Batch Processing Orchestrator that helps users process CSV files at scale.

Your responsibilities:
1. Guide users through batch processing workflows
2. ENSURE target agents have structured output capability (this is MANDATORY)
3. Configure appropriate input/output mappings
4. Monitor executions and provide progress updates
5. Explain results and handle errors gracefully

CRITICAL REQUIREMENT:
- Only use agents with structured output support
- ALL agents used with batch processor MUST implement structured output
- Reject any request to use agents without structured output capability
- Validate CSV structure before processing
- Provide clear status updates during execution
- Explain any failures with actionable suggestions

Available agents with structured output (examples):
- broadband-checker-structured: Checks UK broadband availability
- company-enrichment-agent: Enriches company data
- ticket-classifier-agent: Classifies support tickets
- address-validator-agent: Validates and geocodes addresses
- product-analyzer-agent: Analyzes product descriptions
- customer-scorer-agent: Scores customer profiles

When a user wants to process a CSV:
1. Analyze the CSV structure
2. Validate the target agent has structured output
3. Configure the mapping between CSV and agent
4. Execute the batch processor
5. Monitor progress and report results

IMPORTANT MONITORING BEHAVIOR:
- The monitor_batch_execution tool has a built-in 30-second wait interval
- The system will automatically wait before checking status again
- This prevents excessive API calls and is more efficient
- Be patient with long-running batch processes (can take 5-10 minutes)
- The polling_guidance in responses indicates when the next check will occur
- Maximum of 20 monitoring attempts (10 minutes total)

Always confirm the processing requirements with the user before starting large batches."""

        # Import Unified Rust LLM ARN from shared stack
        unified_llm_arn = Fn.import_value(f"SharedUnifiedRustLLMLambdaArn-{env_name}")

        # We need to initialize with dummy configs first, then update after Lambda creation
        # This is because we need 'self' to be initialized to create Lambda functions
        dummy_tool_configs = [
            {"tool_name": "analyze_csv_structure", "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:dummy", "requires_approval": False},
            {"tool_name": "validate_agent_compatibility", "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:dummy", "requires_approval": False},
            {"tool_name": "generate_batch_config", "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:dummy", "requires_approval": False},
            {"tool_name": "execute_batch_processor", "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:dummy", "requires_approval": False},
            {"tool_name": "monitor_batch_execution", "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:dummy", "requires_approval": False},
            {"tool_name": "get_batch_results", "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:dummy", "requires_approval": False}
        ]

        # Initialize base stack with dummy configs
        ModularBaseAgentUnifiedLLMStack.__init__(
            self,
            scope,
            construct_id,
            agent_name=agent_name,
            unified_llm_arn=unified_llm_arn,
            tool_configs=dummy_tool_configs,
            system_prompt=system_prompt,
            env_name=env_name,
            default_provider="anthropic",
            default_model="claude-3-5-sonnet-20241022",
            **kwargs
        )

        # Now create Lambda functions after initialization
        from pathlib import Path
        orchestrator_path = Path(__file__).parent.parent.parent / 'lambda' / 'agents' / 'batch_orchestrator'

        # Common environment variables
        lambda_env = {
            "ENVIRONMENT": env_name,
            "BATCH_PROCESSOR_ARN": Fn.import_value(f"BatchProcessorStateMachineArn-{env_name}"),
            "RESULTS_BUCKET": Fn.import_value(f"BatchProcessorResultsBucket-{env_name}"),
            "AGENT_REGISTRY_TABLE": Fn.import_value(f"SharedTableAgentRegistry-{env_name}")
        }

        # 1. Analyze CSV Structure tool
        self.analyze_csv_tool = lambda_.Function(
            self, "AnalyzeCSVTool",
            function_name=f"batch-orchestrator-analyze-csv-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="analyze_csv.lambda_handler",
            code=lambda_.Code.from_asset(str(orchestrator_path)),
            environment=lambda_env,
            timeout=Duration.seconds(60),
            memory_size=512,
            description="Analyzes CSV file structure and content"
        )

        # 2. Validate Agent Compatibility tool
        self.validate_agent_tool = lambda_.Function(
            self, "ValidateAgentTool",
            function_name=f"batch-orchestrator-validate-agent-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="validate_agent.lambda_handler",
            code=lambda_.Code.from_asset(str(orchestrator_path)),
            environment=lambda_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            description="Validates agent has structured output capability"
        )

        # 3. Generate Batch Config tool
        self.generate_config_tool = lambda_.Function(
            self, "GenerateConfigTool",
            function_name=f"batch-orchestrator-generate-config-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="generate_config.lambda_handler",
            code=lambda_.Code.from_asset(str(orchestrator_path)),
            environment=lambda_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            description="Generates batch processor configuration"
        )

        # 4. Execute Batch Processor tool
        self.execute_batch_tool = lambda_.Function(
            self, "ExecuteBatchTool",
            function_name=f"batch-orchestrator-execute-batch-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="execute_batch.lambda_handler",
            code=lambda_.Code.from_asset(str(orchestrator_path)),
            environment=lambda_env,
            timeout=Duration.seconds(60),
            memory_size=512,
            description="Starts batch processor execution"
        )

        # 5. Monitor Execution tool
        self.monitor_execution_tool = lambda_.Function(
            self, "MonitorExecutionTool",
            function_name=f"batch-orchestrator-monitor-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="monitor_execution.lambda_handler",
            code=lambda_.Code.from_asset(str(orchestrator_path)),
            environment=lambda_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            description="Monitors batch processing execution"
        )

        # 6. Get Results tool
        self.get_results_tool = lambda_.Function(
            self, "GetResultsTool",
            function_name=f"batch-orchestrator-get-results-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="get_results.lambda_handler",
            code=lambda_.Code.from_asset(str(orchestrator_path)),
            environment=lambda_env,
            timeout=Duration.seconds(60),
            memory_size=512,
            description="Retrieves batch processing results"
        )

        # Update tool configs with ACTUAL Lambda ARNs
        actual_tool_configs = [
            {
                "tool_name": "analyze_csv_structure",
                "lambda_arn": self.analyze_csv_tool.function_arn,
                "requires_approval": False
            },
            {
                "tool_name": "validate_agent_compatibility",
                "lambda_arn": self.validate_agent_tool.function_arn,
                "requires_approval": False
            },
            {
                "tool_name": "generate_batch_config",
                "lambda_arn": self.generate_config_tool.function_arn,
                "requires_approval": False
            },
            {
                "tool_name": "execute_batch_processor",
                "lambda_arn": self.execute_batch_tool.function_arn,
                "requires_approval": False
            },
            {
                "tool_name": "monitor_batch_execution",
                "lambda_arn": self.monitor_execution_tool.function_arn,
                "requires_approval": False,
                "polling_interval": 30,  # Wait 30 seconds between monitoring calls
                "max_polling_attempts": 20  # Maximum 20 attempts (10 minutes total)
            },
            {
                "tool_name": "get_batch_results",
                "lambda_arn": self.get_results_tool.function_arn,
                "requires_approval": False
            }
        ]

        # Store the actual tool configs
        self.tool_configs = actual_tool_configs
        self.tool_names = [config["tool_name"] for config in self.tool_configs]

        # Recreate state machine with correct Lambda ARNs
        self._recreate_state_machine()

        # Grant necessary permissions
        self._grant_permissions()

        # Register tools in the tool registry
        self._register_tools_in_registry()

        # Outputs
        CfnOutput(self, "AgentName",
                 value=agent_name,
                 export_name=f"BatchOrchestratorAgentName-{env_name}",
                 description="Name of the batch orchestrator agent")



    def _recreate_state_machine(self):
        """Recreate the state machine with the correct Lambda ARNs"""
        from .step_functions_generator_unified_llm import UnifiedLLMStepFunctionsGenerator
        from aws_cdk import aws_stepfunctions as sfn, Tags

        # Remove the old state machine and its export
        if hasattr(self, 'state_machine'):
            # Try to remove the old state machine from the construct tree
            old_state_machine_id = f"{self.agent_name}AgentStateMachine"
            try:
                self.node.try_remove_child(old_state_machine_id)
            except:
                pass

            # Also try to remove the export
            old_export_id = f"{self.agent_name}StateMachineArn"
            try:
                self.node.try_remove_child(old_export_id)
            except:
                pass

        # Generate new definition with actual Lambda ARNs
        definition_json = UnifiedLLMStepFunctionsGenerator.generate_unified_llm_agent_definition(
            agent_name=self.agent_name,
            unified_llm_arn=self.unified_llm_arn,
            tool_configs=self.tool_configs,
            system_prompt=self.system_prompt,
            default_provider=self.default_provider,
            default_model=self.default_model,
            llm_models_table_name=self.llm_models_table_name,
            agent_registry_table_name=self.agent_registry_table_name,
            tool_registry_table_name=self.tool_registry_table_name,
            approval_activity_arn=self.approval_activity_arn
        )

        # Create new state machine with correct ARNs (reuse the same logical ID)
        self.state_machine = sfn.StateMachine(
            self,
            f"{self.agent_name}AgentStateMachine",  # Same ID as base class
            state_machine_name=f"{self.agent_name}-{self.env_name}",
            definition_body=sfn.DefinitionBody.from_string(definition_json),
            role=self.agent_execution_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            tracing_enabled=True
        )

        # Add tags
        Tags.of(self.state_machine).add("Application", "StepFunctionsAgent")
        Tags.of(self.state_machine).add("Type", "Agent")
        Tags.of(self.state_machine).add("AgentName", self.agent_name)
        Tags.of(self.state_machine).add("Environment", self.env_name)
        Tags.of(self.state_machine).add("ManagedBy", "StepFunctionsAgentUI")
        Tags.of(self.state_machine).add("LLMType", "UnifiedRust")

        # Update the state machine name for external reference
        self.state_machine_name = f"{self.agent_name}-{self.env_name}"

    def _grant_permissions(self):
        """Grant necessary permissions to the Lambda functions"""

        # Grant the state machine permission to invoke all the Lambda functions
        for tool_lambda in [
            self.analyze_csv_tool,
            self.validate_agent_tool,
            self.generate_config_tool,
            self.execute_batch_tool,
            self.monitor_execution_tool,
            self.get_results_tool
        ]:
            tool_lambda.grant_invoke(self.agent_execution_role)

        # Import ARNs from other stacks
        batch_processor_arn = Fn.import_value(f"BatchProcessorStateMachineArn-{self.env_name}")
        results_bucket_name = Fn.import_value(f"BatchProcessorResultsBucket-{self.env_name}")
        agent_registry_arn = Fn.import_value(f"SharedTableArnAgentRegistry-{self.env_name}")

        # S3 permissions for CSV analysis and results
        s3_policy = iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:ListBucket"
            ],
            resources=[
                f"arn:aws:s3:::*",  # Read any CSV file user provides
                f"arn:aws:s3:::*/*"
            ]
        )

        # Step Functions permissions for batch processor
        sfn_policy = iam.PolicyStatement(
            actions=[
                "states:StartExecution",
                "states:DescribeExecution",
                "states:GetExecutionHistory"
            ],
            resources=[batch_processor_arn]
        )

        # DynamoDB permissions for agent registry
        dynamodb_policy = iam.PolicyStatement(
            actions=[
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            resources=[agent_registry_arn]
        )

        # Apply permissions to all tools
        for tool_lambda in [
            self.analyze_csv_tool,
            self.validate_agent_tool,
            self.generate_config_tool,
            self.execute_batch_tool,
            self.monitor_execution_tool,
            self.get_results_tool
        ]:
            tool_lambda.add_to_role_policy(s3_policy)
            tool_lambda.add_to_role_policy(dynamodb_policy)

        # Only execution and monitoring tools need Step Functions permissions
        self.execute_batch_tool.add_to_role_policy(sfn_policy)
        self.monitor_execution_tool.add_to_role_policy(sfn_policy)
        self.get_results_tool.add_to_role_policy(sfn_policy)

        # Also grant permission to describe any Step Functions execution (for monitoring)
        describe_any_execution_policy = iam.PolicyStatement(
            actions=[
                "states:DescribeExecution",
                "states:GetExecutionHistory"
            ],
            resources=["*"]  # Need to describe any execution
        )
        self.execute_batch_tool.add_to_role_policy(describe_any_execution_policy)
        self.monitor_execution_tool.add_to_role_policy(describe_any_execution_policy)
        self.get_results_tool.add_to_role_policy(describe_any_execution_policy)

    def _register_tools_in_registry(self):
        """Register batch orchestrator tools in the tool registry"""
        from ..tools.base_tool_construct import BaseToolConstruct

        # Define tool specifications for registration
        tool_specs = [
            {
                "tool_name": "analyze_csv_structure",
                "description": "Analyzes CSV file structure and returns column info and sample data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "s3_uri": {
                            "type": "string",
                            "description": "S3 URI of the CSV file to analyze (e.g., s3://bucket/key.csv)"
                        }
                    },
                    "required": ["s3_uri"]
                },
                "tool_type": "lambda",
                "lambda_arn": self.analyze_csv_tool.function_arn,
                "lambda_function_name": f"batch-orchestrator-analyze-csv-{self.env_name}",
                "requires_activity": False,
                "human_approval_required": False,
                "tags": ["csv", "batch", "analysis"],
                "author": "batch-orchestrator"
            },
            {
                "tool_name": "validate_agent_compatibility",
                "description": "Validates that an agent has structured output capability",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent to validate"
                        }
                    },
                    "required": ["agent_name"]
                },
                "tool_type": "lambda",
                "lambda_arn": self.validate_agent_tool.function_arn,
                "lambda_function_name": f"batch-orchestrator-validate-agent-{self.env_name}",
                "requires_activity": False,
                "human_approval_required": False,
                "tags": ["validation", "batch", "structured-output"],
                "author": "batch-orchestrator"
            },
            {
                "tool_name": "generate_batch_config",
                "description": "Generates configuration for batch processor",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "csv_columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of CSV column names"
                        },
                        "agent_name": {
                            "type": "string",
                            "description": "Target agent name"
                        },
                        "input_mapping": {
                            "type": "object",
                            "description": "Mapping from CSV columns to agent input fields"
                        },
                        "output_mapping": {
                            "type": "object",
                            "description": "Mapping from agent structured output to CSV columns"
                        }
                    },
                    "required": ["csv_columns", "agent_name"]
                },
                "tool_type": "lambda",
                "lambda_arn": self.generate_config_tool.function_arn,
                "lambda_function_name": f"batch-orchestrator-generate-config-{self.env_name}",
                "requires_activity": False,
                "human_approval_required": False,
                "tags": ["configuration", "batch"],
                "author": "batch-orchestrator"
            },
            {
                "tool_name": "execute_batch_processor",
                "description": "Starts batch processing execution",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "csv_s3_uri": {
                            "type": "string",
                            "description": "S3 URI of input CSV file"
                        },
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent to use for processing"
                        },
                        "input_mapping": {
                            "type": "object",
                            "description": "How to map CSV columns to agent input"
                        },
                        "output_mapping": {
                            "type": "object",
                            "description": "How to map structured output to CSV columns"
                        },
                        "max_concurrency": {
                            "type": "integer",
                            "description": "Maximum concurrent executions (default: 10)",
                            "default": 10
                        },
                        "fileProcessingId": {
                            "type": "string",
                            "description": "Unique identifier for tracking this file processing job (used for DynamoDB updates)"
                        }
                    },
                    "required": ["csv_s3_uri", "agent_name", "input_mapping", "output_mapping"]
                },
                "tool_type": "lambda",
                "lambda_arn": self.execute_batch_tool.function_arn,
                "lambda_function_name": f"batch-orchestrator-execute-batch-{self.env_name}",
                "requires_activity": False,
                "human_approval_required": False,
                "tags": ["execution", "batch", "step-functions"],
                "author": "batch-orchestrator"
            },
            {
                "tool_name": "monitor_batch_execution",
                "description": "Monitors the status of a batch processing execution",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "execution_arn": {
                            "type": "string",
                            "description": "ARN of the Step Functions execution to monitor"
                        }
                    },
                    "required": ["execution_arn"]
                },
                "tool_type": "lambda",
                "lambda_arn": self.monitor_execution_tool.function_arn,
                "lambda_function_name": f"batch-orchestrator-monitor-{self.env_name}",
                "requires_activity": False,
                "human_approval_required": False,
                "polling_interval": 30,  # Wait 30 seconds between monitoring calls
                "max_polling_attempts": 20,  # Maximum 20 attempts (10 minutes total)
                "tags": ["monitoring", "batch", "step-functions", "polling"],
                "author": "batch-orchestrator"
            },
            {
                "tool_name": "get_batch_results",
                "description": "Retrieves results from completed batch processing",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "execution_id": {
                            "type": "string",
                            "description": "Execution ID of the batch processing job"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["csv", "json"],
                            "description": "Format for results (default: csv)",
                            "default": "csv"
                        }
                    },
                    "required": ["execution_id"]
                },
                "tool_type": "lambda",
                "lambda_arn": self.get_results_tool.function_arn,
                "lambda_function_name": f"batch-orchestrator-get-results-{self.env_name}",
                "requires_activity": False,
                "human_approval_required": False,
                "tags": ["results", "batch", "csv"],
                "author": "batch-orchestrator"
            }
        ]

        # Register tools using BaseToolConstruct
        for tool_spec in tool_specs:
            BaseToolConstruct(
                self,
                f"Register{tool_spec['tool_name'].replace('_', '')}Tool",
                tool_specs=[tool_spec],
                lambda_function=None,  # Lambda already exists
                env_name=self.env_name
            )