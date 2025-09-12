# Python Environment Strategy for Local Agent

## Current Issue
The Local Agent GUI runs Python scripts (script_executor.py) that require PyAutoGUI and other dependencies. Managing Python environments across different execution contexts is complex:

1. **Command line execution**: Uses system Python or venv
2. **GUI execution**: Runs from Tauri app with potentially different environment
3. **Dependency management**: Using uv/pip/venv adds complexity

## Options

### Option 1: Continue with Python + Better Environment Management
**Approach**: Ensure consistent Python environment
```rust
// In execute_test_script command
let output = Command::new("uv")
    .arg("run")
    .arg("script_executor.py")
    .arg(&script_path)
    .output();
```

**Pros**:
- Existing scripts work
- PyAutoGUI is mature and well-documented
- Image recognition works well

**Cons**:
- Requires Python + uv installed
- Environment management complexity
- Cross-platform issues

### Option 2: Switch to Rust-based Automation (Recommended Long-term)

#### 2a. Use enigo (Basic, Available Now)
```rust
use enigo::{Enigo, Key, KeyboardControllable, MouseControllable};

// Simple but no image recognition
let mut enigo = Enigo::new();
enigo.mouse_move_to(500, 200);
enigo.mouse_click(MouseButton::Left);
enigo.key_sequence("Hello World");
```

**Pros**:
- No Python dependency
- Fast and native
- Part of the Rust binary

**Cons**:
- No image recognition
- Less features than PyAutoGUI
- Need to rewrite scripts

#### 2b. Use rdev (More Features)
```rust
use rdev::{simulate, EventType, Key, SimulateError};

// More control over events
simulate(&EventType::MouseMove { x: 500.0, y: 200.0 })?;
simulate(&EventType::ButtonPress(Button::Left))?;
```

#### 2c. Wait for rsautogui (Future)
- Direct PyAutoGUI port to Rust
- Not yet mature/available on crates.io
- Would provide best compatibility

### Option 3: Hybrid Approach (Recommended Short-term)
1. **Keep Python for complex scripts** with image recognition
2. **Add Rust executor for simple scripts** without image needs
3. **Let users choose** execution backend

```rust
#[derive(Serialize, Deserialize)]
pub enum ExecutorBackend {
    Python,    // Use script_executor.py
    RustNative // Use enigo
}
```

## Recommended Implementation Plan

### Phase 1: Fix Python Environment (Immediate)
```rust
// Check for virtual environment
let venv_python = PathBuf::from("cpython-3.12.3-macos-aarch64-none/bin/python3");
let python_cmd = if venv_python.exists() {
    venv_python.to_str().unwrap()
} else {
    "python3"
};
```

### Phase 2: Add Simple Rust Executor
- Implement basic actions (click, type, hotkey) with enigo
- Auto-detect which backend to use based on script complexity
- Scripts with image recognition → Python
- Scripts without images → Rust

### Phase 3: Full Rust Migration
- Wait for rsautogui maturity or
- Build comprehensive image recognition with Rust
- Migrate all scripts to Rust format

## Script Format Compatibility

To maintain compatibility while supporting both backends:

```json
{
  "name": "Example Script",
  "executor": "auto", // or "python", "rust"
  "actions": [
    {
      "type": "click",
      "x": 500,
      "y": 200,
      // This works with both backends
    },
    {
      "type": "locateimage",
      "image": "button.png",
      // This requires Python backend
    }
  ]
}
```

## Decision Factors

| Factor | Python | Rust Native |
|--------|--------|-------------|
| Setup Complexity | High | None |
| Image Recognition | ✅ Excellent | ❌ Limited |
| Performance | 🔶 Good | ✅ Excellent |
| Dependency Management | ❌ Complex | ✅ None |
| Script Compatibility | ✅ Existing | ❌ Need rewrite |
| Cross-platform | 🔶 Issues | ✅ Native |
| Binary Size | ❌ Large | ✅ Small |

## Recommendation

**Short-term**: Fix Python environment detection and use virtual environment consistently
**Medium-term**: Implement hybrid approach with both Python and Rust backends
**Long-term**: Migrate fully to Rust when image recognition is solved