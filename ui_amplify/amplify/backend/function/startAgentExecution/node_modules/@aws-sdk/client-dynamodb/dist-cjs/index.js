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
  ApproximateCreationDateTimePrecision: () => ApproximateCreationDateTimePrecision,
  AttributeAction: () => AttributeAction,
  AttributeValue: () => AttributeValue,
  BackupInUseException: () => BackupInUseException,
  BackupNotFoundException: () => BackupNotFoundException,
  BackupStatus: () => BackupStatus,
  BackupType: () => BackupType,
  BackupTypeFilter: () => BackupTypeFilter,
  BatchExecuteStatementCommand: () => BatchExecuteStatementCommand,
  BatchGetItemCommand: () => BatchGetItemCommand,
  BatchStatementErrorCodeEnum: () => BatchStatementErrorCodeEnum,
  BatchWriteItemCommand: () => BatchWriteItemCommand,
  BillingMode: () => BillingMode,
  ComparisonOperator: () => ComparisonOperator,
  ConditionalCheckFailedException: () => ConditionalCheckFailedException,
  ConditionalOperator: () => ConditionalOperator,
  ContinuousBackupsStatus: () => ContinuousBackupsStatus,
  ContinuousBackupsUnavailableException: () => ContinuousBackupsUnavailableException,
  ContributorInsightsAction: () => ContributorInsightsAction,
  ContributorInsightsStatus: () => ContributorInsightsStatus,
  CreateBackupCommand: () => CreateBackupCommand,
  CreateGlobalTableCommand: () => CreateGlobalTableCommand,
  CreateTableCommand: () => CreateTableCommand,
  DeleteBackupCommand: () => DeleteBackupCommand,
  DeleteItemCommand: () => DeleteItemCommand,
  DeleteResourcePolicyCommand: () => DeleteResourcePolicyCommand,
  DeleteTableCommand: () => DeleteTableCommand,
  DescribeBackupCommand: () => DescribeBackupCommand,
  DescribeContinuousBackupsCommand: () => DescribeContinuousBackupsCommand,
  DescribeContributorInsightsCommand: () => DescribeContributorInsightsCommand,
  DescribeEndpointsCommand: () => DescribeEndpointsCommand,
  DescribeExportCommand: () => DescribeExportCommand,
  DescribeGlobalTableCommand: () => DescribeGlobalTableCommand,
  DescribeGlobalTableSettingsCommand: () => DescribeGlobalTableSettingsCommand,
  DescribeImportCommand: () => DescribeImportCommand,
  DescribeKinesisStreamingDestinationCommand: () => DescribeKinesisStreamingDestinationCommand,
  DescribeLimitsCommand: () => DescribeLimitsCommand,
  DescribeTableCommand: () => DescribeTableCommand,
  DescribeTableReplicaAutoScalingCommand: () => DescribeTableReplicaAutoScalingCommand,
  DescribeTimeToLiveCommand: () => DescribeTimeToLiveCommand,
  DestinationStatus: () => DestinationStatus,
  DisableKinesisStreamingDestinationCommand: () => DisableKinesisStreamingDestinationCommand,
  DuplicateItemException: () => DuplicateItemException,
  DynamoDB: () => DynamoDB,
  DynamoDBClient: () => DynamoDBClient,
  DynamoDBServiceException: () => DynamoDBServiceException,
  EnableKinesisStreamingDestinationCommand: () => EnableKinesisStreamingDestinationCommand,
  ExecuteStatementCommand: () => ExecuteStatementCommand,
  ExecuteTransactionCommand: () => ExecuteTransactionCommand,
  ExportConflictException: () => ExportConflictException,
  ExportFormat: () => ExportFormat,
  ExportNotFoundException: () => ExportNotFoundException,
  ExportStatus: () => ExportStatus,
  ExportTableToPointInTimeCommand: () => ExportTableToPointInTimeCommand,
  ExportType: () => ExportType,
  ExportViewType: () => ExportViewType,
  GetItemCommand: () => GetItemCommand,
  GetResourcePolicyCommand: () => GetResourcePolicyCommand,
  GlobalTableAlreadyExistsException: () => GlobalTableAlreadyExistsException,
  GlobalTableNotFoundException: () => GlobalTableNotFoundException,
  GlobalTableStatus: () => GlobalTableStatus,
  IdempotentParameterMismatchException: () => IdempotentParameterMismatchException,
  ImportConflictException: () => ImportConflictException,
  ImportNotFoundException: () => ImportNotFoundException,
  ImportStatus: () => ImportStatus,
  ImportTableCommand: () => ImportTableCommand,
  IndexNotFoundException: () => IndexNotFoundException,
  IndexStatus: () => IndexStatus,
  InputCompressionType: () => InputCompressionType,
  InputFormat: () => InputFormat,
  InternalServerError: () => InternalServerError,
  InvalidEndpointException: () => InvalidEndpointException,
  InvalidExportTimeException: () => InvalidExportTimeException,
  InvalidRestoreTimeException: () => InvalidRestoreTimeException,
  ItemCollectionSizeLimitExceededException: () => ItemCollectionSizeLimitExceededException,
  KeyType: () => KeyType,
  LimitExceededException: () => LimitExceededException,
  ListBackupsCommand: () => ListBackupsCommand,
  ListContributorInsightsCommand: () => ListContributorInsightsCommand,
  ListExportsCommand: () => ListExportsCommand,
  ListGlobalTablesCommand: () => ListGlobalTablesCommand,
  ListImportsCommand: () => ListImportsCommand,
  ListTablesCommand: () => ListTablesCommand,
  ListTagsOfResourceCommand: () => ListTagsOfResourceCommand,
  MultiRegionConsistency: () => MultiRegionConsistency,
  PointInTimeRecoveryStatus: () => PointInTimeRecoveryStatus,
  PointInTimeRecoveryUnavailableException: () => PointInTimeRecoveryUnavailableException,
  PolicyNotFoundException: () => PolicyNotFoundException,
  ProjectionType: () => ProjectionType,
  ProvisionedThroughputExceededException: () => ProvisionedThroughputExceededException,
  PutItemCommand: () => PutItemCommand,
  PutResourcePolicyCommand: () => PutResourcePolicyCommand,
  QueryCommand: () => QueryCommand,
  ReplicaAlreadyExistsException: () => ReplicaAlreadyExistsException,
  ReplicaNotFoundException: () => ReplicaNotFoundException,
  ReplicaStatus: () => ReplicaStatus,
  ReplicatedWriteConflictException: () => ReplicatedWriteConflictException,
  RequestLimitExceeded: () => RequestLimitExceeded,
  ResourceInUseException: () => ResourceInUseException,
  ResourceNotFoundException: () => ResourceNotFoundException,
  RestoreTableFromBackupCommand: () => RestoreTableFromBackupCommand,
  RestoreTableToPointInTimeCommand: () => RestoreTableToPointInTimeCommand,
  ReturnConsumedCapacity: () => ReturnConsumedCapacity,
  ReturnItemCollectionMetrics: () => ReturnItemCollectionMetrics,
  ReturnValue: () => ReturnValue,
  ReturnValuesOnConditionCheckFailure: () => ReturnValuesOnConditionCheckFailure,
  S3SseAlgorithm: () => S3SseAlgorithm,
  SSEStatus: () => SSEStatus,
  SSEType: () => SSEType,
  ScalarAttributeType: () => ScalarAttributeType,
  ScanCommand: () => ScanCommand,
  Select: () => Select,
  StreamViewType: () => StreamViewType,
  TableAlreadyExistsException: () => TableAlreadyExistsException,
  TableClass: () => TableClass,
  TableInUseException: () => TableInUseException,
  TableNotFoundException: () => TableNotFoundException,
  TableStatus: () => TableStatus,
  TagResourceCommand: () => TagResourceCommand,
  TimeToLiveStatus: () => TimeToLiveStatus,
  TransactGetItemsCommand: () => TransactGetItemsCommand,
  TransactWriteItemsCommand: () => TransactWriteItemsCommand,
  TransactionCanceledException: () => TransactionCanceledException,
  TransactionConflictException: () => TransactionConflictException,
  TransactionInProgressException: () => TransactionInProgressException,
  UntagResourceCommand: () => UntagResourceCommand,
  UpdateContinuousBackupsCommand: () => UpdateContinuousBackupsCommand,
  UpdateContributorInsightsCommand: () => UpdateContributorInsightsCommand,
  UpdateGlobalTableCommand: () => UpdateGlobalTableCommand,
  UpdateGlobalTableSettingsCommand: () => UpdateGlobalTableSettingsCommand,
  UpdateItemCommand: () => UpdateItemCommand,
  UpdateKinesisStreamingDestinationCommand: () => UpdateKinesisStreamingDestinationCommand,
  UpdateTableCommand: () => UpdateTableCommand,
  UpdateTableReplicaAutoScalingCommand: () => UpdateTableReplicaAutoScalingCommand,
  UpdateTimeToLiveCommand: () => UpdateTimeToLiveCommand,
  WitnessStatus: () => WitnessStatus,
  __Client: () => import_smithy_client.Client,
  paginateListContributorInsights: () => paginateListContributorInsights,
  paginateListExports: () => paginateListExports,
  paginateListImports: () => paginateListImports,
  paginateListTables: () => paginateListTables,
  paginateQuery: () => paginateQuery,
  paginateScan: () => paginateScan,
  waitForTableExists: () => waitForTableExists,
  waitForTableNotExists: () => waitForTableNotExists,
  waitUntilTableExists: () => waitUntilTableExists,
  waitUntilTableNotExists: () => waitUntilTableNotExists
});
module.exports = __toCommonJS(index_exports);

// src/DynamoDBClient.ts
var import_account_id_endpoint = require("@aws-sdk/core/account-id-endpoint");
var import_middleware_endpoint_discovery = require("@aws-sdk/middleware-endpoint-discovery");
var import_middleware_host_header = require("@aws-sdk/middleware-host-header");
var import_middleware_logger = require("@aws-sdk/middleware-logger");
var import_middleware_recursion_detection = require("@aws-sdk/middleware-recursion-detection");
var import_middleware_user_agent = require("@aws-sdk/middleware-user-agent");
var import_config_resolver = require("@smithy/config-resolver");
var import_core2 = require("@smithy/core");
var import_middleware_content_length = require("@smithy/middleware-content-length");

var import_middleware_retry = require("@smithy/middleware-retry");

var import_httpAuthSchemeProvider = require("./auth/httpAuthSchemeProvider");

// src/commands/DescribeEndpointsCommand.ts
var import_middleware_endpoint = require("@smithy/middleware-endpoint");
var import_middleware_serde = require("@smithy/middleware-serde");


// src/endpoint/EndpointParameters.ts
var resolveClientEndpointParameters = /* @__PURE__ */ __name((options) => {
  return Object.assign(options, {
    useDualstackEndpoint: options.useDualstackEndpoint ?? false,
    useFipsEndpoint: options.useFipsEndpoint ?? false,
    defaultSigningName: "dynamodb"
  });
}, "resolveClientEndpointParameters");
var commonParams = {
  UseFIPS: { type: "builtInParams", name: "useFipsEndpoint" },
  AccountId: { type: "builtInParams", name: "accountId" },
  Endpoint: { type: "builtInParams", name: "endpoint" },
  Region: { type: "builtInParams", name: "region" },
  UseDualStack: { type: "builtInParams", name: "useDualstackEndpoint" },
  AccountIdEndpointMode: { type: "builtInParams", name: "accountIdEndpointMode" }
};

// src/protocols/Aws_json1_0.ts
var import_core = require("@aws-sdk/core");
var import_protocol_http = require("@smithy/protocol-http");

var import_uuid = require("uuid");

// src/models/DynamoDBServiceException.ts
var import_smithy_client = require("@smithy/smithy-client");
var DynamoDBServiceException = class _DynamoDBServiceException extends import_smithy_client.ServiceException {
  static {
    __name(this, "DynamoDBServiceException");
  }
  /**
   * @internal
   */
  constructor(options) {
    super(options);
    Object.setPrototypeOf(this, _DynamoDBServiceException.prototype);
  }
};

