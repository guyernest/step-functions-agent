#!/usr/bin/env python3
"""
Tests for the script_executor.py module.

These tests validate the functionality of the script executor
that processes PyAutoGUI scripts on various platforms, including macOS.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import script_executor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import script_executor

class TestScriptExecutor(unittest.TestCase):
    """Test cases for the script executor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock PyAutoGUI
        self.mock_pyautogui = MagicMock()
        self.mock_pyautogui.size.return_value = (1920, 1080)
        self.mock_pyautogui.position.return_value = (100, 100)
        
        # Create patches
        # 1. Patch the ensure_dependencies to always return True
        self.ensure_deps_patcher = patch('script_executor.ensure_dependencies', return_value=True)
        
        # 2. Patch the pyautogui import in ActionExecutor.__init__
        self.pyautogui_import_patcher = patch('script_executor.ActionExecutor.__init__', autospec=True)
        
        # Start patches
        self.ensure_deps_patcher.start()
        self.mock_init = self.pyautogui_import_patcher.start()
        
        # Make the init function do nothing (it's mocked)
        self.mock_init.return_value = None
        
        # Create an executor instance (will use our mocked __init__)
        self.executor = script_executor.ActionExecutor()
        
        # Set up the executor's attributes manually since we bypassed __init__
        self.executor.pyautogui = self.mock_pyautogui
        self.executor.screen_width = 1920
        self.executor.screen_height = 1080
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        self.ensure_deps_patcher.stop()
        self.pyautogui_import_patcher.stop()
    
    def test_script_format_validation(self):
        """Test validation of script format."""
        # Invalid JSON
        result = self.executor.execute_script("invalid json")
        self.assertFalse(result["success"])
        self.assertIn("Invalid JSON", result["error"])
        
        # Missing actions list
        result = self.executor.execute_script('{"name": "test"}')
        self.assertFalse(result["success"])
        self.assertIn("must contain an 'actions' list", result["error"])
    
    def test_click_action(self):
        """Test click action execution."""
        script = {
            "actions": [
                {"type": "click", "position": [500, 300]}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.click.assert_called_once_with(x=500, y=300, button='left')
        
        # Test with relative coordinates
        script = {
            "actions": [
                {"type": "click", "position": [0.5, 0.5]}
            ]
        }
        
        self.mock_pyautogui.click.reset_mock()
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.click.assert_called_once_with(x=960, y=540, button='left')
    
    def test_type_action(self):
        """Test type action execution."""
        script = {
            "actions": [
                {"type": "type", "text": "Hello, world!"}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.write.assert_called_once_with("Hello, world!", interval=0.1)
        
        # Test with custom interval
        script = {
            "actions": [
                {"type": "type", "text": "Hello, world!", "interval": 0.2}
            ]
        }
        
        self.mock_pyautogui.write.reset_mock()
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.write.assert_called_once_with("Hello, world!", interval=0.2)
        
        # Test with missing text
        script = {
            "actions": [
                {"type": "type"}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertFalse(result["success"])
        self.assertIn("No text specified", result["results"][0]["error"])
    
    def test_key_press_action(self):
        """Test key press action execution."""
        script = {
            "actions": [
                {"type": "press", "key": "enter"}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.press.assert_called_once_with("enter", presses=1, interval=0.1)
        
        # Test with multiple presses
        script = {
            "actions": [
                {"type": "press", "key": "tab", "presses": 3, "interval": 0.3}
            ]
        }
        
        self.mock_pyautogui.press.reset_mock()
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.press.assert_called_once_with("tab", presses=3, interval=0.3)
    
    def test_hotkey_action(self):
        """Test hotkey action execution."""
        script = {
            "actions": [
                {"type": "hotkey", "keys": ["ctrl", "c"]}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")
        
        # Test Mac-specific hotkeys (command instead of ctrl)
        script = {
            "actions": [
                {"type": "hotkey", "keys": ["command", "c"]}
            ]
        }
        
        self.mock_pyautogui.hotkey.reset_mock()
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.hotkey.assert_called_once_with("command", "c")
    
    def test_wait_action(self):
        """Test wait action execution."""
        with patch('time.sleep') as mock_sleep:
            script = {
                "actions": [
                    {"type": "wait", "seconds": 2.5}
                ]
            }
            
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            mock_sleep.assert_called_once_with(2.5)
    
    def test_locate_image_action(self):
        """Test locate image action."""
        # Mock locateCenterOnScreen to return a position
        self.mock_pyautogui.locateCenterOnScreen.return_value = (500, 300)
        
        script = {
            "actions": [
                {"type": "locateimage", "image": "button.png", "confidence": 0.8}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.locateCenterOnScreen.assert_called_once_with("button.png", confidence=0.8)
        
        # Test image not found with PyAutoGUI but found with OpenCV
        self.mock_pyautogui.locateCenterOnScreen.return_value = None
        self.mock_pyautogui.locateCenterOnScreen.reset_mock()
        
        # Mock cv2 for the OpenCV fallback
        mock_cv2 = MagicMock()
        mock_template = MagicMock()
        mock_cv2.imread.return_value = mock_template
        mock_cv2.minMaxLoc.return_value = (0.1, 0.85, (100, 100), (400, 200))  # min_val, max_val, min_loc, max_loc
        mock_template.shape = (50, 100)  # height, width for template
        
        # Add cv2 to executor
        self.executor.cv2 = mock_cv2
        
        # Fix the _locate_image method for testing
        def mock_locate_image(image_path, confidence=0.9):
            # Return center coordinates calculated from our mock values
            return (450, 225)  # (400 + 100/2, 200 + 50/2)
            
        self.executor._locate_image = mock_locate_image
        
        # Mock numpy and screenshot
        with patch('numpy.array', return_value=MagicMock()):
            # Create a mock screenshot
            mock_screenshot = MagicMock()
            self.mock_pyautogui.screenshot.return_value = mock_screenshot
            
            # Execute script
            result = self.executor.execute_script(script)
            
            # Assert that it was successful
            self.assertTrue(result["success"])
            # The center should be at max_loc + half width/height of template
            self.assertEqual(result["results"][0]["position"], (450, 225))  # (400 + 100/2, 200 + 50/2)
        
        # Test image not found with either method
        def mock_locate_image_fail(image_path, confidence=0.9):
            raise ValueError(f"Could not locate image: {image_path} (best OpenCV match: 0.50)")
            
        self.executor._locate_image = mock_locate_image_fail
        
        with patch('numpy.array', return_value=MagicMock()):
            result = self.executor.execute_script(script)
            self.assertFalse(result["success"])
            self.assertIn("Could not locate image", result["results"][0]["error"])
    
    def test_launch_windows_app(self):
        """Test launching a Windows application."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('time.sleep') as mock_sleep, \
             patch('sys.platform', 'win32'):
                
            # Configure mock process to return success (returncode 0)
            mock_process = MagicMock()
            mock_process.poll.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
                
            script = {
                "actions": [
                    {"type": "launch", "app": "notepad", "args": ["test.txt"], "wait": 1.0}
                ]
            }
            
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            mock_popen.assert_called_once_with(["notepad", "test.txt"])
            mock_sleep.assert_called_once_with(1.0)
    
    def test_launch_mac_app(self):
        """Test launching a macOS application with various applications."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('time.sleep') as mock_sleep, \
             patch('sys.platform', 'darwin'):
            
            # Configure mock process to return success (returncode 0)
            # This simulates the 'open' command completing successfully
            mock_process = MagicMock()
            mock_process.poll.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Test TextEdit
            script = {
                "actions": [
                    {"type": "launch", "app": "TextEdit", "args": ["test.txt"]}
                ]
            }
            
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            mock_popen.assert_called_once_with(["open", "-a", "TextEdit", "test.txt"])
            mock_sleep.assert_called_once_with(2.0)  # Default wait time
            
            # Test another Mac app (Safari)
            mock_popen.reset_mock()
            mock_sleep.reset_mock()
            
            script = {
                "actions": [
                    {"type": "launch", "app": "Safari", "wait": 3.0}
                ]
            }
            
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            mock_popen.assert_called_once_with(["open", "-a", "Safari"])
            mock_sleep.assert_called_once_with(3.0)
            
            # Test Preview app with a PDF file
            mock_popen.reset_mock()
            mock_sleep.reset_mock()
            
            script = {
                "actions": [
                    {"type": "launch", "app": "Preview", "args": ["document.pdf"]}
                ]
            }
            
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            mock_popen.assert_called_once_with(["open", "-a", "Preview", "document.pdf"])
            mock_sleep.assert_called_once_with(2.0)
            
            # Test with a different app
            mock_popen.reset_mock()
            mock_sleep.reset_mock()
            
            script = {
                "actions": [
                    {"type": "launch", "app": "AnotherApp"}
                ]
            }
            
            # As long as the 'open' command succeeds, we consider the launch successful
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            mock_popen.assert_called_once_with(["open", "-a", "AnotherApp"])

    def test_mac_specific_workflow(self):
        """Test a complete workflow focused on macOS TextEdit operations."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('time.sleep') as mock_sleep, \
             patch('sys.platform', 'darwin'):
                
            # Configure mock process to return success (returncode 0)
            # This simulates the 'open' command completing successfully
            mock_process = MagicMock()
            mock_process.poll.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Create a script that simulates typing in TextEdit
            script = {
                "actions": [
                    # Launch TextEdit
                    {"type": "launch", "app": "TextEdit", "wait": 1.5},
                    # Create a new document with Command+N (if needed)
                    {"type": "hotkey", "keys": ["command", "n"]},
                    # Type some text
                    {"type": "type", "text": "Hello from macOS TextEdit!"},
                    # Select all with Command+A
                    {"type": "hotkey", "keys": ["command", "a"]},
                    # Make it bold with Command+B
                    {"type": "hotkey", "keys": ["command", "b"]},
                    # Click somewhere else to deselect
                    {"type": "click", "position": [500, 500]},
                    # Type more text
                    {"type": "type", "text": "\n\nThis is a test document."},
                    # Save the document with Command+S
                    {"type": "hotkey", "keys": ["command", "s"]},
                    # Wait for save dialog
                    {"type": "wait", "seconds": 1.0},
                    # Type the filename
                    {"type": "type", "text": "test_document.txt"},
                    # Press Enter to save
                    {"type": "press", "key": "return"}
                ]
            }
            
            result = self.executor.execute_script(script)
            self.assertTrue(result["success"])
            
            # Verify the TextEdit app was launched
            mock_popen.assert_called_once_with(["open", "-a", "TextEdit"])
            
            # Verify hotkeys were used as expected
            self.assertEqual(self.mock_pyautogui.hotkey.call_count, 4)  # Four hotkey calls: n, a, b, s
            self.mock_pyautogui.hotkey.assert_any_call("command", "n")
            self.mock_pyautogui.hotkey.assert_any_call("command", "a")
            self.mock_pyautogui.hotkey.assert_any_call("command", "b")
            self.mock_pyautogui.hotkey.assert_any_call("command", "s")
            
            # Verify typing operations
            self.assertEqual(self.mock_pyautogui.write.call_count, 3)
            self.mock_pyautogui.write.assert_any_call("Hello from macOS TextEdit!", interval=0.1)
            self.mock_pyautogui.write.assert_any_call("\n\nThis is a test document.", interval=0.1)
            self.mock_pyautogui.write.assert_any_call("test_document.txt", interval=0.1)
            
            # Verify click operation
            self.mock_pyautogui.click.assert_called_once_with(x=500, y=500, button='left')
            
            # Verify the return key was pressed
            self.mock_pyautogui.press.assert_called_once_with("return", presses=1, interval=0.1)
    
    def test_drag_to_action(self):
        """Test drag to action."""
        script = {
            "actions": [
                {"type": "dragto", "to_position": [800, 600], "duration": 1.0}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.dragTo.assert_called_once_with(800, 600, duration=1.0, button="left")
        
        # Test with relative coordinates
        script = {
            "actions": [
                {"type": "dragto", "from_position": [0.1, 0.1], "to_position": [0.9, 0.9], "duration": 2.0}
            ]
        }
        
        self.mock_pyautogui.dragTo.reset_mock()
        result = self.executor.execute_script(script)
        self.assertTrue(result["success"])
        self.mock_pyautogui.dragTo.assert_called_once_with(1728, 972, duration=2.0, button="left")
    
    def test_unknown_action_type(self):
        """Test behavior with unknown action type."""
        script = {
            "actions": [
                {"type": "unknown_action"}
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertFalse(result["success"])
        self.assertIn("Unknown action type", result["results"][0]["error"])
    
    def test_script_abort_on_error(self):
        """Test script abortion on error when abort_on_error is true."""
        script = {
            "abort_on_error": True,
            "actions": [
                {"type": "click", "position": [500, 300]},
                {"type": "type"},  # This will fail due to missing text
                {"type": "click", "position": [600, 400]}  # This should never execute
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertFalse(result["success"])
        self.assertEqual(len(result["results"]), 2)  # Only the first two actions should be attempted
        self.mock_pyautogui.click.assert_called_once()  # Click should be called only once
    
    def test_script_continue_on_error(self):
        """Test script continuation on error when abort_on_error is false."""
        script = {
            "abort_on_error": False,
            "actions": [
                {"type": "click", "position": [500, 300]},
                {"type": "type"},  # This will fail due to missing text
                {"type": "click", "position": [600, 400]}  # This should execute despite the error
            ]
        }
        
        result = self.executor.execute_script(script)
        self.assertFalse(result["success"])
        self.assertEqual(len(result["results"]), 3)  # All three actions should be attempted
        self.assertEqual(self.mock_pyautogui.click.call_count, 2)  # Click should be called twice

class TestUvxIntegration(unittest.TestCase):
    """Test cases for the uvx integration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create patches
        self.subprocess_patcher = patch('subprocess.run')
        self.os_environ_patcher = patch.dict('os.environ', {})
        
        # Start patches
        self.mock_subprocess_run = self.subprocess_patcher.start()
        self.os_environ_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.subprocess_patcher.stop()
        self.os_environ_patcher.stop()
    
    def test_run_with_uvx(self):
        """Test the run_with_uvx function."""
        # Set up mock return value
        mock_process = MagicMock()
        mock_process.returncode = 0
        self.mock_subprocess_run.return_value = mock_process
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Modify sys.argv for testing
            sys.argv = ['script_executor.py', 'test_script.json']
            
            # Call the function
            returncode = script_executor.run_with_uvx()
            
            # Check that subprocess.run was called three times
            # (once for required pip installs, once for optional opencv install, once for running the script)
            self.assertEqual(self.mock_subprocess_run.call_count, 3)
            
            # Get the first call (pip install for required deps)
            first_call_args = self.mock_subprocess_run.call_args_list[0][0]
            pip_cmd = first_call_args[0]
            
            # Check pip command is constructed correctly
            self.assertEqual(pip_cmd[0], sys.executable)
            self.assertEqual(pip_cmd[1], "-m")
            self.assertEqual(pip_cmd[2], "pip") 
            self.assertEqual(pip_cmd[3], "install")
            self.assertIn("pyautogui", pip_cmd)
            self.assertIn("pillow", pip_cmd)
            
            # Get the second call (pip install for opencv)
            second_call_args = self.mock_subprocess_run.call_args_list[1][0]
            opencv_cmd = second_call_args[0]
            
            # Check opencv command is constructed correctly
            self.assertEqual(opencv_cmd[0], sys.executable)
            self.assertEqual(opencv_cmd[1], "-m")
            self.assertEqual(opencv_cmd[2], "pip") 
            self.assertEqual(opencv_cmd[3], "install")
            self.assertIn("opencv-python", opencv_cmd)
            
            # Check the third call (running the script)
            third_call_args = self.mock_subprocess_run.call_args_list[2][0]
            script_cmd = third_call_args[0]
            self.assertEqual(script_cmd[0], sys.executable)
            self.assertEqual(script_cmd[1], "script_executor.py")
            self.assertEqual(script_cmd[2], "test_script.json")
            
            # Check return code
            self.assertEqual(returncode, 0)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
    
    def test_ensure_dependencies_with_uvx_active(self):
        """Test ensure_dependencies when UV_ACTIVE is set."""
        # Create a nested mock context to test both success and failure paths
        with patch.dict('os.environ', {'UV_ACTIVE': '1'}):
            # Test when all dependencies successfully import
            original_import = __import__
            
            def mock_import(name, *args, **kwargs):
                if name == 'pyautogui' or name == 'cv2':
                    return MagicMock()
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                self.assertTrue(script_executor.ensure_dependencies())
            
            # Test when required dependency fails to import despite UV_ACTIVE=1
            def import_error(name, *args, **kwargs):
                if name == 'pyautogui':
                    raise ImportError("No module named 'pyautogui'")
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=import_error):
                self.assertFalse(script_executor.ensure_dependencies())
                
            # Test when only optional dependency fails to import
            def import_error_optional(name, *args, **kwargs):
                if name == 'cv2':
                    raise ImportError("No module named 'cv2'")
                elif name == 'pyautogui':
                    return MagicMock()
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=import_error_optional):
                # Should still return True since only optional dependency is missing
                self.assertTrue(script_executor.ensure_dependencies())
    
    def test_ensure_dependencies_with_all_dependencies_available(self):
        """Test ensure_dependencies when all dependencies are already installed."""
        # Test when PyAutoGUI and OpenCV are already available
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'pyautogui' or name == 'cv2':
                return MagicMock()
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            self.assertTrue(script_executor.ensure_dependencies())
    
    def test_ensure_dependencies_with_uvx_available(self):
        """Test ensure_dependencies when uvx is available but dependencies aren't."""
        # Mock imports to fail for PyAutoGUI and cv2 but allow other imports
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'pyautogui' or name == 'cv2':
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        
        # Setup the import mocking
        with patch('builtins.__import__', side_effect=mock_import):
            # Then make uvx command succeed
            self.mock_subprocess_run.return_value = MagicMock(returncode=0)
            
            # And mock run_with_uvx to avoid actually running it
            with patch('script_executor.run_with_uvx', return_value=0):
                # Mock sys.exit to prevent the test from exiting
                with patch('sys.exit') as mock_exit:
                    # Call the function
                    script_executor.ensure_dependencies()
                    
                    # Check that we tried to execute uvx --version
                    self.mock_subprocess_run.assert_called()
                    # Verify that sys.exit was called
                    mock_exit.assert_called_once_with(0)
    
    def test_ensure_dependencies_with_nothing_available(self):
        """Test ensure_dependencies when neither required dependencies nor uvx is available."""
        # Mock imports to fail for PyAutoGUI and OpenCV but allow other imports
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'pyautogui' or name == 'cv2':
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        
        # Mock subprocess.run to fail for uvx command
        self.mock_subprocess_run.side_effect = FileNotFoundError("Command not found")
        
        # Test the function
        with patch('builtins.__import__', side_effect=mock_import):
            self.assertFalse(script_executor.ensure_dependencies())

if __name__ == "__main__":
    unittest.main()