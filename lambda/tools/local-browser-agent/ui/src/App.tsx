import { useState, useEffect } from 'react'
import ConfigScreen from './components/ConfigScreen'
import ListenScreen from './components/ListenScreen'
import TestScreen from './components/TestScreen'

type Screen = 'listen' | 'test' | 'config'

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('listen')
  const [configExists, setConfigExists] = useState(false)

  useEffect(() => {
    // Check if config.yaml exists
    checkConfigExists()
  }, [])

  const checkConfigExists = async () => {
    // TODO: Add command to check if config exists
    // For now, always show config first
    setConfigExists(false)
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
        {currentScreen === 'config' && <ConfigScreen onConfigSaved={() => setConfigExists(true)} />}
      </div>
    </div>
  )
}

export default App
