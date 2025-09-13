# Windows Testing Guide for Local Agent

## Overview

This guide explains how to test the Local Agent GUI automation tool on Windows using AWS EC2 instances with Remote Desktop Protocol (RDP) connection.

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

## Step 3: Setup Development Environment on Windows

### 3.1 Install Prerequisites

```powershell
# Run PowerShell as Administrator

# Install Chocolatey (Windows package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required tools
choco install -y git
choco install -y rust
choco install -y python3
choco install -y nodejs
choco install -y vscode

# Restart PowerShell after installations
```

### 3.2 Clone and Build Local Agent

```powershell
# Clone repository
git clone https://github.com/your-org/step-functions-agent.git
cd step-functions-agent/lambda/tools/local-agent

# Install Python dependencies (for Python executor)
pip install pyautogui pillow opencv-python

# Build Rust components
cd src-tauri
cargo build --release

# Install Node dependencies for UI
cd ..
npm install
```

### 3.3 Configure AWS Credentials

```powershell
# Create AWS credentials directory
mkdir $env:USERPROFILE\.aws

# Create credentials file
notepad $env:USERPROFILE\.aws\credentials

# Add your credentials:
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

## Step 4: Test Automation Scripts

### 4.1 Create Windows Test Script

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

### 4.2 Run Local Agent GUI

```powershell
# From local-agent directory
npm run tauri dev

# Or for production build
npm run tauri build
# Run: src-tauri\target\release\local-agent-gui.exe
```

### 4.3 Test via Command Line

```powershell
# Test Python executor
python script_executor.py examples/windows_notepad_test.json

# Test Rust executor directly
cd src-tauri
cargo run --release -- --script ../examples/windows_notepad_test.json
```

## Step 5: Windows-Specific Considerations

### 5.1 UAC and Elevation

- Some applications run elevated (as Administrator)
- Non-elevated automation tools cannot send input to elevated windows
- Solution: Run Local Agent as Administrator if needed

```powershell
# Right-click on exe → Run as Administrator
# Or from elevated PowerShell:
Start-Process "local-agent-gui.exe" -Verb RunAs
```

### 5.2 Windows Defender

- May flag automation tools as suspicious
- Add exclusion for development folder:

```powershell
Add-MpPreference -ExclusionPath "C:\path\to\step-functions-agent"
```

### 5.3 Screen Resolution

- RDP may use different resolution than expected
- Set consistent resolution for testing:

```powershell
# In RDP client, set display resolution before connecting
# Or use PowerShell to set:
Set-DisplayResolution -Width 1920 -Height 1080
```

## Step 6: Debugging Tips

### 6.1 Enable Debug Logging

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
