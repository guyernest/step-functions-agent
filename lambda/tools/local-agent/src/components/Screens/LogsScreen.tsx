import { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

export default function LogsScreen() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Fetch logs periodically
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const logEntries = await invoke<LogEntry[]>('get_logs', { lastN: 500 });
        setLogs(logEntries);
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 1000); // Update every second

    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const handleClearLogs = async () => {
    try {
      await invoke('clear_logs');
      setLogs([]);
    } catch (error) {
      console.error('Failed to clear logs:', error);
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'text-red-600 bg-red-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'success': return 'text-green-600 bg-green-50';
      case 'info': 
      default: return 'text-gray-700 bg-gray-50';
    }
  };

  const getLogLevelIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      case 'info': 
      default: return 'ℹ️';
    }
  };

  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter(log => log.level.toLowerCase() === filter);

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Activity Logs</h2>
        
        <div className="flex gap-3 items-center">
          {/* Filter buttons */}
          <div className="flex gap-1 bg-white rounded-lg shadow-sm p-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'all' 
                  ? 'bg-blue-500 text-white' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('info')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'info' 
                  ? 'bg-blue-500 text-white' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Info
            </button>
            <button
              onClick={() => setFilter('success')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'success' 
                  ? 'bg-green-500 text-white' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Success
            </button>
            <button
              onClick={() => setFilter('warning')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'warning' 
                  ? 'bg-yellow-500 text-white' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Warning
            </button>
            <button
              onClick={() => setFilter('error')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'error' 
                  ? 'bg-red-500 text-white' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Error
            </button>
          </div>

          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1 rounded text-sm ${
              autoScroll 
                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                : 'bg-white text-gray-600 border border-gray-300'
            }`}
          >
            {autoScroll ? '📍 Auto-scroll ON' : '📌 Auto-scroll OFF'}
          </button>

          {/* Clear logs button */}
          <button
            onClick={handleClearLogs}
            className="px-4 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
          >
            Clear Logs
          </button>
        </div>
      </div>

      {/* Logs container */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
        {filteredLogs.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-lg mb-2">No logs to display</p>
              <p className="text-sm">Logs will appear here when you start listening for activities</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-auto p-4 font-mono text-sm">
            {filteredLogs.map((log, index) => (
              <div
                key={index}
                className={`flex items-start gap-2 mb-2 p-2 rounded ${getLogLevelColor(log.level)}`}
              >
                <span className="text-xs opacity-60 min-w-[60px]">
                  {log.timestamp}
                </span>
                <span className="text-base">
                  {getLogLevelIcon(log.level)}
                </span>
                <span className="flex-1 break-all">
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}

        {/* Status bar */}
        <div className="border-t bg-gray-50 px-4 py-2 text-xs text-gray-600 flex justify-between">
          <span>Showing {filteredLogs.length} {filter !== 'all' ? filter : ''} log entries</span>
          <span>Total: {logs.length} entries</span>
        </div>
      </div>
    </div>
  );
}