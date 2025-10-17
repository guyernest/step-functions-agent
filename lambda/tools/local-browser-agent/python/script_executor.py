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
from nova_act import NovaAct, BOOL_SCHEMA
from nova_act.util.s3_writer import S3Writer
from profile_manager import ProfileManager


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
        navigation_timeout: int = 60000,  # milliseconds (default 60 seconds)
        nova_act_api_key: Optional[str] = None,
        profiles_dir: Optional[str] = None,
    ):
        self.s3_bucket = s3_bucket
        self.aws_profile = aws_profile
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.record_video = record_video
        self.max_steps = max_steps
        self.timeout = timeout
        self.navigation_timeout = navigation_timeout
        self.nova_act_api_key = nova_act_api_key
        self.boto_session = boto3.Session(profile_name=aws_profile)
        self.profile_manager = ProfileManager(profiles_dir) if profiles_dir else ProfileManager()

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

        # Handle session/profile configuration
        profile_user_data_dir = self.user_data_dir
        # Default: do NOT clone, so sessions persist. Clone only when isolating/parallel.
        clone_user_data_dir = False
        profile_info = {}

        # HARDCODED FOR DEMO: Always use Bt_broadband profile
        # TODO: Remove this hardcoding and use session_config.profile_name after demo
        profile_name = "Bt_broadband"
        mode = "use_profile"

        # Create minimal session config if not provided
        if not session_config:
            session_config = {"profile_name": profile_name}

        print(f"[DEMO MODE] Forcing profile to: {profile_name}", file=sys.stderr)

        if mode == "create_profile" and profile_name:
            # Create a new profile for manual login
            print(f"Creating profile: {profile_name}", file=sys.stderr)
            try:
                profile = self.profile_manager.create_profile(
                    profile_name=profile_name,
                    description=session_config.get("profile_description", ""),
                    tags=session_config.get("profile_tags", []),
                    auto_login_sites=session_config.get("auto_login_sites", [])
                )
                profile_user_data_dir = profile["user_data_dir"]
                clone_user_data_dir = False  # Don't clone when creating profile
                profile_info = {"mode": "create", "profile": profile_name}
                result["profile_created"] = profile_name
            except ValueError as e:
                # Profile already exists, use it
                print(f"Profile exists, using existing: {e}", file=sys.stderr)
                profile_config = self.profile_manager.get_nova_act_config(
                    profile_name,
                    clone_for_parallel=session_config.get("clone_for_parallel", False)
                )
                profile_user_data_dir = profile_config["user_data_dir"]
                clone_user_data_dir = profile_config["clone_user_data_dir"]
                profile_info = {"mode": "existing", "profile": profile_name}

        elif profile_name:
            # Use existing profile
            print(f"Using profile: {profile_name}", file=sys.stderr)
            try:
                profile_config = self.profile_manager.get_nova_act_config(
                    profile_name,
                    clone_for_parallel=session_config.get("clone_for_parallel", False)
                )
                profile_user_data_dir = profile_config["user_data_dir"]
                clone_user_data_dir = profile_config["clone_user_data_dir"]
                profile_info = {"mode": "use", "profile": profile_name}

                # Check if session is still valid
                if not self.profile_manager.is_session_valid(profile_name):
                    print(f"Warning: Profile session may have expired", file=sys.stderr)
                    result["session_expired_warning"] = True

            except ValueError as e:
                print(f"Profile not found: {e}", file=sys.stderr)
                return {
                    "success": False,
                    "error": f"Profile '{profile_name}' not found"
                }

        # Execute script with Nova Act
        nova = None
        try:
            # Build NovaAct kwargs
            # Note: We use a fast-loading placeholder (google.com) as starting_page
            # Then we'll use nova.go_to_url() to navigate to the actual target, which respects go_to_url_timeout
            nova_act_kwargs = {
                "starting_page": starting_page,
                "user_data_dir": profile_user_data_dir,
                "clone_user_data_dir": clone_user_data_dir,
                "headless": self.headless and not session_config.get("requires_human_login", False),
                "record_video": self.record_video,
                "stop_hooks": stop_hooks,
                "ignore_https_errors": True,
                # "go_to_url_timeout": self.navigation_timeout // 1000,  # Convert milliseconds to seconds
                "go_to_url_timeout": 120  # Testing extended timeout
            }

            # Add profile info to result
            if profile_info:
                result["profile_used"] = profile_info

            # Add Nova Act API key if provided (otherwise uses NOVA_ACT_API_KEY env var)
            # Note: Cannot use both API key and boto_session
            if self.nova_act_api_key:
                nova_act_kwargs["nova_act_api_key"] = self.nova_act_api_key
            else:
                # Use boto session for IAM-based auth (requires allowlist)
                nova_act_kwargs["boto_session"] = self.boto_session

            # Track active user_data_dir for validation steps
            self._active_user_data_dir = profile_user_data_dir

            # Create NovaAct instance
            nova = NovaAct(**nova_act_kwargs)
            nova.start()
            # # Navigate to actual target page using go_to_url (respects go_to_url_timeout)
            # print(f"Navigating to: {starting_page} (timeout: {self.navigation_timeout // 1000}s)", file=sys.stderr)
            # nova.go_to_url(starting_page)

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

                # Verify login if verification prompt provided
                verification_prompt = session_config.get("post_login_verification")
                if verification_prompt:
                    try:
                        verify_result = nova.act(verification_prompt, schema=BOOL_SCHEMA)
                        if verify_result.matches_schema and verify_result.parsed_response:
                            print("✓ Login verified successfully", file=sys.stderr)
                            result["login_verified"] = True
                        else:
                            print("⚠ Login verification inconclusive", file=sys.stderr)
                            result["login_verified"] = False
                    except Exception as e:
                        print(f"Warning: Login verification failed: {e}", file=sys.stderr)
                        result["login_verification_error"] = str(e)

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

        finally:
            # Ensure NovaAct is properly stopped and cleaned up
            if nova is not None:
                try:
                    nova.stop()
                except Exception as e:
                    print(f"Warning: Error stopping NovaAct: {e}", file=sys.stderr)

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

        elif action == "validate_profile":
            # Validate current profile/user_data_dir statically and optionally at runtime
            mode = step.get("mode", "static")  # static|runtime|both
            active_ud = getattr(self, "_active_user_data_dir", None) or self.user_data_dir
            static = self.profile_manager.validate_user_data_dir(active_ud) if active_ud else {"status": "missing", "path_exists": False}

            runtime = None
            if mode in ("runtime", "both"):
                ui_prompt = step.get("ui_prompt")
                cookie_domains = step.get("cookie_domains")
                cookie_names = step.get("cookie_names")
                local_storage_keys = step.get("local_storage_keys")

                ui_ok = None
                cookies_ok = None
                ls_ok = None

                if ui_prompt:
                    try:
                        r = nova.act(ui_prompt, schema=BOOL_SCHEMA, max_steps=5, timeout=60)
                        ui_ok = bool(r.matches_schema and r.parsed_response)
                    except Exception as e:
                        ui_ok = False
                        step_result["ui_error"] = str(e)

                if cookie_domains and cookie_names:
                    try:
                        cookies = [c for c in nova.page.context.cookies() if any(d in (c.get("domain") or "") for d in cookie_domains)]
                        names = {c.get("name") for c in cookies}
                        cookies_ok = all(n in names for n in cookie_names)
                        step_result["cookies_found"] = sorted(list(names))
                    except Exception as e:
                        cookies_ok = False
                        step_result["cookies_error"] = str(e)

                if local_storage_keys:
                    try:
                        ls_results = {}
                        for key in local_storage_keys:
                            present = nova.page.evaluate("key => !!window.localStorage.getItem(key)", key)
                            ls_results[key] = bool(present)
                        ls_ok = all(ls_results.values()) if ls_results else None
                        step_result["local_storage"] = ls_results
                    except Exception as e:
                        ls_ok = False
                        step_result["local_storage_error"] = str(e)

                runtime = {
                    "ui_ok": ui_ok,
                    "cookies_ok": cookies_ok,
                    "local_storage_ok": ls_ok,
                }

            step_result["success"] = True
            step_result["static"] = static
            if runtime is not None:
                step_result["runtime"] = runtime

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
    parser.add_argument("--navigation-timeout", type=int, default=60000, help="Page navigation timeout in milliseconds (default: 60000)")
    parser.add_argument("--nova-act-api-key", help="Nova Act API key (or use NOVA_ACT_API_KEY env var)")
    parser.add_argument("--profiles-dir", help="Directory for browser profiles")

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
        navigation_timeout=args.navigation_timeout,
        nova_act_api_key=args.nova_act_api_key,
        profiles_dir=args.profiles_dir,
    )

    # Execute script
    result = executor.execute_script(script)

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
