export function request(ctx) {
  var resourceId = ctx.arguments.resource_id;
  var limit = ctx.arguments.limit;
  
  return {
    operation: 'Query',
    query: {
      expression: 'resource_id = :id',
      expressionValues: util.dynamodb.toMapValues({
        ':id': resourceId
      })
    },
    index: 'resource-results-index',
    limit: limit || 20,
    scanIndexForward: false  // Most recent first
  };
}

export function response(ctx) {
  if (ctx.error) {
    return [];
  }
  
  if (!ctx.result || !ctx.result.items) {
    return [];
  }
  
  var items = ctx.result.items;
  
  return items.map(function(item) {
    return {
      test_event_id: item.test_event_id,
      executed_at: item.executed_at,
      resource_id: item.resource_id,
      execution_time: item.execution_time || 0,
      success: item.success,
      // AWSJSON expects strings, not parsed objects
      output: item.output || null,
      error: item.error,
      metadata: item.metadata || null
    };
  });
}