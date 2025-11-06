import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import ConfigScreen from './components/ConfigScreen'
import ListenScreen from './components/ListenScreen'
import TestScreen from './components/TestScreen'
import ProfilesScreen from './components/ProfilesScreen'

type Screen = 'listen' | 'test' | 'profiles' | 'config'

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

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('listen')
  const [configExists, setConfigExists] = useState(false)

  useEffect(() => {
    // Check if config.yaml exists
    checkConfigExists()
  }, [])

  const checkConfigExists = async () => {
    try {
      const config = await invoke<ConfigData>('load_config_from_file', {
        path: 'config.yaml',
      })

      // Check if essential fields are configured
      const isConfigured = !!(
        config.activity_arn &&
        config.activity_arn.trim() !== '' &&
        config.aws_profile &&
        config.aws_profile.trim() !== '' &&
        config.s3_bucket &&
        config.s3_bucket.trim() !== ''
      )

      setConfigExists(isConfigured)

      if (isConfigured) {
        console.log('✓ Configuration found and valid')
      } else {
        console.log('⚠ Configuration file exists but incomplete')
      }
    } catch (error) {
      console.log('⚠ No configuration file found:', error)
      setConfigExists(false)
    }
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h1>Browser Agent</h1>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${currentScreen === 'listen' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('listen')}
            disabled={!configExists}
          >
            <span className="nav-icon">👂</span>
            <span className="nav-label">Listen</span>
          </button>

          <button
            className={`nav-item ${currentScreen === 'test' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('test')}
          >
            <span className="nav-icon">🧪</span>
            <span className="nav-label">Test</span>
          </button>

          <button
            className={`nav-item ${currentScreen === 'profiles' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('profiles')}
          >
            <span className="nav-icon">👤</span>
            <span className="nav-label">Profiles</span>
          </button>

          <button
            className={`nav-item ${currentScreen === 'config' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('config')}
          >
            <span className="nav-icon">⚙️</span>
            <span className="nav-label">Config</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="status-indicator">
            <span className={`status-dot ${configExists ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">{configExists ? 'Configured' : 'Not Configured'}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {currentScreen === 'listen' && configExists && <ListenScreen />}
        {currentScreen === 'listen' && !configExists && (
          <div className="screen-container">
            <div className="card">
              <h2>Not Configured</h2>
              <p>Please configure the application before listening for activities.</p>
              <button onClick={() => setCurrentScreen('config')} className="btn-primary">
                Go to Configuration
              </button>
            </div>
          </div>
        )}
        {currentScreen === 'test' && <TestScreen />}
        {currentScreen === 'profiles' && <ProfilesScreen />}
        {currentScreen === 'config' && <ConfigScreen onConfigSaved={checkConfigExists} />}
      </div>
    </div>
  )
}

export default App
