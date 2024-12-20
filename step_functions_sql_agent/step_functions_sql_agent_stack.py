from aws_cdk import (
    Duration,
    Stack,
    SecretValue,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_s3 as s3,
    aws_lambda_python_alpha as _lambda_python,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

class SQLAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Create the secret for the API keys from the local .env file

        # Reading the API KEYs for the LLM and related services for each line in the .env file
        # with open(".env", "r") as f:
        #     for line in f:
        #         if line.startswith("#") or line.strip() == "":
        #             continue
        #         key, value = line.strip().split("=", 1)
        #         secretsmanager.Secret(self, f"Secret-{key}", 
        #             secret_name=f"/ai-agent/{key}", 
        #             secret_object_value={
        #                 f"{key}": SecretValue.unsafe_plain_text(value),
        #             }
        #         )

        ####### Call LLM Lambda   ######

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

        call_llm_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/ai-agent/*",
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/*"
                ]
            )
        )

        # Define the Lambda function
        lambda_function = _lambda_python.PythonFunction(
            self, "CallLLMLambda",
            function_name="CallLLM",
            entry="lambda/call-llm",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,       
            role=call_llm_lambda_role,
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

        db_interface_lambda_function = _lambda_python.PythonFunction(
            self, "DBInterfaceLambda",
            function_name="DBInterface",
            entry="lambda/db-interface",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=512,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=db_interface_lambda_role,
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
            bucket_name=f"code-interpreter-output-bucket-{self.account}-{self.region}"
        )

        # Add permissions to access E2B API key from Secrets Manager
        code_interpreter_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/e2b-api-key*"
                ]
            )
        )

        # Add permissions to access S3 bucket
        code_interpreter_output_bucket.grant_read_write(code_interpreter_lambda_role)

        # Create the code interpreter lambda function
        code_interpreter_lambda_function = _lambda_python.PythonFunction(
            self, "CodeInterpreterLambda",
            function_name="CodeInterpreter",
            entry="lambda/code-interpreter",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(300),  # 5 minutes timeout for code execution
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            environment={
                "IMAGE_BUCKET_NAME": code_interpreter_output_bucket.bucket_name,
            },
            architecture=_lambda.Architecture.X86_64,  # Using x86_64 for better compatibility with dependencies
            role=code_interpreter_lambda_role,
        )

        # Define the Step Functions state machine

        # # Get function ARNs
        # call_llm_function_arn = lambda_function.function_arn
        # db_interface_function_arn = db_interface_lambda_function.function_arn
        # code_interpreter_function_arn = code_interpreter_lambda_function.function_arn

        # # Call LLM Task
        # call_llm_task = tasks.LambdaInvoke(
        #     self, "Call LLM",
        #     lambda_function=_lambda.Function.from_function_arn(self, "CallLLM", call_llm_function_arn),
        #     payload=sfn.TaskInput.from_object({
        #         "Payload": sfn.JsonPath.entire_payload,
        #         "FunctionName": call_llm_function_arn
        #     }),
        #     retry_on_service_exceptions=True
        # ).add_retry(
        #     errors=["Lambda.ServiceException", 
        #            "Lambda.AWSLambdaException", 
        #            "Lambda.SdkClientException", 
        #            "Lambda.TooManyRequestsException"],
        #     interval=Duration.seconds(1),
        #     max_attempts=3,
        #     backoff_rate=2.0
        # )

        # # Choice State: If Tool Use
        # if_tool_use = sfn.Choice(self, "If Tool Use").when(
        #     sfn.Condition.string_equals("$.metadata.stop_reason", "tool_use"),
        #     sfn.Map(
        #         self, "For each tool use",
        #         items_path="$.messages[-1].content",
        #         parameters={"Payload.$": "$"},
        #         item_processor=sfn.StateMachineFragment.to_single_state(
        #             sfn.Choice(self, "Which Tool to Use?")
        #             .when(sfn.Condition.and_(
        #                 sfn.Condition.string_equals("$.type", "tool_use"),
        #                 sfn.Condition.string_equals("$.name", "get_db_schema")),
        #                 tasks.LambdaInvoke(
        #                     self, "Get DB Schema",
        #                     lambda_function=_lambda.Function.from_function_arn(
        #                         self, "GetDBSchema", db_interface_function_arn
        #                     ),
        #                     output_path="$.Payload"
        #                 ).add_retry(
        #                     errors=["Lambda.ServiceException", 
        #                            "Lambda.AWSLambdaException", 
        #                            "Lambda.SdkClientException", 
        #                            "Lambda.TooManyRequestsException"],
        #                     interval=Duration.seconds(1),
        #                     max_attempts=3,
        #                     backoff_rate=2.0
        #                 )
        #             )
        #             .when(sfn.Condition.and_(
        #                 sfn.Condition.string_equals("$.type", "tool_use"),
        #                 sfn.Condition.string_equals("$.name", "execute_sql_query")),
        #                 tasks.LambdaInvoke(
        #                     self, "Execute SQL Query",
        #                     lambda_function=_lambda.Function.from_function_arn(
        #                         self, "ExecuteSQLQuery", db_interface_function_arn
        #                     ),
        #                     output_path="$.Payload"
        #                 ).add_retry(
        #                     errors=["Lambda.ServiceException", 
        #                            "Lambda.AWSLambdaException", 
        #                            "Lambda.SdkClientException", 
        #                            "Lambda.TooManyRequestsException"],
        #                     interval=Duration.seconds(1),
        #                     max_attempts=3,
        #                     backoff_rate=2.0
        #                 )
        #             )
        #             .when(sfn.Condition.and_(
        #                 sfn.Condition.string_equals("$.type", "tool_use"),
        #                 sfn.Condition.string_equals("$.name", "execute_python")),
        #                 tasks.LambdaInvoke(
        #                     self, "Execute Python",
        #                     lambda_function=_lambda.Function.from_function_arn(
        #                         self, "ExecutePython", code_interpreter_function_arn
        #                     ),
        #                     output_path="$.Payload"
        #                 ).add_retry(
        #                     errors=["Lambda.ServiceException", 
        #                            "Lambda.AWSLambdaException", 
        #                            "Lambda.SdkClientException", 
        #                            "Lambda.TooManyRequestsException"],
        #                     interval=Duration.seconds(1),
        #                     max_attempts=3,
        #                     backoff_rate=2.0
        #                 )
        #             )
        #             .otherwise(sfn.Pass(self, "No Tool to Use (ignore)"))
        #         )
        #     )
        # ).otherwise(sfn.Pass(self, "Prepare Output"))

        # # Final States
        # prepare_output = sfn.Pass(self, "Prepare Output", parameters={
        #     "messages.$": "$.messages",
        #     "answer.$": "$.messages[-1].content[0].text"
        # })

        # # Define State Machine
        # definition = call_llm_task.next(if_tool_use).next(prepare_output)

        # sfn.StateMachine(
        #     self, "AIAgentStateMachine",
        #     definition=definition,
        #     state_machine_name="AiAgentStateMachine"
        # )