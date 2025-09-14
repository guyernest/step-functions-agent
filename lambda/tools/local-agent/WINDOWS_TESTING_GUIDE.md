# Windows Testing Guide for Local Agent

## Overview

This guide explains how to set up and test the Local Agent GUI automation tool on Windows, which polls AWS Step Functions activities and executes automation scripts.

## Dual Executor Architecture

The Local Agent supports two script execution engines:

### 1. **Rust Executor** (Built-in, Default)
- **Technology**: Native Rust using `enigo` library
- **Location**: Embedded directly in the GUI application
- **Best for**: Windows automation, fast execution, zero dependencies
- **Features**: Mouse/keyboard control, window management, screenshots, basic image recognition
- **How to use**: Set `"executor": "rust"` in script JSON (or omit for default)

### 2. **Python Executor** (External, Fallback)
- **Technology**: Python with PyAutoGUI
- **Location**: `script_executor.py` (must be bundled or in working directory)
- **Best for**: macOS compatibility, advanced image recognition, legacy scripts
- **Features**: Full PyAutoGUI capabilities, OpenCV image matching
- **How to use**: Set `"executor": "python"` in script JSON

### Executor Selection Logic

```json
{
  "name": "My Script",
  "executor": "rust",    // Options: "rust", "native", "python" (defaults to "rust" if omitted)
  "actions": [...]
}
```

**Decision flow:**
1. If `"executor": "rust"` or `"native"` → Use Rust executor
2. If `"executor": "python"` → Use Python executor (requires script_executor.py)
3. If no executor specified → Default to Rust executor
4. If Rust executor fails → Does NOT fall back to Python (explicit choice)

### When to Use Which Executor

| Use Case | Recommended Executor | Reason |
|----------|---------------------|---------|
| Windows automation | Rust | Better performance, no dependencies |
| macOS automation | Python | Better compatibility with macOS |
| Simple clicks/typing | Rust | Faster, built-in |
| Complex image recognition | Python | OpenCV support |
| CI/CD environments | Rust | No Python dependencies needed |
| Legacy scripts | Python | Maintain compatibility |

## Quick Start Guide (5 Minutes)

### For Testing Teams - Get Running Quickly:

