# Message Data Models

This document provides comprehensive documentation for the core message-related data models in the omnichannel-omniservice. These models form the foundation of message processing, routing, and delivery across all communication channels.

## Overview

The message data models handle the complete lifecycle of messages in the omnichannel system, from initial receipt through processing, routing, and delivery. They support multiple carriers, various media types, and complex routing scenarios.

### Related Documentation

- [Channel Models](./channel-models.md) - Digital channel configurations
- [Contact Models](./contact-models.md) - Contact and identity management
- [WhatsApp Models](./whatsapp-models.md) - WhatsApp-specific structures
- [Workflow Models](./workflow-models.md) - Workflow execution tracking

---

## Core Message Models

### ServiceMessage

The core message model for omnichannel service communication, handling both inbound and outbound messages across various channels. This is the primary model that flows through the entire message processing pipeline.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversationId` | `string \| null` | No | Unique identifier for the conversation |
| `correlationId` | `string` | Yes | Unique identifier for tracking/correlating requests across services |
| `createdDateTime` | `string` (ISO 8601) | Yes | Timestamp when the message was created |
| `digitalChannel` | `DigitalChannel` | Yes | The digital channel used for the message |
| `digitalChannelGroup` | `DigitalChannelGroup` | Yes | Group of digital channels for the tenant |
| `direction` | `ServiceDirection` | Yes | Direction of message (`INBOUND` or `OUTBOUND`) |
| `identity` | `Identity` | Yes | Identity information of the contact |
| `messagePayLoad` | `MessagePayLoad` | Yes | The actual message content |
| `receivedChannel` | `ReceivedChannel` | No | Channel through which message was received |
| `sqsGroupId` | `string` | Yes | SQS message group identifier for FIFO ordering |
| `tenant` | `Tenant` | Yes | Organization and user tenant information |
| `externalMessageId` | `string` | No | External message ID (e.g., WhatsApp message ID) |
| `contact` | `Contact` | No | Contact information associated with the message |
| `workFlowSteps` | `WorkFlowSteps` | No | Workflow execution status tracking |
| `emittedEvents` | `object` | No | Events emitted during processing |
| `conversationResolution` | `array<string>` | No | Resolution path audit trail for conversation routing |
| `mappedInboundDigitalChannelGroup` | `IDigitalChannelGroup` | No | Resolved digital channel group for inbound routing |
| `mappedFolder` | `IFolder` | No | Resolved folder for message routing |
| `conversationOnHold` | `boolean` | No | Flag indicating if conversation is on hold |
| `externalIdLookupResponse` | `ExternalIdLookupResponse[]` | No | External ID lookup results |

#### Validation Rules

- `correlationId` must be a valid UUID
- `createdDateTime` must be a valid ISO 8601 timestamp
- `direction` must be either `INBOUND` or `OUTBOUND`
- `sqsGroupId` is required for FIFO queue ordering
- `tenant.orgId` must be a positive integer

#### Example

```json
{
  "conversationId": "conv-12345-abcde-67890",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "createdDateTime": "2024-01-15T10:30:00.000Z",
  "digitalChannel": {
    "digitalChannelId": "dc-001",
    "address": "+14155551234",
    "carrier": "Twilio",
    "channelType": "SMS"
  },
  "digitalChannelGroup": {
    "digitalChannelGroupId": "dcg-001",
    "type": "SHARED",
    "orgId": 1001
  },
  "direction": "INBOUND",
  "identity": {
    "channelType": "SMS",
    "address": "+14155559876",
    "displayName": "John Doe"
  },
  "messagePayLoad": {
    "textMessage": {
      "text": "Hello, I need help with my order"
    }
  },
  "sqsGroupId": "org-1001-+14155559876",
  "tenant": {
    "orgId": 1001,
    "userId": 5001
  },
  "externalMessageId": "SM1234567890abcdef",
  "workFlowSteps": {
    "identityLookup": "EXECUTED_OK",
    "preRoutingWorkFlow": "EXECUTED_OK",
    "inboundWorkFlow": "REQUIRED"
  },
  "emittedEvents": {},
  "conversationResolution": ["folder-lookup", "owner-assignment"],
  "conversationOnHold": false
}
```

#### Relationships

- Contains a `DigitalChannel` for channel configuration
- Contains a `DigitalChannelGroup` for channel grouping
- Contains a `Contact` for customer information
- Contains a `Tenant` for multi-tenancy
- Contains `MessagePayLoad` for actual content
- Contains `WorkFlowSteps` for processing status

---

### MessagePayLoad

Container for message content supporting various media types including text, images, video, and audio.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `textMessage` | `TextMessage` | No | Text message content |
| `image` | `ImageMessage` | No | Image message content |
| `video` | `MediaMessage` | No | Video attachment with external reference |
| `audio` | `MediaMessage` | No | Audio attachment with external reference |

#### Validation Rules

- At least one of `textMessage`, `image`, `video`, or `audio` must be present
- Only one primary content type should be set per message
- Media references must be valid URLs or storage references

#### Example

```json
{
  "textMessage": {
    "text": "Please see the attached image of the product issue"
  },
  "image": {
    "caption": "Damaged product photo",
    "externalRef": {
      "carrier": "Twilio",
      "reference": "https://api.twilio.com/media/ME123456789"
    },
    "internalRef": "s3://media-bucket/org-1001/images/img-12345.jpg"
  }
}
```

---

### TextMessage

Text message payload containing the actual text content of a message.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | Yes | Message text content |

#### Validation Rules

- `text` must not be empty
- Maximum length varies by channel (SMS: 1600, WhatsApp: 4096)

#### Example

```json
{
  "text": "Thank you for contacting support. How can I assist you today?"
}
```

---

### ImageMessage

Image/MMS message payload with support for captions and both external and internal references.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `caption` | `string` | No | Image caption |
| `externalRef` | `MediaReference` | No | External media reference from carrier |
| `internalRef` | `string` | No | Internal storage reference (S3 path) |

#### Validation Rules

- Either `externalRef` or `internalRef` must be provided
- `caption` maximum length is 1024 characters
- Supported formats: JPEG, PNG, GIF, WebP

#### Example

```json
{
  "caption": "Order confirmation receipt",
  "externalRef": {
    "carrier": "WhatsApp",
    "reference": "https://lookaside.fbsbx.com/whatsapp_business/attachments/..."
  },
  "internalRef": "s3://media-bucket/org-1001/images/receipt-20240115.png"
}
```

---

### MediaReference

Reference to external media content hosted by a carrier.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `carrier` | `CarrierName` | Yes | Carrier that hosts the media |
| `reference` | `string` | Yes | URL or reference to the media |

#### Validation Rules

- `carrier` must be a valid `CarrierName` enum value
- `reference` must be a valid URL or carrier-specific reference

#### Example

```json
{
  "carrier": "MessageBird",
  "reference": "https://media.messagebird.com/v1/media/abc123def456"
}
```

---

### MediaMessage

Generic media message structure for video and audio attachments.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `externalRef` | `ExternalRef` | Yes | External reference to the media file |

#### Example

```json
{
  "externalRef": {
    "reference": "https://cdn.carrier.com/media/video-12345.mp4"
  }
}
```

---

## Channel Context Models

### ReceivedChannel

Information about the channel through which a message was received, capturing the original reception context.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channelType` | `ChannelType` | Yes | Type of channel |
| `address` | `string` | Yes | Channel address |
| `carrier` | `CarrierName` | Yes | Carrier provider |
| `requestId` | `string` | No | Request identifier from carrier |
| `receivedDateTime` | `string` (ISO 8601) | Yes | When message was received |
| `senderType` | `SenderType` | Yes | Type of sender (`CONTACT`, `USER`) |
| `messageReference` | `string` | No | Message reference/time token |

