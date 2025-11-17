---
name: appsync-js-resolver-development
description: Comprehensive guide for developing AWS AppSync JavaScript resolvers with DynamoDB data sources. Use when creating custom GraphQL resolvers that interact with DynamoDB tables, handling JSON parsing, type conversion, and client-side data transformation.
license: Complete terms in LICENSE.txt
---

# AWS AppSync JavaScript Resolver Development Guide

## Overview

AWS AppSync JavaScript resolvers enable GraphQL APIs to interact with data sources like DynamoDB. This guide provides battle-tested patterns for creating robust, production-ready resolvers based on real-world development experience. AppSync resolvers use the APPSYNC_JS runtime, which has specific JavaScript feature restrictions that differ from standard Node.js or browser environments.

---

## Key Concepts

### AppSync Resolver Architecture

**Request Function:**
- Transforms GraphQL arguments into data source operations
- Returns operation payload (e.g., DynamoDB GetItem, Scan, Query)
- No async operations - pure transformation logic

**Response Function:**
- Transforms data source response into GraphQL response
- Handles errors and data formatting
- Parses JSON strings from DynamoDB
- Returns data matching GraphQL schema types

**Data Flow:**
```
GraphQL Request → request() → DynamoDB Operation → DynamoDB → Raw Response → response() → GraphQL Response
```

### Critical Understanding: JSON Type Behavior

**The `a.json()` GraphQL Type:**
- GraphQL's JSON scalar type transports JSON as **strings** (this is standard behavior)
- AppSync resolvers should return parsed objects
- **Client is responsible for final JSON parsing** from the GraphQL response
- This separation of concerns is intentional and correct

**Example:**
```javascript
// DynamoDB stores: { "metadata": { "S": "{\"key\": \"value\"}" } }
// Resolver returns: { metadata: { key: "value" } }  // ✅ Parsed object
// GraphQL transports: "{ \"metadata\": \"{\\\"key\\\": \\\"value\\\"}\" }"  // String over wire
// Client receives: response.data.metadata (as string)
// Client parses: JSON.parse(response.data.metadata)  // Final object
```

---

## Process

### Phase 1: Understand Runtime Restrictions

Before writing any resolver code, understand APPSYNC_JS runtime limitations:

#### ✅ Supported Features
- `var` declarations (use exclusively)
- `typeof` operator
- `JSON.parse()` and `JSON.stringify()`
- Array methods: `.map()`, `.filter()`, `.reduce()`, `.find()`
- Object property access with bracket/dot notation
- String methods: `.replace()`, `.split()`, `.indexOf()`, etc.
- Conditional expressions: `if/else`, ternary operators
- Comparison operators: `===`, `!==`, `>`, `<`, etc.
- Logical operators: `&&`, `||`, `!`
- Arithmetic operators: `+`, `-`, `*`, `/`, `%`

#### ❌ Unsupported/Restricted Features
- **NO `const` or `let`** - Use `var` exclusively
- **NO destructuring** - `const { id } = ctx.args` ❌
- **NO async/await** - Resolvers are synchronous
- **NO `for` loops** - Use `.map()` or `.filter()` instead
- **NO `try-catch`** - Use conditional checks instead
- **NO nested function declarations** - Keep functions flat
- **NO arrow functions in some contexts** - Use `function()` syntax
- **NO template literals** - Use string concatenation
- **NO spread operators** - `...obj` ❌
- **NO `Object.keys()`, `Object.values()`, `Object.entries()`** - Use manual iteration

#### Import Restrictions
- Only AppSync utilities can be imported
- Standard modules: `@aws-appsync/utils`, `@aws-appsync/utils/dynamodb`
- NO external npm packages
- NO Node.js built-in modules

### Phase 2: Research and Planning

#### 2.1 Study Official Documentation

**Load these resources using WebFetch or Read tools:**

1. **AppSync JavaScript Runtime Documentation:**
   - WebFetch: `https://docs.aws.amazon.com/appsync/latest/devguide/resolver-reference-overview-js.html`
   - Covers supported features and restrictions

2. **DynamoDB Resolver Utilities:**
   - WebFetch: `https://docs.aws.amazon.com/appsync/latest/devguide/dynamodb-helpers-in-util-dynamodb-js.html`
   - Helper functions for DynamoDB operations

3. **Testing with EvaluateCode:**
   - WebFetch: `https://docs.aws.amazon.com/appsync/latest/devguide/test-debug-resolvers-js.html`
   - CLI command for validating resolver syntax

