# Amplify Build Role IAM Policy for MCP Registration

## Overview

The Amplify build process needs permissions to write to the MCP Registry DynamoDB table during deployment to enable automatic registration of MCP servers. This document provides the IAM policy that needs to be attached to the Amplify build role.

## Finding the Amplify Build Role

1. Go to AWS Amplify Console
2. Select your app
3. Go to "App settings" > "Build settings"
4. Look for "Service role" - it will be named something like:
   - `AmplifySSRLoggingRole-{random-id}`
   - `amplifyconsole-backend-role`

## Required IAM Policy

Add this policy to the Amplify build role to enable MCP server registration:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/MCPServerRegistry-*",
        "arn:aws:dynamodb:*:*:table/MCPServerRegistry-*/index/*"
      ]
    }
  ]
}
```

## How to Apply the Policy

### Option 1: Using AWS Console

1. Go to IAM Console
2. Find the role (search for the role name from Amplify)
3. Click "Add permissions" > "Create inline policy"
4. Switch to JSON editor
5. Paste the policy above
6. Name it: `MCPRegistryAccess`
7. Create the policy

### Option 2: Using AWS CLI

```bash
# Replace ROLE_NAME with your actual Amplify role name
ROLE_NAME="AmplifySSRLoggingRole-YOUR-ID"

# Create the policy document
cat > mcp-registry-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/MCPServerRegistry-*",
        "arn:aws:dynamodb:*:*:table/MCPServerRegistry-*/index/*"
      ]
    }
  ]
}
EOF

# Attach the inline policy to the role
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name MCPRegistryAccess \
  --policy-document file://mcp-registry-policy.json
```

## Alternative: Manual Registration

If you prefer not to grant these permissions to the Amplify build role, the registration will fail gracefully and you can:

1. Use the "Environment Info" tab in the MCP Servers UI
2. Click "Register This Server" to manually register after deployment
3. Or use the AWS CLI/SDK to manually add the entry to DynamoDB

## Security Considerations

- The policy only grants access to MCP Registry tables (tables starting with `MCPServerRegistry-`)
- It only allows write operations needed for registration
- No delete permissions are granted
- The policy is scoped to prevent access to other DynamoDB tables

## Verification

After applying the policy:
1. Trigger a new Amplify deployment
2. Check the build logs for "✅ MCP Server registration completed successfully!"
3. Verify in the UI that the MCP server appears in the registry

## Troubleshooting

If registration still fails after adding the policy:

1. **Check the region**: Ensure the DynamoDB table exists in the same region as your Amplify app
2. **Check the table name**: Verify the table name matches the pattern `MCPServerRegistry-{environment}`
3. **Check CloudTrail**: Look for AccessDenied events to see what specific permission is missing
4. **Check the build logs**: The registration script now provides detailed error messages

## Notes

- As of the latest update, the registration script will not fail the build if it cannot access DynamoDB
- The MCP server will still be deployed and functional even if registration fails
- Registration can always be done manually through the UI or API later