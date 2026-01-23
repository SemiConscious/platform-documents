# Carrier Webhook Endpoints

This document covers webhook endpoints for carrier integrations including Bandwidth, Twilio, MessageBird, and Inteliquent. These endpoints receive inbound messages and delivery status notifications from their respective carrier platforms.

## Overview

The omnichannel service integrates with multiple SMS/messaging carriers through dedicated webhook endpoints. Each carrier sends messages and delivery receipts to these endpoints, which are then validated, processed, and routed to internal SQS queues for further handling.

| Carrier | Endpoint | Primary Use |
|---------|----------|-------------|
| Bandwidth | `/bandwidth/{destination}` | SMS/MMS messages and delivery status |
| Twilio | `/twilio` | SMS messages and delivery status |
| MessageBird | `/messagebird` | SMS messages and delivery status |
| Inteliquent | `/webhooks/inteliquent` | SMS/MMS messages and delivery receipts |

---

## Bandwidth Endpoints

### POST /bandwidth/{destination}

Receives incoming messages and delivery status notifications from the Bandwidth carrier. Handles SMS message fragments, delivery status updates, and routes messages to the inbound queue.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `destination` | string | Yes | The destination phone number or identifier for routing |

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Content-Type` | string | Yes | Must be `application/json` |
| `X-Bandwidth-Signature` | string | No | Bandwidth signature for request validation |

#### Request Body

Bandwidth sends different payload structures for messages vs. delivery status callbacks.

**Inbound Message Example:**

```json
[
  {
    "type": "message-received",
    "time": "2024-01-15T10:30:00.000Z",
    "description": "Incoming message received",
    "to": "+15551234567",
    "message": {
      "id": "msg-abc123def456",
      "owner": "+15559876543",
      "applicationId": "app-12345",
      "time": "2024-01-15T10:30:00.000Z",
      "segmentCount": 1,
      "direction": "in",
      "to": ["+15551234567"],
      "from": "+15559876543",
      "text": "Hello, I need help with my order",
      "media": []
    }
  }
]
```

**Delivery Status Example:**

```json
[
  {
    "type": "message-delivered",
    "time": "2024-01-15T10:30:05.000Z",
    "description": "Message delivered",
    "to": "+15559876543",
    "message": {
      "id": "msg-abc123def456",
      "owner": "+15551234567",
      "applicationId": "app-12345",
      "direction": "out",
      "to": ["+15559876543"],
      "from": "+15551234567",
      "text": "Your order has been shipped!",
      "segmentCount": 1
    }
  }
]
```

#### Request Example

```bash
curl -X POST "https://api.example.com/bandwidth/15551234567" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "type": "message-received",
      "time": "2024-01-15T10:30:00.000Z",
      "description": "Incoming message received",
      "to": "+15551234567",
      "message": {
        "id": "msg-abc123def456",
        "owner": "+15559876543",
        "applicationId": "app-12345",
        "time": "2024-01-15T10:30:00.000Z",
        "segmentCount": 1,
        "direction": "in",
        "to": ["+15551234567"],
        "from": "+15559876543",
        "text": "Hello, I need help with my order",
        "media": []
      }
    }
  ]'
```

#### Response

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Message received and queued for processing"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Message successfully received and queued |
| `400` | Invalid request body or missing required fields |
| `401` | Invalid or missing authentication |
| `500` | Internal server error during processing |

---

### OPTIONS /bandwidth/{destination}

Handles CORS preflight requests for the Bandwidth endpoint.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `destination` | string | Yes | The destination phone number or identifier |

#### Request Example

```bash
curl -X OPTIONS "https://api.example.com/bandwidth/15551234567" \
  -H "Origin: https://bandwidth.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

#### Response

**Success Response (200 OK):**

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-Bandwidth-Signature
```

---

## Twilio Endpoint

### POST /twilio

Receives incoming messages and delivery status notifications from the Twilio carrier. Validates the Twilio signature and routes messages to the inbound queue.

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Content-Type` | string | Yes | Must be `application/x-www-form-urlencoded` |
| `X-Twilio-Signature` | string | Yes | Twilio request signature for validation |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `MessageSid` | string | Yes | Unique identifier for the message |
| `AccountSid` | string | Yes | Twilio account SID |
| `From` | string | Yes | Sender phone number (E.164 format) |
| `To` | string | Yes | Recipient phone number (E.164 format) |
| `Body` | string | No | Message text content |
| `NumMedia` | string | No | Number of media attachments |
| `MediaUrl0` | string | No | URL of first media attachment |
| `MediaContentType0` | string | No | MIME type of first media attachment |
| `MessageStatus` | string | No | Delivery status (for status callbacks) |
| `SmsSid` | string | No | SMS SID (for status callbacks) |

#### Request Example

**Inbound Message:**

