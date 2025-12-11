import { useBrowserStore } from '../stores/browserStore'
import { useConnectionStore } from '../stores/connectionStore'
import { useEffect } from 'react'

export default function BrowserPanel() {
  const { currentUrl, screenshot, isRecording, selectedElement } = useBrowserStore()
  const {
    isConnected,
    backendStatus,
    sessionId,
    connect,
    startBrowserSession,
    closeBrowserSession,
    sendMessage,
  } = useConnectionStore()

  // Auto-connect on mount
  useEffect(() => {
    if (!isConnected) {
      connect()
    }
  }, [])

  const handleRefreshScreenshot = () => {
    if (sessionId) {
      sendMessage({ action: 'screenshot', session_id: sessionId })
    }
  }

  const handleNavigate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const url = formData.get('url') as string
    if (sessionId && url) {
      sendMessage({ action: 'navigate', session_id: sessionId, url })
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Connection Controls */}
      <div className="h-10 px-3 flex items-center gap-2 border-b border-studio-accent/30 bg-studio-panel">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-xs text-gray-400">{backendStatus}</span>
        <div className="flex-1" />
        {!isConnected ? (
          <button
            onClick={() => connect()}
            className="px-3 py-1 text-xs bg-studio-accent hover:bg-studio-accent/80 rounded"
          >
            Connect
          </button>
        ) : !sessionId ? (
          <button
            onClick={() => startBrowserSession()}
            className="px-3 py-1 text-xs bg-studio-highlight hover:bg-studio-highlight/80 rounded text-white"
          >
            Start Browser
          </button>
        ) : (
          <button
            onClick={() => closeBrowserSession()}
            className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 rounded text-white"
          >
            Close Browser
          </button>
        )}
      </div>

      {/* URL Bar */}
      <form onSubmit={handleNavigate} className="h-10 px-3 flex items-center gap-2 border-b border-studio-accent/30">
        <div className="flex gap-1">
          <button
            type="button"
            onClick={handleRefreshScreenshot}
            disabled={!sessionId}
            className="w-7 h-7 rounded hover:bg-studio-accent/50 flex items-center justify-center text-gray-400 disabled:opacity-50"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <div className="flex-1">
          <input
            type="text"
            name="url"
            defaultValue={currentUrl || ''}
            placeholder="Enter URL and press Enter"
            disabled={!sessionId}
            className="w-full px-3 py-1.5 bg-studio-bg border border-studio-accent/30 rounded text-sm text-gray-300 focus:outline-none focus:border-studio-highlight disabled:opacity-50"
          />
        </div>
        {isRecording && (
          <div className="flex items-center gap-1.5 text-sm text-studio-highlight">
            <div className="w-2 h-2 rounded-full bg-studio-highlight recording-indicator" />
            Recording
          </div>
        )}
      </form>

      {/* Browser Viewport / Screenshot */}
      <div className="flex-1 relative bg-white/5 overflow-auto">
        {screenshot ? (
          <img
            src={screenshot}
            alt="Browser view"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
            <svg className="w-16 h-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            {!isConnected ? (
              <>
                <p className="text-lg mb-2">Backend not connected</p>
                <p className="text-sm text-gray-600">Click "Connect" to start</p>
              </>
            ) : !sessionId ? (
              <>
                <p className="text-lg mb-2">No browser session</p>
                <p className="text-sm text-gray-600">Click "Start Browser" to begin</p>
              </>
            ) : (
              <>
                <p className="text-lg mb-2">Browser ready</p>
                <p className="text-sm text-gray-600">Navigate to a URL or click Refresh</p>
              </>
            )}
          </div>
        )}

        {/* Selected Element Overlay */}
        {selectedElement && (
          <div
            className="absolute border-2 border-studio-highlight pointer-events-none"
            style={{
              left: selectedElement.boundingBox.x,
              top: selectedElement.boundingBox.y,
              width: selectedElement.boundingBox.width,
              height: selectedElement.boundingBox.height,
            }}
          />
        )}
      </div>

      {/* Status Bar */}
      <div className="h-6 px-3 flex items-center text-xs text-gray-500 border-t border-studio-accent/30 bg-studio-panel/50">
        <span>{sessionId ? `Session: ${sessionId}` : 'No session'}</span>
        <div className="flex-1" />
        {selectedElement && (
          <span className="text-studio-highlight">
            &lt;{selectedElement.tag}&gt; selected
          </span>
        )}
      </div>
    </div>
  )
}
