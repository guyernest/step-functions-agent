# Windows Installation Fix - Implementation Plan

## Executive Summary

We need to fix Windows installation permission issues by following Microsoft best practices for per-machine admin installations. The core issue is that we're currently trying to write Python virtual environments to `Program Files`, which requires admin permissions at runtime and fails on enterprise machines.

## Current Problem

**What's happening**: Python environment setup fails with permission errors on Windows enterprise machines.

**Root cause**: Creating `.venv` and installing packages in:
```
C:\Program Files\Local Browser Agent\python\.venv\  ❌ (requires admin at runtime)
```

**Why it's a problem**:
- Standard users can't write to Program Files
- Enterprise Group Policies often lock down Program Files
- Anti-virus and EDR solutions flag runtime modifications to Program Files
- Goes against Windows logo certification requirements

## Proposed Solution

Follow Windows installer best practices for per-machine installations:

### Installation Layout

**Read-Only Binaries** (Program Files, written during MSI install with admin):
```
C:\Program Files\YourVendor\Local Browser Agent\
├── Local Browser Agent.exe
├── runtime\python\*.py          # Python scripts (read-only)
└── examples\*.json              # Example scripts (read-only)
```

**Writable User Data** (LOCALAPPDATA, created at first run as user):
```
C:\Users\<user>\AppData\Local\YourVendor\Local Browser Agent\
├── python-envs\
│   ├── main\.venv\              # ✅ Virtual environment here
│   └── uv-cache\                # ✅ UV cache here
├── recordings\                  # ✅ Video recordings here
├── logs\                        # ✅ Logs here
└── browser-profiles\            # ✅ Browser profiles here
```

**User Configuration** (APPDATA roaming):
```
C:\Users\<user>\AppData\Roaming\YourVendor\Local Browser Agent\
└── config.yaml                  # ✅ User config here
```

**Machine Configuration** (PROGRAMDATA, optional for IT):
```
C:\ProgramData\YourVendor\Local Browser Agent\
└── machine-config.yaml          # ✅ IT-deployed defaults
```

## Implementation Steps

### Step 1: Create Path Detection Module (`src-tauri/src/paths.rs`)

**Purpose**: Centralize all path logic with Windows-aware detection.

**Key Functions**:
- `AppPaths::new()` - Detect all paths using Windows SHGetKnownFolderPath
- `python_env_dir()` - Returns `%LOCALAPPDATA%\YourVendor\...\python-envs\main`
- `uv_cache_dir()` - Returns `%LOCALAPPDATA%\YourVendor\...\python-envs\uv-cache`
- `python_scripts_dir()` - Returns `C:\Program Files\...\runtime\python` (read-only)
- `ensure_user_dirs_exist()` - Creates LOCALAPPDATA structure at first run

**Dependencies**: Add to `Cargo.toml`:
```toml
[dependencies]
dirs = "5.0"  # Already have this
```

### Step 2: Update Python Environment Setup (`config_commands.rs`)

**Changes to `setup_python_environment()`**:

1. **Use AppPaths** instead of exe_path detection:
```rust
let paths = AppPaths::new()?;
paths.ensure_user_dirs_exist()?;
```

2. **Create venv in LOCALAPPDATA**:
```rust
let venv_dir = paths.python_env_dir();  // LOCALAPPDATA, not Program Files
let python_scripts = paths.python_scripts_dir();  // Read-only source
```

3. **Set UV environment variables**:
```rust
Command::new(&uv_command)
    .arg("venv")
    .arg(&venv_dir)
    .env("UV_CACHE_DIR", paths.uv_cache_dir())  // Cache in LOCALAPPDATA
    .output()?;
```

4. **Install from read-only requirements.txt**:
```rust
let requirements = python_scripts.join("requirements.txt");
Command::new(&uv_command)
    .arg("pip")
    .arg("install")
    .arg("-r")
    .arg(&requirements)  // Read from Program Files
    .env("UV_CACHE_DIR", paths.uv_cache_dir())
    .output()?;
```

