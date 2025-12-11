import { Outlet, NavLink } from 'react-router-dom'
import { useConnectionStore } from '../stores/connectionStore'

export default function Layout() {
  const { isConnected, backendStatus } = useConnectionStore()

  return (
    <div className="flex flex-col h-screen bg-studio-bg">
      {/* Top Navigation Bar */}
      <header className="h-12 bg-studio-panel border-b border-studio-accent/30 flex items-center px-4 gap-6">
        {/* App Logo/Title */}
        <div className="flex items-center gap-2">
          <svg className="w-6 h-6 text-studio-highlight" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span className="font-semibold text-white">Navigation Studio</span>
        </div>

        {/* Navigation Links */}
        <nav className="flex gap-1">
          <NavLink
            to="/studio"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-studio-accent text-white'
                  : 'text-gray-400 hover:text-white hover:bg-studio-accent/50'
              }`
            }
          >
            Studio
          </NavLink>
          <NavLink
            to="/scripts"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-studio-accent text-white'
                  : 'text-gray-400 hover:text-white hover:bg-studio-accent/50'
              }`
            }
          >
            Scripts
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-studio-accent text-white'
                  : 'text-gray-400 hover:text-white hover:bg-studio-accent/50'
              }`
            }
          >
            Settings
          </NavLink>
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Connection Status */}
        <div className="flex items-center gap-2 text-sm">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-gray-400">
            {isConnected ? backendStatus : 'Disconnected'}
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}
