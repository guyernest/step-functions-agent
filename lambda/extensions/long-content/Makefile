# 
# Lambda Runtime API Proxy Extension
# Makefile for building, deploying, and testing
#

#-- config vars
EXTENSION_X86_ZIP = extension-x86.zip
EXTENSION_ARM_ZIP = extension-arm.zip
LAYER_X86_NAME = lambda-runtime-api-proxy-x86
LAYER_ARM_NAME = lambda-runtime-api-proxy-arm
STACK_NAME = lambda-runtime-api-proxy
REGION := $(shell aws configure get region 2>/dev/null || echo "us-west-2")
STAGE = dev
RS_FILES := $(shell find src -name "*.rs")

.PHONY: all clean build build-x86 build-arm deploy-x86 deploy-arm test-x86 test-arm test-full-x86 test-full-arm test test-full help

# Default target: display help
all: help

# Help target
help:
	@echo "Lambda Runtime API Proxy Extension - Makefile"
	@echo "------------------------------------------"
	@echo "make build        - Build both x86_64 and ARM64 extensions and test functions"
	@echo "make build-x86    - Build the x86_64 extension and test function"
	@echo "make build-arm    - Build the ARM64 extension and test function"
	@echo "make clean        - Clean all build artifacts"
	@echo "make deploy-x86   - Deploy the x86_64 extension and test function"
	@echo "make deploy-arm   - Deploy the ARM64 extension and test function"
	@echo "make test-x86     - Test the deployed x86_64 function"
	@echo "make test-arm     - Test the deployed ARM64 function"
	@echo "make test-full-x86 - Run a full diagnostic test on x86_64 function"
	@echo "make test-full-arm - Run a full diagnostic test on ARM64 function"
	@echo ""
	@echo "Environment variables:"
	@echo "REGION      - AWS region (default: $(REGION))"
	@echo "STACK_NAME  - CloudFormation stack name (default: $(STACK_NAME))"
	@echo "STAGE       - Deployment stage (default: $(STAGE))"

# Clean all build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf ./extension-x86
	@rm -rf ./extension-arm
	@rm -f $(EXTENSION_X86_ZIP) $(EXTENSION_ARM_ZIP)
	@rm -f response.json full_response.json
	@cargo clean
	@echo "Clean complete"

# Build the x86_64 extension
build-x86:
	@echo "Building Rust extension for x86_64..."
	@cargo lambda build --extension --target x86_64-unknown-linux-musl --release
	
	@echo "Creating extension directory structure..."
	@rm -rf ./extension-x86
	@mkdir -p ./extension-x86/extensions
	@mkdir -p ./extension-x86/extensions/lrap-wrapper
	
	@echo "Creating wrapper script..."
	@echo '#!/bin/bash' > ./extension-x86/extensions/lrap-wrapper/wrapper
	@echo 'export AWS_LAMBDA_RUNTIME_API="127.0.0.1:9009"' >> ./extension-x86/extensions/lrap-wrapper/wrapper
	@echo 'exec "$$@"' >> ./extension-x86/extensions/lrap-wrapper/wrapper
	@chmod 755 ./extension-x86/extensions/lrap-wrapper/wrapper
	
	@echo "Copying extension binary to extensions/lrap..."
	@cp ./target/lambda/extensions/aws-lambda-runtime-api-proxy-rs ./extension-x86/extensions/lrap
	@chmod 755 ./extension-x86/extensions/lrap
	
	@echo "Stripping debug symbols to reduce binary size..."
	@strip ./extension-x86/extensions/lrap
	
	@echo "Creating extension zip..."
	@cd extension-x86 && zip -r ../$(EXTENSION_X86_ZIP) . -x "*.DS_Store" -x "._*"
	
	@echo "Extension x86_64 build complete: $(EXTENSION_X86_ZIP)"

# Build the ARM64 extension
build-arm:
	@echo "Building Rust extension for ARM64 (aarch64)..."
	@cargo lambda build --extension --target aarch64-unknown-linux-musl --release
	
	@echo "Creating extension directory structure..."
	@rm -rf ./extension-arm
	@mkdir -p ./extension-arm/extensions
	@mkdir -p ./extension-arm/extensions/lrap-wrapper
	
	@echo "Creating wrapper script..."
	@echo '#!/bin/bash' > ./extension-arm/extensions/lrap-wrapper/wrapper
	@echo 'export AWS_LAMBDA_RUNTIME_API="127.0.0.1:9009"' >> ./extension-arm/extensions/lrap-wrapper/wrapper
	@echo 'exec "$$@"' >> ./extension-arm/extensions/lrap-wrapper/wrapper
	@chmod 755 ./extension-arm/extensions/lrap-wrapper/wrapper
	
	@echo "Copying extension binary to extensions/lrap..."
	@cp ./target/lambda/extensions/aws-lambda-runtime-api-proxy-rs ./extension-arm/extensions/lrap
	@chmod 755 ./extension-arm/extensions/lrap
	
	@echo "Stripping debug symbols to reduce binary size..."
	@strip ./extension-arm/extensions/lrap
	
	@echo "Creating extension zip..."
	@cd extension-arm && zip -r ../$(EXTENSION_ARM_ZIP) . -x "*.DS_Store" -x "._*"
	
	@echo "Extension ARM64 build complete: $(EXTENSION_ARM_ZIP)"

