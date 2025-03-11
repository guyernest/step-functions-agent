# CI/CD Setup - Next Steps

The CI/CD pipeline for building Lambda Extensions is now configured. Here's what has been set up:

## Files Created/Modified

1. **GitHub Actions Workflow**
   - Created at repository root: `.github/workflows/lambda-extension-build.yml`
   - This workflow will notify when changes to the Lambda extension are detected
   - It doesn't actually trigger CodeBuild, but serves as documentation/notification

2. **AWS CodeBuild buildspec.yml**
   - Located at: `lambda/extensions/long-content/buildspec.yml`
   - Defines the build steps for both x86_64 and ARM64 extensions
   - Uses region and account-specific S3 bucket names

3. **README.md**
   - Updated with CI/CD information in the "CI/CD Pipeline" section

## Remaining Setup Tasks

1. **Configure AWS CodeBuild Webhook**
   - Open the AWS CodeBuild console
   - Select project: `arn:aws:codebuild:us-west-2:672915487120:project/step-functions-agent`
   - Configure webhook to GitHub repository:
     - Go to Edit → Source → GitHub
     - Connect to your GitHub account
     - Choose "Rebuild every time a code change is pushed to this repository"
     - Optional: Add filter to trigger only on changes to `lambda/extensions/long-content/**`

2. **Verify CodeBuild Service Role Permissions**
   - Ensure the CodeBuild service role has these permissions:
     - `s3:PutObject` and `s3:CreateBucket` for storing build artifacts
     - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` for logging
     - `sts:GetCallerIdentity` to determine the account ID

3. **Test the Pipeline**
   - Make a small change to a file in `lambda/extensions/long-content`
   - Commit and push to GitHub
   - Verify CodeBuild is triggered and builds successfully
   - Check the S3 bucket for the extension ZIP files

## Using Built Extensions

After a successful build, the extension ZIPs will be available at:
```
s3://step-functions-agent-artifacts-{region}-{account-id}/lambda-layers/extension-arm.zip
s3://step-functions-agent-artifacts-{region}-{account-id}/lambda-layers/extension-x86.zip
```

Create Lambda layers from these ZIPs using:
```bash
# For ARM64
aws lambda publish-layer-version \
  --layer-name lambda-runtime-api-proxy-arm \
  --description "Lambda Runtime API Proxy Extension for ARM64" \
  --license-info "MIT" \
  --content S3Bucket=step-functions-agent-artifacts-{region}-{account-id},S3Key=lambda-layers/extension-arm.zip \
  --compatible-runtimes provided provided.al2 nodejs14.x nodejs16.x nodejs18.x python3.9 python3.10 python3.11 java11 java17 \
  --compatible-architectures arm64

# For x86_64
aws lambda publish-layer-version \
  --layer-name lambda-runtime-api-proxy-x86 \
  --description "Lambda Runtime API Proxy Extension for x86_64" \
  --license-info "MIT" \
  --content S3Bucket=step-functions-agent-artifacts-{region}-{account-id},S3Key=lambda-layers/extension-x86.zip \
  --compatible-runtimes provided provided.al2 nodejs14.x nodejs16.x nodejs18.x python3.9 python3.10 python3.11 java11 java17 \
  --compatible-architectures x86_64
```