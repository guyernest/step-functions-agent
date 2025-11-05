# Local Browser Agent - Windows Improvements Design Document

**Version:** 1.0
**Date:** 2025-01-05
**Status:** Implementation Ready

---

## Executive Summary

This document outlines improvements to the Local Browser Agent focused on Windows corporate deployment, removing hardcoded demo logic, and enhancing browser flexibility.

### Key Goals:
1. ✅ **Windows Corporate Ready** - Use Microsoft Edge by default (pre-installed on Windows 10/11)
2. ✅ **No Hardcoded Values** - Remove "Bt_broadband" demo profile forcing
3. ✅ **Flexible Browser Selection** - Support Edge, Chrome, and Chromium via configuration
4. ✅ **Safe Profile Management** - Never corrupt user's default browser profiles
5. ✅ **Better Installation** - Robust UV detection, minimal browser installation

---

## Current State Analysis

### Critical Issues Identified:

1. **Hardcoded "Bt_broadband" Profile**
   - Location: `python/nova_act_wrapper.py` lines 161-176
   - Location: `python/script_executor.py` lines 148-158
   - Impact: Forces specific profile, prevents real-world usage
   - **Priority: CRITICAL** - Must be removed first

2. **No Browser Channel Selection**
   - Current: Defaults to Chrome installation via Playwright
   - Problem: Windows machines often have Edge pre-installed, Chrome requires admin rights
   - Impact: Unnecessary installation, corporate policy conflicts
   - **Priority: HIGH**

3. **User Profile Risk**
   - Current: Can potentially use user's default Chrome/Edge profile
   - Problem: Risk of corrupting user's personal browser data
   - Impact: User trust, data safety
   - **Priority: MEDIUM**

4. **Chrome Installation Required**
   - Current: SETUP scripts install Chrome via Playwright
   - Problem: Admin rights needed, unnecessary on Windows with Edge
   - Impact: Installation friction, corporate policy issues
   - **Priority: HIGH**

5. **Credential Handling**
   - Current: Always uses AWS profile
   - Problem: Doesn't prefer environment variables
   - Impact: Less flexible for containerized/CI environments
   - **Priority: LOW**

---

## Architecture Design

### Configuration Schema

```yaml
# New configuration fields:

browser_channel: "msedge"  # "msedge" | "chrome" | "chromium" | null (auto)
profiles_dir: null         # OS-specific default path for agent profiles
```

### Platform Defaults

| Platform | Default Browser | Default Profiles Directory |
|----------|----------------|---------------------------|
| Windows  | `msedge`       | `%LOCALAPPDATA%\Local Browser Agent\profiles` |
| macOS    | `chrome`       | `~/Library/Application Support/Local Browser Agent/profiles` |
| Linux    | `chrome`       | `~/.local/share/local-browser-agent/profiles` |

### Browser Channel Resolution

```
User Config
    ↓
browser_channel: "msedge" → Use Microsoft Edge
browser_channel: "chrome" → Use Google Chrome
browser_channel: "chromium" → Use Playwright Chromium
browser_channel: null → Auto-detect by platform
```

### Profile Management Strategy

**Current (Unsafe):**
```
User can select → Default Chrome Profile → Risk of corruption
```

**New (Safe):**
```
Agent Profiles Only → %LOCALAPPDATA%\Local Browser Agent\profiles\{profile_name}
                  → Isolated from user's personal browser
                  → Clone for parallel runs if needed
```

---

## Implementation Plan

### Phase 1: Critical Fixes (Priority 1)

**Estimated Time:** 2-3 hours

#### 1.1 Remove Hardcoded "Bt_broadband" Logic

**File: `python/nova_act_wrapper.py`**

**Lines 161-176 - REMOVE:**
```python
# HARDCODED FOR DEMO: Always use Bt_broadband profile
profile_name = "Bt_broadband"
profile_config = profile_manager.get_nova_act_config(profile_name, clone_for_parallel=False)
user_data_dir = profile_config["user_data_dir"]
clone_user_data_dir = profile_config["clone_user_data_dir"]
```

