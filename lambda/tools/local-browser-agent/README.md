# Local Browser Agent

A Rust-based local agent that executes Nova Act browser automation commands via AWS Step Functions Activity pattern, running on the user's local machine to avoid cloud-based bot detection.

## Overview

The Local Browser Agent solves the bot detection problem inherent in cloud-based browser automation by running Nova Act on the user's actual desktop/laptop with their real browser profile, cookies, and extensions. This provides a truly authentic browsing environment that websites cannot easily distinguish from a human user.

### Key Features

- **Real Browser Environment**: Runs on your actual machine with your Chrome profile
- **Bot Detection Avoidance**: No headless cloud browsers, no Lambda timeouts, no bot signatures
- **Activity Pattern**: Uses AWS Step Functions Activity for long-running tasks
- **Session Persistence**: Maintains authenticated sessions across multiple commands
- **S3 Integration**: Automatic upload of screenshots and recordings via Nova Act's S3Writer
- **Manual Intervention**: UI allows human intervention for CAPTCHAs
- **Tauri UI**: Native desktop application with real-time monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Step Functions Agent                  │
│  ┌────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │ Converse   │───▶│ Tool Router │───▶│ Browser Tool│      │
│  │ (LLM)      │◀───│ (Lambda)    │◀───│ (Activity)  │      │
│  └────────────┘    └─────────────┘    └─────────────┘      │
│                                               │              │
│                                               ▼              │
│                                        ┌─────────────┐      │
│                                        │ S3 Bucket   │      │
│                                        │ Screenshots │      │
│                                        │ Recordings  │      │
│                                        └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
                               ▲
                               │ Activity Task Polling
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Local Browser Agent (Your Desktop)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Rust Activity Worker                                   │ │
│  │  • Polls Step Functions Activity ARN                   │ │
│  │  • Spawns Python subprocess with Nova Act SDK          │ │
│  │  • Manages browser sessions                            │ │
│  │  • Sends heartbeat every 60s                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Nova Act (Python 3.11 venv)                            │ │
│  │  • Executes browser commands                           │ │
│  │  • Uses S3Writer for automatic recording uploads       │ │
│  │  • Maintains session state                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Chrome Browser                                         │ │
│  │  • Your actual Chrome installation                     │ │
│  │  • Your cookies, extensions, profile                   │ │
│  │  • Real desktop environment                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Tauri UI (React + TypeScript)                          │ │
│  │  • Configuration screen with AWS/Chrome detection      │ │
│  │  • Real-time activity monitoring                       │ │
│  │  • Active browser sessions display                     │ │
│  │  • Connection testing and ARN validation               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

1. **Agent Invokes Tool**: Step Functions agent invokes `browser_remote` tool
2. **Activity Posted**: Lambda posts task to Activity ARN
3. **Local Agent Polls**: Your local machine polls for tasks
4. **Task Received**: Gets browser command (prompt, config)
5. **Python Execution**: Rust spawns Python subprocess with Nova Act
6. **Browser Automation**: Nova Act controls your local Chrome
7. **S3 Upload**: S3Writer automatically uploads screenshots/videos
8. **Result Returned**: Task result sent back to Step Functions
9. **Agent Continues**: LLM analyzes results, continues workflow

## Prerequisites

