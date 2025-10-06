#!/bin/bash
# Setup script for Step Functions Agent development environment

echo "🔧 Setting up Step Functions Agent development environment..."

# Check if virtual environment exists
if [ -d "cpython-3.12.3-macos-aarch64-none" ]; then
    echo "✅ Found virtual environment"
    echo "   Activating: source cpython-3.12.3-macos-aarch64-none/bin/activate"
    source cpython-3.12.3-macos-aarch64-none/bin/activate
elif [ -d ".venv" ]; then
    echo "✅ Found .venv virtual environment"
    echo "   Activating: source .venv/bin/activate"
    source .venv/bin/activate
else
    echo "❌ No virtual environment found!"
    echo "   Please create a virtual environment first:"
    echo "   python3 -m venv cpython-3.12.3-macos-aarch64-none"
    exit 1
fi

# Check if uv is available (faster pip alternative)
if command -v uv &> /dev/null; then
    echo "✅ Using uv for dependency installation"
    echo "   Installing dependencies..."
    uv pip install -r requirements.txt
else
    echo "📦 Using pip for dependency installation"
    echo "   Installing dependencies..."
    pip install -r requirements.txt
fi

# Verify key dependencies
echo ""
echo "🔍 Verifying key dependencies..."
python -c "import cdk_monitoring_constructs; print('✅ cdk-monitoring-constructs installed')" 2>/dev/null || echo "❌ cdk-monitoring-constructs NOT installed"
python -c "import aws_cdk; print('✅ aws-cdk-lib installed')" 2>/dev/null || echo "❌ aws-cdk-lib NOT installed"
python -c "import constructs; print('✅ constructs installed')" 2>/dev/null || echo "❌ constructs NOT installed"

echo ""
echo "📝 Next steps:"
echo "   1. Configure AWS credentials: assume CGI-PoC"
echo "   2. Deploy main infrastructure: cdk deploy --app 'python refactored_app.py' --all --profile CGI-PoC"
echo "   3. Deploy long content: cdk deploy --app 'python long_content_app.py' --all --profile CGI-PoC"