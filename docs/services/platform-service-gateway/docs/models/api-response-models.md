# API Response Models

> Standard response structures and error models for the Service Gateway API

This document describes the standard response formats, data models, and error structures used across all Service Gateway API endpoints.

## Overview

The Service Gateway API uses consistent response structures across all platform integrations. Understanding these models is essential for properly handling API responses and implementing error handling in your applications.

---

## Standard Response Structure

### Success Response Model

All successful API responses follow a consistent JSON structure:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    // Response payload varies by endpoint
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123def456",
    "platform": "salesforce"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Response status: `success` or `error` |
| `code` | integer | HTTP status code |
| `data` | object/array | Response payload (structure varies by endpoint) |
| `meta` | object | Metadata about the request/response |
| `meta.timestamp` | string | ISO 8601 timestamp of the response |
| `meta.request_id` | string | Unique identifier for request tracing |
| `meta.platform` | string | The platform that processed the request |

### Query Response Model

Responses from query endpoints include pagination and record information:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "records": [
      {
        "Id": "001ABC123",
        "Name": "Example Record",
        "CreatedDate": "2024-01-10T08:00:00Z"
      }
    ],
    "totalSize": 150,
    "done": false,
    "nextRecordsUrl": "/api/query?offset=100"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123def456",
    "query_time_ms": 245
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.records` | array | Array of record objects |
| `data.totalSize` | integer | Total number of matching records |
| `data.done` | boolean | Whether all records have been returned |
| `data.nextRecordsUrl` | string | URL to fetch next page (if `done` is false) |
| `meta.query_time_ms` | integer | Query execution time in milliseconds |

### Create/Update Response Model

Responses from add/update operations:

```json
{
  "status": "success",
  "code": 201,
  "data": {
    "id": "001ABC123",
    "success": true,
    "created": true,
    "object": "Contact"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data.id` | string | ID of the created/updated record |
| `data.success` | boolean | Whether the operation succeeded |
| `data.created` | boolean | `true` for create, `false` for update |
| `data.object` | string | Object type that was modified |

---

## Error Response Model

### Standard Error Response

All API errors follow a consistent structure:

```json
{
  "status": "error",
  "code": 400,
  "error": {
    "type": "validation_error",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Email address format is invalid"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `error` for error responses |
| `code` | integer | HTTP status code |
| `error.type` | string | Error category identifier |
| `error.message` | string | Human-readable error description |
| `error.details` | array | Optional array of specific error details |
| `error.details[].field` | string | Field that caused the error |
| `error.details[].code` | string | Machine-readable error code |
| `error.details[].message` | string | Field-specific error message |

### Error Types

| Error Type | HTTP Code | Description |
|------------|-----------|-------------|
| `validation_error` | 400 | Request validation failed |
| `authentication_error` | 401 | Invalid or missing authentication |
| `authorization_error` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `method_not_allowed` | 405 | HTTP method not supported |
| `conflict` | 409 | Resource conflict (e.g., duplicate) |
| `rate_limit_exceeded` | 429 | Too many requests |
| `platform_error` | 502 | External platform error |
| `service_unavailable` | 503 | Service temporarily unavailable |
| `internal_error` | 500 | Internal server error |

---

## 404 Error Handler

### GET /e404

Default route handler for 404 errors - returns unknown API call error.

**Handler:** `e404 (default controller)`

#### Response Example

```json
{
  "status": "error",
  "code": 404,
  "error": {
    "type": "not_found",
    "message": "Unknown API call",
    "details": {
      "requested_path": "/invalid/endpoint",
      "method": "GET"
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

### GET /e404/index

Explicit 404 error handler endpoint.

**Handler:** `E404_Controller::index`

#### Request Example

```bash
curl -X GET "https://api.example.com/e404/index" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "error",
  "code": 404,
  "error": {
    "type": "not_found",
    "message": "The requested API endpoint does not exist",
    "details": {
      "suggestion": "Please check the API documentation for available endpoints"
    }
  }
}
```

---

## Platform-Specific Response Models

### Salesforce Response Model

Salesforce queries return data in SFDC format:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "totalSize": 1,
    "done": true,
    "records": [
      {
        "attributes": {
          "type": "Contact",
          "url": "/services/data/v52.0/sobjects/Contact/003ABC123"
        },
        "Id": "003ABC123",
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "john.doe@example.com"
      }
    ]
  }
}
```

### Microsoft Dynamics Response Model

Dynamics CRM responses include OData metadata:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "@odata.context": "https://org.crm.dynamics.com/api/data/v9.2/$metadata#contacts",
    "value": [
      {
        "@odata.etag": "W/\"12345678\"",
        "contactid": "abc-123-def",
        "firstname": "John",
        "lastname": "Doe",
        "emailaddress1": "john.doe@example.com"
      }
    ],
    "@odata.nextLink": "https://org.crm.dynamics.com/api/data/v9.2/contacts?$skiptoken=..."
  }
}
```

### Zendesk Response Model

Zendesk responses follow their API structure:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "tickets": [
      {
        "id": 12345,
        "subject": "Support Request",
        "description": "Need help with...",
        "status": "open",
        "priority": "normal",
        "requester_id": 67890,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "count": 1,
    "next_page": null,
    "previous_page": null
  }
}
```

### Oracle Fusion Response Model

Oracle Fusion CRM responses:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "items": [
      {
        "PartyId": 100000001,
        "PartyName": "Acme Corporation",
        "PartyType": "ORGANIZATION",
        "CreationDate": "2024-01-10T08:00:00+00:00",
        "LastUpdateDate": "2024-01-15T10:30:00+00:00"
      }
    ],
    "totalResults": 1,
    "offset": 0,
    "limit": 25,
    "hasMore": false
  }
}
```

### GoodData Response Model

GoodData analytics responses:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "dataset": {
      "meta": {
        "title": "Sales Data",
        "identifier": "dataset.sales",
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-15T00:00:00Z"
      },
      "content": {
        "attributes": [...],
        "facts": [...],
        "mode": "SLI"
      }
    }
  }
}
```

