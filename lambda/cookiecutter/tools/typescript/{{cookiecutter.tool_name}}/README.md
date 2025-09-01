# TypeScript Tool: {{cookiecutter.tool_name}}

![TypeScript Logo](https://cdn.simpleicons.org/typescript?size=48)

This directory contains the implementation of the tools {{cookiecutter.tool_name}} in **TypeScript**.

## Folder structure

```txt
{{cookiecutter.tool_name}}/
├── src/
│   └── index.ts
│   └── local-test.ts
├── tests/
│   ├── test-event.json (single test event)
│   └── test-events.json (multiple test scenarios)
├── package.json
├── tsconfig.json
├── template.yaml (for SAM CLI)
└── README.md (This file)
```

## Tool list

The tools are:

* `{{cookiecutter.tool_name}}`: {{cookiecutter.tool_description}}.

## Building

To build the TypeScript code, run the following command:

```bash
npm install
npm run build
```

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

To test the Lambda function locally, run the following command:

```bash
npm run test
```

or using SAM CLI:

```bash
sam build
sam local invoke {{cookiecutter.tool_name}} --event tests/test-event.json
```

## Deployment

The deployment can be done using the AWS CDK or the AWS SAM CLI.

### CDK

The CDK stack is defined with the rest of the AI Agent definition to allow full application deployment. Here is the function and tools definitions in the [CDK Stack](../../step_functions_agent/step_functions_graphql_agent_stack.py).

```python

from aws_cdk import (
    ...
    aws_lambda as _lambda,
    aws_lambda_nodejs as nodejs_lambda,
)
...
    ## {{cookiecutter.tool_name}} Tool in Typescript
    # TypeScript Lambda
    {{cookiecutter.tool_name}}_lambda = nodejs_lambda.NodejsFunction(
        self, 
        "{{cookiecutter.tool_name}}Lambda",
        function_name="{{cookiecutter.tool_name}}",
        description="{{cookiecutter.tool_description}}.",
        timeout=Duration.seconds(30),
        entry="lambda/tools/{{cookiecutter.tool_name}}/src/index.ts", 
        handler="handler",  # Name of the exported function
        runtime=_lambda.Runtime.NODEJS_18_X,
        architecture=_lambda.Architecture.ARM_64,
        # Optional: Bundle settings
        bundling=nodejs_lambda.BundlingOptions(
            minify=True,
            source_map=True,
        ),
        role={{cookiecutter.tool_name}}_lambda_role
    )

    # Create graphql tools
    {{cookiecutter.tool_name}}_tools = [
        Tool(
            "{{cookiecutter.tool_name}}",
            "{{cookiecutter.tool_description}}.",
            {{cookiecutter.tool_name}}_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "{{cookiecutter.input_param_name}}": {
                        "type": "string",
                        "description": "{{cookiecutter.input_param_description}}."
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
from step_functions_agent.step_functions_{{cookiecutter.tool_name}}_agent_stack import {{cookiecutter.tool_name}}AgentStack
{{cookiecutter.tool_name}}AgentStack = {{cookiecutter.tool_name}}AgentStack(app, "{{cookiecutter.tool_name}}AgentStack")
```

Finally, you can deploy the stack using the following command:

```bash
cdk deploy {{cookiecutter.tool_name}}AgentStack
```
