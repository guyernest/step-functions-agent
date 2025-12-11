import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Settings {
  backendUrl: string
  browserProfile: string
  aiModel: string
  autoAnalyze: boolean
  anthropicApiKey: string
  apiKeyConfigured: boolean
}

interface SettingsState extends Settings {
  isLoading: boolean
  error: string | null

  setBackendUrl: (url: string) => void
  setBrowserProfile: (profile: string) => void
  setAiModel: (model: string) => void
  setAutoAnalyze: (value: boolean) => void
  setAnthropicApiKey: (key: string) => void

  loadSettings: () => Promise<void>
  saveSettings: () => Promise<void>
  testApiKey: () => Promise<{ status: string; message: string }>
}

const API_BASE = 'http://localhost:8765'

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // Default values
      backendUrl: 'ws://localhost:8765/studio',
      browserProfile: 'default',
      aiModel: 'claude-sonnet-4-20250514',
      autoAnalyze: true,
      anthropicApiKey: '',
      apiKeyConfigured: false,
      isLoading: false,
      error: null,

      setBackendUrl: (url) => set({ backendUrl: url }),
      setBrowserProfile: (profile) => set({ browserProfile: profile }),
      setAiModel: (model) => set({ aiModel: model }),
      setAutoAnalyze: (value) => set({ autoAnalyze: value }),
      setAnthropicApiKey: (key) => set({ anthropicApiKey: key }),

      loadSettings: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_BASE}/api/settings`)
          if (!response.ok) {
            throw new Error('Failed to load settings')
          }
          const data = await response.json()
          if (data.status === 'success') {
            set({
              backendUrl: data.settings.backend_url || get().backendUrl,
              browserProfile: data.settings.browser_profile || get().browserProfile,
              aiModel: data.settings.ai_model || get().aiModel,
              autoAnalyze: data.settings.auto_analyze ?? get().autoAnalyze,
              anthropicApiKey: data.settings.anthropic_api_key || '',
              apiKeyConfigured: data.api_key_configured,
              isLoading: false,
            })
          }
        } catch (error) {
          set({ isLoading: false, error: (error as Error).message })
        }
      },

      saveSettings: async () => {
        const state = get()
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_BASE}/api/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              backend_url: state.backendUrl,
              browser_profile: state.browserProfile,
              ai_model: state.aiModel,
              auto_analyze: state.autoAnalyze,
              anthropic_api_key: state.anthropicApiKey,
            }),
          })
          if (!response.ok) {
            throw new Error('Failed to save settings')
          }
          const data = await response.json()
          set({
            isLoading: false,
            apiKeyConfigured: data.api_key_configured,
            // Clear the API key from local state after saving (it's now stored securely on backend)
            anthropicApiKey: '',
          })
        } catch (error) {
          set({ isLoading: false, error: (error as Error).message })
        }
      },

      testApiKey: async () => {
        try {
          const response = await fetch(`${API_BASE}/api/settings/test-api-key`, {
            method: 'POST',
          })
          if (!response.ok) {
            throw new Error('Failed to test API key')
          }
          return await response.json()
        } catch (error) {
          return { status: 'error', message: (error as Error).message }
        }
      },
    }),
    {
      name: 'navigation-studio-settings',
      // Only persist non-sensitive data locally
      partialize: (state) => ({
        backendUrl: state.backendUrl,
        browserProfile: state.browserProfile,
        aiModel: state.aiModel,
        autoAnalyze: state.autoAnalyze,
      }),
    }
  )
)
