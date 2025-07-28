#!/usr/bin/env python3
"""
Tag-based CloudFormation Stack Analyzer

This tool uses tags to identify and analyze related stacks in CDK applications.
It can handle both standalone and extended architectures by tracking application tags.
"""

import boto3
import json
import argparse
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from datetime import datetime


class TagBasedStackAnalyzer:
    def __init__(self, profile: str = None, region: str = 'us-east-1'):
        """Initialize the analyzer with AWS credentials"""
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        self.cfn = session.client('cloudformation', region_name=region)
        self.region = region
        
    def get_stacks_by_tags(self, required_tags: Dict[str, str] = None, any_tags: List[str] = None) -> List[Dict]:
        """
        Get stacks filtered by tags
        
        Args:
            required_tags: All these tags must match (AND condition)
            any_tags: Match if stack has any of these tag keys (OR condition)
        """
        all_stacks = []
        paginator = self.cfn.get_paginator('describe_stacks')
        
        for page in paginator.paginate():
            for stack in page['Stacks']:
                # Skip deleted stacks
                if stack['StackStatus'] == 'DELETE_COMPLETE':
                    continue
                
                stack_tags = {tag['Key']: tag['Value'] for tag in stack.get('Tags', [])}
                
                # Check required tags (AND)
                if required_tags:
                    if not all(stack_tags.get(k) == v for k, v in required_tags.items()):
                        continue
                
                # Check any tags (OR)
                if any_tags:
                    if not any(tag in stack_tags for tag in any_tags):
                        continue
                
                # Include the stack with its tags
                stack['ParsedTags'] = stack_tags
                all_stacks.append(stack)
        
        return all_stacks
    
    def analyze_application_stacks(self, app_name: str, env: str = None) -> Dict:
        """Analyze all stacks belonging to a specific application"""
        # Define tag patterns for different applications
        app_patterns = {
            'main': {
                'required': {'Application': 'AIAgents'},
                'optional': {'Component': ['Infrastructure', 'Tool', 'Agent', 'Monitoring', 'LLM']}
            },
            'long-content': {
                'required': {'Application': 'AIAgentsLongContent'},
                'optional': {'Component': ['Extension', 'Infrastructure', 'LLM', 'Tool', 'Agent']}
            },
            'flexible': {
                'required': {'Application': 'AIAgentsFlexible'},
                'optional': {'DeploymentMode': ['Standalone', 'Extended', 'Hybrid']}
            },
            # Legacy patterns for existing stacks
            'legacy': {
                'required': {'ManagedBy': 'CDK'},
                'optional': {}
            }
        }
        
        pattern = app_patterns.get(app_name, {'required': {'Application': app_name}})
        
        # Add environment filter if specified
        if env:
            pattern['required']['Environment'] = env
        
        # Get stacks
        stacks = self.get_stacks_by_tags(required_tags=pattern['required'])
        
        # Organize analysis
        analysis = {
            'application': app_name,
            'environment': env,
            'stacks_by_component': defaultdict(list),
            'stacks_by_status': defaultdict(list),
            'dependencies': {},
            'issues': [],
            'tag_summary': defaultdict(set)
        }
        
        for stack in stacks:
            stack_name = stack['StackName']
            tags = stack['ParsedTags']
            
            # Group by component
            component = tags.get('Component', 'Unknown')
            analysis['stacks_by_component'][component].append({
                'name': stack_name,
                'status': stack['StackStatus'],
                'tags': tags
            })
            
            # Group by status
            analysis['stacks_by_status'][stack['StackStatus']].append(stack_name)
            
            # Collect all tag values
            for key, value in tags.items():
                analysis['tag_summary'][key].add(value)
            
            # Get dependencies
            imports = self._get_stack_imports(stack_name)
            exports = self._get_stack_exports(stack_name)
            
            analysis['dependencies'][stack_name] = {
                'imports': imports,
                'exports': [e['Name'] for e in exports]
            }
        
        # Identify issues
        self._identify_issues(analysis)
        
        return analysis
    
    def _get_stack_imports(self, stack_name: str) -> List[str]:
        """Get imports for a stack"""
        try:
            response = self.cfn.get_template(StackName=stack_name)
            template = response['TemplateBody']
            imports = []
            
            def find_imports(obj):
                if isinstance(obj, dict):
                    if 'Fn::ImportValue' in obj:
                        import_name = obj['Fn::ImportValue']
                        if isinstance(import_name, str):
                            imports.append(import_name)
                    for value in obj.values():
                        find_imports(value)
                elif isinstance(obj, list):
                    for item in obj:
                        find_imports(item)
            
            find_imports(template)
            return list(set(imports))
        except:
            return []
    
    def _get_stack_exports(self, stack_name: str) -> List[Dict]:
        """Get exports from a stack"""
        try:
            exports = []
            paginator = self.cfn.get_paginator('list_exports')
            
            for page in paginator.paginate():
                for export in page.get('Exports', []):
                    if export['ExportingStackId'].endswith(f"/{stack_name}/"):
                        exports.append({
                            'Name': export['Name'],
                            'Value': export['Value']
                        })
            return exports
        except:
            return []
    
    def _identify_issues(self, analysis: Dict):
        """Identify common issues in the deployment"""
        # Check for failed stacks
        for status, stacks in analysis['stacks_by_status'].items():
            if 'FAILED' in status or 'ROLLBACK' in status:
                for stack in stacks:
                    analysis['issues'].append(f"Stack {stack} is in {status} state")
        
        # Check for missing imports
        all_exports = set()
        for stack_name, deps in analysis['dependencies'].items():
            all_exports.update(deps['exports'])
        
        for stack_name, deps in analysis['dependencies'].items():
            for import_name in deps['imports']:
                if import_name not in all_exports:
                    analysis['issues'].append(f"Stack {stack_name} imports {import_name} which is not exported")
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate a human-readable report"""
        lines = [
            f"Tag-based Stack Analysis for {analysis['application']}",
            "=" * 60,
            f"Environment: {analysis['environment'] or 'All'}",
            f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Stack summary by component
        lines.append("STACKS BY COMPONENT:")
        for component, stacks in sorted(analysis['stacks_by_component'].items()):
            lines.append(f"\n  {component}:")
            for stack in stacks:
                status_emoji = "✅" if "COMPLETE" in stack['status'] and "ROLLBACK" not in stack['status'] else "❌"
                lines.append(f"    {status_emoji} {stack['name']} [{stack['status']}]")
                # Show key tags
                key_tags = {k: v for k, v in stack['tags'].items() 
                           if k not in ['Application', 'Environment', 'Component']}
                if key_tags:
                    lines.append(f"       Tags: {key_tags}")
        
        # Issues
        if analysis['issues']:
            lines.append("\n" + "=" * 60)
            lines.append("❌ ISSUES FOUND:")
            for issue in analysis['issues']:
                lines.append(f"  - {issue}")
        
        # Tag summary
        lines.append("\n" + "=" * 60)
        lines.append("TAG SUMMARY:")
        for tag_key, values in sorted(analysis['tag_summary'].items()):
            lines.append(f"  {tag_key}: {', '.join(sorted(values))}")
        
        # Recommendations
        lines.append("\n" + "=" * 60)
        lines.append("💡 RECOMMENDATIONS:")
        
        if not analysis['stacks_by_component']:
            lines.append("  - No stacks found with the specified tags")
            lines.append("  - Ensure stacks are tagged with Application and Environment tags")
        elif analysis['issues']:
            lines.append("  - Fix the issues listed above before proceeding")
        else:
            lines.append("  - All stacks appear healthy")
        
        return "\n".join(lines)
    
    def generate_mermaid_diagram(self, analysis: Dict) -> str:
        """Generate a Mermaid diagram showing component relationships"""
        lines = ["```mermaid", "graph TD"]
        
        # Create subgraphs by component
        for component, stacks in analysis['stacks_by_component'].items():
            lines.append(f'    subgraph "{component}"')
            for stack in stacks:
                stack_id = stack['name'].replace('-', '_')
                emoji = "✅" if "COMPLETE" in stack['status'] and "ROLLBACK" not in stack['status'] else "❌"
                lines.append(f'        {stack_id}["{stack["name"]}<br/>{emoji}"]')
            lines.append("    end")
        
        # Add dependencies
        lines.append("")
        for stack_name, deps in analysis['dependencies'].items():
            stack_id = stack_name.replace('-', '_')
            for export in deps['exports']:
                # Find stacks that import this
                for other_stack, other_deps in analysis['dependencies'].items():
                    if export in other_deps['imports']:
                        other_id = other_stack.replace('-', '_')
                        lines.append(f'    {stack_id} -->|{export}| {other_id}')
        
        lines.append("```")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze CloudFormation stacks by tags')
    parser.add_argument('--profile', '-p', help='AWS profile name', default='CGI-PoC')
    parser.add_argument('--region', '-r', help='AWS region', default='eu-west-1')
    parser.add_argument('--app', '-a', choices=['main', 'long-content', 'flexible', 'legacy'],
                        help='Application type to analyze')
    parser.add_argument('--env', '-e', help='Environment (dev, prod)')
    parser.add_argument('--tag', action='append', help='Additional tag filters (key=value)')
    parser.add_argument('--output', '-o', choices=['report', 'mermaid', 'json', 'all'], 
                        default='report', help='Output format')
    
    args = parser.parse_args()
    
    analyzer = TagBasedStackAnalyzer(profile=args.profile, region=args.region)
    
    if args.app:
        # Analyze specific application
        analysis = analyzer.analyze_application_stacks(args.app, args.env)
    else:
        # Custom tag analysis
        tags = {}
        if args.tag:
            for tag in args.tag:
                if '=' in tag:
                    key, value = tag.split('=', 1)
                    tags[key] = value
        
        if not tags:
            print("Error: Either --app or --tag must be specified")
            return
        
        stacks = analyzer.get_stacks_by_tags(required_tags=tags)
        analysis = {
            'application': 'Custom',
            'environment': args.env,
            'stacks_by_component': {'All': [{'name': s['StackName'], 'status': s['StackStatus'], 'tags': s.get('ParsedTags', {})} for s in stacks]},
            'stacks_by_status': defaultdict(list),
            'dependencies': {},
            'issues': [],
            'tag_summary': defaultdict(set)
        }
    
    # Output results
    if args.output in ['report', 'all']:
        print(analyzer.generate_report(analysis))
    
    if args.output in ['mermaid', 'all']:
        print("\n\nMERMAID DIAGRAM:")
        print(analyzer.generate_mermaid_diagram(analysis))
    
    if args.output in ['json', 'all']:
        print("\n\nJSON OUTPUT:")
        print(json.dumps(analysis, indent=2, default=str))


if __name__ == '__main__':
    main()