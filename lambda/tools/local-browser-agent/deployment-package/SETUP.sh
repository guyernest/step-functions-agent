#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════════"
echo "  Local Browser Agent - macOS/Linux Setup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check dependencies
echo "───────────────────────────────────────────────────────────"
echo "Step 1: Checking for UV package manager"
echo "───────────────────────────────────────────────────────────"

command -v uv >/dev/null 2>&1 || {
    echo "  ✗ UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add to PATH for current session
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
}

echo "  ✓ UV package manager found"

# Find the installed app
APP_PATH="/Applications/Local Browser Agent.app"
if [ ! -d "$APP_PATH" ]; then
    echo ""
    echo "Error: App not found at $APP_PATH"
    echo "Please install the .dmg first: open *.dmg"
    exit 1
fi

echo ""
echo "✓ Found app at: $APP_PATH"

# Create Python virtual environment inside the app bundle
echo ""
echo "───────────────────────────────────────────────────────────"
echo "Step 2: Creating Python virtual environment"
echo "───────────────────────────────────────────────────────────"

PYTHON_DIR="$APP_PATH/Contents/Resources/_up_/python"
cd "$PYTHON_DIR"

echo "  Creating Python 3.11 venv..."
uv venv --python 3.11 .venv
echo "  ✓ Python 3.11 virtual environment created"

echo ""
echo "───────────────────────────────────────────────────────────"
echo "Step 3: Installing Python dependencies"
echo "───────────────────────────────────────────────────────────"

echo "  Installing from requirements.txt..."
uv pip install --python .venv/bin/python -r requirements.txt
echo "  ✓ Python dependencies installed"

# Install Playwright Chromium
echo ""
echo "───────────────────────────────────────────────────────────"
echo "Step 4: Installing Playwright browsers"
echo "───────────────────────────────────────────────────────────"

echo "  Installing Chromium only (Chrome can be used via system)"
echo ""
.venv/bin/python -m playwright install chromium --with-deps
echo "  ✓ Chromium browser installed"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✓ Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Browser Configuration:"
echo "  • Google Chrome (recommended for macOS)"
echo "    Install separately if needed"
echo ""
echo "  • Chromium (fallback)"
echo "    Installed by this script"
echo ""
echo "Next Steps:"
echo "  1. Launch 'Local Browser Agent' from Applications"
echo "  2. Go to Configuration → Browser Channel"
echo "  3. Select 'Google Chrome' (recommended)"
echo "  4. Configure AWS credentials"
echo "  5. Test with an example script"
echo ""
echo "Python environment: $PYTHON_DIR/.venv"
echo ""
