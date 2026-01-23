# Record Models

This document provides comprehensive documentation for CDC record-related models in the `cdc-pipeline` service. These models define the structure of Change Data Capture (CDC) records, their metadata, and how they flow through the pipeline from Kinesis streams to EventBridge.

## Overview

The CDC pipeline processes database change events captured from various source tables. Records flow through several stages:

1. **Ingestion**: Raw Kinesis records are decoded into structured data
2. **Enrichment**: Organization and user context is added
3. **Normalization**: Records are transformed into EventBridge-compatible format
4. **Publication**: Normalized records are sent to EventBridge

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌─────────────┐
│  Kinesis Stream │────▶│  Decode/Parse    │────▶│   Enrichment   │────▶│ EventBridge │
│  (Raw Records)  │     │  (KinesisDecoded │     │  (Extended     │     │ (Normalized │
│                 │     │   Data)          │     │   Records)     │     │  Record)    │
└─────────────────┘     └──────────────────┘     └────────────────┘     └─────────────┘
```

---

## Core Enumerations

### DatabaseActionEnum

Enum representing database CRUD operations performed on source records.

| Value | Type | Description |
|-------|------|-------------|
| `CREATE` | string | Record was inserted into the database |
| `UPDATE` | string | Existing record was modified |
| `DELETE` | string | Record was removed from the database |
| `UNKNOWN` | string | Operation type could not be determined |

**Example Usage:**
```json
{
  "operation": "UPDATE"
}
```

---

### RecordTypeEnum

Enum defining all supported CDC record types organized by domain. Each type corresponds to a specific database table being monitored for changes.

| Value | Type | Description |
|-------|------|-------------|
| `CallCenterAgent` | string | Call center agent configuration records |
| `CallCenterQueue` | string | Call center queue entries |
| `AvailabilityLog` | string | Agent availability status logs |
| `CallStatus` | string | Active call status records |
| `GroupMapsLog` | string | Group membership mapping logs |
| `UserScopes` | string | User permission scopes |
| `Channels` | string | Communication channel configurations |
| `Profiles` | string | Configuration profile settings |
| `Pool` | string | Phone number pool entries |
| `Groups` | string | User group definitions |
| `Users` | string | User account records |
| `Orgs` | string | Organization records |

**Example Usage:**
```json
{
  "recordType": "CallCenterAgent"
}
```

---

## Kinesis Record Models

### KinesisDecodedMetadata

Metadata extracted from decoded Kinesis stream records containing source database information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string | Yes | ISO 8601 timestamp when the change occurred |
| `operation` | string | Yes | Database operation type (CREATE, UPDATE, DELETE) |
| `table-name` | string | Yes | Name of the source database table |
| `schema-name` | string | Yes | Database schema containing the table |
| `record-type` | string | Yes | Type classification of the record |
| `transaction-id` | number | Yes | Database transaction identifier |
| `partition-key-type` | string | Yes | Type of partition key used |
| `commit-timestamp` | string | Yes | Timestamp when transaction was committed |

**Validation Rules:**
- `timestamp` must be valid ISO 8601 format
- `operation` must be a valid DatabaseActionEnum value
- `transaction-id` must be a positive integer

**Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "operation": "UPDATE",
  "table-name": "users",
  "schema-name": "public",
  "record-type": "Users",
  "transaction-id": 12345678,
  "partition-key-type": "schema-table",
  "commit-timestamp": "2024-01-15T10:30:00.500Z"
}
```

---

### KinesisDecodedData

Decoded data payload from Kinesis stream containing the actual record data and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | `Record<string, unknown>` | Yes | The current state of the record after the change |
| `metadata` | `KinesisDecodedMetadata` | Yes | Metadata about the change event |
| `beforeImage` | `Record<string, unknown>` | No | Previous state of the record (for UPDATE/DELETE) |

**Validation Rules:**
- `data` must be a non-null object
- `beforeImage` is required for UPDATE and DELETE operations
- `beforeImage` should be null/undefined for CREATE operations

