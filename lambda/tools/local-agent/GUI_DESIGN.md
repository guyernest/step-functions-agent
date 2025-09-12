# Local Agent GUI Design with Tauri

## Overview
A lightweight, cross-platform GUI for the Local Agent tool using Tauri framework, providing configuration management, activity polling control, and script testing capabilities.

## Technology Stack
- **Frontend**: React + TypeScript + Tailwind CSS (or alternatively SolidJS for smaller bundle)
- **Backend**: Rust with Tauri
- **State Management**: Zustand or Tauri's built-in state
- **Icons**: Lucide React or Tabler Icons
- **Notifications**: Native OS notifications via Tauri

## UI Components & Screens

### 1. Main Window Layout
```
┌─────────────────────────────────────────┐
│  Local Agent Control Panel              │
├─────────────────────────────────────────┤
│ ┌───────────┬─────────────────────────┐ │
│ │ Sidebar   │  Main Content Area      │ │
│ │           │                         │ │
│ │ • Config  │  [Dynamic content       │ │
│ │ • Monitor │   based on selection]   │ │
│ │ • Test    │                         │ │
│ │ • Logs    │                         │ │
│ └───────────┴─────────────────────────┘ │
│ Status Bar: ● Connected | Worker: local │
└─────────────────────────────────────────┘
```

### 2. Configuration Screen
**Purpose**: Configure AWS credentials and activity settings

```yaml
Fields:
  - AWS Profile: [Dropdown with profiles from ~/.aws/credentials]
  - Activity ARN: [Text input with validation]
  - Worker Name: [Text input, default: "local-agent-worker"]
  - Poll Interval: [Number input, ms, default: 5000]
  - Auto-start on launch: [Checkbox]

Actions:
  - Save Configuration
  - Test Connection
  - Import from daemon_config.json
  - Export to daemon_config.json
```

### 3. Monitor Screen
**Purpose**: Real-time monitoring of agent status and activity

```yaml
Status Panel:
  - Connection Status: [Connected/Disconnected with indicator]
  - Current Activity: [Idle/Processing task]
  - Tasks Processed: [Counter]
  - Last Task Time: [Timestamp]
  - Uptime: [Duration]

Controls:
  - Start Polling: [Button - green]
  - Stop Polling: [Button - red]
  - Pause: [Button - yellow]

Activity Feed:
  - Real-time list of recent activities
  - Each entry shows:
    - Timestamp
    - Task ID
    - Status (Success/Failed/Processing)
    - Execution time
```

### 4. Script Test Screen
**Purpose**: Test PyAutoGUI scripts locally before deployment

```yaml
Script Input:
  - Script Editor: [Code editor with JSON syntax highlighting]
  - Load from File: [Button]
  - Template Dropdown: [Common script templates]

Test Controls:
  - Validate JSON: [Button]
  - Dry Run: [Button - runs without actual GUI actions]
  - Execute: [Button - runs with actual actions]
  - Stop: [Button - emergency stop]

Output Panel:
  - Execution log
  - Screenshots (if captured)
  - Error messages
  - Performance metrics
```

### 5. Logs Screen
**Purpose**: View detailed application logs

```yaml
Features:
  - Log Level Filter: [All/Info/Warning/Error]
  - Search: [Text input for filtering]
  - Auto-scroll: [Toggle]
  - Clear Logs: [Button]
  - Export Logs: [Button]

Display:
  - Timestamp
  - Level
  - Component
  - Message
  - Expandable details for errors
```

## State Management

### Application State Structure
```typescript
interface AppState {
  config: {
    awsProfile: string;
    activityArn: string;
    workerName: string;
    pollInterval: number;
    autoStart: boolean;
  };
  
  runtime: {
    isPolling: boolean;
    connectionStatus: 'connected' | 'disconnected' | 'connecting';
    currentTask: TaskInfo | null;
    tasksProcessed: number;
    lastTaskTime: Date | null;
    startTime: Date | null;
  };
  
  logs: LogEntry[];
  
  test: {
    script: string;
    isValidJson: boolean;
    isExecuting: boolean;
    results: ExecutionResult | null;
  };
}
```

## Rust Backend API (Tauri Commands)

### Configuration Commands
```rust
#[tauri::command]
async fn load_config() -> Result<AppConfig, String>

#[tauri::command]
async fn save_config(config: AppConfig) -> Result<(), String>

#[tauri::command]
async fn test_connection(config: AppConfig) -> Result<ConnectionStatus, String>

#[tauri::command]
async fn list_aws_profiles() -> Result<Vec<String>, String>
```

### Polling Control Commands
```rust
#[tauri::command]
async fn start_polling(config: AppConfig) -> Result<(), String>

#[tauri::command]
async fn stop_polling() -> Result<(), String>

#[tauri::command]
async fn get_polling_status() -> Result<PollingStatus, String>
```

### Script Testing Commands
```rust
#[tauri::command]
async fn validate_script(script: String) -> Result<ValidationResult, String>

#[tauri::command]
async fn execute_script(script: String, dry_run: bool) -> Result<ExecutionResult, String>

#[tauri::command]
async fn stop_script_execution() -> Result<(), String>
```

### Monitoring Commands
```rust
#[tauri::command]
async fn get_runtime_stats() -> Result<RuntimeStats, String>

#[tauri::command]
async fn get_recent_activities(limit: usize) -> Result<Vec<Activity>, String>
```

## Alternative Script Execution Options

### 1. Native Rust GUI Automation
Replace PyAutoGUI with Rust-native libraries:
- **enigo**: Cross-platform input simulation
- **screenshots-rs**: Screen capture
- **image**: Image processing

### 2. WebDriver Protocol
Use WebDriver for browser automation:
- **fantoccini**: Rust WebDriver client
- More reliable for web-based applications

### 3. Windows UI Automation (Windows-specific)
- **windows-rs**: Direct Windows API access
- **uiautomation-rs**: UI Automation API wrapper

### 4. Platform-specific Solutions
- **Windows**: UI Automation API or Win32 API
- **macOS**: Accessibility API via objc
- **Linux**: AT-SPI or X11 automation

## Implementation Phases

### Phase 1: Basic GUI Foundation
1. Set up Tauri project structure
2. Create basic window with sidebar navigation
3. Implement configuration screen
4. Add config load/save functionality

### Phase 2: Core Functionality
1. Integrate existing polling logic
2. Add start/stop polling controls
3. Implement connection testing
4. Basic status monitoring

### Phase 3: Script Testing
1. Add script editor with JSON validation
2. Implement dry-run capability
3. Add script execution with real-time feedback
4. Error handling and emergency stop

### Phase 4: Enhanced Features
1. Real-time activity feed
2. Comprehensive logging system
3. Performance metrics
4. Export/import capabilities

### Phase 5: Script Executor Improvements
1. Evaluate and implement alternative to PyAutoGUI
2. Add more robust error handling
3. Implement script templates library
4. Add visual feedback during execution

## Security Considerations
- Store AWS credentials securely using OS keychain
- Validate all inputs before execution
- Implement execution sandboxing for scripts
- Add confirmation dialogs for destructive actions
- Log all activities for audit trail

## Performance Goals
- App size: < 20MB
- Startup time: < 2 seconds
- Memory usage: < 100MB during idle
- CPU usage: < 5% during polling

## User Experience Principles
1. **Minimal Configuration**: Smart defaults, auto-detect AWS profiles
2. **Clear Status Indicators**: Always show what the agent is doing
3. **Safe Testing**: Dry-run mode, emergency stop button
4. **Helpful Feedback**: Clear error messages with solutions
5. **Keyboard Shortcuts**: Power user features