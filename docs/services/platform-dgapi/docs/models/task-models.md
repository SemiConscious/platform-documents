# Task Data Models

This document provides comprehensive documentation for task-related models in the platform-dgapi service. These models form the core task management and processing infrastructure for handling asynchronous operations such as email delivery, SMS notifications, CDR processing, and generic task execution.

## Overview

The task system uses a hierarchical model structure where `Task_Model` serves as the base class, with specialized models extending it for specific task types. Tasks are associated with normalized CDR records and can track errors, store additional data, and report status to clients.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Task Architecture                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐         ┌─────────────────────┐               │
│  │  normalized_cdrs │◄────────│     Task_Model      │               │
│  │  (CDR Storage)   │   1:N   │   (Base Task)       │               │
│  └─────────────────┘         └──────────┬──────────┘               │
│                                         │                           │
│              ┌──────────────────────────┼──────────────────────┐   │
│              │              │           │           │          │   │
│              ▼              ▼           ▼           ▼          ▼   │
│     ┌────────────┐  ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌─────┐│
│     │Email_Model │  │Sms_Model  │ │Voicemail │ │CDRTo    │ │CBFin││
│     │            │  │           │ │_Model    │ │SGAPI    │ │ish  ││
│     └────────────┘  └───────────┘ └──────────┘ └─────────┘ └─────┘│
│                                                                     │
│  ┌─────────────────┐         ┌─────────────────────┐               │
│  │   tasks_error   │◄────────│     Task_Model      │               │
│  │  (Error Track)  │   1:1   │                     │               │
│  └─────────────────┘         └──────────┬──────────┘               │
│                                         │                           │
│  ┌─────────────────┐                    │                           │
│  │   tasks_data    │◄───────────────────┘                           │
│  │  (Extra Data)   │   1:N                                          │
│  └─────────────────┘                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Entity Relationship Diagram

```
┌────────────────────┐       ┌────────────────────┐
│  normalized_cdrs   │       │    Task_Model      │
├────────────────────┤       ├────────────────────┤
│ PK id              │◄──────│ FK id_normalized_  │
│    xml             │  1:N  │    cdrs            │
│    uuid            │       │ PK id              │
│    TableSuffix     │       │    task_type       │
│    rmOrgID         │       │    create_time     │
└────────────────────┘       │    next_attempt    │
                             │    done            │
                             │    node_index      │
                             │    retry           │
                             │    priority        │
                             └─────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │   tasks_error   │ │   tasks_data    │ │ TaskStatus      │
          ├─────────────────┤ ├─────────────────┤ │ Response        │
          │ FK id_tasks     │ │ FK id_tasks     │ ├─────────────────┤
          │    description  │ │    xml_fragment │ │    http-status  │
          │    first_error  │ └─────────────────┘ │    state        │
          │    last_error   │                     │    type         │
          └─────────────────┘                     │    message      │
                                                  └─────────────────┘
```

---

## Core Task Models

### Task_Model

The base task model for managing asynchronous tasks in the CDR system. All specialized task types inherit from this model.

#### Purpose

- Serves as the foundation for all task types in the system
- Manages task lifecycle (creation, scheduling, retry, completion)
- Provides common fields for task tracking and prioritization
- Enables distributed processing across multiple nodes

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `id` | int | Yes | Primary key - unique task identifier |
| `id_normalized_cdrs` | int | Yes | Foreign key reference to the normalized_cdrs table |
| `task_type` | string | Yes | Type of task: `SendEmail`, `SendSMS`, `CDRToSGAPI`, `Generic`, `CBFinish`, `Voicemail` |
| `create_time` | datetime | Yes | Timestamp when the task was created |
| `next_attempt` | datetime | Yes | Scheduled time for the next processing attempt |
| `done` | enum | Yes | Task completion status: `y` (completed), `n` (pending), `error` (failed) |
| `node_index` | int | No | Index of the processing node assigned to this task |
| `retry` | int | Yes | Number of retry attempts made (starts at 0) |
| `priority` | string | No | Task priority level: `low`, `medium`, `high` |

