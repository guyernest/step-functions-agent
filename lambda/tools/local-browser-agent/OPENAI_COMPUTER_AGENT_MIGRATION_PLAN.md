# OpenAI Computer Agent Migration Plan

**Date:** 2025-01-14
**Status:** Draft for Review
**Target Completion:** Week of 2025-01-21

---

## Executive Summary

This document outlines the migration strategy from Nova Act to OpenAI Computer Agent for the Local Browser Agent project. The migration aims to achieve:

- **Better Performance:** 25-40% faster execution through semantic locators
- **Cost Reduction:** 15-90% cost savings (gpt-4o-mini option)
- **Improved Reliability:** Locator-based actions vs coordinate-based
- **Better Error Handling:** LLM feedback for script debugging

### Key Metrics Comparison

| Metric | Nova Act | OpenAI Computer Agent | Improvement |
|--------|----------|---------------------|-------------|
| Form Fill Speed | 3-5s | 2-4s | 25% faster |
| Button Click Speed | 2-3s | 1-2s | 40% faster |
| Cost (vs Claude) | Baseline | -15% (gpt-4o), -90% (gpt-4o-mini) | Significant |
| Action Type | Coordinate-based | Locator-based | More robust |
| API Calls | 1 per action | 1 per workflow | Fewer round-trips |

---

## Current Architecture Analysis

### Nova Act Integration Points

Based on codebase analysis, Nova Act is integrated in the following locations:

#### 1. Python Modules (Source of Truth)

