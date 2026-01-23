# Task & Callback Endpoints

This document covers the task management endpoints in the Disposition Gateway API, including voicemail notifications, generic tasks, task status retrieval, and callback finish events.

## Overview

The task endpoints provide functionality for:
- **Voicemail Tasks**: Creating and tracking voicemail notification tasks
- **Generic Tasks**: Creating and tracking generic disposition tasks
- **Task Status**: Retrieving status information for any task
- **Callback Finish**: Signaling completion of callback operations

---

## Voicemail Endpoints

### Create Voicemail Task

Creates a new voicemail notification task for processing voicemail disposition events.

```
PUT /voicemail/{entity}
```

#### Description

This endpoint creates a voicemail notification task that processes voicemail events and triggers appropriate notifications or workflows based on the voicemail data provided.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the voicemail task (e.g., task ID, voicemail ID) |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `voicemail_id` | string | Yes | Unique identifier for the voicemail |
| `caller_id` | string | Yes | Phone number of the caller who left the voicemail |
| `recipient_id` | string | Yes | Identifier of the voicemail recipient |
| `duration` | integer | No | Duration of the voicemail in seconds |
| `timestamp` | string | No | ISO 8601 timestamp when voicemail was left |
| `audio_url` | string | No | URL to the voicemail audio file |
| `transcription` | string | No | Text transcription of the voicemail |
| `priority` | string | No | Priority level: `low`, `normal`, `high` |
| `callback_url` | string | No | URL for webhook notification on completion |
| `metadata` | object | No | Additional metadata for the voicemail task |

#### Request Example

```bash
curl -X PUT "https://api.example.com/voicemail/vm-12345" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "voicemail_id": "vm-12345",
    "caller_id": "+15551234567",
    "recipient_id": "user-789",
    "duration": 45,
    "timestamp": "2024-01-15T10:30:00Z",
    "audio_url": "https://storage.example.com/voicemails/vm-12345.mp3",
    "transcription": "Hi, this is John calling about the appointment...",
    "priority": "normal",
    "callback_url": "https://myapp.example.com/webhooks/voicemail",
    "metadata": {
      "department": "sales",
      "campaign_id": "camp-456"
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-vm-67890",
    "entity": "vm-12345",
    "type": "voicemail",
    "status": "pending",
    "created_at": "2024-01-15T10:30:05Z",
    "estimated_completion": "2024-01-15T10:30:15Z"
  },
  "message": "Voicemail task created successfully"
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_REQUEST` | Missing or invalid required parameters |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `ENTITY_NOT_FOUND` | Specified entity does not exist |
| 409 | `DUPLICATE_TASK` | A task for this voicemail already exists |
| 422 | `INVALID_AUDIO_URL` | The provided audio URL is invalid or inaccessible |
| 500 | `INTERNAL_ERROR` | Server error while creating the task |

---

### Get Voicemail Task Status

Retrieves the status of a voicemail task by entity ID.

```
GET /voicemail/{entity}
```

#### Description

Returns the current status and details of a voicemail notification task, including processing state and any results or errors.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the voicemail task |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_metadata` | boolean | No | Include full metadata in response (default: `false`) |
| `include_history` | boolean | No | Include status change history (default: `false`) |

#### Request Example

```bash
curl -X GET "https://api.example.com/voicemail/vm-12345?include_metadata=true" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-vm-67890",
    "entity": "vm-12345",
    "type": "voicemail",
    "status": "completed",
    "voicemail_id": "vm-12345",
    "caller_id": "+15551234567",
    "recipient_id": "user-789",
    "duration": 45,
    "created_at": "2024-01-15T10:30:05Z",
    "updated_at": "2024-01-15T10:30:12Z",
    "completed_at": "2024-01-15T10:30:12Z",
    "result": {
      "notification_sent": true,
      "notification_type": "email",
      "notification_recipient": "user@example.com"
    },
    "metadata": {
      "department": "sales",
      "campaign_id": "camp-456"
    }
  }
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `TASK_NOT_FOUND` | No voicemail task found for the specified entity |
| 500 | `INTERNAL_ERROR` | Server error while retrieving task status |