#### Validation Rules

- `id` must be a positive integer
- `task_type` must be one of the predefined task types
- `done` must be one of: `y`, `n`, `error`
- `retry` must be non-negative (≥ 0)
- `priority` defaults to `medium` if not specified
- `next_attempt` must be a valid datetime, typically set to current time or future

#### Example JSON

```json
{
  "id": 12345678,
  "id_normalized_cdrs": 98765432,
  "task_type": "SendEmail",
  "create_time": "2024-01-15T10:30:00Z",
  "next_attempt": "2024-01-15T10:30:05Z",
  "done": "n",
  "node_index": 2,
  "retry": 0,
  "priority": "high"
}
```

#### Relationships

- **Parent**: `normalized_cdrs` (many-to-one) - Each task belongs to one normalized CDR record
- **Child**: `tasks_error` (one-to-one) - Error tracking for failed tasks
- **Child**: `tasks_data` (one-to-many) - Additional data storage for the task

---

### Generic_Model

A flexible task model for creating custom tasks that don't fit specialized categories.

#### Purpose

- Enables creation of arbitrary task types
- Provides a flexible XML variables node for custom data
- Supports the standard priority system
- Useful for integration points and extensibility

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `rmOrgID` | int | Yes | Organization ID that owns this task |
| `rmTaskPriority` | string | No | Task priority level: `low`, `medium`, `high` |
| `variables` | xml_node | No | XML node containing additional custom variables |

#### Validation Rules

- `rmOrgID` must be a valid organization ID (positive integer)
- `rmTaskPriority` must be one of: `low`, `medium`, `high` (defaults to `medium`)
- `variables` must be well-formed XML if provided

#### Example JSON

```json
{
  "rmOrgID": 1001,
  "rmTaskPriority": "medium",
  "variables": {
    "custom_field_1": "value1",
    "custom_field_2": "value2",
    "processing_flags": {
      "flag_a": true,
      "flag_b": false
    }
  }
}
```

#### XML Representation

```xml
<task type="Generic">
  <rmOrgID>1001</rmOrgID>
  <rmTaskPriority>medium</rmTaskPriority>
  <variables>
    <custom_field_1>value1</custom_field_1>
    <custom_field_2>value2</custom_field_2>
    <processing_flags>
      <flag_a>true</flag_a>
      <flag_b>false</flag_b>
    </processing_flags>
  </variables>
</task>
```

#### Relationships

- **Inherits from**: `Task_Model`
- **Associated with**: `normalized_cdrs` via parent `Task_Model`

---

## Supporting Task Tables

### tasks_error

Tracks error information for tasks that have encountered failures during processing.

#### Purpose

- Records error descriptions with timestamps
- Tracks first and last occurrence of errors
- Enables debugging and monitoring of task failures
- Supports error aggregation and reporting

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `id_tasks` | int | Yes | Foreign key reference to the tasks table (primary key) |
| `description` | text | Yes | Detailed error description including timestamps and stack traces |
| `first_error_date` | datetime | Yes | Timestamp of the first error occurrence |
| `last_error_date` | datetime | Yes | Timestamp of the most recent error occurrence |

#### Validation Rules

- `id_tasks` must reference a valid task in the tasks table
- `description` should include actionable error information
- `first_error_date` must be ≤ `last_error_date`
- Updates should only modify `description` and `last_error_date`

#### Example JSON

```json
{
  "id_tasks": 12345678,
  "description": "[2024-01-15T10:35:00Z] Connection timeout to SMTP server smtp.example.com:587\n[2024-01-15T10:40:00Z] Retry failed: Connection refused\n[2024-01-15T10:45:00Z] Max retries exceeded",
  "first_error_date": "2024-01-15T10:35:00Z",
  "last_error_date": "2024-01-15T10:45:00Z"
}
```

#### Relationships

- **Parent**: `Task_Model` (one-to-one) - Each error record belongs to exactly one task

---

### tasks_data

