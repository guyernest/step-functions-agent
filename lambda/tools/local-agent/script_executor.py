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
    
    def execute_script(self, script_data: Union[str, Dict]) -> Dict[str, Any]:
        """
        Execute a script defined in JSON format.
        
        Args:
            script_data: Either a JSON string or a dictionary containing the script actions
            
        Returns:
            A dictionary with execution results
        """
        if isinstance(script_data, str):
            try:
                script = json.loads(script_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse script JSON: {e}")
                return {"success": False, "error": f"Invalid JSON: {str(e)}"}
        else:
            script = script_data
        
        # Check if the script has the expected format
        if not isinstance(script, dict) or "actions" not in script:
            return {"success": False, "error": "Script must contain an 'actions' list"}
        
        actions = script["actions"]
        results = []
        
        try:
            for i, action in enumerate(actions):
                action_type = action.get('type', 'unknown')
                logger.info(f"Executing action {i+1}/{len(actions)}: {action_type}")
                
                result = self._execute_action(action)
                results.append(result)
                
                # Log success or failure
                if result["success"]:
                    logger.info(f"Action {i+1}/{len(actions)} ({action_type}) completed successfully")
                else:
                    logger.error(f"Action {i+1}/{len(actions)} ({action_type}) failed: {result.get('error', 'Unknown error')}")
                
                # If an action fails and abort_on_error is set, stop execution
                if not result["success"] and script.get("abort_on_error", True):
                    logger.error(f"Aborting script execution after action {i+1} failed")
                    break
            
            # Determine overall success and create response object
            success = all(r["success"] for r in results)
            response = {
                "success": success,
                "results": results,
                "completed_actions": len(results),
                "total_actions": len(actions)
            }
            
            # Add summary for failed actions
            if not success:
                failed_actions = [
                    {
                        "index": i, 
                        "type": results[i].get("action_type", actions[i].get("type", "unknown")), 
                        "error": results[i].get("error", "Unknown error")
                    }
                    for i in range(len(results)) if not results[i]["success"]
                ]
                response["failed_actions"] = failed_actions
                
                # Include the first failure's screenshot if available
                for result in results:
                    if not result["success"] and "screenshot_data" in result:
                        # response["first_failure_screenshot"] = result["screenshot_data"]
                        break
            
            return response
        
        except Exception as e:
            logger.error(f"Script execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try to capture a screenshot of the error
            screenshot_data = None
            try:
                screenshot_path = self._capture_debug_screenshot("script_execution_error")
                import base64
                with open(screenshot_path, "rb") as img_file:
                    screenshot_data = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception as screenshot_error:
                logger.error(f"Failed to capture error screenshot: {screenshot_error}")
            
            error_response = {
                "success": False, 
                "error": str(e),
                "traceback": traceback.format_exc(),
                "results": results,
                "completed_actions": len(results),
                "total_actions": len(actions)
            }
            
            # if screenshot_data:
            #     error_response["error_screenshot"] = screenshot_data
                
            return error_response
    
    def _execute_action(self, action: Dict) -> Dict[str, Any]:
        """Execute a single action based on its type."""
        action_type = action.get("type", "").lower()
        
        try:
            if action_type == "click":
                return self._handle_click(action)
            elif action_type == "rightclick":
                return self._handle_right_click(action)
            elif action_type == "doubleclick":
                return self._handle_double_click(action)
            elif action_type == "moveto":
                return self._handle_move_to(action)
            elif action_type == "type":
                return self._handle_type(action)
            elif action_type == "press":
                return self._handle_key_press(action)
            elif action_type == "hotkey":
                return self._handle_hotkey(action)
            elif action_type == "wait":
                return self._handle_wait(action)
            elif action_type == "locateimage":
                return self._handle_locate_image(action)
            elif action_type == "dragto":
                return self._handle_drag_to(action)
            elif action_type == "scroll":
                return self._handle_scroll(action)
            elif action_type == "launch":
                return self._handle_launch(action)
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
        except Exception as e:
            logger.error(f"Action execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Capture a screenshot on unexpected errors
            screenshot_path = ""
            screenshot_data = None
            
            try:
                # Capture screenshot for debugging
                screenshot_path = self._capture_debug_screenshot(f"error_{action_type}")
                
                # Encode the screenshot as base64
                import base64
                with open(screenshot_path, "rb") as img_file:
                    screenshot_data = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception as screenshot_error:
                logger.error(f"Failed to capture error screenshot: {screenshot_error}")
            
            error_result = {
                "success": False, 
                "error": str(e),
                "action_type": action_type,
                "traceback": traceback.format_exc()
            }
            
            # if screenshot_data:
            #     error_result["screenshot_data"] = screenshot_data
            # elif screenshot_path:
            #     error_result["screenshot_path"] = screenshot_path
                
            return error_result
    
    def _get_position(self, action: Dict) -> tuple:
        """Extract position from an action, handling both absolute and relative coordinates."""
        if "position" in action:
            x, y = action["position"]
            # Check if position is relative (0.0-1.0) or absolute
            if isinstance(x, float) and 0 <= x <= 1 and isinstance(y, float) and 0 <= y <= 1:
                # Convert relative position to absolute pixels
                x = int(x * self.screen_width)
                y = int(y * self.screen_height)
            return (x, y)
        elif "image" in action:
            image_path = action["image"]
            confidence = action.get("confidence", 0.9)
            
            # Log the image path for debugging
            logger.info(f"Locating position using image: {image_path}")
            
            # Use the locate_image method which has our improved path resolution
            return self._locate_image(image_path, confidence)
        else:
            # Current mouse position
            return self.pyautogui.position()
    
    def _capture_debug_screenshot(self, prefix: str = "error") -> str:
        """
        Capture a screenshot for debugging purposes.
        
        Args:
            prefix: Prefix for the screenshot filename
            
        Returns:
            Path to the saved screenshot file
        """
        try:
            # Create a screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate a filename based on current timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = os.path.join(screenshots_dir, f"{prefix}_{timestamp}.png")
            
            # Take and save the screenshot
            screenshot = self.pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            logger.info(f"Saved debug screenshot to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to capture debug screenshot: {e}")
            return ""
            
    def _resolve_image_path(self, image_path: str) -> str:
        """
        Resolve an image path to an absolute path.
        Checks multiple locations to find the image.
        
        Args:
            image_path: Original image path (absolute or relative)
            
        Returns:
            Resolved absolute path to the image if found, empty string if not found
        """
        # If it's already an absolute path, check if it exists
        if os.path.isabs(image_path):
            if os.path.isfile(image_path):
                return image_path
            else:
                logger.warning(f"Image not found at absolute path: {image_path}")
                return ""
        
        # List of potential base directories to check
        base_dirs = [
            os.getcwd(),  # Current working directory
            os.path.dirname(os.path.abspath(__file__)),  # Script directory
        ]
        
        # Check if this is a path based on script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define potential locations where images might be found
        potential_paths = [
            # Original path relative to various base directories
            *[os.path.abspath(os.path.join(base_dir, image_path)) for base_dir in base_dirs],
            # Check without 'examples/' prefix if it starts with it (example files often include this)
            *[os.path.abspath(os.path.join(base_dir, image_path.replace('examples/', '', 1))) 
              for base_dir in base_dirs if image_path.startswith('examples/')],
            # Check with 'examples/' prefix if it doesn't have it
            *[os.path.abspath(os.path.join(base_dir, 'examples', image_path)) 
              for base_dir in base_dirs if not image_path.startswith('examples/')],
        ]
        
        # Log all potential paths for debugging
        logger.debug(f"Checking potential image paths for: {image_path}")
        for i, path in enumerate(potential_paths):
            logger.debug(f"  {i+1}: {path}")
        
        # Check each potential path
        for path in potential_paths:
            if os.path.isfile(path):
                logger.info(f"Found image at: {path}")
                return path
                
        # Image not found in any location
        logger.error(f"Image not found in any location: {image_path}")
        logger.error(f"Checked paths: {potential_paths}")
        return ""

    def _locate_image(self, image_path: str, confidence: float = 0.9) -> tuple:
        """
        Locate an image on screen and return its position.
        Uses OpenCV for improved image detection when available.
        
        Args:
            image_path: Path to the image to locate
            confidence: Minimum confidence threshold for matching (0.0-1.0)
            
        Returns:
            Tuple of (x, y) coordinates for the center of the matched image
            
        Raises:
            ValueError: If the image cannot be located
        """
        screenshot_path = ""
        
        # Resolve image path to handle both relative and absolute paths
        resolved_path = self._resolve_image_path(image_path)
        if not resolved_path:
            raise ValueError(f"Image not found at path: {image_path}")
            
        logger.info(f"Looking for image at resolved path: {resolved_path}")
        
        try:
            # First try the standard PyAutoGUI approach with higher grayscale parameter
            # This can help with distinguishing similar buttons
            logger.info(f"Attempting to locate image with PyAutoGUI (confidence={confidence})")
            location = self.pyautogui.locateCenterOnScreen(
                resolved_path, 
                confidence=confidence,
                grayscale=False  # Use color matching for better accuracy
            )
            
            if location is not None:
                logger.info(f"Found image {resolved_path} at position {location} using PyAutoGUI")
                return location
            
            # Check if OpenCV is available
            if not hasattr(self, 'cv2'):
                logger.warning("OpenCV (cv2) not available, cannot perform advanced image matching")
                # Capture screen for debugging before raising error
                screenshot_path = self._capture_debug_screenshot(f"image_not_found_{os.path.basename(resolved_path)}")
                raise ValueError(f"Could not locate image: {resolved_path}")
            
            # If PyAutoGUI failed, use OpenCV for more advanced matching
            logger.info(f"PyAutoGUI couldn't find image, trying with OpenCV...")
            
            try:
                # Take a screenshot
                screenshot = self.pyautogui.screenshot()
                screenshot_np = self.np.array(screenshot)
                screenshot_cv = self.cv2.cvtColor(screenshot_np, self.cv2.COLOR_RGB2BGR)
                
                # Load the template image
                template = self.cv2.imread(resolved_path)
                if template is None:
                    raise ValueError(f"Could not load image file: {resolved_path}")
                
                # Log template dimensions for debugging
                template_h, template_w = template.shape[:2]
                logger.debug(f"Template image dimensions: {template_w}x{template_h}")
                
                # Capture a debug screenshot with the current state
                debug_screenshot = self._capture_debug_screenshot(f"search_for_{os.path.basename(resolved_path)}")
                
                # Try multiple matching methods to find the best one
                methods = [
                    (self.cv2.TM_CCOEFF_NORMED, "TM_CCOEFF_NORMED"),
                    (self.cv2.TM_CCORR_NORMED, "TM_CCORR_NORMED")
                ]
                
                best_val = 0
                best_loc = None
                best_method = None
                
                for method, method_name in methods:
                    # Try both grayscale and color matching
                    for use_gray in [True, False]:
                        if use_gray:
                            # Use grayscale
                            search_img = self.cv2.cvtColor(screenshot_cv, self.cv2.COLOR_BGR2GRAY)
                            search_template = self.cv2.cvtColor(template, self.cv2.COLOR_BGR2GRAY)
                        else:
                            # Use color
                            search_img = screenshot_cv
                            search_template = template
                        
                        # Perform template matching
                        result = self.cv2.matchTemplate(search_img, search_template, method)
                        
                        # Find the best match location
                        min_val, max_val, min_loc, max_loc = self.cv2.minMaxLoc(result)
                        
                        # Log the result for debugging
                        logger.debug(f"Method {method_name} {'(grayscale)' if use_gray else '(color)'}: confidence={max_val:.4f}")
                        
                        # If this is the best match so far, save it
                        if max_val > best_val:
                            best_val = max_val
                            best_loc = max_loc
                            best_method = f"{method_name} {'(grayscale)' if use_gray else '(color)'}"
                
                # Log the best method
                logger.info(f"Best match using {best_method} with confidence {best_val:.4f}")
                
                # Check if we found a match with sufficient confidence
                if best_val >= confidence and best_loc is not None:
                    # Get the center of the matched area
                    center_x = best_loc[0] + template_w // 2
                    center_y = best_loc[1] + template_h // 2
                    
                    logger.info(f"Found image {resolved_path} at position ({center_x}, {center_y}) using OpenCV with confidence {best_val:.4f}")
                    
                    # Draw and save a debug image showing the match
                    debug_img = screenshot_cv.copy()
                    self.cv2.rectangle(debug_img, best_loc, (best_loc[0] + template_w, best_loc[1] + template_h), (0, 255, 0), 2)
                    match_path = self._capture_debug_screenshot(f"match_{os.path.basename(resolved_path)}")
                    match_path = os.path.splitext(match_path)[0] + "_annotated.png"
                    self.cv2.imwrite(match_path, debug_img)
                    logger.info(f"Saved image match visualization to {match_path}")
                    
                    return (center_x, center_y)
                
                # If we got here, neither method found the image
                # Capture screen for debugging
                screenshot_path = self._capture_debug_screenshot(f"low_confidence_{os.path.basename(resolved_path)}")
                
                # Draw the best match on the screenshot for debugging
                if best_loc is not None:
                    debug_img = screenshot_cv.copy()
                    self.cv2.rectangle(debug_img, best_loc, (best_loc[0] + template_w, best_loc[1] + template_h), (0, 0, 255), 2)
                    
                    # Save the annotated debug image
                    debug_path = os.path.splitext(screenshot_path)[0] + "_annotated.png"
                    self.cv2.imwrite(debug_path, debug_img)
                    logger.info(f"Saved best match debug image to {debug_path} (confidence {best_val:.4f} below threshold {confidence})")
                
                raise ValueError(f"Could not locate image: {resolved_path} (best OpenCV match: {best_val:.4f}, required: {confidence})")
            except Exception as cv_error:
                if not screenshot_path:
                    screenshot_path = self._capture_debug_screenshot(f"opencv_error_{os.path.basename(resolved_path)}")
                logger.error(f"OpenCV image matching failed: {cv_error}")
                raise ValueError(f"Could not locate image: {resolved_path} (OpenCV error: {cv_error})")
                
        except Exception as e:
            if not screenshot_path:
                screenshot_path = self._capture_debug_screenshot(f"error_{os.path.basename(resolved_path)}")
            logger.error(f"Error trying to locate image {resolved_path}: {e}")
            raise ValueError(f"Could not locate image: {resolved_path} due to error: {e}", screenshot_path)
    
    def _handle_click(self, action: Dict) -> Dict[str, Any]:
        """Handle a click action."""
        # Get the click position
        if "position" in action:
            # Explicit position in the action
            x, y = self._get_position(action)
        elif "image" in action:
            # Direct image target in the click action - this is the standard PyAutoGUI pattern
            # pyautogui.click('button.png') is a common usage pattern
            logger.info(f"Clicking directly on image: {action['image']}")
            x, y = self._locate_image(action["image"], action.get("confidence", 0.9))
        elif self.state["last_image_position"] is not None:
            # Use position from the last located image
            logger.info("Using position from last located image")
            x, y = self.state["last_image_position"]
        else:
            # Fall back to current mouse position
            logger.info("No position specified for click, using current mouse position")
            x, y = self.pyautogui.position()
        
        logger.info(f"Clicking at position: ({x}, {y})")
        
        # Button and click parameters
        button = action.get("button", "left")
        count = action.get("count", 1)
        
        # Move cursor to the target location - this is essential for many applications
        # Especially for Windows/Mac applications that track the actual cursor
        duration = 0.2  # Duration of mouse movement
        self.pyautogui.moveTo(x, y, duration=duration)
        
        # Small pause to ensure the application registers the cursor position
        time.sleep(0.2)
        
        # Click using a more reliable approach that works cross-platform
        try:
            if button == "left" and count == 2:
                # Handle double-click specially
                logger.info(f"Performing a double-click at ({x}, {y})")
                # Double-click with a specific implementation that works reliably
                self.pyautogui.doubleClick(x=x, y=y)
            else:
                # For single clicks or non-left button clicks
                for i in range(count):
                    # Perform click with move (this works more reliably)
                    self.pyautogui.click(x=x, y=y, button=button)
                    if i < count - 1:
                        # Small pause between multiple clicks
                        time.sleep(0.1)
            
            # Store the successful click position
            self.state["last_click_position"] = (x, y)
            
            # Small pause after click to let the application process it
            time.sleep(0.2)
            
            return {"success": True, "position": (x, y)}
            
        except Exception as e:
            # Log the error and try a fallback method
            logger.error(f"Click operation failed: {e}")
            
            try:
                # Fallback to a more direct approach
                logger.info("Using fallback click method")
                self.pyautogui.moveTo(x, y, duration=0.3)  # More deliberate move
                time.sleep(0.3)
                
                # Try a more direct mouse down/up approach
                self.pyautogui.mouseDown(x=x, y=y, button=button)
                time.sleep(0.2)
                self.pyautogui.mouseUp(x=x, y=y, button=button)
                
                # Store the position even in fallback case
                self.state["last_click_position"] = (x, y)
                
                return {"success": True, "position": (x, y), "method": "fallback"}
            except Exception as fallback_error:
                logger.error(f"Fallback click also failed: {fallback_error}")
                return {
                    "success": False, 
                    "error": f"Click operation failed: {str(e)}. Fallback also failed: {str(fallback_error)}",
                    "position": (x, y)
                }
    
    def _handle_right_click(self, action: Dict) -> Dict[str, Any]:
        """Handle a right-click action."""
        # Use similar logic to regular clicks for consistency
        if "position" in action:
            x, y = self._get_position(action)
        elif "image" in action:
            x, y = self._locate_image(action["image"], action.get("confidence", 0.9))
        elif self.state["last_image_position"] is not None:
            logger.info("Using position from last located image")
            x, y = self.state["last_image_position"]
        else:
            x, y = self.pyautogui.position()
        
        logger.info(f"Right-clicking at position: ({x}, {y})")
        
        # Move to position first (important for some applications)
        self.pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.2)
        
        # Perform the right-click
        self.pyautogui.rightClick(x=x, y=y)
        
        # Store the click position
        self.state["last_click_position"] = (x, y)
        
        # Small pause to let the click take effect
        time.sleep(0.2)
        
        return {"success": True, "position": (x, y)}
    
    def _handle_double_click(self, action: Dict) -> Dict[str, Any]:
        """Handle a double-click action."""
        # Use similar logic to regular clicks for consistency
        if "position" in action:
            x, y = self._get_position(action)
        elif "image" in action:
            x, y = self._locate_image(action["image"], action.get("confidence", 0.9))
        elif self.state["last_image_position"] is not None:
            logger.info("Using position from last located image")
            x, y = self.state["last_image_position"]
        else:
            x, y = self.pyautogui.position()
        
        logger.info(f"Double-clicking at position: ({x}, {y})")
        
        # Move to position first (important for some applications)
        self.pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.2)
        
        # Perform the double-click
        self.pyautogui.doubleClick(x=x, y=y)
        
        # Store the click position
        self.state["last_click_position"] = (x, y)
        
        # Small pause to let the click take effect
        time.sleep(0.2)
        
        return {"success": True, "position": (x, y)}
    
    def _handle_move_to(self, action: Dict) -> Dict[str, Any]:
        """Handle a move to action."""
        x, y = self._get_position(action)
        duration = action.get("duration", 0.5)
        self.pyautogui.moveTo(x=x, y=y, duration=duration)
        return {"success": True, "position": (x, y)}
    
    def _handle_type(self, action: Dict) -> Dict[str, Any]:
        """Handle a type action."""
        if "text" not in action:
            return {"success": False, "error": "No text specified for type action"}
        
        text = action["text"]
        interval = action.get("interval", 0.1)
        self.pyautogui.write(text, interval=interval)
        return {"success": True, "text": text}
    
    def _handle_key_press(self, action: Dict) -> Dict[str, Any]:
        """Handle a key press action."""
        if "key" not in action:
            return {"success": False, "error": "No key specified for press action"}
        
        key = action["key"]
        presses = action.get("presses", 1)
        interval = action.get("interval", 0.1)
        self.pyautogui.press(key, presses=presses, interval=interval)
        return {"success": True, "key": key, "presses": presses}
    
    def _handle_hotkey(self, action: Dict) -> Dict[str, Any]:
        """Handle a hotkey action."""
        if "keys" not in action or not isinstance(action["keys"], list):
            return {"success": False, "error": "No keys list specified for hotkey action"}
        
        keys = action["keys"]
        self.pyautogui.hotkey(*keys)
        return {"success": True, "keys": keys}
    
    def _handle_wait(self, action: Dict) -> Dict[str, Any]:
        """Handle a wait action."""
        seconds = action.get("seconds", 1.0)
        time.sleep(seconds)
        return {"success": True, "seconds": seconds}
    
    def _handle_locate_image(self, action: Dict) -> Dict[str, Any]:
        """Handle a locate image action."""
        if "image" not in action:
            return {"success": False, "error": "No image specified for locateImage action"}
        
        image_path = action["image"]
        confidence = action.get("confidence", 0.9)
        
        # Log detailed information about the locate image request
        logger.info(f"Handling locateImage action for: {image_path} with confidence {confidence}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        try:
            # Attempt to locate the image
            x, y = self._locate_image(image_path, confidence)
            
            # Store the position and path in state for subsequent actions
            logger.info(f"Found image and storing position in state: ({x}, {y})")
            self.state["last_image_position"] = (x, y)
            self.state["last_image_path"] = image_path
            
            # Move the mouse to the image position - this is essential
            # Helps with application focus and makes subsequent clicks more reliable
            # This is particularly important on Windows applications
            if action.get("move_cursor", True):
                logger.info(f"Moving cursor to image position: ({x}, {y})")
                self.pyautogui.moveTo(x, y, duration=0.2)
                
                # Give the system time to register the cursor movement
                time.sleep(0.2)
            
            # If the action specifies to click the image after finding it
            if action.get("click_after_locate", False):
                logger.info("Auto-clicking the located image as requested")
                button = action.get("button", "left")
                self.pyautogui.click(x=x, y=y, button=button)
                
                # Store the click position as well
                self.state["last_click_position"] = (x, y)
                
                # Give the application time to respond to the click
                time.sleep(0.2)
            
            return {
                "success": True, 
                "position": (x, y), 
                "image": image_path,
                "resolved_path": self._resolve_image_path(image_path)
            }
        except ValueError as e:
            # Reset the state for failed image location
            self.state["last_image_position"] = None
            self.state["last_image_path"] = None
            
            # Prepare a detailed error result
            error_result = {
                "success": False, 
                "error": str(e), 
                "image": image_path,
            }
            
            # Add the paths that were checked
            attempted_path = self._resolve_image_path(image_path)
            if attempted_path:
                error_result["resolved_path"] = attempted_path
            else:
                error_result["error"] = f"Image not found: {image_path}. Make sure the image file exists and is accessible."
            
            # Check if the exception has a screenshot path as a second argument
            if len(e.args) > 1 and e.args[1]:
                # Load the screenshot and encode it as base64
                try:
                    import base64
                    with open(e.args[1], "rb") as img_file:
                        encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
                        # error_result["screenshot_data"] = encoded_img
                        logger.info(f"Screenshot encoded and included in error result")
                        error_result["screenshot_path"] = e.args[1]
                except Exception as img_error:
                    logger.error(f"Failed to encode screenshot: {img_error}")
                    error_result["screenshot_path"] = e.args[1]
            
            # Add more diagnostic information
            error_result["cwd"] = os.getcwd()
            error_result["script_dir"] = os.path.dirname(os.path.abspath(__file__))
            
            return error_result
    
    def _handle_drag_to(self, action: Dict) -> Dict[str, Any]:
        """Handle a drag to action."""
        # Get start position
        start_x, start_y = self.pyautogui.position()
        if "from_position" in action:
            start_x, start_y = action["from_position"]
            if isinstance(start_x, float) and 0 <= start_x <= 1 and isinstance(start_y, float) and 0 <= start_y <= 1:
                start_x = int(start_x * self.screen_width)
                start_y = int(start_y * self.screen_height)
        
        # Get end position
        if "to_position" not in action:
            return {"success": False, "error": "No to_position specified for dragTo action"}
        
        end_x, end_y = action["to_position"]
        if isinstance(end_x, float) and 0 <= end_x <= 1 and isinstance(end_y, float) and 0 <= end_y <= 1:
            end_x = int(end_x * self.screen_width)
            end_y = int(end_y * self.screen_height)
        
        duration = action.get("duration", 0.5)
        button = action.get("button", "left")
        
        self.pyautogui.dragTo(end_x, end_y, duration=duration, button=button)
        return {"success": True, "from": (start_x, start_y), "to": (end_x, end_y)}
    
    def _handle_scroll(self, action: Dict) -> Dict[str, Any]:
        """Handle a scroll action."""
        clicks = action.get("clicks", 10)
        self.pyautogui.scroll(clicks)
        return {"success": True, "clicks": clicks}
    
    def _handle_launch(self, action: Dict) -> Dict[str, Any]:
        """Handle launching an application."""
        import subprocess
        
        if "app" not in action:
            return {"success": False, "error": "No app specified for launch action"}
        
        app = action["app"]
        args = action.get("args", [])
        
        try:
            process = None
            if sys.platform == "win32":
                process = subprocess.Popen([app] + args)
            elif sys.platform == "darwin":  # macOS
                # On macOS, 'open -a AppName' launches the app and returns immediately
                # We can't check if the actual application launched successfully using the process
                process = subprocess.Popen(["open", "-a", app] + args)
            else:  # Linux and others
                process = subprocess.Popen([app] + args)
            
            # Wait a bit for the app to launch
            wait_time = action.get("wait", 2.0)
            time.sleep(wait_time)
            
            if sys.platform == "darwin":
                # For macOS, we need to check if the 'open' command itself succeeded
                if process and process.poll() is not None and process.returncode != 0:
                    return {
                        "success": False, 
                        "error": f"Failed to launch {app} (open command failed with exit code: {process.returncode})",
                        "app": app,
                        "exit_code": process.returncode
                    }
                
                # For macOS, the 'open' command succeeded. 
                # We don't try to verify if the app is running as this is unreliable
                # Some app process names don't match their app names
                # Just log the assumption and continue
                logger.info(f"Launched {app} on macOS (open command succeeded)")
                
                # For macOS, we assume success if the 'open' command succeeded
                return {"success": True, "app": app}
            else:
                # For Windows/Linux, check if process exited with an error code
                if process and process.poll() is not None and process.returncode != 0:
                    return {
                        "success": False, 
                        "error": f"Application {app} failed to launch (exit code: {process.returncode})",
                        "app": app,
                        "exit_code": process.returncode
                    }
                
                # Process either completed with success or is still running
                return {"success": True, "app": app}
        except FileNotFoundError:
            error_msg = f"Application {app} not found"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "app": app}
        except PermissionError:
            error_msg = f"Permission denied when launching {app}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "app": app}
        except Exception as e:
            error_msg = f"Failed to launch {app}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "app": app}

def main():
    """Main entry point for the script executor."""
    parser = argparse.ArgumentParser(description="Execute PyAutoGUI scripts from JSON")
    parser.add_argument("script", help="JSON script to execute (filepath or JSON string)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging (even more verbose)")
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    elif args.verbose:
        logger.setLevel(logging.INFO)
        logger.info("Verbose logging enabled")
    
    # Log important environment information
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Platform: {sys.platform}")
    
    # Ensure we have all required dependencies
    if not ensure_dependencies():
        return 1
    
    executor = ActionExecutor()
    
    # Check if the script argument is a file path or a JSON string
    if args.script.endswith('.json') or '/' in args.script or '\\' in args.script:
        try:
            script_path = args.script
            # If it's a relative path, make it absolute
            if not os.path.isabs(script_path):
                script_path = os.path.abspath(script_path)
                
            logger.info(f"Reading script from file: {script_path}")
            
            with open(script_path, 'r') as f:
                script_data = f.read()
                
            # Set the working directory to the script's directory for better image path resolution
            script_dir = os.path.dirname(script_path)
            if script_dir:
                logger.info(f"Changing working directory to script location: {script_dir}")
                os.chdir(script_dir)
        except Exception as e:
            logger.error(f"Failed to read script file: {e}")
            return 1
    else:
        logger.info("Using script data provided as command line argument")
        script_data = args.script
    
    try:
        logger.info("Starting script execution")
        result = executor.execute_script(script_data)
        print(json.dumps(result, indent=2, default=str))
        
        if not result["success"]:
            logger.error("Script execution failed")
            return 1
            
        logger.info("Script execution completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())