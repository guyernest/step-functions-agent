import { Authenticator } from '@aws-amplify/ui-react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import AgentExecution from './pages/AgentExecution'
import Registries from './pages/Registries'
import MCPServers from './pages/MCPServers'
import History from './pages/History'
import ApprovalDashboard from './pages/ApprovalDashboard'
import Settings from './pages/Settings'
import ExecutionDetail from './pages/ExecutionDetail'
import Test from './pages/Test'
import ToolTest from './pages/ToolTest'
import MCPTest from './pages/MCPTest'
import Layout from './components/Layout'
import Metrics from './pages/Metrics'
import ModelCosts from './pages/ModelCosts'
import ToolSecrets from './pages/ToolSecrets'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Authenticator>
        {({ signOut, user }) => (
          <Router>
            <Layout user={user} signOut={signOut}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/execute" element={<AgentExecution />} />
                <Route path="/registries" element={<Registries />} />
                <Route path="/mcp-servers" element={<MCPServers />} />
                <Route path="/history" element={<History />} />
                <Route path="/execution/:executionArn" element={<ExecutionDetail />} />
                <Route path="/approvals" element={<ApprovalDashboard />} />
                <Route path="/metrics" element={<Metrics />} />
                <Route path="/model-costs" element={<ModelCosts />} />
                <Route path="/tool-secrets" element={<ToolSecrets />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/test" element={<Test />} />
                <Route path="/tool-test" element={<ToolTest />} />
                <Route path="/mcp-test" element={<MCPTest />} />
              </Routes>
            </Layout>
          </Router>
        )}
      </Authenticator>
    </QueryClientProvider>
  )
}

export default App