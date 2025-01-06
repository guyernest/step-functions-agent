# Python Example: Code Interpreter Tools

This directory contains the implementation of the tools for Code Interpreter AI Agent in **Python**, based on the MCP implementation in https://github.com/modelcontextprotocol/servers/tree/main/src/code-interpreter.

## Folder structure

```txt
code-interpreter/
├── index.py
├── requirements.in
├── requirements.txt
└── README.md
```

## Tool list

The tools are:

* `execute_code`: Execute code and return the result.

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
            case "code_interpreter":
                code = tool_input.get('code')
                result = code_interpret(code)
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
            "tool_use_id": tool_use["id"],
            "content": result
        }
        
    except Exception as e:
        logger.exception("Error executing code")
        return {
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": str(e)
        }
```

## API Key

Tools often need to make requests to external APIs, such as Google Maps API. This requires an API key. Although it is possible to use environment variables to store the API key, it is recommended to use a Secrets Manager to store the API key. The secrets are stored from the main CDK stack that reads the local various API keys from an .env file.

The following code snippet shows how to initialize the API key.

```python
# Global API key
try:
    E2B_API_KEY = json.loads(parameters.get_secret("/ai-agent/E2B_API_KEY"))["E2B_API_KEY"]
except ValueError:
    E2B_API_KEY = parameters.get_secret("/ai-agent/E2B_API_KEY")

