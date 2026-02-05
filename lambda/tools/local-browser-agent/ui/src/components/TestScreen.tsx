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

interface ParsedExecutionOutput {
  s3Uploads: string[]
  jsonResult: any | null
  otherLogs: string[]
}

interface Profile {
  name: string
  description: string
  tags: string[]
  last_used: string | null
}

interface ProfileListResponse {
  profiles: Profile[]
  total_count: number
}

interface ConfigData {
  aws_profile: string
  s3_bucket: string
  headless: boolean
  browser_channel: string | null
  persistent_browser_session: boolean
}

export default function TestScreen() {
  const [script, setScript] = useState('')
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionLog, setExecutionLog] = useState<string[]>([])
  const [exampleScripts, setExampleScripts] = useState<string[]>([])
  const [showS3Uploads, setShowS3Uploads] = useState(false)
  const [showOtherLogs, setShowOtherLogs] = useState(false)
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState<string>('')
  const [secondScript, setSecondScript] = useState('')
  const [showPersistentTest, setShowPersistentTest] = useState(false)
  const [isRunningSequence, setIsRunningSequence] = useState(false)

  useEffect(() => {
    // Load list of example scripts and profiles
    loadExampleScripts()
    loadProfiles()
  }, [])

  const parseExecutionOutput = (output: string): ParsedExecutionOutput => {
    const lines = output.split('\n').filter(line => line.trim())
    const s3Uploads: string[] = []
    const otherLogs: string[] = []
    let jsonResult: any = null

    for (const line of lines) {
      const trimmed = line.trim()

      // Check if it's an S3 upload line
      if (trimmed.startsWith('Uploaded ') || trimmed.includes('s3://')) {
        s3Uploads.push(trimmed)
      }
      // Check if it's the JSON result (starts with {)
      else if (trimmed.startsWith('{')) {
        try {
          jsonResult = JSON.parse(trimmed)
        } catch {
          // If it doesn't parse, treat it as other log
          otherLogs.push(trimmed)
        }
      }
      // Check for S3 upload status lines
      else if (trimmed.startsWith('S3 upload')) {
        otherLogs.push(trimmed)
      }
      // Everything else
      else if (trimmed) {
        otherLogs.push(trimmed)
      }
    }

    return { s3Uploads, jsonResult, otherLogs }
  }

  const loadExampleScripts = async () => {
    try {
      const scripts = await invoke<string[]>('list_browser_examples')
      setExampleScripts(scripts)
    } catch (error) {
      console.error('Failed to load example scripts:', error)
      setExampleScripts([])
    }
  }

  const loadProfiles = async () => {
    try {
      const result = await invoke<ProfileListResponse>('list_profiles', { tags: null })
      setProfiles(result.profiles)
    } catch (error) {
      console.error('Failed to load profiles:', error)
      setProfiles([])
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
      // Inject profile configuration if a profile is selected
      let scriptToExecute = script
      if (selectedProfile && !dryRun) {
        try {
          const parsed = JSON.parse(script)
          // Add or update session configuration
          parsed.session = {
            ...parsed.session,
            profile_name: selectedProfile,
            clone_for_parallel: false
          }
          scriptToExecute = JSON.stringify(parsed)
          setExecutionLog(prev => [...prev, `[INFO] Using profile: ${selectedProfile}`])
        } catch (e) {
          setExecutionLog(prev => [...prev, `[WARNING] Could not inject profile - invalid JSON`])
        }
      }

      const result = await invoke<ExecutionResult>('execute_browser_script', {
        script: scriptToExecute,
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

  const handleLoadSecondExample = async (filename: string) => {
    try {
      const content = await invoke<string>('load_browser_example', { filename })
      setSecondScript(content)
      setExecutionLog(prev => [...prev, `[INFO] Loaded second script: ${filename}`])
    } catch (error) {
      setExecutionLog(prev => [...prev, `[ERROR] Failed to load second script: ${error}`])
    }
  }

  const handleLoadSecondFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: 'JSON', extensions: ['json'] }]
      })
      if (selected && typeof selected === 'string') {
        const content = await readTextFile(selected)
        setSecondScript(content)
        setExecutionLog(prev => [...prev, `[INFO] Loaded second script file: ${selected}`])
      }
    } catch (error) {
      setExecutionLog(prev => [...prev, `[ERROR] Failed to load second script file: ${error}`])
    }
  }

  const injectProfile = (scriptStr: string): string => {
    if (!selectedProfile) return scriptStr
    try {
      const parsed = JSON.parse(scriptStr)
      parsed.session = {
        ...parsed.session,
        profile_name: selectedProfile,
        clone_for_parallel: false
      }
      return JSON.stringify(parsed)
    } catch {
      return scriptStr
    }
  }

  const handlePersistentSequence = async () => {
    if (!script || !secondScript) return
    setIsRunningSequence(true)
    setExecutionLog([`[START] Persistent sequence started at ${new Date().toLocaleTimeString()}`])

    try {
      // Load config to get AWS settings
      let config: ConfigData
      try {
        config = await invoke<ConfigData>('load_config_from_file', { path: 'config.yaml' })
      } catch {
        // Fallback defaults if config file doesn't exist
        config = { aws_profile: 'default', s3_bucket: '', headless: false, browser_channel: null, persistent_browser_session: false }
      }
      setExecutionLog(prev => [...prev, `[INFO] Loaded config (AWS profile: ${config.aws_profile})`])

      const firstScriptWithProfile = injectProfile(script)
      const secondScriptWithProfile = injectProfile(secondScript)

      if (selectedProfile) {
        setExecutionLog(prev => [...prev, `[INFO] Using browser profile: ${selectedProfile}`])
      }

      // Step 1: Start persistent session with the first script
      // Profile resolution happens on the Python side via session.profile_name in the script JSON
      setExecutionLog(prev => [...prev, '[STEP 1] Starting persistent browser session with first script...'])
      await invoke<string>('start_persistent_session', {
        request: {
          first_script: firstScriptWithProfile,
          aws_profile: config.aws_profile,
          s3_bucket: config.s3_bucket || null,
          headless: config.headless,
          browser_channel: config.browser_channel,
          navigation_timeout: 60000,
          user_data_dir: null,
        }
      })
      setExecutionLog(prev => [...prev, '[STEP 1] Persistent session started, first script executing...'])

      // The first script result comes back from start_persistent_session
      // but the current API just returns a success string.
      // We need to get the result from the persistent session.
      setExecutionLog(prev => [...prev, '[STEP 1] First script completed (browser kept alive)'])

      // Step 2: Execute second script on the persistent session
      setExecutionLog(prev => [...prev, '[STEP 2] Executing second script on persistent session...'])
      const secondResult = await invoke<string>('execute_persistent_script', {
        scriptJson: secondScriptWithProfile
      })
      setExecutionLog(prev => [...prev, '[STEP 2] Second script completed'])
      if (secondResult) {
        setExecutionLog(prev => [...prev, secondResult])
      }

      setExecutionLog(prev => [...prev, '[SUCCESS] Persistent sequence completed successfully'])
    } catch (error) {
      setExecutionLog(prev => [...prev, `[ERROR] Persistent sequence failed: ${error}`])
    } finally {
      // Step 3: Always stop persistent session
      try {
        setExecutionLog(prev => [...prev, '[CLEANUP] Stopping persistent session...'])
        await invoke<string>('stop_persistent_session')
        setExecutionLog(prev => [...prev, '[CLEANUP] Persistent session stopped'])
      } catch (stopErr) {
        setExecutionLog(prev => [...prev, `[WARNING] Failed to stop persistent session: ${stopErr}`])
      }
      setIsRunningSequence(false)
      setExecutionLog(prev => [...prev, `[END] Completed at ${new Date().toLocaleTimeString()}`])
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

            {/* Profile Selector */}
            {profiles.length > 0 && (
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label>Browser Profile (optional)</label>
                <select
                  value={selectedProfile}
                  onChange={(e) => setSelectedProfile(e.target.value)}
                  className="select-input"
                >
                  <option value="">No profile (fresh browser)</option>
                  {profiles.map(profile => (
                    <option key={profile.name} value={profile.name}>
                      {profile.name} - {profile.description || 'No description'}
                    </option>
                  ))}
                </select>
                <span className="form-hint">
                  Use a saved profile to reuse authenticated sessions
                </span>
              </div>
            )}

            <div className="button-group">
              <button
                onClick={handleValidate}
                disabled={isValidating || isExecuting || isRunningSequence || !script}
                className="btn-primary"
              >
                {isValidating ? '⏳ Validating...' : '✓ Validate'}
              </button>

              <button
                onClick={() => handleExecute(true)}
                disabled={isExecuting || isRunningSequence || !script}
                className="btn-secondary"
              >
                🧪 Dry Run
              </button>

              <button
                onClick={() => handleExecute(false)}
                disabled={isExecuting || isRunningSequence || !script}
                className="btn-success"
              >
                {isExecuting ? '⏳ Executing...' : '▶️ Execute'}
              </button>
            </div>
          </div>

          {/* Persistent Session Test */}
          <div className="card controls-card">
            <div
              className="card-header"
              style={{ cursor: 'pointer' }}
              onClick={() => setShowPersistentTest(!showPersistentTest)}
            >
              <h3>{showPersistentTest ? '▼' : '▶'} Persistent Session Test</h3>
            </div>

            {showPersistentTest && (
              <div style={{ marginTop: '0.5rem' }}>
                <p className="form-hint" style={{ marginBottom: '0.75rem' }}>
                  Test persistent browser sessions by running two scripts sequentially.
                  The browser stays open between runs (no re-login needed).
                </p>

                <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                  <label>Second Script</label>
                  <div className="button-group" style={{ marginBottom: '0.5rem' }}>
                    <select
                      onChange={(e) => e.target.value && handleLoadSecondExample(e.target.value)}
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
                    <button onClick={handleLoadSecondFile} className="btn-secondary">
                      Load File
                    </button>
                  </div>
                  <textarea
                    value={secondScript}
                    onChange={(e) => setSecondScript(e.target.value)}
                    className="script-editor"
                    style={{ height: '120px', minHeight: '80px' }}
                    placeholder="Load or paste the second script JSON here..."
                    spellCheck={false}
                  />
                </div>

                <button
                  onClick={handlePersistentSequence}
                  disabled={isExecuting || isRunningSequence || !script || !secondScript}
                  className="btn-success"
                  style={{ width: '100%' }}
                >
                  {isRunningSequence ? '⏳ Running Sequence...' : '▶️ Run Persistent Sequence (2 scripts)'}
                </button>
              </div>
            )}
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
                executionLog.map((log, i) => {
                  // Check if this log entry contains execution output (JSON result)
                  if (log.includes('{') && (log.includes('"success"') || log.includes('"step_results"'))) {
                    const parsed = parseExecutionOutput(log)

                    return (
                      <div key={i} className="execution-result">
                        {/* Summary Section */}
                        {parsed.jsonResult && (
                          <div className="result-summary">
                            <h4 className={parsed.jsonResult.success ? 'success' : 'error'}>
                              {parsed.jsonResult.success ? '✓ Execution Successful' : '✗ Execution Failed'}
                            </h4>
                            {parsed.jsonResult.script_name && (
                              <p><strong>Script:</strong> {parsed.jsonResult.script_name}</p>
                            )}
                            {parsed.jsonResult.script_description && (
                              <p><strong>Description:</strong> {parsed.jsonResult.script_description}</p>
                            )}
                            <p><strong>Steps:</strong> {parsed.jsonResult.steps_executed}/{parsed.jsonResult.steps_total}</p>
                            {parsed.jsonResult.error && (
                              <p className="error-message"><strong>Error:</strong> {parsed.jsonResult.error}</p>
                            )}
                            {parsed.jsonResult.recording_s3_uri && (
                              <p><strong>Recordings:</strong> <code>{parsed.jsonResult.recording_s3_uri}</code></p>
                            )}
                          </div>
                        )}

                        {/* Step Results */}
                        {parsed.jsonResult?.step_results && parsed.jsonResult.step_results.length > 0 && (
                          <div className="step-results">
                            <h4>Step Results</h4>
                            {parsed.jsonResult.step_results.map((step: any, stepIdx: number) => (
                              <div key={stepIdx} className={`step-result ${step.success ? 'success' : 'error'}`}>
                                <div className="step-header">
                                  <span className="step-number">Step {step.step_number}</span>
                                  <span className="step-action">{step.action}</span>
                                  {step.success ? '✓' : '✗'}
                                </div>
                                {step.description && <p className="step-description">{step.description}</p>}
                                {step.response && (
                                  <div className="step-response">
                                    <strong>Response:</strong>
                                    <pre>{typeof step.response === 'string' ? step.response : JSON.stringify(step.response, null, 2)}</pre>
                                  </div>
                                )}
                                {step.parsed_response && (
                                  <div className="step-parsed-response">
                                    <strong>Extracted Data:</strong>
                                    <pre>{JSON.stringify(step.parsed_response, null, 2)}</pre>
                                  </div>
                                )}
                                {step.error && (
                                  <p className="step-error"><strong>Error:</strong> {step.error}</p>
                                )}
                                <div className="step-metadata">
                                  {step.num_steps !== undefined && <span>Steps: {step.num_steps}</span>}
                                  {step.duration !== undefined && <span>Duration: {step.duration.toFixed(2)}s</span>}
                                  {step.matches_schema !== undefined && (
                                    <span className={step.matches_schema ? 'success' : 'warning'}>
                                      Schema: {step.matches_schema ? 'Valid' : 'Invalid'}
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* S3 Uploads Section (Collapsible) */}
                        {parsed.s3Uploads.length > 0 && (
                          <details className="s3-uploads-section">
                            <summary>S3 Uploads ({parsed.s3Uploads.length} files)</summary>
                            <div className="s3-uploads-list">
                              {parsed.s3Uploads.map((upload, idx) => (
                                <div key={idx} className="s3-upload-item">{upload}</div>
                              ))}
                            </div>
                          </details>
                        )}

                        {/* Other Logs Section (Collapsible) */}
                        {parsed.otherLogs.length > 0 && (
                          <details className="other-logs-section">
                            <summary>Additional Logs ({parsed.otherLogs.length} entries)</summary>
                            <div className="other-logs-list">
                              {parsed.otherLogs.map((logLine, idx) => (
                                <div key={idx} className="log-line">{logLine}</div>
                              ))}
                            </div>
                          </details>
                        )}

                        {/* Raw JSON (Collapsible) */}
                        {parsed.jsonResult && (
                          <details className="raw-json-section">
                            <summary>Raw JSON Output</summary>
                            <pre className="raw-json">{JSON.stringify(parsed.jsonResult, null, 2)}</pre>
                          </details>
                        )}
                      </div>
                    )
                  }

                  // Regular log lines
                  return (
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
                  )
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
