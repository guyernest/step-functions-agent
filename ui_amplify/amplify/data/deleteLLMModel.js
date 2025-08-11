export function request(ctx) {
  var pk = ctx.arguments.pk;
  
  return {
    operation: 'DeleteItem',
    key: {
      pk: { S: pk }
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
    message: 'Model deleted successfully'
  };
}