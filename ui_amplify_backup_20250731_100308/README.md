# Step Functions Agent Management UI

A modern React-based UI for managing Step Functions agents, built with AWS Amplify Gen 2.

## Features

- 🤖 **Agent Execution**: Execute agents with real-time chat interface
- 📚 **Registry Management**: Browse and search agents and tools
- 🏗️ **Stack Visualization**: View CloudFormation stack dependencies
- 📊 **Monitoring**: Real-time metrics and CloudWatch integration
- 📜 **Execution History**: Track all agent executions with search
- ⚙️ **Settings**: Manage resources, secrets, and feature flags

## Tech Stack

- **Frontend**: React 18 with TypeScript
- **UI Components**: AWS Amplify UI React
- **State Management**: React Query
- **Backend**: AWS Amplify Gen 2
- **Authentication**: AWS Cognito
- **API**: GraphQL with AWS AppSync
- **Database**: DynamoDB

## Prerequisites

- Node.js 16+ and npm
- AWS CLI configured with appropriate credentials
- Amplify CLI (`npm install -g @aws-amplify/cli`)

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables** (create `.env.local`):
   ```bash
   REACT_APP_AWS_REGION=us-east-1
   REACT_APP_ENV=development
   REACT_APP_AGENT_REGISTRY_TABLE=AgentRegistry-dev
   REACT_APP_TOOL_REGISTRY_TABLE=ToolRegistry-dev
   REACT_APP_STATE_MACHINE_PREFIX=StepFunctionsAgent-
   REACT_APP_S3_BUCKET=agent-files-dev
   REACT_APP_CLOUDWATCH_NAMESPACE=StepFunctionsAgent
   ```

3. **Initialize Amplify backend**:
   ```bash
   npx amplify sandbox
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

## Project Structure

```
src/
├── components/        # Reusable UI components
│   └── Layout/       # Main layout with navigation
├── config/           # Configuration files
│   └── resources.ts  # Resource configuration
├── pages/            # Page components
│   ├── Dashboard.tsx
│   ├── AgentExecution.tsx
│   ├── Registries.tsx
│   ├── StackVisualization.tsx
│   ├── Monitoring.tsx
│   ├── History.tsx
│   └── Settings.tsx
├── hooks/            # Custom React hooks
├── utils/            # Utility functions
├── types/            # TypeScript type definitions
├── App.tsx          # Main app component
└── index.tsx        # Entry point
```

## Configuration

### Phase 1: Configuration File
The app uses a configuration file (`src/config/resources.ts`) to define resource names and settings. This can be customized per environment.

### Phase 2: DynamoDB Configuration (Coming Soon)
Configuration will be migrated to DynamoDB for dynamic updates without redeployment.

### Phase 3: Settings UI (Coming Soon)
A comprehensive settings page will allow administrators to manage configuration through the UI.

## Authentication

The app uses AWS Cognito for authentication with two user groups:
- **Users**: Standard access to execute agents and view data
- **Admins**: Additional access to manage secrets and configuration

## Deployment

1. **Build the app**:
   ```bash
   npm run build
   ```

2. **Deploy with Amplify**:
   ```bash
   npx amplify deploy
   ```

## Development

### Adding New Pages
1. Create a new component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Layout/Layout.tsx`

### Connecting to Backend Resources
The app expects existing backend resources (DynamoDB tables, Step Functions, etc.) to be deployed separately. Configure resource names in:
- Environment variables (`.env.local`)
- Configuration file (`src/config/resources.ts`)

## Troubleshooting

### Amplify Sandbox Issues
- Ensure AWS credentials are configured
- Check that all required environment variables are set
- Review CloudFormation stack events in AWS Console

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Ensure TypeScript version compatibility
- Check for missing type definitions

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

[Your License Here]