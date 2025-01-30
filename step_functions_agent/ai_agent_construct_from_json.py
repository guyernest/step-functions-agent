import json
from typing import Dict, Any, List
from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_lambda as lambda_,
    aws_iam as iam
)
from constructs import Construct

# Enum for LLM providers (OpenAI, Anthropic, etc.)
class LLMProviderEnum:
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AI21 = "ai21"

class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        lambda_function: lambda_.Function,
        provider: str = LLMProviderEnum.ANTHROPIC,
        input_schema: Dict[str, Any] = None,
        human_approval_activity: sfn.Activity = None,
    ):
        self.name = name
        self.description = description
        self.lambda_function = lambda_function
        self.provider = provider
        self.input_schema = input_schema or {"type": "object", "properties": {}}
        self.human_approval_activity = human_approval_activity

    
    def get_lambda_function(self) -> lambda_.Function:
        """Get the Lambda function."""
        return self.lambda_function

    def to_tool_definition(self) -> Dict[str, Any]:
        """Convert tool to the format expected in the LLM system message"""
        if self.provider == LLMProviderEnum.OPENAI or self.provider == LLMProviderEnum.AI21:
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.input_schema,
                }
            } 
        elif self.provider == LLMProviderEnum.ANTHROPIC:
            return {
                "name": self.name,
                "description": self.description,
                "input_schema": self.input_schema
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
    def get_lambda_arn(self) -> str:
        return self.lambda_function.function_arn

class ConfigurableStepFunctionsConstruct(Construct):
    def __init__(
        self, 
        scope: Construct,
        construct_id: str,
        state_machine_name: str,
        state_machine_template_path: str,
        llm_caller: lambda_.Function,
        provider: str = LLMProviderEnum.ANTHROPIC,
        tools: List[Tool] = [],
        system_prompt: str = None,
        output_schema: Dict[str, Any] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.state_machine_name = state_machine_name
        self.provider = provider

        # Load the base state machine definition
        with open(state_machine_template_path, 'r') as f:
            state_machine_def = json.load(f)

        # print the call_llm state definition before configuration
        # print(json.dumps(state_machine_def["States"]["Call LLM"], indent=4))
        # Configure the state machine definition with the provided LLM caller
        self._configure_llm_call(
            state_machine_def, 
            llm_caller, 
            provider, 
            system_prompt
        )

        # Update the state machine definition with tools configuration
        self._configure_tools(
            state_machine_def, 
            tools, 
            output_schema
        )
        # print the call_llm state definition after configuration
        # print(json.dumps(state_machine_def["States"]["Call LLM"], indent=4))

        # Create the state machine role with permissions for all tool Lambda functions
        role = self._create_state_machine_role(
            llm_caller, 
            [tool.get_lambda_function() for tool in tools]
        )

        # Create the state machine
        state_machine = sfn.CfnStateMachine(
            self, 
            construct_id,
            state_machine_name=state_machine_name,
            role_arn=role.role_arn,
            definition_string=json.dumps(state_machine_def),
        )

        # Print the generated state machine definition
        # print(json.dumps(state_machine_def, indent=4))


    def _configure_llm_call(
        self, 
        definition: Dict[str, Any], 
        llm_caller: lambda_.Function,
        provider: str = LLMProviderEnum.ANTHROPIC,
        system_prompt: str = None
    ) -> None:
        """Configure the state machine definition with the provided LLM caller"""
        # Update the LLM call state with the provided LLM caller
        llm_state = definition["States"]["Call LLM"]
        llm_state["Arguments"]["FunctionName"] = llm_caller.function_arn
        llm_state["Assign"]["provider"] = provider

        payload = llm_state["Arguments"]["Payload"]

        # Update system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        match provider:
            case LLMProviderEnum.OPENAI:
                payload["model"] = "gpt-4o"
            case LLMProviderEnum.AI21:
                payload["model"] = "ai21.jamba-1-5-large-v1:0"
            case LLMProviderEnum.ANTHROPIC:
                payload["model"] = "claude-3-5-sonnet-20241022"

    def _configure_tools(
        self, 
        definition: Dict[str, Any], 
        tools: List[Tool],
        output_schema: Dict[str, Any] = None
    ) -> None:
        """Configure the state machine definition with the provided tools"""
        # Update the LLM call state with tools and system prompt
        llm_state = definition["States"]["Call LLM"]
        payload = llm_state["Arguments"]["Payload"]
        
        # Update tools list
        payload["tools"] = [tool.to_tool_definition() for tool in tools]

        # Defining the print_output tool basesd on the output schema
        print_output_tool = {
            "name": "print_output",
            "description": "Print the output of the previous steps",
            "input_schema": output_schema if output_schema else {
                "type": "object", 
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The abswer to users question"
                    }
                },
            },
        }

        # Adding print_output tool
        payload["tools"].append(print_output_tool)

        # Update tool choice state
        tool_processor_states = definition["States"]["For each tool use"]["ItemProcessor"]["States"]
        choices = []
        
        # Create a choice for each tool
        for tool in tools:
            # Define the choice condition for the tool

            # We have two options for the choice condition:, one for direct call and one through the human approval activity
            if tool.human_approval_activity:
                next_state = f"Approve {tool.name}"
            else:
                next_state = f"Execute {tool.name}"

            choice = {
                "Condition": (
                    f"{{% ($states.input.**.name = \"{tool.name}\") %}}"
                ),
                "Next": next_state,
            }
            choices.append(choice)

            tool_input_jsonata = "{% $states.input.input %}"
            # Add the tool approval states
            if tool.human_approval_activity:
                # Call the human approval activity
                tool_processor_states[f"Approve {tool.name}"] = {
                    "Type": "Task",
                    "Resource": tool.human_approval_activity.activity_arn,
                    "Next": f"Process Approval {tool.name}",
                }
                # Check the approval result
                tool_processor_states[f"Process Approval {tool.name}"] = {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Condition": (
                                "{% $states.input.approved  %}"
                            ),
                            "Next": f"Execute {tool.name}"
                        }
                    ],
                    ## TODO add a pass state to send the rejection reason to the LLM
                    "Default": f"Handle Rejection {tool.name}"
                }
                # Handle the rejection
                tool_processor_states[f"Handle Rejection {tool.name}"] = {
                    "Type": "Pass",
                    "End": True,
                    "Comment": "The tool usage was rejected by the user."
                }
                # The approval process returns a simpler input format
                tool_input_jsonata = "{% $states.input.input %}"
            
            # Add the tool execution state
            tool_processor_states[f"Execute {tool.name}"] = {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Arguments": {
                    "FunctionName": tool.get_lambda_arn(),
                    "Payload": {
                        "name": "{% $states.input.**.name %}",
                        "id": "{% $states.input.id %}",
                        "input": tool_input_jsonata,
                    }
                },
                "Retry": [{
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
                }],
                "End": True,
                "Comment": f"Call the tool (Lambda function) {tool.name}.",
                "Output": "{%  $states.result.Payload  %}"
            }

        # Update the choice state with new choices
        tool_processor_states["Which Tool to Use?"]["Choices"] = choices

    def _create_state_machine_role(
        self, 
        call_llm: lambda_.Function, 
        tools: List[lambda_.Function]
    ) -> iam.Role:
        """Create IAM role with permissions for all tool Lambda functions"""
        role = iam.Role(
            self, "StateMachineRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )

        call_llm.grant_invoke(role)

        # Add Lambda invoke permissions for each tool
        for tool in tools:
            tool.grant_invoke(role)

        return role


if __name__ == "__main__":
    """
    Example usage
    """
    from aws_cdk import Stack
    # Create a test stack
    stack = Stack()

    # Create a test LLM caller
    llm_caller = lambda_.Function(
        stack, "TestLLMCaller",
        function_name="TestLLMCaller",
        runtime=lambda_.Runtime.PYTHON_3_8,
        handler="index.handler",
        code=lambda_.Code.from_inline("def handler(event, context): return event")
    )

    # Create test tool lambda functions
    tool_lambda_1 = lambda_.Function(
        stack, "TestToolLambda1",
        function_name="TestToolLambda1",
        runtime=lambda_.Runtime.PYTHON_3_8,
        handler="index.handler",
        code=lambda_.Code.from_inline("def handler(event, context): return event")
    )

    # Create test output schema
    output_schema = {
        "type": "object",
        "properties": {
            "sql_query": {
                "type": "string",
                "description": "The sql query to execute against the SQLite database."
            },
            "output": {
                "type": "string",
                "description": "The output of the previous step"
            }
        },
        "required": [
            "sql_query",
            "output"
        ]
    }

    provider = LLMProviderEnum.OPENAI

    # Create test tools
    tools = [
        Tool(
            "calculator", 
            "Calculate the result of a mathematical expression.",
            tool_lambda_1,
            provider
        )
    ]

    # Create the state machine
    ai_state_machine = ConfigurableStepFunctionsConstruct(
        stack, 
        "TestAIStateMachine", 
        state_machine_name="TestSQLAgentWithToolsFlow",
        state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
        system_prompt="Blah",
        llm_caller=llm_caller, 
        provider=provider,
        tools=tools,
        output_schema=output_schema
    )

