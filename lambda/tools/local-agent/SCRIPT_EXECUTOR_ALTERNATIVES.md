# Script Executor Alternatives for Local Agent

## Current State: PyAutoGUI (Python)
The current implementation uses Python with PyAutoGUI library, which requires:
- Python runtime on target machine
- Dependency management (pip/uv)
- Subprocess execution from Rust

## Alternative Options for Rust Implementation

### Option A: RsAutoGUI (Direct PyAutoGUI Port)
**Library**: `rsautogui` - A Rust port of PyAutoGUI with similar API

#### Advantages
- **Direct API compatibility** with existing PyAutoGUI scripts
- **Minimal script format changes** required
- **Feature parity** with Python implementation
- **Easier migration path** from current solution
- **Familiar API** for users already using PyAutoGUI

#### Implementation Example
```rust
use rsautogui::{mouse, keyboard, screen};
use std::time::Duration;
use std::thread;

pub struct RsAutoGuiExecutor;

impl RsAutoGuiExecutor {
    pub fn execute_action(action: &Action) -> Result<ActionResult, String> {
        match action.action_type.as_str() {
            "click" => {
                if let (Some(x), Some(y)) = (action.x, action.y) {
                    mouse::move_to(x as f64, y as f64, Some(0.5));
                    mouse::click(None);
                    Ok(ActionResult::success("Clicked at position"))
                } else if let Some(image) = &action.image {
                    // Click on image
                    if let Some(location) = screen::locate_on_screen(image, None) {
                        mouse::click(Some(location.center()));
                        Ok(ActionResult::success("Clicked on image"))
                    } else {
                        Err("Image not found on screen".to_string())
                    }
                } else {
                    Err("Missing coordinates or image for click".to_string())
                }
            }
            "type" => {
                if let Some(text) = &action.text {
                    keyboard::type_string(text, Some(0.1));
                    Ok(ActionResult::success("Typed text"))
                } else {
                    Err("Missing text for type action".to_string())
                }
            }
            "hotkey" => {
                if let Some(keys) = &action.keys {
                    keyboard::hotkey(&keys);
                    Ok(ActionResult::success("Pressed hotkey"))
                } else {
                    Err("Missing keys for hotkey".to_string())
                }
            }
            "screenshot" => {
                let screenshot = screen::screenshot(None);
                Ok(ActionResult::with_screenshot("Screenshot captured", screenshot))
            }
            "locateimage" => {
                if let Some(image) = &action.image {
                    match screen::locate_on_screen(image, action.confidence) {
                        Some(location) => {
                            Ok(ActionResult::with_location("Image found", location))
                        }
                        None => Err("Image not found on screen".to_string())
                    }
                } else {
                    Err("Missing image for locate action".to_string())
                }
            }
            _ => Err(format!("Unknown action type: {}", action.action_type))
        }
    }
}
```

### Option B: Native Rust Libraries (Enigo + Screenshots)
**Libraries**: 
- `enigo` - Cross-platform input simulation
- `screenshots` - Screen capture
- `image` + `imageproc` - Image processing and template matching

#### Advantages
- **No Python-like dependencies**
- **Better performance** and lower latency
- **Smaller binary size**
- **More control** over low-level operations
- **Native OS integration** possibilities

#### Implementation Example
```rust
use enigo::{Enigo, Key, KeyboardControllable, MouseButton, MouseControllable};
use screenshots::Screen;
use image::{DynamicImage, ImageBuffer};
use imageproc::template_matching::{match_template, MatchTemplateMethod};

pub struct NativeExecutor {
    enigo: Enigo,
}

impl NativeExecutor {
    pub fn new() -> Self {
        Self {
            enigo: Enigo::new(),
        }
    }

    pub fn execute_action(&mut self, action: &Action) -> Result<ActionResult, String> {
        match action.action_type.as_str() {
            "click" => {
                if let (Some(x), Some(y)) = (action.x, action.y) {
                    self.enigo.mouse_move_to(x, y);
                    thread::sleep(Duration::from_millis(50));
                    self.enigo.mouse_click(MouseButton::Left);
                    Ok(ActionResult::success("Clicked"))
                } else {
                    Err("Missing coordinates".to_string())
                }
            }
            "type" => {
                if let Some(text) = &action.text {
                    self.enigo.key_sequence(text);
                    Ok(ActionResult::success("Typed text"))
                } else {
                    Err("Missing text".to_string())
                }
            }
            "screenshot" => {
                let screens = Screen::all()?;
                let image = screens[0].capture()?;
                Ok(ActionResult::with_image("Screenshot captured", image))
            }
            _ => Err(format!("Unknown action: {}", action.action_type))
        }
    }
}
```