#### 2.2 Examine Existing Working Resolvers

**Before creating new resolvers, find and study existing working resolvers in your codebase:**

```bash
# Find existing resolver files
find . -name "*.js" -path "*/amplify/data/*" -type f

# Read working examples to understand patterns
# Look for: variable declarations, JSON parsing, array operations, error handling
```

**Common patterns to identify:**
- How are DynamoDB responses handled?
- How is JSON parsing done?
- How are arrays processed?
- How are errors handled?
- What variable naming conventions are used?

#### 2.3 Understand Your Data Model

**Examine DynamoDB table structure:**
```bash
# Get sample item from DynamoDB
aws dynamodb get-item \
  --table-name YourTable \
  --key '{"id":{"S":"sample-id"}}' \
  --profile YOUR_PROFILE

# Scan a few items to understand data patterns
aws dynamodb scan \
  --table-name YourTable \
  --max-items 3 \
  --profile YOUR_PROFILE
```

**Key questions:**
- Which fields are stored as JSON strings? (e.g., `{"S": "{\"key\":\"value\"}"}`)
- Which fields are simple types? (e.g., `{"S": "simple-string"}`)
- What is the table's partition key and sort key?
- Are there any GSIs (Global Secondary Indexes)?
- What are the expected query patterns?

#### 2.4 Plan Resolver Strategy

**For each resolver, determine:**

1. **Operation Type:**
   - GetItem (fetch single item by key)
   - Query (fetch items by partition key, optionally sort key)
   - Scan (full table scan with optional filters)
   - PutItem, UpdateItem, DeleteItem (mutations)

2. **Input Requirements:**
   - What GraphQL arguments are needed?
   - Are arguments optional or required?
   - What validation is needed?

3. **Response Transformation:**
   - Which fields need JSON parsing?
   - Should arrays be filtered?
   - What default values are needed?
   - How should errors be handled?

4. **GraphQL Schema Alignment:**
   - What is the expected return type?
   - Are fields nullable or required?
   - Are there nested custom types?

---

### Phase 3: Implementation Patterns

#### 3.1 Request Function Patterns

**GetItem Pattern:**
```javascript
export function request(ctx) {
  var item_id = ctx.args.item_id;
  var version = ctx.args.version || '1.0.0';  // Default value

  return {
    operation: 'GetItem',
    key: {
      item_id: { S: item_id },
      version: { S: version }
    }
  };
}
```

**Scan with Filter Pattern:**
```javascript
export function request(ctx) {
  var search_term = ctx.args.search_term;

  return {
    operation: 'Scan',
    filter: {
      expression: 'contains(#field_name, :search_value)',
      expressionNames: {
        '#field_name': 'field_name'
      },
      expressionValues: {
        ':search_value': { S: search_term }
      }
    }
  };
}
```

**Query Pattern:**
```javascript
export function request(ctx) {
  var partition_key = ctx.args.partition_key;
  var sort_key_prefix = ctx.args.sort_key_prefix;

  return {
    operation: 'Query',
    query: {
      expression: '#pk = :pk AND begins_with(#sk, :sk)',
      expressionNames: {
        '#pk': 'partition_key',
        '#sk': 'sort_key'
      },
      expressionValues: {
        ':pk': { S: partition_key },
        ':sk': { S: sort_key_prefix }
      }
    }
  };
}
```

#### 3.2 Response Function Patterns

**Single Item Response (GetItem):**
```javascript
export function response(ctx) {
  // Check if item exists
  if (!ctx.result || !ctx.result.item_id) {
    return null;
  }

  var item = ctx.result;

  // Parse JSON fields - AppSync auto-unwraps DynamoDB types ({S: "value"} becomes "value")
  var metadata = {};
  if (item.metadata) {
    if (typeof item.metadata === 'string') {
      metadata = JSON.parse(item.metadata);
    } else {
      metadata = item.metadata;
    }
  }

  var config = {};
  if (item.config) {
    if (typeof item.config === 'string') {
      config = JSON.parse(item.config);
    } else {
      config = item.config;
    }
  }

  // Return object matching GraphQL schema
  return {
    item_id: item.item_id || '',
    version: item.version || '',
    name: item.name || '',
    status: item.status || 'active',
    metadata: metadata,
    config: config,
    created_at: item.created_at || '',
    updated_at: item.updated_at || ''
  };
}
```