**Example:**
```json
{
  "data": {
    "id": 12345,
    "userName": "john.doe",
    "email": "john.doe@example.com",
    "isEnabled": true
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "operation": "UPDATE",
    "table-name": "users",
    "schema-name": "public",
    "record-type": "Users",
    "transaction-id": 12345678,
    "partition-key-type": "schema-table",
    "commit-timestamp": "2024-01-15T10:30:00.500Z"
  },
  "beforeImage": {
    "id": 12345,
    "userName": "john.doe",
    "email": "john.doe@oldexample.com",
    "isEnabled": true
  }
}
```

---

### KinesisRecordMetadata

Metadata about the Kinesis record itself, used for tracing and deduplication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `partitionKey` | string | Yes | Kinesis partition key for ordering |
| `sourceEventId` | string | Yes | Unique identifier of the source event |
| `sequenceNumber` | string | Yes | Kinesis sequence number for ordering |
| `sourceEventName` | string | Yes | Name/type of the source event |
| `kinesisServiceName` | string | Yes | Name of the Kinesis service/stream |

**Validation Rules:**
- `sequenceNumber` must be a valid Kinesis sequence number
- `sourceEventId` must be unique within the stream

**Example:**
```json
{
  "partitionKey": "public.users",
  "sourceEventId": "evt-abc123-def456",
  "sequenceNumber": "49590338271490256608559692538361571095921575989136588818",
  "sourceEventName": "cdc-users-change",
  "kinesisServiceName": "cdc-kinesis-stream"
}
```

---

### KinesisRecordAttributes

Combined attributes for a Kinesis record including both data and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordData` | `KinesisDecodedData` | Yes | Decoded record data payload |
| `recordMetadata` | `KinesisRecordMetadata` | Yes | Kinesis record metadata |
| `correlationId` | string | Yes | Unique ID for distributed tracing |

**Example:**
```json
{
  "recordData": {
    "data": {
      "id": 12345,
      "userName": "john.doe"
    },
    "metadata": {
      "timestamp": "2024-01-15T10:30:00.000Z",
      "operation": "UPDATE",
      "table-name": "users",
      "schema-name": "public",
      "record-type": "Users",
      "transaction-id": 12345678,
      "partition-key-type": "schema-table",
      "commit-timestamp": "2024-01-15T10:30:00.500Z"
    },
    "beforeImage": {
      "id": 12345,
      "userName": "john.smith"
    }
  },
  "recordMetadata": {
    "partitionKey": "public.users",
    "sourceEventId": "evt-abc123-def456",
    "sequenceNumber": "49590338271490256608559692538361571095921575989136588818",
    "sourceEventName": "cdc-users-change",
    "kinesisServiceName": "cdc-kinesis-stream"
  },
  "correlationId": "corr-789xyz-012abc"
}
```

---

### ExtendedKinesisStreamRecord

AWS Kinesis stream record extended with correlation ID for distributed tracing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlationId` | string | Yes | Unique correlation ID for request tracing |

**Note:** This extends the standard AWS Kinesis StreamRecord type.

---

## Enrichment Models

### Enrichment

Data enrichment object containing organization and user context added during processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number \| null` | Yes | Organization identifier, null if not resolved |
| `userId` | `number \| null` | Yes | User identifier, null if not resolved |

**Validation Rules:**
- Both fields can be null if enrichment cannot determine the values
- When present, `orgId` and `userId` must be positive integers

**Example:**
```json
{
  "orgId": 1001,
  "userId": 5432
}
```

---

### ExtendedKinesisDecodedData

Kinesis decoded data extended with enrichment information for downstream processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | `Record<string, unknown>` | Yes | The actual record data |
| `metadata` | `KinesisDecodedMetadata` | Yes | Record metadata |
| `beforeImage` | `Record<string, unknown>` | No | Previous state of record |
| `enrichment` | `Enrichment` | Yes | Enrichment data with orgId and userId |

**Example:**
```json
{
  "data": {
    "id": 12345,
    "userName": "john.doe",
    "homeOrgId": 1001
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "operation": "UPDATE",
    "table-name": "users",
    "schema-name": "public",
    "record-type": "Users",
    "transaction-id": 12345678,
    "partition-key-type": "schema-table",
    "commit-timestamp": "2024-01-15T10:30:00.500Z"
  },
  "beforeImage": {
    "id": 12345,
    "userName": "john.smith",
    "homeOrgId": 1001
  },
  "enrichment": {
    "orgId": 1001,
    "userId": 12345
  }
}
```

---

### ExtendedKinesisRecordAttributes

Kinesis record attributes with extended decoded data including enrichment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordData` | `ExtendedKinesisDecodedData` | Yes | Extended decoded record data |
| `recordMetadata` | `KinesisRecordMetadata` | Yes | Record metadata |
| `correlationId` | string | Yes | Correlation ID for tracing |

