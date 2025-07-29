"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.ts
var index_exports = {};
__export(index_exports, {
  BatchExecuteStatementCommand: () => BatchExecuteStatementCommand,
  BatchGetCommand: () => BatchGetCommand,
  BatchWriteCommand: () => BatchWriteCommand,
  DeleteCommand: () => DeleteCommand,
  DynamoDBDocument: () => DynamoDBDocument,
  DynamoDBDocumentClient: () => DynamoDBDocumentClient,
  DynamoDBDocumentClientCommand: () => DynamoDBDocumentClientCommand,
  ExecuteStatementCommand: () => ExecuteStatementCommand,
  ExecuteTransactionCommand: () => ExecuteTransactionCommand,
  GetCommand: () => GetCommand,
  NativeAttributeBinary: () => import_util_dynamodb.NativeAttributeBinary,
  NativeAttributeValue: () => import_util_dynamodb.NativeAttributeValue,
  NativeScalarAttributeValue: () => import_util_dynamodb.NativeScalarAttributeValue,
  NumberValue: () => import_util_dynamodb.NumberValueImpl,
  PaginationConfiguration: () => import_types.PaginationConfiguration,
  PutCommand: () => PutCommand,
  QueryCommand: () => QueryCommand,
  ScanCommand: () => ScanCommand,
  TransactGetCommand: () => TransactGetCommand,
  TransactWriteCommand: () => TransactWriteCommand,
  UpdateCommand: () => UpdateCommand,
  __Client: () => import_smithy_client.Client,
  marshallOptions: () => import_util_dynamodb.marshallOptions,
  paginateQuery: () => paginateQuery,
  paginateScan: () => paginateScan,
  unmarshallOptions: () => import_util_dynamodb.unmarshallOptions
});
module.exports = __toCommonJS(index_exports);

// src/commands/BatchExecuteStatementCommand.ts
var import_client_dynamodb = require("@aws-sdk/client-dynamodb");


// src/baseCommand/DynamoDBDocumentClientCommand.ts
var import_core = require("@aws-sdk/core");
var import_smithy_client = require("@smithy/smithy-client");

// src/commands/utils.ts
var import_util_dynamodb = require("@aws-sdk/util-dynamodb");
var SELF = null;
var ALL_VALUES = {};
var ALL_MEMBERS = [];
var NEXT_LEVEL = "*";
var processObj = /* @__PURE__ */ __name((obj, processFunc, keyNodes) => {
  if (obj !== void 0) {
    if (keyNodes == null) {
      return processFunc(obj);
    } else {
      const keys = Object.keys(keyNodes);
      const goToNextLevel = keys.length === 1 && keys[0] === NEXT_LEVEL;
      const someChildren = keys.length >= 1 && !goToNextLevel;
      const allChildren = keys.length === 0;
      if (someChildren) {
        return processKeysInObj(obj, processFunc, keyNodes);
      } else if (allChildren) {
        return processAllKeysInObj(obj, processFunc, SELF);
      } else if (goToNextLevel) {
        return Object.entries(obj ?? {}).reduce((acc, [k, v]) => {
          if (typeof v !== "function") {
            acc[k] = processObj(v, processFunc, keyNodes[NEXT_LEVEL]);
          }
          return acc;
        }, Array.isArray(obj) ? [] : {});
      }
    }
  }
  return void 0;
}, "processObj");
var processKeysInObj = /* @__PURE__ */ __name((obj, processFunc, keyNodes) => {
  let accumulator;
  if (Array.isArray(obj)) {
    accumulator = obj.filter((item) => typeof item !== "function");
  } else {
    accumulator = {};
    for (const [k, v] of Object.entries(obj)) {
      if (typeof v !== "function") {
        accumulator[k] = v;
      }
    }
  }
  for (const [nodeKey, nodes] of Object.entries(keyNodes)) {
    if (typeof obj[nodeKey] === "function") {
      continue;
    }
    const processedValue = processObj(obj[nodeKey], processFunc, nodes);
    if (processedValue !== void 0 && typeof processedValue !== "function") {
      accumulator[nodeKey] = processedValue;
    }
  }
  return accumulator;
}, "processKeysInObj");
var processAllKeysInObj = /* @__PURE__ */ __name((obj, processFunc, keyNodes) => {
  if (Array.isArray(obj)) {
    return obj.filter((item) => typeof item !== "function").map((item) => processObj(item, processFunc, keyNodes));
  }
  return Object.entries(obj).reduce((acc, [key, value]) => {
    if (typeof value === "function") {
      return acc;
    }
    const processedValue = processObj(value, processFunc, keyNodes);
    if (processedValue !== void 0 && typeof processedValue !== "function") {
      acc[key] = processedValue;
    }
    return acc;
  }, {});
}, "processAllKeysInObj");
var marshallInput = /* @__PURE__ */ __name((obj, keyNodes, options) => {
  const marshallFunc = /* @__PURE__ */ __name((toMarshall) => (0, import_util_dynamodb.marshall)(toMarshall, options), "marshallFunc");
  return processKeysInObj(obj, marshallFunc, keyNodes);
}, "marshallInput");
var unmarshallOutput = /* @__PURE__ */ __name((obj, keyNodes, options) => {
  const unmarshallFunc = /* @__PURE__ */ __name((toMarshall) => (0, import_util_dynamodb.unmarshall)(toMarshall, options), "unmarshallFunc");
  return processKeysInObj(obj, unmarshallFunc, keyNodes);
}, "unmarshallOutput");

