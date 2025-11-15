# Refactoring Status - Unified Script Execution

## ✅ Completed (Phase 1, 2 & 3)

### 1. Created Unified Module (`script_executor.rs`)
- ✅ Single source of truth for script execution
- ✅ Automatic browser engine selection based on config
- ✅ Environment variable configuration (USE_COMPUTER_AGENT, OPENAI_*, etc.)
- ✅ Unified logging and error handling
- ✅ Dynamic Python script selection:
  - `script_executor.py` for Nova Act
  - `computer_agent_script_executor.py` for OpenAI Computer Agent
- ✅ Comprehensive unit tests
- ✅ Added to `main.rs`

### 2. Key Features
```rust
pub struct ScriptExecutor {
    config: Arc<Config>,
    python_path: PathBuf,
    script_executor_path: PathBuf,  // Automatically selected!
}

// Automatically selects:
// - Nova Act: script_executor.py
// - Computer Agent: computer_agent_script_executor.py
```

### 3. Migrated Test UI (`test_commands.rs`)
- ✅ Removed 130+ lines of duplicated execution logic
- ✅ Now uses `ScriptExecutor` for all script execution
- ✅ Respects `browser_engine` configuration
- ✅ Deleted old unused helper functions (`find_script_executor`, `find_python_executable`)
- ✅ Compilation verified - no errors

**Before** (130+ lines of duplicated logic):
```rust
// Manual command building, hardcoded Nova Act
let mut cmd = Command::new(python_executable);
cmd.arg(&script_executor);
// ... many lines of argument building
if let Some(api_key) = nova_act_api_key {
    cmd.arg("--nova-act-api-key").arg(api_key.trim());
}
```

**After** (25 lines, engine-agnostic):
```rust
use crate::script_executor::{ScriptExecutor, ScriptExecutionConfig};

let executor = ScriptExecutor::new(Arc::clone(&current_config))?;
let exec_config = ScriptExecutionConfig {
    script_content: script.clone(),
    aws_profile: current_config.aws_profile.trim().to_string(),
    // ... other fields
};
let result = executor.execute(exec_config).await?;
```

## 🔄 Next Steps (Phase 4-5)

### Phase 4: Migrate Activity Poller (Optional)
**File**: `nova_act_executor.rs`

Keep the `NovaActExecutor` struct as a thin wrapper over `ScriptExecutor` for backward compatibility, but move execution logic to the unified module.

### Phase 5: Testing & Cleanup
- Test with Nova Act in Test UI
- Test with Computer Agent in Test UI
- Test with both engines in Activity Poller
- Verify environment variables are set correctly
- Remove old duplicated code
- Update documentation

## 🎯 Benefits Already Achieved

1. **Single Source of Truth**: Environment configuration in one place
2. **Automatic Selection**: Chooses correct Python script based on config
3. **Consistent Logging**: Same log format for both paths
4. **Type Safety**: Rust ensures correct configuration
5. **Testable**: Can unit test environment setup independently

## 📝 Implementation Notes

### How It Works Now

1. **User configures** `browser_engine` in UI → saves to `config.yaml`
2. **ScriptExecutor::new()** reads config → sets environment variables:
   - `USE_COMPUTER_AGENT=true/false`
   - `OPENAI_API_KEY`, `OPENAI_MODEL` (if Computer Agent)
   - `NOVA_ACT_API_KEY` (if Nova Act)
3. **find_script_executor()** checks `USE_COMPUTER_AGENT` → selects Python script
4. **execute()** runs the selected script with proper configuration

### Architecture

```
Config (config.yaml)
    │
    ▼
ScriptExecutor::new(config)
    │
    ├── configure_environment()  ← Sets USE_COMPUTER_AGENT, OPENAI_*, etc.
    ├── find_python_executable() ← Finds venv Python
    └── find_script_executor()   ← Selects correct .py file
        │
        ├── USE_COMPUTER_AGENT=true  → computer_agent_script_executor.py
        └── USE_COMPUTER_AGENT=false → script_executor.py
```

### Python Layer

- `script_executor.py`: Uses Nova Act (unchanged)
- `computer_agent_script_executor.py`: Uses OpenAI Computer Agent (unchanged)
- Both accept same command-line arguments
- Both produce same output format
- Environment variables passed automatically by Rust

## 🚀 Next Actions

1. ✅ **Update `test_commands.rs`** to use `ScriptExecutor` - COMPLETED
2. **Test locally** with both engines (Nova Act and OpenAI Computer Agent)
3. **Update `nova_act_executor.rs`** (optional, can be done later)
4. **Build and test on Windows/macOS/Linux** (validate bundles include both Python scripts)
5. **Document** the unified execution flow

## 💡 Future Enhancements

Once refactoring is complete:
- Easy to add Claude/Gemini engines
- Can A/B test engines on same workload
- Single place to add monitoring/metrics
- Easier to debug execution issues
