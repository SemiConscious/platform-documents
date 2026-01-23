# Messaging API

The Messaging API provides endpoints for sending SMS messages and templated emails to recipients. These endpoints integrate with the DGAPI gateway to deliver communications across the platform.

## Overview

The messaging system supports two primary communication channels:

| Channel | Endpoint | Description |
|---------|----------|-------------|
| SMS | `PUT /sms` | Send SMS messages to one or more recipients |
| Email | `PUT /email` | Send templated emails using predefined templates |

## Authentication

All messaging endpoints require authentication via Bearer token or API key. See the [Authentication Guide](authentication.md) for details.

```
Authorization: Bearer {token}
```

---

## SMS Messaging

### Send SMS Message

Send an SMS message to one or more recipients via the DGAPI gateway.

```
PUT /sms
```

#### Description

Sends an SMS message to the specified recipient phone numbers. The message is processed through the DGAPI gateway and delivered to the carrier network. Supports both single and bulk messaging.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `to` | string/array | body | Yes | Recipient phone number(s) in E.164 format |
| `from` | string | body | Yes | Sender phone number or alphanumeric sender ID |
| `message` | string | body | Yes | The SMS message content (max 160 chars for single SMS, or concatenated) |
| `orgId` | integer | body | No | Organization ID for billing purposes |
| `userId` | integer | body | No | User ID initiating the message |
| `callback_url` | string | body | No | URL for delivery status webhooks |
| `reference` | string | body | No | Custom reference ID for tracking |
| `schedule` | string | body | No | ISO 8601 datetime to schedule message delivery |

#### Request Example

```bash
curl -X PUT "https://api.example.com/sms" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+14155551234",
    "from": "+14155550000",
    "message": "Your verification code is 123456",
    "orgId": 1001,
    "reference": "verification-abc123",
    "callback_url": "https://yourapp.com/webhooks/sms"
  }'
```

#### Bulk SMS Example

```bash
curl -X PUT "https://api.example.com/sms" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["+14155551234", "+14155551235", "+14155551236"],
    "from": "+14155550000",
    "message": "System maintenance scheduled for tonight at 10 PM EST.",
    "orgId": 1001,
    "reference": "maintenance-notice-2024"
  }'
```

#### Response Example

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "message_id": "msg_7f8a9b0c1d2e3f4g",
    "status": "queued",
    "to": "+14155551234",
    "from": "+14155550000",
    "segments": 1,
    "reference": "verification-abc123",
    "created_at": "2024-01-15T10:30:00Z",
    "estimated_cost": 0.0075
  }
}
```

**Bulk Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123def456",
    "total_messages": 3,
    "queued": 3,
    "failed": 0,
    "messages": [
      {
        "message_id": "msg_7f8a9b0c1d2e3f4g",
        "to": "+14155551234",
        "status": "queued"
      },
      {
        "message_id": "msg_8g9b0c1d2e3f4g5h",
        "to": "+14155551235",
        "status": "queued"
      },
      {
        "message_id": "msg_9h0c1d2e3f4g5h6i",
        "to": "+14155551236",
        "status": "queued"
      }
    ]
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_PHONE_NUMBER` | The recipient phone number is not in valid E.164 format |
| 400 | `MESSAGE_TOO_LONG` | Message exceeds maximum allowed length |
| 400 | `INVALID_SENDER` | The sender ID is not valid or not authorized |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 402 | `INSUFFICIENT_CREDITS` | Organization does not have sufficient SMS credits |
| 403 | `SMS_DISABLED` | SMS functionality is disabled for this organization |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests; please retry later |
| 500 | `GATEWAY_ERROR` | DGAPI gateway encountered an error |

---

## Email Messaging

### Send Templated Email

Send an email using a predefined template through the DGAPI gateway.

```
PUT /email
```

#### Description

