import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import time
import subprocess # For testing launch

# Add the parent directory to sys.path to allow importing script_executor
# Assuming test_script_executor.py is in the same directory as script_executor.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import script_executor

class TestActionExecutor(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.pyautogui_patcher = patch('script_executor.pyautogui', autospec=True)
        self.mock_pyautogui = self.pyautogui_patcher.start()
        
        # Mock cv2 and numpy as they are optional dependencies
        # Ensure these mocks are created correctly as MagicMock instances
        self.cv2_patcher = patch('script_executor.cv2', MagicMock(spec=script_executor.cv2 if hasattr(script_executor, 'cv2') else object))
        self.mock_cv2 = self.cv2_patcher.start()
        
        self.numpy_patcher = patch('script_executor.np', MagicMock(spec=script_executor.np if hasattr(script_executor, 'np') else object))
        self.mock_numpy = self.numpy_patcher.start()

        self.executor = script_executor.ActionExecutor()
        
        self.mock_pyautogui.size.return_value = (1920, 1080)
        self.executor.screen_width, self.executor.screen_height = self.mock_pyautogui.size()
        self.executor.state = { # Reset state for each test
            "last_image_position": None,
            "last_click_position": None,
            "last_image_path": None,
            "active_window": None,
        }
        # Ensure cv2 and np are explicitly removed from executor instance if they were patched out globally
        # This makes tests more deterministic regarding cv2 availability
        if not hasattr(script_executor, 'cv2'):
            if hasattr(self.executor, 'cv2'):
                delattr(self.executor, 'cv2')
            if hasattr(self.executor, 'np'):
                delattr(self.executor, 'np')


    def tearDown(self):
        """Clean up after each test."""
        self.pyautogui_patcher.stop()
        self.cv2_patcher.stop()
        self.numpy_patcher.stop()

    # --- Test _handle_wait ---
    def test_handle_wait_success(self):
        action = {"type": "wait", "seconds": 0.01}
        with patch('time.sleep') as mock_sleep:
            result = self.executor._handle_wait(action)
            self.assertTrue(result["success"])
            self.assertEqual(result["seconds"], 0.01)
            mock_sleep.assert_called_once_with(0.01)

    def test_handle_wait_default_seconds(self):
        action = {"type": "wait"}
        with patch('time.sleep') as mock_sleep:
            result = self.executor._handle_wait(action)
            self.assertTrue(result["success"])
            self.assertEqual(result["seconds"], 1.0)
            mock_sleep.assert_called_once_with(1.0)

    # --- Test _handle_type ---
    def test_handle_type_success(self):
        action = {"type": "type", "text": "hello world", "interval": 0.05}
        result = self.executor._handle_type(action)
        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "hello world")
        self.mock_pyautogui.write.assert_called_once_with("hello world", interval=0.05)

    def test_handle_type_missing_text(self):
        action = {"type": "type", "interval": 0.05}
        result = self.executor._handle_type(action)
        self.assertFalse(result["success"])
        self.assertIn("No text specified", result["error"])

    # --- Test _handle_key_press ---
    def test_handle_key_press_success(self):
        action = {"type": "press", "key": "enter", "presses": 2, "interval": 0.1}
        result = self.executor._handle_key_press(action)
        self.assertTrue(result["success"])
        self.mock_pyautogui.press.assert_called_once_with("enter", presses=2, interval=0.1)

    def test_handle_key_press_missing_key(self):
        action = {"type": "press"}
        result = self.executor._handle_key_press(action)
        self.assertFalse(result["success"])
        self.assertIn("No key specified", result["error"])

    # --- Test _handle_hotkey ---
    def test_handle_hotkey_success(self):
        action = {"type": "hotkey", "keys": ["ctrl", "s"]}
        result = self.executor._handle_hotkey(action)
        self.assertTrue(result["success"])
        self.mock_pyautogui.hotkey.assert_called_once_with("ctrl", "s")

    def test_handle_hotkey_missing_keys(self):
        action = {"type": "hotkey"}
        result = self.executor._handle_hotkey(action)
        self.assertFalse(result["success"])
        self.assertIn("No keys list specified", result["error"])

    # --- Test _handle_moveto ---
    def test_handle_moveto_absolute_coords(self):
        action = {"type": "moveto", "position": [100, 200], "duration": 0.2}
        result = self.executor._handle_move_to(action)
        self.assertTrue(result["success"])
        self.mock_pyautogui.moveTo.assert_called_once_with(x=100, y=200, duration=0.2)

    @patch.object(script_executor.ActionExecutor, '_locate_image')
    def test_handle_moveto_with_image(self, mock_locate_image):
        mock_locate_image.return_value = (300, 400)
        action = {"type": "moveto", "image": "test_image.png", "confidence": 0.8, "duration": 0.1}
        result = self.executor._handle_move_to(action)
        self.assertTrue(result["success"])
        mock_locate_image.assert_called_once_with("test_image.png", 0.8)
        self.mock_pyautogui.moveTo.assert_called_once_with(x=300, y=400, duration=0.1)

    # --- Test _resolve_image_path ---
    @patch('os.path.isfile')
    def test_resolve_image_path_absolute_found(self, mock_isfile):
        mock_isfile.return_value = True
        abs_path = os.path.abspath("/abs/path/dummy.png") if os.name == 'posix' else "C:\\abs\\path\\dummy.png"
        with patch('os.path.isabs', return_value=True):
            self.assertEqual(self.executor._resolve_image_path(abs_path), abs_path)

    @patch('os.path.isfile')
    @patch('os.getcwd', return_value="/mock/cwd")
    def test_resolve_image_path_relative_found(self, mock_getcwd, mock_isfile):
        mock_isfile.side_effect = lambda p: p == os.path.abspath("/mock/cwd/relative.png")
        with patch('os.path.isabs', return_value=False):
            self.assertEqual(self.executor._resolve_image_path("relative.png"), os.path.abspath("/mock/cwd/relative.png"))
    
    @patch('os.path.isfile', return_value=False)
    @patch('os.getcwd', return_value="/mock/cwd")
    def test_resolve_image_path_not_found(self, mock_getcwd, mock_isfile):
        with patch('os.path.isabs', return_value=False):
             self.assertEqual(self.executor._resolve_image_path("notfound.png"), "")

    # --- Test _locate_image ---
    @patch.object(script_executor.ActionExecutor, '_resolve_image_path')
    def test_locate_image_pyautogui_success(self, mock_resolve):
        mock_resolve.return_value = "/resolved/path.png"
        self.mock_pyautogui.locateCenterOnScreen.return_value = (10, 20)
        self.assertEqual(self.executor._locate_image("img.png"), (10, 20))
        self.mock_pyautogui.locateCenterOnScreen.assert_called_with("/resolved/path.png", confidence=0.9, grayscale=False)

    @patch.object(script_executor.ActionExecutor, '_resolve_image_path')
    def test_locate_image_pyautogui_fail_no_cv2(self, mock_resolve):
        mock_resolve.return_value = "/resolved/path.png"
        self.mock_pyautogui.locateCenterOnScreen.return_value = None
        if hasattr(self.executor, 'cv2'): # Ensure cv2 is not available for this test
            delattr(self.executor, 'cv2')
        
        with self.assertRaisesRegex(ValueError, "Could not locate image: /resolved/path.png"):
            self.executor._locate_image("img.png")

    @patch.object(script_executor.ActionExecutor, '_resolve_image_path')
    @patch.object(script_executor.ActionExecutor, '_capture_debug_screenshot', return_value="mock_screenshot.png")
    def test_locate_image_pyautogui_fail_with_cv2_fallback_success(self, mock_screenshot, mock_resolve):
        mock_resolve.return_value = "/resolved/path.png"
        self.mock_pyautogui.locateCenterOnScreen.return_value = None # PyAutoGUI fails
        
        # Ensure cv2 is "available"
        self.executor.cv2 = MagicMock()
        self.executor.np = MagicMock()
        
        mock_screenshot_obj = MagicMock()
        self.mock_pyautogui.screenshot.return_value = mock_screenshot_obj
        self.executor.np.array.return_value = "np_array_screenshot"
        self.executor.cv2.cvtColor.return_value = "cv_converted_screenshot" # Mock cvtColor return
        
        mock_template_img = MagicMock()
        mock_template_img.shape = (10, 10) # h, w
        self.executor.cv2.imread.return_value = mock_template_img
        
        # Mock matchTemplate and minMaxLoc to simulate finding an image
        self.executor.cv2.matchTemplate.return_value = "match_result"
        # min_val, max_val, min_loc, max_loc (top-left)
        self.executor.cv2.minMaxLoc.return_value = (0.0, 0.95, (0,0), (50,60)) 
        
        expected_center_x = 50 + 10 // 2
        expected_center_y = 60 + 10 // 2
        
        pos = self.executor._locate_image("img.png", confidence=0.9)
        self.assertEqual(pos, (expected_center_x, expected_center_y))
        self.executor.cv2.imread.assert_called_with("/resolved/path.png")
        self.executor.cv2.matchTemplate.assert_called()
        self.executor.cv2.minMaxLoc.assert_called_with("match_result")


    # --- Test _handle_click ---
    @patch.object(script_executor.ActionExecutor, '_get_position', return_value=(10,20))
    def test_handle_click_position(self, mock_get_pos):
        action = {"type": "click", "position": [10, 20]}
        result = self.executor._handle_click(action)
        self.assertTrue(result["success"])
        self.assertEqual(result["position"], (10,20))
        self.mock_pyautogui.moveTo.assert_called_with(10, 20, duration=0.2)
        self.mock_pyautogui.click.assert_called_with(x=10, y=20, button="left")

    @patch.object(script_executor.ActionExecutor, '_locate_image', return_value=(30,40))
    def test_handle_click_image_direct(self, mock_locate):
        action = {"type": "click", "image": "img.png"}
        result = self.executor._handle_click(action)
        self.assertTrue(result["success"])
        self.assertEqual(result["position"], (30,40))
        mock_locate.assert_called_with("img.png", 0.9)
        self.mock_pyautogui.click.assert_called_with(x=30, y=40, button="left")

    def test_handle_click_last_image_pos(self):
        self.executor.state["last_image_position"] = (50, 60)
        action = {"type": "click"}
        result = self.executor._handle_click(action)
        self.assertTrue(result["success"])
        self.assertEqual(result["position"], (50,60))
        self.mock_pyautogui.click.assert_called_with(x=50, y=60, button="left")
        
    def test_handle_click_double(self):
        action = {"type": "click", "position": [10,20], "count": 2}
        with patch.object(self.executor, '_get_position', return_value=(10,20)) as mock_get_pos:
            result = self.executor._handle_click(action)
            self.assertTrue(result["success"])
            self.mock_pyautogui.doubleClick.assert_called_once_with(x=10,y=20)
            self.mock_pyautogui.click.assert_not_called() # Ensure regular click isn't also called

    # --- Test _handle_launch ---
    @patch('subprocess.Popen')
    def test_handle_launch_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.poll.return_value = None # Simulate process still running or exited successfully
        mock_popen.return_value = mock_process
        
        action = {"type": "launch", "app": "notepad", "wait": 0.01}
        with patch('time.sleep') as mock_sleep: # Patch sleep to speed up test
            result = self.executor._handle_launch(action)
            self.assertTrue(result["success"])
            self.assertEqual(result["app"], "notepad")
            mock_popen.assert_called_once_with(["notepad"])
            mock_sleep.assert_called_once_with(0.01)

    @patch('subprocess.Popen')
    def test_handle_launch_failure_not_found(self, mock_popen):
        mock_popen.side_effect = FileNotFoundError("App not found")
        action = {"type": "launch", "app": "nonexistent"}
        result = self.executor._handle_launch(action)
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    @patch('subprocess.Popen')
    def test_handle_launch_failure_exit_code(self, mock_popen):
        mock_process = MagicMock()
        mock_process.poll.return_value = 1 # Simulate process exited with error
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        # Skip this specific check for macOS 'open' command behavior
        if sys.platform == "darwin": 
            self.skipTest("Skipping exit code check for 'open -a' on macOS in this specific test")

        action = {"type": "launch", "app": "errorapp"}
        with patch('time.sleep'): # Patch sleep
            result = self.executor._handle_launch(action)
            self.assertFalse(result["success"])
            self.assertIn("exit code: 1", result["error"])
            
    # --- Test execute_script (overall flow) ---
    @patch.object(script_executor.ActionExecutor, '_execute_action')
    def test_execute_script_success(self, mock_execute_action):
        mock_execute_action.return_value = {"success": True}
        script_data = {
            "actions": [
                {"type": "wait", "seconds": 0.01},
                {"type": "type", "text": "hello"}
            ]
        }
        result = self.executor.execute_script(script_data)
        self.assertTrue(result["success"])
        self.assertEqual(mock_execute_action.call_count, 2)
        self.assertEqual(len(result["results"]), 2)

    @patch.object(script_executor.ActionExecutor, '_execute_action')
    def test_execute_script_fail_and_abort(self, mock_execute_action):
        mock_execute_action.side_effect = [
            {"success": True, "action_type": "type"},
            {"success": False, "error": "Test error", "action_type": "click"} 
        ]
        script_data = {
            "actions": [
                {"type": "type", "text": "hello"},
                {"type": "click", "image": "img.png"}, # This will fail
                {"type": "wait", "seconds": 1}         # This should not run
            ],
            "abort_on_error": True 
        }
        result = self.executor.execute_script(script_data)
        self.assertFalse(result["success"])
        self.assertEqual(mock_execute_action.call_count, 2) # Aborted after 2nd action
        self.assertEqual(len(result["results"]), 2)
        self.assertIn("failed_actions", result)
        self.assertEqual(len(result["failed_actions"]), 1)
        self.assertEqual(result["failed_actions"][0]["error"], "Test error")

    @patch.object(script_executor.ActionExecutor, '_execute_action')
    def test_execute_script_fail_no_abort(self, mock_execute_action):
        mock_execute_action.side_effect = [
            {"success": True, "action_type": "type"},
            {"success": False, "error": "Test error", "action_type": "click"},
            {"success": True, "action_type": "wait"} 
        ]
        script_data = {
            "actions": [
                {"type": "type", "text": "hello"},
                {"type": "click", "image": "img.png"}, # This will fail
                {"type": "wait", "seconds": 1}         # This should still run
            ],
            "abort_on_error": False
        }
        result = self.executor.execute_script(script_data)
        self.assertFalse(result["success"]) # Overall success is false
        self.assertEqual(mock_execute_action.call_count, 3) # All actions attempted
        self.assertEqual(len(result["results"]), 3)
        self.assertIn("failed_actions", result)
        self.assertEqual(len(result["failed_actions"]), 1)

    def test_execute_script_invalid_json_string(self):
        result = self.executor.execute_script("this is not json")
        self.assertFalse(result["success"])
        self.assertIn("Invalid JSON", result["error"])

    def test_execute_script_missing_actions_key(self):
        result = self.executor.execute_script({"no_actions_here": []})
        self.assertFalse(result["success"])
        self.assertIn("Script must contain an 'actions' list", result["error"])


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