---

## Record Metadata Models

### RecordMetadata

Comprehensive metadata associated with a CDC record event for EventBridge publication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service` | string | Yes | Service name that generated the event |
| `_version` | string | Yes | Schema version for compatibility |
| `timestamp` | string | Yes | Event timestamp in ISO 8601 format |
| `objectName` | string | Yes | Name of the database object/table |
| `schemaName` | string | Yes | Database schema name |
| `objectAction` | string | Yes | Action performed (CREATE/UPDATE/DELETE) |
| `partitionKey` | string | Yes | Kinesis partition key |
| `attemptCount` | number | Yes | Number of processing attempts |
| `orgId` | `number \| null` | Yes | Organization ID from enrichment |
| `userId` | `number \| null` | Yes | User ID from enrichment |
| `sourceEventId` | string | Yes | Source event identifier |
| `correlationId` | string | Yes | Correlation ID for tracing |
| `sourceEventName` | string | Yes | Name of the source event |
| `eventBridgeSentTimestamp` | number | Yes | Unix timestamp when sent to EventBridge |

**Validation Rules:**
- `_version` should follow semantic versioning (e.g., "1.0.0")
- `timestamp` must be valid ISO 8601 format
- `attemptCount` must be a non-negative integer
- `eventBridgeSentTimestamp` must be a valid Unix timestamp

**Example:**
```json
{
  "service": "cdc-pipeline",
  "_version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "objectName": "users",
  "schemaName": "public",
  "objectAction": "UPDATE",
  "partitionKey": "public.users",
  "attemptCount": 1,
  "orgId": 1001,
  "userId": 12345,
  "sourceEventId": "evt-abc123-def456",
  "correlationId": "corr-789xyz-012abc",
  "sourceEventName": "cdc-users-change",
  "eventBridgeSentTimestamp": 1705315800000
}
```

---

### RecordData

Data payload containing before/after states and a list of changed fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `changes` | `string[]` | Yes | List of field names that changed |
| `after` | `Record<string, unknown> \| null` | Yes | State after the change (null for DELETE) |
| `before` | `Record<string, unknown> \| null` | Yes | State before the change (null for CREATE) |

**Validation Rules:**
- For CREATE: `before` should be null, `after` contains the new record
- For UPDATE: Both `before` and `after` should be populated
- For DELETE: `after` should be null, `before` contains the deleted record
- `changes` should list only fields that actually changed

**Example (UPDATE):**
```json
{
  "changes": ["email", "lastModified"],
  "after": {
    "id": 12345,
    "userName": "john.doe",
    "email": "john.doe@newexample.com",
    "lastModified": "2024-01-15T10:30:00.000Z"
  },
  "before": {
    "id": 12345,
    "userName": "john.doe",
    "email": "john.doe@oldexample.com",
    "lastModified": "2024-01-10T08:00:00.000Z"
  }
}
```

---

## Normalized Record Models

### NormalizedRecord

Normalized CDC record structure formatted for EventBridge publication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Event source identifier (e.g., "cdc-pipeline") |
| `detailType` | string | Yes | EventBridge detail type for routing |
| `eventBusName` | string | Yes | Target EventBridge bus name |
| `detail` | object | Yes | Event detail containing data and metadata |

**Validation Rules:**
- `source` must match the service identifier
- `detailType` should follow naming conventions for event routing
- `eventBusName` must be a valid EventBridge bus ARN or name

**Example:**
```json
{
  "source": "cdc-pipeline",
  "detailType": "Users.UPDATE",
  "eventBusName": "cdc-events-bus",
  "detail": {
    "data": {
      "changes": ["email"],
      "after": {
        "id": 12345,
        "email": "john.doe@newexample.com"
      },
      "before": {
        "id": 12345,
        "email": "john.doe@oldexample.com"
      }
    },
    "metadata": {
      "service": "cdc-pipeline",
      "_version": "1.0.0",
      "timestamp": "2024-01-15T10:30:00.000Z",
      "objectName": "users",
      "schemaName": "public",
      "objectAction": "UPDATE",
      "partitionKey": "public.users",
      "attemptCount": 1,
      "orgId": 1001,
      "userId": 12345,
      "sourceEventId": "evt-abc123-def456",
      "correlationId": "corr-789xyz-012abc",
      "sourceEventName": "cdc-users-change",
      "eventBridgeSentTimestamp": 1705315800000
    }
  }
}
```

---

## Abstract Base Classes

### RecordType

Abstract base class for CDC record type processing. Each domain-specific record type extends this class.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordData` | `ExtendedKinesisDecodedData` | Yes | Decoded Kinesis record data |
| `recordMetadata` | `KinesisRecordMetadata` | Yes | Kinesis record metadata |
| `serviceName` | string | Yes | Name of the processing service |
| `eventBusName` | string | Yes | Target EventBridge bus name |
| `recordType` | string | Yes | Abstract record type identifier |

