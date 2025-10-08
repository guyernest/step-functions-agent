# WASM Compilation Error in pmcp v1.7.0 (Published Version)

## Status: ✅ RESOLVED in Local SDK

The local version of pmcp SDK at `~/Development/mcp/sdk/rust-mcp-sdk/` successfully compiles to WASM. The issues described below affect only the **published v1.7.0 crate on crates.io**.

## Summary

The pmcp v1.7.0 crate **published on crates.io** fails to compile to WebAssembly (wasm32-unknown-unknown target) due to incorrect conditional compilation of the `error_codes` module and a missing trait bound in `wasm_typed_tool.rs`.

## Environment

- **pmcp version**: 1.7.0
- **wasm-pack version**: 0.13.1
- **Rust version**: 1.82.0+ (stable)
- **Target**: wasm32-unknown-unknown
- **Build command**: `wasm-pack build --target web`

## Workaround

Currently using pmcp v1.2.2 which compiles successfully to WASM.

```toml
# Cargo.toml
[dependencies]
pmcp = { version = "=1.2.2", default-features = false, features = ["wasm"] }
```

## Error Details

### Error 1: Unresolved Import `error_codes`

**File**: `src/server/wasm_typed_tool.rs:237:24`

```
error[E0432]: unresolved import `crate::server::error_codes`
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/wasm_typed_tool.rs:237:24
    |
237 | pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    |                        ^^^^^^^^^^^ could not find `error_codes` in `server`
    |
note: found an item that was configured out
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/mod.rs:71:9
    |
71  | pub mod error_codes;
    |         ^^^^^^^^^^^
note: the item is gated here
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/mod.rs:70:1
    |
70  | #[cfg(not(target_arch = "wasm32"))]
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**Root Cause**: The `error_codes` module is conditionally compiled with `#[cfg(not(target_arch = "wasm32"))]` in `src/server/mod.rs`, but `wasm_typed_tool.rs` unconditionally imports it at line 237 and 241.

**Affected Lines**:
- `src/server/wasm_typed_tool.rs:237` - Public re-export
- `src/server/wasm_typed_tool.rs:241` - Use statement in tests

### Error 2: Missing Clone Trait Bound

**File**: `src/server/wasm_typed_tool.rs:220:56`

```
error[E0599]: no method named `clone` found for type parameter `impl Into<String>` in the current scope
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/wasm_typed_tool.rs:220:56
    |
212 |         name: impl Into<String>,
    |               ----------------- method `clone` not found for this type parameter
...
220 |         let tool = WasmTypedTool::new_with_schema(name.clone(), schema, handler);
    |                                                        ^^^^^ method not found in `impl Into<String>`
    |
    = help: items from traits can only be used if the type parameter is bounded by the trait
help: the following trait defines an item `clone`, perhaps you need to restrict type parameter `impl Into<String>` with it:
    |
212 |         name: impl Into<String> + Clone,
    |                                 +++++++
```

**Root Cause**: Line 212 defines a parameter `name: impl Into<String>` but line 220 tries to call `name.clone()` without a `Clone` bound.

**Affected Code**:
```rust
// Line 212
pub fn new_with_description(
    name: impl Into<String>,  // Missing Clone bound
    description: impl Into<String>,
    schema: serde_json::Value,
    handler: F,
) -> Self {
    // ...
    // Line 220
    let tool = WasmTypedTool::new_with_schema(name.clone(), schema, handler);
    //                                             ^^^^^^^ Error: no method named `clone`
}
```

## Suggested Fixes

### Fix 1: Conditional Compilation for error_codes Import

**File**: `src/server/wasm_typed_tool.rs`

**Current Code** (lines 237-241):
```rust
// Unconditional public re-export
pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};

#[cfg(test)]
mod tests {
    use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    // ...
}
```

**Suggested Fix**:
```rust
// Conditional public re-export
#[cfg(not(target_arch = "wasm32"))]
pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};

#[cfg(test)]
mod tests {
    #[cfg(not(target_arch = "wasm32"))]
    use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    // ...
}
```

**Alternative**: Create WASM-compatible error types or use a different error handling approach for WASM targets.

### Fix 2: Add Clone Bound

**File**: `src/server/wasm_typed_tool.rs`

**Current Code** (line 212):
```rust
pub fn new_with_description(
    name: impl Into<String>,
    description: impl Into<String>,
    schema: serde_json::Value,
    handler: F,
) -> Self {
```

