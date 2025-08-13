import { util } from '@aws-appsync/utils';

export function request(ctx) {
  return {
    operation: 'Scan',
    limit: 100
  };
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }
  
  if (!ctx.result || !ctx.result.items) {
    return [];
  }
  
  return ctx.result.items.map(function(item) {
    return {
      tool_name: item.tool_name || '',
      secret_keys: item.secret_keys || [],
      description: item.description || '',
      registered_at: item.registered_at || '',
      environment: item.environment || 'prod'
    };
  });
}