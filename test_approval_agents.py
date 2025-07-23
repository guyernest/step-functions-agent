#!/usr/bin/env python3
"""
Test script for approval workflow agents

This script provides commands to deploy and test the approval workflow agents:
1. TestSQLApprovalAgentStack - demonstrates human approval for SQL operations
2. TestAutomationRemoteAgentStack - demonstrates remote execution for local automation

Usage:
    python test_approval_agents.py deploy    # Deploy test agents
    python test_approval_agents.py test      # Run test scenarios
    python test_approval_agents.py status    # Check deployment status
"""

import sys
import subprocess
import json
import boto3
import time
from datetime import datetime


def run_command(command, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return None


def deploy_test_agents():
    """Deploy the test agents for approval workflows"""
    print("🚀 Deploying Test Approval Agents...")
    
    # Deploy required infrastructure first
    print("\n📦 Deploying shared infrastructure...")
    run_command('cdk deploy SharedInfrastructureStack-prod --app "python refactored_app.py" --require-approval never')
    
    print("\n🤖 Deploying shared LLM services...")
    run_command('cdk deploy SharedLLMStack-prod --app "python refactored_app.py" --require-approval never')
    
    print("\n📋 Deploying agent registry...")
    run_command('cdk deploy AgentRegistryStack-prod --app "python refactored_app.py" --require-approval never')
    
    # Deploy required tool stacks
    print("\n🛠️ Deploying required tool stacks...")
    run_command('cdk deploy DBInterfaceToolStack-prod --app "python refactored_app.py" --require-approval never')
    run_command('cdk deploy E2BToolStack-prod --app "python refactored_app.py" --require-approval never')
    run_command('cdk deploy LocalAutomationToolStack-prod --app "python refactored_app.py" --require-approval never')
    
    # Deploy test agents
    print("\n🧪 Deploying test agents...")
    print("Deploying SQL Approval Agent...")
    run_command('cdk deploy TestSQLApprovalAgentStack-prod --app "python refactored_app.py" --require-approval never')
    
    print("Deploying Automation Remote Agent...")
    run_command('cdk deploy TestAutomationRemoteAgentStack-prod --app "python refactored_app.py" --require-approval never')
    
    print("\n✅ Test agents deployed successfully!")
    print("\nNext steps:")
    print("1. Test SQL approval: python test_approval_agents.py test-sql")
    print("2. Test remote execution: python test_approval_agents.py test-remote")
    print("3. Check status: python test_approval_agents.py status")


def test_sql_approval_agent():
    """Test the SQL approval agent workflow"""
    print("🧪 Testing SQL Approval Agent...")
    
    # Create Step Functions client
    sf_client = boto3.client('stepfunctions')
    
    # Test input for SQL agent
    test_input = {
        "messages": [
            {
                "role": "user",
                "content": "Can you show me the database schema first, then count how many records are in each table?"
            }
        ]
    }
    
    try:
        # Start execution
        response = sf_client.start_execution(
            stateMachineArn=f"arn:aws:states:us-east-1:{boto3.client('sts').get_caller_identity()['Account']}:stateMachine:test-sql-approval-agent-prod",
            name=f"test-sql-approval-{int(time.time())}",
            input=json.dumps(test_input)
        )
        
        execution_arn = response['executionArn']
        print(f"✅ Started execution: {execution_arn}")
        
        # Monitor execution
        print("⏳ Monitoring execution (will show approval requests)...")
        
        for i in range(30):  # Monitor for up to 5 minutes
            time.sleep(10)
            
            status = sf_client.describe_execution(executionArn=execution_arn)
            
            print(f"Status: {status['status']}")
            
            if status['status'] in ['SUCCEEDED', 'FAILED', 'TIMED_OUT']:
                break
                
            # Check for activities requiring approval
            activities = sf_client.list_activities()
            for activity in activities.get('activities', []):
                if 'approval-activity' in activity['name']:
                    tasks = sf_client.get_activity_task(
                        activityArn=activity['activityArn'],
                        workerName='test-worker'
                    )
                    if tasks.get('taskToken'):
                        print(f"🔔 APPROVAL REQUIRED for activity: {activity['name']}")
                        print(f"Task: {tasks.get('input', 'No details')}")
        
        # Get final result
        final_status = sf_client.describe_execution(executionArn=execution_arn)
        print(f"\n📊 Final Status: {final_status['status']}")
        
        if final_status.get('output'):
            print(f"Output: {final_status['output']}")
            
    except Exception as e:
        print(f"❌ Error testing SQL approval agent: {e}")


def test_remote_execution_agent():
    """Test the remote execution agent workflow"""
    print("🧪 Testing Remote Execution Agent...")
    
    # Create Step Functions client
    sf_client = boto3.client('stepfunctions')
    
    # Test input for remote automation
    test_input = {
        "messages": [
            {
                "role": "user", 
                "content": "Can you help me automate opening a text editor and typing 'Hello World' on a local machine?"
            }
        ]
    }
    
    try:
        # Start execution
        response = sf_client.start_execution(
            stateMachineArn=f"arn:aws:states:us-east-1:{boto3.client('sts').get_caller_identity()['Account']}:stateMachine:test-automation-remote-agent-prod",
            name=f"test-remote-execution-{int(time.time())}",
            input=json.dumps(test_input)
        )
        
        execution_arn = response['executionArn']
        print(f"✅ Started execution: {execution_arn}")
        
        # Monitor execution
        print("⏳ Monitoring execution (will show remote execution requests)...")
        
        for i in range(18):  # Monitor for up to 3 minutes
            time.sleep(10)
            
            status = sf_client.describe_execution(executionArn=execution_arn)
            print(f"Status: {status['status']}")
            
            if status['status'] in ['SUCCEEDED', 'FAILED', 'TIMED_OUT']:
                break
                
            # Check for remote execution activities
            activities = sf_client.list_activities()
            for activity in activities.get('activities', []):
                if 'remote-activity' in activity['name']:
                    print(f"🔔 REMOTE EXECUTION REQUESTED for activity: {activity['name']}")
                    print("💡 A remote worker should poll this activity to execute the task")
        
        # Get final result
        final_status = sf_client.describe_execution(executionArn=execution_arn)
        print(f"\n📊 Final Status: {final_status['status']}")
        
        if final_status.get('output'):
            print(f"Output: {final_status['output']}")
            
    except Exception as e:
        print(f"❌ Error testing remote execution agent: {e}")


def check_deployment_status():
    """Check the deployment status of test agents"""
    print("📊 Checking Test Agent Deployment Status...")
    
    # Check CloudFormation stacks
    cf_client = boto3.client('cloudformation')
    
    test_stacks = [
        'TestSQLApprovalAgentStack-prod',
        'TestAutomationRemoteAgentStack-prod',
        'LocalAutomationToolStack-prod',
        'DBInterfaceToolStack-prod',
        'E2BToolStack-prod'
    ]
    
    for stack_name in test_stacks:
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            status = stack['StackStatus']
            
            if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                print(f"✅ {stack_name}: {status}")
            else:
                print(f"⚠️ {stack_name}: {status}")
                
        except cf_client.exceptions.ClientError:
            print(f"❌ {stack_name}: NOT DEPLOYED")
    
    # Check Step Functions
    sf_client = boto3.client('stepfunctions')
    
    try:
        state_machines = sf_client.list_state_machines()
        
        test_agents = [
            'test-sql-approval-agent-prod',
            'test-automation-remote-agent-prod'
        ]
        
        print("\n📋 Step Functions Status:")
        for sm in state_machines['stateMachines']:
            if any(agent in sm['name'] for agent in test_agents):
                print(f"✅ {sm['name']}: ACTIVE")
                
    except Exception as e:
        print(f"❌ Error checking Step Functions: {e}")
    
    # Check Activities
    try:
        activities = sf_client.list_activities()
        
        print("\n🎯 Activities Status:")
        for activity in activities['activities']:
            if 'test' in activity['name'] or 'approval' in activity['name'] or 'remote' in activity['name']:
                print(f"✅ {activity['name']}: ACTIVE")
                
    except Exception as e:
        print(f"❌ Error checking Activities: {e}")


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'deploy':
        deploy_test_agents()
    elif command == 'test-sql':
        test_sql_approval_agent()
    elif command == 'test-remote':
        test_remote_execution_agent()
    elif command == 'status':
        check_deployment_status()
    elif command == 'test':
        print("🧪 Running all tests...")
        test_sql_approval_agent()
        print("\n" + "="*50 + "\n")
        test_remote_execution_agent()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()