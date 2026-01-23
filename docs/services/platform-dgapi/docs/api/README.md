# Platform DGAPI - API Reference Overview

## Introduction

The Disposition Gateway API (DGAPI) is a CodeIgniter-based REST API service that orchestrates task disposition workflows for the platform. It serves as the central hub for processing and routing various notification types including SMS messages, emails, voicemail notifications, and callback finish events. The API also handles Call Detail Record (CDR) processing and normalization for integration with downstream services.

DGAPI follows a task-based architecture where each operation creates a trackable task entity that can be monitored for status and completion.

## Base URL

```
https://api.example.com/dgapi/v1
```

## Authentication

All API requests require authentication using one of the following methods:

| Method | Header | Description |
|--------|--------|-------------|
| API Key | `X-API-Key: <your-api-key>` | Primary authentication method for service-to-service communication |
| Bearer Token | `Authorization: Bearer <token>` | OAuth 2.0 bearer token for authenticated sessions |

### Example

```bash
curl -X GET "https://api.example.com/dgapi/v1/info" \
  -H "X-API-Key: your-api-key-here"
```

## API Endpoint Categories

The DGAPI endpoints are organized into the following functional areas:

| Category | Description | Endpoints | Documentation |
|----------|-------------|-----------|---------------|
| **Info & Health** | API status, health checks, and service information | 2 | [Info Endpoints](info-endpoints.md) |
| **Messaging** | SMS and Email notification services | 5 | [Messaging Endpoints](messaging-endpoints.md) |
| **Task Management** | Task creation, status tracking, and generic task handling | 5 | [Task Endpoints](task-endpoints.md) |
| **CDR Processing** | Call Detail Record processing and SGAPI integration | 3 | [CDR Endpoints](cdr-endpoints.md) |

## Endpoint Summary

### Info & Health Endpoints
- `GET /info` - API health and status
- `GET /info/:entity` - Entity-specific information

### Messaging Endpoints
- `PUT /email` - Send template email
- `GET /email/:entity` - Get email status
- `PUT|POST /sms/{entity}` - Send SMS message
- `GET /sms/{entity}` - Get SMS status
- `PUT /voicemail/{entity}` - Create voicemail notification
- `GET /voicemail/{entity}` - Get voicemail status

### Task Management Endpoints
- `GET /task/{entity}` - Get task status
- `PUT|POST /cbfinish/{entity}` - Create callback finish task
- `PUT /generic/{entity}` - Create generic task
- `GET /generic/{entity}` - Get generic task status

### CDR Processing Endpoints
- `PUT /cdrtosgapi` - Create CDR processing task
- `PUT /cdrtosgapi/{entity}` - Create CDR task for specific entity
- `GET /cdrtosgapi/:uuid` - Get CDR task status

## Common Request/Response Patterns

### Request Format

All request bodies should be sent as JSON with the appropriate content type header:

```bash
Content-Type: application/json
```

### Standard Response Structure

Successful responses follow this structure:

```json
{
  "status": "success",
  "data": {
    "task_id": "uuid-string",
    "entity": "entity-identifier",
    "state": "pending|processing|completed|failed"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Task States

All tasks progress through these states:

| State | Description |
|-------|-------------|
| `pending` | Task created and queued for processing |
| `processing` | Task is actively being processed |
| `completed` | Task finished successfully |
| `failed` | Task encountered an error |
| `cancelled` | Task was cancelled before completion |

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource/task created successfully |
| `400` | Bad Request | Invalid request parameters or body |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource or endpoint not found |
| `409` | Conflict | Resource already exists or state conflict |
| `422` | Unprocessable Entity | Valid syntax but semantic errors |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "phone_number",
      "provided": "123",
      "expected": "E.164 format"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Invalid or missing credentials |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource does not exist |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVICE_UNAVAILABLE` | Downstream service unavailable |
| `INTERNAL_ERROR` | Unexpected server error |

## Rate Limiting

API requests are rate-limited to ensure service stability:

| Tier | Limit | Window |
|------|-------|--------|
| Standard | 100 requests | Per minute |
| Burst | 20 requests | Per second |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705315800
```

When rate limited, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

## Pagination

List endpoints support pagination using the following query parameters:

| Parameter | Default | Maximum | Description |
|-----------|---------|---------|-------------|
| `page` | 1 | - | Page number |
| `limit` | 25 | 100 | Results per page |

Paginated responses include metadata:

```json
{
  "data": [...],
  "pagination": {
    "current_page": 1,
    "per_page": 25,
    "total_pages": 10,
    "total_records": 250
  }
}
```

## Idempotency

For `PUT` and `POST` requests, you can include an idempotency key to prevent duplicate operations:

```bash
X-Idempotency-Key: unique-request-identifier
```

Duplicate requests with the same idempotency key within 24 hours will return the original response.

## Versioning

The API version is included in the base URL path. The current version is `v1`. Deprecation notices will be communicated via response headers:

```
X-API-Deprecated: true
X-API-Sunset-Date: 2025-01-01
```

## Detailed Documentation

For complete endpoint specifications including parameters, request/response examples, and error codes, see the topic-specific documentation:

- **[Info Endpoints](info-endpoints.md)** - Health checks and service status
- **[Messaging Endpoints](messaging-endpoints.md)** - SMS, Email, and Voicemail services
- **[Task Endpoints](task-endpoints.md)** - Task management and callback handling
- **[CDR Endpoints](cdr-endpoints.md)** - Call Detail Record processing

## Support

For API support or to report issues:

- **Technical Support**: api-support@example.com
- **Status Page**: https://status.example.com
- **API Changelog**: [CHANGELOG.md](../CHANGELOG.md)