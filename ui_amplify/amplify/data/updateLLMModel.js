import { util } from '@aws-appsync/utils';

export function request(ctx) {
  var pk = ctx.arguments.pk;
  var updateExpression = 'SET updated_at = :updated_at';
  var expressionValues = {
    ':updated_at': { S: util.time.nowISO8601() }
  };
  
  // Build update expression dynamically based on provided arguments
  if (ctx.arguments.display_name !== undefined) {
    updateExpression += ', display_name = :display_name';
    expressionValues[':display_name'] = { S: ctx.arguments.display_name };
  }
  
  if (ctx.arguments.input_price_per_1k !== undefined) {
    updateExpression += ', input_price_per_1k = :input_price';
    expressionValues[':input_price'] = { N: ctx.arguments.input_price_per_1k.toString() };
  }
  
  if (ctx.arguments.output_price_per_1k !== undefined) {
    updateExpression += ', output_price_per_1k = :output_price';
    expressionValues[':output_price'] = { N: ctx.arguments.output_price_per_1k.toString() };
  }
  
  if (ctx.arguments.max_tokens !== undefined) {
    updateExpression += ', max_tokens = :max_tokens';
    expressionValues[':max_tokens'] = ctx.arguments.max_tokens ? 
      { N: ctx.arguments.max_tokens.toString() } : { NULL: true };
  }
  
  if (ctx.arguments.supports_tools !== undefined) {
    updateExpression += ', supports_tools = :supports_tools';
    expressionValues[':supports_tools'] = { BOOL: ctx.arguments.supports_tools };
  }
  
  if (ctx.arguments.supports_vision !== undefined) {
    updateExpression += ', supports_vision = :supports_vision';
    expressionValues[':supports_vision'] = { BOOL: ctx.arguments.supports_vision };
  }
  
  if (ctx.arguments.is_active !== undefined) {
    updateExpression += ', is_active = :is_active';
    expressionValues[':is_active'] = { S: ctx.arguments.is_active };
  }
  
  if (ctx.arguments.is_default !== undefined) {
    updateExpression += ', is_default = :is_default';
    expressionValues[':is_default'] = { BOOL: ctx.arguments.is_default };
  }
  
  return {
    operation: 'UpdateItem',
    key: {
      pk: { S: pk }
    },
    update: {
      expression: updateExpression,
      expressionValues: expressionValues
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
    message: 'Model updated successfully'
  };
}