1. **Download the Latest Build**
   - Go to [GitHub Actions](https://github.com/guyernest/step-functions-agent/actions/workflows/build-local-agent.yml)
   - Download `local-agent-x86_64-pc-windows-msvc.zip` from latest run

2. **Install the Application**
   ```powershell
   # Extract and install
   Expand-Archive -Path "local-agent-*.zip" -DestinationPath "C:\local-agent"
   cd C:\local-agent
   msiexec /i "Local Agent_0.2.0_x64_en-US.msi"
   ```

3. **Set Up AWS Credentials**
   ```powershell
   # Install AWS CLI (if not already installed)
   msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
   
   # Configure credentials properly
   aws configure
   # Enter when prompted:
   # AWS Access Key ID: YOUR_KEY_HERE
   # AWS Secret Access Key: YOUR_SECRET_HERE
   # Default region name: us-east-1
   # Default output format: json
   ```

4. **Launch and Configure**
   - Start "Local Agent" from Start Menu
   - Go to Config tab → Enter Activity ARN
   - Click "Start Polling" in Listen tab
   - Done! The agent is now waiting for tasks

### For Quick Testing Without Installation:

### Option A: Use Pre-built Binaries (Easiest - No Build Required!)

The pre-built binaries are automatically created by GitHub Actions for each push to main branch.

```powershell
# 1. Download latest Windows build artifact
# Go to: https://github.com/guyernest/step-functions-agent/actions/workflows/build-local-agent.yml
# Click on the latest successful run
# Download "local-agent-x86_64-pc-windows-msvc" artifact

# Alternative: Direct download from releases (when available)
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/guyernest/step-functions-agent/releases/latest"
$windowsAsset = $release.assets | Where-Object { $_.name -like "*windows*" }
Invoke-WebRequest -Uri $windowsAsset.browser_download_url -OutFile "local-agent-windows.zip"

# 2. Extract
Expand-Archive -Path "local-agent-windows.zip" -DestinationPath "local-agent"
cd local-agent

# 3. Run the standalone Rust executor (ZERO dependencies!)
.\rust-executor-windows-x64.exe examples\windows_simple_test.json

# That's it! No Python, no build tools, no dependencies needed!
```

### Option B: Python with uvx (No Compilation)

```powershell
# 1. Install uv (one-time setup)
irm https://astral.sh/uv/install.ps1 | iex

# 2. Clone just the local-agent folder
git clone --filter=blob:none --sparse https://github.com/guyernest/step-functions-agent.git
cd step-functions-agent
git sparse-checkout set lambda/tools/local-agent
cd lambda/tools/local-agent

# 3. Run automation directly with uvx (no installation needed)
uvx --with pyautogui --with pillow --with opencv-python \
    python script_executor.py examples/windows_simple_test.json
```

Both approaches work immediately without any build tools! Continue reading for development setup.

## Prerequisites

- AWS Account with EC2 access
- RDP client on your local machine
  - **macOS**: Microsoft Remote Desktop (from App Store)
  - **Windows**: Built-in Remote Desktop Connection
  - **Linux**: Remmina or similar RDP client

## Step 1: Launch Windows EC2 Instance

### 1.1 Choose AMI

1. Go to EC2 Console → Launch Instance
2. Select: **Microsoft Windows Server 2022 Base** or **Windows Server 2019 Base**
   - For GUI testing, ensure you choose an AMI with Desktop Experience
   - Recommended: `Windows_Server-2022-English-Full-Base`

### 1.2 Instance Configuration

```yaml
Instance Type: t3.medium or larger (minimum 4GB RAM)
Storage: 30GB minimum (50GB recommended)
Security Group:
  - RDP (port 3389) from your IP
  - HTTP/HTTPS if testing web automation
Network: Default VPC is fine
Key Pair: Create new or use existing (.pem file)
```

### 1.3 Security Group Rules

```text
Type: RDP
Protocol: TCP
Port: 3389
Source: My IP (or specific IP range for security)
```

## Step 2: Connect to Windows Instance

### 2.1 Get Windows Password

1. Wait ~4 minutes after launch for instance to be ready
2. Select instance → Actions → Security → Get Windows password
3. Upload your .pem key file
4. Copy the decrypted Administrator password

### 2.2 Connect via RDP

```bash
# Get Public DNS/IP from EC2 console
Host: ec2-XX-XX-XX-XX.compute-1.amazonaws.com
Username: Administrator
Password: [decrypted password from step 2.1]
```

## Step 3: Download and Install Pre-built Binaries (Recommended)

### 3.1 Download Latest Build

```powershell
# Run PowerShell as Administrator

# Download from GitHub Actions artifacts
# 1. Go to: https://github.com/guyernest/step-functions-agent/actions/workflows/build-local-agent.yml
# 2. Click on the latest successful workflow run
# 3. Scroll down to "Artifacts" section
# 4. Download "local-agent-x86_64-pc-windows-msvc.zip"

# Or download from releases page (if available)
# https://github.com/guyernest/step-functions-agent/releases/latest
```

### 3.2 Extract and Install

```powershell
# Extract the downloaded ZIP file
Expand-Archive -Path "local-agent-x86_64-pc-windows-msvc.zip" -DestinationPath "C:\local-agent"
cd C:\local-agent

# List available files
dir

# You should see:
# - Local Agent_0.2.0_x64-setup.exe    (GUI installer - recommended)
# - Local Agent_0.2.0_x64_en-US.msi    (MSI installer - alternative)
# - rust-executor-windows-x64.exe      (Standalone CLI executor)
# - script_executor.py                 (Python executor)
# - examples/                          (Sample automation scripts)
```

### 3.3 Install the GUI Application

```powershell
# Option 1: Run the NSIS installer (recommended)
& ".\Local Agent_0.2.0_x64-setup.exe"

# Option 2: Use MSI installer (for enterprise deployments)
msiexec /i "Local Agent_0.2.0_x64_en-US.msi"

# The installer will:
# - Install the application to Program Files
# - Create Start Menu shortcuts
# - Register the application for uninstall
```

### 3.4 Configure AWS Credentials

Before running the Local Agent GUI, you need to set up AWS credentials:

#### Option A: Create IAM User (Simplest)

1. **Create IAM User in AWS Console:**
```bash
# Go to AWS IAM Console
# Create new user: local-agent-user
# Enable "Programmatic access"
# Save the Access Key ID and Secret Access Key
```

2. **Create IAM Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "states:GetActivityTask",
                "states:SendTaskSuccess",
                "states:SendTaskFailure",
                "states:SendTaskHeartbeat",
                "states:DescribeActivity"
            ],
            "Resource": "arn:aws:states:*:*:activity/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "states:ListActivities"
            ],
            "Resource": "*"
        }
    ]
}
```

3. **Attach Policy to User:**
- Name the policy: `LocalAgentStepFunctionsPolicy`
- Attach to the `local-agent-user`

4. **Configure Credentials on Windows:**
```powershell
# Install AWS CLI first (if not already installed)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configure using AWS CLI (ensures correct format)
aws configure
# Enter when prompted:
# AWS Access Key ID: [your access key]
# AWS Secret Access Key: [your secret key]  
# Default region name: us-east-1
# Default output format: json

