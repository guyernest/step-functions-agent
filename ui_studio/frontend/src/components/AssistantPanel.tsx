import { useState, useRef, useEffect } from 'react'
import { useConnectionStore } from '../stores/connectionStore'
import { useScriptStore } from '../stores/scriptStore'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  toolCalls?: Array<{
    tool: string
    input: Record<string, unknown>
    result?: Record<string, unknown>
  }>
}

export default function AssistantPanel() {
  const { isConnected, sessionId, sendMessage: wsSendMessage } = useConnectionStore()
  const { addStep } = useScriptStore()

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI assistant. I can help you build browser automation scripts by navigating pages, clicking elements, and building scripts step-by-step. Start a browser session and tell me what you'd like to automate!",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Listen for WebSocket messages
  useEffect(() => {
    const handleWsMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'ai_thinking') {
          setIsThinking(true)
        } else if (data.type === 'ai_response') {
          setIsThinking(false)
          const assistantMessage: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.response,
            timestamp: new Date(),
            toolCalls: data.tool_results,
          }
          setMessages((prev) => [...prev, assistantMessage])

          // If script steps were generated, add them to the script
          if (data.script_steps && data.script_steps.length > 0) {
            data.script_steps.forEach((step: Record<string, unknown>) => {
              addStep({
                id: crypto.randomUUID(),
                type: step.action as 'click' | 'fill' | 'navigate' | 'wait' | 'screenshot' | 'extract',
                description: step.description as string,
                value: step.value as string | undefined,
                url: step.url as string | undefined,
                locators: step.locator ? [{
                  type: (step.locator as Record<string, string>).strategy,
                  value: (step.locator as Record<string, string>).value,
                }] : undefined,
              })
            })
          }
        } else if (data.type === 'ai_tool_call') {
          // Show tool call in progress
          const toolMessage: Message = {
            id: crypto.randomUUID(),
            role: 'system',
            content: `Using tool: ${data.tool}`,
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, toolMessage])
        } else if (data.type === 'ai_error') {
          setIsThinking(false)
          const errorMessage: Message = {
            id: crypto.randomUUID(),
            role: 'system',
            content: `Error: ${data.error}`,
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, errorMessage])
        }
      } catch {
        // Ignore non-JSON messages
      }
    }

    // Get the websocket from the store
    const ws = useConnectionStore.getState().websocket
    if (ws) {
      ws.addEventListener('message', handleWsMessage)
      return () => ws.removeEventListener('message', handleWsMessage)
    }
  }, [addStep])

  const handleSend = () => {
    if (!input.trim() || !isConnected) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')

    // Send to backend
    wsSendMessage({
      action: 'ai_chat',
      message: input,
      session_id: sessionId,
      assistant_id: 'default',
    })
  }

  const handleQuickAction = (action: string) => {
    if (!isConnected) return

    let message = ''
    switch (action) {
      case 'screenshot':
        message = 'Take a screenshot and describe what you see on the page.'
        break
      case 'analyze':
        message = 'Analyze the current page and suggest what automation steps could be performed.'
        break
      case 'build':
        message = 'Help me build a script to automate this page. What elements can I interact with?'
        break
      default:
        return
    }

    setInput(message)
  }

  const handleClearHistory = () => {
    setMessages([{
      id: crypto.randomUUID(),
      role: 'assistant',
      content: "Chat cleared. How can I help you?",
      timestamp: new Date(),
    }])

    if (isConnected) {
      wsSendMessage({
        action: 'ai_clear_history',
        assistant_id: 'default',
      })
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-10 px-3 flex items-center gap-2 border-b border-studio-accent/30 bg-studio-panel">
        <svg className="w-4 h-4 text-studio-highlight" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span className="text-sm font-medium text-gray-300">AI Assistant</span>
        <div className="flex-1" />
        <button
          onClick={handleClearHistory}
          className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded hover:bg-studio-accent/30"
          title="Clear chat history"
        >
          Clear
        </button>
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div className="px-3 py-2 bg-yellow-500/10 border-b border-yellow-500/20 text-xs text-yellow-400">
          Connect to backend to use AI assistant
        </div>
      )}
      {isConnected && !sessionId && (
        <div className="px-3 py-2 bg-blue-500/10 border-b border-blue-500/20 text-xs text-blue-400">
          Start a browser session to enable browser automation tools
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                message.role === 'user'
                  ? 'bg-studio-highlight text-white'
                  : message.role === 'system'
                  ? 'bg-studio-accent/30 text-gray-400 text-xs italic'
                  : 'bg-studio-accent/50 text-gray-200'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.toolCalls && message.toolCalls.length > 0 && (
                <div className="mt-2 pt-2 border-t border-white/10 text-xs text-gray-400">
                  <span className="font-medium">Tools used:</span>
                  <ul className="mt-1 space-y-0.5">
                    {message.toolCalls.map((tc, i) => (
                      <li key={i} className="flex items-center gap-1">
                        <span className="text-studio-highlight">{tc.tool}</span>
                        {tc.result && (
                          <span className={tc.result.status === 'success' ? 'text-green-400' : 'text-red-400'}>
                            ({tc.result.status as string})
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {isThinking && (
          <div className="flex justify-start">
            <div className="bg-studio-accent/50 rounded-lg px-3 py-2 text-sm text-gray-400 flex items-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-studio-accent/30">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder={isConnected ? "Ask for help..." : "Connect to backend first..."}
            disabled={!isConnected}
            className="flex-1 px-3 py-2 bg-studio-bg border border-studio-accent/30 rounded-md text-sm text-white placeholder-gray-500 focus:outline-none focus:border-studio-highlight disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isThinking || !isConnected}
            className="px-3 py-2 bg-studio-highlight hover:bg-studio-highlight/80 disabled:opacity-50 disabled:cursor-not-allowed rounded-md text-white"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => handleQuickAction('screenshot')}
            disabled={!isConnected || !sessionId}
            className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded hover:bg-studio-accent/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Screenshot
          </button>
          <button
            onClick={() => handleQuickAction('analyze')}
            disabled={!isConnected || !sessionId}
            className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded hover:bg-studio-accent/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Analyze page
          </button>
          <button
            onClick={() => handleQuickAction('build')}
            disabled={!isConnected || !sessionId}
            className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded hover:bg-studio-accent/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Build script
          </button>
        </div>
      </div>
    </div>
  )
}
