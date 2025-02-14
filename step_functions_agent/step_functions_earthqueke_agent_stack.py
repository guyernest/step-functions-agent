from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_lambda_python_alpha as _lambda_python,
)
from constructs import Construct
from .ai_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Tool

class EarthquakeAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallClaudeLLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLM", 
            call_llm_function_name
        )

        ### Tools Lambda Functions

        #### CloudWatch Tools

        earthquake_tool_lambda_role = iam.Role(
            self, "EarthquakeToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                "EarthquakeToolLambdaPolicy",
                managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            ]
        )

        # Define the Lambda function
        earthquake_tool_lambda_function = _lambda_python.PythonFunction(
            self, 
            "EarthquakeToolLambdaFunction",
            function_name="EarthquakeToolLambdaFunction",
            description="Query earthquake data from USGS API.",
            entry="lambda/tools/EarthQuakeQuery",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=128,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=earthquake_tool_lambda_role,
        )

        # Define the Step Functions state machine

        # Create graphql tools
        earthquake_tools = [
            Tool(
                "query_earthquakes",
                "Retrieve earthquake data from the USGS Earthquake Hazards Program API and display the .",
                earthquake_tool_lambda_function,
                input_schema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "The start date for the earthquake data in YYYY-MM-DD format."
                        },
                        "end_date": {
                            "type": "string",
                            "description": "The end date for the earthquake data in YYYY-MM-DD format."
                        }
                    },
                    "required": [
                        "start_date", 
                        "end_date"
                    ]
                }
            )
        ]  # type: list[Tool]

        system_prompt="""
        You are an expert earth science analyst with deep knowledge or earthquakes and other natural disasters.

        You have access to a set of tools, and please use them when needed. 

        Answer only based on the retrived data.
        """  # type: str

        earthquake_insights_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "EarthquakeInsightsAIStateMachine",
            state_machine_name="EarthquakeInsightsAIStateMachine",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            tools=earthquake_tools,
            system_prompt=system_prompt,
        )

                # Adding the generated lambda and step functions to self to allow monitoring stack to access them
        self.llm_functions = []

        self.tool_functions = [
            earthquake_tool_lambda_function.function_name,
        ]

        self.agent_flows = [
            earthquake_insights_agent_flow.state_machine_name,
        ]

        # self.log_group_name = log_group.log_group_name  