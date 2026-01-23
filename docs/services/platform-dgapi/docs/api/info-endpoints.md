# Info Endpoints

Documentation for system information and health check endpoints in the Disposition Gateway API.

## Overview

The Info endpoints provide system status, health check functionality, and entity-specific information retrieval. These endpoints are essential for monitoring API availability, debugging, and integration verification.

## Endpoints

### GET /info

Returns API status and health information for the Disposition Gateway service.

#### Description

This endpoint serves as the default health check route, providing information about the API's current status, version, and operational state. It's commonly used by load balancers, monitoring systems, and integration tests to verify the service is running.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| None | - | - | - | No parameters required |

#### Request Example

```bash
curl -X GET \
  "https://api.example.com/info" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

**Success Response (200 OK)**

```json
{
  "status": "ok",
  "service": "platform-dgapi",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": 86400,
  "environment": "production",
  "components": {
    "database": "connected",
    "queue": "connected",
    "cache": "connected"
  }
}
```

**Minimal Health Response (200 OK)**

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 401 | Unauthorized | Missing or invalid authentication token |
| 500 | Internal Server Error | Service is experiencing issues |
| 503 | Service Unavailable | Service is temporarily unavailable |

---

### GET /info/:entity

Retrieve information for a specific entity or subsystem.

#### Description

This endpoint provides detailed information about a specific entity, subsystem, or component of the Disposition Gateway API. It can be used to check the status of individual services, retrieve configuration details, or query specific system information.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | The entity identifier or subsystem name to query (e.g., `version`, `config`, `health`, `database`, `queue`) |

#### Request Example

```bash
# Get version information
curl -X GET \
  "https://api.example.com/info/version" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

```bash
# Get database status
curl -X GET \
  "https://api.example.com/info/database" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

```bash
# Get queue status
curl -X GET \
  "https://api.example.com/info/queue" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Examples

**Version Information (200 OK)**

```json
{
  "status": "ok",
  "entity": "version",
  "data": {
    "api_version": "1.0.0",
    "build": "2024.01.15.001",
    "codeigniter_version": "3.1.13",
    "php_version": "8.1.0",
    "release_date": "2024-01-15"
  }
}
```

**Database Status (200 OK)**

```json
{
  "status": "ok",
  "entity": "database",
  "data": {
    "connection": "active",
    "host": "db.example.com",
    "database": "dgapi_production",
    "latency_ms": 2,
    "pool_size": 10,
    "active_connections": 3
  }
}
```

**Queue Status (200 OK)**

```json
{
  "status": "ok",
  "entity": "queue",
  "data": {
    "connection": "active",
    "provider": "rabbitmq",
    "pending_tasks": 15,
    "processing_tasks": 3,
    "failed_tasks": 0,
    "queues": {
      "sms": 5,
      "email": 8,
      "voicemail": 2,
      "cdr": 0
    }
  }
}
```

**Health Check (200 OK)**

```json
{
  "status": "ok",
  "entity": "health",
  "data": {
    "overall": "healthy",
    "checks": {
      "database": {
        "status": "healthy",
        "latency_ms": 2
      },
      "queue": {
        "status": "healthy",
        "latency_ms": 5
      },
      "cache": {
        "status": "healthy",
        "latency_ms": 1
      },
      "external_services": {
        "status": "healthy",
        "sgapi": "reachable",
        "smtp": "reachable"
      }
    },
    "last_check": "2024-01-15T10:30:00Z"
  }
}
```

**Configuration Information (200 OK)**

```json
{
  "status": "ok",
  "entity": "config",
  "data": {
    "environment": "production",
    "debug_mode": false,
    "log_level": "info",
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 100
    },
    "features": {
      "sms_enabled": true,
      "email_enabled": true,
      "voicemail_enabled": true,
      "cdr_processing_enabled": true
    }
  }
}
```

#### Error Codes

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 400 | Bad Request | Invalid entity identifier format |
| 401 | Unauthorized | Missing or invalid authentication token |
| 404 | Not Found | Specified entity does not exist |
| 500 | Internal Server Error | Failed to retrieve entity information |
| 503 | Service Unavailable | The requested subsystem is unavailable |

#### Error Response Example

```json
{
  "status": "error",
  "error": {
    "code": 404,
    "message": "Entity not found",
    "entity": "unknown_entity",
    "available_entities": [
      "version",
      "config",
      "health",
      "database",
      "queue"
    ]
  }
}
```

---

## Common Use Cases

### Health Check for Load Balancers

```bash
# Simple health check endpoint for load balancer configuration
curl -X GET "https://api.example.com/info" \
  -H "Accept: application/json" \
  --fail --silent --show-error
```

### Monitoring Integration

```bash
# Comprehensive health check for monitoring systems
curl -X GET "https://api.example.com/info/health" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" | jq '.data.overall'
```

### Pre-deployment Verification

```bash
# Verify version after deployment
curl -X GET "https://api.example.com/info/version" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

---

## Related Documentation

- [Task Endpoints](task-endpoints.md) - Task status and management
- [Messaging Endpoints](messaging-endpoints.md) - SMS and email operations
- [CDR Endpoints](cdr-endpoints.md) - Call detail record processing
- [API Overview](README.md) - Complete API reference