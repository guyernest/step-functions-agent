# Lambda Deployment for Local Automation Tool

## Overview
The local-agent directory contains both a Tauri desktop application and a Rust Lambda function.
To avoid Lambda deployment size issues, we only deploy the Lambda binary.

## Problem
The directory contains:
- Tauri desktop app (`src-tauri/` - 7.7GB!)
- Node.js dependencies (`node_modules/` - 198MB)
- Rust Lambda function (`src/` - actual Lambda code)

Lambda has a 250MB uncompressed size limit, so we can't deploy everything.

## Solution
We build the Rust Lambda function separately and deploy only the compiled binary:
1. Build using `cargo lambda` (creates ~10MB binary)
2. Copy binary to `deployment/` directory
3. CDK deploys only the `deployment/` directory

## Build Process

### Manual Build
```bash
cd lambda/tools/local-agent
make all  # Builds and prepares deployment
```

### What it does:
1. Installs `cargo-lambda` if needed
2. Builds the Lambda function: `cargo lambda build --release --arm64`
3. Copies the binary to `deployment/bootstrap`
4. Result: `deployment/` contains only the 10MB bootstrap file

### Automatic Build
The main project Makefile includes this:
```bash
make build-rust  # Builds all Rust tools including local-agent
```

## Deployment
The CDK stack (`local_automation_tool_stack.py`) now:
1. Looks for `deployment/bootstrap`
2. Fails with clear error if not built
3. Deploys only the `deployment/` directory

## Directory Structure
```
lambda/tools/local-agent/
├── src/                    # Lambda source code
├── src-tauri/             # Desktop app (NOT deployed)
├── node_modules/          # Desktop app deps (NOT deployed)
├── deployment/            # Lambda deployment directory
│   └── bootstrap          # Compiled Lambda binary (ONLY this is deployed)
├── Makefile               # Build automation
└── .lambdaignore          # Excludes unnecessary files
```

## Troubleshooting

### "Bootstrap binary not found" Error
```bash
cd lambda/tools/local-agent
make all
```

### Lambda too large Error
Check that `deployment/` only contains `bootstrap`:
```bash
ls -lah lambda/tools/local-agent/deployment/
# Should show only bootstrap (~10MB)
```

### Build Failures
Ensure Rust and cargo-lambda are installed:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install cargo-lambda
```

## Important Notes
- Never deploy the entire `local-agent/` directory
- The `src-tauri/` directory is for the desktop app only
- Always use the Makefile to ensure consistent builds
- The Lambda binary must be named `bootstrap` for AWS Lambda runtime