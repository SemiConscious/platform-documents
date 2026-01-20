# Platform Sapien API Reference

> **Last Updated**: 2026-01-20  
> **Document Status**: Active  
> **Base URL**: `https://api.{domain}/v1`

## Overview

Platform Sapien provides a RESTful API for managing telephony services, users, recordings, and call data. The API uses OAuth 2.0 for authentication and returns JSON responses.

---

## Authentication

### OAuth 2.0 Token Endpoint

#### Request Access Token

```http
POST /oauth/v2/token
Content-Type: application/x-www-form-urlencoded
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `grant_type` | string | Yes | `password`, `refresh_token`, or `client_credentials` |
| `client_id` | string | Yes | OAuth client ID |
| `client_secret` | string | Yes | OAuth client secret |
| `username` | string | Conditional | Required for `password` grant |
| `password` | string | Conditional | Required for `password` grant |
| `refresh_token` | string | Conditional | Required for `refresh_token` grant |
| `scope` | string | No | Space-separated list of scopes |

**Example Request (Password Grant)**:
```bash
curl -X POST https://api.example.com/oauth/v2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=your_client_id" \
  -d "client_secret=your_client_secret" \
  -d "username=user@example.com" \
  -d "password=user_password"
```

**Success Response** (200 OK):
```json
{
    "access_token": "YTk4NTY3OGM0YzM2MjU5N2E2NjAyMjI5M...",
    "expires_in": 3600,
    "token_type": "bearer",
    "scope": "read write",
    "refresh_token": "ZDRiZmE5NjM4ZDU5M2Q1YjY2NzEwYTk2..."
}
```

**Error Response** (400 Bad Request):
```json
{
    "error": "invalid_grant",
    "error_description": "Invalid username and password combination"
}
```

### Using Access Tokens

Include the access token in the Authorization header:

```http
Authorization: Bearer YTk4NTY3OGM0YzM2MjU5N2E2NjAyMjI5M...
```

---

## Customer Management

### List Customers

```http
GET /api/v1/customers
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 25 | Items per page (max 100) |
| `search` | string | No | - | Search term for name/email |
| `status` | string | No | - | Filter by status: `active`, `inactive` |
| `sort` | string | No | `name` | Sort field |
| `order` | string | No | `asc` | Sort order: `asc`, `desc` |

**Example Request**:
```bash
curl -X GET "https://api.example.com/api/v1/customers?page=1&limit=10&status=active" \
  -H "Authorization: Bearer {access_token}"
```

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 12345,
            "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "name": "Acme Corporation",
            "email": "contact@acme.com",
            "phone": "+442071234567",
            "status": "active",
            "created_at": "2024-01-15T10:30:00+00:00",
            "updated_at": "2024-06-20T14:45:00+00:00"
        }
    ],
    "meta": {
        "current_page": 1,
        "per_page": 10,
        "total": 150,
        "total_pages": 15
    }
}
```

### Get Customer

```http
GET /api/v1/customers/{customer_id}
Authorization: Bearer {access_token}
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | integer | Yes | Customer ID |

**Success Response** (200 OK):
```json
{
    "data": {
        "id": 12345,
        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Acme Corporation",
        "email": "contact@acme.com",
        "phone": "+442071234567",
        "address": {
            "line1": "123 Main Street",
            "line2": "Suite 100",
            "city": "London",
            "postcode": "EC1A 1BB",
            "country": "GB"
        },
        "status": "active",
        "settings": {
            "timezone": "Europe/London",
            "language": "en_GB"
        },
        "created_at": "2024-01-15T10:30:00+00:00",
        "updated_at": "2024-06-20T14:45:00+00:00"
    }
}
```

**Error Response** (404 Not Found):
```json
{
    "error": {
        "code": "CUSTOMER_NOT_FOUND",
        "message": "Customer with ID 12345 not found"
    }
}
```

### Create Customer

