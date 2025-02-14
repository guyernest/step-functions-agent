# TypeScript Tool: EarthQuakeQueryTS

![TypeScript Logo](https://cdn.simpleicons.org/typescript?size=48)

This directory contains the implementation of the tools EarthQuakeQueryTS in **TypeScript**.

## Folder structure

```txt
EarthQuakeQueryTS/
├── src/
│   └── index.ts
|   └── local-test.ts
├── tests/
│   └── test-event.json
├── package.json
├── tsconfig.json
├── template.yaml (for SAM CLI)
└── README.md (This file)
```

## Tool list

The tools are:

* `EarthQuakeQueryTS`: Query interface to the USGS Earthquake Catalog API.

## Building

To build the TypeScript code, run the following command:

```bash
npm install
npm run build
```

## Testing

To test the Lambda function locally, run the following command:

```bash
npm run test
```

or using SAM CLI:

```bash
sam build
sam local invoke EarthQuakeQueryTS --event tests/test-event.json
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
    ## EarthQuakeQueryTS Tool in Typescript
    # TypeScript Lambda
    EarthQuakeQueryTS_lambda = nodejs_lambda.NodejsFunction(
        self, 
        "EarthQuakeQueryTSLambda",
        function_name="EarthQuakeQueryTS",
        description="Query interface to the USGS Earthquake Catalog API.",
        timeout=Duration.seconds(30),
        entry="lambda/tools/EarthQuakeQueryTS/src/index.ts", 
        handler="handler",  # Name of the exported function
        runtime=_lambda.Runtime.NODEJS_18_X,
        architecture=_lambda.Architecture.ARM_64,
        # Optional: Bundle settings
        bundling=nodejs_lambda.BundlingOptions(
            minify=True,
            source_map=True,
        ),
        role=EarthQuakeQueryTS_lambda_role
    )

    # Create graphql tools
    EarthQuakeQueryTS_tools = [
        Tool(
            "EarthQuakeQueryTS",
            "Query interface to the USGS Earthquake Catalog API.",
            EarthQuakeQueryTS_lambda_function,
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "The start date of the query in YYYY-MM-DD format."
                    }
                },
                "required": [
                    "start_date",
                ]
            }
        )
    ]  # type: list[Tool]
```

Then you can add the stack the main CDK stack (`app.py`) that defines the AI Agent application.

```python
from step_functions_agent.step_functions_EarthQuakeQueryTS_agent_stack import EarthQuakeQueryTSAgentStack
EarthQuakeQueryTSAgentStack = EarthQuakeQueryTSAgentStack(app, "EarthQuakeQueryTSAgentStack")
```

Finally, you can deploy the stack using the following command:

```bash
cdk deploy EarthQuakeQueryTSAgentStack
```