**REPLACE WITH:**
```python
# Use profile from session config or input
profile_name = session_config.get("profile_name") if session_config else None

if profile_name:
    # Named profile from profile manager
    profile_config = profile_manager.get_nova_act_config(
        profile_name,
        clone_for_parallel=session_config.get("clone_for_parallel", False)
    )
    user_data_dir = profile_config["user_data_dir"]
    clone_user_data_dir = profile_config["clone_user_data_dir"]
else:
    # Use from input or null (temporary profile)
    user_data_dir = input_data.get("user_data_dir")
    clone_user_data_dir = input_data.get("clone_user_data_dir", False)
```

**File: `python/script_executor.py`**

**Lines 148-158 - REMOVE:**
```python
# HARDCODED FOR DEMO: Always use Bt_broadband profile
profile_name = "Bt_broadband"
mode = "use_profile"
```

**REPLACE WITH:**
```python
# Use profile from script session config
if session_config and session_config.get("profile_name"):
    profile_name = session_config["profile_name"]
    mode = "use_profile"
else:
    # Use provided user_data_dir or temporary profile
    mode = "use_existing" if self.user_data_dir else "temp_profile"
```

**Testing:**
- Run test scripts without "Bt_broadband" profile
- Verify temporary profiles work
- Verify named profiles work when specified

---

#### 1.2 Add `browser_channel` Configuration

**File: `src-tauri/src/config.rs`**

**Add field to Config struct:**
```rust
pub struct Config {
    // ... existing fields ...

    /// Browser channel: "msedge", "chrome", "chromium", or null for auto-detect
    pub browser_channel: Option<String>,
}
```

**Add to Default implementation:**
```rust
impl Default for Config {
    fn default() -> Self {
        Self {
            // ... existing defaults ...
            browser_channel: Self::default_browser_channel(),
        }
    }
}

impl Config {
    /// Platform-specific default browser channel
    fn default_browser_channel() -> Option<String> {
        #[cfg(target_os = "windows")]
        return Some("msedge".to_string());

        #[cfg(not(target_os = "windows"))]
        return Some("chrome".to_string());
    }
}
```

**File: `config.example.yaml`**

**Add configuration:**
```yaml
# ────────────────────────────────────────────────────────────────
# Browser Configuration
# ────────────────────────────────────────────────────────────────

# Browser channel: "msedge" (Windows default), "chrome", "chromium"
# null = auto-detect (Edge on Windows, Chrome on Mac/Linux)
browser_channel: null

# User data directory for browser profiles
# null = use temporary profile (recommended for most use cases)
user_data_dir: null

# Headless mode (true = no browser window, false = visible browser)
headless: false
```

**File: `src-tauri/src/config_commands.rs`**

**Update save/load to handle new field:**
```rust
// Already handled by serde, just verify serialization works
```

**Testing:**
- Load config with browser_channel: "msedge"
- Verify platform defaults work
- Save and reload config preserves browser_channel

---

#### 1.3 Pass `browser_channel` to Python Scripts

**File: `src-tauri/src/nova_act_executor.rs`**

**Update build_command() method:**
```rust
fn build_command(&self, mut input: Value) -> Result<Value> {
    // Add config values
    if let Some(obj) = input.as_object_mut() {
        // ... existing fields ...

        // Add browser_channel if configured
        if let Some(ref channel) = self.config.browser_channel {
            obj.insert("browser_channel".to_string(), json!(channel));
        }
    }

    Ok(input)
}
```

**File: `src-tauri/src/test_commands.rs`**