```http
POST /api/v1/customers
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
    "name": "New Corporation",
    "email": "contact@newcorp.com",
    "phone": "+442079876543",
    "address": {
        "line1": "456 Business Road",
        "city": "Manchester",
        "postcode": "M1 1AA",
        "country": "GB"
    },
    "settings": {
        "timezone": "Europe/London",
        "language": "en_GB"
    }
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Customer name (max 255 chars) |
| `email` | string | Yes | Contact email |
| `phone` | string | No | Contact phone (E.164 format) |
| `address` | object | No | Address object |
| `address.line1` | string | No | Address line 1 |
| `address.line2` | string | No | Address line 2 |
| `address.city` | string | No | City |
| `address.postcode` | string | No | Postal code |
| `address.country` | string | No | ISO 3166-1 alpha-2 country code |
| `settings` | object | No | Customer settings |
| `settings.timezone` | string | No | Timezone (IANA format) |
| `settings.language` | string | No | Language code |

**Success Response** (201 Created):
```json
{
    "data": {
        "id": 12346,
        "uuid": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
        "name": "New Corporation",
        "email": "contact@newcorp.com",
        "status": "active",
        "created_at": "2026-01-20T12:00:00+00:00"
    }
}
```

---

## Audio Management

### List Audio Files

```http
GET /api/v1/audio
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 25 | Items per page |
| `type` | string | No | - | Audio type: `prompt`, `moh`, `greeting` |
| `customer_id` | integer | No | - | Filter by customer |

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 5001,
            "uuid": "audio-uuid-123",
            "name": "Welcome Greeting",
            "type": "greeting",
            "format": "wav",
            "duration_seconds": 15,
            "size_bytes": 240000,
            "customer_id": 12345,
            "url": "https://storage.example.com/audio/greeting-123.wav",
            "created_at": "2024-03-10T09:00:00+00:00"
        }
    ],
    "meta": {
        "current_page": 1,
        "per_page": 25,
        "total": 42
    }
}
```

### Upload Audio File

```http
POST /api/v1/audio
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Form Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | Audio file (WAV, MP3, max 10MB) |
| `name` | string | Yes | Display name |
| `type` | string | Yes | Audio type: `prompt`, `moh`, `greeting` |
| `customer_id` | integer | Yes | Customer ID |

**Example Request**:
```bash
curl -X POST https://api.example.com/api/v1/audio \
  -H "Authorization: Bearer {access_token}" \
  -F "file=@/path/to/audio.wav" \
  -F "name=Welcome Message" \
  -F "type=greeting" \
  -F "customer_id=12345"
```

**Success Response** (201 Created):
```json
{
    "data": {
        "id": 5002,
        "uuid": "audio-uuid-456",
        "name": "Welcome Message",
        "type": "greeting",
        "format": "wav",
        "duration_seconds": 12,
        "size_bytes": 192000,
        "status": "processing",
        "created_at": "2026-01-20T12:30:00+00:00"
    }
}
```

### Download Audio File

```http
GET /api/v1/audio/{audio_id}/download
Authorization: Bearer {access_token}
```

**Response**: Binary audio file with appropriate Content-Type header.

---

## Call Recordings

### List Recordings

```http
GET /api/v1/recordings
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 25 | Items per page (max 100) |
| `customer_id` | integer | No | - | Filter by customer |
| `extension` | string | No | - | Filter by extension |
| `from` | datetime | No | - | Start date (ISO 8601) |
| `to` | datetime | No | - | End date (ISO 8601) |
| `direction` | string | No | - | `inbound`, `outbound`, `internal` |
| `min_duration` | integer | No | - | Minimum duration in seconds |

**Example Request**:
```bash
curl -X GET "https://api.example.com/api/v1/recordings?customer_id=12345&from=2026-01-01T00:00:00Z&to=2026-01-20T23:59:59Z" \
  -H "Authorization: Bearer {access_token}"
```

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 8001,
            "uuid": "rec-uuid-789",
            "call_uuid": "call-uuid-123",
            "customer_id": 12345,
            "extension": "101",
            "caller_id": "+442071111111",
            "callee_id": "+442072222222",
            "direction": "inbound",
            "started_at": "2026-01-15T14:30:00+00:00",
            "duration_seconds": 185,
            "size_bytes": 2960000,
            "status": "available",
            "download_url": "https://storage.example.com/recordings/rec-789.mp3",
            "expires_at": "2026-01-22T14:30:00+00:00"
        }
    ],
    "meta": {
        "current_page": 1,
        "per_page": 25,
        "total": 1250
    }
}
```

