# Browser Agent Architecture Refactoring Proposal

## Current Problems

### 1. **Code Duplication Across Execution Paths**

We have **TWO separate execution paths** with duplicated logic:

#### Path A: Activity Poller (`nova_act_executor.rs` → `nova_act_wrapper.py`)
- ✅ **Respects `browser_engine` config**
- ✅ **Sets environment variables** (`USE_COMPUTER_AGENT`, `OPENAI_API_KEY`, `OPENAI_MODEL`)
- ✅ **Dynamically selects wrapper** (`nova_act_wrapper.py` vs `computer_agent_wrapper.py`)
- Used by: Step Functions Activity tasks

#### Path B: Test UI (`test_commands.rs` → `script_executor.py`)
- ❌ **Ignores `browser_engine` config**
- ❌ **Only passes Nova Act API key**
- ❌ **Always uses Nova Act** (hardcoded)
- Used by: Local testing UI

### 2. **Specific Issues in Path B**

**File: `test_commands.rs:519-585`**
```rust
// PROBLEM 1: Only reads nova_act_api_key, ignores browser_engine
let nova_act_api_key = current_config.nova_act_api_key.clone();

// PROBLEM 2: Hardcoded "Nova Act" in logs
log::info!("Step 6: Nova Act API key provided");

// PROBLEM 3: No environment variables for OpenAI
// Missing: USE_COMPUTER_AGENT, OPENAI_API_KEY, OPENAI_MODEL
```

**File: `script_executor.py`**
```python
# PROBLEM 4: Doesn't check USE_COMPUTER_AGENT env var
# Always uses nova_act_wrapper.py
```

### 3. **User Impact**

When user configures OpenAI Computer Agent in UI:
1. ✅ Activity Poller **correctly** uses OpenAI Computer Agent
2. ❌ Test UI **incorrectly** uses Nova Act (despite showing success)
3. ❌ User gets false confidence from test

This is **dangerous** because:
- Tests pass with Nova Act
- Production uses OpenAI Computer Agent
- Different behavior between test and production
- Debugging nightmare

---

## Proposed Solution: Unified Execution Layer

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Rust Application Layer                   │
├─────────────────────────────────────────────────────────────┤
│  activity_poller.rs     │     test_commands.rs             │
│  (Step Functions)        │     (Local Testing)               │
└────────────┬─────────────┴──────────────┬───────────────────┘
             │                            │
             │    ┌──────────────────────┐│
             └────┤ script_executor.rs   ││  ← NEW UNIFIED MODULE
                  │ (Shared Logic)       ││
                  └──────────┬───────────┘│
                             │            │
                  ┌──────────▼────────────▼─────────────┐
                  │   Environment Configuration          │
                  │   - USE_COMPUTER_AGENT               │
                  │   - OPENAI_API_KEY / NOVA_ACT_API_KEY│
                  │   - OPENAI_MODEL                     │
                  │   - Browser channel, headless, etc.  │
                  └──────────┬───────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │   Python subprocess          │
              │   script_executor.py         │
              └──────────────┬───────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
    ┌────▼───────────────┐         ┌───────────▼────────────┐
    │ nova_act_wrapper.py│         │computer_agent_wrapper.py│
    └────────────────────┘         └────────────────────────┘
```

### New Unified Module: `script_executor.rs`

```rust
// src-tauri/src/script_executor.rs

use anyhow::Result;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::process::Command;

use crate::config::Config;
use crate::paths::AppPaths;

/// Unified script execution configuration
pub struct ScriptExecutionConfig {
    pub script_content: String,
    pub aws_profile: String,
    pub s3_bucket: Option<String>,
    pub headless: bool,
    pub browser_channel: Option<String>,
    pub navigation_timeout: u64,
}

/// Unified script executor for both Activity Poller and Test UI
pub struct ScriptExecutor {
    config: Arc<Config>,
    python_path: PathBuf,
    script_executor_path: PathBuf,
}

impl ScriptExecutor {
    /// Create new script executor
    pub fn new(config: Arc<Config>) -> Result<Self> {
        // Find Python executable
        let python_path = Self::find_python_executable()?;

        // Find script_executor.py
        let script_executor_path = Self::find_script_executor()?;

        // Set environment variables based on config
        Self::configure_environment(&config)?;

        Ok(Self {
            config,
            python_path,
            script_executor_path,
        })
    }

    /// Configure environment variables for Python subprocess
    fn configure_environment(config: &Config) -> Result<()> {
        // Determine which browser engine to use
        let use_computer_agent = config.browser_engine == "computer_agent";
        std::env::set_var("USE_COMPUTER_AGENT", use_computer_agent.to_string());

        if use_computer_agent {
            // Set OpenAI configuration
            if let Some(ref api_key) = config.openai_api_key {
                std::env::set_var("OPENAI_API_KEY", api_key);
            }
            std::env::set_var("OPENAI_MODEL", &config.openai_model);
            std::env::set_var("ENABLE_REPLANNING", config.enable_replanning.to_string());
            std::env::set_var("MAX_REPLANS", config.max_replans.to_string());

            log::info!("✓ Configured OpenAI Computer Agent ({})", config.openai_model);
        } else {
            // Set Nova Act configuration
            if let Some(ref api_key) = config.nova_act_api_key {
                std::env::set_var("NOVA_ACT_API_KEY", api_key);
            }

            log::info!("✓ Configured Nova Act");
        }

        Ok(())
    }

