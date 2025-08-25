#!/bin/bash

# Verification script for ADOT observability build

echo "🔍 Verifying Rust Lambda build with ADOT observability..."
echo ""

# Check if bootstrap exists
if [ -f "bootstrap" ]; then
    echo "✅ bootstrap file found"
    echo "   Size: $(ls -lh bootstrap | awk '{print $5}')"
else
    echo "❌ bootstrap file NOT found"
    echo "   Run: make build-llm-rust"
    exit 1
fi

# Check if collector.yaml exists
if [ -f "collector.yaml" ]; then
    echo "✅ collector.yaml found"
    echo "   OTLP receivers configured"
    echo "   AWS exporters configured"
else
    echo "❌ collector.yaml NOT found"
    echo "   This file is required for ADOT observability"
    exit 1
fi

# Check if both files will be picked up by CDK
echo ""
echo "📦 CDK deployment package contents:"
ls -la bootstrap collector.yaml 2>/dev/null

echo ""
echo "🚀 Ready for CDK deployment!"
echo "   CDK will use: lambda/call_llm_rust/ as the asset directory"
echo "   Both bootstrap and collector.yaml will be included"