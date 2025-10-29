# IAM Permissions for Local Browser Agent

This document describes the AWS IAM permissions required for the Local Browser Agent to function properly.

## Overview

The Local Browser Agent needs permissions to:
1. **Poll for Activity Tasks** from AWS Step Functions
2. **Send Task Results** back to Step Functions
3. **Upload Recordings** to S3 bucket
4. **Send Heartbeats** to keep long-running tasks alive

## Quick Setup: IAM User with Policy

### Step 1: Create IAM User

```bash
# Create a dedicated IAM user for the browser agent
aws iam create-user --user-name browser-agent-user

# Create access keys for the user
aws iam create-access-key --user-name browser-agent-user
```

Save the output containing `AccessKeyId` and `SecretAccessKey` - you'll need these for configuration.

### Step 2: Create IAM Policy

Create a file named `browser-agent-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "StepFunctionsActivityAccess",
      "Effect": "Allow",
      "Action": [
        "states:GetActivityTask",
        "states:SendTaskSuccess",
        "states:SendTaskFailure",
        "states:SendTaskHeartbeat",
        "states:DescribeActivity"
      ],
      "Resource": [
        "arn:aws:states:*:ACCOUNT_ID:activity:browser-remote-*"
      ]
    },
    {
      "Sid": "S3RecordingsAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::browser-agent-recordings-*",
        "arn:aws:s3:::browser-agent-recordings-*/*"
      ]
    },
    {
      "Sid": "STSGetCallerIdentity",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

Replace `ACCOUNT_ID` with your AWS account ID.

### Step 3: Attach Policy to User

```bash
# Create the policy
aws iam create-policy \
  --policy-name BrowserAgentPolicy \
  --policy-document file://browser-agent-policy.json

# Attach policy to user
aws iam attach-user-policy \
  --user-name browser-agent-user \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/BrowserAgentPolicy
```

## Configuration Methods

The Local Browser Agent supports multiple methods for AWS credentials:

### Method 1: Environment Variables (Recommended for Windows)

This method is most reliable on Windows where profile file parsing can have issues.

**PowerShell**:
```powershell
# Set AWS credentials
$env:AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_DEFAULT_REGION = "us-west-2"

# Run the application
& ".\Local Browser Agent.exe"
```

**Bash/Zsh** (macOS/Linux):
```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-west-2"

# Run the application
./Local\ Browser\ Agent
```

### Method 2: AWS CLI Profile (macOS/Linux)

**Create Profile**:
```bash
# Configure a dedicated profile
aws configure --profile browser-agent

# Enter credentials when prompted:
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name: us-west-2
# Default output format: json
```

**Verify Profile**:
```bash
# Test the credentials
aws sts get-caller-identity --profile browser-agent

# Should output:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/browser-agent-user"
# }
```

**Select in Application**:
1. Open Local Browser Agent
2. Go to Configuration screen
3. Select `browser-agent` from the AWS Profile dropdown
4. Click "Test Connection"

### Method 3: Shared Credentials File

**Create/Edit** `~/.aws/credentials` (or `%USERPROFILE%\.aws\credentials` on Windows):

```ini
[browser-agent]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Create/Edit** `~/.aws/config`:

```ini
[profile browser-agent]
region = us-west-2
output = json
```

## Detailed Permission Breakdown

### 1. Step Functions Permissions

#### `states:GetActivityTask`
- **Purpose**: Poll for browser automation tasks
- **Frequency**: Continuous long-polling (waits up to 60 seconds per call)
- **Resource**: Activity ARN (e.g., `arn:aws:states:us-west-2:123456789012:activity:browser-remote-prod`)

#### `states:SendTaskSuccess`
- **Purpose**: Return successful browser automation results
- **Frequency**: Once per task completion
- **Payload**: JSON with browser output, session ID, S3 recording URI

#### `states:SendTaskFailure`
- **Purpose**: Report task failures (errors, timeouts, crashes)
- **Frequency**: Once per failed task
- **Payload**: Error message and cause

#### `states:SendTaskHeartbeat`
- **Purpose**: Keep long-running tasks alive
- **Frequency**: Every 60 seconds during task execution
- **Note**: Prevents Step Functions from timing out during multi-minute browser sessions

#### `states:DescribeActivity`
- **Purpose**: Validate Activity ARN in UI
- **Frequency**: Once during configuration
- **Returns**: Activity name, creation date, ARN

### 2. S3 Permissions

#### `s3:PutObject`
- **Purpose**: Upload browser recordings, screenshots, and HTML snapshots
- **Frequency**: Multiple times per browser session
- **Objects**:
  - `recordings/{session-id}/video.webm`
  - `recordings/{session-id}/screenshots/{step-N}.png`
  - `recordings/{session-id}/html/{step-N}.html`
  - `recordings/{session-id}/metadata.json`

#### `s3:PutObjectAcl`
- **Purpose**: Set object permissions (if needed for access control)
- **Frequency**: Per object upload
- **Note**: Optional, only if using ACLs

#### `s3:GetObject`
- **Purpose**: Retrieve recordings for playback
- **Frequency**: On-demand
- **Note**: Useful for verifying uploads

