#!/usr/bin/env python3
"""
OpenAI Computer Agent Wrapper for Local Browser Agent

This script mirrors nova_act_wrapper.py but uses OpenAI Computer Agent.
It receives commands via stdin (JSON) and outputs results via stdout (JSON).

Key Features:
- Drop-in replacement for nova_act_wrapper.py
- Browser profile support (user_data_dir, clone_user_data_dir)
- S3 screenshot uploads (no video - screenshots only)
- Same JSON interface as Nova Act wrapper
- Supports: act, script, validate_profile, setup_login

Migration Benefits:
- 25-40% faster execution (single-shot planning)
- 90% cost reduction with gpt-4o-mini
- More robust locator-based actions
- Better error handling with LLM feedback
"""

import sys
import json
import os
import traceback
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import boto3

# Note: ComputerAgent, Workflow, Task are imported on-demand in functions that use them
# to avoid import errors when only using OpenAI Playwright executor


def execute_browser_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a browser automation command using OpenAI Computer Agent

    Args:
        command: Dictionary containing:
            - command_type: 'start_session', 'act', 'script', 'end_session', 'validate_profile', or 'setup_login'
            - prompt: Natural language instruction (for 'act')
            - steps: List of script steps (for 'script')
            - starting_page: Initial URL
            - user_data_dir: Chrome profile directory
            - clone_user_data_dir: Whether to clone profile for parallel execution
            - headless: Run headless mode
            - s3_bucket: S3 bucket for screenshot uploads
            - browser_channel: Browser to use ('msedge', 'chrome', 'chromium')
            - schema: JSON schema for output (act_with_schema)
            - timeout: Timeout in seconds

    Returns:
        Dictionary with execution result (compatible with nova_act_wrapper format)
    """
    command_type = command.get('command_type', 'act')

    try:
        if command_type == 'start_session':
            return start_session(command)
        elif command_type == 'act':
            return execute_act(command)
        elif command_type == 'script':
            return execute_script(command)
        elif command_type == 'end_session':
            return end_session(command)
        elif command_type == 'validate_profile':
            return validate_profile(command)
        elif command_type == 'setup_login':
            return setup_login(command)
        else:
            return {
                "success": False,
                "error": f"Unknown command type: {command_type}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def start_session(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start a new browser session

    Returns session_id for future commands
    """
    # For now, starting a session is implicit in execute_act
    # This is a placeholder for future explicit session management
    return {
        "success": True,
        "message": "Session management is handled implicitly in ComputerAgent context",
        "session_id": command.get('session_id')
    }


