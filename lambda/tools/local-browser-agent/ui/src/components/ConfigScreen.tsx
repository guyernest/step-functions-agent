import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'

interface ConfigScreenProps {
  onConfigSaved: () => void
}

interface ConfigData {
  activity_arn: string
  aws_profile: string
  aws_region: string | null
  s3_bucket: string
  user_data_dir: string | null
  ui_port: number
  nova_act_api_key: string | null
  headless: boolean
  heartbeat_interval: number
  browser_channel: string | null
}

interface ChromeProfile {
  name: string
  path: string
}

interface ConnectionTestResult {
  success: boolean
  message: string
  error: string | null
}

interface ValidationResult {
  valid: boolean
  message: string
  details: string | null
}

interface SetupResult {
  success: boolean
  message: string
  steps: SetupStep[]
}

interface SetupStep {
  name: string
  status: string
  details: string
}

function ConfigScreen({ onConfigSaved }: ConfigScreenProps) {
  const [config, setConfig] = useState<ConfigData>({
    activity_arn: '',
    aws_profile: 'browser-agent',
    aws_region: null,
    s3_bucket: '',
    user_data_dir: null,
    ui_port: 3000,
    nova_act_api_key: null,
    headless: false,
    heartbeat_interval: 60,
    browser_channel: null,
  })

  const [awsProfiles, setAwsProfiles] = useState<string[]>([])
  const [chromeProfiles, setChromeProfiles] = useState<ChromeProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [validating, setValidating] = useState(false)
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [settingUp, setSettingUp] = useState(false)
  const [setupResult, setSetupResult] = useState<SetupResult | null>(null)

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      // First, try to load existing config
      let loadedConfig: ConfigData | null = null
      try {
        loadedConfig = await invoke<ConfigData>('load_config_from_file', {
          path: 'config.yaml',
        })
        console.log('✓ Loaded config from ~/.local-browser-agent/config.yaml:', loadedConfig)
      } catch (error) {
        console.log('⚠ Config file not found, will use defaults:', error)
      }

      // Then load AWS and Chrome profiles
      try {
        const [profiles, chromeProfs] = await Promise.all([
          invoke<string[]>('list_aws_profiles').catch(err => {
            console.error('Failed to load AWS profiles:', err)
            return []
          }),
          invoke<ChromeProfile[]>('list_chrome_profiles').catch(err => {
            console.error('Failed to load Chrome profiles:', err)
            return []
          }),
        ])

        console.log('Loaded AWS profiles:', profiles)
        console.log('Loaded Chrome profiles:', chromeProfs)

        setAwsProfiles(profiles)
        setChromeProfiles(chromeProfs)
      } catch (error) {
        console.error('Error loading profiles:', error)
      }

      // Set config AFTER we have profiles loaded (so dropdowns render correctly)
      if (loadedConfig) {
        console.log('Setting config state with loaded values')
        setConfig(loadedConfig)
      } else {
        console.log('Using default config values')
      }

      setLoading(false)
    } catch (error) {
      console.error('Error loading initial data:', error)
      setLoading(false)
    }
  }

  const handleSaveConfig = async () => {
    setSaving(true)
    setTestResult(null)
    setValidationResult(null)

    try {
      await invoke('save_config_to_file', {
        path: 'config.yaml',
        config,
      })

      onConfigSaved()
      alert('Configuration saved successfully to:\n~/.local-browser-agent/config.yaml\n\nThe configuration will be used for new script executions.\n\nNote: To start polling for Step Functions activities, you need to restart the application.')
    } catch (error) {
      console.error('Error saving config:', error)
      alert(`Error saving configuration: ${error}`)
    } finally {
      setSaving(false)
    }
  }

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)

    try {
      const result = await invoke<ConnectionTestResult>('test_aws_connection', {
        awsProfile: config.aws_profile,
        awsRegion: config.aws_region,
      })

      setTestResult(result)
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Connection test failed',
        error: String(error),
      })
    } finally {
      setTesting(false)
    }
  }

  const handleValidateArn = async () => {
    if (!config.activity_arn) {
      alert('Please enter an Activity ARN first')
      return
    }

    setValidating(true)
    setValidationResult(null)

    try {
      const result = await invoke<ValidationResult>('validate_activity_arn', {
        activityArn: config.activity_arn,
        awsProfile: config.aws_profile,
      })

      setValidationResult(result)
    } catch (error) {
      setValidationResult({
        valid: false,
        message: `Validation failed: ${error}`,
        details: null,
      })
    } finally {
      setValidating(false)
    }
  }

  const handleSetupPython = async () => {
    setSettingUp(true)
    setSetupResult(null)

    try {
      const result = await invoke<SetupResult>('setup_python_environment')
      setSetupResult(result)
    } catch (error) {
      setSetupResult({
        success: false,
        message: `Setup failed: ${error}`,
        steps: [],
      })
    } finally {
      setSettingUp(false)
    }
  }

  const handleCheckPython = async () => {
    setSettingUp(true)
    setSetupResult(null)

    try {
      const result = await invoke<SetupResult>('check_python_environment')
      setSetupResult(result)
    } catch (error) {
      setSetupResult({
        success: false,
        message: `Check failed: ${error}`,
        steps: [],
      })
    } finally {
      setSettingUp(false)
    }
  }

  if (loading) {
    return (
      <div className="screen-container">
        <h2>Loading...</h2>
      </div>
    )
  }

  return (
    <div className="screen-container">
      <div className="screen-header">
        <h2>Configuration</h2>
        <p className="screen-description">
          Configure your browser agent to connect to AWS Step Functions Activity
        </p>
      </div>

      <div className="config-form">
        {/* AWS Configuration */}
        <section className="config-section">
          <h3>AWS Configuration</h3>

          <div className="form-group">
            <label htmlFor="aws_profile">AWS Profile</label>
            <select
              id="aws_profile"
              value={config.aws_profile}
              onChange={(e) => setConfig({ ...config, aws_profile: e.target.value })}
            >
              {awsProfiles.length === 0 && (
                <option value="">No profiles found</option>
              )}
              {awsProfiles.map((profile) => (
                <option key={profile} value={profile}>
                  {profile}
                </option>
              ))}
            </select>
            <span className="form-hint">
              {navigator.platform.includes('Win')
                ? 'Profile from %USERPROFILE%\\.aws\\credentials or config'
                : 'Profile from ~/.aws/credentials or config'}
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="aws_region">AWS Region (optional)</label>
            <input
              type="text"
              id="aws_region"
              value={config.aws_region || ''}
              onChange={(e) => setConfig({ ...config, aws_region: e.target.value || null })}
              placeholder="us-west-2"
            />
            <span className="form-hint">Leave empty to use profile default</span>
          </div>

          <div className="form-actions">
            <button
              onClick={handleTestConnection}
              disabled={testing || !config.aws_profile}
              className="btn-secondary"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
          </div>

          {testResult && (
            <div className={`alert ${testResult.success ? 'alert-success' : 'alert-error'}`}>
              <strong>{testResult.message}</strong>
              {testResult.error && <div className="alert-details">{testResult.error}</div>}
            </div>
          )}
        </section>

        {/* Python Environment Setup */}
        <section className="config-section">
          <h3>Python Environment</h3>

          <p className="section-description">
            Before running browser automation scripts, you need to set up the Python environment inside the app bundle.
            This will install Python dependencies and the Chromium browser.
          </p>

          <div className="form-actions">
            <button
              onClick={handleCheckPython}
              disabled={settingUp}
              className="btn-secondary"
            >
              {settingUp ? 'Checking...' : 'Check Status'}
            </button>
            <button
              onClick={handleSetupPython}
              disabled={settingUp}
              className="btn-primary"
            >
              {settingUp ? 'Setting up...' : 'Setup Python Environment'}
            </button>
          </div>

          {setupResult && (
            <div className={`alert ${setupResult.success ? 'alert-success' : 'alert-error'}`}>
              <strong>{setupResult.message}</strong>
              {setupResult.steps.length > 0 && (
                <div className="setup-steps">
                  {setupResult.steps.map((step, index) => (
                    <div key={index} className={`setup-step setup-step-${step.status}`}>
                      <span className="step-name">{step.name}</span>
                      <span className={`step-status status-${step.status}`}>
                        {step.status === 'success' ? '✓' : step.status === 'failed' ? '✗' : '-'}
                      </span>
                      <div className="step-details">{step.details}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Activity Configuration */}
        <section className="config-section">
          <h3>Step Functions Activity</h3>

          <div className="form-group">
            <label htmlFor="activity_arn">Activity ARN</label>
            <input
              type="text"
              id="activity_arn"
              value={config.activity_arn}
              onChange={(e) => setConfig({ ...config, activity_arn: e.target.value })}
              placeholder="arn:aws:states:us-west-2:123456789:activity:browser-remote-prod"
            />
            <span className="form-hint">From CDK deployment outputs</span>
          </div>

          <div className="form-group">
            <label htmlFor="s3_bucket">S3 Recordings Bucket</label>
            <input
              type="text"
              id="s3_bucket"
              value={config.s3_bucket}
              onChange={(e) => setConfig({ ...config, s3_bucket: e.target.value })}
              placeholder="browser-agent-recordings-prod-123456789"
            />
            <span className="form-hint">From CDK deployment outputs</span>
          </div>

          <div className="form-actions">
            <button
              onClick={handleValidateArn}
              disabled={validating || !config.activity_arn}
              className="btn-secondary"
            >
              {validating ? 'Validating...' : 'Validate ARN'}
            </button>
          </div>

          {validationResult && (
            <div className={`alert ${validationResult.valid ? 'alert-success' : 'alert-error'}`}>
              <strong>{validationResult.message}</strong>
              {validationResult.details && (
                <div className="alert-details">{validationResult.details}</div>
              )}
            </div>
          )}
        </section>

        {/* Browser Configuration */}
        <section className="config-section">
          <h3>Browser Configuration</h3>

          <div className="form-group">
            <label htmlFor="browser_channel">Browser Channel</label>
            <select
              id="browser_channel"
              value={config.browser_channel || ''}
              onChange={(e) => setConfig({ ...config, browser_channel: e.target.value || null })}
            >
              <option value="">Auto-detect (Edge on Windows, Chrome on other platforms)</option>
              <option value="msedge">Microsoft Edge</option>
              <option value="chrome">Google Chrome</option>
              <option value="chromium">Chromium (installed by setup script)</option>
            </select>
            <span className="form-hint">
              {navigator.platform.includes('Win')
                ? 'Recommended: Microsoft Edge (pre-installed on Windows 10/11)'
                : 'Recommended: Google Chrome (or auto-detect)'}
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="user_data_dir">Chrome Profile (optional)</label>
            <select
              id="user_data_dir"
              value={config.user_data_dir || ''}
              onChange={(e) => setConfig({ ...config, user_data_dir: e.target.value || null })}
            >
              <option value="">Temporary profile</option>
              {chromeProfiles.map((profile) => (
                <option key={profile.path} value={profile.path}>
                  {profile.name}
                </option>
              ))}
            </select>
            <span className="form-hint">
              Use existing profile for authenticated sessions
            </span>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={config.headless}
                onChange={(e) => setConfig({ ...config, headless: e.target.checked })}
              />
              <span>Run browser in headless mode</span>
            </label>
            <span className="form-hint">Not recommended for bot detection avoidance</span>
          </div>
        </section>

        {/* Nova Act Configuration */}
        <section className="config-section">
          <h3>Nova Act Configuration</h3>

          <div className="form-group">
            <label htmlFor="nova_act_api_key">Nova Act API Key (optional)</label>
            <input
              type="password"
              id="nova_act_api_key"
              value={config.nova_act_api_key || ''}
              onChange={(e) => setConfig({ ...config, nova_act_api_key: e.target.value || null })}
              placeholder="Enter API key or use NOVA_ACT_API_KEY env var"
            />
            <span className="form-hint">Can also be set via environment variable</span>
          </div>
        </section>

        {/* Advanced Settings */}
        <section className="config-section">
          <h3>Advanced Settings</h3>

          <div className="form-group">
            <label htmlFor="heartbeat_interval">Heartbeat Interval (seconds)</label>
            <input
              type="number"
              id="heartbeat_interval"
              value={config.heartbeat_interval}
              onChange={(e) =>
                setConfig({ ...config, heartbeat_interval: parseInt(e.target.value) })
              }
              min="30"
              max="300"
            />
            <span className="form-hint">How often to send heartbeat (30-300 seconds)</span>
          </div>

          <div className="form-group">
            <label htmlFor="ui_port">UI Port</label>
            <input
              type="number"
              id="ui_port"
              value={config.ui_port}
              onChange={(e) => setConfig({ ...config, ui_port: parseInt(e.target.value) })}
              min="1024"
              max="65535"
            />
            <span className="form-hint">Port for the web UI</span>
          </div>
        </section>

        {/* Save Button */}
        <div className="form-footer">
          <button onClick={handleSaveConfig} disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfigScreen
