import React from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import '@aws-amplify/ui-react/styles.css';
import './App.css';

// Pages
import Dashboard from './pages/Dashboard';
import AgentExecution from './pages/AgentExecution';
import Registries from './pages/Registries';
import StackVisualization from './pages/StackVisualization';
import Monitoring from './pages/Monitoring';
import History from './pages/History';
import Settings from './pages/Settings';

// Components
import Layout from './components/Layout/Layout';

function App() {
  return (
    <Authenticator>
      {({ signOut, user }) => (
        <Router>
          <Layout user={user} onSignOut={signOut || (() => {})}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/execute" element={<AgentExecution />} />
              <Route path="/registries" element={<Registries />} />
              <Route path="/stacks" element={<StackVisualization />} />
              <Route path="/monitoring" element={<Monitoring />} />
              <Route path="/history" element={<History />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </Router>
      )}
    </Authenticator>
  );
}

export default App;