#### Validation Rules

- `channelType` must be a valid channel type
- `carrier` must match the actual carrier that delivered the message
- `receivedDateTime` must be a valid ISO 8601 timestamp

#### Example

```json
{
  "channelType": "WhatsApp",
  "address": "+14155551234",
  "carrier": "WhatsApp",
  "requestId": "wamid.HBgNMTQ0NTU1NTEyMzQ=",
  "receivedDateTime": "2024-01-15T10:29:58.000Z",
  "senderType": "CONTACT",
  "messageReference": "16842075980000"
}
```

---

### Identity

Simple identity information for message sender/recipient.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channelType` | `ChannelType` | Yes | Channel type |
| `address` | `string` | Yes | Address/phone number |
| `displayName` | `string` | No | Display name |

#### Validation Rules

- `address` format depends on `channelType` (phone number for SMS/WhatsApp)
- `displayName` maximum length is 255 characters

#### Example

```json
{
  "channelType": "SMS",
  "address": "+14155559876",
  "displayName": "Jane Smith"
}
```

---

### Tenant

Organization and user context for multi-tenant operations.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization identifier |
| `userId` | `number` | No | User identifier |

#### Validation Rules

- `orgId` must be a positive integer
- `userId` must be a positive integer when present

#### Example

```json
{
  "orgId": 1001,
  "userId": 5001
}
```

---

## Publishing Models

### PublishChannel

Channel configuration for publishing outbound messages to contacts.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `digitalChannelType` | `ChannelType` | Yes | Channel type for publishing |
| `identityId` | `string` | Yes | Target identity ID |
| `contactId` | `string` | Yes | Target contact ID |
| `digitalChannelId` | `string` | Yes | Channel ID to use |
| `digitalChannelGroupId` | `string` | Yes | Channel group ID |
| `digitalChannel` | `DigitalChannel` | Yes | Full digital channel details |
| `identity` | `PublishIdentity` | Yes | Target identity details |
| `interactionId` | `string` | No | Associated interaction ID |

#### Validation Rules

- All ID fields must be valid UUIDs
- `digitalChannel` must be configured for outbound messaging
- `identity` must have a valid address for the channel type

#### Example

```json
{
  "digitalChannelType": "WhatsApp",
  "identityId": "ident-001-abc",
  "contactId": "contact-001-xyz",
  "digitalChannelId": "dc-wa-001",
  "digitalChannelGroupId": "dcg-001",
  "digitalChannel": {
    "digitalChannelId": "dc-wa-001",
    "address": "+14155551234",
    "carrier": "WhatsApp",
    "channelType": "WhatsApp",
    "externalAddress": "123456789012345"
  },
  "identity": {
    "identityId": "ident-001-abc",
    "address": "+14155559876",
    "channelType": "WhatsApp",
    "contactId": "contact-001-xyz",
    "displayName": "John Doe"
  },
  "interactionId": "int-001-def"
}
```

---

### PublishIdentity

Identity information for message publishing with full contact details.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | `string` | Yes | Target address |
| `channelType` | `ChannelType` | Yes | Channel type |
| `contactId` | `string` | Yes | Contact ID |
| `displayName` | `string` | No | Display name |
| `identityId` | `string` | Yes | Identity ID |
| `countryCodeIso` | `string` | No | ISO country code |
| `countryCodePrefix` | `string` | No | Country code prefix |
| `createdDate` | `string` (ISO 8601) | No | Creation timestamp |
| `modifiedDate` | `string` (ISO 8601) | No | Modification timestamp |
| `externalIds` | `ExternalId[]` | No | External identifiers |

#### Example

```json
{
  "address": "+14155559876",
  "channelType": "SMS",
  "contactId": "contact-001-xyz",
  "displayName": "John Doe",
  "identityId": "ident-001-abc",
  "countryCodeIso": "US",
  "countryCodePrefix": "1",
  "createdDate": "2024-01-10T08:00:00.000Z",
  "modifiedDate": "2024-01-15T10:30:00.000Z",
  "externalIds": [
    {
      "externalId": "003xx000001234ABC",
      "confirmed": true,
      "displayName": "John Doe (Salesforce)",
      "primary": true
    }
  ]
}
```

---

## Message Fragment Handling

### MessageFragment

Model for handling fragmented SMS messages that arrive in multiple parts.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization identifier |
| `from` | `string` | Yes | Sender address |
| `destination` | `string` | Yes | Destination address |
| `fragRef` | `string` | Yes | Fragment reference identifier |
| `carrierName` | `CarrierName` | Yes | Name of the carrier |
| `fragments` | `array` | Yes | Array of fragment objects |

#### Fragment Object Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fragmentText` | `string` | Yes | Text content of this fragment |
| `fragmentNumber` | `number` | Yes | Sequence number of fragment |

