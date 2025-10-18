#!/usr/bin/env python3
"""
Script to register browser automation templates in the TemplateRegistry DynamoDB table.

Usage:
    python scripts/register_template.py <template_file> [--env prod|dev]

Example:
    python scripts/register_template.py templates/broadband_availability_bt_wholesale_v1.0.0.json --env prod
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
import boto3
from botocore.exceptions import ClientError


def load_template_file(file_path: str) -> dict:
    """Load and validate template JSON file."""
    template_path = Path(file_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {file_path}")

    with open(template_path, 'r') as f:
        template_data = json.load(f)

    return template_data


def extract_metadata_from_template(template_data: dict, file_name: str) -> dict:
    """Extract metadata from the template structure."""
    # Parse version from filename (e.g., "broadband_availability_bt_wholesale_v1.0.0.json")
    name_parts = file_name.replace('.json', '').split('_v')
    template_id = name_parts[0] if len(name_parts) > 0 else "unknown"
    version = name_parts[1] if len(name_parts) > 1 else "1.0.0"

    # Extract extraction_name (same as template_id for canonical schemas)
    extraction_name = template_id

    # Get profile name from template session
    profile_name = template_data.get("session", {}).get("profile_name", "default")

    # Get starting page
    starting_page = template_data.get("starting_page", "")

    return {
        "template_id": template_id,
        "version": version,
        "extraction_name": extraction_name,
        "profile_name": profile_name,
        "starting_page": starting_page
    }


def extract_variables_from_template(template_data: dict) -> dict:
    """
    Extract variable definitions from the template.
    Scans the template for Mustache placeholders and infers their types.
    """
    import re

    # Find all {{variable}} patterns in the template JSON string
    template_str = json.dumps(template_data)
    variable_pattern = r'\{\{([^#^/][^}]*)\}\}'
    matches = re.findall(variable_pattern, template_str)

    # Deduplicate and create variable schema
    variables = {}
    for var_name in set(matches):
        var_name = var_name.strip()
        # Skip Mustache helpers and conditions
        if var_name.startswith('#') or var_name.startswith('^') or var_name.startswith('/'):
            continue

        # Infer type and create schema
        variables[var_name] = {
            "type": "string",  # Default to string
            "description": f"Value for {var_name}",
            "required": True  # Default to required
        }

    return variables


def register_template(
    template_file: str,
    env: str = "prod",
    profile: str = None,
    dry_run: bool = False
) -> dict:
    """
    Register a template in the TemplateRegistry DynamoDB table.

    Args:
        template_file: Path to the template JSON file
        env: Environment (prod, dev)
        profile: AWS profile to use
        dry_run: If True, print what would be done without actually doing it

    Returns:
        Dictionary with registration details
    """
    # Load template file
    print(f"📖 Loading template from: {template_file}")
    template_data = load_template_file(template_file)

    # Extract metadata
    file_name = Path(template_file).name
    metadata = extract_metadata_from_template(template_data, file_name)

    print(f"📝 Template ID: {metadata['template_id']}")
    print(f"📝 Version: {metadata['version']}")
    print(f"📝 Extraction Name: {metadata['extraction_name']}")
    print(f"📝 Profile: {metadata['profile_name']}")

    # Extract variables from template
    variables = extract_variables_from_template(template_data)
    print(f"📝 Found {len(variables)} variables: {list(variables.keys())}")

    # Prepare DynamoDB item
    current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Template includes starting_page - it's required by Nova Act executor
    item = {
        "template_id": {"S": metadata["template_id"]},
        "version": {"S": metadata["version"]},
        "extraction_name": {"S": metadata["extraction_name"]},
        "status": {"S": "active"},
        "template": {"S": json.dumps(template_data)},
        "variables": {"S": json.dumps(variables)},
        "metadata": {"S": json.dumps({
            "author": "schema-factory",
            "canonical_schema_id": metadata["template_id"],
            "canonical_schema_version": metadata["version"],
            "starting_url": metadata["starting_page"],
            "profile_name": metadata["profile_name"],
            "tags": ["browser-automation", "schema-driven"]
        })},
        "created_at": {"S": current_time},
        "updated_at": {"S": current_time}
    }

    if dry_run:
        print("\n🔍 DRY RUN - Would register the following item:")
        print(json.dumps(item, indent=2, default=str))
        return {"dry_run": True, "item": item}

    # Connect to DynamoDB
    session_kwargs = {}
    if profile:
        session_kwargs["profile_name"] = profile

    session = boto3.Session(**session_kwargs)
    dynamodb = session.client('dynamodb')

    table_name = f"TemplateRegistry-{env}"

    try:
        print(f"\n💾 Registering template in {table_name}...")

        response = dynamodb.put_item(
            TableName=table_name,
            Item=item
        )

        print(f"✅ Successfully registered template!")
        print(f"   Template ID: {metadata['template_id']}")
        print(f"   Version: {metadata['version']}")
        print(f"   Status: active")

        return {
            "success": True,
            "template_id": metadata["template_id"],
            "version": metadata["version"],
            "table_name": table_name,
            "response": response
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ Error registering template: {error_code} - {error_msg}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Register browser automation templates in TemplateRegistry DynamoDB table"
    )
    parser.add_argument(
        "template_file",
        help="Path to the template JSON file"
    )
    parser.add_argument(
        "--env",
        default="prod",
        choices=["prod", "dev"],
        help="Environment (default: prod)"
    )
    parser.add_argument(
        "--profile",
        help="AWS profile to use (default: from CLAUDE.local.md or environment)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without actually doing it"
    )

    args = parser.parse_args()

    # Default to CGI-PoC profile if not specified
    profile = args.profile or "CGI-PoC"

    try:
        result = register_template(
            template_file=args.template_file,
            env=args.env,
            profile=profile,
            dry_run=args.dry_run
        )

        if result.get("success"):
            print(f"\n🎉 Template registration complete!")
            sys.exit(0)
        elif result.get("dry_run"):
            print(f"\n🔍 Dry run complete - no changes made")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Failed to register template: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
