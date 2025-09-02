#!/usr/bin/env python3
"""
Tool Name Alignment Validator

This script validates that tool names are consistent across:
1. Tool stack registrations
2. Agent tool references  
3. Lambda implementations (where possible)

Usage: python scripts/validate_tool_alignment.py
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Set, List
from collections import defaultdict

def find_tool_registrations(project_root: Path) -> Dict[str, Set[str]]:
    """Find all tool registrations in tool stacks."""
    tool_registrations = defaultdict(set)
    
    tool_stacks_dir = project_root / "stacks" / "tools"
    if not tool_stacks_dir.exists():
        return tool_registrations
    
    for py_file in tool_stacks_dir.glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            
        # Find tool_name entries in tool_specs
        tool_names = re.findall(r'"tool_name":\s*"([^"]+)"', content)
        for tool_name in tool_names:
            tool_registrations[py_file.stem].add(tool_name)
            
    return tool_registrations

def find_agent_tool_references(project_root: Path) -> Dict[str, Set[str]]:
    """Find all tool references in agent stacks."""
    agent_references = defaultdict(set)
    
    agent_stacks_dir = project_root / "stacks" / "agents"
    if not agent_stacks_dir.exists():
        return agent_references
    
    for py_file in agent_stacks_dir.glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            
        # Find tool_name entries in tool_configs
        tool_names = re.findall(r'"tool_name":\s*"([^"]+)"', content)
        for tool_name in tool_names:
            agent_references[py_file.stem].add(tool_name)
            
    return agent_references

def find_lambda_tool_implementations(project_root: Path) -> Dict[str, Set[str]]:
    """Find tool implementations in Lambda functions."""
    lambda_implementations = defaultdict(set)
    
    lambda_dir = project_root / "lambda" / "tools"
    if not lambda_dir.exists():
        return lambda_implementations
    
    # Check TypeScript/JavaScript files
    for ts_file in lambda_dir.glob("**/src/*.ts"):
        with open(ts_file, 'r') as f:
            content = f.read()
            
        # Find case statements for tool names
        tool_names = re.findall(r'case\s*["\'`]([^"\'`]+)["\'`]\s*:', content)
        for tool_name in tool_names:
            lambda_implementations[ts_file.parent.parent.name].add(tool_name)
            
        # Also check tool definitions
        tool_defs = re.findall(r'name:\s*["\'`]([^"\'`]+)["\'`]', content)
        for tool_name in tool_defs:
            lambda_implementations[ts_file.parent.parent.name].add(tool_name)
    
    # Check Python files
    for py_file in lambda_dir.glob("**/lambda_function.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            
        # Find tool name checks
        tool_names = re.findall(r'tool_name\s*==\s*["\'`]([^"\'`]+)["\'`]', content)
        for tool_name in tool_names:
            lambda_implementations[py_file.parent.name].add(tool_name)
            
    # Check Go files
    for go_file in lambda_dir.glob("**/*.go"):
        with open(go_file, 'r') as f:
            content = f.read()
            
        # Find tool name checks in Go
        tool_names = re.findall(r'toolName\s*==\s*"([^"]+)"', content)
        for tool_name in tool_names:
            lambda_implementations[go_file.parent.name].add(tool_name)
            
    return lambda_implementations

def validate_alignment(tool_registrations: Dict[str, Set[str]], 
                      agent_references: Dict[str, Set[str]],
                      lambda_implementations: Dict[str, Set[str]]) -> List[str]:
    """Validate that tool names are aligned across components."""
    issues = []
    
    # Collect all tool names from registrations
    all_registered_tools = set()
    for tools in tool_registrations.values():
        all_registered_tools.update(tools)
    
    # Collect all tool names referenced by agents
    all_referenced_tools = set()
    for tools in agent_references.values():
        all_referenced_tools.update(tools)
    
    # Check for tools referenced but not registered
    unregistered_tools = all_referenced_tools - all_registered_tools
    if unregistered_tools:
        issues.append(f"❌ Tools referenced by agents but not registered: {unregistered_tools}")
    
    # Check for tools registered but never referenced
    unreferenced_tools = all_registered_tools - all_referenced_tools
    if unreferenced_tools:
        issues.append(f"⚠️  Tools registered but never referenced by agents: {unreferenced_tools}")
    
    # Check specific agent-tool alignments
    for agent_name, referenced_tools in agent_references.items():
        for tool_name in referenced_tools:
            if tool_name not in all_registered_tools:
                issues.append(f"❌ Agent '{agent_name}' references unregistered tool: '{tool_name}'")
    
    # Check Lambda implementations match registrations
    for lambda_name, implemented_tools in lambda_implementations.items():
        # Try to find corresponding tool stack
        for stack_name, registered_tools in tool_registrations.items():
            # Simple heuristic: if names are similar
            if lambda_name.replace('-', '_') in stack_name or stack_name.replace('_stack', '') in lambda_name:
                unregistered_impl = implemented_tools - registered_tools
                if unregistered_impl:
                    issues.append(f"⚠️  Lambda '{lambda_name}' implements tools not in '{stack_name}': {unregistered_impl}")
                
                unimplemented_reg = registered_tools - implemented_tools
                if unimplemented_reg:
                    issues.append(f"❌ Stack '{stack_name}' registers tools not in Lambda '{lambda_name}': {unimplemented_reg}")
    
    return issues

def print_summary(tool_registrations: Dict[str, Set[str]], 
                  agent_references: Dict[str, Set[str]],
                  lambda_implementations: Dict[str, Set[str]]):
    """Print a summary of findings."""
    print("\n" + "="*60)
    print("TOOL NAME ALIGNMENT VALIDATION REPORT")
    print("="*60)
    
    print("\n📦 TOOL REGISTRATIONS (in tool stacks):")
    for stack_name, tools in sorted(tool_registrations.items()):
        print(f"  {stack_name}: {sorted(tools)}")
    
    print("\n🤖 AGENT REFERENCES (in agent stacks):")
    for agent_name, tools in sorted(agent_references.items()):
        if tools:  # Only show agents that reference tools
            print(f"  {agent_name}: {sorted(tools)}")
    
    print("\n⚙️  LAMBDA IMPLEMENTATIONS:")
    for lambda_name, tools in sorted(lambda_implementations.items()):
        print(f"  {lambda_name}: {sorted(tools)}")
    
    # Validate alignment
    issues = validate_alignment(tool_registrations, agent_references, lambda_implementations)
    
    if issues:
        print("\n🚨 ALIGNMENT ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ All tool names are properly aligned!")
    
    print("\n" + "="*60)

def main():
    """Main entry point."""
    # Get project root (assuming script is in scripts/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Validating tool alignment in: {project_root}")
    
    # Find all components
    tool_registrations = find_tool_registrations(project_root)
    agent_references = find_agent_tool_references(project_root)
    lambda_implementations = find_lambda_tool_implementations(project_root)
    
    # Print summary and validation
    print_summary(tool_registrations, agent_references, lambda_implementations)
    
    # Return exit code based on issues
    issues = validate_alignment(tool_registrations, agent_references, lambda_implementations)
    if any("❌" in issue for issue in issues):
        return 1  # Exit with error if critical issues found
    return 0

if __name__ == "__main__":
    exit(main())