**Array Response (Scan/Query):**
```javascript
export function response(ctx) {
  // Check if results exist
  if (!ctx.result || !ctx.result.items) {
    return [];
  }

  return ctx.result.items
    .filter(function(item) {
      // Filter out items without required fields
      return item.item_id;
    })
    .map(function(item) {
      // Parse JSON fields for each item
      var metadata = {};
      if (item.metadata) {
        if (typeof item.metadata === 'string') {
          metadata = JSON.parse(item.metadata);
        } else {
          metadata = item.metadata;
        }
      }

      var tags = [];
      if (item.tags) {
        if (typeof item.tags === 'string') {
          tags = JSON.parse(item.tags);
        } else {
          tags = item.tags;
        }
      }

      return {
        item_id: item.item_id || '',
        name: item.name || '',
        status: item.status || 'active',
        metadata: metadata,
        tags: tags,
        created_at: item.created_at || ''
      };
    })
    .filter(function(item) {
      // Apply business logic filters (e.g., only active items)
      return item.status === 'active';
    });
}
```

#### 3.3 Advanced Patterns

**Complex Filtering with Multiple Conditions:**
```javascript
export function request(ctx) {
  var filters = [];
  var expressionNames = {};
  var expressionValues = {};

  // Build dynamic filter expression
  if (ctx.args.status) {
    filters.push('#status = :status');
    expressionNames['#status'] = 'status';
    expressionValues[':status'] = { S: ctx.args.status };
  }

  if (ctx.args.category) {
    filters.push('contains(#category, :category)');
    expressionNames['#category'] = 'category';
    expressionValues[':category'] = { S: ctx.args.category };
  }

  var filterExpression = filters.length > 0 ? filters.join(' AND ') : '';

  return {
    operation: 'Scan',
    filter: filterExpression ? {
      expression: filterExpression,
      expressionNames: expressionNames,
      expressionValues: expressionValues
    } : undefined
  };
}
```

**Conditional Field Parsing:**
```javascript
export function response(ctx) {
  if (!ctx.result || !ctx.result.item_id) {
    return null;
  }

  var item = ctx.result;
  var parsed_data = {};

  // List of fields that might be JSON strings
  var json_fields = ['metadata', 'config', 'settings', 'attributes'];

  var i = 0;
  for (i = 0; i < json_fields.length; i++) {
    var field = json_fields[i];
    if (item[field]) {
      if (typeof item[field] === 'string') {
        parsed_data[field] = JSON.parse(item[field]);
      } else {
        parsed_data[field] = item[field];
      }
    } else {
      parsed_data[field] = {};
    }
  }

  return {
    item_id: item.item_id,
    version: item.version,
    metadata: parsed_data.metadata,
    config: parsed_data.config,
    settings: parsed_data.settings,
    attributes: parsed_data.attributes
  };
}
```

---

### Phase 4: Testing and Validation

#### 4.1 Syntax Validation with EvaluateCode

**ALWAYS validate resolver syntax before deployment using AWS CLI:**

```bash
# Test request function
aws appsync evaluate-code \
  --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 \
  --code file://path/to/resolver.js \
  --function request \
  --context '{"arguments":{"item_id":"test","version":"1.0.0"}}'

# Test response function with DynamoDB-style response
aws appsync evaluate-code \
  --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 \
  --code file://path/to/resolver.js \
  --function response \
  --context '{"result":{"item_id":"test","version":"1.0.0","metadata":"{\"key\":\"value\"}","config":"{}"}}'
```

**Success Response:**
```json
{
  "evaluationResult": "{\"operation\":\"GetItem\",\"key\":{\"item_id\":{\"S\":\"test\"},\"version\":{\"S\":\"1.0.0\"}}}",
  "logs": [],
  "stash": "{}",
  "outErrors": "[]"
}
```

**Error Response:**
```json
{
  "error": {
    "message": "Error: Unable to find valid export for request",
    "codeErrors": [
      {
        "errorType": "MISSING_MAPPING_EXPORT",
        "value": "Unable to find valid export for request",
        "location": {"line": 0, "column": 0, "span": 0}
      }
    ]
  }
}
```

#### 4.2 Common Validation Errors

**"MISSING_MAPPING_EXPORT" Error:**
- **Cause:** Missing `export function request()` or `export function response()`
- **Fix:** Ensure both functions are exported correctly

