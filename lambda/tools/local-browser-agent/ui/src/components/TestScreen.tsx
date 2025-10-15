import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { open } from '@tauri-apps/api/dialog'
import { readTextFile } from '@tauri-apps/api/fs'

interface ValidationResult {
  valid: boolean
  errors?: string[]
  warnings?: string[]
}

interface ExecutionResult {
  success: boolean
  output?: string
  error?: string
}

export default function TestScreen() {
  const [script, setScript] = useState('')
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionLog, setExecutionLog] = useState<string[]>([])
  const [exampleScripts, setExampleScripts] = useState<string[]>([])

  useEffect(() => {
    // Load list of example scripts
    loadExampleScripts()
  }, [])

  const loadExampleScripts = async () => {
    try {
      const scripts = await invoke<string[]>('list_browser_examples')
      setExampleScripts(scripts)
    } catch (error) {
      console.error('Failed to load example scripts:', error)
      setExampleScripts([])
    }
  }

  const handleLoadExample = async (filename: string) => {
    try {
      const content = await invoke<string>('load_browser_example', { filename })
      setScript(content)
      setValidationResult(null)
      setExecutionLog([])
      setExecutionLog(prev => [...prev, `[INFO] Loaded example: ${filename}`])
    } catch (error) {
      console.error('Failed to load example:', error)
      setExecutionLog([`[ERROR] Failed to load example: ${error}`])
    }
  }

  const handleLoadFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'JSON',
          extensions: ['json']
        }]
      })

      if (selected && typeof selected === 'string') {
        const content = await readTextFile(selected)
        setScript(content)
        setValidationResult(null)
        setExecutionLog([])
        setExecutionLog(prev => [...prev, `[INFO] Loaded file: ${selected}`])
      }
    } catch (error) {
      console.error('Failed to load file:', error)
      setExecutionLog([`[ERROR] Failed to load file: ${error}`])
    }
  }

  const handleValidate = async () => {
    setIsValidating(true)
    try {
      const result = await invoke<ValidationResult>('validate_browser_script', { script })
      setValidationResult(result)
      if (result.valid) {
        setExecutionLog(prev => [...prev, '[VALIDATION] ✓ Script is valid'])
      } else {
        setExecutionLog(prev => [...prev, '[VALIDATION] ✗ Script has errors'])
        result.errors?.forEach(err => {
          setExecutionLog(prev => [...prev, `  ${err}`])
        })
      }
    } catch (error) {
      setValidationResult({
        valid: false,
        errors: [String(error)]
      })
      setExecutionLog(prev => [...prev, `[ERROR] Validation failed: ${error}`])
    } finally {
      setIsValidating(false)
    }
  }

  const handleExecute = async (dryRun: boolean) => {
    setIsExecuting(true)
    setExecutionLog([`[START] ${dryRun ? 'Dry run' : 'Execution'} started at ${new Date().toLocaleTimeString()}`])

    try {
      const result = await invoke<ExecutionResult>('execute_browser_script', {
        script,
        dryRun
      })

      if (result.success) {
        setExecutionLog(prev => [...prev, '[SUCCESS] ✓ Script executed successfully'])
        if (result.output) {
          setExecutionLog(prev => [...prev, result.output!])
        }
      } else {
        setExecutionLog(prev => [...prev, `[FAILED] ✗ Script execution failed: ${result.error}`])
      }

    } catch (error) {
      setExecutionLog(prev => [...prev, `[ERROR] Execution failed: ${error}`])
    } finally {
      setIsExecuting(false)
      setExecutionLog(prev => [...prev, `[END] Completed at ${new Date().toLocaleTimeString()}`])
    }
  }

  const formatScript = () => {
    try {
      const parsed = JSON.parse(script)
      setScript(JSON.stringify(parsed, null, 2))
      setExecutionLog(prev => [...prev, '[INFO] Script formatted'])
    } catch (error) {
      setExecutionLog(prev => [...prev, '[ERROR] Cannot format - invalid JSON'])
    }
  }

  return (
    <div className="screen-container">
      <div className="screen-header">
        <h2>Test Browser Scripts</h2>
        <p className="screen-description">
          Load and test browser automation scripts locally without waiting for server tasks
        </p>
      </div>

      <div className="test-grid">
        {/* Left Panel - Script Editor */}
        <div className="test-panel">
          <div className="card editor-card">
            <div className="card-header">
              <h3>Script Editor</h3>
              <div className="button-group">
                <select
                  onChange={(e) => e.target.value && handleLoadExample(e.target.value)}
                  className="select-input"
                  defaultValue=""
                >
                  <option value="" disabled>Load Example</option>
                  {exampleScripts.map(name => (
                    <option key={name} value={name}>
                      {name.replace('.json', '').replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
                <button onClick={handleLoadFile} className="btn-secondary">
                  Load File
                </button>
                <button onClick={formatScript} className="btn-secondary" disabled={!script}>
                  Format JSON
                </button>
              </div>
            </div>

            <textarea
              value={script}
              onChange={(e) => setScript(e.target.value)}
              className="script-editor"
              placeholder={`{
  "name": "Example Browser Script",
  "description": "Script description",
  "abort_on_error": true,
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com",
      "wait": 2.0,
      "description": "Navigate to website"
    },
    {
      "type": "click",
      "selector": "button.submit",
      "description": "Click submit button"
    }
  ]
}`}
              spellCheck={false}
            />

            {/* Validation Result */}
            {validationResult && (
              <div className={`validation-result ${validationResult.valid ? 'valid' : 'invalid'}`}>
                {validationResult.valid ? (
                  <p className="validation-message success">✅ Script is valid</p>
                ) : (
                  <div>
                    <p className="validation-message error">❌ Validation errors:</p>
                    <ul className="error-list">
                      {validationResult.errors?.map((error, i) => (
                        <li key={i}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {validationResult.warnings && validationResult.warnings.length > 0 && (
                  <div>
                    <p className="validation-message warning">⚠️ Warnings:</p>
                    <ul className="warning-list">
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
          <div className="card controls-card">
            <h3>Test Controls</h3>
            <div className="button-group">
              <button
                onClick={handleValidate}
                disabled={isValidating || isExecuting || !script}
                className="btn-primary"
              >
                {isValidating ? '⏳ Validating...' : '✓ Validate'}
              </button>

              <button
                onClick={() => handleExecute(true)}
                disabled={isExecuting || !script}
                className="btn-secondary"
              >
                🧪 Dry Run
              </button>

              <button
                onClick={() => handleExecute(false)}
                disabled={isExecuting || !script}
                className="btn-success"
              >
                {isExecuting ? '⏳ Executing...' : '▶️ Execute'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Execution Log */}
        <div className="test-panel">
          <div className="card log-card">
            <div className="card-header">
              <h3>Execution Log</h3>
              {executionLog.length > 0 && (
                <button
                  onClick={() => setExecutionLog([])}
                  className="btn-secondary"
                >
                  Clear Log
                </button>
              )}
            </div>
            <div className="execution-log">
              {executionLog.length === 0 ? (
                <p className="log-empty">No execution logs yet. Load a script and click Execute to test.</p>
              ) : (
                executionLog.map((log, i) => (
                  <div
                    key={i}
                    className={`log-line ${
                      log.includes('[ERROR]') || log.includes('[FAILED]') || log.includes('✗') ? 'error' :
                      log.includes('[SUCCESS]') || log.includes('✓') ? 'success' :
                      log.includes('[WARNING]') ? 'warning' :
                      log.includes('[START]') || log.includes('[END]') ? 'info' :
                      ''
                    }`}
                  >
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