#### Validation Rules

- `fragRef` must uniquely identify the fragmented message
- `fragments` must be ordered by `fragmentNumber`
- All fragments must be received before message reconstruction

#### Example

```json
{
  "orgId": 1001,
  "from": "+14155559876",
  "destination": "+14155551234",
  "fragRef": "frag-ref-abc123",
  "carrierName": "Twilio",
  "fragments": [
    {
      "fragmentText": "This is the first part of a long message that ",
      "fragmentNumber": 1
    },
    {
      "fragmentText": "was split into multiple fragments for delivery.",
      "fragmentNumber": 2
    }
  ]
}
```

---

## Delivery Status Models

### DeliveryStatus

Delivery status notification message for tracking message delivery outcomes.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization identifier |
| `status` | `IDeliveryStatus` | Yes | Delivery status (`Failed`, `Delivered`, etc.) |
| `reason` | `DeliveryStatusReason` | No | Reason for status (`Undeliverable`, `TemplateBadQuality`) |

#### Example

```json
{
  "orgId": 1001,
  "status": "Delivered",
  "reason": null
}
```

```json
{
  "orgId": 1001,
  "status": "Failed",
  "reason": "Undeliverable"
}
```

---

### DeliveryStatusMessage

Base structure for delivery status notifications from carriers.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization identifier |

