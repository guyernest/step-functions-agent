#!/bin/bash

# Test the browser_broadband tool Lambda function
# This script invokes the Lambda directly and waits for completion

LAMBDA_FUNCTION_NAME="agentcore-browser-tool-prod"
TEST_EVENT_FILE="test_events/browser_broadband_test.json"
LOG_FILE="logs/browser_broadband_test_$(date +%Y%m%d_%H%M%S).log"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "========================================="
echo "Testing Browser Broadband Tool"
echo "========================================="
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "Test Event: $TEST_EVENT_FILE"
echo "Log File: $LOG_FILE"
echo ""

# Show the test event
echo "Test Event Content:"
cat $TEST_EVENT_FILE | jq '.'
echo ""

echo "Invoking Lambda function..."
echo "This may take 1-2 minutes to complete as it performs browser automation..."
echo ""

# Invoke the Lambda function synchronously and capture the response
RESPONSE=$(aws lambda invoke \
    --function-name $LAMBDA_FUNCTION_NAME \
    --invocation-type RequestResponse \
    --payload file://$TEST_EVENT_FILE \
    --cli-read-timeout 300 \
    --cli-connect-timeout 300 \
    --log-type Tail \
    --query 'LogResult' \
    --output text \
    response.json 2>&1)

# Check if the invocation was successful
if [ $? -eq 0 ]; then
    echo "✅ Lambda invocation successful!"
    echo ""
    
    # Display the response
    echo "Response:"
    echo "----------------------------------------"
    cat response.json | jq '.'
    echo "----------------------------------------"
    
    # Save the full response to the log file
    echo "Full response saved to: $LOG_FILE"
    cat response.json | jq '.' > $LOG_FILE
    
    # Decode and display the logs (if available)
    if [ ! -z "$RESPONSE" ] && [ "$RESPONSE" != "None" ]; then
        echo ""
        echo "Lambda Execution Logs (last 4KB):"
        echo "----------------------------------------"
        echo $RESPONSE | base64 --decode
        echo "----------------------------------------"
    fi
    
    # Extract the actual content from the tool response
    echo ""
    echo "Extracted Result:"
    echo "----------------------------------------"
    cat response.json | jq -r '.content' 2>/dev/null || cat response.json
    echo "----------------------------------------"
    
else
    echo "❌ Lambda invocation failed!"
    echo "Error: $RESPONSE"
    echo "Check CloudWatch logs for details:"
    echo "aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow"
fi

# Clean up the temporary response file
rm -f response.json

echo ""
echo "Test completed at $(date)"