```bash
curl -X POST "https://api.example.com/twilio" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Twilio-Signature: abc123signature456" \
  -d "MessageSid=SM1234567890abcdef&AccountSid=AC1234567890abcdef&From=%2B15559876543&To=%2B15551234567&Body=Hello%2C%20I%20need%20assistance&NumMedia=0"
```

**Delivery Status Callback:**

```bash
curl -X POST "https://api.example.com/twilio" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Twilio-Signature: abc123signature456" \
  -d "MessageSid=SM1234567890abcdef&AccountSid=AC1234567890abcdef&From=%2B15551234567&To=%2B15559876543&MessageStatus=delivered&SmsSid=SM1234567890abcdef"
```

**MMS with Media:**

```bash
curl -X POST "https://api.example.com/twilio" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Twilio-Signature: abc123signature456" \
  -d "MessageSid=MM1234567890abcdef&AccountSid=AC1234567890abcdef&From=%2B15559876543&To=%2B15551234567&Body=Check%20this%20image&NumMedia=1&MediaUrl0=https%3A%2F%2Fapi.twilio.com%2F2010-04-01%2FAccounts%2FAC123%2FMessages%2FMM123%2FMedia%2FME123&MediaContentType0=image%2Fjpeg"
```

#### Response

**Success Response (200 OK):**

Twilio expects a TwiML response or empty body:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

Or simply an empty `200 OK` response.

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Message successfully received and processed |
| `400` | Invalid request format or missing required fields |
| `401` | Invalid X-Twilio-Signature |
| `403` | Request validation failed |
| `500` | Internal server error |

#### Message Status Values

| Status | Description |
|--------|-------------|
| `queued` | Message is queued for sending |
| `sending` | Message is being sent |
| `sent` | Message sent to carrier |
| `delivered` | Message delivered to recipient |
| `undelivered` | Message failed to deliver |
| `failed` | Message sending failed |

---

## MessageBird Endpoint

### POST /messagebird

Receives incoming messages and delivery status notifications from the MessageBird carrier. Routes messages to the inbound queue for processing.

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Content-Type` | string | Yes | Must be `application/json` |
| `MessageBird-Signature` | string | No | MessageBird request signature |
| `MessageBird-Request-Timestamp` | string | No | Request timestamp for signature validation |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Unique message identifier |
| `recipient` | string | Yes | Recipient phone number |
| `originator` | string | Yes | Sender phone number |
| `body` | string | No | Message text content |
| `createdDatetime` | string | No | ISO 8601 timestamp of message creation |
| `status` | string | No | Delivery status (for status callbacks) |
| `statusDatetime` | string | No | ISO 8601 timestamp of status update |
| `reference` | string | No | Customer reference ID |

#### Request Example

**Inbound Message:**

```bash
curl -X POST "https://api.example.com/messagebird" \
  -H "Content-Type: application/json" \
  -H "MessageBird-Signature: sha256=abc123def456" \
  -H "MessageBird-Request-Timestamp: 1705315800" \
  -d '{
    "id": "mb-msg-123456789",
    "recipient": "15551234567",
    "originator": "15559876543",
    "body": "I would like to schedule an appointment",
    "createdDatetime": "2024-01-15T10:30:00+00:00",
    "reference": "ref-12345"
  }'
```

**Delivery Status Report:**

```bash
curl -X POST "https://api.example.com/messagebird" \
  -H "Content-Type: application/json" \
  -H "MessageBird-Signature: sha256=abc123def456" \
  -d '{
    "id": "mb-msg-123456789",
    "recipient": "15559876543",
    "originator": "15551234567",
    "status": "delivered",
    "statusDatetime": "2024-01-15T10:30:05+00:00",
    "reference": "ref-12345"
  }'
