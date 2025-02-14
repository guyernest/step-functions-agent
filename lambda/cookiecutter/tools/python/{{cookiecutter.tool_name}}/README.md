# Python Tool: {{cookiecutter.tool_name}}

![Python Logo](https://cdn.simpleicons.org/python?size=48) 

This directory contains the implementation of the tools {{cookiecutter.tool_name}} in **Python**.

## Folder structure

```txt
{{cookiecutter.tool_name}}/
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

* `{{cookiecutter.tool_name}}`: {{cookiecutter.tool_description}}.

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
sam local invoke {{cookiecutter.tool_name}} --event tests/test-query-event.json
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
            "{{cookiecutter.tool_name}}",
            "{{cookiecutter.tool_description}}.",
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
