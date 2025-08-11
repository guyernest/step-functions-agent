export function request(ctx) {
  return {
    operation: 'Query',
    index: 'provider-index',
    query: {
      expression: '#provider = :provider AND #is_active = :active',
      expressionNames: {
        '#provider': 'provider',
        '#is_active': 'is_active'
      },
      expressionValues: {
        ':provider': { S: ctx.arguments.provider },
        ':active': { S: 'true' }
      }
    }
  };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.items) {
    return [];
  }
  
  return ctx.result.items
    .map(function(item) {
      return {
        pk: item.pk || '',
        provider: item.provider || '',
        model_id: item.model_id || '',
        display_name: item.display_name || '',
        input_price_per_1k: item.input_price_per_1k || 0,
        output_price_per_1k: item.output_price_per_1k || 0,
        max_tokens: item.max_tokens || 4096,
        supports_tools: item.supports_tools !== false,
        supports_vision: item.supports_vision === true,
        is_active: item.is_active || 'true',
        is_default: item.is_default === true,
        created_at: item.created_at || '',
        updated_at: item.updated_at || ''
      };
    });
}