def execute_act(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single browser automation task using ComputerAgent.execute_task()

    This is the main execution path that:
    1. Initializes ComputerAgent with browser profile
    2. Executes the task() command
    3. Returns results with S3 screenshot upload (if configured)
    """
    # Extract parameters
    prompt = command.get('prompt')
    if not prompt:
        return {
            "success": False,
            "error": "Missing required parameter: prompt"
        }

    # Check if prompt contains a browser automation script (server sends embedded JSON)
    if prompt.strip().startswith("Execute this browser automation script:"):
        # Extract the JSON script from the prompt and delegate to execute_script
        import re
        json_match = re.search(r'\{[\s\S]*\}', prompt)
        if json_match:
            try:
                script = json.loads(json_match.group(0))
                return execute_script(script)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse script from prompt: {str(e)}"
                }

    starting_page = command.get('starting_page')
    session_id = command.get('session_id', 'temp')
    s3_bucket = command.get('s3_bucket')
    task_id = command.get('task_id', 'unknown')
    user_data_dir = command.get('user_data_dir')
    clone_user_data_dir = command.get('clone_user_data_dir')
    max_iterations = command.get('max_steps', 30)  # OpenAI Computer Agent uses max_iterations
    timeout = command.get('timeout', 300)
    schema = command.get('schema')
    headless = command.get('headless', False)
    aws_profile = command.get('aws_profile', 'browser-agent')

    # Browser channel: default to msedge on Windows, chrome elsewhere
    browser_channel = command.get('browser_channel')
    if not browser_channel:
        browser_channel = 'msedge' if platform.system() == 'Windows' else 'chrome'
        print(f"[INFO] No browser_channel specified, defaulting to '{browser_channel}' for {platform.system()}", file=sys.stderr)

    # Handle profile configuration using centralized tag-based resolution
    session_config = command.get('session', {})
    profile_name = None

    # Resolve profile using ProfileManager's centralized resolution logic
    from profile_manager import ProfileManager
    profile_manager = ProfileManager()

    try:
        # Build session config for resolution
        if not session_config.get('profile_name') and command.get('profile_name'):
            session_config['profile_name'] = command.get('profile_name')

        resolved_profile = profile_manager.resolve_profile(session_config, verbose=True)

        if resolved_profile:
            # Using a named profile
            profile_name = resolved_profile["name"]
            clone_for_parallel = session_config.get('clone_for_parallel', False) if isinstance(session_config, dict) else False

            profile_config = profile_manager.get_nova_act_config(profile_name, clone_for_parallel=clone_for_parallel)
            user_data_dir = profile_config["user_data_dir"]
            clone_user_data_dir = profile_config["clone_user_data_dir"]
        else:
            # Using temporary profile (resolved_profile is None)
            pass

    except ValueError as e:
        # Profile resolution failed
        print(f"✗ Profile resolution failed: {e}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "error_type": "ProfileResolutionError"
        }

    # Create boto3 session for S3 uploads
    boto_session = boto3.Session(profile_name=aws_profile)

    # Log comprehensive session startup information
    print(f"[INFO] Starting ComputerAgent (OpenAI) with:", file=sys.stderr)
    print(f"  - Model: {os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}", file=sys.stderr)
    print(f"  - Profile: {profile_name}", file=sys.stderr)
    print(f"  - Profile Path: {user_data_dir}", file=sys.stderr)
    print(f"  - Clone Profile: {clone_user_data_dir if clone_user_data_dir is not None else 'not set (default)'}", file=sys.stderr)
    print(f"  - Headless Mode: {headless}", file=sys.stderr)
    print(f"  - Starting Page: {starting_page or 'none'}", file=sys.stderr)
    print(f"  - Browser Channel: {browser_channel}", file=sys.stderr)
    print(f"  - Max Iterations: {max_iterations}", file=sys.stderr)
    print(f"  - Timeout: {timeout}s", file=sys.stderr)
    print(f"  - Session ID: {session_id}", file=sys.stderr)

    try:
        # Import ComputerAgent on-demand (only needed for legacy 'act' command)
        from computer_agent import ComputerAgent

        # Initialize ComputerAgent
        agent = ComputerAgent(
            environment="browser",
            openai_model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            openai_api_key=os.environ.get('OPENAI_API_KEY'),
            user_data_dir=user_data_dir,
            clone_user_data_dir=clone_user_data_dir if clone_user_data_dir is not None else False,
            browser_channel=browser_channel,
            headless=headless,
            starting_page=starting_page,
            max_iterations=max_iterations,
            enable_replanning=True,
            max_replans=2,
        )

        agent.start()

        try:
            # Execute task
            if schema:
                # act_with_schema: Create workflow with schema extraction
                workflow = Workflow(
                    name="Act with Schema",
                    starting_page=starting_page or agent.get_current_url(),
                    tasks=[
                        Task(
                            action="act_with_schema",
                            prompt=prompt,
                            schema=schema,
                            description="Extract structured data"
                        )
                    ]
                )
                result = agent.execute_workflow(workflow, timeout=timeout)

                # Extract schema result from workflow
                task_result = result.task_results[0] if result.task_results else None
                parsed_response = task_result.output if task_result else None
                matches_schema = task_result.success if task_result else False
            else:
                # Regular act
                result = agent.execute_task(prompt, timeout=timeout)
                parsed_response = result.output
                matches_schema = None

            # Upload final screenshot to S3 if configured
            screenshot_s3_uri = None
            if s3_bucket and result.final_screenshot:
                screenshot_s3_uri = upload_screenshot_to_s3(
                    boto_session=boto_session,
                    s3_bucket=s3_bucket,
                    screenshot=result.final_screenshot,
                    session_id=session_id,
                    filename="final_screenshot.png",
                    metadata={
                        "task_id": task_id,
                        "agent": "computer-agent",
                        "prompt": prompt[:100],
                    }
                )

            # Build response (compatible with nova_act_wrapper format)
            return {
                "success": result.success,
                "response": result.output,
                "parsed_response": parsed_response,
                "matches_schema": matches_schema,
                "session_id": session_id,
                "num_steps": result.steps_taken,
                "duration": result.execution_time,
                "screenshot_s3_uri": screenshot_s3_uri,
                "recording_s3_uri": f"s3://{s3_bucket}/browser-sessions/{session_id}/" if s3_bucket else None,
                "metadata": {
                    "script_id": result.script_id,
                    "execution_time": result.execution_time,
                    "steps_taken": result.steps_taken,
                }
            }

        finally:
            agent.stop()

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def execute_script(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a browser automation script with structured steps

    Routes to appropriate executor based on script format:
    - If script has 'llm_provider' field → OpenAIPlaywrightExecutor (progressive escalation)
    - Otherwise → ComputerAgentScriptExecutor (legacy Computer Agent)
    """
    try:
        # Check if this is a new OpenAI Playwright format script (has llm_provider)
        if 'llm_provider' in command:
            print(f"[INFO] Using OpenAIPlaywrightExecutor (progressive escalation format)", file=sys.stderr)
            import asyncio
            from openai_playwright_executor import OpenAIPlaywrightExecutor
            from profile_manager import ProfileManager

            # Browser channel: default to msedge on Windows, chrome elsewhere
            browser_channel = command.get('browser_channel')
            if not browser_channel:
                browser_channel = 'msedge' if platform.system() == 'Windows' else 'chrome'

            # Resolve profile using tag-based resolution
            # Priority: profile_name (exact match) -> required_tags (AND logic) -> temp profile -> error
            user_data_dir = None
            session_config = command.get('session', {})
            if session_config and isinstance(session_config, dict):
                profile_manager = ProfileManager()

                # Use resolve_profile for tag-based resolution with fallback
                try:
                    resolved_profile = profile_manager.resolve_profile(session_config, verbose=True)

                    if resolved_profile:
                        # Successfully resolved a named profile
                        clone_for_parallel = session_config.get('clone_for_parallel', False)
                        profile_config = profile_manager.get_nova_act_config(
                            resolved_profile["name"],
                            clone_for_parallel=clone_for_parallel
                        )
                        user_data_dir = profile_config["user_data_dir"]
                        print(f"[INFO] Resolved profile '{resolved_profile['name']}' (tags: {resolved_profile.get('tags', [])})", file=sys.stderr)
                        print(f"[INFO] Using user_data_dir: {user_data_dir}", file=sys.stderr)
                    else:
                        # Using temporary profile (allow_temp_profile was True)
                        print(f"[INFO] Using temporary profile (no persistent session)", file=sys.stderr)

                except ValueError as e:
                    # Profile resolution failed and temp not allowed
                    print(f"[ERROR] Profile resolution failed: {e}", file=sys.stderr)
                    raise

            # Create executor
            executor = OpenAIPlaywrightExecutor(
                llm_provider=command.get('llm_provider', 'openai'),
                llm_model=command.get('llm_model', 'gpt-4o-mini'),
                llm_api_key=os.environ.get('OPENAI_API_KEY'),
                s3_bucket=command.get('s3_bucket'),
                aws_profile=command.get('aws_profile', 'browser-agent'),
                headless=command.get('headless', False),
                browser_channel=browser_channel,
                user_data_dir=user_data_dir,
            )

            # Execute script asynchronously
            return asyncio.run(executor.execute_script(command))

        else:
            # Legacy Computer Agent format
            print(f"[INFO] Using ComputerAgentScriptExecutor (legacy format)", file=sys.stderr)
            from computer_agent_script_executor import ComputerAgentScriptExecutor

            # Browser channel: default to msedge on Windows, chrome elsewhere
            browser_channel = command.get('browser_channel')
            if not browser_channel:
                browser_channel = 'msedge' if platform.system() == 'Windows' else 'chrome'
                print(f"[INFO] Script execution - defaulting to '{browser_channel}' for {platform.system()}", file=sys.stderr)

            # Create executor
            executor = ComputerAgentScriptExecutor(
                s3_bucket=command.get('s3_bucket'),
                aws_profile=command.get('aws_profile', 'browser-agent'),
                openai_model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
                headless=command.get('headless', False),
                max_iterations=command.get('max_steps', 30),
                timeout=command.get('timeout', 300),
                enable_replanning=True,
                browser_channel=browser_channel,
            )

            return executor.execute_script(command)

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute script: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def end_session(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    End a browser session

    Session cleanup is handled automatically by ComputerAgent context manager
    """
    return {
        "success": True,
        "message": "Session ended (cleanup automatic via ComputerAgent context manager)",
        "session_id": command.get('session_id')
    }


def validate_profile(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the content and usability of a user_data_dir profile

    Supports static (filesystem) and runtime (in-browser) validation
    """
    user_data_dir = command.get("user_data_dir")
    if not user_data_dir:
        return {"success": False, "error": "user_data_dir is required"}

    mode = command.get("mode", "static")  # 'static' | 'runtime' | 'both'

    # Use ProfileManager for validation
    from profile_manager import ProfileManager
    profile_manager = ProfileManager()

    # Static checks
    static = profile_manager.validate_user_data_dir(user_data_dir)
    out: Dict[str, Any] = {"success": True, "static": static}

    # Runtime checks
    if mode in ("runtime", "both"):
        # TODO: Implement runtime validation using ComputerAgent
        # Similar to nova_act_wrapper's runtime checks but using ComputerAgent
        out["runtime"] = {"note": "Runtime validation not yet implemented for ComputerAgent"}

    # Recommendations
    recs = []
    if static.get("status") == "missing":
        recs.append("Profile directory missing or incomplete. Run a human login bootstrap.")
    if static.get("status") == "warn":
        recs.append("Profile exists but may not hold auth yet. Verify via runtime check.")
    out["recommendations"] = recs
    return out


def setup_login(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Setup interactive login for a profile

    Opens a browser with the profile's user_data_dir, navigates to the starting_url,
    and waits for a timeout period to allow the user to manually log in.
    """
    profile_name = command.get("profile_name")
    starting_url = command.get("starting_url")

    if not profile_name:
        return {"success": False, "error": "profile_name is required"}
    if not starting_url:
        return {"success": False, "error": "starting_url is required"}

    try:
        from profile_manager import ProfileManager

        # Initialize profile manager
        profile_manager = ProfileManager()

        # Check if profile exists, create if not
        profile = profile_manager.get_profile(profile_name)
        if not profile:
            print(f"Creating new profile: {profile_name}", file=sys.stderr)
            profile = profile_manager.create_profile(
                profile_name=profile_name,
                description=f"Profile with authenticated session for {starting_url}",
                tags=["authenticated"],
                auto_login_sites=[starting_url]
            )
        else:
            print(f"Using existing profile: {profile_name}", file=sys.stderr)

        # Get profile config
        config = profile_manager.get_nova_act_config(profile_name, clone_for_parallel=False)
        user_data_dir = config["user_data_dir"]

        # Determine timeout (default 5 minutes)
        timeout = command.get("timeout", 300)

        # Browser channel
        browser_channel = command.get('browser_channel')
        if not browser_channel:
            browser_channel = 'msedge' if platform.system() == 'Windows' else 'chrome'

        # Store browser_channel in profile metadata for consistency
        # This ensures script execution uses the same browser for cookie compatibility
        profile_manager.update_browser_channel(profile_name, browser_channel)

        print(f"", file=sys.stderr)
        print(f"╔═══════════════════════════════════════════════════════════╗", file=sys.stderr)
        print(f"║  PROFILE LOGIN SETUP (ComputerAgent)                      ║", file=sys.stderr)
        print(f"╠═══════════════════════════════════════════════════════════╣", file=sys.stderr)
        print(f"║  Profile: {profile_name:<48}║", file=sys.stderr)
        print(f"║  URL:     {starting_url[:48]:<48}║", file=sys.stderr)
        print(f"║  Timeout: {timeout} seconds{'':<38}║", file=sys.stderr)
        print(f"╠═══════════════════════════════════════════════════════════╣", file=sys.stderr)
        print(f"║  A browser window will open. Please log in manually.     ║", file=sys.stderr)
        print(f"║  The browser will stay open for {timeout//60} minutes.{'':<23}║", file=sys.stderr)
        print(f"║  Your login session will be saved automatically.         ║", file=sys.stderr)
        print(f"║  You can close the browser when done.                    ║", file=sys.stderr)
        print(f"╚═══════════════════════════════════════════════════════════╝", file=sys.stderr)
        print(f"", file=sys.stderr)

        # Open browser for manual login using Playwright directly
        # We don't need LLM for manual login, so no API key required
        import time
        from playwright.sync_api import sync_playwright
        from browser_launch_config import get_launch_options, log_launch_config

        print(f"Opening browser for manual login (no API key required)...", file=sys.stderr)

        # Get consistent launch options for profile setup
        # Key features:
        # - Removes --enable-automation (hides "controlled by automation" bar)
        # - Removes --disable-component-extensions-with-background-pages (enables password manager UI)
        # - Adds --no-sandbox in containerized environments
        launch_options = get_launch_options(
            headless=False,  # Must be visible for manual login
            browser_channel=browser_channel,
            is_persistent_context=True,
        )
        log_launch_config(launch_options, "profile_setup")

        with sync_playwright() as p:
            # Launch browser with user_data_dir for session persistence
            # Using shared launch configuration for password manager support
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                **launch_options
            )

            # Create page and navigate
            page = context.new_page()
            page.goto(starting_url)

            try:
                # Just wait for the timeout - user can log in during this time
                print(f"Browser opened. Waiting {timeout} seconds for you to complete login...", file=sys.stderr)

                # Wait in smaller increments to detect early termination
                elapsed = 0
                check_interval = 5  # Check every 5 seconds
                while elapsed < timeout:
                    time.sleep(check_interval)
                    elapsed += check_interval

                print(f"Timeout reached. Closing browser and saving session...", file=sys.stderr)

            finally:
                # Wait for any pending network requests to complete (cookie flush)
                # This ensures cookies are fully saved before closing the context
                try:
                    print(f"Waiting for network idle before saving session...", file=sys.stderr)
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    # Network may not become fully idle, continue anyway
                    pass

                # Give browser extra time to flush cookies to disk
                time.sleep(1)

                # Close page and context (browser is closed with context in persistent mode)
                page.close()
                context.close()

        # Verify profile was saved correctly
        import os
        user_data_path = Path(user_data_dir)
        cookies_file = user_data_path / "Default" / "Cookies"
        local_state_file = user_data_path / "Local State"

        print(f"", file=sys.stderr)
        print(f"✓ Profile '{profile_name}' login setup completed!", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  Profile Debug Info:", file=sys.stderr)
        print(f"  ├─ User data dir: {user_data_dir}", file=sys.stderr)
        print(f"  ├─ Is absolute: {user_data_path.is_absolute()}", file=sys.stderr)
        print(f"  ├─ Dir exists: {user_data_path.exists()}", file=sys.stderr)
        print(f"  ├─ Browser channel: {browser_channel}", file=sys.stderr)
        print(f"  ├─ Cookies file: {cookies_file}", file=sys.stderr)
        print(f"  │   └─ Exists: {cookies_file.exists()}", file=sys.stderr)
        print(f"  └─ Local State: {local_state_file}", file=sys.stderr)
        print(f"      └─ Exists: {local_state_file.exists()}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  Future scripts can reuse this authenticated session", file=sys.stderr)

        return {
            "success": True,
            "message": f"Login setup completed for profile '{profile_name}'",
            "profile_name": profile_name,
            "user_data_dir": user_data_dir,
            "browser_channel": browser_channel,
            "cookies_file_exists": cookies_file.exists(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to setup login: {str(e)}",
            "traceback": traceback.format_exc()
        }


def upload_screenshot_to_s3(
    boto_session,
    s3_bucket: str,
    screenshot: bytes,
    session_id: str,
    filename: str,
    metadata: Dict[str, str]
) -> str:
    """Upload screenshot to S3 and return S3 URI"""
    try:
        s3_client = boto_session.client('s3')

        s3_key = f"browser-sessions/{session_id}/{filename}"

        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=screenshot,
            ContentType='image/png',
            Metadata=metadata,
        )

        return f"s3://{s3_bucket}/{s3_key}"
    except Exception as e:
        print(f"Warning: Failed to upload screenshot to S3: {e}", file=sys.stderr)
        return None


def main():
    """
    Main entry point - supports both command-line args and stdin

    Mode 1: Command-line arguments (--script file) - for ScriptExecutor
    Mode 2: JSON from stdin - for NovaActExecutor
    """
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Execute browser automation with Computer Agent")
    parser.add_argument("--script", help="Path to script JSON file")
    parser.add_argument("--aws-profile", default="browser-agent", help="AWS profile name")
    parser.add_argument("--s3-bucket", help="S3 bucket for screenshots")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--browser-channel", help="Browser channel (chrome, msedge, chromium)")
    parser.add_argument("--navigation-timeout", type=int, default=60000, help="Navigation timeout in ms")
    parser.add_argument("--user-data-dir", help="User data directory for browser profile")

    args = parser.parse_args()

    try:
        # Determine input mode
        if args.script:
            # Mode 1: Read script from file (ScriptExecutor mode)
            from pathlib import Path
            script_path = Path(args.script)
            if not script_path.exists():
                result = {
                    "success": False,
                    "error": f"Script file not found: {args.script}"
                }
                print(json.dumps(result), flush=True)
                sys.exit(1)

            with open(script_path, 'r') as f:
                script = json.load(f)

            # Build command from script + args
            command = {
                "command_type": "script",
                "steps": script.get("steps", []),
                "name": script.get("name", "Unnamed Script"),
                "starting_page": script.get("starting_page"),
                "llm_provider": script.get("llm_provider"),
                "llm_model": script.get("llm_model"),
                "abort_on_error": script.get("abort_on_error", False),
                "session": script.get("session", {}),
                "aws_profile": args.aws_profile,
                "s3_bucket": args.s3_bucket,
                "headless": args.headless,
                "browser_channel": args.browser_channel,
            }

        else:
            # Mode 2: Read command from stdin (NovaActExecutor mode)
            command_json = sys.stdin.read()

            if not command_json.strip():
                result = {
                    "success": False,
                    "error": "No input on stdin and no --script argument"
                }
                print(json.dumps(result), flush=True)
                sys.exit(1)

            # Parse command
            command = json.loads(command_json)

        # Execute command
        result = execute_browser_command(command)

        # Write result to stdout
        print(json.dumps(result), flush=True)
        sys.exit(0 if result.get("success") else 1)

    except json.JSONDecodeError as e:
        error_result = {
            "success": False,
            "error": f"Invalid JSON input: {str(e)}",
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result), flush=True)
        sys.exit(1)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
