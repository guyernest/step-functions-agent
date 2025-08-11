# Provider Naming Alignment Issue

## Current State

There is a naming inconsistency between the Agent Registry and LLM Models table:

### Agent Registry (AgentRegistry-prod)
- Uses model family names in `llm_provider` field:
  - `claude` (for Anthropic models)
  - `gemini` (for Google models)  
  - `gpt` or `openai` (for OpenAI models)

### LLM Models Table (LLMModels-prod)
- Uses company/provider names in `provider` field:
  - `anthropic`
  - `google`
  - `openai`
  - `amazon`
  - `xai`
  - `deepseek`

## Current Workaround

A mapping is implemented in the UI (`AgentDetailsModal.tsx`) to translate between naming conventions:

```javascript
const PROVIDER_MAPPING = {
  'claude': 'anthropic',
  'gemini': 'google',
  'gpt': 'openai',
  // ...
}
```

## Recommended Long-term Solution

Update the agent creation and registration process to use consistent provider names:

1. **Update Agent Creation Scripts**
   - Modify agent creation to use company names (anthropic, google, openai)
   - Update any scripts in `scripts/` directory that create agents

2. **Migrate Existing Agents**
   - Create a migration script to update existing agents in AgentRegistry-prod
   - Map: `claude` → `anthropic`, `gemini` → `google`, `gpt` → `openai`

3. **Update Step Functions Templates**
   - Ensure Step Functions templates use consistent provider names
   - Check `step-functions/` directory templates

4. **Remove UI Mapping**
   - Once migration is complete, remove the `PROVIDER_MAPPING` from UI
   - Simplify the code to use provider names directly

## Benefits of Alignment

- **Consistency**: Single source of truth for provider names
- **Maintainability**: No need to maintain mappings in multiple places
- **Clarity**: Company names are clearer than model family names
- **Extensibility**: Easier to add new providers without confusion

## Migration Script Example

```python
import boto3

# Update existing agents
updates = {
    'claude': 'anthropic',
    'gemini': 'google',
    'gpt': 'openai'
}

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('AgentRegistry-prod')

# Scan and update
response = table.scan()
for item in response['Items']:
    if item.get('llm_provider') in updates:
        table.update_item(
            Key={'agent_name': item['agent_name'], 'version': item['version']},
            UpdateExpression='SET llm_provider = :provider',
            ExpressionAttributeValues={
                ':provider': updates[item['llm_provider']]
            }
        )
```