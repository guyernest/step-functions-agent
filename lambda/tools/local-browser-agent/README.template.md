# Local Browser Agent - Deployment Package

## Quick Start

```bash
# 1. Install the app
open *.dmg
# Drag to Applications folder

# 2. Launch the app and setup Python environment via UI
open "/Applications/Local Browser Agent.app"
# Click "Setup Python Environment" button in Configuration tab

# 3. Set your Nova Act API key
export NOVA_ACT_API_KEY="your-key-here"

# 4. Configure and start monitoring
```

## What Gets Installed

The **DMG** contains:
- Local Browser Agent.app (with Python scripts bundled inside)

The **Python Environment Setup** (via UI button or SETUP.sh script) installs:
- uv package manager (if not present)
- Python 3.11 virtual environment (inside the app bundle at `/Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv`)
- Python dependencies (nova-act, boto3, playwright, etc.)
- Chromium browser (via Playwright)

**Note:** The Python environment is NOT included in the DMG to keep the package size small (3.8MB vs 96MB). You must run the setup after installing the app.

## Detailed Installation

### 1. Install the Application

```bash
open Local\ Browser\ Agent_*.dmg
# Drag "Local Browser Agent" to Applications folder
```

### 2. Setup Python Environment

You have two options:

**Option A: UI Button (Recommended)**
1. Launch the app: `open "/Applications/Local Browser Agent.app"`
2. Navigate to the "Configuration" screen
3. Click "Setup Python Environment" button
4. Wait for setup to complete (displays progress with checkmarks)

**Option B: Terminal Script**
```bash
./SETUP.sh
```

What the setup does:
- Installs uv package manager (if not present)
- Creates Python 3.11 venv at: `/Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv`
- Installs Python packages from requirements.txt
- Downloads Chromium browser via Playwright

**Note:** Setup takes 2-5 minutes depending on your internet connection. The UI shows detailed progress for each step.

### 3. Configure (Optional)

You can configure via:

**Option A: UI** (Recommended)
- Launch the app
- Use the Settings tab
- Enter Activity ARN, S3 Bucket, AWS Profile

**Option B: Config File**
```bash
# Edit the provided config.yaml template
vim config.yaml
# Copy to your home directory or use UI to load it
```

### 4. Set Environment Variables

```bash
# Add to ~/.zshrc or ~/.bash_profile
export NOVA_ACT_API_KEY="your-api-key-here"
```

### 5. Run the Application

```bash
open "/Applications/Local Browser Agent.app"
```

## Testing with Examples

The `examples/` directory contains 11 sample automation scripts:

- `simple_test_example.json` - Basic navigation test
- `wikipedia_search_example.json` - Search and extract
- `bt_broadband_example.json` - UK broadband availability check
- `form_filling_example.json` - Form automation
- And more...

Load these through the UI to test your setup.

## Requirements

- macOS 10.15+ (Catalina or later)
- 500MB free disk space
- Internet connection (for setup)

The SETUP.sh script will install:
- uv (Python package manager)
- Python 3.11 (via uv)
- All Python dependencies

## Troubleshooting

### "App is damaged" error
```bash
xattr -cr "/Applications/Local Browser Agent.app"
```

### Setup script fails
```bash
# Manually install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Re-run setup
./SETUP.sh
```

### Python not found
The app uses the venv inside the bundle. If it fails, re-run SETUP.sh or use the UI setup button.