### Step 3: Update Config Handling (`config.rs`)

**Add config precedence**:
1. Load machine config from PROGRAMDATA (if exists)
2. Overlay user config from APPDATA
3. User settings override machine defaults

**Changes**:
```rust
impl Config {
    pub fn load() -> Result<Self> {
        let paths = AppPaths::new()?;

        // Try machine config first (IT deployment)
        let mut config = if let Ok(machine) = Self::load_machine_config(&paths) {
            machine
        } else {
            Self::default_minimal()
        };

        // Overlay user config
        if let Ok(user) = Self::load_user_config(&paths) {
            config.merge(user);
        }

        Ok(config)
    }
}
```

### Step 4: Update Nova Act Executor (`nova_act_executor.rs`)

**Use new paths for script execution**:

```rust
pub async fn execute(&self, script: &BrowserScript) -> Result<ScriptResult> {
    let paths = AppPaths::new()?;

    // Python from LOCALAPPDATA venv
    let python_exe = if cfg!(windows) {
        paths.python_env_dir().join("Scripts").join("python.exe")
    } else {
        paths.python_env_dir().join("bin").join("python")
    };

    // Scripts from read-only Program Files
    let script_executor = paths.python_scripts_dir().join("script_executor.py");

    // Recordings to LOCALAPPDATA
    let recordings_dir = paths.recordings_dir();

    Command::new(&python_exe)
        .arg(&script_executor)
        .arg("--recordings-dir")
        .arg(&recordings_dir)
        .env("PYTHONPATH", paths.python_scripts_dir())
        .output()?;
}
```

### Step 5: Update Tauri Bundle Config (`tauri.conf.json`)

**Ensure MSI uses per-machine installation**:

```json
{
  "tauri": {
    "bundle": {
      "windows": {
        "wix": {
          "language": "en-US"
        },
        "certificateThumbprint": null,
        "digestAlgorithm": "sha256",
        "timestampUrl": ""
      }
    }
  }
}
```

Note: Tauri's default is already per-machine for Windows MSI. We just need to ensure our code doesn't assume Program Files is writable.

### Step 6: Update Profile Commands (`profile_commands.rs`)

**Use LOCALAPPDATA for browser profiles**:

```rust
pub fn get_profiles_dir() -> Result<PathBuf> {
    let paths = AppPaths::new()?;
    Ok(paths.browser_profiles_dir())  // LOCALAPPDATA
}
```

## Installation Flow (New Machines Only)

**Note**: This implementation focuses on new installations only. No migration from old versions.

Clean installation experience:
1. Run MSI installer (requires admin, one-time)
2. Launch app (standard user, no admin)
3. Click "Setup Python Environment"
4. Environment created in LOCALAPPDATA automatically
5. No permission errors!

## Testing Plan

### Test Scenarios

1. **Fresh Install on Admin Account**
   - Install MSI as admin
   - Launch as admin
   - Setup Python environment
   - Execute browser script
   - ✅ Should succeed

2. **Fresh Install on Standard User**
   - Install MSI as admin
   - Launch as standard user (NO ADMIN)
   - Setup Python environment
   - Execute browser script
   - ✅ Should succeed (key test!)

3. **Locked-Down Enterprise Machine**
   - Deploy MSI via SCCM/Intune (admin)
   - User has no local admin rights
   - Program Files is read-only via GPO
   - Launch as standard user
   - Setup Python environment
   - ✅ Should succeed (critical test!)

4. **IT-Deployed Machine Config**
   - Create machine config in PROGRAMDATA
   - Install app
   - Launch as standard user
   - ✅ Should load machine config
   - User can override in their config
   - ✅ Should respect user overrides

### Test Matrix