**Update execute_browser_script() to pass browser_channel:**
```rust
// Build script input
let mut script_input = json!({
    "script": parsed,
    "s3_bucket": current_config.s3_bucket,
    "aws_profile": current_config.aws_profile,
    "headless": headless,
    "record_video": true,
    "user_data_dir": current_config.user_data_dir,
});

// Add browser_channel if configured
if let Some(ref channel) = current_config.browser_channel {
    script_input["browser_channel"] = json!(channel);
}
```

**Testing:**
- Verify browser_channel passed to Python scripts
- Check Python receives correct value

---

#### 1.4 Support `browser_channel` in Python Scripts

**File: `python/nova_act_wrapper.py`**

**Update execute_command() function:**
```python
def execute_command(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Nova Act command via stdin/stdout."""

    # Extract parameters
    command_type = input_data.get("command_type", "act")
    # ... existing parameters ...
    browser_channel = input_data.get("browser_channel")  # NEW

    # Create Nova Act agent with browser channel
    agent = NovaActAgent(
        api_key=api_key,
        user_data_dir=user_data_dir,
        headless=headless,
        record_video=record_video,
        browser_channel=browser_channel,  # NEW - Playwright supports this
        clone_user_data_dir=clone_user_data_dir,
        s3_writer=s3_writer,
    )
```