# Build both x86_64 and ARM64 extensions and test functions
build: build-x86 build-arm
	@echo "All builds complete"

# Deploy the x86_64 extension and test function
deploy-x86: build-x86
	@echo "Deploying x86_64 to region: $(REGION) with stack name: $(STACK_NAME)-x86"
	@sam deploy \
		--template-file template-x86.yaml \
		--stack-name $(STACK_NAME)-x86 \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			ParameterKey=DeploymentStage,ParameterValue=$(STAGE) \
			ParameterKey=CreateDynamoDBTable,ParameterValue=false \
		--region $(REGION)
	@echo "x86_64 deployment complete"

# Deploy the ARM64 extension and test function
deploy-arm: build-arm
	@echo "Deploying ARM64 to region: $(REGION) with stack name: $(STACK_NAME)-arm"
	@sam deploy \
		--template-file template-arm.yaml \
		--stack-name $(STACK_NAME)-arm \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			ParameterKey=DeploymentStage,ParameterValue=$(STAGE) \
			ParameterKey=CreateDynamoDBTable,ParameterValue=false \
		--region $(REGION)
	@echo "ARM64 deployment complete"

# Deploy both architectures
deploy: deploy-x86 deploy-arm
	@echo "Both architectures deployed"

# Test the deployed x86_64 function
test-x86:
	@echo "Testing the deployed x86_64 function..."
	$(eval FUNCTION_NAME := $(shell aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME)-x86 \
		--query "Stacks[0].Outputs[?OutputKey=='ProxyTestFunctionName'].OutputValue" \
		--output text \
		--region $(REGION)))
	@echo "Invoking function: $(FUNCTION_NAME)"
	@aws lambda invoke \
		--function-name $(FUNCTION_NAME) \
		--payload '{"test":"value","message":"Testing x86_64 Lambda Runtime API Proxy","content":"@content:dynamodb:table:TEST-TEST-TEST-TEST","nested":{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},"array_of_contents":[{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},{"content":"regular content"}]}' \
		--cli-binary-format raw-in-base64-out \
		--region $(REGION) \
		response.json
	@echo "Response:"
	@cat response.json
	@echo ""
	@echo "Retrieving logs (waiting 3 seconds for logs to be available)..."
	@sleep 3
	$(eval LOG_GROUP := /aws/lambda/$(FUNCTION_NAME))
	@echo "Retrieving latest log stream..."
	@bash -c 'STREAM_NAME=$$(aws logs describe-log-streams \
		--log-group-name $(LOG_GROUP) \
		--order-by LastEventTime \
		--descending \
		--limit 1 \
		--query "logStreams[0].logStreamName" \
		--output text \
		--region $(REGION)); \
		echo "Log stream: $$STREAM_NAME"; \
		aws logs get-log-events \
		--log-group-name $(LOG_GROUP) \
		--log-stream-name "$$STREAM_NAME" \
		--limit 100 \
		--region $(REGION) \
		--query "events[*].message" \
		--output text'
	@echo "x86_64 test complete"

# Test the deployed ARM64 function
test-arm:
	@echo "Testing the deployed ARM64 function..."
	$(eval FUNCTION_NAME := $(shell aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME)-arm \
		--query "Stacks[0].Outputs[?OutputKey=='ProxyTestFunctionName'].OutputValue" \
		--output text \
		--region $(REGION)))
	@echo "Invoking function: $(FUNCTION_NAME)"
	@aws lambda invoke \
		--function-name $(FUNCTION_NAME) \
		--payload '{"test":"value","message":"Testing ARM64 Lambda Runtime API Proxy","content":"@content:dynamodb:table:TEST-TEST-TEST-TEST","nested":{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},"array_of_contents":[{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},{"content":"regular content"}]}' \
		--cli-binary-format raw-in-base64-out \
		--region $(REGION) \
		response.json
	@echo "Response:"
	@cat response.json
	@echo ""
	@echo "Retrieving logs (waiting 3 seconds for logs to be available)..."
	@sleep 3
	$(eval LOG_GROUP := /aws/lambda/$(FUNCTION_NAME))
	@echo "Retrieving latest log stream..."
	@bash -c 'STREAM_NAME=$$(aws logs describe-log-streams \
		--log-group-name $(LOG_GROUP) \
		--order-by LastEventTime \
		--descending \
		--limit 1 \
		--query "logStreams[0].logStreamName" \
		--output text \
		--region $(REGION)); \
		echo "Log stream: $$STREAM_NAME"; \
		aws logs get-log-events \
		--log-group-name $(LOG_GROUP) \
		--log-stream-name "$$STREAM_NAME" \
		--limit 100 \
		--region $(REGION) \
		--query "events[*].message" \
		--output text'
	@echo "ARM64 test complete"

