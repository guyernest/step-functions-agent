export function request(ctx) {
  return { operation: 'Scan' };
}

export function response(ctx) {
  if (!ctx.result) {
    return [];
  }
  
  if (!ctx.result.items) {
    return [];
  }
  
  var items = ctx.result.items;
  
  const agents = items
    .filter(item => item.agent_name)
    .map(item => {
      // Parse tools array from JSON string if needed
      var tools = [];
      if (item.tools) {
        // Check if tools is a string that needs parsing
        if (typeof item.tools === 'string' && item.tools.charAt(0) === '[') {
          var parsed = JSON.parse(item.tools);
          // Extract tool names from the parsed data
          if (Array.isArray(parsed)) {
            tools = parsed.map(function(tool) {
              // Handle different tool formats
              if (typeof tool === 'string') {
                return tool;
              } else if (tool && tool.tool_name) {
                return tool.tool_name;
              } else if (tool && tool.name) {
                return tool.name;
              }
              return '';
            }).filter(function(name) { return name !== ''; });
          }
        } else if (Array.isArray(item.tools)) {
          // If tools is already an array
          tools = item.tools;
        }
      }
      
      return {
        id: item.agent_name,
        name: item.agent_name,
        description: item.description || '',
        version: item.version || '1.0.0',
        type: 'agent',
        createdAt: item.created_at || '',
        tools: tools
      };
    });
  
  return agents;
}