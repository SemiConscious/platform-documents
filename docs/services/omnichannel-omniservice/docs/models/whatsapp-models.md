# WhatsApp Data Models

This document covers WhatsApp-specific data models and payload structures used in the omnichannel-omniservice for WhatsApp Business API integration.

## Overview

The WhatsApp integration handles:
- **Inbound webhooks** from the WhatsApp Business API
- **Outbound message publishing** to WhatsApp users
- **Template status and quality updates**
- **Message delivery status tracking**
- **Internal routing** of WhatsApp notifications

## Entity Relationships

```
WhatsAppWebhookPayload
    └── WhatsAppEntry[]
            └── WhatsAppChange[]
                    └── WhatsAppChangeValue (union)
                            ├── WhatsAppMessageValue
                            │       ├── WhatsAppMetadata
                            │       ├── WhatsAppContact[]
                            │       │       └── WhatsAppProfile
                            │       ├── WhatsAppMessage[]
                            │       │       └── WhatsAppTextContent
                            │       └── WhatsAppStatus[]
                            │               ├── WhatsAppConversation
                            │               │       └── WhatsAppOrigin
                            │               └── pricing (object)
                            ├── WhatsAppTemplateStatusUpdate
                            └── WhatsAppTemplateQualityUpdate

WhatsAppRoutingMessage
    └── WhatsAppMessageValue

WhatsAppPayload (outbound)
    ├── IWhatsAppMessageTemplate
    └── IWhatsAppReaction
```

---

## Webhook Payload Models

### WhatsAppWebhookPayload

Root payload structure for all WhatsApp webhook notifications received from the WhatsApp Business API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `object` | `string` | Yes | Object type, always `"whatsapp_business_account"` |
| `entry` | `WhatsAppEntry[]` | Yes | Array of notification entries |

**Validation Rules:**
- `object` must equal `"whatsapp_business_account"`
- `entry` must contain at least one entry

**Example JSON:**
```json
{
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
                "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBQzRUI",
                "timestamp": "1699459200",
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
}
```

---

### WhatsAppEntry

Single entry in a WhatsApp webhook notification, representing events from one WhatsApp Business Account.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | WhatsApp Business Account ID (WABA ID) |
| `changes` | `WhatsAppChange[]` | Yes | Array of changes/updates for this account |

**Validation Rules:**
- `id` must be a valid WABA ID (numeric string)
- `changes` array must contain at least one change

**Example JSON:**
```json
{
  "id": "123456789012345",
  "changes": [
    {
      "value": { ... },
      "field": "messages"
    }
  ]
}
```

**Relationships:**
- Parent of `WhatsAppChange` objects
- The `id` maps to `ReRouterMapping.wabaId` for environment routing

---

### WhatsAppChange

Change notification from WhatsApp, can contain messages, statuses, or template updates.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | `WhatsAppChangeValue` | Yes | Change value containing the actual data (union type) |
| `field` | `string` | Yes | Field type: `"messages"`, `"message_template_status_update"`, or `"message_template_quality_update"` |

**Validation Rules:**
- `field` determines the structure of `value`
- Valid `field` values: `messages`, `message_template_status_update`, `message_template_quality_update`

**Example JSON (Message):**
```json
{
  "value": {
    "messaging_product": "whatsapp",
    "metadata": { ... },
    "contacts": [ ... ],
    "messages": [ ... ]
  },
  "field": "messages"
}
```

**Example JSON (Template Status):**
```json
{
  "value": {
    "event": "APPROVED",
    "message_template_id": 123456789,
    "message_template_name": "order_confirmation",
    "message_template_language": "en_US"
  },
  "field": "message_template_status_update"
}
```

---

## Message Value Models

### WhatsAppMessageValue