**Abstract Methods:**
- `getSchemaVersion()`: Returns the schema version for this record type
- `buildDataMapper()`: Transforms raw data into domain-specific format
- `getEventDetailType()`: Returns the EventBridge detail type

---

### RecordsEnrichment

Abstract base class for all record enrichment implementations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `records` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records to be enriched |

**Abstract Methods:**
- `enrich()`: Enriches records with organization and user context

---

## Domain-Specific Record Types

### UsersRecord

Record class for user account CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string \| null` | No | User identifier |
| `type` | `string \| null` | No | User type classification |
| `permissionLevel` | `string \| null` | No | Permission level assigned |
| `orgId` | `string \| null` | No | Home organization ID |
| `userName` | `string \| null` | No | Username for login |
| `encUserName` | `string \| null` | No | Encrypted username |
| `maxSequentialLogins` | `string \| null` | No | Maximum concurrent login sessions |
| `firstName` | `string \| null` | No | User's first name |
| `middleNames` | `string \| null` | No | User's middle names |
| `lastName` | `string \| null` | No | User's last name |
| `passwordSetDate` | `string \| null` | No | Date password was last changed |
| `primaryMobile` | `string \| null` | No | Primary mobile phone number |
| `isPrimaryMobileAuthorised` | boolean | No | Whether mobile is verified |
| `pin` | `string \| null` | No | User PIN code |
| `isEnabled` | boolean | No | Whether account is active |

**Record Type:** `RecordTypeEnum.Users`

**Example:**
```json
{
  "id": "12345",
  "type": "standard",
  "permissionLevel": "admin",
  "orgId": "1001",
  "userName": "john.doe",
  "firstName": "John",
  "lastName": "Doe",
  "isEnabled": true,
  "isPrimaryMobileAuthorised": true
}
```

---

### OrgsRecord

Record class for organization CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgsData` | `ExtendedKinesisDecodedData` | Yes | The organization data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier (Orgs) |

**Record Type:** `RecordTypeEnum.Orgs`

---

### GroupsRecord

Record class for user group definition CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `groupsData` | `ExtendedKinesisDecodedData` | Yes | The groups data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier (Groups) |

**Record Type:** `RecordTypeEnum.Groups`

---

### ProfilesRecord

Record representing configuration profiles with scoped settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scopeId` | `string \| null` | No | Scope identifier (org or user ID) |
| `scope` | `string \| null` | No | Scope type (User, Org, System) |
| `isRef` | boolean | No | Whether this is a reference profile |
| `category` | `string \| null` | No | Main category of the setting |
| `name` | `string \| null` | No | Variable/setting name |
| `value` | `string \| null` | No | Variable/setting value |
| `availableTo` | `string \| null` | No | Availability scope restriction |
| `publishedAs` | `string \| null` | No | Published name for external use |
| `freeswitchName` | `string \| null` | No | FreeSWITCH variable name mapping |
| `modifiedTime` | `string \| null` | No | Last modification timestamp |

**Record Type:** `RecordTypeEnum.Profiles`

**Example:**
```json
{
  "scopeId": "1001",
  "scope": "Org",
  "isRef": false,
  "category": "telephony",
  "name": "max_call_duration",
  "value": "3600",
  "availableTo": "all",
  "publishedAs": "maxCallDuration",
  "freeswitchName": "max_duration",
  "modifiedTime": "2024-01-15T10:30:00.000Z"
}
```

---

### ChannelsRecord

Record class for communication channel configuration CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channelsData` | `ExtendedKinesisDecodedData` | Yes | The channels data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier (Channels) |

