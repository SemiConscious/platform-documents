# CDR Data Models

> **Documentation for CDR processing models and normalized CDR schemas**

This document covers the core data models used for Call Detail Record (CDR) processing, storage, and normalization in the platform-dgapi service.

## Overview

The CDR data model system handles the ingestion, normalization, and storage of call detail records. CDRs flow through a pipeline where they are received as XML, normalized into a standard format, and stored for processing by various task handlers.

## Entity Relationship Diagram

```
┌─────────────────────┐
│  normalized_cdrs    │
│  ─────────────────  │
│  id (PK)            │
│  xml                │
│  uuid               │
│  TableSuffix        │
│  rmOrgID            │
└─────────┬───────────┘
          │
          │ 1:N
          ▼
┌─────────────────────┐       ┌─────────────────────┐
│     Task_Model      │──────▶│    tasks_error      │
│  ─────────────────  │  1:1  │  ─────────────────  │
│  id (PK)            │       │  id_tasks (FK)      │
│  id_normalized_cdrs │       │  description        │
│  task_type          │       │  first_error_date   │
│  done               │       │  last_error_date    │
│  retry              │       └─────────────────────┘
└─────────┬───────────┘
          │ 1:1
          ▼
┌─────────────────────┐
│    tasks_data       │
│  ─────────────────  │
│  id_tasks (FK)      │
│  xml_fragment       │
└─────────────────────┘
```

---

## Core Storage Models

### normalized_cdrs

Primary storage table for normalized Call Detail Records. Each record contains the complete CDR data in XML format with metadata for efficient querying and partitioning.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | int | Yes | Primary key (idNormalizedCdrs), auto-incremented |
| `xml` | text | Yes | Complete XML content of the normalized CDR |
| `uuid` | binary(16) | Yes | Unique identifier stored as unhexed binary for efficient storage |
| `TableSuffix` | string | Yes | Date-based table suffix in YYYYMMDD format for partitioning |
| `rmOrgID` | int | Yes | Organization ID that owns this CDR |

#### Validation Rules

- `uuid` must be a valid UUID converted to binary(16) using UNHEX()
- `TableSuffix` must follow YYYYMMDD format (e.g., "20240115")
- `rmOrgID` must reference a valid organization
- `xml` must contain valid XML conforming to the normalized CDR schema

#### Example Record

```json
{
  "id": 4582901,
  "xml": "<?xml version=\"1.0\"?><cdr><data><uuid>a1b2c3d4-e5f6-7890-abcd-ef1234567890</uuid><rmOrgID>1001</rmOrgID><StartEpoch>1705312800</StartEpoch></data></cdr>",
  "uuid": "0xA1B2C3D4E5F67890ABCDEF1234567890",
  "TableSuffix": "20240115",
  "rmOrgID": 1001
}
```

#### Common Use Cases

- Storing incoming CDRs after normalization
- Querying CDRs by organization and date range
- Retrieving CDR XML for task processing
- Partitioning data by date for performance optimization

---

### tasks_data

Stores additional XML data fragments associated with tasks. Used when task-specific data exceeds what can be stored in the main task record or requires structured XML storage.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id_tasks` | int | Yes | Foreign key referencing the parent task |
| `xml_fragment` | text | Yes | XML fragment containing additional task-specific data |

#### Validation Rules

- `id_tasks` must reference an existing task in the tasks table
- `xml_fragment` must contain valid, well-formed XML
- One-to-one relationship with parent task

#### Example Record

```json
{
  "id_tasks": 892341,
  "xml_fragment": "<?xml version=\"1.0\"?><task-data><recording-path>/recordings/2024/01/15/call-123.wav</recording-path><duration>245</duration><caller-id>+15551234567</caller-id></task-data>"
}
```

#### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| `Task_Model` | Many-to-One | Each tasks_data record belongs to one task |

---

### tasks_error

Tracks error information for tasks that encounter problems during processing. Maintains a history of errors with timestamps for debugging and monitoring.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id_tasks` | int | Yes | Foreign key referencing the failed task |
| `description` | text | Yes | Detailed error description with timestamps and context |
| `first_error_date` | datetime | Yes | Timestamp of the first error occurrence |
| `last_error_date` | datetime | Yes | Timestamp of the most recent error occurrence |

#### Validation Rules

- `id_tasks` must reference an existing task
- `first_error_date` must be less than or equal to `last_error_date`
- `description` should include actionable error information

#### Example Record

```json
{
  "id_tasks": 892342,
  "description": "[2024-01-15 10:30:45] Connection timeout to SGAPI endpoint\n[2024-01-15 10:35:45] Retry 1: Connection timeout to SGAPI endpoint\n[2024-01-15 10:40:45] Retry 2: Connection refused",
  "first_error_date": "2024-01-15T10:30:45Z",
  "last_error_date": "2024-01-15T10:40:45Z"
}
```

#### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| `Task_Model` | One-to-One | Each task can have at most one error record |

---

## XML Schema Models

### cdr-normalized (XML Schema)

