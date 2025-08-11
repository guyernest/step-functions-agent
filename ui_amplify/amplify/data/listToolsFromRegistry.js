export function request(ctx) {
  return { operation: 'Scan' };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.items) {
    return [];
  }
  
  return ctx.result.items
    .filter(function(item) {
      return item.tool_name || item.name;
    })
    .map(function(item) {
      return {
        id: item.tool_name || item.name || '',
        name: item.tool_name || item.name || '',
        description: item.description || '',
        version: item.version || '1.0.0',
        type: 'tool',
        createdAt: item.created_at || item.createdAt || '',
        language: item.language || 'python',
        lambda_function_name: item.lambda_function_name || '',
        lambda_arn: item.lambda_arn || '',
        inputSchema: item.input_schema || null
      };
    });
}