# Verify credentials are working
aws sts get-caller-identity
```

#### Option B: Use AWS SSO (For Corporate Environments)

```powershell
# Install AWS CLI first
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configure SSO
aws configure sso
# Follow prompts to set up SSO profile

# Export credentials for the application
aws sso login --profile your-sso-profile
$env:AWS_PROFILE = "your-sso-profile"
```

#### Option C: Use EC2 Instance Role (When Running on EC2)

If running on an EC2 instance, attach an IAM role with the required permissions:
```bash
# No configuration needed - credentials are automatic
# Just ensure the EC2 instance has a role with the LocalAgentStepFunctionsPolicy
```

### 3.5 Launch the Application

```powershell
# Start from the Start Menu
# Look for "Local Agent" in the Start Menu

# Or run the standalone executor for testing
.\rust-executor-windows-x64.exe examples\windows_simple_test.json
```

### 3.6 First-Time Setup in GUI

1. **Launch Local Agent** from Start Menu
2. **Go to Config tab**
3. **Enter AWS Settings:**
   - Region: `us-east-1` (or your region)
   - Activity ARN: `arn:aws:states:region:account:activity/YourActivityName`
   - Access Key ID: (if not using default credentials)
   - Secret Access Key: (if not using default credentials)
4. **Click "Save Configuration"**
5. **Go to Listen tab**
6. **Click "Start Polling"**

The agent will now poll for activities and execute automation scripts!

## Step 4: Development Setup (Optional - Only for Contributors)

If you need to modify the code or build from source:

### 4.1 Install Development Tools

```powershell
# Install Git for cloning the repository
choco install -y git

# For Python executor development
irm https://astral.sh/uv/install.ps1 | iex

# For Rust executor development (requires build tools)
choco install -y visualstudio2022buildtools
choco install -y visualstudio2022-workload-vctools
choco install -y rust-ms
```

### 4.2 Clone and Build from Source

```powershell
# Clone repository
git clone --filter=blob:none --sparse https://github.com/guyernest/step-functions-agent.git
cd step-functions-agent
git sparse-checkout set lambda/tools/local-agent
cd lambda/tools/local-agent

