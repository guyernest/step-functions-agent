# Local Browser Agent - Path & Configuration Architecture Analysis

## Executive Summary

**Critical Issues Found:**
1. Browser channel defaulting to Chrome instead of Edge on Windows
2. Wrong S3 bucket name in configuration
3. Inconsistent path management (config, profiles, Python venv)
4. Insufficient path logging (relative paths, no full paths)
5. Configuration not being properly initialized with defaults

---

## Problem 1: Browser Channel Selection Failure

### The Issue

**Log Evidence:**
```
2025-11-11 19:55:55,328 - WARNING - The Nova Act SDK is unable to run with `chrome_channel='chrome'`
and is falling back to 'chromium'.
```

**Expected Behavior:**
- Windows → Use `msedge` (Microsoft Edge)
- macOS/Linux → Use `chrome` (Google Chrome)

**Actual Behavior:**
- Windows → Trying to use `chrome`, falling back to `chromium`
- Profile `bt_wholesale` is configured for Edge
- Chromium doesn't have the saved credentials → Login fails

### Root Cause

The Rust code HAS the correct platform detection:

```rust
// src-tauri/src/config.rs:51-58
fn default_browser_channel() -> Option<String> {
    #[cfg(target_os = "windows")]
    return Some("msedge".to_string());  // ✅ CORRECT DEFAULT

    #[cfg(not(target_os = "windows"))]
    return Some("chrome".to_string());
}
```

**BUT** the user's config file at `C:\Users\nikos\.local-browser-agent\config.yaml` likely has:
```yaml
browser_channel: chrome  # ❌ WRONG - Overrides the default!
```

### Why This Happened

When the config file is created/saved for the first time, it might be serializing ALL fields including the default, or the user selected Chrome in the UI dropdown.

### The Fix

**Option A: Don't serialize default values**
```rust
// Only write browser_channel to config if it's explicitly set by user
// Let defaults come from code, not config file

#[serde(skip_serializing_if = "Option::is_none")]
pub browser_channel: Option<String>,
```

**Option B: Reset to default on platform mismatch**
```rust
// On Windows, if config has "chrome", reset to "msedge"
if cfg!(target_os = "windows") && config.browser_channel == Some("chrome".to_string()) {
    log::warn!("Config has 'chrome' on Windows, resetting to 'msedge'");
    config.browser_channel = Some("msedge".to_string());
}
```

**Option C: Make it obvious in UI**
```typescript
// UI shows: "Browser: Edge (default for Windows)" instead of just "Edge"
// And warns if user selects Chrome on Windows
```

---

## Problem 2: Wrong S3 Bucket Name

### The Issue

**Log Evidence:**
```
Warning: Failed to initialize S3Writer: Insufficient permissions to perform 'HeadBucket'
on S3 resource 'nova-act-browser-results-prod-923154134542'
```

**Expected Bucket:**
```
browser-agent-recordings-prod-923154134542
```

**Actual Bucket in Config:**
```
nova-act-browser-results-prod-923154134542
```

### Root Cause

The config file has an old/wrong bucket name. This bucket either:
1. Doesn't exist
2. Exists but user doesn't have permissions
3. Is from an old deployment

### The Fix

**Update config file:**
```yaml
# C:\Users\nikos\.local-browser-agent\config.yaml
s3_bucket: "browser-agent-recordings-prod-923154134542"  # Correct bucket
```

**Better: Auto-detect from CDK outputs**
```rust
// Fetch bucket name from SSM Parameter Store or CDK outputs
// Don't rely on manual configuration
```

---

## Problem 3: Path Management Chaos

### Current State (Inconsistent)

