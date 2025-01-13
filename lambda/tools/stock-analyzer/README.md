# ![Java Logo](https://img.icons8.com/?size=48&id=13679&format=png&color=000000) Java Example: Time Series Tools

This directory contains the implementation of the tools for time series analysis AI Agent in **Java**, using Fork/Join Framework.

## Folder structure

```txt
stock-analyzer/
├── src/
│   ├── main
│   │   └── java
│   │       └── tools
│   │           └── StockAnalyzerLambda.java
│   └── test
│       └── java
│           └── tools
│               └── InvokeTest.java
├── pom.xml   (for Maven)
├── template.yaml  (for SAM local testing)
└── README.md
```

## Tool list

The tools are:

* `calculate_moving_average`: calculate moving average of a large set of time series.
* `calculate_volatility`: calculate volatility of a large set of time series.

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```java

    // Input Classes (with some verbosity)
    public static class ToolEvent {
        @JsonProperty("id")
        private String id;

        @JsonProperty("input")
        private ToolInput input;

        @JsonProperty("name")
        private String name;

        @JsonProperty("type")
        private String type;

        public String getId() { return id; }

        public void setId(String id) { this.id = id; }

        public ToolInput getInput() { return input; }

        public void setInput(ToolInput input) { this.input = input; }

        public String getName() { return name; }

        public void setName(String name) {  this.name = name; }

        public String getType() { return type; }

        public void setType(String type) {  this.type = type; }
    }

    public static class ToolInput {
        @JsonProperty("bucket")
        private String bucket;

        @JsonProperty("key")
        private String key;

        public String getBucket() { return bucket; }

        public void setBucket(String bucket) { this.bucket = bucket; }

        public String getKey() { return key; }

        public void setKey(String key) { this.key = key; }
    }


public Map<String, String> handleRequest(ToolEvent event, Context context) {
        try {
            String result = "";
            switch (event.getName()) {
                case "calculate_moving_average":
                    result = calculateMovingAverage(event.getInput());
                    break;
                case "calculate_volatility":
                    result = calculateVolatility(event.getInput());
                    break;
                default:
                    result = String.format("no such tool %s", event.getName());
            }
```

The tools return the output as a JSON object, with the result in the `content` field as a string.

```java
        ...
            Map<String, String> response = new HashMap<>();
            response.put("type", "tool_result");
            response.put("tool_use_id", event.getId());
            response.put("content", result);
            
            return response;
            
        } catch (Exception e) {
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("type", "tool_result");
            errorResponse.put("tool_use_id", event.getId());
            errorResponse.put("content", String.format("error executing tool %s: %s", event.getName(), e.getMessage()));
            return errorResponse;
        }
```

## API Key

Tools often need to make requests to external APIs, such as Google Maps API. This requires an API key. Although it is possible to use environment variables to store the API key, it is recommended to use a Secrets Manager to store the API key. The secrets are stored from the main CDK stack that reads the local various API keys from an .env file.

The following code snippet shows how to initialize the API key.

```java
import software.amazon.lambda.powertools.parameters.SecretsProvider;
import software.amazon.lambda.powertools.parameters.ParamManager;

    ...
    // Get an instance of the Secrets Provider
    SecretsProvider secretsProvider = ParamManager.getSecretsProvider();

    // Retrieve a single secret
    String value = secretsProvider.get("/ai-agent/OPENAI_API_KEY");
    ...
```

## Building 

To build the Lambda function, run 

```bash
mvn clean package
``` 

in the root directory of the lambda tool (lambda/tools/stock-analyzer). 

## Testing

You can test it locally using [AWS SAM](https://docs.aws.amazon.com/lambda/latest/dg/sam-cli-local.html) by running 

```bash
sam local invoke StockAnalyzerFunction -e events/test_event.json
```

## Deployment

The deployment is done using a CDK stack, which is implemented in the [step_functions_analysis_agent_stack.py](../../../step_functions_sql_agent/step_functions_analysis_agent_stack.py) file.

```python
analysis_lambda = _lambda.Function(
    self, 
    "AnalysisLambda",
    function_name="AnalysisTools",
    code=_lambda.Code.from_asset("lambda/tools/stock-analyzer/target/stock-analyzer-lambda-1.0-SNAPSHOT.jar"), 
    handler="tools.StockAnalyzerLambda::handleRequest",
    runtime=_lambda.Runtime.JAVA_17,
    architecture=_lambda.Architecture.ARM_64,
    role=analysis_lambda_role
)
```