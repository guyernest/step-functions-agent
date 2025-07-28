#!/usr/bin/env python3
"""
CloudFormation Stack Dependency Analyzer

This tool queries AWS CloudFormation to:
1. List all stacks (optionally filtered by tags or naming patterns)
2. Show their exports and imports
3. Generate a dependency diagram
4. Help identify missing exports or mismatched names
"""

import boto3
import json
import argparse
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import re


class CloudFormationAnalyzer:
    def __init__(self, profile: str = None, region: str = 'us-east-1'):
        """Initialize the analyzer with AWS credentials"""
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        
        self.cfn = session.client('cloudformation', region_name=region)
        self.region = region
        
    def get_stacks(self, name_pattern: str = None, tags: Dict[str, str] = None) -> List[Dict]:
        """Get all stacks, optionally filtered by name pattern or tags"""
        all_stacks = []
        paginator = self.cfn.get_paginator('describe_stacks')
        
        for page in paginator.paginate():
            for stack in page['Stacks']:
                # Skip stacks in DELETE_COMPLETE state
                if stack['StackStatus'] == 'DELETE_COMPLETE':
                    continue
                    
                # Apply name filter if provided
                if name_pattern and not re.search(name_pattern, stack['StackName']):
                    continue
                
                # Apply tag filter if provided
                if tags:
                    stack_tags = {tag['Key']: tag['Value'] for tag in stack.get('Tags', [])}
                    if not all(stack_tags.get(k) == v for k, v in tags.items()):
                        continue
                
                all_stacks.append(stack)
        
        return all_stacks
    
    def get_stack_exports(self, stack_name: str) -> List[Dict]:
        """Get all exports from a specific stack"""
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
        except Exception as e:
            print(f"Error getting exports for {stack_name}: {e}")
            return []
    
    def get_stack_imports(self, stack_name: str) -> List[str]:
        """Get all imports used by a specific stack"""
        try:
            # Get stack template
            response = self.cfn.get_template(StackName=stack_name)
            template = response['TemplateBody']
            
            # Parse template to find Fn::ImportValue references
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
            return list(set(imports))  # Remove duplicates
            
        except Exception as e:
            print(f"Error getting imports for {stack_name}: {e}")
            return []
    
    def analyze_dependencies(self, stacks: List[Dict]) -> Dict:
        """Analyze dependencies between stacks"""
        analysis = {
            'stacks': {},
            'exports': {},
            'imports': {},
            'missing_exports': set(),
            'unused_exports': set()
        }
        
        # Collect all exports and imports
        all_exports = {}
        all_imports = set()
        
        for stack in stacks:
            stack_name = stack['StackName']
            
            # Get exports
            exports = self.get_stack_exports(stack_name)
            analysis['stacks'][stack_name] = {
                'status': stack['StackStatus'],
                'exports': exports,
                'imports': []
            }
            
            for export in exports:
                export_name = export['Name']
                all_exports[export_name] = stack_name
                analysis['exports'][export_name] = {
                    'stack': stack_name,
                    'value': export['Value']
                }
            
            # Get imports
            imports = self.get_stack_imports(stack_name)
            analysis['stacks'][stack_name]['imports'] = imports
            all_imports.update(imports)
        
        # Find missing exports (imports that don't have corresponding exports)
        analysis['missing_exports'] = all_imports - set(all_exports.keys())
        
        # Find unused exports (exports that aren't imported by any stack in our filter)
        analysis['unused_exports'] = set(all_exports.keys()) - all_imports
        
        return analysis
    
    def generate_mermaid_diagram(self, analysis: Dict) -> str:
        """Generate a Mermaid diagram of stack dependencies"""
        lines = ["```mermaid", "graph TD"]
        
        # Define stack nodes with status indicators
        for stack_name, stack_info in analysis['stacks'].items():
            status = stack_info['status']
            if status == 'CREATE_COMPLETE' or status == 'UPDATE_COMPLETE':
                emoji = "✅"
            elif 'ROLLBACK' in status:
                emoji = "❌"
            elif 'IN_PROGRESS' in status:
                emoji = "🔄"
            else:
                emoji = "⚠️"
            
            lines.append(f'    {self._sanitize_id(stack_name)}["{stack_name}<br/>{emoji} {status}"]')
        
        # Add export relationships
        lines.append("    ")
        for export_name, export_info in analysis['exports'].items():
            exporting_stack = export_info['stack']
            
            # Find stacks that import this export
            importing_stacks = []
            for stack_name, stack_info in analysis['stacks'].items():
                if export_name in stack_info['imports']:
                    importing_stacks.append(stack_name)
            
            if importing_stacks:
                for importing_stack in importing_stacks:
                    lines.append(f'    {self._sanitize_id(exporting_stack)} -->|{export_name}| {self._sanitize_id(importing_stack)}')
            else:
                # Show unused exports
                lines.append(f'    {self._sanitize_id(exporting_stack)} -.->|{export_name}| UNUSED[Unused Export]')
        
        # Show missing exports
        if analysis['missing_exports']:
            lines.append("    ")
            lines.append("    MISSING[Missing Exports]")
            for missing in analysis['missing_exports']:
                # Find which stacks need this export
                for stack_name, stack_info in analysis['stacks'].items():
                    if missing in stack_info['imports']:
                        lines.append(f'    MISSING -.->|{missing}| {self._sanitize_id(stack_name)}')
        
        lines.append("```")
        return "\n".join(lines)
    
    def generate_text_report(self, analysis: Dict) -> str:
        """Generate a text report of the analysis"""
        lines = ["CloudFormation Stack Analysis Report", "=" * 40, ""]
        
        # Stack Summary
        lines.append("STACK SUMMARY:")
        for stack_name, stack_info in sorted(analysis['stacks'].items()):
            lines.append(f"\n📦 {stack_name}")
            lines.append(f"   Status: {stack_info['status']}")
            
            if stack_info['exports']:
                lines.append("   Exports:")
                for export in stack_info['exports']:
                    lines.append(f"     - {export['Name']}")
            
            if stack_info['imports']:
                lines.append("   Imports:")
                for import_name in stack_info['imports']:
                    if import_name in analysis['missing_exports']:
                        lines.append(f"     - {import_name} ❌ (MISSING)")
                    else:
                        source_stack = analysis['exports'].get(import_name, {}).get('stack', 'Unknown')
                        lines.append(f"     - {import_name} (from {source_stack})")
        
        # Missing Exports
        if analysis['missing_exports']:
            lines.append("\n" + "=" * 40)
            lines.append("❌ MISSING EXPORTS:")
            lines.append("These imports are referenced but no stack exports them:")
            for missing in sorted(analysis['missing_exports']):
                # Find which stacks need this
                needing_stacks = []
                for stack_name, stack_info in analysis['stacks'].items():
                    if missing in stack_info['imports']:
                        needing_stacks.append(stack_name)
                lines.append(f"  - {missing}")
                lines.append(f"    Needed by: {', '.join(needing_stacks)}")
        
        # Unused Exports
        if analysis['unused_exports']:
            lines.append("\n" + "=" * 40)
            lines.append("⚠️  UNUSED EXPORTS:")
            lines.append("These exports exist but aren't imported by any analyzed stack:")
            for unused in sorted(analysis['unused_exports']):
                source_stack = analysis['exports'][unused]['stack']
                lines.append(f"  - {unused} (from {source_stack})")
        
        return "\n".join(lines)
    
    def _sanitize_id(self, name: str) -> str:
        """Sanitize stack name for use as Mermaid node ID"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    def export_json(self, analysis: Dict, filename: str):
        """Export analysis as JSON for further processing"""
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"Analysis exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Analyze CloudFormation stack dependencies')
    parser.add_argument('--profile', '-p', help='AWS profile name', default='CGI-PoC')
    parser.add_argument('--region', '-r', help='AWS region', default='us-east-1')
    parser.add_argument('--pattern', help='Stack name pattern (regex)', default='.*')
    parser.add_argument('--tag', action='append', help='Filter by tag (format: key=value)')
    parser.add_argument('--output', '-o', choices=['text', 'mermaid', 'json', 'all'], 
                        default='all', help='Output format')
    parser.add_argument('--json-file', help='JSON output filename', default='stack-analysis.json')
    
    args = parser.parse_args()
    
    # Parse tags
    tags = {}
    if args.tag:
        for tag in args.tag:
            if '=' in tag:
                key, value = tag.split('=', 1)
                tags[key] = value
    
    # Create analyzer
    analyzer = CloudFormationAnalyzer(profile=args.profile, region=args.region)
    
    print(f"🔍 Analyzing CloudFormation stacks in {args.region}...")
    print(f"   Profile: {args.profile}")
    print(f"   Pattern: {args.pattern}")
    if tags:
        print(f"   Tags: {tags}")
    print()
    
    # Get stacks
    stacks = analyzer.get_stacks(name_pattern=args.pattern, tags=tags)
    
    if not stacks:
        print("No stacks found matching the criteria.")
        return
    
    print(f"Found {len(stacks)} stacks")
    
    # Analyze dependencies
    analysis = analyzer.analyze_dependencies(stacks)
    
    # Output results
    if args.output in ['text', 'all']:
        print("\n" + analyzer.generate_text_report(analysis))
    
    if args.output in ['mermaid', 'all']:
        print("\n\nMERMAID DIAGRAM:")
        print(analyzer.generate_mermaid_diagram(analysis))
    
    if args.output in ['json', 'all']:
        analyzer.export_json(analysis, args.json_file)


if __name__ == '__main__':
    main()