| Resource | Location | Relative/Absolute | Issue |
|----------|----------|-------------------|-------|
| **Config File** | `C:\Users\nikos\.local-browser-agent\config.yaml` | Absolute | ✅ Good |
| **Python Venv** | `C:\Program Files\Local Browser Agent\_up_\python\.venv\` | Absolute | ⚠️ Weird path `_up_` |
| **Browser Profiles** | `browser-profiles\bt_wholesale` | **RELATIVE** | ❌ **Where is this?** |
| **Nova Act Logs** | `C:\Users\nikos\AppData\Local\Temp\tmpl27i48g7_nova_act_logs\` | Absolute | ✅ Good (temp) |
| **Python Scripts** | `C:\Program Files\Local Browser Agent\_up_\python\` | Absolute | ⚠️ `_up_` unclear |

### The Problem

**Browser Profiles Path is Relative:**
```
Python:   - Profile Path: browser-profiles\bt_wholesale
```

**Questions:**
- Relative to what? Current working directory? App directory? User home?
- What if the app is launched from different directories?
- How do we debug when profile isn't found?

### Log Evidence of Path Confusion

```
[2025-11-11T19:54:09Z INFO] Looking for Python scripts at: C:\Program Files\Local Browser Agent\_up_\python
[2025-11-11T19:56:42Z INFO] Python:   - Profile Path: browser-profiles\bt_wholesale
```

First path is absolute (`C:\Program Files\...`), second is relative (`browser-profiles\...`).

**Users can't tell:**
- Where the profile actually is
- Why it might not be found
- How to fix it if it's in the wrong place

---

## Problem 4: Insufficient Logging

### Current Logs (Inadequate)

```
✓ Found at: C:\Program Files\Local Browser Agent\_up_\python
Profile Path: browser-profiles\bt_wholesale  ← RELATIVE, NO CONTEXT
```

### What We Need

```
✓ Found Python at: C:\Program Files\Local Browser Agent\_up_\python
✓ Resolved profile 'bt_wholesale' by tags: ['btwholesale.com', 'authenticated']
✓ Profile directory: C:\Users\nikos\.local-browser-agent\profiles\bt_wholesale  ← ABSOLUTE
✓ Profile data dir: C:\Users\nikos\.local-browser-agent\profiles\bt_wholesale\UserData
✓ Config file: C:\Users\nikos\.local-browser-agent\config.yaml
✓ Python venv: C:\Program Files\Local Browser Agent\_up_\python\.venv
```

**Key Principles:**
1. **Always log absolute paths** - No guessing required
2. **Show resolution steps** - How did we get from tag → profile → path?
3. **Include existence checks** - Does the path actually exist?
4. **Use consistent prefix** - `✓` for found, `✗` for missing, `→` for derived

---

## Proposed Unified Path Architecture

### Design Principles

1. **User Data Isolation** - All user-specific data in `~/.local-browser-agent/`
2. **App Resources Isolation** - All app resources in app installation directory
3. **Absolute Paths Always** - Never use relative paths in logs or storage
4. **Consistent Structure** - Same layout on Windows, macOS, Linux
5. **Self-Documenting** - Path names make purpose obvious

### Proposed Directory Structure

```
HOME DIRECTORY (~/ or C:\Users\username\)
│
├── .local-browser-agent/                    ← User data directory
│   ├── config.yaml                          ← Main configuration
│   ├── profiles/                            ← Browser profiles
│   │   ├── bt_wholesale/                    ← Profile definition
│   │   │   ├── profile.yaml                 ← Profile metadata (name, tags, description)
│   │   │   └── UserData/                    ← Chrome/Edge user data directory
│   │   │       ├── Default/
│   │   │       ├── Cookies
│   │   │       └── ...
│   │   └── openreach/
│   │       ├── profile.yaml
│   │       └── UserData/
│   ├── logs/                                ← Application logs
│   │   ├── agent-2025-11-11.log
│   │   └── activity-poller.log
│   └── cache/                               ← Temporary files
│       └── ...
│
└── AppData/Local/Temp/                      ← System temp
    └── nova_act_logs/                       ← Nova Act session logs

APPLICATION DIRECTORY (C:\Program Files\Local Browser Agent\ or /Applications/)
│
├── Local Browser Agent.exe / .app
├── resources/                               ← App resources (Tauri)
│   └── python/                              ← Python environment
│       ├── .venv/                           ← Python venv
│       ├── nova_act_wrapper.py              ← Python scripts
│       ├── script_executor.py
│       ├── profile_manager.py
│       └── requirements.txt
└── templates/                               ← Browser automation templates (optional)
    └── ...
```

### Path Resolution Rules

1. **Config Path**: Always `~/.local-browser-agent/config.yaml`
2. **Profiles Path**: Always `~/.local-browser-agent/profiles/{profile_name}/`
3. **Profile Data Dir**: Always `~/.local-browser-agent/profiles/{profile_name}/UserData/`
4. **Python Venv**: Always `{APP_DIR}/resources/python/.venv/`
5. **Logs**: Always `~/.local-browser-agent/logs/`

**No Exceptions, No Overrides** (unless explicitly debugging)

---

## Implementation Plan

### Phase 1: Fix Immediate Issues (1 hour)

**1. Browser Channel - Quick Fix**
```rust
// src-tauri/src/config.rs
impl Config {
    pub fn validate_and_fix(&mut self) {
        // Reset browser channel to platform default if misconfigured
        #[cfg(target_os = "windows")]
        {
            if self.browser_channel.as_deref() == Some("chrome")
                || self.browser_channel.as_deref() == Some("chromium") {
                log::warn!("Config has '{}' on Windows, resetting to 'msedge'",
                    self.browser_channel.as_ref().unwrap());
                self.browser_channel = Some("msedge".to_string());
            }
        }

        #[cfg(not(target_os = "windows"))]
        {
            if self.browser_channel.as_deref() == Some("msedge") {
                log::warn!("Config has 'msedge' on non-Windows, resetting to 'chrome'");
                self.browser_channel = Some("chrome".to_string());
            }
        }
    }
}
```

**2. S3 Bucket - Update User Config**
```bash
# Manual fix for now
# Edit C:\Users\nikos\.local-browser-agent\config.yaml
s3_bucket: "browser-agent-recordings-prod-923154134542"
```

**3. Profile Path Logging - Immediate Improvement**
```python
# lambda/tools/local-browser-agent/python/script_executor.py

