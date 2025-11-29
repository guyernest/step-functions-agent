#!/usr/bin/env python3
"""
Browser Launch Configuration

Centralized configuration for Playwright browser launch arguments.
Ensures consistent browser behavior across all entry points:
- Profile setup (setup_login)
- Script execution (openai_playwright_executor, computer_agent_wrapper)
- Testing

Key Goals:
1. Enable password manager functionality (both built-in and third-party)
2. Remove "controlled by automation software" infobar
3. Support containerized environments (Docker, etc.)
4. Maintain security while enabling usability

Reference: Nova Act SDK implementation
"""

import os
import sys
import platform
from typing import List, Dict, Any, Optional


def is_containerized_environment() -> bool:
    """
    Detect if running in a containerized environment (Docker, Kubernetes, etc.)

    Returns:
        True if running in a container, False otherwise
    """
    # Check for Docker
    if os.path.exists("/.dockerenv"):
        return True

    # Check for environment variable
    if os.environ.get("DOCKER_CONTAINER") or os.environ.get("CONTAINER"):
        return True

    # Check cgroup for container indicators
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            if "docker" in content or "kubepods" in content or "containerd" in content:
                return True
    except (FileNotFoundError, PermissionError):
        pass

    return False


def get_base_browser_args(
    is_persistent_context: bool = True,
    window_size: Optional[tuple] = None,
    extra_args: Optional[List[str]] = None
) -> List[str]:
    """
    Get base browser arguments that should be used for all launches.

    Args:
        is_persistent_context: Whether using persistent context (profile-based)
        window_size: Optional (width, height) tuple for window size
        extra_args: Additional custom arguments to include

    Returns:
        List of browser arguments
    """
    args = [
        # Prevent /dev/shm OOM issues in containers and memory-constrained environments
        "--disable-dev-shm-usage",
    ]

    # Add window size if specified
    if window_size:
        args.append(f"--window-size={window_size[0]},{window_size[1]}")

    # Only add AutomationControlled flag for ephemeral (non-persistent) sessions
    # For persistent sessions, we want the browser to behave normally
    # This helps websites detect automation, but it's a tradeoff for profile stability
    if not is_persistent_context:
        args.append("--disable-blink-features=AutomationControlled")

    # Cleaner debugging output (from Nova Act SDK)
    args.append("--silent-debugger-extension-api")

    # Allow Chrome DevTools remote connections (useful for debugging)
    args.append("--remote-allow-origins=https://chrome-devtools-frontend.appspot.com")

    # Add --no-sandbox only in containerized environments
    # Security: --no-sandbox reduces Chrome's security on non-containerized systems
    if is_containerized_environment():
        args.append("--no-sandbox")
        print("[INFO] Containerized environment detected, adding --no-sandbox", file=sys.stderr)

    # Add user-provided extra arguments
    if extra_args:
        args.extend(extra_args)

    # Add environment variable arguments (similar to Nova Act's NOVA_ACT_BROWSER_ARGS)
    env_args = os.environ.get("BROWSER_LAUNCH_ARGS", "").strip()
    if env_args:
        args.extend(env_args.split())
        print(f"[INFO] Added browser args from BROWSER_LAUNCH_ARGS: {env_args}", file=sys.stderr)

    return args


def get_ignore_default_args() -> List[str]:
    """
    Get list of default Playwright arguments to ignore/remove.

    These are removed to enable password manager functionality:
    - --enable-automation: When set, shows "controlled by automation" infobar
      and disables some password manager features
    - --disable-component-extensions-with-background-pages: When set, disables
      background extension pages which breaks password manager popup UI
    - --hide-scrollbars: Playwright hides scrollbars by default in headless,
      but we want them visible for better UX in screenshots

    Returns:
        List of argument names to ignore
    """
    return [
        # Remove automation flag to:
        # 1. Hide "Chrome is being controlled by automated test software" infobar
        # 2. Enable password manager save prompts
        # 3. Enable password autofill on subsequent visits
        "--enable-automation",

        # Remove to enable password manager extension UI
        # This is CRITICAL for password managers that use popups/bubbles
        "--disable-component-extensions-with-background-pages",

        # Show scrollbars for better UX (Nova Act SDK does this too)
        "--hide-scrollbars",
    ]