**"SYNTAX_ERROR" Error:**
- **Cause:** Using unsupported JavaScript features (const, let, destructuring, etc.)
- **Fix:** Convert to supported syntax (var, no destructuring)

**"UNDEFINED_VARIABLE" Error:**
- **Cause:** Variable used before declaration
- **Fix:** Declare all variables with `var` at the top of function

**No errors but wrong result:**
- **Cause:** Logic error or incorrect DynamoDB operation format
- **Fix:** Check DynamoDB operation structure matches expected format

#### 4.3 Integration Testing with DynamoDB

**After syntax validation passes, test with actual DynamoDB:**

```bash
# 1. Deploy resolver to AppSync
# (via Amplify, CDK, or CloudFormation)

# 2. Test GraphQL query from console or API
# Query example:
{
  getItem(item_id: "test-id", version: "1.0.0") {
    item_id
    version
    name
    metadata
    config
  }
}

# 3. Check CloudWatch Logs for resolver execution
aws logs tail /aws/appsync/apis/YOUR_API_ID --follow
```

#### 4.4 Common Runtime Issues

**Issue: JSON fields showing as escaped strings in UI**
- **Symptom:** `"{\\"key\\":\\"value\\"}"`  instead of `{"key": "value"}`
- **Root Cause:** Client not parsing GraphQL JSON scalar type
- **Fix:** Add client-side parsing (see Phase 5)

**Issue: `ctx.result` is undefined**
- **Symptom:** Response function returns null
- **Root Cause:** DynamoDB operation failed or returned no data
- **Fix:** Add error checking: `if (!ctx.result) return null;`

**Issue: JSON.parse fails in resolver**
- **Symptom:** Resolver throws error
- **Root Cause:** Field is not a JSON string or is already parsed
- **Fix:** Use `typeof` check before parsing:
```javascript
if (typeof item.field === 'string') {
  parsed = JSON.parse(item.field);
}
```

---

### Phase 5: Client-Side Integration

#### 5.1 Understanding the Client Responsibility

**AppSync resolver returns parsed objects, but GraphQL JSON scalar transports them as strings.**

**Resolver output:**
```javascript
{
  item_id: "abc",
  metadata: { key: "value" },  // ✅ Object
  config: { setting: true }    // ✅ Object
}
```

**GraphQL response (over wire):**
```json
{
  "data": {
    "getItem": {
      "item_id": "abc",
      "metadata": "{\"key\":\"value\"}",  // ❗ String
      "config": "{\"setting\":true}"      // ❗ String
    }
  }
}
```

#### 5.2 Client-Side Parsing Pattern

**React/TypeScript Example:**

```typescript
// Helper function to parse template data from GraphQL response
const parseItemData = (itemResponse: any) => {
  if (!itemResponse) return null;

  return {
    ...itemResponse,
    metadata: typeof itemResponse.metadata === 'string'
      ? JSON.parse(itemResponse.metadata)
      : itemResponse.metadata || {},
    config: typeof itemResponse.config === 'string'
      ? JSON.parse(itemResponse.config)
      : itemResponse.config || {},
    tags: typeof itemResponse.tags === 'string'
      ? JSON.parse(itemResponse.tags)
      : itemResponse.tags || []
  };
};

// Usage in component
const fetchData = async () => {
  const response = await client.queries.getItem({
    item_id: 'test-id',
    version: '1.0.0'
  });

  if (response.data) {
    // Parse JSON fields before setting state
    setItemData(parseItemData(response.data));
  }
};

// Display in UI
<pre>{JSON.stringify(itemData.metadata, null, 2)}</pre>
```

**Key Points:**
- Always parse JSON fields after receiving GraphQL response
- Use `typeof` checks to handle both string and object cases
- Provide default values (`{}` or `[]`) for missing fields
- Parse consistently across all queries/mutations that return the same type

#### 5.3 TypeScript Type Safety

**Define types that match your GraphQL schema:**

```typescript
interface Item {
  item_id: string;
  version: string;
  name: string;
  status: string;
  metadata: Record<string, any>;  // Parsed object
  config: {
    enabled: boolean;
    settings: Record<string, any>;
  };
  tags: string[];
  created_at: string;
  updated_at: string;
}

// GraphQL response type (before parsing)
interface ItemGraphQLResponse {
  item_id: string;
  version: string;
  name: string;
  status: string;
  metadata: string;  // JSON string from GraphQL
  config: string;    // JSON string from GraphQL
  tags: string;      // JSON string from GraphQL
  created_at: string;
  updated_at: string;
}

// Parser with type safety
const parseItemData = (response: ItemGraphQLResponse): Item => {
  return {
    ...response,
    metadata: JSON.parse(response.metadata || '{}'),
    config: JSON.parse(response.config || '{}'),
    tags: JSON.parse(response.tags || '[]')
  };
};
```

