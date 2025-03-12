#!/usr/bin/env python3
"""
Script to generate a buildspec file from templates for a specific component.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path


def list_templates():
    """List all available templates."""
    templates_dir = Path(__file__).parent
    
    print("Available CDK templates:")
    cdk_templates = list(templates_dir.glob("cdk/*.yml"))
    for template in cdk_templates:
        print(f"  - {template.name}")
    
    print("\nAvailable Lambda templates:")
    lambda_templates = list(templates_dir.glob("lambda/*.yml"))
    for template in lambda_templates:
        print(f"  - {template.name}")


def generate_cdk_buildspec(stack_name, output_path):
    """Generate a buildspec for a CDK stack."""
    template_path = Path(__file__).parent / "cdk/buildspec-template.yml"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        return False
    
    # Read the template
    with open(template_path, "r") as f:
        template_content = f.read()
    
    # Replace placeholders
    stack_name_lower = stack_name.lower()
    content = template_content.replace("STACK_NAME", stack_name)
    content = content.replace("STACK_NAME_LOWERCASE", stack_name_lower)
    
    # Write the output file
    with open(output_path, "w") as f:
        f.write(content)
    
    print(f"Generated buildspec for CDK stack {stack_name} at {output_path}")
    return True


def generate_lambda_buildspec(lambda_type, lambda_dir, lambda_name, output_path):
    """Generate a buildspec for a Lambda function."""
    template_path = Path(__file__).parent / f"lambda/buildspec-{lambda_type}-lambda.yml"
    
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        return False
    
    # Read the template
    with open(template_path, "r") as f:
        template_content = f.read()
    
    # Replace placeholders
    content = template_content.replace("LAMBDA_DIR", lambda_dir)
    content = content.replace("LAMBDA_NAME", lambda_name)
    
    # Write the output file
    with open(output_path, "w") as f:
        f.write(content)
    
    print(f"Generated buildspec for {lambda_type} Lambda function at {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate buildspec files from templates")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available templates")
    
    # CDK command
    cdk_parser = subparsers.add_parser("cdk", help="Generate a CDK stack buildspec")
    cdk_parser.add_argument("stack_name", help="Name of the CDK stack (e.g., SQLAgentStack)")
    cdk_parser.add_argument("--output", "-o", default="buildspec-{stack_name}.yml", 
                            help="Output file path (default: buildspec-{stack_name}.yml)")
    
    # Lambda command
    lambda_parser = subparsers.add_parser("lambda", help="Generate a Lambda function buildspec")
    lambda_parser.add_argument("type", choices=["python", "typescript", "rust", "go", "java"], 
                              help="Type of Lambda function")
    lambda_parser.add_argument("dir", help="Directory path to the Lambda function (e.g., lambda/tools/web-scraper)")
    lambda_parser.add_argument("name", help="Name of the Lambda function (e.g., web-scraper)")
    lambda_parser.add_argument("--output", "-o", default="buildspec-{name}.yml", 
                              help="Output file path (default: buildspec-{name}.yml)")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_templates()
    elif args.command == "cdk":
        output_path = args.output.format(stack_name=args.stack_name.lower())
        generate_cdk_buildspec(args.stack_name, output_path)
    elif args.command == "lambda":
        output_path = args.output.format(name=args.name)
        generate_lambda_buildspec(args.type, args.dir, args.name, output_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()