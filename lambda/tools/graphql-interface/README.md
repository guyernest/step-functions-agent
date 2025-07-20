# ![Python Logo](https://cdn.simpleicons.org/python?size=48) Python Example: GraphQL AI Agent Tools

This directory contains the implementation of the tools for GraphQL AI Agent in **Python**.

## Folder structure

```txt
graphql-interface/
├── index.py
├── requirements.in
├── requirements.txt
├── tests/
│   ├── __init__.py
│   ├── test_tool.py
|   └── requirements-test.txt
├── template.yaml (AWS SAM template)
|── .env (API keys)
└── README.md (this file)
```

## Tool list

The tools are:

* `generate_query_prompt`: generate a query prompt for the GraphQL API based on the API schema and the user's request.
* `execute_graphql_query`: execute a query on the GraphQL API and return the results.

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```python
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use.get('name')
    tool_input = tool_use.get('input')

    try:
        match tool_name:
            case "generate_query_prompt":
                code = tool_input.get('api_schema')
                result = generate_query_prompt(code)
                ...
            case "execute_graphql_query":
                code = tool_input.get('graphql_query')
                result = execute_graphql_query(code)
                ...
            case _:
                result = f"Unknown tool: {tool_name}"
```

The tools return the output as a JSON object, with the result in the `content` field as a string.

```python
        ...
        logger.info("Code execution finished", extra={"result": result})
        # Return the execution results
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        }
        
    except Exception as e:
        logger.exception("Error executing code")
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": str(e)
        }
```

## API Key

The following code snippet shows how to initialize the API key, that are stored in the AWS Secrets Manager and parameter store by the CDK stack from the `.env` file. The API key is used to authenticate the API calls to the external services.

```python
# Global API key
GRAPHQL_API_KEY = json.loads(parameters.get_secret("/ai-agent/graphql-tool/keys"))["GRAPHQL_API_KEY"]
GRAPHQL_ENDPOINT = parameters.get_parameter("/ai-agent/graphql-tool/graphql-endpoint")
```

## Testing

You can test the tool using Pytest as other Python code, or using the AWS SAM CLI to test the Lambda function locally.

### Pytest

The tests are defined in the `tests/` directory. You can run the tests using the following command:

```bash
pytest tests/
```

### AWS SAM CLI

The AWS Function is defined in the `template.yaml` file. You can test the Lambda function locally using the AWS SAM CLI. The following command will invoke the Lambda function locally using the `tests/event.json` file as the input event:

```bash
sam build
sam local invoke GraphQLToolLambda --event tests/test-query-event.json
```

### Test event with AWS EventBridge

You can add a scheduled rule in AWS EventBridge to test the Lambda function with a real event. The test can run every day and notify you in case of failure. You can define the rule in the CDK stack or using the AWS CLI.

```python
    # Adding test event to the lambda function in EventBridge
    graphql_function_test_event = events.Rule(
        self,
        "GraphQLFunctionTestEvent",
        rule_name="GraphQLFunctionTestEvent",
        description="Test event for the GraphQL Lambda function",
        schedule=events.Schedule.rate(Duration.days(1)),
        targets=[
            targets.LambdaFunction(
                handler=graphql_lambda_function,
                event=events.RuleTargetInput.from_object(
                    {
                        "id": "unique_tool_use_id",
                        "input": {
                            "graphql_query": "query test { organization { name } }"
                        },
                        "name": "execute_graphql_query",
                        "type": "tool_use"
                    }
                )
            )
        ]
    )
```

## Deployment

The deployment can be done using the AWS CDK or the AWS SAM CLI.

### CDK

The CDK stack is defined with the rest of the AI Agent definition to allow full application deployment. Here is the function and tools definitions in the [CDK Stack](../../step_functions_agent/step_functions_graphql_agent_stack.py).

```python
    # Define the Lambda function
    graphql_lambda_function = _lambda_python.PythonFunction(
        self, 
        "GraphQLToolLambdaFunction",
        function_name="GraphQLToolLambdaFunction",
        description="Explore and query a GraphQL API.",
        entry="lambda/tools/graphql-interface",
        runtime=_lambda.Runtime.PYTHON_3_12,
        timeout=Duration.seconds(90),
        memory_size=128,
        index="index.py",
        handler="lambda_handler",
        architecture=_lambda.Architecture.ARM_64,
        log_retention=logs.RetentionDays.ONE_WEEK,
        role=graphql_lambda_role,
    )

    # Create graphql tools
    graphql_tools = [
        Tool(
            "generate_query_prompt",
            "Generate the prompt for a GraphQL query, including the API schema and query examples.",
            graphql_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The question of the user to be answered."
                    }
                },
                "required": [
                    "description",
                ]
            }
        ),
        Tool(
            "execute_graphql_query",
            "Execute a GraphQL query to allow retrival of relevant policies from the GraphQL API.",
            graphql_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "graphql_query": {
                        "type": "string",
                        "description": "The GraphQL query to execute."
                    }
                },
                "required": [
                    "gql_query"
                ]
            }
        )
    ]  # type: list[Tool]
```

Then you can add the stack the main CDK stack (`app.py`) that defines the AI Agent application.

```python
from step_functions_agent.step_functions_graphql_agent_stack import GraphQLAgentStack
graphqlAgentStack = GraphQLAgentStack(app, "GraphQLAgentStack")
```

Finally, you can deploy the stack using the following command:

```bash
cdk deploy GraphQLAgentStack
```