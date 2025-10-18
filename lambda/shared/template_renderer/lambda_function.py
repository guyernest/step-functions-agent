"""
Template Renderer Lambda Function

Renders browser automation script templates using Mustache/Handlebars syntax.
Used by Step Functions state machines to populate templates with LLM-provided variables.

Input:
{
  "template": {
    "session": {"profile_name": "Bt_broadband"},
    "steps": [
      {"action": "act", "prompt": "Fill in {{building_number}}..."}
    ]
  },
  "variables": {
    "building_number": "23",
    "street": "High Street",
    "postcode": "SW1A 1AA"
  }
}

Output:
{
  "rendered_script": {
    "session": {"profile_name": "Bt_broadband"},
    "steps": [
      {"action": "act", "prompt": "Fill in 23..."}
    ]
  }
}
"""

import json
import logging
from typing import Any, Dict
import chevron

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def render_template(template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively render a template with variables using Mustache syntax.

    Args:
        template: Template dictionary with {{placeholder}} syntax
        variables: Dictionary of variable values to substitute

    Returns:
        Rendered template with all placeholders replaced
    """
    # Convert template to JSON string for Mustache rendering
    template_str = json.dumps(template, indent=2)

    # Render with Mustache/Handlebars syntax
    # chevron supports:
    # - {{variable}} - simple variable substitution
    # - {{#condition}}...{{/condition}} - conditional sections
    # - {{^condition}}...{{/condition}} - inverted sections (if not)
    # - {{#list}}...{{/list}} - iteration over lists
    rendered_str = chevron.render(template_str, variables)

    # Parse back to JSON
    rendered_template = json.loads(rendered_str)

    return rendered_template


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for template rendering.

    Args:
        event: Contains 'template' and 'variables' keys
        context: Lambda context (unused)

    Returns:
        Dictionary with 'rendered_script' key containing the rendered template
    """
    try:
        logger.info(f"Rendering template with variables: {json.dumps(event, default=str)}")

        # Extract template and variables from event
        template = event.get("template")
        variables = event.get("variables", {})

        if not template:
            raise ValueError("Missing 'template' in event")

        # Render the template
        rendered_script = render_template(template, variables)

        logger.info("Template rendering completed successfully")

        return {
            "rendered_script": rendered_script
        }

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in template rendering: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"Error rendering template: {str(e)}"
        logger.error(error_msg)
        raise