**Suggested Fix**:
```rust
pub fn new_with_description(
    name: impl Into<String> + Clone,
    description: impl Into<String>,
    schema: serde_json::Value,
    handler: F,
) -> Self {
```

**Alternative**: Convert to String immediately and avoid cloning:
```rust
pub fn new_with_description(
    name: impl Into<String>,
    description: impl Into<String>,
    schema: serde_json::Value,
    handler: F,
) -> Self {
    let name_str = name.into();  // Convert once
    let mut tool = WasmTypedTool::new_with_schema(&name_str, schema, handler);
    tool.description = Some(description.into());
    tool
}
```

## Full Compilation Output

```
[INFO]: 🎯  Checking for the Wasm target...
[INFO]: 🌀  Compiling to Wasm...
   Compiling pmcp v1.7.0
error[E0432]: unresolved import `crate::server::error_codes`
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/wasm_typed_tool.rs:237:24
    |
237 | pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    |                        ^^^^^^^^^^^ could not find `error_codes` in `server`

error[E0432]: unresolved import `crate::server::error_codes`
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/wasm_typed_tool.rs:241:24
    |
241 |     use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    |                        ^^^^^^^^^^^ could not find `error_codes` in `server`

error[E0599]: no method named `clone` found for type parameter `impl Into<String>` in the current scope
   --> /Users/guy/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/pmcp-1.7.0/src/server/wasm_typed_tool.rs:220:56
    |
212 |         name: impl Into<String>,
    |               ----------------- method `clone` not found for this type parameter
...
220 |         let tool = WasmTypedTool::new_with_schema(name.clone(), schema, handler);
    |                                                        ^^^^^ method not found in `impl Into<String>`

Some errors have detailed explanations: E0432, E0599.
For more information about an error, try `rustc --explain E0432`.
error: could not compile `pmcp` (lib) due to 3 previous errors
Error: Compiling your crate to WebAssembly failed
Caused by: failed to execute `cargo build`: exited with exit status: 101
```

## Impact

This prevents using pmcp v1.7.0 for WASM-based MCP clients in browser applications. Users must downgrade to v1.2.2 to compile successfully.

## Use Case

We're building a browser-based MCP management UI that:
- Tests MCP servers interactively from the browser
- Executes YAML test scenarios client-side
- Provides zero-backend-cost testing for MCP servers
- Demonstrates MCP capabilities in presentations

The WASM client is essential for this use case as it eliminates Lambda cold starts and provides instant feedback.

## Testing

To reproduce:

```bash
# Create a new WASM wrapper crate
cargo new --lib test-wasm-client
cd test-wasm-client

# Edit Cargo.toml
cat > Cargo.toml <<EOF
[package]
name = "test-wasm-client"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pmcp = { version = "1.7.0", default-features = false, features = ["wasm"] }
wasm-bindgen = "0.2"
EOF

# Try to build
wasm-pack build --target web
# Result: Compilation errors as described above
```

## Verification

### ✅ Confirmed: Local SDK Compiles Successfully

Using the local SDK version, WASM compilation succeeds:

```toml
# Cargo.toml
[dependencies]
pmcp = { path = "/Users/guy/Development/mcp/sdk/rust-mcp-sdk", default-features = false, features = ["wasm"] }
```

**Build Output:**
```
[INFO]: 🌀  Compiling to Wasm...
   Compiling pmcp v1.7.0 (/Users/guy/Development/mcp/sdk/rust-mcp-sdk)
warning: `pmcp` (lib) generated 33 warnings
   Compiling mcp-management-wasm-client v0.1.0
    Finished `release` profile [optimized] target(s) in 17.98s
[INFO]: ✨   Done in 19.43s
[INFO]: 📦   Your wasm pkg is ready to publish
```

The local version has the fixes applied and compiles successfully to WASM.

## Request

Please **publish the latest version of pmcp** (with WASM fixes) to crates.io so that the broader community can use pmcp in browser-based applications without needing local path dependencies.

Thank you for maintaining this excellent SDK!

## Related Files

- `src/server/mod.rs` - Module declarations with conditional compilation
- `src/server/wasm_typed_tool.rs` - WASM-specific typed tool implementation
- `src/server/error_codes.rs` - Error codes module (not available in WASM)
