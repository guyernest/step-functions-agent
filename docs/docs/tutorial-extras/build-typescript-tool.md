---
sidebar_position: 1
---

# Building a tool in TypeScript

![TypeScript Logo](https://cdn.simpleicons.org/typescript?size=48)

## Tutorial: Building a New TypeScript Function Tool

### Step 1: Set up the tool structure

First, add your new tool to the `index.ts` file. Each tool follows this pattern:

```typescript
case "your_tool_name": {
    const { param1, param2 } = tool_input as { param1: string, param2: string }
    result = await handleYourTool(param1, param2);
    break;
}
```

### Step 2: Create the handler function

Create a handler function that implements your tool's logic:

```typescript
async function handleYourTool(param1: string, param2: string): Promise<string> {
    try {
        // Your tool implementation here
        const response = await makeApiCall(param1, param2);
        
        // Always return result as a string (usually JSON.stringify)
        return JSON.stringify(response);
    } catch (error) {
        logger.error('Error in handleYourTool', { error });
        throw error;
    }
}
```

### Step 3: Implement API calls

If your tool needs to make API calls, follow this pattern:

```typescript
async function makeApiCall(param1: string, param2: string) {
    const url = `https://api.example.com/endpoint?key=${API_KEY}&param1=${encodeURIComponent(param1)}`;
    
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`API call failed: ${response.statusText}`);
    }
    
    return await response.json();
}
```

### Step 4: Add type definitions

Create proper TypeScript interfaces for your input and output:

```typescript
interface ToolInput {
    param1: string;
    param2: string;
}

interface ToolOutput {
    result: string;
    timestamp: number;
}
```

### Step 5: Testing your tool

1. Create a test event in `tests/test-event.json`:

  ```json
  {
      "name": "your_tool_name",
      "id": "test-1",
      "input": {
          "param1": "test value 1",
          "param2": "test value 2"
      }
  }
  ```

1. Run the test using SAM CLI:

  ```bash
  sam local invoke YourLambda --event tests/test-event.json
  ```

### Best Practices

1. **Error Handling**: Always wrap your tool implementation in try-catch blocks
2. **Input Validation**: Validate all input parameters before processing
3. **Logging**: Use the logger for important operations and errors
4. **API Keys**: Store sensitive data in AWS Secrets Manager
5. **Types**: Use strict TypeScript types for better code reliability
6. **Documentation**: Add JSDoc comments to describe your functions

### Example Complete Tool

Here's a complete example of a simple tool that calculates distance between two points:

```typescript
// Type definitions
interface DistanceInput {
    point1: string;
    point2: string;
}

interface DistanceOutput {
    distance: number;
    unit: string;
}

// Handler function
async function handleDistance(point1: string, point2: string): Promise<string> {
    try {
        // Validate inputs
        if (!point1 || !point2) {
            throw new Error('Both points are required');
        }

        // Make API call
        const result = await calculateDistance(point1, point2);
        
        // Format output
        const output: DistanceOutput = {
            distance: result.distance,
            unit: 'kilometers'
        };

        return JSON.stringify(output);
    } catch (error) {
        logger.error('Error calculating distance', { error });
        throw error;
    }
}

// Add to main handler
case "calculate_distance": {
    const { point1, point2 } = tool_input as DistanceInput;
    result = await handleDistance(point1, point2);
    break;
}
```
