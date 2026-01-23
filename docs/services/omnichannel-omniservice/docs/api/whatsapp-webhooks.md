# WhatsApp Webhook Endpoints

This document provides detailed documentation for WhatsApp-specific webhook endpoints in the Omni Channel Service. These endpoints handle WhatsApp webhook verification, incoming message processing, and WABA ID routing configuration.

## Overview

The WhatsApp webhook endpoints integrate with Meta's WhatsApp Business API to:
- Verify webhook subscriptions during initial setup
- Receive and process incoming messages and status notifications
- Route notifications to different environments based on WABA ID mappings

## Endpoints

### GET /webhooks/whatsapp/receive

Handles WhatsApp webhook verification requests when setting up the webhook in the Meta Admin panel.

**Description**

When configuring a webhook in the Meta Business Admin panel, Meta sends a GET request to verify the endpoint. This endpoint validates the `hub.verify_token` against the expected value and returns the `hub.challenge` to confirm ownership.

**Request Parameters**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `hub.mode` | string | query | Yes | Must be `subscribe` for webhook verification |
| `hub.verify_token` | string | query | Yes | The verification token configured in Meta Admin panel |
| `hub.challenge` | string | query | Yes | Challenge string from Meta that must be returned |

**Request Example**

```bash
curl -X GET "https://api.example.com/webhooks/whatsapp/receive?hub.mode=subscribe&hub.verify_token=your_verify_token&hub.challenge=1234567890"
```

**Response Example**

Success (200 OK):
```
1234567890
```

The response body contains only the challenge string (plain text).

**Error Codes**

| Status Code | Description |
|-------------|-------------|
| 200 | Verification successful, returns challenge |
| 403 | Verification failed - invalid verify token |

---

### POST /webhooks/whatsapp/receive

Receives incoming WhatsApp notifications and messages from Meta's webhook system.

**Description**

This endpoint processes incoming WhatsApp webhook notifications including:
- Inbound messages (text, media, location, contacts, etc.)
- Message delivery status updates (sent, delivered, read, failed)
- Template message status callbacks

The endpoint validates the request signature, processes the payload, and routes messages to appropriate SQS queues for further processing. It can also re-route notifications to different environments based on WABA ID mapping configuration.

**Request Parameters**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `X-Hub-Signature-256` | string | header | Yes | HMAC SHA256 signature of the request body for validation |
| `Content-Type` | string | header | Yes | Must be `application/json` |
| Body | object | body | Yes | WhatsApp webhook notification payload |

