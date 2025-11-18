# AppSync JavaScript Resolver Best Practices

This guide documents the constraints and best practices for writing AWS AppSync JavaScript resolvers using the APPSYNC_JS runtime.

## Critical Constraints

### 1. NO REGEX LITERALS
**Problem**: AppSync JS runtime does not support regex literals (`/pattern/flags`)

**DON'T**:
```javascript
// ❌ WRONG - Will cause deployment failure
var extraction_name = agent_name.replace(/-/g, '_');
var cleaned = text.replace(/[^a-z]/gi, '');
```

**DO**:
```javascript
// ✅ CORRECT - Use split/join for simple replacements
var extraction_name = agent_name.split('-').join('_');

// ✅ CORRECT - Use util.str methods when available
// See: https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html#utility-helpers-in-util-str
```

### 2. NO FOR LOOPS
**Problem**: AppSync JS runtime is ES6-based but doesn't support all loop constructs

**DON'T**:
```javascript
// ❌ WRONG - for loops may not work
for (var i = 0; i < items.length; i++) {
  processItem(items[i]);
}
```

**DO**:
```javascript
// ✅ CORRECT - Use map/filter/forEach
items.map(function(item) {
  return processItem(item);
});

items.filter(function(item) {
  return item.status === 'active';
});
```

### 3. TIME/DATE HANDLING
**Problem**: Standard JavaScript Date() constructor may not work as expected

**DON'T**:
```javascript
// ❌ WRONG - May not work in AppSync runtime
var now = new Date().toISOString();
var timestamp = Date.now();
```

**DO**:
```javascript
// ✅ CORRECT - Use util.time helpers
var now = util.time.nowISO8601();
var epochMillis = util.time.nowEpochMilliSeconds();

// See: https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html#time-helpers-in-util-time
```

### 4. JSON PARSING SAFETY
**Problem**: Always validate before parsing JSON to avoid runtime errors

**DON'T**:
```javascript
// ❌ WRONG - No validation, may fail
var template = JSON.parse(item.template);
```

**DO**:
```javascript
// ✅ CORRECT - Validate type and format first
var template = {};
if (item.template) {
  if (typeof item.template === 'string' && item.template.charAt(0) === '{') {
    template = JSON.parse(item.template);
  } else if (typeof item.template === 'object') {
    template = item.template;
  }
}
```

## Testing Resolvers Locally

Always test resolvers before deploying using the AWS CLI:

### 1. Create Test Context File

```json
// test-context.json
{
  "arguments": {
    "template_id": "test-123",
    "version": "1.0.0"
  },
  "result": {
    "template_id": "test-123",
    "template": "{\"name\":\"test\"}",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 2. Test Request Function

```bash
aws appsync evaluate-code \
  --code file://yourResolver.js \
  --function request \
  --context file://test-context.json \
  --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 \
  --profile YOUR_PROFILE
```

### 3. Test Response Function

```bash
aws appsync evaluate-code \
  --code file://yourResolver.js \
  --function response \
  --context file://test-context.json \
  --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 \
  --profile YOUR_PROFILE
```

### 4. Check for Errors

Successful test output:
```json
{
    "evaluationResult": "{...}",
    "logs": [],
    "stash": "{}",
    "outErrors": "[]"  // ← Should be empty!
}
```

Failed test output:
```json
{
    "error": {
        "message": "Error: code.js(5,44): error @aws-appsync/no-regex: Regex literals are not supported.",
        "codeErrors": [...]
    }
}
```

## Common Patterns

### String Replacement Without Regex

```javascript
// Replace hyphens with underscores
var normalized = agent_name.split('-').join('_');

// Remove specific characters (chain splits/joins)
var cleaned = text.split('-').join('').split('_').join('');
```

### Array Operations

```javascript
// Filter items
var activeItems = items.filter(function(item) {
  return item.status === 'active';
});

// Transform items
var processed = items.map(function(item) {
  return {
    id: item.id,
    name: item.name || 'Unknown'
  };
});

// Chain operations
var result = items
  .filter(function(item) { return item.id; })
  .map(function(item) { return transformItem(item); });
```

### Safe JSON Parsing

```javascript
// For objects
var config = null;
if (item.configuration) {
  if (typeof item.configuration === 'string' &&
      (item.configuration.charAt(0) === '{' || item.configuration.charAt(0) === '[')) {
    config = JSON.parse(item.configuration);
  } else {
    config = item.configuration;
  }
}