#### Relationships

- Extended by carrier-specific delivery status models (e.g., `BandwidthDeliveryStatus`)

---

### BandwidthDeliveryStatus

Handles Bandwidth carrier delivery status processing.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deliveryStatusMessage` | `DeliveryStatusMessage` | Yes | The delivery status message object |

---

## Queue and Lock Models

### MessageQueueLock

Model for managing message queue locks to prevent concurrent processing of the same message group.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization identifier |
| `messageGroupId` | `string` | Yes | Message group identifier for the lock |
| `serviceName` | `string` | Yes | Name of the service holding the lock |
| `cachePeriod` | `number` | Yes | Lock cache period in seconds |

#### Validation Rules

- `messageGroupId` must be unique within an organization
- `cachePeriod` must be a positive integer (typically 30-300 seconds)
- Lock expires automatically after `cachePeriod`

#### Example

```json
{
  "orgId": 1001,
  "messageGroupId": "org-1001-+14155559876",
  "serviceName": "inbound-message-processor",
  "cachePeriod": 60
}
```

---

## Carrier Event Models

### CarrierChannelEvent

Event structure for carrier channel communications used for analytics and billing.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `attemptCount` | `number` | Yes | Number of delivery attempts |
| `carrier` | `CarrierName` | Yes | Name of the carrier |
| `carrierBillingId` | `number` | Yes | Carrier billing identifier |
| `channelType` | `ChannelType` | Yes | Type of channel |
| `correlationId` | `string` | Yes | Correlation ID for tracking |
| `deliverySuccess` | `boolean` | Yes | Whether delivery was successful |
| `direction` | `ServiceDirection` | Yes | Direction of the message |
| `eventDateTime` | `string` | Yes | ISO timestamp of the event |
| `fromAddress` | `string` | Yes | Sender address |
| `toAddress` | `string` | Yes | Recipient address |
| `orgId` | `number` | Yes | Organization identifier |
| `userId` | `string` | No | User identifier |
| `channelData` | `object` | No | Channel-specific data |
| `interactionData` | `object` | No | Interaction data |

#### Interaction Data Structure

| Field | Type | Description |
|-------|------|-------------|
| `interactionId` | `string` | Interaction identifier |
| `conversationId` | `string` | Conversation identifier |
| `timeToken` | `string` | Time token |
| `contactId` | `string` | Contact identifier |
| `digitalChannelGroupId` | `string` | Digital channel group ID |
| `identityId` | `string` | Identity identifier |
| `digitalChannelId` | `string` | Digital channel ID |

#### Example

```json
{
  "attemptCount": 1,
  "carrier": "Twilio",
  "carrierBillingId": 100,
  "channelType": "SMS",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "deliverySuccess": true,
  "direction": "OUTBOUND",
  "eventDateTime": "2024-01-15T10:30:05.000Z",
  "fromAddress": "+14155551234",
  "toAddress": "+14155559876",
  "orgId": 1001,
  "userId": "5001",
  "interactionData": {
    "interactionId": "int-001-abc",
    "conversationId": "conv-001-xyz",
    "timeToken": "16842075980000",
    "contactId": "contact-001",
    "digitalChannelGroupId": "dcg-001",
    "identityId": "ident-001",
    "digitalChannelId": "dc-001"
  }
}
```

---

## Logging and Metrics Models

### CarrierLogInfo

Structured logging information for carrier events.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logRecordName` | `string` | Yes | Name identifier for log record |
| `successful` | `boolean` | Yes | Whether the operation was successful |
| `direction` | `ServiceDirection` | Yes | Direction of the service message |
| `carrier` | `CarrierName` | Yes | Name of the carrier |
| `channelType` | `string` | Yes | Type of communication channel |
| `identityAddress` | `string` | Yes | Address of the identity |
| `digitalChannelAddress` | `string` | Yes | Address of the digital channel |
| `digitalChannelId` | `string` | Yes | ID of the digital channel |
| `identityId` | `string` | Yes | ID of the identity |
| `interactionId` | `string` | No | ID of the interaction |
| `orgId` | `number` | Yes | Organization identifier |