// src/models/models_0.ts
var ApproximateCreationDateTimePrecision = {
  MICROSECOND: "MICROSECOND",
  MILLISECOND: "MILLISECOND"
};
var AttributeAction = {
  ADD: "ADD",
  DELETE: "DELETE",
  PUT: "PUT"
};
var ScalarAttributeType = {
  B: "B",
  N: "N",
  S: "S"
};
var BackupStatus = {
  AVAILABLE: "AVAILABLE",
  CREATING: "CREATING",
  DELETED: "DELETED"
};
var BackupType = {
  AWS_BACKUP: "AWS_BACKUP",
  SYSTEM: "SYSTEM",
  USER: "USER"
};
var BillingMode = {
  PAY_PER_REQUEST: "PAY_PER_REQUEST",
  PROVISIONED: "PROVISIONED"
};
var KeyType = {
  HASH: "HASH",
  RANGE: "RANGE"
};
var ProjectionType = {
  ALL: "ALL",
  INCLUDE: "INCLUDE",
  KEYS_ONLY: "KEYS_ONLY"
};
var SSEType = {
  AES256: "AES256",
  KMS: "KMS"
};
var SSEStatus = {
  DISABLED: "DISABLED",
  DISABLING: "DISABLING",
  ENABLED: "ENABLED",
  ENABLING: "ENABLING",
  UPDATING: "UPDATING"
};
var StreamViewType = {
  KEYS_ONLY: "KEYS_ONLY",
  NEW_AND_OLD_IMAGES: "NEW_AND_OLD_IMAGES",
  NEW_IMAGE: "NEW_IMAGE",
  OLD_IMAGE: "OLD_IMAGE"
};
var TimeToLiveStatus = {
  DISABLED: "DISABLED",
  DISABLING: "DISABLING",
  ENABLED: "ENABLED",
  ENABLING: "ENABLING"
};
var BackupInUseException = class _BackupInUseException extends DynamoDBServiceException {
  static {
    __name(this, "BackupInUseException");
  }
  name = "BackupInUseException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "BackupInUseException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _BackupInUseException.prototype);
  }
};
var BackupNotFoundException = class _BackupNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "BackupNotFoundException");
  }
  name = "BackupNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "BackupNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _BackupNotFoundException.prototype);
  }
};
var BackupTypeFilter = {
  ALL: "ALL",
  AWS_BACKUP: "AWS_BACKUP",
  SYSTEM: "SYSTEM",
  USER: "USER"
};
var ReturnConsumedCapacity = {
  INDEXES: "INDEXES",
  NONE: "NONE",
  TOTAL: "TOTAL"
};
var ReturnValuesOnConditionCheckFailure = {
  ALL_OLD: "ALL_OLD",
  NONE: "NONE"
};
var BatchStatementErrorCodeEnum = {
  AccessDenied: "AccessDenied",
  ConditionalCheckFailed: "ConditionalCheckFailed",
  DuplicateItem: "DuplicateItem",
  InternalServerError: "InternalServerError",
  ItemCollectionSizeLimitExceeded: "ItemCollectionSizeLimitExceeded",
  ProvisionedThroughputExceeded: "ProvisionedThroughputExceeded",
  RequestLimitExceeded: "RequestLimitExceeded",
  ResourceNotFound: "ResourceNotFound",
  ThrottlingError: "ThrottlingError",
  TransactionConflict: "TransactionConflict",
  ValidationError: "ValidationError"
};
var InternalServerError = class _InternalServerError extends DynamoDBServiceException {
  static {
    __name(this, "InternalServerError");
  }
  name = "InternalServerError";
  $fault = "server";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "InternalServerError",
      $fault: "server",
      ...opts
    });
    Object.setPrototypeOf(this, _InternalServerError.prototype);
  }
};
var RequestLimitExceeded = class _RequestLimitExceeded extends DynamoDBServiceException {
  static {
    __name(this, "RequestLimitExceeded");
  }
  name = "RequestLimitExceeded";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "RequestLimitExceeded",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _RequestLimitExceeded.prototype);
  }
};
var InvalidEndpointException = class _InvalidEndpointException extends DynamoDBServiceException {
  static {
    __name(this, "InvalidEndpointException");
  }
  name = "InvalidEndpointException";
  $fault = "client";
  Message;
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "InvalidEndpointException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _InvalidEndpointException.prototype);
    this.Message = opts.Message;
  }
};
var ProvisionedThroughputExceededException = class _ProvisionedThroughputExceededException extends DynamoDBServiceException {
  static {
    __name(this, "ProvisionedThroughputExceededException");
  }
  name = "ProvisionedThroughputExceededException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ProvisionedThroughputExceededException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ProvisionedThroughputExceededException.prototype);
  }
};
var ResourceNotFoundException = class _ResourceNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "ResourceNotFoundException");
  }
  name = "ResourceNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ResourceNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ResourceNotFoundException.prototype);
  }
};
var ReturnItemCollectionMetrics = {
  NONE: "NONE",
  SIZE: "SIZE"
};
var ItemCollectionSizeLimitExceededException = class _ItemCollectionSizeLimitExceededException extends DynamoDBServiceException {
  static {
    __name(this, "ItemCollectionSizeLimitExceededException");
  }
  name = "ItemCollectionSizeLimitExceededException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ItemCollectionSizeLimitExceededException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ItemCollectionSizeLimitExceededException.prototype);
  }
};
var ReplicatedWriteConflictException = class _ReplicatedWriteConflictException extends DynamoDBServiceException {
  static {
    __name(this, "ReplicatedWriteConflictException");
  }
  name = "ReplicatedWriteConflictException";
  $fault = "client";
  $retryable = {};
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ReplicatedWriteConflictException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ReplicatedWriteConflictException.prototype);
  }
};
var ComparisonOperator = {
  BEGINS_WITH: "BEGINS_WITH",
  BETWEEN: "BETWEEN",
  CONTAINS: "CONTAINS",
  EQ: "EQ",
  GE: "GE",
  GT: "GT",
  IN: "IN",
  LE: "LE",
  LT: "LT",
  NE: "NE",
  NOT_CONTAINS: "NOT_CONTAINS",
  NOT_NULL: "NOT_NULL",
  NULL: "NULL"
};
var ConditionalOperator = {
  AND: "AND",
  OR: "OR"
};
var ContinuousBackupsStatus = {
  DISABLED: "DISABLED",
  ENABLED: "ENABLED"
};
var PointInTimeRecoveryStatus = {
  DISABLED: "DISABLED",
  ENABLED: "ENABLED"
};
var ContinuousBackupsUnavailableException = class _ContinuousBackupsUnavailableException extends DynamoDBServiceException {
  static {
    __name(this, "ContinuousBackupsUnavailableException");
  }
  name = "ContinuousBackupsUnavailableException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ContinuousBackupsUnavailableException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ContinuousBackupsUnavailableException.prototype);
  }
};
var ContributorInsightsAction = {
  DISABLE: "DISABLE",
  ENABLE: "ENABLE"
};
var ContributorInsightsStatus = {
  DISABLED: "DISABLED",
  DISABLING: "DISABLING",
  ENABLED: "ENABLED",
  ENABLING: "ENABLING",
  FAILED: "FAILED"
};
var LimitExceededException = class _LimitExceededException extends DynamoDBServiceException {
  static {
    __name(this, "LimitExceededException");
  }
  name = "LimitExceededException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "LimitExceededException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _LimitExceededException.prototype);
  }
};
var TableInUseException = class _TableInUseException extends DynamoDBServiceException {
  static {
    __name(this, "TableInUseException");
  }
  name = "TableInUseException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "TableInUseException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TableInUseException.prototype);
  }
};
var TableNotFoundException = class _TableNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "TableNotFoundException");
  }
  name = "TableNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "TableNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TableNotFoundException.prototype);
  }
};
var GlobalTableStatus = {
  ACTIVE: "ACTIVE",
  CREATING: "CREATING",
  DELETING: "DELETING",
  UPDATING: "UPDATING"
};
var IndexStatus = {
  ACTIVE: "ACTIVE",
  CREATING: "CREATING",
  DELETING: "DELETING",
  UPDATING: "UPDATING"
};
var ReplicaStatus = {
  ACTIVE: "ACTIVE",
  ARCHIVED: "ARCHIVED",
  ARCHIVING: "ARCHIVING",
  CREATING: "CREATING",
  CREATION_FAILED: "CREATION_FAILED",
  DELETING: "DELETING",
  INACCESSIBLE_ENCRYPTION_CREDENTIALS: "INACCESSIBLE_ENCRYPTION_CREDENTIALS",
  REGION_DISABLED: "REGION_DISABLED",
  REPLICATION_NOT_AUTHORIZED: "REPLICATION_NOT_AUTHORIZED",
  UPDATING: "UPDATING"
};
var TableClass = {
  STANDARD: "STANDARD",
  STANDARD_INFREQUENT_ACCESS: "STANDARD_INFREQUENT_ACCESS"
};
var TableStatus = {
  ACTIVE: "ACTIVE",
  ARCHIVED: "ARCHIVED",
  ARCHIVING: "ARCHIVING",
  CREATING: "CREATING",
  DELETING: "DELETING",
  INACCESSIBLE_ENCRYPTION_CREDENTIALS: "INACCESSIBLE_ENCRYPTION_CREDENTIALS",
  REPLICATION_NOT_AUTHORIZED: "REPLICATION_NOT_AUTHORIZED",
  UPDATING: "UPDATING"
};
var GlobalTableAlreadyExistsException = class _GlobalTableAlreadyExistsException extends DynamoDBServiceException {
  static {
    __name(this, "GlobalTableAlreadyExistsException");
  }
  name = "GlobalTableAlreadyExistsException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "GlobalTableAlreadyExistsException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _GlobalTableAlreadyExistsException.prototype);
  }
};
var WitnessStatus = {
  ACTIVE: "ACTIVE",
  CREATING: "CREATING",
  DELETING: "DELETING"
};
var MultiRegionConsistency = {
  EVENTUAL: "EVENTUAL",
  STRONG: "STRONG"
};
var ResourceInUseException = class _ResourceInUseException extends DynamoDBServiceException {
  static {
    __name(this, "ResourceInUseException");
  }
  name = "ResourceInUseException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ResourceInUseException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ResourceInUseException.prototype);
  }
};
var ReturnValue = {
  ALL_NEW: "ALL_NEW",
  ALL_OLD: "ALL_OLD",
  NONE: "NONE",
  UPDATED_NEW: "UPDATED_NEW",
  UPDATED_OLD: "UPDATED_OLD"
};
var TransactionConflictException = class _TransactionConflictException extends DynamoDBServiceException {
  static {
    __name(this, "TransactionConflictException");
  }
  name = "TransactionConflictException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "TransactionConflictException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TransactionConflictException.prototype);
  }
};
var PolicyNotFoundException = class _PolicyNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "PolicyNotFoundException");
  }
  name = "PolicyNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "PolicyNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _PolicyNotFoundException.prototype);
  }
};
var ExportFormat = {
  DYNAMODB_JSON: "DYNAMODB_JSON",
  ION: "ION"
};
var ExportStatus = {
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  IN_PROGRESS: "IN_PROGRESS"
};
var ExportType = {
  FULL_EXPORT: "FULL_EXPORT",
  INCREMENTAL_EXPORT: "INCREMENTAL_EXPORT"
};
var ExportViewType = {
  NEW_AND_OLD_IMAGES: "NEW_AND_OLD_IMAGES",
  NEW_IMAGE: "NEW_IMAGE"
};
var S3SseAlgorithm = {
  AES256: "AES256",
  KMS: "KMS"
};
var ExportNotFoundException = class _ExportNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "ExportNotFoundException");
  }
  name = "ExportNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ExportNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ExportNotFoundException.prototype);
  }
};
var GlobalTableNotFoundException = class _GlobalTableNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "GlobalTableNotFoundException");
  }
  name = "GlobalTableNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "GlobalTableNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _GlobalTableNotFoundException.prototype);
  }
};
var ImportStatus = {
  CANCELLED: "CANCELLED",
  CANCELLING: "CANCELLING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  IN_PROGRESS: "IN_PROGRESS"
};
var InputCompressionType = {
  GZIP: "GZIP",
  NONE: "NONE",
  ZSTD: "ZSTD"
};
var InputFormat = {
  CSV: "CSV",
  DYNAMODB_JSON: "DYNAMODB_JSON",
  ION: "ION"
};
var ImportNotFoundException = class _ImportNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "ImportNotFoundException");
  }
  name = "ImportNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ImportNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ImportNotFoundException.prototype);
  }
};
var DestinationStatus = {
  ACTIVE: "ACTIVE",
  DISABLED: "DISABLED",
  DISABLING: "DISABLING",
  ENABLE_FAILED: "ENABLE_FAILED",
  ENABLING: "ENABLING",
  UPDATING: "UPDATING"
};
var DuplicateItemException = class _DuplicateItemException extends DynamoDBServiceException {
  static {
    __name(this, "DuplicateItemException");
  }
  name = "DuplicateItemException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "DuplicateItemException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _DuplicateItemException.prototype);
  }
};
var IdempotentParameterMismatchException = class _IdempotentParameterMismatchException extends DynamoDBServiceException {
  static {
    __name(this, "IdempotentParameterMismatchException");
  }
  name = "IdempotentParameterMismatchException";
  $fault = "client";
  Message;
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "IdempotentParameterMismatchException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _IdempotentParameterMismatchException.prototype);
    this.Message = opts.Message;
  }
};
var TransactionInProgressException = class _TransactionInProgressException extends DynamoDBServiceException {
  static {
    __name(this, "TransactionInProgressException");
  }
  name = "TransactionInProgressException";
  $fault = "client";
  Message;
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "TransactionInProgressException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TransactionInProgressException.prototype);
    this.Message = opts.Message;
  }
};
var ExportConflictException = class _ExportConflictException extends DynamoDBServiceException {
  static {
    __name(this, "ExportConflictException");
  }
  name = "ExportConflictException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ExportConflictException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ExportConflictException.prototype);
  }
};
var InvalidExportTimeException = class _InvalidExportTimeException extends DynamoDBServiceException {
  static {
    __name(this, "InvalidExportTimeException");
  }
  name = "InvalidExportTimeException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "InvalidExportTimeException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _InvalidExportTimeException.prototype);
  }
};
var PointInTimeRecoveryUnavailableException = class _PointInTimeRecoveryUnavailableException extends DynamoDBServiceException {
  static {
    __name(this, "PointInTimeRecoveryUnavailableException");
  }
  name = "PointInTimeRecoveryUnavailableException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "PointInTimeRecoveryUnavailableException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _PointInTimeRecoveryUnavailableException.prototype);
  }
};
var ImportConflictException = class _ImportConflictException extends DynamoDBServiceException {
  static {
    __name(this, "ImportConflictException");
  }
  name = "ImportConflictException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ImportConflictException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ImportConflictException.prototype);
  }
};
var Select = {
  ALL_ATTRIBUTES: "ALL_ATTRIBUTES",
  ALL_PROJECTED_ATTRIBUTES: "ALL_PROJECTED_ATTRIBUTES",
  COUNT: "COUNT",
  SPECIFIC_ATTRIBUTES: "SPECIFIC_ATTRIBUTES"
};
var TableAlreadyExistsException = class _TableAlreadyExistsException extends DynamoDBServiceException {
  static {
    __name(this, "TableAlreadyExistsException");
  }
  name = "TableAlreadyExistsException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "TableAlreadyExistsException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TableAlreadyExistsException.prototype);
  }
};
var InvalidRestoreTimeException = class _InvalidRestoreTimeException extends DynamoDBServiceException {
  static {
    __name(this, "InvalidRestoreTimeException");
  }
  name = "InvalidRestoreTimeException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "InvalidRestoreTimeException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _InvalidRestoreTimeException.prototype);
  }
};
var ReplicaAlreadyExistsException = class _ReplicaAlreadyExistsException extends DynamoDBServiceException {
  static {
    __name(this, "ReplicaAlreadyExistsException");
  }
  name = "ReplicaAlreadyExistsException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ReplicaAlreadyExistsException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ReplicaAlreadyExistsException.prototype);
  }
};
var ReplicaNotFoundException = class _ReplicaNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "ReplicaNotFoundException");
  }
  name = "ReplicaNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ReplicaNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ReplicaNotFoundException.prototype);
  }
};
var IndexNotFoundException = class _IndexNotFoundException extends DynamoDBServiceException {
  static {
    __name(this, "IndexNotFoundException");
  }
  name = "IndexNotFoundException";
  $fault = "client";
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "IndexNotFoundException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _IndexNotFoundException.prototype);
  }
};
var AttributeValue;
((AttributeValue2) => {
  AttributeValue2.visit = /* @__PURE__ */ __name((value, visitor) => {
    if (value.S !== void 0) return visitor.S(value.S);
    if (value.N !== void 0) return visitor.N(value.N);
    if (value.B !== void 0) return visitor.B(value.B);
    if (value.SS !== void 0) return visitor.SS(value.SS);
    if (value.NS !== void 0) return visitor.NS(value.NS);
    if (value.BS !== void 0) return visitor.BS(value.BS);
    if (value.M !== void 0) return visitor.M(value.M);
    if (value.L !== void 0) return visitor.L(value.L);
    if (value.NULL !== void 0) return visitor.NULL(value.NULL);
    if (value.BOOL !== void 0) return visitor.BOOL(value.BOOL);
    return visitor._(value.$unknown[0], value.$unknown[1]);
  }, "visit");
})(AttributeValue || (AttributeValue = {}));
var ConditionalCheckFailedException = class _ConditionalCheckFailedException extends DynamoDBServiceException {
  static {
    __name(this, "ConditionalCheckFailedException");
  }
  name = "ConditionalCheckFailedException";
  $fault = "client";
  /**
   * <p>Item which caused the <code>ConditionalCheckFailedException</code>.</p>
   * @public
   */
  Item;
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "ConditionalCheckFailedException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _ConditionalCheckFailedException.prototype);
    this.Item = opts.Item;
  }
};
var TransactionCanceledException = class _TransactionCanceledException extends DynamoDBServiceException {
  static {
    __name(this, "TransactionCanceledException");
  }
  name = "TransactionCanceledException";
  $fault = "client";
  Message;
  /**
   * <p>A list of cancellation reasons.</p>
   * @public
   */
  CancellationReasons;
  /**
   * @internal
   */
  constructor(opts) {
    super({
      name: "TransactionCanceledException",
      $fault: "client",
      ...opts
    });
    Object.setPrototypeOf(this, _TransactionCanceledException.prototype);
    this.Message = opts.Message;
    this.CancellationReasons = opts.CancellationReasons;
  }
};

