# Executing AI Agents in AWS Step Functions

## AI Agent Overview

AI Agents are a combination of LLMs and Tools. Each tool can perform a specific task, and the LLM can use them to perform complex tasks, requested by the user. AI Agents are a powerful tool for automating complex tasks in the cloud, and they are a great way to reduce the cost of building and maintaining complex systems. However, the deployment and operation of AI Agents can be a complex process. 

This repository provides a simple implementation of AI Agents in AWS Step Functions, which is a serverless computing platform for building and deploying serverless applications. The repository contains the implementation of an SQL Agent, which can analyze a SQL database with multiple tables, and answer business questions about the data, including visualization and reporting. The implementation should be used as a template for building a custom AI Agent for any specific use case.

You can read more in [this blog post](https://medium.com/@guyernest/building-scalable-ai-agents-with-aws-step-functions-a-practical-guide-1e4f6dd19764).

### Step Functions Graph for SQL AI Agent:
<img src="images/agent_stepfunctions_graph.svg" width="100%"/>


## MLOps of AI Agents

There are a few frameworks for MLOps of AI Agents, such as: LangGraph, Crew.ai, Pydanic AI, etc. There are also some cloud platforms that can be used to build and deploy AI Agents, such as Amazon Bedrock, Google Vertex AI, and Azure OpenAI. There are cons and pros for each of these frameworks and platforms. The proposed implementation of AI Agents in AWS Step Functions is solving most of the problems with the existing frameworks and platforms.

## AI Agent Implementation

The AI Agent implementation in AWS Step Functions is based on the following steps:

1. Develop Lambda functions which are the tools for the AI Agent. These functions can be used to perform complex tasks, such as calling APIs, querying databases, etc.
2. Develop Lambda function which calls your preferred LLM for the AI Agent. 
3. Create a Step Function which orchestrate the AI Agent. This Step Function calls the LLM and passes the results to the tools.

This repository contains an example of some tools that are used to build a SQL Agent. Each Lambda function is implemented under the `lambda` directory. The `CDK` stack integrates all the Lambda functions into the Step Function flow to build the AI Agent.

Please note that each Lambda function is implemented in a dedicated directory and has its own requirements.txt file. The requirements.txt file is used to install the required Python packages for the Lambda function, by the `CDK` stack.

## Pre-requisites

1. uv (https://github.com/astral-sh/uv)
2. AWS CLI (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. AWS CDK (https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)

## Building Tools

Each tool is implemented using a Lambda function in a dedicated directory, and has its own requirements.txt file. The requirements.txt file is used to install the required Python packages for the tool, by the `CDK` stack.

A tool should know how to parse the tool input, and return the tool output. The tool input is passed to the tool as a JSON object, and the tool output is returned as a JSON object. For example, the following [Lambda function](lambda/db-interface/index.py) implements two tools: `get_db_schema` and `execute_sql_query`:

```python
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event

    db = SQLDatabase(db_name)

    # Once the db is ready, execute the requested method on the db
    if tool_use['name'] == 'get_db_schema':
        result = db.get_db_schema()
    elif tool_use['name'] == 'execute_sql_query':        
        # The SQL provided might cause ad error. We need to return the error message to the LLM
        # so it can fix the SQL and try again.
        try:
            result = db.execute_sql_query(tool_use['input']['sql_query'])
        except sqlite3.OperationalError as e:
            result = {
                'error': str(e)
            }
```

The output of this Lambda function is a JSON object, which is passed to the LLM as the tool output.

```python
return {
      "type": "tool_result",
      "tool_use_id": tool_use["id"],
      "content": result
}
```

## Building the LLM caller

The LLM caller is implemented using a Lambda function. The LLM caller is called by the `CDK` stack, and it calls the LLM API, with the tools option ("function calling"), and returns the LLM response. Please note that the code below (and in [this repo implementation](lambda/call-llm/index.py)) is the format for [Claude](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) models from Anthropic. However, the tool usage is very similar to other LLM, such as [OpenAI](https://platform.openai.com/docs/guides/function-calling), FAIR [Llama]([https](https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/prompt_format.md#json-based-tool-calling)], Amazon [Nova](https://docs.aws.amazon.com/nova/latest/userguide/prompting-tools-function.html), etc.

```python
ANTHROPIC_API_KEY = json.loads(parameters.get_secret("/ai-agent/ANTHROPIC_API_KEY"))["ANTHROPIC_API_KEY"]
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def lambda_handler(event, context):
    # Get system, messages, and model from event
    system = event.get('system')
    messages = event.get('messages')
    tools = event.get('tools', [])
    
    try:
        response = anthropic_client.messages.create(
            system = system,
            model=model,
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        assistant_message = convert_claude_message_to_json(response)

        # Update messages to include Claude's response
        messages.append(assistant_message["message"])

        return {
            'statusCode': 200,
            'body': {
                'messages': messages,
                'metadata' : assistant_message["metadata"]
            }
        }
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
```

## Building the AI Agent Step Function

Once we have the LLM caller, and the tools, we can build the AI Agent Step Function, which is implemented in the `CDK` stack, using the  [stack definition](step_functions_sql_agent/step_functions_sql_agent_stack.py). The stack uses a local construct that reads a [template](step-functions/agent-with-tools-flow-template.json) of the Amazon Step Functions Language (ASL) to create the AI Agent Step Functions Flow. The construct is implemented in the [ai_agent_construct_from_json.py](step_functions_sql_agent/ai_agent_construct_from_json.py) file.

Please note that the template is needed, instead of the CDK constructs for Step Functions, because current constructs for Step Functions do not support JSONata, which is needed to simplify the AI Agent implementation.

### Defining the tools

In the CDK stack we define the tools by following the following steps:

1. Define the IAM role for the Lambda function.

```python
    tool_1_role = iam.Role(
        self, "ToolRole",
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
    )
    # Add relevant permissions to the tool role, such as SSM and Secrets Manager access
    tool_1_role.add_to_policy(
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
```

2. Create the Lambda function.

```python
        # Create the tool lambda function
        tool_1_lambda_function = _lambda_python.PythonFunction(
            self, "Tool1Lambda",
            function_name="Tool1Lambda",
            entry="lambda/tool1",
            runtime=_lambda.Runtime.PYTHON_3_12,
            # analyze using aws-lambda-power-tuning to find the best memory size
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            role=tool_1_role,
        )
```

3. Add the Lambda function as tool for the AI Agent.

```python
# Create test tools
        tools = [
            Tool(
                "get_db_schema", 
                "Describe the schema of the SQLite database, including table names, and column names and types.",
                tool_1_lambda_function
            ),
            Tool(
                "execute_sql_query", 
                "Return the query results of the given SQL query to the SQLite database.",
                tool_2_lambda_function,
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
        ]
```

## Create the AI Agent Step Function.

```python
        agent_flow = ConfigurableStepFunctionsConstruct(
            self, 
            "AIStateMachine",
            region=self.region,
            account=self.account,
            state_machine_path="step-functions/agent-with-tools-flow-template.json", 
            llm_caller=call_llm_lambda_function, 
            provider=LLMProviderEnum.ANTHROPIC,
            tools=tools,
            system_prompt="You are an expert business analyst with deep knowledge of SQL and visualization code in Python. Your job is to help users understand and analyze their internal baseball data. You have access to a set of tools, but only use them when needed. You also have access to a tool that allows execution of python code. Use it to generate the visualizations in your analysis. - the python code runs in jupyter notebook. - every time you call `execute_python` tool, the python code is executed in a separate cell. it's okay to multiple calls to `execute_python`. - display visualizations using matplotlib directly in the notebook. don't worry about saving the visualizations to a file. - you can run any python code you want, everything is running in a secure sandbox environment.",
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

## Create a new tool

To create a new tool, you need to:
1. create a new Lambda function code in the `lambda` directory, 

```bash
mkdir lambda/tools/new-tool
touch lambda/tools/new-tool/index.py
```
2. create dependencies in the `requirements.txt` file,

```bash
touch lambda/tools/new-tool/requirements.in
echo "yfinance" >> lambda/tools/new-tool/requirements.in
uv pip compile lambda/tools/new-tool/requirements.in --output-file lambda/tools/new-tool/requirements.txt
```

3. add the Lambda function code to the stack,

```python
        new_tool_lambda_role = iam.Role(
            self, "NewToolLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "NewToolLambdaPolicy",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        new_tool_lambda_function = _lambda_python.PythonFunction(
            self, "NewToolLambda",
            function_name="NewTool",
            entry="lambda/tools/new-tool",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=512,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=new_tool_lambda_role,
        )

```

4. create a new tool in the tools list for the AI Agent, 

```python
tools = [
        Tool(
            "new_tool", 
            "new tool description",
            new_tool_lambda_function,
            provider=LLMProviderEnum.ANTHROPIC
        )
    ]
```

## uv Set up

An easy way to deploy Lambda functions is to have a requirements.txt file in the same directory as the Lambda function (`index.py`, for example). Using `uv` is the great way to build that requirements.txt file, from the requirements.in file. For example:

```shell
uv venv
source .venv/bin/activate 
uv pip compile lambda/db-interface/requirements.in --output-file lambda/db-interface/requirements.txt 
```

The `CDK` stack will use Docker to build the Lambda functions, and it will use the requirements.txt file to install the required Python packages, into the format of zip file, and deploy it to the Cloud.

## Deploying the AI Agent Step Function using CDK

The CDK Stack defines all the necessary resources to deploy the AI Agent Step Function, including the IAM roles, Secrets Manager secrets (for API keys), Lambda functions (tools and LLM caller), and Step Functions.

```shell
cdk deploy
```