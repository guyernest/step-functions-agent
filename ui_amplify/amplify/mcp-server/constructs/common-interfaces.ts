import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as logs from "aws-cdk-lib/aws-logs";

/**
 * Common properties for MCP constructs
 */
export interface McpConstructProps {
  projectName: string;
  environment: string;
  applicationName: string;
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  graphqlApi: any; // AppSync GraphQL API reference
  mcpServerLogGroup: logs.LogGroup;
  lambdaRole: iam.Role;
  httpApi: apigateway.HttpApi;
}

/**
 * MCP Tool definition for the server
 */
export interface McpTool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, any>;
    required?: string[];
  };
}

/**
 * MCP Server response structure
 */
export interface McpResponse {
  content?: Array<{
    type: "text";
    text: string;
  }>;
  isError?: boolean;
}

/**
 * Available MCP operations
 */
export enum McpOperation {
  LIST_TOOLS = "tools/list",
  CALL_TOOL = "tools/call",
  INITIALIZE = "initialize",
  PING = "ping",
}

/**
 * Agent execution request structure
 */
export interface AgentExecutionRequest {
  agent_name: string;
  input_message: string;
  parameters?: Record<string, any>;
  execution_name?: string;
}

/**
 * Agent execution response structure
 */
export interface AgentExecutionResponse {
  execution_id: string;
  status: string;
  execution_arn?: string;
  estimated_time?: number;
}