# Build Rust executor
cd rust-executor-standalone
cargo build --release
# Output: target/release/rust-executor.exe
```

**Note**: This uses Git's sparse checkout feature to download only the `local-agent` folder, saving bandwidth and time. The full repository is over 100MB, but this approach downloads only what's needed (~10MB).

## Step 5: Test Automation Scripts (Using Pre-built Binary)

### 5.1 Test Included Examples

Create `examples/windows_notepad_test.json`:

```json
{
  "name": "Windows Notepad Test",
  "description": "Test automation on Windows with Notepad",
  "executor": "rust",
  "abort_on_error": true,
  "actions": [
    {
      "type": "launch",
      "app": "notepad.exe",
      "description": "Launch Notepad"
    },
    {
      "type": "wait",
      "seconds": 2,
      "description": "Wait for Notepad to load"
    },
    {
      "type": "type",
      "text": "Hello from Windows Rust Executor!\\n\\n",
      "description": "Type greeting"
    },
    {
      "type": "type",
      "text": "Testing automation on Windows EC2 instance.",
      "interval": 0.05,
      "description": "Type with effect"
    },
    {
      "type": "hotkey",
      "keys": ["ctrl", "a"],
      "description": "Select all text"
    },
    {
      "type": "hotkey",
      "keys": ["ctrl", "c"],
      "description": "Copy text"
    },
    {
      "type": "hotkey",
      "keys": ["ctrl", "v"],
      "description": "Paste text"
    },
    {
      "type": "wait",
      "seconds": 2,
      "description": "Show result"
    },
    {
      "type": "hotkey",
      "keys": ["alt", "f4"],
      "description": "Close Notepad"
    },
    {
      "type": "press",
      "key": "n",
      "description": "Don't save"
    }
  ]
}
```

### 5.2 Run Tests with Pre-built Binary

```powershell
# Test the included example
.\rust-executor-windows-x64.exe examples\windows_simple_test.json

# Test the Notepad example (if you created it)
.\rust-executor-windows-x64.exe examples\windows_notepad_test.json

# The executor will:
# 1. Parse the JSON automation script
# 2. Execute each action in sequence
# 3. Display results with timing information
# 4. Exit with status code (0 = success)
```

### 5.3 Alternative: Python Executor (Requires Python)

If you prefer Python or need to modify the script executor:

```powershell
# Install uv first (one-time)
irm https://astral.sh/uv/install.ps1 | iex

# Run with uvx (no installation needed)
uvx --with pyautogui --with pillow --with opencv-python \
    python script_executor.py examples\windows_simple_test.json
```

## Step 6: Windows-Specific Considerations

### 6.1 UAC and Elevation

- Some applications run elevated (as Administrator)
- Non-elevated automation tools cannot send input to elevated windows
- Solution: Run Local Agent as Administrator if needed

```powershell
# Right-click on exe → Run as Administrator
# Or from elevated PowerShell:
Start-Process "local-agent-gui.exe" -Verb RunAs
```

### 6.2 Windows Defender

- May flag automation tools as suspicious
- Add exclusion for development folder:

```powershell
Add-MpPreference -ExclusionPath "C:\path\to\step-functions-agent"
```

### 6.3 Screen Resolution

- RDP may use different resolution than expected
- Set consistent resolution for testing:

```powershell
# In RDP client, set display resolution before connecting
# Or use PowerShell to set:
Set-DisplayResolution -Width 1920 -Height 1080
```

## Step 7: Troubleshooting Common Issues

### 7.1 AWS Credentials Issues

**Problem: "No credentials found" or "Invalid credentials"**
```powershell
# Check if credentials file exists
Test-Path $env:USERPROFILE\.aws\credentials

# Verify credentials are valid
aws sts get-caller-identity

# If using SSO, ensure you're logged in
aws sso login --profile your-profile
```

**Problem: "Access Denied" when polling activities**
```powershell
# Verify IAM permissions - should have these actions:
# - states:GetActivityTask
# - states:SendTaskSuccess
# - states:SendTaskFailure
# - states:SendTaskHeartbeat
# - states:ListActivities

# Test with AWS CLI
aws stepfunctions get-activity-task --activity-arn "your-activity-arn"
```

### 7.2 Installation Issues

**Problem: "Windows protected your PC" warning**
- Click "More info"
- Click "Run anyway"
- This is normal for unsigned executables

**Problem: MSI installer fails**
```powershell
# Run with logging for debugging
msiexec /i "Local Agent_0.2.0_x64_en-US.msi" /l*v install.log

