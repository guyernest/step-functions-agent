import { util } from '@aws-appsync/utils';

export function request(ctx) {
  var provider = ctx.arguments.provider;
  var modelId = ctx.arguments.model_id;
  var displayName = ctx.arguments.display_name;
  var inputPrice = ctx.arguments.input_price_per_1k;
  var outputPrice = ctx.arguments.output_price_per_1k;
  var maxTokens = ctx.arguments.max_tokens;
  var supportsTools = ctx.arguments.supports_tools;
  var supportsVision = ctx.arguments.supports_vision;
  var isDefault = ctx.arguments.is_default;
  
  var timestamp = util.time.nowISO8601();
  var pk = provider + '#' + modelId;
  
  return {
    operation: 'PutItem',
    key: {
      pk: { S: pk }
    },
    attributeValues: {
      pk: { S: pk },
      provider: { S: provider },
      model_id: { S: modelId },
      display_name: { S: displayName },
      input_price_per_1k: { N: '' + inputPrice },
      output_price_per_1k: { N: '' + outputPrice },
      max_tokens: maxTokens ? { N: '' + maxTokens } : { NULL: true },
      supports_tools: { BOOL: supportsTools || false },
      supports_vision: { BOOL: supportsVision || false },
      is_active: { S: 'true' },
      is_default: { BOOL: isDefault || false },
      created_at: { S: timestamp },
      updated_at: { S: timestamp }
    }
  };
}

export function response(ctx) {
  if (ctx.error) {
    return {
      success: false,
      error: ctx.error.message
    };
  }
  
  return {
    success: true,
    message: 'Model added successfully'
  };
}