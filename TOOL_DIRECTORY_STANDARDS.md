# Tool Directory Structure Standards

## Overview
This document defines the standard directory structure for all Lambda tools to ensure consistency across different languages and deployment methods.

## Standard Directory Structure

### Python Tools
```
lambda/tools/{tool-name}/
├── index.py                 # Main Lambda handler
├── requirements.txt         # Python dependencies
├── template.yaml           # SAM template for local testing
├── README.md               # Tool documentation
├── tests/                  # Unit tests
│   ├── __init__.py
│   └── test_{tool_name}.py
└── .env.{tool-name}        # Environment variables (if needed)
```

### TypeScript Tools
```
lambda/tools/{tool-name}/
├── src/
│   └── index.ts            # Main Lambda handler
├── package.json            # Node dependencies
├── tsconfig.json           # TypeScript configuration
├── template.yaml           # SAM template for local testing
├── README.md               # Tool documentation
├── tests/                  # Unit tests
│   └── index.test.ts
└── .env.{tool-name}        # Environment variables (if needed)
```

### Go Tools
```
lambda/tools/{tool-name}/
├── main.go                 # Main Lambda handler
├── go.mod                  # Go module definition
├── go.sum                  # Go dependencies lock file
├── Makefile               # Build instructions
├── template.yaml          # SAM template for local testing
├── README.md              # Tool documentation
├── tests/                 # Unit tests
│   └── main_test.go
└── .env.{tool-name}       # Environment variables (if needed)
```

## Naming Conventions

### Directory Names
- Use **kebab-case** (lowercase with hyphens)
- Be descriptive but concise
- Match the tool name in the registry
- Examples: `google-maps`, `db-interface`, `web-research`

### File Names
- **Python**: `index.py` for main handler
- **TypeScript**: `src/index.ts` for main handler
- **Go**: `main.go` for main handler
- **Tests**: `test_{tool_name}.py` or `index.test.ts` or `main_test.go`

## Required Files

### 1. Main Handler
Must export a handler function that matches Lambda signature:
- Python: `def lambda_handler(event, context):`
- TypeScript: `export const handler = async (event, context) => {}`
- Go: `func HandleRequest(ctx context.Context, event Event) (Response, error)`

### 2. Dependencies File
- Python: `requirements.txt` with pinned versions
- TypeScript: `package.json` with exact versions
- Go: `go.mod` with specific versions

### 3. SAM Template (template.yaml)
Standard SAM template for local testing:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: SAM template for {tool-name} tool

Resources:
  {ToolName}Function:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: {tool-name}-tool
      CodeUri: .
      Handler: index.lambda_handler  # Adjust for language
      Runtime: python3.11           # Or nodejs18.x, provided.al2023
      Timeout: 30
      MemorySize: 256
      Environment:
        Variables:
          LOG_LEVEL: INFO
```

### 4. README.md
Must include:
- Tool description
- Input/output schemas
- Local testing instructions
- Environment variables needed
- Example usage

## Environment Variables

### Standard Variables
All tools should support:
- `LOG_LEVEL`: INFO, DEBUG, ERROR (default: INFO)
- `ENVIRONMENT`: prod, dev, staging (from CDK)

### Tool-Specific Variables
- Store in `.env.{tool-name}` file
- Load using appropriate library (python-dotenv, dotenv, etc.)
- Document in README.md

## Testing Standards

### Unit Tests
- Minimum 80% code coverage
- Test all handler functions
- Mock external dependencies
- Test error cases

### Local Testing
- Use SAM CLI: `sam local invoke`
- Provide test event files in `tests/events/`
- Document testing procedures in README

## Migration Checklist

When standardizing an existing tool:

- [ ] Rename directory to kebab-case if needed
- [ ] Ensure main handler file follows naming convention
- [ ] Add SAM template.yaml if missing
- [ ] Create/update README.md
- [ ] Add unit tests if missing
- [ ] Pin dependency versions
- [ ] Add .env.{tool-name} if using secrets
- [ ] Test with SAM locally
- [ ] Update tool registration in CDK

## Current Tool Status

| Tool | Directory | Language | Standard Compliant | SAM Template | Notes |
|------|-----------|----------|-------------------|--------------|-------|
| Google Maps | `google-maps` | TypeScript | ✅ Yes | ❌ Missing | Add SAM template |
| DB Interface | `db-interface` | Python | ✅ Yes | ✅ Yes | Fully compliant |
| Execute Code | `execute_code` | Python | ❌ No | ✅ Yes | Rename to `execute-code` |
| YFinance | `yfinance` | Python | ✅ Yes | ✅ Yes | Fully compliant |
| Web Research | `web-research` | Go | ✅ Yes | ❌ Missing | Add SAM template |

## Future Guidelines

1. All new tools must follow this structure
2. Use cookiecutter templates for consistency
3. Review structure during code reviews
4. Update this document when adding new patterns