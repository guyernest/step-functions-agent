# Python Tool: MicrosoftGraphAPI

![Python Logo](https://cdn.simpleicons.org/python?size=48) 

This directory contains the implementation of the tools MicrosoftGraphAPI in **Python**.

## Folder structure

```txt
MicrosoftGraphAPI/
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

* `MicrosoftGraphAPI`: Interface to the Microsoft Graph API of a specific tenant..

## Setup

You should update the `requirements.in` file with the dependencies of the tool (for example, `requests`).

To setup the tool, you need to compile the dependencies using the following command:

```bash
uv pip compile requirements.in --output-file requirements.txt
```

The `requirements.txt` file is used to install the dependencies in the Lambda function by the SAM CLI and the CDK.

## Accessing the Microsoft Graph API

The tool uses the Microsoft Graph API to access the data. You need to create an app in the Azure portal and get the client ID and client secret. You can find more information in the [Microsoft Graph API documentation](https://docs.microsoft.com/en-us/graph/auth-v2-service).
You should store the client ID and client secret in the `.env` file as follows:

```text
TENANT_ID=your_tenant_id
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

The CDK stack will pass the secrets to the Lambda function through the secrets manager.

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
sam local invoke MicrosoftGraphAPI --event tests/test-event.json
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
            "MicrosoftGraphAPI",
            "Interface to the Microsoft Graph API of a specific tenant.",
            graphql_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The API query to perform.",
                    }
                },
                "required": [
                    "query",
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
