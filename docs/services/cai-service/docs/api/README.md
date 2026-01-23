# API Overview

## Introduction

The CAI Service provides a Conversational AI platform that enables real-time AI completion requests across multiple models and services. The API supports both REST and WebSocket protocols, with WebSocket being the primary interface for interactive AI conversations.

## Base URL

```
Production: wss://your-domain.com
Health Check: https://your-domain.com
```

## API Protocols

### REST API

The REST API provides health check and monitoring capabilities for load balancer integration.

| Endpoint | Description |
|----------|-------------|
| `GET /` | ALB health check endpoint |

### WebSocket API

The WebSocket API is the primary interface for AI completion requests, supporting real-time bidirectional communication for streaming AI responses.

| Connection | Description |
|------------|-------------|
| `WEBSOCKET /` | Main connection endpoint for AI conversations |
| `WEBSOCKET_MESSAGE /` | Message handler for completion requests |

## Authentication

All API requests require authentication via query parameters on the WebSocket connection:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `authorization` | string | Yes | Bearer token or API key for authentication |
| `orgId` | string | Yes | Organization identifier for multi-tenant access |

### Connection Example

```javascript
const ws = new WebSocket('wss://your-domain.com/?authorization=Bearer%20YOUR_TOKEN&orgId=YOUR_ORG_ID');
```

## Message Types

The WebSocket API supports the following request types:

| Type | Description |
|------|-------------|
| `COMPLETION` | Request AI completion for a given prompt |
| `INTERRUPTED` | Signal that the user has interrupted the response |
| `AWAIT_MORE` | Indicate readiness to receive additional content |
| `SENTENCE_COMPLETED` | Acknowledge completion of a sentence/segment |

## Common Patterns

### Connection Lifecycle

1. **Connect** - Establish WebSocket connection with authentication
2. **Send Request** - Send completion request with prompt data
3. **Receive Stream** - Receive streaming AI response chunks
4. **Control Flow** - Use control messages (INTERRUPTED, AWAIT_MORE) as needed
5. **Close** - Gracefully close connection when finished

### Error Handling

Errors are returned via WebSocket messages with the following structure:

```json
{
  "type": "ERROR",
  "code": "ERROR_CODE",
  "message": "Human-readable error description"
}
```

| Error Code | Description |
|------------|-------------|
| `AUTH_FAILED` | Invalid or expired authentication credentials |
| `INVALID_ORG` | Organization ID not found or access denied |
| `RATE_LIMITED` | Too many requests, retry after backoff |
| `MODEL_ERROR` | AI model processing error |
| `INVALID_REQUEST` | Malformed request payload |

### Rate Limiting

Rate limits are applied per organization and connection:

- Connections are subject to concurrent session limits
- Message throughput is monitored to prevent abuse
- Exceeding limits results in `RATE_LIMITED` errors with retry guidance

## Detailed Documentation

For complete endpoint specifications, refer to the following documentation:

| Document | Description | Link |
|----------|-------------|------|
| REST Endpoints | Health check and HTTP endpoint details | [rest-endpoints.md](rest-endpoints.md) |
| WebSocket API | Complete WebSocket protocol documentation | [websocket.md](websocket.md) |

## Quick Start

### 1. Establish Connection

```javascript
const ws = new WebSocket('wss://api.example.com/?authorization=Bearer%20token&orgId=org123');

ws.onopen = () => {
  console.log('Connected to CAI Service');
};
```

### 2. Send Completion Request

```javascript
ws.send(JSON.stringify({
  type: 'COMPLETION',
  payload: {
    prompt: 'Hello, how can you help me today?',
    model: 'default'
  }
}));
```

### 3. Handle Responses

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## SDK Support

While direct WebSocket integration is supported, consider using official SDKs for simplified integration:

- TypeScript/JavaScript client libraries
- Connection pooling and automatic reconnection
- Built-in retry logic and error handling

## Support

For API issues or questions, consult the detailed documentation linked above or contact your organization's CAI Service administrator.