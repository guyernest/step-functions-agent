import { create } from 'zustand'
import { useBrowserStore } from './browserStore'

interface ConnectionState {
  isConnected: boolean
  backendStatus: string
  websocket: WebSocket | null
  sessionId: string | null

  connect: (url?: string) => void
  disconnect: () => void
  setStatus: (status: string) => void
  sendMessage: (message: object) => void
  startBrowserSession: (options?: { headless?: boolean; profileName?: string }) => void
  closeBrowserSession: () => void
}

const DEFAULT_WS_URL = 'ws://localhost:8765/ws'

export const useConnectionStore = create<ConnectionState>((set, get) => ({
  isConnected: false,
  backendStatus: 'Ready',
  websocket: null,
  sessionId: null,

  connect: (url = DEFAULT_WS_URL) => {
    const { websocket } = get()
    if (websocket) {
      websocket.close()
    }

    set({ backendStatus: 'Connecting...' })
    const ws = new WebSocket(url)

    ws.onopen = () => {
      set({ isConnected: true, backendStatus: 'Connected', websocket: ws })
      console.log('WebSocket connected')
    }

    ws.onclose = () => {
      set({ isConnected: false, backendStatus: 'Disconnected', websocket: null, sessionId: null })
      console.log('WebSocket disconnected')
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      set({ backendStatus: 'Error' })
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('Received message:', message)
        handleMessage(message)
      } catch (e) {
        console.error('Failed to parse message:', e)
      }
    }

    set({ websocket: ws })
  },

  disconnect: () => {
    const { websocket, sessionId } = get()
    if (sessionId) {
      get().closeBrowserSession()
    }
    if (websocket) {
      websocket.close()
    }
    set({ websocket: null, isConnected: false, sessionId: null })
  },

  setStatus: (status: string) => {
    set({ backendStatus: status })
  },

  sendMessage: (message: object) => {
    const { websocket, isConnected } = get()
    if (websocket && isConnected) {
      websocket.send(JSON.stringify(message))
    } else {
      console.warn('Cannot send message: WebSocket not connected')
    }
  },

  startBrowserSession: (options = {}) => {
    const { sendMessage, isConnected } = get()
    if (!isConnected) {
      console.warn('Cannot start session: not connected')
      return
    }
    sendMessage({
      action: 'start_session',
      headless: options.headless ?? false,
      profile_name: options.profileName,
    })
    set({ backendStatus: 'Starting browser...' })
  },

  closeBrowserSession: () => {
    const { sendMessage, sessionId, isConnected } = get()
    if (!isConnected || !sessionId) {
      return
    }
    sendMessage({
      action: 'close_session',
      session_id: sessionId,
    })
    set({ sessionId: null })
  },
}))

// Handle incoming messages
function handleMessage(message: { type: string; [key: string]: unknown }) {
  const { type, ...data } = message

  switch (type) {
    case 'session_started':
      useConnectionStore.setState({
        sessionId: data.session_id as string,
        backendStatus: 'Browser ready',
      })
      console.log('Browser session started:', data.session_id)
      break

    case 'session_closed':
      useConnectionStore.setState({
        sessionId: null,
        backendStatus: 'Connected',
      })
      break

    case 'screenshot':
      if (data.screenshot) {
        useBrowserStore.getState().setScreenshot(`data:image/png;base64,${data.screenshot}`)
        useBrowserStore.getState().setCurrentUrl(data.url as string)
      }
      break

    case 'navigate_complete':
    case 'click_complete':
    case 'fill_complete':
      if (data.status === 'success') {
        useConnectionStore.setState({ backendStatus: 'Ready' })
      } else if (data.error) {
        useConnectionStore.setState({ backendStatus: `Error: ${data.error}` })
      }
      break

    case 'page_info':
      useBrowserStore.getState().setCurrentUrl(data.url as string)
      break

    case 'recording_status':
      useBrowserStore.getState().setIsRecording(data.status === 'recording_started')
      break

    case 'recording_complete':
      useBrowserStore.getState().setIsRecording(false)
      console.log('Recording complete, steps:', data.steps)
      break

    case 'error':
      console.error('Backend error:', data.error)
      useConnectionStore.setState({ backendStatus: `Error: ${data.error}` })
      break

    case 'pong':
      // Heartbeat response
      break

    default:
      console.log('Unknown message type:', type)
  }
}