#### Example

```json
{
  "logRecordName": "OutboundMessageDelivery",
  "successful": true,
  "direction": "OUTBOUND",
  "carrier": "WhatsApp",
  "channelType": "WhatsApp",
  "identityAddress": "+14155559876",
  "digitalChannelAddress": "+14155551234",
  "digitalChannelId": "dc-wa-001",
  "identityId": "ident-001-abc",
  "interactionId": "int-001-def",
  "orgId": 1001
}
```

---

## HTTP Response Models

### CarrierHttpResponse

HTTP response model for carrier webhook handlers.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `statusCode` | `number` | Yes | HTTP status code |
| `body` | `string` | Yes | Response body |
| `carrierResponseMetric` | `CarrierResponseMetric` | No | Metric type for tracking |
| `messageTypeDimension` | `MessageTypeDimension` | No | Message type dimension |
| `channelTypeDimension` | `ChannelType` | No | Channel type dimension |
| `orgId` | `number` | No | Organization ID |
| `headers` | `object` | No | Optional HTTP response headers |

#### Example

```json
{
  "statusCode": 200,
  "body": "{\"status\": \"received\"}",
  "carrierResponseMetric": "ReceivedAndForwarded",
  "messageTypeDimension": "Message",
  "channelTypeDimension": "SMS",
  "orgId": 1001
}
```

---

### SQSLambdaResponse