---

## Quality Checklist

### ✅ Resolver Code Quality

**Variable Declarations:**
- [ ] All variables declared with `var` (no `const`, no `let`)
- [ ] No destructuring syntax used
- [ ] Variables declared before use

**JavaScript Features:**
- [ ] No `for` loops (use `.map()`, `.filter()` instead)
- [ ] No `try-catch` blocks (use conditional checks)
- [ ] No nested function declarations
- [ ] No template literals (use string concatenation)
- [ ] No spread operators (`...`)

**DynamoDB Operations:**
- [ ] Correct operation type (`GetItem`, `Scan`, `Query`, etc.)
- [ ] Proper key structure with type descriptors (`{S: "value"}`)
- [ ] Filter expressions use `expressionNames` and `expressionValues`
- [ ] Reserved words escaped with `#` prefix in expression names

**JSON Parsing:**
- [ ] All JSON fields checked with `typeof` before parsing
- [ ] Fallback to empty object/array for missing fields
- [ ] No assumptions about data types without checking

**Error Handling:**
- [ ] `ctx.result` existence checked before accessing properties
- [ ] Empty arrays/objects returned for missing data (not null unless appropriate)
- [ ] Null returned for single-item queries when item not found

**Return Values:**
- [ ] Return values match GraphQL schema types exactly
- [ ] All required fields included in return object
- [ ] Optional fields have default values or null handling

### ✅ Testing Validation

**Syntax Validation:**
- [ ] Request function validated with `aws appsync evaluate-code`
- [ ] Response function validated with `aws appsync evaluate-code`
- [ ] Both functions pass without errors

**Context Testing:**
- [ ] Tested with realistic argument values
- [ ] Tested with missing optional arguments
- [ ] Tested with DynamoDB response containing JSON strings
- [ ] Tested with empty DynamoDB responses

**Integration Testing:**
- [ ] Tested GraphQL query in AppSync console
- [ ] Verified actual DynamoDB data returned correctly
- [ ] Checked CloudWatch Logs for errors
- [ ] Tested error cases (missing items, invalid IDs)

### ✅ Client Integration

**Parsing Implementation:**
- [ ] Client-side parsing function created
- [ ] All GraphQL queries/mutations use parsing function
- [ ] TypeScript types defined (if applicable)
- [ ] UI displays parsed objects correctly (no escaped strings)

**Error Handling:**
- [ ] Client handles null responses gracefully
- [ ] Client handles GraphQL errors
- [ ] Loading and error states implemented in UI

---

## Common Pitfalls and Solutions

### Pitfall 1: Using Unsupported JavaScript Features

**Problem:**
```javascript
// ❌ This will fail deployment
export function request(ctx) {
  const { item_id, version = '1.0.0' } = ctx.args;  // Destructuring + const

  return {
    operation: 'GetItem',
    key: { item_id: { S: item_id } }
  };
}
```

**Solution:**
```javascript
// ✅ Use var and explicit property access
export function request(ctx) {
  var item_id = ctx.args.item_id;
  var version = ctx.args.version || '1.0.0';

  return {
    operation: 'GetItem',
    key: {
      item_id: { S: item_id },
      version: { S: version }
    }
  };
}
```

### Pitfall 2: Forgetting Type Checks Before JSON.parse

**Problem:**
```javascript
// ❌ This will fail if field is already an object
export function response(ctx) {
  return {
    metadata: JSON.parse(ctx.result.metadata)  // Error if not a string!
  };
}
```

**Solution:**
```javascript
// ✅ Always check type before parsing
export function response(ctx) {
  var metadata = {};
  if (ctx.result.metadata) {
    if (typeof ctx.result.metadata === 'string') {
      metadata = JSON.parse(ctx.result.metadata);
    } else {
      metadata = ctx.result.metadata;
    }
  }

  return { metadata: metadata };
}
```

### Pitfall 3: Using For Loops

**Problem:**
```javascript
// ❌ For loops not supported
export function response(ctx) {
  var results = [];
  for (var i = 0; i < ctx.result.items.length; i++) {
    results.push(ctx.result.items[i]);
  }
  return results;
}
```