Sends an email to recipients using a pre-configured email template. Templates support variable substitution for personalization. This endpoint integrates with the DGAPI `SendTemplateEmail` function.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `to` | string/array | body | Yes | Recipient email address(es) |
| `template` | string | body | Yes | Template identifier/name |
| `subject` | string | body | No | Email subject (overrides template default) |
| `variables` | object | body | No | Key-value pairs for template variable substitution |
| `from` | string | body | No | Sender email address (overrides template default) |
| `from_name` | string | body | No | Sender display name |
| `reply_to` | string | body | No | Reply-to email address |
| `cc` | string/array | body | No | CC recipient(s) |
| `bcc` | string/array | body | No | BCC recipient(s) |
| `orgId` | integer | body | No | Organization ID for tracking |
| `attachments` | array | body | No | Array of attachment objects |
| `priority` | string | body | No | Email priority: `low`, `normal`, `high` |
| `track_opens` | boolean | body | No | Enable open tracking (default: true) |
| `track_clicks` | boolean | body | No | Enable click tracking (default: true) |

#### Attachment Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | Yes | Name of the attachment file |
| `content` | string | Yes | Base64-encoded file content |
| `content_type` | string | Yes | MIME type of the file |

#### Request Example

```bash
curl -X PUT "https://api.example.com/email" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "template": "welcome_email",
    "variables": {
      "first_name": "John",
      "company_name": "Acme Corp",
      "activation_link": "https://app.example.com/activate?token=xyz123"
    },
    "orgId": 1001
  }'
```

#### Advanced Email Example

```bash
curl -X PUT "https://api.example.com/email" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["user1@example.com", "user2@example.com"],
    "cc": "manager@example.com",
    "template": "monthly_report",
    "subject": "Your Monthly Usage Report - January 2024",
    "from": "reports@company.com",
    "from_name": "Company Reports",
    "reply_to": "support@company.com",
    "variables": {
      "month": "January",
      "year": "2024",
      "total_calls": "1,234",
      "total_minutes": "5,678",
      "total_cost": "$123.45"
    },
    "attachments": [
      {
        "filename": "report-january-2024.pdf",
        "content": "JVBERi0xLjQKJeLjz9MK...",
        "content_type": "application/pdf"
      }
    ],
    "priority": "normal",
    "track_opens": true,
    "track_clicks": true,
    "orgId": 1001
  }'
```

#### Response Example

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "email_id": "eml_abc123def456",
    "status": "queued",
    "to": ["user@example.com"],
    "template": "welcome_email",
    "subject": "Welcome to Our Platform!",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Multiple Recipients Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "batch_id": "batch_email_789xyz",
    "total_emails": 2,
    "queued": 2,
    "failed": 0,
    "emails": [
      {
        "email_id": "eml_abc123def456",
        "to": "user1@example.com",
        "status": "queued"
      },
      {
        "email_id": "eml_def456ghi789",
        "to": "user2@example.com",
        "status": "queued"
      }
    ]
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_EMAIL_ADDRESS` | One or more email addresses are invalid |
| 400 | `TEMPLATE_NOT_FOUND` | The specified template does not exist |
| 400 | `MISSING_REQUIRED_VARIABLE` | A required template variable is missing |
| 400 | `ATTACHMENT_TOO_LARGE` | Attachment exceeds maximum size limit |
| 400 | `INVALID_ATTACHMENT` | Attachment content is invalid or corrupted |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `EMAIL_DISABLED` | Email functionality is disabled for this organization |
| 403 | `TEMPLATE_NOT_AUTHORIZED` | Organization not authorized to use this template |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests; please retry later |
| 500 | `GATEWAY_ERROR` | DGAPI gateway encountered an error |

---

## SMS Logging

### Push SMS Logs

Push SMS log entries for archival and compliance purposes.

```
POST /smslogs/push
```

#### Description

Files SMS log data for record-keeping, compliance, and analytics. This endpoint is typically used by internal systems to archive SMS transactions.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | integer | body | Yes | Organization ID |
| `logs` | array | body | Yes | Array of SMS log entries |

#### Log Entry Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | string | Yes | Unique message identifier |
| `direction` | string | Yes | `inbound` or `outbound` |
| `from` | string | Yes | Sender phone number |
| `to` | string | Yes | Recipient phone number |
| `message` | string | Yes | Message content |
| `status` | string | Yes | Delivery status |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `userId` | integer | No | Associated user ID |
| `segments` | integer | No | Number of SMS segments |
| `cost` | number | No | Cost of the message |

#### Request Example

```bash
curl -X POST "https://api.example.com/smslogs/push" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "orgId": 1001,
    "logs": [
      {
        "message_id": "msg_7f8a9b0c1d2e3f4g",
        "direction": "outbound",
        "from": "+14155550000",
        "to": "+14155551234",
        "message": "Your verification code is 123456",
        "status": "delivered",
        "timestamp": "2024-01-15T10:30:00Z",
        "userId": 5001,
        "segments": 1,
        "cost": 0.0075
      }
    ]
  }'
