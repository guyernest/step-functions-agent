export function request(ctx) {
  var agentName = ctx.arguments.agentName;
  var version = ctx.arguments.version;
  var systemPrompt = ctx.arguments.systemPrompt;
  
  return {
    operation: 'UpdateItem',
    key: {
      agent_name: { S: agentName },
      version: { S: version }
    },
    update: {
      expression: 'SET system_prompt = :systemPrompt',
      expressionValues: {
        ':systemPrompt': { S: systemPrompt }
      }
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
    agentName: ctx.arguments.agentName
  };
}