# Check Windows Event Viewer for errors
eventvwr.msc
```

### 7.3 Application Won't Start

**Problem: Missing Visual C++ Redistributables**
```powershell
# Install Visual C++ Redistributables
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

**Problem: Antivirus blocking the application**
- Add exception for Local Agent in your antivirus
- Windows Defender: Settings → Virus & threat protection → Exclusions

### 7.4 Activity Polling Issues

**Problem: "No tasks received" continuously**
- Verify Activity ARN is correct
- Check if State Machine is actually sending tasks to the activity
- Ensure the activity exists in the correct region

**Problem: "Heartbeat timeout"**
- The script is taking too long to execute
- Add heartbeat calls in long-running scripts
- Increase timeout in State Machine definition

### 7.5 Automation Execution Issues

**Problem: "Cannot find window" or "Element not found"**
- Ensure target application is running and visible
- Check if running with correct permissions (may need Administrator)
- Verify screen resolution matches script expectations

**Problem: Clicks/typing not working**
```powershell
# Run as Administrator
Start-Process "Local Agent.exe" -Verb RunAs

# Disable UAC temporarily for testing
# Control Panel → User Accounts → Change User Account Control settings
```

### 7.6 Network/Firewall Issues

**Problem: Cannot connect to AWS**
```powershell
# Test connectivity
Test-NetConnection -ComputerName states.us-east-1.amazonaws.com -Port 443

# Check proxy settings
[System.Net.WebRequest]::DefaultWebProxy.GetProxy("https://states.us-east-1.amazonaws.com")

# Set proxy if needed
$env:HTTPS_PROXY = "http://your-proxy:8080"
```

## Step 8: Debugging Tips

### 8.1 Enable Debug Logging

```powershell
# Set environment variable for Rust logging
$env:RUST_LOG = "debug"

# Run with verbose output
cargo run --release -- --verbose
```

### 6.2 Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| "Access Denied" errors | Run as Administrator |
| Keys not registering | Check if target app has focus, add delays |
| Ctrl+X shortcuts not working | Use VK codes instead of Unicode |
| Window not found | Increase wait time after launch |
| Text not appearing | Click to focus before typing |

### 6.3 Test Checklist

- [ ] Basic text input (type action)
- [ ] Special characters and newlines
- [ ] Ctrl+Key shortcuts (copy, paste, select all)
- [ ] Alt+Key shortcuts (Alt+F4, Alt+Tab)
- [ ] Window management (launch, focus, close)
- [ ] Mouse actions (click, drag, right-click)
- [ ] Image recognition (if implemented)
- [ ] Multi-window scenarios
- [ ] Elevated application interaction

## Step 7: Performance Testing

### 7.1 Measure Execution Time

```powershell
Measure-Command {
    python script_executor.py examples/windows_notepad_test.json
}
```

### 7.2 Compare Executors

```powershell
# Create comparison script
@"
Python Executor:
"@ | Out-Host
Measure-Command { python script_executor.py test.json }

@"
Rust Executor:
"@ | Out-Host  
Measure-Command { .\local-agent-gui.exe --script test.json }
```

## Step 8: CI/CD Integration

### 8.1 GitHub Actions Windows Runner

```yaml
# .github/workflows/windows-test.yml
name: Windows Testing
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - name: Build
        run: |
          cd lambda/tools/local-agent/src-tauri
          cargo build --release
      - name: Test
        run: |
          cargo test --release
```

## Step 9: Cost Optimization

### 9.1 Instance Management

- **Stop** (not terminate) instances when not testing
- Use **Spot Instances** for non-critical testing (up to 90% discount)
- Set up **CloudWatch alarms** for idle instances

### 9.2 Estimated Costs

```text
t3.medium (2 vCPU, 4GB RAM):
- On-Demand: ~$0.0416/hour
- Spot: ~$0.0125/hour
- Monthly (8hr/day): ~$10-35

Storage (50GB gp3):
- ~$4/month
```

### 9.3 Auto-Shutdown Script

