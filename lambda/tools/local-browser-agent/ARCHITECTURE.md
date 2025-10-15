# Local Browser Agent Architecture

This document describes the detailed architecture, components, and data flow of the Local Browser Agent system.

## Table of Contents

- [System Overview](#system-overview)
- [Components](#components)
- [Data Flow](#data-flow)
- [Activity Pattern](#activity-pattern)
- [Session Management](#session-management)
- [S3 Integration](#s3-integration)
- [Security Model](#security-model)

## System Overview

The Local Browser Agent implements a remote execution pattern where browser automation runs on a user's local machine rather than in the cloud, avoiding bot detection while maintaining the orchestration benefits of AWS Step Functions.

### Design Principles

1. **Local Execution**: Browser runs on user's actual desktop with authentic environment
2. **Activity Pattern**: Long-running tasks without Lambda timeout constraints
3. **Session Persistence**: Maintains authenticated state across multiple commands
4. **Automatic Recording**: Built-in S3 upload via Nova Act's S3Writer
5. **Manual Intervention**: UI allows human CAPTCHA solving
6. **Native UI**: Tauri provides native desktop experience

## Components

### 1. AWS Step Functions Agent

**Purpose**: Orchestrates the overall agentic workflow with LLM reasoning

**Components**:
- **Converse State**: Calls LLM (Claude, GPT, etc.) for reasoning
- **Tool Router**: Routes tool calls to appropriate Lambda functions
- **Browser Remote Tool**: Posts tasks to Activity ARN
- **Result Processor**: Analyzes browser automation results

**Technology Stack**:
- AWS Step Functions (Standard workflow)
- AWS Lambda (Python)
- Amazon Bedrock / Anthropic Claude
- DynamoDB (Tool Registry)

### 2. Browser Remote Tool (Cloud)

**Purpose**: Bridge between Step Functions and local agent via Activity pattern

**Components**:
- **Tool Lambda** (`lambda/tools/browser_remote/lambda_function.py`):
  - Registers as tool in DynamoDB
  - Returns Activity ARN to Step Functions
  - Does NOT execute browser automation

- **Activity Resource**:
  - ARN: `arn:aws:states:REGION:ACCOUNT:activity:browser-remote-prod`
  - Timeout: 30 minutes
  - Heartbeat: 60 seconds

- **S3 Bucket**:
  - Stores browser session recordings
  - Managed by Nova Act S3Writer
  - Bucket: `browser-agent-recordings-prod-{account_id}`

**CDK Stack**: `stacks/tools/browser_remote_tool_stack.py`

### 3. Local Browser Agent (Rust)

**Purpose**: Polls Activity, executes Nova Act, manages browser sessions

**Architecture**:
```
┌────────────────────────────────────────────────┐
│          Tauri Application (main.rs)           │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ Activity Poller (activity_poller.rs)     │ │
│  │ • GetActivityTask polling loop           │ │
│  │ • Sends heartbeat every 60s              │ │
│  │ • Manages task lifecycle                 │ │
│  └──────────────────────────────────────────┘ │
│                    ▼                           │
│  ┌──────────────────────────────────────────┐ │
│  │ Session Manager (session_manager.rs)     │ │
│  │ • Tracks active browser sessions         │ │
│  │ • Manages user_data_dir                  │ │
│  │ • Handles session lifecycle              │ │
│  └──────────────────────────────────────────┘ │
│                    ▼                           │
│  ┌──────────────────────────────────────────┐ │
│  │ Nova Act Executor (nova_act_executor.rs) │ │
│  │ • Spawns Python subprocess               │ │
│  │ • Passes command via stdin (JSON)        │ │
│  │ • Reads result from stdout (JSON)        │ │
│  │ • Captures stderr for debugging          │ │
│  └──────────────────────────────────────────┘ │
│                    ▼                           │
│  ┌──────────────────────────────────────────┐ │
│  │ Tauri Commands (commands.rs)             │ │
│  │ • Exposed to frontend UI                 │ │
│  │ • get_status(), get_sessions()           │ │
│  │ • manual_intervention()                  │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

**Technology Stack**:
- Rust (Tauri backend)
- AWS SDK for Rust (Step Functions client)
- Tokio (async runtime)
- Serde (JSON serialization)

### 4. Nova Act Wrapper (Python)

**Purpose**: Executes browser automation commands using Nova Act SDK

**File**: `python/nova_act_wrapper.py`

**Responsibilities**:
- Parse command JSON from stdin
- Initialize Nova Act with S3Writer
- Execute act() command
- Serialize result to JSON
- Output to stdout

**Integration**:
```python
# Reads from stdin
command = json.loads(sys.stdin.read())

# Configure S3Writer
s3_writer = S3Writer(
    boto_session=boto_session,
    s3_bucket_name=command['s3_bucket'],
    s3_prefix=f"browser-sessions/{command['session_id']}/",
    metadata={"task_id": command['task_id']}
)

# Execute Nova Act
with NovaAct(..., stop_hooks=[s3_writer]) as nova:
    result = nova.act(command['prompt'], ...)

# Output result to stdout
print(json.dumps(result_dict))
```

**Technology Stack**:
- Python 3.10+
- Nova Act SDK
- Boto3 (AWS SDK)
- Playwright (via Nova Act)

### 5. Tauri UI (Frontend)

**Purpose**: Provides real-time monitoring and manual intervention controls

**Components**:
- **Activity Monitor**: Shows polling status, current task
- **Session Viewer**: Lists active browser sessions
- **Screenshot Viewer**: Displays latest screenshots
- **Intervention Panel**: Manual control for CAPTCHAs
- **Configuration Editor**: Edit settings without restart

**Technology Stack**:
- Svelte (frontend framework)
- Tauri (native window)
- Tailwind CSS (styling)
- WebSockets (real-time updates)

## Data Flow

### Complete Request/Response Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Step Functions Agent                                      │
│    LLM decides to use browser_remote tool                    │
│    Input: {                                                  │
│      "prompt": "Search BT broadband for address",           │
│      "starting_page": "https://btwholesale.com",            │
│      "max_steps": 20                                        │
│    }                                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Tool Lambda (browser_remote)                              │
│    Returns activity ARN to Step Functions                    │
│    Output: {                                                 │
│      "activity_arn": "arn:aws:states:...:activity:...",     │
│      "tool_name": "browser_remote"                          │
│    }                                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Step Functions Posts to Activity                          │
│    SendTaskSuccess waits for response                        │
│    Activity Task: {                                          │
│      "taskToken": "AAAAA...",                               │
│      "input": {browser command}                             │
│    }                                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ Activity ARN polling
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Local Rust Agent (GetActivityTask)                        │
│    Receives task from Step Functions                         │
│    Extracts: prompt, config, session_id                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Spawn Python Subprocess                                   │
│    Command: python3 nova_act_wrapper.py                      │
│    Stdin: JSON command                                       │
│    Stdout: JSON result                                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. Nova Act Execution                                        │
│    • Opens Chrome with user profile                          │
│    • Executes act() with prompt                              │
│    • Takes screenshots                                       │
│    • Records video                                           │
│    • S3Writer uploads to S3 on stop                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. Python Returns Result                                     │
│    Stdout: {                                                 │
│      "success": true,                                        │
│      "response": "...",                                      │
│      "session_id": "...",                                    │
│      "recording_s3_uri": "s3://..."                         │
│    }                                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 8. Rust Agent (SendTaskSuccess)                              │
│    Returns result to Step Functions                          │
│    Uses taskToken from GetActivityTask                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ 9. Step Functions Receives Result                            │
│    LLM analyzes browser automation result                    │
│    Decides next action                                       │
└──────────────────────────────────────────────────────────────┘
```

### Heartbeat Flow

```
┌─────────────────────────────────────────┐
│ Rust Agent (every 60 seconds)          │
│ SendTaskHeartbeat(taskToken)            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Step Functions                          │
│ Resets timeout, keeps task alive        │
└─────────────────────────────────────────┘
```

## Activity Pattern

### Why Activity Pattern?

Traditional Lambda-based tools have limitations:
- **15 minute timeout**: Too short for complex browser automation
- **Stateless**: Cannot maintain browser sessions
- **Cloud environment**: Triggers bot detection

Activity pattern solves these:
- **No timeout**: Runs as long as needed (up to configured limit)
- **Stateful**: Local agent maintains persistent browser sessions
- **Local execution**: Real browser, real environment

### Activity Lifecycle

```
1. Agent Starts
   ├─ Read config (Activity ARN, AWS profile)
   ├─ Initialize AWS Step Functions client
   └─ Start polling loop

2. Polling
   ├─ GetActivityTask (blocks up to 60 seconds)
   ├─ If task received: goto 3
   └─ If timeout: loop back to 2

3. Task Execution
   ├─ Extract command from task input
   ├─ Start heartbeat thread (every 60s)
   ├─ Execute browser automation
   ├─ Wait for completion
   └─ Stop heartbeat thread

4. Task Completion
   ├─ If successful: SendTaskSuccess(taskToken, result)
   ├─ If failed: SendTaskFailure(taskToken, error)
   └─ Loop back to 2

5. Agent Stops
   ├─ Cancel in-progress task (if any)
   ├─ SendTaskFailure for cancelled tasks
   └─ Close browser sessions
```

### Error Handling

| Error Type | Handler | Action |
|------------|---------|--------|
| Python subprocess crash | Rust | SendTaskFailure with stderr |
| Browser timeout | Nova Act | Return error in result JSON |
| Network error | AWS SDK | Retry with exponential backoff |
| Activity deleted | Polling loop | Log error, exit gracefully |
| Manual cancellation | UI | SendTaskFailure, stop browser |

## Session Management

### Session Lifecycle

```
┌────────────────────────────────────────────────┐
│ start_session                                  │
│ ├─ Create user_data_dir (if not exists)       │
│ ├─ Initialize NovaAct instance                 │
│ ├─ Open browser to starting_page              │
│ ├─ Generate session_id (UUID)                 │
│ └─ Store in sessions HashMap                  │
└─────────────────┬──────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────┐
│ act (multiple times)                           │
│ ├─ Lookup session by session_id               │
│ ├─ Execute nova.act(prompt)                    │
│ ├─ Capture screenshots                         │
│ └─ Update session state                        │
└─────────────────┬──────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────┐
│ end_session                                    │
│ ├─ Lookup session by session_id               │
│ ├─ Call nova.stop()                            │
│ ├─ S3Writer uploads recordings                │
│ ├─ Remove from sessions HashMap                │
│ └─ Clean up temp files                        │
└────────────────────────────────────────────────┘
```

### Session Data Structure

```rust
struct BrowserSession {
    session_id: String,
    user_data_dir: PathBuf,
    starting_page: String,
    created_at: DateTime<Utc>,
    last_activity: DateTime<Utc>,
    python_process: Option<Child>,
    status: SessionStatus,
}

enum SessionStatus {
    Starting,
    Ready,
    Executing,
    Idle,
    Stopping,
    Stopped,
}
```

### Session Persistence

User data directory structure:
```
~/.local-browser-agent/
├─ chrome-profile/           # Chrome user data
│  ├─ Default/              # Default profile
│  │  ├─ Cookies
│  │  ├─ Local Storage
│  │  └─ Extensions/
│  └─ Profile 1/            # Additional profiles
└─ sessions/                # Session metadata
   ├─ {session-id-1}.json
   └─ {session-id-2}.json
```

## S3 Integration

### Nova Act S3Writer

Nova Act's built-in S3Writer is used for automatic recording uploads:

```python
from nova_act.util.s3_writer import S3Writer

s3_writer = S3Writer(
    boto_session=boto_session,
    s3_bucket_name="browser-recordings-prod",
    s3_prefix="sessions/2024-01-15/",
    metadata={
        "session_id": "abc-123",
        "task_id": "task-456",
        "agent": "browser-remote"
    }
)

# Registers as stop hook
with NovaAct(..., stop_hooks=[s3_writer]) as nova:
    # When context exits, S3Writer uploads everything
    nova.act("...")
```

### S3 Bucket Structure

```
s3://browser-agent-recordings-prod-{account}/
├─ browser-sessions/
│  ├─ 2024-01-15/
│  │  ├─ session-abc-123/
│  │  │  ├─ act-001-step-001-screenshot.png
│  │  │  ├─ act-001-step-002-screenshot.png
│  │  │  ├─ act-001-video.webm
│  │  │  ├─ act-001-output.html
│  │  │  └─ session-metadata.json
│  │  └─ session-def-456/
│  │     └─ ...
│  └─ 2024-01-16/
│     └─ ...
└─ metadata/
   └─ sessions-index.json
```

### Permissions Required

Local AWS credentials need:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListObjects",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::browser-agent-recordings-prod-*",
        "arn:aws:s3:::browser-agent-recordings-prod-*/*"
      ]
    }
  ]
}
```

## Security Model

### Credential Management

1. **AWS Credentials**:
   - Stored in `~/.aws/credentials` (standard AWS CLI location)
   - Profile name: `browser-agent` (configurable)
   - Never sent over network except to AWS services
   - Scoped to minimum required permissions

2. **Nova Act API Key**:
   - Environment variable: `NOVA_ACT_API_KEY`
   - Or in config.yaml (encrypted at rest)
   - Passed to Python subprocess via env var
   - Never logged or displayed in UI

3. **Browser Cookies**:
   - Stored in user_data_dir
   - Encrypted at rest by Chrome
   - Never uploaded to S3 (excluded by S3Writer)
   - User responsible for securing directory

### Network Security

- **Outbound Only**: Agent only makes outbound connections
- **AWS API**: Uses HTTPS with SigV4 authentication
- **No Listening Ports**: UI server is localhost-only
- **No Remote Access**: Agent cannot be remotely controlled

### Data Privacy

| Data Type | Storage | Transmitted To | Retention |
|-----------|---------|----------------|-----------|
| Browser Cookies | Local disk | Never | Until user deletes |
| Screenshots | S3 | AWS S3 | Configurable |
| Videos | S3 | AWS S3 | Configurable |
| Commands | Memory | Step Functions | Task duration |
| Results | Memory | Step Functions | Task duration |

## Performance Considerations

### Resource Usage

- **CPU**: Low when polling, moderate during browser automation
- **Memory**: ~500MB base + ~1GB per active browser session
- **Disk**: Screenshots/videos accumulate (cleaned by S3Writer)
- **Network**: Minimal except during S3 uploads

### Scaling

- **Single Machine**: Can handle multiple concurrent sessions
- **Multiple Machines**: Each polls same Activity ARN (load balanced)
- **Session Affinity**: No built-in support (each task is independent)

### Optimization Tips

1. Reuse sessions for related tasks
2. Enable headless mode when possible
3. Configure S3Writer to skip video recording if not needed
4. Use local S3 endpoint (LocalStack) for development
5. Adjust heartbeat interval based on task duration

## Comparison with Alternatives

### vs. Lambda-based Browser Automation

| Feature | Lambda | Local Agent |
|---------|--------|-------------|
| Execution Time | 15 min max | Unlimited |
| Bot Detection | High risk | Low risk |
| Session Persistence | No | Yes |
| Cost | Per invocation | Fixed (machine) |
| Deployment | Automatic | Manual setup |

### vs. Cloud VMs (EC2, ECS)

| Feature | Cloud VM | Local Agent |
|---------|----------|-------------|
| IP Address | Datacenter | User's ISP |
| Browser Profile | Temporary | User's real profile |
| Cost | Always running | On-demand |
| Maintenance | Automated | User managed |
| Extensions | Limited | Full support |

### vs. Browser Extension

| Feature | Extension | Local Agent |
|---------|-----------|-------------|
| Installation | Chrome Web Store | Manual |
| Orchestration | Limited | Full Step Functions |
| LLM Integration | Difficult | Native |
| Permissions | Browser sandbox | Full system |

## Future Enhancements

### Planned Features

1. **Multi-Browser Support**: Firefox, Safari, Edge
2. **Session Sharing**: Multiple agents share authenticated sessions
3. **Mobile Emulation**: Test mobile-specific workflows
4. **Network Recording**: Capture HAR files for debugging
5. **Browser DevTools**: Remote debugging protocol integration
6. **Performance Metrics**: Track step duration, success rates
7. **Auto-Recovery**: Restart crashed sessions automatically
8. **Distributed Sessions**: Multiple machines share session state

### Under Consideration

- WebRTC support for video conferencing automation
- Selenium Grid compatibility layer
- Docker container mode (for CI/CD)
- Cloud sync for user_data_dir
- Multi-account support (different AWS profiles)
- Screenshot diff detection (visual regression)

## References

- [Nova Act Documentation](https://nova.amazon.com/act)
- [AWS Step Functions Activities](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-activities.html)
- [Tauri Framework](https://tauri.app/)
- [Playwright](https://playwright.dev/)
- [AWS SDK for Rust](https://github.com/awslabs/aws-sdk-rust)