// src/protocols/Aws_json1_0.ts
var se_BatchExecuteStatementCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("BatchExecuteStatement");
  let body;
  body = JSON.stringify(se_BatchExecuteStatementInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_BatchExecuteStatementCommand");
var se_BatchGetItemCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("BatchGetItem");
  let body;
  body = JSON.stringify(se_BatchGetItemInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_BatchGetItemCommand");
var se_BatchWriteItemCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("BatchWriteItem");
  let body;
  body = JSON.stringify(se_BatchWriteItemInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_BatchWriteItemCommand");
var se_CreateBackupCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("CreateBackup");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_CreateBackupCommand");
var se_CreateGlobalTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("CreateGlobalTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_CreateGlobalTableCommand");
var se_CreateTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("CreateTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_CreateTableCommand");
var se_DeleteBackupCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DeleteBackup");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DeleteBackupCommand");
var se_DeleteItemCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DeleteItem");
  let body;
  body = JSON.stringify(se_DeleteItemInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DeleteItemCommand");
var se_DeleteResourcePolicyCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DeleteResourcePolicy");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DeleteResourcePolicyCommand");
var se_DeleteTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DeleteTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DeleteTableCommand");
var se_DescribeBackupCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeBackup");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeBackupCommand");
var se_DescribeContinuousBackupsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeContinuousBackups");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeContinuousBackupsCommand");
var se_DescribeContributorInsightsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeContributorInsights");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeContributorInsightsCommand");
var se_DescribeEndpointsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeEndpoints");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeEndpointsCommand");
var se_DescribeExportCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeExport");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeExportCommand");
var se_DescribeGlobalTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeGlobalTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeGlobalTableCommand");
var se_DescribeGlobalTableSettingsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeGlobalTableSettings");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeGlobalTableSettingsCommand");
var se_DescribeImportCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeImport");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeImportCommand");
var se_DescribeKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeKinesisStreamingDestination");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeKinesisStreamingDestinationCommand");
var se_DescribeLimitsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeLimits");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeLimitsCommand");
var se_DescribeTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeTableCommand");
var se_DescribeTableReplicaAutoScalingCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeTableReplicaAutoScaling");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeTableReplicaAutoScalingCommand");
var se_DescribeTimeToLiveCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DescribeTimeToLive");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DescribeTimeToLiveCommand");
var se_DisableKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("DisableKinesisStreamingDestination");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_DisableKinesisStreamingDestinationCommand");
var se_EnableKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("EnableKinesisStreamingDestination");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_EnableKinesisStreamingDestinationCommand");
var se_ExecuteStatementCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ExecuteStatement");
  let body;
  body = JSON.stringify(se_ExecuteStatementInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ExecuteStatementCommand");
var se_ExecuteTransactionCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ExecuteTransaction");
  let body;
  body = JSON.stringify(se_ExecuteTransactionInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ExecuteTransactionCommand");
var se_ExportTableToPointInTimeCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ExportTableToPointInTime");
  let body;
  body = JSON.stringify(se_ExportTableToPointInTimeInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ExportTableToPointInTimeCommand");
var se_GetItemCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("GetItem");
  let body;
  body = JSON.stringify(se_GetItemInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_GetItemCommand");
var se_GetResourcePolicyCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("GetResourcePolicy");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_GetResourcePolicyCommand");
var se_ImportTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ImportTable");
  let body;
  body = JSON.stringify(se_ImportTableInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ImportTableCommand");
var se_ListBackupsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListBackups");
  let body;
  body = JSON.stringify(se_ListBackupsInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListBackupsCommand");
var se_ListContributorInsightsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListContributorInsights");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListContributorInsightsCommand");
var se_ListExportsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListExports");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListExportsCommand");
var se_ListGlobalTablesCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListGlobalTables");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListGlobalTablesCommand");
var se_ListImportsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListImports");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListImportsCommand");
var se_ListTablesCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListTables");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListTablesCommand");
var se_ListTagsOfResourceCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("ListTagsOfResource");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ListTagsOfResourceCommand");
var se_PutItemCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("PutItem");
  let body;
  body = JSON.stringify(se_PutItemInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_PutItemCommand");
var se_PutResourcePolicyCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("PutResourcePolicy");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_PutResourcePolicyCommand");
var se_QueryCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("Query");
  let body;
  body = JSON.stringify(se_QueryInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_QueryCommand");
var se_RestoreTableFromBackupCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("RestoreTableFromBackup");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_RestoreTableFromBackupCommand");
var se_RestoreTableToPointInTimeCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("RestoreTableToPointInTime");
  let body;
  body = JSON.stringify(se_RestoreTableToPointInTimeInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_RestoreTableToPointInTimeCommand");
var se_ScanCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("Scan");
  let body;
  body = JSON.stringify(se_ScanInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_ScanCommand");
var se_TagResourceCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("TagResource");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_TagResourceCommand");
var se_TransactGetItemsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("TransactGetItems");
  let body;
  body = JSON.stringify(se_TransactGetItemsInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_TransactGetItemsCommand");
var se_TransactWriteItemsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("TransactWriteItems");
  let body;
  body = JSON.stringify(se_TransactWriteItemsInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_TransactWriteItemsCommand");
var se_UntagResourceCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UntagResource");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UntagResourceCommand");
var se_UpdateContinuousBackupsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateContinuousBackups");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateContinuousBackupsCommand");
var se_UpdateContributorInsightsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateContributorInsights");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateContributorInsightsCommand");
var se_UpdateGlobalTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateGlobalTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateGlobalTableCommand");
var se_UpdateGlobalTableSettingsCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateGlobalTableSettings");
  let body;
  body = JSON.stringify(se_UpdateGlobalTableSettingsInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateGlobalTableSettingsCommand");
var se_UpdateItemCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateItem");
  let body;
  body = JSON.stringify(se_UpdateItemInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateItemCommand");
var se_UpdateKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateKinesisStreamingDestination");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateKinesisStreamingDestinationCommand");
var se_UpdateTableCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateTable");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateTableCommand");
var se_UpdateTableReplicaAutoScalingCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateTableReplicaAutoScaling");
  let body;
  body = JSON.stringify(se_UpdateTableReplicaAutoScalingInput(input, context));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateTableReplicaAutoScalingCommand");
var se_UpdateTimeToLiveCommand = /* @__PURE__ */ __name(async (input, context) => {
  const headers = sharedHeaders("UpdateTimeToLive");
  let body;
  body = JSON.stringify((0, import_smithy_client._json)(input));
  return buildHttpRpcRequest(context, headers, "/", void 0, body);
}, "se_UpdateTimeToLiveCommand");
var de_BatchExecuteStatementCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_BatchExecuteStatementOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_BatchExecuteStatementCommand");
var de_BatchGetItemCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_BatchGetItemOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_BatchGetItemCommand");
var de_BatchWriteItemCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_BatchWriteItemOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_BatchWriteItemCommand");
var de_CreateBackupCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_CreateBackupOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_CreateBackupCommand");
var de_CreateGlobalTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_CreateGlobalTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_CreateGlobalTableCommand");
var de_CreateTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_CreateTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_CreateTableCommand");
var de_DeleteBackupCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DeleteBackupOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DeleteBackupCommand");
var de_DeleteItemCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DeleteItemOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DeleteItemCommand");
var de_DeleteResourcePolicyCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DeleteResourcePolicyCommand");
var de_DeleteTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DeleteTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DeleteTableCommand");
var de_DescribeBackupCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeBackupOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeBackupCommand");
var de_DescribeContinuousBackupsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeContinuousBackupsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeContinuousBackupsCommand");
var de_DescribeContributorInsightsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeContributorInsightsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeContributorInsightsCommand");
var de_DescribeEndpointsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeEndpointsCommand");
var de_DescribeExportCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeExportOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeExportCommand");
var de_DescribeGlobalTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeGlobalTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeGlobalTableCommand");
var de_DescribeGlobalTableSettingsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeGlobalTableSettingsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeGlobalTableSettingsCommand");
var de_DescribeImportCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeImportOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeImportCommand");
var de_DescribeKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeKinesisStreamingDestinationCommand");
var de_DescribeLimitsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeLimitsCommand");
var de_DescribeTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeTableCommand");
var de_DescribeTableReplicaAutoScalingCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_DescribeTableReplicaAutoScalingOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeTableReplicaAutoScalingCommand");
var de_DescribeTimeToLiveCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DescribeTimeToLiveCommand");
var de_DisableKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_DisableKinesisStreamingDestinationCommand");
var de_EnableKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_EnableKinesisStreamingDestinationCommand");
var de_ExecuteStatementCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ExecuteStatementOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ExecuteStatementCommand");
var de_ExecuteTransactionCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ExecuteTransactionOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ExecuteTransactionCommand");
var de_ExportTableToPointInTimeCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ExportTableToPointInTimeOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ExportTableToPointInTimeCommand");
var de_GetItemCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_GetItemOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_GetItemCommand");
var de_GetResourcePolicyCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_GetResourcePolicyCommand");
var de_ImportTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ImportTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ImportTableCommand");
var de_ListBackupsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ListBackupsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListBackupsCommand");
var de_ListContributorInsightsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListContributorInsightsCommand");
var de_ListExportsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListExportsCommand");
var de_ListGlobalTablesCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListGlobalTablesCommand");
var de_ListImportsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ListImportsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListImportsCommand");
var de_ListTablesCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListTablesCommand");
var de_ListTagsOfResourceCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ListTagsOfResourceCommand");
var de_PutItemCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_PutItemOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_PutItemCommand");
var de_PutResourcePolicyCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_PutResourcePolicyCommand");
var de_QueryCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_QueryOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_QueryCommand");
var de_RestoreTableFromBackupCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_RestoreTableFromBackupOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_RestoreTableFromBackupCommand");
var de_RestoreTableToPointInTimeCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_RestoreTableToPointInTimeOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_RestoreTableToPointInTimeCommand");
var de_ScanCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_ScanOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_ScanCommand");
var de_TagResourceCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  await (0, import_smithy_client.collectBody)(output.body, context);
  const response = {
    $metadata: deserializeMetadata(output)
  };
  return response;
}, "de_TagResourceCommand");
var de_TransactGetItemsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_TransactGetItemsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_TransactGetItemsCommand");
var de_TransactWriteItemsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_TransactWriteItemsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_TransactWriteItemsCommand");
var de_UntagResourceCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  await (0, import_smithy_client.collectBody)(output.body, context);
  const response = {
    $metadata: deserializeMetadata(output)
  };
  return response;
}, "de_UntagResourceCommand");
var de_UpdateContinuousBackupsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_UpdateContinuousBackupsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateContinuousBackupsCommand");
var de_UpdateContributorInsightsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateContributorInsightsCommand");
var de_UpdateGlobalTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_UpdateGlobalTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateGlobalTableCommand");
var de_UpdateGlobalTableSettingsCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_UpdateGlobalTableSettingsOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateGlobalTableSettingsCommand");
var de_UpdateItemCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_UpdateItemOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateItemCommand");
var de_UpdateKinesisStreamingDestinationCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateKinesisStreamingDestinationCommand");
var de_UpdateTableCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_UpdateTableOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateTableCommand");
var de_UpdateTableReplicaAutoScalingCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = de_UpdateTableReplicaAutoScalingOutput(data, context);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateTableReplicaAutoScalingCommand");
var de_UpdateTimeToLiveCommand = /* @__PURE__ */ __name(async (output, context) => {
  if (output.statusCode >= 300) {
    return de_CommandError(output, context);
  }
  const data = await (0, import_core.parseJsonBody)(output.body, context);
  let contents = {};
  contents = (0, import_smithy_client._json)(data);
  const response = {
    $metadata: deserializeMetadata(output),
    ...contents
  };
  return response;
}, "de_UpdateTimeToLiveCommand");
var de_CommandError = /* @__PURE__ */ __name(async (output, context) => {
  const parsedOutput = {
    ...output,
    body: await (0, import_core.parseJsonErrorBody)(output.body, context)
  };
  const errorCode = (0, import_core.loadRestJsonErrorCode)(output, parsedOutput.body);
  switch (errorCode) {
    case "InternalServerError":
    case "com.amazonaws.dynamodb#InternalServerError":
      throw await de_InternalServerErrorRes(parsedOutput, context);
    case "RequestLimitExceeded":
    case "com.amazonaws.dynamodb#RequestLimitExceeded":
      throw await de_RequestLimitExceededRes(parsedOutput, context);
    case "InvalidEndpointException":
    case "com.amazonaws.dynamodb#InvalidEndpointException":
      throw await de_InvalidEndpointExceptionRes(parsedOutput, context);
    case "ProvisionedThroughputExceededException":
    case "com.amazonaws.dynamodb#ProvisionedThroughputExceededException":
      throw await de_ProvisionedThroughputExceededExceptionRes(parsedOutput, context);
    case "ResourceNotFoundException":
    case "com.amazonaws.dynamodb#ResourceNotFoundException":
      throw await de_ResourceNotFoundExceptionRes(parsedOutput, context);
    case "ItemCollectionSizeLimitExceededException":
    case "com.amazonaws.dynamodb#ItemCollectionSizeLimitExceededException":
      throw await de_ItemCollectionSizeLimitExceededExceptionRes(parsedOutput, context);
    case "ReplicatedWriteConflictException":
    case "com.amazonaws.dynamodb#ReplicatedWriteConflictException":
      throw await de_ReplicatedWriteConflictExceptionRes(parsedOutput, context);
    case "BackupInUseException":
    case "com.amazonaws.dynamodb#BackupInUseException":
      throw await de_BackupInUseExceptionRes(parsedOutput, context);
    case "ContinuousBackupsUnavailableException":
    case "com.amazonaws.dynamodb#ContinuousBackupsUnavailableException":
      throw await de_ContinuousBackupsUnavailableExceptionRes(parsedOutput, context);
    case "LimitExceededException":
    case "com.amazonaws.dynamodb#LimitExceededException":
      throw await de_LimitExceededExceptionRes(parsedOutput, context);
    case "TableInUseException":
    case "com.amazonaws.dynamodb#TableInUseException":
      throw await de_TableInUseExceptionRes(parsedOutput, context);
    case "TableNotFoundException":
    case "com.amazonaws.dynamodb#TableNotFoundException":
      throw await de_TableNotFoundExceptionRes(parsedOutput, context);
    case "GlobalTableAlreadyExistsException":
    case "com.amazonaws.dynamodb#GlobalTableAlreadyExistsException":
      throw await de_GlobalTableAlreadyExistsExceptionRes(parsedOutput, context);
    case "ResourceInUseException":
    case "com.amazonaws.dynamodb#ResourceInUseException":
      throw await de_ResourceInUseExceptionRes(parsedOutput, context);
    case "BackupNotFoundException":
    case "com.amazonaws.dynamodb#BackupNotFoundException":
      throw await de_BackupNotFoundExceptionRes(parsedOutput, context);
    case "ConditionalCheckFailedException":
    case "com.amazonaws.dynamodb#ConditionalCheckFailedException":
      throw await de_ConditionalCheckFailedExceptionRes(parsedOutput, context);
    case "TransactionConflictException":
    case "com.amazonaws.dynamodb#TransactionConflictException":
      throw await de_TransactionConflictExceptionRes(parsedOutput, context);
    case "PolicyNotFoundException":
    case "com.amazonaws.dynamodb#PolicyNotFoundException":
      throw await de_PolicyNotFoundExceptionRes(parsedOutput, context);
    case "ExportNotFoundException":
    case "com.amazonaws.dynamodb#ExportNotFoundException":
      throw await de_ExportNotFoundExceptionRes(parsedOutput, context);
    case "GlobalTableNotFoundException":
    case "com.amazonaws.dynamodb#GlobalTableNotFoundException":
      throw await de_GlobalTableNotFoundExceptionRes(parsedOutput, context);
    case "ImportNotFoundException":
    case "com.amazonaws.dynamodb#ImportNotFoundException":
      throw await de_ImportNotFoundExceptionRes(parsedOutput, context);
    case "DuplicateItemException":
    case "com.amazonaws.dynamodb#DuplicateItemException":
      throw await de_DuplicateItemExceptionRes(parsedOutput, context);
    case "IdempotentParameterMismatchException":
    case "com.amazonaws.dynamodb#IdempotentParameterMismatchException":
      throw await de_IdempotentParameterMismatchExceptionRes(parsedOutput, context);
    case "TransactionCanceledException":
    case "com.amazonaws.dynamodb#TransactionCanceledException":
      throw await de_TransactionCanceledExceptionRes(parsedOutput, context);
    case "TransactionInProgressException":
    case "com.amazonaws.dynamodb#TransactionInProgressException":
      throw await de_TransactionInProgressExceptionRes(parsedOutput, context);
    case "ExportConflictException":
    case "com.amazonaws.dynamodb#ExportConflictException":
      throw await de_ExportConflictExceptionRes(parsedOutput, context);
    case "InvalidExportTimeException":
    case "com.amazonaws.dynamodb#InvalidExportTimeException":
      throw await de_InvalidExportTimeExceptionRes(parsedOutput, context);
    case "PointInTimeRecoveryUnavailableException":
    case "com.amazonaws.dynamodb#PointInTimeRecoveryUnavailableException":
      throw await de_PointInTimeRecoveryUnavailableExceptionRes(parsedOutput, context);
    case "ImportConflictException":
    case "com.amazonaws.dynamodb#ImportConflictException":
      throw await de_ImportConflictExceptionRes(parsedOutput, context);
    case "TableAlreadyExistsException":
    case "com.amazonaws.dynamodb#TableAlreadyExistsException":
      throw await de_TableAlreadyExistsExceptionRes(parsedOutput, context);
    case "InvalidRestoreTimeException":
    case "com.amazonaws.dynamodb#InvalidRestoreTimeException":
      throw await de_InvalidRestoreTimeExceptionRes(parsedOutput, context);
    case "ReplicaAlreadyExistsException":
    case "com.amazonaws.dynamodb#ReplicaAlreadyExistsException":
      throw await de_ReplicaAlreadyExistsExceptionRes(parsedOutput, context);
    case "ReplicaNotFoundException":
    case "com.amazonaws.dynamodb#ReplicaNotFoundException":
      throw await de_ReplicaNotFoundExceptionRes(parsedOutput, context);
    case "IndexNotFoundException":
    case "com.amazonaws.dynamodb#IndexNotFoundException":
      throw await de_IndexNotFoundExceptionRes(parsedOutput, context);
    default:
      const parsedBody = parsedOutput.body;
      return throwDefaultError({
        output,
        parsedBody,
        errorCode
      });
  }
}, "de_CommandError");
var de_BackupInUseExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new BackupInUseException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_BackupInUseExceptionRes");
var de_BackupNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new BackupNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_BackupNotFoundExceptionRes");
var de_ConditionalCheckFailedExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = de_ConditionalCheckFailedException(body, context);
  const exception = new ConditionalCheckFailedException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ConditionalCheckFailedExceptionRes");
var de_ContinuousBackupsUnavailableExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ContinuousBackupsUnavailableException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ContinuousBackupsUnavailableExceptionRes");
var de_DuplicateItemExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new DuplicateItemException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_DuplicateItemExceptionRes");
var de_ExportConflictExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ExportConflictException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ExportConflictExceptionRes");
var de_ExportNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ExportNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ExportNotFoundExceptionRes");
var de_GlobalTableAlreadyExistsExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new GlobalTableAlreadyExistsException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_GlobalTableAlreadyExistsExceptionRes");
var de_GlobalTableNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new GlobalTableNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_GlobalTableNotFoundExceptionRes");
var de_IdempotentParameterMismatchExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new IdempotentParameterMismatchException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_IdempotentParameterMismatchExceptionRes");
var de_ImportConflictExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ImportConflictException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ImportConflictExceptionRes");
var de_ImportNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ImportNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ImportNotFoundExceptionRes");
var de_IndexNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new IndexNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_IndexNotFoundExceptionRes");
var de_InternalServerErrorRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new InternalServerError({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_InternalServerErrorRes");
var de_InvalidEndpointExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new InvalidEndpointException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_InvalidEndpointExceptionRes");
var de_InvalidExportTimeExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new InvalidExportTimeException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_InvalidExportTimeExceptionRes");
var de_InvalidRestoreTimeExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new InvalidRestoreTimeException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_InvalidRestoreTimeExceptionRes");
var de_ItemCollectionSizeLimitExceededExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ItemCollectionSizeLimitExceededException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ItemCollectionSizeLimitExceededExceptionRes");
var de_LimitExceededExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new LimitExceededException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_LimitExceededExceptionRes");
var de_PointInTimeRecoveryUnavailableExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new PointInTimeRecoveryUnavailableException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_PointInTimeRecoveryUnavailableExceptionRes");
var de_PolicyNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new PolicyNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_PolicyNotFoundExceptionRes");
var de_ProvisionedThroughputExceededExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ProvisionedThroughputExceededException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ProvisionedThroughputExceededExceptionRes");
var de_ReplicaAlreadyExistsExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ReplicaAlreadyExistsException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ReplicaAlreadyExistsExceptionRes");
var de_ReplicaNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ReplicaNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ReplicaNotFoundExceptionRes");
var de_ReplicatedWriteConflictExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ReplicatedWriteConflictException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ReplicatedWriteConflictExceptionRes");
var de_RequestLimitExceededRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new RequestLimitExceeded({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_RequestLimitExceededRes");
var de_ResourceInUseExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ResourceInUseException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ResourceInUseExceptionRes");
var de_ResourceNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new ResourceNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_ResourceNotFoundExceptionRes");
var de_TableAlreadyExistsExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new TableAlreadyExistsException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_TableAlreadyExistsExceptionRes");
var de_TableInUseExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new TableInUseException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_TableInUseExceptionRes");
var de_TableNotFoundExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new TableNotFoundException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_TableNotFoundExceptionRes");
var de_TransactionCanceledExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = de_TransactionCanceledException(body, context);
  const exception = new TransactionCanceledException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_TransactionCanceledExceptionRes");
var de_TransactionConflictExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new TransactionConflictException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_TransactionConflictExceptionRes");
var de_TransactionInProgressExceptionRes = /* @__PURE__ */ __name(async (parsedOutput, context) => {
  const body = parsedOutput.body;
  const deserialized = (0, import_smithy_client._json)(body);
  const exception = new TransactionInProgressException({
    $metadata: deserializeMetadata(parsedOutput),
    ...deserialized
  });
  return (0, import_smithy_client.decorateServiceException)(exception, body);
}, "de_TransactionInProgressExceptionRes");
var se_AttributeUpdates = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_AttributeValueUpdate(value, context);
    return acc;
  }, {});
}, "se_AttributeUpdates");
var se_AttributeValue = /* @__PURE__ */ __name((input, context) => {
  return AttributeValue.visit(input, {
    B: /* @__PURE__ */ __name((value) => ({ B: context.base64Encoder(value) }), "B"),
    BOOL: /* @__PURE__ */ __name((value) => ({ BOOL: value }), "BOOL"),
    BS: /* @__PURE__ */ __name((value) => ({ BS: se_BinarySetAttributeValue(value, context) }), "BS"),
    L: /* @__PURE__ */ __name((value) => ({ L: se_ListAttributeValue(value, context) }), "L"),
    M: /* @__PURE__ */ __name((value) => ({ M: se_MapAttributeValue(value, context) }), "M"),
    N: /* @__PURE__ */ __name((value) => ({ N: value }), "N"),
    NS: /* @__PURE__ */ __name((value) => ({ NS: (0, import_smithy_client._json)(value) }), "NS"),
    NULL: /* @__PURE__ */ __name((value) => ({ NULL: value }), "NULL"),
    S: /* @__PURE__ */ __name((value) => ({ S: value }), "S"),
    SS: /* @__PURE__ */ __name((value) => ({ SS: (0, import_smithy_client._json)(value) }), "SS"),
    _: /* @__PURE__ */ __name((name, value) => ({ [name]: value }), "_")
  });
}, "se_AttributeValue");
var se_AttributeValueList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_AttributeValue(entry, context);
  });
}, "se_AttributeValueList");
var se_AttributeValueUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    Action: [],
    Value: /* @__PURE__ */ __name((_) => se_AttributeValue(_, context), "Value")
  });
}, "se_AttributeValueUpdate");
var se_AutoScalingPolicyUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    PolicyName: [],
    TargetTrackingScalingPolicyConfiguration: /* @__PURE__ */ __name((_) => se_AutoScalingTargetTrackingScalingPolicyConfigurationUpdate(_, context), "TargetTrackingScalingPolicyConfiguration")
  });
}, "se_AutoScalingPolicyUpdate");
var se_AutoScalingSettingsUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AutoScalingDisabled: [],
    AutoScalingRoleArn: [],
    MaximumUnits: [],
    MinimumUnits: [],
    ScalingPolicyUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingPolicyUpdate(_, context), "ScalingPolicyUpdate")
  });
}, "se_AutoScalingSettingsUpdate");
var se_AutoScalingTargetTrackingScalingPolicyConfigurationUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    DisableScaleIn: [],
    ScaleInCooldown: [],
    ScaleOutCooldown: [],
    TargetValue: import_smithy_client.serializeFloat
  });
}, "se_AutoScalingTargetTrackingScalingPolicyConfigurationUpdate");
var se_BatchExecuteStatementInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ReturnConsumedCapacity: [],
    Statements: /* @__PURE__ */ __name((_) => se_PartiQLBatchRequest(_, context), "Statements")
  });
}, "se_BatchExecuteStatementInput");
var se_BatchGetItemInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    RequestItems: /* @__PURE__ */ __name((_) => se_BatchGetRequestMap(_, context), "RequestItems"),
    ReturnConsumedCapacity: []
  });
}, "se_BatchGetItemInput");
var se_BatchGetRequestMap = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_KeysAndAttributes(value, context);
    return acc;
  }, {});
}, "se_BatchGetRequestMap");
var se_BatchStatementRequest = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConsistentRead: [],
    Parameters: /* @__PURE__ */ __name((_) => se_PreparedStatementParameters(_, context), "Parameters"),
    ReturnValuesOnConditionCheckFailure: [],
    Statement: []
  });
}, "se_BatchStatementRequest");
var se_BatchWriteItemInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    RequestItems: /* @__PURE__ */ __name((_) => se_BatchWriteItemRequestMap(_, context), "RequestItems"),
    ReturnConsumedCapacity: [],
    ReturnItemCollectionMetrics: []
  });
}, "se_BatchWriteItemInput");
var se_BatchWriteItemRequestMap = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_WriteRequests(value, context);
    return acc;
  }, {});
}, "se_BatchWriteItemRequestMap");
var se_BinarySetAttributeValue = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return context.base64Encoder(entry);
  });
}, "se_BinarySetAttributeValue");
var se_Condition = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributeValueList: /* @__PURE__ */ __name((_) => se_AttributeValueList(_, context), "AttributeValueList"),
    ComparisonOperator: []
  });
}, "se_Condition");
var se_ConditionCheck = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionExpression: [],
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ReturnValuesOnConditionCheckFailure: [],
    TableName: []
  });
}, "se_ConditionCheck");
var se_Delete = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionExpression: [],
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ReturnValuesOnConditionCheckFailure: [],
    TableName: []
  });
}, "se_Delete");
var se_DeleteItemInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionExpression: [],
    ConditionalOperator: [],
    Expected: /* @__PURE__ */ __name((_) => se_ExpectedAttributeMap(_, context), "Expected"),
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ReturnConsumedCapacity: [],
    ReturnItemCollectionMetrics: [],
    ReturnValues: [],
    ReturnValuesOnConditionCheckFailure: [],
    TableName: []
  });
}, "se_DeleteItemInput");
var se_DeleteRequest = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key")
  });
}, "se_DeleteRequest");
var se_ExecuteStatementInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConsistentRead: [],
    Limit: [],
    NextToken: [],
    Parameters: /* @__PURE__ */ __name((_) => se_PreparedStatementParameters(_, context), "Parameters"),
    ReturnConsumedCapacity: [],
    ReturnValuesOnConditionCheckFailure: [],
    Statement: []
  });
}, "se_ExecuteStatementInput");
var se_ExecuteTransactionInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ClientRequestToken: [true, (_) => _ ?? (0, import_uuid.v4)()],
    ReturnConsumedCapacity: [],
    TransactStatements: /* @__PURE__ */ __name((_) => se_ParameterizedStatements(_, context), "TransactStatements")
  });
}, "se_ExecuteTransactionInput");
var se_ExpectedAttributeMap = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_ExpectedAttributeValue(value, context);
    return acc;
  }, {});
}, "se_ExpectedAttributeMap");
var se_ExpectedAttributeValue = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributeValueList: /* @__PURE__ */ __name((_) => se_AttributeValueList(_, context), "AttributeValueList"),
    ComparisonOperator: [],
    Exists: [],
    Value: /* @__PURE__ */ __name((_) => se_AttributeValue(_, context), "Value")
  });
}, "se_ExpectedAttributeValue");
var se_ExportTableToPointInTimeInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ClientToken: [true, (_) => _ ?? (0, import_uuid.v4)()],
    ExportFormat: [],
    ExportTime: /* @__PURE__ */ __name((_) => _.getTime() / 1e3, "ExportTime"),
    ExportType: [],
    IncrementalExportSpecification: /* @__PURE__ */ __name((_) => se_IncrementalExportSpecification(_, context), "IncrementalExportSpecification"),
    S3Bucket: [],
    S3BucketOwner: [],
    S3Prefix: [],
    S3SseAlgorithm: [],
    S3SseKmsKeyId: [],
    TableArn: []
  });
}, "se_ExportTableToPointInTimeInput");
var se_ExpressionAttributeValueMap = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_AttributeValue(value, context);
    return acc;
  }, {});
}, "se_ExpressionAttributeValueMap");
var se_FilterConditionMap = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_Condition(value, context);
    return acc;
  }, {});
}, "se_FilterConditionMap");
var se_Get = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ExpressionAttributeNames: import_smithy_client._json,
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ProjectionExpression: [],
    TableName: []
  });
}, "se_Get");
var se_GetItemInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributesToGet: import_smithy_client._json,
    ConsistentRead: [],
    ExpressionAttributeNames: import_smithy_client._json,
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ProjectionExpression: [],
    ReturnConsumedCapacity: [],
    TableName: []
  });
}, "se_GetItemInput");
var se_GlobalSecondaryIndexAutoScalingUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    IndexName: [],
    ProvisionedWriteCapacityAutoScalingUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ProvisionedWriteCapacityAutoScalingUpdate")
  });
}, "se_GlobalSecondaryIndexAutoScalingUpdate");
var se_GlobalSecondaryIndexAutoScalingUpdateList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_GlobalSecondaryIndexAutoScalingUpdate(entry, context);
  });
}, "se_GlobalSecondaryIndexAutoScalingUpdateList");
var se_GlobalTableGlobalSecondaryIndexSettingsUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    IndexName: [],
    ProvisionedWriteCapacityAutoScalingSettingsUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ProvisionedWriteCapacityAutoScalingSettingsUpdate"),
    ProvisionedWriteCapacityUnits: []
  });
}, "se_GlobalTableGlobalSecondaryIndexSettingsUpdate");
var se_GlobalTableGlobalSecondaryIndexSettingsUpdateList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_GlobalTableGlobalSecondaryIndexSettingsUpdate(entry, context);
  });
}, "se_GlobalTableGlobalSecondaryIndexSettingsUpdateList");
var se_ImportTableInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ClientToken: [true, (_) => _ ?? (0, import_uuid.v4)()],
    InputCompressionType: [],
    InputFormat: [],
    InputFormatOptions: import_smithy_client._json,
    S3BucketSource: import_smithy_client._json,
    TableCreationParameters: import_smithy_client._json
  });
}, "se_ImportTableInput");
var se_IncrementalExportSpecification = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ExportFromTime: /* @__PURE__ */ __name((_) => _.getTime() / 1e3, "ExportFromTime"),
    ExportToTime: /* @__PURE__ */ __name((_) => _.getTime() / 1e3, "ExportToTime"),
    ExportViewType: []
  });
}, "se_IncrementalExportSpecification");
var se_Key = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_AttributeValue(value, context);
    return acc;
  }, {});
}, "se_Key");
var se_KeyConditions = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_Condition(value, context);
    return acc;
  }, {});
}, "se_KeyConditions");
var se_KeyList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_Key(entry, context);
  });
}, "se_KeyList");
var se_KeysAndAttributes = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributesToGet: import_smithy_client._json,
    ConsistentRead: [],
    ExpressionAttributeNames: import_smithy_client._json,
    Keys: /* @__PURE__ */ __name((_) => se_KeyList(_, context), "Keys"),
    ProjectionExpression: []
  });
}, "se_KeysAndAttributes");
var se_ListAttributeValue = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_AttributeValue(entry, context);
  });
}, "se_ListAttributeValue");
var se_ListBackupsInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    BackupType: [],
    ExclusiveStartBackupArn: [],
    Limit: [],
    TableName: [],
    TimeRangeLowerBound: /* @__PURE__ */ __name((_) => _.getTime() / 1e3, "TimeRangeLowerBound"),
    TimeRangeUpperBound: /* @__PURE__ */ __name((_) => _.getTime() / 1e3, "TimeRangeUpperBound")
  });
}, "se_ListBackupsInput");
var se_MapAttributeValue = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_AttributeValue(value, context);
    return acc;
  }, {});
}, "se_MapAttributeValue");
var se_ParameterizedStatement = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    Parameters: /* @__PURE__ */ __name((_) => se_PreparedStatementParameters(_, context), "Parameters"),
    ReturnValuesOnConditionCheckFailure: [],
    Statement: []
  });
}, "se_ParameterizedStatement");
var se_ParameterizedStatements = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_ParameterizedStatement(entry, context);
  });
}, "se_ParameterizedStatements");
var se_PartiQLBatchRequest = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_BatchStatementRequest(entry, context);
  });
}, "se_PartiQLBatchRequest");
var se_PreparedStatementParameters = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_AttributeValue(entry, context);
  });
}, "se_PreparedStatementParameters");
var se_Put = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionExpression: [],
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Item: /* @__PURE__ */ __name((_) => se_PutItemInputAttributeMap(_, context), "Item"),
    ReturnValuesOnConditionCheckFailure: [],
    TableName: []
  });
}, "se_Put");
var se_PutItemInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionExpression: [],
    ConditionalOperator: [],
    Expected: /* @__PURE__ */ __name((_) => se_ExpectedAttributeMap(_, context), "Expected"),
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Item: /* @__PURE__ */ __name((_) => se_PutItemInputAttributeMap(_, context), "Item"),
    ReturnConsumedCapacity: [],
    ReturnItemCollectionMetrics: [],
    ReturnValues: [],
    ReturnValuesOnConditionCheckFailure: [],
    TableName: []
  });
}, "se_PutItemInput");
var se_PutItemInputAttributeMap = /* @__PURE__ */ __name((input, context) => {
  return Object.entries(input).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = se_AttributeValue(value, context);
    return acc;
  }, {});
}, "se_PutItemInputAttributeMap");
var se_PutRequest = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    Item: /* @__PURE__ */ __name((_) => se_PutItemInputAttributeMap(_, context), "Item")
  });
}, "se_PutRequest");
var se_QueryInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributesToGet: import_smithy_client._json,
    ConditionalOperator: [],
    ConsistentRead: [],
    ExclusiveStartKey: /* @__PURE__ */ __name((_) => se_Key(_, context), "ExclusiveStartKey"),
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    FilterExpression: [],
    IndexName: [],
    KeyConditionExpression: [],
    KeyConditions: /* @__PURE__ */ __name((_) => se_KeyConditions(_, context), "KeyConditions"),
    Limit: [],
    ProjectionExpression: [],
    QueryFilter: /* @__PURE__ */ __name((_) => se_FilterConditionMap(_, context), "QueryFilter"),
    ReturnConsumedCapacity: [],
    ScanIndexForward: [],
    Select: [],
    TableName: []
  });
}, "se_QueryInput");
var se_ReplicaAutoScalingUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    RegionName: [],
    ReplicaGlobalSecondaryIndexUpdates: /* @__PURE__ */ __name((_) => se_ReplicaGlobalSecondaryIndexAutoScalingUpdateList(_, context), "ReplicaGlobalSecondaryIndexUpdates"),
    ReplicaProvisionedReadCapacityAutoScalingUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ReplicaProvisionedReadCapacityAutoScalingUpdate")
  });
}, "se_ReplicaAutoScalingUpdate");
var se_ReplicaAutoScalingUpdateList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_ReplicaAutoScalingUpdate(entry, context);
  });
}, "se_ReplicaAutoScalingUpdateList");
var se_ReplicaGlobalSecondaryIndexAutoScalingUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    IndexName: [],
    ProvisionedReadCapacityAutoScalingUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ProvisionedReadCapacityAutoScalingUpdate")
  });
}, "se_ReplicaGlobalSecondaryIndexAutoScalingUpdate");
var se_ReplicaGlobalSecondaryIndexAutoScalingUpdateList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_ReplicaGlobalSecondaryIndexAutoScalingUpdate(entry, context);
  });
}, "se_ReplicaGlobalSecondaryIndexAutoScalingUpdateList");
var se_ReplicaGlobalSecondaryIndexSettingsUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    IndexName: [],
    ProvisionedReadCapacityAutoScalingSettingsUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ProvisionedReadCapacityAutoScalingSettingsUpdate"),
    ProvisionedReadCapacityUnits: []
  });
}, "se_ReplicaGlobalSecondaryIndexSettingsUpdate");
var se_ReplicaGlobalSecondaryIndexSettingsUpdateList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_ReplicaGlobalSecondaryIndexSettingsUpdate(entry, context);
  });
}, "se_ReplicaGlobalSecondaryIndexSettingsUpdateList");
var se_ReplicaSettingsUpdate = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    RegionName: [],
    ReplicaGlobalSecondaryIndexSettingsUpdate: /* @__PURE__ */ __name((_) => se_ReplicaGlobalSecondaryIndexSettingsUpdateList(_, context), "ReplicaGlobalSecondaryIndexSettingsUpdate"),
    ReplicaProvisionedReadCapacityAutoScalingSettingsUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ReplicaProvisionedReadCapacityAutoScalingSettingsUpdate"),
    ReplicaProvisionedReadCapacityUnits: [],
    ReplicaTableClass: []
  });
}, "se_ReplicaSettingsUpdate");
var se_ReplicaSettingsUpdateList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_ReplicaSettingsUpdate(entry, context);
  });
}, "se_ReplicaSettingsUpdateList");
var se_RestoreTableToPointInTimeInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    BillingModeOverride: [],
    GlobalSecondaryIndexOverride: import_smithy_client._json,
    LocalSecondaryIndexOverride: import_smithy_client._json,
    OnDemandThroughputOverride: import_smithy_client._json,
    ProvisionedThroughputOverride: import_smithy_client._json,
    RestoreDateTime: /* @__PURE__ */ __name((_) => _.getTime() / 1e3, "RestoreDateTime"),
    SSESpecificationOverride: import_smithy_client._json,
    SourceTableArn: [],
    SourceTableName: [],
    TargetTableName: [],
    UseLatestRestorableTime: []
  });
}, "se_RestoreTableToPointInTimeInput");
var se_ScanInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributesToGet: import_smithy_client._json,
    ConditionalOperator: [],
    ConsistentRead: [],
    ExclusiveStartKey: /* @__PURE__ */ __name((_) => se_Key(_, context), "ExclusiveStartKey"),
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    FilterExpression: [],
    IndexName: [],
    Limit: [],
    ProjectionExpression: [],
    ReturnConsumedCapacity: [],
    ScanFilter: /* @__PURE__ */ __name((_) => se_FilterConditionMap(_, context), "ScanFilter"),
    Segment: [],
    Select: [],
    TableName: [],
    TotalSegments: []
  });
}, "se_ScanInput");
var se_TransactGetItem = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    Get: /* @__PURE__ */ __name((_) => se_Get(_, context), "Get")
  });
}, "se_TransactGetItem");
var se_TransactGetItemList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_TransactGetItem(entry, context);
  });
}, "se_TransactGetItemList");
var se_TransactGetItemsInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ReturnConsumedCapacity: [],
    TransactItems: /* @__PURE__ */ __name((_) => se_TransactGetItemList(_, context), "TransactItems")
  });
}, "se_TransactGetItemsInput");
var se_TransactWriteItem = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionCheck: /* @__PURE__ */ __name((_) => se_ConditionCheck(_, context), "ConditionCheck"),
    Delete: /* @__PURE__ */ __name((_) => se_Delete(_, context), "Delete"),
    Put: /* @__PURE__ */ __name((_) => se_Put(_, context), "Put"),
    Update: /* @__PURE__ */ __name((_) => se_Update(_, context), "Update")
  });
}, "se_TransactWriteItem");
var se_TransactWriteItemList = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_TransactWriteItem(entry, context);
  });
}, "se_TransactWriteItemList");
var se_TransactWriteItemsInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ClientRequestToken: [true, (_) => _ ?? (0, import_uuid.v4)()],
    ReturnConsumedCapacity: [],
    ReturnItemCollectionMetrics: [],
    TransactItems: /* @__PURE__ */ __name((_) => se_TransactWriteItemList(_, context), "TransactItems")
  });
}, "se_TransactWriteItemsInput");
var se_Update = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    ConditionExpression: [],
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ReturnValuesOnConditionCheckFailure: [],
    TableName: [],
    UpdateExpression: []
  });
}, "se_Update");
var se_UpdateGlobalTableSettingsInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    GlobalTableBillingMode: [],
    GlobalTableGlobalSecondaryIndexSettingsUpdate: /* @__PURE__ */ __name((_) => se_GlobalTableGlobalSecondaryIndexSettingsUpdateList(_, context), "GlobalTableGlobalSecondaryIndexSettingsUpdate"),
    GlobalTableName: [],
    GlobalTableProvisionedWriteCapacityAutoScalingSettingsUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "GlobalTableProvisionedWriteCapacityAutoScalingSettingsUpdate"),
    GlobalTableProvisionedWriteCapacityUnits: [],
    ReplicaSettingsUpdate: /* @__PURE__ */ __name((_) => se_ReplicaSettingsUpdateList(_, context), "ReplicaSettingsUpdate")
  });
}, "se_UpdateGlobalTableSettingsInput");
var se_UpdateItemInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    AttributeUpdates: /* @__PURE__ */ __name((_) => se_AttributeUpdates(_, context), "AttributeUpdates"),
    ConditionExpression: [],
    ConditionalOperator: [],
    Expected: /* @__PURE__ */ __name((_) => se_ExpectedAttributeMap(_, context), "Expected"),
    ExpressionAttributeNames: import_smithy_client._json,
    ExpressionAttributeValues: /* @__PURE__ */ __name((_) => se_ExpressionAttributeValueMap(_, context), "ExpressionAttributeValues"),
    Key: /* @__PURE__ */ __name((_) => se_Key(_, context), "Key"),
    ReturnConsumedCapacity: [],
    ReturnItemCollectionMetrics: [],
    ReturnValues: [],
    ReturnValuesOnConditionCheckFailure: [],
    TableName: [],
    UpdateExpression: []
  });
}, "se_UpdateItemInput");
var se_UpdateTableReplicaAutoScalingInput = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    GlobalSecondaryIndexUpdates: /* @__PURE__ */ __name((_) => se_GlobalSecondaryIndexAutoScalingUpdateList(_, context), "GlobalSecondaryIndexUpdates"),
    ProvisionedWriteCapacityAutoScalingUpdate: /* @__PURE__ */ __name((_) => se_AutoScalingSettingsUpdate(_, context), "ProvisionedWriteCapacityAutoScalingUpdate"),
    ReplicaUpdates: /* @__PURE__ */ __name((_) => se_ReplicaAutoScalingUpdateList(_, context), "ReplicaUpdates"),
    TableName: []
  });
}, "se_UpdateTableReplicaAutoScalingInput");
var se_WriteRequest = /* @__PURE__ */ __name((input, context) => {
  return (0, import_smithy_client.take)(input, {
    DeleteRequest: /* @__PURE__ */ __name((_) => se_DeleteRequest(_, context), "DeleteRequest"),
    PutRequest: /* @__PURE__ */ __name((_) => se_PutRequest(_, context), "PutRequest")
  });
}, "se_WriteRequest");
var se_WriteRequests = /* @__PURE__ */ __name((input, context) => {
  return input.filter((e) => e != null).map((entry) => {
    return se_WriteRequest(entry, context);
  });
}, "se_WriteRequests");
var de_ArchivalSummary = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ArchivalBackupArn: import_smithy_client.expectString,
    ArchivalDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "ArchivalDateTime"),
    ArchivalReason: import_smithy_client.expectString
  });
}, "de_ArchivalSummary");
var de_AttributeMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_AttributeValue((0, import_core.awsExpectUnion)(value), context);
    return acc;
  }, {});
}, "de_AttributeMap");
var de_AttributeValue = /* @__PURE__ */ __name((output, context) => {
  if (output.B != null) {
    return {
      B: context.base64Decoder(output.B)
    };
  }
  if ((0, import_smithy_client.expectBoolean)(output.BOOL) !== void 0) {
    return { BOOL: (0, import_smithy_client.expectBoolean)(output.BOOL) };
  }
  if (output.BS != null) {
    return {
      BS: de_BinarySetAttributeValue(output.BS, context)
    };
  }
  if (output.L != null) {
    return {
      L: de_ListAttributeValue(output.L, context)
    };
  }
  if (output.M != null) {
    return {
      M: de_MapAttributeValue(output.M, context)
    };
  }
  if ((0, import_smithy_client.expectString)(output.N) !== void 0) {
    return { N: (0, import_smithy_client.expectString)(output.N) };
  }
  if (output.NS != null) {
    return {
      NS: (0, import_smithy_client._json)(output.NS)
    };
  }
  if ((0, import_smithy_client.expectBoolean)(output.NULL) !== void 0) {
    return { NULL: (0, import_smithy_client.expectBoolean)(output.NULL) };
  }
  if ((0, import_smithy_client.expectString)(output.S) !== void 0) {
    return { S: (0, import_smithy_client.expectString)(output.S) };
  }
  if (output.SS != null) {
    return {
      SS: (0, import_smithy_client._json)(output.SS)
    };
  }
  return { $unknown: Object.entries(output)[0] };
}, "de_AttributeValue");
var de_AutoScalingPolicyDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    PolicyName: import_smithy_client.expectString,
    TargetTrackingScalingPolicyConfiguration: /* @__PURE__ */ __name((_) => de_AutoScalingTargetTrackingScalingPolicyConfigurationDescription(_, context), "TargetTrackingScalingPolicyConfiguration")
  });
}, "de_AutoScalingPolicyDescription");
var de_AutoScalingPolicyDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_AutoScalingPolicyDescription(entry, context);
  });
  return retVal;
}, "de_AutoScalingPolicyDescriptionList");
var de_AutoScalingSettingsDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    AutoScalingDisabled: import_smithy_client.expectBoolean,
    AutoScalingRoleArn: import_smithy_client.expectString,
    MaximumUnits: import_smithy_client.expectLong,
    MinimumUnits: import_smithy_client.expectLong,
    ScalingPolicies: /* @__PURE__ */ __name((_) => de_AutoScalingPolicyDescriptionList(_, context), "ScalingPolicies")
  });
}, "de_AutoScalingSettingsDescription");
var de_AutoScalingTargetTrackingScalingPolicyConfigurationDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    DisableScaleIn: import_smithy_client.expectBoolean,
    ScaleInCooldown: import_smithy_client.expectInt32,
    ScaleOutCooldown: import_smithy_client.expectInt32,
    TargetValue: import_smithy_client.limitedParseDouble
  });
}, "de_AutoScalingTargetTrackingScalingPolicyConfigurationDescription");
var de_BackupDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupDetails: /* @__PURE__ */ __name((_) => de_BackupDetails(_, context), "BackupDetails"),
    SourceTableDetails: /* @__PURE__ */ __name((_) => de_SourceTableDetails(_, context), "SourceTableDetails"),
    SourceTableFeatureDetails: /* @__PURE__ */ __name((_) => de_SourceTableFeatureDetails(_, context), "SourceTableFeatureDetails")
  });
}, "de_BackupDescription");
var de_BackupDetails = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupArn: import_smithy_client.expectString,
    BackupCreationDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "BackupCreationDateTime"),
    BackupExpiryDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "BackupExpiryDateTime"),
    BackupName: import_smithy_client.expectString,
    BackupSizeBytes: import_smithy_client.expectLong,
    BackupStatus: import_smithy_client.expectString,
    BackupType: import_smithy_client.expectString
  });
}, "de_BackupDetails");
var de_BackupSummaries = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_BackupSummary(entry, context);
  });
  return retVal;
}, "de_BackupSummaries");
var de_BackupSummary = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupArn: import_smithy_client.expectString,
    BackupCreationDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "BackupCreationDateTime"),
    BackupExpiryDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "BackupExpiryDateTime"),
    BackupName: import_smithy_client.expectString,
    BackupSizeBytes: import_smithy_client.expectLong,
    BackupStatus: import_smithy_client.expectString,
    BackupType: import_smithy_client.expectString,
    TableArn: import_smithy_client.expectString,
    TableId: import_smithy_client.expectString,
    TableName: import_smithy_client.expectString
  });
}, "de_BackupSummary");
var de_BatchExecuteStatementOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacityMultiple(_, context), "ConsumedCapacity"),
    Responses: /* @__PURE__ */ __name((_) => de_PartiQLBatchResponse(_, context), "Responses")
  });
}, "de_BatchExecuteStatementOutput");
var de_BatchGetItemOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacityMultiple(_, context), "ConsumedCapacity"),
    Responses: /* @__PURE__ */ __name((_) => de_BatchGetResponseMap(_, context), "Responses"),
    UnprocessedKeys: /* @__PURE__ */ __name((_) => de_BatchGetRequestMap(_, context), "UnprocessedKeys")
  });
}, "de_BatchGetItemOutput");
var de_BatchGetRequestMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_KeysAndAttributes(value, context);
    return acc;
  }, {});
}, "de_BatchGetRequestMap");
var de_BatchGetResponseMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce(
    (acc, [key, value]) => {
      if (value === null) {
        return acc;
      }
      acc[key] = de_ItemList(value, context);
      return acc;
    },
    {}
  );
}, "de_BatchGetResponseMap");
var de_BatchStatementError = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Code: import_smithy_client.expectString,
    Item: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Item"),
    Message: import_smithy_client.expectString
  });
}, "de_BatchStatementError");
var de_BatchStatementResponse = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Error: /* @__PURE__ */ __name((_) => de_BatchStatementError(_, context), "Error"),
    Item: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Item"),
    TableName: import_smithy_client.expectString
  });
}, "de_BatchStatementResponse");
var de_BatchWriteItemOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacityMultiple(_, context), "ConsumedCapacity"),
    ItemCollectionMetrics: /* @__PURE__ */ __name((_) => de_ItemCollectionMetricsPerTable(_, context), "ItemCollectionMetrics"),
    UnprocessedItems: /* @__PURE__ */ __name((_) => de_BatchWriteItemRequestMap(_, context), "UnprocessedItems")
  });
}, "de_BatchWriteItemOutput");
var de_BatchWriteItemRequestMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_WriteRequests(value, context);
    return acc;
  }, {});
}, "de_BatchWriteItemRequestMap");
var de_BillingModeSummary = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BillingMode: import_smithy_client.expectString,
    LastUpdateToPayPerRequestDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "LastUpdateToPayPerRequestDateTime")
  });
}, "de_BillingModeSummary");
var de_BinarySetAttributeValue = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return context.base64Decoder(entry);
  });
  return retVal;
}, "de_BinarySetAttributeValue");
var de_CancellationReason = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Code: import_smithy_client.expectString,
    Item: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Item"),
    Message: import_smithy_client.expectString
  });
}, "de_CancellationReason");
var de_CancellationReasonList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_CancellationReason(entry, context);
  });
  return retVal;
}, "de_CancellationReasonList");
var de_Capacity = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    CapacityUnits: import_smithy_client.limitedParseDouble,
    ReadCapacityUnits: import_smithy_client.limitedParseDouble,
    WriteCapacityUnits: import_smithy_client.limitedParseDouble
  });
}, "de_Capacity");
var de_ConditionalCheckFailedException = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Item: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Item"),
    message: import_smithy_client.expectString
  });
}, "de_ConditionalCheckFailedException");
var de_ConsumedCapacity = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    CapacityUnits: import_smithy_client.limitedParseDouble,
    GlobalSecondaryIndexes: /* @__PURE__ */ __name((_) => de_SecondaryIndexesCapacityMap(_, context), "GlobalSecondaryIndexes"),
    LocalSecondaryIndexes: /* @__PURE__ */ __name((_) => de_SecondaryIndexesCapacityMap(_, context), "LocalSecondaryIndexes"),
    ReadCapacityUnits: import_smithy_client.limitedParseDouble,
    Table: /* @__PURE__ */ __name((_) => de_Capacity(_, context), "Table"),
    TableName: import_smithy_client.expectString,
    WriteCapacityUnits: import_smithy_client.limitedParseDouble
  });
}, "de_ConsumedCapacity");
var de_ConsumedCapacityMultiple = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ConsumedCapacity(entry, context);
  });
  return retVal;
}, "de_ConsumedCapacityMultiple");
var de_ContinuousBackupsDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ContinuousBackupsStatus: import_smithy_client.expectString,
    PointInTimeRecoveryDescription: /* @__PURE__ */ __name((_) => de_PointInTimeRecoveryDescription(_, context), "PointInTimeRecoveryDescription")
  });
}, "de_ContinuousBackupsDescription");
var de_CreateBackupOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupDetails: /* @__PURE__ */ __name((_) => de_BackupDetails(_, context), "BackupDetails")
  });
}, "de_CreateBackupOutput");
var de_CreateGlobalTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalTableDescription: /* @__PURE__ */ __name((_) => de_GlobalTableDescription(_, context), "GlobalTableDescription")
  });
}, "de_CreateGlobalTableOutput");
var de_CreateTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableDescription: /* @__PURE__ */ __name((_) => de_TableDescription(_, context), "TableDescription")
  });
}, "de_CreateTableOutput");
var de_DeleteBackupOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupDescription: /* @__PURE__ */ __name((_) => de_BackupDescription(_, context), "BackupDescription")
  });
}, "de_DeleteBackupOutput");
var de_DeleteItemOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Attributes: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Attributes"),
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    ItemCollectionMetrics: /* @__PURE__ */ __name((_) => de_ItemCollectionMetrics(_, context), "ItemCollectionMetrics")
  });
}, "de_DeleteItemOutput");
var de_DeleteRequest = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Key: /* @__PURE__ */ __name((_) => de_Key(_, context), "Key")
  });
}, "de_DeleteRequest");
var de_DeleteTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableDescription: /* @__PURE__ */ __name((_) => de_TableDescription(_, context), "TableDescription")
  });
}, "de_DeleteTableOutput");
var de_DescribeBackupOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupDescription: /* @__PURE__ */ __name((_) => de_BackupDescription(_, context), "BackupDescription")
  });
}, "de_DescribeBackupOutput");
var de_DescribeContinuousBackupsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ContinuousBackupsDescription: /* @__PURE__ */ __name((_) => de_ContinuousBackupsDescription(_, context), "ContinuousBackupsDescription")
  });
}, "de_DescribeContinuousBackupsOutput");
var de_DescribeContributorInsightsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ContributorInsightsRuleList: import_smithy_client._json,
    ContributorInsightsStatus: import_smithy_client.expectString,
    FailureException: import_smithy_client._json,
    IndexName: import_smithy_client.expectString,
    LastUpdateDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "LastUpdateDateTime"),
    TableName: import_smithy_client.expectString
  });
}, "de_DescribeContributorInsightsOutput");
var de_DescribeExportOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ExportDescription: /* @__PURE__ */ __name((_) => de_ExportDescription(_, context), "ExportDescription")
  });
}, "de_DescribeExportOutput");
var de_DescribeGlobalTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalTableDescription: /* @__PURE__ */ __name((_) => de_GlobalTableDescription(_, context), "GlobalTableDescription")
  });
}, "de_DescribeGlobalTableOutput");
var de_DescribeGlobalTableSettingsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalTableName: import_smithy_client.expectString,
    ReplicaSettings: /* @__PURE__ */ __name((_) => de_ReplicaSettingsDescriptionList(_, context), "ReplicaSettings")
  });
}, "de_DescribeGlobalTableSettingsOutput");
var de_DescribeImportOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ImportTableDescription: /* @__PURE__ */ __name((_) => de_ImportTableDescription(_, context), "ImportTableDescription")
  });
}, "de_DescribeImportOutput");
var de_DescribeTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Table: /* @__PURE__ */ __name((_) => de_TableDescription(_, context), "Table")
  });
}, "de_DescribeTableOutput");
var de_DescribeTableReplicaAutoScalingOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableAutoScalingDescription: /* @__PURE__ */ __name((_) => de_TableAutoScalingDescription(_, context), "TableAutoScalingDescription")
  });
}, "de_DescribeTableReplicaAutoScalingOutput");
var de_ExecuteStatementOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    Items: /* @__PURE__ */ __name((_) => de_ItemList(_, context), "Items"),
    LastEvaluatedKey: /* @__PURE__ */ __name((_) => de_Key(_, context), "LastEvaluatedKey"),
    NextToken: import_smithy_client.expectString
  });
}, "de_ExecuteStatementOutput");
var de_ExecuteTransactionOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacityMultiple(_, context), "ConsumedCapacity"),
    Responses: /* @__PURE__ */ __name((_) => de_ItemResponseList(_, context), "Responses")
  });
}, "de_ExecuteTransactionOutput");
var de_ExportDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BilledSizeBytes: import_smithy_client.expectLong,
    ClientToken: import_smithy_client.expectString,
    EndTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "EndTime"),
    ExportArn: import_smithy_client.expectString,
    ExportFormat: import_smithy_client.expectString,
    ExportManifest: import_smithy_client.expectString,
    ExportStatus: import_smithy_client.expectString,
    ExportTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "ExportTime"),
    ExportType: import_smithy_client.expectString,
    FailureCode: import_smithy_client.expectString,
    FailureMessage: import_smithy_client.expectString,
    IncrementalExportSpecification: /* @__PURE__ */ __name((_) => de_IncrementalExportSpecification(_, context), "IncrementalExportSpecification"),
    ItemCount: import_smithy_client.expectLong,
    S3Bucket: import_smithy_client.expectString,
    S3BucketOwner: import_smithy_client.expectString,
    S3Prefix: import_smithy_client.expectString,
    S3SseAlgorithm: import_smithy_client.expectString,
    S3SseKmsKeyId: import_smithy_client.expectString,
    StartTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "StartTime"),
    TableArn: import_smithy_client.expectString,
    TableId: import_smithy_client.expectString
  });
}, "de_ExportDescription");
var de_ExportTableToPointInTimeOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ExportDescription: /* @__PURE__ */ __name((_) => de_ExportDescription(_, context), "ExportDescription")
  });
}, "de_ExportTableToPointInTimeOutput");
var de_GetItemOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    Item: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Item")
  });
}, "de_GetItemOutput");
var de_GlobalSecondaryIndexDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Backfilling: import_smithy_client.expectBoolean,
    IndexArn: import_smithy_client.expectString,
    IndexName: import_smithy_client.expectString,
    IndexSizeBytes: import_smithy_client.expectLong,
    IndexStatus: import_smithy_client.expectString,
    ItemCount: import_smithy_client.expectLong,
    KeySchema: import_smithy_client._json,
    OnDemandThroughput: import_smithy_client._json,
    Projection: import_smithy_client._json,
    ProvisionedThroughput: /* @__PURE__ */ __name((_) => de_ProvisionedThroughputDescription(_, context), "ProvisionedThroughput"),
    WarmThroughput: import_smithy_client._json
  });
}, "de_GlobalSecondaryIndexDescription");
var de_GlobalSecondaryIndexDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_GlobalSecondaryIndexDescription(entry, context);
  });
  return retVal;
}, "de_GlobalSecondaryIndexDescriptionList");
var de_GlobalTableDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    CreationDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "CreationDateTime"),
    GlobalTableArn: import_smithy_client.expectString,
    GlobalTableName: import_smithy_client.expectString,
    GlobalTableStatus: import_smithy_client.expectString,
    ReplicationGroup: /* @__PURE__ */ __name((_) => de_ReplicaDescriptionList(_, context), "ReplicationGroup")
  });
}, "de_GlobalTableDescription");
var de_ImportSummary = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    CloudWatchLogGroupArn: import_smithy_client.expectString,
    EndTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "EndTime"),
    ImportArn: import_smithy_client.expectString,
    ImportStatus: import_smithy_client.expectString,
    InputFormat: import_smithy_client.expectString,
    S3BucketSource: import_smithy_client._json,
    StartTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "StartTime"),
    TableArn: import_smithy_client.expectString
  });
}, "de_ImportSummary");
var de_ImportSummaryList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ImportSummary(entry, context);
  });
  return retVal;
}, "de_ImportSummaryList");
var de_ImportTableDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ClientToken: import_smithy_client.expectString,
    CloudWatchLogGroupArn: import_smithy_client.expectString,
    EndTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "EndTime"),
    ErrorCount: import_smithy_client.expectLong,
    FailureCode: import_smithy_client.expectString,
    FailureMessage: import_smithy_client.expectString,
    ImportArn: import_smithy_client.expectString,
    ImportStatus: import_smithy_client.expectString,
    ImportedItemCount: import_smithy_client.expectLong,
    InputCompressionType: import_smithy_client.expectString,
    InputFormat: import_smithy_client.expectString,
    InputFormatOptions: import_smithy_client._json,
    ProcessedItemCount: import_smithy_client.expectLong,
    ProcessedSizeBytes: import_smithy_client.expectLong,
    S3BucketSource: import_smithy_client._json,
    StartTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "StartTime"),
    TableArn: import_smithy_client.expectString,
    TableCreationParameters: import_smithy_client._json,
    TableId: import_smithy_client.expectString
  });
}, "de_ImportTableDescription");
var de_ImportTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ImportTableDescription: /* @__PURE__ */ __name((_) => de_ImportTableDescription(_, context), "ImportTableDescription")
  });
}, "de_ImportTableOutput");
var de_IncrementalExportSpecification = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ExportFromTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "ExportFromTime"),
    ExportToTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "ExportToTime"),
    ExportViewType: import_smithy_client.expectString
  });
}, "de_IncrementalExportSpecification");
var de_ItemCollectionKeyAttributeMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_AttributeValue((0, import_core.awsExpectUnion)(value), context);
    return acc;
  }, {});
}, "de_ItemCollectionKeyAttributeMap");
var de_ItemCollectionMetrics = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ItemCollectionKey: /* @__PURE__ */ __name((_) => de_ItemCollectionKeyAttributeMap(_, context), "ItemCollectionKey"),
    SizeEstimateRangeGB: /* @__PURE__ */ __name((_) => de_ItemCollectionSizeEstimateRange(_, context), "SizeEstimateRangeGB")
  });
}, "de_ItemCollectionMetrics");
var de_ItemCollectionMetricsMultiple = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ItemCollectionMetrics(entry, context);
  });
  return retVal;
}, "de_ItemCollectionMetricsMultiple");
var de_ItemCollectionMetricsPerTable = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_ItemCollectionMetricsMultiple(value, context);
    return acc;
  }, {});
}, "de_ItemCollectionMetricsPerTable");
var de_ItemCollectionSizeEstimateRange = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return (0, import_smithy_client.limitedParseDouble)(entry);
  });
  return retVal;
}, "de_ItemCollectionSizeEstimateRange");
var de_ItemList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_AttributeMap(entry, context);
  });
  return retVal;
}, "de_ItemList");
var de_ItemResponse = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Item: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Item")
  });
}, "de_ItemResponse");
var de_ItemResponseList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ItemResponse(entry, context);
  });
  return retVal;
}, "de_ItemResponseList");
var de_Key = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_AttributeValue((0, import_core.awsExpectUnion)(value), context);
    return acc;
  }, {});
}, "de_Key");
var de_KeyList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_Key(entry, context);
  });
  return retVal;
}, "de_KeyList");
var de_KeysAndAttributes = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    AttributesToGet: import_smithy_client._json,
    ConsistentRead: import_smithy_client.expectBoolean,
    ExpressionAttributeNames: import_smithy_client._json,
    Keys: /* @__PURE__ */ __name((_) => de_KeyList(_, context), "Keys"),
    ProjectionExpression: import_smithy_client.expectString
  });
}, "de_KeysAndAttributes");
var de_ListAttributeValue = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_AttributeValue((0, import_core.awsExpectUnion)(entry), context);
  });
  return retVal;
}, "de_ListAttributeValue");
var de_ListBackupsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BackupSummaries: /* @__PURE__ */ __name((_) => de_BackupSummaries(_, context), "BackupSummaries"),
    LastEvaluatedBackupArn: import_smithy_client.expectString
  });
}, "de_ListBackupsOutput");
var de_ListImportsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ImportSummaryList: /* @__PURE__ */ __name((_) => de_ImportSummaryList(_, context), "ImportSummaryList"),
    NextToken: import_smithy_client.expectString
  });
}, "de_ListImportsOutput");
var de_MapAttributeValue = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_AttributeValue((0, import_core.awsExpectUnion)(value), context);
    return acc;
  }, {});
}, "de_MapAttributeValue");
var de_PartiQLBatchResponse = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_BatchStatementResponse(entry, context);
  });
  return retVal;
}, "de_PartiQLBatchResponse");
var de_PointInTimeRecoveryDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    EarliestRestorableDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "EarliestRestorableDateTime"),
    LatestRestorableDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "LatestRestorableDateTime"),
    PointInTimeRecoveryStatus: import_smithy_client.expectString,
    RecoveryPeriodInDays: import_smithy_client.expectInt32
  });
}, "de_PointInTimeRecoveryDescription");
var de_ProvisionedThroughputDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    LastDecreaseDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "LastDecreaseDateTime"),
    LastIncreaseDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "LastIncreaseDateTime"),
    NumberOfDecreasesToday: import_smithy_client.expectLong,
    ReadCapacityUnits: import_smithy_client.expectLong,
    WriteCapacityUnits: import_smithy_client.expectLong
  });
}, "de_ProvisionedThroughputDescription");
var de_PutItemInputAttributeMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_AttributeValue((0, import_core.awsExpectUnion)(value), context);
    return acc;
  }, {});
}, "de_PutItemInputAttributeMap");
var de_PutItemOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Attributes: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Attributes"),
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    ItemCollectionMetrics: /* @__PURE__ */ __name((_) => de_ItemCollectionMetrics(_, context), "ItemCollectionMetrics")
  });
}, "de_PutItemOutput");
var de_PutRequest = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Item: /* @__PURE__ */ __name((_) => de_PutItemInputAttributeMap(_, context), "Item")
  });
}, "de_PutRequest");
var de_QueryOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    Count: import_smithy_client.expectInt32,
    Items: /* @__PURE__ */ __name((_) => de_ItemList(_, context), "Items"),
    LastEvaluatedKey: /* @__PURE__ */ __name((_) => de_Key(_, context), "LastEvaluatedKey"),
    ScannedCount: import_smithy_client.expectInt32
  });
}, "de_QueryOutput");
var de_ReplicaAutoScalingDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalSecondaryIndexes: /* @__PURE__ */ __name((_) => de_ReplicaGlobalSecondaryIndexAutoScalingDescriptionList(_, context), "GlobalSecondaryIndexes"),
    RegionName: import_smithy_client.expectString,
    ReplicaProvisionedReadCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ReplicaProvisionedReadCapacityAutoScalingSettings"),
    ReplicaProvisionedWriteCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ReplicaProvisionedWriteCapacityAutoScalingSettings"),
    ReplicaStatus: import_smithy_client.expectString
  });
}, "de_ReplicaAutoScalingDescription");
var de_ReplicaAutoScalingDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ReplicaAutoScalingDescription(entry, context);
  });
  return retVal;
}, "de_ReplicaAutoScalingDescriptionList");
var de_ReplicaDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalSecondaryIndexes: import_smithy_client._json,
    KMSMasterKeyId: import_smithy_client.expectString,
    OnDemandThroughputOverride: import_smithy_client._json,
    ProvisionedThroughputOverride: import_smithy_client._json,
    RegionName: import_smithy_client.expectString,
    ReplicaInaccessibleDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "ReplicaInaccessibleDateTime"),
    ReplicaStatus: import_smithy_client.expectString,
    ReplicaStatusDescription: import_smithy_client.expectString,
    ReplicaStatusPercentProgress: import_smithy_client.expectString,
    ReplicaTableClassSummary: /* @__PURE__ */ __name((_) => de_TableClassSummary(_, context), "ReplicaTableClassSummary"),
    WarmThroughput: import_smithy_client._json
  });
}, "de_ReplicaDescription");
var de_ReplicaDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ReplicaDescription(entry, context);
  });
  return retVal;
}, "de_ReplicaDescriptionList");
var de_ReplicaGlobalSecondaryIndexAutoScalingDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    IndexName: import_smithy_client.expectString,
    IndexStatus: import_smithy_client.expectString,
    ProvisionedReadCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ProvisionedReadCapacityAutoScalingSettings"),
    ProvisionedWriteCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ProvisionedWriteCapacityAutoScalingSettings")
  });
}, "de_ReplicaGlobalSecondaryIndexAutoScalingDescription");
var de_ReplicaGlobalSecondaryIndexAutoScalingDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ReplicaGlobalSecondaryIndexAutoScalingDescription(entry, context);
  });
  return retVal;
}, "de_ReplicaGlobalSecondaryIndexAutoScalingDescriptionList");
var de_ReplicaGlobalSecondaryIndexSettingsDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    IndexName: import_smithy_client.expectString,
    IndexStatus: import_smithy_client.expectString,
    ProvisionedReadCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ProvisionedReadCapacityAutoScalingSettings"),
    ProvisionedReadCapacityUnits: import_smithy_client.expectLong,
    ProvisionedWriteCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ProvisionedWriteCapacityAutoScalingSettings"),
    ProvisionedWriteCapacityUnits: import_smithy_client.expectLong
  });
}, "de_ReplicaGlobalSecondaryIndexSettingsDescription");
var de_ReplicaGlobalSecondaryIndexSettingsDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ReplicaGlobalSecondaryIndexSettingsDescription(entry, context);
  });
  return retVal;
}, "de_ReplicaGlobalSecondaryIndexSettingsDescriptionList");
var de_ReplicaSettingsDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    RegionName: import_smithy_client.expectString,
    ReplicaBillingModeSummary: /* @__PURE__ */ __name((_) => de_BillingModeSummary(_, context), "ReplicaBillingModeSummary"),
    ReplicaGlobalSecondaryIndexSettings: /* @__PURE__ */ __name((_) => de_ReplicaGlobalSecondaryIndexSettingsDescriptionList(_, context), "ReplicaGlobalSecondaryIndexSettings"),
    ReplicaProvisionedReadCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ReplicaProvisionedReadCapacityAutoScalingSettings"),
    ReplicaProvisionedReadCapacityUnits: import_smithy_client.expectLong,
    ReplicaProvisionedWriteCapacityAutoScalingSettings: /* @__PURE__ */ __name((_) => de_AutoScalingSettingsDescription(_, context), "ReplicaProvisionedWriteCapacityAutoScalingSettings"),
    ReplicaProvisionedWriteCapacityUnits: import_smithy_client.expectLong,
    ReplicaStatus: import_smithy_client.expectString,
    ReplicaTableClassSummary: /* @__PURE__ */ __name((_) => de_TableClassSummary(_, context), "ReplicaTableClassSummary")
  });
}, "de_ReplicaSettingsDescription");
var de_ReplicaSettingsDescriptionList = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_ReplicaSettingsDescription(entry, context);
  });
  return retVal;
}, "de_ReplicaSettingsDescriptionList");
var de_RestoreSummary = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    RestoreDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "RestoreDateTime"),
    RestoreInProgress: import_smithy_client.expectBoolean,
    SourceBackupArn: import_smithy_client.expectString,
    SourceTableArn: import_smithy_client.expectString
  });
}, "de_RestoreSummary");
var de_RestoreTableFromBackupOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableDescription: /* @__PURE__ */ __name((_) => de_TableDescription(_, context), "TableDescription")
  });
}, "de_RestoreTableFromBackupOutput");
var de_RestoreTableToPointInTimeOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableDescription: /* @__PURE__ */ __name((_) => de_TableDescription(_, context), "TableDescription")
  });
}, "de_RestoreTableToPointInTimeOutput");
var de_ScanOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    Count: import_smithy_client.expectInt32,
    Items: /* @__PURE__ */ __name((_) => de_ItemList(_, context), "Items"),
    LastEvaluatedKey: /* @__PURE__ */ __name((_) => de_Key(_, context), "LastEvaluatedKey"),
    ScannedCount: import_smithy_client.expectInt32
  });
}, "de_ScanOutput");
var de_SecondaryIndexesCapacityMap = /* @__PURE__ */ __name((output, context) => {
  return Object.entries(output).reduce((acc, [key, value]) => {
    if (value === null) {
      return acc;
    }
    acc[key] = de_Capacity(value, context);
    return acc;
  }, {});
}, "de_SecondaryIndexesCapacityMap");
var de_SourceTableDetails = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    BillingMode: import_smithy_client.expectString,
    ItemCount: import_smithy_client.expectLong,
    KeySchema: import_smithy_client._json,
    OnDemandThroughput: import_smithy_client._json,
    ProvisionedThroughput: import_smithy_client._json,
    TableArn: import_smithy_client.expectString,
    TableCreationDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "TableCreationDateTime"),
    TableId: import_smithy_client.expectString,
    TableName: import_smithy_client.expectString,
    TableSizeBytes: import_smithy_client.expectLong
  });
}, "de_SourceTableDetails");
var de_SourceTableFeatureDetails = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalSecondaryIndexes: import_smithy_client._json,
    LocalSecondaryIndexes: import_smithy_client._json,
    SSEDescription: /* @__PURE__ */ __name((_) => de_SSEDescription(_, context), "SSEDescription"),
    StreamDescription: import_smithy_client._json,
    TimeToLiveDescription: import_smithy_client._json
  });
}, "de_SourceTableFeatureDetails");
var de_SSEDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    InaccessibleEncryptionDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "InaccessibleEncryptionDateTime"),
    KMSMasterKeyArn: import_smithy_client.expectString,
    SSEType: import_smithy_client.expectString,
    Status: import_smithy_client.expectString
  });
}, "de_SSEDescription");
var de_TableAutoScalingDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Replicas: /* @__PURE__ */ __name((_) => de_ReplicaAutoScalingDescriptionList(_, context), "Replicas"),
    TableName: import_smithy_client.expectString,
    TableStatus: import_smithy_client.expectString
  });
}, "de_TableAutoScalingDescription");
var de_TableClassSummary = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    LastUpdateDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "LastUpdateDateTime"),
    TableClass: import_smithy_client.expectString
  });
}, "de_TableClassSummary");
var de_TableDescription = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ArchivalSummary: /* @__PURE__ */ __name((_) => de_ArchivalSummary(_, context), "ArchivalSummary"),
    AttributeDefinitions: import_smithy_client._json,
    BillingModeSummary: /* @__PURE__ */ __name((_) => de_BillingModeSummary(_, context), "BillingModeSummary"),
    CreationDateTime: /* @__PURE__ */ __name((_) => (0, import_smithy_client.expectNonNull)((0, import_smithy_client.parseEpochTimestamp)((0, import_smithy_client.expectNumber)(_))), "CreationDateTime"),
    DeletionProtectionEnabled: import_smithy_client.expectBoolean,
    GlobalSecondaryIndexes: /* @__PURE__ */ __name((_) => de_GlobalSecondaryIndexDescriptionList(_, context), "GlobalSecondaryIndexes"),
    GlobalTableVersion: import_smithy_client.expectString,
    GlobalTableWitnesses: import_smithy_client._json,
    ItemCount: import_smithy_client.expectLong,
    KeySchema: import_smithy_client._json,
    LatestStreamArn: import_smithy_client.expectString,
    LatestStreamLabel: import_smithy_client.expectString,
    LocalSecondaryIndexes: import_smithy_client._json,
    MultiRegionConsistency: import_smithy_client.expectString,
    OnDemandThroughput: import_smithy_client._json,
    ProvisionedThroughput: /* @__PURE__ */ __name((_) => de_ProvisionedThroughputDescription(_, context), "ProvisionedThroughput"),
    Replicas: /* @__PURE__ */ __name((_) => de_ReplicaDescriptionList(_, context), "Replicas"),
    RestoreSummary: /* @__PURE__ */ __name((_) => de_RestoreSummary(_, context), "RestoreSummary"),
    SSEDescription: /* @__PURE__ */ __name((_) => de_SSEDescription(_, context), "SSEDescription"),
    StreamSpecification: import_smithy_client._json,
    TableArn: import_smithy_client.expectString,
    TableClassSummary: /* @__PURE__ */ __name((_) => de_TableClassSummary(_, context), "TableClassSummary"),
    TableId: import_smithy_client.expectString,
    TableName: import_smithy_client.expectString,
    TableSizeBytes: import_smithy_client.expectLong,
    TableStatus: import_smithy_client.expectString,
    WarmThroughput: import_smithy_client._json
  });
}, "de_TableDescription");
var de_TransactGetItemsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacityMultiple(_, context), "ConsumedCapacity"),
    Responses: /* @__PURE__ */ __name((_) => de_ItemResponseList(_, context), "Responses")
  });
}, "de_TransactGetItemsOutput");
var de_TransactionCanceledException = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    CancellationReasons: /* @__PURE__ */ __name((_) => de_CancellationReasonList(_, context), "CancellationReasons"),
    Message: import_smithy_client.expectString
  });
}, "de_TransactionCanceledException");
var de_TransactWriteItemsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacityMultiple(_, context), "ConsumedCapacity"),
    ItemCollectionMetrics: /* @__PURE__ */ __name((_) => de_ItemCollectionMetricsPerTable(_, context), "ItemCollectionMetrics")
  });
}, "de_TransactWriteItemsOutput");
var de_UpdateContinuousBackupsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    ContinuousBackupsDescription: /* @__PURE__ */ __name((_) => de_ContinuousBackupsDescription(_, context), "ContinuousBackupsDescription")
  });
}, "de_UpdateContinuousBackupsOutput");
var de_UpdateGlobalTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalTableDescription: /* @__PURE__ */ __name((_) => de_GlobalTableDescription(_, context), "GlobalTableDescription")
  });
}, "de_UpdateGlobalTableOutput");
var de_UpdateGlobalTableSettingsOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    GlobalTableName: import_smithy_client.expectString,
    ReplicaSettings: /* @__PURE__ */ __name((_) => de_ReplicaSettingsDescriptionList(_, context), "ReplicaSettings")
  });
}, "de_UpdateGlobalTableSettingsOutput");
var de_UpdateItemOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    Attributes: /* @__PURE__ */ __name((_) => de_AttributeMap(_, context), "Attributes"),
    ConsumedCapacity: /* @__PURE__ */ __name((_) => de_ConsumedCapacity(_, context), "ConsumedCapacity"),
    ItemCollectionMetrics: /* @__PURE__ */ __name((_) => de_ItemCollectionMetrics(_, context), "ItemCollectionMetrics")
  });
}, "de_UpdateItemOutput");
var de_UpdateTableOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableDescription: /* @__PURE__ */ __name((_) => de_TableDescription(_, context), "TableDescription")
  });
}, "de_UpdateTableOutput");
var de_UpdateTableReplicaAutoScalingOutput = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    TableAutoScalingDescription: /* @__PURE__ */ __name((_) => de_TableAutoScalingDescription(_, context), "TableAutoScalingDescription")
  });
}, "de_UpdateTableReplicaAutoScalingOutput");
var de_WriteRequest = /* @__PURE__ */ __name((output, context) => {
  return (0, import_smithy_client.take)(output, {
    DeleteRequest: /* @__PURE__ */ __name((_) => de_DeleteRequest(_, context), "DeleteRequest"),
    PutRequest: /* @__PURE__ */ __name((_) => de_PutRequest(_, context), "PutRequest")
  });
}, "de_WriteRequest");
var de_WriteRequests = /* @__PURE__ */ __name((output, context) => {
  const retVal = (output || []).filter((e) => e != null).map((entry) => {
    return de_WriteRequest(entry, context);
  });
  return retVal;
}, "de_WriteRequests");
var deserializeMetadata = /* @__PURE__ */ __name((output) => ({
  httpStatusCode: output.statusCode,
  requestId: output.headers["x-amzn-requestid"] ?? output.headers["x-amzn-request-id"] ?? output.headers["x-amz-request-id"],
  extendedRequestId: output.headers["x-amz-id-2"],
  cfId: output.headers["x-amz-cf-id"]
}), "deserializeMetadata");
var throwDefaultError = (0, import_smithy_client.withBaseException)(DynamoDBServiceException);
var buildHttpRpcRequest = /* @__PURE__ */ __name(async (context, headers, path, resolvedHostname, body) => {
  const { hostname, protocol = "https", port, path: basePath } = await context.endpoint();
  const contents = {
    protocol,
    hostname,
    port,
    method: "POST",
    path: basePath.endsWith("/") ? basePath.slice(0, -1) + path : basePath + path,
    headers
  };
  if (resolvedHostname !== void 0) {
    contents.hostname = resolvedHostname;
  }
  if (body !== void 0) {
    contents.body = body;
  }
  return new import_protocol_http.HttpRequest(contents);
}, "buildHttpRpcRequest");
function sharedHeaders(operation) {
  return {
    "content-type": "application/x-amz-json-1.0",
    "x-amz-target": `DynamoDB_20120810.${operation}`
  };
}
__name(sharedHeaders, "sharedHeaders");