Stores additional XML data fragments associated with tasks that exceed the main task storage capacity.

#### Purpose

- Extends task storage with additional XML data
- Stores supplementary information that doesn't fit in the main task record
- Supports complex task configurations
- Enables task-specific data attachments

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `id_tasks` | int | Yes | Foreign key reference to the tasks table |
| `xml_fragment` | text | Yes | XML fragment containing additional task data |

#### Validation Rules

- `id_tasks` must reference a valid task in the tasks table
- `xml_fragment` must be well-formed XML
- Multiple records can exist per task

#### Example JSON

```json
{
  "id_tasks": 12345678,
  "xml_fragment": "<extended_data><attachment_url>https://storage.example.com/files/abc123</attachment_url><metadata><size>1048576</size><content_type>audio/wav</content_type></metadata></extended_data>"
}
```

#### XML Representation

```xml
<extended_data>
  <attachment_url>https://storage.example.com/files/abc123</attachment_url>
  <metadata>
    <size>1048576</size>
    <content_type>audio/wav</content_type>
  </metadata>
</extended_data>
```

#### Relationships

- **Parent**: `Task_Model` (many-to-one) - Multiple data records can belong to one task

---

## Specialized Task Models

### CBFinish_Model

Call Buffering Finish task model for completing buffered recording tasks.

#### Purpose

- Signals completion of call buffering operations
- Reports success or failure outcomes
- Supports both primary and secondary storage locations
- Handles non-call (ANC) policy scenarios

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `OrgID` | int | Yes | Organization ID that owns the recording |
| `TaskID` | int | Yes | ID of the buffering task to complete |
| `Outcome` | string | Yes | Task outcome: `success` or `failure` |
| `Message` | string | No | Human-readable outcome message |
| `rmARNCPolicy` | string | No | Non-call policy flag for special handling |
| `rmARLocationType` | string | No | Storage location type: `primary` or `secondary` |
| `variables` | xml_node | No | Additional variables for task completion |

#### Validation Rules

- `OrgID` must be a valid organization ID
- `TaskID` must reference an existing buffering task
- `Outcome` must be either `success` or `failure`
- `rmARLocationType` must be `primary` or `secondary` if specified

#### Example JSON

```json
{
  "OrgID": 1001,
  "TaskID": 87654321,
  "Outcome": "success",
  "Message": "Recording successfully buffered and stored",
  "rmARNCPolicy": "standard",
  "rmARLocationType": "primary",
  "variables": {
    "storage_path": "/recordings/2024/01/15/call_12345.wav",
    "file_size": 2097152,
    "duration_seconds": 180
  }
}
```

#### XML Representation

```xml
<task type="CBFinish">
  <OrgID>1001</OrgID>
  <TaskID>87654321</TaskID>
  <Outcome>success</Outcome>
  <Message>Recording successfully buffered and stored</Message>
  <rmARNCPolicy>standard</rmARNCPolicy>
  <rmARLocationType>primary</rmARLocationType>
  <variables>
    <storage_path>/recordings/2024/01/15/call_12345.wav</storage_path>
    <file_size>2097152</file_size>
    <duration_seconds>180</duration_seconds>
  </variables>
</task>
```

#### Relationships

- **Inherits from**: `Task_Model`
- **References**: Original buffering task via `TaskID`

---

## Response Models

### TaskStatusResponse

Response structure for task status queries via the API.

#### Purpose

- Provides standardized task status information to API clients
- Supports polling-based task tracking
- Includes HATEOAS links for navigation
- Communicates errors and completion states

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `@http-status` | int | Yes | HTTP status code: `200` (done), `202` (pending), `404` (not found), `422` (validation error) |
| `status/state` | string | Yes | Task state: `done`, `pending`, `failed` |
| `status/type` | string | Yes | Task type identifier |
| `status/link/@href` | string | Yes | Self-referential URL for the task status endpoint |
| `status/link/@rel` | string | Yes | Link relation type (typically `self`) |
| `status/message` | string | No | Human-readable status message |
| `status/detail` | string | No | Additional error or status details |
| `status/ping-after` | datetime | No | ISO 8601 timestamp indicating when to poll next (for pending tasks) |