// For arrays
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
```

### Default Values

```javascript
// Provide sensible defaults for all fields
return {
  id: item.id,
  name: item.name || '',
  status: item.status || 'inactive',
  count: item.count || 0,
  metadata: metadata || {},
  created_at: item.created_at || '2024-01-01T00:00:00Z',
  updated_at: item.updated_at || '2024-01-01T00:00:00Z'
};
```

## DynamoDB Filter Expressions

### Using Expression Names and Values

```javascript
// CORRECT way to build DynamoDB filters
return {
  operation: 'Scan',
  filter: {
    expression: 'contains(#metadata, :agent_name) OR #extraction_name = :extraction_name_value',
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
```

**Key Points**:
- Use `#` prefix for attribute names (expressionNames)
- Use `:` prefix for values (expressionValues)
- Always specify DynamoDB types (`S` for String, `N` for Number, etc.)
- Avoid name collisions in placeholders

## Deployment Checklist

Before deploying new resolvers:

- [ ] Test request function locally with `aws appsync evaluate-code`
- [ ] Test response function locally with `aws appsync evaluate-code`
- [ ] Verify no regex literals (`/pattern/flags`)
- [ ] Verify no for loops (use map/filter instead)
- [ ] Verify JSON parsing has validation
- [ ] Verify all fields have default values
- [ ] Verify DynamoDB filter expressions use correct syntax
- [ ] Add descriptive comments explaining resolver purpose

## Useful Resources

- [AppSync JS Runtime Reference](https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html)
- [Built-in Utilities (util)](https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html#utility-helpers-in-util)
- [Time Helpers (util.time)](https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html#time-helpers-in-util-time)
- [DynamoDB Helpers (util.dynamodb)](https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html#dynamodb-helpers-in-util-dynamodb)
- [String Helpers (util.str)](https://docs.aws.amazon.com/appsync/latest/devguide/resolver-util-reference-js.html#string-helpers-in-util-str)

## Common Error Messages

### "Regex literals are not supported"
**Cause**: Used `/pattern/flags` syntax
**Fix**: Use `split().join()` or util.str methods

### "The code contains one or more errors"
**Cause**: Generic syntax or runtime error
**Fix**: Test locally with `aws appsync evaluate-code` to get specific error details

### "Resource handler returned message: The code contains one or more errors"
**Cause**: CloudFormation deployment failed due to resolver syntax errors
**Fix**: Test resolvers locally before deploying

## Example: Complete Working Resolver

```javascript
// AppSync resolver for listing items by name
export function request(ctx) {
  var item_name = ctx.args.item_name;
  // Convert hyphens to underscores (no regex!)
  var normalized_name = item_name.split('-').join('_');

  return {
    operation: 'Scan',
    filter: {
      expression: '#name = :name OR #normalized_name = :normalized_name',
      expressionNames: {
        '#name': 'name',
        '#normalized_name': 'normalized_name'
      },
      expressionValues: {
        ':name': { S: item_name },
        ':normalized_name': { S: normalized_name }
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
      return item.id && item.status === 'active';
    })
    .map(function(item) {
      // Safe JSON parsing
      var metadata = {};
      if (item.metadata) {
        if (typeof item.metadata === 'string' && item.metadata.charAt(0) === '{') {
          metadata = JSON.parse(item.metadata);
        } else if (typeof item.metadata === 'object') {
          metadata = item.metadata;
        }
      }

      return {
        id: item.id,
        name: item.name || '',
        status: item.status || 'inactive',
        metadata: metadata,
        created_at: item.created_at || '2024-01-01T00:00:00Z',
        updated_at: item.updated_at || '2024-01-01T00:00:00Z'
      };
    });
}
```

## Agent/AI Assistant Instructions

When writing AppSync resolvers:

1. **NEVER use regex literals** - Always use `split().join()` for simple string replacements
2. **NEVER use for loops** - Always use `.map()`, `.filter()`, or `.forEach()`
3. **ALWAYS test locally first** using `aws appsync evaluate-code` before deploying
4. **ALWAYS validate** JSON strings before parsing (check type and first character)
5. **ALWAYS provide defaults** for all returned fields
6. **ALWAYS use expressionNames and expressionValues** for DynamoDB filter expressions
7. **ALWAYS add comments** explaining the resolver's purpose

Follow these rules strictly to avoid deployment failures and runtime errors.