// src/commands/DescribeEndpointsCommand.ts
var DescribeEndpointsCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeEndpoints", {}).n("DynamoDBClient", "DescribeEndpointsCommand").f(void 0, void 0).ser(se_DescribeEndpointsCommand).de(de_DescribeEndpointsCommand).build() {
  static {
    __name(this, "DescribeEndpointsCommand");
  }
};

// src/DynamoDBClient.ts
var import_runtimeConfig = require("././runtimeConfig");

// src/runtimeExtensions.ts
var import_region_config_resolver = require("@aws-sdk/region-config-resolver");



// src/auth/httpAuthExtensionConfiguration.ts
var getHttpAuthExtensionConfiguration = /* @__PURE__ */ __name((runtimeConfig) => {
  const _httpAuthSchemes = runtimeConfig.httpAuthSchemes;
  let _httpAuthSchemeProvider = runtimeConfig.httpAuthSchemeProvider;
  let _credentials = runtimeConfig.credentials;
  return {
    setHttpAuthScheme(httpAuthScheme) {
      const index = _httpAuthSchemes.findIndex((scheme) => scheme.schemeId === httpAuthScheme.schemeId);
      if (index === -1) {
        _httpAuthSchemes.push(httpAuthScheme);
      } else {
        _httpAuthSchemes.splice(index, 1, httpAuthScheme);
      }
    },
    httpAuthSchemes() {
      return _httpAuthSchemes;
    },
    setHttpAuthSchemeProvider(httpAuthSchemeProvider) {
      _httpAuthSchemeProvider = httpAuthSchemeProvider;
    },
    httpAuthSchemeProvider() {
      return _httpAuthSchemeProvider;
    },
    setCredentials(credentials) {
      _credentials = credentials;
    },
    credentials() {
      return _credentials;
    }
  };
}, "getHttpAuthExtensionConfiguration");
var resolveHttpAuthRuntimeConfig = /* @__PURE__ */ __name((config) => {
  return {
    httpAuthSchemes: config.httpAuthSchemes(),
    httpAuthSchemeProvider: config.httpAuthSchemeProvider(),
    credentials: config.credentials()
  };
}, "resolveHttpAuthRuntimeConfig");