---

## Generic Task Endpoints

### Create Generic Task

Creates a generic task for custom disposition workflows.

```
PUT /generic/{entity}
```

#### Description

Creates a generic task that can be used for custom disposition workflows not covered by specific task types. This provides flexibility for implementing custom business logic.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the generic task |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_type` | string | Yes | Custom task type identifier |
| `action` | string | Yes | Action to perform (e.g., `process`, `notify`, `update`) |
| `target_id` | string | No | Target entity for the task |
| `payload` | object | No | Task-specific payload data |
| `priority` | integer | No | Task priority (1-10, default: 5) |
| `scheduled_at` | string | No | ISO 8601 timestamp for scheduled execution |
| `timeout` | integer | No | Task timeout in seconds (default: 300) |
| `retry_count` | integer | No | Number of retry attempts (default: 3) |
| `callback_url` | string | No | URL for webhook notification on completion |
| `tags` | array | No | Array of tags for task categorization |

#### Request Example

```bash
curl -X PUT "https://api.example.com/generic/custom-task-001" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "task_type": "lead_followup",
    "action": "process",
    "target_id": "lead-12345",
    "payload": {
      "contact_method": "phone",
      "script_id": "script-789",
      "agent_group": "sales-team-a"
    },
    "priority": 7,
    "timeout": 600,
    "retry_count": 2,
    "callback_url": "https://myapp.example.com/webhooks/task-complete",
    "tags": ["sales", "high-value", "followup"]
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-gen-11111",
    "entity": "custom-task-001",
    "type": "generic",
    "task_type": "lead_followup",
    "action": "process",
    "status": "pending",
    "priority": 7,
    "created_at": "2024-01-15T11:00:00Z",
    "scheduled_at": null,
    "timeout": 600,
    "retry_count": 2,
    "retries_remaining": 2
  },
  "message": "Generic task created successfully"
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_REQUEST` | Missing or invalid required parameters |
| 400 | `INVALID_TASK_TYPE` | Unknown or unsupported task type |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 409 | `DUPLICATE_ENTITY` | A task with this entity already exists |
| 422 | `INVALID_PAYLOAD` | The payload structure is invalid for this task type |
| 500 | `INTERNAL_ERROR` | Server error while creating the task |

---

### Get Generic Task Status

Retrieves the status of a generic task by entity ID.

```
GET /generic/{entity}
```

#### Description

Returns the current status, progress, and results of a generic task.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the generic task |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_payload` | boolean | No | Include original payload in response (default: `false`) |
| `include_result` | boolean | No | Include task result data (default: `true`) |
| `include_logs` | boolean | No | Include execution logs (default: `false`) |

#### Request Example

```bash
curl -X GET "https://api.example.com/generic/custom-task-001?include_payload=true&include_logs=true" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-gen-11111",
    "entity": "custom-task-001",
    "type": "generic",
    "task_type": "lead_followup",
    "action": "process",
    "status": "completed",
    "priority": 7,
    "created_at": "2024-01-15T11:00:00Z",
    "started_at": "2024-01-15T11:00:02Z",
    "completed_at": "2024-01-15T11:00:45Z",
    "execution_time_ms": 43000,
    "retries_used": 0,
    "payload": {
      "contact_method": "phone",
      "script_id": "script-789",
      "agent_group": "sales-team-a"
    },
    "result": {
      "success": true,
      "lead_contacted": true,
      "outcome": "interested",
      "next_action": "schedule_demo"
    },
    "logs": [
      {
        "timestamp": "2024-01-15T11:00:02Z",
        "level": "info",
        "message": "Task started"
      },
      {
        "timestamp": "2024-01-15T11:00:45Z",
        "level": "info",
        "message": "Task completed successfully"
      }
    ],
    "tags": ["sales", "high-value", "followup"]
  }
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `TASK_NOT_FOUND` | No generic task found for the specified entity |
| 500 | `INTERNAL_ERROR` | Server error while retrieving task status |

---

## Task Status Endpoint

### Get Task Status

Retrieves the status of any task by entity ID.

```
GET /task/{entity}
```

#### Description

A universal endpoint for retrieving the status of any task type (SMS, email, voicemail, generic, etc.) by its entity identifier. This is useful when the task type is unknown or when building generic status-checking functionality.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the task |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_details` | boolean | No | Include full task details (default: `false`) |
| `include_history` | boolean | No | Include status change history (default: `false`) |