**Request Body Schema**

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WABA_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "contacts": [
              {
                "profile": {
                  "name": "John Doe"
                },
                "wa_id": "15559876543"
              }
            ],
            "messages": [
              {
                "from": "15559876543",
                "id": "wamid.ABC123...",
                "timestamp": "1677721200",
                "type": "text",
                "text": {
                  "body": "Hello, I need help!"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Request Example**

```bash
curl -X POST "https://api.example.com/webhooks/whatsapp/receive" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=abc123def456..." \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [
      {
        "id": "123456789012345",
        "changes": [
          {
            "value": {
              "messaging_product": "whatsapp",
              "metadata": {
                "display_phone_number": "15551234567",
                "phone_number_id": "987654321098765"
              },
              "contacts": [
                {
                  "profile": {
                    "name": "John Doe"
                  },
                  "wa_id": "15559876543"
                }
              ],
              "messages": [
                {
                  "from": "15559876543",
                  "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBI2QjM...",
                  "timestamp": "1677721200",
                  "type": "text",
                  "text": {
                    "body": "Hello, I need help with my order"
                  }
                }
              ]
            },
            "field": "messages"
          }
        ]
      }
    ]
  }'
```

**Request Example - Status Update**

```bash
curl -X POST "https://api.example.com/webhooks/whatsapp/receive" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=abc123def456..." \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [
      {
        "id": "123456789012345",
        "changes": [
          {
            "value": {
              "messaging_product": "whatsapp",
              "metadata": {
                "display_phone_number": "15551234567",
                "phone_number_id": "987654321098765"
              },
              "statuses": [
                {
                  "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBI2QjM...",
                  "status": "delivered",
                  "timestamp": "1677721300",
                  "recipient_id": "15559876543"
                }
              ]
            },
            "field": "messages"
          }
        ]
      }
    ]
  }'
```

**Response Example**

Success (200 OK):
```json
{
  "status": "ok"
}
```

**Error Codes**

| Status Code | Description |
|-------------|-------------|
| 200 | Notification received and processed successfully |
| 401 | Invalid or missing X-Hub-Signature-256 header |
| 400 | Invalid request body or malformed JSON |
| 500 | Internal server error during processing |

---

### OPTIONS /webhooks/whatsapp/receive

Handles CORS preflight requests for the WhatsApp webhook endpoint.

**Description**

Returns appropriate CORS headers for cross-origin requests to the WhatsApp receive endpoint.

**Request Example**

```bash
curl -X OPTIONS "https://api.example.com/webhooks/whatsapp/receive" \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST"
```

**Response Example**

Success (200 OK):
```
(Empty body with CORS headers)
```

**Response Headers**

| Header | Value |
|--------|-------|
| `Access-Control-Allow-Origin` | `*` |
| `Access-Control-Allow-Methods` | `GET, POST, OPTIONS` |
| `Access-Control-Allow-Headers` | `Content-Type, X-Hub-Signature-256` |

---

### POST /webhooks/whatsapp/mapping

Creates or updates WhatsApp WABA ID to URL mapping for routing notifications to specific environments.

**Description**

This endpoint allows configuration of WABA ID routing rules. When a WhatsApp notification is received, the system can re-route it to a different URL based on the WABA ID. This is useful for:
- Routing different WhatsApp Business Accounts to different environments (dev, staging, production)
- Multi-tenant configurations where different organizations use different backends
- Testing webhooks in development environments

**Request Parameters**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `Content-Type` | string | header | Yes | Must be `application/json` |
| `wabaId` | string | body | Yes | The WhatsApp Business Account ID to map |
| `targetUrl` | string | body | Yes | The destination URL to route notifications for this WABA ID |
| `enabled` | boolean | body | No | Whether the mapping is active (default: `true`) |

**Request Body Schema**

```json
{
  "wabaId": "string",
  "targetUrl": "string",
  "enabled": true
}
```

**Request Example**

```bash
curl -X POST "https://api.example.com/webhooks/whatsapp/mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "wabaId": "123456789012345",
    "targetUrl": "https://dev.example.com/webhooks/whatsapp/receive",
    "enabled": true
  }'
```

**Response Example**

Success (200 OK):
```json
{
  "success": true,
  "mapping": {
    "wabaId": "123456789012345",
    "targetUrl": "https://dev.example.com/webhooks/whatsapp/receive",
    "enabled": true,
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T10:30:00.000Z"
  }
}
```

**Error Codes**

| Status Code | Description |
|-------------|-------------|
| 200 | Mapping created or updated successfully |
| 400 | Invalid request body - missing required fields or invalid URL format |
| 401 | Unauthorized - invalid or missing authentication |
| 500 | Internal server error |

---

### OPTIONS /webhooks/whatsapp/mapping

Handles CORS preflight requests for the WhatsApp mapping endpoint.

**Description**

Returns appropriate CORS headers for cross-origin requests to the WhatsApp mapping endpoint.

**Request Example**

```bash
curl -X OPTIONS "https://api.example.com/webhooks/whatsapp/mapping" \
  -H "Origin: https://admin.example.com" \
  -H "Access-Control-Request-Method: POST"
```

**Response Example**

Success (200 OK):
```
(Empty body with CORS headers)
```

**Response Headers**

| Header | Value |
|--------|-------|
| `Access-Control-Allow-Origin` | `*` |
| `Access-Control-Allow-Methods` | `POST, OPTIONS` |
| `Access-Control-Allow-Headers` | `Content-Type, Authorization` |

---

## Message Types

The WhatsApp receive endpoint supports various message types in the webhook payload:

| Type | Description |
|------|-------------|
| `text` | Plain text message |
| `image` | Image attachment |
| `video` | Video attachment |
| `audio` | Audio/voice message |
| `document` | Document file attachment |
| `location` | Shared location |
| `contacts` | Shared contact cards |
| `sticker` | Sticker message |
| `button` | Button response |
| `interactive` | Interactive message response (list, button) |
| `reaction` | Emoji reaction to a message |

## Status Types

Delivery status notifications include the following status values:

| Status | Description |
|--------|-------------|
| `sent` | Message sent to WhatsApp servers |
| `delivered` | Message delivered to recipient's device |
| `read` | Message read by recipient |
| `failed` | Message delivery failed |

## Security Considerations

1. **Signature Validation**: All POST requests to `/webhooks/whatsapp/receive` must include a valid `X-Hub-Signature-256` header. The signature is computed as `sha256=HMAC-SHA256(app_secret, request_body)`.

2. **Token Verification**: The GET verification endpoint validates the `hub.verify_token` against the configured secret.

3. **HTTPS Required**: All WhatsApp webhook endpoints must be served over HTTPS with a valid SSL certificate.

## Related Documentation

- [Carrier Webhooks](./carrier-webhooks.md) - Documentation for other carrier webhook endpoints
- [LiveChat Webhooks](./livechat-webhooks.md) - Documentation for LiveChat integration endpoints
- [API Overview](./README.md) - General API documentation and overview