// src/runtimeExtensions.ts
var resolveRuntimeExtensions = /* @__PURE__ */ __name((runtimeConfig, extensions) => {
  const extensionConfiguration = Object.assign(
    (0, import_region_config_resolver.getAwsRegionExtensionConfiguration)(runtimeConfig),
    (0, import_smithy_client.getDefaultExtensionConfiguration)(runtimeConfig),
    (0, import_protocol_http.getHttpHandlerExtensionConfiguration)(runtimeConfig),
    getHttpAuthExtensionConfiguration(runtimeConfig)
  );
  extensions.forEach((extension) => extension.configure(extensionConfiguration));
  return Object.assign(
    runtimeConfig,
    (0, import_region_config_resolver.resolveAwsRegionExtensionConfiguration)(extensionConfiguration),
    (0, import_smithy_client.resolveDefaultRuntimeConfig)(extensionConfiguration),
    (0, import_protocol_http.resolveHttpHandlerRuntimeConfig)(extensionConfiguration),
    resolveHttpAuthRuntimeConfig(extensionConfiguration)
  );
}, "resolveRuntimeExtensions");

// src/DynamoDBClient.ts
var DynamoDBClient = class extends import_smithy_client.Client {
  static {
    __name(this, "DynamoDBClient");
  }
  /**
   * The resolved configuration of DynamoDBClient class. This is resolved and normalized from the {@link DynamoDBClientConfig | constructor configuration interface}.
   */
  config;
  constructor(...[configuration]) {
    const _config_0 = (0, import_runtimeConfig.getRuntimeConfig)(configuration || {});
    super(_config_0);
    this.initConfig = _config_0;
    const _config_1 = resolveClientEndpointParameters(_config_0);
    const _config_2 = (0, import_account_id_endpoint.resolveAccountIdEndpointModeConfig)(_config_1);
    const _config_3 = (0, import_middleware_user_agent.resolveUserAgentConfig)(_config_2);
    const _config_4 = (0, import_middleware_retry.resolveRetryConfig)(_config_3);
    const _config_5 = (0, import_config_resolver.resolveRegionConfig)(_config_4);
    const _config_6 = (0, import_middleware_host_header.resolveHostHeaderConfig)(_config_5);
    const _config_7 = (0, import_middleware_endpoint.resolveEndpointConfig)(_config_6);
    const _config_8 = (0, import_httpAuthSchemeProvider.resolveHttpAuthSchemeConfig)(_config_7);
    const _config_9 = (0, import_middleware_endpoint_discovery.resolveEndpointDiscoveryConfig)(_config_8, {
      endpointDiscoveryCommandCtor: DescribeEndpointsCommand
    });
    const _config_10 = resolveRuntimeExtensions(_config_9, configuration?.extensions || []);
    this.config = _config_10;
    this.middlewareStack.use((0, import_middleware_user_agent.getUserAgentPlugin)(this.config));
    this.middlewareStack.use((0, import_middleware_retry.getRetryPlugin)(this.config));
    this.middlewareStack.use((0, import_middleware_content_length.getContentLengthPlugin)(this.config));
    this.middlewareStack.use((0, import_middleware_host_header.getHostHeaderPlugin)(this.config));
    this.middlewareStack.use((0, import_middleware_logger.getLoggerPlugin)(this.config));
    this.middlewareStack.use((0, import_middleware_recursion_detection.getRecursionDetectionPlugin)(this.config));
    this.middlewareStack.use(
      (0, import_core2.getHttpAuthSchemeEndpointRuleSetPlugin)(this.config, {
        httpAuthSchemeParametersProvider: import_httpAuthSchemeProvider.defaultDynamoDBHttpAuthSchemeParametersProvider,
        identityProviderConfigProvider: /* @__PURE__ */ __name(async (config) => new import_core2.DefaultIdentityProviderConfig({
          "aws.auth#sigv4": config.credentials
        }), "identityProviderConfigProvider")
      })
    );
    this.middlewareStack.use((0, import_core2.getHttpSigningPlugin)(this.config));
  }
  /**
   * Destroy underlying resources, like sockets. It's usually not necessary to do this.
   * However in Node.js, it's best to explicitly shut down the client's agent when it is no longer needed.
   * Otherwise, sockets might stay open for quite a long time before the server terminates them.
   */
  destroy() {
    super.destroy();
  }
};