| Scenario | User Rights | Expected Result | Priority |
|----------|-------------|-----------------|----------|
| Fresh install admin | Admin | Success | High |
| Fresh install standard user | Standard | Success | **Critical** |
| Locked-down enterprise | Standard (heavily restricted) | Success | **Critical** |
| Multi-user same machine | Standard (User A & B) | Both succeed independently | Medium |
| IT-deployed config | Standard | Success with machine config | Medium |

## File Changes Summary

### New Files
- `src-tauri/src/paths.rs` - Windows path detection module
- `WINDOWS_INSTALLATION_ARCHITECTURE.md` - Detailed architecture doc
- `WINDOWS_INSTALLATION_IMPLEMENTATION_PLAN.md` - This file

### Modified Files
- `src-tauri/src/main.rs` - Import and use AppPaths
- `src-tauri/src/config.rs` - Config precedence (machine → user)
- `src-tauri/src/config_commands.rs` - Python setup uses LOCALAPPDATA
- `src-tauri/src/nova_act_executor.rs` - Script execution uses new paths
- `src-tauri/src/profile_commands.rs` - Profiles in LOCALAPPDATA
- `src-tauri/Cargo.toml` - Ensure `dirs` crate is listed

### No Changes Required
- `tauri.conf.json` - Already defaults to per-machine MSI
- Python scripts - Stay in `../python/` directory
- Examples - Stay in `../examples/` directory

## Implementation Order

1. ✅ **Create architecture documentation** (completed)
2. **Create `paths.rs` module** with Windows path detection
3. **Update `config_commands.rs`** for Python setup
4. **Update `config.rs`** for config precedence
5. **Update `nova_act_executor.rs`** for script execution
6. **Update `profile_commands.rs`** for profiles
7. **Test on Windows VM** as standard user
8. **Test on locked-down enterprise VM**
9. **Document deployment** for IT admins

## Deployment Notes for IT Admins

### MSI Deployment
```powershell
# Deploy via SCCM/Intune/GPO
msiexec /i "Local Browser Agent.msi" /qn /norestart

# Optional: Deploy machine-wide config
Copy-Item -Path "machine-config.yaml" -Destination "C:\ProgramData\YourVendor\Local Browser Agent\"
```

### Machine Config Example
```yaml
# C:\ProgramData\YourVendor\Local Browser Agent\machine-config.yaml
# IT-deployed defaults (users can override)

aws_profile: "company-browser-agent"
aws_region: "us-east-1"
activity_arn: "arn:aws:states:us-east-1:123456789012:activity:browser-agent-prod"
s3_bucket: "company-browser-recordings-prod"
headless: false
heartbeat_interval: 60

# Users can override any of these in their personal config.yaml
```

## Success Criteria

1. ✅ Install MSI as admin → Launch as standard user → Setup Python → Execute script (all succeed)
2. ✅ No permission errors on enterprise machines
3. ✅ All writable operations use `%LOCALAPPDATA%`
4. ✅ All read-only operations use `Program Files`
5. ✅ Existing users migrate smoothly
6. ✅ Multi-user support (each user gets own env)
7. ✅ IT can deploy machine-wide config

## Next Steps

1. **Review this plan** - Confirm approach before implementation
2. **Create `paths.rs`** - Start with the foundation module
3. **Implement changes** - One file at a time
4. **Test thoroughly** - Especially as standard user on Windows
5. **Update documentation** - Installation guide for end users

## Questions to Resolve

1. **Vendor Name**: Should we use a specific vendor name instead of "YourVendor"?
   - Recommendation: "StepFunctions" or your company name

2. **Machine Config**: Do we need PROGRAMDATA support in v1?
   - Recommendation: Yes, it's simple to add and IT-friendly

## References

- Windows Installer Best Practices: https://learn.microsoft.com/en-us/windows/win32/msi/windows-installer-best-practices
- Known Folders API: https://learn.microsoft.com/en-us/windows/win32/shell/known-folders
- Tauri MSI Configuration: https://tauri.app/v1/guides/building/windows