**Record Type:** `RecordTypeEnum.Channels`

---

### PoolRecord

Record representing a phone number pool entry with provider and billing information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string \| null` | No | MSISDN phone number |
| `subTypeId` | `string \| null` | No | Sub-type identifier |
| `countryCode` | `string \| null` | No | Cached country code |
| `prefixCode` | `string \| null` | No | Number prefix code |
| `providerId` | `string \| null` | No | Telecom provider identifier |
| `pciCompliance` | `string \| null` | No | PCI compliance status |
| `chargeBandId` | `string \| null` | No | Billing charge band identifier |
| `numberProfileId` | `string \| null` | No | Number profile identifier |
| `specialType` | `string \| null` | No | Special number type (e.g., toll-free) |
| `ipAddressFor999` | `string \| null` | No | IP address for emergency calls |
| `orgId` | `string \| null` | No | Organization identifier |
| `userId` | `string \| null` | No | User identifier |
| `label` | `string \| null` | No | Human-readable label |
| `description` | `string \| null` | No | Description of the number |
| `auxiliaryRedirect` | `string \| null` | No | Auxiliary redirect configuration |

**Record Type:** `RecordTypeEnum.Pool`

**Example:**
```json
{
  "number": "+14155551234",
  "countryCode": "US",
  "prefixCode": "415",
  "providerId": "twilio-01",
  "pciCompliance": "compliant",
  "chargeBandId": "standard",
  "orgId": "1001",
  "userId": "12345",
  "label": "Main Support Line",
  "description": "Primary customer support number"
}
```

---

### CallStatusRecord

Record representing the current status of an active call with SIP and codec details.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | `string \| null` | No | Call UUID |
| `otherLegUuid` | `string \| null` | No | UUID of the other call leg |
| `devId` | `string \| null` | No | Device identifier |
| `userId` | `string \| null` | No | User identifier |
| `carrierName` | `string \| null` | No | Telecom carrier name |
| `carrierId` | `string \| null` | No | Carrier identifier |
| `carrierGatewayId` | `string \| null` | No | Carrier gateway identifier |
| `orgId` | `string \| null` | No | Organization identifier |
| `sipCallId` | `string \| null` | No | SIP Call-ID header value |
| `sipFromTag` | `string \| null` | No | SIP From tag |
| `sipToTag` | `string \| null` | No | SIP To tag |
| `sipFromUri` | `string \| null` | No | SIP From URI |
| `sipRequestUri` | `string \| null` | No | SIP Request URI |
| `sipContactUri` | `string \| null` | No | SIP Contact URI |
| `freeswitchIp` | `string \| null` | No | FreeSWITCH server IP address |

**Record Type:** `RecordTypeEnum.CallStatus`

**Example:**
```json
{
  "uuid": "call-uuid-abc123",
  "otherLegUuid": "call-uuid-def456",
  "userId": "12345",
  "carrierName": "Carrier-A",
  "carrierId": "carrier-01",
  "orgId": "1001",
  "sipCallId": "abc123@sip.example.com",
  "sipFromUri": "sip:+14155551234@sip.example.com",
  "freeswitchIp": "10.0.1.50"
}
```

---

### CallCenterAgentRecord

Record class for call center agent CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `callCenterAgentData` | `ExtendedKinesisDecodedData` | Yes | The call center agent data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier |

**Record Type:** `RecordTypeEnum.CallCenterAgent`

---

### CallCenterQueueRecord

Record representing a call center queue entry with caller information, callback settings, and queue positioning.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | `string \| null` | No | Unique identifier for the queue record |
| `coreUuid` | `string \| null` | No | Core system UUID |
| `createdTime` | `string \| null` | No | Time when the record was created |
| `stateUpdatedTime` | `string \| null` | No | ISO timestamp when state was last updated |
| `headOfQueueTime` | `string \| null` | No | ISO timestamp when caller reached head of queue |
| `agentUuid` | `string \| null` | No | UUID of assigned agent |
| `freeswitchIp` | `string \| null` | No | FreeSWITCH machine IP address |
| `freeswitchIpInternal` | `string \| null` | No | FreeSWITCH internal machine IP |
| `queueName` | `string \| null` | No | Name of the queue |
| `status` | `string \| null` | No | Current status of the queue entry |
| `isPositionLocked` | boolean | No | Whether position in queue is locked |
| `orgId` | `string \| null` | No | Organization identifier |
| `priority` | `string \| null` | No | Priority level in queue |
| `position` | `string \| null` | No | Current position in queue |
| `dialAttempts` | `string \| null` | No | Number of dial attempts made |

**Record Type:** `RecordTypeEnum.CallCenterQueue`

**Example:**
```json
{
  "uuid": "queue-entry-abc123",
  "coreUuid": "core-uuid-xyz789",
  "createdTime": "2024-01-15T10:25:00.000Z",
  "stateUpdatedTime": "2024-01-15T10:30:00.000Z",
  "headOfQueueTime": null,
  "agentUuid": null,
  "queueName": "support-queue",
  "status": "waiting",
  "isPositionLocked": false,
  "orgId": "1001",
  "priority": "normal",
  "position": "5",
  "dialAttempts": "0"
}
```

---

### AvailabilityLogRecord

Record class for agent availability log CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `availabilityLogData` | `ExtendedKinesisDecodedData` | Yes | The availability log data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier |

**Record Type:** `RecordTypeEnum.AvailabilityLog`

---

### GroupMapsLogRecord

Record class for group membership mapping log CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `groupMapsLogData` | `ExtendedKinesisDecodedData` | Yes | The group maps log data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier |

**Record Type:** `RecordTypeEnum.GroupMapsLog`

---

### UserScopesRecord

Record class for user permission scopes CDC events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `usersData` | `ExtendedKinesisDecodedData` | Yes | The user scopes data |
| `recordType` | `RecordTypeEnum` | Yes | Record type identifier |

**Record Type:** `RecordTypeEnum.UserScopes`

---

## Enrichment Classes

### UsersEnrichment

Enrichment class for Users records that maps HomeOrgID to orgId and ID to userId.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `usersRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records for users |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier (Users) |

