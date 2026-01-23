# Infrastructure Models

This document covers the infrastructure models used in Sapien for server operations, request handling, logging, event tracking, and internal system functionality.

## Overview

Infrastructure models provide the foundation for:

- **WebSocket Server Operations**: Managing ESL (Event Socket Library) connections and real-time communication
- **Event Logging**: Audit trails and system event tracking
- **Rate Limiting**: API usage control per organisation
- **Database Utilities**: DBAL entity field mapping and connection management
- **Bundle Configuration**: Symfony bundle and kernel setup

## Related Documentation

- [Core Models](./core-models.md) - User, Organisation, and domain entities
- [Authentication Models](./authentication-models.md) - OAuth tokens, sessions, and security

---

## WebSocket Server Models

### Server

WebSocket server implementing `MessageComponentInterface` for ESL (Event Socket Library) Listener operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `clients` | `\SplObjectStorage` | Yes | Storage container for connected client connections |
| `handler` | `Handler` | Yes | Handler instance for processing messages and connections |

**Purpose**: Manages WebSocket connections for real-time ESL event streaming, allowing clients to receive telephony events.

**Relationships**:
- Contains one `Handler` instance for message processing
- Manages multiple client connections via `\SplObjectStorage`

**Example Usage**:
```php
$server = new Server();
$server->onOpen($connection);
$server->onMessage($connection, $message);
$server->onClose($connection);
```

---

### Handler

