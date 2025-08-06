import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  View,
  Flex,
  Text,
  Button,
  Divider,
  Card,
  Icon
} from '@aws-amplify/ui-react'
import { MdDashboard, MdPlayArrow, MdStorage, MdHistory, MdApproval, MdSettings, MdLogout, MdInsights, MdAttachMoney } from 'react-icons/md'

interface LayoutProps {
  children: React.ReactNode
  user: any
  signOut?: (() => void) | ((data?: any) => void)
}

const Layout: React.FC<LayoutProps> = ({ children, user, signOut }) => {

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: MdDashboard },
    { path: '/execute', label: 'Execute Agent', icon: MdPlayArrow },
    { path: '/registries', label: 'Registries', icon: MdStorage },
    { path: '/history', label: 'History', icon: MdHistory },
    { path: '/approvals', label: 'Approvals', icon: MdApproval },
    { path: '/metrics', label: 'Metrics', icon: MdInsights },
    { path: '/model-costs', label: 'Model Costs', icon: MdAttachMoney },
    { path: '/settings', label: 'Settings', icon: MdSettings },
  ]

  const navLinkStyle = (isActive: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    textDecoration: 'none',
    color: isActive ? '#047D95' : '#414141',
    backgroundColor: isActive ? '#E6F7F9' : 'transparent',
    borderRadius: '8px',
    transition: 'all 0.2s ease',
    fontWeight: isActive ? '600' : '400',
  })

  const getUserEmail = () => {
    // Try to get email from different possible attributes
    return user?.attributes?.email || user?.signInDetails?.loginId || user?.username || 'User'
  }

  return (
    <Flex height="100vh" backgroundColor="#F5F5F5">
      {/* Sidebar */}
      <View
        as="nav"
        width="280px"
        backgroundColor="white"
        boxShadow="0 0 10px rgba(0,0,0,0.1)"
        height="100%"
      >
        <Flex direction="column" height="100%">
        {/* Logo/Title */}
        <View padding="24px 16px">
          <Text fontSize="xl" fontWeight="bold" color="#047D95">
            Step Functions Agent
          </Text>
          <Text fontSize="small" color="gray" marginTop="4px">
            AI Agent Management Console
          </Text>
        </View>

        <Divider />

        {/* Navigation Links */}
        <View flex="1" padding="16px" overflow="auto">
          <Flex direction="column" gap="8px">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => navLinkStyle(isActive)}
              >
                <Icon as={item.icon} fontSize="20px" />
                <Text>{item.label}</Text>
              </NavLink>
            ))}
          </Flex>
        </View>

        <Divider />

        {/* User Info & Sign Out */}
        <View padding="16px">
          <Card variation="outlined" padding="12px" marginBottom="12px">
            <Text fontSize="small" color="gray" marginBottom="4px">
              Signed in as
            </Text>
            <Text fontSize="small" fontWeight="medium" style={{ wordBreak: 'break-all' }}>
              {getUserEmail()}
            </Text>
          </Card>
          
          <Button
            variation="primary"
            size="small"
            width="100%"
            onClick={() => signOut && signOut()}
            gap="8px"
          >
            <Icon as={MdLogout} />
            Sign Out
          </Button>
        </View>
        </Flex>
      </View>

      {/* Main Content Area */}
      <View flex="1" overflow="hidden">
        <View
          as="main"
          padding="24px"
          height="100%"
          overflow="auto"
          backgroundColor="#F5F5F5"
        >
          <View maxWidth="1400px" margin="0 auto">
            {children}
          </View>
        </View>
      </View>
    </Flex>
  )
}

export default Layout