"""
Helper functions for building NovaAct kwargs consistently across modules.

This module centralizes the logic for constructing NovaAct initialization parameters
to avoid duplication between script_executor.py and nova_act_wrapper.py.
"""

import os
import sys
import platform
from typing import Dict, Any, Optional, List


def build_nova_act_kwargs(
    starting_page: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    clone_user_data_dir: Optional[bool] = None,
    headless: bool = True,
    record_video: bool = False,
    browser_channel: Optional[str] = None,
    stop_hooks: Optional[List[Any]] = None,
    nova_act_api_key: Optional[str] = None,
    boto_session: Optional[Any] = None,
    go_to_url_timeout: Optional[int] = None,
    ignore_https_errors: bool = True,
) -> Dict[str, Any]:
    """
    Build NovaAct initialization kwargs with consistent defaults.

    Args:
        starting_page: URL to navigate to on browser start
        user_data_dir: Path to browser profile directory
        clone_user_data_dir: Whether to clone the profile (None = use NovaAct default)
        headless: Run browser in headless mode
        record_video: Record browser session video
        browser_channel: Browser to use ('msedge', 'chrome', 'chromium')
        stop_hooks: List of stop hooks (e.g., S3Writer)
        nova_act_api_key: Nova Act API key for authentication
        boto_session: Boto3 session for AWS authentication
        go_to_url_timeout: Timeout for page navigation in seconds
        ignore_https_errors: Ignore HTTPS certificate errors

    Returns:
        Dictionary of kwargs ready to pass to NovaAct()
    """
    kwargs = {}

    # Required/common parameters
    if starting_page is not None:
        kwargs["starting_page"] = starting_page

    if user_data_dir is not None:
        kwargs["user_data_dir"] = user_data_dir

    # Only set clone flag if explicitly provided
    if clone_user_data_dir is not None:
        kwargs["clone_user_data_dir"] = bool(clone_user_data_dir)

    kwargs["headless"] = headless

    if record_video:
        kwargs["record_video"] = record_video

    if stop_hooks:
        kwargs["stop_hooks"] = stop_hooks

    kwargs["ignore_https_errors"] = ignore_https_errors

    # Browser channel with platform-specific defaults
    if browser_channel:
        kwargs["chrome_channel"] = browser_channel
    elif browser_channel is None:
        # Apply platform default only if not explicitly disabled (empty string)
        default_channel = get_default_browser_channel()
        if default_channel:
            kwargs["chrome_channel"] = default_channel

    # Authentication
    if nova_act_api_key:
        kwargs["nova_act_api_key"] = nova_act_api_key
    elif boto_session:
        kwargs["boto_session"] = boto_session

    # Timeouts
    if go_to_url_timeout is not None:
        kwargs["go_to_url_timeout"] = go_to_url_timeout

    return kwargs


def get_default_browser_channel() -> str:
    """
    Get platform-specific default browser channel.

    Returns:
        'msedge' on Windows, 'chrome' elsewhere
    """
    return 'msedge' if platform.system() == 'Windows' else 'chrome'


def log_nova_act_kwargs(kwargs: Dict[str, Any], prefix: str = "", file=sys.stderr):
    """
    Log NovaAct kwargs in a consistent format for debugging.

    Args:
        kwargs: NovaAct kwargs dictionary
        prefix: Optional prefix for log lines (e.g., "  ")
        file: File object to write to (default: stderr)
    """
    print(f"{prefix}NovaAct Configuration:", file=file)
    print(f"{prefix}  - Starting Page: {kwargs.get('starting_page', 'none')}", file=file)
    print(f"{prefix}  - User Data Dir: {kwargs.get('user_data_dir', 'none')}", file=file)

    clone_val = kwargs.get('clone_user_data_dir')
    if clone_val is not None:
        print(f"{prefix}  - Clone Profile: {clone_val}", file=file)
    else:
        print(f"{prefix}  - Clone Profile: not set (NovaAct default)", file=file)

    print(f"{prefix}  - Headless: {kwargs.get('headless', True)}", file=file)
    print(f"{prefix}  - Record Video: {kwargs.get('record_video', False)}", file=file)

    chrome_channel = kwargs.get('chrome_channel')
    if chrome_channel:
        print(f"{prefix}  - Browser Channel: {chrome_channel}", file=file)

    timeout = kwargs.get('go_to_url_timeout')
    if timeout:
        print(f"{prefix}  - Navigation Timeout: {timeout}s", file=file)

    print(f"{prefix}  - Ignore HTTPS Errors: {kwargs.get('ignore_https_errors', True)}", file=file)
