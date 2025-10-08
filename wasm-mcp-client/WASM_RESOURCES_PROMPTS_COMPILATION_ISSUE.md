# WASM Compilation Issue: Resources and Prompts Support

## Issue Summary

When attempting to add `list_resources`, `read_resource`, `list_prompts`, and `get_prompt` methods to the WASM MCP client, compilation fails due to errors in the pmcp Rust SDK.

## Environment

- **SDK**: pmcp v1.7.0 (local development version)
- **SDK Path**: `/Users/guy/Development/mcp/sdk/rust-mcp-sdk`
- **WASM Client**: `/Users/guy/projects/step-functions-agent/wasm-mcp-client`
- **Target**: wasm32-unknown-unknown
- **Build Tool**: wasm-pack build --target web

## Current Status

**Working**:
- ✅ `initialize()` - MCP connection initialization
- ✅ `list_tools()` - List available tools
- ✅ `call_tool()` - Execute tools

**Not Working** (due to compilation errors):
- ❌ `list_resources()` - List available resources
- ❌ `read_resource()` - Read a specific resource
- ❌ `list_prompts()` - List available prompts
- ❌ `get_prompt()` - Get a prompt with arguments

## Compilation Errors

### Error 1: Unresolved Import `error_codes`

```
error[E0432]: unresolved import `crate::server::error_codes`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:237:24
    |
237 | pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    |                        ^^^^^^^^^^^ could not find `error_codes` in `server`
    |
note: found an item that was configured out
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:71:9
    |
71  | pub mod error_codes;
    |         ^^^^^^^^^^^
note: the item is gated here
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:70:1
    |
70  | #[cfg(not(target_arch = "wasm32"))]
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**Root Cause**: The `error_codes` module is conditionally compiled only for non-WASM targets, but `wasm_typed_tool.rs` tries to import it unconditionally.

**Location**:
- `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:70-71`
- `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:237`
- `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:241`

### Error 2: Missing `clone()` Method

```
error[E0599]: no method named `clone` found for type parameter `impl Into<String>` in the current scope
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:220:56
    |
212 |         name: impl Into<String>,
    |               ----------------- method `clone` not found for this type parameter
...
220 |         let tool = WasmTypedTool::new_with_schema(name.clone(), schema, handler);
    |                                                        ^^^^^ method not found in `impl Into<String>`
```

**Root Cause**: The `name` parameter has type `impl Into<String>` which doesn't guarantee a `clone()` method. The trait bound needs to be expanded to `impl Into<String> + Clone`.

**Location**: `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:220`

**Suggested Fix**:
```rust
// Change from:
name: impl Into<String>,

// To:
name: impl Into<String> + Clone,
```

## Warnings

### Warning 1: Unexpected cfg Condition

```
warning: unexpected `cfg` condition value: `wasi-http`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasi_adapter.rs:175:35
    |
175 | #[cfg(all(target_arch = "wasm32", feature = "wasi-http"))]
    |                                   ^^^^^^^^^^^^^^^^^^^^^
```

**Impact**: Low - This is just a warning about a feature flag that doesn't exist in Cargo.toml

### Warning 2: Unused Mutable Variable

```
warning: variable does not need to be mutable
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/shared/wasm_http.rs:126:13
    |
126 |         let mut request_init = RequestInit::new();
    |             ----^^^^^^^^^^^^
```

**Impact**: Low - Code quality issue, not a blocker

### Warning 3: Unused Import

```
warning: unused import: `Error`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:242:17
    |
242 |     use crate::{Error, Result};
    |                 ^^^^^
```

**Impact**: Low - Code quality issue, not a blocker

## Changes Made to WASM Client

The following methods were added to `wasm-mcp-client/src/lib.rs`:

```rust
/// List all available resources using pmcp
#[wasm_bindgen]
pub async fn list_resources(&mut self) -> Result<JsValue, JsValue> { ... }

/// Read a specific resource using pmcp
#[wasm_bindgen]
pub async fn read_resource(&mut self, uri: String) -> Result<JsValue, JsValue> { ... }

/// List all available prompts using pmcp
#[wasm_bindgen]
pub async fn list_prompts(&mut self) -> Result<JsValue, JsValue> { ... }

/// Get a prompt with arguments using pmcp
#[wasm_bindgen]
pub async fn get_prompt(&mut self, name: String, arguments: JsValue) -> Result<JsValue, JsValue> { ... }
```

These methods follow the same pattern as `list_tools()` and `call_tool()` which work correctly.

## Full Compilation Output

```
[INFO]: 🎯  Checking for the Wasm target...
[INFO]: 🌀  Compiling to Wasm...
   Compiling pmcp v1.7.0 (/Users/guy/Development/mcp/sdk/rust-mcp-sdk)
error[E0432]: unresolved import `crate::server::error_codes`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:237:24
    |
237 | pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    |                        ^^^^^^^^^^^ could not find `error_codes` in `server`
    |
note: found an item that was configured out
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:71:9
    |
71  | pub mod error_codes;
    |         ^^^^^^^^^^^
note: the item is gated here
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:70:1
    |
70  | #[cfg(not(target_arch = "wasm32"))]
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