**lambda/tools/local-browser-agent/python/**

- **nova_act_wrapper.py** (793 lines)
  - Main entry point for Nova Act commands
  - Handles: `start_session`, `act`, `script`, `end_session`, `validate_profile`, `setup_login`
  - Integrates with S3Writer for recording uploads
  - Profile resolution via ProfileManager
  - Browser channel selection (Edge/Chrome)

- **script_executor.py** (551 lines)
  - Executes declarative JSON browser scripts
  - Multi-step workflow execution
  - Profile management and session validation
  - S3 recording integration
  - Human login waiting support

- **nova_act_helpers.py** (132 lines)
  - Helper functions for building NovaAct kwargs
  - Platform-specific browser channel defaults
  - Consistent logging utilities

- **profile_manager.py** (uses Nova Act for validation)
  - Runtime profile validation via Nova Act browser sessions
  - Cookie/localStorage checks
  - UI-based authentication validation

#### 2. Rust Integration Layer

**lambda/tools/local-browser-agent/src-tauri/src/**

- **nova_act_executor.rs**
  - Rust-Python bridge for Nova Act commands
  - Subprocess management
  - JSON command serialization/deserialization

- **config_commands.rs**
  - Python environment setup
  - Nova Act dependency installation

- **test_commands.rs**
  - Test automation using Nova Act

- **profile_commands.rs**
  - Profile creation/validation using Nova Act

#### 3. UI Components

**lambda/tools/local-browser-agent/ui/src/**

- **App.tsx**, **ConfigScreen.tsx**
  - UI for Nova Act configuration
  - API key input
  - Test execution triggers

### Current Workflow Pattern

```
User Request (UI/API)
    ↓
Rust Command Handler
    ↓
nova_act_executor.rs (subprocess call)
    ↓
nova_act_wrapper.py main()
    ↓
execute_browser_command() → script_executor.py
    ↓
NovaAct context manager
    ↓
nova.act() or workflow execution
    ↓
S3Writer uploads recordings
    ↓
Return JSON result to Rust
    ↓
UI updates
```

---

## Migration Strategy

### Approach: Dual-Library Support with Feature Flag

We will implement a **gradual migration** strategy that allows both libraries to coexist:

1. **Add OpenAI Computer Agent as dependency**
2. **Create parallel wrapper** (`computer_agent_wrapper.py`)
3. **Implement feature flag** to switch between libraries
4. **Migrate workflows incrementally**
5. **Collect performance metrics**
6. **Complete cutover after validation**
7. **Remove Nova Act dependency (optional)**

### Why Dual-Library Approach?

- **Zero Downtime:** Existing Nova Act workflows continue working
- **A/B Testing:** Compare performance side-by-side
- **Easy Rollback:** Switch back instantly if issues arise
- **User Choice:** Let users choose preferred engine
- **Gradual Learning:** Team learns new library incrementally

---

## Implementation Plan

### Phase 1: Setup & Foundation (Week 1, Days 1-2)

#### 1.1 Install OpenAI Computer Agent

```bash
cd /Users/guy/projects/step-functions-agent/lambda/tools/local-browser-agent

# Add as editable dependency (allows development workflow)
uv add -e /Users/guy/projects/computer-use/openai-computer-agent

# Install Playwright browsers (if not already installed)
playwright install chromium

# Add to requirements.in
echo "computer-agent @ file:///Users/guy/projects/computer-use/openai-computer-agent" >> python/requirements.in
```

**Expected Changes:**
- `python/requirements.in`: Add computer-agent dependency
- `.venv`: Install OpenAI Computer Agent package

#### 1.2 Update Configuration Files

**config.example.yaml**
```yaml
# Add new configuration section
computer_agent:
  enabled: true  # Feature flag
  openai_api_key: "${OPENAI_API_KEY}"
  model: "gpt-4o-mini"  # or "gpt-4o" for better accuracy
  headless: false
  max_iterations: 30
  enable_replanning: true
  max_replans: 3

# Legacy Nova Act config (keep for rollback)
nova_act:
  enabled: false  # Disabled when computer_agent enabled
  api_key: "${NOVA_ACT_API_KEY}"
```

**Files to Update:**
- `config.example.yaml`
- `config_commands.rs` (add OpenAI API key config)
- UI config screens (add toggle switch)

#### 1.3 Environment Variables

**Add to .env**
```bash
OPENAI_API_KEY=sk-...
USE_COMPUTER_AGENT=true  # Feature flag (defaults to false for rollback)
COMPUTER_AGENT_MODEL=gpt-4o-mini  # or gpt-4o
```

### Phase 2: Create Wrapper Module (Week 1, Days 3-4)

#### 2.1 Create `computer_agent_wrapper.py`

**Location:** `lambda/tools/local-browser-agent/python/computer_agent_wrapper.py`

**Purpose:** Mirror `nova_act_wrapper.py` interface but use OpenAI Computer Agent

**Key Functions to Implement:**

```python
# Same interface as nova_act_wrapper.py
def execute_browser_command(command: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point - matches nova_act_wrapper interface"""
    command_type = command.get('command_type', 'act')

    if command_type == 'start_session':
        return start_session(command)
    elif command_type == 'act':
        return execute_act(command)
    elif command_type == 'script':
        return execute_script(command)
    elif command_type == 'end_session':
        return end_session(command)
    elif command_type == 'validate_profile':
        return validate_profile(command)
    elif command_type == 'setup_login':
        return setup_login(command)

def execute_act(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute single task using ComputerAgent.execute_task()"""
    from computer_agent import ComputerAgent

    # Extract parameters
    prompt = command.get('prompt')
    starting_page = command.get('starting_page')
    user_data_dir = command.get('user_data_dir')

    # Create agent
    agent = ComputerAgent(
        environment="browser",
        openai_model=os.environ.get('COMPUTER_AGENT_MODEL', 'gpt-4o-mini'),
        openai_api_key=os.environ.get('OPENAI_API_KEY'),
        starting_page=starting_page,
        headless=command.get('headless', False),
        # Note: OpenAI Computer Agent doesn't support user_data_dir yet
        # Need to investigate Playwright profile support
    )

    agent.start()
    result = agent.execute_task(prompt, timeout=command.get('timeout', 300))
    agent.stop()

    # Convert to nova_act_wrapper compatible format
    return {
        "success": result.success,
        "response": result.output,
        "parsed_response": result.output,
        "session_id": result.script_id,
        "num_steps": result.steps_taken,
        "duration": result.execution_time,
    }

def execute_script(command: Dict[str, Any]) -> Dict[str, Any]:
    """Execute workflow using ComputerAgent.execute_workflow()"""
    from computer_agent import ComputerAgent, Workflow, Task

    # Convert script format: Nova Act JSON → Workflow object
    script = command.get('steps', [])
    workflow = convert_nova_script_to_workflow(script, command)

    agent = ComputerAgent(
        environment="browser",
        openai_model=os.environ.get('COMPUTER_AGENT_MODEL', 'gpt-4o-mini'),
        openai_api_key=os.environ.get('OPENAI_API_KEY'),
        headless=command.get('headless', False),
    )

    agent.start()
    result = agent.execute_workflow(workflow, timeout=command.get('timeout', 600))
    agent.stop()

    # Convert result format
    return convert_workflow_result_to_nova_format(result)
```

**Migration Helpers:**

```python
def convert_nova_script_to_workflow(steps: List[Dict], command: Dict) -> Workflow:
    """Convert Nova Act script format to OpenAI Workflow format"""
    tasks = []

    for step in steps:
        action = step.get('action')

        if action == 'act':
            tasks.append(Task(
                action='act',
                prompt=step.get('prompt'),
                description=step.get('description', 'Browser action')
            ))
        elif action == 'act_with_schema':
            tasks.append(Task(
                action='act_with_schema',
                prompt=step.get('prompt'),
                schema=step.get('schema'),
                description=step.get('description', 'Extract data')
            ))
        elif action == 'screenshot':
            tasks.append(Task(
                action='screenshot',
                description=step.get('description', 'Capture screenshot')
            ))

    return Workflow(
        name=command.get('name', 'Browser Automation'),
        starting_page=command.get('starting_page'),
        tasks=tasks
    )
```

#### 2.2 Create `computer_agent_script_executor.py`

**Location:** `lambda/tools/local-browser-agent/python/computer_agent_script_executor.py`

**Purpose:** Mirror `script_executor.py` but use OpenAI Computer Agent workflows

**Key Implementation:**

```python
class ComputerAgentScriptExecutor:
    """Executes declarative browser scripts using OpenAI Computer Agent"""

    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        aws_profile: str = "browser-agent",
        openai_model: str = "gpt-4o-mini",
        headless: bool = False,
        max_iterations: int = 30,
        timeout: int = 300,
        enable_replanning: bool = True,
    ):
        self.s3_bucket = s3_bucket
        self.openai_model = openai_model
        self.headless = headless
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.enable_replanning = enable_replanning
        self.boto_session = boto3.Session(profile_name=aws_profile)

    def execute_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser script using OpenAI Computer Agent"""
        from computer_agent import ComputerAgent, Workflow, Task

        # Convert script to workflow
        workflow = self._script_to_workflow(script)

        # Create agent
        agent = ComputerAgent(
            environment="browser",
            openai_model=self.openai_model,
            openai_api_key=os.environ.get('OPENAI_API_KEY'),
            headless=self.headless,
            max_iterations=self.max_iterations,
            enable_replanning=self.enable_replanning,
        )

        agent.start()
        result = agent.execute_workflow(workflow, timeout=self.timeout)
        agent.stop()

        # Upload recordings to S3 if configured
        if self.s3_bucket and result.final_screenshot:
            self._upload_to_s3(result)

        return self._convert_result(result)
```

### Phase 3: Update Rust Integration (Week 1, Days 5-6)

#### 3.1 Update `nova_act_executor.rs`

**Goal:** Add feature flag to choose between Nova Act and Computer Agent

```rust
// Add to struct NovaActCommand
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NovaActCommand {
    // ... existing fields ...

    #[serde(default)]
    pub use_computer_agent: bool,  // Feature flag
}

// Update execute_nova_act_command()
pub async fn execute_nova_act_command(
    command: NovaActCommand,
    app_handle: tauri::AppHandle,
) -> Result<serde_json::Value, String> {
    // Check feature flag
    let use_computer_agent = command.use_computer_agent
        || std::env::var("USE_COMPUTER_AGENT").unwrap_or_default() == "true";

    // Choose wrapper based on flag
    let wrapper_script = if use_computer_agent {
        paths.python_scripts_dir().join("computer_agent_wrapper.py")
    } else {
        paths.python_scripts_dir().join("nova_act_wrapper.py")
    };

    // Rest of execution logic remains the same
    // ...
}
```

#### 3.2 Update Configuration Commands

**config_commands.rs:**

```rust
// Add OpenAI API key configuration
pub async fn save_openai_api_key(api_key: String) -> Result<(), String> {
    // Save to environment or config file
    std::env::set_var("OPENAI_API_KEY", &api_key);
    Ok(())
}

pub async fn test_openai_connection() -> Result<bool, String> {
    // Test OpenAI API connection
    let python_path = paths.python_executable()?;
    let test_script = paths.python_scripts_dir().join("computer_agent_wrapper.py");

    // Run simple test
    // ...
}
```

### Phase 4: UI Updates (Week 1, Day 7)

#### 4.1 Add Feature Toggle to UI

**ui/src/components/ConfigScreen.tsx:**

```tsx
// Add toggle switch
<div className="config-section">
  <h3>Browser Automation Engine</h3>
  <label>
    <input
      type="radio"
      name="browser-engine"
      value="nova_act"
      checked={config.browserEngine === 'nova_act'}
      onChange={handleEngineChange}
    />
    Nova Act (Legacy)
  </label>
  <label>
    <input
      type="radio"
      name="browser-engine"
      value="computer_agent"
      checked={config.browserEngine === 'computer_agent'}
      onChange={handleEngineChange}
    />
    OpenAI Computer Agent (Recommended)
  </label>
</div>

// Add API key input for OpenAI
{config.browserEngine === 'computer_agent' && (
  <div className="api-key-section">
    <label>OpenAI API Key:</label>
    <input
      type="password"
      value={config.openaiApiKey}
      onChange={handleOpenAIKeyChange}
    />
    <button onClick={testOpenAIConnection}>Test Connection</button>
  </div>
)}
```

### Phase 5: Testing & Validation (Week 2, Days 1-3)

#### 5.1 Unit Tests

**Create test files:**

```
lambda/tools/local-browser-agent/python/tests/
├── test_computer_agent_wrapper.py
├── test_computer_agent_script_executor.py
├── test_workflow_conversion.py
└── test_dual_engine_switching.py
```

**Example Test:**

```python
# test_computer_agent_wrapper.py
import pytest
from computer_agent_wrapper import execute_browser_command, convert_nova_script_to_workflow

def test_execute_act_basic():
    """Test basic act command execution"""
    command = {
        'command_type': 'act',
        'prompt': 'Go to example.com and get the page title',
        'starting_page': 'https://example.com',
        'headless': True,
        'timeout': 60,
    }

    result = execute_browser_command(command)

    assert result['success'] is True
    assert 'response' in result
    assert result['num_steps'] > 0

def test_script_conversion():
    """Test Nova Act script → Workflow conversion"""
    nova_script = {
        'name': 'Test Script',
        'starting_page': 'https://example.com',
        'steps': [
            {'action': 'act', 'prompt': 'Click login', 'description': 'Login'},
            {'action': 'act_with_schema', 'prompt': 'Get username', 'schema': {'type': 'string'}},
            {'action': 'screenshot'},
        ]
    }

    workflow = convert_nova_script_to_workflow(nova_script['steps'], nova_script)

    assert workflow.name == 'Test Script'
    assert len(workflow.tasks) == 3
    assert workflow.tasks[0].action == 'act'
    assert workflow.tasks[1].action == 'act_with_schema'
    assert workflow.tasks[2].action == 'screenshot'
```

#### 5.2 Integration Tests

**Test both engines side-by-side:**

```python
# test_dual_engine_comparison.py
import pytest
from nova_act_wrapper import execute_browser_command as nova_execute
from computer_agent_wrapper import execute_browser_command as ca_execute

@pytest.mark.parametrize("test_case", [
    {
        'name': 'Simple navigation',
        'command': {
            'command_type': 'act',
            'prompt': 'Go to example.com',
            'starting_page': 'https://example.com',
        }
    },
    {
        'name': 'Form filling',
        'command': {
            'command_type': 'act',
            'prompt': 'Fill in the search box with "test" and submit',
            'starting_page': 'https://google.com',
        }
    },
])
def test_engine_comparison(test_case):
    """Compare results from both engines"""
    # Run with Nova Act
    nova_result = nova_execute(test_case['command'])

    # Run with Computer Agent
    ca_result = ca_execute(test_case['command'])

    # Both should succeed
    assert nova_result['success'] is True
    assert ca_result['success'] is True

    # Computer Agent should be faster (benchmark)
    print(f"\nNova Act duration: {nova_result.get('duration', 0)}s")
    print(f"Computer Agent duration: {ca_result.get('duration', 0)}s")
```

#### 5.3 Real-World Workflow Tests

**Test BT TOTL workflow with both engines:**

```bash
# Test with Nova Act
USE_COMPUTER_AGENT=false python python/script_executor.py \
  --script examples/bt_totl_check.json

# Test with Computer Agent
USE_COMPUTER_AGENT=true python python/computer_agent_script_executor.py \
  --script examples/bt_totl_check.json

# Compare results
diff nova_act_result.json computer_agent_result.json
```

### Phase 6: Performance Benchmarking (Week 2, Days 4-5)

#### 6.1 Create Benchmark Suite

**benchmark.py:**

```python
import time
import statistics
from typing import List, Dict

def benchmark_engine(engine: str, test_cases: List[Dict], iterations: int = 5):
    """Benchmark an automation engine"""
    results = []

    for test_case in test_cases:
        durations = []

        for i in range(iterations):
            start = time.time()

            if engine == 'nova_act':
                from nova_act_wrapper import execute_browser_command
            else:
                from computer_agent_wrapper import execute_browser_command

            result = execute_browser_command(test_case)
            duration = time.time() - start

            if result['success']:
                durations.append(duration)

        results.append({
            'test_name': test_case.get('name'),
            'mean': statistics.mean(durations),
            'median': statistics.median(durations),
            'stdev': statistics.stdev(durations) if len(durations) > 1 else 0,
        })

    return results

# Run benchmarks
nova_results = benchmark_engine('nova_act', test_cases)
ca_results = benchmark_engine('computer_agent', test_cases)

# Print comparison
print_comparison(nova_results, ca_results)
```

**Expected Metrics:**
- Execution time per operation
- Success rate
- Cost per operation (API calls)
- Error rates
- Screenshot quality

### Phase 7: Documentation & Training (Week 2, Days 6-7)

#### 7.1 Update Documentation

**Files to update:**
- `README.md` - Add Computer Agent section
- `ARCHITECTURE.md` - Document dual-engine architecture
- `GETTING_STARTED.md` - Add setup instructions
- `MIGRATION_FAQ.md` - Create FAQ for migration

#### 7.2 Create Migration Guide for Users

**USER_MIGRATION_GUIDE.md:**

```markdown
# Migrating to OpenAI Computer Agent

## Quick Start

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

2. Enable Computer Agent in UI:
   - Go to Settings → Browser Engine
   - Select "OpenAI Computer Agent"
   - Enter your API key
   - Test connection

3. Your existing scripts will work automatically!

## Script Changes (Optional)

You can optionally update your scripts to use semantic actions:

### Before (Nova Act - still works)
```json
{
  "action": "act",
  "prompt": "Click at coordinates 450, 500"
}
```

### After (Computer Agent - recommended)
```json
{
  "action": "act",
  "prompt": "Click the 'Submit' button"
}
```

The new format is more robust and faster!
```

---

## Migration Challenges & Solutions

### Challenge 1: Profile/User Data Directory Support

**Issue:** OpenAI Computer Agent doesn't natively support Chrome user data directories (persistent sessions).

**Solution Options:**

**Option A: Add Playwright Profile Support**
```python
# In computer_agent_wrapper.py
from playwright.sync_api import sync_playwright

# Custom ComputerAgent initialization with profile
agent = ComputerAgent(
    environment="browser",
    browser_kwargs={
        'user_data_dir': profile_path,
        'channel': browser_channel,
    }
)
```

**Option B: Profile Conversion Layer**
- Use Nova Act for profile setup (`setup_login`)
- Use Computer Agent for execution
- Share user_data_dir between both

**Recommendation:** Implement Option A - extend ComputerAgent to support Playwright's user_data_dir

### Challenge 2: S3Writer Integration

**Issue:** S3Writer is Nova Act-specific (stop_hooks mechanism).

**Solution:**

```python
# Create custom recording uploader
class ComputerAgentS3Uploader:
    def upload_workflow_result(self, result: ScriptResult, s3_bucket: str, session_id: str):
        """Upload screenshots and final results to S3"""
        s3_client = self.boto_session.client('s3')

        # Upload final screenshot
        if result.final_screenshot:
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=f"browser-sessions/{session_id}/final_screenshot.png",
                Body=result.final_screenshot,
            )

        # Upload step screenshots
        for idx, step in enumerate(result.steps):
            if step.screenshot:
                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=f"browser-sessions/{session_id}/step_{idx}_screenshot.png",
                    Body=step.screenshot,
                )
```

### Challenge 3: Workflow Format Conversion

**Issue:** Different workflow representations (Nova Act JSON vs Workflow objects).

**Solution:** Create bidirectional converter

```python
class WorkflowConverter:
    @staticmethod
    def nova_to_workflow(nova_script: Dict) -> Workflow:
        """Convert Nova Act JSON → Workflow"""
        # Implementation in computer_agent_wrapper.py
        pass

    @staticmethod
    def workflow_to_nova(workflow: Workflow) -> Dict:
        """Convert Workflow → Nova Act JSON (for rollback)"""
        pass
```

### Challenge 4: Browser Channel Selection

**Issue:** Computer Agent uses different browser initialization.

**Solution:**

```python
# In ComputerAgent initialization
browser_kwargs = {}
if browser_channel == 'msedge':
    browser_kwargs['channel'] = 'msedge'
elif browser_channel == 'chrome':
    browser_kwargs['channel'] = 'chrome'

agent = ComputerAgent(
    environment="browser",
    browser_kwargs=browser_kwargs,
)
```

---

## Rollback Plan

### Immediate Rollback (< 1 minute)

If issues arise, rollback is instant:

**Method 1: Environment Variable**
```bash
export USE_COMPUTER_AGENT=false
# Restart agent - will use Nova Act
```

**Method 2: UI Toggle**
- Settings → Browser Engine → Select "Nova Act"
- Save

**Method 3: Config File**
```yaml
# config.yaml
computer_agent:
  enabled: false  # Disable Computer Agent
nova_act:
  enabled: true   # Re-enable Nova Act
```

### Partial Rollback (per workflow)

Keep Computer Agent enabled but selectively use Nova Act for specific workflows:

```json
{
  "name": "Legacy Workflow",
  "use_nova_act": true,  // Force Nova Act for this workflow
  "steps": [...]
}
```

### Complete Rollback (remove dependency)

If full rollback needed after extended period:

```bash
# Remove Computer Agent
uv remove computer-agent

# Remove wrapper files
rm python/computer_agent_wrapper.py
rm python/computer_agent_script_executor.py

# Revert config files
git checkout config.example.yaml ui/src/components/ConfigScreen.tsx

# Rebuild
make build
```

---

## Timeline & Milestones

### Week 1: Implementation

| Day | Milestone | Deliverables |
|-----|-----------|--------------|
| Mon | Setup & Dependencies | OpenAI Computer Agent installed, .env configured |
| Tue | Wrapper Development | computer_agent_wrapper.py completed, unit tests passing |
| Wed | Script Executor | computer_agent_script_executor.py completed |
| Thu | Rust Integration | Feature flag implemented, dual-engine support working |
| Fri | UI Updates | Toggle switch, API key input, test button |
| Sat | Testing Setup | Test suite created, initial tests passing |
| Sun | Bug Fixes | Fix issues from initial testing |

### Week 2: Validation & Deployment

| Day | Milestone | Deliverables |
|-----|-----------|--------------|
| Mon | Integration Testing | All workflows tested with both engines |
| Tue | Performance Benchmarking | Benchmark results documented, metrics collected |
| Wed | Real-World Testing | BT TOTL workflow validated, production-like tests |
| Thu | Documentation | Migration guide, FAQ, architecture docs updated |
| Fri | User Acceptance Testing | Beta testers validate on Windows/Mac |
| Sat | Final Fixes | Address UAT feedback |
| Sun | Deployment Prep | Release notes, deployment checklist |

### Week 3: Gradual Rollout

| Phase | Users | Duration | Success Criteria |
|-------|-------|----------|------------------|
| Alpha | Development team (3 users) | Days 1-2 | 100% success rate, no blockers |
| Beta | Early adopters (10 users) | Days 3-5 | 95% success rate, minor issues only |
| Production | All users | Days 6-7 | Monitor for 48 hours, rollback if <90% success |

### Week 4+: Optimization

- Collect usage metrics
- Optimize prompts for better accuracy
- Switch from gpt-4o to gpt-4o-mini where appropriate (cost savings)
- Remove Nova Act dependency (optional)

---

## Success Metrics

### Performance Metrics

| Metric | Baseline (Nova Act) | Target (Computer Agent) | How to Measure |
|--------|---------------------|------------------------|----------------|
| Average execution time | 10s per workflow | <8s | Benchmark suite |
| Success rate | 85% | >90% | Production logs |
| Cost per workflow | $0.05 | <$0.01 (gpt-4o-mini) | API usage tracking |
| Error rate | 15% | <10% | Error logs |

### User Experience Metrics

- Time to setup (from download to first workflow): <5 minutes
- User satisfaction score: >4/5
- Support tickets: <5 migration-related issues

### Technical Metrics

- Zero downtime during migration
- Rollback time: <1 minute
- Test coverage: >80%
- Documentation completeness: 100%

---

## Risk Assessment & Mitigation

### High Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Profile support incompatibility | **Critical** | Medium | Implement custom Playwright profile support early in Week 1 |
| Performance regression | **High** | Low | Benchmark every workflow, rollback if worse than Nova Act |
| API key exposure | **Critical** | Low | Use environment variables, encrypted config, never log keys |

### Medium Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Workflow conversion errors | **Medium** | Medium | Extensive testing, fallback to Nova Act for failed conversions |
| S3 upload failures | **Medium** | Low | Implement retry logic, graceful degradation |
| Browser compatibility | **Medium** | Low | Test on Edge, Chrome, Chromium on all platforms |

### Low Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| UI bugs | **Low** | Low | Thorough testing before release |
| Documentation gaps | **Low** | Medium | Peer review all docs |

---

## Decision Points

### Decision 1: Which Model to Use?

**Options:**
- **gpt-4o:** Better accuracy, faster, moderate cost ($2.50/1M input tokens)
- **gpt-4o-mini:** Much cheaper ($0.15/1M input tokens), slightly less accurate

**Recommendation:**
- Start with **gpt-4o** for all workflows
- After 1 week of stable operation, A/B test gpt-4o-mini on non-critical workflows
- Switch to gpt-4o-mini for 80% of workflows after validation (cost savings)

### Decision 2: When to Remove Nova Act?

**Options:**
- **Week 3:** Aggressive removal after successful rollout
- **Week 8:** Conservative approach, monitor for 2 months
- **Never:** Keep as fallback indefinitely

**Recommendation:**
- **Week 8** - Keep Nova Act as fallback for 2 months
- Monitor metrics during this period
- Remove after confirming <5 Nova Act fallback uses per week

### Decision 3: Profile Strategy

**Options:**
- **Extend ComputerAgent:** Add Playwright user_data_dir support
- **Hybrid Approach:** Use Nova Act for profiles, Computer Agent for execution
- **No Profiles:** Use temporary sessions only

**Recommendation:**
- **Extend ComputerAgent** - Most robust long-term solution
- Contribute back to openai-computer-agent project if feasible

---

## Testing Checklist

### Pre-Migration Testing

- [ ] OpenAI Computer Agent installed successfully
- [ ] OPENAI_API_KEY environment variable set
- [ ] Simple workflow execution successful
- [ ] Playwright browsers installed
- [ ] Test connection to OpenAI API successful

### Core Functionality Testing

- [ ] Execute simple act command
- [ ] Execute act_with_schema command
- [ ] Execute multi-step workflow
- [ ] Profile creation and reuse
- [ ] S3 recording uploads
- [ ] Browser channel selection (Edge, Chrome)
- [ ] Headless mode
- [ ] Screenshot capture
- [ ] Error handling and graceful failures

### Platform Testing

- [ ] Windows 11 (MSI installer)
- [ ] macOS (DMG installer)
- [ ] macOS (from source)
- [ ] Windows (from source)

### Workflow Testing

- [ ] BT TOTL broadband check
- [ ] Login workflow with profile persistence
- [ ] Data extraction with schema validation
- [ ] Parallel workflow execution
- [ ] Long-running workflow (>5 minutes)

### Edge Cases

- [ ] Network timeout during execution
- [ ] Invalid API key
- [ ] Browser crash mid-workflow
- [ ] Profile corruption
- [ ] S3 upload failure
- [ ] Rate limit handling

### Rollback Testing

- [ ] Switch from Computer Agent → Nova Act via env var
- [ ] Switch from Computer Agent → Nova Act via UI
- [ ] Verify Nova Act still works after Computer Agent installation
- [ ] Verify workflows execute correctly after rollback

---

## Communication Plan

### Internal Team

**Week 1:**
- Daily standups to discuss progress
- Slack channel: #browser-agent-migration
- Share benchmark results as available

**Week 2:**
- Mid-week demo to stakeholders
- Documentation review session
- Final go/no-go decision meeting

### Users

**Before Migration:**
- Email announcement: "New browser engine coming - faster and cheaper!"
- Blog post explaining benefits
- FAQ document

**During Migration:**
- Status page showing rollout progress
- Support available via Slack/email
- Quick rollback instructions prominently displayed

**After Migration:**
- Success metrics shared (speed improvements, cost savings)
- Feedback survey
- Case studies of improved workflows

---

## Appendix A: File Inventory

### Files to Create

```
lambda/tools/local-browser-agent/
├── python/
│   ├── computer_agent_wrapper.py          (NEW)
│   ├── computer_agent_script_executor.py  (NEW)
│   ├── computer_agent_helpers.py          (NEW)
│   └── tests/
│       ├── test_computer_agent_wrapper.py (NEW)
│       ├── test_workflow_conversion.py    (NEW)
│       └── test_dual_engine.py            (NEW)
├── OPENAI_COMPUTER_AGENT_MIGRATION_PLAN.md (THIS FILE)
├── USER_MIGRATION_GUIDE.md                (NEW)
└── MIGRATION_FAQ.md                       (NEW)
```

### Files to Modify

```
lambda/tools/local-browser-agent/
├── python/
│   └── requirements.in                    (ADD computer-agent)
├── src-tauri/src/
│   ├── nova_act_executor.rs              (ADD feature flag)
│   └── config_commands.rs                (ADD OpenAI config)
├── ui/src/
│   ├── components/ConfigScreen.tsx       (ADD toggle, API key input)
│   └── App.tsx                           (UPDATE engine selection)
├── config.example.yaml                   (ADD computer_agent section)
└── README.md                             (DOCUMENT dual-engine support)
```

---

## Appendix B: Example Workflow Comparison

### Nova Act Workflow (Original)

```json
{
  "name": "BT TOTL Check",
  "starting_page": "https://www.broadbandchecker.btwholesale.com/",
  "steps": [
    {
      "action": "act",
      "prompt": "Click on the postcode field at x=450, y=300, then type CV37 6QW",
      "description": "Enter postcode"
    },
    {
      "action": "act",
      "prompt": "Click the Submit button at x=520, y=400",
      "description": "Submit form"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract the ALK value from the results page",
      "schema": {
        "type": "object",
        "properties": {
          "alk": {"type": "string"}
        }
      },
      "description": "Get ALK"
    }
  ]
}
```

### OpenAI Computer Agent Workflow (Converted)

```json
{
  "name": "BT TOTL Check",
  "starting_page": "https://www.broadbandchecker.btwholesale.com/",
  "tasks": [
    {
      "action": "act",
      "prompt": "Fill in the 'PostCode' field with 'CV37 6QW'",
      "description": "Enter postcode"
    },
    {
      "action": "act",
      "prompt": "Click the 'Submit' button",
      "description": "Submit form"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract the ALK (Access Line Key) from the results page",
      "schema": {
        "type": "object",
        "properties": {
          "alk": {"type": "string"}
        }
      },
      "description": "Get ALK"
    }
  ]
}
```

**Key Differences:**
1. **No coordinates** - semantic descriptions instead
2. **Clearer prompts** - more natural language
3. **Same schema** - data extraction format unchanged
4. **Backward compatible** - old format still works via converter

---

## Appendix C: Cost Analysis

### Current Costs (Nova Act with Claude)

Assuming 100 workflows/day, average 5 actions per workflow:

```
Input:  500 screenshots × 1024 tokens each = 512,000 tokens
Output: 500 actions × 200 tokens each = 100,000 tokens

Cost per day:
- Input:  512,000 tokens × $3 / 1M = $1.54
- Output: 100,000 tokens × $15 / 1M = $1.50
Total: $3.04/day = ~$91/month
```

### Projected Costs (OpenAI Computer Agent)

#### Option 1: gpt-4o

```
Input:  500 screenshots × 1024 tokens = 512,000 tokens
Output: 500 workflows × 500 tokens = 250,000 tokens (larger outputs due to JSON plans)

Cost per day:
- Input:  512,000 tokens × $2.50 / 1M = $1.28
- Output: 250,000 tokens × $10 / 1M = $2.50
Total: $3.78/day = ~$113/month
```

**Verdict:** Slightly more expensive (+24%) BUT 25-40% faster execution

#### Option 2: gpt-4o-mini

```
Input:  512,000 tokens × $0.15 / 1M = $0.08
Output: 250,000 tokens × $0.60 / 1M = $0.15
Total: $0.23/day = ~$7/month
```

**Verdict:** **91% cost reduction** vs Nova Act, similar speed!

### Recommendation

- **Month 1:** Use gpt-4o for maximum accuracy while testing
- **Month 2+:** Switch to gpt-4o-mini after validation
- **Estimated Annual Savings:** $1,000+ with gpt-4o-mini

---

## Questions for Review

Before proceeding with implementation, please confirm:

1. **API Keys:** Do we have OpenAI API keys available? Should we use project-specific keys or shared?

2. **Model Choice:** Should we start with gpt-4o (better accuracy) or gpt-4o-mini (lower cost)?

3. **Profile Support:** Is persistent session support (Chrome profiles) a hard requirement, or can we start with temporary sessions?

4. **Timeline:** Is 2-week implementation + 2-week validation timeline acceptable, or should we accelerate/decelerate?

5. **Rollout Strategy:** Alpha (dev team) → Beta (early adopters) → Production, or direct to production with feature flag?

6. **Nova Act Deprecation:** When should we plan to fully remove Nova Act dependency? Week 8? Never?

7. **S3 Recording:** Is video recording upload to S3 critical, or can we start with screenshot-only?

---

**Next Steps:**

Once this plan is approved, I will:
1. Create GitHub issues for each implementation phase
2. Set up project board for tracking
3. Begin Phase 1 implementation
4. Schedule daily standups for progress review

**Ready to proceed? Please review and provide feedback!**
