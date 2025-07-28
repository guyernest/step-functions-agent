#!/usr/bin/env python3
"""
Step Functions Agent Deployment State Checker

This tool specifically analyzes the Step Functions Agent project deployment state:
1. Checks which stacks are deployed
2. Verifies exports match expected patterns
3. Identifies what's needed for long content deployment
4. Suggests fixes for common issues
"""

import boto3
import argparse
from typing import Dict, List, Set, Optional
import re
from datetime import datetime


class DeploymentStateChecker:
    def __init__(self, profile: str = 'CGI-PoC', region: str = 'us-east-1', env: str = 'prod'):
        """Initialize the checker"""
        session = boto3.Session(profile_name=profile)
        self.cfn = session.client('cloudformation', region_name=region)
        self.env = env
        self.profile = profile
        self.region = region
        
        # Expected stack patterns for main infrastructure
        self.main_stacks = {
            'SharedInfrastructure': f'SharedInfrastructureStack-{env}',
            'AgentRegistry': f'AgentRegistryStack-{env}',
            'SharedLLM': f'SharedLLMStack-{env}',
        }
        
        # Expected stack patterns for long content
        self.long_content_stacks = {
            'LambdaExtensionLayer': f'LambdaExtensionLayer-{env}',
            'SharedLongContentInfrastructure': f'SharedLongContentInfrastructure-{env}',
            'SharedLLMWithLongContent': f'SharedLLMWithLongContent-{env}',
        }
        
        # Expected exports from main infrastructure
        self.expected_main_exports = {
            'AgentRegistry': [
                f'SharedTableAgentRegistry-{env}',
                f'SharedTableArnAgentRegistry-{env}'
            ],
            'ToolRegistry': [
                f'SharedTableToolRegistry-{env}',
                f'SharedTableArnToolRegistry-{env}'
            ],
            'LLM': [
                f'SharedClaudeLambdaArn-{env}',
                f'SharedOpenAILambdaArn-{env}',
                f'SharedGeminiLambdaArn-{env}',
                f'SharedBedrockLambdaArn-{env}',
                f'SharedDeepSeekLambdaArn-{env}'
            ]
        }
        
    def check_stack_exists(self, stack_name: str) -> Optional[Dict]:
        """Check if a stack exists and return its info"""
        try:
            response = self.cfn.describe_stacks(StackName=stack_name)
            return response['Stacks'][0]
        except self.cfn.exceptions.ClientError:
            return None
    
    def get_all_exports(self) -> Dict[str, str]:
        """Get all CloudFormation exports"""
        exports = {}
        paginator = self.cfn.get_paginator('list_exports')
        
        for page in paginator.paginate():
            for export in page.get('Exports', []):
                exports[export['Name']] = export['ExportingStackId'].split('/')[-2]
        
        return exports
    
    def check_secret_exists(self, secret_name: str) -> bool:
        """Check if a Secrets Manager secret exists"""
        try:
            session = boto3.Session(profile_name=self.profile)
            sm = session.client('secretsmanager', region_name=self.region)
            sm.describe_secret(SecretId=secret_name)
            return True
        except:
            return False
    
    def analyze_deployment_state(self) -> Dict:
        """Analyze the current deployment state"""
        print(f"🔍 Analyzing deployment state for environment: {self.env}")
        print(f"   Region: {self.region}")
        print(f"   Profile: {self.profile}")
        print("=" * 60)
        
        state = {
            'main_infrastructure': {},
            'long_content_infrastructure': {},
            'exports': self.get_all_exports(),
            'issues': [],
            'recommendations': []
        }
        
        # Check main infrastructure
        print("\n📦 MAIN INFRASTRUCTURE STACKS:")
        for stack_type, stack_name in self.main_stacks.items():
            stack_info = self.check_stack_exists(stack_name)
            if stack_info:
                status = stack_info['StackStatus']
                print(f"  ✅ {stack_name}: {status}")
                state['main_infrastructure'][stack_type] = {
                    'name': stack_name,
                    'status': status,
                    'exists': True
                }
            else:
                print(f"  ❌ {stack_name}: NOT FOUND")
                state['main_infrastructure'][stack_type] = {
                    'name': stack_name,
                    'exists': False
                }
                state['issues'].append(f"Main infrastructure stack {stack_name} not found")
        
        # Check long content infrastructure
        print("\n📦 LONG CONTENT INFRASTRUCTURE STACKS:")
        for stack_type, stack_name in self.long_content_stacks.items():
            stack_info = self.check_stack_exists(stack_name)
            if stack_info:
                status = stack_info['StackStatus']
                print(f"  ✅ {stack_name}: {status}")
                state['long_content_infrastructure'][stack_type] = {
                    'name': stack_name,
                    'status': status,
                    'exists': True
                }
            else:
                print(f"  ⚠️  {stack_name}: Not deployed")
                state['long_content_infrastructure'][stack_type] = {
                    'name': stack_name,
                    'exists': False
                }
        
        # Check critical exports
        print("\n🔗 CRITICAL EXPORTS:")
        
        print("\n  Agent Registry Exports:")
        for export_name in self.expected_main_exports['AgentRegistry']:
            if export_name in state['exports']:
                print(f"    ✅ {export_name} (from {state['exports'][export_name]})")
            else:
                print(f"    ❌ {export_name} - MISSING")
                state['issues'].append(f"Missing export: {export_name}")
        
        print("\n  Tool Registry Exports:")
        for export_name in self.expected_main_exports['ToolRegistry']:
            if export_name in state['exports']:
                print(f"    ✅ {export_name} (from {state['exports'][export_name]})")
            else:
                print(f"    ❌ {export_name} - MISSING")
                state['issues'].append(f"Missing export: {export_name}")
        
        print("\n  LLM Function Exports:")
        for export_name in self.expected_main_exports['LLM']:
            if export_name in state['exports']:
                print(f"    ✅ {export_name} (from {state['exports'][export_name]})")
            else:
                print(f"    ⚠️  {export_name} - Missing (optional)")
        
        # Check secrets
        print("\n🔑 SECRETS:")
        secret_name = f"/ai-agent/llm-secrets/{self.env}"
        if self.check_secret_exists(secret_name):
            print(f"  ✅ {secret_name} exists")
        else:
            print(f"  ❌ {secret_name} - MISSING")
            state['issues'].append(f"Missing secret: {secret_name}")
        
        # Check for long content specific exports if extension layer is deployed
        if state['long_content_infrastructure'].get('LambdaExtensionLayer', {}).get('exists'):
            print("\n🔧 LONG CONTENT EXPORTS:")
            expected_lc_exports = [
                f'SharedProxyLayerX86ExtensionBuild-{self.env}',
                f'SharedProxyLayerArmExtensionBuild-{self.env}',
                f'SharedProxyLayerX86LongContent-{self.env}',
                f'SharedProxyLayerArmLongContent-{self.env}',
                f'SharedContentTableLongContent-{self.env}'
            ]
            
            for export_name in expected_lc_exports:
                if export_name in state['exports']:
                    print(f"  ✅ {export_name}")
                else:
                    print(f"  ⚠️  {export_name} - Not yet created")
        
        # Provide recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if not all(s.get('exists') for s in state['main_infrastructure'].values()):
            print("\n  ⚠️  Deploy main infrastructure first:")
            print("     cdk deploy --app 'python refactored_app.py' --all --profile CGI-PoC")
            state['recommendations'].append("Deploy main infrastructure first")
        
        elif state['issues']:
            print("\n  ❌ Fix the following issues before deploying long content:")
            for issue in state['issues']:
                print(f"     - {issue}")
        
        else:
            print("\n  ✅ Main infrastructure is ready!")
            
            if not state['long_content_infrastructure']['LambdaExtensionLayer'].get('exists'):
                print("\n  📋 Next step: Deploy long content infrastructure")
                print("     cdk deploy --app 'python long_content_app.py' --all --profile CGI-PoC")
            else:
                print("\n  ✅ Long content infrastructure is deployed!")
                
                # Check for any failed stacks
                failed_stacks = []
                for stack_info in state['long_content_infrastructure'].values():
                    if stack_info.get('exists') and 'FAILED' in stack_info.get('status', ''):
                        failed_stacks.append(stack_info['name'])
                
                if failed_stacks:
                    print(f"\n  ⚠️  Some stacks need attention: {', '.join(failed_stacks)}")
                    print("     Check CloudFormation console for details")
        
        return state
    
    def generate_import_config(self, state: Dict) -> str:
        """Generate configuration code for importing resources"""
        lines = [
            "# Configuration for importing existing resources into long content stacks",
            f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Environment: {self.env}",
            "",
            "# Add this configuration to your long content stack files:",
            ""
        ]
        
        # Agent Registry import
        if f'SharedTableArnAgentRegistry-{self.env}' in state['exports']:
            lines.extend([
                "# Import Agent Registry (in agent stacks):",
                f"agent_registry_table_name = Fn.import_value('SharedTableAgentRegistry-{self.env}')",
                f"agent_registry_table_arn = Fn.import_value('SharedTableArnAgentRegistry-{self.env}')",
                ""
            ])
        
        # Tool Registry import
        if f'SharedTableArnToolRegistry-{self.env}' in state['exports']:
            lines.extend([
                "# Import Tool Registry (in tool stacks):",
                f"tool_registry_table_name = Fn.import_value('SharedTableToolRegistry-{self.env}')",
                f"tool_registry_table_arn = Fn.import_value('SharedTableArnToolRegistry-{self.env}')",
                ""
            ])
        
        # LLM Secrets import
        lines.extend([
            "# Import LLM Secrets (in SharedLLMWithLongContentStack):",
            "from aws_cdk import aws_secretsmanager as secretsmanager",
            "self.llm_secret = secretsmanager.Secret.from_secret_name_v2(",
            "    self,",
            '    "ImportedLLMSecrets",',
            f'    secret_name="/ai-agent/llm-secrets/{self.env}"',
            ")",
            ""
        ])
        
        # Direct table imports (alternative method)
        lines.extend([
            "# Alternative: Direct table imports (if exports not available):",
            "# from aws_cdk import aws_dynamodb as dynamodb",
            "# agent_registry_table = dynamodb.Table.from_table_name(",
            "#     self,",
            '#     "ImportedAgentRegistry",',
            f'#     "AgentRegistry-{self.env}"',
            "# )",
            ""
        ])
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Check Step Functions Agent deployment state')
    parser.add_argument('--profile', '-p', help='AWS profile name', default='CGI-PoC')
    parser.add_argument('--region', '-r', help='AWS region', default='us-east-1')
    parser.add_argument('--env', '-e', help='Environment name', default='prod')
    parser.add_argument('--generate-config', '-g', action='store_true', 
                        help='Generate import configuration code')
    
    args = parser.parse_args()
    
    checker = DeploymentStateChecker(
        profile=args.profile,
        region=args.region,
        env=args.env
    )
    
    state = checker.analyze_deployment_state()
    
    if args.generate_config:
        print("\n" + "=" * 60)
        print("📝 IMPORT CONFIGURATION:")
        print("=" * 60)
        print(checker.generate_import_config(state))
        
        # Save to file
        config_file = f"import_config_{args.env}.py"
        with open(config_file, 'w') as f:
            f.write(checker.generate_import_config(state))
        print(f"\nConfiguration saved to: {config_file}")


if __name__ == '__main__':
    main()