import { Authenticator } from '@aws-amplify/ui-react'
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import AgentExecution from './pages/AgentExecution'
import Registries from './pages/Registries'
import History from './pages/History'
import ApprovalDashboard from './pages/ApprovalDashboard'
import Settings from './pages/Settings'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Authenticator>
        {({ signOut, user }) => (
          <Router>
            <div style={{ padding: '20px' }}>
              <header style={{ marginBottom: '20px', borderBottom: '1px solid #ddd', paddingBottom: '10px' }}>
                <h1>Step Functions Agent UI</h1>
                <nav style={{ margin: '10px 0' }}>
                  <Link to="/dashboard" style={{ marginRight: '20px' }}>Dashboard</Link>
                  <Link to="/execute" style={{ marginRight: '20px' }}>Execute Agent</Link>
                  <Link to="/registries" style={{ marginRight: '20px' }}>Registries</Link>
                  <Link to="/history" style={{ marginRight: '20px' }}>History</Link>
                  <Link to="/approvals" style={{ marginRight: '20px' }}>Approvals</Link>
                  <Link to="/settings" style={{ marginRight: '20px' }}>Settings</Link>
                </nav>
                <div>
                  Welcome {user?.username}! 
                  <button onClick={signOut} style={{ marginLeft: '10px' }}>Sign out</button>
                </div>
              </header>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/execute" element={<AgentExecution />} />
                <Route path="/registries" element={<Registries />} />
                <Route path="/history" element={<History />} />
                <Route path="/approvals" element={<ApprovalDashboard />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </Router>
        )}
      </Authenticator>
    </QueryClientProvider>
  )
}

export default App