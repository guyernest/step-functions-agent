# TypeScript Example: Google Maps Tools

This directory contains the implementation of the tools for Google Maps AI Agent in **TypeScript**, based on the MCP implementation in https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps.

## Folder structure

```txt
google-maps/
├── src/
│   └── index.ts
├── package.json
├── tsconfig.json
└── README.md
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
            "tool_use_id": tool_use["id"],
            "content": result
        }
      } catch (error) {
        return {
            "type": "tool_result",
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
        const apiKeySecret = await getSecret("/ai-agent/GOOGLE_MAPS_API_KEY");
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
