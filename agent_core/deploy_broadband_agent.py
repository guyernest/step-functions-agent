#!/usr/bin/env python3
"""
Deploy Broadband Checker Agent to Bedrock Agent Core
"""

import boto3
import json
import time
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Check if bedrock_agentcore_starter_toolkit is available
try:
    from bedrock_agentcore_starter_toolkit import Runtime
    HAS_STARTER_TOOLKIT = True
except ImportError:
    HAS_STARTER_TOOLKIT = False
    print("Warning: bedrock_agentcore_starter_toolkit not installed")
    print("Install with: pip install bedrock-agentcore-starter-toolkit")

def create_iam_role(agent_name: str, region: str = "us-west-2") -> str:
    """
    Create or get IAM role for Agent Core runtime with S3 permissions
    """
    iam_client = boto3.client('iam')
    role_name = f"AgentCoreRuntime-{agent_name}"
    
    # Trust policy for Agent Core
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                        "bedrock-agentcore.amazonaws.com",
                        "lambda.amazonaws.com"
                    ]
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Execution policy with S3 and Lambda permissions
    execution_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::*/*",
                    "arn:aws:s3:::*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue"
                ],
                "Resource": "arn:aws:secretsmanager:*:*:secret:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParameterHistory"
                ],
                "Resource": [
                    "arn:aws:ssm:*:*:parameter/agentcore/*",
                    "arn:aws:ssm:*:*:parameter/agentcore/nova-act-api-key"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Check if role exists
        try:
            response = iam_client.get_role(RoleName=role_name)
            print(f"✓ Using existing role: {role_name}")
            return response['Role']['Arn']
        except iam_client.exceptions.NoSuchEntityException:
            pass
        
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Execution role for Agent Core: {agent_name}"
        )
        
        # Add inline policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCoreExecutionPolicy",
            PolicyDocument=json.dumps(execution_policy)
        )
        
        print(f"✓ Created role: {role_name}")
        
        # Wait for role to propagate
        time.sleep(10)
        
        return response['Role']['Arn']
        
    except Exception as e:
        print(f"❌ Error creating role: {e}")
        raise

def build_docker_image(agent_name: str) -> bool:
    """
    Build Docker image locally for testing
    """
    import subprocess
    
    print(f"Building Docker image for {agent_name}...")
    
    dockerfile = "Dockerfile.broadband"
    image_name = f"broadband-checker-agent:latest"
    
    try:
        # Build the Docker image
        cmd = [
            "docker", "build",
            "-f", dockerfile,
            "-t", image_name,
            "."
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Docker image built successfully: {image_name}")
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error building Docker image: {e}")
        return False

def test_local_docker(image_name: str = "broadband-checker-agent:latest") -> bool:
    """
    Test the Docker container locally
    """
    import subprocess
    
    print(f"Testing Docker container locally...")
    
    try:
        # Run container with test payload
        cmd = [
            "docker", "run",
            "--rm",
            "-e", "AWS_REGION=us-west-2",
            "-e", "BYPASS_TOOL_CONSENT=true",
            image_name,
            "python", "-c",
            """
import json
from broadband_checker_agent import handler
result = handler({'test': True}, {})
print(json.dumps(result, indent=2))
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✓ Local test passed")
            print(f"Output: {result.stdout[:500]}")
            return True
        else:
            print(f"❌ Local test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Local test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing locally: {e}")
        return False

def deploy_with_toolkit(agent_name: str, region: str = "us-west-2") -> Optional[Dict[str, Any]]:
    """
    Deploy using bedrock-agentcore-starter-toolkit
    """
    if not HAS_STARTER_TOOLKIT:
        print("❌ Starter toolkit not available")
        return None
    
    print(f"Deploying {agent_name} with Agent Core starter toolkit...")
    
    # Create IAM role
    role_arn = create_iam_role(agent_name, region)
    
    # Initialize runtime
    runtime = Runtime()
    
    try:
        # Configure the runtime
        print("Configuring runtime...")
        response = runtime.configure(
            entrypoint="broadband_checker_agent.py",
            execution_role=role_arn,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region
        )
        print(f"✓ Configuration complete")
        
        # Launch the agent
        print("Launching agent...")
        launch_result = runtime.launch()
        
        deployment_info = {
            "agent_id": launch_result.agent_id,
            "agent_arn": launch_result.agent_arn,
            "ecr_uri": launch_result.ecr_uri,
            "role_arn": role_arn,
            "region": region,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"✓ Agent launched successfully")
        print(f"  Agent ID: {deployment_info['agent_id']}")
        print(f"  Agent ARN: {deployment_info['agent_arn']}")
        
        return deployment_info
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return None

def deploy_as_lambda(agent_name: str, region: str = "us-west-2") -> Optional[Dict[str, Any]]:
    """
    Alternative: Deploy as Lambda function for testing
    """
    import zipfile
    import tempfile
    import subprocess
    import shutil
    
    print(f"Deploying {agent_name} as Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name=region)
    
    # Create temporary directory for dependencies
    with tempfile.TemporaryDirectory() as temp_dir:
        # Install dependencies to temp directory
        print("Installing dependencies...")
        # Use Lambda-specific requirements if available
        req_file = "requirements-lambda.txt" if os.path.exists("requirements-lambda.txt") else "requirements.txt"
        
        subprocess.run([
            "pip", "install", "-r", req_file,
            "-t", temp_dir,
            "--upgrade"
        ], check=True, capture_output=True)
        
        # Copy agent files to temp directory
        # Use Lambda version if available
        if os.path.exists('broadband_checker_lambda.py'):
            shutil.copy('broadband_checker_lambda.py', os.path.join(temp_dir, 'broadband_checker_agent.py'))
        else:
            shutil.copy('broadband_checker_agent.py', temp_dir)
        shutil.copy('broadband_extraction_config.json', temp_dir)
        
        # Create deployment package
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            zip_path = tmp_file.name
        
        # Create zip file with all dependencies
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files from temp directory
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arc_name)
    
    try:
        # Create or update function
        function_name = f"broadband-checker-agent-{region}"
        role_arn = create_iam_role(agent_name, region)
        
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        try:
            # Try to update existing function
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            print(f"✓ Updated existing Lambda function: {function_name}")
            
        except lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='broadband_checker_agent.handler',
                Code={'ZipFile': zip_content},
                Description='Broadband availability checker agent',
                Timeout=120,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'BYPASS_TOOL_CONSENT': 'true'
                    }
                }
            )
            print(f"✓ Created new Lambda function: {function_name}")
        
        deployment_info = {
            "function_name": function_name,
            "function_arn": response['FunctionArn'],
            "role_arn": role_arn,
            "region": region,
            "deployment_type": "lambda",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return deployment_info
        
    except Exception as e:
        print(f"❌ Lambda deployment failed: {e}")
        return None
    finally:
        # Cleanup temp file
        if os.path.exists(zip_path):
            os.remove(zip_path)

def test_deployment(deployment_info: Dict[str, Any]) -> bool:
    """
    Test the deployed agent
    """
    print("\nTesting deployed agent...")
    
    test_payload = {
        "test": True
    }
    
    try:
        if deployment_info.get("deployment_type") == "lambda":
            # Test Lambda function
            lambda_client = boto3.client('lambda', region_name=deployment_info['region'])
            
            response = lambda_client.invoke(
                FunctionName=deployment_info['function_name'],
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            result = json.loads(response['Payload'].read())
            print(f"✓ Test successful")
            print(f"Response: {json.dumps(result, indent=2)[:500]}")
            return True
            
        else:
            # Test Agent Core deployment
            # Would need Agent Core client setup
            print("⚠️  Agent Core testing requires manual verification in console")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def save_deployment_info(deployment_info: Dict[str, Any], agent_name: str):
    """
    Save deployment information to file
    """
    output_file = f"deployment-{agent_name}-{deployment_info.get('region', 'unknown')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"\n✓ Deployment info saved to: {output_file}")

def main():
    """
    Main deployment orchestrator
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy Broadband Checker Agent")
    parser.add_argument("--agent-name", default="broadband-checker", help="Agent name")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--deployment-type", choices=["agentcore", "lambda", "local"], 
                       default="lambda", help="Deployment type")
    parser.add_argument("--build-docker", action="store_true", help="Build Docker image")
    parser.add_argument("--test", action="store_true", help="Test after deployment")
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════╗
║     Broadband Checker Agent Deployment Tool      ║
╚══════════════════════════════════════════════════╝
    
Agent Name: {args.agent_name}
Region: {args.region}
Deployment Type: {args.deployment_type}
""")
    
    # Check required files
    required_files = [
        "broadband_checker_agent.py",
        "broadband_extraction_config.json",
        "requirements.txt"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file not found: {file}")
            print("Please run this script from the agent_core directory")
            return 1
    
    deployment_info = None
    
    # Build Docker if requested
    if args.build_docker or args.deployment_type == "local":
        if not build_docker_image(args.agent_name):
            print("❌ Docker build failed")
            return 1
        
        if args.deployment_type == "local":
            # Test locally only
            if test_local_docker():
                print("\n✅ Local testing successful!")
                return 0
            else:
                return 1
    
    # Deploy based on type
    if args.deployment_type == "agentcore":
        deployment_info = deploy_with_toolkit(args.agent_name, args.region)
    elif args.deployment_type == "lambda":
        deployment_info = deploy_as_lambda(args.agent_name, args.region)
    
    if not deployment_info:
        print("\n❌ Deployment failed")
        return 1
    
    # Save deployment info
    save_deployment_info(deployment_info, args.agent_name)
    
    # Test if requested
    if args.test:
        test_deployment(deployment_info)
    
    print(f"""
╔══════════════════════════════════════════════════╗
║           Deployment Complete! 🎉                ║
╚══════════════════════════════════════════════════╝

Next steps:
1. Test the agent with a sample address
2. Configure Step Functions for batch processing
3. Monitor in CloudWatch Logs
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())