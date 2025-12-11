import { useState, useEffect } from 'react'
import { useSettingsStore } from '../stores/settingsStore'

export default function SettingsPage() {
  const {
    backendUrl,
    browserProfile,
    aiModel,
    autoAnalyze,
    anthropicApiKey,
    apiKeyConfigured,
    isLoading,
    error,
    setBackendUrl,
    setBrowserProfile,
    setAiModel,
    setAutoAnalyze,
    setAnthropicApiKey,
    loadSettings,
    saveSettings,
    testApiKey,
  } = useSettingsStore()

  const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null)
  const [isTesting, setIsTesting] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  const handleSave = async () => {
    await saveSettings()
    setSaveSuccess(true)
    setTimeout(() => setSaveSuccess(false), 3000)
  }

  const handleTestApiKey = async () => {
    setIsTesting(true)
    setTestResult(null)
    const result = await testApiKey()
    setTestResult(result)
    setIsTesting(false)
  }

  return (
    <div className="p-4 h-full max-w-2xl">
      <h1 className="text-xl font-semibold text-white mb-6">Settings</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-md text-red-400 text-sm">
          {error}
        </div>
      )}

      {saveSuccess && (
        <div className="mb-4 p-3 bg-green-500/20 border border-green-500/50 rounded-md text-green-400 text-sm">
          Settings saved successfully!
        </div>
      )}

      <div className="space-y-6">
        {/* API Keys */}
        <div className="panel p-4">
          <h2 className="text-lg font-medium text-white mb-4">API Keys</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Anthropic API Key</label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={anthropicApiKey}
                    onChange={(e) => setAnthropicApiKey(e.target.value)}
                    placeholder={apiKeyConfigured ? '••••••••••••••••' : 'sk-ant-...'}
                    className="w-full px-3 py-2 bg-studio-bg border border-studio-accent/30 rounded-md text-white placeholder-gray-500 focus:outline-none focus:border-studio-highlight font-mono text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    {showApiKey ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                <button
                  onClick={handleTestApiKey}
                  disabled={isTesting || !apiKeyConfigured}
                  className="px-3 py-2 bg-studio-accent/50 hover:bg-studio-accent/70 disabled:opacity-50 disabled:cursor-not-allowed rounded-md text-white text-sm"
                >
                  {isTesting ? 'Testing...' : 'Test'}
                </button>
              </div>
              <div className="flex items-center gap-2 mt-2">
                {apiKeyConfigured ? (
                  <span className="text-xs text-green-400 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    API key configured
                  </span>
                ) : (
                  <span className="text-xs text-yellow-400 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    No API key configured
                  </span>
                )}
              </div>
              {testResult && (
                <div className={`mt-2 text-xs ${testResult.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                  {testResult.message}
                </div>
              )}
              <p className="text-xs text-gray-500 mt-2">
                Get your API key from{' '}
                <a
                  href="https://console.anthropic.com/settings/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-studio-highlight hover:underline"
                >
                  console.anthropic.com
                </a>
              </p>
            </div>
          </div>
        </div>

        {/* Backend Connection */}
        <div className="panel p-4">
          <h2 className="text-lg font-medium text-white mb-4">Backend Connection</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">WebSocket URL</label>
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                className="w-full px-3 py-2 bg-studio-bg border border-studio-accent/30 rounded-md text-white focus:outline-none focus:border-studio-highlight"
              />
            </div>
          </div>
        </div>

        {/* Browser Settings */}
        <div className="panel p-4">
          <h2 className="text-lg font-medium text-white mb-4">Browser Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Browser Profile</label>
              <select
                value={browserProfile}
                onChange={(e) => setBrowserProfile(e.target.value)}
                className="w-full px-3 py-2 bg-studio-bg border border-studio-accent/30 rounded-md text-white focus:outline-none focus:border-studio-highlight"
              >
                <option value="default">Default</option>
                <option value="work">Work</option>
                <option value="testing">Testing</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Browser profiles store cookies, passwords, and session data
              </p>
            </div>
          </div>
        </div>

        {/* AI Assistant Settings */}
        <div className="panel p-4">
          <h2 className="text-lg font-medium text-white mb-4">AI Assistant</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Model</label>
              <select
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
                className="w-full px-3 py-2 bg-studio-bg border border-studio-accent/30 rounded-md text-white focus:outline-none focus:border-studio-highlight"
              >
                <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                <option value="claude-3-haiku-20240307">Claude 3 Haiku (faster, cheaper)</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="autoAnalyze"
                checked={autoAnalyze}
                onChange={(e) => setAutoAnalyze(e.target.checked)}
                className="rounded border-studio-accent/30 bg-studio-bg text-studio-highlight focus:ring-studio-highlight"
              />
              <label htmlFor="autoAnalyze" className="text-sm text-gray-400">
                Auto-analyze elements during recording
              </label>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="btn btn-primary disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
