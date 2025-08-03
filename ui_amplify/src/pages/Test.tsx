import React, { useEffect } from 'react'
import { View, Text, Heading } from '@aws-amplify/ui-react'
import { generateClient } from 'aws-amplify/data'
import type { Schema } from '../../amplify/data/resource'

const client = generateClient<Schema>()

const Test: React.FC = () => {
  useEffect(() => {
    console.log('Available queries:', Object.keys(client.queries || {}))
    console.log('Available mutations:', Object.keys(client.mutations || {}))
    console.log('Client structure:', client)
  }, [])

  return (
    <View>
      <Heading level={2}>GraphQL Client Test</Heading>
      <Text>Check the browser console for available queries and mutations.</Text>
    </View>
  )
}

export default Test