# BEFORE
print(f"  - Profile Path: {user_data_dir}", file=sys.stderr)

# AFTER
import os
abs_user_data_dir = os.path.abspath(user_data_dir) if user_data_dir else "N/A"
print(f"  - Profile Path: {abs_user_data_dir}", file=sys.stderr)
print(f"  - Profile Exists: {os.path.exists(abs_user_data_dir) if user_data_dir else False}", file=sys.stderr)
```

### Phase 2: Unified Path Management (2-3 hours)

**1. Create PathManager Module**
```rust
// src-tauri/src/path_manager.rs

pub struct PathManager {
    home_dir: PathBuf,
    app_dir: PathBuf,
}

impl PathManager {
    pub fn new() -> Result<Self> {
        let home_dir = Self::get_home_dir()?;
        let app_dir = Self::get_app_dir()?;

        Ok(PathManager { home_dir, app_dir })
    }

    /// Get user data directory: ~/.local-browser-agent/
    pub fn user_data_dir(&self) -> PathBuf {
        self.home_dir.join(".local-browser-agent")
    }

    /// Get config file path: ~/.local-browser-agent/config.yaml
    pub fn config_file(&self) -> PathBuf {
        self.user_data_dir().join("config.yaml")
    }

    /// Get profiles directory: ~/.local-browser-agent/profiles/
    pub fn profiles_dir(&self) -> PathBuf {
        self.user_data_dir().join("profiles")
    }

    /// Get specific profile directory: ~/.local-browser-agent/profiles/{name}/
    pub fn profile_dir(&self, name: &str) -> PathBuf {
        self.profiles_dir().join(name)
    }

    /// Get profile user data directory: ~/.local-browser-agent/profiles/{name}/UserData/
    pub fn profile_user_data_dir(&self, name: &str) -> PathBuf {
        self.profile_dir(name).join("UserData")
    }

    /// Get Python resources directory: {app}/resources/python/
    pub fn python_dir(&self) -> PathBuf {
        self.app_dir.join("resources").join("python")
    }

    /// Get Python venv directory: {app}/resources/python/.venv/
    pub fn python_venv_dir(&self) -> PathBuf {
        self.python_dir().join(".venv")
    }

    /// Get logs directory: ~/.local-browser-agent/logs/
    pub fn logs_dir(&self) -> PathBuf {
        self.user_data_dir().join("logs")
    }

    /// Ensure all required directories exist
    pub fn ensure_directories(&self) -> Result<()> {
        std::fs::create_dir_all(self.user_data_dir())?;
        std::fs::create_dir_all(self.profiles_dir())?;
        std::fs::create_dir_all(self.logs_dir())?;
        Ok(())
    }

    /// Log all paths for debugging
    pub fn log_all_paths(&self) {
        log::info!("═══ Path Configuration ═══");
        log::info!("Home Directory: {}", self.home_dir.display());
        log::info!("App Directory: {}", self.app_dir.display());
        log::info!("User Data: {}", self.user_data_dir().display());
        log::info!("Config File: {}", self.config_file().display());
        log::info!("Profiles: {}", self.profiles_dir().display());
        log::info!("Python: {}", self.python_dir().display());
        log::info!("Python Venv: {}", self.python_venv_dir().display());
        log::info!("Logs: {}", self.logs_dir().display());
        log::info!("═══════════════════════════");
    }
}
```

**2. Update ProfileManager to use absolute paths**
```python
# lambda/tools/local-browser-agent/python/profile_manager.py

