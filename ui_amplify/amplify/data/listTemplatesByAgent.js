// AppSync resolver for listing templates by agent name
export function request(ctx) {
  var agent_name = ctx.args.agent_name;
  // Convert hyphens to underscores for extraction_name matching
  var extraction_name = agent_name.replace(/-/g, '_');

  return {
    operation: 'Scan',
    filter: {
      expression: 'contains(#metadata, :agent_name) OR #extraction_name = :agent_name OR #extraction_name = :extraction_name_value',
      expressionNames: {
        '#metadata': 'metadata',
        '#extraction_name': 'extraction_name'
      },
      expressionValues: {
        ':agent_name': { S: agent_name },
        ':extraction_name_value': { S: extraction_name }
      }
    }
  };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.items) {
    return [];
  }

  return ctx.result.items
    .filter(function(item) {
      return item.template_id;
    })
    .map(function(item) {
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
    })
    .filter(function(template) {
      return template.status === 'active';
    });
}
