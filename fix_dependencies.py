#!/usr/bin/env python3
"""
Quick dependency check and fix script for Step Functions Agent
"""

import subprocess
import sys
import os

def check_dependency(module_name, package_name=None):
    """Check if a Python module is installed"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

def main():
    print("🔍 Checking Step Functions Agent dependencies...\n")
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("⚠️  WARNING: Not running in a virtual environment!")
        print("   It's recommended to use a virtual environment.")
        print("   Activate with: source cpython-3.12.3-macos-aarch64-none/bin/activate")
        print("")
    
    # Check critical dependencies
    dependencies = [
        ("cdk_monitoring_constructs", "cdk-monitoring-constructs"),
        ("aws_cdk", "aws-cdk-lib"),
        ("constructs", "constructs"),
        ("boto3", "boto3"),
        ("anthropic", "anthropic"),
        ("openai", "openai"),
    ]
    
    missing = []
    for module_name, package_name in dependencies:
        if not check_dependency(module_name, package_name):
            missing.append(package_name)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} dependencies: {', '.join(missing)}")
        print("\n📦 To install missing dependencies, run:")
        print("   pip install -r requirements.txt")
        print("\n   Or if you have uv installed (faster):")
        print("   uv pip install -r requirements.txt")
        
        # Offer to install
        response = input("\nWould you like to install them now? (y/n): ")
        if response.lower() == 'y':
            print("\nInstalling dependencies...")
            try:
                # Check if uv is available
                subprocess.run(["uv", "--version"], capture_output=True, check=True)
                subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=True)
            except:
                # Fall back to pip
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("\n✅ Dependencies installed!")
    else:
        print("\n✅ All dependencies are installed!")
    
    # Additional checks
    print("\n📋 Additional information:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    
    # Check for AWS CDK CLI
    try:
        result = subprocess.run(["cdk", "--version"], capture_output=True, text=True)
        print(f"   CDK CLI version: {result.stdout.strip()}")
    except:
        print("   ❌ CDK CLI not found. Install with: npm install -g aws-cdk")

if __name__ == "__main__":
    main()