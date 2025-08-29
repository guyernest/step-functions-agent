#!/bin/bash

# Script to grant Amplify build role permissions to write to MCP Registry

ROLE_NAME="AmplifySSRLoggingRole-1bb41e53-26f9-4521-9919-1bc09ce7cf4e"
POLICY_NAME="MCPRegistryAccess"

# Create the policy document
cat > /tmp/mcp-registry-policy.json << 'EOF'
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
        "arn:aws:dynamodb:us-west-2:672915487120:table/MCPServerRegistry-prod",
        "arn:aws:dynamodb:us-west-2:672915487120:table/MCPServerRegistry-prod/index/*"
      ]
    }
  ]
}
EOF

echo "Adding MCP Registry permissions to Amplify build role..."

# Attach the inline policy to the role
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/mcp-registry-policy.json \
  --profile ze-kasher-dev

if [ $? -eq 0 ]; then
  echo "✅ Successfully added permissions to $ROLE_NAME"
  echo "   The next Amplify deployment will automatically register the MCP server."
else
  echo "❌ Failed to add permissions. Please check your AWS credentials and try again."
fi

# Clean up
rm /tmp/mcp-registry-policy.json