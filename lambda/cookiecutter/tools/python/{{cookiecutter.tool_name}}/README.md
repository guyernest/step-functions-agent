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
│   ├── test-event.json (single test event)
│   ├── test-events.json (multiple test scenarios)
│   └── requirements-test.txt
├── template.yaml (AWS SAM template)
├── .env (API keys)
└── README.md (this file)
```

## Tool list

The tools are:

{% for name in cookiecutter.tool_functions.functions_names %}
* `{{name}}`: {{cookiecutter.tool_description}}.
{% endfor %}

## Setup

You should update the `requirements.in` file with the dependencies of the tool (for example, `requests`).

To setup the tool, you need to compile the dependencies using the following command:

```bash
uv pip compile requirements.in --output-file requirements.txt
```

The `requirements.txt` file is used to install the dependencies in the Lambda function by the SAM CLI and the CDK.

## Test Events

This tool includes test events that can be used for automated health testing and validation. Test events are stored in:
- `tests/test-event.json` - Single test event for quick testing
- `tests/test-events.json` - Multiple test scenarios for comprehensive testing

### Test Events Format

The `tests/test-events.json` file should contain multiple test scenarios:

```json
{
  "smoke_test": {
    "description": "Basic functionality test",
    "input": {
      "{{cookiecutter.input_param_name}}": "{{cookiecutter.input_test_value}}"
    },
    "expected_output": {
      "validation_type": "contains",
      "value": "expected_substring"
    }
  },
  "edge_case_test": {
    "description": "Test with edge case input",
    "input": {
      "{{cookiecutter.input_param_name}}": ""
    },
    "expected_output": {
      "validation_type": "schema",
      "value": {"type": "object"}
    }
  }
}
```

These test events will be automatically discovered and made available in the management console for:
- Quick tool testing during development
- Automated health checks
- Regression testing

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
sam local invoke {{cookiecutter.tool_name}} --event tests/test-event.json
```

## Deployment

The deployment can be done using the AWS CDK or the AWS SAM CLI.

### CDK

The CDK stack is defined with the rest of the AI Agent definition to allow full application deployment. Here is the function and tools definitions in the [CDK Stack](../../step_functions_agent/step_functions_graphql_agent_stack.py).

```python
    # Define the Lambda function
    tool_lambda_function = _lambda_python.PythonFunction(
        self, 
        "{{cookiecutter.tool_name}}ToolLambdaFunction",
        function_name="{{cookiecutter.tool_name}}ToolLambdaFunction",
        description="{{cookiecutter.tool_description}}.",
        entry="lambda/tools/{{cookiecutter.tool_name}}",
        runtime=_lambda.Runtime.PYTHON_3_12,
        timeout=Duration.seconds(90),
        memory_size=128,
        index="index.py",
        handler="lambda_handler",
        architecture=_lambda.Architecture.ARM_64,
        log_retention=logs.RetentionDays.ONE_WEEK,
        role=tool_lambda_role,
    )

    # Create graphql tools
    tools = [
        Tool(
            "{{cookiecutter.tool_name}}",
            "{{cookiecutter.tool_description}}.",
            tool_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "{{cookiecutter.input_param_name}}": {
                        "type": "string",
                        "description": "{{cookiecutter.input_param_description}}.",
                    }
                },
                "required": [
                    "{{cookiecutter.input_param_name}}",
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
