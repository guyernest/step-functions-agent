#!/usr/bin/env python3
"""
Nova Act Wrapper for Local Browser Agent

This script is called by the Rust agent via subprocess.
It receives commands via stdin (JSON) and outputs results via stdout (JSON).

Handles:
- Browser session lifecycle (start, act, stop)
- S3Writer integration for automatic recordings upload
- Error handling and result serialization
"""

import sys
import json
import os
import traceback
from typing import Dict, Any, Optional, List
import boto3
from nova_act import NovaAct, BOOL_SCHEMA
from nova_act.util.s3_writer import S3Writer
from pathlib import Path
from datetime import datetime


def execute_browser_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a browser automation command using Nova Act

    Args:
        command: Dictionary containing:
            - command_type: 'start_session', 'act', 'script', 'end_session', 'validate_profile', or 'setup_login'
            - prompt: Natural language instruction (for 'act')
            - steps: List of script steps (for 'script')
            - starting_page: Initial URL (for 'start_session' or 'script')
            - session_id: Session identifier
            - s3_bucket: S3 bucket for recordings
            - user_data_dir: Chrome profile directory
            - max_steps: Maximum browser steps
            - timeout: Timeout in seconds
            - schema: JSON schema for output
            - headless: Run headless mode
            - record_video: Record video
            - profile_name: Profile name (for 'setup_login')

    Returns:
        Dictionary with execution result
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
        "message": "Session management is handled implicitly in Nova Act context",
        "session_id": command.get('session_id')
    }