Response object for SQS Lambda handlers indicating batch processing failures.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batchItemFailures` | `Array<{itemIdentifier: string}>` | Yes | List of failed batch items with their message identifiers |

#### Example

```json
{
  "batchItemFailures": [
    {
      "itemIdentifier": "msg-id-12345"
    },
    {
      "itemIdentifier": "msg-id-67890"
    }
  ]
}
```

---

## Enumerations

### CarrierResponseMetric

Metric types for carrier response tracking.

| Value | Description |
|-------|-------------|
| `ReceivedAndForwarded` | Message received and forwarded successfully |
| `FragmentReceived` | Message fragment received and stored |
| `DuplicateFragment` | Duplicate fragment discarded |
| `Rejected` | Message rejected |
| `DiscardDigitalChannelNotFound` | Message discarded - digital channel not found |

### MessageTypeDimension

Message type dimensions used in metrics.

| Value | Description |
|-------|-------------|
| `Unknown` | Unknown message type |
| `Message` | Regular message |
| `DeliveryStatusNotification` | Delivery status notification message |

### MessageType

Message type identifiers.

| Value | Description |
|-------|-------------|
| `Msg` | Standard message type |
| `DSN` | Delivery status notification type |

### ServiceDirection

Direction of message flow.

| Value | Description |
|-------|-------------|
| `INBOUND` | Message from contact to system |
| `OUTBOUND` | Message from system to contact |

### SenderType

Type of message sender.

| Value | Description |
|-------|-------------|
| `CONTACT` | Message from external contact |
| `USER` | Message from system user |

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ServiceMessage (Core)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐          ┌─────────────────┐        ┌──────────────┐       │
│  │   Tenant    │          │  MessagePayLoad │        │   Identity   │       │
│  │  - orgId    │          │                 │        │  - address   │       │
│  │  - userId   │          │         │       │        │  - type      │       │
│  └─────────────┘          │         │       │        └──────────────┘       │
│                           │         ▼       │                               │
│                           │  ┌─────────────┐│                               │
│                           │  │ TextMessage ││                               │
│                           │  │ ImageMessage││                               │
│                           │  │ MediaMessage││                               │
│                           │  └─────────────┘│                               │
│                           └─────────────────┘                               │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌──────────────┐         ┌────────────────┐        ┌─────────────────┐     │
│  │DigitalChannel│         │ReceivedChannel │        │ WorkFlowSteps   │     │
│  │  - address   │         │  - carrier     │        │ - identityLookup│     │
│  │  - carrier   │         │  - channelType │        │ - preRouting    │     │
│  └──────────────┘         └────────────────┘        └─────────────────┘     │
│         │                                                                    │
│         ▼                                                                    │
│  ┌───────────────────┐                                                       │
│  │DigitalChannelGroup│                                                       │
│  │  - digitalChannels│                                                       │
│  └───────────────────┘                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    Publishing Flow
                    ═══════════════
┌────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ PublishChannel │ ───▶ │ PublishIdentity │ ───▶ │  ExternalId     │
│ - channelType  │      │   - address     │      │  - externalId   │
│ - identityId   │      │   - contactId   │      │  - confirmed    │
└────────────────┘      └─────────────────┘      └─────────────────┘

                    Delivery Tracking
                    ═════════════════
┌────────────────────┐      ┌─────────────────┐
│ CarrierChannelEvent│ ───▶ │  DeliveryStatus │
│ - correlationId    │      │   - status      │
│ - deliverySuccess  │      │   - reason      │
└────────────────────┘      └─────────────────┘
```

---

## Common Use Cases

### 1. Processing an Inbound SMS Message

```json
{
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "direction": "INBOUND",
  "tenant": {
    "orgId": 1001
  },
  "digitalChannel": {
    "address": "+14155551234",
    "carrier": "Twilio",
    "channelType": "SMS"
  },
  "identity": {
    "channelType": "SMS",
    "address": "+14155559876"
  },
  "messagePayLoad": {
    "textMessage": {
      "text": "I need help with my order #12345"
    }
  },
  "receivedChannel": {
    "channelType": "SMS",
    "carrier": "Twilio",
    "receivedDateTime": "2024-01-15T10:30:00.000Z",
    "senderType": "CONTACT"
  }
}
```

### 2. Sending an Outbound WhatsApp Message with Image

```json
{
  "correlationId": "660e8400-e29b-41d4-a716-446655440001",
  "direction": "OUTBOUND",
  "tenant": {
    "orgId": 1001,
    "userId": 5001
  },
  "digitalChannel": {
    "address": "+14155551234",
    "carrier": "WhatsApp",
    "channelType": "WhatsApp",
    "externalAddress": "123456789012345"
  },
  "identity": {
    "channelType": "WhatsApp",
    "address": "+14155559876",
    "displayName": "John Doe"
  },
  "messagePayLoad": {
    "textMessage": {
      "text": "Here is your order confirmation:"
    },
    "image": {
      "caption": "Order #12345 - Confirmation",
      "internalRef": "s3://media-bucket/org-1001/confirmations/order-12345.png"
    }
  }
}
```

### 3. Tracking Message Delivery Status

```json
{
  "attemptCount": 1,
  "carrier": "Twilio",
  "channelType": "SMS",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "deliverySuccess": true,
  "direction": "OUTBOUND",
  "eventDateTime": "2024-01-15T10:30:15.000Z",
  "orgId": 1001,
  "interactionData": {
    "conversationId": "conv-001-xyz",
    "interactionId": "int-001-abc"
  }
}
```