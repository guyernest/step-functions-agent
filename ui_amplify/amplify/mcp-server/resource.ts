import { Tags, RemovalPolicy } from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Duration } from "aws-cdk-lib";
import { Backend } from "@aws-amplify/backend";
import { CfnApiKey } from "aws-cdk-lib/aws-appsync";

import { SimpleApiKeyMcpConstruct } from "./constructs/SimpleApiKeyMcpConstruct";
import { McpConstructProps } from "./constructs/common-interfaces";

// Configuration constants
const ENVIRONMENT = "prod"; // Match the environment used by other stacks
const APPLICATION_NAME = "step-functions-agents";
const PROJECT_NAME = `${APPLICATION_NAME}-${ENVIRONMENT}`;

// Common tags for all resources
const COMMON_TAGS = {
  Environment: ENVIRONMENT,
  Application: APPLICATION_NAME,
  Project: PROJECT_NAME,
  ManagedBy: "Amplify-Gen2",
  Purpose: "MCP-Server-with-API-Key-Authentication",
  Template: "step-functions-agents-mcp",
};

/**
 * Creates MCP server resources with simple API key authentication
 * This function is called from backend.ts after auth and data resources are created
 */
export function createMcpServerResources(backend: Backend<{ auth: any; data: any }>) {
  const mcpServerStack = backend.createStack(`${PROJECT_NAME}-mcp-stack`);

  // Apply common tags to the entire stack
  Object.entries(COMMON_TAGS).forEach(([key, value]) => {
    Tags.of(mcpServerStack).add(key, value);
  });

  // Get references to existing Amplify resources
  const userPool = backend.auth.resources.userPool;
  const userPoolClient = backend.auth.resources.userPoolClient;
  const graphqlApi = backend.data.resources.cfnResources.cfnGraphqlApi;
  
  // Create an API key for the GraphQL API
  const apiKey = new CfnApiKey(mcpServerStack, 'GraphQLApiKey', {
    apiId: graphqlApi.attrApiId,
    description: 'API key for MCP server to access GraphQL API',
    expires: Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60, // 30 days from now
  });

  // Create CloudWatch log groups
  const mcpServerLogGroup = new logs.LogGroup(
    mcpServerStack,
    `${PROJECT_NAME}-mcp-server-logs`,
    {
      logGroupName: `/aws/lambda/${PROJECT_NAME}-mcp-server`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    }
  );

  // Create DynamoDB table for API key management
  const apiKeyTable = new dynamodb.Table(
    mcpServerStack,
    `${PROJECT_NAME}-api-keys`,
    {
      tableName: `${PROJECT_NAME}-api-keys`,
      partitionKey: { name: "api_key_hash", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      removalPolicy: RemovalPolicy.DESTROY,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    }
  );

  // Add GSI for looking up keys by client_id
  apiKeyTable.addGlobalSecondaryIndex({
    indexName: "client-id-index",
    partitionKey: { name: "client_id", type: dynamodb.AttributeType.STRING },
  });

  // Create IAM role for Lambda functions
  const lambdaRole = new iam.Role(
    mcpServerStack,
    `${PROJECT_NAME}-lambda-role`,
    {
      roleName: `${PROJECT_NAME}-mcp-lambda-role`,
      description: `Lambda execution role for ${PROJECT_NAME} MCP server`,
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole"
        ),
      ],
    }
  );

  // Add permissions for DynamoDB
  apiKeyTable.grantReadWriteData(lambdaRole);

  // Add permissions for CloudWatch Logs and Metrics
  lambdaRole.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
      ],
      resources: ["arn:aws:logs:*:*:*"],
    })
  );

  // Add permissions for AppSync GraphQL API calls
  lambdaRole.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "appsync:GraphQL",
      ],
      resources: [`${graphqlApi.attrArn}/*`],
    })
  );

  // Add permissions for Step Functions execution (needed for agent execution)
  lambdaRole.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:ListExecutions",
        "states:DescribeStateMachine",
      ],
      resources: ["*"], // Will be restricted to specific state machines
    })
  );

  // Add permissions for DynamoDB reads (for agent and tool registries)
  lambdaRole.addToPolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
      ],
      resources: [
        "arn:aws:dynamodb:*:*:table/AgentRegistry-*",
        "arn:aws:dynamodb:*:*:table/ToolRegistry-*",
        "arn:aws:dynamodb:*:*:table/*agent-registry*",
        "arn:aws:dynamodb:*:*:table/*tool-registry*",
      ],
    })
  );

  // Create HTTP API Gateway
  const httpApi = new apigateway.HttpApi(mcpServerStack, `${PROJECT_NAME}-api`, {
    apiName: `${PROJECT_NAME}-mcp-api`,
    description: `API Gateway for ${PROJECT_NAME} MCP server with API key auth`,
    corsPreflight: {
      allowHeaders: ["*"],
      allowMethods: [apigateway.CorsHttpMethod.ANY],
      allowOrigins: ["*"],
      allowCredentials: false,
      maxAge: Duration.hours(1),
    },
  });

  // Prepare construct props
  const constructProps: McpConstructProps = {
    projectName: PROJECT_NAME,
    environment: ENVIRONMENT,
    applicationName: APPLICATION_NAME,
    userPool,
    userPoolClient,
    graphqlApi,
    mcpServerLogGroup,
    lambdaRole,
    httpApi,
  };

  // Create MCP server infrastructure using simple API key construct
  const mcpConstruct = new SimpleApiKeyMcpConstruct(
    mcpServerStack,
    `${PROJECT_NAME}-mcp-construct`,
    constructProps
  );

  // Get API URL for outputs
  const apiUrl: string = httpApi.url!.replace(/\/$/, "");

  // Export important values using backend.addOutput
  backend.addOutput({
    custom: {
      // Primary endpoints
      mcpServerEndpoint: `${apiUrl}/mcp`,
      healthCheckEndpoint: `${apiUrl}/health`,

      // Resource information
      environment: ENVIRONMENT,
      applicationName: APPLICATION_NAME,
      projectName: PROJECT_NAME,

      // AWS resource names for reference
      lambdaFunctions: {
        mcpServer: `${PROJECT_NAME}-mcp-server`,
      },


      logGroups: {
        mcpServer: mcpServerLogGroup.logGroupName,
      },

      // API Gateway information
      apiGatewayUrl: apiUrl,
      apiGatewayId: httpApi.httpApiId,
    },
  });

  return {
    httpApi,
    mcpConstruct,
    mcpServerLogGroup,
  };
}