#### `s3:ListBucket`
- **Purpose**: List recordings in bucket
- **Frequency**: On-demand
- **Note**: For browsing past sessions

### 3. STS Permissions

#### `sts:GetCallerIdentity`
- **Purpose**: Verify AWS credentials are valid
- **Frequency**: Once during "Test Connection" in UI
- **Returns**: User ID, Account ID, ARN

## Testing Permissions

### Test Step Functions Access

```bash
# Test polling for activity tasks (will timeout after 60s if no tasks)
aws stepfunctions get-activity-task \
  --activity-arn "arn:aws:states:us-west-2:123456789012:activity:browser-remote-prod" \
  --profile browser-agent

# Describe the activity
aws stepfunctions describe-activity \
  --activity-arn "arn:aws:states:us-west-2:123456789012:activity:browser-remote-prod" \
  --profile browser-agent
```

### Test S3 Access

```bash
# List bucket contents
aws s3 ls s3://browser-agent-recordings-prod-123456789012/ \
  --profile browser-agent

# Upload a test file
echo "test" > test.txt
aws s3 cp test.txt s3://browser-agent-recordings-prod-123456789012/test.txt \
  --profile browser-agent

# Verify upload
aws s3 ls s3://browser-agent-recordings-prod-123456789012/test.txt \
  --profile browser-agent
```

### Test via Application

1. **Open Local Browser Agent**
2. **Go to Configuration Screen**
3. **Select AWS Profile**: Choose `browser-agent`
4. **Click "Test Connection"**: Should show ✓ Success
5. **Enter Activity ARN**: From CDK deployment
6. **Click "Validate ARN"**: Should show activity details

## Security Best Practices

### 1. Principle of Least Privilege

The policy above grants only the minimum permissions needed. Consider further restricting:

```json
{
  "Resource": [
    "arn:aws:states:us-west-2:123456789012:activity:browser-remote-prod"
  ]
}
```

Instead of wildcards:
```json
{
  "Resource": [
    "arn:aws:states:*:*:activity:browser-remote-*"
  ]
}
```

### 2. Separate Environments

Use different IAM users/roles for each environment:

- `browser-agent-dev` → dev environment
- `browser-agent-staging` → staging environment
- `browser-agent-prod` → production environment

### 3. Credential Rotation

```bash
# Create new access key
aws iam create-access-key --user-name browser-agent-user

# Update credentials in application

# Delete old access key
aws iam delete-access-key \
  --user-name browser-agent-user \
  --access-key-id AKIAIOSFODNN7EXAMPLE
```

### 4. Audit Logging

Enable CloudTrail to monitor API calls:

```bash
# Check recent API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=browser-agent-user \
  --max-items 10
```

## Advanced: IAM Role with AssumeRole

For organizations using IAM Roles instead of users:

### Create Role Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/your-username"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Assume Role

```bash
# Assume the role
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/BrowserAgentRole \
  --role-session-name browser-agent-session

# Use temporary credentials
export AWS_ACCESS_KEY_ID="ASIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_SESSION_TOKEN="FwoGZXIvYXdzEBQaD..."
```

## Troubleshooting

### Error: "Access Denied"

**Check permissions**:
```bash
# List attached policies
aws iam list-attached-user-policies --user-name browser-agent-user

# Get policy version
aws iam get-policy-version \
  --policy-arn arn:aws:iam::123456789012:policy/BrowserAgentPolicy \
  --version-id v1
```

### Error: "InvalidClientTokenId"

**Verify credentials**:
```bash
# Check if access key is valid
aws sts get-caller-identity --profile browser-agent

# List access keys for user
aws iam list-access-keys --user-name browser-agent-user
```

### Error: "Profile file could not be parsed"

**Use environment variables instead** (see Method 1 above).

### Windows-Specific: Profile Parsing Issues

On Windows, the AWS SDK may have trouble parsing profile files due to encoding or line endings. **Solution**: Use environment variables (Method 1) instead of profile files.

## CDK Deployment Outputs

After deploying the CDK stack, you'll receive outputs containing the resources you need to configure:

```bash
cdk deploy BrowserRemoteToolStack-prod

# Outputs:
# BrowserRemoteToolStack-prod.ActivityArn = arn:aws:states:us-west-2:123456789012:activity:browser-remote-prod
# BrowserRemoteToolStack-prod.S3BucketName = browser-agent-recordings-prod-abc123
```

Use these values in the Local Browser Agent configuration screen.

## Summary

**Minimum Required Permissions**:
- ✅ Step Functions: GetActivityTask, SendTaskSuccess, SendTaskFailure, SendTaskHeartbeat
- ✅ S3: PutObject, ListBucket (on recordings bucket)
- ✅ STS: GetCallerIdentity (for testing)

**Recommended Setup**:
1. Create dedicated IAM user: `browser-agent-user`
2. Attach minimal policy with specific resource ARNs
3. Use environment variables for credentials (especially on Windows)
4. Test permissions via application UI
5. Monitor with CloudTrail

**Need Help?**
- See [README.md](../README.md) for general setup
- See [DEPLOYMENT.md](./DEPLOYMENT.md) for CDK infrastructure
- Create an issue for permission-related problems