---

## Metadata Response Models

### Object List Response

Response structure for metadata object list queries:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "objects": [
      {
        "name": "Contact",
        "label": "Contacts",
        "plural_label": "Contacts",
        "key_prefix": "003",
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deletable": true
      },
      {
        "name": "Account",
        "label": "Account",
        "plural_label": "Accounts",
        "key_prefix": "001",
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deletable": true
      }
    ]
  }
}
```

### Field List Response

Response structure for field metadata queries:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "object": "Contact",
    "fields": [
      {
        "name": "Id",
        "label": "Contact ID",
        "type": "id",
        "length": 18,
        "required": false,
        "updateable": false,
        "createable": false
      },
      {
        "name": "FirstName",
        "label": "First Name",
        "type": "string",
        "length": 40,
        "required": false,
        "updateable": true,
        "createable": true
      },
      {
        "name": "Email",
        "label": "Email",
        "type": "email",
        "length": 80,
        "required": true,
        "updateable": true,
        "createable": true
      }
    ]
  }
}
```

---

## Authentication Response Models

### Successful Authentication

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2024-01-15T12:30:00Z",
    "refresh_token": "rt_abc123def456",
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "permissions": ["read", "write"]
    }
  }
}
```

### Authentication Error

```json
{
  "status": "error",
  "code": 401,
  "error": {
    "type": "authentication_error",
    "message": "Invalid credentials",
    "details": {
      "reason": "TOKEN_EXPIRED",
      "expired_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

---

## Feed Response Models

### Feed Context Response

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "token": "feed_abc123",
    "feed_name": "My Email Feed",
    "item_count": 25,
    "unread_count": 5,
    "last_refresh": "2024-01-15T10:30:00Z"
  }
}
```

### Message Info Response

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "feed_name": "My Email Feed",
    "time_received": "2024-01-15T09:45:00Z",
    "sender": "sender@example.com",
    "subject": "Important Update",
    "has_attachments": true,
    "attachments": [
      {
        "filename": "document.pdf",
        "size": 102400,
        "content_type": "application/pdf"
      }
    ],
    "is_read": false
  }
}
```

---

## Statistics Response Model

### GET /stats/{entity}

Get cached statistical data for the service gateway.

**Handler:** `Stats_Controller::__call`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | Yes | Statistics entity to retrieve |

#### Request Example

```bash
curl -X GET "https://api.example.com/stats/api_calls" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer your-token"
```

#### Response Example

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "entity": "api_calls",
    "period": "24h",
    "statistics": {
      "total_requests": 15420,
      "successful_requests": 14985,
      "failed_requests": 435,
      "average_response_time_ms": 187,
      "requests_by_platform": {
        "salesforce": 8500,
        "msdynamics": 3200,
        "zendesk": 2100,
        "custom": 1620
      },
      "requests_by_endpoint": {
        "query": 10500,
        "add": 2800,
        "update": 1750,
        "delete": 370
      }
    },
    "cached_at": "2024-01-15T10:25:00Z",
    "cache_ttl_seconds": 300
  }
}
```

---

## HTTP Status Codes

### Success Codes

| Code | Status | Usage |
|------|--------|-------|
| 200 | OK | Successful GET, PUT, DELETE operations |
| 201 | Created | Successful POST (create) operations |
| 202 | Accepted | Request accepted for async processing |
| 204 | No Content | Successful operation with no response body |

### Client Error Codes

| Code | Status | Usage |
|------|--------|-------|
| 400 | Bad Request | Invalid request syntax or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource or endpoint not found |
| 405 | Method Not Allowed | HTTP method not supported |
| 409 | Conflict | Resource conflict (duplicate, etc.) |
| 422 | Unprocessable Entity | Valid syntax but semantic errors |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Status | Usage |
|------|--------|-------|
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External platform error |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | External platform timeout |

---

## Error Code Reference

### Validation Error Codes

| Code | Description |
|------|-------------|
| `REQUIRED_FIELD` | A required field is missing |
| `INVALID_FORMAT` | Field value format is invalid |
| `INVALID_TYPE` | Field value type is incorrect |
| `VALUE_TOO_LONG` | String exceeds maximum length |
| `VALUE_TOO_SHORT` | String below minimum length |
| `VALUE_OUT_OF_RANGE` | Numeric value outside allowed range |
| `INVALID_ENUM_VALUE` | Value not in allowed list |
| `INVALID_DATE_FORMAT` | Date string format is invalid |

### Authentication Error Codes

| Code | Description |
|------|-------------|
| `MISSING_TOKEN` | Authorization token not provided |
| `INVALID_TOKEN` | Token format or signature invalid |
| `TOKEN_EXPIRED` | Token has expired |
| `TOKEN_REVOKED` | Token has been revoked |
| `INVALID_CREDENTIALS` | Username/password incorrect |
| `ACCOUNT_LOCKED` | Account is locked |
| `SESSION_EXPIRED` | Session has expired |

### Platform Error Codes

| Code | Description |
|------|-------------|
| `PLATFORM_UNAVAILABLE` | External platform is unavailable |
| `PLATFORM_TIMEOUT` | External platform request timed out |
| `PLATFORM_AUTH_FAILED` | Platform authentication failed |
| `PLATFORM_RATE_LIMIT` | Platform rate limit exceeded |
| `PLATFORM_INVALID_RESPONSE` | Platform returned invalid response |
| `QUERY_SYNTAX_ERROR` | Query syntax is invalid |
| `OBJECT_NOT_FOUND` | Requested object doesn't exist |
| `FIELD_NOT_FOUND` | Referenced field doesn't exist |

---

## Related Documentation

- [Generic API Endpoints](../api/generic-endpoints.md) - Core API query and data operations
- [Salesforce Endpoints](../api/salesforce-endpoints.md) - Salesforce-specific responses
- [Microsoft Dynamics Endpoints](../api/msdynamics-endpoints.md) - Dynamics CRM responses
- [Zendesk Endpoints](../api/zendesk-endpoints.md) - Zendesk-specific responses
- [Authentication Guide](../guides/authentication.md) - Authentication and token handling