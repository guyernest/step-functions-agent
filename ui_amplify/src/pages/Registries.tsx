import React from 'react'
import { Card, Heading, Text, View } from '@aws-amplify/ui-react'

const Registries: React.FC = () => {
  return (
    <View>
      <Heading level={2}>Agent & Tool Registries</Heading>
      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Registered Agents</Heading>
        <Text>List of registered agents will appear here.</Text>
      </Card>
      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Registered Tools</Heading>
        <Text>List of registered tools will appear here.</Text>
      </Card>
    </View>
  )
}

export default Registries