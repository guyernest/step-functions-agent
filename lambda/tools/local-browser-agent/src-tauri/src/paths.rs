use std::path::PathBuf;
use anyhow::{Context, Result};

/// Application paths following Windows best practices
///
/// This module centralizes all path logic with proper separation between:
/// - Read-only installation files (Program Files)
/// - Writable user data (LOCALAPPDATA)
/// - Roaming user config (APPDATA)
/// - Optional machine-wide config (PROGRAMDATA)
#[derive(Debug, Clone)]
pub struct AppPaths {
    /// Program Files: Installation directory with read-only binaries and resources
    pub install_dir: PathBuf,

    /// APPDATA: Roaming user config (follows user across machines)
    pub user_config_dir: PathBuf,

    /// LOCALAPPDATA: Local user data (machine-specific, caches, envs)
    pub user_data_dir: PathBuf,

    /// PROGRAMDATA: Machine-wide config (optional, for IT deployment)
    pub machine_config_dir: PathBuf,
}

impl AppPaths {
    /// Create new AppPaths using platform-specific conventions
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

    /// Windows paths following Microsoft best practices
    #[cfg(target_os = "windows")]
    fn windows_paths() -> Result<Self> {
        use std::env;

        // Get install directory from executable location
        let exe_path = env::current_exe()
            .context("Failed to get executable path")?;
        let install_dir = exe_path.parent()
            .context("Failed to get install directory")?
            .to_path_buf();

        // Use "Local Browser Agent" for all Windows paths (consistent with existing code)
        let app_name = "Local Browser Agent";

        // APPDATA roaming (config that follows user)
        let user_config_dir = dirs::config_dir()
            .context("Failed to get APPDATA directory")?
            .join(app_name);

        // LOCALAPPDATA (machine-specific user data)
        let user_data_dir = dirs::data_local_dir()
            .context("Failed to get LOCALAPPDATA directory")?
            .join(app_name);

        // PROGRAMDATA (machine-wide config)
        let machine_config_dir = PathBuf::from(
            env::var("PROGRAMDATA")
                .unwrap_or_else(|_| "C:\\ProgramData".to_string())
        )
        .join(app_name);

        Ok(AppPaths {
            install_dir,
            user_config_dir,
            user_data_dir,
            machine_config_dir,
        })
    }

    /// macOS paths following Apple conventions
    #[cfg(target_os = "macos")]
    fn macos_paths() -> Result<Self> {
        use std::env;

        // Get install directory from executable location
        // On macOS: exe is at /Applications/Local Browser Agent.app/Contents/MacOS/Local Browser Agent
        let exe_path = env::current_exe()
            .context("Failed to get executable path")?;

        // Navigate up to the .app bundle
        let install_dir = exe_path.parent()  // Contents/MacOS
            .and_then(|p| p.parent())  // Contents
            .and_then(|p| p.parent())  // Local Browser Agent.app
            .context("Failed to determine app bundle path on macOS")?
            .to_path_buf();

        let app_name = "Local Browser Agent";

        // Use same directory for both config and data on macOS (Application Support)
        let app_support = dirs::data_local_dir()
            .context("Failed to get Application Support directory")?
            .join(app_name);

        Ok(AppPaths {
            install_dir,
            user_config_dir: app_support.clone(),
            user_data_dir: app_support.clone(),
            machine_config_dir: PathBuf::from("/Library/Application Support").join(app_name),
        })
    }

    /// Linux paths following XDG conventions
    #[cfg(target_os = "linux")]
    fn linux_paths() -> Result<Self> {
        use std::env;

        let exe_path = env::current_exe()
            .context("Failed to get executable path")?;
        let install_dir = exe_path.parent()
            .context("Failed to get install directory")?
            .to_path_buf();

        let app_name = "local-browser-agent";

        // XDG_CONFIG_HOME (~/.config)
        let user_config_dir = dirs::config_dir()
            .context("Failed to get XDG_CONFIG_HOME directory")?
            .join(app_name);

        // XDG_DATA_HOME (~/.local/share)
        let user_data_dir = dirs::data_local_dir()
            .context("Failed to get XDG_DATA_HOME directory")?
            .join(app_name);

        // System-wide config
        let machine_config_dir = PathBuf::from("/etc").join(app_name);

        Ok(AppPaths {
            install_dir,
            user_config_dir,
            user_data_dir,
            machine_config_dir,
        })
    }

    /// Get Python environment directory (in LOCALAPPDATA on Windows)
    pub fn python_env_dir(&self) -> PathBuf {
        self.user_data_dir.join("python-envs").join("main")
    }

    /// Get UV cache directory (in LOCALAPPDATA on Windows)
    pub fn uv_cache_dir(&self) -> PathBuf {
        self.user_data_dir.join("python-envs").join("uv-cache")
    }