#### Request Example

```bash
curl -X GET "https://api.example.com/task/task-12345?include_details=true&include_history=true" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-12345",
    "entity": "task-12345",
    "type": "sms",
    "status": "completed",
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T09:00:05Z",
    "completed_at": "2024-01-15T09:00:05Z",
    "details": {
      "recipient": "+15559876543",
      "message_length": 145,
      "segments": 1,
      "provider": "twilio"
    },
    "result": {
      "delivered": true,
      "delivery_time": "2024-01-15T09:00:04Z"
    },
    "history": [
      {
        "status": "pending",
        "timestamp": "2024-01-15T09:00:00Z",
        "message": "Task created"
      },
      {
        "status": "processing",
        "timestamp": "2024-01-15T09:00:01Z",
        "message": "SMS queued for delivery"
      },
      {
        "status": "completed",
        "timestamp": "2024-01-15T09:00:05Z",
        "message": "SMS delivered successfully"
      }
    ]
  }
}
```

#### Task Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task has been created but not yet started |
| `queued` | Task is in the processing queue |
| `processing` | Task is actively being processed |
| `completed` | Task completed successfully |
| `failed` | Task failed after all retry attempts |
| `cancelled` | Task was cancelled before completion |
| `expired` | Task timed out or exceeded its TTL |

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `TASK_NOT_FOUND` | No task found for the specified entity |
| 500 | `INTERNAL_ERROR` | Server error while retrieving task status |

---

## Callback Finish Endpoints

### Create Callback Finish Task (PUT)

Creates a callback finish task to signal completion of a callback operation.

```
PUT /cbfinish/{entity}
```

#### Description

This endpoint creates a callback finish task that signals the completion of a callback operation in the contact center workflow. It processes the callback completion event and triggers any associated disposition workflows.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the callback finish task (typically the callback ID) |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `callback_id` | string | Yes | Unique identifier of the callback being completed |
| `agent_id` | string | Yes | Identifier of the agent who handled the callback |
| `disposition_code` | string | Yes | Disposition code for the callback outcome |
| `call_duration` | integer | No | Duration of the callback in seconds |
| `start_time` | string | No | ISO 8601 timestamp when callback started |
| `end_time` | string | No | ISO 8601 timestamp when callback ended |
| `outcome` | string | No | Callback outcome: `connected`, `no_answer`, `busy`, `voicemail`, `wrong_number` |
| `notes` | string | No | Agent notes about the callback |
| `next_action` | object | No | Scheduled next action, if any |
| `customer_data` | object | No | Updated customer data from the callback |
| `recording_url` | string | No | URL to the call recording |
| `wrap_up_time` | integer | No | Agent wrap-up time in seconds |

#### Request Example