**Note:** Based on Playwright documentation (https://playwright.dev/python/docs/browsers#google-chrome--microsoft-edge), the `channel` parameter is supported:

```python
# Playwright supports channel parameter:
browser = playwright.chromium.launch(channel="msedge")  # For Edge
browser = playwright.chromium.launch(channel="chrome")  # For Chrome
```

**File: `python/script_executor.py`**

**Update ScriptExecutor class:**
```python
class ScriptExecutor:
    def __init__(
        self,
        # ... existing parameters ...
        browser_channel: Optional[str] = None,  # NEW
    ):
        self.browser_channel = browser_channel
        # ... existing initialization ...

    def _create_agent(self, **kwargs) -> NovaActAgent:
        """Create Nova Act agent with configuration."""
        return NovaActAgent(
            api_key=self.nova_act_api_key,
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            record_video=self.record_video,
            browser_channel=self.browser_channel,  # NEW
            s3_writer=self.s3_writer,
            **kwargs
        )
```

**Testing:**
- Test with browser_channel="msedge" on Windows
- Test with browser_channel="chrome"
- Test with browser_channel="chromium"
- Verify Playwright launches correct browser

---

#### 1.5 Update SETUP.ps1 - UV Detection

**File: `SETUP.ps1`**

**Replace UV detection section:**
```powershell
# ═══════════════════════════════════════════════════════════════
# Enhanced UV Detection and Installation
# ═══════════════════════════════════════════════════════════════

function Find-UV {
    Write-Host "Checking for UV package manager..." -ForegroundColor Cyan

    # Check known installation locations
    $uvPaths = @(
        "$env:USERPROFILE\.local\bin\uv.exe",
        "$env:USERPROFILE\.cargo\bin\uv.exe"
    )

    foreach ($path in $uvPaths) {
        if (Test-Path $path) {
            Write-Host "  ✓ Found UV at: $path" -ForegroundColor Green
            return $path
        }
    }

    # Check PATH
    $uvInPath = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($uvInPath) {
        Write-Host "  ✓ Found UV in PATH: $($uvInPath.Source)" -ForegroundColor Green
        return $uvInPath.Source
    }

    Write-Host "  ✗ UV not found in known locations" -ForegroundColor Yellow
    return $null
}

$uvPath = Find-UV

if (-not $uvPath) {
    Write-Host ""
    Write-Host "Installing UV package manager..." -ForegroundColor Yellow

    try {
        irm https://astral.sh/uv/install.ps1 | iex

        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path", "Machine")

        # Try to find UV again
        Start-Sleep -Seconds 2
        $uvPath = Find-UV

        if (-not $uvPath) {
            Write-Error "Failed to install UV. Please install manually: https://docs.astral.sh/uv/getting-started/installation/"
            exit 1
        }

        Write-Host "  ✓ UV installed successfully" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install UV: $_"
        exit 1
    }
}

Write-Host ""
```

**Testing:**
- Test on machine without UV
- Test on machine with UV in .local\bin
- Test on machine with UV in .cargo\bin
- Verify installation succeeds

---

#### 1.6 Update SETUP Scripts - Chromium Only Installation

**File: `SETUP.ps1`**

**Replace Playwright installation section:**
```powershell
# ═══════════════════════════════════════════════════════════════
# Install Playwright Browsers (Chromium only)
# ═══════════════════════════════════════════════════════════════

Write-Host "Installing Playwright browsers..." -ForegroundColor Cyan
Write-Host "  → Installing Chromium only (Microsoft Edge can be used via system installation)" -ForegroundColor Gray
Write-Host ""

& "$VenvPath\Scripts\playwright.exe" install chromium --with-deps

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Playwright browser installation had issues, but continuing..."
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Browser Configuration:" -ForegroundColor Yellow
Write-Host "  • Microsoft Edge (recommended) - Already installed on Windows 10/11" -ForegroundColor White
Write-Host "    No additional installation needed!" -ForegroundColor Gray
Write-Host ""
Write-Host "  • Google Chrome - Install separately if needed" -ForegroundColor White
Write-Host "    See: docs/CHROME_ENTERPRISE_INSTALL.md" -ForegroundColor Gray
Write-Host ""
Write-Host "  • Chromium (fallback) - Installed by this script" -ForegroundColor White
Write-Host ""
Write-Host "To configure browser:" -ForegroundColor Cyan
Write-Host "  1. Launch Local Browser Agent" -ForegroundColor White
Write-Host "  2. Go to Configuration → Browser Channel" -ForegroundColor White
Write-Host "  3. Select 'Microsoft Edge' (recommended for Windows)" -ForegroundColor White
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
```

**File: `deployment-package/SETUP.sh`**

**Update macOS/Linux version:**
```bash
# ═══════════════════════════════════════════════════════════════
# Install Playwright Browsers (Chromium only)
# ═══════════════════════════════════════════════════════════════

echo "Installing Playwright browsers..."
echo "  → Installing Chromium only (Chrome can be used via system installation)"
echo ""

.venv/bin/python -m playwright install chromium --with-deps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Setup Complete!"
echo ""
echo "Browser Configuration:"
echo "  • Google Chrome (recommended) - Install separately if needed"
echo "  • Chromium (fallback) - Installed by this script"
echo ""
echo "To configure browser:"
echo "  1. Launch Local Browser Agent"
echo "  2. Go to Configuration → Browser Channel"
echo "  3. Select your preferred browser"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**Testing:**
- Run SETUP.ps1 on Windows - verify only Chromium installed
- Run SETUP.sh on macOS - verify only Chromium installed
- Check that no Chrome installation attempted

---

### Phase 2: Configuration Enhancements (Priority 2)

**Estimated Time:** 2-3 hours

#### 2.1 Add `profiles_dir` Configuration

**File: `src-tauri/src/config.rs`**

```rust
pub struct Config {
    // ... existing fields ...

    /// Directory for agent-managed browser profiles
    pub profiles_dir: Option<PathBuf>,
}

impl Config {
    /// Get OS-specific default profiles directory
    pub fn default_profiles_dir() -> Result<PathBuf, String> {
        #[cfg(target_os = "windows")]
        {
            let local_appdata = std::env::var("LOCALAPPDATA")
                .map_err(|_| "LOCALAPPDATA environment variable not set")?;
            Ok(PathBuf::from(local_appdata)
                .join("Local Browser Agent")
                .join("profiles"))
        }

        #[cfg(target_os = "macos")]
        {
            let home = dirs::home_dir()
                .ok_or("Could not determine home directory")?;
            Ok(home
                .join("Library")
                .join("Application Support")
                .join("Local Browser Agent")
                .join("profiles"))
        }

        #[cfg(target_os = "linux")]
        {
            let home = dirs::home_dir()
                .ok_or("Could not determine home directory")?;
            Ok(home
                .join(".local")
                .join("share")
                .join("local-browser-agent")
                .join("profiles"))
        }
    }

    /// Get profiles directory (configured or default)
    pub fn get_profiles_dir(&self) -> Result<PathBuf, String> {
        match &self.profiles_dir {
            Some(dir) => Ok(dir.clone()),
            None => Self::default_profiles_dir(),
        }
    }
}
```

**File: `config.example.yaml`**

```yaml
# Agent-managed profiles directory
# null = OS-specific default:
#   Windows: %LOCALAPPDATA%\Local Browser Agent\profiles
#   macOS: ~/Library/Application Support/Local Browser Agent/profiles
#   Linux: ~/.local/share/local-browser-agent/profiles
profiles_dir: null
```

---

#### 2.2 Update Profile Manager for OS-Specific Defaults

**File: `python/profile_manager.py`**

**Update __init__ method:**
```python
class ProfileManager:
    def __init__(self, profiles_dir: Optional[str] = None):
        """
        Initialize profile manager.

        Args:
            profiles_dir: Custom profiles directory, or None to use OS default
        """
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            # Use OS-specific defaults
            self.profiles_dir = self._get_default_profiles_dir()

        # Create directory if it doesn't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.profiles_dir / "profiles.json"
        self._load_metadata()

    @staticmethod
    def _get_default_profiles_dir() -> Path:
        """Get OS-specific default profiles directory."""
        system = platform.system()

        if system == "Windows":
            local_appdata = os.environ.get("LOCALAPPDATA")
            if not local_appdata:
                raise ValueError("LOCALAPPDATA environment variable not set")
            return Path(local_appdata) / "Local Browser Agent" / "profiles"

        elif system == "Darwin":  # macOS
            home = Path.home()
            return home / "Library" / "Application Support" / "Local Browser Agent" / "profiles"

        else:  # Linux
            home = Path.home()
            return home / ".local" / "share" / "local-browser-agent" / "profiles"
```

---

#### 2.3 Wire Configuration to UI

**File: `ui/src/components/ConfigScreen.tsx`**

**Add Browser Configuration Section:**
```typescript
// Add state
const [browserChannel, setBrowserChannel] = useState<string>(config.browser_channel || 'auto');
const [profilesDir, setProfilesDir] = useState<string>(config.profiles_dir || '');

// Add to form
<div className="config-section">
  <h3>Browser Configuration</h3>

  <div className="form-group">
    <label htmlFor="browser-channel">
      Browser Channel:
      <span className="help-text">
        Select which browser to use for automation
      </span>
    </label>
    <select
      id="browser-channel"
      value={browserChannel}
      onChange={(e) => setBrowserChannel(e.target.value)}
    >
      <option value="auto">Auto-detect (Edge on Windows, Chrome on others)</option>
      <option value="msedge">Microsoft Edge (recommended for Windows)</option>
      <option value="chrome">Google Chrome</option>
      <option value="chromium">Chromium (installed by setup)</option>
    </select>
  </div>

  <div className="form-group">
    <label htmlFor="profiles-dir">
      Profiles Directory:
      <span className="help-text">
        Where agent-managed browser profiles are stored
      </span>
    </label>
    <div className="input-with-button">
      <input
        id="profiles-dir"
        type="text"
        value={profilesDir}
        onChange={(e) => setProfilesDir(e.target.value)}
        placeholder="Leave empty for OS default"
      />
      <button onClick={handleBrowseProfilesDir}>Browse...</button>
    </div>
    <div className="help-text">
      Default: {getDefaultProfilesDir()}
    </div>
  </div>
</div>
```

---

### Phase 3: Profile Management (Priority 3)

**Estimated Time:** 2-3 hours

#### 3.1 Windows Browser Profile Enumeration

**File: `src-tauri/src/config_commands.rs`**

**Rename and enhance profile listing:**
```rust
#[derive(Debug, Serialize, Deserialize)]
pub struct BrowserProfile {
    pub name: String,
    pub path: PathBuf,
    pub browser: String,  // "edge", "chrome", "agent"
    pub is_default: bool,
    pub is_agent_managed: bool,
}

#[tauri::command]
pub async fn list_browser_profiles(
    config: State<'_, Arc<Config>>
) -> Result<Vec<BrowserProfile>, String> {
    let mut profiles = Vec::new();

    // List agent-managed profiles first
    let profiles_dir = config.get_profiles_dir()
        .map_err(|e| format!("Failed to get profiles directory: {}", e))?;

    if profiles_dir.exists() {
        for entry in std::fs::read_dir(&profiles_dir)
            .map_err(|e| format!("Failed to read profiles directory: {}", e))?
        {
            if let Ok(entry) = entry {
                let path = entry.path();
                if path.is_dir() {
                    if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                        profiles.push(BrowserProfile {
                            name: name.to_string(),
                            path,
                            browser: "agent".to_string(),
                            is_default: false,
                            is_agent_managed: true,
                        });
                    }
                }
            }
        }
    }

    // List system browser profiles (read-only, for reference)
    #[cfg(target_os = "windows")]
    {
        let local_appdata = std::env::var("LOCALAPPDATA")
            .map_err(|_| "LOCALAPPDATA not set")?;

        // Microsoft Edge profiles
        let edge_dir = PathBuf::from(&local_appdata)
            .join("Microsoft")
            .join("Edge")
            .join("User Data");

        if edge_dir.exists() {
            profiles.extend(discover_system_profiles(&edge_dir, "edge")?);
        }

        // Google Chrome profiles
        let chrome_dir = PathBuf::from(&local_appdata)
            .join("Google")
            .join("Chrome")
            .join("User Data");

        if chrome_dir.exists() {
            profiles.extend(discover_system_profiles(&chrome_dir, "chrome")?);
        }
    }

    #[cfg(target_os = "macos")]
    {
        let home = dirs::home_dir()
            .ok_or("Could not determine home directory")?;

        let chrome_dir = home
            .join("Library")
            .join("Application Support")
            .join("Google")
            .join("Chrome");

        if chrome_dir.exists() {
            profiles.extend(discover_system_profiles(&chrome_dir, "chrome")?);
        }
    }

    Ok(profiles)
}

