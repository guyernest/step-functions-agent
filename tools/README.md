# CloudFormation Analysis Tools

This directory contains tools for analyzing and debugging CloudFormation deployments for the Step Functions Agent project.

## Tools Overview

### 1. analyze_cloudformation_dependencies.py

A general-purpose CloudFormation stack analyzer that:
- Lists all stacks (with optional filtering)
- Shows exports and imports
- Generates dependency diagrams
- Identifies missing exports and unused exports

**Usage:**
```bash
# Analyze all stacks
./analyze_cloudformation_dependencies.py --profile CGI-PoC

# Filter by pattern
./analyze_cloudformation_dependencies.py --pattern ".*LongContent.*" --profile CGI-PoC

# Filter by tags
./analyze_cloudformation_dependencies.py --tag Environment=prod --profile CGI-PoC

# Output formats
./analyze_cloudformation_dependencies.py --output mermaid  # Just diagram
./analyze_cloudformation_dependencies.py --output text     # Just text report
./analyze_cloudformation_dependencies.py --output json     # Export to JSON
```

**Example Output:**
- Text report showing stack status, exports, and imports
- Mermaid diagram visualizing dependencies
- JSON file for further processing

### 2. check_deployment_state.py

A specialized tool for the Step Functions Agent project that:
- Checks if required stacks are deployed
- Verifies exports match expected patterns
- Identifies what's needed for long content deployment
- Generates import configuration code

**Usage:**
```bash
# Check deployment state
./check_deployment_state.py --profile CGI-PoC --env prod

# Generate import configuration
./check_deployment_state.py --profile CGI-PoC --env prod --generate-config

# Check different environment
./check_deployment_state.py --profile CGI-PoC --env dev
```

**Example Output:**
```
🔍 Analyzing deployment state for environment: prod
   Region: us-east-1
   Profile: CGI-PoC
============================================================

📦 MAIN INFRASTRUCTURE STACKS:
  ✅ SharedInfrastructure-prod: CREATE_COMPLETE
  ✅ AgentRegistry-prod: CREATE_COMPLETE
  ✅ SharedLLM-prod: CREATE_COMPLETE

📦 LONG CONTENT INFRASTRUCTURE STACKS:
  ⚠️  LambdaExtensionLayer-prod: Not deployed
  ⚠️  SharedLongContentInfrastructure-prod: Not deployed
  ⚠️  SharedLLMWithLongContent-prod: Not deployed

🔗 CRITICAL EXPORTS:
  Agent Registry Exports:
    ✅ SharedTableAgentRegistry-prod (from AgentRegistry-prod)
    ✅ SharedTableArnAgentRegistry-prod (from AgentRegistry-prod)

💡 RECOMMENDATIONS:
  ✅ Main infrastructure is ready!
  📋 Next step: Deploy long content infrastructure
     cdk deploy --app 'python long_content_app.py' --all --profile CGI-PoC
```

## Common Use Cases

### 1. Before Deploying Long Content Stacks

Check that main infrastructure is properly deployed:
```bash
./check_deployment_state.py --profile CGI-PoC --env prod
```

### 2. Debugging "Export Not Found" Errors

See what exports are actually available:
```bash
./analyze_cloudformation_dependencies.py --profile CGI-PoC --output text | grep -A 20 "STACK SUMMARY"
```

### 3. Understanding Dependencies

Generate a visual diagram of stack dependencies:
```bash
./analyze_cloudformation_dependencies.py --pattern ".*Agent.*" --output mermaid
```

Copy the Mermaid output to a markdown file or [Mermaid Live Editor](https://mermaid.live) to visualize.

### 4. Finding Unused Exports

Identify exports that can be safely removed:
```bash
./analyze_cloudformation_dependencies.py --profile CGI-PoC | grep -A 10 "UNUSED EXPORTS"
```

### 5. Generating Import Configuration

Get ready-to-use import code for your stacks:
```bash
./check_deployment_state.py --profile CGI-PoC --env prod --generate-config
```

## Requirements

Both tools require:
- Python 3.6+
- boto3
- AWS credentials configured (via profile or environment variables)

## Tips

1. **Use Filters**: When analyzing large deployments, use pattern matching to focus on relevant stacks
2. **Check Status**: Pay attention to stack status - ROLLBACK states indicate deployment failures
3. **Export Names**: The tools highlight mismatches between expected and actual export names
4. **Environment Consistency**: Make sure you're checking the same environment (dev/prod) as you're deploying to