```bash
curl -X PUT "https://api.example.com/cbfinish/cb-98765" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "callback_id": "cb-98765",
    "agent_id": "agent-456",
    "disposition_code": "SALE_COMPLETE",
    "call_duration": 342,
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T14:05:42Z",
    "outcome": "connected",
    "notes": "Customer agreed to premium plan. Contract sent via email.",
    "next_action": {
      "type": "followup_email",
      "scheduled_at": "2024-01-16T10:00:00Z",
      "template": "contract_reminder"
    },
    "customer_data": {
      "plan_selected": "premium",
      "contract_sent": true,
      "email_confirmed": "customer@example.com"
    },
    "recording_url": "https://recordings.example.com/calls/cb-98765.mp3",
    "wrap_up_time": 45
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-cbf-22222",
    "entity": "cb-98765",
    "type": "callback_finish",
    "status": "completed",
    "callback_id": "cb-98765",
    "disposition_code": "SALE_COMPLETE",
    "created_at": "2024-01-15T14:06:30Z",
    "processed_at": "2024-01-15T14:06:31Z",
    "actions_triggered": [
      {
        "type": "crm_update",
        "status": "completed"
      },
      {
        "type": "followup_scheduled",
        "status": "completed",
        "scheduled_for": "2024-01-16T10:00:00Z"
      }
    ]
  },
  "message": "Callback finish task processed successfully"
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_REQUEST` | Missing or invalid required parameters |
| 400 | `INVALID_DISPOSITION` | Unknown disposition code |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `CALLBACK_NOT_FOUND` | Referenced callback does not exist |
| 409 | `CALLBACK_ALREADY_FINISHED` | This callback has already been finished |
| 422 | `INVALID_AGENT` | Agent ID is not valid or not authorized |
| 500 | `INTERNAL_ERROR` | Server error while processing callback finish |

---

### Create Callback Finish Task (POST)

Alternative method to create a callback finish task.

```
POST /cbfinish/{entity}
```

#### Description

This endpoint provides an alternative HTTP method for creating callback finish tasks. The functionality is identical to the PUT method.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Entity identifier for the callback finish task |

#### Request Body Parameters

Same as [PUT /cbfinish/{entity}](#create-callback-finish-task-put).

#### Request Example

```bash
curl -X POST "https://api.example.com/cbfinish/cb-98765" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "callback_id": "cb-98765",
    "agent_id": "agent-456",
    "disposition_code": "NO_ANSWER",
    "call_duration": 0,
    "start_time": "2024-01-15T15:00:00Z",
    "end_time": "2024-01-15T15:00:30Z",
    "outcome": "no_answer",
    "next_action": {
      "type": "retry_callback",
      "scheduled_at": "2024-01-15T17:00:00Z",
      "attempt_number": 2
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "task_id": "task-cbf-33333",
    "entity": "cb-98765",
    "type": "callback_finish",
    "status": "completed",
    "callback_id": "cb-98765",
    "disposition_code": "NO_ANSWER",
    "created_at": "2024-01-15T15:00:35Z",
    "processed_at": "2024-01-15T15:00:36Z",
    "actions_triggered": [
      {
        "type": "callback_rescheduled",
        "status": "completed",
        "scheduled_for": "2024-01-15T17:00:00Z",
        "new_callback_id": "cb-98766"
      }
    ]
  },
  "message": "Callback finish task processed successfully"
}
```

#### Error Codes

Same as [PUT /cbfinish/{entity}](#create-callback-finish-task-put).

---

## Common Disposition Codes

The following disposition codes are commonly used across callback finish tasks:

| Code | Description |
|------|-------------|
| `SALE_COMPLETE` | Sale successfully completed |
| `APPOINTMENT_SET` | Appointment scheduled with customer |
| `CALLBACK_REQUESTED` | Customer requested a callback at a later time |
| `NO_ANSWER` | Customer did not answer |
| `BUSY` | Line was busy |
| `VOICEMAIL` | Left voicemail message |
| `WRONG_NUMBER` | Incorrect phone number |
| `DO_NOT_CALL` | Customer requested to be added to DNC list |
| `NOT_INTERESTED` | Customer not interested |
| `FOLLOW_UP_REQUIRED` | Additional follow-up needed |
| `TRANSFERRED` | Call transferred to another department |

---

## Related Documentation

- [Messaging Endpoints](messaging-endpoints.md) - SMS and Email task creation
- [CDR Endpoints](cdr-endpoints.md) - Call Detail Record processing
- [Info Endpoints](info-endpoints.md) - API health and status information