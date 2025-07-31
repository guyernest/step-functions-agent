import React from 'react'
import { Authenticator } from '@aws-amplify/ui-react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'

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
                <div>
                  Welcome {user?.username}! 
                  <button onClick={signOut} style={{ marginLeft: '10px' }}>Sign out</button>
                </div>
              </header>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </div>
          </Router>
        )}
      </Authenticator>
    </QueryClientProvider>
  )
}

export default App