export interface EnvironmentConfig {
  region: string;
  resources: {
    agentRegistryTable: string;
    toolRegistryTable: string;
    stateMachinePrefix: string;
    s3BucketName: string;
    cloudWatchNamespace: string;
  };
  secrets: {
    openAiSecretName?: string;
    anthropicSecretName?: string;
    bedrockConfigSecretName?: string;
    customSecretsPrefix?: string;
  };
  features: {
    enableStackVisualization: boolean;
    enableCostTracking: boolean;
    enableAdvancedMonitoring: boolean;
  };
}

// This will be populated from environment variables or DynamoDB in the future
export const resourceConfig: Record<string, EnvironmentConfig> = {
  development: {
    region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
    resources: {
      agentRegistryTable: process.env.REACT_APP_AGENT_REGISTRY_TABLE || 'AgentRegistry-dev',
      toolRegistryTable: process.env.REACT_APP_TOOL_REGISTRY_TABLE || 'ToolRegistry-dev',
      stateMachinePrefix: process.env.REACT_APP_STATE_MACHINE_PREFIX || 'StepFunctionsAgent-',
      s3BucketName: process.env.REACT_APP_S3_BUCKET || 'agent-files-dev',
      cloudWatchNamespace: process.env.REACT_APP_CLOUDWATCH_NAMESPACE || 'StepFunctionsAgent'
    },
    secrets: {
      openAiSecretName: '/ai-agent/llm-secrets/dev',
      anthropicSecretName: '/ai-agent/anthropic-secrets/dev',
      customSecretsPrefix: '/ai-agent/custom/'
    },
    features: {
      enableStackVisualization: true,
      enableCostTracking: true,
      enableAdvancedMonitoring: false
    }
  },
  production: {
    region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
    resources: {
      agentRegistryTable: process.env.REACT_APP_AGENT_REGISTRY_TABLE || 'AgentRegistry-prod',
      toolRegistryTable: process.env.REACT_APP_TOOL_REGISTRY_TABLE || 'ToolRegistry-prod',
      stateMachinePrefix: process.env.REACT_APP_STATE_MACHINE_PREFIX || 'StepFunctionsAgent-',
      s3BucketName: process.env.REACT_APP_S3_BUCKET || 'agent-files-prod',
      cloudWatchNamespace: process.env.REACT_APP_CLOUDWATCH_NAMESPACE || 'StepFunctionsAgent'
    },
    secrets: {
      openAiSecretName: '/ai-agent/llm-secrets/prod',
      anthropicSecretName: '/ai-agent/anthropic-secrets/prod',
      customSecretsPrefix: '/ai-agent/custom/'
    },
    features: {
      enableStackVisualization: true,
      enableCostTracking: true,
      enableAdvancedMonitoring: true
    }
  }
};

export const getCurrentConfig = (): EnvironmentConfig => {
  const env = process.env.REACT_APP_ENV || 'development';
  return resourceConfig[env] || resourceConfig.development;
};