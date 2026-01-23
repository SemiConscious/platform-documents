# System and Administrative API

The System and Administrative API provides endpoints for CDR (Call Detail Record) processing, event logging, scheduled tasks, and various administrative operations essential for platform monitoring and maintenance.

## Overview

This API covers:
- **CDR Processing**: Call Detail Record ingestion and processing
- **Event Logging**: Platform event tracking and audit trails
- **Scheduled Tasks**: Background job management
- **SIP Gateway Monitoring**: Gateway health and status monitoring
- **Bespoke Data Access**: Custom configuration data retrieval
- **QR Code Generation**: Utility endpoints for QR code creation
- **Error Handling**: System error management

## Base URL

All endpoints are relative to: `https://api.platform.example.com`

---

## CDR Processing

### Process CDR Data

Processes Call Detail Record data and forwards it to the Service Gateway API for storage and analysis.

```
POST /{action}/{index}
```

#### Description

This endpoint receives CDR data from telephony systems and processes it through the CDRMunch system, which normalizes and forwards records to the Service Gateway API. This is typically called by internal systems rather than external clients.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `action` | string | path | Yes | The CDR action type (e.g., `cdr`, `process`) |
| `index` | string | path | Yes | Index or identifier for the CDR batch |
| `records` | array | body | Yes | Array of CDR record objects |
| `source` | string | body | No | Source system identifier |
| `timestamp` | string | body | No | Processing timestamp (ISO 8601) |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/cdr/batch001" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "call_id": "abc123-def456",
        "caller": "+14155551234",
        "callee": "+14155555678",
        "start_time": "2024-01-15T10:30:00Z",
        "end_time": "2024-01-15T10:35:42Z",
        "duration": 342,
        "disposition": "ANSWERED",
        "trunk_id": "trunk_001"
      }
    ],
    "source": "freeswitch-node-01",
    "timestamp": "2024-01-15T10:36:00Z"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "processed": 1,
  "batch_id": "batch001",
  "sgapi_reference": "sgapi-20240115-103600-001"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid CDR record format |
| 401 | Authentication required |
| 403 | Insufficient permissions for CDR processing |
| 422 | CDR validation failed |
| 500 | Internal processing error |

---

### Perform CDR Munch Task

Triggers CDR processing tasks for batch operations.

```
POST /cdrmunch/task
PUT /cdrmunch/task
```

#### Description

Initiates or updates a CDR munch task for processing accumulated call records. Supports both creation (PUT) and update (POST) of processing tasks.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `task_type` | string | body | Yes | Type of munch task (`process`, `reprocess`, `cleanup`) |
| `date_range` | object | body | No | Date range for processing |
| `date_range.start` | string | body | No | Start date (ISO 8601) |
| `date_range.end` | string | body | No | End date (ISO 8601) |
| `org_id` | integer | body | No | Filter by organization ID |
| `priority` | string | body | No | Task priority (`low`, `normal`, `high`) |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/cdrmunch/task" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "process",
    "date_range": {
      "start": "2024-01-15T00:00:00Z",
      "end": "2024-01-15T23:59:59Z"
    },
    "priority": "high"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "task_id": "cdrmunch-task-20240115-001",
  "task_type": "process",
  "queued_at": "2024-01-15T11:00:00Z",
  "estimated_records": 15420,
  "priority": "high"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid task parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 409 | Conflicting task already running |
| 500 | Task creation failed |

---

## Event Logging

### Create Event Log Entry

Creates a new event log entry for audit and tracking purposes.

```
PUT /eventlog/:orgId
```

#### Description

Records platform events for a specific organization. Events can include user actions, system events, security incidents, and configuration changes.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | integer | path | Yes | Organization ID |
| `event_type` | string | body | Yes | Type of event (e.g., `user_login`, `config_change`, `security`) |
| `severity` | string | body | No | Event severity (`info`, `warning`, `error`, `critical`) |
| `actor_id` | integer | body | No | User ID who triggered the event |
| `actor_type` | string | body | No | Type of actor (`user`, `system`, `api`) |
| `resource_type` | string | body | No | Type of resource affected |
| `resource_id` | string | body | No | ID of the affected resource |
| `description` | string | body | Yes | Human-readable event description |
| `metadata` | object | body | No | Additional event-specific data |
| `ip_address` | string | body | No | Source IP address |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/eventlog/12345" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "config_change",
    "severity": "info",
    "actor_id": 67890,
    "actor_type": "user",
    "resource_type": "dialplan",
    "resource_id": "dp-001",
    "description": "Updated outbound dialing rules",
    "metadata": {
      "previous_value": "old_rule",
      "new_value": "new_rule",
      "fields_changed": ["destination_pattern", "priority"]
    },
    "ip_address": "192.168.1.100"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "event_log_id": "evt-20240115-abc123",
  "org_id": 12345,
  "created_at": "2024-01-15T11:30:00Z",
  "event_type": "config_change",
  "severity": "info"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid event data |
