from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class ImageAnalysisAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Getting the secret by its name
        secret_name = "/ai-agent/api-keys"
        api_key_secret = secretsmanager.Secret.from_secret_name_v2(
            self, 
            "Secret", 
            secret_name
        )

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallOpenAILLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLM", 
            call_llm_function_name
        )

        ### Tools Lambda Functions

        #### Create a bucket for the image analysis tool
        image_analysis_bucket = s3.Bucket(
            self, "ImageAnalysisBucket",
            bucket_name=f"image-analysis-bucket-{self.account}-{self.region}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        #### GraphQL Tools

        graphql_lambda_role = iam.Role(
            self, "GraphQLToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "GraphQLToolLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        api_key_secret.grant_read(graphql_lambda_role)
        image_analysis_bucket.grant_read(graphql_lambda_role)

        # Define the Lambda function
        image_analysis_lambda_function = _lambda_python.PythonFunction(
            self, 
            "ImageAnalysisLambdaFunction",
            function_name="ImageAnalysisToolLambdaFunction",
            description="Image Analysis Tool Lambda Function based on MultiModal LLM.",
            entry="lambda/tools/image-analysis",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=128,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.X86_64,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=graphql_lambda_role,
            tracing=_lambda.Tracing.ACTIVE,
        )

        # Define the Step Functions state machine

        # Create graphql tools
        image_analysis_tools = [
            Tool(
                "analyze_images",
                "Analyze the content of the provided images from their location in S3, with the provided query.",
                image_analysis_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "image_locations" : {
                            "type": "array",
                            "description": "The locations of the images to analyze.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "bucket": {
                                        "type": "string",
                                        "description": "the bucket name"
                                    },
                                    "key": {
                                        "type": "string",
                                        "description": "the key name of the image object in the bucket"
                                    }
                                }
                            },
                        },
                        "query": {
                            "type": "string",
                            "description": "The query of the image analysis."
                        }
                    },
                    "required": [
                        "image_locations",
                        "query"
                    ]
                }
            )
        ]  # type: list[Tool]

        system_prompt="""
        You are an expert business analyst with deep knowledge of food products and their nutritional content.
         
        Your job is to help users understand what are health value of their food. 
        You have access to a set of tools, and please use them when needed.
        Please prefer to use the print_output tool to format the reply, instead of ending the turn. 
        """

        image_analysis_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "ImageAnalysisAIStateMachine",
            state_machine_name="ImageAnalysisAIAgentStateMachine",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=image_analysis_tools,
            system_prompt=system_prompt,
        )

        self.tool_functions = [
            image_analysis_lambda_function.function_name,
        ]

        self.agent_flows = [
            image_analysis_agent_flow.state_machine_name,
        ]
