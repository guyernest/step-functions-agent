export function request(ctx) {
  // For now, we'll just return a mock response since actual testing
  // would require invoking a Lambda function to make HTTP requests
  // This can be enhanced later to use a Lambda data source
  return {
    operation: 'GetItem',
    key: {
      server_id: ctx.arguments.server_id,
      version: '1.0.0'  // Default to version 1.0.0
    }
  };
}

export function response(ctx) {
  var server_id = ctx.arguments.server_id;
  
  // For now, return a mock successful connection test
  // In production, this would invoke a Lambda function that actually tests the connection
  if (!ctx.result || !ctx.result.item) {
    return {
      success: false,
      message: 'Server not found',
      response_time: 0,
      server_id: server_id,
      endpoint_url: null
    };
  }
  
  var item = ctx.result.item;
  var status = item.status || 'inactive';
  var endpoint = item.endpoint_url || '';
  
  // Generate a simple response time
  var responseTime = 100;
  
  // Mock response based on server status
  if (status === 'active') {
    return {
      success: true,
      message: 'Connection successful',
      response_time: responseTime,
      server_id: server_id,
      endpoint_url: endpoint
    };
  }
  
  if (status === 'unhealthy') {
    return {
      success: false,
      message: 'Server is unhealthy',
      response_time: 5000,
      server_id: server_id,
      endpoint_url: endpoint
    };
  }
  
  if (status === 'maintenance') {
    return {
      success: false,
      message: 'Server is under maintenance',
      response_time: 0,
      server_id: server_id,
      endpoint_url: endpoint
    };
  }
  
  // Default case
  return {
    success: false,
    message: 'Server is not active',
    response_time: 0,
    server_id: server_id,
    endpoint_url: endpoint
  };
}