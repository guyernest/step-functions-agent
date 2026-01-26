---
render_with_liquid: false
---

# Detailed UI Component Design for Local Agent

## 1. Monitor Screen Component

```tsx
// src/components/Screens/MonitorScreen.tsx
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import { useAppStore } from '../../store/appStore';

interface PollingStatus {
  isPolling: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  currentTask: TaskInfo | null;
  tasksProcessed: number;
  lastTaskTime: string | null;
  uptime: number; // seconds
}

interface TaskInfo {
  id: string;
  startTime: string;
  status: 'processing' | 'completed' | 'failed';
  duration?: number;
  error?: string;
}

interface Activity {
  timestamp: string;
  taskId: string;
  status: 'success' | 'failed' | 'processing';
  duration: number;
  details?: string;
}

export default function MonitorScreen() {
  const [status, setStatus] = useState<PollingStatus | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  useEffect(() => {
    // Initial load
    loadStatus();
    loadRecentActivities();

    // Set up real-time updates
    const unlistenStatus = listen('polling-status-update', (event) => {
      setStatus(event.payload as PollingStatus);
    });

    const unlistenActivity = listen('new-activity', (event) => {
      const activity = event.payload as Activity;
      setActivities(prev => [activity, ...prev].slice(0, 100)); // Keep last 100
    });

    // Poll for updates every second
    const interval = setInterval(loadStatus, 1000);

    return () => {
      unlistenStatus.then(fn => fn());
      unlistenActivity.then(fn => fn());
      clearInterval(interval);
    };
  }, []);

  const loadStatus = async () => {
    try {
      const pollingStatus = await invoke<PollingStatus>('get_polling_status');
      setStatus(pollingStatus);
    } catch (error) {
      console.error('Failed to load status:', error);
    }
  };

  const loadRecentActivities = async () => {
    try {
      const recent = await invoke<Activity[]>('get_recent_activities', { limit: 50 });
      setActivities(recent);
    } catch (error) {
      console.error('Failed to load activities:', error);
    }
  };

  const handleStart = async () => {
    setIsStarting(true);
    try {
      await invoke('start_polling');
      await loadStatus();
    } catch (error) {
      console.error('Failed to start polling:', error);
      // Show error notification
    } finally {
      setIsStarting(false);
    }
  };

  const handleStop = async () => {
    setIsStopping(true);
    try {
      await invoke('stop_polling');
      await loadStatus();
    } catch (error) {
      console.error('Failed to stop polling:', error);
    } finally {
      setIsStopping(false);
    }
  };

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'disconnected': return 'text-red-600';
      case 'connecting': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getActivityIcon = (status: string) => {
    switch (status) {
      case 'success': return '✅';
      case 'failed': return '❌';
      case 'processing': return '⏳';
      default: return '❓';
    }
  };

  if (!status) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Activity Monitor</h2>
      
      {/* Status Panel */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">Connection</p>
            <p className={`text-lg font-medium ${getStatusColor(status.connectionStatus)}`}>
              {status.connectionStatus.charAt(0).toUpperCase() + status.connectionStatus.slice(1)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Current Activity</p>
            <p className="text-lg font-medium">
              {status.currentTask ? 'Processing' : 'Idle'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Tasks Processed</p>
            <p className="text-lg font-medium">{status.tasksProcessed}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Last Task</p>
            <p className="text-lg font-medium">
              {status.lastTaskTime || 'Never'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Uptime</p>
            <p className="text-lg font-medium">
              {formatUptime(status.uptime)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Polling</p>
            <p className="text-lg font-medium">
              {status.isPolling ? '🟢 Active' : '🔴 Stopped'}
            </p>
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Controls</h3>
        <div className="flex gap-4">
          {!status.isPolling ? (
            <button
              onClick={handleStart}
              disabled={isStarting || status.connectionStatus === 'connecting'}
              className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isStarting ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Starting...
                </>
              ) : (
                <>
                  ▶️ Start Polling
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={isStopping}
              className="px-6 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isStopping ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Stopping...
                </>
              ) : (
                <>
                  ⏹️ Stop Polling
                </>
              )}
            </button>
          )}
          
          <button
            className="px-6 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
            disabled={!status.isPolling}
          >
            ⏸️ Pause
          </button>
          
          <button
            onClick={loadRecentActivities}
            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Activities</h3>
        <div className="overflow-auto max-h-96">
          {activities.length === 0 ? (
            <p className="text-gray-500">No activities yet</p>
          ) : (
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Task ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {activities.map((activity, index) => (
                  <tr key={`${activity.taskId}-${index}`} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {new Date(activity.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-2 text-sm font-mono text-gray-900">
                      {activity.taskId.substring(0, 8)}...
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <span className="flex items-center gap-1">
                        {getActivityIcon(activity.status)}
                        {activity.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {activity.duration}ms
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {activity.details || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
```

