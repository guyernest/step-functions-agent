import React from 'react'
import { Card, Heading, Text, View } from '@aws-amplify/ui-react'

const History: React.FC = () => {
  return (
    <View>
      <Heading level={2}>Execution History</Heading>
      <Card variation="elevated" marginTop="20px">
        <Heading level={4}>Recent Executions</Heading>
        <Text>Execution history will be displayed here.</Text>
      </Card>
    </View>
  )
}

export default History