fn discover_system_profiles(
    base_dir: &Path,
    browser: &str
) -> Result<Vec<BrowserProfile>, String> {
    let mut profiles = Vec::new();

    // Check for Default profile
    let default_dir = base_dir.join("Default");
    if default_dir.exists() && is_valid_profile_dir(&default_dir) {
        profiles.push(BrowserProfile {
            name: format!("{} - Default (System)", browser),
            path: default_dir,
            browser: browser.to_string(),
            is_default: true,
            is_agent_managed: false,
        });
    }

    // Check for Profile 1, Profile 2, etc.
    if let Ok(entries) = std::fs::read_dir(base_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                    if name.starts_with("Profile ") && is_valid_profile_dir(&path) {
                        profiles.push(BrowserProfile {
                            name: format!("{} - {} (System)", browser, name),
                            path,
                            browser: browser.to_string(),
                            is_default: false,
                            is_agent_managed: false,
                        });
                    }
                }
            }
        }
    }

    Ok(profiles)
}

fn is_valid_profile_dir(path: &Path) -> bool {
    // Check for common profile files
    path.join("Preferences").exists() ||
    path.join("Cookies").exists() ||
    path.join("Local State").exists()
}
```

---

### Phase 4: Documentation (Priority 4)

**Estimated Time:** 1-2 hours

#### 4.1 Create Chrome Enterprise Installation Guide

**File: `docs/CHROME_ENTERPRISE_INSTALL.md`**

(Content as specified in previous plan)

#### 4.2 Update README.md

**File: `README.md`**

Add sections:
- Browser Configuration
- Windows Corporate Deployment
- Profile Management

---

## Testing Strategy

### Unit Tests

1. **Config Tests:**
   - Default browser channel by platform
   - Default profiles directory by platform
   - Config serialization/deserialization

2. **Profile Discovery Tests:**
   - Windows Edge profile enumeration
   - Windows Chrome profile enumeration
   - Agent profile listing

### Integration Tests

1. **Windows Environment:**
   - Edge launches successfully with channel="msedge"
   - Chrome launches with channel="chrome"
   - Chromium launches with channel="chromium"
   - Auto-detect selects Edge on Windows

2. **Profile Management:**
   - Create agent profile in profiles_dir
   - Session reuse with agent profile
   - Clone profile for parallel execution

3. **Installation:**
   - SETUP.ps1 finds UV in .local\bin
   - SETUP.ps1 finds UV in .cargo\bin
   - SETUP.ps1 installs UV if missing
   - Only Chromium installed, no Chrome

### End-to-End Tests

1. **Fresh Windows Installation:**
   - Install on Windows 11 without admin rights
   - Run SETUP.ps1
   - Configure Edge as browser
   - Run example test script
   - Verify recording uploaded to S3

2. **Corporate Windows Environment:**
   - No local admin rights
   - Edge pre-installed
   - Environment variable credentials
   - Run Activity worker

---

## Success Criteria

### Must Have (Phase 1):
- ✅ No hardcoded "Bt_broadband" references in code
- ✅ browser_channel configuration working
- ✅ Edge launches successfully on Windows
- ✅ SETUP.ps1 robust UV detection
- ✅ Only Chromium installed by setup

### Should Have (Phase 2-3):
- ✅ profiles_dir configuration
- ✅ Agent-managed profiles created correctly
- ✅ Windows profile enumeration for Edge and Chrome
- ✅ UI controls for browser_channel and profiles_dir

### Nice to Have (Phase 4):
- ✅ Comprehensive documentation
- ✅ Chrome Enterprise install guide
- ✅ Updated examples

---

## Risk Mitigation

### Risk: Nova Act doesn't support browser_channel parameter

**Mitigation:**
- Playwright supports `channel` parameter per documentation
- Nova Act uses Playwright internally
- If not exposed, we can use `executable_path` parameter
- Test with Edge first, fall back to explicit path if needed

**Fallback Implementation:**
```python
# If Nova Act doesn't support channel directly:
if browser_channel == "msedge":
    # Find Edge executable
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in edge_paths:
        if os.path.exists(path):
            executable_path = path
            break