| 401 | Authentication required |
| 403 | Not authorized for this organization |
| 404 | Organization not found |
| 500 | Failed to create event log |

---

### Get Event Log Entry

Retrieves a specific event log entry.

```
GET /eventlog/:orgId/:eventLogId
```

#### Description

Fetches detailed information about a specific event log entry within an organization.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | integer | path | Yes | Organization ID |
| `eventLogId` | string | path | Yes | Event log entry ID |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/eventlog/12345/evt-20240115-abc123" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "event_log_id": "evt-20240115-abc123",
  "org_id": 12345,
  "event_type": "config_change",
  "severity": "info",
  "actor": {
    "id": 67890,
    "type": "user",
    "name": "John Smith",
    "email": "john.smith@example.com"
  },
  "resource": {
    "type": "dialplan",
    "id": "dp-001",
    "name": "Main Outbound Plan"
  },
  "description": "Updated outbound dialing rules",
  "metadata": {
    "previous_value": "old_rule",
    "new_value": "new_rule",
    "fields_changed": ["destination_pattern", "priority"]
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2024-01-15T11:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Authentication required |
| 403 | Not authorized for this organization |
| 404 | Event log entry not found |
| 500 | Internal server error |

---

### Search Event Logs

Searches and filters event logs for an organization.

```
POST /eventlog/:orgId
```

#### Description

Performs a search across event logs with various filtering options. Supports pagination for large result sets.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | integer | path | Yes | Organization ID |
| `event_types` | array | body | No | Filter by event types |
| `severities` | array | body | No | Filter by severity levels |
| `actor_id` | integer | body | No | Filter by actor user ID |
| `actor_type` | string | body | No | Filter by actor type |
| `resource_type` | string | body | No | Filter by resource type |
| `resource_id` | string | body | No | Filter by resource ID |
| `date_from` | string | body | No | Start date (ISO 8601) |
| `date_to` | string | body | No | End date (ISO 8601) |
| `search_text` | string | body | No | Full-text search in descriptions |
| `ip_address` | string | body | No | Filter by source IP |
| `page` | integer | body | No | Page number (default: 1) |
| `per_page` | integer | body | No | Results per page (default: 50, max: 500) |
| `sort_by` | string | body | No | Sort field (`created_at`, `severity`, `event_type`) |
| `sort_order` | string | body | No | Sort direction (`asc`, `desc`) |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/eventlog/12345" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_types": ["config_change", "security"],
    "severities": ["warning", "error", "critical"],
    "date_from": "2024-01-01T00:00:00Z",
    "date_to": "2024-01-15T23:59:59Z",
    "page": 1,
    "per_page": 25,
    "sort_by": "created_at",
    "sort_order": "desc"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_records": 156,
    "total_pages": 7
  },
  "results": [
    {
      "event_log_id": "evt-20240115-def456",
      "event_type": "security",
      "severity": "warning",
      "description": "Failed login attempt from unknown IP",
      "actor": {
        "type": "system"
      },
      "ip_address": "203.0.113.50",
      "created_at": "2024-01-15T10:45:00Z"
    },
    {
      "event_log_id": "evt-20240115-abc123",
      "event_type": "config_change",
      "severity": "warning",
      "description": "Updated outbound dialing rules",
      "actor": {
        "id": 67890,
        "type": "user",
        "name": "John Smith"
      },
      "created_at": "2024-01-15T11:30:00Z"
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid search parameters |
| 401 | Authentication required |
| 403 | Not authorized for this organization |
| 404 | Organization not found |
| 500 | Search failed |

---

## Logs Management

### Read Logs

Retrieves logs for a specified entity.

```
GET /logs/:entity
```

#### Description

Fetches system logs associated with a specific entity (user, device, trunk, etc.). Useful for debugging and audit purposes.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (e.g., `user/123`, `device/456`) |
| `type` | string | query | No | Log type filter (`call`, `sip`, `error`, `debug`) |
| `from` | string | query | No | Start timestamp (ISO 8601) |
| `to` | string | query | No | End timestamp (ISO 8601) |
| `limit` | integer | query | No | Maximum records to return (default: 100) |
| `offset` | integer | query | No | Offset for pagination |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/logs/user/67890?type=call&from=2024-01-15T00:00:00Z&limit=50" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "status": "success",
  "entity": "user/67890",
  "count": 50,
  "total": 1234,
  "logs": [
    {
      "id": "log-001",
      "timestamp": "2024-01-15T10:30:00Z",
      "type": "call",
      "level": "info",
      "message": "Outbound call initiated to +14155555678",
      "details": {
        "call_id": "call-abc123",
        "destination": "+14155555678",
        "trunk": "trunk_001"
      }
    },
    {
      "id": "log-002",
      "timestamp": "2024-01-15T10:35:42Z",
      "type": "call",
      "level": "info",
      "message": "Call completed",
      "details": {
        "call_id": "call-abc123",
        "duration": 342,
        "disposition": "ANSWERED"
      }
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid parameters |
| 401 | Authentication required |
| 403 | Not authorized to view logs for this entity |
| 404 | Entity not found |
| 500 | Failed to retrieve logs |

---

### File Imported Call Logs

Files imported call log data for processing.

```
POST /logs/:entity
```

#### Description

Allows importing call logs from external systems or bulk uploading historical data for a specific entity.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier for log association |
| `logs` | array | body | Yes | Array of log entries to import |
| `logs[].timestamp` | string | body | Yes | Log timestamp (ISO 8601) |
| `logs[].type` | string | body | Yes | Log type |
| `logs[].level` | string | body | No | Log level (`debug`, `info`, `warning`, `error`) |
| `logs[].message` | string | body | Yes | Log message |
| `logs[].details` | object | body | No | Additional log details |
| `source` | string | body | No | Source system identifier |
| `deduplicate` | boolean | body | No | Skip duplicate entries (default: true) |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/logs/trunk/trunk_001" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      {
        "timestamp": "2024-01-14T15:00:00Z",
        "type": "call",
        "level": "info",
        "message": "Call processed via trunk",
        "details": {
          "call_id": "imported-001",
          "duration": 120
        }
      },
      {
        "timestamp": "2024-01-14T15:30:00Z",
        "type": "call",
        "level": "warning",
        "message": "Call failed - trunk congestion",
        "details": {
          "call_id": "imported-002",
          "error_code": "503"
        }
      }
    ],
    "source": "legacy-pbx-import",
    "deduplicate": true
  }'
```

#### Response Example

```json
{
  "status": "success",
  "imported": 2,
  "duplicates_skipped": 0,
  "entity": "trunk/trunk_001",
  "import_id": "import-20240115-001"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid log format |
| 401 | Authentication required |
| 403 | Not authorized to import logs for this entity |
| 413 | Payload too large |
| 422 | Log validation failed |
| 500 | Import failed |

---

## SIP Gateway Monitoring

### Get SIP Gateway Ping Status

Retrieves the health status of a SIP gateway.

```
GET /sipgwping/:entity
```

#### Description

Returns the current ping status and health metrics for a specified SIP gateway. Used for monitoring gateway availability and performance.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Gateway identifier or name |
| `include_history` | boolean | query | No | Include historical ping data |
| `history_hours` | integer | query | No | Hours of history to include (default: 24) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/sipgwping/gateway-east-01?include_history=true&history_hours=6" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "status": "success",
  "gateway": {
    "id": "gateway-east-01",
    "name": "East Coast Primary Gateway",
    "host": "sip-east.example.com",
    "port": 5060
  },
  "current_status": {
    "reachable": true,
    "latency_ms": 23,
    "last_check": "2024-01-15T11:55:00Z",
    "consecutive_successes": 288,
    "uptime_percent_24h": 99.98
  },
  "history": [
    {
      "timestamp": "2024-01-15T11:00:00Z",
      "reachable": true,
      "latency_ms": 21
    },
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "reachable": true,
      "latency_ms": 25
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Authentication required |
| 403 | Not authorized to view gateway status |
| 404 | Gateway not found |
| 500 | Failed to retrieve status |

---

### Update SIP Gateway Ping Status

Updates the ping status for a SIP gateway (typically called by monitoring systems).

```
POST /sipgwping/:entity/:param1/:param2
```

#### Description

Records a new ping result for a SIP gateway. This endpoint is typically called by automated monitoring systems to report gateway health.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Gateway identifier |
| `param1` | string | path | Yes | Status indicator (`up`, `down`, `degraded`) |
| `param2` | string | path | No | Latency in milliseconds |
| `details` | object | body | No | Additional status details |
| `details.latency_ms` | integer | body | No | Measured latency |
| `details.packet_loss` | float | body | No | Packet loss percentage |
| `details.jitter_ms` | integer | body | No | Jitter measurement |
| `details.error_message` | string | body | No | Error message if status is down |
| `source` | string | body | No | Monitoring source identifier |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/sipgwping/gateway-east-01/up/23" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "details": {
      "latency_ms": 23,
      "packet_loss": 0.0,
      "jitter_ms": 2
    },
    "source": "monitor-node-01"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "gateway": "gateway-east-01",
  "recorded_status": "up",
  "latency_ms": 23,
  "recorded_at": "2024-01-15T12:00:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid status parameters |
| 401 | Authentication required |
| 403 | Not authorized to update gateway status |
| 404 | Gateway not found |
| 500 | Failed to record status |

---

## Events

### Get Events

Retrieves events for a specified entity.

```
GET /events/:entity
```

#### Description

Fetches platform events associated with a specific entity. Events represent significant occurrences like registrations, calls, and status changes.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (e.g., `user/123`, `org/456`) |
| `type` | string | query | No | Filter by event type |
| `since` | string | query | No | Return events since timestamp (ISO 8601) |
| `limit` | integer | query | No | Maximum events to return (default: 100) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/events/org/12345?type=registration&limit=25" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "status": "success",
  "entity": "org/12345",
  "events": [
    {
      "event_id": "evt-reg-001",
      "type": "registration",
      "timestamp": "2024-01-15T10:00:00Z",
      "data": {
        "user_id": 67890,
        "device": "Polycom VVX 450",
        "ip_address": "192.168.1.50",
        "registration_type": "new"
      }
    },
    {
      "event_id": "evt-reg-002",
      "type": "registration",
      "timestamp": "2024-01-15T10:30:00Z",
      "data": {
        "user_id": 67891,
        "device": "Yealink T46S",
        "ip_address": "192.168.1.51",
        "registration_type": "refresh"
      }
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid parameters |
| 401 | Authentication required |
| 403 | Not authorized to view events for this entity |
| 404 | Entity not found |
| 500 | Failed to retrieve events |

---

### Create Event

Creates a new event for a specified entity.

```
PUT /events/:entity
```

#### Description

Records a new event for tracking and notification purposes. Events can trigger webhooks or other automated responses.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier |
| `type` | string | body | Yes | Event type |
| `data` | object | body | Yes | Event-specific data |
| `timestamp` | string | body | No | Event timestamp (defaults to current time) |
| `notify` | boolean | body | No | Trigger notifications (default: false) |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/events/user/67890" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "device_offline",
    "data": {
      "device_id": "dev-001",
      "device_name": "Desk Phone",
      "last_seen": "2024-01-15T09:45:00Z",
      "reason": "timeout"
    },
    "notify": true
  }'
```

#### Response Example

```json
{
  "status": "success",
  "event_id": "evt-20240115-xyz789",
  "entity": "user/67890",
  "type": "device_offline",
  "created_at": "2024-01-15T12:00:00Z",
  "notifications_sent": 1
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid event data |
| 401 | Authentication required |
| 403 | Not authorized to create events for this entity |
| 404 | Entity not found |
| 500 | Failed to create event |

---

## Bespoke Data Access

### Read Queue Monitor Bespoke Data

Retrieves custom queue monitoring configuration data.

```
GET /bespoke/queuemon
```

#### Description

Fetches bespoke (custom) configuration data for queue monitoring features. Used for advanced queue statistics and real-time monitoring customizations.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `org_id` | integer | query | No | Filter by organization ID |
| `queue_id` | string | query | No | Filter by specific queue |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/bespoke/queuemon?org_id=12345" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "refresh_interval": 5,
    "display_columns": ["agent_name", "status", "calls_handled", "avg_handle_time"],
    "alert_thresholds": {
      "queue_length": 10,
      "wait_time_seconds": 120,
      "abandon_rate": 5.0
    },
    "custom_metrics": [
      {
        "name": "service_level",
        "formula": "calls_answered_in_20s / total_calls * 100",
        "target": 80
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Authentication required |
| 403 | Not authorized |
| 404 | No bespoke data found |
| 500 | Failed to retrieve data |

---

### Read Notifier Bespoke Data

Retrieves custom notification configuration data.

```
GET /bespoke/notifier
```

#### Description

Fetches bespoke configuration for the notification system, including custom notification rules, templates, and delivery preferences.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `org_id` | integer | query | No | Filter by organization ID |
| `type` | string | query | No | Filter by notification type |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/bespoke/notifier?org_id=12345&type=sms" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "notification_rules": [
      {
        "id": "rule-001",
        "name": "Missed Call Alert",
        "trigger": "missed_call",
        "channels": ["sms", "email"],
        "template": "You missed a call from {{caller_id}} at {{time}}",
        "enabled": true
      },
      {
        "id": "rule-002",
        "name": "Voicemail Notification",
        "trigger": "new_voicemail",
        "channels": ["email"],
        "template": "New voicemail from {{caller_id}}. Duration: {{duration}}s",
        "enabled": true
      }
    ],
    "delivery_preferences": {
      "quiet_hours": {
        "enabled": true,
        "start": "22:00",
        "end": "07:00"
      },
      "max_notifications_per_hour": 10
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Authentication required |
| 403 | Not authorized |
| 404 | No bespoke data found |
| 500 | Failed to retrieve data |

---

## QR Code Generation

### Generate QR Code

Generates a QR code image from provided data.

```
GET /qrcode/:data
```

#### Description

Creates a QR code image from the provided string data. Commonly used for generating two-factor authentication setup codes, provisioning URLs, or contact information.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `data` | string | path | Yes | Data to encode in QR code (URL encoded) |
| `size` | integer | query | No | QR code size in pixels (default: 200) |
| `format` | string | query | No | Image format (`png`, `svg`) - default: `png` |
| `margin` | integer | query | No | Margin around QR code (default: 4) |
| `error_correction` | string | query | No | Error correction level (`L`, `M`, `Q`, `H`) - default: `M` |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/qrcode/otpauth%3A%2F%2Ftotp%2FPlatform%3Auser%40example.com%3Fsecret%3DJBSWY3DPEHPK3PXP?size=300&format=png" \
  -H "Authorization: Bearer {token}" \
  --output qrcode.png
```

#### Response

Returns binary image data with appropriate content-type header (`image/png` or `image/svg+xml`).

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid data or parameters |
| 401 | Authentication required |
| 413 | Data too long for QR code |
| 500 | Failed to generate QR code |

---

## Error Handling

### Generic Error Handler

Handles unmatched routes and system errors.

```
ANY /errors
```

#### Description

This endpoint serves as a catch-all error handler, returning standardized XML error responses for various error conditions.

#### Response Format

Error responses are returned in XML format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<error>
  <code>404</code>
  <message>Resource not found</message>
  <timestamp>2024-01-15T12:00:00Z</timestamp>
  <request_id>req-abc123</request_id>
</error>
```

#### Common Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request syntax or parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource or endpoint not found |
| 405 | Method Not Allowed | HTTP method not supported |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## API Documentation

### Get API Documentation

Returns API documentation for the platform.

```
GET /documentation
```

#### Description

The default route that displays API documentation, providing an overview of available endpoints and usage information.

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/documentation" \
  -H "Authorization: Bearer {token}"
```

#### Response

Returns HTML or JSON documentation depending on the Accept header.

---

## Rate Limiting

Administrative API endpoints are subject to rate limiting:

| Endpoint Category | Rate Limit |
|-------------------|------------|
| CDR Processing | 1000 requests/minute |
| Event Logging | 500 requests/minute |
| Log Queries | 100 requests/minute |
| Gateway Status | 300 requests/minute |
| QR Code Generation | 60 requests/minute |

## Best Practices

1. **CDR Processing**: Batch CDR records when possible to reduce API calls
2. **Event Logging**: Include relevant metadata for effective auditing
3. **Log Searches**: Use specific filters to reduce result sets
4. **Monitoring**: Set up regular health checks using SIP gateway ping endpoints
5. **Error Handling**: Implement exponential backoff for transient failures