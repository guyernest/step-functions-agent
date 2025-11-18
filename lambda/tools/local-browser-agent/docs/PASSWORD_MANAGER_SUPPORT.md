# Password Manager Autofill Support

This document describes the password manager autofill support added in v0.4.1 to handle browser password managers reliably across different platforms, especially Windows.

## Problem Statement

When using browser automation, the "controlled by automation" banner can interfere with browser password manager autofill:
- Password manager may not automatically fill passwords
- Autofilled passwords may be cleared when the banner appears
- Behavior is inconsistent across Windows, macOS, and Linux

## Solution: Three-Layer Defense

### Layer 1: Disable Automation Detection (Browser Level)

The browser is launched with arguments to disable automation detection:

```rust
// In openai_playwright_executor.py:303-308
args = [
    '--disable-blink-features=AutomationControlled',  // Remove automation banner
    '--disable-dev-shm-usage',  // Overcome limited resource problems
    '--no-sandbox',  // Disable sandbox for compatibility
]
```

**Benefits:**
- Makes browser appear less "automated"
- Allows natural password manager behavior
- Improves compatibility with password autofill

### Layer 2: Keyboard Press Support (Script Level)

New `press` step type for programmatic keyboard input:

```json
{
    "type": "press",
    "description": "Select password from manager (Arrow Down + Enter)",
    "keys": ["ArrowDown", "Enter"],
    "delay": 500
}
```

**Supports:**
- Single key: `{"type": "press", "key": "Enter"}`
- Multiple keys: `{"type": "press", "keys": ["ArrowDown", "Enter"]}`
- Configurable delay: `{"type": "press", "keys": ["ArrowDown", "Enter"], "delay": 500}`
- Any Playwright keyboard key (Tab, ArrowUp, ArrowDown, Enter, Escape, etc.)

**Parameters:**
- `key` (string): Single key to press
- `keys` (array): Multiple keys to press in sequence
- `delay` (number, optional): Delay in milliseconds between key presses (default: 100ms)

**Implementation:**
```python
# In openai_playwright_executor.py:757-787
async def _step_press(self, step: Dict[str, Any], step_num: int):
    """Press keyboard key(s) with configurable delay"""
    keys = step.get("keys", [])
    delay_ms = step.get("delay", 100)  # Default 100ms

    for i, k in enumerate(keys):
        await self.page.keyboard.press(k)
        # Apply delay after each key (including the last one)
        # This gives UI time to respond to the key press
        await asyncio.sleep(delay_ms / 1000.0)

    return {"success": True, "action": "press", "keys": keys, "delay_ms": delay_ms}
```

**Why Configurable Delay?**
- Password managers on different platforms respond at different speeds
- Windows may require longer delays (500ms recommended) for dropdown to appear
- macOS and Linux may work fine with default 100ms
- Prevents commands from executing too fast for UI to respond
- Delay applied AFTER each key, including the last one, to ensure password fills before next step

### Layer 3: Progressive Fallback (Template Level)

Script templates use a progressive approach:

```json
[
    {
        "type": "wait",
        "description": "Wait for browser autofill to complete",
        "duration": 2000
    },
    {
        "type": "click",
        "description": "Click password field to activate password manager",
        "escalation_chain": [...]
    },
    {
        "type": "wait",
        "description": "Wait for password manager dropdown",
        "duration": 1000
    },
    {
        "type": "press",
        "description": "Select password from manager (Arrow Down + Enter)",
        "keys": ["ArrowDown", "Enter"],
        "delay": 500
    },
    {
        "type": "wait",
        "description": "Wait for password to fill from manager",
        "duration": 1500
    },
    {
        "type": "execute_js",
        "description": "Verify password was filled by password manager",
        "script": "(function() { var pwdField = document.querySelector('input[type=\"password\"]'); return { passwordFilled: pwdField ? pwdField.value.length > 0 : false }; })()"
    }
]
```

## How It Works

### Workflow

1. **Wait for autofill** (2000ms)
   - Give browser time to naturally fill password