```

### Risk: Edge behaves differently than Chrome

**Mitigation:**
- Both use Chromium engine
- Playwright abstracts differences
- Test suite validates behavior parity
- Document any known differences

### Risk: Breaking existing deployments

**Mitigation:**
- Backwards compatible: existing configs still work
- Default to previous behavior if browser_channel not set
- Migration guide for existing users
- Version bump to 0.2.0 signals changes

---

## Rollout Plan

### Version 0.2.0 Release

**Tag:** `browser-agent-v0.2.0`

**Release Notes:**
```markdown
## Local Browser Agent v0.2.0 - Windows Corporate Ready

### 🎯 Major Changes

- **Windows Corporate Support**: Uses Microsoft Edge by default (pre-installed on Windows 10/11)
- **Browser Flexibility**: Configure browser channel (Edge, Chrome, Chromium) via UI
- **No More Demo Hardcoding**: Removed forced "Bt_broadband" profile
- **Safe Profile Management**: Agent profiles isolated from user's personal browser
- **Improved Installation**: Robust UV detection, minimal browser installation

### ✨ New Features

- `browser_channel` configuration (auto-detect, msedge, chrome, chromium)
- `profiles_dir` configuration for agent-managed profiles
- Windows Edge and Chrome profile enumeration
- Platform-specific defaults (Edge on Windows, Chrome on Mac/Linux)

