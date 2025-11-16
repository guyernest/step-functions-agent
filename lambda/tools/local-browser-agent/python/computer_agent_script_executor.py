#!/usr/bin/env python3
"""
OpenAI Computer Agent Script Executor

Executes declarative browser scripts in JSON format using OpenAI Computer Agent.
Mirrors script_executor.py but uses ComputerAgent with Workflow objects.

Script Format (same as Nova Act):
{
  "name": "Script name",
  "description": "What the script does",
  "starting_page": "https://example.com",
  "abort_on_error": false,
  "session": {
    "profile_name": "my-profile",
    "clone_for_parallel": false
  },
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
import platform
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
import boto3

# Import OpenAI Computer Agent
from computer_agent import ComputerAgent, Workflow, Task
from profile_manager import ProfileManager


class ComputerAgentScriptExecutor:
    """Executes declarative browser scripts using OpenAI Computer Agent"""

    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        aws_profile: str = "browser-agent",
        openai_model: str = "gpt-4o-mini",
        headless: bool = False,
        max_iterations: int = 30,
        timeout: int = 300,
        enable_replanning: bool = True,
        browser_channel: Optional[str] = None,
    ):
        self.s3_bucket = s3_bucket
        self.aws_profile = aws_profile
        self.openai_model = openai_model
        self.headless = headless
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.enable_replanning = enable_replanning
        self.browser_channel = browser_channel
        self.boto_session = boto3.Session(profile_name=aws_profile)
        self.profile_manager = ProfileManager()

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
        session_config = script.get("session", {})

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

        session_id = f"script_{name.replace(' ', '_').lower()}"

        # Handle session/profile configuration using tag-based resolution
        profile_user_data_dir = None
        clone_user_data_dir = False
        profile_info = {}
        profile_name = None

        # Resolve profile using ProfileManager
        try:
            if session_config:
                resolved_profile = self.profile_manager.resolve_profile(session_config, verbose=True)

                if resolved_profile:
                    # Using a named profile
                    profile_name = resolved_profile["name"]
                    profile_config = self.profile_manager.get_nova_act_config(
                        profile_name,
                        clone_for_parallel=session_config.get("clone_for_parallel", False)
                    )
                    profile_user_data_dir = profile_config["user_data_dir"]
                    clone_user_data_dir = profile_config["clone_user_data_dir"]
                    profile_info = {"mode": "resolved", "profile": profile_name, "tags": resolved_profile.get("tags", [])}

                    # Check if session is still valid
                    if not self.profile_manager.is_session_valid(profile_name):
                        print(f"⚠ Warning: Profile session may have expired", file=sys.stderr)
                        result["session_expired_warning"] = True
                else:
                    # Using temporary profile
                    print(f"→ Using temporary profile (no persistent session)", file=sys.stderr)
                    profile_info = {"mode": "temporary"}

        except ValueError as e:
            print(f"✗ Profile resolution failed: {e}", file=sys.stderr)
            return {
                "success": False,
                "error": str(e),
                "error_type": "ProfileResolutionError"
            }

        # Convert Nova Act script steps to OpenAI Computer Agent Workflow
        workflow = self._convert_script_to_workflow(
            name=name,
            description=description,
            starting_page=starting_page,
            steps=steps
        )

        # Execute script with ComputerAgent
        agent = None
        try:
            # Add profile info to result
            if profile_info:
                result["profile_used"] = profile_info

            # Log comprehensive session startup information
            print(f"[INFO] Starting ComputerAgent script execution:", file=sys.stderr)
            print(f"  - Script: {name}", file=sys.stderr)
            print(f"  - Model: {self.openai_model}", file=sys.stderr)
            print(f"  - Profile: {profile_name}", file=sys.stderr)

            # Log absolute path for profile
            if profile_user_data_dir:
                abs_profile_path = os.path.abspath(profile_user_data_dir)
                profile_exists = os.path.exists(abs_profile_path)
                print(f"  - Profile Path (absolute): {abs_profile_path}", file=sys.stderr)
                print(f"  - Profile Exists: {'✓' if profile_exists else '✗'}", file=sys.stderr)

            print(f"  - Clone Profile: {clone_user_data_dir}", file=sys.stderr)
            print(f"  - Headless Mode: {self.headless and not session_config.get('requires_human_login', False)}", file=sys.stderr)
            print(f"  - Starting Page: {starting_page}", file=sys.stderr)
            print(f"  - Browser Channel: {self.browser_channel or 'default'}", file=sys.stderr)
            print(f"  - Max Iterations: {self.max_iterations}", file=sys.stderr)
            print(f"  - Timeout: {self.timeout}s", file=sys.stderr)
            print(f"  - Total Steps: {len(steps)}", file=sys.stderr)

            # Create ComputerAgent instance
            agent = ComputerAgent(
                environment="browser",
                openai_model=self.openai_model,
                openai_api_key=os.environ.get('OPENAI_API_KEY'),
                user_data_dir=profile_user_data_dir,
                clone_user_data_dir=clone_user_data_dir if clone_user_data_dir is not None else False,
                browser_channel=self.browser_channel,
                headless=self.headless and not session_config.get("requires_human_login", False),
                starting_page=starting_page,
                max_iterations=self.max_iterations,
                enable_replanning=self.enable_replanning,
                max_replans=2,
            )

            agent.start()

            # Handle human login wait if configured
            if session_config.get("wait_for_human_login"):
                print("\n" + "="*60, file=sys.stderr)
                print("WAITING FOR HUMAN LOGIN", file=sys.stderr)
                print("="*60, file=sys.stderr)
                print(f"Browser opened to: {starting_page}", file=sys.stderr)
                print("Please complete the login process manually.", file=sys.stderr)
                print("Press ENTER when you're logged in and ready to continue...", file=sys.stderr)
                print("="*60 + "\n", file=sys.stderr)
                input()  # Wait for user confirmation

            # Execute workflow
            workflow_result = agent.execute_workflow(workflow, timeout=self.timeout)

            # Convert workflow result to script result format
            result["success"] = workflow_result.success
            result["steps_executed"] = len(workflow_result.task_results)
            result["total_duration"] = workflow_result.execution_time
            result["session_id"] = workflow_result.workflow_id

            # Convert task results to step results
            for idx, task_result in enumerate(workflow_result.task_results):
                step_result = {
                    "step_number": idx + 1,
                    "action": task_result.task_description,
                    "description": task_result.task_description,
                    "success": task_result.success,
                    "num_steps": task_result.steps_taken,
                    "duration": task_result.execution_time,
                }

                # Add output if available
                if task_result.output is not None:
                    step_result["response"] = task_result.output
                    step_result["parsed_response"] = task_result.output

                # Add error if failed
                if not task_result.success and task_result.error:
                    step_result["error"] = task_result.error

                # Add LLM feedback if available
                if task_result.llm_feedback:
                    step_result["llm_feedback"] = task_result.llm_feedback

                result["step_results"].append(step_result)

                # Check if step failed and abort_on_error is set
                if not task_result.success and abort_on_error:
                    result["success"] = False
                    result["error"] = f"Step {idx + 1} failed (abort_on_error=true): {task_result.error}"
                    break

            # Upload final screenshot to S3 if configured
            if self.s3_bucket and workflow_result.final_screenshot:
                screenshot_uri = self._upload_screenshot_to_s3(
                    screenshot=workflow_result.final_screenshot,
                    session_id=session_id,
                    filename="final_screenshot.png",
                    metadata={
                        "script_name": name,
                        "agent": "computer-agent",
                    }
                )
                result["screenshots"].append(screenshot_uri)
                result["recording_s3_uri"] = f"s3://{self.s3_bucket}/browser-scripts/{session_id}/"

        except Exception as e:
            result["success"] = False
            result["error"] = f"Script execution failed: {str(e)}"
            result["error_type"] = type(e).__name__
            result["traceback"] = traceback.format_exc()

        finally:
            # Ensure ComputerAgent is properly stopped and cleaned up
            if agent is not None:
                try:
                    agent.stop()
                except Exception as e:
                    print(f"Warning: Error stopping ComputerAgent: {e}", file=sys.stderr)

        return result

    def _convert_script_to_workflow(
        self,
        name: str,
        description: str,
        starting_page: str,
        steps: list
    ) -> Workflow:
        """Convert Nova Act script format to OpenAI Computer Agent Workflow format"""
        tasks = []

        for step in steps:
            action = step.get('action')
            prompt = step.get('prompt', '')
            step_description = step.get('description', f"{action} step")

            if action == 'act':
                tasks.append(Task(
                    action='act',
                    prompt=prompt,
                    description=step_description
                ))
            elif action == 'act_with_schema':
                schema = step.get('schema')
                tasks.append(Task(
                    action='act_with_schema',
                    prompt=prompt,
                    schema=schema,
                    description=step_description
                ))
            elif action == 'screenshot':
                tasks.append(Task(
                    action='screenshot',
                    description=step_description
                ))
            elif action == 'validate_profile':
                # Profile validation is handled by ProfileManager, not in workflow
                # Skip this step in workflow conversion
                print(f"[INFO] Skipping validate_profile step in workflow (handled separately)", file=sys.stderr)
                continue
            else:
                print(f"[WARNING] Unknown action '{action}' - skipping step", file=sys.stderr)
                continue

        return Workflow(
            name=name,
            description=description,
            starting_page=starting_page,
            tasks=tasks
        )

    def _upload_screenshot_to_s3(
        self,
        screenshot: bytes,
        session_id: str,
        filename: str,
        metadata: Dict[str, str]
    ) -> str:
        """Upload screenshot to S3 and return S3 URI"""
        try:
            s3_client = self.boto_session.client('s3')
            s3_key = f"browser-scripts/{session_id}/{filename}"

            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=screenshot,
                ContentType='image/png',
                Metadata=metadata,
            )

            return f"s3://{self.s3_bucket}/{s3_key}"
        except Exception as e:
            print(f"Warning: Failed to upload screenshot to S3: {e}", file=sys.stderr)
            return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute browser automation scripts using OpenAI Computer Agent")
    parser.add_argument("--script", required=True, help="Path to script file (JSON)")
    parser.add_argument("--aws-profile", default="browser-agent", help="AWS profile name")
    parser.add_argument("--s3-bucket", help="S3 bucket for screenshots")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--browser-channel", help="Browser channel (chrome, msedge, chromium)")
    parser.add_argument("--navigation-timeout", type=int, default=60000, help="Navigation timeout in milliseconds")
    parser.add_argument("--user-data-dir", help="Chrome user data directory for profile")

    args = parser.parse_args()

    # Read environment variables for OpenAI Computer Agent configuration
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    enable_replanning = os.environ.get("ENABLE_REPLANNING", "true").lower() == "true"
    max_replans = int(os.environ.get("MAX_REPLANS", "2"))

    try:
        # Load script from file
        with open(args.script, 'r') as f:
            script = json.load(f)

        # Create executor
        executor = ComputerAgentScriptExecutor(
            s3_bucket=args.s3_bucket,
            aws_profile=args.aws_profile,
            openai_model=openai_model,
            headless=args.headless,
            enable_replanning=enable_replanning,
            browser_channel=args.browser_channel,
        )

        # Execute script
        result = executor.execute_script(script)

        # Print result as JSON to stdout
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result.get("success", False) else 1)

    except FileNotFoundError:
        print(json.dumps({
            "success": False,
            "error": f"Script file not found: {args.script}"
        }), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "error": f"Invalid JSON in script file: {e}"
        }), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "traceback": traceback.format_exc()
        }), file=sys.stderr)
        sys.exit(1)