// src/DynamoDB.ts


// src/commands/BatchExecuteStatementCommand.ts



var BatchExecuteStatementCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "BatchExecuteStatement", {}).n("DynamoDBClient", "BatchExecuteStatementCommand").f(void 0, void 0).ser(se_BatchExecuteStatementCommand).de(de_BatchExecuteStatementCommand).build() {
  static {
    __name(this, "BatchExecuteStatementCommand");
  }
};

// src/commands/BatchGetItemCommand.ts



var BatchGetItemCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArnList: { type: "operationContextParams", get: /* @__PURE__ */ __name((input) => Object.keys(input?.RequestItems ?? {}), "get") }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "BatchGetItem", {}).n("DynamoDBClient", "BatchGetItemCommand").f(void 0, void 0).ser(se_BatchGetItemCommand).de(de_BatchGetItemCommand).build() {
  static {
    __name(this, "BatchGetItemCommand");
  }
};

// src/commands/BatchWriteItemCommand.ts



var BatchWriteItemCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArnList: { type: "operationContextParams", get: /* @__PURE__ */ __name((input) => Object.keys(input?.RequestItems ?? {}), "get") }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "BatchWriteItem", {}).n("DynamoDBClient", "BatchWriteItemCommand").f(void 0, void 0).ser(se_BatchWriteItemCommand).de(de_BatchWriteItemCommand).build() {
  static {
    __name(this, "BatchWriteItemCommand");
  }
};

// src/commands/CreateBackupCommand.ts



var CreateBackupCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "CreateBackup", {}).n("DynamoDBClient", "CreateBackupCommand").f(void 0, void 0).ser(se_CreateBackupCommand).de(de_CreateBackupCommand).build() {
  static {
    __name(this, "CreateBackupCommand");
  }
};

// src/commands/CreateGlobalTableCommand.ts



var CreateGlobalTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "GlobalTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "CreateGlobalTable", {}).n("DynamoDBClient", "CreateGlobalTableCommand").f(void 0, void 0).ser(se_CreateGlobalTableCommand).de(de_CreateGlobalTableCommand).build() {
  static {
    __name(this, "CreateGlobalTableCommand");
  }
};

// src/commands/CreateTableCommand.ts



var CreateTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "CreateTable", {}).n("DynamoDBClient", "CreateTableCommand").f(void 0, void 0).ser(se_CreateTableCommand).de(de_CreateTableCommand).build() {
  static {
    __name(this, "CreateTableCommand");
  }
};

// src/commands/DeleteBackupCommand.ts



var DeleteBackupCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "BackupArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DeleteBackup", {}).n("DynamoDBClient", "DeleteBackupCommand").f(void 0, void 0).ser(se_DeleteBackupCommand).de(de_DeleteBackupCommand).build() {
  static {
    __name(this, "DeleteBackupCommand");
  }
};

// src/commands/DeleteItemCommand.ts



var DeleteItemCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DeleteItem", {}).n("DynamoDBClient", "DeleteItemCommand").f(void 0, void 0).ser(se_DeleteItemCommand).de(de_DeleteItemCommand).build() {
  static {
    __name(this, "DeleteItemCommand");
  }
};

// src/commands/DeleteResourcePolicyCommand.ts



var DeleteResourcePolicyCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ResourceArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DeleteResourcePolicy", {}).n("DynamoDBClient", "DeleteResourcePolicyCommand").f(void 0, void 0).ser(se_DeleteResourcePolicyCommand).de(de_DeleteResourcePolicyCommand).build() {
  static {
    __name(this, "DeleteResourcePolicyCommand");
  }
};

// src/commands/DeleteTableCommand.ts



var DeleteTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DeleteTable", {}).n("DynamoDBClient", "DeleteTableCommand").f(void 0, void 0).ser(se_DeleteTableCommand).de(de_DeleteTableCommand).build() {
  static {
    __name(this, "DeleteTableCommand");
  }
};

// src/commands/DescribeBackupCommand.ts



var DescribeBackupCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "BackupArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeBackup", {}).n("DynamoDBClient", "DescribeBackupCommand").f(void 0, void 0).ser(se_DescribeBackupCommand).de(de_DescribeBackupCommand).build() {
  static {
    __name(this, "DescribeBackupCommand");
  }
};

// src/commands/DescribeContinuousBackupsCommand.ts



var DescribeContinuousBackupsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeContinuousBackups", {}).n("DynamoDBClient", "DescribeContinuousBackupsCommand").f(void 0, void 0).ser(se_DescribeContinuousBackupsCommand).de(de_DescribeContinuousBackupsCommand).build() {
  static {
    __name(this, "DescribeContinuousBackupsCommand");
  }
};

// src/commands/DescribeContributorInsightsCommand.ts



var DescribeContributorInsightsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeContributorInsights", {}).n("DynamoDBClient", "DescribeContributorInsightsCommand").f(void 0, void 0).ser(se_DescribeContributorInsightsCommand).de(de_DescribeContributorInsightsCommand).build() {
  static {
    __name(this, "DescribeContributorInsightsCommand");
  }
};

// src/commands/DescribeExportCommand.ts



var DescribeExportCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ExportArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeExport", {}).n("DynamoDBClient", "DescribeExportCommand").f(void 0, void 0).ser(se_DescribeExportCommand).de(de_DescribeExportCommand).build() {
  static {
    __name(this, "DescribeExportCommand");
  }
};

// src/commands/DescribeGlobalTableCommand.ts



var DescribeGlobalTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "GlobalTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeGlobalTable", {}).n("DynamoDBClient", "DescribeGlobalTableCommand").f(void 0, void 0).ser(se_DescribeGlobalTableCommand).de(de_DescribeGlobalTableCommand).build() {
  static {
    __name(this, "DescribeGlobalTableCommand");
  }
};

// src/commands/DescribeGlobalTableSettingsCommand.ts



var DescribeGlobalTableSettingsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "GlobalTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeGlobalTableSettings", {}).n("DynamoDBClient", "DescribeGlobalTableSettingsCommand").f(void 0, void 0).ser(se_DescribeGlobalTableSettingsCommand).de(de_DescribeGlobalTableSettingsCommand).build() {
  static {
    __name(this, "DescribeGlobalTableSettingsCommand");
  }
};

// src/commands/DescribeImportCommand.ts



var DescribeImportCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ImportArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeImport", {}).n("DynamoDBClient", "DescribeImportCommand").f(void 0, void 0).ser(se_DescribeImportCommand).de(de_DescribeImportCommand).build() {
  static {
    __name(this, "DescribeImportCommand");
  }
};

// src/commands/DescribeKinesisStreamingDestinationCommand.ts



var DescribeKinesisStreamingDestinationCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeKinesisStreamingDestination", {}).n("DynamoDBClient", "DescribeKinesisStreamingDestinationCommand").f(void 0, void 0).ser(se_DescribeKinesisStreamingDestinationCommand).de(de_DescribeKinesisStreamingDestinationCommand).build() {
  static {
    __name(this, "DescribeKinesisStreamingDestinationCommand");
  }
};

// src/commands/DescribeLimitsCommand.ts



var DescribeLimitsCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeLimits", {}).n("DynamoDBClient", "DescribeLimitsCommand").f(void 0, void 0).ser(se_DescribeLimitsCommand).de(de_DescribeLimitsCommand).build() {
  static {
    __name(this, "DescribeLimitsCommand");
  }
};

// src/commands/DescribeTableCommand.ts



var DescribeTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeTable", {}).n("DynamoDBClient", "DescribeTableCommand").f(void 0, void 0).ser(se_DescribeTableCommand).de(de_DescribeTableCommand).build() {
  static {
    __name(this, "DescribeTableCommand");
  }
};

// src/commands/DescribeTableReplicaAutoScalingCommand.ts



var DescribeTableReplicaAutoScalingCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeTableReplicaAutoScaling", {}).n("DynamoDBClient", "DescribeTableReplicaAutoScalingCommand").f(void 0, void 0).ser(se_DescribeTableReplicaAutoScalingCommand).de(de_DescribeTableReplicaAutoScalingCommand).build() {
  static {
    __name(this, "DescribeTableReplicaAutoScalingCommand");
  }
};

// src/commands/DescribeTimeToLiveCommand.ts



var DescribeTimeToLiveCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DescribeTimeToLive", {}).n("DynamoDBClient", "DescribeTimeToLiveCommand").f(void 0, void 0).ser(se_DescribeTimeToLiveCommand).de(de_DescribeTimeToLiveCommand).build() {
  static {
    __name(this, "DescribeTimeToLiveCommand");
  }
};

// src/commands/DisableKinesisStreamingDestinationCommand.ts



var DisableKinesisStreamingDestinationCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "DisableKinesisStreamingDestination", {}).n("DynamoDBClient", "DisableKinesisStreamingDestinationCommand").f(void 0, void 0).ser(se_DisableKinesisStreamingDestinationCommand).de(de_DisableKinesisStreamingDestinationCommand).build() {
  static {
    __name(this, "DisableKinesisStreamingDestinationCommand");
  }
};

// src/commands/EnableKinesisStreamingDestinationCommand.ts



var EnableKinesisStreamingDestinationCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "EnableKinesisStreamingDestination", {}).n("DynamoDBClient", "EnableKinesisStreamingDestinationCommand").f(void 0, void 0).ser(se_EnableKinesisStreamingDestinationCommand).de(de_EnableKinesisStreamingDestinationCommand).build() {
  static {
    __name(this, "EnableKinesisStreamingDestinationCommand");
  }
};

// src/commands/ExecuteStatementCommand.ts



var ExecuteStatementCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ExecuteStatement", {}).n("DynamoDBClient", "ExecuteStatementCommand").f(void 0, void 0).ser(se_ExecuteStatementCommand).de(de_ExecuteStatementCommand).build() {
  static {
    __name(this, "ExecuteStatementCommand");
  }
};

// src/commands/ExecuteTransactionCommand.ts



var ExecuteTransactionCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ExecuteTransaction", {}).n("DynamoDBClient", "ExecuteTransactionCommand").f(void 0, void 0).ser(se_ExecuteTransactionCommand).de(de_ExecuteTransactionCommand).build() {
  static {
    __name(this, "ExecuteTransactionCommand");
  }
};

// src/commands/ExportTableToPointInTimeCommand.ts



var ExportTableToPointInTimeCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ExportTableToPointInTime", {}).n("DynamoDBClient", "ExportTableToPointInTimeCommand").f(void 0, void 0).ser(se_ExportTableToPointInTimeCommand).de(de_ExportTableToPointInTimeCommand).build() {
  static {
    __name(this, "ExportTableToPointInTimeCommand");
  }
};

// src/commands/GetItemCommand.ts



var GetItemCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "GetItem", {}).n("DynamoDBClient", "GetItemCommand").f(void 0, void 0).ser(se_GetItemCommand).de(de_GetItemCommand).build() {
  static {
    __name(this, "GetItemCommand");
  }
};

// src/commands/GetResourcePolicyCommand.ts



var GetResourcePolicyCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ResourceArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "GetResourcePolicy", {}).n("DynamoDBClient", "GetResourcePolicyCommand").f(void 0, void 0).ser(se_GetResourcePolicyCommand).de(de_GetResourcePolicyCommand).build() {
  static {
    __name(this, "GetResourcePolicyCommand");
  }
};

// src/commands/ImportTableCommand.ts



var ImportTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "operationContextParams", get: /* @__PURE__ */ __name((input) => input?.TableCreationParameters?.TableName, "get") }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ImportTable", {}).n("DynamoDBClient", "ImportTableCommand").f(void 0, void 0).ser(se_ImportTableCommand).de(de_ImportTableCommand).build() {
  static {
    __name(this, "ImportTableCommand");
  }
};

// src/commands/ListBackupsCommand.ts



var ListBackupsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListBackups", {}).n("DynamoDBClient", "ListBackupsCommand").f(void 0, void 0).ser(se_ListBackupsCommand).de(de_ListBackupsCommand).build() {
  static {
    __name(this, "ListBackupsCommand");
  }
};

// src/commands/ListContributorInsightsCommand.ts



var ListContributorInsightsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListContributorInsights", {}).n("DynamoDBClient", "ListContributorInsightsCommand").f(void 0, void 0).ser(se_ListContributorInsightsCommand).de(de_ListContributorInsightsCommand).build() {
  static {
    __name(this, "ListContributorInsightsCommand");
  }
};

// src/commands/ListExportsCommand.ts



var ListExportsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListExports", {}).n("DynamoDBClient", "ListExportsCommand").f(void 0, void 0).ser(se_ListExportsCommand).de(de_ListExportsCommand).build() {
  static {
    __name(this, "ListExportsCommand");
  }
};

// src/commands/ListGlobalTablesCommand.ts



var ListGlobalTablesCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListGlobalTables", {}).n("DynamoDBClient", "ListGlobalTablesCommand").f(void 0, void 0).ser(se_ListGlobalTablesCommand).de(de_ListGlobalTablesCommand).build() {
  static {
    __name(this, "ListGlobalTablesCommand");
  }
};

// src/commands/ListImportsCommand.ts



var ListImportsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListImports", {}).n("DynamoDBClient", "ListImportsCommand").f(void 0, void 0).ser(se_ListImportsCommand).de(de_ListImportsCommand).build() {
  static {
    __name(this, "ListImportsCommand");
  }
};

// src/commands/ListTablesCommand.ts



var ListTablesCommand = class extends import_smithy_client.Command.classBuilder().ep(commonParams).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListTables", {}).n("DynamoDBClient", "ListTablesCommand").f(void 0, void 0).ser(se_ListTablesCommand).de(de_ListTablesCommand).build() {
  static {
    __name(this, "ListTablesCommand");
  }
};

// src/commands/ListTagsOfResourceCommand.ts



var ListTagsOfResourceCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ResourceArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "ListTagsOfResource", {}).n("DynamoDBClient", "ListTagsOfResourceCommand").f(void 0, void 0).ser(se_ListTagsOfResourceCommand).de(de_ListTagsOfResourceCommand).build() {
  static {
    __name(this, "ListTagsOfResourceCommand");
  }
};

// src/commands/PutItemCommand.ts



var PutItemCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "PutItem", {}).n("DynamoDBClient", "PutItemCommand").f(void 0, void 0).ser(se_PutItemCommand).de(de_PutItemCommand).build() {
  static {
    __name(this, "PutItemCommand");
  }
};