### Get Recording

```http
GET /api/v1/recordings/{recording_id}
Authorization: Bearer {access_token}
```

**Success Response** (200 OK):
```json
{
    "data": {
        "id": 8001,
        "uuid": "rec-uuid-789",
        "call_uuid": "call-uuid-123",
        "call_details": {
            "caller_name": "John Smith",
            "queue_name": "Sales Queue",
            "agent_name": "Jane Doe"
        },
        "customer_id": 12345,
        "extension": "101",
        "caller_id": "+442071111111",
        "callee_id": "+442072222222",
        "direction": "inbound",
        "started_at": "2026-01-15T14:30:00+00:00",
        "duration_seconds": 185,
        "format": "mp3",
        "size_bytes": 2960000,
        "bitrate": 128000,
        "status": "available",
        "download_url": "https://storage.example.com/recordings/rec-789.mp3",
        "transcription": {
            "status": "completed",
            "text": "Hello, this is John calling about..."
        },
        "retention": {
            "policy": "90_days",
            "expires_at": "2026-04-15T14:30:00+00:00"
        }
    }
}
```

### Download Recording

```http
GET /api/v1/recordings/{recording_id}/download
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `format` | string | No | `mp3` | Download format: `mp3`, `wav` |

**Response**: Binary audio file

---

## Voicemail

### List Voicemails

```http
GET /api/v1/voicemails
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 25 | Items per page |
| `extension` | string | No | - | Filter by extension |
| `status` | string | No | - | `new`, `listened`, `deleted` |
| `from` | datetime | No | - | Start date (ISO 8601) |
| `to` | datetime | No | - | End date (ISO 8601) |

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 3001,
            "uuid": "vm-uuid-456",
            "extension": "101",
            "caller_id": "+442071234567",
            "caller_name": "Unknown Caller",
            "duration_seconds": 45,
            "status": "new",
            "received_at": "2026-01-19T16:45:00+00:00",
            "listened_at": null,
            "transcription": "Hi, this is a message for..."
        }
    ],
    "meta": {
        "current_page": 1,
        "per_page": 25,
        "total": 12
    }
}
```

### Mark Voicemail as Listened

```http
PATCH /api/v1/voicemails/{voicemail_id}/listened
Authorization: Bearer {access_token}
```

**Success Response** (200 OK):
```json
{
    "data": {
        "id": 3001,
        "status": "listened",
        "listened_at": "2026-01-20T10:30:00+00:00"
    }
}
```

---

## Users

### List Users

```http
GET /api/v1/users
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 25 | Items per page |
| `customer_id` | integer | No | - | Filter by customer |
| `role` | string | No | - | Filter by role |
| `status` | string | No | - | `active`, `inactive`, `suspended` |

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 1001,
            "uuid": "user-uuid-123",
            "email": "john.smith@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "role": "user",
            "customer_id": 12345,
            "extension": "101",
            "status": "active",
            "last_login_at": "2026-01-19T09:15:00+00:00",
            "created_at": "2024-03-01T10:00:00+00:00"
        }
    ],
    "meta": {
        "current_page": 1,
        "per_page": 25,
        "total": 85
    }
}
```

### Create User

```http
POST /api/v1/users
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
    "email": "jane.doe@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "password": "SecureP@ssw0rd!",
    "role": "user",
    "customer_id": 12345,
    "extension": "102",
    "settings": {
        "timezone": "Europe/London",
        "language": "en_GB",
        "notifications": {
            "email": true,
            "sms": false
        }
    }
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email (unique) |
| `first_name` | string | Yes | First name |
| `last_name` | string | Yes | Last name |
| `password` | string | Yes | Password (min 8 chars, complexity required) |
| `role` | string | Yes | Role: `admin`, `manager`, `user` |
| `customer_id` | integer | Yes | Customer ID |
| `extension` | string | No | Phone extension |
| `settings` | object | No | User settings |

**Success Response** (201 Created):
```json
{
    "data": {
        "id": 1002,
        "uuid": "user-uuid-456",
        "email": "jane.doe@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "role": "user",
        "status": "active",
        "created_at": "2026-01-20T12:00:00+00:00"
    }
}
```