### 🔧 Improvements

- SETUP.ps1: Enhanced UV detection (.local\bin, .cargo\bin, PATH)
- SETUP scripts: Install only Chromium (no Chrome by default)
- Better error messages and setup feedback
- Updated documentation for Windows corporate environments

### 🐛 Bug Fixes

- Fixed hardcoded profile forcing
- Fixed UV path detection after installation
- Fixed profile corruption risk

### ⚠️ Breaking Changes

None - all changes are backwards compatible.

### 📚 Documentation

- New: Chrome Enterprise Installation Guide
- Updated: README with browser configuration
- Updated: Example configurations

### 🧪 Testing

Tested on:
- ✅ Windows 11 (Edge, Chrome, Chromium)
- ✅ macOS Sonoma (Chrome, Chromium)
- ✅ Ubuntu 22.04 (Chrome, Chromium)
```

---

## Implementation Checklist

### Phase 1: Critical Fixes
- [ ] Remove "Bt_broadband" from nova_act_wrapper.py
- [ ] Remove "Bt_broadband" from script_executor.py
- [ ] Add browser_channel to config.rs
- [ ] Add platform defaults for browser_channel
- [ ] Pass browser_channel to Python scripts
- [ ] Support browser_channel in nova_act_wrapper.py
- [ ] Support browser_channel in script_executor.py
- [ ] Update SETUP.ps1 UV detection
- [ ] Update SETUP scripts to Chromium-only
- [ ] Test on Windows with Edge
- [ ] Test on Windows with Chrome
- [ ] Test on Windows with Chromium

### Phase 2: Configuration
- [ ] Add profiles_dir to config.rs
- [ ] Add profiles_dir defaults by platform
- [ ] Update profile_manager.py for OS defaults
- [ ] Wire browser_channel to UI
- [ ] Wire profiles_dir to UI
- [ ] Update config.example.yaml
- [ ] Test configuration save/load

### Phase 3: Profile Management
- [ ] Implement Windows Edge profile discovery
- [ ] Implement Windows Chrome profile discovery
- [ ] Update UI to show browser profiles
- [ ] Test agent profile creation
- [ ] Test profile isolation

### Phase 4: Documentation
- [ ] Create CHROME_ENTERPRISE_INSTALL.md
- [ ] Update README.md
- [ ] Update example configurations
- [ ] Create migration guide
- [ ] Write release notes

### Final
- [ ] Complete end-to-end testing
- [ ] Tag browser-agent-v0.2.0
- [ ] Build and publish release

---

## Appendix: Playwright Browser Channel Reference

From https://playwright.dev/python/docs/browsers#google-chrome--microsoft-edge:

```python
# Google Chrome
browser = playwright.chromium.launch(channel="chrome")

# Microsoft Edge
browser = playwright.chromium.launch(channel="msedge")

# Beta/Dev/Canary channels
browser = playwright.chromium.launch(channel="chrome-beta")
browser = playwright.chromium.launch(channel="msedge-beta")
browser = playwright.chromium.launch(channel="msedge-dev")
```

Supported channels:
- `chrome` - Google Chrome (stable)
- `chrome-beta` - Google Chrome Beta
- `chrome-dev` - Google Chrome Dev
- `chrome-canary` - Google Chrome Canary
- `msedge` - Microsoft Edge (stable)
- `msedge-beta` - Microsoft Edge Beta
- `msedge-dev` - Microsoft Edge Dev
- `msedge-canary` - Microsoft Edge Canary

---

**Document Status:** Ready for Implementation
**Next Step:** Begin Phase 1 Implementation
