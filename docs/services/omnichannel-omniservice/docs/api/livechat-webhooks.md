# LiveChat Webhook Endpoints

This document covers the LiveChat integration webhook endpoints for receiving messages, handling delivery status updates, fetching conversation history, and managing media uploads.

## Overview

LiveChat webhooks enable real-time communication with LiveChat services. The endpoints support:

- Receiving incoming messages from LiveChat
- Delivery status notifications
- Fetching conversation message history
- Media file uploads
- CORS support for browser-based integrations

## Endpoints

### POST /webhooks/livechat/{identifier}

Receives incoming live chat messages from the LiveChat service webhook.

#### Description

This endpoint handles webhook notifications from LiveChat. The `identifier` parameter is a base64-encoded string containing organization and user context information in the format `orgId:userId:livechat-id`.

#### Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `identifier` | path | string | Yes | Base64-encoded string containing `orgId:userId:livechat-id` |

#### Request Example

```bash
curl -X POST "https://api.example.com/webhooks/livechat/b3JnMTIzOnVzZXI0NTY6bGMtNzg5" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "incoming_chat",
    "chat_id": "chat_abc123",
    "message": {
      "id": "msg_001",
      "text": "Hello, I need help with my order",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "visitor": {
      "id": "visitor_xyz",
      "name": "John Doe",
      "email": "john@example.com"
    }
  }'
```

#### Response Example

**Success (200 OK)**

```json
{
  "status": "received",
  "messageId": "msg_001"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Invalid identifier format or malformed request body |
| `401` | Unauthorized - invalid webhook credentials |
| `500` | Internal server error during message processing |

---

### POST /livechat/{identifier}

Receives incoming LiveChat messages with support for delivery status, conversation fetching, and media uploads.

#### Description

This is the primary LiveChat endpoint that handles multiple operations based on query parameters:

- **Default**: Receives incoming LiveChat messages
- **Delivery status**: Handles message delivery confirmations
- **Fetch messages**: Retrieves conversation message history
- **Media upload**: Uploads media files to LiveChat conversations

#### Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `identifier` | path | string | Yes | Base64-encoded string containing `orgId:userId:livechat-id` |
| `action` | query | string | No | Action type: `delivery_status`, `fetch_messages`, `upload_media` |
| `chat_id` | query | string | Conditional | Required for `fetch_messages` and `upload_media` actions |
| `limit` | query | integer | No | Number of messages to fetch (default: 50, max: 100) |

#### Request Example - Receive Message

```bash
curl -X POST "https://api.example.com/livechat/b3JnMTIzOnVzZXI0NTY6bGMtNzg5" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "incoming_message",
    "chat_id": "chat_abc123",
    "message": {
      "id": "msg_002",
      "type": "text",
      "text": "Can you check order #12345?",
      "author": {
        "id": "visitor_xyz",
        "type": "visitor"
      },
      "created_at": "2024-01-15T10:32:00Z"
    }
  }'
```

#### Response Example - Receive Message

**Success (200 OK)**

```json
{
  "status": "processed",
  "messageId": "msg_002",
  "queuedAt": "2024-01-15T10:32:00.123Z"
}
```

#### Request Example - Delivery Status

```bash
curl -X POST "https://api.example.com/livechat/b3JnMTIzOnVzZXI0NTY6bGMtNzg5?action=delivery_status" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_outbound_001",
    "chat_id": "chat_abc123",
    "status": "delivered",
    "delivered_at": "2024-01-15T10:33:00Z"
  }'
```

#### Response Example - Delivery Status

**Success (200 OK)**

```json
{
  "status": "acknowledged",
  "messageId": "msg_outbound_001",
  "deliveryStatus": "delivered"
}
```

#### Request Example - Fetch Messages

```bash
curl -X POST "https://api.example.com/livechat/b3JnMTIzOnVzZXI0NTY6bGMtNzg5?action=fetch_messages&chat_id=chat_abc123&limit=20" \
  -H "Content-Type: application/json" \
  -d '{
    "from_timestamp": "2024-01-15T00:00:00Z",
    "to_timestamp": "2024-01-15T12:00:00Z"
  }'
