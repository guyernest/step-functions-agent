export function request(ctx) {
  var resourceType = ctx.arguments.resource_type;
  var id = ctx.arguments.id;
  
  return {
    operation: 'DeleteItem',
    key: {
      resource_type: util.dynamodb.toDynamoDB(resourceType),
      id: util.dynamodb.toDynamoDB(id)
    }
  };
}

export function response(ctx) {
  if (ctx.error) {
    // Ignore error if item doesn't exist
    if (ctx.error.type === 'ResourceNotFoundException') {
      return true;
    }
    return false;
  }
  
  return true;
}