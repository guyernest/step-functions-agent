# Step Functions AI Agents - Deployment Checklist

Quick reference checklist for deploying to a new AWS account/region.

## Pre-Deployment

- [ ] AWS Account access configured
- [ ] AWS CLI installed and configured
- [ ] Node.js 20.x+ installed
- [ ] CDK CLI installed (`npm install -g aws-cdk`)
- [ ] Git repository cloned
- [ ] Dependencies installed (root and ui_amplify)

## Backend Deployment (CDK)

- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] CDK bootstrapped (`cdk bootstrap`)
- [ ] Review `cdk.json` configuration
- [ ] Deploy CDK stacks (`cdk deploy --all`)
- [ ] Note DynamoDB table names from outputs
- [ ] Note Step Functions ARNs from outputs
- [ ] Verify resources in AWS Console

## Frontend Deployment (Amplify)

- [ ] Create Amplify app in AWS Console
- [ ] Connect Git repository
- [ ] Note Amplify App ID
- [ ] Configure build settings (or use auto-detected)
- [ ] Set environment variables:
  - [ ] `VITE_AGENT_REGISTRY_TABLE`
  - [ ] `VITE_TOOL_REGISTRY_TABLE`  
  - [ ] `VITE_AWS_REGION`
- [ ] Trigger deployment
- [ ] Wait for build completion
- [ ] Note Amplify app URL

## Integration & Verification

- [ ] Access Amplify app URL
- [ ] Configure settings in UI
- [ ] Verify Dashboard loads
- [ ] Check Agent Registry
- [ ] Check Tool Registry
- [ ] Test agent execution
- [ ] Verify execution history
- [ ] Register sample agents/tools
- [ ] Test end-to-end workflow

## Post-Deployment

- [ ] Set up CloudWatch monitoring
- [ ] Configure alarms
- [ ] Enable DynamoDB backups
- [ ] Document custom configurations
- [ ] Update team documentation
- [ ] Security review completed

## Troubleshooting Checklist

If issues occur, check:
- [ ] Amplify build logs
- [ ] Lambda function logs
- [ ] IAM permissions
- [ ] Network/CORS settings
- [ ] Environment variables
- [ ] AWS region consistency

## Sign-off

- [ ] Deployment completed successfully
- [ ] All tests passed
- [ ] Documentation updated
- [ ] Team notified

Date: _______________
Deployed by: _______________
Environment: _______________
AWS Account: _______________
Region: _______________