Handles WebSocket connection logic, traffic recording, and command processing for ESL Listener.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordTrafficForNewConnections` | `bool` | Yes | Whether traffic for new connections should be recorded |
| `recordedTraffic` | `array` | Yes | Recorded traffic for connections, keyed by `resourceId` |
| `openConnections` | `array` | Yes | List of currently open connections |
| `customResponses` | `array` | Yes | Collection of custom responses in nested array format |
| `uuid` | `string\|bool` | Yes | UUID value for replacing `CallControlUuids` in responses |

**Purpose**: Central handler for processing incoming WebSocket messages, managing traffic capture for debugging, and defining custom responses for testing.

**Example JSON State**:
```json
{
  "recordTrafficForNewConnections": true,
  "recordedTraffic": {
    "conn_12345": [
      {
        "source": "CLIENT",
        "type": "MESSAGE",
        "properties": {"event": "CHANNEL_CREATE"}
      }
    ]
  },
  "openConnections": ["conn_12345", "conn_67890"],
  "customResponses": {
    "api/originate": {
      "response": "+OK"
    }
  },
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### RecordedTrafficEntry

Implicit data structure for recorded traffic entries used in debugging and testing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `string` | Yes | Source of the traffic: `CLIENT` or `SERVER` |
| `type` | `string` | Yes | Type of traffic: `CONNECTION`, `MESSAGE`, `RESPONSE`, `DISCONNECT` |
| `properties` | `array` | Yes | Array of message properties and payload data |

**Purpose**: Captures detailed traffic information for debugging WebSocket communications.

**Validation Rules**:
- `source` must be one of: `CLIENT`, `SERVER`
- `type` must be one of: `CONNECTION`, `MESSAGE`, `RESPONSE`, `DISCONNECT`

**Example JSON**:
```json
{
  "source": "CLIENT",
  "type": "MESSAGE",
  "properties": {
    "command": "api",
    "args": "originate user/1000 &park()",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

### CommandMessage

Implicit JSON structure for command messages sent to the WebSocket server.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `string` | Yes | Command type identifier |
| `value` | `mixed` | No | Command value/payload (type depends on command) |

**Purpose**: Standardised format for control commands sent to the ESL WebSocket server.

**Validation Rules**:
- `type` must be one of:
  - `START_CAPTURING_TRAFFIC`
  - `RETRIEVE_CAPTURED_TRAFFIC`
  - `STOP_CAPTURING_TRAFFIC`
  - `DEFINE_CUSTOM_RESPONSES`

**Example JSON - Start Capturing**:
```json
{
  "type": "START_CAPTURING_TRAFFIC",
  "value": {
    "captureCallControlUuid": true
  }
}
```

**Example JSON - Define Custom Responses**:
```json
{
  "type": "DEFINE_CUSTOM_RESPONSES",
  "value": {
    "api/originate": {
      "response": "+OK 550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

---

### StartCapturingTrafficValue

Implicit structure for the `START_CAPTURING_TRAFFIC` command value.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `captureCallControlUuid` | `bool` | Yes | Whether to capture and track call control UUIDs |

**Example JSON**:
```json
{
  "captureCallControlUuid": true
}
```

---

### Responses

Static utility class for generating ESL event response strings.

**Purpose**: Provides factory methods for creating standardised ESL response strings for various telephony events.

**Note**: This is a utility class with no instance fields - all methods are static.

---

## Event Logging Models

### EventLog

Audit/event logging entity for tracking system events and user actions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `int` | Yes (auto) | Primary key, auto-generated |
| `organisationId` | `int` | Yes | Organisation ID where event occurred |
| `userId` | `int` | Yes | User ID who performed the action |
| `sudoUserId` | `int` | No | Sudo user ID if action performed via impersonation |
| `level` | `string` | Yes | Log level (e.g., `Message`, `Warning`, `Error`) |
| `context` | `string` | Yes | Event context category |
| `action` | `string` | Yes | Specific action performed |
| `message` | `string` | Yes | Human-readable event description |
| `extraData` | `array` | No | Additional JSON data for the event |
| `dateTime` | `DateTime` | Yes | Event timestamp |
| `lowResEpoch` | `DateTime` | Yes | Low resolution epoch (10-second intervals) for grouping |

**Purpose**: Provides a complete audit trail for compliance, security monitoring, and troubleshooting.

**Context Values**:
- `Security` - Authentication and authorisation events
- `Archiving` - Recording and retention operations
- `Resources` - Resource access and modifications

**Action Examples**:
- `Auth:Login` - User login attempt
- `Auth:Logout` - User logout
- `DeleteRequest` - Data deletion request
- `Download` - File download

**Validation Rules**:
- `organisationId` must reference valid organisation
- `userId` must reference valid user
- `level` should follow standard log levels

**Example JSON**:
```json
{
  "id": 12345,
  "organisationId": 100,
  "userId": 5001,
  "sudoUserId": null,
  "level": "Message",
  "context": "Security",
  "action": "Auth:Login",
  "message": "User successfully logged in",
  "extraData": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "two_factor_used": true
  },
  "dateTime": "2024-01-15T14:30:00Z",
  "lowResEpoch": "2024-01-15T14:30:00Z"
}
```

**Relationships**:
- References `User` via `userId`
- References `Organisation` via `organisationId`
- Optionally references sudo `User` via `sudoUserId`

---

### EventLogRepositoryInterface

Interface defining event logging operations for creating audit trail entries.

**Purpose**: Defines contract for logging various system events including authentication, file access, and data operations.

**Key Operations**:

| Method Context | Parameters | Description |
|----------------|------------|-------------|
| Login Event | `organisation_id`, `user_id`, `two_factor_authentication_used`, `successful` | Log authentication attempts |
| Recording Access | `organisation_id`, `user_id`, `retention_uuid`, `accessReason`, `action`, `message` | Log recording file access |
| Analytics Download | `organisation_id`, `user_id`, `analytics_uuid` | Log analytics file download |
| Delete Request | `organisation_id`, `user_id`, `reason`, `reference`, `uuid_map` | Log data deletion requests |
| Legal Hold | `organisation_id`, `user_id`, `channel_uuids`, `reason` | Log legal hold operations |

---

## Rate Limiting Models

### OrganisationApiRateLimit

Rate limiting configuration and state for controlling API access per organisation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `organisationId` | `int` | Yes | Organisation ID (primary key) |
| `requestLimit` | `int` | No | Maximum requests allowed; `null` or `0` for unlimited |
| `resetSeconds` | `int` | Yes | Seconds until rate limit window resets |
| `nextReset` | `DateTime` | No | DateTime when current rate limit window resets |
| `requests` | `int` | Yes | Current request count in the window |

**Purpose**: Tracks and enforces API rate limits to prevent abuse and ensure fair resource usage.

**Validation Rules**:
- `requestLimit` of `null` or `0` indicates unlimited access
- `requests` must be non-negative
- `resetSeconds` must be positive
- `nextReset` must be in the future when active

**Example JSON**:
```json
{
  "organisationId": 100,
  "requestLimit": 1000,
  "resetSeconds": 3600,
  "nextReset": "2024-01-15T15:00:00Z",
  "requests": 247
}
```

**Database Mapping** (OrgAPIRateLimit table):

| Entity Field | Database Column |
|--------------|-----------------|
| `organisationId` | `OrgID` |
| `requestLimit` | Read from `Orgs.APIRequestLimit` |
| `resetSeconds` | Read from `Orgs.APIResetSeconds` |
| `nextReset` | `NextReset` |
| `requests` | `Requests` |

---

## Database Table Models

### DeleteRequest (Database Table)

Archiving delete request record stored in `ArchivingRetention.DeleteRequest_X` tables.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `ExternalReference` | `string` | Yes | External reference identifier for tracking |
| `Time` | `int` | Yes | Unix timestamp of request creation |
| `OrgID` | `int` | Yes | Organisation ID |
| `UserID` | `int` | Yes | User ID who made the request |
| `AuditLogID` | `int` | Yes | Associated event log entry ID |
| `State` | `string` | Yes | Current request state |

**Purpose**: Tracks data deletion requests for GDPR/compliance purposes.

**Relationships**:
- Has many `DeleteRequestItems`
- References `EventLog` via `AuditLogID`

---

### DeleteRequestItems (Database Table)

Individual items within a delete request stored in `ArchivingRetention.DeleteRequestItems_X`.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `OrgID` | `int` | Yes | Organisation ID |
| `DeleteRequestID` | `int` | Yes | Parent delete request ID |
| `RetentionID` | `int` | Yes | Retention record ID to delete |

**Relationships**:
- Belongs to `DeleteRequest` via `DeleteRequestID`
- References retention record via `RetentionID`

---

### Audit (Database Table)

Audit log for file access stored in `ArchivingRetention.Audit_X` tables.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `OrgID` | `int` | Yes | Organisation ID |
| `Type` | `string` | Yes | File type: `recording`, `call-analytics` |
| `UUID` | `uuid` | Yes | File UUID being accessed |
| `Action` | `string` | Yes | Action performed (e.g., `Download`) |
| `Time` | `datetime` | Yes | Action timestamp |
| `AuditLogID` | `int` | Yes | Associated event log ID |

**Purpose**: Tracks all access to archived files for compliance auditing.

---

## Database Utility Models

### DbalEntityFieldsCollection

Utility class for managing bidirectional field name mappings between serialised (API) and database representations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `serialised` | `array` | Yes | Map of serialised names to database column names |
| `database` | `array` | Yes | Map of database column names to serialised names |
| `values` | `array` | Yes | Map of hash keys to field values |

**Purpose**: Provides consistent field name translation when moving data between API responses and database storage.

**Example Usage**:
```php
$collection = new DbalEntityFieldsCollection();
$collection->addField('organisationId', 'OrgID');

// Get database column name
$dbColumn = $collection->getDatabaseName('organisationId'); // Returns 'OrgID'

// Get serialised name
$apiField = $collection->getSerialisedName('OrgID'); // Returns 'organisationId'
```

---

### DbalEntityInterface

Interface for DBAL entities that provide field collections.

**Purpose**: Contract ensuring entities can expose their field mappings for consistent serialisation.

---

### DbalRepositoryConnectionInterface

Interface for DBAL repository connection configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection` | `Doctrine\DBAL\Connection` | Yes | Database connection instance |
| `cache` | `Doctrine\Common\Cache\PhpFileCache` | Yes | PHP file cache instance |

**Purpose**: Defines contract for repositories needing database connectivity with caching support.

---

### SwitchableDatabaseConnectionInterface

Interface for connections that can switch databases at runtime.

| Method Parameter | Type | Description |
|------------------|------|-------------|
| `database_name` | `string` | Name of database to switch to |

**Purpose**: Supports multi-tenant architectures where connection needs to switch between databases dynamically.

---

## Symfony Bundle Models

### AppKernel

Symfony application kernel for configuring bundles and dependency injection container.

**Purpose**: Bootstrap class that registers all bundles and configures the Symfony container.

---

### RedmatterSapienBundle

Main Sapien bundle that registers custom Doctrine types.

**Purpose**: Registers custom DBAL types including `pkdatetime` and `uuid`.

**Registered Types**:
- `PrimaryKeyDateTimeType` as `pkdatetime`
- `UuidType` as `uuid`

---

### RedmatterUserBundle

Bundle for user-related functionality.

**Purpose**: Provides user management services and entities.

---

### RedmatterBlobStorageBundle

Bundle for blob storage functionality.

**Purpose**: Provides services for storing and retrieving binary large objects (recordings, files).

---

### RedmatterHelloBundle

Development/test bundle loaded only in `dev`, `test`, and `local` environments.

**Purpose**: Provides test endpoints and development utilities.

---

## Custom Doctrine Types

### PrimaryKeyDateTimeType

Custom Doctrine DBAL type for primary key datetime fields.

**Type Name**: `pkdatetime`

**Purpose**: Handles datetime values used as part of composite primary keys with specific formatting requirements.

---

### UuidType

Custom Doctrine DBAL type for UUID fields.

**Type Name**: `uuid`

**Purpose**: Handles UUID storage and conversion between PHP and database representations.

---

## Exception Models

### EndOfWorldErrorException

Custom REST exception for invalid error level validation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `HTTP_STATUS_CODE` | `int` | Yes (const) | HTTP status code to return |
| `CODE` | `string` | Yes (const) | Error code identifier |
| `MESSAGE` | `string` | Yes (const) | Error message text |

**Purpose**: Thrown when an invalid or catastrophic error level is encountered.

---

## Voter Models

### AbstractVoter

Abstract base class for Symfony security voters.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allowed_roles` | `array` | Yes | List of roles permitted by this voter |
| `supported_attributes` | `array` | Yes | List of attributes this voter handles |
| `supported_classes` | `array` | Yes | List of entity classes this voter supports |
| `logger` | `LoggerInterface` | Yes | PSR logger for debugging authorisation |

**Purpose**: Provides base implementation for custom security voters that determine access permissions.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WebSocket Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐         ┌──────────┐         ┌───────────────────┐   │
│  │  Server  │────────▶│ Handler  │────────▶│RecordedTrafficEntry│   │
│  └──────────┘         └──────────┘         └───────────────────┘   │
│       │                    │                                         │
│       │                    ▼                                         │
│       │              ┌──────────────┐                               │
│       │              │CommandMessage│                               │
│       │              └──────────────┘                               │
│       ▼                                                              │
│  ┌──────────┐                                                       │
│  │ Responses│ (static utility)                                       │
│  └──────────┘                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        Event Logging                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐     ┌─────────────────┐                       │
│  │    EventLog      │◀────│DeleteRequest    │                       │
│  │                  │     │(AuditLogID)     │                       │
│  │  - organisationId│     └────────┬────────┘                       │
│  │  - userId        │              │                                 │
│  │  - context       │              ▼                                 │
│  │  - action        │     ┌─────────────────┐                       │
│  └──────────────────┘     │DeleteRequestItems│                       │
│           ▲               └─────────────────┘                       │
│           │                                                          │
│  ┌────────┴───────┐                                                 │
│  │  Audit Table   │                                                 │
│  │  (AuditLogID)  │                                                 │
│  └────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        Rate Limiting                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────┐         ┌──────────────────┐          │
│  │ OrganisationApiRateLimit│◀────────│   Orgs Table     │          │
│  │                         │         │ - APIRequestLimit │          │
│  │  - organisationId       │         │ - APIResetSeconds │          │
│  │  - requestLimit         │         └──────────────────┘          │
│  │  - resetSeconds         │                                        │
│  │  - nextReset            │                                        │
│  │  - requests             │                                        │
│  └─────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    DBAL Utilities                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────┐                                        │
│  │ DbalEntityFieldsCollection│◀──implements──┌──────────────────┐   │
│  │                         │                 │DbalEntityInterface│   │
│  │  - serialised[]         │                 └──────────────────┘   │
│  │  - database[]           │                                        │
│  │  - values[]             │                                        │
│  └─────────────────────────┘                                        │
│                                                                      │
│  ┌─────────────────────────────────┐                                │
│  │DbalRepositoryConnectionInterface│                                │
│  │                                 │                                 │
│  │  - connection                   │                                 │
│  │  - cache                        │                                 │
│  └─────────────────────────────────┘                                │
│                                                                      │
│  ┌─────────────────────────────────────┐                            │
│  │SwitchableDatabaseConnectionInterface│                            │
│  │                                     │                             │
│  │  + switchDatabase(name)            │                             │
│  └─────────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Common Use Cases

### 1. Recording API Request Rate Limiting

```php
// Check rate limit before processing request
$rateLimit = $rateLimitRepo->findByOrganisationId($orgId);

if ($rateLimit->requests >= $rateLimit->requestLimit) {
    if (new DateTime() < $rateLimit->nextReset) {
        throw new RateLimitExceededException();
    }
    // Reset the window
    $rateLimit->requests = 0;
    $rateLimit->nextReset = (new DateTime())->add(
        new DateInterval("PT{$rateLimit->resetSeconds}S")
    );
}

$rateLimit->requests++;
$rateLimitRepo->save($rateLimit);
```

### 2. Logging a Security Event

```php
$eventLog = new EventLog();
$eventLog->setOrganisationId($user->getOrganisationId());
$eventLog->setUserId($user->getId());
$eventLog->setLevel('Message');
$eventLog->setContext('Security');
$eventLog->setAction('Auth:Login');
$eventLog->setMessage('User logged in successfully');
$eventLog->setExtraData([
    'ip_address' => $request->getClientIp(),
    'two_factor_used' => true
]);
$eventLog->setDateTime(new DateTime());

$eventLogRepo->save($eventLog);
```

### 3. Capturing WebSocket Traffic for Debugging

```php
// Start capturing
$handler->handleCommand([
    'type' => 'START_CAPTURING_TRAFFIC',
    'value' => ['captureCallControlUuid' => true]
]);

// ... traffic occurs ...

// Retrieve captured traffic
$traffic = $handler->handleCommand([
    'type' => 'RETRIEVE_CAPTURED_TRAFFIC',
    'value' => null
]);

// Stop capturing
$handler->handleCommand([
    'type' => 'STOP_CAPTURING_TRAFFIC',
    'value' => null
]);
```