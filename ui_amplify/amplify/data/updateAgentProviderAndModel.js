export function request(ctx) {
  var agentName = ctx.arguments.agentName;
  var version = ctx.arguments.version;
  var provider = ctx.arguments.provider;
  var modelId = ctx.arguments.modelId;
  
  // Map provider names back to what agent registry expects
  // UI uses company names (anthropic, google) but registry might use model family names (claude, gemini)
  var providerMapping = {
    'anthropic': 'anthropic',
    'google': 'google',
    'openai': 'openai',
    'amazon': 'amazon',
    'xai': 'xai',
    'deepseek': 'deepseek'
  };
  
  var mappedProvider = providerMapping[provider] || provider;
  
  return {
    operation: 'UpdateItem',
    key: {
      agent_name: { S: agentName },
      version: { S: version }
    },
    update: {
      expression: 'SET llm_provider = :provider, llm_model = :modelId',
      expressionValues: {
        ':provider': { S: mappedProvider },
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
    provider: ctx.arguments.provider,
    modelId: ctx.arguments.modelId
  };
}