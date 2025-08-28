# Authentication Architecture

## Table of Contents
- [Current Authentication Setup](#current-authentication-setup)
- [Authentication Options Analysis](#authentication-options-analysis)
- [API Key Implementation](#api-key-implementation)
- [OAuth 2.0 Integration](#oauth-20-integration)
- [Security Best Practices](#security-best-practices)
- [Implementation Roadmap](#implementation-roadmap)
- [Monitoring and Audit](#monitoring-and-audit)

## Current Authentication Setup

### Existing Infrastructure

The Step Functions Agent Framework currently uses AWS Amplify with Cognito for authentication:

```typescript
// Current GraphQL Configuration
export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'userPool',  // Cognito User Pool
    apiKeyAuthorizationMode: {
      expiresInDays: 30,  // API Key support configured but not enabled
    },
  },
});
```

### Authentication Flow

```
User/Client
     ↓
[Cognito User Pool]
     ↓
[ID Token / Access Token]
     ↓
[AppSync GraphQL API]
     ↓
[Lambda Functions]
     ↓
[Step Functions]
```

### Current Limitations

1. **All operations require Cognito authentication**
   - Every GraphQL operation uses `allow.authenticated()`
   - No public or API key access enabled

2. **No machine-to-machine auth**
   - Designed for UI users, not automation
   - OAuth client credentials not configured

3. **Token management complexity**
   - Requires token refresh logic
   - Complex for n8n integration

## Authentication Options Analysis

### Comparison Matrix

| Method | Setup Complexity | User Experience | Security | Maintenance | Use Case |
|--------|-----------------|-----------------|----------|-------------|----------|
| **API Keys** | Low | Simple | Medium | Low | Automation, n8n |
| **OAuth 2.0 (Client Credentials)** | Medium | Complex | High | Medium | Enterprise M2M |
| **Cognito JWT** | High | Complex | High | High | UI Users |
| **Service Accounts** | Medium | Simple | High | Medium | Dedicated Services |
| **mTLS** | High | Complex | Very High | High | High Security |

### Recommended Approach: Hybrid Model

Implement multiple authentication methods for different use cases:

1. **Cognito JWT**: UI users (existing)
2. **API Keys**: n8n and automation (new)
3. **OAuth 2.0**: Future enterprise integrations (optional)

## API Key Implementation

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   API Gateway                        │
├─────────────────────────────────────────────────────┤
│           API Key Validation Lambda                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Generate    │  │   Validate   │  │  Rotate  │ │
│  │   API Key    │  │   API Key    │  │  API Key │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│         ↓                  ↓                ↓       │
│  ┌────────────────────────────────────────────┐    │
│  │         DynamoDB / Parameter Store          │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### GraphQL Schema Modifications

```typescript
// amplify/data/resource.ts

// Step 1: Enable API key auth for specific operations
const mcpOperations = {
  // Queries
  listAvailableAgents: a
    .query()
    .authorization((allow) => [
      allow.authenticated(),  // UI users
      allow.apiKey()          // n8n/MCP
    ]),
  
  getExecutionStatus: a
    .query()
    .arguments({ executionId: a.string().required() })
    .authorization((allow) => [
      allow.authenticated(),
      allow.apiKey()
    ]),

  // Mutations  
  startAgentExecution: a
    .mutation()
    .arguments({
      agentName: a.string().required(),
      input: a.json().required()
    })
    .authorization((allow) => [
      allow.authenticated(),
      allow.apiKey()
    ]),

  // Protected operations (UI only)
  updateAgentConfiguration: a
    .mutation()
    .authorization((allow) => [
      allow.authenticated()  // No API key access
    ])
};
```

### API Key Management System

```typescript
// lambda/api-key-manager/index.ts

import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { SSMClient, PutParameterCommand } from '@aws-sdk/client-ssm';
import crypto from 'crypto';

export class APIKeyManager {
  private dynamodb: DynamoDBClient;
  private ssm: SSMClient;
  
  constructor() {
    this.dynamodb = new DynamoDBClient({});
    this.ssm = new SSMClient({});
  }

  /**
   * Generate a new API key with metadata
   */
  async generateAPIKey(params: {
    userId: string;
    description: string;
    permissions: string[];
    expiresInDays?: number;
  }): Promise<APIKeyResult> {
    // Generate cryptographically secure key
    const apiKey = this.generateSecureKey();
    const apiKeyHash = this.hashKey(apiKey);
    
    // Store metadata in DynamoDB
    const metadata = {
      api_key_hash: apiKeyHash,
      user_id: params.userId,
      description: params.description,
      permissions: params.permissions,
      created_at: new Date().toISOString(),
      expires_at: this.calculateExpiry(params.expiresInDays || 90),
      last_used: null,
      usage_count: 0,
      status: 'active'
    };
    
    await this.saveKeyMetadata(metadata);
    
    // Store the actual key in Parameter Store (encrypted)
    await this.ssm.send(new PutParameterCommand({
      Name: `/api-keys/${apiKeyHash}`,
      Value: JSON.stringify({
        key: apiKey,
        metadata: metadata
      }),
      Type: 'SecureString',
      Overwrite: false
    }));
    
    // Return the key (only shown once)
    return {
      apiKey: apiKey,
      apiKeyId: apiKeyHash.substring(0, 8),
      expiresAt: metadata.expires_at,
      permissions: params.permissions
    };
  }

  /**
   * Validate an API key
   */
  async validateAPIKey(apiKey: string): Promise<ValidationResult> {
    const apiKeyHash = this.hashKey(apiKey);
    
    // Check cache first (implement Redis/ElastiCache for production)
    const cached = await this.checkCache(apiKeyHash);
    if (cached) {
      return cached;
    }
    
    // Lookup in DynamoDB
    const metadata = await this.getKeyMetadata(apiKeyHash);
    
    if (!metadata) {
      return { valid: false, error: 'Invalid API key' };
    }
    
    // Check expiration
    if (new Date(metadata.expires_at) < new Date()) {
      return { valid: false, error: 'API key expired' };
    }
    
    // Check status
    if (metadata.status !== 'active') {
      return { valid: false, error: `API key ${metadata.status}` };
    }
    
    // Update usage statistics
    await this.updateUsageStats(apiKeyHash);
    
    // Cache the result
    await this.cacheResult(apiKeyHash, metadata);
    
    return {
      valid: true,
      userId: metadata.user_id,
      permissions: metadata.permissions
    };
  }

  /**
   * Rotate an API key
   */
  async rotateAPIKey(oldApiKey: string): Promise<RotationResult> {
    const oldKeyHash = this.hashKey(oldApiKey);
    const metadata = await this.getKeyMetadata(oldKeyHash);
    
    if (!metadata) {
      throw new Error('API key not found');
    }
    
    // Generate new key with same permissions
    const newKey = await this.generateAPIKey({
      userId: metadata.user_id,
      description: `Rotated from ${oldKeyHash.substring(0, 8)}`,
      permissions: metadata.permissions,
      expiresInDays: 90
    });
    
    // Mark old key for deletion (grace period)
    await this.updateKeyStatus(oldKeyHash, 'rotating', 7);
    
    return {
      newApiKey: newKey.apiKey,
      oldApiKeyId: oldKeyHash.substring(0, 8),
      gracePeriodDays: 7
    };
  }

  /**
   * List all API keys for a user
   */
  async listAPIKeys(userId: string): Promise<APIKeyInfo[]> {
    const keys = await this.queryKeysByUser(userId);
    
    return keys.map(key => ({
      apiKeyId: key.api_key_hash.substring(0, 8),
      description: key.description,
      createdAt: key.created_at,
      expiresAt: key.expires_at,
      lastUsed: key.last_used,
      usageCount: key.usage_count,
      status: key.status,
      permissions: key.permissions
    }));
  }

  /**
   * Revoke an API key
   */
  async revokeAPIKey(apiKeyId: string): Promise<void> {
    await this.updateKeyStatus(apiKeyId, 'revoked');
    await this.invalidateCache(apiKeyId);
  }

  // Helper methods
  private generateSecureKey(): string {
    // Format: sfaf_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    const prefix = 'sfaf_live_';
    const randomBytes = crypto.randomBytes(32);
    const key = randomBytes.toString('base64url');
    return `${prefix}${key}`;
  }

  private hashKey(apiKey: string): string {
    return crypto
      .createHash('sha256')
      .update(apiKey)
      .digest('hex');
  }

  private calculateExpiry(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date.toISOString();
  }
}
```

### API Key UI Component

```tsx
// ui_amplify/src/components/APIKeyManagement.tsx

import React, { useState } from 'react';
import { generateClient } from 'aws-amplify/api';

export const APIKeyManagement: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [showNewKey, setShowNewKey] = useState<string | null>(null);
  const client = generateClient();

  const generateNewKey = async () => {
    const response = await client.mutations.generateAPIKey({
      description: 'n8n Integration',
      permissions: ['execute_agents', 'view_results']
    });

    setShowNewKey(response.apiKey);
    await loadAPIKeys();
  };

  const rotateKey = async (apiKeyId: string) => {
    const response = await client.mutations.rotateAPIKey({ apiKeyId });
    setShowNewKey(response.newApiKey);
    await loadAPIKeys();
  };

  const revokeKey = async (apiKeyId: string) => {
    if (confirm('Are you sure you want to revoke this API key?')) {
      await client.mutations.revokeAPIKey({ apiKeyId });
      await loadAPIKeys();
    }
  };

  return (
    <div className="api-key-management">
      <h2>API Keys</h2>
      
      {showNewKey && (
        <div className="alert alert-warning">
          <h3>New API Key Generated</h3>
          <p>Copy this key now - it won't be shown again!</p>
          <code>{showNewKey}</code>
          <button onClick={() => navigator.clipboard.writeText(showNewKey)}>
            Copy to Clipboard
          </button>
        </div>
      )}

      <button onClick={generateNewKey}>Generate New API Key</button>

      <table>
        <thead>
          <tr>
            <th>Key ID</th>
            <th>Description</th>
            <th>Created</th>
            <th>Expires</th>
            <th>Last Used</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {apiKeys.map(key => (
            <tr key={key.apiKeyId}>
              <td>{key.apiKeyId}</td>
              <td>{key.description}</td>
              <td>{new Date(key.createdAt).toLocaleDateString()}</td>
              <td>{new Date(key.expiresAt).toLocaleDateString()}</td>
              <td>{key.lastUsed || 'Never'}</td>
              <td>{key.status}</td>
              <td>
                <button onClick={() => rotateKey(key.apiKeyId)}>Rotate</button>
                <button onClick={() => revokeKey(key.apiKeyId)}>Revoke</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

## OAuth 2.0 Integration

### Cognito Configuration for M2M

```typescript
// cdk/cognito-stack.ts

import * as cognito from 'aws-cdk-lib/aws-cognito';

export class CognitoM2MStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: 'step-functions-agents',
      // ... existing configuration
    });

    // Add resource server for M2M
    const resourceServer = userPool.addResourceServer('AgentResourceServer', {
      identifier: 'agents',
      scopes: [
        {
          scopeName: 'execute',
          scopeDescription: 'Execute agents'
        },
        {
          scopeName: 'read',
          scopeDescription: 'Read execution results'
        },
        {
          scopeName: 'admin',
          scopeDescription: 'Administrative operations'
        }
      ]
    });

    // Create app client for M2M
    const m2mClient = userPool.addClient('M2MClient', {
      generateSecret: true,
      authFlows: {
        custom: false,
        userPassword: false,
        userSrp: false,
        adminUserPassword: false
      },
      oAuth: {
        flows: {
          clientCredentials: true,  // Enable M2M flow
          authorizationCodeGrant: false,
          implicitCodeGrant: false
        },
        scopes: [
          cognito.OAuthScope.custom('agents/execute'),
          cognito.OAuthScope.custom('agents/read')
        ]
      }
    });
  }
}
```

### OAuth Token Validation

```typescript
// lambda/oauth-validator/index.ts

import jwt from 'jsonwebtoken';
import jwksRsa from 'jwks-rsa';

export class OAuthValidator {
  private jwksClient: jwksRsa.JwksClient;
  
  constructor(private cognitoIssuer: string) {
    this.jwksClient = jwksRsa({
      jwksUri: `${cognitoIssuer}/.well-known/jwks.json`,
      cache: true,
      cacheMaxAge: 600000, // 10 minutes
      rateLimit: true,
      jwksRequestsPerMinute: 10
    });
  }

  async validateToken(token: string): Promise<TokenValidation> {
    try {
      // Decode token header to get kid
      const decoded = jwt.decode(token, { complete: true });
      if (!decoded) {
        return { valid: false, error: 'Invalid token format' };
      }

      // Get signing key
      const key = await this.getSigningKey(decoded.header.kid);
      
      // Verify token
      const verified = jwt.verify(token, key, {
        issuer: this.cognitoIssuer,
        algorithms: ['RS256']
      }) as any;

      // Check token type (access token for M2M)
      if (verified.token_use !== 'access') {
        return { valid: false, error: 'Invalid token type' };
      }

      // Extract scopes
      const scopes = verified.scope ? verified.scope.split(' ') : [];

      return {
        valid: true,
        clientId: verified.client_id,
        scopes: scopes,
        expiresAt: verified.exp
      };

    } catch (error) {
      return {
        valid: false,
        error: error.message
      };
    }
  }

  private async getSigningKey(kid: string): Promise<string> {
    const key = await this.jwksClient.getSigningKey(kid);
    return key.getPublicKey();
  }
}
```

## Security Best Practices

### 1. Key Storage

```yaml
# Best Practices for API Key Storage
Storage Locations:
  Secrets:
    - AWS Secrets Manager for production keys
    - Parameter Store with encryption for development
    - Never in environment variables or code

Encryption:
  - Always use SecureString type in Parameter Store
  - Enable automatic rotation in Secrets Manager
  - Use KMS customer-managed keys for sensitive data

Access Control:
  - Least privilege IAM policies
  - Separate read/write permissions
  - Audit access with CloudTrail
```

### 2. Rate Limiting

```typescript
// lambda/rate-limiter/index.ts

export class RateLimiter {
  private limits = {
    'execute_agents': { requests: 100, window: 60 },  // 100 req/min
    'view_results': { requests: 1000, window: 60 },    // 1000 req/min
    'admin': { requests: 10, window: 60 }              // 10 req/min
  };

  async checkLimit(
    apiKeyHash: string, 
    operation: string
  ): Promise<RateLimitResult> {
    const limit = this.limits[operation] || { requests: 60, window: 60 };
    const key = `rate:${apiKeyHash}:${operation}`;
    
    // Use Redis/ElastiCache for distributed rate limiting
    const current = await redis.incr(key);
    
    if (current === 1) {
      await redis.expire(key, limit.window);
    }
    
    if (current > limit.requests) {
      return {
        allowed: false,
        limit: limit.requests,
        remaining: 0,
        resetAt: await redis.ttl(key)
      };
    }
    
    return {
      allowed: true,
      limit: limit.requests,
      remaining: limit.requests - current,
      resetAt: await redis.ttl(key)
    };
  }
}
```

### 3. Audit Logging

```typescript
// lambda/audit-logger/index.ts

export class AuditLogger {
  async logAPIUsage(event: APIUsageEvent): Promise<void> {
    const auditEntry = {
      timestamp: new Date().toISOString(),
      apiKeyHash: this.hashPartial(event.apiKey),
      userId: event.userId,
      operation: event.operation,
      resource: event.resource,
      result: event.result,
      sourceIp: event.sourceIp,
      userAgent: event.userAgent,
      requestId: event.requestId,
      latency: event.latency
    };

    // Write to CloudWatch Logs
    console.log(JSON.stringify(auditEntry));

    // Write to DynamoDB for long-term storage
    await dynamodb.putItem({
      TableName: 'APIAuditLog',
      Item: {
        ...auditEntry,
        ttl: Math.floor(Date.now() / 1000) + (90 * 24 * 60 * 60) // 90 days
      }
    });

    // Send metrics to CloudWatch
    await cloudwatch.putMetricData({
      Namespace: 'API/Usage',
      MetricData: [{
        MetricName: 'APICallCount',
        Value: 1,
        Unit: 'Count',
        Dimensions: [
          { Name: 'Operation', Value: event.operation },
          { Name: 'Result', Value: event.result }
        ]
      }]
    });
  }

  private hashPartial(apiKey: string): string {
    // Store only partial hash for security
    const hash = crypto.createHash('sha256').update(apiKey).digest('hex');
    return hash.substring(0, 8);
  }
}
```

### 4. Security Headers

```typescript
// lambda/security-headers/index.ts

export const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': "default-src 'self'",
  'X-API-Version': '1.0',
  'Cache-Control': 'no-store, no-cache, must-revalidate',
  'Pragma': 'no-cache'
};
```

### 5. Input Validation

```typescript
// lambda/input-validator/index.ts

import Ajv from 'ajv';

export class InputValidator {
  private ajv: Ajv;
  
  constructor() {
    this.ajv = new Ajv({
      allErrors: true,
      coerceTypes: false,
      useDefaults: true
    });
  }

  validateAgentInput(input: any): ValidationResult {
    const schema = {
      type: 'object',
      properties: {
        agent_name: {
          type: 'string',
          pattern: '^[a-z0-9-]+$',
          minLength: 3,
          maxLength: 50
        },
        input_message: {
          type: 'string',
          minLength: 1,
          maxLength: 10000
        },
        parameters: {
          type: 'object'
        }
      },
      required: ['agent_name', 'input_message'],
      additionalProperties: false
    };

    const validate = this.ajv.compile(schema);
    const valid = validate(input);

    if (!valid) {
      return {
        valid: false,
        errors: validate.errors
      };
    }

    // Additional security checks
    if (this.containsSQLInjection(input.input_message)) {
      return {
        valid: false,
        errors: [{ message: 'Potential SQL injection detected' }]
      };
    }

    return { valid: true };
  }

  private containsSQLInjection(input: string): boolean {
    const patterns = [
      /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)/gi,
      /(--|;|\/\*|\*\/|xp_|sp_|0x)/gi,
      /(\bUNION\b.*\bSELECT\b)/gi
    ];

    return patterns.some(pattern => pattern.test(input));
  }
}
```

## Implementation Roadmap

### Phase 1: API Key Support (Week 1)
- [ ] Modify GraphQL schema to allow API key auth
- [ ] Create API key management Lambda
- [ ] Build DynamoDB tables for key storage
- [ ] Implement key generation UI

### Phase 2: Validation & Security (Week 2)
- [ ] Implement rate limiting
- [ ] Add audit logging
- [ ] Create key rotation mechanism
- [ ] Add input validation

### Phase 3: OAuth 2.0 Support (Week 3)
- [ ] Configure Cognito for M2M
- [ ] Implement token validation
- [ ] Add scope-based permissions
- [ ] Test with n8n OAuth flow

### Phase 4: Monitoring & Operations (Week 4)
- [ ] Create CloudWatch dashboards
- [ ] Set up alarms for suspicious activity
- [ ] Implement key usage analytics
- [ ] Document operational procedures

## Monitoring and Audit

### CloudWatch Dashboard Configuration

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "API Key Usage",
        "metrics": [
          ["API/Usage", "APICallCount", {"stat": "Sum"}],
          [".", ".", {"stat": "Average"}]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Authentication Methods",
        "metrics": [
          ["API/Auth", "Method", {"stat": "Sum", "dimensions": {"Method": "APIKey"}}],
          [".", ".", {"stat": "Sum", "dimensions": {"Method": "OAuth"}}],
          [".", ".", {"stat": "Sum", "dimensions": {"Method": "Cognito"}}]
        ],
        "period": 3600
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Rate Limit Violations",
        "metrics": [
          ["API/RateLimit", "Violations", {"stat": "Sum"}]
        ],
        "period": 60
      }
    },
    {
      "type": "log",
      "properties": {
        "title": "Recent API Activity",
        "query": "SOURCE '/aws/lambda/api-key-validator' | fields @timestamp, apiKeyHash, operation, result | sort @timestamp desc | limit 20",
        "region": "us-east-1"
      }
    }
  ]
}
```

### Alerting Rules

```yaml
# cloudwatch-alarms.yaml
HighAPIKeyUsage:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: APICallCount
    Namespace: API/Usage
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 1000
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SNSTopic

SuspiciousActivity:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: FailedAuthentications
    Namespace: API/Auth
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SecurityTeamTopic

ExpiredKeyUsage:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: ExpiredKeyAttempts
    Namespace: API/Auth
    Statistic: Sum
    Period: 3600
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
```

### Audit Query Examples

```sql
-- Find most active API keys
SELECT 
  api_key_hash,
  COUNT(*) as usage_count,
  COUNT(DISTINCT operation) as unique_operations,
  MIN(timestamp) as first_use,
  MAX(timestamp) as last_use
FROM api_audit_log
WHERE timestamp > NOW() - INTERVAL 7 DAY
GROUP BY api_key_hash
ORDER BY usage_count DESC
LIMIT 10;

-- Detect potential abuse
SELECT 
  source_ip,
  COUNT(DISTINCT api_key_hash) as unique_keys,
  COUNT(*) as total_requests
FROM api_audit_log  
WHERE timestamp > NOW() - INTERVAL 1 HOUR
GROUP BY source_ip
HAVING unique_keys > 5 OR total_requests > 1000;

-- Track error rates
SELECT
  DATE_TRUNC('hour', timestamp) as hour,
  operation,
  SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as successes,
  SUM(CASE WHEN result = 'error' THEN 1 ELSE 0 END) as errors,
  AVG(latency) as avg_latency
FROM api_audit_log
WHERE timestamp > NOW() - INTERVAL 24 HOUR
GROUP BY hour, operation
ORDER BY hour DESC;
```

## Conclusion

The hybrid authentication approach provides flexibility for different use cases:

1. **UI Users**: Continue using Cognito JWT authentication
2. **n8n/Automation**: Use API keys for simplicity
3. **Enterprise**: OAuth 2.0 client credentials for standards compliance

This architecture ensures:
- Security through multiple layers of validation
- Scalability with caching and rate limiting
- Observability through comprehensive logging
- Maintainability with clear separation of concerns

Next steps:
1. Implement API key support for immediate n8n integration
2. Add OAuth 2.0 for future enterprise needs
3. Deploy monitoring and alerting
4. Document for end users