# Go Example: Web Research Tools using Perplexity

This directory contains the implementation of the tools for Web Research AI Agent in **Go**, using Perplexity.

## Folder structure

```txt
web-research/
├── main.go
├── main_test.go
├── Makefile
├── mod.go 
├── template.yaml  (for SAM local testing)
└── README.md
```

## Tool list

The tools are:

* `calculate_moving_average`: calculate moving average of a large set of time series.
* `calculate_volatility`: calculate volatility of a large set of time series.

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```go

type ToolEvent struct {
    Id string `json:"id"`
    Input ToolInput `json:"input"`
    Name string `json:"name"`
    Type string `json:"type"`    
}

type ToolInput struct {
    Url string `json:"url"`
    MaxDepth int `json:"max_depth"`
    MaxPages int `json:"max_pages"`
    MaxLinks int `json:"max_links"`
}

type ToolOutput struct {
    Type string `json:"type"`
    ToolUseId string `json:"tool_use_id"`
    Content string `json:"content"`
}

func handleRequest(event ToolEvent) (ToolOutput, error) {
    ...
    return ToolOutput{
        Type: "tool_result",
        ToolUseId: event.Id,
        Content: result,
    }, nil  
}
```

The tools return the output as a JSON object, with the result in the `content` field as a string.

```go
        try {
            var result string
            switch event.Name {
            case "calculate_moving_average":
                result = calculateMovingAverage(event.Input)
                break
            case "calculate_volatility":
                result = calculateVolatility(event.Input)
                break
            default:
                result = fmt.Sprintf("no such tool %s", event.Name)
}
        ...
        return ToolOutput{
            Type: "tool_result",
            ToolUseId: event.Id,
            Content: result,
        }, nil  
}
```

## API Key

Tools often need to make requests to external APIs, such as Google Maps API. This requires an API key. Although it is possible to use environment variables to store the API key, it is recommended to use a Secrets Manager to store the API key. The secrets are stored from the main CDK stack that reads the local various API keys from an .env file.

The following code snippet shows how to initialize the API key.

```go



```

## Setup

To set up the project, run:
```bash
# Create a new Go module
go mod init web-research
# Install dependencies
go get github.com/aws/aws-lambda-go/events
go get github.com/aws/aws-sdk-go-v2/config
go get github.com/aws/aws-sdk-go-v2/service/secretsmanager
go get github.com/aws/aws-sdk-go/aws
go get github.com/sgaunet/perplexity-go
```

## Building 

To build the Lambda function, run 

```bash
sam build
``` 

in the root directory of the lambda tool (lambda/tools/web-research). 

## Testing

```bash
go test -v 
```

You can test it locally using [AWS SAM](https://docs.aws.amazon.com/lambda/latest/dg/sam-cli-local.html) by running 

```bash
sam local invoke WebResearchFunction -e events/test_event.json
```

## Deployment

The deployment is done using a CDK stack, which is implemented in the [step_functions_analysis_agent_stack.py](../../../step_functions_sql_agent/step_functions_research_agent_stack.py) file.

```python
    research_lambda = _lambda_go.GoFunction(
        self, 
        "ResearchLambda",
        function_name="ResearchTools",
        description="Stock market stock research tools using Go and Perplexity.",
        entry="lambda/tools/web-research/", 
        runtime=_lambda.Runtime.PROVIDED_AL2023,
        architecture=_lambda.Architecture.ARM_64,
        timeout=Duration.seconds(120),
        role=research_lambda_role
    )
```