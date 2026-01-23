# Event & Integration Models

This document provides comprehensive documentation for the event and integration models used in the CDC Pipeline service. These models handle the flow of data between Kinesis streams, EventBridge, and DynamoDB.

## Overview

The CDC Pipeline uses a sophisticated event-driven architecture where data flows from source databases through Kinesis streams, gets processed and enriched, and is then published to EventBridge for downstream consumers. This document covers three main categories:

1. **EventBridge Models** - Structures for publishing events to AWS EventBridge
2. **Kinesis Models** - Structures for consuming and processing stream records
3. **DynamoDB Models** - Structures for database operations and caching

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Event Flow Architecture                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌─────────────────────────┐     ┌───────────────────┐
│  Kinesis Stream  │────▶│  KinesisDecodedData     │────▶│   Enrichment      │
│                  │     │  KinesisDecodedMetadata │     │   (orgId, userId) │
└──────────────────┘     └─────────────────────────┘     └─────────┬─────────┘
                                                                   │
                                    ┌──────────────────────────────┘
                                    ▼
                         ┌─────────────────────────┐
                         │ ExtendedKinesisDecoded  │
                         │ Data                    │
                         └───────────┬─────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
┌───────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ RecordMetadata    │    │ RecordData          │    │ NormalizedRecord    │
│ (event context)   │    │ (before/after/      │    │ (EventBridge ready) │
│                   │    │  changes)           │    │                     │
└───────────────────┘    └─────────────────────┘    └──────────┬──────────┘
                                                               │
                                                               ▼
                                                    ┌─────────────────────┐
                                                    │    EventBridge      │
                                                    │    (downstream)     │
                                                    └─────────────────────┘
```

---

## EventBridge Models

### NormalizedRecord

The standardized structure for publishing CDC events to AWS EventBridge. This is the final transformation applied to all CDC records before publication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `string` | Yes | Event source identifier (e.g., `cdc-pipeline`) |
| `detailType` | `string` | Yes | EventBridge detail type for routing (e.g., `Users.UPDATE`) |
| `eventBusName` | `string` | Yes | Target EventBridge bus name or ARN |
| `detail` | `object` | Yes | Event detail containing `data` and `metadata` |

**Validation Rules:**
- `source` must be a non-empty string
- `detailType` must follow the pattern `{RecordType}.{Action}`
- `eventBusName` must be a valid EventBridge bus name or ARN
- `detail` must contain both `data` and `metadata` properties

**Example:**
```json
{
  "source": "cdc-pipeline",
  "detailType": "Users.UPDATE",
  "eventBusName": "arn:aws:events:us-east-1:123456789012:event-bus/cdc-events",
  "detail": {
    "data": {
      "changes": ["firstName", "lastName"],
      "after": {
        "id": "12345",
        "firstName": "John",
        "lastName": "Smith",
        "orgId": "100"
      },
      "before": {
        "id": "12345",
        "firstName": "Jane",
        "lastName": "Doe",
        "orgId": "100"
      }
    },
    "metadata": {
      "service": "cdc-pipeline",
      "_version": "1.0",
      "timestamp": "2024-01-15T10:30:00.000Z",
      "objectName": "users",
      "schemaName": "public",
      "objectAction": "UPDATE",
      "partitionKey": "users-12345",
      "attemptCount": 1,
      "orgId": 100,
      "userId": 12345,
      "sourceEventId": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522",
      "correlationId": "550e8400-e29b-41d4-a716-446655440000",
      "sourceEventName": "aws:kinesis:record",
      "eventBridgeSentTimestamp": 1705314600000
    }
  }
}
```

**Relationships:**
- Contains `RecordData` in `detail.data`
- Contains `RecordMetadata` in `detail.metadata`
- Published to EventBridge bus specified by `eventBusName`

---

### RecordMetadata

Metadata associated with a CDC record event, providing context for tracing, versioning, and processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service` | `string` | Yes | Service name that generated the event |
| `_version` | `string` | Yes | Schema version for event consumers |
| `timestamp` | `string` | Yes | ISO 8601 event timestamp |
| `objectName` | `string` | Yes | Name of the database table |
| `schemaName` | `string` | Yes | Database schema name |
| `objectAction` | `string` | Yes | Action performed (`CREATE`, `UPDATE`, `DELETE`) |
| `partitionKey` | `string` | Yes | Kinesis partition key for ordering |
| `attemptCount` | `number` | Yes | Number of processing attempts (starts at 1) |
| `orgId` | `number \| null` | No | Organization ID from enrichment |
| `userId` | `number \| null` | No | User ID from enrichment |
| `sourceEventId` | `string` | Yes | Unique source event identifier |
| `correlationId` | `string` | Yes | UUID for distributed tracing |
| `sourceEventName` | `string` | Yes | Name of the source event type |
| `eventBridgeSentTimestamp` | `number` | Yes | Unix timestamp when sent to EventBridge |

