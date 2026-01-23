# Channel Data Models

This document provides comprehensive documentation for channel and publishing-related data models in the omnichannel-omniservice. These models define the structure and configuration of digital communication channels, channel groups, and the mechanisms for publishing messages across different platforms.

## Overview

The channel data models form the foundation of the omnichannel communication system, enabling organizations to:

- Configure and manage multiple digital communication channels (SMS, MMS, WhatsApp, LiveChat, PubNub)
- Group channels for shared or private use
- Route and publish messages to the appropriate channels
- Track carrier-specific configurations and responses

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌───────────────────┐         ┌──────────────────────┐                │
│  │ DigitalChannelGroup│◄────────│    DigitalChannel    │                │
│  │                   │ 1     * │                      │                │
│  │ - digitalChannelGroupId     │ - digitalChannelId   │                │
│  │ - type            │         │ - address            │                │
│  │ - orgId           │         │ - carrier            │                │
│  │ - defaultGroup    │         │ - channelType        │                │
│  └─────────┬─────────┘         └──────────┬───────────┘                │
│            │                              │                             │
│            │                              │                             │
│            ▼                              ▼                             │
│  ┌───────────────────┐         ┌──────────────────────┐                │
│  │   PublishChannel  │─────────│   PublishIdentity    │                │
│  │                   │         │                      │                │
│  │ - digitalChannelId│         │ - identityId         │                │
│  │ - interactionId   │         │ - address            │                │
│  └───────────────────┘         │ - contactId          │                │
│                                └──────────────────────┘                │
│                                                                         │
│  ┌───────────────────┐         ┌──────────────────────┐                │
│  │  ReceivedChannel  │         │       Carrier        │                │
│  │                   │         │                      │                │
│  │ - channelType     │         │ - carrierName        │                │
│  │ - address         │         │ - carrierId          │                │
│  │ - carrier         │         │ - serviceMessage     │                │
│  └───────────────────┘         └──────────────────────┘                │
│                                                                         │
│  ┌───────────────────┐         ┌──────────────────────┐                │
│  │CarrierHttpResponse│         │  CarrierChannelEvent │                │
│  │                   │         │                      │                │
│  │ - statusCode      │         │ - carrier            │                │
│  │ - carrierMetric   │         │ - channelType        │                │
│  └───────────────────┘         │ - interactionData    │                │
│                                └──────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Channel Models

### DigitalChannel

Represents a single digital communication channel such as SMS, MMS, WhatsApp, or PubNub. This is the fundamental unit of channel configuration.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `digitalChannelId` | string | Yes | Unique identifier for the channel |
| `digitalChannelGroupId` | string | Yes | Parent group identifier |
| `address` | string | Yes | Phone number or channel address |
| `externalAddress` | string | No | External address (e.g., WhatsApp phone number ID) |
| `carrier` | CarrierName | Yes | Carrier provider (Test, MessageBird, WhatsApp, Twilio, Inteliquent, Bandwidth) |
| `channelType` | ChannelType | Yes | Type of channel (SMS, MMS, WhatsApp, PubNub, LiveChat) |
| `countryCodePrefix` | string \| null | No | Country code prefix (e.g., '44', '1') |
| `countryCodeIso` | string \| null | No | ISO country code (e.g., 'GB', 'US') |
| `createdBy` | number | Yes | User ID who created the channel |
| `createdDate` | string (ISO 8601) | Yes | Creation timestamp |
| `modifiedBy` | number | No | User ID who last modified |
| `modifiedDate` | string (ISO 8601) | No | Last modification timestamp |

#### Validation Rules

- `address` must be a valid phone number format for SMS/MMS/WhatsApp channels
- `carrier` must be a valid CarrierName enum value
- `channelType` must be a valid ChannelType enum value
- `digitalChannelGroupId` must reference an existing DigitalChannelGroup

#### Example