Value object for WhatsApp message notifications, containing incoming messages and/or status updates.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messaging_product` | `string` | Yes | Messaging product, always `"whatsapp"` |
| `metadata` | `WhatsAppMetadata` | Yes | Business phone metadata |
| `contacts` | `WhatsAppContact[]` | No | Contact information (present with messages) |
| `messages` | `WhatsAppMessage[]` | No | Incoming messages array |
| `statuses` | `WhatsAppStatus[]` | No | Message status updates array |

**Validation Rules:**
- `messaging_product` must equal `"whatsapp"`
- Either `messages` or `statuses` should be present (not typically both)
- `contacts` is present when `messages` is present

**Example JSON (Incoming Message):**
```json
{
  "messaging_product": "whatsapp",
  "metadata": {
    "display_phone_number": "15551234567",
    "phone_number_id": "987654321098765"
  },
  "contacts": [
    {
      "profile": {
        "name": "Jane Smith"
      },
      "wa_id": "15559876543"
    }
  ],
  "messages": [
    {
      "from": "15559876543",
      "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBQzRUI",
      "timestamp": "1699459200",
      "type": "text",
      "text": {
        "body": "What are your business hours?"
      }
    }
  ]
}
```

**Example JSON (Status Update):**
```json
{
  "messaging_product": "whatsapp",
  "metadata": {
    "display_phone_number": "15551234567",
    "phone_number_id": "987654321098765"
  },
  "statuses": [
    {
      "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBQzRUI",
      "status": "delivered",
      "timestamp": "1699459300",
      "recipient_id": "15559876543",
      "conversation": {
        "id": "CONVERSATION_ID",
        "origin": {
          "type": "service"
        }
      },
      "pricing": {
        "billable": true,
        "pricing_model": "CBP",
        "category": "service"
      }
    }
  ]
}
```

---

### WhatsAppMetadata

Metadata for the WhatsApp business phone number that received the webhook.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_phone_number` | `string` | Yes | Display phone number of the business (E.164 format without +) |
| `phone_number_id` | `string` | Yes | Phone number ID in WhatsApp system |

**Validation Rules:**
- `display_phone_number` should be numeric string in E.164 format
- `phone_number_id` is used to match with `DigitalChannel.externalAddress`

**Example JSON:**
```json
{
  "display_phone_number": "15551234567",
  "phone_number_id": "987654321098765"
}
```

**Relationships:**
- `phone_number_id` maps to `DigitalChannel.externalAddress` for channel resolution

---

### WhatsAppContact

Contact information extracted from an incoming WhatsApp message.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile` | `WhatsAppProfile` | Yes | Contact profile information |
| `wa_id` | `string` | Yes | WhatsApp user ID (phone number) |

**Validation Rules:**
- `wa_id` is the user's phone number in E.164 format without +

**Example JSON:**
```json
{
  "profile": {
    "name": "John Doe"
  },
  "wa_id": "15559876543"
}
```

**Relationships:**
- Maps to `Identity.address` and `ContactIdentity.address` in the system

---

### WhatsAppProfile

WhatsApp user profile information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | User's WhatsApp display name |

**Example JSON:**
```json
{
  "name": "John Doe"
}
```

**Relationships:**
- Used to populate `Identity.displayName` and `Contact.displayName`

---

### WhatsAppMessage

Incoming WhatsApp message structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | `string` | Yes | Sender phone number (E.164 without +) |
| `id` | `string` | Yes | WhatsApp message ID (wamid format) |
| `timestamp` | `string` | Yes | Unix timestamp as string |
| `type` | `string` | Yes | Message type: `text`, `image`, `audio`, `video`, `document`, `sticker`, `location`, `contacts`, `reaction` |
| `text` | `WhatsAppTextContent` | No | Text message content (when type is `text`) |

**Validation Rules:**
- `id` follows WhatsApp's wamid format
- `timestamp` is Unix epoch in seconds
- Content field depends on `type` (e.g., `text` field for text messages)

**Example JSON:**
```json
{
  "from": "15559876543",
  "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBQzRUI0QzVGNkI1NUY3QzE5OTRB",
  "timestamp": "1699459200",
  "type": "text",
  "text": {
    "body": "Hello, I need assistance"
  }
}
```

**Relationships:**
- `id` stored in `ServiceMessage.externalMessageId`
- `from` maps to `Identity.address`

---

### WhatsAppTextContent

Text content of a WhatsApp text message.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `body` | `string` | Yes | Message body text |

**Validation Rules:**
- Maximum 4096 characters

**Example JSON:**
```json
{
  "body": "Hello, I need help with my recent order #12345"
}
```

---

## Status Models

### WhatsAppStatus

WhatsApp message delivery status update.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Message ID this status refers to |
| `status` | `string` | Yes | Status: `sent`, `delivered`, `read`, `failed` |
| `timestamp` | `string` | Yes | Status update Unix timestamp |
| `recipient_id` | `string` | Yes | Recipient phone number |
| `conversation` | `WhatsAppConversation` | No | Conversation details (for billing) |
| `pricing` | `object` | No | Pricing information for the message |

**Validation Rules:**
- `status` must be one of: `sent`, `delivered`, `read`, `failed`
- `id` must match a previously sent message ID

**Example JSON:**
```json
{
  "id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBQzRUI0QzVGNkI1NUY3QzE5OTRB",
  "status": "delivered",
  "timestamp": "1699459350",
  "recipient_id": "15559876543",
  "conversation": {
    "id": "CONVERSATION_ABC123",
    "origin": {
      "type": "business_initiated"
    }
  },
  "pricing": {
    "billable": true,
    "pricing_model": "CBP",
    "category": "business_initiated"
  }
}
```

**Relationships:**
- Updates `DeliveryStatus` for the corresponding outbound message

---

### WhatsAppConversation

WhatsApp conversation metadata for billing and categorization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | WhatsApp conversation ID |
| `origin` | `WhatsAppOrigin` | Yes | Conversation origin information |

**Example JSON:**
```json
{
  "id": "CONVERSATION_ABC123DEF456",
  "origin": {
    "type": "user_initiated"
  }
}
```

---

### WhatsAppOrigin

Origin classification of a WhatsApp conversation (affects billing).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `string` | Yes | Conversation category: `user_initiated`, `business_initiated`, `referral_conversion`, `service` |

**Example JSON:**
```json
{
  "type": "user_initiated"
}
```

---

## Template Update Models

### WhatsAppTemplateStatusUpdate

Notification when a WhatsApp message template status changes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event` | `string` | Yes | Event type: `APPROVED`, `REJECTED`, `PENDING_DELETION`, `DELETED`, `DISABLED`, `PAUSED`, `IN_APPEAL`, `REINSTATED` |
| `message_template_id` | `bigint` | Yes | Numeric template ID |
| `message_template_name` | `string` | Yes | Template name identifier |
| `message_template_language` | `string` | Yes | Template language and locale (e.g., `en_US`) |
| `reason` | `string` | No | Rejection reason (when event is `REJECTED`) |

