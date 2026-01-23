# Feed Management Endpoints

> **API Reference:** [Overview](README.md) | [MS Dynamics](msdynamics-endpoints.md) | [Salesforce](salesforce-endpoints.md) | [Zendesk](zendesk-endpoints.md) | [Custom](custom-endpoints.md) | **Feed Management** | [Generic](generic-endpoints.md)

This document covers webhook and feed subscription management endpoints for the Platform Service Gateway. Feed endpoints enable session-based access to data feeds, virtual inbox management, and message processing capabilities.

---

## Table of Contents

- [Overview](#overview)
- [Feed Authentication](#feed-authentication)
  - [Create Feed Context](#create-feed-context)
  - [Destroy Feed Context](#destroy-feed-context)
- [Feed Operations](#feed-operations)
  - [Refresh Virtual Inbox](#refresh-virtual-inbox)
  - [Filter Virtual Inbox](#filter-virtual-inbox)
  - [Get Item Count](#get-item-count)
- [Message Navigation](#message-navigation)
  - [Move Through Messages](#move-through-messages)
- [Message Operations](#message-operations)
  - [Get Message Info](#get-message-info)
  - [Get Message Content](#get-message-content)
  - [Mark Message as Read](#mark-message-as-read)
- [SGAPI Authentication](#sgapi-authentication)
  - [Create SGAPI Context](#create-sgapi-context)
  - [Destroy SGAPI Context](#destroy-sgapi-context)
  - [Modify SGAPI Context](#modify-sgapi-context)
- [Task Management](#task-management)
  - [Add Task Activity](#add-task-activity)
- [Error Codes](#error-codes)

---

## Overview

Feed Management provides a session-based system for managing data feeds and virtual inboxes. The workflow typically follows this pattern:

1. **Authenticate** - Create a feed context with credentials
2. **Navigate** - Move through messages in the virtual inbox
3. **Process** - Read message content and metadata
4. **Update** - Mark messages as read
5. **Cleanup** - Destroy the feed context when done

All feed endpoints require a valid session token obtained during context creation.

---

## Feed Authentication

### Create Feed Context

Creates a new feed context and loads the initial virtual inbox.

```
PUT /feed/auth/{token}
```

#### Description

Initializes a feed session using the provided credentials. This loads the virtual inbox and prepares the feed for message operations. The token returned should be used for all subsequent feed operations.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token for the feed |
| `credentials` | object | body | Yes | Feed-specific authentication credentials |
| `norefresh` | boolean | body | No | If `true`, skip initial inbox refresh |

#### Request Example

```bash
curl -X PUT "https://api.example.com/feed/auth/abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "username": "feed_user",
      "password": "secure_password",
      "server": "mail.example.com"
    },
    "norefresh": false
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "token": "abc123token",
    "feed_name": "Primary Inbox",
    "message_count": 42,
    "created_at": "2024-01-15T10:30:00Z",
    "context_id": "ctx_789xyz"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request parameters |
| `401` | Authentication failed with provided credentials |
| `500` | Internal server error during context creation |

---

### Destroy Feed Context

Destroys an existing feed context and releases resources.

```
DELETE /feed/auth/{token}
```

#### Description

Terminates the feed session and cleans up all associated resources including the virtual inbox cache.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token to destroy |

#### Request Example

```bash
curl -X DELETE "https://api.example.com/feed/auth/abc123token"
```

#### Response Example

```json
{
  "status": "success",
  "message": "Feed context destroyed successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `404` | Token not found or already expired |
| `500` | Error during context cleanup |

---

## Feed Operations

### Refresh Virtual Inbox

Refreshes the virtual inbox using the original credentials.

```
GET /feed/refresh/{token}
```

#### Description

Reloads messages from the source feed into the virtual inbox. Use this to sync new messages that arrived after context creation.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |

#### Request Example

```bash
curl -X GET "https://api.example.com/feed/refresh/abc123token"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "message_count": 48,
    "new_messages": 6,
    "refreshed_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |
| `503` | Source feed temporarily unavailable |

---

### Filter Virtual Inbox

Applies a filter to the virtual inbox contents.

```
GET /feed/filter/{token}/{filter}
```

#### Description

Filters messages in the virtual inbox based on specified criteria. The filter persists until changed or the context is destroyed.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |
| `filter` | string | path | Yes | Filter expression (URL-encoded) |

#### Supported Filter Expressions

| Filter Type | Example | Description |
|-------------|---------|-------------|
| `unread` | `unread` | Show only unread messages |
| `from:` | `from:john@example.com` | Filter by sender |
| `subject:` | `subject:invoice` | Filter by subject keyword |
| `date:` | `date:2024-01-15` | Filter by specific date |
| `has:attachment` | `has:attachment` | Messages with attachments |

#### Request Example

```bash
curl -X GET "https://api.example.com/feed/filter/abc123token/unread"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "filter_applied": "unread",
    "filtered_count": 12,
    "total_count": 48
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid filter expression |
| `401` | Invalid or expired token |

---

### Get Item Count

Returns the count of items in the virtual inbox.

```
GET /feed/count/{token}
```

#### Description

Returns the current number of messages in the virtual inbox, respecting any active filters.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |

#### Request Example

```bash
curl -X GET "https://api.example.com/feed/count/abc123token"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "count": 48,
    "unread_count": 12,
    "filter_active": false
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |

---

## Message Navigation

### Move Through Messages

Navigates to a specific position in the virtual inbox.

```
GET /feed/move/{token}/{direction}
```

#### Description

Moves the message pointer to navigate through the virtual inbox. The current position determines which message is accessed by subsequent info and content requests.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |
| `direction` | string | path | Yes | Navigation direction |

#### Direction Values

| Direction | Description |
|-----------|-------------|
| `youngest` | Move to the most recent message |
| `oldest` | Move to the oldest message |
| `nextoldest` | Move to the next older message |
| `nextyoungest` | Move to the next newer message |

#### Request Example

```bash
curl -X GET "https://api.example.com/feed/move/abc123token/youngest"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "position": 1,
    "total_messages": 48,
    "message_id": "msg_001",
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid direction specified |
| `401` | Invalid or expired token |
| `404` | No messages in inbox or end of list reached |

---

## Message Operations

### Get Message Info

Retrieves metadata about the current message.

```
GET /feed/messageinfo/{token}
```

#### Description

Returns information about the currently selected message including feed name, timestamp, sender, subject, and attachment list.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |

#### Request Example

```bash
curl -X GET "https://api.example.com/feed/messageinfo/abc123token"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "message_id": "msg_001",
    "feed_name": "Primary Inbox",
    "received_at": "2024-01-15T10:45:00Z",
    "sender": {
      "name": "John Doe",
      "email": "john.doe@example.com"
    },
    "subject": "Q4 Sales Report",
    "is_read": false,
    "attachments": [
      {
        "filename": "report.pdf",
        "size": 245678,
        "content_type": "application/pdf"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |
| `404` | No message currently selected |

---

### Get Message Content

Retrieves the text content of the current message.

```
GET /feed/messagecontent/{token}
```

#### Description

Returns the full text content of the currently selected message.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |

#### Request Example

```bash
curl -X GET "https://api.example.com/feed/messagecontent/abc123token"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "message_id": "msg_001",
    "content_type": "text/html",
    "body": "<html><body><p>Please find attached the Q4 sales report...</p></body></html>",
    "plain_text": "Please find attached the Q4 sales report..."
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |
| `404` | No message currently selected |
| `500` | Error parsing message content |

---

### Mark Message as Read

Marks the current message as read.

```
PUT /feed/markasread/{token}/{localonly}
```

#### Description

Marks the currently selected message as read in the virtual inbox and optionally in the actual source feed.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |
| `localonly` | boolean | path | Yes | If `true`, only mark read in virtual inbox; if `false`, also mark in source feed |

#### Request Example

```bash
# Mark as read in both virtual inbox and source feed
curl -X PUT "https://api.example.com/feed/markasread/abc123token/false"

# Mark as read only in virtual inbox
curl -X PUT "https://api.example.com/feed/markasread/abc123token/true"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "message_id": "msg_001",
    "marked_read": true,
    "local_only": false,
    "source_updated": true
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |
| `404` | No message currently selected |
| `503` | Source feed unavailable (when `localonly=false`) |

---

## SGAPI Authentication

### Create SGAPI Context

Creates a new SGAPI feed context.

```
PUT /sgapi_auth/auth
```

#### Description

Initializes an SGAPI session and loads the initial virtual inbox. Optionally skip the initial refresh operation.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `credentials` | object | body | Yes | Authentication credentials |
| `feed_type` | string | body | Yes | Type of feed (salesforce, dynamics, zendesk, etc.) |
| `norefresh` | boolean | body | No | Skip initial inbox refresh if `true` |

#### Request Example

```bash
curl -X PUT "https://api.example.com/sgapi_auth/auth" \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "client_id": "your_client_id",
      "client_secret": "your_client_secret",
      "instance_url": "https://yourinstance.salesforce.com"
    },
    "feed_type": "salesforce",
    "norefresh": false
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "token": "sgapi_token_xyz789",
    "feed_type": "salesforce",
    "context_id": "ctx_456abc",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-15T11:30:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request parameters or unsupported feed type |
| `401` | Authentication failed |
| `500` | Internal server error |

---

### Destroy SGAPI Context

Destroys an existing SGAPI feed context.

```
DELETE /sgapi_auth/auth/{token}
```

#### Description

Terminates the SGAPI session and releases all associated resources.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active SGAPI session token |

#### Request Example

```bash
curl -X DELETE "https://api.example.com/sgapi_auth/auth/sgapi_token_xyz789"
```

#### Response Example

```json
{
  "status": "success",
  "message": "SGAPI context destroyed successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `404` | Token not found or already expired |
| `500` | Error during context cleanup |

---

### Modify SGAPI Context

Modifies an existing SGAPI context.

```
POST /sgapi_auth/auth/{token}
```

#### Description

Updates configuration or credentials for an existing SGAPI session without creating a new context.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active SGAPI session token |
| `credentials` | object | body | No | Updated credentials |
| `settings` | object | body | No | Updated context settings |

#### Request Example

```bash
curl -X POST "https://api.example.com/sgapi_auth/auth/sgapi_token_xyz789" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "auto_refresh": true,
      "refresh_interval": 300
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "token": "sgapi_token_xyz789",
    "modified_at": "2024-01-15T10:45:00Z",
    "settings": {
      "auto_refresh": true,
      "refresh_interval": 300
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid modification parameters |
| `401` | Invalid or expired token |
| `500` | Error applying modifications |

---

## Task Management

### Add Task Activity

Adds activity to a task and refreshes the virtual inbox.

```
PUT /sgapi_tasks/task/{token}
```

#### Description

Records an activity against a task and triggers a refresh of the virtual inbox using the original credentials.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `token` | string | path | Yes | Active session token |
| `activity_type` | string | body | Yes | Type of activity to record |
| `description` | string | body | No | Activity description |
| `metadata` | object | body | No | Additional activity metadata |

#### Request Example

```bash
curl -X PUT "https://api.example.com/sgapi_tasks/task/abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "status_update",
    "description": "Processed incoming lead",
    "metadata": {
      "lead_id": "lead_123",
      "status": "qualified"
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "activity_id": "act_789",
    "activity_type": "status_update",
    "created_at": "2024-01-15T10:50:00Z",
    "inbox_refreshed": true,
    "new_message_count": 2
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid activity type or parameters |
| `401` | Invalid or expired token |
| `500` | Error recording activity |

---

## Error Codes

All feed management endpoints may return these common error responses:

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `INVALID_REQUEST` | Request parameters are malformed or missing |
| `401` | `UNAUTHORIZED` | Token is invalid, expired, or missing |
| `403` | `FORBIDDEN` | Insufficient permissions for the requested operation |
| `404` | `NOT_FOUND` | Requested resource (token, message, context) not found |
| `429` | `RATE_LIMITED` | Too many requests, please slow down |
| `500` | `INTERNAL_ERROR` | Unexpected server error |
| `503` | `SERVICE_UNAVAILABLE` | Source feed or dependent service temporarily unavailable |

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "The provided token has expired",
    "details": {
      "token": "abc123token",
      "expired_at": "2024-01-15T09:30:00Z"
    }
  }
}
```

---

## See Also

- [API Overview](README.md) - Authentication and general concepts
- [Generic Endpoints](generic-endpoints.md) - Platform-agnostic data operations
- [Response Models](../models/api-response-models.md) - Standard response formats