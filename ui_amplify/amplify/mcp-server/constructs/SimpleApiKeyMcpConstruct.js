import { Construct } from "constructs";
import { Duration, Stack } from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as lambda from "aws-cdk-lib/aws-lambda";
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
    mcpServerFunction;
    constructor(scope, id, props) {
        super(scope, id);
        // Create the main MCP server Lambda function (Rust)
        this.mcpServerFunction = new lambda.Function(this, `${props.projectName}-mcp-server-function`, {
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
                AWS_ACCOUNT_ID: Stack.of(this).account,
                // GraphQL endpoint will be set after creation
                GRAPHQL_ENDPOINT: props.graphqlApi.attrGraphQlUrl || "", // Note: capital Q in GraphQl
                // API key will be passed from request headers
                RUST_LOG: "info",
                RUST_BACKTRACE: "1",
            },
            description: "Rust MCP server with API key authentication for Step Functions agents",
        });
        // Create HTTP API integration
        const mcpIntegration = new HttpLambdaIntegration(`${props.projectName}-mcp-integration`, this.mcpServerFunction);
        // Add MCP routes to HTTP API Gateway
        // Main MCP endpoint (handles all MCP protocol requests)
        // Authentication is handled by passing API key to GraphQL
        props.httpApi.addRoutes({
            path: "/mcp",
            methods: [
                apigateway.HttpMethod.POST,
                apigateway.HttpMethod.OPTIONS,
            ],
            integration: mcpIntegration,
        });
        // Health check endpoint - NOT PROTECTED (useful for monitoring)
        props.httpApi.addRoutes({
            path: "/health",
            methods: [
                apigateway.HttpMethod.GET,
                apigateway.HttpMethod.OPTIONS,
            ],
            integration: mcpIntegration,
            // No authorizer - health check is public
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
        // Ensure GraphQL endpoint is set
        // The attribute name uses capital Q: attrGraphQlUrl
        const graphqlUrl = props.graphqlApi.attrGraphQlUrl;
        if (graphqlUrl) {
            this.mcpServerFunction.addEnvironment("GRAPHQL_ENDPOINT", graphqlUrl);
        }
    }
}
