#!/bin/bash
# Deploy Agent Core agent and create Step Functions wrapper

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
REGION="us-east-1"
ENVIRONMENT="prod"
PROFILE=""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Parse command line arguments
usage() {
    echo "Usage: $0 -c CONFIG_FILE [-r REGION] [-e ENVIRONMENT] [-p PROFILE]"
    echo ""
    echo "Options:"
    echo "  -c CONFIG_FILE   Agent configuration file (YAML or JSON)"
    echo "  -r REGION        AWS region (default: us-east-1)"
    echo "  -e ENVIRONMENT   Environment name (default: prod)"
    echo "  -p PROFILE       AWS profile name (optional)"
    echo "  -h               Show this help message"
    exit 1
}

while getopts "c:r:e:p:h" opt; do
    case $opt in
        c) CONFIG_FILE="$OPTARG";;
        r) REGION="$OPTARG";;
        e) ENVIRONMENT="$OPTARG";;
        p) PROFILE="$OPTARG";;
        h) usage;;
        *) usage;;
    esac
done

# Check required arguments
if [ -z "$CONFIG_FILE" ]; then
    print_error "Configuration file is required"
    usage
fi

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Extract agent name from config file
AGENT_NAME=$(python3 -c "
import yaml, json, sys
with open('$CONFIG_FILE', 'r') as f:
    if '$CONFIG_FILE'.endswith(('.yaml', '.yml')):
        config = yaml.safe_load(f)
    else:
        config = json.load(f)
    print(config.get('agent_name', 'unknown'))
")

print_status "Deploying Agent Core agent: $AGENT_NAME"
print_status "Region: $REGION"
print_status "Environment: $ENVIRONMENT"

# Step 1: Get Nova Act Browser Lambda ARN from CDK
print_status "Getting Nova Act Browser Lambda ARN..."
NOVA_ACT_ARN=$(aws cloudformation describe-stacks \
    --stack-name "NovaActBrowserToolStack-${ENVIRONMENT}" \
    --region "$REGION" \
    ${PROFILE:+--profile "$PROFILE"} \
    --query "Stacks[0].Outputs[?OutputKey=='NovaActBrowserFunctionArn'].OutputValue" \
    --output text 2>/dev/null || echo "")

if [ -z "$NOVA_ACT_ARN" ]; then
    print_warning "Nova Act Browser stack not found. Please deploy it first:"
    echo "  cdk deploy NovaActBrowserToolStack-${ENVIRONMENT}"
    exit 1
fi

print_status "Found Nova Act Browser Lambda: $NOVA_ACT_ARN"

# Step 2: Update config file with actual Lambda ARN
TEMP_CONFIG="/tmp/agent-config-${AGENT_NAME}.yaml"
sed "s|\${NOVA_ACT_BROWSER_LAMBDA_ARN}|$NOVA_ACT_ARN|g" "$CONFIG_FILE" > "$TEMP_CONFIG"

# Step 3: Deploy Agent Core agent
print_status "Deploying agent to Agent Core..."
DEPLOY_CMD="python3 scripts/agent_core/deploy_agent.py $TEMP_CONFIG --region $REGION"
if [ -n "$PROFILE" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --profile $PROFILE"
fi

if ! $DEPLOY_CMD; then
    print_error "Agent Core deployment failed"
    rm -f "$TEMP_CONFIG"
    exit 1
fi

# Step 4: Check for output file
OUTPUT_FILE="agent-core-output-${AGENT_NAME}.json"
if [ ! -f "$OUTPUT_FILE" ]; then
    print_error "Deployment output file not found: $OUTPUT_FILE"
    rm -f "$TEMP_CONFIG"
    exit 1
fi

print_status "Agent Core deployment successful!"

# Step 5: Create CDK app for wrapper state machine
print_status "Creating Step Functions wrapper..."

# Create temporary CDK app file
TEMP_CDK_APP="/tmp/agent-wrapper-app-${AGENT_NAME}.py"
cat > "$TEMP_CDK_APP" << EOF
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.agents.agent_core_wrapper_stack import AgentCoreWrapperStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region="${REGION}"
)

# Create wrapper stack from deployment output
wrapper_stack = AgentCoreWrapperStack.from_deployment_output(
    app,
    "AgentCoreWrapper-${AGENT_NAME}-${ENVIRONMENT}",
    output_file="${OUTPUT_FILE}",
    env_name="${ENVIRONMENT}",
    env=env
)

app.synth()
EOF

# Step 6: Deploy wrapper state machine
print_status "Deploying wrapper state machine..."
export CDK_APP="python3 $TEMP_CDK_APP"

CDK_DEPLOY_CMD="cdk deploy AgentCoreWrapper-${AGENT_NAME}-${ENVIRONMENT} --require-approval never"
if [ -n "$PROFILE" ]; then
    export AWS_PROFILE="$PROFILE"
fi

if ! $CDK_DEPLOY_CMD; then
    print_error "Wrapper deployment failed"
    rm -f "$TEMP_CONFIG" "$TEMP_CDK_APP"
    exit 1
fi

# Step 7: Get wrapper state machine ARN
WRAPPER_ARN=$(aws cloudformation describe-stacks \
    --stack-name "AgentCoreWrapper-${AGENT_NAME}-${ENVIRONMENT}" \
    --region "$REGION" \
    ${PROFILE:+--profile "$PROFILE"} \
    --query "Stacks[0].Outputs[?contains(OutputKey, 'StateMachineArn')].OutputValue" \
    --output text)

# Step 8: Create integration summary
SUMMARY_FILE="agent-integration-${AGENT_NAME}.json"
cat > "$SUMMARY_FILE" << EOF
{
  "agent_name": "${AGENT_NAME}",
  "environment": "${ENVIRONMENT}",
  "region": "${REGION}",
  "agent_core": $(cat "$OUTPUT_FILE"),
  "wrapper_state_machine_arn": "${WRAPPER_ARN}",
  "integration_type": "agent",
  "invocation_pattern": "states:startExecution.sync:2"
}
EOF

# Clean up temporary files
rm -f "$TEMP_CONFIG" "$TEMP_CDK_APP"

print_status "✅ Deployment complete!"
echo ""
echo "Summary saved to: $SUMMARY_FILE"
echo ""
echo "To use this agent in your hybrid supervisor, add to agent_configs:"
echo "  \"${AGENT_NAME}\": {"
echo "    \"arn\": \"${WRAPPER_ARN}\","
echo "    \"description\": \"Agent Core ${AGENT_NAME}\""
echo "  }"
echo ""
echo "Example invocation from Step Functions:"
echo "  {"
echo "    \"Type\": \"Task\","
echo "    \"Resource\": \"arn:aws:states:::states:startExecution.sync:2\","
echo "    \"Parameters\": {"
echo "      \"StateMachineArn\": \"${WRAPPER_ARN}\","
echo "      \"Input\": {"
echo "        \"session_id.\$\": \"\$\$.Execution.Name\","
echo "        \"agent_config\": {"
echo "          \"input_text.\$\": \"\$.query\""
echo "        }"
echo "      }"
echo "    }"
echo "  }"