```

#### Response

**Success Response (200 OK):**

```json
{
  "success": true,
  "messageId": "mb-msg-123456789"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Message successfully received and queued |
| `400` | Invalid JSON or missing required fields |
| `401` | Invalid signature |
| `500` | Internal server error |

#### Status Values

| Status | Description |
|--------|-------------|
| `scheduled` | Message scheduled for delivery |
| `sent` | Message sent to carrier |
| `buffered` | Message buffered by carrier |
| `delivered` | Message delivered |
| `expired` | Message expired before delivery |
| `delivery_failed` | Delivery failed |

---

## Inteliquent Endpoints

### POST /webhooks/inteliquent

Receives inbound SMS/MMS messages and delivery receipts from the Inteliquent carrier via webhook. Handles authorization, processes messages (including MMS with multiple attachments), and routes to SQS for further processing.

#### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Content-Type` | string | Yes | Must be `application/json` |
| `Authorization` | string | Yes | Bearer token or API key for authorization |

#### Request Body Parameters

**Inbound Message:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `messageId` | string | Yes | Unique message identifier |
| `type` | string | Yes | Message type: `sms` or `mms` |
| `from` | string | Yes | Sender phone number |
| `to` | string | Yes | Recipient phone number |
| `text` | string | No | Message text content |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `attachments` | array | No | MMS media attachments |
| `attachments[].url` | string | No | URL of media attachment |
| `attachments[].contentType` | string | No | MIME type of attachment |
| `attachments[].size` | number | No | Size in bytes |

**Delivery Receipt:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `messageId` | string | Yes | Original message identifier |
| `type` | string | Yes | Must be `delivery_receipt` |
| `status` | string | Yes | Delivery status |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `errorCode` | string | No | Error code if failed |
| `errorMessage` | string | No | Error description if failed |

#### Request Example

**Inbound SMS:**

```bash
curl -X POST "https://api.example.com/webhooks/inteliquent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "messageId": "intq-msg-abc123456",
    "type": "sms",
    "from": "+15559876543",
    "to": "+15551234567",
    "text": "What are your business hours?",
    "timestamp": "2024-01-15T10:30:00.000Z"
  }'
```

**Inbound MMS with Multiple Attachments:**

```bash
curl -X POST "https://api.example.com/webhooks/inteliquent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "messageId": "intq-msg-def789012",
    "type": "mms",
    "from": "+15559876543",
    "to": "+15551234567",
    "text": "Here are the photos from the inspection",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "attachments": [
      {
        "url": "https://media.inteliquent.com/attachments/img1.jpg",
        "contentType": "image/jpeg",
        "size": 245678
      },
      {
        "url": "https://media.inteliquent.com/attachments/img2.jpg",
        "contentType": "image/jpeg",
        "size": 312456
      },
      {
        "url": "https://media.inteliquent.com/attachments/doc.pdf",
        "contentType": "application/pdf",
        "size": 1024567
      }
    ]
  }'
```

**Delivery Receipt:**

```bash
curl -X POST "https://api.example.com/webhooks/inteliquent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "messageId": "intq-msg-abc123456",
    "type": "delivery_receipt",
    "status": "delivered",
    "timestamp": "2024-01-15T10:30:05.000Z"
  }'
```

**Failed Delivery Receipt:**

```bash
curl -X POST "https://api.example.com/webhooks/inteliquent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "messageId": "intq-msg-abc123456",
    "type": "delivery_receipt",
    "status": "failed",
    "timestamp": "2024-01-15T10:30:10.000Z",
    "errorCode": "30008",
    "errorMessage": "Unknown destination handset"
  }'
```

#### Response

**Success Response (200 OK):**

```json
{
  "success": true,
  "messageId": "intq-msg-abc123456",
  "status": "accepted"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Message successfully received and queued |
| `400` | Invalid request body or malformed JSON |
| `401` | Missing or invalid Authorization header |
| `403` | Authorization failed |
| `422` | Unprocessable entity - validation failed |
| `500` | Internal server error |

#### Delivery Status Values

| Status | Description |
|--------|-------------|
| `pending` | Message queued for delivery |
| `sent` | Message sent to carrier network |
| `delivered` | Message successfully delivered |
| `failed` | Message delivery failed |
| `rejected` | Message rejected by carrier |
| `expired` | Message expired before delivery |

---

### OPTIONS /webhooks/inteliquent

Handles CORS preflight requests for the Inteliquent webhook endpoint.

#### Request Example

```bash
curl -X OPTIONS "https://api.example.com/webhooks/inteliquent" \
  -H "Origin: https://inteliquent.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization"
```

#### Response

**Success Response (200 OK):**

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

---

## Common Patterns

### Message Processing Flow

All carrier webhooks follow a similar processing pattern:

1. **Request Validation** - Verify signatures/authentication
2. **Payload Parsing** - Extract message or status data
3. **Normalization** - Convert to internal message format
4. **Queue Routing** - Send to appropriate SQS queue for processing

### Retry Handling

Carriers typically retry webhook delivery on failure. Ensure your error responses follow these guidelines:

| Response | Carrier Behavior |
|----------|------------------|
| `2xx` | Success - no retry |
| `4xx` | Client error - may not retry (depends on carrier) |
| `5xx` | Server error - carrier will retry |

### Security Best Practices

1. **Validate Signatures** - Always verify carrier-provided signatures
2. **Use HTTPS** - All webhook URLs should use TLS
3. **Allowlist IPs** - Consider allowlisting carrier IP ranges
4. **Rate Limiting** - Implement rate limiting to prevent abuse
5. **Idempotency** - Handle duplicate webhook deliveries gracefully

---

## Related Documentation

- [WhatsApp Webhooks](./whatsapp-webhooks.md) - WhatsApp-specific webhook endpoints
- [LiveChat Webhooks](./livechat-webhooks.md) - LiveChat integration endpoints
- [API Overview](./README.md) - Complete API reference