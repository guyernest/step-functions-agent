import { Construct } from "constructs";
import { Duration, Stack } from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as lambda from "aws-cdk-lib/aws-lambda";

import { McpConstructProps } from "./common-interfaces";

/**
 * Simple API Key MCP Construct
 * 
 * This construct creates a lightweight MCP server that:
 * 1. Validates API keys against DynamoDB
 * 2. Provides MCP protocol endpoints
 * 3. Integrates with existing GraphQL API for agent execution
 * 4. Follows the MCP specification for tool listing and execution
 */
export class SimpleApiKeyMcpConstruct extends Construct {
  public readonly mcpServerFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: McpConstructProps) {
    super(scope, id);

    // Create the main MCP server Lambda function (Rust)
    this.mcpServerFunction = new lambda.Function(
      this,
      `${props.projectName}-mcp-server-function`,
      {
        functionName: `${props.projectName}-mcp-server`,
        runtime: lambda.Runtime.PROVIDED_AL2023,
        handler: "bootstrap",
        code: lambda.Code.fromAsset("./amplify/mcp-server/rust-mcp-server/.build/rust-mcp-server"),
        memorySize: 512,
        timeout: Duration.seconds(60), // Increased for Rust cold start
        role: props.lambdaRole,
        logGroup: props.mcpServerLogGroup,
        environment: {
          ENVIRONMENT: props.environment,
          APPLICATION_NAME: props.applicationName,
          API_KEY_TABLE_NAME: props.apiKeyTable.tableName,
          AWS_ACCOUNT_ID: Stack.of(this).account,
          // GraphQL endpoint will be set after creation
          GRAPHQL_ENDPOINT: props.graphqlApi.attrGraphQlUrl || "", // Note: capital Q in GraphQl
          // Use the API key from the created CfnApiKey
          GRAPHQL_API_KEY: props.graphqlApiKey?.attrApiKey || "",
          RUST_LOG: "info",
          RUST_BACKTRACE: "1",
        },
        description: "Rust MCP server with API key authentication for Step Functions agents",
      }
    );

    // Create HTTP API integration
    const mcpIntegration = new HttpLambdaIntegration(
      `${props.projectName}-mcp-integration`,
      this.mcpServerFunction
    );

    // Add MCP routes to HTTP API Gateway
    // Main MCP endpoint (handles all MCP protocol requests)
    props.httpApi.addRoutes({
      path: "/mcp",
      methods: [
        apigateway.HttpMethod.POST,
        apigateway.HttpMethod.OPTIONS,
      ],
      integration: mcpIntegration,
    });

    // Health check endpoint
    props.httpApi.addRoutes({
      path: "/health",
      methods: [
        apigateway.HttpMethod.GET,
        apigateway.HttpMethod.OPTIONS,
      ],
      integration: mcpIntegration,
    });

    // MCP-specific endpoints following the protocol
    props.httpApi.addRoutes({
      path: "/mcp/{proxy+}",
      methods: [
        apigateway.HttpMethod.POST,
        apigateway.HttpMethod.GET,
        apigateway.HttpMethod.OPTIONS,
      ],
      integration: mcpIntegration,
    });
    
    // Ensure GraphQL endpoint is set (similar to reference project)
    // The attribute name uses capital Q: attrGraphQlUrl
    const graphqlUrl = props.graphqlApi.attrGraphQlUrl;
    if (graphqlUrl) {
      this.mcpServerFunction.addEnvironment("GRAPHQL_ENDPOINT", graphqlUrl);
    }
    
    // Also ensure API key is properly set from the created key
    if (props.graphqlApiKey) {
      const apiKeyValue = props.graphqlApiKey.attrApiKey;
      console.log("Using created GraphQL API Key");
      this.mcpServerFunction.addEnvironment("GRAPHQL_API_KEY", apiKeyValue);
    } else {
      console.log("Warning: No API key provided to construct");
    }
  }
}