- **Operating System**: macOS, Linux, or Windows
- **Python**: 3.11+ (managed via `uv` or direct installation)
- **uv** (recommended): Fast Python package installer ([install](https://docs.astral.sh/uv/))
- **Rust**: Latest stable ([install](https://rustup.rs/))
- **Node.js**: 16+ (for Tauri frontend)
- **AWS Account**: With Step Functions and S3 access
- **Chrome**: Google Chrome browser

### Platform-Specific Notes

**Windows**:
- Use `python` command (not `python3`)
- Chrome typically installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- User data directory at `%LOCALAPPDATA%\Google\Chrome\User Data`
- AWS credentials at `%USERPROFILE%\.aws\credentials`

**macOS**:
- Use `python3` command
- Chrome at `/Applications/Google Chrome.app`
- User data directory at `~/Library/Application Support/Google/Chrome`

**Linux**:
- Use `python3` command
- Chrome at `/usr/bin/google-chrome`
- User data directory at `~/.config/google-chrome`

## Quick Start

### 1. Install Dependencies

```bash
# Clone repository and navigate to local-browser-agent
cd lambda/tools/local-browser-agent

# Install all dependencies (Rust, Python 3.11 venv with uv, Node.js, Playwright)
make install
```

This will:
- Create Python 3.11 virtual environment with `uv`
- Compile `requirements.txt` from `requirements.in`
- Install all Python dependencies in `.venv`
- Install Node.js dependencies for the UI
- Install Playwright Chrome browser
- Create `config.yaml` from example

### 2. Configure AWS Credentials

```bash
# Configure AWS profile for local agent
make aws-setup

# Or manually:
aws configure --profile browser-agent

# Required permissions:
# - states:GetActivityTask
# - states:SendTaskSuccess
# - states:SendTaskFailure
# - states:SendTaskHeartbeat
# - s3:ListObjects (on recordings bucket)
# - s3:PutObject (on recordings bucket)
```

### 3. Deploy AWS Infrastructure

```bash
# Deploy the CDK stack to create Activity ARN and S3 bucket
cd ../../..  # Navigate to project root
cdk deploy BrowserRemoteToolStack-prod --profile your-aws-profile

# Save the outputs:
# - ActivityArn: arn:aws:states:...
# - S3BucketName: browser-agent-recordings-prod-...
```

### 4. Configure Application via UI

```bash
# Build and run the application in development mode
cd lambda/tools/local-browser-agent
make dev
```

The Tauri application will open with a configuration screen where you can:

1. **AWS Configuration**:
   - Select AWS profile from detected profiles
   - Optionally specify AWS region
   - Test connection to verify credentials

2. **Activity Configuration**:
   - Enter Activity ARN from CDK deployment
   - Enter S3 bucket name from CDK deployment
   - Validate ARN to verify it exists

3. **Browser Configuration**:
   - Select Chrome profile from detected profiles
   - Choose headless mode (not recommended for bot detection)

4. **Nova Act Configuration**:
   - Enter Nova Act API key (or use `NOVA_ACT_API_KEY` env var)

5. **Advanced Settings**:
   - Set heartbeat interval (30-300 seconds)
   - Configure UI port

Click **Save Configuration** to create `config.yaml`.

### 5. Build and Run

```bash
# Build release version
make build

# Run the agent
make run

# Or continue in development mode
make dev
```

### 6. Monitor Activity

The application UI provides two screens:

- **Configuration**: Setup and test your AWS/browser settings
- **Monitor**: Real-time view of Activity polling status and active browser sessions

## Usage

### Starting the Agent

```bash
# Start the agent (polls for tasks)
./target/release/local-browser-agent

# Or with custom config
./target/release/local-browser-agent --config /path/to/config.yaml
```

### Creating an Agent that Uses Browser Remote

In your Step Functions agent stack:

```python
from stacks.agents.base_agent_construct import BaseAgentConstruct

class BroadbandAgentStack(Stack):
    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Use browser_remote tool
        agent = BaseAgentConstruct(
            self, "BroadbandAgent",
            agent_name="broadband-checker",
            tools=["browser_remote"],  # Remote browser tool
            env_name="prod"
        )
```

The agent can now use the browser like this:

```python
# In your agent's system prompt:
"""
You have access to browser_remote tool for web automation.

Example usage:
{
    "tool": "browser_remote",
    "params": {
        "prompt": "Navigate to BT broadband checker and search for address",
        "starting_page": "https://www.btwholesale.com",
        "user_data_dir": "/path/to/authenticated/profile",
        "max_steps": 20,
        "timeout": 300
    }
}

The tool will return:
{
    "success": true,
    "response": "...",
    "session_id": "...",
    "recording_s3_uri": "s3://bucket/path/to/recording"
}
"""
```

## Configuration

### Environment Variables

- `NOVA_ACT_API_KEY`: Your Nova Act API key (required)
- `AWS_PROFILE`: AWS profile to use (default: `browser-agent`)
- `RUST_LOG`: Log level (default: `info`)

### Config File Options

| Option | Description | Required |
|--------|-------------|----------|
| `activity_arn` | Step Functions Activity ARN | Yes |
| `aws_profile` | AWS credentials profile name | Yes |
| `s3_bucket` | S3 bucket for recordings | Yes |
| `user_data_dir` | Chrome profile directory | No (creates temp) |
| `ui_port` | UI server port | No (default: 3000) |
| `nova_act_api_key` | Nova Act API key | No (can use env var) |
| `headless` | Run browser headless | No (default: false) |
| `heartbeat_interval` | Activity heartbeat (seconds) | No (default: 60) |

## Features

### Session Persistence

Maintain authenticated sessions across multiple browser commands:

```python
# First command: Login
{
    "command": "start_session",
    "starting_page": "https://example.com",
    "user_data_dir": "/path/to/profile"
}

# Subsequent commands use same session
{
    "command": "act",
    "session_id": "previous-session-id",
    "prompt": "Navigate to dashboard"
}

# End session when done
{
    "command": "end_session",
    "session_id": "previous-session-id"
}
```

### Manual Intervention

When the browser encounters a CAPTCHA or requires human interaction:

1. Agent detects intervention needed
2. UI displays alert with screenshot
3. User interacts with browser window
4. User clicks "Resume" in UI
5. Agent continues execution

### S3 Recording

All browser sessions are automatically recorded and uploaded to S3:

- **Screenshots**: Captured after each step
- **Videos**: Full session recording
- **HTML**: Page snapshots
- **Metadata**: Session info, timestamps

Access recordings via S3 URI returned in tool response.

## Windows-Specific Setup

### Building on Windows

```powershell
# Install Rust from https://rustup.rs/
# Install Node.js from https://nodejs.org/
# Install Python 3.11+ from https://www.python.org/

# Navigate to the local-browser-agent directory
cd lambda\tools\local-browser-agent

# Install Python dependencies with uv (recommended)
pip install uv
uv venv python\.venv
python\.venv\Scripts\activate
uv pip install -r python\requirements.txt

# Or install manually
python -m venv python\.venv
python\.venv\Scripts\activate
pip install -r python\requirements.txt

# Install Node.js dependencies
cd ui
npm install
cd ..

# Build the Tauri application
cd src-tauri
cargo build --release
```

### Running on Windows

```powershell
# Set Nova Act API key
$env:NOVA_ACT_API_KEY = "your-api-key"

# Configure AWS credentials
aws configure --profile browser-agent

# Run the application
.\target\release\local-browser-agent.exe

# Or in development mode
cd src-tauri
cargo run
```

### Windows-Specific Notes

1. **Python Command**: Windows uses `python` instead of `python3`
2. **Path Separators**: The application automatically handles Windows backslashes
3. **Chrome Detection**: Will look for Chrome at:
   - `C:\Program Files\Google\Chrome\Application\chrome.exe`
   - `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
4. **User Data Directory**: Default location is `%LOCALAPPDATA%\Google\Chrome\User Data`
5. **AWS Credentials**: Located at `%USERPROFILE%\.aws\credentials`
6. **Firewall**: Ensure Windows Firewall allows outbound HTTPS connections to AWS

### Common Windows Issues

**Issue**: Python not found
```powershell
# Add Python to PATH or use full path
$env:PATH += ";C:\Python311"
```

**Issue**: Chrome not found
```powershell
# Verify Chrome installation
Get-Command chrome
# Or check manually
Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

**Issue**: AWS credentials not loading
```powershell
# Verify AWS CLI configuration
aws configure list --profile browser-agent
aws sts get-caller-identity --profile browser-agent
```

## Troubleshooting

### Agent Not Polling

Check AWS credentials:
```bash
aws sts get-caller-identity --profile browser-agent
```

Verify Activity ARN:
```bash
aws stepfunctions describe-activity \
  --activity-arn "your-activity-arn" \
  --region us-west-2
```

### Chrome Not Found

Ensure Chrome is installed:
```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt install google-chrome-stable
```

### Python Dependencies

The project uses `uv` for fast, reliable Python dependency management with a virtual environment:

```bash
# Update dependencies from requirements.in
make update-deps

# Reinstall all dependencies
make install-python

# Reinstall Playwright browser
make install-playwright
```

Dependencies are managed in two files:
- `python/requirements.in`: Direct dependencies only
- `python/requirements.txt`: Full lockfile (auto-generated, committed to repo)

### S3 Upload Failures

Verify S3 permissions:
```bash
aws s3 ls s3://your-bucket/ --profile browser-agent
```

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for development setup, project structure, and contribution guidelines.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system architecture, component descriptions, and data flow.

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for AWS infrastructure setup and deployment instructions.

## Security Considerations

- **Credentials**: Never commit AWS credentials or Nova Act API keys
- **Browser Profile**: User data directory may contain sensitive cookies
- **S3 Bucket**: Ensure bucket has appropriate access controls
- **Network**: Agent requires outbound HTTPS to AWS services

## Benefits Over Cloud-Based Automation

| Feature | Cloud (Lambda/ECS) | Local Browser Agent |
|---------|-------------------|---------------------|
| Bot Detection | High risk | Low risk |
| Browser Profile | Temporary | Persistent |
| Extensions | Not supported | Fully supported |
| CAPTCHAs | Hard to solve | Human can solve |
| Timeout | 15 min (Lambda) | Unlimited |
| IP Address | Cloud datacenter | User's ISP |
| Cost | Per execution | One-time setup |

## License

Same as parent project.

## Support

For issues or questions:
- Create an issue in the main repository
- Email: support@your-domain.com
- Documentation: [Full docs](../../docs/)

## Related Tools

- [local-agent](../local-agent/) - Windows application automation
- [agentcore-browser](../agentcore_browser/) - Cloud-based browser automation
- [nova-act-browser](../nova_act_browser/) - Direct Nova Act Lambda integration
