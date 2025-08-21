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

class Agent:
    def __init__(
        self,
        name: str,
        description: str,
        state_machine: sfn.StateMachine,
        provider: str = LLMProviderEnum.ANTHROPIC,
    ):
        self.name: str = name
        self.description: str = description
        self.state_machine: sfn.StateMachine = state_machine
        self.provider: str = provider
        self.input_schema: Dict[str, Any] = {
                "type": "object",
                "properties": {
                  "question": {
                    "type": "string",
                    "description": "The question of the user."
                  }
                },
                "required": [
                  "question"
                ]
              }


    def get_state_machine(self) -> sfn.StateMachine:
        """Get the State Machine."""
        return self.state_machine

    def to_tool_definition(self) -> Dict[str, Any]:
        """Convert tool to the format expected in the LLM system message"""
        if self.provider == LLMProviderEnum.OPENAI:
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

    def get_state_machine_arn(self) -> str:
        return self.state_machine.state_machine_arn

class ConfigurableStepFunctionsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        state_machine_name: str,
        state_machine_template_path: str,
        llm_caller: lambda_.Function,
        provider: str = LLMProviderEnum.ANTHROPIC,
        tools: List[Agent] = [],
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
            [tool.get_state_machine() for tool in tools]
        )

        self.state_machine_def = state_machine_def

        # Create the state machine
        state_machine = sfn.StateMachine(
            self,
            construct_id,
            state_machine_name=state_machine_name,
            role=role,
            definition_body=sfn.DefinitionBody.from_string(json.dumps(state_machine_def)),
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

        if provider == LLMProviderEnum.OPENAI:
            payload["model"] = "gpt-4o"
        elif provider == LLMProviderEnum.ANTHROPIC:
            payload["model"] = "claude-3-haiku-20240307"

    def _configure_tools(
        self,
        definition: Dict[str, Any],
        tools: List[Agent],
        output_schema: Dict[str, Any] = None
    ) -> None:
        """Configure the state machine definition with the provided tools"""
        # Update the LLM call state with tools and system prompt
        llm_state = definition["States"]["Call LLM"]
        payload = llm_state["Arguments"]["Payload"]

        # Update tools list
        payload["tools"] = [tool.to_tool_definition() for tool in tools]

        if self.provider == LLMProviderEnum.OPENAI:
            print_output_tool = {
                "type": "function",
                "function": {
                    "name": "print_output",
                    "description": "Print the output of the previous steps",
                    "parameters": output_schema if output_schema else {
                        "type": "object",
                        "properties": {
                            "answer": {
                                "type": "string",
                                "description": "The abswer to users question"
                            }
                        }
                    }
                }
            }
        elif self.provider == LLMProviderEnum.ANTHROPIC:
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
            choice = {
                "Condition": (
                    "{% ($states.input.type in [\"function\",\"tool_use\"]) and "
                    f"($states.input.**.name = \"{tool.name}\") %}}"
                ),
                "Next": f"Execute {tool.name}"
            }
            choices.append(choice)

            # Add the tool execution state
            tool_processor_states[f"Execute {tool.name}"] = {
                "Type": "Task",
                "Resource": "arn:aws:states:::states:startExecution.sync:2",
                "Arguments": {
                "StateMachineArn": tool.get_state_machine_arn(),
                "Input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "{% $states.input.input.question %}"
                        }
                    ]
                }
                },
                "Comment": f"Call the agent: {tool.name}",
                "Output": "{% \n{\n  \"messages\": $append(\n    $states.result.Output.messages,\n    $states.result.Output.output.{\n      \"role\": \"user\",\n      \"content\": [\n        {\n          \"type\": \"tool_result\",\n          \"tool_use_id\": $states.input.id,\n          \"content\": $map($keys($), function($key) { $string($[$key]) })\n        }\n      ]\n    }\n  )\n}\n%}",
                "End": True
            }

        # Update the choice state with new choices
        tool_processor_states["Which Tool to Use?"]["Choices"] = choices

    def _create_state_machine_role(
        self,
        call_llm: lambda_.Function,
        tools: List[Agent]
    ) -> iam.Role:
        """Create IAM role with permissions for all tool Lambda functions"""
        role = iam.Role(
            self, "StateMachineRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com")
        )

        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "events:PutTargets",
                    "events:PutRule",
                    "events:DescribeRule"
                ],
                resources=[
                    "arn:aws:events:*:*:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule",
                ]
            )
        )

        call_llm.grant_invoke(role)

        # Add Lambda invoke permissions for each tool
        for tool in tools:
            tool.grant_execution(
                role,
                "states:DescribeExecution",
                "states:StopExecution"
            )
            tool.grant_start_execution(role)

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
    agent_1 = sfn.StateMachine(
        stack, "TestAgent1",
        state_machine_name="TestAgent1",
        definition=sfn.Pass(stack, "TestToolLambda1")
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
        Agent(
            "calculator",
            "Calculate the result of a mathematical expression.",
            agent_1,
            provider
        )
    ]

    # Create the state machine
    ai_state_machine = ConfigurableStepFunctionsConstruct(
        stack,
        "TestSupervisorAIStateMachine",
        state_machine_name="TestSupervisorAgentWithToolsFlow",
        state_machine_template_path="step-functions/supervisor-agent-flow-template.json",
        system_prompt="Blah",
        llm_caller=llm_caller,
        provider=provider,
        tools=tools,
        output_schema=output_schema
    )

    # Print the generated state machine definition
    print(json.dumps(ai_state_machine.state_machine_def, indent=4))