### Option C: Hybrid Approach
**Strategy**: Support both executors and choose based on script requirements

#### Advantages
- **Backwards compatibility** with existing scripts
- **Performance optimization** where possible
- **Gradual migration** path
- **Best of both worlds**

```rust
pub enum ExecutorMode {
    RsAutoGui,  // Compatible with existing scripts
    Native,     // High-performance native implementation
    Auto,       // Choose based on script complexity
}

pub struct ScriptExecutor {
    mode: ExecutorMode,
    rsautogui_executor: Option<RsAutoGuiExecutor>,
    native_executor: Option<NativeExecutor>,
}

impl ScriptExecutor {
    pub async fn execute_script(&mut self, script: Script) -> Result<ScriptResult, String> {
        // Determine which executor to use
        let use_native = match self.mode {
            ExecutorMode::Native => true,
            ExecutorMode::RsAutoGui => false,
            ExecutorMode::Auto => self.should_use_native(&script),
        };

        // Execute with selected backend
        if use_native {
            self.native_executor.execute(script)
        } else {
            self.rsautogui_executor.execute(script)
        }
    }

    fn should_use_native(&self, script: &Script) -> bool {
        // Use native for simple scripts without image matching
        script.actions.iter().all(|a| 
            matches!(a.action_type.as_str(), "click" | "type" | "screenshot" | "hotkey")
            && a.image.is_none()
        )
    }
}
```

## Comparison Matrix

| Feature | PyAutoGUI (Current) | RsAutoGUI | Native Libraries | Hybrid |
|---------|-------------------|-----------|------------------|--------|
| **Script Compatibility** | ✅ Baseline | ✅ High | ❌ Requires changes | ✅ High |
| **Performance** | ❌ Slow (subprocess) | ✅ Good | ✅ Excellent | ✅ Excellent |
| **Binary Size** | ❌ Requires Python | 🔶 Medium | ✅ Small | ❌ Large |
| **Maintenance** | ❌ Two languages | ✅ Single language | ✅ Single language | 🔶 Complex |
| **Image Matching** | ✅ Full support | ✅ Full support | 🔶 Basic | ✅ Full |
| **Cross-platform** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Dependencies** | ❌ Python + libs | 🔶 Rust libs | ✅ Minimal | ❌ Many |
| **Development Speed** | - | ✅ Fast | 🔶 Moderate | ❌ Slow |

## Cargo.toml Dependencies

```toml
# For RsAutoGUI approach
[dependencies]
rsautogui = "0.1"  # Check for latest version

# For Native approach
[dependencies]
enigo = "0.2"
screenshots = "0.8"
image = "0.24"
imageproc = "0.23"

# Additional useful libraries
rdev = "0.5"  # Global hotkeys
winit = "0.29"  # Window management

# For Hybrid approach (all of the above)
```

## Migration Strategy

### Phase 1: Immediate (Week 1-2)
- Implement **RsAutoGUI** as drop-in replacement
- Maintain 100% script compatibility
- Remove Python dependency
- Focus on GUI implementation

### Phase 2: Optimization (Week 3-4)
- Profile performance bottlenecks
- Implement native alternatives for critical paths
- Add execution mode selection in GUI
- Benchmark both approaches

### Phase 3: Enhancement (Week 5+)
- Add features beyond PyAutoGUI:
  - OCR text recognition
  - Advanced image matching algorithms
  - Window-specific automation
  - Macro recording
- Platform-specific optimizations:
  - Windows: UI Automation API
  - macOS: Accessibility API
  - Linux: AT-SPI

## Recommendation

**Start with RsAutoGUI** for the following reasons:

1. **Immediate compatibility** - No need to change existing scripts
2. **Faster development** - Can focus on GUI implementation
3. **Proven API** - PyAutoGUI's API is battle-tested
4. **Easy rollback** - Can always fall back to Python if issues arise
5. **Clear migration path** - Can gradually introduce native optimizations

Once the GUI is stable and working well with RsAutoGUI, evaluate performance requirements and consider implementing the hybrid approach for optimal performance while maintaining compatibility.

## Next Steps

1. **Test RsAutoGUI** with existing script formats
2. **Benchmark** RsAutoGUI vs current PyAutoGUI implementation
3. **Prototype** basic native executor for comparison
4. **Decide** on initial approach based on testing results
5. **Implement** chosen solution in Tauri app

## Open Questions

1. **Image matching accuracy**: How does RsAutoGUI's image matching compare to PyAutoGUI?
2. **Platform-specific issues**: Any known limitations on Windows/macOS/Linux?
3. **Performance requirements**: What's the acceptable latency for actions?
4. **Script complexity**: What percentage of scripts use advanced features like image matching?
5. **User base**: Will users need to modify existing scripts?