```

#### Response Example

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "processed": 1,
    "failed": 0,
    "batch_id": "logbatch_xyz789"
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_LOG_FORMAT` | Log entries are not in the correct format |
| 400 | `MISSING_REQUIRED_FIELD` | A required field is missing from log entry |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `FORBIDDEN` | Not authorized to push logs for this organization |
| 413 | `PAYLOAD_TOO_LARGE` | Too many log entries in a single request |

---

### Search SMS Logs

Queue a search request for SMS logs.

```
POST /smslogs/search
```

#### Description

Initiates an asynchronous search of SMS logs based on specified criteria. Returns a search job ID that can be used to retrieve results.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | integer | body | Yes | Organization ID |
| `start_date` | string | body | Yes | Start date for search (ISO 8601) |
| `end_date` | string | body | Yes | End date for search (ISO 8601) |
| `direction` | string | body | No | Filter by direction: `inbound`, `outbound`, `all` |
| `from` | string | body | No | Filter by sender phone number |
| `to` | string | body | No | Filter by recipient phone number |
| `userId` | integer | body | No | Filter by user ID |
| `status` | string | body | No | Filter by delivery status |
| `content` | string | body | No | Search within message content |
| `limit` | integer | body | No | Maximum results to return (default: 1000) |

#### Request Example

```bash
curl -X POST "https://api.example.com/smslogs/search" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "orgId": 1001,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "direction": "outbound",
    "status": "delivered",
    "limit": 500
  }'
```

#### Response Example

**Success (202 Accepted):**

```json
{
  "success": true,
  "data": {
    "search_id": "search_abc123xyz",
    "status": "processing",
    "estimated_completion": "2024-01-15T10:35:00Z",
    "criteria": {
      "orgId": 1001,
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "direction": "outbound",
      "status": "delivered"
    }
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_DATE_RANGE` | Invalid or missing date range |
| 400 | `DATE_RANGE_TOO_LARGE` | Date range exceeds maximum allowed (90 days) |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `FORBIDDEN` | Not authorized to search logs for this organization |

---

### Download SMS Log Results

Download the results of a completed SMS log search.

```
POST /smslogs/download
```

#### Description

Retrieves the results of a previously queued SMS log search. The search must be in a `completed` state.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `search_id` | string | body | Yes | Search job ID from the search request |
| `format` | string | body | No | Output format: `json` (default), `csv` |
| `page` | integer | body | No | Page number for paginated results |
| `per_page` | integer | body | No | Results per page (default: 100, max: 1000) |

#### Request Example

```bash
curl -X POST "https://api.example.com/smslogs/download" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "search_id": "search_abc123xyz",
    "format": "json",
    "page": 1,
    "per_page": 100
  }'
```