// src/commands/PutResourcePolicyCommand.ts



var PutResourcePolicyCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ResourceArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "PutResourcePolicy", {}).n("DynamoDBClient", "PutResourcePolicyCommand").f(void 0, void 0).ser(se_PutResourcePolicyCommand).de(de_PutResourcePolicyCommand).build() {
  static {
    __name(this, "PutResourcePolicyCommand");
  }
};

// src/commands/QueryCommand.ts



var QueryCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "Query", {}).n("DynamoDBClient", "QueryCommand").f(void 0, void 0).ser(se_QueryCommand).de(de_QueryCommand).build() {
  static {
    __name(this, "QueryCommand");
  }
};

// src/commands/RestoreTableFromBackupCommand.ts



var RestoreTableFromBackupCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TargetTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "RestoreTableFromBackup", {}).n("DynamoDBClient", "RestoreTableFromBackupCommand").f(void 0, void 0).ser(se_RestoreTableFromBackupCommand).de(de_RestoreTableFromBackupCommand).build() {
  static {
    __name(this, "RestoreTableFromBackupCommand");
  }
};

// src/commands/RestoreTableToPointInTimeCommand.ts



var RestoreTableToPointInTimeCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TargetTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "RestoreTableToPointInTime", {}).n("DynamoDBClient", "RestoreTableToPointInTimeCommand").f(void 0, void 0).ser(se_RestoreTableToPointInTimeCommand).de(de_RestoreTableToPointInTimeCommand).build() {
  static {
    __name(this, "RestoreTableToPointInTimeCommand");
  }
};

// src/commands/ScanCommand.ts



var ScanCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "Scan", {}).n("DynamoDBClient", "ScanCommand").f(void 0, void 0).ser(se_ScanCommand).de(de_ScanCommand).build() {
  static {
    __name(this, "ScanCommand");
  }
};

// src/commands/TagResourceCommand.ts



var TagResourceCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ResourceArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "TagResource", {}).n("DynamoDBClient", "TagResourceCommand").f(void 0, void 0).ser(se_TagResourceCommand).de(de_TagResourceCommand).build() {
  static {
    __name(this, "TagResourceCommand");
  }
};

// src/commands/TransactGetItemsCommand.ts



var TransactGetItemsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArnList: {
    type: "operationContextParams",
    get: /* @__PURE__ */ __name((input) => input?.TransactItems?.map((obj) => obj?.Get?.TableName), "get")
  }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "TransactGetItems", {}).n("DynamoDBClient", "TransactGetItemsCommand").f(void 0, void 0).ser(se_TransactGetItemsCommand).de(de_TransactGetItemsCommand).build() {
  static {
    __name(this, "TransactGetItemsCommand");
  }
};

// src/commands/TransactWriteItemsCommand.ts



var TransactWriteItemsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArnList: {
    type: "operationContextParams",
    get: /* @__PURE__ */ __name((input) => input?.TransactItems?.map(
      (obj) => [obj?.ConditionCheck?.TableName, obj?.Put?.TableName, obj?.Delete?.TableName, obj?.Update?.TableName].filter(
        (i) => i
      )
    ).flat(), "get")
  }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "TransactWriteItems", {}).n("DynamoDBClient", "TransactWriteItemsCommand").f(void 0, void 0).ser(se_TransactWriteItemsCommand).de(de_TransactWriteItemsCommand).build() {
  static {
    __name(this, "TransactWriteItemsCommand");
  }
};

// src/commands/UntagResourceCommand.ts



var UntagResourceCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "ResourceArn" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UntagResource", {}).n("DynamoDBClient", "UntagResourceCommand").f(void 0, void 0).ser(se_UntagResourceCommand).de(de_UntagResourceCommand).build() {
  static {
    __name(this, "UntagResourceCommand");
  }
};

// src/commands/UpdateContinuousBackupsCommand.ts



var UpdateContinuousBackupsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateContinuousBackups", {}).n("DynamoDBClient", "UpdateContinuousBackupsCommand").f(void 0, void 0).ser(se_UpdateContinuousBackupsCommand).de(de_UpdateContinuousBackupsCommand).build() {
  static {
    __name(this, "UpdateContinuousBackupsCommand");
  }
};

// src/commands/UpdateContributorInsightsCommand.ts



var UpdateContributorInsightsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateContributorInsights", {}).n("DynamoDBClient", "UpdateContributorInsightsCommand").f(void 0, void 0).ser(se_UpdateContributorInsightsCommand).de(de_UpdateContributorInsightsCommand).build() {
  static {
    __name(this, "UpdateContributorInsightsCommand");
  }
};

// src/commands/UpdateGlobalTableCommand.ts



var UpdateGlobalTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "GlobalTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateGlobalTable", {}).n("DynamoDBClient", "UpdateGlobalTableCommand").f(void 0, void 0).ser(se_UpdateGlobalTableCommand).de(de_UpdateGlobalTableCommand).build() {
  static {
    __name(this, "UpdateGlobalTableCommand");
  }
};

// src/commands/UpdateGlobalTableSettingsCommand.ts



var UpdateGlobalTableSettingsCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "GlobalTableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateGlobalTableSettings", {}).n("DynamoDBClient", "UpdateGlobalTableSettingsCommand").f(void 0, void 0).ser(se_UpdateGlobalTableSettingsCommand).de(de_UpdateGlobalTableSettingsCommand).build() {
  static {
    __name(this, "UpdateGlobalTableSettingsCommand");
  }
};

// src/commands/UpdateItemCommand.ts



var UpdateItemCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateItem", {}).n("DynamoDBClient", "UpdateItemCommand").f(void 0, void 0).ser(se_UpdateItemCommand).de(de_UpdateItemCommand).build() {
  static {
    __name(this, "UpdateItemCommand");
  }
};

// src/commands/UpdateKinesisStreamingDestinationCommand.ts



var UpdateKinesisStreamingDestinationCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateKinesisStreamingDestination", {}).n("DynamoDBClient", "UpdateKinesisStreamingDestinationCommand").f(void 0, void 0).ser(se_UpdateKinesisStreamingDestinationCommand).de(de_UpdateKinesisStreamingDestinationCommand).build() {
  static {
    __name(this, "UpdateKinesisStreamingDestinationCommand");
  }
};

// src/commands/UpdateTableCommand.ts



var UpdateTableCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateTable", {}).n("DynamoDBClient", "UpdateTableCommand").f(void 0, void 0).ser(se_UpdateTableCommand).de(de_UpdateTableCommand).build() {
  static {
    __name(this, "UpdateTableCommand");
  }
};

// src/commands/UpdateTableReplicaAutoScalingCommand.ts



var UpdateTableReplicaAutoScalingCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateTableReplicaAutoScaling", {}).n("DynamoDBClient", "UpdateTableReplicaAutoScalingCommand").f(void 0, void 0).ser(se_UpdateTableReplicaAutoScalingCommand).de(de_UpdateTableReplicaAutoScalingCommand).build() {
  static {
    __name(this, "UpdateTableReplicaAutoScalingCommand");
  }
};

// src/commands/UpdateTimeToLiveCommand.ts



var UpdateTimeToLiveCommand = class extends import_smithy_client.Command.classBuilder().ep({
  ...commonParams,
  ResourceArn: { type: "contextParams", name: "TableName" }
}).m(function(Command, cs, config, o) {
  return [
    (0, import_middleware_serde.getSerdePlugin)(config, this.serialize, this.deserialize),
    (0, import_middleware_endpoint.getEndpointPlugin)(config, Command.getEndpointParameterInstructions())
  ];
}).s("DynamoDB_20120810", "UpdateTimeToLive", {}).n("DynamoDBClient", "UpdateTimeToLiveCommand").f(void 0, void 0).ser(se_UpdateTimeToLiveCommand).de(de_UpdateTimeToLiveCommand).build() {
  static {
    __name(this, "UpdateTimeToLiveCommand");
  }
};

// src/DynamoDB.ts
var commands = {
  BatchExecuteStatementCommand,
  BatchGetItemCommand,
  BatchWriteItemCommand,
  CreateBackupCommand,
  CreateGlobalTableCommand,
  CreateTableCommand,
  DeleteBackupCommand,
  DeleteItemCommand,
  DeleteResourcePolicyCommand,
  DeleteTableCommand,
  DescribeBackupCommand,
  DescribeContinuousBackupsCommand,
  DescribeContributorInsightsCommand,
  DescribeEndpointsCommand,
  DescribeExportCommand,
  DescribeGlobalTableCommand,
  DescribeGlobalTableSettingsCommand,
  DescribeImportCommand,
  DescribeKinesisStreamingDestinationCommand,
  DescribeLimitsCommand,
  DescribeTableCommand,
  DescribeTableReplicaAutoScalingCommand,
  DescribeTimeToLiveCommand,
  DisableKinesisStreamingDestinationCommand,
  EnableKinesisStreamingDestinationCommand,
  ExecuteStatementCommand,
  ExecuteTransactionCommand,
  ExportTableToPointInTimeCommand,
  GetItemCommand,
  GetResourcePolicyCommand,
  ImportTableCommand,
  ListBackupsCommand,
  ListContributorInsightsCommand,
  ListExportsCommand,
  ListGlobalTablesCommand,
  ListImportsCommand,
  ListTablesCommand,
  ListTagsOfResourceCommand,
  PutItemCommand,
  PutResourcePolicyCommand,
  QueryCommand,
  RestoreTableFromBackupCommand,
  RestoreTableToPointInTimeCommand,
  ScanCommand,
  TagResourceCommand,
  TransactGetItemsCommand,
  TransactWriteItemsCommand,
  UntagResourceCommand,
  UpdateContinuousBackupsCommand,
  UpdateContributorInsightsCommand,
  UpdateGlobalTableCommand,
  UpdateGlobalTableSettingsCommand,
  UpdateItemCommand,
  UpdateKinesisStreamingDestinationCommand,
  UpdateTableCommand,
  UpdateTableReplicaAutoScalingCommand,
  UpdateTimeToLiveCommand
};
var DynamoDB = class extends DynamoDBClient {
  static {
    __name(this, "DynamoDB");
  }
};
(0, import_smithy_client.createAggregatedClient)(commands, DynamoDB);

// src/pagination/ListContributorInsightsPaginator.ts
var import_core3 = require("@smithy/core");
var paginateListContributorInsights = (0, import_core3.createPaginator)(DynamoDBClient, ListContributorInsightsCommand, "NextToken", "NextToken", "MaxResults");

// src/pagination/ListExportsPaginator.ts
var import_core4 = require("@smithy/core");
var paginateListExports = (0, import_core4.createPaginator)(DynamoDBClient, ListExportsCommand, "NextToken", "NextToken", "MaxResults");

// src/pagination/ListImportsPaginator.ts
var import_core5 = require("@smithy/core");
var paginateListImports = (0, import_core5.createPaginator)(DynamoDBClient, ListImportsCommand, "NextToken", "NextToken", "PageSize");

// src/pagination/ListTablesPaginator.ts
var import_core6 = require("@smithy/core");
var paginateListTables = (0, import_core6.createPaginator)(DynamoDBClient, ListTablesCommand, "ExclusiveStartTableName", "LastEvaluatedTableName", "Limit");

// src/pagination/QueryPaginator.ts
var import_core7 = require("@smithy/core");
var paginateQuery = (0, import_core7.createPaginator)(DynamoDBClient, QueryCommand, "ExclusiveStartKey", "LastEvaluatedKey", "Limit");

// src/pagination/ScanPaginator.ts
var import_core8 = require("@smithy/core");
var paginateScan = (0, import_core8.createPaginator)(DynamoDBClient, ScanCommand, "ExclusiveStartKey", "LastEvaluatedKey", "Limit");

// src/waiters/waitForTableExists.ts
var import_util_waiter = require("@smithy/util-waiter");
var checkState = /* @__PURE__ */ __name(async (client, input) => {
  let reason;
  try {
    const result = await client.send(new DescribeTableCommand(input));
    reason = result;
    try {
      const returnComparator = /* @__PURE__ */ __name(() => {
        return result.Table.TableStatus;
      }, "returnComparator");
      if (returnComparator() === "ACTIVE") {
        return { state: import_util_waiter.WaiterState.SUCCESS, reason };
      }
    } catch (e) {
    }
  } catch (exception) {
    reason = exception;
    if (exception.name && exception.name == "ResourceNotFoundException") {
      return { state: import_util_waiter.WaiterState.RETRY, reason };
    }
  }
  return { state: import_util_waiter.WaiterState.RETRY, reason };
}, "checkState");
var waitForTableExists = /* @__PURE__ */ __name(async (params, input) => {
  const serviceDefaults = { minDelay: 20, maxDelay: 120 };
  return (0, import_util_waiter.createWaiter)({ ...serviceDefaults, ...params }, input, checkState);
}, "waitForTableExists");
var waitUntilTableExists = /* @__PURE__ */ __name(async (params, input) => {
  const serviceDefaults = { minDelay: 20, maxDelay: 120 };
  const result = await (0, import_util_waiter.createWaiter)({ ...serviceDefaults, ...params }, input, checkState);
  return (0, import_util_waiter.checkExceptions)(result);
}, "waitUntilTableExists");

// src/waiters/waitForTableNotExists.ts

var checkState2 = /* @__PURE__ */ __name(async (client, input) => {
  let reason;
  try {
    const result = await client.send(new DescribeTableCommand(input));
    reason = result;
  } catch (exception) {
    reason = exception;
    if (exception.name && exception.name == "ResourceNotFoundException") {
      return { state: import_util_waiter.WaiterState.SUCCESS, reason };
    }
  }
  return { state: import_util_waiter.WaiterState.RETRY, reason };
}, "checkState");
var waitForTableNotExists = /* @__PURE__ */ __name(async (params, input) => {
  const serviceDefaults = { minDelay: 20, maxDelay: 120 };
  return (0, import_util_waiter.createWaiter)({ ...serviceDefaults, ...params }, input, checkState2);
}, "waitForTableNotExists");
var waitUntilTableNotExists = /* @__PURE__ */ __name(async (params, input) => {
  const serviceDefaults = { minDelay: 20, maxDelay: 120 };
  const result = await (0, import_util_waiter.createWaiter)({ ...serviceDefaults, ...params }, input, checkState2);
  return (0, import_util_waiter.checkExceptions)(result);
}, "waitUntilTableNotExists");
// Annotate the CommonJS export names for ESM import in node:

0 && (module.exports = {
  DynamoDBServiceException,
  __Client,
  DynamoDBClient,
  DynamoDB,
  $Command,
  BatchExecuteStatementCommand,
  BatchGetItemCommand,
  BatchWriteItemCommand,
  CreateBackupCommand,
  CreateGlobalTableCommand,
  CreateTableCommand,
  DeleteBackupCommand,
  DeleteItemCommand,
  DeleteResourcePolicyCommand,
  DeleteTableCommand,
  DescribeBackupCommand,
  DescribeContinuousBackupsCommand,
  DescribeContributorInsightsCommand,
  DescribeEndpointsCommand,
  DescribeExportCommand,
  DescribeGlobalTableCommand,
  DescribeGlobalTableSettingsCommand,
  DescribeImportCommand,
  DescribeKinesisStreamingDestinationCommand,
  DescribeLimitsCommand,
  DescribeTableCommand,
  DescribeTableReplicaAutoScalingCommand,
  DescribeTimeToLiveCommand,
  DisableKinesisStreamingDestinationCommand,
  EnableKinesisStreamingDestinationCommand,
  ExecuteStatementCommand,
  ExecuteTransactionCommand,
  ExportTableToPointInTimeCommand,
  GetItemCommand,
  GetResourcePolicyCommand,
  ImportTableCommand,
  ListBackupsCommand,
  ListContributorInsightsCommand,
  ListExportsCommand,
  ListGlobalTablesCommand,
  ListImportsCommand,
  ListTablesCommand,
  ListTagsOfResourceCommand,
  PutItemCommand,
  PutResourcePolicyCommand,
  QueryCommand,
  RestoreTableFromBackupCommand,
  RestoreTableToPointInTimeCommand,
  ScanCommand,
  TagResourceCommand,
  TransactGetItemsCommand,
  TransactWriteItemsCommand,
  UntagResourceCommand,
  UpdateContinuousBackupsCommand,
  UpdateContributorInsightsCommand,
  UpdateGlobalTableCommand,
  UpdateGlobalTableSettingsCommand,
  UpdateItemCommand,
  UpdateKinesisStreamingDestinationCommand,
  UpdateTableCommand,
  UpdateTableReplicaAutoScalingCommand,
  UpdateTimeToLiveCommand,
  paginateListContributorInsights,
  paginateListExports,
  paginateListImports,
  paginateListTables,
  paginateQuery,
  paginateScan,
  waitForTableExists,
  waitUntilTableExists,
  waitForTableNotExists,
  waitUntilTableNotExists,
  ApproximateCreationDateTimePrecision,
  AttributeAction,
  ScalarAttributeType,
  BackupStatus,
  BackupType,
  BillingMode,
  KeyType,
  ProjectionType,
  SSEType,
  SSEStatus,
  StreamViewType,
  TimeToLiveStatus,
  BackupInUseException,
  BackupNotFoundException,
  BackupTypeFilter,
  ReturnConsumedCapacity,
  ReturnValuesOnConditionCheckFailure,
  BatchStatementErrorCodeEnum,
  InternalServerError,
  RequestLimitExceeded,
  InvalidEndpointException,
  ProvisionedThroughputExceededException,
  ResourceNotFoundException,
  ReturnItemCollectionMetrics,
  ItemCollectionSizeLimitExceededException,
  ReplicatedWriteConflictException,
  ComparisonOperator,
  ConditionalOperator,
  ContinuousBackupsStatus,
  PointInTimeRecoveryStatus,
  ContinuousBackupsUnavailableException,
  ContributorInsightsAction,
  ContributorInsightsStatus,
  LimitExceededException,
  TableInUseException,
  TableNotFoundException,
  GlobalTableStatus,
  IndexStatus,
  ReplicaStatus,
  TableClass,
  TableStatus,
  GlobalTableAlreadyExistsException,
  WitnessStatus,
  MultiRegionConsistency,
  ResourceInUseException,
  ReturnValue,
  TransactionConflictException,
  PolicyNotFoundException,
  ExportFormat,
  ExportStatus,
  ExportType,
  ExportViewType,
  S3SseAlgorithm,
  ExportNotFoundException,
  GlobalTableNotFoundException,
  ImportStatus,
  InputCompressionType,
  InputFormat,
  ImportNotFoundException,
  DestinationStatus,
  DuplicateItemException,
  IdempotentParameterMismatchException,
  TransactionInProgressException,
  ExportConflictException,
  InvalidExportTimeException,
  PointInTimeRecoveryUnavailableException,
  ImportConflictException,
  Select,
  TableAlreadyExistsException,
  InvalidRestoreTimeException,
  ReplicaAlreadyExistsException,
  ReplicaNotFoundException,
  IndexNotFoundException,
  AttributeValue,
  ConditionalCheckFailedException,
  TransactionCanceledException
});

