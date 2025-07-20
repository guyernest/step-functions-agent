#!/usr/bin/env python3
"""
Script Executor for Local Agent

This module executes scripts received from the Step Functions Activity tasks.
It uses PyAutoGUI to automate GUI interactions with local applications.
Dependencies are managed with uv/uvx.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("script_executor")

def run_with_uvx():
    """
    Re-run this script using uvx with the required dependencies.
    
    This allows us to execute the script with the necessary dependencies
    without requiring prior installation. The uvx run command will create a temporary
    environment with the required packages and execute this script within it.
    """
    # Since uvx is causing issues with the 'file' vs 'open' function in some dependencies,
    # and we can't easily fix all those dependencies, we'll use pip directly if dependencies
    # aren't already installed.
    
    logger.info("Required dependencies not installed, installing with pip...")
    try:
        # Try to install required dependencies with pip
        pip_cmd = [sys.executable, "-m", "pip", "install", "pyautogui", "pillow"]
        logger.info(f"Running: {' '.join(pip_cmd)}")
        subprocess.run(pip_cmd, check=True)
        
        # Try to install optional dependency, but continue if it fails
        try:
            opencv_cmd = [sys.executable, "-m", "pip", "install", "opencv-python"]
            logger.info(f"Running: {' '.join(opencv_cmd)}")
            subprocess.run(opencv_cmd, check=True)
            logger.info("Successfully installed OpenCV")
        except subprocess.SubprocessError as cv_error:
            logger.warning(f"Failed to install optional dependency OpenCV: {cv_error}")
            logger.warning("Continuing without OpenCV support")
        
        # Now re-run this script (which should now have dependencies available)
        logger.info("Re-running script with installed dependencies")
        return subprocess.run([sys.executable] + sys.argv, check=False).returncode
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to install required dependencies with pip: {e}")
        return 1

def ensure_dependencies():
    """Ensure all required dependencies are installed, or use uvx to run the script."""
    required_packages = ["pyautogui", "pillow"]
    optional_packages = ["opencv-python"]
    
    # Check if the script is being run by uvx
    if os.environ.get("UV_ACTIVE") == "1":
        try:
            # uvx is running us - try to import required packages
            import pyautogui
            logger.info("Running with uvx with required dependencies available")
            # Try to import optional packages
            try:
                import cv2
                logger.info("OpenCV is also available")
            except ImportError:
                logger.warning("OpenCV not available but continuing anyway")
            return True
        except ImportError as e:
            logger.error(f"Required dependency not available despite running with uvx: {e}")
            return False
    
    # Not running with uvx - try to import directly
    try:
        import pyautogui
        logger.info("Required dependencies are already installed")
        # Try to import optional packages
        try:
            import cv2
            logger.info("OpenCV is also available")
        except ImportError:
            logger.warning("OpenCV not available but continuing anyway")
        return True
    except ImportError as e:
        logger.info(f"Required dependency not installed: {e}, trying to use uvx...")
        
        # Check if uvx is available
        try:
            subprocess.run(["uvx", "--version"], check=True, capture_output=True)
            logger.info("uvx is available, rerunning script with dependencies")
            
            # Re-run this script with uvx
            sys.exit(run_with_uvx())
            
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("uvx is not available. Please install it first.")
            logger.error("Install with: curl -sSf https://astral.sh/uv/install.sh | sh")
            return False

class ActionExecutor:
    """Executes PyAutoGUI actions based on JSON script definitions."""
    
    def __init__(self):
        # Import pyautogui here after ensuring dependencies
        import pyautogui
        self.pyautogui = pyautogui
        
        # Try to import OpenCV and numpy, but continue if they're not available
        try:
            import cv2
            import numpy as np
            self.cv2 = cv2
            self.np = np
            logger.info("OpenCV (cv2) is available for enhanced image detection")
        except ImportError as e:
            logger.warning(f"OpenCV or numpy not available, falling back to basic image detection: {e}")
            
        # Set safety features for PyAutoGUI
        self.pyautogui.PAUSE = 0.5  # Add a 0.5 second pause after each PyAutoGUI call
        self.pyautogui.FAILSAFE = True  # Move mouse to upper left to abort
        
        self.screen_width, self.screen_height = self.pyautogui.size()
        logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")
        
        # State tracking for actions
        self.state = {
            "last_image_position": None,  # Store the position of the last located image
            "last_click_position": None,  # Store the position of the last click
            "last_image_path": None,      # Store the path of the last located image
            "active_window": None,        # Track the currently active window
        }

def main():
    """Main entry point for the script executor."""
    if len(sys.argv) != 2:
        print("Usage: script_executor.py <script_file>")
        sys.exit(1)
    
    script_file = sys.argv[1]
    
    # Ensure dependencies are available
    if not ensure_dependencies():
        logger.error("Failed to ensure dependencies")
        sys.exit(1)
    
    # Initialize the action executor
    executor = ActionExecutor()
    
    try:
        # Load the script from file
        with open(script_file, 'r') as f:
            script_data = json.load(f)
        
        # Execute the script
        result = executor.execute_script(script_data)
        
        # Output the result as JSON
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()