2. **Click password field**
   - Focuses the field
   - Triggers password manager dropdown

3. **Wait for dropdown** (1000ms)
   - Password manager UI appears

4. **Trigger selection** (ArrowDown + Enter with 500ms delay)
   - ArrowDown selects first saved password (wait 500ms)
   - Enter confirms selection (wait 500ms after)
   - Total time: 1000ms for keyboard interaction

5. **Wait for fill** (1500ms)
   - Password manager fills the field
   - Ensures password is fully populated

6. **Verify fill** (JavaScript check)
   - Check if password field has value
   - Log the result for debugging
   - Ensures password is ready before clicking Next

### Why This Approach Works

- **Non-intrusive**: Doesn't interfere if natural autofill works
- **Reliable**: Programmatically triggers password manager if needed
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Browser-agnostic**: Works with Chrome, Edge, and Chromium password managers

## Example: BT Broadband Authentication

See `examples/bt_broadband_password_manager.json` for a complete example:

**Password Steps (simplified):**
```json
{
    "steps": [
        // ... username entry steps ...

        {
            "type": "wait",
            "description": "Wait for password field to appear",
            "locator": {
                "strategy": "selector",
                "value": "input[type='password']"
            },
            "timeout": 30000
        },
        {
            "type": "wait",
            "description": "Wait for browser autofill",
            "duration": 2000
        },
        {
            "type": "click",
            "description": "Click password field",
            "escalation_chain": [
                {
                    "method": "playwright_locator",
                    "locator": {
                        "strategy": "selector",
                        "value": "input[type='password']"
                    }
                }
            ]
        },
        {
            "type": "wait",
            "description": "Wait for password manager dropdown",
            "duration": 800
        },
        {
            "type": "press",
            "description": "Select password (Arrow Down + Enter)",
            "keys": ["ArrowDown", "Enter"]
        },
        {
            "type": "wait",
            "description": "Wait for password to fill",
            "duration": 500
        },
        {
            "type": "click",
            "description": "Click Next button",
            "escalation_chain": [...]
        }
    ]
}
```

## Configuration

No additional configuration required! The features are automatically enabled in v0.4.1+.

**Browser arguments** are automatically applied when using OpenAI Playwright executor.

**Press step type** is automatically available for all scripts.

## Keyboard Keys Reference

Supported keys for the `press` step type (from Playwright):

### Common Keys
- `Enter` - Submit/confirm
- `Escape` - Cancel/close
- `Tab` - Navigate forward
- `Space` - Spacebar
- `Backspace` - Delete backward
- `Delete` - Delete forward

### Arrow Keys
- `ArrowUp` - Move up
- `ArrowDown` - Move down
- `ArrowLeft` - Move left
- `ArrowRight` - Move right

### Function Keys
- `F1` through `F12`

### Modifier Keys
- `Shift`
- `Control` (or `Meta` on macOS)
- `Alt`

### Special Keys
- `PageUp`, `PageDown`
- `Home`, `End`
- `Insert`

