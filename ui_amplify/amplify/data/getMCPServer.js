export function request(ctx) {
  var server_id = ctx.arguments.server_id;
  var version = ctx.arguments.version;
  
  if (version) {
    // Get specific version
    return {
      operation: 'GetItem',
      key: {
        server_id: server_id,
        version: version
      }
    };
  } else {
    // For simplicity, default to version 1.0.0 if not specified
    // In production, you could use Query to get the latest version
    return {
      operation: 'GetItem',
      key: {
        server_id: server_id,
        version: '1.0.0'
      }
    };
  }
}

export function response(ctx) {
  if (!ctx.result) {
    return null;
  }
  
  var item = null;
  
  // Handle GetItem response
  if (ctx.result.item) {
    item = ctx.result.item;
  }
  // Handle Query response
  else if (ctx.result.items && ctx.result.items.length > 0) {
    item = ctx.result.items[0];
  }
  
  if (!item) {
    return null;
  }
  
  // Parse available_tools from JSON string if needed
  var tools = [];
  if (item.available_tools) {
    if (typeof item.available_tools === 'string' && item.available_tools.charAt(0) === '[') {
      var parsed = JSON.parse(item.available_tools);
      if (Array.isArray(parsed)) {
        tools = parsed;
      }
    } else if (Array.isArray(item.available_tools)) {
      tools = item.available_tools;
    }
  }
  
  // Parse configuration from JSON string if needed
  var config = null;
  if (item.configuration) {
    if (typeof item.configuration === 'string' && (item.configuration.charAt(0) === '{' || item.configuration.charAt(0) === '[')) {
      config = JSON.parse(item.configuration);
    } else {
      config = item.configuration;
    }
  }
  
  // Parse metadata from JSON string if needed
  var meta = null;
  if (item.metadata) {
    if (typeof item.metadata === 'string' && (item.metadata.charAt(0) === '{' || item.metadata.charAt(0) === '[')) {
      meta = JSON.parse(item.metadata);
    } else {
      meta = item.metadata;
    }
  }
  
  return {
    server_id: item.server_id,
    version: item.version || '1.0.0',
    server_name: item.server_name || '',
    description: item.description || '',
    endpoint_url: item.endpoint_url || '',
    protocol_type: item.protocol_type || 'jsonrpc',
    authentication_type: item.authentication_type || 'none',
    api_key_header: item.api_key_header || null,
    available_tools: tools,
    status: item.status || 'inactive',
    health_check_url: item.health_check_url || null,
    health_check_interval: item.health_check_interval || null,
    configuration: config,
    metadata: meta,
    deployment_stack: item.deployment_stack || null,
    deployment_region: item.deployment_region || null,
    created_at: item.created_at || '2024-01-01T00:00:00Z',
    updated_at: item.updated_at || '2024-01-01T00:00:00Z',
    created_by: item.created_by || null
  };
}