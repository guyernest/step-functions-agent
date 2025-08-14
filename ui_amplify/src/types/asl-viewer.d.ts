declare module 'asl-viewer' {
  import React from 'react'
  
  interface WorkflowViewerProps {
    definition: any // ASL JSON object or string
    className?: string
    theme?: 'light' | 'dark' | 'highContrast' | 'soft'
    height?: number
    width?: number
    fitView?: boolean
    onStateClick?: (stateName: string) => void
    onConnectionClick?: (connection: any) => void
  }
  
  export const WorkflowViewer: React.FC<WorkflowViewerProps>
}

declare module 'asl-viewer/dist/index.css'