# API Reference Overview

This document provides a comprehensive index of all API endpoints and WebSocket connections used by the FreedomCTI client application. The CTI client communicates with multiple backend services to provide real-time call management, presence updates, and call logging functionality within Salesforce.

## API Architecture

The FreedomCTI client interacts with two primary backend systems:

| System | Base URL | Purpose |
|--------|----------|---------|
| FreedomCTI Backend | `https://api.freedomcti.com` | Call logs, presence management, WebSocket connections |
| Salesforce REST API | `https://{instance}.salesforce.com` | Call reporting, missed calls, CRM data |

```
┌─────────────────────────────────────────────────────────────────┐
│                    Salesforce Lightning                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  FreedomCTI Client (iframe)               │  │
│  │                                                           │  │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │  │
│  │   │  REST API   │    │  Salesforce │    │  WebSocket  │  │  │
│  │   │   Client    │    │  API Client │    │   Client    │  │  │
│  │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │  │
│  └──────────┼──────────────────┼──────────────────┼─────────┘  │
└─────────────┼──────────────────┼──────────────────┼─────────────┘
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  FreedomCTI     │  │   Salesforce    │  │  FreedomCTI     │
    │  Backend API    │  │   REST API      │  │  WebSocket      │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Authentication

### FreedomCTI Backend API

All requests to the FreedomCTI backend require a Bearer token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

Tokens are obtained through the FreedomCTI authentication flow and are managed by the client application.

### Salesforce REST API

Salesforce API calls use OAuth 2.0 access tokens obtained through the Salesforce Lightning container:

```http
Authorization: Bearer <salesforce_access_token>
```

The CTI client receives Salesforce credentials via the Lightning Container SDK.

### WebSocket Authentication

WebSocket connections authenticate using query parameters during the connection handshake:

```
wss://ws.freedomcti.com/organisation/{orgId}/user/{userId}?token=<access_token>
```

## Endpoint Categories

### Call Logs API

Endpoints for retrieving and managing call history and activity logs.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/organisation/{orgId}/user/{userId}/log/call` | GET | Fetch Chatter/Limited View call logs |

**Use Cases:**
- Display call history in the CTI panel
- Populate activity timelines
- Support limited view mode for restricted users

📄 **Detailed Documentation:** [Call Logs API](call-logs-api.md)

---

### Salesforce API

Direct Salesforce REST API queries for call reporting and missed call data.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/services/data/{version}/query` | GET | Query call reporting records |
| `/services/data/{version}/query` | GET | Query missed call phone events |

**Use Cases:**
- Fetch detailed call reports with full CRM context
- Retrieve missed call notifications
- Synchronize call data with Salesforce records

📄 **Detailed Documentation:** [Salesforce API](salesforce-api.md)

---

### WebSocket Endpoints

Real-time bidirectional connections for presence and event streaming.

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/organisation/{orgId}/user/{userId}` | WebSocket | User presence subscription |
| `/organisation/{orgId}/user-group/{groupId}` | WebSocket | Group presence subscription |

**Use Cases:**
- Real-time agent availability updates
- Live call status notifications
- Team presence monitoring
- Incoming call alerts

📄 **Detailed Documentation:** [WebSocket Endpoints](websocket-endpoints.md)

## Quick Reference Index

| Documentation | Endpoints | Description |
|---------------|-----------|-------------|
| [Call Logs API](call-logs-api.md) | 1 | FreedomCTI backend call log retrieval |
| [Salesforce API](salesforce-api.md) | 2 | Salesforce SOQL queries for call data |
| [WebSocket Endpoints](websocket-endpoints.md) | 2 | Real-time presence and event subscriptions |

## Common Patterns

### Request Headers

All REST API requests should include:

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>
X-Request-ID: <uuid>
```

### Response Format

Successful responses follow a consistent structure:

```json
{
  "success": true,
  "data": { },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "requestId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Pagination

List endpoints support cursor-based pagination:

```http
GET /v1/organisation/{orgId}/user/{userId}/log/call?limit=50&cursor=eyJsYXN0SWQiOjEyMzQ1fQ
```

Response includes pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "hasMore": true,
    "nextCursor": "eyJsYXN0SWQiOjEyMzk5fQ",
    "totalCount": 150
  }
}
```

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| `200` | Success | Process response data |
| `400` | Bad Request | Check request parameters |
| `401` | Unauthorized | Refresh authentication token |
| `403` | Forbidden | User lacks required permissions |
| `404` | Not Found | Resource doesn't exist |
| `429` | Too Many Requests | Implement backoff and retry |
| `500` | Server Error | Retry with exponential backoff |
| `503` | Service Unavailable | Service temporarily down, retry later |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The orgId parameter is required",
    "details": {
      "field": "orgId",
      "reason": "missing"
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "requestId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_PARAMETER` | Request parameter validation failed |
| `AUTHENTICATION_REQUIRED` | Missing or invalid authentication token |
| `PERMISSION_DENIED` | User not authorized for this operation |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `RATE_LIMIT_EXCEEDED` | Too many requests in time window |
| `SERVICE_UNAVAILABLE` | Backend service temporarily unavailable |

## Rate Limiting

### FreedomCTI Backend API

| Endpoint Type | Rate Limit | Window |
|---------------|------------|--------|
| Call Logs | 100 requests | Per minute |
| General API | 1000 requests | Per minute |

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705315860
```

### Salesforce API

Salesforce enforces organization-wide API limits. The CTI client respects these limits and implements automatic throttling.

### WebSocket Connections

| Limit Type | Value |
|------------|-------|
| Connections per user | 3 |
| Messages per second | 10 |
| Connection idle timeout | 5 minutes |

## Environment Configuration

### Production

```
REST API:      https://api.freedomcti.com
WebSocket:     wss://ws.freedomcti.com
Salesforce:    https://{instance}.salesforce.com
```

### Sandbox/Testing

```
REST API:      https://api.sandbox.freedomcti.com
WebSocket:     wss://ws.sandbox.freedomcti.com
Salesforce:    https://{instance}.sandbox.salesforce.com
```

## SDK and Client Libraries

The CTI client uses internal service modules for API communication:

| Module | Purpose |
|--------|---------|
| `CallLogService` | Call log retrieval and caching |
| `SalesforceService` | Salesforce API integration |
| `WebSocketService` | Real-time connection management |
| `AuthService` | Token management and refresh |

## Related Documentation

- [Call Logs API](call-logs-api.md) - Detailed call log endpoint documentation
- [Salesforce API](salesforce-api.md) - Salesforce query endpoint documentation  
- [WebSocket Endpoints](websocket-endpoints.md) - Real-time subscription documentation