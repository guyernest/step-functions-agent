export function request(ctx) {
  var agentName = ctx.arguments.agentName;
  var version = ctx.arguments.version;
  var modelId = ctx.arguments.modelId;
  
  return {
    operation: 'UpdateItem',
    key: {
      agent_name: { S: agentName },
      version: { S: version }
    },
    update: {
      expression: 'SET llm_model = :modelId',
      expressionValues: {
        ':modelId': { S: modelId }
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
    agentName: ctx.arguments.agentName,
    modelId: ctx.arguments.modelId
  };
}