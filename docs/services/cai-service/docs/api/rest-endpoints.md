# REST API Endpoints

This document covers the REST API endpoints for cai-service accessed via AWS API Gateway.

> **Note:** For WebSocket-based AI completion functionality, see [WebSocket API Documentation](./websocket.md).

## Overview

The cai-service REST API is minimal by design, with most functionality exposed through WebSocket connections for real-time AI interactions. The primary REST endpoint serves infrastructure health monitoring.

## Base URL

```
https://{api-gateway-id}.execute-api.{region}.amazonaws.com/{stage}
```

## Endpoints

### Health Check

Check the health status of the service. This endpoint is used by AWS Application Load Balancer (ALB) for health monitoring and service availability checks.

```
GET /
```

#### Description

Returns the current health status of the cai-service. This endpoint is designed for infrastructure health checks and does not require authentication.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| *None* | - | - | - | This endpoint accepts no parameters |

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Accept` | No | Response content type (defaults to `application/json`) |

#### Request Example

```bash
curl -X GET "https://api.example.com/" \
  -H "Accept: application/json"
```

#### Response

##### Success Response

**Status Code:** `200 OK`

```json
{
  "status": "healthy"
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service health status. Returns `"healthy"` when the service is operational |

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `503` | Service Unavailable | The service is temporarily unavailable or unhealthy |
| `504` | Gateway Timeout | The health check request timed out |

#### Usage Notes

- **Frequency:** ALB typically polls this endpoint every 30 seconds
- **Timeout:** Health checks should respond within 5 seconds
- **No Authentication:** This endpoint is publicly accessible for infrastructure monitoring
- **Idempotent:** Safe to call repeatedly without side effects

---

## Authentication

The REST API health check endpoint does not require authentication. For authenticated operations and AI completion requests, use the [WebSocket API](./websocket.md) which supports authentication via query parameters:

- `authorization` - Bearer token for authentication
- `orgId` - Organization identifier

## Rate Limiting

| Endpoint | Rate Limit | Burst Limit |
|----------|------------|-------------|
| `GET /` | 100 requests/second | 200 requests |

## Related Documentation

- [API Overview](./README.md) - General API information and getting started
- [WebSocket API](./websocket.md) - Real-time AI completion requests via WebSocket