**Validation Rules:**
- `event` must be a valid template status event
- `reason` is typically present for `REJECTED` events

**Example JSON (Approved):**
```json
{
  "event": "APPROVED",
  "message_template_id": 123456789012345,
  "message_template_name": "order_shipped",
  "message_template_language": "en_US"
}
```

**Example JSON (Rejected):**
```json
{
  "event": "REJECTED",
  "message_template_id": 123456789012346,
  "message_template_name": "promo_offer",
  "message_template_language": "en_US",
  "reason": "PROMOTIONAL_CONTENT"
}
```

---

### WhatsAppTemplateQualityUpdate

Notification when a WhatsApp message template quality score changes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `previous_quality_score` | `string` | Yes | Previous quality: `GREEN`, `YELLOW`, `RED`, `UNKNOWN` |
| `new_quality_score` | `string` | Yes | New quality score |
| `message_template_id` | `bigint` | Yes | Numeric template ID |
| `message_template_name` | `string` | Yes | Template name identifier |
| `message_template_language` | `string` | Yes | Template language and locale |

**Validation Rules:**
- Quality scores: `GREEN` (high), `YELLOW` (medium), `RED` (low), `UNKNOWN`
- `RED` quality may result in template being paused

**Example JSON:**
```json
{
  "previous_quality_score": "GREEN",
  "new_quality_score": "YELLOW",
  "message_template_id": 123456789012345,
  "message_template_name": "appointment_reminder",
  "message_template_language": "en_US"
}
```

**Relationships:**
- Quality degradation to `RED` may trigger `WhatsAppErrorCodes.TEMPLATE_BAD_QUALITY` errors

---

## Internal Routing Models

### WhatsAppRoutingMessage

