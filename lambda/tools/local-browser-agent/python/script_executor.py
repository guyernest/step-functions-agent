#!/usr/bin/env python3
"""
Nova Act Script Executor

Executes declarative browser scripts in JSON format.
Accepts a script file path via --script argument.
Outputs results as JSON to stdout.

Script Format:
{
  "name": "Script name",
  "description": "What the script does",
  "starting_page": "https://example.com",
  "abort_on_error": false,
  "steps": [
    {
      "action": "act",
      "prompt": "Click the login button",
      "description": "Optional step description"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract the page title",
      "schema": {"type": "string"},
      "description": "Get title"
    },
    {
      "action": "screenshot",
      "description": "Capture page state"
    }
  ]
}
"""

import sys
import json
import os
import argparse
import traceback
from typing import Dict, Any, List, Optional
from pathlib import Path
import boto3
from nova_act import NovaAct
from nova_act.util.s3_writer import S3Writer


class ScriptExecutor:
    """Executes declarative browser scripts"""

    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        aws_profile: str = "browser-agent",
        user_data_dir: Optional[str] = None,
        headless: bool = False,
        record_video: bool = True,
        max_steps: int = 30,
        timeout: int = 300,
        nova_act_api_key: Optional[str] = None,
    ):
        self.s3_bucket = s3_bucket
        self.aws_profile = aws_profile
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.record_video = record_video
        self.max_steps = max_steps
        self.timeout = timeout
        self.nova_act_api_key = nova_act_api_key
        self.boto_session = boto3.Session(profile_name=aws_profile)

    def execute_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a browser script

        Args:
            script: Parsed script dictionary

        Returns:
            Execution result with all step outputs
        """
        name = script.get("name", "Unnamed Script")
        description = script.get("description", "")
        starting_page = script.get("starting_page")
        abort_on_error = script.get("abort_on_error", False)
        steps = script.get("steps", [])

        if not starting_page:
            return {
                "success": False,
                "error": "Script must have a starting_page"
            }

        if not steps:
            return {
                "success": False,
                "error": "Script must have at least one step"
            }

        # Prepare result structure
        result = {
            "success": True,
            "script_name": name,
            "script_description": description,
            "starting_page": starting_page,
            "steps_executed": 0,
            "steps_total": len(steps),
            "step_results": [],
            "screenshots": [],
            "recording_s3_uri": None,
            "session_id": None,
            "total_duration": 0,
            "error": None,
        }

        # Configure S3Writer for automatic uploads
        stop_hooks = []
        session_id = f"script_{name.replace(' ', '_').lower()}"

        if self.s3_bucket and self.record_video:
            try:
                s3_writer = S3Writer(
                    boto_session=self.boto_session,
                    s3_bucket_name=self.s3_bucket.strip(),  # Strip whitespace
                    s3_prefix=f"browser-scripts/{session_id}/",
                    metadata={
                        "script_name": name,
                        "agent": "local-browser-agent",
                    }
                )
                stop_hooks.append(s3_writer)
            except Exception as e:
                # Log S3Writer error but continue without it
                print(f"Warning: Failed to initialize S3Writer: {e}", file=sys.stderr)
                print(f"Continuing without S3 recording uploads", file=sys.stderr)

        # Execute script with Nova Act
        try:
            # Build NovaAct kwargs
            nova_act_kwargs = {
                "starting_page": starting_page,
                "user_data_dir": self.user_data_dir,
                "headless": self.headless,
                "record_video": self.record_video,
                "stop_hooks": stop_hooks,
                "ignore_https_errors": True,
            }

            # Add Nova Act API key if provided (otherwise uses NOVA_ACT_API_KEY env var)
            # Note: Cannot use both API key and boto_session
            if self.nova_act_api_key:
                nova_act_kwargs["nova_act_api_key"] = self.nova_act_api_key
            else:
                # Use boto session for IAM-based auth (requires allowlist)
                nova_act_kwargs["boto_session"] = self.boto_session

            with NovaAct(**nova_act_kwargs) as nova:

                # Execute each step
                for idx, step in enumerate(steps):
                    step_num = idx + 1
                    action = step.get("action")
                    step_desc = step.get("description", f"Step {step_num}")

                    print(f"[Step {step_num}/{len(steps)}] {action}: {step_desc}", file=sys.stderr)

                    try:
                        step_result = self._execute_step(nova, step, step_num)
                        result["step_results"].append(step_result)
                        result["steps_executed"] = step_num

                        # Collect screenshots
                        if step_result.get("screenshot_s3_uri"):
                            result["screenshots"].append(step_result["screenshot_s3_uri"])

                        # Check if step failed and abort_on_error is set
                        if not step_result.get("success", False) and abort_on_error:
                            result["success"] = False
                            result["error"] = f"Step {step_num} failed (abort_on_error=true): {step_result.get('error')}"
                            break

                    except Exception as e:
                        step_error = {
                            "step_number": step_num,
                            "action": action,
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "traceback": traceback.format_exc(),
                        }
                        result["step_results"].append(step_error)

                        if abort_on_error:
                            result["success"] = False
                            result["error"] = f"Step {step_num} failed: {str(e)}"
                            break

                # Get session metadata
                result["session_id"] = session_id
                if self.s3_bucket:
                    result["recording_s3_uri"] = f"s3://{self.s3_bucket}/browser-scripts/{session_id}/"

        except Exception as e:
            result["success"] = False
            result["error"] = f"Script execution failed: {str(e)}"
            result["error_type"] = type(e).__name__
            result["traceback"] = traceback.format_exc()

        return result

    def _execute_step(self, nova: NovaAct, step: Dict[str, Any], step_num: int) -> Dict[str, Any]:
        """Execute a single step"""
        action = step.get("action")
        description = step.get("description")

        step_result = {
            "step_number": step_num,
            "action": action,
            "description": description,
            "success": False,
        }

        if action == "act":
            prompt = step.get("prompt")
            if not prompt:
                step_result["error"] = "Act step missing prompt"
                return step_result

            act_result = nova.act(
                prompt=prompt,
                max_steps=self.max_steps,
                timeout=self.timeout,
            )

            step_result["success"] = True
            step_result["response"] = act_result.response
            step_result["num_steps"] = act_result.metadata.num_steps_executed if act_result.metadata else 0
            step_result["duration"] = (act_result.metadata.end_time - act_result.metadata.start_time) if act_result.metadata else 0

        elif action == "act_with_schema":
            prompt = step.get("prompt")
            schema = step.get("schema")

            if not prompt:
                step_result["error"] = "ActWithSchema step missing prompt"
                return step_result

            if not schema:
                step_result["error"] = "ActWithSchema step missing schema"
                return step_result

            act_result = nova.act(
                prompt=prompt,
                schema=schema,
                max_steps=self.max_steps,
                timeout=self.timeout,
            )

            step_result["success"] = True
            step_result["response"] = act_result.response
            step_result["parsed_response"] = act_result.parsed_response
            step_result["matches_schema"] = act_result.matches_schema
            step_result["num_steps"] = act_result.metadata.num_steps_executed if act_result.metadata else 0
            step_result["duration"] = (act_result.metadata.end_time - act_result.metadata.start_time) if act_result.metadata else 0

        elif action == "screenshot":
            # Nova Act doesn't have a separate screenshot method
            # Screenshots are automatically captured during act() calls
            # For now, just mark as success
            step_result["success"] = True
            step_result["message"] = "Screenshots are automatically captured during browser actions"

        else:
            step_result["error"] = f"Unknown action: {action}"
            return step_result

        return step_result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Execute Nova Act browser scripts")
    parser.add_argument("--script", required=True, help="Path to script JSON file")
    parser.add_argument("--s3-bucket", help="S3 bucket for recordings")
    parser.add_argument("--aws-profile", default="browser-agent", help="AWS profile name")
    parser.add_argument("--user-data-dir", help="Chrome user data directory")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--no-video", action="store_true", help="Disable video recording")
    parser.add_argument("--max-steps", type=int, default=30, help="Max steps per act()")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--nova-act-api-key", help="Nova Act API key (or use NOVA_ACT_API_KEY env var)")

    args = parser.parse_args()

    # Read script file
    script_path = Path(args.script)
    if not script_path.exists():
        error_result = {
            "success": False,
            "error": f"Script file not found: {args.script}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

    try:
        with open(script_path, "r") as f:
            script = json.load(f)
    except json.JSONDecodeError as e:
        error_result = {
            "success": False,
            "error": f"Invalid JSON in script file: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to read script file: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

    # Create executor
    executor = ScriptExecutor(
        s3_bucket=args.s3_bucket,
        aws_profile=args.aws_profile,
        user_data_dir=args.user_data_dir,
        headless=args.headless,
        record_video=not args.no_video,
        max_steps=args.max_steps,
        timeout=args.timeout,
        nova_act_api_key=args.nova_act_api_key,
    )

    # Execute script
    result = executor.execute_script(script)

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