**Validation Rules:**
- `timestamp` must be a valid ISO 8601 string
- `objectAction` must be one of `CREATE`, `UPDATE`, `DELETE`, or `UNKNOWN`
- `attemptCount` must be a positive integer
- `correlationId` must be a valid UUID
- `eventBridgeSentTimestamp` must be a valid Unix timestamp (milliseconds)

**Example:**
```json
{
  "service": "cdc-pipeline",
  "_version": "1.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "objectName": "call_center_agents",
  "schemaName": "call_center",
  "objectAction": "UPDATE",
  "partitionKey": "agent-789",
  "attemptCount": 1,
  "orgId": 500,
  "userId": 789,
  "sourceEventId": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522",
  "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sourceEventName": "aws:kinesis:record",
  "eventBridgeSentTimestamp": 1705314600000
}
```

**Relationships:**
- Part of `NormalizedRecord.detail.metadata`
- `objectAction` values come from `DatabaseActionEnum`
- `orgId` and `userId` populated by enrichment process

---

### RecordData

Data payload containing the before and after states of a record, along with the list of changed fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `changes` | `string[]` | Yes | List of field names that changed |
| `after` | `Record<string, unknown> \| null` | No | State after the change (null for DELETE) |
| `before` | `Record<string, unknown> \| null` | No | State before the change (null for CREATE) |

**Validation Rules:**
- `changes` must be an array (can be empty for full record events)
- For `CREATE` operations: `before` is null, `after` contains the new record
- For `UPDATE` operations: both `before` and `after` are populated
- For `DELETE` operations: `after` is null, `before` contains the deleted record

**Example (UPDATE operation):**
```json
{
  "changes": ["status", "stateUpdatedTime"],
  "after": {
    "uuid": "queue-123",
    "queueName": "support-queue",
    "status": "ACTIVE",
    "position": "1",
    "orgId": "200",
    "stateUpdatedTime": "2024-01-15T10:30:00.000Z"
  },
  "before": {
    "uuid": "queue-123",
    "queueName": "support-queue",
    "status": "WAITING",
    "position": "3",
    "orgId": "200",
    "stateUpdatedTime": "2024-01-15T10:25:00.000Z"
  }
}
```

**Example (CREATE operation):**
```json
{
  "changes": [],
  "after": {
    "id": "12345",
    "userName": "jsmith",
    "firstName": "John",
    "lastName": "Smith",
    "orgId": "100",
    "isEnabled": true
  },
  "before": null
}
```

**Relationships:**
- Part of `NormalizedRecord.detail.data`
- Derived from `KinesisDecodedData.data` and `KinesisDecodedData.beforeImage`

---

### EventBridgeEventFailure

Represents a failed item in an EventBridge batch operation, used for partial failure handling.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `itemIdentifier` | `string` | Yes | Identifier of the failed item (typically the event ID) |

**Validation Rules:**
- `itemIdentifier` must be a non-empty string matching a submitted event

**Example:**
```json
{
  "itemIdentifier": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522"
}
```

**Relationships:**
- Contained in `LambdaResponse.batchItemFailures`
- Used to identify which Kinesis records should be retried

---

### LambdaResponse