error[E0432]: unresolved import `crate::server::error_codes`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:241:24
    |
241 |     use crate::server::error_codes::{ValidationError, ValidationErrorCode};
    |                        ^^^^^^^^^^^ could not find `error_codes` in `server`
    |
note: found an item that was configured out
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:71:9
    |
71  | pub mod error_codes;
    |         ^^^^^^^^^^^
note: the item is gated here
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs:70:1
    |
70  | #[cfg(not(target_arch = "wasm32"))]
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

warning: unused import: `Error`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:242:17
    |
242 |     use crate::{Error, Result};
    |                 ^^^^^
    |
    = note: `#[warn(unused_imports)]` on by default

warning: unexpected `cfg` condition value: `wasi-http`
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasi_adapter.rs:175:35
    |
175 | #[cfg(all(target_arch = "wasm32", feature = "wasi-http"))]
    |                                   ^^^^^^^^^^^^^^^^^^^^^
    |
    = note: expected values for `feature` are: `authentication_example`, `cancellation_example`, `default`, `full`, `http`, `progress_example`, `rayon`, `resource-watcher`, `schema-generation`, `simd`, `sse`, `streamable-http`, `test-helpers`, `unstable`, `validation`, `wasm`, `wasm-tokio`, `websocket`, and `websocket-wasm`
    = help: consider adding `wasi-http` as a feature in `Cargo.toml`
    = note: see <https://doc.rust-lang.org/nightly/rustc/check-cfg/cargo-specifics.html> for more information about checking conditional configuration
    = note: `#[warn(unexpected_cfgs)]` on by default

warning: variable does not need to be mutable
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/shared/wasm_http.rs:126:13
    |
126 |         let mut request_init = RequestInit::new();
    |             ----^^^^^^^^^^^^
    |             |
    |             help: remove this `mut`
    |
    = note: `#[warn(unused_mut)]` on by default

error[E0599]: no method named `clone` found for type parameter `impl Into<String>` in the current scope
   --> /Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:220:56
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

Some errors have detailed explanations: E0432, E0599.
For more information about an error, try `rustc --explain E0432`.
warning: `pmcp` (lib) generated 3 warnings
error: could not compile `pmcp` (lib) due to 3 previous errors; 3 warnings emitted
Error: Compiling your crate to WebAssembly failed
Caused by: Compiling your crate to WebAssembly failed
Caused by: failed to execute `cargo build`: exited with exit status: 101
  full command: cd "/Users/guy/projects/step-functions-agent/wasm-mcp-client" && "cargo" "build" "--lib" "--release" "--target" "wasm32-unknown-unknown"
```

## Impact

**Current Functionality**: Users can test MCP servers with tools functionality only.

**Missing Functionality**:
- Cannot browse or read MCP server resources (documentation, data files, etc.)
- Cannot list or test MCP server prompts (workflows, templates)

## Workaround

For now, the WASM client can still be used to:
1. Connect to MCP servers
2. List available tools
3. Execute tools with parameters
4. View tool results

This covers the primary use case for testing MCP servers, but full MCP protocol support requires resources and prompts.

## Suggested Fixes

### Fix 1: Conditional Compilation for error_codes

In `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs`:

```rust
// Change line 237:
#[cfg(not(target_arch = "wasm32"))]
pub use crate::server::error_codes::{ValidationError, ValidationErrorCode};

// Change line 241 (inside a function):
#[cfg(not(target_arch = "wasm32"))]
use crate::server::error_codes::{ValidationError, ValidationErrorCode};
```

Or make `error_codes` module available for WASM targets.

### Fix 2: Add Clone Bound

In `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs:212`:

```rust
// Change from:
pub fn new_with_handler(
    name: impl Into<String>,
    description: impl Into<String>,
    handler: impl Fn(Value) -> Result<Value> + 'static,
) -> Self

// To:
pub fn new_with_handler(
    name: impl Into<String> + Clone,
    description: impl Into<String>,
    handler: impl Fn(Value) -> Result<Value> + 'static,
) -> Self
```

## Next Steps

1. Fix the pmcp SDK WASM compilation errors
2. Rebuild WASM client with resource and prompt methods
3. Update React UI component to add tabs for Resources and Prompts
4. Test complete MCP protocol support in browser

## Related Files

- **WASM Client**: `/Users/guy/projects/step-functions-agent/wasm-mcp-client/src/lib.rs`
- **SDK Server Module**: `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/mod.rs`
- **SDK WASM Tool**: `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/server/wasm_typed_tool.rs`
- **SDK WASM HTTP**: `/Users/guy/Development/mcp/sdk/rust-mcp-sdk/src/shared/wasm_http.rs`
- **UI Component**: `/Users/guy/projects/step-functions-agent/ui_amplify/src/components/WasmMcpClient.tsx`

## Expected Outcome

Once fixed, users will be able to:
1. Browse MCP server resources (guides, documentation, data)
2. Read resource contents
3. List available prompts/workflows
4. Execute prompts with parameters
5. Complete end-to-end MCP server testing in the browser

This will provide full MCP protocol coverage for browser-based testing without needing backend Lambda functions.
