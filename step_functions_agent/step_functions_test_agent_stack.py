from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_lambda_python_alpha as _lambda_python,
    aws_logs as logs,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class TestAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## Create the DynamoDB table for the long content extension
        dynamodb_long_content_table = dynamodb.Table(
            self, 
            "LongContentDynamoDBTable",
            table_name=f"LongContentDynamoDBTable-test-{self.account}-{self.region}",
            partition_key=dynamodb.Attribute(
                name="id", 
                type=dynamodb.AttributeType.STRING
            ),
            # Adding TTL for the records to be deleted after 1 hour
            time_to_live_attribute="ttl",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        ## Create Log Group to be used by the lambdas and step functions
        log_group = logs.LogGroup(
            self, 
            "TestAgentLogGroup", 
            retention=logs.RetentionDays.ONE_WEEK
        )

        ####### Call LLM Lambda with long context extension  ######

        # The execution role for the lambda
        call_llm_lambda_role = iam.Role(
            self,
            "CallLLMLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Grant the lambda access to the secrets with the API keys for the LLM
        call_llm_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/ai-agent/*",
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/api-keys*"
                ]
            )
        )

        dynamodb_long_content_table.grant_read_write_data(call_llm_lambda_role)

        ### Get the extension layer from its name (we will create it here later)
        # TODO: Create the extension layer in the CDK stacks

        extension_layer_arm_version = 17

        extension_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "ExtensionLayerArm",
            layer_version_arn=f"arn:aws:lambda:{self.region}:{self.account}:layer:lambda-runtime-api-proxy-arm-dev:{extension_layer_arm_version}"
        )

        llm_layer = _lambda_python.PythonLayerVersion(
            self, "LLMLayer",
            entry="lambda/call_llm/lambda_layer/python",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            description="A layer for the LLM Lambda functions",
        )

        # Creating the Call LLM lambda function for Claude only 
        call_llm_lambda_function = _lambda_python.PythonFunction(
            self, "CallLLMLambdaWithExtension",
            # Name of the Lambda function that will be used by the agents to find the function.
            function_name="CallLLMWithExtension",
            description="Lambda function to Call LLM (GPT) with messages history, tools and long content support.",
            entry="lambda/call_llm/functions/openai_llm",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="openai_lambda.py",
            handler="lambda_handler",
            layers=[
                llm_layer,
                extension_layer
            ],
            environment={
                "AGENT_CONTEXT_TABLE": dynamodb_long_content_table.table_name,
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
            },
            architecture=_lambda.Architecture.ARM_64,
            log_group=log_group,
            role=call_llm_lambda_role,
            tracing= _lambda.Tracing.ACTIVE,
        )

        ### Tools Lambda Functions

        #### DB Tools

        db_interface_lambda_role = iam.Role(
            self, "DBInterfaceLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "DBInterfaceLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        dynamodb_long_content_table.grant_read_write_data(db_interface_lambda_role)

        db_interface_lambda_function = _lambda_python.PythonFunction(
            self, "DBInterfaceLambda",
            function_name="TestDBInterface",
            description="Lambda function to interface with the SQLite database.",
            entry="lambda/tools/db-interface",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=512,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            layers=[
                extension_layer
            ],
            environment={
                "AGENT_CONTEXT_TABLE": dynamodb_long_content_table.table_name,
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
            },
              log_group=log_group,
            role=db_interface_lambda_role,
            tracing= _lambda.Tracing.ACTIVE,
        )

        #### Code Interpreter Tools

        # Create IAM role for code interpreter lambda
        code_interpreter_lambda_role = iam.Role(
            self, "CodeInterpreterLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "CodeInterpreterLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # The S3 bucket that stores the output images
        code_interpreter_output_bucket = s3.Bucket(
            self,
            "CodeInterpreterOutputBucket",
            bucket_name=f"code-interpreter-output-bucket-test-{self.account}-{self.region}"
        )

        # Add permissions to access E2B API key from Secrets Manager
        code_interpreter_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/api-keys*"
                ]
            )
        )

        # Add permissions to access S3 bucket
        code_interpreter_output_bucket.grant_read_write(code_interpreter_lambda_role)
        dynamodb_long_content_table.grant_read_write_data(code_interpreter_lambda_role)

        # Create the code interpreter lambda function
        code_interpreter_lambda_function = _lambda_python.PythonFunction(
            self, "CodeInterpreterLambda",
            function_name="TestCodeInterpreter",
            description="Lambda function to execute visualization code in a Jupyter notebook and return the URL of the image that was created.",
            entry="lambda/tools/code-interpreter",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(300),  # 5 minutes timeout for code execution
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            layers=[
                extension_layer
            ],
            environment={
                "IMAGE_BUCKET_NAME": code_interpreter_output_bucket.bucket_name,
                "AGENT_CONTEXT_TABLE": dynamodb_long_content_table.table_name,
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/extensions/lrap-wrapper/wrapper",
            },
            architecture=_lambda.Architecture.X86_64,  # Using x86_64 for better compatibility with dependencies
            log_group=log_group,
            role=code_interpreter_lambda_role,
            tracing= _lambda.Tracing.ACTIVE,
        )

        # Define the Step Functions state machine

        # Create claude tools

        tools = [
            Tool(
                "get_db_schema", 
                "Describe the schema of the SQLite database, including table names, and column names and types.",
                db_interface_lambda_function,
            ),
            Tool(
                "execute_sql_query", 
                "Return the query results of the given SQL query to the SQLite database.",
                db_interface_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "The sql query to execute against the SQLite database."
                        }
                    },
                    "required": [
                        "sql_query"
                    ]
                },
                # human_approval_activity=human_approval_activity
            ),
            Tool(
                "execute_python", 
                "Execute python code in a Jupyter notebook cell and return the URL of the image that was created.",
                code_interpreter_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The python code to execute in a single cell."
                        }
                    },
                    "required": [
                        "code"
                    ]
                }
            )
        ]

        system_prompt="""
        You are an expert business analyst with deep knowledge of SQL and visualization code in Python. 
        Your job is to help users understand and analyze their internal baseball data. 
        You have access to a set of tools, but only use them when needed.
        Please don't assume to know the schema of the database, and use the get_db_schema tool to learn table and column names and types before using it.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        You also have access to a tool that allows execution of python code. 
        Use it to generate the visualizations in your analysis. 
        - the python code runs in jupyter notebook. 
        - every time you call `execute_python` tool, the python code is executed in a separate cell. 
        it's okay to multiple calls to `execute_python`. 
        - display visualizations using matplotlib directly in the notebook. don't worry about saving the visualizations to a file. 
        - you can run any python code you want, everything is running in a secure sandbox environment.
        """

        output_schema={
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to the question"
                },
                "chart": {
                    "type": "string",
                    "description": "The URL of the chart"
                }
            },
            "required": [
                "answer",
                "chart"
            ]
        }

        test_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "TestAgentWithToolsFlowAndClaude",
            state_machine_name="TestAgentWithToolsFlowAndClaude",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=tools,
            system_prompt=system_prompt,
            output_schema=output_schema,
        )

        self.llm_functions = [
            call_llm_lambda_function.function_name,
        ]

        self.tool_functions = [
            db_interface_lambda_function.function_name,
            code_interpreter_lambda_function.function_name,
        ]

        self.agent_flows = [
            test_agent_flow.state_machine_name,
        ]

        self.log_group_name = log_group.log_group_name