For a complete list, see [Playwright Keyboard API](https://playwright.dev/docs/api/class-keyboard).

## Testing

### Test Locally First

Before deploying to production:

1. **Save password** in your browser profile
   - Manually login once in the profile
   - Allow browser to save credentials

2. **Run the script** locally
   - Use Test UI or CLI
   - Watch the password manager interaction

3. **Verify behavior**
   - Check if autofill works naturally (wait step)
   - Check if programmatic trigger works (click + press)
   - Review logs for password field status

### Example Test

```bash
# Run BT Broadband password manager example
cd lambda/tools/local-browser-agent

# Option 1: Via UI
# 1. Open Local Browser Agent
# 2. Go to Test Scripts tab
# 3. Select "bt_broadband_password_manager.json"
# 4. Click "Run Script"

# Option 2: Via CLI
python python/openai_playwright_executor.py \
  --script examples/bt_broadband_password_manager.json \
  --aws-profile CGI-PoC \
  --navigation-timeout 60000 \
  --user-data-dir "$HOME/Library/Application Support/Local Browser Agent/profiles/Bt_broadband"
```

### Troubleshooting

**Password manager doesn't appear:**
- Ensure password is saved in the browser profile
- Check that you're using the correct profile (with saved credentials)
- Try increasing wait duration after click (default: 800ms)

**Password not selected:**
- The first saved password for the site should be selected
- If you have multiple passwords, ArrowDown selects the first one
- You can press ArrowDown multiple times: `"keys": ["ArrowDown", "ArrowDown", "Enter"]`

**Keyboard commands too fast (Windows issue):**
- **Symptom**: Password manager dropdown appears but password not selected
- **Root cause**: Commands execute faster than UI can respond (especially on remote/slower machines)
- **Solution**: Add `delay` parameter to slow down key presses:
  ```json
  {
      "type": "press",
      "keys": ["ArrowDown", "Enter"],
      "delay": 500  // 500ms delay between keys (recommended for Windows)
  }
  ```
- **Recommended delays**:
  - Windows: 500ms (slower password manager UI)
  - macOS: 100ms (default, faster response)
  - Linux: 100-300ms (varies by desktop environment)
- **Alternative**: Break into separate steps with wait times:
  ```json
  [
      {"type": "press", "key": "ArrowDown"},
      {"type": "wait", "duration": 500},
      {"type": "press", "key": "Enter"}
  ]
  ```

**Still fails on Windows:**
- Verify browser channel is set (chrome, msedge, etc.)
- Check that Windows password manager has credentials
- Try running in non-headless mode for debugging
- Increase the delay parameter (try 700ms or 1000ms)

## Migrating Existing Templates

To add password manager support to existing templates:

1. **Remove hardcoded password fills** (if any)
2. **Add wait for autofill** (2000ms recommended)
3. **Add click on password field**
4. **Add wait for dropdown** (800ms recommended)
5. **Add press step** (ArrowDown + Enter)
6. **Add wait for fill** (500ms recommended)

**Before:**
```json
{
    "type": "fill",
    "description": "Enter password",
    "locator": {"strategy": "selector", "value": "input[type='password']"},
    "value": "{{password}}"  // Hardcoded password
}
```

**After:**
```json
{
    "type": "wait",
    "description": "Wait for browser autofill",
    "duration": 2000
},
{
    "type": "click",
    "description": "Click password field",
    "escalation_chain": [
        {
            "method": "playwright_locator",
            "locator": {"strategy": "selector", "value": "input[type='password']"}
        }
    ]
},
{
    "type": "wait",
    "description": "Wait for password manager dropdown",
    "duration": 800
},
{
    "type": "press",
    "description": "Select password from manager",
    "keys": ["ArrowDown", "Enter"],
    "delay": 500
},
{
    "type": "wait",
    "description": "Wait for password to fill",
    "duration": 500
}
```

## Security Considerations

**Benefits:**
- ✅ No passwords stored in scripts or templates
- ✅ Passwords remain in browser password manager
- ✅ Uses browser's built-in encryption
- ✅ Password manager policies respected

**Best Practices:**
- Use browser profiles with saved credentials
- Don't commit passwords to templates
- Use profile tagging for multi-account scenarios
- Review recordings to ensure no password exposure

## Version History

- **v0.4.2** (2025-01-17)
  - Added configurable `delay` parameter to `press` step type
  - Fixes timing issues on Windows where keyboard commands were too fast
  - Updated documentation with troubleshooting for timing issues
  - Updated example template with recommended 500ms delay for Windows

- **v0.4.1** (2024-11-17)
  - Added `--disable-blink-features=AutomationControlled` browser argument
  - Implemented `press` step type for keyboard actions
  - Created example template: `bt_broadband_password_manager.json`
  - Documented password manager support

## See Also

- [Session Management Guide](../SESSION_MANAGEMENT_GUIDE.md) - Browser profiles
- [Examples README](../examples/README.md) - Sample scripts
- [Playwright Keyboard API](https://playwright.dev/docs/api/class-keyboard) - Key reference
