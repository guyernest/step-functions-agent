import json
from typing import Dict, Any, List
from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_lambda as lambda_,
    aws_iam as iam
)
from constructs import Construct

class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        lambda_function: lambda_.Function,
        input_schema: Dict[str, Any] = None
    ):
        self.name = name
        self.description = description
        self.lambda_function = lambda_function
        self.input_schema = input_schema or {"type": "object", "properties": {}}

    
    def get_lambda_function(self) -> lambda_.Function:
        """Get the Lambda function."""
        return self.lambda_function

    def to_tool_definition(self) -> Dict[str, Any]:
        """Convert tool to the format expected in the LLM system message"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }

    def get_lambda_arn(self) -> str:
        return self.lambda_function.function_arn

class ConfigurableStepFunctionsConstruct(Construct):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        region: str,
        account: str,
        state_machine_path: str,
        llm_caller: lambda_.Function,
        tools: List[Tool],
        system_prompt: str = None,
        output_schema: Dict[str, Any] = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.region = region
        self.account = account

        # Load the base state machine definition
        with open(state_machine_path, 'r') as f:
            state_machine_def = json.load(f)

        # Configure the state machine definition with the provided LLM caller
        self._configure_llm_call(state_machine_def, llm_caller, system_prompt)

        # Update the state machine definition with tools configuration
        self._configure_tools(state_machine_def, tools, output_schema)

        # Create the state machine role with permissions for all tool Lambda functions
        role = self._create_state_machine_role(
            llm_caller, 
            [tool.get_lambda_function() for tool in tools]
        )

        # Create the state machine
        state_machine = sfn.CfnStateMachine(
            self, "ConfigurableStateMachine",
            role_arn=role.role_arn,
            definition_string=json.dumps(state_machine_def),
        )

        # Print the generated state machine definition
        print(json.dumps(state_machine_def, indent=4))


    def _configure_llm_call(
        self, 
        definition: Dict[str, Any], 
        llm_caller: lambda_.Function,
        system_prompt: str = None
    ) -> None:
        """Configure the state machine definition with the provided LLM caller"""
        # Update the LLM call state with the provided LLM caller
        llm_state = definition["States"]["Call LLM"]
        llm_state["Arguments"]["FunctionName"] = llm_caller.function_arn

        payload = llm_state["Arguments"]["Payload"]
        # Update system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

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

        # Adding print_output tool
        if output_schema is not None:
            payload["tools"].append({
                "name": "print_output",
                "description": "Print the output of the previous step",
                "input_schema": output_schema
            })
        else:
            payload["tools"].append({
                "name": "print_output",
                "description": "Print the output of the previous step",
                "input_schema": {"type": "object", "properties": {}}
            })

        # Update tool choice state
        tool_processor_states = definition["States"]["For each tool use"]["ItemProcessor"]["States"]
        choices = []
        
        # Create a choice for each tool
        for tool in tools:
            choice = {
                "Next": f"Execute {tool.name}",
                "Condition": (
                    f"{{% ($states.input.type = \"tool_use\") and "
                    f"($states.input.name = \"{tool.name}\") %}}"
                )
            }
            choices.append(choice)
            
            # Add the tool execution state
            tool_processor_states[f"Execute {tool.name}"] = {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Arguments": {
                    "FunctionName": tool.get_lambda_arn(),
                    "Payload": "{% $states.input %}",
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
                "Output": "{% $states.result.Payload %}",
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
            "output": {
                "type": "string",
                "description": "The output of the previous step"
            }
        }
    }

    # Create test tools
    tools = [
        Tool(
            "get_db_schema", 
            "Describe the schema of the SQLite database, including table names, and column names and types.",
            tool_lambda_1
        ),
        Tool(
            "execute_sql_query", 
            "Return the query results of the given SQL query to the SQLite database.",
            tool_lambda_1,
            input_schema={
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                }
            }
        ),
        Tool(
            "execute_python", 
            "Execute python code in a Jupyter notebook cell and URL of the image that was created.",
            tool_lambda_1,
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The python code to execute"
                    }
                }
            }
        )
    ]

    # Create the state machine
    ai_state_machine = ConfigurableStepFunctionsConstruct(
        stack, 
        "AIStateMachine", 
        region="us-east-1",
        account="123456789012",
        state_machine_path="step-functions/agent-with-tools-flow-template.json", 
        llm_caller=llm_caller, 
        tools=tools
    )