**Solution:**
```javascript
// ✅ Use .map() or .filter()
export function response(ctx) {
  return ctx.result.items.map(function(item) {
    return {
      item_id: item.item_id,
      name: item.name
    };
  });
}
```

### Pitfall 4: Assuming AppSync Parses JSON Automatically

**Problem:**
```javascript
// ❌ Thinking resolver doesn't need to parse
export function response(ctx) {
  // Assuming AppSync will parse JSON fields automatically
  return ctx.result;  // Metadata will be a string!
}
```

**Client sees:**
```json
{
  "metadata": "{\"key\":\"value\"}"  // String, not object
}
```

**Solution:**
```javascript
// ✅ Parse in resolver, let GraphQL transport as string
export function response(ctx) {
  var metadata = {};
  if (ctx.result.metadata && typeof ctx.result.metadata === 'string') {
    metadata = JSON.parse(ctx.result.metadata);
  }

  return {
    item_id: ctx.result.item_id,
    metadata: metadata  // Object in resolver
  };
}
```

**Then parse on client:**
```typescript
// Client-side
const data = parseItemData(response.data);  // Parse JSON scalar types
```

### Pitfall 5: Not Testing with EvaluateCode Before Deployment

**Problem:**
- Write resolver code
- Deploy to AppSync
- Wait for CloudFormation deployment (5-10 minutes)
- Discover syntax error
- Fix and redeploy (another 5-10 minutes)
- Repeat...

**Solution:**
```bash
# ✅ Test locally FIRST with evaluate-code
aws appsync evaluate-code \
  --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 \
  --code file://resolver.js \
  --function request \
  --context '{"arguments":{"item_id":"test"}}'

# Fix any errors immediately
# Deploy only after validation passes
```

**Time saved:** Hours of deployment cycles

---

## Reference Examples

### Example 1: Simple GetItem Resolver

**File: `getItem.js`**
```javascript
export function request(ctx) {
  var item_id = ctx.args.item_id;
  var version = ctx.args.version || '1.0.0';

  return {
    operation: 'GetItem',
    key: {
      item_id: { S: item_id },
      version: { S: version }
    }
  };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.item_id) {
    return null;
  }

  var item = ctx.result;

  var metadata = {};
  if (item.metadata) {
    if (typeof item.metadata === 'string') {
      metadata = JSON.parse(item.metadata);
    } else {
      metadata = item.metadata;
    }
  }

  return {
    item_id: item.item_id || '',
    version: item.version || '',
    name: item.name || '',
    status: item.status || 'active',
    metadata: metadata,
    created_at: item.created_at || '',
    updated_at: item.updated_at || ''
  };
}
```

### Example 2: Scan with Filtering

**File: `listActiveItems.js`**
```javascript
export function request(ctx) {
  return {
    operation: 'Scan',
    filter: {
      expression: '#status = :status',
      expressionNames: {
        '#status': 'status'
      },
      expressionValues: {
        ':status': { S: 'active' }
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
      return item.item_id;
    })
    .map(function(item) {
      var metadata = {};
      if (item.metadata) {
        if (typeof item.metadata === 'string') {
          metadata = JSON.parse(item.metadata);
        } else {
          metadata = item.metadata;
        }
      }

      return {
        item_id: item.item_id || '',
        name: item.name || '',
        status: item.status || 'active',
        metadata: metadata,
        created_at: item.created_at || ''
      };
    })
    .filter(function(item) {
      return item.status === 'active';
    });
}
```

### Example 3: Complex Search with Multiple Filters

