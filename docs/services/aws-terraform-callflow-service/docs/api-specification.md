# API Specification

This document provides comprehensive documentation of the Callflow Service API endpoints based on the OpenAPI specification defined in the Terraform module.

## Overview

The Callflow Service API provides RESTful endpoints for storing and retrieving call flow events. The API is deployed via AWS API Gateway with Lambda backend functions.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

The actual base URL is determined by your Terraform deployment and can be retrieved from the module outputs.

## Authentication

Authentication is configured based on your API Gateway settings. Common authentication methods include:

- **API Key**: Pass via `x-api-key` header
- **IAM Authentication**: AWS Signature Version 4
- **Cognito User Pools**: JWT token in `Authorization` header

## Endpoints

### Store Call Flow Event

Creates a new call flow event record in the system.

```
POST /callflow/events
```

#### Description

Stores a call flow event containing metadata about a call interaction. This endpoint accepts event data and persists it to the configured data store (DynamoDB).

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `Content-Type` | Header | string | Yes | Must be `application/json` |
| `x-api-key` | Header | string | Conditional | API key if authentication is enabled |
| `callId` | Body | string | Yes | Unique identifier for the call |
| `eventType` | Body | string | Yes | Type of call event (e.g., `initiated`, `answered`, `ended`) |
| `timestamp` | Body | string | Yes | ISO 8601 formatted timestamp of the event |
| `metadata` | Body | object | No | Additional event-specific metadata |

#### Request Example

```bash
curl -X POST "https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/callflow/events" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "callId": "call-12345-abcde",
    "eventType": "initiated",
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
      "callerNumber": "+1234567890",
      "calledNumber": "+0987654321",
      "direction": "inbound"
    }
  }'
```

#### Response Example

**Success (201 Created)**

```json
{
  "statusCode": 201,
  "body": {
    "message": "Event stored successfully",
    "eventId": "evt-67890-fghij",
    "callId": "call-12345-abcde",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | Bad Request | Invalid request body or missing required fields |
| `401` | Unauthorized | Missing or invalid authentication credentials |
| `403` | Forbidden | Valid credentials but insufficient permissions |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side processing error |

---

### Retrieve Call Flow Events

Retrieves call flow events based on specified criteria.

```
GET /callflow/events
```

#### Description

Queries and returns call flow events. Supports filtering by call ID, event type, and time range.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `x-api-key` | Header | string | Conditional | API key if authentication is enabled |
| `callId` | Query | string | No | Filter by specific call ID |
| `eventType` | Query | string | No | Filter by event type |
| `startTime` | Query | string | No | ISO 8601 start time for time range filter |
| `endTime` | Query | string | No | ISO 8601 end time for time range filter |
| `limit` | Query | integer | No | Maximum number of results (default: 100, max: 1000) |
| `nextToken` | Query | string | No | Pagination token from previous response |

#### Request Example

```bash
curl -X GET "https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/callflow/events?callId=call-12345-abcde&limit=50" \
  -H "x-api-key: your-api-key"
```

#### Response Example

**Success (200 OK)**

```json
{
  "statusCode": 200,
  "body": {
    "events": [
      {
        "eventId": "evt-67890-fghij",
        "callId": "call-12345-abcde",
        "eventType": "initiated",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
          "callerNumber": "+1234567890",
          "calledNumber": "+0987654321",
          "direction": "inbound"
        }
      },
      {
        "eventId": "evt-67891-klmno",
        "callId": "call-12345-abcde",
        "eventType": "answered",
        "timestamp": "2024-01-15T10:30:15Z",
        "metadata": {
          "answeredBy": "agent-001"
        }
      }
    ],
    "count": 2,
    "nextToken": null
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | Bad Request | Invalid query parameters |
| `401` | Unauthorized | Missing or invalid authentication credentials |
| `403` | Forbidden | Valid credentials but insufficient permissions |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side processing error |

---

### Get Call Flow Event by ID

Retrieves a specific call flow event by its unique identifier.

```
GET /callflow/events/{eventId}
```

#### Description

Returns detailed information about a single call flow event.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `eventId` | Path | string | Yes | Unique identifier of the event |
| `x-api-key` | Header | string | Conditional | API key if authentication is enabled |

#### Request Example

```bash
curl -X GET "https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/callflow/events/evt-67890-fghij" \
  -H "x-api-key: your-api-key"
```

#### Response Example

**Success (200 OK)**

```json
{
  "statusCode": 200,
  "body": {
    "eventId": "evt-67890-fghij",
    "callId": "call-12345-abcde",
    "eventType": "initiated",
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
      "callerNumber": "+1234567890",
      "calledNumber": "+0987654321",
      "direction": "inbound"
    },
    "createdAt": "2024-01-15T10:30:01Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | Bad Request | Invalid event ID format |
| `401` | Unauthorized | Missing or invalid authentication credentials |
| `403` | Forbidden | Valid credentials but insufficient permissions |
| `404` | Not Found | Event with specified ID does not exist |
| `500` | Internal Server Error | Server-side processing error |

---

## Data Models

### CallFlowEvent

| Field | Type | Description |
|-------|------|-------------|
| `eventId` | string | Unique identifier for the event (auto-generated) |
| `callId` | string | Identifier for the associated call |
| `eventType` | string | Type of call flow event |
| `timestamp` | string | ISO 8601 timestamp when event occurred |
| `metadata` | object | Event-specific additional data |
| `createdAt` | string | ISO 8601 timestamp when record was created |

### Event Types

Common event types supported by the API:

| Event Type | Description |
|------------|-------------|
| `initiated` | Call has been initiated |
| `ringing` | Destination is ringing |
| `answered` | Call has been answered |
| `hold` | Call placed on hold |
| `resumed` | Call resumed from hold |
| `transferred` | Call transferred to another destination |
| `ended` | Call has ended |
| `failed` | Call failed to connect |

## Rate Limiting

The API enforces rate limits to ensure fair usage:

| Limit Type | Default Value |
|------------|---------------|
| Requests per second | 100 |
| Burst limit | 200 |

Rate limit headers in response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312200
```

## Error Response Format

All error responses follow a consistent format:

```json
{
  "statusCode": 400,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": [
      {
        "field": "callId",
        "message": "callId is required"
      }
    ]
  },
  "requestId": "req-abc123"
}
```

## Related Documentation

- [Getting Started](getting-started.md) - Initial setup and deployment
- [Architecture](architecture.md) - System design and components
- [Troubleshooting](troubleshooting.md) - Common issues and solutions