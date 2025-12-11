import { useState } from 'react'
import { useScriptStore, type Step } from '../stores/scriptStore'
import { useConnectionStore } from '../stores/connectionStore'

export default function ScriptPanel() {
  const { currentScript, removeStep, updateScriptName } = useScriptStore()
  const { isConnected, sessionId, sendMessage } = useConnectionStore()
  const [isExecuting, setIsExecuting] = useState(false)
  const [executingStepIndex, setExecutingStepIndex] = useState<number | null>(null)

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'click':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
          </svg>
        )
      case 'fill':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        )
      case 'navigate':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        )
      case 'wait':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'screenshot':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        )
      case 'extract':
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        )
      default:
        return (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        )
    }
  }

  const getStabilityColor = (stability?: 'high' | 'medium' | 'low') => {
    switch (stability) {
      case 'high':
        return 'text-green-400'
      case 'medium':
        return 'text-yellow-400'
      case 'low':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const handleExecuteScript = () => {
    if (!isConnected || !sessionId || !currentScript) return

    setIsExecuting(true)
    setExecutingStepIndex(0)

    // Convert steps to backend format
    const scriptPayload = {
      name: currentScript.name,
      starting_page: currentScript.startUrl,
      steps: currentScript.steps.map((step) => ({
        action: step.type,
        description: step.description,
        locator: step.locators?.[0] ? {
          strategy: step.locators[0].type,
          value: step.locators[0].value
        } : undefined,
        url: step.url,
        value: step.value,
      }))
    }

    sendMessage({
      action: 'execute_script',
      session_id: sessionId,
      script: scriptPayload
    })
  }

  const handleStopScript = () => {
    if (!isConnected || !sessionId) return
    sendMessage({
      action: 'stop_script',
      session_id: sessionId
    })
    setIsExecuting(false)
    setExecutingStepIndex(null)
  }

  const handleExecuteSingleStep = (step: Step, _index: number) => {
    if (!isConnected || !sessionId) return

    const stepPayload = {
      action: step.type,
      description: step.description,
      locator: step.locators?.[0] ? {
        strategy: step.locators[0].type,
        value: step.locators[0].value
      } : undefined,
      url: step.url,
      value: step.value,
    }

    sendMessage({
      action: 'execute_step',
      session_id: sessionId,
      step: stepPayload
    })
  }

  if (!currentScript || currentScript.steps.length === 0) {
    return (
      <div className="h-full flex flex-col">
        {/* Toolbar */}
        <div className="h-10 px-3 flex items-center gap-2 border-b border-studio-accent/30 bg-studio-panel">
          <span className="text-sm font-medium text-gray-300">Script Editor</span>
        </div>

        <div className="flex-1 p-4 flex flex-col items-center justify-center text-gray-500">
          <svg className="w-12 h-12 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-sm">No steps recorded</p>
          <p className="text-xs text-gray-600 mt-1">Use the AI assistant to build a script</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="h-10 px-3 flex items-center gap-2 border-b border-studio-accent/30 bg-studio-panel">
        <span className="text-sm font-medium text-gray-300">Script Editor</span>
        <div className="flex-1" />
        {!isExecuting ? (
          <button
            onClick={handleExecuteScript}
            disabled={!isConnected || !sessionId}
            className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white flex items-center gap-1"
          >
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
            Run
          </button>
        ) : (
          <button
            onClick={handleStopScript}
            className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 rounded text-white flex items-center gap-1"
          >
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" />
            </svg>
            Stop
          </button>
        )}
      </div>

      {/* Script Header */}
      <div className="px-3 py-2 border-b border-studio-accent/20">
        <input
          type="text"
          value={currentScript.name}
          onChange={(e) => updateScriptName(e.target.value)}
          className="w-full bg-transparent text-white font-medium focus:outline-none text-sm"
          placeholder="Script name..."
        />
        <input
          type="text"
          value={currentScript.startUrl || ''}
          className="w-full bg-transparent text-xs text-gray-400 focus:outline-none mt-1"
          placeholder="Start URL..."
          readOnly
        />
      </div>

      {/* Steps List */}
      <div className="flex-1 overflow-auto p-2 space-y-2">
        {currentScript.steps.map((step, index) => (
          <div
            key={step.id}
            className={`group relative bg-studio-bg/50 rounded-lg border transition-colors ${
              executingStepIndex === index
                ? 'border-studio-highlight animate-pulse'
                : 'border-studio-accent/20 hover:border-studio-accent/50'
            }`}
          >
            <div className="flex items-start gap-3 p-3">
              {/* Step Number */}
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                executingStepIndex === index
                  ? 'bg-studio-highlight text-white'
                  : 'bg-studio-accent/50 text-gray-300'
              }`}>
                {index + 1}
              </div>

              {/* Step Icon */}
              <div className="w-8 h-8 rounded bg-studio-accent/30 flex items-center justify-center text-gray-300">
                {getStepIcon(step.type)}
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase text-studio-highlight font-medium">
                    {step.type}
                  </span>
                </div>
                <p className="text-sm text-white mt-0.5 truncate">
                  {step.description}
                </p>
                {step.value && (
                  <p className="text-xs text-gray-400 mt-0.5 truncate">
                    Value: {step.value}
                  </p>
                )}
                {step.locators && step.locators.length > 0 && (
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-xs text-gray-500 font-mono truncate max-w-[200px]">
                      {step.locators[0]?.value}
                    </span>
                    <span className={`text-xs ${getStabilityColor(step.locators[0]?.stability)}`}>
                      {step.locators[0]?.stability || 'unknown'}
                    </span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                <button
                  onClick={() => handleExecuteSingleStep(step, index)}
                  disabled={!isConnected || !sessionId || isExecuting}
                  className="w-6 h-6 rounded hover:bg-green-500/30 flex items-center justify-center text-gray-400 hover:text-green-400 disabled:opacity-50"
                  title="Run this step"
                >
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </button>
                <button className="w-6 h-6 rounded hover:bg-studio-accent/50 flex items-center justify-center text-gray-400 hover:text-white">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <button
                  onClick={() => removeStep(step.id)}
                  className="w-6 h-6 rounded hover:bg-red-500/30 flex items-center justify-center text-gray-400 hover:text-red-400"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="h-8 px-3 flex items-center text-xs text-gray-500 border-t border-studio-accent/30 bg-studio-panel/50">
        <span>{currentScript.steps.length} steps</span>
        <div className="flex-1" />
        {isExecuting && <span className="text-studio-highlight">Executing...</span>}
      </div>
    </div>
  )
}