    /// Get Python scripts directory (read-only in installation directory)
    pub fn python_scripts_dir(&self) -> PathBuf {
        #[cfg(target_os = "windows")]
        {
            // Windows MSI: Tauri bundles resources directly in _up_\python
            // (no "resources" subdirectory for MSI installations)
            let tauri_msi = self.install_dir.join("_up_").join("python");
            if tauri_msi.exists() {
                return tauri_msi;
            }

            // Fallback: install_dir/python (dev mode)
            let python_dir = self.install_dir.join("python");
            if python_dir.exists() {
                return python_dir;
            }

            // Default: return MSI location
            tauri_msi
        }

        #[cfg(target_os = "macos")]
        {
            // macOS: inside .app bundle at Contents/Resources/_up_/python
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

    /// Get examples directory (read-only in installation directory)
    pub fn examples_dir(&self) -> PathBuf {
        #[cfg(target_os = "macos")]
        {
            self.install_dir
                .join("Contents")
                .join("Resources")
                .join("_up_")
                .join("examples")
        }

        #[cfg(target_os = "windows")]
        {
            // Windows MSI: Tauri bundles resources directly in _up_\examples
            let tauri_msi = self.install_dir.join("_up_").join("examples");
            if tauri_msi.exists() {
                return tauri_msi;
            }

            // Fallback: install_dir/examples (dev mode)
            let examples_dir = self.install_dir.join("examples");
            if examples_dir.exists() {
                return examples_dir;
            }

            // Default: return MSI location
            tauri_msi
        }

        #[cfg(target_os = "linux")]
        {
            // Linux: Tauri bundles resources in resources/_up_/examples
            let tauri_resources = self.install_dir.join("resources").join("_up_").join("examples");
            if tauri_resources.exists() {
                return tauri_resources;
            }

            // Fallback: install_dir/examples (dev mode)
            self.install_dir.join("examples")
        }
    }

    /// Get recordings directory (in LOCALAPPDATA on Windows)
    pub fn recordings_dir(&self) -> PathBuf {
        self.user_data_dir.join("recordings")
    }

    /// Get logs directory (in LOCALAPPDATA on Windows)
    pub fn logs_dir(&self) -> PathBuf {
        self.user_data_dir.join("logs")
    }

    /// Get browser profiles directory (in LOCALAPPDATA on Windows)
    pub fn browser_profiles_dir(&self) -> PathBuf {
        self.user_data_dir.join("browser-profiles")
    }

    /// Get user config file path
    pub fn user_config_file(&self) -> PathBuf {
        self.user_config_dir.join("config.yaml")
    }

    /// Get machine config file path (optional, for IT deployments)
    pub fn machine_config_file(&self) -> PathBuf {
        self.machine_config_dir.join("machine-config.yaml")
    }

    /// Create all necessary user directories
    ///
    /// This is safe to call multiple times and will only create directories
    /// that don't exist. Should be called on first run.
    pub fn ensure_user_dirs_exist(&self) -> Result<()> {
        // Store PathBufs before borrowing to avoid temporary lifetime issues
        let python_env = self.python_env_dir();
        let uv_cache = self.uv_cache_dir();
        let recordings = self.recordings_dir();
        let logs = self.logs_dir();
        let profiles = self.browser_profiles_dir();

        let dirs = vec![
            &self.user_config_dir,
            &self.user_data_dir,
            &python_env,
            &uv_cache,
            &recordings,
            &logs,
            &profiles,
        ];

        for dir in dirs {
            if !dir.exists() {
                std::fs::create_dir_all(&dir)
                    .context(format!("Failed to create directory: {}", dir.display()))?;
                log::info!("Created directory: {}", dir.display());
            }
        }

        Ok(())
    }

    /// Log all paths for debugging
    pub fn log_paths(&self) {
        log::info!("═══ Application Paths ═══");
        log::info!("Install Dir:        {}", self.install_dir.display());
        log::info!("User Config Dir:    {}", self.user_config_dir.display());
        log::info!("User Data Dir:      {}", self.user_data_dir.display());
        log::info!("Machine Config Dir: {}", self.machine_config_dir.display());
        log::info!("Python Env:         {}", self.python_env_dir().display());
        log::info!("Python Scripts:     {}", self.python_scripts_dir().display());
        log::info!("UV Cache:           {}", self.uv_cache_dir().display());
        log::info!("Recordings:         {}", self.recordings_dir().display());
        log::info!("Logs:               {}", self.logs_dir().display());
        log::info!("Browser Profiles:   {}", self.browser_profiles_dir().display());
        log::info!("═════════════════════════");
    }
}

/// Get the legacy config directory for backward compatibility
///
/// This returns the old path used before the Windows fix.
/// Used to detect and potentially migrate old installations.
pub fn get_legacy_config_dir() -> Result<PathBuf> {
    #[cfg(target_os = "windows")]
    {
        Ok(dirs::data_local_dir()
            .context("Failed to get LOCALAPPDATA")?
            .join("Local Browser Agent"))
    }

    #[cfg(target_os = "macos")]
    {
        Ok(dirs::data_local_dir()
            .context("Failed to get Application Support")?
            .join("Local Browser Agent"))
    }

    #[cfg(target_os = "linux")]
    {
        Ok(dirs::config_dir()
            .context("Failed to get config directory")?
            .join("local-browser-agent"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_paths_creation() {
        let paths = AppPaths::new().unwrap();

        // Basic sanity checks
        assert!(paths.install_dir.is_absolute());
        assert!(paths.user_config_dir.is_absolute());
        assert!(paths.user_data_dir.is_absolute());

        // Verify subdirectories are properly constructed
        assert!(paths.python_env_dir().ends_with("python-envs/main") ||
                paths.python_env_dir().ends_with("python-envs\\main"));
        assert!(paths.uv_cache_dir().ends_with("python-envs/uv-cache") ||
                paths.uv_cache_dir().ends_with("python-envs\\uv-cache"));
    }

    #[test]
    #[cfg(target_os = "windows")]
    fn test_windows_paths() {
        let paths = AppPaths::new().unwrap();

        // Windows-specific checks
        assert!(paths.user_config_dir.to_str().unwrap().contains("AppData\\Roaming"));
        assert!(paths.user_data_dir.to_str().unwrap().contains("AppData\\Local"));
        assert!(paths.machine_config_dir.to_str().unwrap().contains("ProgramData"));
    }

    #[test]
    fn test_ensure_dirs_no_panic() {
        let paths = AppPaths::new().unwrap();
        // Should not panic, even if it can't create dirs in some test environments
        let _ = paths.ensure_user_dirs_exist();
    }
}