// src/baseCommand/DynamoDBDocumentClientCommand.ts
var DynamoDBDocumentClientCommand = class extends import_smithy_client.Command {
  static {
    __name(this, "DynamoDBDocumentClientCommand");
  }
  addMarshallingMiddleware(configuration) {
    const { marshallOptions: marshallOptions3 = {}, unmarshallOptions: unmarshallOptions3 = {} } = configuration.translateConfig || {};
    marshallOptions3.convertTopLevelContainer = marshallOptions3.convertTopLevelContainer ?? true;
    unmarshallOptions3.convertWithoutMapWrapper = unmarshallOptions3.convertWithoutMapWrapper ?? true;
    this.clientCommand.middlewareStack.addRelativeTo(
      (next, context) => async (args) => {
        (0, import_core.setFeature)(context, "DDB_MAPPER", "d");
        return next({
          ...args,
          /**
           * We overwrite `args.input` at this middleware, but do not
           * mutate the args object itself, which is initially the Command instance.
           *
           * The reason for this is to prevent mutations to the Command instance's inputs
           * from being carried over if the Command instance is reused in a new
           * request.
           */
          input: marshallInput(args.input, this.inputKeyNodes, marshallOptions3)
        });
      },
      {
        name: "DocumentMarshall",
        relation: "before",
        toMiddleware: "serializerMiddleware",
        override: true
      }
    );
    this.clientCommand.middlewareStack.addRelativeTo(
      (next, context) => async (args) => {
        const deserialized = await next(args);
        deserialized.output = unmarshallOutput(deserialized.output, this.outputKeyNodes, unmarshallOptions3);
        return deserialized;
      },
      {
        name: "DocumentUnmarshall",
        relation: "before",
        toMiddleware: "deserializerMiddleware",
        override: true
      }
    );
  }
};