```json
{
  "digitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "digitalChannelGroupId": "dcg-98765432-1abc-def0-1234-567890abcdef",
  "address": "+14155551234",
  "externalAddress": "109876543210987",
  "carrier": "WhatsApp",
  "channelType": "WhatsApp",
  "countryCodePrefix": "1",
  "countryCodeIso": "US",
  "createdBy": 1001,
  "createdDate": "2024-01-15T10:30:00.000Z",
  "modifiedBy": 1001,
  "modifiedDate": "2024-01-20T14:45:00.000Z"
}
```

#### Relationships

- **Belongs to**: `DigitalChannelGroup` (via `digitalChannelGroupId`)
- **Referenced by**: `PublishChannel`, `ReceivedChannel`, `CarrierChannelEvent`

---

### DigitalChannelGroup

Groups multiple digital channels together for shared or private use within an organization. Groups enable routing and access control at the channel level.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `digitalChannelGroupId` | string | Yes | Unique group identifier |
| `type` | DigitalChannelGroupType | Yes | Group type (PRIVATE, SHARED) |
| `orgId` | number | Yes | Organization ID |
| `name` | string | Yes | Group name |
| `description` | string | No | Group description |
| `digitalChannels` | DigitalChannel[] | No | List of channels in the group |
| `defaultGroup` | boolean | Yes | Whether this is the default group |
| `leaseDigitalChannels` | boolean | No | Whether channels are leased |
| `userId` | number | No | User ID for private groups |
| `groupId` | number \| null | No | Associated group ID |
| `referencedDigitalChannelId` | string | No | Primary referenced channel ID |

#### Validation Rules

- `type` must be either 'PRIVATE' or 'SHARED'
- For PRIVATE groups, `userId` is required
- `orgId` must be a valid organization identifier
- Only one group per organization can have `defaultGroup` set to true

#### Example

```json
{
  "digitalChannelGroupId": "dcg-98765432-1abc-def0-1234-567890abcdef",
  "type": "SHARED",
  "orgId": 5001,
  "name": "Customer Support Channels",
  "description": "Shared channels for customer support team",
  "digitalChannels": [
    {
      "digitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "address": "+14155551234",
      "carrier": "WhatsApp",
      "channelType": "WhatsApp"
    },
    {
      "digitalChannelId": "dc-b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "address": "+14155555678",
      "carrier": "Twilio",
      "channelType": "SMS"
    }
  ],
  "defaultGroup": true,
  "leaseDigitalChannels": false,
  "userId": null,
  "groupId": 200,
  "referencedDigitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

#### Relationships

- **Contains**: Multiple `DigitalChannel` instances
- **Referenced by**: `ServiceMessage`, `PublishChannel`, `Interaction`

---

## Publishing Models

### PublishChannel

Configuration model for publishing outbound messages to a specific channel and identity combination.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `digitalChannelType` | ChannelType | Yes | Channel type for publishing |
| `identityId` | string | Yes | Target identity ID |
| `contactId` | string | Yes | Target contact ID |
| `digitalChannelId` | string | Yes | Channel ID to use |
| `digitalChannelGroupId` | string | Yes | Channel group ID |
| `digitalChannel` | DigitalChannel | No | Full digital channel details |
| `identity` | PublishIdentity | No | Target identity details |
| `interactionId` | string | No | Associated interaction ID |

#### Validation Rules

- `digitalChannelType` must match the type of the referenced `digitalChannel`
- `digitalChannelId` must reference a valid channel within the specified group
- `identityId` and `contactId` must reference existing records

#### Example

```json
{
  "digitalChannelType": "WhatsApp",
  "identityId": "id-11111111-2222-3333-4444-555555555555",
  "contactId": "ct-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "digitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "digitalChannelGroupId": "dcg-98765432-1abc-def0-1234-567890abcdef",
  "digitalChannel": {
    "digitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "address": "+14155551234",
    "carrier": "WhatsApp",
    "channelType": "WhatsApp"
  },
  "identity": {
    "identityId": "id-11111111-2222-3333-4444-555555555555",
    "address": "+447700900123",
    "channelType": "WhatsApp",
    "contactId": "ct-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "displayName": "John Smith"
  },
  "interactionId": "int-12345678-abcd-ef01-2345-6789abcdef01"
}
```

#### Relationships

- **References**: `DigitalChannel`, `DigitalChannelGroup`, `PublishIdentity`
- **Used by**: Outbound message processing pipeline

---

### PublishIdentity

Identity information specifically structured for message publishing operations.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identityId` | string | Yes | Unique identity identifier |
| `address` | string | Yes | Target address (phone number) |
| `channelType` | ChannelType | Yes | Channel type |
| `contactId` | string | Yes | Associated contact ID |
| `displayName` | string | No | Display name |
| `countryCodeIso` | string | No | ISO country code |
| `countryCodePrefix` | string | No | Country code prefix |
| `createdDate` | string (ISO 8601) | No | Creation timestamp |
| `modifiedDate` | string (ISO 8601) | No | Modification timestamp |
| `externalIds` | ExternalId[] | No | External system identifiers |

