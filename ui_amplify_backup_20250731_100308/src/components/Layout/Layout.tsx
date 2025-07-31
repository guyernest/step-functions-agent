import React from 'react';
import { View, Flex, Button, Heading, Divider } from '@aws-amplify/ui-react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  user: any;
  onSignOut: () => void;
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ user, onSignOut, children }) => {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/execute', label: 'Execute Agent', icon: '🤖' },
    { path: '/registries', label: 'Registries', icon: '📚' },
    { path: '/stacks', label: 'Stacks', icon: '🏗️' },
    { path: '/monitoring', label: 'Monitoring', icon: '📈' },
    { path: '/history', label: 'History', icon: '📜' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <View className="layout-container">
      <View className="header">
        <Flex justifyContent="space-between" alignItems="center">
          <Heading level={3}>Step Functions Agent Management</Heading>
          <Flex gap="1rem" alignItems="center">
            <span>Welcome, {user?.attributes?.email || 'User'}</span>
            <Button onClick={onSignOut} size="small">Sign Out</Button>
          </Flex>
        </Flex>
      </View>
      <Divider />
      <Flex className="main-layout">
        <View className="sidebar">
          <nav>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </Link>
            ))}
          </nav>
        </View>
        <View className="content">
          {children}
        </View>
      </Flex>
    </View>
  );
};

export default Layout;