// src/commands/BatchExecuteStatementCommand.ts
var BatchExecuteStatementCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.BatchExecuteStatementCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "BatchExecuteStatementCommand");
  }
  inputKeyNodes = {
    Statements: {
      "*": {
        Parameters: ALL_MEMBERS
        // set/list of AttributeValue
      }
    }
  };
  outputKeyNodes = {
    Responses: {
      "*": {
        Error: {
          Item: ALL_VALUES
          // map with AttributeValue
        },
        Item: ALL_VALUES
        // map with AttributeValue
      }
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/BatchGetCommand.ts


var BatchGetCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.BatchGetItemCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "BatchGetCommand");
  }
  inputKeyNodes = {
    RequestItems: {
      "*": {
        Keys: {
          "*": ALL_VALUES
          // map with AttributeValue
        }
      }
    }
  };
  outputKeyNodes = {
    Responses: {
      "*": {
        "*": ALL_VALUES
        // map with AttributeValue
      }
    },
    UnprocessedKeys: {
      "*": {
        Keys: {
          "*": ALL_VALUES
          // map with AttributeValue
        }
      }
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/BatchWriteCommand.ts


var BatchWriteCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.BatchWriteItemCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "BatchWriteCommand");
  }
  inputKeyNodes = {
    RequestItems: {
      "*": {
        "*": {
          PutRequest: {
            Item: ALL_VALUES
            // map with AttributeValue
          },
          DeleteRequest: {
            Key: ALL_VALUES
            // map with AttributeValue
          }
        }
      }
    }
  };
  outputKeyNodes = {
    UnprocessedItems: {
      "*": {
        "*": {
          PutRequest: {
            Item: ALL_VALUES
            // map with AttributeValue
          },
          DeleteRequest: {
            Key: ALL_VALUES
            // map with AttributeValue
          }
        }
      }
    },
    ItemCollectionMetrics: {
      "*": {
        "*": {
          ItemCollectionKey: ALL_VALUES
          // map with AttributeValue
        }
      }
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/DeleteCommand.ts


var DeleteCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.DeleteItemCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "DeleteCommand");
  }
  inputKeyNodes = {
    Key: ALL_VALUES,
    // map with AttributeValue
    Expected: {
      "*": {
        Value: SELF,
        AttributeValueList: ALL_MEMBERS
        // set/list of AttributeValue
      }
    },
    ExpressionAttributeValues: ALL_VALUES
    // map with AttributeValue
  };
  outputKeyNodes = {
    Attributes: ALL_VALUES,
    // map with AttributeValue
    ItemCollectionMetrics: {
      ItemCollectionKey: ALL_VALUES
      // map with AttributeValue
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/ExecuteStatementCommand.ts


var ExecuteStatementCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.ExecuteStatementCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "ExecuteStatementCommand");
  }
  inputKeyNodes = {
    Parameters: ALL_MEMBERS
    // set/list of AttributeValue
  };
  outputKeyNodes = {
    Items: {
      "*": ALL_VALUES
      // map with AttributeValue
    },
    LastEvaluatedKey: ALL_VALUES
    // map with AttributeValue
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/ExecuteTransactionCommand.ts


var ExecuteTransactionCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.ExecuteTransactionCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "ExecuteTransactionCommand");
  }
  inputKeyNodes = {
    TransactStatements: {
      "*": {
        Parameters: ALL_MEMBERS
        // set/list of AttributeValue
      }
    }
  };
  outputKeyNodes = {
    Responses: {
      "*": {
        Item: ALL_VALUES
        // map with AttributeValue
      }
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/GetCommand.ts


var GetCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.GetItemCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "GetCommand");
  }
  inputKeyNodes = {
    Key: ALL_VALUES
    // map with AttributeValue
  };
  outputKeyNodes = {
    Item: ALL_VALUES
    // map with AttributeValue
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/PutCommand.ts


var PutCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.PutItemCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "PutCommand");
  }
  inputKeyNodes = {
    Item: ALL_VALUES,
    // map with AttributeValue
    Expected: {
      "*": {
        Value: SELF,
        AttributeValueList: ALL_MEMBERS
        // set/list of AttributeValue
      }
    },
    ExpressionAttributeValues: ALL_VALUES
    // map with AttributeValue
  };
  outputKeyNodes = {
    Attributes: ALL_VALUES,
    // map with AttributeValue
    ItemCollectionMetrics: {
      ItemCollectionKey: ALL_VALUES
      // map with AttributeValue
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/QueryCommand.ts


var QueryCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.QueryCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "QueryCommand");
  }
  inputKeyNodes = {
    KeyConditions: {
      "*": {
        AttributeValueList: ALL_MEMBERS
        // set/list of AttributeValue
      }
    },
    QueryFilter: {
      "*": {
        AttributeValueList: ALL_MEMBERS
        // set/list of AttributeValue
      }
    },
    ExclusiveStartKey: ALL_VALUES,
    // map with AttributeValue
    ExpressionAttributeValues: ALL_VALUES
    // map with AttributeValue
  };
  outputKeyNodes = {
    Items: {
      "*": ALL_VALUES
      // map with AttributeValue
    },
    LastEvaluatedKey: ALL_VALUES
    // map with AttributeValue
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/ScanCommand.ts


var ScanCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.ScanCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "ScanCommand");
  }
  inputKeyNodes = {
    ScanFilter: {
      "*": {
        AttributeValueList: ALL_MEMBERS
        // set/list of AttributeValue
      }
    },
    ExclusiveStartKey: ALL_VALUES,
    // map with AttributeValue
    ExpressionAttributeValues: ALL_VALUES
    // map with AttributeValue
  };
  outputKeyNodes = {
    Items: {
      "*": ALL_VALUES
      // map with AttributeValue
    },
    LastEvaluatedKey: ALL_VALUES
    // map with AttributeValue
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/TransactGetCommand.ts


var TransactGetCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.TransactGetItemsCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "TransactGetCommand");
  }
  inputKeyNodes = {
    TransactItems: {
      "*": {
        Get: {
          Key: ALL_VALUES
          // map with AttributeValue
        }
      }
    }
  };
  outputKeyNodes = {
    Responses: {
      "*": {
        Item: ALL_VALUES
        // map with AttributeValue
      }
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/TransactWriteCommand.ts


var TransactWriteCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.TransactWriteItemsCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "TransactWriteCommand");
  }
  inputKeyNodes = {
    TransactItems: {
      "*": {
        ConditionCheck: {
          Key: ALL_VALUES,
          // map with AttributeValue
          ExpressionAttributeValues: ALL_VALUES
          // map with AttributeValue
        },
        Put: {
          Item: ALL_VALUES,
          // map with AttributeValue
          ExpressionAttributeValues: ALL_VALUES
          // map with AttributeValue
        },
        Delete: {
          Key: ALL_VALUES,
          // map with AttributeValue
          ExpressionAttributeValues: ALL_VALUES
          // map with AttributeValue
        },
        Update: {
          Key: ALL_VALUES,
          // map with AttributeValue
          ExpressionAttributeValues: ALL_VALUES
          // map with AttributeValue
        }
      }
    }
  };
  outputKeyNodes = {
    ItemCollectionMetrics: {
      "*": {
        "*": {
          ItemCollectionKey: ALL_VALUES
          // map with AttributeValue
        }
      }
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/commands/UpdateCommand.ts


var UpdateCommand = class extends DynamoDBDocumentClientCommand {
  constructor(input) {
    super();
    this.input = input;
    this.clientCommand = new import_client_dynamodb.UpdateItemCommand(this.input);
    this.middlewareStack = this.clientCommand.middlewareStack;
  }
  static {
    __name(this, "UpdateCommand");
  }
  inputKeyNodes = {
    Key: ALL_VALUES,
    // map with AttributeValue
    AttributeUpdates: {
      "*": {
        Value: SELF
      }
    },
    Expected: {
      "*": {
        Value: SELF,
        AttributeValueList: ALL_MEMBERS
        // set/list of AttributeValue
      }
    },
    ExpressionAttributeValues: ALL_VALUES
    // map with AttributeValue
  };
  outputKeyNodes = {
    Attributes: ALL_VALUES,
    // map with AttributeValue
    ItemCollectionMetrics: {
      ItemCollectionKey: ALL_VALUES
      // map with AttributeValue
    }
  };
  clientCommand;
  middlewareStack;
  /**
   * @internal
   */
  resolveMiddleware(clientStack, configuration, options) {
    this.addMarshallingMiddleware(configuration);
    const stack = clientStack.concat(this.middlewareStack);
    const handler = this.clientCommand.resolveMiddleware(stack, configuration, options);
    return async () => handler(this.clientCommand);
  }
};

// src/DynamoDBDocumentClient.ts

var DynamoDBDocumentClient = class _DynamoDBDocumentClient extends import_smithy_client.Client {
  static {
    __name(this, "DynamoDBDocumentClient");
  }
  config;
  constructor(client, translateConfig) {
    super(client.config);
    this.config = client.config;
    this.config.translateConfig = translateConfig;
    this.middlewareStack = client.middlewareStack;
    if (this.config?.cacheMiddleware) {
      throw new Error(
        "@aws-sdk/lib-dynamodb - cacheMiddleware=true is not compatible with the DynamoDBDocumentClient. This option must be set to false."
      );
    }
  }
  static from(client, translateConfig) {
    return new _DynamoDBDocumentClient(client, translateConfig);
  }
  destroy() {
  }
};

// src/DynamoDBDocument.ts
var DynamoDBDocument = class _DynamoDBDocument extends DynamoDBDocumentClient {
  static {
    __name(this, "DynamoDBDocument");
  }
  static from(client, translateConfig) {
    return new _DynamoDBDocument(client, translateConfig);
  }
  batchExecuteStatement(args, optionsOrCb, cb) {
    const command = new BatchExecuteStatementCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  batchGet(args, optionsOrCb, cb) {
    const command = new BatchGetCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  batchWrite(args, optionsOrCb, cb) {
    const command = new BatchWriteCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  delete(args, optionsOrCb, cb) {
    const command = new DeleteCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  executeStatement(args, optionsOrCb, cb) {
    const command = new ExecuteStatementCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  executeTransaction(args, optionsOrCb, cb) {
    const command = new ExecuteTransactionCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  get(args, optionsOrCb, cb) {
    const command = new GetCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  put(args, optionsOrCb, cb) {
    const command = new PutCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  query(args, optionsOrCb, cb) {
    const command = new QueryCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  scan(args, optionsOrCb, cb) {
    const command = new ScanCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  transactGet(args, optionsOrCb, cb) {
    const command = new TransactGetCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  transactWrite(args, optionsOrCb, cb) {
    const command = new TransactWriteCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
  update(args, optionsOrCb, cb) {
    const command = new UpdateCommand(args);
    if (typeof optionsOrCb === "function") {
      this.send(command, optionsOrCb);
    } else if (typeof cb === "function") {
      if (typeof optionsOrCb !== "object") {
        throw new Error(`Expect http options but get ${typeof optionsOrCb}`);
      }
      this.send(command, optionsOrCb || {}, cb);
    } else {
      return this.send(command, optionsOrCb);
    }
  }
};

// src/pagination/Interfaces.ts
var import_types = require("@smithy/types");

// src/pagination/QueryPaginator.ts
var import_core2 = require("@smithy/core");

var paginateQuery = (0, import_core2.createPaginator)(DynamoDBDocumentClient, QueryCommand, "ExclusiveStartKey", "LastEvaluatedKey", "Limit");

// src/pagination/ScanPaginator.ts
var import_core3 = require("@smithy/core");

var paginateScan = (0, import_core3.createPaginator)(DynamoDBDocumentClient, ScanCommand, "ExclusiveStartKey", "LastEvaluatedKey", "Limit");

// src/index.ts



// Annotate the CommonJS export names for ESM import in node:

0 && (module.exports = {
  NumberValue,
  DynamoDBDocument,
  __Client,
  DynamoDBDocumentClient,
  DynamoDBDocumentClientCommand,
  $Command,
  BatchExecuteStatementCommand,
  BatchGetCommand,
  BatchWriteCommand,
  DeleteCommand,
  ExecuteStatementCommand,
  ExecuteTransactionCommand,
  GetCommand,
  PutCommand,
  QueryCommand,
  ScanCommand,
  TransactGetCommand,
  TransactWriteCommand,
  UpdateCommand,
  paginateQuery,
  paginateScan
});