**File: `searchItems.js`**
```javascript
export function request(ctx) {
  var search_term = ctx.args.search_term;
  var category = ctx.args.category;
  var status = ctx.args.status;

  var filters = [];
  var expressionNames = {};
  var expressionValues = {};

  if (search_term) {
    filters.push('contains(#name, :search_term)');
    expressionNames['#name'] = 'name';
    expressionValues[':search_term'] = { S: search_term };
  }

  if (category) {
    filters.push('contains(#metadata, :category)');
    expressionNames['#metadata'] = 'metadata';
    expressionValues[':category'] = { S: category };
  }

  if (status) {
    filters.push('#status = :status');
    expressionNames['#status'] = 'status';
    expressionValues[':status'] = { S: status };
  }

  var filterExpression = filters.join(' AND ');

  if (filterExpression) {
    return {
      operation: 'Scan',
      filter: {
        expression: filterExpression,
        expressionNames: expressionNames,
        expressionValues: expressionValues
      }
    };
  }

  return {
    operation: 'Scan'
  };
}

export function response(ctx) {
  if (!ctx.result || !ctx.result.items) {
    return [];
  }

  return ctx.result.items.map(function(item) {
    var metadata = {};
    if (item.metadata) {
      if (typeof item.metadata === 'string') {
        metadata = JSON.parse(item.metadata);
      } else {
        metadata = item.metadata;
      }
    }

    var tags = [];
    if (item.tags) {
      if (typeof item.tags === 'string') {
        tags = JSON.parse(item.tags);
      } else {
        tags = item.tags;
      }
    }

    return {
      item_id: item.item_id || '',
      name: item.name || '',
      category: item.category || '',
      status: item.status || 'active',
      metadata: metadata,
      tags: tags,
      created_at: item.created_at || ''
    };
  });
}
```

---

## Workflow Summary

1. **Research Phase:**
   - Study AppSync JavaScript runtime restrictions
   - Load official documentation
   - Examine existing working resolvers
   - Understand DynamoDB data model

2. **Planning Phase:**
   - Determine operation type (GetItem, Scan, Query)
   - Plan input arguments and validation
   - Identify JSON fields requiring parsing
   - Design response transformation

3. **Implementation Phase:**
   - Write request function (GraphQL → DynamoDB)
   - Write response function (DynamoDB → GraphQL)
   - Use only supported JavaScript features
   - Parse JSON fields with type checking

4. **Testing Phase:**
   - Validate syntax with `aws appsync evaluate-code`
   - Test request function with sample arguments
   - Test response function with sample DynamoDB data
   - Fix errors before deployment

5. **Deployment Phase:**
   - Deploy resolver via Amplify/CDK/CloudFormation
   - Test GraphQL queries in console
   - Check CloudWatch Logs for runtime errors
   - Verify data returned correctly

6. **Client Integration Phase:**
   - Create client-side parsing function
   - Parse JSON scalar types from GraphQL response
   - Implement UI to display parsed data
   - Test end-to-end workflow

---

## Quick Reference

### Variable Declaration
```javascript
// ❌ Don't use
const x = 1;
let y = 2;
const { id } = obj;

// ✅ Use
var x = 1;
var y = 2;
var id = obj.id;
```

### Loops and Iteration
```javascript
// ❌ Don't use
for (let i = 0; i < arr.length; i++) { }
for (const item of arr) { }

// ✅ Use
arr.map(function(item) { })
arr.filter(function(item) { })
```

### JSON Parsing
```javascript
// ❌ Don't assume
var data = JSON.parse(field);  // Fails if not string

// ✅ Check type first
var data = {};
if (field) {
  if (typeof field === 'string') {
    data = JSON.parse(field);
  } else {
    data = field;
  }
}
```

### Error Handling
```javascript
// ❌ Don't use try-catch
try {
  var data = JSON.parse(field);
} catch (e) {
  var data = {};
}

// ✅ Use conditionals
var data = {};
if (field && typeof field === 'string') {
  data = JSON.parse(field);
}
```

### Testing Command
```bash
aws appsync evaluate-code \
  --runtime name=APPSYNC_JS,runtimeVersion=1.0.0 \
  --code file://resolver.js \
  --function request \
  --context '{"arguments":{"id":"test"}}'
```

---

## Additional Resources

### Official Documentation
- AppSync JavaScript Resolvers: https://docs.aws.amazon.com/appsync/latest/devguide/resolver-reference-overview-js.html
- DynamoDB Helpers: https://docs.aws.amazon.com/appsync/latest/devguide/dynamodb-helpers-in-util-dynamodb-js.html
- Testing Resolvers: https://docs.aws.amazon.com/appsync/latest/devguide/test-debug-resolvers-js.html

### Key Learnings from Real Development
1. GraphQL JSON scalar types transport JSON as strings (by design)
2. Resolvers should parse JSON, clients should parse GraphQL JSON scalars
3. Always test with `evaluate-code` before deployment
4. Study working resolvers in your codebase first
5. Use `typeof` checks before JSON.parse every time
6. AppSync auto-unwraps DynamoDB type descriptors in response function

---

**Last Updated:** 2025-10-21
**Based on:** Real-world AWS AppSync JavaScript resolver development experience with DynamoDB data sources
