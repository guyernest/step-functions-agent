use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::thread;
use std::time::Duration;
use enigo::{Enigo, Key, Keyboard, Button, Mouse, Settings, Direction, Coordinate};
use image::{DynamicImage, GrayImage};
use imageproc::template_matching::{match_template, MatchTemplateMethod};
use xcap::Monitor;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

// Static flag for stopping execution
lazy_static::lazy_static! {
    static ref STOP_EXECUTION: Arc<AtomicBool> = Arc::new(AtomicBool::new(false));
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScriptAction {
    #[serde(rename = "type")]
    pub action_type: String,
    pub description: Option<String>,
    
    // Common fields
    pub x: Option<f64>,
    pub y: Option<f64>,
    pub text: Option<String>,
    pub key: Option<String>,
    pub keys: Option<Vec<String>>,
    pub seconds: Option<f64>,
    pub wait: Option<f64>,
    pub app: Option<String>,
    pub interval: Option<f64>,
    pub button: Option<String>,
    pub clicks: Option<u32>,
    pub duration: Option<f64>,
    
    // Image recognition
    pub image: Option<String>,
    pub confidence: Option<f64>,
    pub region: Option<Region>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Region {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScriptResult {
    pub success: bool,
    pub results: Vec<ActionResult>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionResult {
    pub action: String,
    pub status: String,
    pub details: String,
    pub duration: Option<u64>,
}

pub struct RustScriptExecutor {
    results: Vec<ActionResult>,
    abort_on_error: bool,
    enigo: Option<Enigo>,
}

impl RustScriptExecutor {
    pub fn new() -> Self {
        // Try to create Enigo instance with proper settings for macOS
        let enigo = match Self::create_enigo() {
            Ok(e) => Some(e),
            Err(err) => {
                eprintln!("Warning: Failed to initialize Enigo: {}. Will try creating per-action.", err);
                None
            }
        };
        
        Self {
            results: Vec::new(),
            abort_on_error: true,
            enigo,
        }
    }
    
    fn create_enigo() -> Result<Enigo, String> {
        eprintln!("🔍 [DEBUG] Creating new Enigo instance");
        
        // Use custom settings for macOS to avoid crashes
        let mut settings = Settings::default();
        
        // Configure settings for better compatibility
        settings.release_keys_when_dropped = true;
        settings.independent_of_keyboard_state = true;
        
        eprintln!("🔍 [DEBUG] About to call Enigo::new()");
        
        match Enigo::new(&settings) {
            Ok(e) => {
                eprintln!("🔍 [DEBUG] Enigo::new() succeeded");
                // Don't test the enigo instance here to avoid early crashes
                // Permissions will be checked during actual use
                Ok(e)
            },
            Err(e) => {
                eprintln!("🔍 [DEBUG] Enigo::new() failed: {}", e);
                let error_msg = format!("Failed to create Enigo: {}", e);
                
                // Check if this is a macOS accessibility permission issue
                #[cfg(target_os = "macos")]
                {
                    if error_msg.contains("accessibility") || error_msg.contains("permission") {
                        return Err(format!(
                            "{}\n\nOn macOS, you need to grant accessibility permissions:\n\
                            1. Open System Settings > Privacy & Security > Accessibility\n\
                            2. Enable the toggle for this application\n\
                            3. You may need to restart the application after granting permissions",
                            error_msg
                        ));
                    }
                }
                
                Err(error_msg)
            }
        }
    }
    
    fn get_or_create_enigo(&mut self) -> Option<&mut Enigo> {
        eprintln!("🔍 [DEBUG] Entering get_or_create_enigo");
        
        if self.enigo.is_none() {
            eprintln!("🔍 [DEBUG] Enigo instance is None, creating new one");
            match Self::create_enigo() {
                Ok(e) => {
                    eprintln!("🔍 [DEBUG] Successfully created Enigo instance");
                    self.enigo = Some(e);
                },
                Err(e) => {
                    eprintln!("🔍 [DEBUG] Failed to create Enigo: {}", e);
                    return None;
                }
            }
        } else {
            eprintln!("🔍 [DEBUG] Using existing Enigo instance");
        }
        
        eprintln!("🔍 [DEBUG] Returning Enigo instance");
        self.enigo.as_mut()
    }
    
    pub fn stop_execution() {
        STOP_EXECUTION.store(true, Ordering::Relaxed);
    }
    
    pub fn reset_stop_flag() {
        STOP_EXECUTION.store(false, Ordering::Relaxed);
    }
    
    fn should_stop(&self) -> bool {
        STOP_EXECUTION.load(Ordering::Relaxed)
    }
    
    pub fn execute_script(&mut self, script_json: &str) -> ScriptResult {
        Self::reset_stop_flag();
        self.results.clear();
        
        // Parse the script
        let script: Value = match serde_json::from_str(script_json) {
            Ok(v) => v,
            Err(e) => {
                return ScriptResult {
                    success: false,
                    results: vec![],
                    error: Some(format!("Failed to parse script: {}", e)),
                };
            }
        };
        
        // Get abort_on_error setting
        if let Some(abort) = script["abort_on_error"].as_bool() {
            self.abort_on_error = abort;
        }
        
        // Get actions array
        let actions = match script["actions"].as_array() {
            Some(a) => a,
            None => {
                return ScriptResult {
                    success: false,
                    results: vec![],
                    error: Some("Script must contain an 'actions' array".to_string()),
                };
            }
        };
        
        // Execute each action
        for (index, action_value) in actions.iter().enumerate() {
            eprintln!("🔍 [DEBUG] Processing action {} of {}", index + 1, actions.len());
            
            if self.should_stop() {
                self.add_result(
                    format!("Script execution stopped at action {}", index + 1),
                    "stopped",
                    "User requested stop".to_string(),
                    None,
                );
                break;
            }
            
            let action: ScriptAction = match serde_json::from_value::<ScriptAction>(action_value.clone()) {
                Ok(a) => {
                    eprintln!("🔍 [DEBUG] Successfully parsed action: {:?}", a.action_type);
                    a
                },
                Err(e) => {
                    eprintln!("🔍 [DEBUG] Failed to parse action: {}", e);
                    self.add_result(
                        format!("Action {}", index + 1),
                        "failed",
                        format!("Failed to parse action: {}", e),
                        None,
                    );
                    if self.abort_on_error {
                        break;
                    }
                    continue;
                }
            };
            
            eprintln!("🔍 [DEBUG] About to execute action: {}", action.action_type);
            let start = std::time::Instant::now();
            let success = self.execute_action(&action);
            let _duration = start.elapsed().as_millis() as u64;
            eprintln!("🔍 [DEBUG] Action {} completed with success: {}", action.action_type, success);
            
            if !success && self.abort_on_error {
                eprintln!("🔍 [DEBUG] Aborting on error");
                break;
            }
            
            // Add wait time if specified
            if let Some(wait_secs) = action.wait {
                eprintln!("🔍 [DEBUG] Waiting {} seconds after action", wait_secs);
                thread::sleep(Duration::from_secs_f64(wait_secs));
            }
            
            eprintln!("🔍 [DEBUG] Moving to next action");
        }
        
        eprintln!("🔍 [DEBUG] Script execution completed, preparing results");
        
        let success = self.results.iter().all(|r| r.status == "success");
        eprintln!("🔍 [DEBUG] Overall success: {}", success);
        eprintln!("🔍 [DEBUG] Number of results: {}", self.results.len());
        
        let result = ScriptResult {
            success,
            results: self.results.clone(),
            error: None,
        };
        
        eprintln!("🔍 [DEBUG] Returning ScriptResult");
        result
    }
    
    fn execute_action(&mut self, action: &ScriptAction) -> bool {
        let action_type = action.action_type.as_str();
        let description = action.description.clone()
            .unwrap_or_else(|| action_type.to_string());
        
        println!("Executing action: {} - {}", action_type, description);
        
        let result = match action_type {
            "click" => self.handle_click(action),
            "doubleclick" => self.handle_double_click(action),
            "rightclick" => self.handle_right_click(action),
            "moveto" => self.handle_move_to(action),
            "dragto" => self.handle_drag_to(action),
            "type" | "typewrite" => self.handle_type(action),
            "press" => self.handle_press(action),
            "hotkey" => self.handle_hotkey(action),
            "keydown" => self.handle_key_down(action),
            "keyup" => self.handle_key_up(action),
            "wait" | "sleep" => self.handle_wait(action),
            "screenshot" => self.handle_screenshot(action),
            "locateimage" => self.handle_locate_image(action),
            "launch" => self.handle_launch(action),
            _ => {
                self.add_result(
                    description.clone(),
                    "failed",
                    format!("Unknown action type: {}", action_type),
                    Some(0),
                );
                false
            }
        };
        
        result
    }
    
    fn handle_click(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Click".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        // If x,y provided, move there first
        if let (Some(x), Some(y)) = (action.x, action.y) {
            let _ = enigo.move_mouse(x as i32, y as i32, Coordinate::Abs);
        }
        
        // Perform click
        let clicks = action.clicks.unwrap_or(1);
        for _ in 0..clicks {
            let _ = enigo.button(Button::Left, Direction::Click);
            if clicks > 1 {
                thread::sleep(Duration::from_millis(50));
            }
        }
        
        self.add_result(description, "success", "Click performed".to_string(), Some(50));
        true
    }
    
    fn handle_double_click(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Double Click".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        if let (Some(x), Some(y)) = (action.x, action.y) {
            let _ = enigo.move_mouse(x as i32, y as i32, Coordinate::Abs);
        }
        
        let _ = enigo.button(Button::Left, Direction::Click);
        thread::sleep(Duration::from_millis(50));
        let _ = enigo.button(Button::Left, Direction::Click);
        
        self.add_result(description, "success", "Double click performed".to_string(), Some(100));
        true
    }
    
    fn handle_right_click(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Right Click".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        if let (Some(x), Some(y)) = (action.x, action.y) {
            let _ = enigo.move_mouse(x as i32, y as i32, Coordinate::Abs);
        }
        
        let _ = enigo.button(Button::Right, Direction::Click);
        
        self.add_result(description, "success", "Right click performed".to_string(), Some(50));
        true
    }
    
    fn handle_move_to(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Move Mouse".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        match (action.x, action.y) {
            (Some(x), Some(y)) => {
                let _ = enigo.move_mouse(x as i32, y as i32, Coordinate::Abs);
                self.add_result(description, "success", 
                    format!("Moved to ({}, {})", x, y), Some(10));
                true
            },
            _ => {
                self.add_result(description, "failed", 
                    "Missing x or y coordinates".to_string(), Some(0));
                false
            }
        }
    }
    
    fn handle_drag_to(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Drag Mouse".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        match (action.x, action.y) {
            (Some(x), Some(y)) => {
                // Press mouse button
                let _ = enigo.button(Button::Left, Direction::Press);
                
                // Move to target with some delay
                thread::sleep(Duration::from_millis(100));
                let _ = enigo.move_mouse(x as i32, y as i32, Coordinate::Abs);
                thread::sleep(Duration::from_millis(100));
                
                // Release mouse button
                let _ = enigo.button(Button::Left, Direction::Release);
                
                self.add_result(description, "success", 
                    format!("Dragged to ({}, {})", x, y), Some(200));
                true
            },
            _ => {
                self.add_result(description, "failed", 
                    "Missing x or y coordinates".to_string(), Some(0));
                false
            }
        }
    }
    
    fn handle_type(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Type Text".to_string());
        
        eprintln!("🔍 [DEBUG] Starting handle_type function");
        eprintln!("🔍 [DEBUG] Action description: {}", description);
        
        if let Some(text) = &action.text {
            eprintln!("🔍 [DEBUG] Text to type: '{}'", text);
            eprintln!("🔍 [DEBUG] Text length: {}", text.len());
            
            // Add a small delay before typing to ensure focus
            thread::sleep(Duration::from_millis(100));
            eprintln!("🔍 [DEBUG] Added focus delay");
            
            let interval = action.interval.unwrap_or(0.0);
            eprintln!("🔍 [DEBUG] Interval: {}", interval);
            
            eprintln!("🔍 [DEBUG] About to start typing process");
            
            // Use character-by-character typing for better reliability on macOS
            let success = if interval > 0.0 {
                eprintln!("🔍 [DEBUG] Using type_text_with_interval");
                self.type_text_with_interval(text, interval)
            } else {
                eprintln!("🔍 [DEBUG] Using type_text_safe");
                self.type_text_safe(text)
            };
            
            eprintln!("🔍 [DEBUG] Typing completed, success: {}", success);
            
            if success {
                let duration = if interval > 0.0 {
                    (text.len() as f64 * interval * 1000.0) as u64
                } else {
                    text.len() as u64 * 20 // Estimate 20ms per character
                };
                self.add_result(description, "success", 
                    format!("Typed: {}", text), Some(duration));
                true
            } else {
                self.add_result(description, "failed", 
                    "Failed to type text".to_string(), Some(0));
                false
            }
        } else {
            eprintln!("🔍 [DEBUG] No text provided in action");
            self.add_result(description, "failed", 
                "No text provided".to_string(), Some(0));
            false
        }
    }
    
    // Safe text typing with error handling and fallback
    fn type_text_safe(&mut self, text: &str) -> bool {
        eprintln!("🔍 [DEBUG] Entering type_text_safe");
        eprintln!("🔍 [DEBUG] Text to type character by character: '{}'", text);
        
        // Get enigo instance for typing
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                eprintln!("🔍 [DEBUG] Failed to get enigo for typing");
                return false;
            }
        };
        
        // First, try to ensure we have focus by clicking in the center of the screen
        // This is a workaround for macOS focus issues
        #[cfg(target_os = "macos")]
        {
            eprintln!("🔍 [DEBUG] Clicking to ensure focus before typing");
            // Click in the middle of the text area (rough estimate)
            let _ = enigo.button(Button::Left, Direction::Click);
            thread::sleep(Duration::from_millis(50));
        }
        
        // Try character-by-character typing for better reliability
        for (i, ch) in text.chars().enumerate() {
            eprintln!("🔍 [DEBUG] About to type character {} of {}: '{}'", i + 1, text.chars().count(), ch);
            
            if !self.type_single_character(ch) {
                eprintln!("🔍 [DEBUG] Failed to type character: '{}'", ch);
                return false;
            }
            
            eprintln!("🔍 [DEBUG] Successfully typed character: '{}'", ch);
            // Small delay between characters to avoid overwhelming the system
            thread::sleep(Duration::from_millis(10)); // Slightly increased delay
        }
        
        eprintln!("🔍 [DEBUG] Completed type_text_safe successfully");
        true
    }
    
    fn type_text_with_interval(&mut self, text: &str, interval: f64) -> bool {
        for ch in text.chars() {
            if !self.type_single_character(ch) {
                return false;
            }
            thread::sleep(Duration::from_secs_f64(interval));
        }
        true
    }
    
    fn type_single_character(&mut self, ch: char) -> bool {
        eprintln!("🔍 [DEBUG] Entering type_single_character for: '{}'", ch);
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => {
                eprintln!("🔍 [DEBUG] Got enigo instance successfully");
                e
            },
            None => {
                eprintln!("🔍 [DEBUG] Failed to get enigo instance");
                return false;
            },
        };
        
        eprintln!("🔍 [DEBUG] About to match character type for: '{}'", ch);
        
        // Handle special characters that might cause crashes
        let result = match ch {
            '\n' => {
                eprintln!("🔍 [DEBUG] Handling newline character");
                // Use Key::Return for newlines
                match enigo.key(Key::Return, Direction::Click) {
                    Ok(_) => {
                        eprintln!("🔍 [DEBUG] Successfully sent Return key");
                        true
                    },
                    Err(e) => {
                        eprintln!("🔍 [DEBUG] Failed to send Return key: {}", e);
                        false
                    }
                }
            },
            '\t' => {
                eprintln!("🔍 [DEBUG] Handling tab character");
                // Use Key::Tab for tabs
                match enigo.key(Key::Tab, Direction::Click) {
                    Ok(_) => {
                        eprintln!("🔍 [DEBUG] Successfully sent Tab key");
                        true
                    },
                    Err(e) => {
                        eprintln!("🔍 [DEBUG] Failed to send Tab key: {}", e);
                        false
                    }
                }
            },
            ch if ch.is_control() => {
                eprintln!("🔍 [DEBUG] Skipping control character: '{}'", ch);
                // Skip other control characters to avoid crashes
                true
            },
            _ => {
                eprintln!("🔍 [DEBUG] Handling regular character: '{}'", ch);
                // Use text method for regular characters with error handling
                eprintln!("🔍 [DEBUG] About to call enigo.text() with: '{}'", ch);
                
                match enigo.text(&ch.to_string()) {
                    Ok(_) => {
                        eprintln!("🔍 [DEBUG] Successfully typed character with text(): '{}'", ch);
                        true
                    },
                    Err(e) => {
                        eprintln!("🔍 [DEBUG] Failed to type character '{}' with text(): {}", ch, e);
                        eprintln!("🔍 [DEBUG] Trying fallback with Unicode key press");
                        
                        // Try fallback using Unicode key press
                        match enigo.key(Key::Unicode(ch), Direction::Click) {
                            Ok(_) => {
                                eprintln!("🔍 [DEBUG] Successfully typed character with Unicode key: '{}'", ch);
                                true
                            },
                            Err(e2) => {
                                eprintln!("🔍 [DEBUG] Failed fallback Unicode key for '{}': {}", ch, e2);
                                false
                            }
                        }
                    }
                }
            }
        };
        
        eprintln!("🔍 [DEBUG] type_single_character result for '{}': {}", ch, result);
        result
    }
    
    fn handle_press(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Press Key".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        if let Some(key_str) = &action.key {
            if let Some(key) = Self::parse_key(key_str) {
                let _ = enigo.key(key, Direction::Click);
                self.add_result(description, "success", 
                    format!("Pressed: {}", key_str), Some(50));
                true
            } else {
                self.add_result(description, "failed", 
                    format!("Unknown key: {}", key_str), Some(0));
                false
            }
        } else {
            self.add_result(description, "failed", 
                "No key provided".to_string(), Some(0));
            false
        }
    }
    
    fn handle_hotkey(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Hotkey".to_string());
        
        eprintln!("🔍 [DEBUG] Starting handle_hotkey");
        
        if let Some(keys) = &action.keys {
            eprintln!("🔍 [DEBUG] Keys to press: {:?}", keys);
            
            // Windows-specific handling for better reliability
            #[cfg(target_os = "windows")]
            {
                eprintln!("🔍 [DEBUG] Using Windows-specific hotkey handling");
                
                let enigo = match self.get_or_create_enigo() {
                    Some(e) => e,
                    None => {
                        self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                        return false;
                    }
                };
                
                // Separate modifiers from main keys
                let mut modifiers = Vec::new();
                let mut main_keys = Vec::new();
                
                for key_str in keys {
                    match key_str.to_lowercase().as_str() {
                        "ctrl" | "control" | "alt" | "shift" | "win" | "windows" | "meta" => {
                            if let Some(key) = Self::parse_key(key_str) {
                                modifiers.push(key);
                            }
                        },
                        _ => {
                            if let Some(key) = Self::parse_key(key_str) {
                                main_keys.push(key);
                            }
                        }
                    }
                }
                
                // Press modifiers first
                for modifier in &modifiers {
                    eprintln!("🔍 [DEBUG] Pressing modifier: {:?}", modifier);
                    let _ = enigo.key(*modifier, Direction::Press);
                    thread::sleep(Duration::from_millis(20));
                }
                
                // Press and release main keys (using Click for atomic press+release)
                for main_key in &main_keys {
                    eprintln!("🔍 [DEBUG] Pressing main key: {:?}", main_key);
                    let _ = enigo.key(*main_key, Direction::Click);
                    thread::sleep(Duration::from_millis(20));
                }
                
                // Release modifiers in reverse order
                for modifier in modifiers.iter().rev() {
                    eprintln!("🔍 [DEBUG] Releasing modifier: {:?}", modifier);
                    let _ = enigo.key(*modifier, Direction::Release);
                    thread::sleep(Duration::from_millis(20));
                }
                
                eprintln!("🔍 [DEBUG] Windows hotkey completed");
                self.add_result(description, "success", 
                    format!("Pressed: {}", keys.join("+")), Some(100));
                return true;
            }
            
            // macOS-specific handling to avoid crashes
            #[cfg(target_os = "macos")]
            if keys.len() == 2 {
                let is_cmd_shortcut = keys[0] == "cmd" || keys[0] == "command" || keys[0] == "meta";
                let is_single_char = keys[1].len() == 1;
                
                if is_cmd_shortcut && is_single_char {
                    eprintln!("🔍 [DEBUG] Using simplified approach for Cmd+{} on macOS", keys[1]);
                    
                    // Try a simpler approach: use Click direction instead of Press/Release
                    let enigo = match self.get_or_create_enigo() {
                        Some(e) => e,
                        None => {
                            self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                            return false;
                        }
                    };
                    
                    // Press modifier
                    let _ = enigo.key(Key::Meta, Direction::Press);
                    thread::sleep(Duration::from_millis(50));
                    
                    // Send the character as text while modifier is held
                    let char_to_send = keys[1].chars().next().unwrap();
                    eprintln!("🔍 [DEBUG] Sending character '{}' as text with Cmd held", char_to_send);
                    
                    // Use the raw method to send the key event
                    let _ = enigo.raw(char_to_send as u16, Direction::Click);
                    thread::sleep(Duration::from_millis(50));
                    
                    // Release modifier
                    let _ = enigo.key(Key::Meta, Direction::Release);
                    
                    eprintln!("🔍 [DEBUG] Simplified Cmd+{} completed", keys[1]);
                    self.add_result(description, "success", 
                        format!("Pressed: {} (simplified)", keys.join("+")), Some(150));
                    return true;
                }
            }
        }
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => {
                eprintln!("🔍 [DEBUG] Got enigo for hotkey");
                e
            },
            None => {
                eprintln!("🔍 [DEBUG] Failed to get enigo for hotkey");
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        if let Some(keys) = &action.keys {            
            // Press all keys down
            let mut parsed_keys = Vec::new();
            for (i, key_str) in keys.iter().enumerate() {
                eprintln!("🔍 [DEBUG] Parsing key {} of {}: {}", i + 1, keys.len(), key_str);
                
                if let Some(key) = Self::parse_key(key_str) {
                    eprintln!("🔍 [DEBUG] Successfully parsed key: {}", key_str);
                    
                    eprintln!("🔍 [DEBUG] About to press key down: {} (key type: {:?})", key_str, key);
                    
                    // Add extra delay before pressing non-modifier keys while modifiers are held
                    if i > 0 && !matches!(key, Key::Meta | Key::Control | Key::Alt | Key::Shift) {
                        eprintln!("🔍 [DEBUG] Adding extra delay before non-modifier key");
                        thread::sleep(Duration::from_millis(100)); // Increased delay even more
                        
                        // CRITICAL WORKAROUND: On macOS, pressing Unicode keys while modifiers are held
                        // can cause crashes. Instead, we'll use the text() method for single characters
                        // when modifiers are already pressed.
                        if let Key::Unicode(ch) = key {
                            eprintln!("🔍 [DEBUG] Using text() method for character '{}' with modifier", ch);
                            
                            // Try using the text method instead of key press
                            match enigo.text(&ch.to_string()) {
                                Ok(_) => {
                                    eprintln!("🔍 [DEBUG] Successfully sent character '{}' via text()", ch);
                                    // Don't add to parsed_keys since we didn't press it, just sent the text
                                    continue; // Skip the normal key press
                                },
                                Err(e) => {
                                    eprintln!("🔍 [DEBUG] text() failed for '{}': {}, trying key press anyway", ch, e);
                                    // Fall through to try the regular key press
                                }
                            }
                        }
                    }
                    
                    // Only add to parsed_keys if we're actually pressing the key
                    parsed_keys.push(key);
                    
                    match enigo.key(key, Direction::Press) {
                        Ok(_) => eprintln!("🔍 [DEBUG] Key pressed down successfully: {}", key_str),
                        Err(e) => {
                            eprintln!("🔍 [DEBUG] Failed to press key down {}: {}", key_str, e);
                            // Try to release any previously pressed keys before returning
                            for prev_key in parsed_keys.iter().rev() {
                                let _ = enigo.key(*prev_key, Direction::Release);
                            }
                            parsed_keys.pop(); // Remove the key we just added since it failed
                            return false;
                        },
                    }
                    thread::sleep(Duration::from_millis(30)); // Increased delay
                } else {
                    eprintln!("🔍 [DEBUG] Failed to parse key: {}", key_str);
                    self.add_result(description, "failed", 
                        format!("Unknown key: {}", key_str), Some(0));
                    return false;
                }
            }
            
            eprintln!("🔍 [DEBUG] All keys pressed, now releasing in reverse order");
            
            // Add a delay before releasing to ensure the hotkey registers
            thread::sleep(Duration::from_millis(50));
            
            // Release all keys in reverse order
            for (i, key) in parsed_keys.iter().rev().enumerate() {
                eprintln!("🔍 [DEBUG] Releasing key {} of {}", i + 1, parsed_keys.len());
                match enigo.key(*key, Direction::Release) {
                    Ok(_) => eprintln!("🔍 [DEBUG] Key released successfully"),
                    Err(e) => eprintln!("🔍 [DEBUG] Failed to release key: {}", e),
                }
                thread::sleep(Duration::from_millis(20));
            }
            
            eprintln!("🔍 [DEBUG] All keys released, hotkey complete");
            
            self.add_result(description, "success", 
                format!("Pressed: {}", keys.join("+")), Some(200));
            eprintln!("🔍 [DEBUG] Hotkey action completed successfully");
            true
        } else {
            eprintln!("🔍 [DEBUG] No keys provided for hotkey");
            self.add_result(description, "failed", 
                "No keys provided".to_string(), Some(0));
            false
        }
    }
    
    fn handle_key_down(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Key Down".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        if let Some(key_str) = &action.key {
            if let Some(key) = Self::parse_key(key_str) {
                let _ = enigo.key(key, Direction::Press);
                self.add_result(description, "success", 
                    format!("Key down: {}", key_str), Some(10));
                true
            } else {
                self.add_result(description, "failed", 
                    format!("Unknown key: {}", key_str), Some(0));
                false
            }
        } else {
            self.add_result(description, "failed", 
                "No key provided".to_string(), Some(0));
            false
        }
    }
    
    fn handle_key_up(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Key Up".to_string());
        
        let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
        
        if let Some(key_str) = &action.key {
            if let Some(key) = Self::parse_key(key_str) {
                let _ = enigo.key(key, Direction::Release);
                self.add_result(description, "success", 
                    format!("Key up: {}", key_str), Some(10));
                true
            } else {
                self.add_result(description, "failed", 
                    format!("Unknown key: {}", key_str), Some(0));
                false
            }
        } else {
            self.add_result(description, "failed", 
                "No key provided".to_string(), Some(0));
            false
        }
    }
    
    fn handle_wait(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Wait".to_string());
        
        let seconds = action.seconds.unwrap_or(1.0);
        thread::sleep(Duration::from_secs_f64(seconds));
        
        self.add_result(description, "success", 
            format!("Waited {} seconds", seconds), 
            Some((seconds * 1000.0) as u64));
        true
    }
    
    fn handle_screenshot(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Screenshot".to_string());
        
        match self.capture_screen() {
            Ok(_) => {
                self.add_result(description, "success", 
                    "Screenshot captured".to_string(), Some(100));
                true
            },
            Err(e) => {
                self.add_result(description, "failed", 
                    format!("Failed to capture screenshot: {}", e), Some(0));
                false
            }
        }
    }
    
    fn handle_locate_image(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Locate Image".to_string());
        
        if let Some(image_path) = &action.image {
            let confidence = action.confidence.unwrap_or(0.9);
            
            // Load target image
            let target = match image::open(image_path) {
                Ok(img) => img.to_luma8(),
                Err(e) => {
                    self.add_result(description, "failed", 
                        format!("Failed to load image: {}", e), Some(0));
                    return false;
                }
            };
            
            // Take screenshot
            let screenshot = match self.capture_screen() {
                Ok(img) => img.to_luma8(),
                Err(e) => {
                    self.add_result(description, "failed", 
                        format!("Failed to capture screen: {}", e), Some(0));
                    return false;
                }
            };
            
            // Find image location using template matching
            if let Some((x, y)) = self.find_image_on_screen(&screenshot, &target, confidence) {
                // Move to center of found image
                let center_x = x + (target.width() / 2) as i32;
                let center_y = y + (target.height() / 2) as i32;
                
                let enigo = match self.get_or_create_enigo() {
            Some(e) => e,
            None => {
                self.add_result(description, "failed", "Failed to initialize automation".to_string(), Some(0));
                return false;
            }
        };
                let _ = enigo.move_mouse(center_x, center_y, Coordinate::Abs);
                self.add_result(description, "success", 
                    format!("Found image at ({}, {})", center_x, center_y), Some(200));
                true
            } else {
                self.add_result(description, "failed", 
                    "Image not found on screen".to_string(), Some(200));
                false
            }
        } else {
            self.add_result(description, "failed", 
                "No image path provided".to_string(), Some(0));
            false
        }
    }
    
    fn handle_launch(&mut self, action: &ScriptAction) -> bool {
        let description = action.description.clone()
            .unwrap_or_else(|| "Launch Application".to_string());
        
        if let Some(app) = &action.app {
            #[cfg(target_os = "macos")]
            {
                // Use open -a to launch the app and bring it to front
                let result = std::process::Command::new("open")
                    .arg("-a")
                    .arg(app)
                    .arg("--fresh")  // Start fresh instance
                    .spawn();
                    
                match result {
                    Ok(_) => {
                        eprintln!("🔍 [DEBUG] Launched {} successfully", app);
                        
                        // Give the app more time to fully launch and become active
                        thread::sleep(Duration::from_millis(1000));
                        
                        // Try to activate the app window using AppleScript
                        let activate_script = format!("tell application \"{}\" to activate", app);
                        let _ = std::process::Command::new("osascript")
                            .arg("-e")
                            .arg(&activate_script)
                            .output();
                        
                        eprintln!("🔍 [DEBUG] Activated {} window", app);
                        
                        // Additional delay to ensure window is ready
                        thread::sleep(Duration::from_millis(500));
                        
                        self.add_result(description, "success", 
                            format!("Launched: {}", app), Some(1500));
                        true
                    },
                    Err(e) => {
                        self.add_result(description, "failed", 
                            format!("Failed to launch: {}", e), Some(0));
                        false
                    }
                }
            }
            
            #[cfg(target_os = "windows")]
            {
                eprintln!("🔍 [DEBUG] Launching {} on Windows", app);
                
                // Use START command with /MAX to maximize window
                let result = std::process::Command::new("cmd")
                    .args(&["/C", "start", "/MAX", "", app])
                    .spawn();
                    
                match result {
                    Ok(_) => {
                        eprintln!("🔍 [DEBUG] {} launched successfully", app);
                        
                        // Give the app time to launch
                        thread::sleep(Duration::from_millis(1000));
                        
                        // Try to bring the window to foreground using PowerShell
                        // This helps ensure the window has focus for keyboard input
                        let focus_script = format!(
                            r#"
                            Add-Type @"
                            using System;
                            using System.Runtime.InteropServices;
                            public class Win32 {{
                                [DllImport("user32.dll")]
                                public static extern bool SetForegroundWindow(IntPtr hWnd);
                                [DllImport("user32.dll")]
                                public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                            }}
"@
                            $appName = "{}"
                            $handle = [Win32]::FindWindow($null, $appName)
                            if ($handle -ne [IntPtr]::Zero) {{
                                [Win32]::SetForegroundWindow($handle)
                            }}
                            "#,
                            if app.contains(".exe") { 
                                app.replace(".exe", "") 
                            } else { 
                                app.to_string() 
                            }
                        );
                        
                        let _ = std::process::Command::new("powershell")
                            .args(&["-Command", &focus_script])
                            .output();
                        
                        eprintln!("🔍 [DEBUG] Attempted to focus {} window", app);
                        
                        // Additional delay to ensure window is ready
                        thread::sleep(Duration::from_millis(500));
                        
                        self.add_result(description, "success", 
                            format!("Launched: {}", app), Some(1500));
                        true
                    },
                    Err(e) => {
                        eprintln!("🔍 [DEBUG] Failed to launch {}: {}", app, e);
                        self.add_result(description, "failed", 
                            format!("Failed to launch: {}", e), Some(0));
                        false
                    }
                }
            }
            
            #[cfg(target_os = "linux")]
            {
                let result = std::process::Command::new(app)
                    .spawn();
                    
                match result {
                    Ok(_) => {
                        self.add_result(description, "success", 
                            format!("Launched: {}", app), Some(500));
                        true
                    },
                    Err(e) => {
                        self.add_result(description, "failed", 
                            format!("Failed to launch: {}", e), Some(0));
                        false
                    }
                }
            }
        } else {
            self.add_result(description, "failed", 
                "No application specified".to_string(), Some(0));
            false
        }
    }
    
    fn capture_screen(&self) -> Result<DynamicImage, String> {
        // Get all monitors
        let monitors = Monitor::all().map_err(|e| format!("Failed to get monitors: {}", e))?;
        
        if monitors.is_empty() {
            return Err("No monitors found".to_string());
        }
        
        // Capture the primary monitor
        let primary = monitors.into_iter().next().unwrap();
        let image = primary.capture_image()
            .map_err(|e| format!("Failed to capture screen: {}", e))?;
        
        // Convert xcap's RgbaImage to image crate's DynamicImage
        // xcap uses the image crate internally, but we need to convert the buffer
        let width = image.width();
        let height = image.height();
        let raw = image.into_raw();
        let img_buffer = image::RgbaImage::from_raw(width, height, raw)
            .ok_or_else(|| "Failed to create image buffer".to_string())?;
        
        Ok(DynamicImage::ImageRgba8(img_buffer))
    }
    
    fn find_image_on_screen(&self, screen: &GrayImage, template: &GrayImage, confidence: f64) -> Option<(i32, i32)> {
        // Use normalized cross-correlation for better matching
        let result = match_template(screen, template, MatchTemplateMethod::CrossCorrelationNormalized);
        
        // Find the best match
        let mut best_score = 0.0f32;
        let mut best_pos = (0, 0);
        
        for (x, y, pixel) in result.enumerate_pixels() {
            let score = pixel[0];
            if score > best_score {
                best_score = score;
                best_pos = (x as i32, y as i32);
            }
        }
        
        // Check if the best match meets the confidence threshold
        if best_score >= confidence as f32 {
            Some(best_pos)
        } else {
            None
        }
    }
    
    #[cfg(target_os = "windows")]
    fn parse_key_windows(key_str: &str) -> Option<Key> {
        eprintln!("🔍 [DEBUG] parse_key_windows called with: '{}'", key_str);
        
        // Windows Virtual Key codes for reliable hotkey handling
        // Using Raw key codes ensures proper accelerator triggering
        match key_str.to_lowercase().as_str() {
            // Modifiers - use standard Key enum
            "ctrl" | "control" => Some(Key::Control),
            "alt" | "menu" => Some(Key::Alt),
            "shift" => Some(Key::Shift),
            "win" | "windows" | "meta" | "cmd" | "command" => Some(Key::Meta),
            
            // Letters - use VK codes for reliability with modifiers
            "a" => Some(Key::Raw(0x41)), // VK_A
            "b" => Some(Key::Raw(0x42)), // VK_B
            "c" => Some(Key::Raw(0x43)), // VK_C
            "d" => Some(Key::Raw(0x44)), // VK_D
            "e" => Some(Key::Raw(0x45)), // VK_E
            "f" => Some(Key::Raw(0x46)), // VK_F
            "g" => Some(Key::Raw(0x47)), // VK_G
            "h" => Some(Key::Raw(0x48)), // VK_H
            "i" => Some(Key::Raw(0x49)), // VK_I
            "j" => Some(Key::Raw(0x4A)), // VK_J
            "k" => Some(Key::Raw(0x4B)), // VK_K
            "l" => Some(Key::Raw(0x4C)), // VK_L
            "m" => Some(Key::Raw(0x4D)), // VK_M
            "n" => Some(Key::Raw(0x4E)), // VK_N
            "o" => Some(Key::Raw(0x4F)), // VK_O
            "p" => Some(Key::Raw(0x50)), // VK_P
            "q" => Some(Key::Raw(0x51)), // VK_Q
            "r" => Some(Key::Raw(0x52)), // VK_R
            "s" => Some(Key::Raw(0x53)), // VK_S
            "t" => Some(Key::Raw(0x54)), // VK_T
            "u" => Some(Key::Raw(0x55)), // VK_U
            "v" => Some(Key::Raw(0x56)), // VK_V
            "w" => Some(Key::Raw(0x57)), // VK_W
            "x" => Some(Key::Raw(0x58)), // VK_X
            "y" => Some(Key::Raw(0x59)), // VK_Y
            "z" => Some(Key::Raw(0x5A)), // VK_Z
            
            // Numbers
            "0" => Some(Key::Raw(0x30)), // VK_0
            "1" => Some(Key::Raw(0x31)), // VK_1
            "2" => Some(Key::Raw(0x32)), // VK_2
            "3" => Some(Key::Raw(0x33)), // VK_3
            "4" => Some(Key::Raw(0x34)), // VK_4
            "5" => Some(Key::Raw(0x35)), // VK_5
            "6" => Some(Key::Raw(0x36)), // VK_6
            "7" => Some(Key::Raw(0x37)), // VK_7
            "8" => Some(Key::Raw(0x38)), // VK_8
            "9" => Some(Key::Raw(0x39)), // VK_9
            
            // Special keys - use VK codes
            "space" => Some(Key::Raw(0x20)), // VK_SPACE
            "return" | "enter" => Some(Key::Raw(0x0D)), // VK_RETURN
            "tab" => Some(Key::Raw(0x09)), // VK_TAB
            "escape" | "esc" => Some(Key::Raw(0x1B)), // VK_ESCAPE
            "backspace" => Some(Key::Raw(0x08)), // VK_BACK
            "delete" | "del" => Some(Key::Raw(0x2E)), // VK_DELETE
            "home" => Some(Key::Raw(0x24)), // VK_HOME
            "end" => Some(Key::Raw(0x23)), // VK_END
            "pageup" | "pgup" => Some(Key::Raw(0x21)), // VK_PRIOR
            "pagedown" | "pgdn" => Some(Key::Raw(0x22)), // VK_NEXT
            "up" | "uparrow" => Some(Key::Raw(0x26)), // VK_UP
            "down" | "downarrow" => Some(Key::Raw(0x28)), // VK_DOWN
            "left" | "leftarrow" => Some(Key::Raw(0x25)), // VK_LEFT
            "right" | "rightarrow" => Some(Key::Raw(0x27)), // VK_RIGHT
            
            // Function keys
            "f1" => Some(Key::Raw(0x70)), // VK_F1
            "f2" => Some(Key::Raw(0x71)), // VK_F2
            "f3" => Some(Key::Raw(0x72)), // VK_F3
            "f4" => Some(Key::Raw(0x73)), // VK_F4
            "f5" => Some(Key::Raw(0x74)), // VK_F5
            "f6" => Some(Key::Raw(0x75)), // VK_F6
            "f7" => Some(Key::Raw(0x76)), // VK_F7
            "f8" => Some(Key::Raw(0x77)), // VK_F8
            "f9" => Some(Key::Raw(0x78)), // VK_F9
            "f10" => Some(Key::Raw(0x79)), // VK_F10
            "f11" => Some(Key::Raw(0x7A)), // VK_F11
            "f12" => Some(Key::Raw(0x7B)), // VK_F12
            
            _ => None, // Fall back to generic parsing
        }
    }
    
    fn parse_key(key_str: &str) -> Option<Key> {
        eprintln!("🔍 [DEBUG] parse_key called with: '{}'", key_str);
        
        // Use Windows-specific parsing for better reliability
        #[cfg(target_os = "windows")]
        {
            if let Some(key) = Self::parse_key_windows(key_str) {
                eprintln!("🔍 [DEBUG] Using Windows-specific key mapping");
                return Some(key);
            }
        }
        
        let result = match key_str.to_lowercase().as_str() {
            // Special keys
            "space" => Some(Key::Space),
            "return" | "enter" => Some(Key::Return),
            "tab" => Some(Key::Tab),
            "escape" | "esc" => Some(Key::Escape),
            "backspace" => Some(Key::Backspace),
            "delete" | "del" => Some(Key::Delete),
            "home" => Some(Key::Home),
            "end" => Some(Key::End),
            "pageup" | "pgup" => Some(Key::PageUp),
            "pagedown" | "pgdn" => Some(Key::PageDown),
            "up" | "uparrow" => Some(Key::UpArrow),
            "down" | "downarrow" => Some(Key::DownArrow),
            "left" | "leftarrow" => Some(Key::LeftArrow),
            "right" | "rightarrow" => Some(Key::RightArrow),
            
            // Modifiers
            "shift" | "shiftleft" | "shiftright" => Some(Key::Shift),
            "control" | "ctrl" | "ctrlleft" | "ctrlright" => Some(Key::Control),
            "alt" | "option" | "altleft" | "altright" => Some(Key::Alt),
            "meta" | "command" | "cmd" | "win" | "windows" => Some(Key::Meta),
            
            // Function keys
            "f1" => Some(Key::F1),
            "f2" => Some(Key::F2),
            "f3" => Some(Key::F3),
            "f4" => Some(Key::F4),
            "f5" => Some(Key::F5),
            "f6" => Some(Key::F6),
            "f7" => Some(Key::F7),
            "f8" => Some(Key::F8),
            "f9" => Some(Key::F9),
            "f10" => Some(Key::F10),
            "f11" => Some(Key::F11),
            "f12" => Some(Key::F12),
            
            // For letters and numbers, use Unicode variant
            // Note: We'll handle the crash issue with proper delays and error handling
            "a" => Some(Key::Unicode('a')),
            "b" => Some(Key::Unicode('b')),
            "c" => Some(Key::Unicode('c')),
            "d" => Some(Key::Unicode('d')),
            "e" => Some(Key::Unicode('e')),
            "f" => Some(Key::Unicode('f')),
            "g" => Some(Key::Unicode('g')),
            "h" => Some(Key::Unicode('h')),
            "i" => Some(Key::Unicode('i')),
            "j" => Some(Key::Unicode('j')),
            "k" => Some(Key::Unicode('k')),
            "l" => Some(Key::Unicode('l')),
            "m" => Some(Key::Unicode('m')),
            "n" => Some(Key::Unicode('n')),
            "o" => Some(Key::Unicode('o')),
            "p" => Some(Key::Unicode('p')),
            "q" => Some(Key::Unicode('q')),
            "r" => Some(Key::Unicode('r')),
            "s" => Some(Key::Unicode('s')),
            "t" => Some(Key::Unicode('t')),
            "u" => Some(Key::Unicode('u')),
            "v" => Some(Key::Unicode('v')),
            "w" => Some(Key::Unicode('w')),
            "x" => Some(Key::Unicode('x')),
            "y" => Some(Key::Unicode('y')),
            "z" => Some(Key::Unicode('z')),
            "0" => Some(Key::Unicode('0')),
            "1" => Some(Key::Unicode('1')),
            "2" => Some(Key::Unicode('2')),
            "3" => Some(Key::Unicode('3')),
            "4" => Some(Key::Unicode('4')),
            "5" => Some(Key::Unicode('5')),
            "6" => Some(Key::Unicode('6')),
            "7" => Some(Key::Unicode('7')),
            "8" => Some(Key::Unicode('8')),
            "9" => Some(Key::Unicode('9')),
            
            // For any other single character, use Unicode variant
            _ if key_str.len() == 1 => {
                Some(Key::Unicode(key_str.chars().next().unwrap()))
            },
            
            _ => None,
        };
        
        eprintln!("🔍 [DEBUG] parse_key result: {:?}", result);
        result
    }
    
    fn add_result(&mut self, action: String, status: &str, details: String, duration: Option<u64>) {
        self.results.push(ActionResult {
            action,
            status: status.to_string(),
            details,
            duration,
        });
    }
}

// Command to check if a script can be executed with Rust
pub fn can_execute_with_rust(script_json: &str) -> bool {
    let script: Value = match serde_json::from_str(script_json) {
        Ok(v) => v,
        Err(_) => return false,
    };
    
    // Check if executor is specified
    if let Some(executor) = script["executor"].as_str() {
        return executor == "rust" || executor == "native";
    }
    
    // For now, we support all actions including image recognition
    true
}