---

## Extensions

### List Extensions

```http
GET /api/v1/extensions
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `customer_id` | integer | No | - | Filter by customer |
| `status` | string | No | - | `active`, `inactive` |
| `type` | string | No | - | `user`, `queue`, `ivr`, `parking` |

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 2001,
            "extension": "101",
            "name": "John Smith",
            "type": "user",
            "customer_id": 12345,
            "user_id": 1001,
            "status": "active",
            "caller_id": "+442071234567",
            "voicemail_enabled": true,
            "recording_enabled": true,
            "created_at": "2024-03-01T10:00:00+00:00"
        }
    ],
    "meta": {
        "current_page": 1,
        "per_page": 25,
        "total": 150
    }
}
```

---

## Call Queues

### List Queues

```http
GET /api/v1/queues
Authorization: Bearer {access_token}
```

**Success Response** (200 OK):
```json
{
    "data": [
        {
            "id": 4001,
            "extension": "800",
            "name": "Sales Queue",
            "customer_id": 12345,
            "strategy": "ring_all",
            "timeout_seconds": 30,
            "max_wait_seconds": 300,
            "agents": [
                {
                    "extension": "101",
                    "name": "John Smith",
                    "penalty": 0
                },
                {
                    "extension": "102",
                    "name": "Jane Doe",
                    "penalty": 1
                }
            ],
            "settings": {
                "announce_position": true,
                "music_on_hold": "default",
                "wrap_up_time": 10
            },
            "stats": {
                "calls_waiting": 2,
                "agents_available": 3,
                "average_wait_time": 45
            }
        }
    ]
}
```

### Get Queue Statistics

```http
GET /api/v1/queues/{queue_id}/stats
Authorization: Bearer {access_token}
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `from` | datetime | No | Today | Start date |
| `to` | datetime | No | Now | End date |
| `interval` | string | No | `hour` | `hour`, `day`, `week` |

**Success Response** (200 OK):
```json
{
    "data": {
        "queue_id": 4001,
        "period": {
            "from": "2026-01-20T00:00:00+00:00",
            "to": "2026-01-20T23:59:59+00:00"
        },
        "summary": {
            "total_calls": 156,
            "answered_calls": 142,
            "abandoned_calls": 14,
            "answer_rate": 91.03,
            "average_wait_time": 35,
            "average_talk_time": 180,
            "service_level": 85.5
        },
        "hourly": [
            {
                "hour": "09:00",
                "calls": 15,
                "answered": 14,
                "abandoned": 1,
                "avg_wait": 28
            }
        ]
    }
}
```

---

## Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Error Response Format

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "The request contains invalid parameters",
        "details": [
            {
                "field": "email",
                "message": "Email is already registered"
            }
        ]
    }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_TOKEN` | Access token is invalid or expired |
| `INSUFFICIENT_SCOPE` | Token lacks required scope |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `VALIDATION_ERROR` | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `PERMISSION_DENIED` | Insufficient permissions |

---

## Rate Limiting

API requests are rate limited per client:

| Tier | Requests/Minute | Requests/Hour |
|------|-----------------|---------------|
| Standard | 60 | 1000 |
| Premium | 120 | 5000 |
| Enterprise | 300 | 10000 |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705750800
```

---

## Webhooks

### Available Events

| Event | Description |
|-------|-------------|
| `call.started` | Call has begun |
| `call.ended` | Call has ended |
| `call.recording.ready` | Recording available |
| `voicemail.received` | New voicemail |
| `user.created` | User created |
| `user.updated` | User updated |
| `extension.status.changed` | Extension status changed |

### Webhook Payload

```json
{
    "id": "evt_123456789",
    "type": "call.ended",
    "created_at": "2026-01-20T14:30:00+00:00",
    "data": {
        "call_uuid": "call-uuid-123",
        "customer_id": 12345,
        "extension": "101",
        "duration_seconds": 185,
        "disposition": "answered"
    }
}
```

### Webhook Security

Webhooks include a signature header for verification:

```
X-Sapien-Signature: sha256=abc123...
```

Verify by computing HMAC-SHA256 of the raw body with your webhook secret.