Defines the XML structure for normalized CDR data. This schema ensures consistent CDR format across all ingestion sources.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data/uuid` | uuid | Yes | Unique identifier for the CDR |
| `data/TimeZoneOffset` | int | No | Timezone offset in minutes from UTC |
| `data/StartEpoch` | int | Yes | Unix timestamp when the call started |
| `data/TableSuffix` | string | Yes | Date suffix (YYYYMMDD) for table partitioning |
| `data/LegUUID` | string | No | UUID of the specific call leg |
| `data/rmOrgID` | int | Yes | Organization ID |
| `data/rmUserID` | string | No | User ID associated with the call |
| `data/variables` | xml_node | No | Container for additional custom variables |
| `tasks/task` | xml_node | No | Container for task definitions to be created |

#### Validation Rules

- `uuid` must be a valid UUID format (8-4-4-4-12 hex characters)
- `StartEpoch` must be a valid Unix timestamp (positive integer)
- `TableSuffix` must match pattern `^\d{8}$` (YYYYMMDD)
- `rmOrgID` must be a positive integer
- XML must be well-formed and validate against the schema

#### Example XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<cdr>
  <data>
    <uuid>a1b2c3d4-e5f6-7890-abcd-ef1234567890</uuid>
    <TimeZoneOffset>-300</TimeZoneOffset>
    <StartEpoch>1705312800</StartEpoch>
    <TableSuffix>20240115</TableSuffix>
    <LegUUID>f9e8d7c6-b5a4-3210-9876-543210fedcba</LegUUID>
    <rmOrgID>1001</rmOrgID>
    <rmUserID>user_42</rmUserID>
    <variables>
      <caller_id_number>+15551234567</caller_id_number>
      <destination_number>+15559876543</destination_number>
      <call_direction>inbound</call_direction>
      <billsec>245</billsec>
      <hangup_cause>NORMAL_CLEARING</hangup_cause>
    </variables>
  </data>
  <tasks>
    <task type="CDRToSGAPI" priority="high">
      <rmDispStoreItems>1</rmDispStoreItems>
      <rmDispStorePriority_0>high</rmDispStorePriority_0>
    </task>
    <task type="SendEmail" priority="low">
      <template>voicemail-notification</template>
      <recipient>user@example.com</recipient>
    </task>
  </tasks>
</cdr>
```

#### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| `normalized_cdrs` | Embedded | XML is stored in the `xml` field of normalized_cdrs |
| `Task_Model` | Generated | Tasks defined in XML are created as Task_Model records |
| `CDRToSGAPI_Model` | Extracted | SGAPI tasks extract fields from this structure |

---

### CDRToSGAPI_Model

Task model for processing CDRs and storing them via the SGAPI (Storage Gateway API). Extracts key fields from normalized CDR XML for dispatch to storage and analytics systems.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rmOrgID` | int | Yes | Organization ID extracted from `/cdr/variables/rmOrgID` |
| `uuid` | string | Yes | Unique identifier extracted from `/cdr/variables/uuid` |
| `start_epoch` | int | Yes | Unix timestamp of call start |
| `rmTaskPriority` | string | No | Task priority level (low, medium, high). Default: medium |
| `rmDispStoreItems` | int | No | Number of storage dispatch items to process |
| `rmDispStorePriority_N` | string | No | Priority for storage dispatch item N (0-indexed) |
| `rmAnalyticsItems` | int | No | Number of analytics items to process |
| `rmAnalyticsPriority_N` | string | No | Priority for analytics item N (0-indexed) |

#### Validation Rules

- `rmOrgID` must be a positive integer
- `uuid` must be a valid UUID format
- `start_epoch` must be a valid Unix timestamp
- `rmTaskPriority` must be one of: `low`, `medium`, `high`
- `rmDispStoreItems` and `rmAnalyticsItems` must be non-negative integers
- Priority fields (`rmDispStorePriority_N`, `rmAnalyticsPriority_N`) must be `low`, `medium`, or `high`

#### Example JSON

```json
{
  "rmOrgID": 1001,
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "start_epoch": 1705312800,
  "rmTaskPriority": "high",
  "rmDispStoreItems": 2,
  "rmDispStorePriority_0": "high",
  "rmDispStorePriority_1": "medium",
  "rmAnalyticsItems": 1,
  "rmAnalyticsPriority_0": "low"
}
```

#### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| `Task_Model` | Extends | Inherits base task properties (id, done, retry, etc.) |
| `normalized_cdrs` | References | Links to source CDR via id_normalized_cdrs |
| `cdr-normalized` | Extracts From | Field values extracted from normalized CDR XML |

#### Common Use Cases

- Dispatching CDR data to long-term storage systems
- Feeding CDR data to analytics pipelines
- Managing multiple storage destinations with different priorities
- Coordinating storage and analytics processing for a single CDR

---

## Processing Flow

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Raw CDR     │────▶│  Normalization  │────▶│ cdr-normalized   │
│  (Various    │     │  Process        │     │ (XML Schema)     │
│  Formats)    │     │                 │     │                  │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                      │
                                                      ▼
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ CDRToSGAPI_Model │◀────│ Task Creation   │◀────│ normalized_cdrs  │
│ (Processing)     │     │                 │     │ (Storage)        │
└────────┬─────────┘     └─────────────────┘     └──────────────────┘
         │
         │ On Error
         ▼
┌──────────────────┐
│   tasks_error    │
│   (Error Log)    │
└──────────────────┘
```

---

## Related Documentation

- [Task Models](task-models.md) - Base task model and task lifecycle documentation
- [Messaging Models](messaging-models.md) - Email and SMS notification models
- [Models Overview](README.md) - Complete data model index