**Enrichment Logic:**
- `orgId` is extracted from the record's `HomeOrgID` field
- `userId` is extracted from the record's `ID` field

---

### CallCenterAgentEnrichment

Enrichment class for CallCenterAgent records with conditional user ID assignment based on agent type.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `callCenterAgentRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |

**Enrichment Logic:**
- `userId` is assigned based on agent type conditions
- `orgId` is extracted from the agent's organization assignment

---

### CallCenterQueueEnrichment

Enrichment class for CallCenterQueue records that extracts organization ID only.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `callCenterQueueRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |

**Enrichment Logic:**
- `userId` is always null (queue entries are not user-specific)
- `orgId` is extracted from the record's organization field

---

### GroupMapsLogEnrichment

Enrichment class for GroupMapsLog records that adds organization and user IDs based on group mappings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `groupMapsLogRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |
| `groupMapsLogRepository` | `GroupMapsLogRepository` | Yes | Repository for database lookups |

**Enrichment Logic:**
- Performs database lookup to resolve `orgId` from group ID
- `userId` is extracted from the record if available

---

### UserScopesEnrichment

Enrichment class for UserScopes records that extracts organization and user IDs directly from record data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userScopesRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |

---

### CallStatusEnrichment

Enrichment class for CallStatus records that extracts organization and user IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `callStatusRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |

---

### AvailabilityLogEnrichment

