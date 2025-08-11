export function request(ctx) {
  return { operation: 'Scan' };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.items) {
    return [];
  }
  
  return ctx.result.items
    .filter(function(item) { 
      return item.agent_name; 
    })
    .map(function(item) {
      // Parse tools array from JSON string if needed
      var tools = [];
      if (item.tools) {
        if (typeof item.tools === 'string' && item.tools.charAt(0) === '[') {
          var parsed = JSON.parse(item.tools);
          if (Array.isArray(parsed)) {
            tools = parsed.map(function(tool) {
              if (typeof tool === 'string') {
                return tool;
              } else if (tool && tool.tool_name) {
                return tool.tool_name;
              } else if (tool && tool.name) {
                return tool.name;
              }
              return '';
            }).filter(function(name) { 
              return name !== ''; 
            });
          }
        } else if (Array.isArray(item.tools)) {
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
        tools: tools,
        systemPrompt: item.system_prompt || '',
        llmProvider: item.llm_provider || '',
        llmModel: item.llm_model || '',
        status: item.status || 'active',
        parameters: item.parameters || '{}',
        metadata: item.metadata || '{}',
        observability: item.observability || '{}'
      };
    });
}