export function request(ctx) {
  var resourceType = ctx.arguments.resource_type;
  var resourceId = ctx.arguments.resource_id;
  
  return {
    operation: 'Query',
    query: {
      expression: 'resource_type = :type AND begins_with(id, :prefix)',
      expressionValues: util.dynamodb.toMapValues({
        ':type': resourceType,
        ':prefix': resourceId + '#'
      })
    }
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
      id: item.id,
      resource_type: item.resource_type,
      resource_id: item.resource_id,
      test_name: item.test_name,
      description: item.description,
      // AWSJSON expects strings, not parsed objects
      test_input: item.input || '{}',
      expected_output: item.expected_output || null,
      metadata: item.metadata || null,
      created_at: item.created_at,
      updated_at: item.updated_at
    };
  });
}