#### Validation Rules

- `@http-status` must be a valid HTTP status code
- `state` must be one of: `done`, `pending`, `failed`
- `ping-after` should only be present when state is `pending`
- `link/@href` must be a valid URL

#### Example JSON - Pending Task

```json
{
  "@http-status": 202,
  "status": {
    "state": "pending",
    "type": "SendEmail",
    "link": {
      "@href": "https://api.example.com/dgapi/tasks/12345678/status",
      "@rel": "self"
    },
    "message": "Task is queued for processing",
    "ping-after": "2024-01-15T10:31:00Z"
  }
}
```

#### Example JSON - Completed Task

```json
{
  "@http-status": 200,
  "status": {
    "state": "done",
    "type": "SendEmail",
    "link": {
      "@href": "https://api.example.com/dgapi/tasks/12345678/status",
      "@rel": "self"
    },
    "message": "Email sent successfully"
  }
}
```

#### Example JSON - Failed Task

```json
{
  "@http-status": 200,
  "status": {
    "state": "failed",
    "type": "SendEmail",
    "link": {
      "@href": "https://api.example.com/dgapi/tasks/12345678/status",
      "@rel": "self"
    },
    "message": "Task failed after maximum retries",
    "detail": "SMTP connection timeout after 3 attempts"
  }
}
```

#### Example JSON - Not Found

```json
{
  "@http-status": 404,
  "status": {
    "state": "failed",
    "type": "unknown",
    "link": {
      "@href": "https://api.example.com/dgapi/tasks/99999999/status",
      "@rel": "self"
    },
    "message": "Task not found",
    "detail": "No task exists with ID 99999999"
  }
}
```

#### XML Representation

```xml
<response http-status="202">
  <status>
    <state>pending</state>
    <type>SendEmail</type>
    <link href="https://api.example.com/dgapi/tasks/12345678/status" rel="self"/>
    <message>Task is queued for processing</message>
    <ping-after>2024-01-15T10:31:00Z</ping-after>
  </status>
</response>
```

#### Relationships

- **References**: `Task_Model` - Status response describes a specific task

---

## Common Use Cases and Patterns

### Task Creation Flow

```
1. Receive CDR data
2. Create normalized_cdrs record
3. Extract task definitions from CDR XML
4. Create Task_Model records for each task type
5. Set initial priority and next_attempt
6. Task processor picks up pending tasks
```

### Task Retry Pattern

```
1. Task processor attempts task execution
2. On failure:
   a. Increment retry counter
   b. Create/update tasks_error record
   c. Calculate backoff delay
   d. Update next_attempt with backoff
   e. If max retries exceeded, set done='error'
3. On success:
   a. Set done='y'
   b. Record completion timestamp
```

### Status Polling Pattern

```
1. Client submits task request
2. API returns 202 with TaskStatusResponse
3. Client extracts ping-after timestamp
4. Client waits until ping-after
5. Client polls status endpoint
6. Repeat until state is 'done' or 'failed'
```

### Generic Task Usage

Generic tasks are ideal for:
- Custom integration workflows
- Scheduled maintenance operations
- Data synchronization tasks
- Webhook deliveries
- Custom notification types

```xml
<task type="Generic">
  <rmOrgID>1001</rmOrgID>
  <rmTaskPriority>low</rmTaskPriority>
  <variables>
    <action>sync_crm</action>
    <endpoint>https://crm.example.com/api/calls</endpoint>
    <payload_ref>data_12345</payload_ref>
  </variables>
</task>
```

---

## Related Documentation

- [CDR Models](./cdr-models.md) - Documentation for `normalized_cdrs` and CDR XML schemas
- [Messaging Models](./messaging-models.md) - Documentation for `Email_Model`, `Sms_Model`, and `Voicemail_Model`
- [API Overview](../README.md) - Service overview and architecture