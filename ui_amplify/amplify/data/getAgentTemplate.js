// AppSync resolver for getting a single agent template by ID
export function request(ctx) {
  var template_id = ctx.args.template_id;
  var version = ctx.args.version || '1.0.0';

  return {
    operation: 'GetItem',
    key: {
      template_id: { S: template_id },
      version: { S: version }
    }
  };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.template_id) {
    return null;
  }

  var item = ctx.result;

  // Parse JSON fields - AppSync auto-unwraps DynamoDB types
  var template = {};
  if (item.template) {
    if (typeof item.template === 'string') {
      template = JSON.parse(item.template);
    } else {
      template = item.template;
    }
  }

  var variables = {};
  if (item.variables) {
    if (typeof item.variables === 'string') {
      variables = JSON.parse(item.variables);
    } else {
      variables = item.variables;
    }
  }

  var metadata = {};
  if (item.metadata) {
    if (typeof item.metadata === 'string') {
      metadata = JSON.parse(item.metadata);
    } else {
      metadata = item.metadata;
    }
  }

  return {
    template_id: item.template_id || '',
    version: item.version || '',
    extraction_name: item.extraction_name || '',
    status: item.status || 'active',
    template: template,
    variables: variables,
    metadata: metadata,
    created_at: item.created_at || '',
    updated_at: item.updated_at || ''
  };
}