```powershell
# Schedule shutdown after 4 hours (safety measure)
shutdown /s /t 14400 /c "Auto-shutdown after 4 hours"

# Cancel if needed:
shutdown /a
```

## Step 10: Alternative Testing Options

### 10.1 Local Windows VM

- **VirtualBox/VMware**: Free Windows 10/11 evaluation (90 days)
- **Parallels** (Mac): Commercial but excellent integration
- **QEMU/KVM** (Linux): Free and performant

### 10.2 Azure Windows Virtual Desktop

- Similar to EC2 but with better Windows integration
- Free tier available (limited hours)

### 10.3 Windows 365 Cloud PC

- Monthly subscription
- Persistent development environment
- Good for long-term testing

## Troubleshooting

### Script Executor Errors

#### Error: "Script executor not found"

This error occurs when the Python executor is needed but not available.

**Common Causes:**
1. Script explicitly requests Python executor (`"executor": "python"`)
2. Python executor file (`script_executor.py`) not in installation directory
3. MSI installer didn't bundle the Python executor

**Solutions:**

1. **Use Rust executor instead** (Recommended for Windows):
   ```json
   {
     "executor": "rust",  // Or just omit this field
     "actions": [...]
   }
   ```

2. **Copy Python executor to installation directory**:
   ```powershell
   # Find where Local Agent is installed
   $installPath = "C:\Program Files\Local Agent"
   
   # Copy script_executor.py to installation directory
   Copy-Item "script_executor.py" -Destination $installPath
   ```

3. **Run from development directory**:
   ```powershell
   # Run from the source directory where script_executor.py exists
   cd C:\path\to\lambda\tools\local-agent
   "C:\Program Files\Local Agent\Local Agent.exe"
   ```

#### Error: "Python executor failed"

**Common Causes:**
- Python not installed
- PyAutoGUI dependencies missing
- Display/permission issues

**Solution:**
```powershell
# Install Python and dependencies
winget install Python.Python.3.12
pip install pyautogui pillow opencv-python

# Or use uv for isolated execution
pip install uv
uvx --with pyautogui --with pillow --with opencv-python python script_executor.py
```

### Rust Build Errors

#### Error: "dlltool.exe not found"

This error occurs when building Rust crates with native dependencies. Solutions:

**Solution 1: Install Visual Studio Build Tools (Recommended)**
```powershell
# Install MSVC toolchain
choco install -y visualstudio2022buildtools
choco install -y visualstudio2022-workload-vctools

# Or install full Visual Studio Community
winget install Microsoft.VisualStudio.2022.Community

# Restart PowerShell and retry build
cargo build --release
```

**Solution 2: Use MinGW Toolchain**
```powershell
# Install MinGW
choco install -y mingw

# Set Rust to use GNU toolchain
rustup default stable-x86_64-pc-windows-gnu

# Retry build
cargo build --release
```

**Solution 3: Install Rust via rustup (includes toolchain setup)**
```powershell
# Uninstall existing Rust
choco uninstall rust

# Install via rustup (will prompt for MSVC installation)
Invoke-WebRequest -Uri https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
.\rustup-init.exe

# Follow prompts to install MSVC toolchain
# Restart PowerShell
cargo build --release
```

### Connection Issues

```powershell
# Check Windows Firewall
netsh advfirewall firewall show rule name=all | findstr 3389

# Enable RDP if disabled
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0

# Restart RDP service
Restart-Service TermService -Force
```

### Performance Issues

```powershell
# Check available resources
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"

# Disable Windows animations for better RDP performance
SystemPropertiesPerformance.exe
# Select "Adjust for best performance"
```

## Next Steps

1. Create Windows-specific test suite
2. Implement VK-based key handling for better reliability
3. Add Windows-specific error handling
4. Create automation for common Windows applications (Office, browsers)
5. Set up automated testing pipeline

## Resources

- [AWS EC2 Windows Guide](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/)
- [Windows SendInput API](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [Rust Windows Crate](https://github.com/microsoft/windows-rs)
- [PyAutoGUI Windows Documentation](https://pyautogui.readthedocs.io/en/latest/platform_differences.html)
