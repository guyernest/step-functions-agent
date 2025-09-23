# GraphQL Agent Setup Guide

## Overview

The GraphQL Agent now supports dynamic endpoint selection, allowing you to work with multiple GraphQL APIs through a single agent. Each endpoint is identified by a unique ID (e.g., 'LogisticZ', 'CustomerService').

## Features

- **Dynamic Endpoint Selection**: Connect to different GraphQL APIs by specifying an endpoint ID
- **Schema Introspection**: Fetch and analyze GraphQL schemas
- **Query Generation**: Generate GraphQL queries based on schema and requirements
- **Query Execution**: Execute GraphQL queries with variable support

## Tool Configuration

### Available Tools

1. **get_graphql_schema**
   - Fetches the GraphQL schema for a specific endpoint
   - Parameters:
     - `graphql_id` (required): Endpoint identifier

2. **generate_query_prompt**
   - Generates a prompt template for creating GraphQL queries
   - Parameters:
     - `graphql_id` (required): Endpoint identifier
     - `description` (required): Description of the query to generate

3. **execute_graphql_query**
   - Executes a GraphQL query against a specific endpoint
   - Parameters:
     - `graphql_id` (required): Endpoint identifier
     - `graphql_query` (required): The GraphQL query to execute
     - `variables` (optional): Query variables as JSON object

## Configuring GraphQL Endpoints

GraphQL endpoints are configured through the CDK deployment process and stored in the consolidated tool secrets at `/ai-agent/tool-secrets/{env_name}`. There are two ways to configure endpoints:

### Secret Structure

```json
{
  "graphql-interface": {
    "LogisticZ": {
      "endpoint": "https://logisticz-api.example.com/graphql",
      "api_key": "your-api-key-here",
      "headers": {
        "X-Custom-Header": "CustomValue"
      }
    },
    "CustomerService": {
      "endpoint": "https://customer-api.example.com/graphql",
      "api_key": "another-api-key"
    },
    "InternalAPI": {
      "endpoint": "https://internal.company.com/graphql",
      "api_key": "internal-key",
      "headers": {
        "Authorization": "Bearer token-here"
      }
    }
  }
}
```

### Configuration Methods

#### Method 1: Configuration File (Recommended)

1. Create a `.env.graphql-endpoints` file in the project root:
```bash
cp .env.graphql-endpoints.example .env.graphql-endpoints
```

2. Edit the file with your GraphQL endpoints:
```json
{
  "LogisticZ": {
    "endpoint": "https://your-logisticz-api.com/graphql",
    "api_key": "your-api-key-here"
  },
  "CustomerService": {
    "endpoint": "https://your-customer-api.com/graphql",
    "api_key": "your-api-key-here"
  }
}
```

3. Deploy the stack - it will automatically read the configuration:
```bash
cdk deploy GraphQLInterfaceToolStack-prod
```

#### Method 2: Environment Variables

Set environment variables before deployment:
```bash
export GRAPHQL_LOGISTICZ_ENDPOINT="https://your-api.com/graphql"
export GRAPHQL_LOGISTICZ_API_KEY="your-api-key"
export GRAPHQL_CUSTOMER_ENDPOINT="https://customer.com/graphql"
export GRAPHQL_CUSTOMER_API_KEY="customer-api-key"

cdk deploy GraphQLInterfaceToolStack-prod
```

### Configuration Fields

- **endpoint** (required): The GraphQL API endpoint URL
- **api_key** (optional): API key for authentication (sent as `x-api-key` header)
- **headers** (optional): Additional headers to include in requests

## Deployment

### 1. Deploy the GraphQL Tool Stack

```bash
# Deploy the GraphQL tool stack
cdk deploy GraphQLInterfaceToolStack-prod
```

### 2. Deploy the GraphQL Agent Stack

```bash
# Deploy the GraphQL agent stack
cdk deploy GraphQLAgentStack-prod
```

### 3. Verify Configuration

After deployment, verify your GraphQL endpoints are properly configured:

```bash
# View the consolidated secrets
aws secretsmanager get-secret-value \
  --secret-id /ai-agent/tool-secrets/prod \
  --query SecretString \
  --output text | jq '.["graphql-interface"]'
```

To update endpoints after deployment, simply modify your `.env.graphql-endpoints` file and redeploy:

```bash
cdk deploy GraphQLInterfaceToolStack-prod
```

## Usage Examples

### Example 1: Fetching a Schema

```
User: Get the GraphQL schema for LogisticZ

Agent: I'll fetch the GraphQL schema for the LogisticZ endpoint.

[Uses get_graphql_schema with graphql_id="LogisticZ"]
```

### Example 2: Generating and Executing a Query

```
User: Query the CustomerService GraphQL API to get all customers with their recent orders

Agent: I'll help you query the CustomerService GraphQL API. Let me first fetch the schema and then generate an appropriate query.

[Uses get_graphql_schema with graphql_id="CustomerService"]
[Uses generate_query_prompt with graphql_id="CustomerService" and description]
[Uses execute_graphql_query with graphql_id="CustomerService" and the generated query]
```

### Example 3: Executing a Specific Query

```
User: Execute this query on LogisticZ:
query GetShipments($status: String) {
  shipments(status: $status) {
    id
    trackingNumber
    status
  }
}

With variables: {"status": "IN_TRANSIT"}

Agent: I'll execute this query on the LogisticZ GraphQL endpoint.

[Uses execute_graphql_query with graphql_id="LogisticZ", query, and variables]
```

## Testing

Run the test script to verify the GraphQL tool functionality:

```bash
cd lambda/tools/graphql-interface
python test_dynamic_endpoints.py
```

## Troubleshooting

### Common Issues

1. **"GraphQL configuration not found for ID: X"**
   - The specified graphql_id is not configured in tool secrets
   - Check available IDs in the error message
   - Update tool secrets to add the missing endpoint

2. **Connection errors**
   - Verify the endpoint URL is correct
   - Check API key and authentication headers
   - Ensure the Lambda function has network access to the endpoint

3. **Schema fetch failures**
   - Some GraphQL endpoints may not support introspection
   - Check if the endpoint requires special headers for introspection
   - Verify authentication is configured correctly

## Security Considerations

- API keys and sensitive headers are stored securely in AWS Secrets Manager
- The Lambda function only has access to the consolidated secret
- Each GraphQL endpoint configuration is isolated
- Consider using AWS PrivateLink for internal APIs

## Future Enhancements

- Support for GraphQL subscriptions
- Caching of schemas for improved performance
- Automatic retry logic with exponential backoff
- Support for OAuth2 authentication flows
- Query cost analysis and optimization