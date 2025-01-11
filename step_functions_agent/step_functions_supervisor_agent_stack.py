from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
)
from constructs import Construct
from .ai_supervisor_agent_construct_from_json import ConfigurableStepFunctionsConstruct, Agent, LLMProviderEnum

class SupervisorAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ####### Call LLM Lambda   ######

        # Since we already have the previous agent, we can reuse the same function

        # TODO - Get the function name from the previous agent
        call_llm_function_name = "CallLLM"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLM", 
            call_llm_function_name
        )

        ### Agent Step Functions

        ## SQL Agent
        sql_agent = sfn.StateMachine.from_state_machine_name(
            self,
            "SQLAgent",
            "QLAgentWithToolsFlowAndClaude"
        )

        # Analysis Agent
        research_agent = sfn.StateMachine.from_state_machine_name(
            self,
            "ResearchAgent",
            "ResearchAgentWithToolsAndClaude"
        )

        # Define the Step Functions state machine

        provider = LLMProviderEnum.ANTHROPIC

        # Create research tools
        supervisor_tools = [
            Agent(
                "sql_agent",
                "Analyze user request and generate SQL query to extract data from a baseball database, and generate a visualization to answer the user's question.",
                sql_agent,
                provider=provider,
            ),
            Agent(
                "research_agent",
                "Provide web research information to answer user's question regaring stock market companies.",
                research_agent,
                provider=provider,
            )
        ]

        system_prompt="""
        You are supervisor of a team of expert business analysts. 
        Your team job is to help users understand and analyze their internal data. 
        You have access to a set of tools, which are the different agents. 
        You must use them to complete the tasks. 
        When you see a user request that matches the capabilities of one of the agent, transfer the request to that agent, and don't try to solve it yourself. 
        Please note that the tool result of the agent can include two content parts, text and image. 
        When you are ready to reply to the user, please use the print_output tool to format the reply.
        """

        research_agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "SupervisorStateMachine",
            state_machine_name="SupervisorAgentWithToolsAndClaude",
            state_machine_template_path="step-functions/supervisor-agent-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            provider=provider,
            tools=supervisor_tools,
            system_prompt=system_prompt,
        )