class ProfileManager:
    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir:
            self.profiles_dir = os.path.abspath(profiles_dir)
        else:
            # Default: ~/.local-browser-agent/profiles/
            home = os.path.expanduser("~")
            self.profiles_dir = os.path.join(home, ".local-browser-agent", "profiles")

        # Ensure directory exists
        os.makedirs(self.profiles_dir, exist_ok=True)

        # Log the absolute path
        print(f"✓ Profile manager initialized", file=sys.stderr)
        print(f"  Profiles directory: {self.profiles_dir}", file=sys.stderr)
        print(f"  Directory exists: {os.path.exists(self.profiles_dir)}", file=sys.stderr)

    def get_profile_path(self, profile_name: str) -> str:
        """Get absolute path to profile directory"""
        return os.path.join(self.profiles_dir, profile_name)

    def get_profile_user_data_dir(self, profile_name: str) -> str:
        """Get absolute path to profile's Chrome UserData directory"""
        return os.path.join(self.get_profile_path(profile_name), "UserData")
```

**3. Enhanced Logging**
```python
# Log profile resolution with full paths
def resolve_profile(self, session_config, verbose=False):
    if verbose:
        print(f"→ Resolving profile...", file=sys.stderr)
        print(f"  Profiles directory: {self.profiles_dir}", file=sys.stderr)
        print(f"  Required tags: {session_config.get('required_tags', [])}", file=sys.stderr)

    profile = self._find_matching_profile(session_config)

    if profile:
        abs_path = self.get_profile_user_data_dir(profile['name'])
        print(f"✓ Resolved profile: '{profile['name']}'", file=sys.stderr)
        print(f"  Profile directory: {self.get_profile_path(profile['name'])}", file=sys.stderr)
        print(f"  User data directory: {abs_path}", file=sys.stderr)
        print(f"  Directory exists: {os.path.exists(abs_path)}", file=sys.stderr)
        print(f"  Matched tags: {profile.get('tags', [])}", file=sys.stderr)
    else:
        print(f"✗ No matching profile found", file=sys.stderr)

    return profile
```

### Phase 3: Documentation & Migration (1-2 hours)

**1. Update all documentation**
- README.md
- GETTING_STARTED.md
- IAM_PERMISSIONS.md

**2. Create migration guide**
```markdown
# Migrating to New Path Structure

## Old Structure (Inconsistent)
- Profiles: Anywhere / Relative paths
- Config: Various locations
- Python: `_up_` directory

## New Structure (Unified)
- Everything in `~/.local-browser-agent/`
- Absolute paths everywhere
- Clear separation of concerns

## Migration Steps
1. Copy old profiles to `~/.local-browser-agent/profiles/`
2. Update config paths
3. Restart application
```

**3. Add startup validation**
```rust
// On startup, validate all paths and log them
let path_manager = PathManager::new()?;
path_manager.ensure_directories()?;
path_manager.log_all_paths();

// Validate config
let mut config = Config::load_or_default()?;
config.validate_and_fix();  // Fix browser channel, etc.
config.save()?;
```

---

## Testing Plan

### Test Case 1: Fresh Windows Install
1. Install app on clean Windows machine
2. Verify `browser_channel` defaults to `msedge`
3. Verify all paths are absolute in logs
4. Verify profiles directory created in home

### Test Case 2: Existing Config Migration
1. Copy old config with `browser_channel: chrome`
2. Start app
3. Verify it auto-corrects to `msedge` on Windows
4. Verify warning is logged

### Test Case 3: Profile Resolution
1. Create profile at `~/.local-browser-agent/profiles/test_profile/`
2. Tag it with `["test.com", "authenticated"]`
3. Run agent with those tags
4. Verify logs show full absolute paths

### Test Case 4: S3 Bucket
1. Configure correct bucket name
2. Verify S3Writer initializes successfully
3. Verify recordings are uploaded

---

## Summary

| Issue | Severity | Fix Complexity | Status |
|-------|----------|----------------|--------|
| Browser channel wrong | HIGH | LOW (config validation) | Phase 1 |
| S3 bucket wrong | HIGH | LOW (config update) | Phase 1 |
| Relative paths in logs | MEDIUM | LOW (add abs paths) | Phase 1 |
| Inconsistent path structure | MEDIUM | MEDIUM (refactor) | Phase 2 |
| No path validation | LOW | LOW (add checks) | Phase 2 |

**Immediate Actions:**
1. Fix `browser_channel` auto-correction (5 minutes)
2. Update user's config with correct S3 bucket (1 minute)
3. Add absolute path logging (10 minutes)

**Next Steps:**
1. Implement PathManager (2 hours)
2. Update ProfileManager (1 hour)
3. Update documentation (1 hour)
4. Test on Windows and macOS (1 hour)
