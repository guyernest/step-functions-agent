import React from 'react';
import { Card, Text, View, Divider } from '@aws-amplify/ui-react';

const ExpectedData: React.FC = () => {
  const expectedAgents = [
    {
      id: "WebScraperLongContent-v1.0",
      name: "WebScraperLongContent",
      version: "v1.0",
      description: "WebScraperLongContent - AI-powered agent",
      tools: ["web_scraper_large"],
      status: "active"
    },
    {
      id: "sql-agent-v1.0", 
      name: "sql-agent",
      version: "v1.0",
      description: "SQL query generation and database analysis agent",
      tools: ["get_db_schema", "execute_sql_query", "execute_python"],
      status: "active"
    }
  ];

  const expectedTools = [
    {
      id: "maps_distance_matrix-latest",
      name: "maps_distance_matrix", 
      version: "latest",
      description: "Calculate distances and travel times between multiple origins and destinations",
      status: "active"
    },
    {
      id: "semantic_search_rust-latest",
      name: "semantic_search_rust",
      version: "latest", 
      description: "Perform semantic search using Qdrant vector database with Cohere embeddings in Rust",
      status: "active"
    }
  ];

  return (
    <Card marginBottom="2rem">
      <View>
        <Text fontSize="large" fontWeight="bold">Expected Data After Backend Deployment</Text>
        
        <Divider marginTop="1rem" marginBottom="1rem" />
        
        <Text fontWeight="bold">Agents ({expectedAgents.length}):</Text>
        {expectedAgents.map(agent => (
          <Card key={agent.id} variation="outlined" marginTop="0.5rem">
            <Text fontWeight="semibold">{agent.name}</Text>
            <Text fontSize="small" color="gray.60">{agent.description}</Text>
            <Text fontSize="small">Tools: {agent.tools.join(', ')}</Text>
          </Card>
        ))}
        
        <Divider marginTop="1rem" marginBottom="1rem" />
        
        <Text fontWeight="bold">Tools ({expectedTools.length}):</Text>
        {expectedTools.map(tool => (
          <Card key={tool.id} variation="outlined" marginTop="0.5rem">
            <Text fontWeight="semibold">{tool.name}</Text>
            <Text fontSize="small" color="gray.60">{tool.description}</Text>
          </Card>
        ))}
        
        <Divider marginTop="1rem" marginBottom="1rem" />
        
        <Text fontSize="small" color="orange.60">
          ⚠️ To see this data in the actual UI, you need to redeploy the Amplify backend to update the Lambda functions with the correct table names and data parsing logic.
        </Text>
      </View>
    </Card>
  );
};

export default ExpectedData;