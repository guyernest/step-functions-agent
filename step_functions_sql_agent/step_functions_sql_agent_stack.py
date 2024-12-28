from aws_cdk import (
    Duration,
    Stack,
    SecretValue,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_s3 as s3,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class SQLAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Create the secret for the API keys from the local .env file

        # Reading the API KEYs for the LLM and related services for each line in the .env file
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("#") or line.strip() == "":
                    continue
                key, value = line.strip().split("=", 1)
                secretsmanager.Secret(self, f"Secret-{key}", 
                    secret_name=f"/ai-agent/{key}", 
                    secret_object_value={
                        f"{key}": SecretValue.unsafe_plain_text(value),
                    }
                )

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
        call_llm_lambda_function = _lambda_python.PythonFunction(
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
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:/ai-agent/E2B_API_KEY*"
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

        # Create test tools
        tools = [
            Tool(
                "get_db_schema", 
                "Describe the schema of the SQLite database, including table names, and column names and types.",
                db_interface_lambda_function
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
                }
            ),
            Tool(
                "execute_python", 
                "Execute python code in a Jupyter notebook cell and URL of the image that was created.",
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

        agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "AIStateMachine",
            region=self.region,
            account=self.account,
            state_machine_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=tools,
            system_prompt="You are an expert business analyst with deep knowledge of SQL and visualization code in Python. Your job is to help users understand and analyze their internal baseball data. You have access to a set of tools, but only use them when needed. You also have access to a tool that allows execution of python code. Use it to generate the visualizations in your analysis. - the python code runs in jupyter notebook. - every time you call `execute_python` tool, the python code is executed in a separate cell. it's okay to multiple calls to `execute_python`. - display visualizations using matplotlib directly in the notebook. don't worry about saving the visualizations to a file. - you can run any python code you want, everything is running in a secure sandbox environment.",
            output_schema={
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The answer to the question"
                    }
                },
                "required": [
                    "answer"
                ]
            }
        )
