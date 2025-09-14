import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { open } from '@tauri-apps/api/dialog';
import { readTextFile } from '@tauri-apps/api/fs';

interface ValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

interface ExecutionResult {
  success: boolean;
  results: ActionResult[];
  error?: string;
}

interface ActionResult {
  action: string;
  status: 'success' | 'failed';
  details: string;
  duration?: number;
}

export default function TestScreen() {
  const [script, setScript] = useState('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [_executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [executionLog, setExecutionLog] = useState<string[]>([]);
  const [exampleScripts, setExampleScripts] = useState<string[]>([]);
  // const abortControllerRef = useRef<AbortController | null>(null); // TODO: Implement abort functionality

  useEffect(() => {
    // Load list of example scripts
    loadExampleScripts();
  }, []);

  const loadExampleScripts = async () => {
    try {
      const scripts = await invoke<string[]>('list_example_scripts');
      setExampleScripts(scripts);
    } catch (error) {
      console.error('Failed to load example scripts:', error);
      // Set some default examples if loading fails
      setExampleScripts(['textedit_mac_example.json', 'notepad_windows_example.json']);
    }
  };

  const handleLoadExample = async (filename: string) => {
    try {
      const content = await invoke<string>('load_example_script', { filename });
      setScript(content);
      setValidationResult(null);
      setExecutionResult(null);
      setExecutionLog([]);
    } catch (error) {
      console.error('Failed to load example:', error);
      setExecutionLog([`Error loading example: ${error}`]);
    }
  };

  const handleLoadFile = async () => {
    try {
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
        setExecutionLog([]);
      }
    } catch (error) {
      console.error('Failed to load file:', error);
      setExecutionLog([`Error loading file: ${error}`]);
    }
  };

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const result = await invoke<ValidationResult>('validate_script', { script });
      setValidationResult(result);
      if (result.valid) {
        setExecutionLog(prev => [...prev, '[VALIDATION] Script is valid']);
      } else {
        setExecutionLog(prev => [...prev, '[VALIDATION] Script has errors']);
      }
    } catch (error) {
      setValidationResult({
        valid: false,
        errors: [error as string]
      });
      setExecutionLog(prev => [...prev, `[ERROR] Validation failed: ${error}`]);
    } finally {
      setIsValidating(false);
    }
  };

  const handleExecute = async (dryRun: boolean) => {
    setIsExecuting(true);
    setExecutionResult(null);
    setExecutionLog([`[START] ${dryRun ? 'Dry run' : 'Execution'} started at ${new Date().toLocaleTimeString()}`]);
    
    try {
      const result = await invoke<ExecutionResult>('execute_test_script', {
        script,
        dryRun
      });
      
      setExecutionResult(result);
      
      if (result.success) {
        setExecutionLog(prev => [...prev, '[SUCCESS] Script executed successfully']);
      } else {
        setExecutionLog(prev => [...prev, `[FAILED] Script execution failed: ${result.error}`]);
      }
      
      // Add action results to log
      result.results?.forEach(actionResult => {
        const status = actionResult.status === 'success' ? '✓' : '✗';
        const duration = actionResult.duration ? ` (${actionResult.duration}ms)` : '';
        setExecutionLog(prev => [...prev, 
          `  ${status} ${actionResult.action}: ${actionResult.details}${duration}`
        ]);
      });
      
    } catch (error) {
      setExecutionResult({
        success: false,
        results: [],
        error: error as string
      });
      setExecutionLog(prev => [...prev, `[ERROR] Execution failed: ${error}`]);
    } finally {
      setIsExecuting(false);
      setExecutionLog(prev => [...prev, `[END] Completed at ${new Date().toLocaleTimeString()}`]);
    }
  };

  const handleStop = async () => {
    try {
      await invoke('stop_script_execution');
      setIsExecuting(false);
      setExecutionLog(prev => [...prev, '[STOPPED] Execution stopped by user']);
    } catch (error) {
      console.error('Failed to stop execution:', error);
    }
  };

  // Format JSON with proper indentation
  const formatScript = () => {
    try {
      const parsed = JSON.parse(script);
      setScript(JSON.stringify(parsed, null, 2));
    } catch (error) {
      // Script is not valid JSON, can't format
    }
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <h2 className="text-2xl font-bold mb-6">Script Testing</h2>
      
      <div className="flex-1 grid grid-cols-2 gap-6 min-h-0">
        {/* Left Panel - Script Editor */}
        <div className="flex flex-col min-h-0">
          <div className="bg-white rounded-lg shadow p-4 mb-4 flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold">Script Editor</h3>
              <div className="flex gap-2 items-center">
                <select
                  onChange={(e) => e.target.value && handleLoadExample(e.target.value)}
                  className="px-2 py-1 border rounded text-sm h-8"
                  defaultValue=""
                >
                  <option value="" disabled>Select</option>
                  {exampleScripts.map(name => (
                    <option key={name} value={name}>
                      {name.replace('.json', '').replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleLoadFile}
                  className="px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm h-8"
                >
                  Load
                </button>
                <button
                  onClick={formatScript}
                  className="px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm h-8"
                >
                  Format
                </button>
              </div>
            </div>
            
            <textarea
              value={script}
              onChange={(e) => setScript(e.target.value)}
              className="w-full flex-1 p-3 border rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-0"
              placeholder={`{
  "name": "Script Name",
  "description": "Script description",
  "abort_on_error": true,
  "actions": [
    {
      "type": "launch",
      "app": "Application Name",
      "wait": 2.0,
      "description": "Launch application"
    }
  ]
}`}
              spellCheck={false}
            />

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
                disabled={isValidating || isExecuting || !script}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isValidating ? '⏳ Validating...' : '✓ Validate'}
              </button>
              
              <button
                onClick={() => handleExecute(true)}
                disabled={isExecuting || !script}
                className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                🧪 Dry Run
              </button>
              
              <button
                onClick={() => handleExecute(false)}
                disabled={isExecuting || !script}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
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
        <div className="flex flex-col min-h-0">
          {/* Execution Log */}
          <div className="bg-white rounded-lg shadow p-4 flex-1 flex flex-col">
            <h3 className="text-lg font-semibold mb-4">Execution Log</h3>
            <div className="bg-gray-50 rounded p-3 flex-1 overflow-auto font-mono text-sm">
              {executionLog.length === 0 ? (
                <p className="text-gray-500">No execution logs yet. Load a script and click Execute to test.</p>
              ) : (
                executionLog.map((log, i) => (
                  <div 
                    key={i} 
                    className={`mb-1 ${
                      log.includes('[ERROR]') || log.includes('[FAILED]') || log.includes('✗') ? 'text-red-600' :
                      log.includes('[SUCCESS]') || log.includes('✓') ? 'text-green-600' :
                      log.includes('[WARNING]') ? 'text-yellow-600' :
                      log.includes('[START]') || log.includes('[END]') ? 'text-blue-600 font-semibold' :
                      'text-gray-700'
                    }`}
                  >
                    {log}
                  </div>
                ))
              )}
            </div>
            
            {executionLog.length > 0 && (
              <button
                onClick={() => setExecutionLog([])}
                className="mt-2 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
              >
                Clear Log
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}