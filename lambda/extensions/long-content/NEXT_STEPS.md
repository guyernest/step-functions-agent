# CI/CD Setup - Complete

The CI/CD pipeline for building Lambda Extensions is now configured and ready to use. Here's what has been set up:

## Files Created/Modified

1. **GitHub Actions Workflow**
   - Created at repository root: `.github/workflows/lambda-extension-build.yml`
   - This workflow will notify when changes to the Lambda extension are detected
   - It serves as documentation/notification for builds

2. **Root-level buildspec.yml**
   - Created at repository root: `buildspec.yml`
   - Contains all build instructions for both x86_64 and ARM64 extensions
   - Uses region and account-specific S3 bucket names

3. **README.md**
   - Updated with CI/CD information in the "CI/CD Pipeline" section

## How the Pipeline Works

1. When code is pushed to the repository, GitHub webhook notifies CodeBuild
2. CodeBuild reads the buildspec.yml at the root of the repository 
3. The buildspec.yml file:
   - Installs all necessary dependencies
   - Builds both ARM64 and x86_64 extensions using the Makefile
   - Creates a region and account-specific S3 bucket
   - Uploads the built extensions to this bucket

4. The GitHub Actions workflow provides a notification that a build should be triggered
   - It doesn't perform the actual build
   - It provides a link to monitor build status

## Testing the Pipeline

To verify everything is working:
1. Make a small change to a file in `lambda/extensions/long-content`
2. Commit and push to GitHub
3. Monitor the GitHub Actions workflow execution
4. Check the build status in CodeBuild console
5. After a successful build, verify the extensions are in the S3 bucket

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