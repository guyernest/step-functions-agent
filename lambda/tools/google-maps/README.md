# ![TypeScript Logo](https://cdn.simpleicons.org/typescript?size=48) TypeScript Example: Google Maps Tools

This directory contains the implementation of the tools for Google Maps AI Agent in **TypeScript**, based on the MCP implementation in [this MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps).

The AI Agent that is created using these tools is implemented in the [step_functions_googlemap_agent_stack.py](../../../step_functions_sql_agent/step_functions_googlemap_agent_stack.py) file.

![Google Maps Agent Step Functions](../../../images/GoogleMaps-agent-step-functions.svg)

## Folder structure

```txt
google-maps/
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

* `maps_geocode`: Geocode an address into geographic coordinates.
* `maps_reverse_geocode`: Reverse geocode coordinates into an address.
* `maps_search_places`: Search for places using Google Places API.
* `maps_place_details`: Get detailed information about a specific place.
* `maps_distance_matrix`: Calculate travel distance and time for multiple origins and destinations.
* `maps_elevation`: Get elevation data for locations on the earth.
* `maps_directions`: Get directions between two points.

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```typescript
export const handler: Handler = async (event, context) => {

    logger.info("Received event", { event });
    const tool_use = event
    const tool_name = tool_use["name"]
    const tool_input = tool_use["input"]

    try {
        let result: string
        switch (tool_name) {
          case "maps_geocode": {
            const { address } = tool_input as { address: string }
            result = await handleGeocode(address);
            break;
          }
          ...
          default: {
            result = `Unknown tool name: ${tool_name}`;
          }
        }
```

The tools return the output as a JSON object, with the result in the `content` field as a string.

```typescript
        ...
        logger.info("Result", { result });
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        }
      } catch (error) {
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": `Error: ${error instanceof Error ? error.message : String(error)}`
        }
      }
```

## API Key

Tools often need to make requests to external APIs, such as Google Maps API. This requires an API key. Although it is possible to use environment variables to store the API key, it is recommended to use a Secrets Manager to store the API key. The secrets are stored from the main CDK stack that reads the local various API keys from an .env file.

The following code snippet shows how to initialize the API key.

```typescript
// Global API key
let GOOGLE_MAPS_API_KEY: string;

async function initializeApiKey(): Promise<void> {
    try {
        const apiKeySecret = await getSecret("/ai-agent/api-keys");
        if (!apiKeySecret) {
            throw new Error("Failed to retrieve secret from Secrets Manager");
        }
        GOOGLE_MAPS_API_KEY = JSON.parse(apiKeySecret.toString())["GOOGLE_MAPS_API_KEY"];
        logger.info("API key initialized successfully");
    } catch (error) {
        logger.error('Failed to initialize API key', { error });
        throw error;
    }
}
```

The initializeApiKey function is called from the main Lambda handler.

```typescript
export const handler: Handler = async (event, context) => {
    ...
    // Initialize API key if not already set
    if (!GOOGLE_MAPS_API_KEY) {
        await initializeApiKey();
    }
    ...
}
```

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
sam local invoke GoogleMapsLambda --event tests/test-event.json
```

## Deployment

### Using CDK

```python

from aws_cdk import (
    ...
    aws_lambda as _lambda,
    aws_lambda_nodejs as nodejs_lambda,
)

       ## Google Maps Tools in Typescript
        # TypeScript Lambda
        google_maps_lambda = nodejs_lambda.NodejsFunction(
            self, 
            "GoogleMapsLambda",
            function_name="GoogleMaps",
            description="Lambda function to execute Google Maps API calls.",
            timeout=Duration.seconds(30),
            entry="lambda/tools/google-maps/src/index.ts", 
            handler="handler",  # Name of the exported function
            runtime=_lambda.Runtime.NODEJS_18_X,
            architecture=_lambda.Architecture.ARM_64,
            # Optional: Bundle settings
            bundling=nodejs_lambda.BundlingOptions(
                minify=True,
                source_map=True,
            ),
            role=google_maps_lambda_role
        )
```
