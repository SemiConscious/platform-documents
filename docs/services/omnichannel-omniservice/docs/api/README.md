# Omni Channel Service API Documentation

## Overview

The Omni Channel Service provides a unified messaging pipeline for handling inbound and outbound message routing across multiple communication carriers. Built on AWS Lambda with a TypeScript NodeJS monorepo architecture, this service acts as the central hub for processing messages from WhatsApp, Bandwidth, Twilio, LiveChat, MessageBird, and Inteliquent.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│                 │     │                      │     │                 │
│  Carrier        │────▶│  Omni Channel        │────▶│  SQS Queues     │
│  Webhooks       │     │  Service (Lambda)    │     │  (Processing)   │
│                 │     │                      │     │                 │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                        │
        │                        │
   WhatsApp                 Signature
   Bandwidth                Validation
   Twilio                   Message Routing
   LiveChat                 Status Updates
   MessageBird
   Inteliquent
```

## Base URL

All endpoints are served from your deployed Lambda function URL or API Gateway endpoint:

```
https://{your-deployment-url}/
```

## Authentication

Authentication varies by carrier integration:

| Carrier | Authentication Method |
|---------|----------------------|
| **WhatsApp** | `X-Hub-Signature-256` header validation (HMAC-SHA256) |
| **Twilio** | Twilio signature validation |
| **Bandwidth** | Request origin validation |
| **LiveChat** | Base64-encoded identifier containing `orgId:userId:livechat-id` |
| **MessageBird** | Request origin validation |
| **Inteliquent** | Authorization header validation |

### WhatsApp Webhook Verification

WhatsApp requires webhook verification during setup. The service validates:
- `hub.verify_token` - Must match your configured verification token
- `hub.challenge` - Returned to Meta to confirm ownership

## API Endpoints Summary

The service exposes **16 endpoints** across 6 carrier integrations:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| WhatsApp Webhooks | 5 | Message receiving, status updates, and WABA routing |
| Bandwidth Webhooks | 2 | SMS/MMS receiving and delivery status |
| Twilio Webhooks | 1 | SMS receiving and delivery status |
| LiveChat Webhooks | 4 | Live chat message handling and media uploads |
| MessageBird Webhooks | 1 | SMS receiving and delivery status |
| Inteliquent Webhooks | 3 | SMS/MMS receiving and delivery receipts |

## Detailed Documentation

For comprehensive endpoint documentation, refer to the carrier-specific guides:

| Documentation | Path | Coverage |
|---------------|------|----------|
| [WhatsApp Webhooks](./whatsapp-webhooks.md) | `docs/api/whatsapp-webhooks.md` | WhatsApp message receiving, verification, status updates, and WABA ID routing configuration |
| [Carrier Webhooks](./carrier-webhooks.md) | `docs/api/carrier-webhooks.md` | Bandwidth, Twilio, MessageBird, and Inteliquent SMS/MMS integrations |
| [LiveChat Webhooks](./livechat-webhooks.md) | `docs/api/livechat-webhooks.md` | LiveChat message handling, conversation fetching, and media uploads |

## Common Patterns

### Message Flow

1. **Inbound Message**: Carrier webhook → Validation → SQS Queue → Processing
2. **Status Update**: Carrier notification → Validation → Status Queue → Processing
3. **Re-routing** (WhatsApp): Based on WABA ID mapping, messages can be routed to different environment URLs

### CORS Support

All endpoints support CORS preflight requests via `OPTIONS` methods, enabling browser-based integrations where required.

### Request Processing

```
Incoming Request
       │
       ▼
┌──────────────────┐
│ Signature/Auth   │
│ Validation       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Message Parsing  │
│ & Normalization  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SQS Queue        │
│ Routing          │
└──────────────────┘
```

## Error Handling

The service returns standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| `200` | Request processed successfully |
| `400` | Bad request - malformed payload or missing required fields |
| `401` | Unauthorized - signature validation failed |
| `403` | Forbidden - verification token mismatch |
| `404` | Not found - invalid endpoint or identifier |
| `500` | Internal server error |

### Error Response Format

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "requestId": "unique-request-identifier"
}
```

## Rate Limiting

Rate limits are enforced at the AWS Lambda and API Gateway level:

- **Concurrent Executions**: Configured per Lambda function
- **Burst Capacity**: Managed by AWS service limits
- **Carrier-Specific Limits**: Follow individual carrier webhook guidelines

## Message Types Supported

| Carrier | Text | Media (MMS) | Templates | Status Updates |
|---------|------|-------------|-----------|----------------|
| WhatsApp | ✓ | ✓ | ✓ | ✓ |
| Bandwidth | ✓ | ✓ (fragments) | — | ✓ |
| Twilio | ✓ | ✓ | — | ✓ |
| LiveChat | ✓ | ✓ | — | ✓ |
| MessageBird | ✓ | ✓ | — | ✓ |
| Inteliquent | ✓ | ✓ (multi-attachment) | — | ✓ |

## Environment Configuration

The service supports environment-based routing, particularly for WhatsApp integrations where WABA IDs can be mapped to specific environment URLs for development, staging, and production isolation.

## Getting Started

1. Review the [WhatsApp Webhooks](./whatsapp-webhooks.md) documentation for Meta integration setup
2. Configure carrier credentials in your environment
3. Set up SQS queues for message processing
4. Deploy the Lambda functions
5. Register webhook URLs with each carrier

## Support

For issues with specific carrier integrations, refer to the detailed documentation linked above or consult the carrier's official webhook documentation.