def execute_act(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a browser automation command

    This is the main execution path that:
    1. Initializes Nova Act with S3Writer
    2. Executes the act() command
    3. Returns results with S3 URIs
    """
    # Extract parameters
    prompt = command.get('prompt')
    if not prompt:
        return {
            "success": False,
            "error": "Missing required parameter: prompt"
        }

    # Check if prompt contains a browser automation script
    # Server sends: "Execute this browser automation script:\n\n{...json...}"
    if prompt.strip().startswith("Execute this browser automation script:"):
        # Extract the JSON script from the prompt
        import re
        # Find the JSON object in the prompt
        json_match = re.search(r'\{[\s\S]*\}', prompt)
        if json_match:
            try:
                script = json.loads(json_match.group(0))
                # Execute using script_executor instead
                from script_executor import ScriptExecutor

                executor = ScriptExecutor(
                    s3_bucket=command.get('s3_bucket'),
                    aws_profile=command.get('aws_profile', 'browser-agent'),
                    user_data_dir=command.get('user_data_dir'),
                    headless=command.get('headless', False),
                    record_video=command.get('record_video', True),
                    max_steps=command.get('max_steps', 30),
                    timeout=command.get('timeout', 300),
                    nova_act_api_key=os.environ.get('NOVA_ACT_API_KEY')
                )

                return executor.execute_script(script)

            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse script from prompt: {str(e)}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to execute script: {str(e)}",
                    "traceback": traceback.format_exc()
                }

    starting_page = command.get('starting_page')
    session_id = command.get('session_id')
    s3_bucket = command.get('s3_bucket')
    task_id = command.get('task_id', 'unknown')
    user_data_dir = command.get('user_data_dir')
    max_steps = command.get('max_steps', 30)
    timeout = command.get('timeout', 300)
    schema = command.get('schema')
    headless = command.get('headless', False)
    record_video = command.get('record_video', True)
    aws_profile = command.get('aws_profile', 'browser-agent')
    clone_user_data_dir = command.get('clone_user_data_dir')

    # Browser channel: default to msedge on Windows, chrome elsewhere
    browser_channel = command.get('browser_channel')
    if not browser_channel:
        import platform
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
        # Handle legacy profile_name from command root (for backward compatibility)
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
            # Keep user_data_dir and clone_user_data_dir from command if provided
            pass

    except ValueError as e:
        # Profile resolution failed
        print(f"✗ Profile resolution failed: {e}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "error_type": "ProfileResolutionError"
        }

    # Create boto3 session with local credentials
    boto_session = boto3.Session(profile_name=aws_profile)

    # Configure S3Writer for automatic uploads
    stop_hooks = []
    if s3_bucket and record_video:
        s3_writer = S3Writer(
            boto_session=boto_session,
            s3_bucket_name=s3_bucket,
            s3_prefix=f"browser-sessions/{session_id or 'temp'}/",
            metadata={
                "task_id": task_id,
                "agent": "browser-remote",
                "prompt": prompt[:100]  # First 100 chars
            }
        )
        stop_hooks.append(s3_writer)

    # Execute Nova Act
    # Check if we have a Nova Act API key in environment
    nova_act_api_key = os.environ.get('NOVA_ACT_API_KEY')

    try:
        # Build NovaAct kwargs
        nova_act_kwargs = {
            "starting_page": starting_page,
            "user_data_dir": user_data_dir,
            "headless": headless,
            "record_video": record_video,
            "stop_hooks": stop_hooks,
            "ignore_https_errors": True,
        }

        # Only set clone flag if explicitly provided by caller
        if clone_user_data_dir is not None:
            nova_act_kwargs["clone_user_data_dir"] = bool(clone_user_data_dir)

        # Add browser channel if specified (for Edge, Chrome, Chromium selection)
        if browser_channel:
            print(f"[DEBUG] Received browser_channel from Rust: '{browser_channel}'", file=sys.stderr)
            nova_act_kwargs["chrome_channel"] = browser_channel
            print(f"[DEBUG] Passing chrome_channel to NovaAct: '{nova_act_kwargs['chrome_channel']}'", file=sys.stderr)
        else:
            print(f"[DEBUG] No browser_channel received from Rust, NovaAct will use default", file=sys.stderr)

        # Add authentication: use API key if available, otherwise use boto_session
        # Nova Act doesn't allow both
        if nova_act_api_key:
            nova_act_kwargs["nova_act_api_key"] = nova_act_api_key
        else:
            nova_act_kwargs["boto_session"] = boto_session

        # Log comprehensive session startup information
        print(f"[INFO] Starting browser session with:", file=sys.stderr)
        print(f"  - Profile: {profile_name}", file=sys.stderr)
        print(f"  - Profile Path: {user_data_dir}", file=sys.stderr)
        print(f"  - Headless Mode: {headless}", file=sys.stderr)
        print(f"  - Clone Profile: {clone_user_data_dir if clone_user_data_dir is not None else 'not set (NovaAct default)'}", file=sys.stderr)
        print(f"  - Starting Page: {starting_page or 'none'}", file=sys.stderr)
        print(f"  - Record Video: {record_video}", file=sys.stderr)
        print(f"  - Max Steps: {max_steps}", file=sys.stderr)
        print(f"  - Timeout: {timeout}s", file=sys.stderr)
        print(f"  - Session ID: {session_id or 'auto-generated'}", file=sys.stderr)

        with NovaAct(**nova_act_kwargs) as nova:
            # Execute act command
            result = nova.act(
                prompt=prompt,
                max_steps=max_steps,
                timeout=timeout,
                schema=schema
            )

            # Build response
            return {
                "success": True,
                "response": result.response,
                "parsed_response": result.parsed_response,
                "matches_schema": result.matches_schema if schema else None,
                "session_id": str(result.metadata.session_id) if result.metadata else session_id,
                "num_steps": result.metadata.num_steps_executed if result.metadata else 0,
                "duration": (result.metadata.end_time - result.metadata.start_time) if result.metadata else 0,
                "recording_s3_uri": f"s3://{s3_bucket}/browser-sessions/{result.metadata.session_id}/" if s3_bucket and result.metadata else None,
                "metadata": {
                    "act_id": result.metadata.act_id if result.metadata else None,
                    "start_time": result.metadata.start_time if result.metadata else None,
                    "end_time": result.metadata.end_time if result.metadata else None,
                } if result.metadata else None
            }

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

    This uses the ScriptExecutor to run a script with multiple steps.
    The script format matches the local examples in examples/ directory.
    """
    try:
        from script_executor import ScriptExecutor

        # Browser channel: default to msedge on Windows, chrome elsewhere
        browser_channel = command.get('browser_channel')
        if not browser_channel:
            import platform
            browser_channel = 'msedge' if platform.system() == 'Windows' else 'chrome'
            print(f"[INFO] Script execution - no browser_channel specified, defaulting to '{browser_channel}' for {platform.system()}", file=sys.stderr)

        # ScriptExecutor expects the full script structure with steps, session, etc.
        # The command already contains these fields from the template
        executor = ScriptExecutor(
            s3_bucket=command.get('s3_bucket'),
            aws_profile=command.get('aws_profile', 'browser-agent'),
            user_data_dir=command.get('user_data_dir'),
            headless=command.get('headless', False),
            record_video=command.get('record_video', True),
            max_steps=command.get('max_steps', 30),
            timeout=command.get('timeout', 300),
            nova_act_api_key=os.environ.get('NOVA_ACT_API_KEY'),
            browser_channel=browser_channel
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

    Session cleanup is handled automatically by Nova Act context manager
    """
    return {
        "success": True,
        "message": "Session ended (cleanup automatic via Nova Act context manager)",
        "session_id": command.get('session_id')
    }


def _static_profile_checks(user_data_dir: str) -> Dict[str, Any]:
    """Perform static filesystem checks on a Chromium user data dir."""
    p = Path(user_data_dir) if user_data_dir else None
    exists = p.exists() if p else False
    items = []
    size_bytes = 0
    last_modified = None

    if exists:
        try:
            # Shallow stats
            items = [str(child.name) for child in p.iterdir()]
            for root, _, files in os.walk(p):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size_bytes += os.path.getsize(fp)
                        mtime = os.path.getmtime(fp)
                        if last_modified is None or mtime > last_modified:
                            last_modified = mtime
                    except Exception:
                        pass
        except Exception:
            pass

    # Chromium profile heuristics (support legacy and modern paths, and when p already points to profile dir)
    default_dir = p / "Default" if exists else None
    profile_dir_candidates = []
    if default_dir and default_dir.exists():
        profile_dir_candidates.append(default_dir)
    # If path itself looks like a profile folder (contains Preferences or Network)
    if exists and ((p / "Preferences").exists() or (p / "Network").exists() or (p / "Cookies").exists()):
        profile_dir_candidates.append(p)

    def find_first_existing(paths):
        for x in paths:
            if x.exists():
                return x
        return None

    cookies_path = find_first_existing([
        *(d / "Network" / "Cookies" for d in profile_dir_candidates),
        *(d / "Cookies" for d in profile_dir_candidates),
    ])
    local_storage_dir = find_first_existing([
        *(d / "Local Storage" / "leveldb" for d in profile_dir_candidates)
    ])
    preferences_path = find_first_existing([
        *(d / "Preferences" for d in profile_dir_candidates)
    ])
    local_state_path = p / "Local State" if exists else None

    checks = {
        "path_exists": exists,
        "has_default_dir": bool(default_dir and default_dir.exists()),
        "has_cookies_db": bool(cookies_path and cookies_path.exists()),
        "has_local_storage": bool(local_storage_dir and local_storage_dir.exists()),
        "has_preferences": bool(preferences_path and preferences_path.exists()),
        "has_local_state": bool(local_state_path and local_state_path.exists()),
        "size_bytes": size_bytes,
        "last_modified": datetime.fromtimestamp(last_modified).isoformat() if last_modified else None,
        "top_level_items": items[:20],
    }

    # Status assessment
    status = "ok" if checks["path_exists"] and (checks["has_default_dir"] or checks["has_local_state"]) else "missing"
    if status == "ok" and not (checks["has_cookies_db"] or checks["has_local_storage"]):
        status = "warn"  # profile exists but may not be logged-in yet

    checks["status"] = status
    return checks


def _runtime_profile_checks(
    starting_page: Optional[str],
    user_data_dir: str,
    headless: bool,
    clone_user_data_dir: Optional[bool],
    ui_prompt: Optional[str] = None,
    cookie_domains: Optional[List[str]] = None,
    cookie_names: Optional[List[str]] = None,
    local_storage_keys: Optional[List[str]] = None,
    nova_act_api_key: Optional[str] = None,
    boto_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """Open the profile and check cookies/localStorage or a UI prompt in-process."""
    if not starting_page:
        return {"success": False, "error": "starting_page required for runtime validation"}

    kwargs: Dict[str, Any] = {
        "starting_page": starting_page,
        "user_data_dir": user_data_dir,
        "headless": headless,
        "ignore_https_errors": True,
    }
    if clone_user_data_dir is not None:
        kwargs["clone_user_data_dir"] = bool(clone_user_data_dir)
    if nova_act_api_key:
        kwargs["nova_act_api_key"] = nova_act_api_key
    elif boto_session is not None:
        kwargs["boto_session"] = boto_session

    results: Dict[str, Any] = {"success": True}
    with NovaAct(**kwargs) as nova:
        ui_ok = None
        cookies_ok = None
        ls_ok = None

        if ui_prompt:
            try:
                r = nova.act(ui_prompt, schema=BOOL_SCHEMA, max_steps=5, timeout=60)
                ui_ok = bool(r.matches_schema and r.parsed_response)
            except Exception as e:
                ui_ok = False
                results["ui_error"] = str(e)

        if cookie_domains and cookie_names:
            try:
                cookies = [c for c in nova.page.context.cookies() if any(d in (c.get("domain") or "") for d in cookie_domains)]
                names = {c.get("name") for c in cookies}
                cookies_ok = all(n in names for n in cookie_names)
                results["cookies_found"] = sorted(list(names))
            except Exception as e:
                cookies_ok = False
                results["cookies_error"] = str(e)

        if local_storage_keys:
            try:
                ls_results = {}
                for key in local_storage_keys:
                    present = nova.page.evaluate("key => !!window.localStorage.getItem(key)", key)
                    ls_results[key] = bool(present)
                ls_ok = all(ls_results.values()) if ls_results else None
                results["local_storage"] = ls_results
            except Exception as e:
                ls_ok = False
                results["local_storage_error"] = str(e)

        results["ui_ok"] = ui_ok
        results["cookies_ok"] = cookies_ok
        results["local_storage_ok"] = ls_ok
        # Consider success if any selected method passed
        chosen = [v for v in [ui_ok, cookies_ok, ls_ok] if v is not None]
        results["authenticated"] = any(chosen) if chosen else None
        return results


def validate_profile(command: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the content and usability of a user_data_dir profile.

    Supports static (filesystem) and runtime (in-browser) validation.
    """
    user_data_dir = command.get("user_data_dir")
    if not user_data_dir:
        return {"success": False, "error": "user_data_dir is required"}

    mode = command.get("mode", "static")  # 'static' | 'runtime' | 'both'
    headless = command.get("headless", True)
    starting_page = command.get("starting_page")
    clone_user_data_dir = command.get("clone_user_data_dir")
    ui_prompt = command.get("ui_prompt")
    cookie_domains = command.get("cookie_domains")
    cookie_names = command.get("cookie_names")
    local_storage_keys = command.get("local_storage_keys")

    # Static checks
    static = _static_profile_checks(user_data_dir)
    out: Dict[str, Any] = {"success": True, "static": static}

    # Runtime checks
    if mode in ("runtime", "both"):
        nova_act_api_key = os.environ.get('NOVA_ACT_API_KEY')
        boto_session = None
        try:
            aws_profile = command.get('aws_profile', 'browser-agent')
            boto_session = boto3.Session(profile_name=aws_profile)
        except Exception:
            boto_session = None

        runtime = _runtime_profile_checks(
            starting_page=starting_page,
            user_data_dir=user_data_dir,
            headless=headless,
            clone_user_data_dir=clone_user_data_dir,
            ui_prompt=ui_prompt,
            cookie_domains=cookie_domains,
            cookie_names=cookie_names,
            local_storage_keys=local_storage_keys,
            nova_act_api_key=nova_act_api_key,
            boto_session=boto_session,
        )
        out["runtime"] = runtime
        # Overall assessment
        if not runtime.get("success", False):
            out["success"] = False

    # Recommendations
    recs = []
    if static.get("status") == "missing":
        recs.append("Profile directory missing or incomplete. Run a human login bootstrap.")
    if static.get("status") == "warn":
        recs.append("Profile exists but may not hold auth yet. Verify via runtime check.")
    if command.get("recommend_clone") is not False:
        recs.append("Use clone_user_data_dir=False to persist sessions; set True only for parallel or throwaway runs.")
    out["recommendations"] = recs
    return out


def setup_login(command: Dict[str, Any]) -> Dict[str, Any]:
    """Setup interactive login for a profile.

    Opens a browser with the profile's user_data_dir, navigates to the starting_url,
    and waits for a timeout period to allow the user to manually log in.
    When the browser closes or timeout expires, the session is automatically saved.

    Args:
        command: Dictionary containing:
            - profile_name: Name of the profile
            - starting_url: URL to navigate to for login
            - timeout: Timeout in seconds (default: 300 = 5 minutes)

    Returns:
        Dictionary with success status
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

        # Mark profile as requiring human login
        profile_manager.mark_profile_for_login(
            profile_name=profile_name,
            requires_human=True,
            notes=f"Manual login required for {starting_url}"
        )

        # Get Nova Act config
        config = profile_manager.get_nova_act_config(profile_name, clone_for_parallel=False)
        user_data_dir = config["user_data_dir"]

        # Determine timeout (default 5 minutes)
        timeout = command.get("timeout", 300)

        # Get authentication credentials
        nova_act_api_key = os.environ.get('NOVA_ACT_API_KEY')
        boto_session = None
        if not nova_act_api_key:
            try:
                aws_profile = command.get('aws_profile', 'browser-agent')
                boto_session = boto3.Session(profile_name=aws_profile)
            except Exception:
                pass

        # Build NovaAct kwargs
        nova_act_kwargs = {
            "starting_page": starting_url,
            "user_data_dir": user_data_dir,
            "clone_user_data_dir": False,  # Don't clone to preserve session
            "headless": False,  # Must be visible for human login
            "ignore_https_errors": True,
        }

        # Add browser channel if specified
        browser_channel = command.get('browser_channel')
        if browser_channel:
            print(f"[DEBUG] Script execution - received browser_channel from Rust: '{browser_channel}'", file=sys.stderr)
            nova_act_kwargs["chrome_channel"] = browser_channel
            print(f"[DEBUG] Script execution - passing chrome_channel to NovaAct: '{nova_act_kwargs['chrome_channel']}'", file=sys.stderr)
        else:
            print(f"[DEBUG] Script execution - no browser_channel received from Rust", file=sys.stderr)

        if nova_act_api_key:
            nova_act_kwargs["nova_act_api_key"] = nova_act_api_key
        elif boto_session:
            nova_act_kwargs["boto_session"] = boto_session

        print(f"", file=sys.stderr)
        print(f"╔═══════════════════════════════════════════════════════════╗", file=sys.stderr)
        print(f"║  PROFILE LOGIN SETUP                                      ║", file=sys.stderr)
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

        # Open browser for manual login
        import time
        print(f"[DEBUG] About to create NovaAct instance with kwargs:", file=sys.stderr)
        print(f"[DEBUG]   user_data_dir: {nova_act_kwargs.get('user_data_dir')}", file=sys.stderr)
        print(f"[DEBUG]   chrome_channel: {nova_act_kwargs.get('chrome_channel', 'NOT SET')}", file=sys.stderr)
        print(f"[DEBUG]   headless: {nova_act_kwargs.get('headless')}", file=sys.stderr)
        print(f"[DEBUG]   starting_page: {nova_act_kwargs.get('starting_page')}", file=sys.stderr)
        sys.stderr.flush()

        print(f"[DEBUG] Creating NovaAct instance...", file=sys.stderr)
        sys.stderr.flush()

        try:
            with NovaAct(**nova_act_kwargs) as nova:
                print(f"[DEBUG] NovaAct instance created successfully!", file=sys.stderr)
                sys.stderr.flush()
                # Just wait for the timeout - user can log in during this time
                # The browser will stay open and visible
                print(f"Browser opened. Waiting {timeout} seconds for you to complete login...", file=sys.stderr)
                sys.stderr.flush()

                # Wait in smaller increments to detect early termination
                elapsed = 0
                check_interval = 5  # Check every 5 seconds
                while elapsed < timeout:
                    time.sleep(check_interval)
                    elapsed += check_interval
                    # If browser crashes, NovaAct should raise an exception
                    # This loop allows us to detect issues earlier

                print(f"Timeout reached. Closing browser and saving session...", file=sys.stderr)
                sys.stderr.flush()
        except KeyboardInterrupt:
            print(f"[INFO] User interrupted login setup", file=sys.stderr)
            sys.stderr.flush()
            raise
        except SystemExit as sys_exit:
            print(f"[WARNING] Browser process exited early (exit code: {sys_exit.code})", file=sys.stderr)
            print(f"[WARNING] This may happen if:", file=sys.stderr)
            print(f"  - User closed the browser window", file=sys.stderr)
            print(f"  - Browser crashed due to compatibility issues", file=sys.stderr)
            print(f"  - Profile directory has permission problems", file=sys.stderr)
            sys.stderr.flush()
            raise
        except Exception as nova_error:
            print(f"[ERROR] Failed to create/use NovaAct instance: {str(nova_error)}", file=sys.stderr)
            print(f"[ERROR] Error type: {type(nova_error).__name__}", file=sys.stderr)
            print(f"[ERROR] Full traceback:", file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
            sys.stderr.flush()
            raise  # Re-raise to be caught by outer exception handler

        print(f"", file=sys.stderr)
        print(f"✓ Profile '{profile_name}' login setup completed!", file=sys.stderr)
        print(f"  User data directory: {user_data_dir}", file=sys.stderr)
        print(f"  Future scripts can reuse this authenticated session", file=sys.stderr)

        return {
            "success": True,
            "message": f"Login setup completed for profile '{profile_name}'",
            "profile_name": profile_name,
            "user_data_dir": user_data_dir,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to setup login: {str(e)}",
            "traceback": traceback.format_exc()
        }


def main():
    """
    Main entry point

    Reads command from stdin, executes, writes result to stdout
    """
    try:
        # Read command from stdin
        command_json = sys.stdin.read()

        if not command_json.strip():
            result = {
                "success": False,
                "error": "No input received on stdin"
            }
        else:
            # Parse command
            command = json.loads(command_json)

            # Execute command
            result = execute_browser_command(command)

        # Write result to stdout
        print(json.dumps(result), flush=True)
        sys.exit(0)

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