Lambda function response structure supporting partial batch failures for Kinesis event processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batchItemFailures` | `EventBridgeEventFailure[]` | Yes | Array of failed batch items to retry |

**Validation Rules:**
- `batchItemFailures` must be an array (empty array indicates all items succeeded)
- Each failure must have a valid `itemIdentifier`

**Example (partial failure):**
```json
{
  "batchItemFailures": [
    {
      "itemIdentifier": "shardId-000000000000:49590338271490256608559692540925702759324208523137515523"
    },
    {
      "itemIdentifier": "shardId-000000000000:49590338271490256608559692540925702759324208523137515525"
    }
  ]
}
```

**Example (all succeeded):**
```json
{
  "batchItemFailures": []
}
```

**Relationships:**
- Contains `EventBridgeEventFailure` items
- Returned by Lambda handlers to AWS for retry handling

---

### EventBridgeHC

Enumeration for EventBridge health check status values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `OK` | `string` | N/A | Service is healthy and operational |
| `IN_ALARM` | `string` | N/A | Service is experiencing issues |
| `UNKNOWN` | `string` | N/A | Health status cannot be determined |

**Example Usage:**
```typescript
const healthStatus: EventBridgeHC = EventBridgeHC.OK;
```

---

### DatabaseActionEnum

Enumeration representing database CRUD operations captured by CDC.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `CREATE` | `string` | N/A | Record insertion operation |
| `UPDATE` | `string` | N/A | Record modification operation |
| `DELETE` | `string` | N/A | Record deletion operation |
| `UNKNOWN` | `string` | N/A | Unrecognized operation type |

**Mapping from DMS Operations:**
- `load` / `insert` → `CREATE`
- `update` → `UPDATE`
- `delete` → `DELETE`
- Other → `UNKNOWN`

**Example Usage:**
```typescript
const action = DatabaseActionEnum.UPDATE;
// Results in detailType: "Users.UPDATE"
```

---

## Kinesis Models

### KinesisDecodedData

Decoded data payload from a Kinesis stream record, containing the current state and before image.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | `Record<string, unknown>` | Yes | Current state of the record |
| `metadata` | `KinesisDecodedMetadata` | Yes | DMS metadata about the change |
| `beforeImage` | `Record<string, unknown>` | No | Previous state (for UPDATE/DELETE) |

**Validation Rules:**
- `data` must be a valid object
- `metadata` must contain required DMS fields
- `beforeImage` is populated only for UPDATE and DELETE operations

**Example:**
```json
{
  "data": {
    "id": 12345,
    "userName": "jsmith",
    "firstName": "John",
    "lastName": "Smith",
    "homeOrgId": 100,
    "isEnabled": true,
    "createdTime": "2024-01-01T00:00:00.000Z"
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "operation": "update",
    "table-name": "users",
    "schema-name": "public",
    "record-type": "data",
    "transaction-id": 987654321,
    "partition-key-type": "primary-key",
    "commit-timestamp": "2024-01-15T10:30:00.000Z"
  },
  "beforeImage": {
    "id": 12345,
    "userName": "jsmith",
    "firstName": "Jane",
    "lastName": "Doe",
    "homeOrgId": 100,
    "isEnabled": true,
    "createdTime": "2024-01-01T00:00:00.000Z"
  }
}
```

**Relationships:**
- Contains `KinesisDecodedMetadata`
- Extended by `ExtendedKinesisDecodedData` with enrichment

---

### KinesisDecodedMetadata

Metadata from AWS DMS describing the database change event.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | `string` | Yes | ISO timestamp of the change |
| `operation` | `string` | Yes | DMS operation type (`load`, `insert`, `update`, `delete`) |
| `table-name` | `string` | Yes | Source database table name |
| `schema-name` | `string` | Yes | Source database schema name |
| `record-type` | `string` | Yes | Type of CDC record |
| `transaction-id` | `number` | Yes | Database transaction identifier |
| `partition-key-type` | `string` | Yes | Type of partition key used |
| `commit-timestamp` | `string` | Yes | Database commit timestamp |

**Validation Rules:**
- `operation` must be one of: `load`, `insert`, `update`, `delete`
- `table-name` must match a supported record type
- `transaction-id` must be a positive integer

**Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "operation": "update",
  "table-name": "call_center_queues",
  "schema-name": "call_center",
  "record-type": "data",
  "transaction-id": 123456789,
  "partition-key-type": "primary-key",
  "commit-timestamp": "2024-01-15T10:30:00.123Z"
}
```

**Relationships:**
- Contained in `KinesisDecodedData.metadata`
- Used to determine `DatabaseActionEnum` mapping

