# AI Agent State Machines

This directory contains the implementation of the various CDK stacks and constructs to build the step functions for the AI agents.

## Table of Contents

- [AI Agent Definition](#ai-agent-definition)
  - [LLM Call Lambda](#llm-call-lambda)
    - [Building a new LLM call](#building-a-new-llm-call)
    - [Using an existing LLM call](#using-an-existing-llm-call)
  - [Tools](#tools)
    - [Creating a new tool](#creating-a-new-tool)
    - [Using an existing tool](#using-an-existing-tool)
    - [Defining the Tool for the AI Agent](#defining-the-tool-for-the-ai-agent)
    - [Defining a tool needed a human approval](#defining-a-tool-needed-a-human-approval)
  - [Deployment](#deployment)

## AI Agent Definition

### LLM Call Lambda

Each agent is based on a specific LLM model that supports function calling or tool usage. You can choose the LLM based on cost, accuracy and other functional and non functional requirements. When building the AI agent you have two options:

#### Building a new LLM call

The process of building a new LLM call is described in the [lambda/call_llm](lambda/call_llm) directory. once you built the LLM call you can use it in the AI agent, and define it in the CDK stack as follows:

```python
        # Creating the Call LLM lambda function for the agent
        call_llm_lambda_function_claude = _lambda_python.PythonFunction(
            self, "CallLLMLambdaClaude",
            # Name of the Lambda function that will be used by the agents to find the function.
            function_name="CallLLMLambdaClaude", 
            description="Lambda function to Call LLM (Anthropic) with messages history and tools.",
            entry="lambda/call_llm",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="handlers/claude_handler.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=call_llm_lambda_claude_role,
        )
```

This definition will create a Lambda function and deploy it to AWS Lambda.

#### Using an existing LLM call

If the LLM call lambda function already exists, you can use it in the AI agent. You can define it in the CDK stack as follows:

```python
        # Define the name of the Call LLM Lambda function to be used in the AI agent
        call_llm_function_name = "CallLLMLambdaClaude"

        # Define the Lambda function
        call_llm_lambda_function = _lambda.Function.from_function_name(
            self, 
            "CallLLMLambdaClaude", 
            call_llm_function_name
        )
```

### Tools

Each of the tools that are used by the AI agents are defined and AWS Lambda functions and are define in the [lambda/tools](lambda/tools) directory. The process of building a new tool is described in the [lambda/tools/README.md](lambda/tools/README.md) file. Once you built the tool you can use it in the AI agent, and define it in the CDK stack as above (new tool or existing tool).

#### Creating a new tool

```python
    # Creating the Tool lambda function for the agent
    tool_x_lambda_function = _lambda_python.PythonFunction(
        self, "ToolXLambda",
        function_name="ToolXLambda", 
        description="Lambda function to Call tool X.",
        entry="lambda/tools/tool_x",
        runtime=_lambda.Runtime.PYTHON_3_12,
        timeout=Duration.seconds(90),
        memory_size=256,
        index="index.py",
        handler="lambda_handler",
        architecture=_lambda.Architecture.ARM_64,
        role=tool_x_lambda_role,
    )
```

#### Using an existing tool

```python
    # Define the name of the tool Lambda function to be used in the AI agent
    tool_x_function_name = "ToolXLambda"
    # Define the Lambda function
    tool_x_lambda_function = _lambda.Function.from_function_name(
        self,
        "ToolXLambda",
        tool_function_name
    )
```

#### Defining the Tool for the AI Agent

Once you have the tool defined you can use it in the AI agent. You can define it in the CDK stack as follows:

```python
    provider = LLMProviderEnum.ANTHROPIC

    # Create agent tools
    agent_tools = [
        Tool(
            "maps_geocode",
            "Convert an address into geographic coordinates.",
            tool_x_lambda_function,
            provider=provider,
            input_schema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The address to geocode."
                    }
                },
                "required": [
                    "address"
                ]
            }
        ),
        Tool(
            "maps_reverse_geocode",
            "Convert coordinates into an address.",
            tool_x_lambda_function,
            provider=provider,
            input_schema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "The latitude coordinate."
                    },
                    "longitude": {
                        "type": "number",
                        "description": "The longitude coordinate."
                    }
                },
                "required": [
                    "latitude",
                    "longitude"
                ]
            }
        )
    ]
```

#### Defining a tool needed a human (or external system) approval

Some of the tools might have side effects and need a human approval. In this case you can define the tool as follows:

```python
    # Adding human approval to the usage of the tools
    human_approval_activity = sfn.Activity(
        self, 
        "HumanApprovalActivityForToolX",
        activity_name="HumanApprovalActivityForToolX",
    )

    anthropic = LLMProviderEnum.ANTHROPIC

    agent_tools = [
        ...
        Tool(
            "execute_sql_query", 
            "Return the query results of the given SQL query to the SQLite database.",
            tool_x_lambda_function,
            provider=anthropic,
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
            human_approval_activity=human_approval_activity
        ),
        ...
    ]
```

## Define the AI Agent State Machine

### Define the System Prompt for the Agent

The system prompt is the message that the agent will use to start the conversation. You can define it as follows:

```python
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
```

The above example is a multi-line string that defines the system prompt for the agent. It is specific for the baseball data analysis use case. It can mention the tools that the agent has access to, the job of the agent, and any other information that is relevant to the agent.

### Define the Agent Step Functions State Machine

Using CDK:

```python
    agent_x_flow = ConfigurableStepFunctionsConstruct(
        self, 
        "AIAgentXStateMachine",
        state_machine_name="AIAgentXStateMachine",
        state_machine_template_path="step-functions/agent-with-tools-flow-template.json", 
        llm_caller=call_llm_lambda_function, 
        provider=anthropic,
        tools=agent_tools,
        system_prompt=system_prompt,
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
    )
```

You also need to add it to the [App](../app.py) file.

```python
from step_functions_agent.agent_x_stack import AgentXStack

app = cdk.App()

# Add the agent flow to the stack
agent_x_flow = AgentXStack(app, "AgentXStack")
```

## Deployment

The deployment to the AWS account is done using the following command:

```bash
cdk list
cdk deploy AgentXStack #(or --all)
```
