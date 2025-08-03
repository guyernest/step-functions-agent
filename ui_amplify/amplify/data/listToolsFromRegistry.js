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
  
  // Log first item to see structure (remove in production)
  if (items.length > 0) {
    console.log('First tool item:', JSON.stringify(items[0]));
  }
  
  const tools = items
    .filter(item => item.tool_name || item.name)
    .map(item => ({
      id: item.tool_name || item.name || '',
      name: item.tool_name || item.name || '',
      description: item.description || '',
      version: item.version || '1.0.0',
      type: 'tool',
      createdAt: item.created_at || item.createdAt || ''
    }));
  
  return tools;
}