    /// Execute a browser automation script
    pub async fn execute(&self, exec_config: ScriptExecutionConfig) -> Result<ExecutionResult> {
        // Write script to temp file
        let temp_file = tempfile::NamedTempFile::new()?;
        std::fs::write(temp_file.path(), &exec_config.script_content)?;

        // Build command
        let mut cmd = Command::new(&self.python_path);
        cmd.arg(&self.script_executor_path);
        cmd.arg("--script").arg(temp_file.path());
        cmd.arg("--aws-profile").arg(&exec_config.aws_profile);
        cmd.arg("--navigation-timeout").arg(exec_config.navigation_timeout.to_string());

        if exec_config.headless {
            cmd.arg("--headless");
        }

        if let Some(ref bucket) = exec_config.s3_bucket {
            cmd.arg("--s3-bucket").arg(bucket);
        }

        if let Some(ref channel) = exec_config.browser_channel {
            cmd.arg("--browser-channel").arg(channel);
        }

        // Log execution details
        self.log_execution_details(&exec_config);

        // Execute
        let output = cmd
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await?;

        // Parse results
        self.parse_output(output)
    }

    fn log_execution_details(&self, exec_config: &ScriptExecutionConfig) {
        log::info!("═══ Script Execution ═══");
        log::info!("Engine: {}", match self.config.browser_engine.as_str() {
            "computer_agent" => format!("OpenAI Computer Agent ({})", self.config.openai_model),
            _ => "Nova Act".to_string(),
        });
        log::info!("AWS Profile: {}", exec_config.aws_profile);
        log::info!("Headless: {}", exec_config.headless);
        if let Some(ref channel) = exec_config.browser_channel {
            log::info!("Browser: {}", channel);
        }
        log::info!("═════════════════════");
    }

    // ... helper methods: find_python_executable, find_script_executor, parse_output
}
```

### Updated Python Layer: `script_executor.py`

```python
#!/usr/bin/env python3
"""
Unified script executor that respects USE_COMPUTER_AGENT environment variable.
Works with both nova_act_wrapper.py and computer_agent_wrapper.py.
"""

import os
import sys
from pathlib import Path

def get_wrapper_module():
    """Dynamically select wrapper based on USE_COMPUTER_AGENT env var"""
    use_computer_agent = os.environ.get('USE_COMPUTER_AGENT', 'false').lower() == 'true'

    if use_computer_agent:
        try:
            from computer_agent_wrapper import execute_browser_command
            print(f"✓ Using OpenAI Computer Agent (model: {os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')})",
                  file=sys.stderr)
            return execute_browser_command
        except ImportError as e:
            print(f"✗ Failed to import computer_agent_wrapper: {e}", file=sys.stderr)
            print("  Falling back to Nova Act", file=sys.stderr)

    # Fall back to Nova Act
    from nova_act_wrapper import execute_browser_command
    print("✓ Using Nova Act", file=sys.stderr)
    return execute_browser_command

def main():
    # Get the appropriate wrapper
    execute_command = get_wrapper_module()

    # ... rest of script execution logic (unchanged)
```

---

## Benefits of Refactoring

### 1. **Single Source of Truth**
- ✅ One place for browser engine selection logic
- ✅ One place for environment configuration
- ✅ One place for Python subprocess execution

### 2. **Consistency**
- ✅ Test UI uses **same code** as Activity Poller
- ✅ Test results **match** production behavior
- ✅ No more "works in test, fails in production"

### 3. **Maintainability**
- ✅ Fix bug once, fixes everywhere
- ✅ Add feature once, available everywhere
- ✅ Less code to maintain

### 4. **Testability**
- ✅ Can unit test `ScriptExecutor` independently
- ✅ Mock environment variables for testing
- ✅ Test both engines with same test suite

### 5. **Correctness**
- ✅ UI accurately shows which engine is being used
- ✅ Logs clearly indicate configuration
- ✅ User gets reliable feedback

---

## Migration Plan

### Phase 1: Create Unified Module (Low Risk)
1. Create `script_executor.rs` with unified logic
2. Add comprehensive logging
3. Unit tests for environment configuration

### Phase 2: Migrate Test UI (Medium Risk)
1. Update `test_commands.rs` to use `ScriptExecutor`
2. Remove duplicated logic
3. Test locally with both engines

### Phase 3: Migrate Activity Poller (Medium Risk)
1. Update `nova_act_executor.rs` to use `ScriptExecutor`
2. Keep existing `NovaActExecutor` struct as thin wrapper
3. Test with Step Functions

### Phase 4: Update Python Layer (Low Risk)
1. Update `script_executor.py` to check `USE_COMPUTER_AGENT`
2. Add logging for which wrapper is loaded
3. Test both execution paths

### Phase 5: Cleanup (Low Risk)
1. Remove old duplicated code
2. Update documentation
3. Add integration tests

---

## Implementation Estimate

- **Phase 1**: 2-3 hours (new module creation)
- **Phase 2**: 1-2 hours (test UI migration)
- **Phase 3**: 1-2 hours (activity poller migration)
- **Phase 4**: 1 hour (Python updates)
- **Phase 5**: 1 hour (cleanup)

**Total**: 6-9 hours for complete refactoring

---

## Alternative: Quick Fix (Not Recommended)

If time is critical, we could:
1. Copy the environment setup code from `nova_act_executor.rs` to `test_commands.rs`
2. Update `script_executor.py` to check `USE_COMPUTER_AGENT`

**Downsides**:
- Still have code duplication
- Technical debt increases
- Will bite us later

**Recommended**: Do the refactoring now to save time in the long run.

---

## Decision

**Recommendation**: Proceed with unified refactoring

**Rationale**:
- Code is already small enough to refactor safely
- Benefits far outweigh the effort
- Prevents future bugs and confusion
- Makes adding new engines (Claude, Gemini) trivial

**Next Steps**:
1. Get approval for refactoring approach
2. Create new branch: `refactor/unified-script-executor`
3. Implement Phase 1 (unified module)
4. Test thoroughly before merging
