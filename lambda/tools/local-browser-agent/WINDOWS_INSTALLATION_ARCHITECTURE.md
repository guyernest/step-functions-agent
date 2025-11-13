# Windows Installation Architecture

## Overview

This document describes the proper Windows installation architecture following Microsoft best practices to avoid permission issues during installation and runtime on enterprise machines.

## Current Issues

### Problem 1: Python Environment in Program Files
**Current Behavior**: Python virtual environments (`.venv`) are created inside the application directory under `Program Files`:
```
C:\Program Files\Local Browser Agent\python\.venv\
```

**Issue**: This requires write permissions at runtime for:
- Creating `.venv` directory
- Installing/updating Python packages
- Writing cache files and logs
- Modifying environment files

**Result**: Fails on locked-down enterprise machines or non-admin users.

### Problem 2: Config Files in LOCALAPPDATA
**Current Behavior**: Config files are stored in:
```
C:\Users\<user>\AppData\Local\Local Browser Agent\config.yaml
```

**Issue**: This is correct for per-user config, but mixes with other runtime data without clear separation.

### Problem 3: No Machine-Wide Config Support
**Issue**: No support for IT-deployed machine-wide configuration in `%PROGRAMDATA%`.

## Solution: Per-Machine Admin Installation Pattern

### Installation Structure (Requires Admin)

Following Windows best practices, we implement a clean separation:

#### 1. Read-Only Program Files (Installed by MSI, elevated)
```
C:\Program Files\YourVendor\Local Browser Agent\
├── Local Browser Agent.exe        # Main application binary
├── frontend\                       # React UI build artifacts (read-only)
├── runtime\                        # Bundled runtimes (read-only)
│   └── python\                     # Python scripts (read-only)
│       ├── script_executor.py
│       ├── requirements.txt
│       └── ... (other Python files)
└── examples\                       # Example scripts (read-only)
```

**Key Points**:
- All files here are **read-only** at runtime
- No `.venv` directories here
- No package installation here
- No log files here
- Written ONLY during MSI install (elevated)

#### 2. Per-User Writable Data (Created at First Run)

**User Configuration** (`%APPDATA%` - roaming):
```
C:\Users\<user>\AppData\Roaming\YourVendor\Local Browser Agent\
└── config.yaml                     # Per-user configuration overrides
```

**User Runtime Data** (`%LOCALAPPDATA%` - local only):
```
C:\Users\<user>\AppData\Local\YourVendor\Local Browser Agent\
├── python-envs\                    # Python virtual environments
│   ├── main\.venv\                 # Main venv for script execution
│   │   ├── Scripts\                # (Windows: Scripts, Unix: bin)
│   │   │   ├── python.exe
│   │   │   ├── activate.bat
│   │   │   └── ... (installed packages)
│   │   └── pyvenv.cfg
│   └── uv-cache\                   # UV package manager cache
├── browser-profiles\               # Browser profiles (if managed here)
│   ├── BT_wholesale\
│   └── ...
├── recordings\                     # Local video recordings
│   └── *.webm
└── logs\                           # Application logs
    ├── app.log
    └── python-setup.log
```

**Key Points**:
- Created automatically on first run by the **user** (not installer)
- User has full read/write permissions
- No admin required
- Survives app reinstalls/upgrades

#### 3. Machine-Wide Config (Optional, for IT Deployment)

**Machine Configuration** (`%PROGRAMDATA%` - all users):
```
C:\ProgramData\YourVendor\Local Browser Agent\
└── machine-config.yaml             # Optional machine-wide defaults
```

**Key Points**:
- Created by MSI installer (elevated) if needed
- Sets ACLs: Users=Read, Administrators=Modify
- App reads this first, then overlays user config
- Allows IT to deploy org-wide settings

## Implementation Plan

### Phase 1: Path Detection Module

Create a new Rust module `paths.rs` for Windows-aware path detection:

```rust
use std::path::PathBuf;
use anyhow::{Context, Result};

/// Windows installation paths following Microsoft best practices
pub struct AppPaths {
    /// Program Files: C:\Program Files\YourVendor\Local Browser Agent
    /// Read-only binaries and resources
    pub install_dir: PathBuf,

    /// APPDATA: C:\Users\<user>\AppData\Roaming\YourVendor\Local Browser Agent
    /// Roaming user config (follows user across machines)
    pub user_config_dir: PathBuf,

    /// LOCALAPPDATA: C:\Users\<user>\AppData\Local\YourVendor\Local Browser Agent
    /// Local user data (machine-specific, caches, envs)
    pub user_data_dir: PathBuf,

    /// PROGRAMDATA: C:\ProgramData\YourVendor\Local Browser Agent
    /// Machine-wide config (optional, for IT deployment)
    pub machine_config_dir: PathBuf,
}

impl AppPaths {
    pub fn new() -> Result<Self> {
        #[cfg(target_os = "windows")]
        {
            Self::windows_paths()
        }

        #[cfg(target_os = "macos")]
        {
            Self::macos_paths()
        }

        #[cfg(target_os = "linux")]
        {
            Self::linux_paths()
        }
    }

    #[cfg(target_os = "windows")]
    fn windows_paths() -> Result<Self> {
        use dirs::{config_dir, data_local_dir};
        use std::env;

        // Get install directory from exe location
        let exe_path = env::current_exe()
            .context("Failed to get executable path")?;
        let install_dir = exe_path.parent()
            .context("Failed to get install directory")?
            .to_path_buf();

        // APPDATA roaming (config that follows user)
        let user_config_dir = config_dir()
            .context("Failed to get APPDATA directory")?
            .join("YourVendor")
            .join("Local Browser Agent");

        // LOCALAPPDATA (machine-specific user data)
        let user_data_dir = data_local_dir()
            .context("Failed to get LOCALAPPDATA directory")?
            .join("YourVendor")
            .join("Local Browser Agent");

        // PROGRAMDATA (machine-wide config)
        let machine_config_dir = PathBuf::from(
            env::var("PROGRAMDATA")
                .context("PROGRAMDATA environment variable not set")?
        )
        .join("YourVendor")
        .join("Local Browser Agent");

        Ok(AppPaths {
            install_dir,
            user_config_dir,
            user_data_dir,
            machine_config_dir,
        })
    }

    /// Get Python environment directory (in LOCALAPPDATA)
    pub fn python_env_dir(&self) -> PathBuf {
        self.user_data_dir.join("python-envs").join("main")
    }

    /// Get UV cache directory (in LOCALAPPDATA)
    pub fn uv_cache_dir(&self) -> PathBuf {
        self.user_data_dir.join("python-envs").join("uv-cache")
    }

    /// Get Python scripts directory (read-only in Program Files)
    pub fn python_scripts_dir(&self) -> PathBuf {
        #[cfg(target_os = "windows")]
        {
            self.install_dir.join("runtime").join("python")
        }

        #[cfg(target_os = "macos")]
        {
            self.install_dir
                .join("Contents")
                .join("Resources")
                .join("_up_")
                .join("python")
        }

        #[cfg(target_os = "linux")]
        {
            self.install_dir.join("python")
        }
    }

    /// Get recordings directory (in LOCALAPPDATA)
    pub fn recordings_dir(&self) -> PathBuf {
        self.user_data_dir.join("recordings")
    }

    /// Get logs directory (in LOCALAPPDATA)
    pub fn logs_dir(&self) -> PathBuf {
        self.user_data_dir.join("logs")
    }

    /// Get browser profiles directory (in LOCALAPPDATA)
    pub fn browser_profiles_dir(&self) -> PathBuf {
        self.user_data_dir.join("browser-profiles")
    }

    /// Create all necessary user directories
    pub fn ensure_user_dirs_exist(&self) -> Result<()> {
        let dirs = vec![
            &self.user_config_dir,
            &self.user_data_dir,
            self.python_env_dir(),
            self.uv_cache_dir(),
            self.recordings_dir(),
            self.logs_dir(),
            self.browser_profiles_dir(),
        ];

        for dir in dirs {
            if !dir.exists() {
                std::fs::create_dir_all(&dir)
                    .context(format!("Failed to create directory: {}", dir.display()))?;
            }
        }

        Ok(())
    }
}
```

### Phase 2: Update Python Environment Setup

Modify `config_commands.rs::setup_python_environment()`:

```rust
pub async fn setup_python_environment() -> Result<SetupResult, String> {
    let paths = AppPaths::new()
        .map_err(|e| format!("Failed to initialize paths: {}", e))?;

    // Ensure all user directories exist
    paths.ensure_user_dirs_exist()
        .map_err(|e| format!("Failed to create user directories: {}", e))?;

    // Get read-only Python scripts from Program Files
    let python_scripts_dir = paths.python_scripts_dir();

    // Get writable venv location in LOCALAPPDATA
    let venv_dir = paths.python_env_dir();
    let uv_cache = paths.uv_cache_dir();

    // Find or install UV (user's home .cargo/bin or .local/bin)
    let uv_command = find_or_install_uv()?;

    // Create venv in LOCALAPPDATA, not Program Files
    Command::new(&uv_command)
        .arg("venv")
        .arg("--python")
        .arg("3.11")
        .arg(&venv_dir)  // Full path to venv in LOCALAPPDATA
        .env("UV_CACHE_DIR", &uv_cache)  // Set UV cache to LOCALAPPDATA
        .output()?;

    // Install packages using requirements.txt from Program Files
    let requirements_txt = python_scripts_dir.join("requirements.txt");
    let venv_python = if cfg!(windows) {
        venv_dir.join("Scripts").join("python.exe")
    } else {
        venv_dir.join("bin").join("python")
    };

    Command::new(&uv_command)
        .arg("pip")
        .arg("install")
        .arg("--python")
        .arg(&venv_python)
        .arg("-r")
        .arg(&requirements_txt)
        .env("UV_CACHE_DIR", &uv_cache)
        .output()?;

    Ok(SetupResult { success: true, ... })
}
```

