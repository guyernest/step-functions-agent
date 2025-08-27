import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
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
  graphqlApiKey?: any; // AppSync API Key reference
  mcpServerLogGroup: logs.LogGroup;
  apiKeyTable: dynamodb.Table;
  lambdaRole: iam.Role;
  httpApi: apigateway.HttpApi;
}

/**
 * API Key structure for DynamoDB storage
 */
export interface ApiKeyRecord {
  api_key_hash: string; // PK - SHA256 hash of the API key
  client_id: string; // GSI - Client identifier for lookup
  client_name: string; // Human readable name
  created_at: string; // ISO timestamp
  expires_at: string; // ISO timestamp
  last_used?: string; // ISO timestamp
  is_active: boolean;
  permissions: string[]; // Array of allowed operations
  usage_count: number;
  created_by: string; // User who created the key
  metadata?: Record<string, any>; // Additional metadata
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