#### Validation Rules

- `address` must be a valid format for the specified `channelType`
- `channelType` must be a valid ChannelType enum value

#### Example

```json
{
  "identityId": "id-11111111-2222-3333-4444-555555555555",
  "address": "+447700900123",
  "channelType": "WhatsApp",
  "contactId": "ct-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "displayName": "John Smith",
  "countryCodeIso": "GB",
  "countryCodePrefix": "44",
  "createdDate": "2024-01-10T08:00:00.000Z",
  "modifiedDate": "2024-01-15T12:30:00.000Z",
  "externalIds": [
    {
      "externalId": "003xx000004TmiVAAS",
      "confirmed": true,
      "displayName": "John Smith",
      "primary": true
    }
  ]
}
```

#### Relationships

- **References**: `Contact` (via `contactId`)
- **Used by**: `PublishChannel`

---

### ReceivedChannel

Information about the channel through which an inbound message was received.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channelType` | ChannelType | Yes | Type of channel |
| `address` | string | Yes | Channel address |
| `carrier` | CarrierName | Yes | Carrier provider |
| `requestId` | string | No | Request identifier |
| `receivedDateTime` | string (ISO 8601) | Yes | When message was received |
| `senderType` | SenderType | Yes | Type of sender (CONTACT, USER) |
| `messageReference` | string | No | Message reference/time token |

#### Validation Rules

- `receivedDateTime` must be a valid ISO 8601 timestamp
- `senderType` must be either 'CONTACT' or 'USER'

#### Example

```json
{
  "channelType": "SMS",
  "address": "+14155551234",
  "carrier": "Twilio",
  "requestId": "req-abcdef12-3456-7890-abcd-ef1234567890",
  "receivedDateTime": "2024-01-20T15:30:45.123Z",
  "senderType": "CONTACT",
  "messageReference": "SM1234567890abcdef1234567890abcdef"
}
```

#### Relationships

- **Used by**: `ServiceMessage` for tracking inbound message origin

---

## Carrier Models

### Carrier

Abstract base class for carrier implementations that handle message publishing to different communication providers.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `serviceMessage` | ServiceMessage | Yes | The service message being processed |
| `carrierName` | CarrierName | Yes | Name of the carrier |
| `carrierId` | number | Yes | Unique carrier identifier for billing |

#### Validation Rules

- `carrierName` must be a valid CarrierName enum value
- `carrierId` must be a positive integer

#### Example

```json
{
  "serviceMessage": {
    "correlationId": "corr-12345678-abcd-ef01-2345-6789abcdef01",
    "tenant": { "orgId": 5001, "userId": 1001 },
    "direction": "OUTBOUND"
  },
  "carrierName": "WhatsApp",
  "carrierId": 3
}
```

#### Common Use Cases

- Extended by specific carrier implementations (WhatsApp, Twilio, Bandwidth, etc.)
- Used for message publishing and delivery status handling

---

### CarrierHttpResponse

HTTP response model returned by carrier webhook handlers after processing incoming messages or status updates.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `statusCode` | number | Yes | HTTP status code |
| `body` | string | Yes | Response body content |
| `carrierResponseMetric` | CarrierResponseMetric | Yes | Metric type for tracking |
| `messageTypeDimension` | MessageTypeDimension | No | Type of message received |
| `channelTypeDimension` | ChannelType | No | Channel type for metrics |
| `orgId` | number | No | Organization identifier |
| `headers` | object | No | Optional HTTP response headers |

#### Validation Rules

- `statusCode` must be a valid HTTP status code (100-599)
- `carrierResponseMetric` must be a valid enum value

#### Example

```json
{
  "statusCode": 200,
  "body": "{\"status\": \"received\"}",
  "carrierResponseMetric": "ReceivedAndForwarded",
  "messageTypeDimension": "Message",
  "channelTypeDimension": "WhatsApp",
  "orgId": 5001,
  "headers": {
    "Content-Type": "application/json"
  }
}
```

---

### CarrierChannelEvent

Event structure for tracking carrier channel communications, used for analytics and billing.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `attemptCount` | number | Yes | Number of delivery attempts |
| `carrier` | CarrierName | Yes | Name of the carrier |
| `carrierBillingId` | number | Yes | Carrier billing identifier |
| `channelType` | ChannelType | Yes | Type of channel |
| `correlationId` | string | Yes | Correlation ID for tracking |
| `deliverySuccess` | boolean | Yes | Whether delivery was successful |
| `direction` | ServiceDirection | Yes | Direction of the message |
| `eventDateTime` | string (ISO 8601) | Yes | Timestamp of the event |
| `fromAddress` | string | Yes | Sender address |
| `toAddress` | string | Yes | Recipient address |
| `orgId` | number | Yes | Organization identifier |
| `userId` | string | No | User identifier |
| `channelData` | object | No | Channel-specific data |
| `interactionData` | object | No | Interaction data with IDs |

#### Validation Rules

- `attemptCount` must be a positive integer
- `eventDateTime` must be a valid ISO 8601 timestamp
- `direction` must be 'INBOUND' or 'OUTBOUND'

#### Example

```json
{
  "attemptCount": 1,
  "carrier": "WhatsApp",
  "carrierBillingId": 3,
  "channelType": "WhatsApp",
  "correlationId": "corr-12345678-abcd-ef01-2345-6789abcdef01",
  "deliverySuccess": true,
  "direction": "OUTBOUND",
  "eventDateTime": "2024-01-20T15:35:00.000Z",
  "fromAddress": "+14155551234",
  "toAddress": "+447700900123",
  "orgId": 5001,
  "userId": "1001",
  "channelData": {
    "templateName": "order_confirmation",
    "templateLanguage": "en_US"
  },
  "interactionData": {
    "interactionId": "int-12345678-abcd-ef01-2345-6789abcdef01",
    "conversationId": "conv-87654321-dcba-10fe-5432-10fedcba9876",
    "timeToken": "16796544000000000",
    "contactId": "ct-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "digitalChannelGroupId": "dcg-98765432-1abc-def0-1234-567890abcdef",
    "identityId": "id-11111111-2222-3333-4444-555555555555",
    "digitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

---

### CarrierLogInfo

Structured logging information for carrier-related events, used for debugging and monitoring.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logRecordName` | string | Yes | Name identifier for log record |
| `successful` | boolean | Yes | Whether the operation was successful |
| `direction` | ServiceDirection | Yes | Direction of the service message |
| `carrier` | CarrierName | Yes | Name of the carrier |
| `channelType` | string | Yes | Type of communication channel |
| `identityAddress` | string | No | Address of the identity |
| `digitalChannelAddress` | string | No | Address of the digital channel |
| `digitalChannelId` | string | No | ID of the digital channel |
| `identityId` | string | No | ID of the identity |
| `interactionId` | string | No | ID of the interaction |
| `orgId` | number | Yes | Organization identifier |

#### Example

```json
{
  "logRecordName": "CARRIER_PUBLISH_SUCCESS",
  "successful": true,
  "direction": "OUTBOUND",
  "carrier": "WhatsApp",
  "channelType": "WhatsApp",
  "identityAddress": "+447700900123",
  "digitalChannelAddress": "+14155551234",
  "digitalChannelId": "dc-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "identityId": "id-11111111-2222-3333-4444-555555555555",
  "interactionId": "int-12345678-abcd-ef01-2345-6789abcdef01",
  "orgId": 5001
}
```

---

## Carrier Configuration Models

### BandwidthConfig

Configuration structure for integrating with the Bandwidth carrier service.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `account_id` | string | Yes | Bandwidth account ID |
| `api_secret` | string | Yes | Bandwidth API secret |
| `api_token` | string | Yes | Bandwidth API token |
| `application_id` | string | Yes | Bandwidth application ID |
| `user_name` | string | Yes | Bandwidth username |
| `user_password` | string | Yes | Bandwidth user password |

#### Validation Rules

- All fields are required for Bandwidth integration
- Credentials must be valid for the Bandwidth API

#### Example

```json
{
  "account_id": "9999999",
  "api_secret": "aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",
  "api_token": "abc123def456ghi789jkl012mno345pq",
  "application_id": "12345678-abcd-ef01-2345-6789abcdef01",
  "user_name": "support@example.com",
  "user_password": "SecurePassword123!"
}
```

---

## Enumerations

### CarrierName

Supported carrier providers.

| Value | Description |
|-------|-------------|
| `Test` | Test carrier for development |
| `MessageBird` | MessageBird carrier |
| `WhatsApp` | WhatsApp Business API |
| `Twilio` | Twilio SMS/MMS |
| `Inteliquent` | Inteliquent carrier |
| `Bandwidth` | Bandwidth carrier |

### ChannelType

Types of communication channels.

| Value | Description |
|-------|-------------|
| `SMS` | Short Message Service |
| `MMS` | Multimedia Messaging Service |
| `WhatsApp` | WhatsApp messaging |
| `PubNub` | PubNub real-time messaging |
| `LiveChat` | Live chat widget |

### DigitalChannelGroupType

Types of digital channel groups.

| Value | Description |
|-------|-------------|
| `PRIVATE` | Private group for single user |
| `SHARED` | Shared group for multiple users |

### CarrierResponseMetric

Metric types for carrier response tracking.

| Value | Description |
|-------|-------------|
| `ReceivedAndForwarded` | Message successfully received and forwarded |
| `FragmentReceived` | Message fragment received and stored |
| `DuplicateFragment` | Duplicate fragment received and discarded |
| `Rejected` | Message rejected |
| `DiscardDigitalChannelNotFound` | Message discarded - channel not found |

### MessageTypeDimension

Message type dimensions for metrics.

| Value | Description |
|-------|-------------|
| `Unknown` | Unknown message type |
| `Message` | Standard message |
| `DeliveryStatusNotification` | Delivery status notification |

---

## Common Use Cases

### Creating a New Digital Channel

```json
{
  "digitalChannelId": "dc-new12345-6789-abcd-ef01-234567890abc",
  "digitalChannelGroupId": "dcg-existing-group-id",
  "address": "+18005551234",
  "carrier": "Twilio",
  "channelType": "SMS",
  "countryCodePrefix": "1",
  "countryCodeIso": "US",
  "createdBy": 1001,
  "createdDate": "2024-01-25T09:00:00.000Z"
}
```

### Setting Up a Channel Group for a Team

```json
{
  "digitalChannelGroupId": "dcg-team-support-channels",
  "type": "SHARED",
  "orgId": 5001,
  "name": "Support Team Channels",
  "description": "Channels shared by the customer support team",
  "defaultGroup": false,
  "leaseDigitalChannels": false,
  "groupId": 150,
  "digitalChannels": []
}
```

### Publishing to a Channel

```json
{
  "digitalChannelType": "SMS",
  "identityId": "id-customer-identity",
  "contactId": "ct-customer-contact",
  "digitalChannelId": "dc-support-sms-channel",
  "digitalChannelGroupId": "dcg-team-support-channels",
  "interactionId": "int-active-conversation"
}
```

---

## Related Documentation

- [Message Models](./message-models.md) - Core message structures including ServiceMessage
- [Contact Models](./contact-models.md) - Contact and identity management
- [WhatsApp Models](./whatsapp-models.md) - WhatsApp-specific webhook and message models
- [Workflow Models](./workflow-models.md) - Workflow execution and routing