Enrichment class for AvailabilityLog records that extracts organization and user IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `availabilityLogRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |

---

### PoolEnrichment

Enrichment class for Pool records that extracts organization and user IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `poolRecords` | `KinesisRecordAttributes[]` | Yes | Array of Kinesis records |
| `recordsType` | `RecordTypeEnum` | Yes | Type identifier |

---

## Database Response Types

### ProfilesGetOrgResponse

Database response for profiles organization lookup.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | number | Yes | User identifier |
| `orgId` | number | Yes | Organization identifier |

---

### GroupsMapLogGetOrgResponse

Database response for group maps log organization lookup.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `groupId` | number | Yes | Group identifier |
| `orgId` | number | Yes | Organization identifier |

---

### ChannelsGetOrgAndUserResponse

Database response for channels organization and user lookup.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `msisdn` | number | Yes | MSISDN phone number |
| `orgId` | number | Yes | Organization identifier |
| `userId` | number | Yes | User identifier |

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Record Flow Relationships                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐
│ KinesisDecodedData│
│   - data          │──────┐
│   - metadata      │      │
│   - beforeImage   │      │
└───────────────────┘      │
         │                 │
         │ extended by     │
         ▼                 │
┌───────────────────────┐  │
│ExtendedKinesisDecoded │  │
│Data                   │  │
│   - enrichment ───────┼──┼───▶ ┌────────────┐
└───────────────────────┘  │     │ Enrichment │
         │                 │     │  - orgId   │
         │ used by         │     │  - userId  │
         ▼                 │     └────────────┘
┌───────────────────────┐  │
│KinesisRecordAttributes│  │
│   - recordData ───────┼──┘
│   - recordMetadata ───┼──────▶ ┌─────────────────────┐
│   - correlationId     │        │ KinesisRecordMetadata│
└───────────────────────┘        │   - partitionKey     │
         │                       │   - sourceEventId    │
         │ processed by          │   - sequenceNumber   │
         ▼                       └─────────────────────┘
┌───────────────────────┐
│    RecordType         │◀─────── Abstract Base
│   (Abstract Class)    │
│   - recordData        │
│   - recordMetadata    │
│   - serviceName       │
│   - eventBusName      │
└───────────────────────┘
         │
         │ extended by
         ▼
┌────────────────────────────────────────────────────────┐
│              Domain-Specific Record Types               │
├──────────────┬──────────────┬──────────────┬───────────┤
│ UsersRecord  │ProfilesRecord│PoolRecord   │CallStatus │
│ OrgsRecord   │ChannelsRecord│GroupsRecord │Record     │
│ CallCenter   │GroupMapsLog  │UserScopes   │Availability│
│ AgentRecord  │Record        │Record       │LogRecord  │
│ CallCenter   │              │             │           │
│ QueueRecord  │              │             │           │
└──────────────┴──────────────┴──────────────┴───────────┘
         │
         │ transformed to
         ▼
┌───────────────────────┐
│   NormalizedRecord    │
│   - source            │
│   - detailType        │
│   - eventBusName      │
│   - detail ───────────┼──────▶ ┌────────────────┐
└───────────────────────┘        │  RecordData    │
                                 │   - changes    │
                                 │   - after      │
                                 │   - before     │
                                 └────────────────┘
                                         │
                                         │ contains
                                         ▼
                                 ┌────────────────┐
                                 │ RecordMetadata │
                                 │   - service    │
                                 │   - _version   │
                                 │   - timestamp  │
                                 │   - objectName │
                                 │   - orgId      │
                                 │   - userId     │
                                 │   - ...        │
                                 └────────────────┘
```

---

## Common Use Cases

### Processing a User Update

```typescript
// 1. Receive Kinesis record
const kinesisRecord: KinesisRecordAttributes = {
  recordData: {
    data: { id: 12345, email: "new@example.com" },
    metadata: { operation: "UPDATE", "table-name": "users" },
    beforeImage: { id: 12345, email: "old@example.com" }
  },
  recordMetadata: { partitionKey: "public.users" },
  correlationId: "corr-123"
};

// 2. Enrich with org/user context
const enrichment = new UsersEnrichment([kinesisRecord]);
const enrichedRecords = await enrichment.enrich();

// 3. Create domain record
const usersRecord = new UsersRecord(enrichedRecords[0]);

// 4. Normalize for EventBridge
const normalized = usersRecord.normalize();
```

### Handling a Call Center Queue Entry

```typescript
// Queue entries only have orgId, userId is always null
const queueEnrichment = new CallCenterQueueEnrichment([queueRecord]);
const enriched = await queueEnrichment.enrich();

// enriched[0].recordData.enrichment = { orgId: 1001, userId: null }
```

---

## Related Documentation

- [Events Documentation](./events.md) - EventBridge event structures
- [Configuration Documentation](./configuration.md) - Environment and service configuration
- [Models Overview](./README.md) - Complete model index