#### Response Example

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "search_id": "search_abc123xyz",
    "total_results": 250,
    "page": 1,
    "per_page": 100,
    "total_pages": 3,
    "results": [
      {
        "message_id": "msg_7f8a9b0c1d2e3f4g",
        "direction": "outbound",
        "from": "+14155550000",
        "to": "+14155551234",
        "message": "Your verification code is 123456",
        "status": "delivered",
        "timestamp": "2024-01-15T10:30:00Z",
        "userId": 5001,
        "segments": 1,
        "cost": 0.0075
      },
      {
        "message_id": "msg_8h9i0j1k2l3m4n5o",
        "direction": "outbound",
        "from": "+14155550000",
        "to": "+14155551235",
        "message": "Your appointment is confirmed for tomorrow.",
        "status": "delivered",
        "timestamp": "2024-01-15T11:00:00Z",
        "userId": 5002,
        "segments": 1,
        "cost": 0.0075
      }
    ]
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_SEARCH_ID` | The search ID is invalid or not found |
| 400 | `SEARCH_NOT_COMPLETE` | The search is still processing |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `SEARCH_EXPIRED` | Search results have expired and are no longer available |
| 410 | `SEARCH_FAILED` | The search job failed; please retry |

---

## SMS Archiving

### Store SMS Export Data

Store SMS export data for archiving compliance.

```
PUT /archiving/store/smsexport
```

#### Description

Stores SMS data exports for long-term archival and compliance purposes. This endpoint is typically used in conjunction with archiving policies.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | integer | body | Yes | Organization ID |
| `policyId` | integer | body | Yes | Archiving policy ID to apply |
| `data` | object | body | Yes | SMS export data object |
| `metadata` | object | body | No | Additional metadata for the export |

#### Data Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | array | Yes | Array of SMS message objects |
| `export_date` | string | Yes | Date of export (ISO 8601) |
| `date_range` | object | Yes | Start and end dates of exported data |

#### Request Example

```bash
curl -X PUT "https://api.example.com/archiving/store/smsexport" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "orgId": 1001,
    "policyId": 50,
    "data": {
      "messages": [
        {
          "message_id": "msg_7f8a9b0c1d2e3f4g",
          "direction": "outbound",
          "from": "+14155550000",
          "to": "+14155551234",
          "message": "Your verification code is 123456",
          "timestamp": "2024-01-15T10:30:00Z"
        }
      ],
      "export_date": "2024-01-16T00:00:00Z",
      "date_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-15T23:59:59Z"
      }
    },
    "metadata": {
      "export_type": "scheduled",
      "retention_days": 365
    }
  }'
```

#### Response Example

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "archive_id": "arch_sms_xyz789",
    "status": "stored",
    "message_count": 1,
    "storage_location": "s3://archive-bucket/org-1001/sms/2024-01/",
    "created_at": "2024-01-16T00:05:00Z",
    "policy_applied": {
      "id": 50,
      "name": "SMS Retention Policy",
      "retention_days": 365
    }
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_DATA_FORMAT` | Export data is not in the correct format |
| 400 | `POLICY_NOT_FOUND` | The specified archiving policy does not exist |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `FORBIDDEN` | Not authorized to archive data for this organization |
| 507 | `STORAGE_FULL` | Archive storage quota exceeded |

---

## Best Practices

### SMS Guidelines

1. **Phone Number Format**: Always use E.164 format (e.g., `+14155551234`) for phone numbers
2. **Message Length**: Keep messages under 160 characters when possible to avoid segmentation
3. **Rate Limiting**: Implement exponential backoff when receiving 429 errors
4. **Delivery Callbacks**: Use `callback_url` to receive delivery status updates asynchronously

### Email Guidelines

1. **Template Variables**: Ensure all required template variables are provided
2. **Attachments**: Keep total attachment size under 10MB
3. **Tracking**: Disable tracking for sensitive or transactional emails if required
4. **Unsubscribe**: Include unsubscribe links for marketing emails

### Error Handling

```bash
# Example with error handling
response=$(curl -s -w "\n%{http_code}" -X PUT "https://api.example.com/sms" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"to": "+14155551234", "from": "+14155550000", "message": "Test"}')

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 429 ]; then
  echo "Rate limited. Retrying after delay..."
  sleep 5
  # Retry logic here
fi
```

---

## Related Documentation

- [Authentication Guide](authentication.md) - Token management and authentication
- [Billing API](billing.md) - SMS and email credit management
- [System API](system.md) - Event logging and notifications