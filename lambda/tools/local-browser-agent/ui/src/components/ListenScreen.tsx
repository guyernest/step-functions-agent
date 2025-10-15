import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'

interface PollerStatus {
  is_running: boolean
  current_task: string | null
  last_error: string | null
  tasks_processed: number
}

interface BrowserSession {
  session_id: string
  task_token: string
  started_at: string
  last_heartbeat: string
  url: string
  recording_key: string | null
}

function ListenScreen() {
  const [pollerStatus, setPollerStatus] = useState<PollerStatus | null>(null)
  const [sessions, setSessions] = useState<BrowserSession[]>([])
  const [loading, setLoading] = useState(true)
  const [isPolling, setIsPolling] = useState(false)
  const [actionInProgress, setActionInProgress] = useState(false)

  useEffect(() => {
    // Load initial data
    loadData()

    // Refresh every 2 seconds
    const interval = setInterval(() => {
      loadData()
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [status, activeSessions] = await Promise.all([
        invoke<PollerStatus>('get_poller_status'),
        invoke<BrowserSession[]>('get_active_sessions'),
      ])

      setPollerStatus(status)
      setSessions(activeSessions)
      setIsPolling(status.is_running)
      setLoading(false)
    } catch (error) {
      console.error('Error loading data:', error)
      // If we get a state error, it means not configured yet
      if (error && String(error).includes('state not managed')) {
        setPollerStatus(null)
        setSessions([])
        setIsPolling(false)
      }
      setLoading(false)
    }
  }

  const handleStartPolling = async () => {
    setActionInProgress(true)
    try {
      await invoke('start_polling')
      setIsPolling(true)
      loadData() // Refresh status
    } catch (error) {
      console.error('Error starting polling:', error)
      alert(`Failed to start polling: ${error}`)
    } finally {
      setActionInProgress(false)
    }
  }

  const handleStopPolling = async () => {
    setActionInProgress(true)
    try {
      await invoke('stop_polling')
      setIsPolling(false)
      loadData() // Refresh status
    } catch (error) {
      console.error('Error stopping polling:', error)
      alert(`Failed to stop polling: ${error}`)
    } finally {
      setActionInProgress(false)
    }
  }

  const handleEndSession = async (sessionId: string) => {
    try {
      await invoke('end_session', { sessionId })
      loadData() // Refresh data
    } catch (error) {
      console.error('Error ending session:', error)
      alert(`Failed to end session: ${error}`)
    }
  }

  const handleCleanupIdle = async () => {
    try {
      const count = await invoke<number>('cleanup_idle_sessions', {
        maxIdleSeconds: 300,
      })
      alert(`Cleaned up ${count} idle session(s)`)
      loadData() // Refresh data
    } catch (error) {
      console.error('Error cleaning up idle sessions:', error)
      alert(`Failed to cleanup sessions: ${error}`)
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
        <h2>Listen for Activities</h2>
        <p className="screen-description">
          Listening for browser automation tasks from Step Functions Activity
        </p>
      </div>

      {/* Listen Status Card */}
      <div className="card">
        <div className="card-header">
          <h3>Listen Status</h3>
          <div className="card-actions">
            {!isPolling ? (
              <button
                onClick={handleStartPolling}
                className="btn-success"
                disabled={actionInProgress}
              >
                {actionInProgress ? '⏳ Starting...' : '▶️ Start Listening'}
              </button>
            ) : (
              <button
                onClick={handleStopPolling}
                className="btn-danger"
                disabled={actionInProgress}
              >
                {actionInProgress ? '⏳ Stopping...' : '⏹️ Stop Listening'}
              </button>
            )}
            <button onClick={loadData} className="btn-secondary">
              Refresh
            </button>
          </div>
        </div>

        {pollerStatus && (
          <div className="status-rows">
            <div className="status-row">
              <span className="label">Status:</span>
              <span className={`status ${pollerStatus.is_running ? 'polling' : 'idle'}`}>
                {pollerStatus.is_running ? 'LISTENING' : 'IDLE'}
              </span>
            </div>

            {pollerStatus.current_task && (
              <div className="status-row">
                <span className="label">Current Task:</span>
                <span className="task">{pollerStatus.current_task}</span>
              </div>
            )}

            <div className="status-row">
              <span className="label">Tasks Processed:</span>
              <span>{pollerStatus.tasks_processed}</span>
            </div>

            {pollerStatus.last_error && (
              <div className="status-row">
                <span className="label">Last Error:</span>
                <span className="error-text">{pollerStatus.last_error}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Active Sessions Card */}
      <div className="card">
        <div className="card-header">
          <h3>Active Browser Sessions ({sessions.length})</h3>
          <div className="card-actions">
            {sessions.length > 0 && (
              <button onClick={handleCleanupIdle} className="btn-secondary">
                Cleanup Idle
              </button>
            )}
          </div>
        </div>

        {sessions.length === 0 ? (
          <div className="empty-state">
            <p>No active browser sessions</p>
          </div>
        ) : (
          <div className="sessions-list">
            {sessions.map((session) => (
              <div key={session.session_id} className="session-card">
                <div className="session-header">
                  <h4>Session: {session.session_id.substring(0, 8)}...</h4>
                  <button
                    onClick={() => handleEndSession(session.session_id)}
                    className="btn-danger"
                  >
                    End Session
                  </button>
                </div>

                <div className="session-details">
                  <div className="detail-row">
                    <span className="label">URL:</span>
                    <span className="url">{session.url || 'N/A'}</span>
                  </div>

                  <div className="detail-row">
                    <span className="label">Started:</span>
                    <span>{new Date(session.started_at).toLocaleString()}</span>
                  </div>

                  <div className="detail-row">
                    <span className="label">Last Heartbeat:</span>
                    <span>{new Date(session.last_heartbeat).toLocaleString()}</span>
                  </div>

                  {session.recording_key && (
                    <div className="detail-row">
                      <span className="label">Recording:</span>
                      <span className="recording-key">{session.recording_key}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ListenScreen
