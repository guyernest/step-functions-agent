# Rust Script Executor

## Overview

The Rust Script Executor is a native alternative to the Python-based PyAutoGUI executor. It provides GUI automation capabilities without requiring Python, uv, or OpenCV dependencies.

## Features

### Supported Actions

#### Mouse Actions
- **click**: Click at current position or specified coordinates
- **doubleclick**: Double-click at current position or specified coordinates  
- **rightclick**: Right-click at current position or specified coordinates
- **moveto**: Move mouse to absolute coordinates
- **dragto**: Drag mouse from current position to target coordinates

#### Keyboard Actions
- **type/typewrite**: Type text with optional interval between characters
- **press**: Press a single key
- **hotkey**: Press multiple keys simultaneously (e.g., Ctrl+C)
- **keydown**: Hold a key down
- **keyup**: Release a held key

#### Utility Actions
- **wait/sleep**: Wait for specified seconds
- **screenshot**: Capture the screen
- **locateimage**: Find an image on screen using template matching
- **launch**: Launch an application

### Image Recognition

The Rust executor includes native image recognition capabilities using:
- **xcap**: Cross-platform screen capture
- **imageproc**: Template matching algorithms
- **image**: Image processing and manipulation

Template matching supports confidence thresholds and returns the position of found images.

## Usage

### Specifying the Executor

To use the Rust executor, set the `executor` field in your script JSON:

```json
{
  "executor": "rust",
  "actions": [...]
}
```

If no executor is specified, the system will automatically choose based on the script content:
- Scripts with image recognition default to Python (for OpenCV compatibility)
- All other scripts use the Rust executor

### Example Script

```json
{
  "executor": "rust",
  "name": "Example Rust Script",
  "abort_on_error": true,
  "actions": [
    {
      "type": "moveto",
      "x": 500,
      "y": 300,
      "description": "Move to center area"
    },
    {
      "type": "click",
      "description": "Click at current position"
    },
    {
      "type": "type",
      "text": "Hello, World!",
      "interval": 0.05,
      "description": "Type with 50ms between characters"
    },
    {
      "type": "hotkey",
      "keys": ["cmd", "s"],
      "description": "Save (Cmd+S on macOS)"
    }
  ]
}
```

## Benefits Over Python Executor

1. **No Python Dependencies**: Eliminates issues with Python environments, uv, and pip
2. **No OpenCV Requirements**: Uses native Rust image processing libraries
3. **Faster Startup**: No interpreter overhead
4. **Better Performance**: Native compiled code
5. **Simpler Deployment**: Single binary, no virtual environments

## Technical Implementation

### Architecture

The Rust executor is implemented in `src-tauri/src/rust_automation.rs` and uses:
- **enigo**: Cross-platform input simulation (keyboard and mouse)
- **xcap**: Screen capture functionality
- **imageproc**: Template matching for image recognition
- **serde**: JSON parsing and serialization

### Key Components

1. **RustScriptExecutor**: Main executor struct that processes scripts
2. **ScriptAction**: Represents individual automation actions
3. **ScriptResult**: Contains execution results and any errors
4. **Image Recognition**: Template matching with configurable confidence

### Cross-Platform Support

The executor works on:
- **macOS**: Full support for all features
- **Windows**: Full support for all features
- **Linux**: Full support (X11 and Wayland)

Platform-specific code is handled transparently by the underlying libraries.

## Migration from Python

To migrate existing Python scripts:

1. Add `"executor": "rust"` to the script JSON
2. Most actions work identically
3. Image recognition uses the same confidence thresholds
4. Key names are compatible (e.g., "cmd", "ctrl", "shift")

## Limitations

- Advanced OpenCV features (e.g., feature matching) are not yet implemented
- Some PyAutoGUI-specific functions may behave slightly differently
- Image recognition currently uses basic template matching

## Future Enhancements

- [ ] Advanced image recognition algorithms
- [ ] OCR text recognition
- [ ] Recording and playback functionality
- [ ] Visual script builder
- [ ] Performance optimizations for large-scale automation