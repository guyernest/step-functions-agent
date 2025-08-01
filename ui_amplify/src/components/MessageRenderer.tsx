import React from 'react'
import {
  Card,
  Text,
  View,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Flex,
  Heading,
  Image,
  Link
} from '@aws-amplify/ui-react'

interface MessageContent {
  type?: string
  text?: string
  content?: any
  name?: string
  input?: any
  tool_use_id?: string
  id?: string
}

interface MessageRendererProps {
  content: string | MessageContent | MessageContent[]
  role: string
}

// Helper function to detect content type
const detectContentType = (content: any): string => {
  if (typeof content === 'string') {
    // Check if it's a URL
    if (content.match(/^https?:\/\//)) {
      if (content.match(/\.(png|jpg|jpeg|gif|webp)$/i)) return 'image'
      if (content.match(/\.html$/i)) return 'html'
      return 'url'
    }
    // Check if it's JSON
    try {
      const parsed = JSON.parse(content)
      return detectContentType(parsed) // Recursively detect type of parsed JSON
    } catch {}
    // Check if it looks like code
    if (content.includes('```')) return 'markdown-code'
    if (content.match(/^(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s/i)) return 'sql'
    return 'text'
  }
  if (Array.isArray(content)) {
    if (content.length > 0 && typeof content[0] === 'object') return 'table'
    return 'array'
  }
  if (typeof content === 'object') {
    // Check for specific patterns
    if (content.answer) return 'answer'
    if (content.error) return 'error'
    // Check for Google Maps Distance Matrix response
    if (content.destination_addresses && content.origin_addresses && content.rows) {
      return 'distance-matrix'
    }
    // Check for weather data
    if (content.weather && content.main && content.name) {
      return 'weather'
    }
    // Check if it's a schema definition (tables with columns)
    const values = Object.values(content)
    if (values.every(v => Array.isArray(v) && v.length > 0 && Array.isArray(v[0]))) {
      return 'schema'
    }
    return 'object'
  }
  return 'unknown'
}

// Render different content types
const renderContent = (content: any, type: string) => {
  switch (type) {
    case 'text':
      return (
        <Text style={{ whiteSpace: 'pre-wrap' }}>{content}</Text>
      )
    
    case 'sql':
      return (
        <Card variation="outlined" backgroundColor="gray.10">
          <Text fontFamily="monospace" fontSize="small" style={{ whiteSpace: 'pre-wrap' }}>
            {content}
          </Text>
        </Card>
      )
    
    case 'json':
      try {
        const parsed = typeof content === 'string' ? JSON.parse(content) : content
        return (
          <Card variation="outlined" backgroundColor="gray.10">
            <Text fontFamily="monospace" fontSize="small" style={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(parsed, null, 2)}
            </Text>
          </Card>
        )
      } catch {
        return <Text>{content}</Text>
      }
    
    case 'image':
      return (
        <Image 
          src={content} 
          alt="Tool output image"
          maxWidth="100%"
          height="auto"
        />
      )
    
    case 'url':
      return (
        <Link href={content} isExternal>
          {content}
        </Link>
      )
    
    case 'html':
      // For security, we'll just show it as a link instead of embedding
      return (
        <View>
          <Text>HTML content available at:</Text>
          <Link href={content} isExternal>{content}</Link>
        </View>
      )
    
    case 'table':
      if (!Array.isArray(content) || content.length === 0) return null
      const headers = Object.keys(content[0])
      
      return (
        <View style={{ overflowX: 'auto' }}>
          <Table>
            <TableHead>
              <TableRow>
                {headers.map(header => (
                  <TableCell as="th" key={header}>
                    {header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {content.map((row, idx) => (
                <TableRow key={idx}>
                  {headers.map(header => (
                    <TableCell key={header}>
                      {String(row[header] ?? '')}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </View>
      )
    
    case 'schema':
      return (
        <View>
          {Object.entries(content).map(([tableName, columns]) => (
            <Card key={tableName} variation="outlined" marginBottom="10px">
              <Heading level={6} marginBottom="10px">Table: {tableName}</Heading>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell as="th">Column Name</TableCell>
                    <TableCell as="th">Type</TableCell>
                    <TableCell as="th">Nullable</TableCell>
                    <TableCell as="th">Default</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(columns as any[]).map((col, idx) => (
                    <TableRow key={idx}>
                      <TableCell fontWeight="medium">{col[1]}</TableCell>
                      <TableCell fontFamily="monospace" fontSize="small">{col[2]}</TableCell>
                      <TableCell>{col[3] === 0 ? 'NOT NULL' : 'NULL'}</TableCell>
                      <TableCell>{col[4] !== null ? String(col[4]) : 'None'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          ))}
        </View>
      )
    
    case 'answer':
      return (
        <Card variation="elevated" backgroundColor="blue.10">
          <Text style={{ whiteSpace: 'pre-wrap' }}>{content.answer}</Text>
        </Card>
      )
    
    case 'error':
      return (
        <Card variation="elevated" backgroundColor="red.10">
          <Text color="red">Error: {content.error}</Text>
          {content.details && (
            <Text fontSize="small" marginTop="5px">{content.details}</Text>
          )}
        </Card>
      )
    
    case 'distance-matrix':
      return (
        <View>
          <Card variation="outlined" marginBottom="10px">
            <Heading level={6} marginBottom="5px">Distance Matrix Results</Heading>
            <Text fontSize="small"><strong>From:</strong> {content.origin_addresses?.join(', ')}</Text>
            <Text fontSize="small"><strong>To:</strong> {content.destination_addresses?.join(', ')}</Text>
          </Card>
          {content.rows?.map((row: any, originIndex: number) => (
            <View key={originIndex}>
              {row.elements?.map((element: any, destIndex: number) => (
                <Card key={destIndex} variation="outlined" marginBottom="10px">
                  <Flex justifyContent="space-between">
                    <View>
                      <Text fontWeight="bold">Route {originIndex + 1} → {destIndex + 1}</Text>
                      {element.status === 'OK' ? (
                        <View marginTop="5px">
                          <Text>📏 Distance: {element.distance?.text}</Text>
                          <Text>⏱️ Duration: {element.duration?.text}</Text>
                          {element.duration_in_traffic && (
                            <Text>🚗 Duration in traffic: {element.duration_in_traffic.text}</Text>
                          )}
                        </View>
                      ) : (
                        <Text color="red">Status: {element.status}</Text>
                      )}
                    </View>
                  </Flex>
                </Card>
              ))}
            </View>
          ))}
          {content.status && content.status !== 'OK' && (
            <Text color="orange" fontSize="small">API Status: {content.status}</Text>
          )}
        </View>
      )
    
    case 'weather':
      return (
        <Card variation="elevated" backgroundColor="blue.10">
          <Heading level={6} marginBottom="10px">🌤️ Weather in {content.name}</Heading>
          <View>
            <Text><strong>Conditions:</strong> {content.weather?.[0]?.description}</Text>
            <Text><strong>Temperature:</strong> {content.main?.temp}°C (feels like {content.main?.feels_like}°C)</Text>
            <Text><strong>Humidity:</strong> {content.main?.humidity}%</Text>
            <Text><strong>Wind:</strong> {content.wind?.speed} m/s</Text>
            {content.clouds && <Text><strong>Cloudiness:</strong> {content.clouds.all}%</Text>}
          </View>
        </Card>
      )
    
    default:
      return (
        <Card variation="outlined" backgroundColor="gray.10">
          <Text fontFamily="monospace" fontSize="small" style={{ whiteSpace: 'pre-wrap' }}>
            {typeof content === 'object' ? JSON.stringify(content, null, 2) : String(content)}
          </Text>
        </Card>
      )
  }
}

// Main component
export const MessageRenderer: React.FC<MessageRendererProps> = ({ content }) => {
  if (typeof content === 'string') {
    const type = detectContentType(content)
    return renderContent(content, type)
  }

  if (Array.isArray(content)) {
    return (
      <View>
        {content.map((item, index) => (
          <View key={index} marginBottom="10px">
            {renderMessageItem(item)}
          </View>
        ))}
      </View>
    )
  }

  return renderMessageItem(content)
}

// Render individual message items (for arrays of content)
const renderMessageItem = (item: MessageContent) => {
  // Handle tool use
  if (item.type === 'tool_use' || item.type === 'function') {
    const toolName = item.name || item.tool_use_id || 'Unknown Tool'
    const toolInput = item.input || {}
    
    return (
      <Card variation="elevated" backgroundColor="gray.80" padding="15px">
        <Flex alignItems="center" gap="10px" marginBottom="10px">
          <Text fontSize="large">🔧</Text>
          <Text fontWeight="bold">Using tool: {toolName}</Text>
        </Flex>
        <Card variation="outlined" backgroundColor="gray.10" padding="10px">
          <Text 
            fontFamily="monospace" 
            fontSize="small" 
            style={{ whiteSpace: 'pre-wrap' }}
          >
            {JSON.stringify(toolInput, null, 2)}
          </Text>
        </Card>
      </Card>
    )
  }

  // Handle tool result
  if (item.type === 'tool_result') {
    let content = item.content
    
    // Parse content if it's a JSON string
    if (typeof content === 'string') {
      try {
        content = JSON.parse(content)
      } catch {}
    }
    
    const type = detectContentType(content)
    
    return (
      <Card variation="elevated" backgroundColor="gray.10" padding="15px">
        <Flex alignItems="center" gap="10px" marginBottom="10px">
          <Text fontSize="large">📊</Text>
          <Text fontWeight="bold">Tool Result</Text>
        </Flex>
        {renderContent(content, type)}
      </Card>
    )
  }

  // Handle text
  if (item.type === 'text' && item.text) {
    const type = detectContentType(item.text)
    return renderContent(item.text, type)
  }

  // Default rendering
  const type = detectContentType(item)
  return renderContent(item, type)
}

export default MessageRenderer