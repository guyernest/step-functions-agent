#!/bin/bash
# Force delete CloudFormation stacks in the correct order

PROFILE="CGI-PoC"
REGION="eu-west-1"

echo "🔥 Force deleting long content stacks in dependency order..."

# Function to delete a stack and wait
delete_stack() {
    local stack_name=$1
    echo "Deleting $stack_name..."
    
    # Delete the stack
    aws cloudformation delete-stack \
        --stack-name "$stack_name" \
        --profile "$PROFILE" \
        --region "$REGION" 2>/dev/null
    
    # Wait for deletion to complete
    echo "Waiting for $stack_name to be deleted..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$stack_name" \
        --profile "$PROFILE" \
        --region "$REGION" 2>/dev/null
    
    echo "✅ $stack_name deleted (or was already gone)"
}

# Delete in reverse dependency order
echo "Step 1: Deleting agents..."
delete_stack "SqlLongContentAgent-prod"
delete_stack "WebScraperLongContentAgent-prod"
delete_stack "ImageAnalysisLongContentAgent-prod"

echo "Step 2: Deleting tools..."
delete_stack "SqlLongContentTools-prod"
delete_stack "WebScraperLongContentTools-prod"

echo "Step 3: Deleting LLM stack..."
delete_stack "SharedLLMWithLongContent-prod"

echo "Step 4: Deleting infrastructure..."
delete_stack "SharedLongContentInfrastructure-prod"

echo "Step 5: Deleting extension layer..."
delete_stack "LambdaExtensionLayer-prod"

echo "🎉 All stacks deleted!"