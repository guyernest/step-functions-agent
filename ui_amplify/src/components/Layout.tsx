import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  View,
  Flex,
  Text,
  Button,
  Divider,
  Card,
  Icon,
  Input,
} from '@aws-amplify/ui-react'
import { MdDashboard, MdPlayArrow, MdStorage, MdHistory, MdApproval, MdSettings, MdLogout, MdInsights, MdAttachMoney, MdBugReport, MdVpnKey, MdExtension, MdEdit, MdCheck, MdClose } from 'react-icons/md'

const DEFAULT_TITLE = 'Step Functions Agent'
const DEFAULT_SUBTITLE = 'AI Agent Management Console'

interface LayoutProps {
  children: React.ReactNode
  user: any
  signOut?: (() => void) | ((data?: any) => void)
}

const Layout: React.FC<LayoutProps> = ({ children, user, signOut }) => {
  const [title, setTitle] = useState(() => localStorage.getItem('customTitle') || DEFAULT_TITLE)
  const [subtitle, setSubtitle] = useState(() => localStorage.getItem('customSubtitle') || DEFAULT_SUBTITLE)
  const [editingTitle, setEditingTitle] = useState(false)
  const [draftTitle, setDraftTitle] = useState(title)
  const [draftSubtitle, setDraftSubtitle] = useState(subtitle)

  const saveTitle = () => {
    const newTitle = draftTitle.trim() || DEFAULT_TITLE
    const newSubtitle = draftSubtitle.trim() || DEFAULT_SUBTITLE
    setTitle(newTitle)
    setSubtitle(newSubtitle)
    localStorage.setItem('customTitle', newTitle)
    localStorage.setItem('customSubtitle', newSubtitle)
    setEditingTitle(false)
  }

  const cancelEditTitle = () => {
    setDraftTitle(title)
    setDraftSubtitle(subtitle)
    setEditingTitle(false)
  }

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: MdDashboard },
    { path: '/execute', label: 'Execute Agent', icon: MdPlayArrow },
    { path: '/registries', label: 'Registries', icon: MdStorage },
    { path: '/mcp-servers', label: 'MCP Servers', icon: MdExtension },
    { path: '/history', label: 'History', icon: MdHistory },
    { path: '/approvals', label: 'Approvals', icon: MdApproval },
    { path: '/metrics', label: 'Metrics', icon: MdInsights },
    { path: '/model-costs', label: 'Model Management', icon: MdAttachMoney },
    { path: '/tool-secrets', label: 'Tool Secrets', icon: MdVpnKey },
    { path: '/tool-test', label: 'Tool Test', icon: MdBugReport },
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
          {editingTitle ? (
            <Flex direction="column" gap="8px">
              <Input
                size="small"
                value={draftTitle}
                onChange={(e) => setDraftTitle(e.target.value)}
                placeholder={DEFAULT_TITLE}
                autoFocus
                onKeyDown={(e) => { if (e.key === 'Enter') saveTitle(); if (e.key === 'Escape') cancelEditTitle(); }}
              />
              <Input
                size="small"
                value={draftSubtitle}
                onChange={(e) => setDraftSubtitle(e.target.value)}
                placeholder={DEFAULT_SUBTITLE}
                onKeyDown={(e) => { if (e.key === 'Enter') saveTitle(); if (e.key === 'Escape') cancelEditTitle(); }}
              />
              <Flex gap="4px">
                <Button size="small" variation="primary" onClick={saveTitle} gap="4px">
                  <Icon as={MdCheck} fontSize="16px" />
                  Save
                </Button>
                <Button size="small" onClick={cancelEditTitle} gap="4px">
                  <Icon as={MdClose} fontSize="16px" />
                  Cancel
                </Button>
              </Flex>
            </Flex>
          ) : (
            <Flex direction="row" alignItems="flex-start" justifyContent="space-between">
              <View>
                <Text fontSize="xl" fontWeight="bold" color="#047D95">
                  {title}
                </Text>
                <Text fontSize="small" color="gray" marginTop="4px">
                  {subtitle}
                </Text>
              </View>
              <Button
                size="small"
                variation="link"
                padding="4px"
                onClick={() => { setDraftTitle(title); setDraftSubtitle(subtitle); setEditingTitle(true); }}
                title="Customize title"
              >
                <Icon as={MdEdit} fontSize="16px" color="gray" />
              </Button>
            </Flex>
          )}
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