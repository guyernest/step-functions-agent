# Build Process

This document describes the build process for the Step Functions Agent project.

## Overview

The project uses AWS CodeBuild to build various components:
- CDK stacks that generate CloudFormation templates
- Lambda functions written in different languages (Python, TypeScript, Rust, Go, Java)
- Lambda extensions

All builds use a single `buildspec.yml` file in the root of the repository, which serves as a router to the appropriate build process based on the `BUILD_TYPE` environment variable.

## Setting Up a New Build

1. Create a new CodeBuild project in AWS
2. Configure the source repository
3. Set the `BUILD_TYPE` environment variable to one of the supported build types
4. Use the default buildspec path (buildspec.yml in the root directory)
5. Configure other build settings as needed (compute, service role, etc.)

## Supported Build Types

The router supports the following build types through the `BUILD_TYPE` environment variable:

### CDK Stacks

- `sql-stack`: Builds the SQL Agent CDK stack into CloudFormation templates

### Lambda Functions

- `lambda-extension`: Builds the Lambda extension written in Rust
- `web-scraper`: Builds the Web Scraper Lambda function written in TypeScript
- `db-interface`: Builds the DB Interface Lambda function written in Python
- `web-scraper-memory`: Builds the WebScraperMemory Lambda function written in Rust

## Adding New Build Types

To add support for a new component:

1. Identify the component's type and build requirements
2. In `buildspec.yml`, add a new condition to each phase (install, build, post_build) to handle the new component
3. Update the artifacts section to include any new artifacts

Example for a new Go Lambda function:
```yaml
# In the build phase
elif [ "$BUILD_TYPE" == "new-go-function" ]; then
  echo "Building New Go Lambda..."
  cd lambda/tools/new-go-function
  go mod download
  GOOS=linux GOARCH=arm64 go build -tags lambda.norpc -o bootstrap main.go
  cd ../../..

# In the post_build phase
elif [ "$BUILD_TYPE" == "new-go-function" ]; then
  aws s3api put-object --bucket $S3_BUCKET --key lambda/new-go-function/ --content-length 0 || true
  cd lambda/tools/new-go-function
  zip -r lambda.zip bootstrap
  aws s3 cp lambda.zip s3://${S3_BUCKET}/lambda/new-go-function/lambda.zip
  cd ../../..
  echo "Lambda code available at s3://$S3_BUCKET/lambda/new-go-function/"
```

## Deployment

All build artifacts are uploaded to an S3 bucket with the pattern:
```
step-functions-agent-artifacts-${AWS_REGION}-${AWS_ACCOUNT_ID}
```

The artifacts are organized in the bucket as follows:
- `/cloudformation/{stack-name}/` - CloudFormation templates
- `/lambda-layers/` - Lambda extensions/layers
- `/lambda/{function-name}/` - Lambda function packages

## Troubleshooting

If the build fails, check the following:

1. Verify the `BUILD_TYPE` is set correctly
2. Check that all necessary permissions are granted to the CodeBuild service role
3. Ensure the required directories and files exist in the source code
4. Review the build logs for specific error messages