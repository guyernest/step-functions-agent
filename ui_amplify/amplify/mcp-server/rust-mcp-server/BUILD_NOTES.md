# MCP Server Build Notes

## Build Strategy
We pre-build the Rust Lambda binary locally and commit it to the repository.
This avoids cross-compilation issues in the Amplify CI/CD pipeline.

## Building the MCP Server

```bash
# From this directory
make build

# Or from the ui_amplify root
cd amplify/mcp-server/rust-mcp-server && make build
```

This creates `.build/rust-mcp-server/bootstrap` which is used by Amplify deployment.

## Why Pre-build?
1. **Avoids CI/CD complexity**: No need to install Rust, cargo-lambda, or Zig in Amplify build
2. **Consistent with project pattern**: Other Rust Lambdas in the project follow this approach
3. **Faster deployments**: Skip compilation during deployment
4. **Reliable**: No cross-compilation issues or toolchain problems

## Important
- The `.build/` directory is NOT gitignored (intentionally)
- Remember to rebuild and commit when making changes to the Rust code
- The binary is built for `x86_64-unknown-linux-gnu` (Lambda runtime)

## Architecture
- Target: x86_64-unknown-linux-gnu
- Runtime: provided.al2023
- Handler: bootstrap