# Tool Implementation in AWS Lambda Functions

This directory contains the implementation of the various lambda functions used tools for AI agents. The tools are implemented in various programming languages to demonstrate the flexibility of the agents, and allow each organization to use the language that best fits their needs.

## Multi-Language Support

Please note that each Lambda function is implemented in a dedicated directory and has its own dependencies file. The examples for the different programming languages are:

- ![Python Logo](https://cdn.simpleicons.org/python?size=16) Python: [code-interpreter](code-interpreter) - using [uv](https://github.com/astral-sh/uv) to build the requirements.txt file from the requirements.in file.
- ![TypeScript Logo](https://cdn.simpleicons.org/typescript?size=16) TypeScript: [google-maps](google-maps) - using tsconfig.json for dependencies.
- ![Rust logo](https://cdn.simpleicons.org/rust/gray?size=16) Rust: [rust-clustering](rust-clustering) - using Cargo.toml for dependencies.
- ![Java Logo](https://img.icons8.com/?size=16&id=13679&format=png&color=000000) Java: [stock-analyzer](stock-analyzer) - using Maven to build the jar based on the pom.xml.
- ![Go logo](https://cdn.simpleicons.org/go?size=16) Go: [web-research](web-research) - using mod.go for dependencies.

## Building Tools

Each tool is implemented using a Lambda function in a dedicated directory, and has its own requirements.txt file. The requirements.txt file is used to install the required Python packages for the tool, by the `CDK` stack.

A tool should know how to parse the tool input, and return the tool output. The tool input is passed to the tool as a JSON object, and the tool output is returned as a JSON object. For example, the following [Lambda function](db-interface/index.py) implements two tools: `get_db_schema` and `execute_sql_query`:

```python
def lambda_handler(event, context):
    # Get the tool name from the input event
    tool_use = event
    tool_name = tool_use['name']
    tool_input = tool_use['input']

    db = SQLDatabase(DB_NAME)

    # Once the db is ready, execute the requested method on the db
    match tool_name:
        case 'get_db_schema':
            result = db.get_db_schema()
        case 'execute_sql_query':
            # The SQL provided might cause ad error. We need to return the error message to the LLM
            # so it can fix the SQL and try again.
            try:
                result = db.execute_sql_query(tool_input['sql_query'])
            except sqlite3.OperationalError as e:
                result = json.dumps({
                    'error': str(e)
                })
        case _:
            result = json.dumps({
                'error': f"Unknown tool name: {tool_name}"
            })
```

The output of this Lambda function is a JSON object, which is passed to the LLM as the tool output.

```python
return {
      "type": "tool_result",
      "name": tool_name,
      "tool_use_id": tool_use["id"],
      "content": result
}
```

## Testing

### Unit Tests

Add a test file to the `tests` folder. The test file should contain the unit tests for the tool handler.

To run the unit tests, you can use the following command:

```bash
pytest tests/
```

### Testing using SAM CLI

1. Add a to the `template.yaml` file to define the Lambda function.

    ```yaml
    ...
    DBInterfaceToolLambda:
        Type: AWS::Serverless::Function
        Properties:
        CodeUri: lambda/tools
        Handler: db-interface.index.lambda_handler
        Runtime: python3.12
        Timeout: 90
        MemorySize: 256
        Environment:
            Variables:
            POWERTOOLS_SERVICE_NAME: ai-agents-tools
        Architectures:
            - arm64
        Policies:
            - SecretsManagerReadWrite
            - AWSLambdaBasicExecutionRole
    ```

1. Add a test event to the `events` folder.

    ```json
    {
        "name": "get_db_schema",
        "id": "execute_sql_query_unique_id",
        "input": {},
        "type": "tool_use"
    }
    ```

1. To test the Lambda function locally, you can use the following command:

    ```bash
    sam build
    sam local invoke DBInterfaceToolLambda -e events/db-interface-tool-event.json
    ```

## Deployment

Using CDK:

```python
        # Creating the tool  lambda function using PythonFunction (other languages can be used)
        tool_lambda_function_db_interface = _lambda_python.PythonFunction(
            self, 
            "ToolLambdaDBInterface",
            # Name of the Lambda function that will be used by the agents to find the function.
            function_name="ToolLambdaDBInterface", 
            description="SQL database interface Lambda function for AI agents tools.",
            entry="lambda/tools/db-interface",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(90),
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=db_interface_tool_lambda_role,
        )
```
