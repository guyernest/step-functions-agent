# Multi-Platform Release Process

This document explains how to create releases for both local agents using GitHub Actions.

## Overview

We have two separate agents with independent release cycles:

1. **Local Browser Agent** - Browser automation with Nova Act
2. **Local Agent** - GUI automation with PyAutoGUI

Each agent builds for **macOS (Intel + Apple Silicon), Windows, and Linux** automatically via GitHub Actions.

## Release Process

### 1. Browser Agent Release

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create and push a tag
git tag browser-agent-v0.1.0
git push origin browser-agent-v0.1.0
```

This triggers `.github/workflows/release-browser-agent.yml` which:
- ✅ Builds on macOS (Intel + ARM64), Windows (x64), Linux (x64)
- ✅ Creates DMG, MSI, and DEB installers
- ✅ Bundles Python dependencies (Nova Act, Playwright, boto3)
- ✅ Creates a **draft** GitHub release with all artifacts

### 2. Local Agent Release

```bash
# Create and push a tag
git tag local-agent-v0.2.0
git push origin local-agent-v0.2.0
```

This triggers `.github/workflows/release-local-agent.yml` which:
- ✅ Builds on macOS (Intel + ARM64), Windows (x64), Linux (x64)
- ✅ Creates DMG, MSI, and DEB installers
- ✅ Bundles Python dependencies (PyAutoGUI, OpenCV, Pillow)
- ✅ Creates a **draft** GitHub release with all artifacts

### 3. Review and Publish

1. Go to [GitHub Releases](https://github.com/YOUR_ORG/step-functions-agent/releases)
2. Find your **draft** release
3. Review the artifacts:
   - macOS DMG files (Intel and ARM64)
   - Windows MSI installer
   - Linux DEB package
4. Edit release notes if needed
5. Click **Publish release**

## Tag Naming Convention

- **Browser Agent**: `browser-agent-v{MAJOR}.{MINOR}.{PATCH}`
  - Example: `browser-agent-v0.1.0`
- **Local Agent**: `local-agent-v{MAJOR}.{MINOR}.{PATCH}`
  - Example: `local-agent-v0.2.0`

## Manual Triggering

You can also trigger builds manually without tags:

1. Go to Actions → Select workflow
2. Click "Run workflow"
3. Select branch
4. Click "Run workflow" button

## What Gets Built

### Browser Agent Installers

| Platform | Architecture | File | Size (approx) |
|----------|--------------|------|---------------|
| macOS    | ARM64 (M1/M2/M3) | `Local.Browser.Agent_0.1.0_aarch64.dmg` | ~4MB |
| macOS    | Intel (x64)      | `Local.Browser.Agent_0.1.0_x64.dmg` | ~4MB |
| Windows  | x64             | `Local.Browser.Agent_0.1.0_x64_en-US.msi` | ~3MB |
| Linux    | x64             | `local-browser-agent_0.1.0_amd64.deb` | ~3MB |

### Local Agent Installers

| Platform | Architecture | File | Size (approx) |
|----------|--------------|------|---------------|
| macOS    | ARM64 (M1/M2/M3) | `Local.Agent_0.2.0_aarch64.dmg` | ~3MB |
| macOS    | Intel (x64)      | `Local.Agent_0.2.0_x64.dmg` | ~3MB |
| Windows  | x64             | `Local.Agent_0.2.0_x64_en-US.msi` | ~2.5MB |
| Linux    | x64             | `local-agent_0.2.0_amd64.deb` | ~2.5MB |

**Note**: Installers are small because Python dependencies are downloaded on first run via `SETUP.sh` (macOS/Linux) or `SETUP.ps1` (Windows).

## Installation Instructions

### macOS

```bash
# Download and open DMG
open Local.Browser.Agent_*.dmg

# Drag app to Applications folder
# First run: System Preferences → Security → Allow

# Run setup
open "/Applications/Local Browser Agent.app"
# Click "Setup Python Environment" in UI
```

### Windows

```powershell
# Run MSI installer (double-click or):
msiexec /i Local.Browser.Agent_*.msi

# Run setup script
cd "C:\Program Files\Local Browser Agent"
.\SETUP.ps1

# Or use batch file
.\SETUP.bat
```

### Linux (Ubuntu/Debian)

```bash
# Install DEB package
sudo dpkg -i local-browser-agent_*.deb
sudo apt-get install -f  # Fix dependencies

# Run setup
cd /opt/local-browser-agent  # or wherever installed
./SETUP.sh
```

## Troubleshooting

### Build Fails on Specific Platform

1. Check the Actions tab for detailed logs
2. Common issues:
   - **macOS**: Code signing (can be disabled for testing)
   - **Windows**: Missing Visual Studio Build Tools
   - **Linux**: Missing system libraries (webkit, gtk)

### Python Dependencies Not Installing

- Ensure `requirements.txt` (browser-agent) or `pyproject.toml` (local-agent) is up to date
- Check uv installation in GitHub Actions logs
- Verify Python 3.11 compatibility

### Large File Sizes

If installers become too large:
1. Check `.taurignore` is excluding unnecessary files
2. Ensure `.venv` directories are not bundled
3. Review bundle configuration in `tauri.conf.json`

## Future Improvements

- [ ] Add code signing for macOS (requires Apple Developer account)
- [ ] Add code signing for Windows (requires certificate)
- [ ] Add auto-update functionality (Tauri updater)
- [ ] Combine agents into unified local agent
- [ ] Add Linux AppImage format
- [ ] Add macOS Homebrew cask
- [ ] Add Windows Chocolatey package

## Workflow Configuration Files

- `.github/workflows/release-browser-agent.yml` - Browser agent builds
- `.github/workflows/release-local-agent.yml` - Local agent builds

## Support

For issues with the release process:
1. Check GitHub Actions logs
2. Review this documentation
3. Open an issue in the repository