# Test both architectures
test: test-x86 test-arm
	@echo "Both architecture tests complete"

# Full diagnostic test for x86_64
test-full-x86:
	@echo "Running a full diagnostic test on x86_64 function..."
	$(eval FUNCTION_NAME := $(shell aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME)-x86 \
		--query "Stacks[0].Outputs[?OutputKey=='ProxyTestFunctionName'].OutputValue" \
		--output text \
		--region $(REGION)))
	@echo "Invoking function with full diagnostics: $(FUNCTION_NAME)"
	@aws lambda invoke \
		--function-name $(FUNCTION_NAME) \
		--payload '{"diagnostics":"full","test":"value","message":"Testing x86_64 Lambda Runtime API Proxy","content":"@content:dynamodb:table:TEST-TEST-TEST-TEST","nested":{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},"array_of_contents":[{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},{"content":"regular content"}]}' \
		--cli-binary-format raw-in-base64-out \
		--region $(REGION) \
		full_response.json
	@echo "Response:"
	@cat full_response.json
	@echo ""
	@echo "Retrieving logs (waiting 3 seconds for logs to be available)..."
	@sleep 3
	$(eval LOG_GROUP := /aws/lambda/$(FUNCTION_NAME))
	@echo "Retrieving latest log stream..."
	@bash -c 'STREAM_NAME=$$(aws logs describe-log-streams \
		--log-group-name $(LOG_GROUP) \
		--order-by LastEventTime \
		--descending \
		--limit 1 \
		--query "logStreams[0].logStreamName" \
		--output text \
		--region $(REGION)); \
		echo "Log stream: $$STREAM_NAME"; \
		aws logs get-log-events \
		--log-group-name $(LOG_GROUP) \
		--log-stream-name "$$STREAM_NAME" \
		--limit 200 \
		--region $(REGION) \
		--query "events[*].message" \
		--output text'
	@echo "x86_64 full diagnostic test complete"

# Full diagnostic test for ARM64
test-full-arm:
	@echo "Running a full diagnostic test on ARM64 function..."
	$(eval FUNCTION_NAME := $(shell aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME)-arm \
		--query "Stacks[0].Outputs[?OutputKey=='ProxyTestFunctionName'].OutputValue" \
		--output text \
		--region $(REGION)))
	@echo "Invoking function with full diagnostics: $(FUNCTION_NAME)"
	@aws lambda invoke \
		--function-name $(FUNCTION_NAME) \
		--payload '{"diagnostics":"full","test":"value","message":"Testing ARM64 Lambda Runtime API Proxy","content":"@content:dynamodb:table:TEST-TEST-TEST-TEST","nested":{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},"array_of_contents":[{"content":"@content:dynamodb:table:TEST-TEST-TEST-TEST"},{"content":"regular content"}]}' \
		--cli-binary-format raw-in-base64-out \
		--region $(REGION) \
		full_response.json
	@echo "Response:"
	@cat full_response.json
	@echo ""
	@echo "Retrieving logs (waiting 3 seconds for logs to be available)..."
	@sleep 3
	$(eval LOG_GROUP := /aws/lambda/$(FUNCTION_NAME))
	@echo "Retrieving latest log stream..."
	@bash -c 'STREAM_NAME=$$(aws logs describe-log-streams \
		--log-group-name $(LOG_GROUP) \
		--order-by LastEventTime \
		--descending \
		--limit 1 \
		--query "logStreams[0].logStreamName" \
		--output text \
		--region $(REGION)); \
		echo "Log stream: $$STREAM_NAME"; \
		aws logs get-log-events \
		--log-group-name $(LOG_GROUP) \
		--log-stream-name "$$STREAM_NAME" \
		--limit 200 \
		--region $(REGION) \
		--query "events[*].message" \
		--output text'
	@echo "ARM64 full diagnostic test complete"

# Test full for both architectures
test-full: test-full-x86 test-full-arm
	@echo "Both architecture full tests complete"