Internal message format for routing WhatsApp notifications within the system.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlationId` | `string` | Yes | Correlation ID for distributed tracing |
| `value` | `WhatsAppMessageValue` | Yes | The WhatsApp change value payload |
| `field` | `string` | Yes | Field type from the original webhook |
| `wabaId` | `string` | Yes | WhatsApp Business Account ID |

**Validation Rules:**
- `correlationId` must be a valid UUID
- `wabaId` must match a configured account

**Example JSON:**
```json
{
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "value": {
    "messaging_product": "whatsapp",
    "metadata": {
      "display_phone_number": "15551234567",
      "phone_number_id": "987654321098765"
    },
    "contacts": [
      {
        "profile": { "name": "John Doe" },
        "wa_id": "15559876543"
      }
    ],
    "messages": [
      {
        "from": "15559876543",
        "id": "wamid.HBgLMTU1NTk4NzY1NDM",
        "timestamp": "1699459200",
        "type": "text",
        "text": { "body": "Hello" }
      }
    ]
  },
  "field": "messages",
  "wabaId": "123456789012345"
}
```

**Relationships:**
- Created from `WhatsAppWebhookPayload` after initial processing
- Routed to appropriate handler based on `field` type

---

### ReRouterMapping

Configuration for routing WhatsApp notifications to the correct environment/region.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `wabaId` | `string` | Yes | WhatsApp Business Account ID |
| `url` | `string` | Yes | Target URL for routing notifications |

**Validation Rules:**
- `wabaId` must be a valid WABA ID
- `url` must be a valid HTTPS URL

**Example JSON:**
```json
{
  "wabaId": "123456789012345",
  "url": "https://api.us-east.example.com/whatsapp/webhook"
}
```

**Use Case:**
When WhatsApp sends webhooks, the re-router uses this mapping to forward notifications to the correct regional environment based on the WABA ID.

---

## Outbound Message Models

### WhatsAppPayload

Payload structure for sending outbound WhatsApp messages via the WhatsApp Business API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messaging_product` | `string` | Yes | Always `"whatsapp"` |
| `recipient_type` | `string` | Yes | Recipient type, typically `"individual"` |
| `to` | `string` | Yes | Recipient phone number (E.164 without +) |
| `type` | `string` | Yes | Message type: `text`, `image`, `audio`, `video`, `document`, `template`, `reaction` |
| `text` | `{ body: string }` | No | Text message content |
| `image` | `{ id: string, caption?: string }` | No | Image attachment |
| `audio` | `{ id: string }` | No | Audio attachment |
| `video` | `{ id: string, caption?: string }` | No | Video attachment |
| `document` | `{ id: string, caption?: string, filename: string }` | No | Document attachment |
| `template` | `IWhatsAppMessageTemplate` | No | Template message |

**Validation Rules:**
- Only one content field should be present based on `type`
- `to` must be valid E.164 format
- Media `id` references uploaded media in WhatsApp's media system

**Example JSON (Text Message):**
```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "15559876543",
  "type": "text",
  "text": {
    "body": "Thank you for contacting us. How can we help you today?"
  }
}
```

**Example JSON (Image Message):**
```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "15559876543",
  "type": "image",
  "image": {
    "id": "media_id_from_upload",
    "caption": "Your order receipt"
  }
}
```

**Example JSON (Template Message):**
```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "15559876543",
  "type": "template",
  "template": {
    "name": "order_confirmation",
    "language": {
      "code": "en_US"
    },
    "components": [
      {
        "type": "body",
        "parameters": [
          {
            "type": "text",
            "text": "12345"
          }
        ]
      }
    ]
  }
}
```

---

### IWhatsAppReaction

WhatsApp message reaction payload for reacting to messages with emoji.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | `string` | Yes | ID of the message to react to |
| `emoji` | `string` | Yes | Emoji character for the reaction |

**Validation Rules:**
- `message_id` must be a valid WhatsApp message ID
- `emoji` must be a single emoji character
- Empty string `""` removes the reaction

**Example JSON:**
```json
{
  "message_id": "wamid.HBgLMTU1NTk4NzY1NDMVAgASGBQzRUI",
  "emoji": "👍"
}
```

---

## Error Handling

### WhatsAppErrorCodes

Error codes specific to WhatsApp integration.

| Field | Type | Value | Description |
|-------|------|-------|-------------|
| `TEMPLATE_BAD_QUALITY` | `number` | `131026` | Template has been paused due to low quality score |

**Usage:**
```typescript
if (errorCode === WhatsAppErrorCodes.TEMPLATE_BAD_QUALITY) {
  // Handle template quality issue
  deliveryStatus.reason = DeliveryStatusReason.TemplateBadQuality;
}
```

---

## Common Use Cases

### Processing Inbound Messages

1. Receive `WhatsAppWebhookPayload` at webhook endpoint
2. Extract `WhatsAppEntry` and `WhatsAppChange` objects
3. For `field === "messages"`, process `WhatsAppMessageValue`
4. Create `WhatsAppRoutingMessage` for internal routing
5. Map to `ServiceMessage` for unified processing

### Handling Delivery Status Updates

1. Receive webhook with `statuses` array
2. Match `WhatsAppStatus.id` to sent message
3. Update delivery status based on `status` field
4. Store conversation and pricing information for billing

### Template Management

1. Monitor `message_template_status_update` for approval/rejection
2. Monitor `message_template_quality_update` for quality degradation
3. Disable templates that reach `RED` quality score
4. Re-enable templates when `REINSTATED`

---

## Related Documentation

- [Message Models](./message-models.md) - Core `ServiceMessage` and `MessagePayLoad` models
- [Channel Models](./channel-models.md) - `DigitalChannel` and carrier configuration
- [Contact Models](./contact-models.md) - Contact and identity management
- [Workflow Models](./workflow-models.md) - Message processing workflows