## 2. Test Screen Component

```tsx
// src/components/Screens/TestScreen.tsx
import { useState, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import CodeEditor from '../Common/CodeEditor';
import { listen } from '@tauri-apps/api/event';

interface ValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

interface ExecutionResult {
  success: boolean;
  results: ActionResult[];
  error?: string;
  screenshots?: string[]; // Base64 encoded
}

interface ActionResult {
  action: string;
  status: 'success' | 'failed';
  details: string;
  duration?: number;
}

const SCRIPT_TEMPLATES = {
  'Launch App': {
    name: 'Launch Application',
    description: 'Launch an application',
    abort_on_error: true,
    actions: [
      {
        type: 'launch',
        app: 'notepad.exe',
        wait: 2,
        description: 'Launch Notepad'
      }
    ]
  },
  'Click and Type': {
    name: 'Click and Type',
    description: 'Click at position and type text',
    abort_on_error: true,
    actions: [
      {
        type: 'click',
        x: 500,
        y: 300,
        description: 'Click at center'
      },
      {
        type: 'type',
        text: 'Hello World',
        description: 'Type greeting'
      }
    ]
  },
  'Find and Click Image': {
    name: 'Find and Click',
    description: 'Find an image and click on it',
    abort_on_error: true,
    actions: [
      {
        type: 'locateimage',
        image: 'button.png',
        confidence: 0.8,
        description: 'Find button'
      },
      {
        type: 'click',
        image: 'button.png',
        description: 'Click button'
      }
    ]
  }
};

export default function TestScreen() {
  const [script, setScript] = useState(JSON.stringify(SCRIPT_TEMPLATES['Launch App'], null, 2));
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [executionLog, setExecutionLog] = useState<string[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const result = await invoke<ValidationResult>('validate_script', { script });
      setValidationResult(result);
    } catch (error) {
      setValidationResult({
        valid: false,
        errors: [error as string]
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleExecute = async (dryRun: boolean) => {
    setIsExecuting(true);
    setExecutionResult(null);
    setExecutionLog([]);
    
    // Set up abort controller
    abortControllerRef.current = new AbortController();
    
    // Listen for execution updates
    const unlisten = await listen('script-execution-update', (event) => {
      const update = event.payload as { type: string; message: string };
      setExecutionLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${update.message}`]);
    });

    try {
      const result = await invoke<ExecutionResult>('execute_test_script', {
        script,
        dryRun
      });
      setExecutionResult(result);
    } catch (error) {
      setExecutionResult({
        success: false,
        results: [],
        error: error as string
      });
    } finally {
      setIsExecuting(false);
      abortControllerRef.current = null;
      unlisten();
    }
  };

  const handleStop = async () => {
    if (abortControllerRef.current) {
      try {
        await invoke('stop_script_execution');
        abortControllerRef.current.abort();
        setIsExecuting(false);
        setExecutionLog(prev => [...prev, '[STOPPED] Execution stopped by user']);
      } catch (error) {
        console.error('Failed to stop execution:', error);
      }
    }
  };

  const handleLoadTemplate = (templateName: string) => {
    const template = SCRIPT_TEMPLATES[templateName as keyof typeof SCRIPT_TEMPLATES];
    if (template) {
      setScript(JSON.stringify(template, null, 2));
      setValidationResult(null);
      setExecutionResult(null);
    }
  };

  const handleLoadFile = async () => {
    try {
      const { open } = await import('@tauri-apps/api/dialog');
      const { readTextFile } = await import('@tauri-apps/api/fs');
      
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'JSON',
          extensions: ['json']
        }]
      });
      
      if (selected && typeof selected === 'string') {
        const content = await readTextFile(selected);
        setScript(content);
        setValidationResult(null);
        setExecutionResult(null);
      }
    } catch (error) {
      console.error('Failed to load file:', error);
    }
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <h2 className="text-2xl font-bold mb-6">Script Testing</h2>
      
      <div className="flex-1 grid grid-cols-2 gap-6">
        {/* Left Panel - Script Editor */}
        <div className="flex flex-col">
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Script Editor</h3>
              <div className="flex gap-2">
                <select
                  onChange={(e) => handleLoadTemplate(e.target.value)}
                  className="px-3 py-1 border rounded text-sm"
                  defaultValue=""
                >
                  <option value="" disabled>Load Template</option>
                  {Object.keys(SCRIPT_TEMPLATES).map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
                <button
                  onClick={handleLoadFile}
                  className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
                >
                  📁 Load File
                </button>
              </div>
            </div>
            
            <div className="border rounded" style={{ height: '400px' }}>
              <CodeEditor
                value={script}
                onChange={setScript}
                language="json"
                theme="light"
              />
            </div>

            {/* Validation Result */}
            {validationResult && (
              <div className={`mt-4 p-3 rounded ${validationResult.valid ? 'bg-green-50' : 'bg-red-50'}`}>
                {validationResult.valid ? (
                  <p className="text-green-700">✅ Script is valid</p>
                ) : (
                  <div>
                    <p className="text-red-700 font-semibold">❌ Validation errors:</p>
                    <ul className="list-disc list-inside text-red-600 text-sm mt-1">
                      {validationResult.errors?.map((error, i) => (
                        <li key={i}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {validationResult.warnings && validationResult.warnings.length > 0 && (
                  <div className="mt-2">
                    <p className="text-yellow-700 font-semibold">⚠️ Warnings:</p>
                    <ul className="list-disc list-inside text-yellow-600 text-sm mt-1">
                      {validationResult.warnings.map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-semibold mb-4">Test Controls</h3>
            <div className="flex gap-3">
              <button
                onClick={handleValidate}
                disabled={isValidating || isExecuting}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {isValidating ? '⏳ Validating...' : '✓ Validate JSON'}
              </button>
              
              <button
                onClick={() => handleExecute(true)}
                disabled={isExecuting || !validationResult?.valid}
                className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
              >
                🧪 Dry Run
              </button>
              
              <button
                onClick={() => handleExecute(false)}
                disabled={isExecuting || !validationResult?.valid}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                ▶️ Execute
              </button>
              
              {isExecuting && (
                <button
                  onClick={handleStop}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                >
                  ⏹️ Stop
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Output */}
        <div className="flex flex-col">
          {/* Execution Log */}
          <div className="bg-white rounded-lg shadow p-4 mb-4 flex-1">
            <h3 className="text-lg font-semibold mb-4">Execution Log</h3>
            <div className="bg-gray-50 rounded p-3 h-64 overflow-auto font-mono text-sm">
              {executionLog.length === 0 ? (
                <p className="text-gray-500">No execution logs yet</p>
              ) : (
                executionLog.map((log, i) => (
                  <div key={i} className="mb-1">{log}</div>
                ))
              )}
            </div>
          </div>

          {/* Execution Results */}
          {executionResult && (
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-semibold mb-4">Results</h3>
              <div className={`p-3 rounded mb-4 ${executionResult.success ? 'bg-green-50' : 'bg-red-50'}`}>
                <p className={`font-semibold ${executionResult.success ? 'text-green-700' : 'text-red-700'}`}>
                  {executionResult.success ? '✅ Execution Successful' : '❌ Execution Failed'}
                </p>
                {executionResult.error && (
                  <p className="text-red-600 mt-1">{executionResult.error}</p>
                )}
              </div>

              {/* Action Results */}
              <div className="space-y-2">
                {executionResult.results.map((result, i) => (
                  <div key={i} className="border rounded p-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{result.action}</span>
                      <span className={`text-sm ${result.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                        {result.status === 'success' ? '✅' : '❌'} {result.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{result.details}</p>
                    {result.duration && (
                      <p className="text-xs text-gray-500 mt-1">Duration: {result.duration}ms</p>
                    )}
                  </div>
                ))}
              </div>

              {/* Screenshots */}
              {executionResult.screenshots && executionResult.screenshots.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">Screenshots</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {executionResult.screenshots.map((screenshot, i) => (
                      <img
                        key={i}
                        src={`data:image/png;base64,${screenshot}`}
                        alt={`Screenshot ${i + 1}`}
                        className="border rounded"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

## 3. Logs Screen Component

```tsx
// src/components/Screens/LogsScreen.tsx
import { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import { save } from '@tauri-apps/api/dialog';
import { writeTextFile } from '@tauri-apps/api/fs';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  component: string;
  message: string;
  details?: string;
}

export default function LogsScreen() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [logLevel, setLogLevel] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load initial logs
    loadLogs();

    // Listen for new logs
    const unlisten = listen('new-log', (event) => {
      const log = event.payload as LogEntry;
      setLogs(prev => [...prev, log].slice(-1000)); // Keep last 1000 logs
    });

    return () => {
      unlisten.then(fn => fn());
    };
  }, []);

  useEffect(() => {
    // Apply filters
    let filtered = logs;
    
    if (logLevel !== 'ALL') {
      filtered = filtered.filter(log => log.level === logLevel);
    }
    
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.component.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.details && log.details.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    setFilteredLogs(filtered);
  }, [logs, logLevel, searchTerm]);

  useEffect(() => {
    // Auto-scroll to bottom
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  const loadLogs = async () => {
    try {
      const loadedLogs = await invoke<LogEntry[]>('get_logs', { limit: 1000 });
      setLogs(loadedLogs);
    } catch (error) {
      console.error('Failed to load logs:', error);
    }
  };

  const handleClearLogs = async () => {
    try {
      await invoke('clear_logs');
      setLogs([]);
    } catch (error) {
      console.error('Failed to clear logs:', error);
    }
  };

  const handleExportLogs = async () => {
    try {
      const filePath = await save({
        filters: [{
          name: 'Log files',
          extensions: ['log', 'txt']
        }]
      });
      
      if (filePath) {
        const logContent = filteredLogs.map(log => 
          `[${log.timestamp}] [${log.level}] [${log.component}] ${log.message}${log.details ? `\n    Details: ${log.details}` : ''}`
        ).join('\n');
        
        await writeTextFile(filePath, logContent);
        // Show success notification
      }
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-600 bg-red-50';
      case 'WARNING': return 'text-yellow-600 bg-yellow-50';
      case 'INFO': return 'text-blue-600 bg-blue-50';
      case 'DEBUG': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'ERROR': return '❌';
      case 'WARNING': return '⚠️';
      case 'INFO': return 'ℹ️';
      case 'DEBUG': return '🔍';
      default: return '📝';
    }
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <h2 className="text-2xl font-bold mb-6">Application Logs</h2>
      
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Log Level Filter */}
            <div>
              <label className="text-sm text-gray-500 mr-2">Level:</label>
              <select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                className="px-3 py-1 border rounded"
              >
                <option value="ALL">All</option>
                <option value="ERROR">Error</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
                <option value="DEBUG">Debug</option>
              </select>
            </div>

            {/* Search */}
            <div>
              <input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-1 border rounded w-64"
              />
            </div>

            {/* Auto-scroll */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">Auto-scroll</span>
            </label>
          </div>

          <div className="flex gap-2">
            <button
              onClick={loadLogs}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              🔄 Refresh
            </button>
            <button
              onClick={handleClearLogs}
              className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
            >
              🗑️ Clear
            </button>
            <button
              onClick={handleExportLogs}
              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
            >
              💾 Export
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-6 mt-4 text-sm text-gray-600">
          <span>Total: {logs.length}</span>
          <span>Filtered: {filteredLogs.length}</span>
          <span className="text-red-600">
            Errors: {logs.filter(l => l.level === 'ERROR').length}
          </span>
          <span className="text-yellow-600">
            Warnings: {logs.filter(l => l.level === 'WARNING').length}
          </span>
        </div>
      </div>

      {/* Log Display */}
      <div className="bg-white rounded-lg shadow flex-1 overflow-hidden">
        <div
          ref={logContainerRef}
          className="h-full overflow-auto p-4"
        >
          {filteredLogs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No logs to display</p>
          ) : (
            <div className="space-y-1">
              {filteredLogs.map((log, index) => (
                <div
                  key={index}
                  className="font-mono text-sm border-b border-gray-100 pb-1 hover:bg-gray-50"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-gray-500 text-xs whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getLevelColor(log.level)}`}>
                      {getLevelIcon(log.level)} {log.level}
                    </span>
                    <span className="text-purple-600 text-xs">
                      [{log.component}]
                    </span>
                    <span className="flex-1 text-gray-800">
                      {log.message}
                    </span>
                  </div>
                  {log.details && (
                    <div className="ml-32 mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded">
                      {log.details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

## 4. Sidebar Component

```tsx
// src/components/Layout/Sidebar.tsx
import { FC } from 'react';

interface SidebarProps {
  activeScreen: string;
  onNavigate: (screen: string) => void;
}

const Sidebar: FC<SidebarProps> = ({ activeScreen, onNavigate }) => {
  const menuItems = [
    { id: 'config', label: 'Configuration', icon: '⚙️' },
    { id: 'monitor', label: 'Monitor', icon: '📊' },
    { id: 'test', label: 'Test Scripts', icon: '🧪' },
    { id: 'logs', label: 'Logs', icon: '📝' },
  ];

  return (
    <aside className="w-64 bg-gray-800 text-white">
      <div className="p-4">
        <h1 className="text-xl font-bold mb-8">🤖 Local Agent</h1>
        <nav>
          <ul className="space-y-2">
            {menuItems.map(item => (
              <li key={item.id}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className={`w-full text-left px-4 py-2 rounded transition-colors ${
                    activeScreen === item.id
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-700'
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      
      {/* Version info at bottom */}
      <div className="absolute bottom-4 left-4 right-4 text-xs text-gray-400">
        <div className="border-t border-gray-700 pt-4">
          <p>Version 0.2.0</p>
          <p>© 2024 Step Functions Agent</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
```

## 5. Status Bar Component

```tsx
// src/components/Layout/StatusBar.tsx
import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

interface StatusInfo {
  connected: boolean;
  workerName: string;
  awsProfile: string;
  lastError?: string;
}

export default function StatusBar() {
  const [status, setStatus] = useState<StatusInfo>({
    connected: false,
    workerName: 'local-agent',
    awsProfile: 'default'
  });

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const info = await invoke<StatusInfo>('get_connection_info');
        setStatus(info);
      } catch (error) {
        console.error('Failed to load status:', error);
      }
    };

    loadStatus();

    const unlisten = listen('connection-status-changed', (event) => {
      setStatus(event.payload as StatusInfo);
    });

    return () => {
      unlisten.then(fn => fn());
    };
  }, []);

  return (
    <div className="h-8 bg-gray-100 border-t border-gray-300 px-4 flex items-center justify-between text-xs">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${status.connected ? 'bg-green-500' : 'bg-red-500'}`} />
          {status.connected ? 'Connected' : 'Disconnected'}
        </span>
        <span className="text-gray-600">|</span>
        <span>Worker: {status.workerName}</span>
        <span className="text-gray-600">|</span>
        <span>Profile: {status.awsProfile}</span>
      </div>
      
      {status.lastError && (
        <div className="text-red-600 flex items-center gap-1">
          <span>⚠️</span>
          <span className="truncate max-w-md">{status.lastError}</span>
        </div>
      )}
    </div>
  );
}
```

## 6. Zustand Store

```tsx
// src/store/appStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AppConfig {
  awsProfile: string;
  activityArn: string;
  workerName: string;
  pollInterval: number;
  autoStart: boolean;
}

interface RuntimeState {
  isPolling: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  currentTask: any | null;
  tasksProcessed: number;
  lastTaskTime: Date | null;
  startTime: Date | null;
}

interface AppState {
  // Configuration
  config: AppConfig;
  setConfig: (config: Partial<AppConfig>) => void;
  
  // Runtime state
  runtime: RuntimeState;
  setRuntimeState: (state: Partial<RuntimeState>) => void;
  
  // Logs
  logs: any[];
  addLog: (log: any) => void;
  clearLogs: () => void;
  
  // Test state
  testScript: string;
  setTestScript: (script: string) => void;
  testResults: any | null;
  setTestResults: (results: any) => void;
  
  // UI state
  activeScreen: string;
  setActiveScreen: (screen: string) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // Configuration
        config: {
          awsProfile: 'default',
          activityArn: '',
          workerName: 'local-agent-worker',
          pollInterval: 5000,
          autoStart: false,
        },
        setConfig: (newConfig) =>
          set((state) => ({
            config: { ...state.config, ...newConfig }
          })),
        
        // Runtime state
        runtime: {
          isPolling: false,
          connectionStatus: 'disconnected',
          currentTask: null,
          tasksProcessed: 0,
          lastTaskTime: null,
          startTime: null,
        },
        setRuntimeState: (newState) =>
          set((state) => ({
            runtime: { ...state.runtime, ...newState }
          })),
        
        // Logs
        logs: [],
        addLog: (log) =>
          set((state) => ({
            logs: [...state.logs.slice(-999), log] // Keep last 1000 logs
          })),
        clearLogs: () => set({ logs: [] }),
        
        // Test state
        testScript: '',
        setTestScript: (script) => set({ testScript: script }),
        testResults: null,
        setTestResults: (results) => set({ testResults: results }),
        
        // UI state
        activeScreen: 'config',
        setActiveScreen: (screen) => set({ activeScreen: screen }),
      }),
      {
        name: 'local-agent-storage',
        partialize: (state) => ({
          config: state.config,
          testScript: state.testScript,
          activeScreen: state.activeScreen,
        }),
      }
    )
  )
);
```

## 7. Common Components

### Code Editor Component
```tsx
// src/components/Common/CodeEditor.tsx
import { FC, useEffect, useRef } from 'react';
// Using Monaco Editor for better code editing experience
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  theme?: 'light' | 'dark';
  readOnly?: boolean;
}

const CodeEditor: FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'json',
  theme = 'light',
  readOnly = false
}) => {
  return (
    <Editor
      height="100%"
      language={language}
      value={value}
      onChange={(val) => onChange(val || '')}
      theme={theme === 'dark' ? 'vs-dark' : 'light'}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        wordWrap: 'on',
        formatOnPaste: true,
        formatOnType: true,
        automaticLayout: true,
      }}
    />
  );
};

export default CodeEditor;
```

### Notification System
```tsx
// src/components/Common/NotificationProvider.tsx
import { createContext, useContext, useState, FC, ReactNode } from 'react';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface NotificationContextType {
  showNotification: (notification: Omit<Notification, 'id'>) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};

export const NotificationProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const showNotification = (notification: Omit<Notification, 'id'>) => {
    const id = Date.now().toString();
    const newNotification = { ...notification, id };
    
    setNotifications(prev => [...prev, newNotification]);
    
    // Auto-remove after duration
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, notification.duration || 3000);
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      
      {/* Notification Display */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`${getColor(notification.type)} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in`}
          >
            <span>{getIcon(notification.type)}</span>
            <span>{notification.message}</span>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
};
```

This completes the detailed UI component design!