### Phase 3: Update Config File Handling

Modify `config.rs::Config`:

```rust
impl Config {
    /// Load configuration with proper precedence:
    /// 1. Machine-wide config (PROGRAMDATA) - if exists
    /// 2. User config (APPDATA) - overlays machine config
    pub fn load() -> Result<Self> {
        let paths = AppPaths::new()?;

        // Start with default
        let mut config = Config::default_minimal();

        // Load machine-wide config if exists (IT deployment)
        let machine_config = paths.machine_config_dir.join("machine-config.yaml");
        if machine_config.exists() {
            let machine = Config::from_file(&machine_config)?;
            config.merge(machine);  // Merge machine defaults
        }

        // Load/overlay user config
        let user_config = paths.user_config_dir.join("config.yaml");
        if user_config.exists() {
            let user = Config::from_file(&user_config)?;
            config.merge(user);  // User overrides machine
        }

        Ok(config)
    }

    /// Save user configuration to APPDATA
    pub fn save(&self) -> Result<()> {
        let paths = AppPaths::new()?;
        paths.ensure_user_dirs_exist()?;

        let user_config = paths.user_config_dir.join("config.yaml");
        self.save_to_file(&user_config)
    }
}
```

### Phase 4: Update Tauri Bundle Configuration

Modify `tauri.conf.json`:

```json
{
  "tauri": {
    "bundle": {
      "windows": {
        "wix": {
          "language": "en-US",
          "install_mode": "perMachine",
          "install_scope": "machine",
          "install_location": "ProgramFiles"
        }
      },
      "resources": [
        "../python",
        "../examples"
      ]
    }
  }
}
```

### Phase 5: Update Nova Act Executor

Modify Python script execution to use new paths:

```rust
impl NovaActExecutor {
    pub async fn execute(&self, script: &BrowserScript) -> Result<ScriptResult> {
        let paths = AppPaths::new()?;

        // Read-only Python scripts from Program Files
        let python_scripts_dir = paths.python_scripts_dir();
        let script_executor = python_scripts_dir.join("script_executor.py");

        // Writable venv from LOCALAPPDATA
        let venv_python = if cfg!(windows) {
            paths.python_env_dir().join("Scripts").join("python.exe")
        } else {
            paths.python_env_dir().join("bin").join("python")
        };

        // Recordings go to LOCALAPPDATA
        let recordings_dir = paths.recordings_dir();

        Command::new(&venv_python)
            .arg(&script_executor)
            .arg("--script")
            .arg(&script_json)
            .arg("--recordings-dir")
            .arg(&recordings_dir)
            .env("PYTHONPATH", &python_scripts_dir)
            .output()?;
    }
}
```

## Installation Flow

**Note**: This architecture is designed for new installations only.

Clean installation:
1. MSI installs binaries to Program Files (admin, one-time)
2. First app launch creates user directories (no admin)
3. Python environment setup uses LOCALAPPDATA
4. No permission errors

## Benefits

1. **No Runtime Permission Issues**: All writable operations use LOCALAPPDATA
2. **Follows Windows Best Practices**: Proper use of special folders
3. **IT-Friendly**: Supports PROGRAMDATA for org-wide config
4. **Multi-User**: Each user gets their own environments and config
5. **Enterprise-Ready**: Works on locked-down corporate machines
6. **Simple Installation**: Clean architecture, no migration complexity

## Testing Checklist

- [ ] Install MSI with admin rights
- [ ] Launch app as standard user (no admin)
- [ ] Setup Python environment (should succeed)
- [ ] Create browser profile (should succeed)
- [ ] Execute browser script (should succeed)
- [ ] Verify all files are in correct locations:
  - [ ] Binaries in Program Files (read-only)
  - [ ] Config in APPDATA (read-write)
  - [ ] Python venv in LOCALAPPDATA (read-write)
  - [ ] Recordings in LOCALAPPDATA (read-write)
- [ ] Test on locked-down enterprise VM
- [ ] Test with PROGRAMDATA machine config (optional)

## References

- [Windows Installer Best Practices](https://learn.microsoft.com/en-us/windows/win32/msi/windows-installer-best-practices)
- [Known Folders (SHGetKnownFolderPath)](https://learn.microsoft.com/en-us/windows/win32/shell/known-folders)
- [Application Data Locations](https://learn.microsoft.com/en-us/windows/apps/design/app-settings/store-and-retrieve-app-data)
