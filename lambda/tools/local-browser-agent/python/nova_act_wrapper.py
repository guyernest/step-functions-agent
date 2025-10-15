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
from typing import Dict, Any, Optional
import boto3
from nova_act import NovaAct, BOOL_SCHEMA
from nova_act.util.s3_writer import S3Writer


def execute_browser_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a browser automation command using Nova Act

    Args:
        command: Dictionary containing:
            - command_type: 'start_session', 'act', or 'end_session'
            - prompt: Natural language instruction (for 'act')
            - starting_page: Initial URL (for 'start_session')
            - session_id: Session identifier
            - s3_bucket: S3 bucket for recordings
            - user_data_dir: Chrome profile directory
            - max_steps: Maximum browser steps
            - timeout: Timeout in seconds
            - schema: JSON schema for output
            - headless: Run headless mode
            - record_video: Record video

    Returns:
        Dictionary with execution result
    """
    command_type = command.get('command_type', 'act')

    try:
        if command_type == 'start_session':
            return start_session(command)
        elif command_type == 'act':
            return execute_act(command)
        elif command_type == 'end_session':
            return end_session(command)
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

        # Add authentication: use API key if available, otherwise use boto_session
        # Nova Act doesn't allow both
        if nova_act_api_key:
            nova_act_kwargs["nova_act_api_key"] = nova_act_api_key
        else:
            nova_act_kwargs["boto_session"] = boto_session

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
