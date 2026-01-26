# Local Browser Agent - Patch Update

This directory contains scripts to update the Python executor without requiring a full reinstall.

## Quick Update

### Option 1: Double-click (Easiest)
1. Double-click `patch-update.bat`
2. Follow the prompts

### Option 2: PowerShell
```powershell
.\patch-python-executor.ps1
```

### Option 3: With custom install path
```powershell
.\patch-python-executor.ps1 -InstallPath "D:\CustomPath\Local Browser Agent"
```

## What Gets Updated

The patch downloads and updates these Python files from GitHub:

| File | Description |
|------|-------------|
| `openai_playwright_executor.py` | Main browser automation executor |
| `browser_launch_config.py` | Browser launch configuration |
| `workflow_executor.py` | Workflow control flow engine |
| `condition_evaluator.py` | Condition evaluation logic |
| `profile_manager.py` | Browser profile management |
| `progressive_escalation_engine.py` | Progressive escalation strategies |

## Features

- **Automatic backups**: All existing files are backed up before replacement
- **Version detection**: Shows current and new file versions
- **Skip unchanged**: Files that haven't changed are not replaced
- **Dry run mode**: Preview changes without applying them
- **Rollback support**: Restore from backups if needed

## Command Line Options

```powershell
.\patch-python-executor.ps1 [-InstallPath <path>] [-Branch <branch>] [-DryRun] [-Force]
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-InstallPath` | Installation directory | `%LOCALAPPDATA%\Local Browser Agent` |
| `-Branch` | GitHub branch to download from | `main` |
| `-DryRun` | Show what would be done without making changes | Off |
| `-Force` | Skip confirmation prompts | Off |

## Examples

### Preview changes without applying
```powershell
.\patch-python-executor.ps1 -DryRun
```

### Update from a specific branch
```powershell
.\patch-python-executor.ps1 -Branch "feature/new-actions"
```

### Silent update (no prompts)
```powershell
.\patch-python-executor.ps1 -Force
```

## Backups

Backups are saved to:
```
%LOCALAPPDATA%\Local Browser Agent\backups\
```

Each backup file includes a timestamp:
```
openai_playwright_executor.py.backup_20240126_143022
```

### Restoring from backup

1. Navigate to the backups folder
2. Find the backup file you want to restore
3. Copy it back to the `python` folder
4. Remove the `.backup_TIMESTAMP` suffix

## Troubleshooting

### "Cannot reach GitHub"
- Check your internet connection
- Check if GitHub is accessible from your network
- Try again later if GitHub is experiencing issues

### "Installation not found"
- Verify the install path is correct
- Use `-InstallPath` to specify the correct location

### "Access denied" errors
- Run the script as Administrator
- Right-click `patch-update.bat` → "Run as administrator"

### Rollback after failed update
1. Go to `%LOCALAPPDATA%\Local Browser Agent\backups\`
2. Copy the most recent backup files back to `python\`
3. Remove the `.backup_TIMESTAMP` suffix from filenames

## Version History

### v1.0.0 (2024-01-26)
- Initial patch system release
- Added `wait_for_selector` action
- Added `extract_dom` action
- Improved password page wait timing
- Added more login button strategies
- Fixed `ignore_https_errors` for non-persistent contexts