def get_launch_options(
    headless: bool = False,
    browser_channel: Optional[str] = None,
    is_persistent_context: bool = True,
    window_size: Optional[tuple] = None,
    ignore_https_errors: bool = True,
    extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get complete launch options for Playwright browser launch.

    This is the main function to use for consistent browser launches.

    Args:
        headless: Whether to run in headless mode
        browser_channel: Browser channel ('chrome', 'msedge', 'chromium', etc.)
        is_persistent_context: Whether using persistent context
        window_size: Optional (width, height) tuple
        ignore_https_errors: Whether to ignore HTTPS certificate errors
        extra_args: Additional custom arguments

    Returns:
        Dictionary of launch options for Playwright

    Example:
        ```python
        from browser_launch_config import get_launch_options

        options = get_launch_options(
            headless=False,
            browser_channel='msedge',
            is_persistent_context=True
        )

        context = p.chromium.launch_persistent_context(
            user_data_dir,
            **options
        )
        ```
    """
    options = {
        "headless": headless,
        "args": get_base_browser_args(
            is_persistent_context=is_persistent_context,
            window_size=window_size,
            extra_args=extra_args
        ),
        "ignore_default_args": get_ignore_default_args(),
    }

    # Add browser channel if specified (and not 'chromium' which is the default)
    if browser_channel and browser_channel.lower() != "chromium":
        options["channel"] = browser_channel

    # Add HTTPS error handling
    if ignore_https_errors:
        options["ignore_https_errors"] = True

    return options


def get_default_browser_channel() -> str:
    """
    Get the default browser channel for the current platform.

    Returns:
        'msedge' on Windows, 'chrome' on other platforms
    """
    if platform.system() == "Windows":
        return "msedge"
    return "chrome"


def log_launch_config(options: Dict[str, Any], context_type: str = "launch") -> None:
    """
    Log the browser launch configuration for debugging.

    Args:
        options: Launch options dictionary
        context_type: Description of launch context (e.g., "profile_setup", "script_execution")
    """
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Browser Launch Configuration ({context_type})", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"  Headless: {options.get('headless', False)}", file=sys.stderr)
    print(f"  Channel: {options.get('channel', 'chromium (default)')}", file=sys.stderr)
    print(f"  Args: {options.get('args', [])}", file=sys.stderr)
    print(f"  Ignored defaults: {options.get('ignore_default_args', [])}", file=sys.stderr)
    print(f"  Container mode: {is_containerized_environment()}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)


# Convenience constants for common configurations
PROFILE_SETUP_OPTIONS = {
    "headless": False,  # Must be visible for manual login
    "is_persistent_context": True,
    "ignore_https_errors": True,
}

SCRIPT_EXECUTION_OPTIONS = {
    "headless": False,  # Default to visible, can be overridden
    "is_persistent_context": True,
    "ignore_https_errors": True,
}

EPHEMERAL_SESSION_OPTIONS = {
    "headless": False,
    "is_persistent_context": False,  # Adds AutomationControlled flag
    "ignore_https_errors": True,
}


if __name__ == "__main__":
    # Test/demo the configuration
    print("Browser Launch Configuration Demo")
    print("-" * 40)

    print("\n1. Profile Setup Options:")
    options = get_launch_options(**PROFILE_SETUP_OPTIONS, browser_channel="msedge")
    log_launch_config(options, "profile_setup")

    print("\n2. Script Execution Options:")
    options = get_launch_options(**SCRIPT_EXECUTION_OPTIONS, browser_channel="chrome")
    log_launch_config(options, "script_execution")

    print("\n3. Ephemeral Session Options:")
    options = get_launch_options(**EPHEMERAL_SESSION_OPTIONS)
    log_launch_config(options, "ephemeral")

    print("\n4. Container Detection:")
    print(f"  Is containerized: {is_containerized_environment()}")