---

### KinesisRecordMetadata

Metadata about the Kinesis record itself (not the database change).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `partitionKey` | `string` | Yes | Kinesis partition key for ordering |
| `sourceEventId` | `string` | Yes | Unique identifier combining shard and sequence |
| `sequenceNumber` | `string` | Yes | Kinesis sequence number |
| `sourceEventName` | `string` | Yes | Event source type (e.g., `aws:kinesis:record`) |
| `kinesisServiceName` | `string` | Yes | Name of the Kinesis stream |

**Validation Rules:**
- `partitionKey` must be a non-empty string
- `sequenceNumber` must be a valid Kinesis sequence number
- `sourceEventId` format: `{shardId}:{sequenceNumber}`

**Example:**
```json
{
  "partitionKey": "users-12345",
  "sourceEventId": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522",
  "sequenceNumber": "49590338271490256608559692540925702759324208523137515522",
  "sourceEventName": "aws:kinesis:record",
  "kinesisServiceName": "cdc-source-stream"
}
```

**Relationships:**
- Part of `KinesisRecordAttributes`
- Used to identify records for retry handling

---

### KinesisRecordAttributes

Combined attributes for a Kinesis record, including decoded data and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordData` | `KinesisDecodedData` | Yes | Decoded record data payload |
| `recordMetadata` | `KinesisRecordMetadata` | Yes | Kinesis-specific metadata |
| `correlationId` | `string` | Yes | UUID for distributed tracing |

**Validation Rules:**
- `correlationId` must be a valid UUID v4
- Both `recordData` and `recordMetadata` must be valid objects

**Example:**
```json
{
  "recordData": {
    "data": {
      "id": 12345,
      "userName": "jsmith"
    },
    "metadata": {
      "timestamp": "2024-01-15T10:30:00.000Z",
      "operation": "update",
      "table-name": "users",
      "schema-name": "public",
      "record-type": "data",
      "transaction-id": 987654321,
      "partition-key-type": "primary-key",
      "commit-timestamp": "2024-01-15T10:30:00.000Z"
    },
    "beforeImage": {
      "id": 12345,
      "userName": "jdoe"
    }
  },
  "recordMetadata": {
    "partitionKey": "users-12345",
    "sourceEventId": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522",
    "sequenceNumber": "49590338271490256608559692540925702759324208523137515522",
    "sourceEventName": "aws:kinesis:record",
    "kinesisServiceName": "cdc-source-stream"
  },
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Relationships:**
- Contains `KinesisDecodedData` and `KinesisRecordMetadata`
- Extended by `ExtendedKinesisRecordAttributes`
- Input to enrichment processors

---

### ExtendedKinesisDecodedData

Kinesis decoded data extended with enrichment information (organization and user context).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | `Record<string, unknown>` | Yes | Current state of the record |
| `metadata` | `KinesisDecodedMetadata` | Yes | DMS metadata |
| `beforeImage` | `Record<string, unknown>` | No | Previous state |
| `enrichment` | `Enrichment` | Yes | Added organization and user context |

**Validation Rules:**
- All `KinesisDecodedData` validations apply
- `enrichment` must contain `orgId` and `userId` (can be null)

**Example:**
```json
{
  "data": {
    "id": 12345,
    "userName": "jsmith",
    "homeOrgId": 100
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "operation": "update",
    "table-name": "users",
    "schema-name": "public",
    "record-type": "data",
    "transaction-id": 987654321,
    "partition-key-type": "primary-key",
    "commit-timestamp": "2024-01-15T10:30:00.000Z"
  },
  "beforeImage": {
    "id": 12345,
    "userName": "jdoe",
    "homeOrgId": 100
  },
  "enrichment": {
    "orgId": 100,
    "userId": 12345
  }
}
```

**Relationships:**
- Extends `KinesisDecodedData`
- Contains `Enrichment`
- Output from enrichment processors

---

### ExtendedKinesisRecordAttributes

Kinesis record attributes with extended decoded data including enrichment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordData` | `ExtendedKinesisDecodedData` | Yes | Extended decoded data with enrichment |
| `recordMetadata` | `KinesisRecordMetadata` | Yes | Kinesis-specific metadata |
| `correlationId` | `string` | Yes | UUID for distributed tracing |

**Example:**
```json
{
  "recordData": {
    "data": {
      "uuid": "agent-789",
      "orgId": 500,
      "agentType": "HUMAN"
    },
    "metadata": {
      "timestamp": "2024-01-15T10:30:00.000Z",
      "operation": "insert",
      "table-name": "call_center_agents",
      "schema-name": "call_center",
      "record-type": "data",
      "transaction-id": 123456,
      "partition-key-type": "primary-key",
      "commit-timestamp": "2024-01-15T10:30:00.000Z"
    },
    "enrichment": {
      "orgId": 500,
      "userId": 789
    }
  },
  "recordMetadata": {
    "partitionKey": "agent-789",
    "sourceEventId": "shardId-000000000000:49590338271490256608559692540925702759324208523137515523",
    "sequenceNumber": "49590338271490256608559692540925702759324208523137515523",
    "sourceEventName": "aws:kinesis:record",
    "kinesisServiceName": "cdc-source-stream"
  },
  "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Relationships:**
- Extends `KinesisRecordAttributes`
- Contains `ExtendedKinesisDecodedData`
- Used by `RecordType` implementations

---

### ExtendedKinesisStreamRecord

AWS Kinesis stream record extended with a correlation ID for tracing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlationId` | `string` | Yes | UUID for distributed tracing |
| *(inherited AWS fields)* | - | - | Standard Kinesis record fields |

**Validation Rules:**
- `correlationId` must be a valid UUID v4
- Inherits validation from AWS Kinesis record type

**Example:**
```json
{
  "kinesis": {
    "kinesisSchemaVersion": "1.0",
    "partitionKey": "users-12345",
    "sequenceNumber": "49590338271490256608559692540925702759324208523137515522",
    "data": "eyJkYXRhIjp7...}",
    "approximateArrivalTimestamp": 1705314600.123
  },
  "eventSource": "aws:kinesis",
  "eventVersion": "1.0",
  "eventID": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522",
  "eventName": "aws:kinesis:record",
  "invokeIdentityArn": "arn:aws:iam::123456789012:role/cdc-pipeline-role",
  "awsRegion": "us-east-1",
  "eventSourceARN": "arn:aws:kinesis:us-east-1:123456789012:stream/cdc-source-stream",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Relationships:**
- Extended from AWS `KinesisStreamRecord`
- Processed into `KinesisRecordAttributes`

---

### Enrichment

Data enrichment object containing organization and user context added during processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number \| null` | Yes | Organization ID (null if not resolvable) |
| `userId` | `number \| null` | Yes | User ID (null if not resolvable) |

**Validation Rules:**
- Both fields must be present (but can be null)
- When populated, values must be positive integers

**Example (fully enriched):**
```json
{
  "orgId": 100,
  "userId": 12345
}
```

**Example (org only):**
```json
{
  "orgId": 500,
  "userId": null
}
```

**Example (not resolvable):**
```json
{
  "orgId": null,
  "userId": null
}
```

**Relationships:**
- Part of `ExtendedKinesisDecodedData`
- Populated by enrichment classes
- Copied to `RecordMetadata`

---

## DynamoDB Models

### DynamoDBActionParams

Parameters for DynamoDB operations such as queries and writes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queryDescription` | `string` | Yes | Human-readable description for logging |
| `tableName` | `string` | Yes | Target DynamoDB table name |
| `pk` | `string` | Yes | Primary key value |
| `additionalColumns` | `Map<string, unknown>` | No | Additional columns for the operation |
| `disableLogging` | `boolean` | No | Flag to suppress query logging |

**Validation Rules:**
- `tableName` must be a valid DynamoDB table name
- `pk` must be a non-empty string
- `additionalColumns` keys must be valid DynamoDB attribute names

**Example:**
```json
{
  "queryDescription": "Fetch hash for deduplication check",
  "tableName": "cdc-pipeline-hash-table",
  "pk": "users-12345-v1",
  "additionalColumns": {
    "hash": "a1b2c3d4e5f6...",
    "ttl": 1705918200
  },
  "disableLogging": false
}
```

**Relationships:**
- Used by DynamoDB client wrapper
- `tableName` comes from `EnvVariables.dynamoHashTableName`

---

## Record Type Enumeration

### RecordTypeEnum

Enumeration of all supported CDC record types in the pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `CallCenterAgent` | `string` | Call center agent records |
| `CallCenterQueue` | `string` | Call center queue entries |
| `AvailabilityLog` | `string` | Agent availability log records |
| `CallStatus` | `string` | Active call status records |
| `GroupMapsLog` | `string` | Group mapping log records |
| `UserScopes` | `string` | User scope assignment records |
| `Channels` | `string` | Communication channel records |
| `Profiles` | `string` | Configuration profile records |
| `Pool` | `string` | Phone number pool records |
| `Groups` | `string` | Group definition records |
| `Users` | `string` | User account records |
| `Orgs` | `string` | Organization records |

**Example Usage:**
```typescript
// Check if a table name maps to a supported record type
const recordType = RecordTypeEnum[tableName];
if (recordType) {
  // Process the record
}

// Use in detailType construction
const detailType = `${RecordTypeEnum.Users}.${DatabaseActionEnum.UPDATE}`;
// Result: "Users.UPDATE"
```

**Relationships:**
- Used in `RecordType` implementations
- Determines enrichment strategy
- Used in EventBridge `detailType` construction

---

## Database Response Models

### ProfilesGetOrgResponse

Response type for profiles organization lookup queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization ID |
| `userId` | `number` | Yes | User ID |

**Example:**
```json
{
  "orgId": 100,
  "userId": 12345
}
```

---

### GroupsMapLogGetOrgResponse

Response type for group maps log organization lookup queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `groupId` | `number` | Yes | Group ID used for lookup |
| `orgId` | `number` | Yes | Organization ID associated with the group |

**Example:**
```json
{
  "groupId": 50,
  "orgId": 100
}
```

---

### ChannelsGetOrgAndUserResponse

Response type for channels organization and user lookup queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `msisdn` | `number` | Yes | Mobile station international subscriber directory number |
| `userId` | `number` | Yes | User ID |
| `orgId` | `number` | Yes | Organization ID |

**Example:**
```json
{
  "msisdn": 447700900123,
  "userId": 12345,
  "orgId": 100
}
```

---

## Common Use Cases

### Processing a Kinesis Batch

```typescript
// 1. Receive Kinesis records
const kinesisRecords: ExtendedKinesisStreamRecord[] = event.Records;

// 2. Decode and extract attributes
const recordAttributes: KinesisRecordAttributes[] = kinesisRecords.map(
  record => extractRecordAttributes(record)
);

// 3. Enrich with org/user context
const enrichedRecords: ExtendedKinesisRecordAttributes[] = await enricher.enrich(
  recordAttributes
);

// 4. Transform to EventBridge format
const normalizedRecords: NormalizedRecord[] = enrichedRecords.map(
  record => normalizeRecord(record)
);

// 5. Publish to EventBridge
const result = await eventBridge.putEvents(normalizedRecords);

// 6. Return failures for retry
return {
  batchItemFailures: result.failures.map(f => ({ itemIdentifier: f.eventId }))
};
```

### Enrichment Flow by Record Type

| Record Type | Enrichment Source | orgId Source | userId Source |
|-------------|-------------------|--------------|---------------|
| `Users` | Direct from data | `homeOrgId` | `id` |
| `CallCenterAgent` | Direct from data | `orgId` | `userId` (conditional) |
| `CallCenterQueue` | Direct from data | `orgId` | Always null |
| `CallStatus` | Direct from data | `orgId` | `userId` |
| `AvailabilityLog` | Direct from data | `orgId` | `userId` |
| `Pool` | Direct from data | `orgId` | `userId` |
| `UserScopes` | Direct from data | `orgId` | `userId` |
| `GroupMapsLog` | Database lookup | Via `groupId` | `userId` |
| `Profiles` | Database lookup | Via `scopeId` | `userId` |
| `Channels` | Database lookup | Via `msisdn` | Via lookup |

---

## Related Documentation

- [Record Models](./records.md) - Domain-specific record type documentation
- [Configuration Models](./configuration.md) - Environment and configuration models
- [Models Overview](./README.md) - Complete data model index