```

#### Response Example - Fetch Messages

**Success (200 OK)**

```json
{
  "chat_id": "chat_abc123",
  "messages": [
    {
      "id": "msg_001",
      "type": "text",
      "text": "Hello, I need help with my order",
      "author": {
        "id": "visitor_xyz",
        "type": "visitor"
      },
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg_002",
      "type": "text",
      "text": "Can you check order #12345?",
      "author": {
        "id": "visitor_xyz",
        "type": "visitor"
      },
      "created_at": "2024-01-15T10:32:00Z"
    }
  ],
  "total": 2,
  "hasMore": false
}
```

#### Request Example - Upload Media

```bash
curl -X POST "https://api.example.com/livechat/b3JnMTIzOnVzZXI0NTY6bGMtNzg5?action=upload_media&chat_id=chat_abc123" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@screenshot.png" \
  -F "filename=screenshot.png" \
  -F "content_type=image/png"
```

#### Response Example - Upload Media

**Success (200 OK)**

```json
{
  "status": "uploaded",
  "media": {
    "id": "media_abc123",
    "url": "https://cdn.livechat.com/media/media_abc123.png",
    "filename": "screenshot.png",
    "content_type": "image/png",
    "size": 245678
  }
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Invalid request - malformed identifier, missing required parameters, or invalid action |
| `401` | Unauthorized - invalid or missing authentication |
| `404` | Chat not found when fetching messages or uploading media |
| `413` | Payload too large - media file exceeds size limit |
| `415` | Unsupported media type for upload |
| `500` | Internal server error |

---

### OPTIONS /livechat/{identifier}

Handles CORS preflight requests for the LiveChat endpoint.

#### Description

This endpoint responds to CORS preflight requests, enabling browser-based LiveChat integrations to communicate with the API.

#### Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `identifier` | path | string | Yes | Base64-encoded string containing `orgId:userId:livechat-id` |

#### Request Example

```bash
curl -X OPTIONS "https://api.example.com/livechat/b3JnMTIzOnVzZXI0NTY6bGMtNzg5" \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

#### Response Example

**Success (200 OK)**

```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

#### Response Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Access-Control-Allow-Origin` | `*` or specific origin | Allowed origins for CORS |
| `Access-Control-Allow-Methods` | `POST, OPTIONS` | Allowed HTTP methods |
| `Access-Control-Allow-Headers` | `Content-Type, Authorization` | Allowed request headers |
| `Access-Control-Max-Age` | `86400` | Cache duration for preflight response (24 hours) |

---

## Identifier Format

The `identifier` parameter used across LiveChat endpoints is a base64-encoded string with the following format:

```
orgId:userId:livechat-id
```

### Components

| Component | Description |
|-----------|-------------|
| `orgId` | Organization identifier in the system |
| `userId` | User identifier associated with the LiveChat |
| `livechat-id` | Unique LiveChat integration identifier |

### Encoding Example

```javascript
// Original values
const orgId = "org123";
const userId = "user456";
const livechatId = "lc-789";

// Create identifier
const identifier = Buffer.from(`${orgId}:${userId}:${livechatId}`).toString('base64');
// Result: "b3JnMTIzOnVzZXI0NTY6bGMtNzg5"
```

### Decoding Example

```javascript
// Decode identifier
const decoded = Buffer.from("b3JnMTIzOnVzZXI0NTY6bGMtNzg5", 'base64').toString('utf-8');
// Result: "org123:user456:lc-789"

const [orgId, userId, livechatId] = decoded.split(':');
```

---

## Message Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  LiveChat   │────▶│  POST /livechat/ │────▶│  SQS Queue  │
│   Service   │     │   {identifier}   │     │  (Inbound)  │
└─────────────┘     └──────────────────┘     └─────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Message Router   │
                    │ (AWS Lambda)     │
                    └──────────────────┘
```

---

## Related Documentation

- [WhatsApp Webhooks](./whatsapp-webhooks.md) - WhatsApp integration endpoints
- [Carrier Webhooks](./carrier-webhooks.md) - Bandwidth, Twilio, MessageBird, and Inteliquent endpoints
- [API Overview](./README.md) - Complete API reference