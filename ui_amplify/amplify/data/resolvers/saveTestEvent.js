export function request(ctx) {
  var resourceType = ctx.arguments.resource_type;
  var resourceId = ctx.arguments.resource_id;
  var testName = ctx.arguments.test_name;
  var description = ctx.arguments.description;
  var inputData = ctx.arguments.test_input;
  var expectedOutput = ctx.arguments.expected_output;
  var metadata = ctx.arguments.metadata;
  
  var id = resourceId + '#' + testName;
  var now = util.time.nowISO8601();
  
  // Build the DynamoDB item manually to ensure strings stay as strings
  var attributeValues = {
    resource_type: util.dynamodb.toDynamoDB(resourceType),
    id: util.dynamodb.toDynamoDB(id),
    resource_id: util.dynamodb.toDynamoDB(resourceId),
    test_name: util.dynamodb.toDynamoDB(testName),
    description: util.dynamodb.toDynamoDB(description || ''),
    // IMPORTANT: input must be stored as a string, not parsed into a Map
    input: util.dynamodb.toDynamoDB(inputData || '{}'),
    created_at: util.dynamodb.toDynamoDB(now),
    updated_at: util.dynamodb.toDynamoDB(now)
  };
  
  // Only add optional fields if they have values
  if (expectedOutput) {
    attributeValues.expected_output = util.dynamodb.toDynamoDB(expectedOutput);
  }
  
  if (metadata) {
    attributeValues.metadata = util.dynamodb.toDynamoDB(metadata);
  }
  
  return {
    operation: 'PutItem',
    key: {
      resource_type: util.dynamodb.toDynamoDB(resourceType),
      id: util.dynamodb.toDynamoDB(id)
    },
    attributeValues: attributeValues
  };
}

export function response(ctx) {
  if (ctx.error) {
    return null;
  }
  
  // DynamoDB PutItem doesn't return the item by default
  // We need to construct the response from the arguments we received
  var now = util.time.nowISO8601();
  var resourceId = ctx.arguments.resource_id;
  var testName = ctx.arguments.test_name;
  
  return {
    id: resourceId + '#' + testName,
    resource_type: ctx.arguments.resource_type,
    resource_id: resourceId,
    test_name: testName,
    description: ctx.arguments.description || '',
    // AWSJSON expects strings, not parsed objects
    test_input: ctx.arguments.test_input || '{}',
    expected_output: ctx.arguments.expected_output || null,
    metadata: ctx.arguments.metadata || null,
    created_at: now,
    updated_at: now
  };
}