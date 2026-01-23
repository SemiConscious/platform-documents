# WebSocket API

This document covers the WebSocket connection handling, message schemas, and real-time communication patterns for the cai-service.

## Overview

The cai-service provides a WebSocket interface for real-time AI completion requests. This enables bidirectional communication for streaming AI responses and handling interactive conversations.

## Connection Endpoint

### WebSocket Connection

```
WEBSOCKET /
```

Establishes a WebSocket connection for AI completion requests. Authentication is performed during the connection handshake via query parameters.

#### Connection Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `authorization` | Query | string | Yes | Bearer token or API key for authentication |
| `orgId` | Query | string | Yes | Organization identifier for multi-tenant access |

#### Connection Example

```javascript
// JavaScript WebSocket connection example
const ws = new WebSocket('wss://api.example.com/?authorization=Bearer%20YOUR_TOKEN&orgId=org_123456');

ws.onopen = () => {
  console.log('Connected to cai-service WebSocket');
};

ws.onclose = (event) => {
  console.log(`Connection closed: ${event.code} - ${event.reason}`);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

```bash
# Using wscat for testing
wscat -c "wss://api.example.com/?authorization=Bearer%20YOUR_TOKEN&orgId=org_123456"
```

#### Connection Response

On successful connection, the WebSocket will be established and ready to receive messages. No explicit connection acknowledgment message is sent.

#### Connection Error Codes

| Code | Description |
|------|-------------|
| `1000` | Normal closure |
| `1008` | Policy violation - authentication failed |
| `1011` | Unexpected server error |
| `4001` | Invalid or missing authorization token |
| `4002` | Invalid or missing organization ID |
| `4003` | Organization not found or access denied |

---

## Message Handling

### WebSocket Messages

```
WEBSOCKET_MESSAGE /
```

Handles incoming WebSocket messages for AI completion requests. Messages must be sent as JSON-encoded strings.

#### Supported Request Types

| Request Type | Description |
|--------------|-------------|
| `COMPLETION` | Request an AI completion/response |
| `INTERRUPTED` | Signal that the user has interrupted the current generation |
| `AWAIT_MORE` | Indicate the client is ready to receive more streamed content |
| `SENTENCE_COMPLETED` | Acknowledge that a sentence/chunk has been processed |

---

## Message Schemas

### COMPLETION Request

Initiates an AI completion request.

#### Request Format

```json
{
  "type": "COMPLETION",
  "requestId": "req_abc123",
  "payload": {
    "prompt": "Explain quantum computing in simple terms",
    "model": "gpt-4",
    "options": {
      "temperature": 0.7,
      "maxTokens": 1024,
      "stream": true
    },
    "conversationId": "conv_xyz789",
    "context": []
  }
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `"COMPLETION"` |
| `requestId` | string | Yes | Unique identifier for tracking the request |
| `payload.prompt` | string | Yes | The user prompt or message |
| `payload.model` | string | No | AI model to use (defaults to organization setting) |
| `payload.options.temperature` | number | No | Sampling temperature (0-2, default: 0.7) |
| `payload.options.maxTokens` | integer | No | Maximum tokens to generate |
| `payload.options.stream` | boolean | No | Enable streaming responses (default: true) |
| `payload.conversationId` | string | No | ID to maintain conversation context |
| `payload.context` | array | No | Previous messages for context |

#### Response Messages

The server responds with multiple message types during completion:

**Stream Start:**
```json
{
  "type": "STREAM_START",
  "requestId": "req_abc123",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Content Chunk (streamed):**
```json
{
  "type": "CONTENT_CHUNK",
  "requestId": "req_abc123",
  "payload": {
    "content": "Quantum computing is",
    "index": 0
  }
}
```

**Sentence Boundary:**
```json
{
  "type": "SENTENCE_BOUNDARY",
  "requestId": "req_abc123",
  "payload": {
    "sentence": "Quantum computing is a type of computation that uses quantum mechanics.",
    "sentenceIndex": 0
  }
}
```

**Stream Complete:**
```json
{
  "type": "STREAM_COMPLETE",
  "requestId": "req_abc123",
  "payload": {
    "fullContent": "Quantum computing is a type of computation...",
    "usage": {
      "promptTokens": 12,
      "completionTokens": 156,
      "totalTokens": 168
    },
    "model": "gpt-4",
    "finishReason": "stop"
  }
}
```

---

### INTERRUPTED Request

Signals that the user has interrupted the current AI generation.

#### Request Format

```json
{
  "type": "INTERRUPTED",
  "requestId": "req_abc123"
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `"INTERRUPTED"` |
| `requestId` | string | Yes | ID of the request to interrupt |

#### Response

```json
{
  "type": "INTERRUPTED_ACK",
  "requestId": "req_abc123",
  "payload": {
    "partialContent": "Quantum computing is a type of",
    "tokensGenerated": 45
  }
}
```

---

### AWAIT_MORE Request

Indicates the client is ready to receive more streamed content (for flow control).

#### Request Format

```json
{
  "type": "AWAIT_MORE",
  "requestId": "req_abc123",
  "payload": {
    "lastReceivedIndex": 5
  }
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `"AWAIT_MORE"` |
| `requestId` | string | Yes | ID of the active request |
| `payload.lastReceivedIndex` | integer | No | Index of the last received chunk |

#### Response

Server continues streaming content chunks.

---

### SENTENCE_COMPLETED Request

Acknowledges that a sentence or chunk has been fully processed by the client.

#### Request Format

```json
{
  "type": "SENTENCE_COMPLETED",
  "requestId": "req_abc123",
  "payload": {
    "sentenceIndex": 0
  }
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `"SENTENCE_COMPLETED"` |
| `requestId` | string | Yes | ID of the active request |
| `payload.sentenceIndex` | integer | Yes | Index of the completed sentence |

#### Response

No explicit response; server continues processing.

---

## Error Messages

When an error occurs, the server sends an error message:

```json
{
  "type": "ERROR",
  "requestId": "req_abc123",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid request type specified",
    "details": {}
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Malformed request or invalid request type |
| `INVALID_PAYLOAD` | Missing or invalid payload fields |
| `MODEL_NOT_FOUND` | Specified model is not available |
| `RATE_LIMITED` | Too many requests, try again later |
| `CONTEXT_TOO_LONG` | Context exceeds maximum token limit |
| `GENERATION_FAILED` | AI model failed to generate response |
| `INTERNAL_ERROR` | Unexpected server error |

---

## Complete Usage Example

```javascript
const ws = new WebSocket('wss://api.example.com/?authorization=Bearer%20YOUR_TOKEN&orgId=org_123456');

ws.onopen = () => {
  // Send a completion request
  ws.send(JSON.stringify({
    type: 'COMPLETION',
    requestId: 'req_' + Date.now(),
    payload: {
      prompt: 'Write a haiku about programming',
      model: 'gpt-4',
      options: {
        temperature: 0.8,
        stream: true
      }
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'STREAM_START':
      console.log('Generation started');
      break;
    case 'CONTENT_CHUNK':
      process.stdout.write(message.payload.content);
      break;
    case 'SENTENCE_BOUNDARY':
      // Acknowledge sentence completion
      ws.send(JSON.stringify({
        type: 'SENTENCE_COMPLETED',
        requestId: message.requestId,
        payload: { sentenceIndex: message.payload.sentenceIndex }
      }));
      break;
    case 'STREAM_COMPLETE':
      console.log('\n\nGeneration complete');
      console.log('Tokens used:', message.payload.usage.totalTokens);
      break;
    case 'ERROR':
      console.error('Error:', message.error.message);
      break;
  }
};
```

---

## Related Documentation

- [REST Endpoints](rest-endpoints.md) - HTTP-based API endpoints
- [API Overview](README.md) - General API information and authentication