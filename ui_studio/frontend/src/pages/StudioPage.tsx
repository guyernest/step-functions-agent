import { useEffect } from 'react'
import { useConnectionStore } from '../stores/connectionStore'
import { useBrowserStore } from '../stores/browserStore'
import BrowserPanel from '../components/BrowserPanel'
import ScriptPanel from '../components/ScriptPanel'
import AssistantPanel from '../components/AssistantPanel'

export default function StudioPage() {
  const { connect, isConnected } = useConnectionStore()
  const { isRecording, setRecording } = useBrowserStore()

  useEffect(() => {
    // Auto-connect to backend on mount
    if (!isConnected) {
      connect()
    }
  }, [connect, isConnected])

  return (
    <div className="flex h-full gap-2 p-2">
      {/* Left Panel: Browser View */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Browser Controls */}
        <div className="h-10 panel mb-2 flex items-center px-3 gap-3">
          <button
            onClick={() => setRecording(!isRecording)}
            className={`btn ${isRecording ? 'btn-primary recording-indicator' : 'btn-secondary'}`}
          >
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </button>
          <div className="h-6 w-px bg-studio-accent/50" />
          <button className="btn btn-secondary">Run Script</button>
          <button className="btn btn-secondary">Run Step</button>
        </div>

        {/* Browser View */}
        <div className="flex-1 panel overflow-hidden">
          <BrowserPanel />
        </div>
      </div>

      {/* Right Panel: Script Editor + AI Assistant */}
      <div className="w-[450px] flex flex-col gap-2">
        {/* Script Editor */}
        <div className="flex-1 panel overflow-hidden flex flex-col">
          <div className="panel-header flex items-center justify-between">
            <span>Script Editor</span>
            <div className="flex gap-1">
              <button className="text-xs px-2 py-1 rounded bg-studio-accent/50 hover:bg-studio-accent">
                Visual
              </button>
              <button className="text-xs px-2 py-1 rounded text-gray-400 hover:bg-studio-accent/50">
                YAML
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto">
            <ScriptPanel />
          </div>
        </div>

        {/* AI Assistant */}
        <div className="h-[300px] panel overflow-hidden flex flex-col">
          <div className="panel-header">AI Assistant</div>
          <div className="flex-1 overflow-hidden">
            <AssistantPanel />
          </div>
        </div>
      </div>
    </div>
  )
}
