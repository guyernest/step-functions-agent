import React from 'react'
import { Card, Heading, Text, View } from '@aws-amplify/ui-react'

const Dashboard: React.FC = () => {
  return (
    <View>
      <Heading level={2}>Dashboard</Heading>
      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Welcome to Step Functions Agent UI</Heading>
        <Text>This is the dashboard page. More features coming soon!</Text>
      </Card>
    </View>
  )
}

export default Dashboard