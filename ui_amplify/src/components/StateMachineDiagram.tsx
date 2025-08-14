import React from 'react'
import { WorkflowViewer } from 'asl-viewer'
import 'asl-viewer/dist/index.css'
import { View, Text, Alert } from '@aws-amplify/ui-react'

interface StateMachineDiagramProps {
  asl: any
  name?: string
  width?: number
  height?: number
}

const StateMachineDiagram: React.FC<StateMachineDiagramProps> = ({ 
  asl, 
  name,
  width = 900, 
  height = 600 
}) => {
  const [error] = React.useState<string | null>(null)

  if (!asl) {
    return (
      <Alert variation="warning">
        No state machine definition available for visualization
      </Alert>
    )
  }

  // Prepare the definition for the viewer
  // The AslViewer accepts both strings and objects
  let definition = asl
  
  // If it's already a string, keep it as is
  // If it's an object, it will be used directly
  if (typeof asl === 'object' && asl !== null) {
    // Validate minimal structure
    if (!asl.States && !asl.Comment) {
      console.warn('ASL may be missing States property:', asl)
    }
  }

  return (
    <View>
      {name && <Text fontSize="large" fontWeight="bold" marginBottom="10px">{name}</Text>}
      <View 
        style={{ 
          width: width, 
          height: height,
          border: '1px solid #ddd',
          borderRadius: '4px',
          overflow: 'auto',
          backgroundColor: '#fff',
          padding: '10px'
        }}
      >
        <WorkflowViewer
          definition={definition}
          theme="light"
          height={height - 20}
        />
      </View>
      {error && (
        <Alert variation="error" marginTop="10px">
          {error}
        </Alert>
      )}
    </View>
  )
}

export default StateMachineDiagram