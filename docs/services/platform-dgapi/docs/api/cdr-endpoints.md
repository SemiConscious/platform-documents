# CDR Processing Endpoints

This document covers the CDR (Call Detail Record) to SGAPI integration endpoints in the Disposition Gateway API. These endpoints handle the processing of call detail records and their normalization for integration with the SGAPI system.

## Overview

The CDR to SGAPI endpoints process call detail records from telephony systems and create normalized CDR entries with associated tasks. This integration ensures that call data is properly formatted and routed to the appropriate downstream systems.

## Endpoints

### Create CDR to SGAPI Task

Creates a new CDR to SGAPI task that processes call detail record data and creates normalized CDR entries with associated tasks.

```
PUT /cdrtosgapi
```

**Alternative Endpoint:**
```
PUT /cdrtosgapi/{entity}
```

#### Description

This endpoint accepts raw CDR data from telephony systems, normalizes the data format, creates a CDR entry in the system, and generates associated tasks for further processing. The entity parameter can be used to specify a particular CDR entity type or identifier.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `entity` | Path | string | No | Entity identifier or type for the CDR task |
| `uuid` | Body | string | Yes | Unique identifier for the call |
| `caller_id` | Body | string | Yes | Caller's phone number (ANI) |
| `called_number` | Body | string | Yes | Called phone number (DNIS) |
| `start_time` | Body | string | Yes | Call start timestamp (ISO 8601 format) |
| `end_time` | Body | string | Yes | Call end timestamp (ISO 8601 format) |
| `duration` | Body | integer | Yes | Call duration in seconds |
| `disposition` | Body | string | Yes | Call disposition code (e.g., "ANSWERED", "NO ANSWER", "BUSY") |
| `direction` | Body | string | No | Call direction ("inbound" or "outbound") |
| `queue_id` | Body | string | No | Queue identifier if call was queued |
| `agent_id` | Body | string | No | Agent identifier who handled the call |
| `recording_url` | Body | string | No | URL to call recording if available |
| `custom_data` | Body | object | No | Additional custom fields for the CDR |

#### Request Example

```bash
curl -X PUT "https://api.example.com/cdrtosgapi" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "caller_id": "+15551234567",
    "called_number": "+15559876543",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:35:30Z",
    "duration": 330,
    "disposition": "ANSWERED",
    "direction": "inbound",
    "queue_id": "sales_queue_01",
    "agent_id": "agent_1234",
    "recording_url": "https://recordings.example.com/calls/550e8400.mp3",
    "custom_data": {
      "campaign_id": "camp_2024_01",
      "lead_source": "web_form"
    }
  }'
```

#### Response Example

**Success Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "task_id": "task_789xyz",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "cdr_id": "cdr_456abc",
    "state": "pending",
    "created_at": "2024-01-15T10:36:00Z",
    "message": "CDR task created successfully"
  }
}
```

**Success Response with Entity (200 OK):**

```json
{
  "status": "success",
  "data": {
    "task_id": "task_789xyz",
    "entity": "outbound_sales",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "cdr_id": "cdr_456abc",
    "state": "pending",
    "created_at": "2024-01-15T10:36:00Z",
    "message": "CDR task created successfully for entity: outbound_sales"
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Request body is malformed or missing required fields |
| 400 | `INVALID_UUID` | The provided UUID format is invalid |
| 400 | `INVALID_TIMESTAMP` | Start time or end time format is invalid |
| 400 | `INVALID_DISPOSITION` | The disposition code is not recognized |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 409 | `DUPLICATE_CDR` | A CDR with this UUID already exists |
| 422 | `VALIDATION_ERROR` | Request data failed validation rules |
| 500 | `INTERNAL_ERROR` | Server error during CDR processing |
| 503 | `SGAPI_UNAVAILABLE` | SGAPI service is temporarily unavailable |

---

### Get CDR to SGAPI Task Status

Retrieves the status of a CDR to SGAPI task by its UUID.

```
GET /cdrtosgapi/{uuid}
```

#### Description

This endpoint allows you to check the processing status of a previously submitted CDR task. Use the UUID returned from the create endpoint to query the current state of the task.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `uuid` | Path | string | Yes | The unique identifier of the CDR task to retrieve |

#### Request Example

```bash
curl -X GET "https://api.example.com/cdrtosgapi/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

**Success Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "task_789xyz",
    "cdr_id": "cdr_456abc",
    "state": "completed",
    "caller_id": "+15551234567",
    "called_number": "+15559876543",
    "disposition": "ANSWERED",
    "duration": 330,
    "sgapi_status": "synced",
    "sgapi_reference": "sgapi_ref_12345",
    "created_at": "2024-01-15T10:36:00Z",
    "updated_at": "2024-01-15T10:36:05Z",
    "completed_at": "2024-01-15T10:36:05Z"
  }
}
```

**Pending Task Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "task_789xyz",
    "cdr_id": "cdr_456abc",
    "state": "processing",
    "caller_id": "+15551234567",
    "called_number": "+15559876543",
    "disposition": "ANSWERED",
    "duration": 330,
    "sgapi_status": "pending",
    "sgapi_reference": null,
    "created_at": "2024-01-15T10:36:00Z",
    "updated_at": "2024-01-15T10:36:02Z",
    "completed_at": null
  }
}
```

**Failed Task Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "task_789xyz",
    "cdr_id": "cdr_456abc",
    "state": "failed",
    "caller_id": "+15551234567",
    "called_number": "+15559876543",
    "disposition": "ANSWERED",
    "duration": 330,
    "sgapi_status": "error",
    "sgapi_reference": null,
    "error_message": "SGAPI validation failed: invalid queue_id",
    "retry_count": 3,
    "created_at": "2024-01-15T10:36:00Z",
    "updated_at": "2024-01-15T10:38:00Z",
    "completed_at": null
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_UUID` | The provided UUID format is invalid |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 404 | `NOT_FOUND` | No CDR task found with the specified UUID |
| 500 | `INTERNAL_ERROR` | Server error while retrieving task status |

---

## Task States

CDR to SGAPI tasks progress through the following states:

| State | Description |
|-------|-------------|
| `pending` | Task has been created and is queued for processing |
| `processing` | Task is currently being processed |
| `completed` | Task has been successfully processed and synced to SGAPI |
| `failed` | Task processing failed after all retry attempts |
| `retrying` | Task failed but is scheduled for retry |

## SGAPI Sync Status

The `sgapi_status` field indicates the synchronization status with the SGAPI system:

| Status | Description |
|--------|-------------|
| `pending` | CDR has not yet been sent to SGAPI |
| `syncing` | CDR is currently being transmitted to SGAPI |
| `synced` | CDR has been successfully received by SGAPI |
| `error` | SGAPI rejected the CDR or sync failed |

## Related Documentation

- [Task Endpoints](task-endpoints.md) - General task management endpoints
- [API Overview](README.md) - General API information and authentication