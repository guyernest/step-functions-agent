# CLAUDE.md - Local SQS Agent Guidelines

## Build & Test Commands
```bash
# Build the project
cargo build

# Run the project
cargo run

# Run all tests
cargo test

# Run a specific test
cargo test test_process_message

# Run integration tests (requires AWS credentials)
cargo test -- --ignored

# Check code coverage
cargo tarpaulin --out Html

# Lint the code
cargo clippy
```

## Code Style Guidelines
- **Imports**: Group standard library, external, and internal imports separately
- **Error Handling**: Use `anyhow` for application errors with context via `.context()` or `anyhow!()`
- **Naming**: Use snake_case for variables/functions, CamelCase for types/structs
- **Types**: Always provide explicit types for struct fields and function returns
- **Logging**: Use log crate levels (info, error, etc.) appropriately based on severity
- **Comments**: Document public functions/structs with doc comments (///)
- **Testing**: Write unit tests for all functions, mock external services
- **Formatting**: Use rustfmt for consistent code style (max 100 chars per line)
- **Config**: External configuration should be loaded from JSON files via config crate