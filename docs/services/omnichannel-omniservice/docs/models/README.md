# Data Models Overview

## omnichannel-omniservice

This document provides a comprehensive index of all data models used in the omnichannel-omniservice, organized by domain. For detailed field-level documentation, refer to the linked topic-specific documents.

---

## Data Architecture Overview

The omnichannel-omniservice data architecture is designed around a **message-centric pipeline** that enables unified communication across multiple digital channels (SMS, MMS, WhatsApp, LiveChat, PubNub). The architecture supports:

- **Multi-tenant operations** with organization and user-level isolation
- **Bi-directional messaging** (inbound from customers, outbound from agents)
- **Channel abstraction** allowing consistent handling regardless of carrier
- **Contact identity resolution** across multiple channels and external systems
- **Workflow-driven processing** with configurable routing and automation
- **Event-driven architecture** using AWS SQS and EventBridge for asynchronous processing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CARRIER WEBHOOKS                                   │
│         (WhatsApp, Bandwidth, Inteliquent, MessageBird, Twilio)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INBOUND MESSAGE PROCESSING                            │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │   Carrier    │───▶│   Service    │───▶│   Identity   │                  │
│   │   Webhook    │    │   Message    │    │   Lookup     │                  │
│   │   Models     │    │   Creation   │    │   & Contact  │                  │
│   └──────────────┘    └──────────────┘    │   Resolution │                  │
│                                           └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW & ROUTING ENGINE                            │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │   Workflow   │───▶│  Interaction │───▶│    Folder    │                  │
│   │   Steps      │    │   & Channel  │    │   Routing    │                  │
│   │   Execution  │    │   Assignment │    │              │                  │
│   └──────────────┘    └──────────────┘    └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OUTBOUND MESSAGE PUBLISHING                            │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │   Publish    │───▶│   Carrier    │───▶│   Delivery   │                  │
│   │   Channel    │    │   Specific   │    │   Status     │                  │
│   │   Selection  │    │   Payload    │    │   Tracking   │                  │
│   └──────────────┘    └──────────────┘    └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Model Categories

### 1. Message Models
**Count:** 15 models | **Documentation:** [Message Models](./message-models.md)

Core message structures that flow through the service pipeline, including payloads for text, image, video, and audio content.

| Model | Purpose |
|-------|---------|
| `ServiceMessage` | Core message object passed through the entire service pipeline |
| `MessagePayLoad` | Container for message content supporting multiple media types |
| `TextMessage` | Text message content structure |
| `ImageMessage` | Image/MMS message payload with media references |
| `MediaMessage` | Generic media message with external reference |
| `MediaReference` | Reference to external media content |
| `ExternalRef` | External reference for media files |
| `ReceivedChannel` | Information about the channel through which a message was received |
| `Identity` | Simple identity information for message sender/recipient |
| `Tenant` | Organization and user context for multi-tenant operations |
| `MessageFragment` | Model for handling fragmented SMS messages |
| `DeliveryStatus` | Delivery status notification message |
| `DeliveryStatusMessage` | Base structure for delivery status notifications |
| `CarrierChannelEvent` | Event structure for carrier channel communications |
| `UpdateConsentParams` | Parameters for updating user consent |

---

### 2. Channel Models
**Count:** 18 models | **Documentation:** [Channel Models](./channel-models.md)

Digital channel configuration, carrier integrations, and channel group management for multi-channel communication.

| Model | Purpose |
|-------|---------|
| `DigitalChannel` | Represents a single digital communication channel |
| `DigitalChannelGroup` | Group of digital channels assigned to a user or organization |
| `IDigitalChannelGroup` | Interface for digital channel group routing configuration |
| `PublishChannel` | Channel configuration for publishing outbound messages |
| `PublishIdentity` | Identity information for message publishing |
| `Carrier` | Abstract base class for carrier implementations |
| `BandwidthConfig` | Configuration structure for Bandwidth carrier integration |
| `BandwidthDeliveryStatus` | Handles Bandwidth carrier delivery status processing |
| `CarrierHttpResponse` | HTTP response model for carrier webhook handlers |
| `ReRouterHttpResponse` | HTTP response for re-router mapping endpoints |
| `ReRouterMapping` | Mapping for routing notifications to correct environment |
| `IFolder` | Folder entity for organizing conversations |
| `Interaction` | Represents an interaction between a contact identity and a digital channel |
| `InteractionOwner` | Owner entity for an interaction |
| `ILiveChatPayload` | Payload structure for live chat messages |
| `ILiveChatMessage` | Base structure for live chat messages |
| `InteliquentWebhookBody` | Inteliquent carrier webhook request body |
| `CarrierLogInfo` | Structured logging information for carrier events |

---

### 3. Contact Models
**Count:** 8 models | **Documentation:** [Contact Models](./contact-models.md)

Contact management, identity resolution, and external system integration for customer data.

| Model | Purpose |
|-------|---------|
| `Contact` | Contact entity representing a person communicating through the system |
| `ContactIdentity` | Identity record linking a contact to a specific channel address |
| `ExternalId` | External system identifier for contacts/identities |
| `ExternalIdLookupResponse` | Response object for external identity lookup |
| `PublishIdentity` | Identity information for message publishing |
| `WhatsAppContact` | Contact information from WhatsApp message |
| `WhatsAppProfile` | WhatsApp user profile |
| `CDCEvent` | Change Data Capture event from EventBridge |

---

### 4. WhatsApp Models
**Count:** 22 models | **Documentation:** [WhatsApp Models](./whatsapp-models.md)

WhatsApp Business API integration including webhook payloads, templates, and status notifications.

| Model | Purpose |
|-------|---------|
| `WhatsAppWebhookPayload` | Root payload structure for WhatsApp webhook notifications |
| `WhatsAppEntry` | Single entry in WhatsApp webhook notification |
| `WhatsAppChange` | Change notification from WhatsApp |
| `WhatsAppMessageValue` | Value object for WhatsApp message notifications |
| `WhatsAppMetadata` | Metadata for WhatsApp business phone |
| `WhatsAppContact` | Contact information from WhatsApp message |
| `WhatsAppProfile` | WhatsApp user profile |
| `WhatsAppMessage` | Incoming WhatsApp message |
| `WhatsAppTextContent` | Text content of WhatsApp message |
| `WhatsAppStatus` | WhatsApp message status update |
| `WhatsAppConversation` | WhatsApp conversation metadata |
| `WhatsAppOrigin` | Origin of WhatsApp conversation |
| `WhatsAppTemplateStatusUpdate` | Template status update notification |
| `WhatsAppTemplateQualityUpdate` | Template quality score update notification |
| `WhatsAppRoutingMessage` | Internal routing message for WhatsApp notifications |
| `WhatsAppPayload` | Payload structure for outbound WhatsApp messages |
| `IWhatsAppMessageTemplate` | WhatsApp message template structure |
| `IWhatsAppReaction` | WhatsApp message reaction structure |
| `WhatsAppEnvMapping` | WhatsApp Business Account to environment URL mapping |
| `WhatsAppErrorCodes` | Enum for WhatsApp error codes |
| `ReRoutingMapper` | Enum for re-routing mapper values |
| `CDCEventDetail` | CDC event detail containing metadata |

---

### 5. Workflow Models
**Count:** 12 models | **Documentation:** [Workflow Models](./workflow-models.md)

Workflow execution, SQS event handling, and system infrastructure models.

| Model | Purpose |
|-------|---------|
| `WorkFlowSteps` | Tracks execution status of workflow steps in message processing |
| `WorkFlowResult` | Enum for workflow execution results |
| `WorkFlowResponse` | Response structure from workflow execution |
| `SQSEventRecord` | AWS SQS event record structure |
| `SQSAttributes` | Standard SQS message attributes |
| `SQSMessageAttributes` | Custom SQS message attributes for routing |
| `SQSStringAttribute` | SQS string attribute structure |
| `SQSLambdaResponse` | Response object for SQS Lambda handlers |
| `DynamoDBBatchResponse` | Response object for DynamoDB stream Lambda handlers |
| `MappedStreamRecordSet` | Remapped DynamoDB stream records grouped by primary key |
| `MessageQueueLock` | Model for managing message queue locks |
| `MediaConvertJob` | Media conversion job tracking |

---

## Model Group Relationships

The following diagram illustrates how model groups relate to each other in the message processing flow:

```
                    ┌─────────────────────┐
                    │   EXTERNAL CARRIERS │
                    │   (WhatsApp, SMS,   │
                    │    Bandwidth, etc.) │
                    └──────────┬──────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      WHATSAPP MODELS                              │
│  (WhatsAppWebhookPayload, WhatsAppMessage, WhatsAppStatus, etc.) │
│                                                                   │
│  Carrier-specific webhook parsing and template management         │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                       MESSAGE MODELS                              │
│  (ServiceMessage, MessagePayLoad, TextMessage, MediaMessage)     │
│                                                                   │
│  Normalized message format for internal processing                │
└──────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│   CONTACT MODELS    │ │   CHANNEL MODELS    │ │  WORKFLOW MODELS    │
│                     │ │                     │ │                     │
│ (Contact,           │ │ (DigitalChannel,    │ │ (WorkFlowSteps,     │
│  ContactIdentity,   │ │  DigitalChannelGroup│ │  WorkFlowResponse,  │
│  ExternalId)        │ │  Interaction)       │ │  SQSEventRecord)    │
│                     │ │                     │ │                     │
│ WHO is messaging    │ │ HOW messages route  │ │ WHAT happens to     │
│                     │ │                     │ │ messages            │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    INTERACTION &    │
                    │   CONVERSATION      │
                    │    (Combines all    │
                    │     model groups)   │
                    └─────────────────────┘
```

### Key Relationships

| From | To | Relationship |
|------|-----|--------------|
| `ServiceMessage` | `Tenant` | Contains tenant context for multi-tenant routing |
| `ServiceMessage` | `DigitalChannel` | References the channel used for communication |
| `ServiceMessage` | `Identity` | Contains sender/recipient identity information |
| `ServiceMessage` | `MessagePayLoad` | Contains the actual message content |
| `ServiceMessage` | `WorkFlowSteps` | Tracks workflow execution status |
| `Contact` | `ContactIdentity` | One-to-many: A contact has multiple identities |
| `ContactIdentity` | `ExternalId` | One-to-many: Identity linked to external systems |
| `DigitalChannelGroup` | `DigitalChannel` | One-to-many: Group contains multiple channels |
| `Interaction` | `Contact` | Links conversation to a contact |
| `Interaction` | `DigitalChannel` | Links conversation to a specific channel |
| `PublishChannel` | `DigitalChannel` | References channel for outbound publishing |
| `PublishChannel` | `PublishIdentity` | References target identity for publishing |
| `WhatsAppWebhookPayload` | `WhatsAppEntry` | Contains array of notification entries |
| `WhatsAppEntry` | `WhatsAppChange` | Contains array of changes |
| `WhatsAppMessageValue` | `WhatsAppMessage` | Contains incoming messages |
| `WhatsAppMessageValue` | `WhatsAppStatus` | Contains status updates |

---

## Enumerations Reference

The following enumerations are used across model groups:

| Enum | Values | Used By |
|------|--------|---------|
| `ChannelType` | SMS, MMS, WhatsApp, PubNub, LiveChat | DigitalChannel, Identity, ContactIdentity |
| `CarrierName` | Test, MessageBird, WhatsApp, Twilio, Bandwidth, Inteliquent | DigitalChannel, Carrier, MediaReference |
| `ServiceDirection` | INBOUND, OUTBOUND | ServiceMessage, CarrierChannelEvent |
| `DigitalChannelGroupType` | PRIVATE, SHARED | DigitalChannelGroup |
| `FolderType` | DEFAULT, TEMPORARY | IFolder |
| `SenderType` | CONTACT, USER | ReceivedChannel |
| `OrganisationalEntity` | User, Group | InteractionOwner |
| `CarrierResponseMetric` | ReceivedAndForwarded, FragmentReceived, DuplicateFragment, Rejected, DiscardDigitalChannelNotFound | CarrierHttpResponse |
| `MessageTypeDimension` | Unknown, Message, DeliveryStatusNotification | CarrierHttpResponse |
| `WorkFlowResult` | HTTP_SUCCESS, HTTP_NOT_FOUND, HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR | WorkFlowResponse |
| `MediaConvertJobStatus` | Complete, Failed, Incompatible | MediaConvertJob |
| `MediaType` | image, video, audio, document | ILiveChatPayload, WhatsAppPayload |

---

## Quick Reference by Use Case

### Receiving Inbound Messages
1. [WhatsApp Models](./whatsapp-models.md) - Parse carrier webhooks
2. [Message Models](./message-models.md) - Create ServiceMessage
3. [Contact Models](./contact-models.md) - Resolve contact identity
4. [Channel Models](./channel-models.md) - Route to appropriate channel group

### Sending Outbound Messages
1. [Message Models](./message-models.md) - Construct ServiceMessage
2. [Channel Models](./channel-models.md) - Select PublishChannel
3. [WhatsApp Models](./whatsapp-models.md) - Build carrier-specific payload

### Managing Contacts
1. [Contact Models](./contact-models.md) - CRUD operations on contacts
2. [Channel Models](./channel-models.md) - Link identities to channels

### Workflow Automation
1. [Workflow Models](./workflow-models.md) - Configure workflow steps
2. [Message Models](./message-models.md) - Track workflow execution in ServiceMessage

---

## Detailed Documentation Links

| Document | Description |
|----------|-------------|
| [Message Models](./message-models.md) | Complete field-level documentation for core message structures |
| [Channel Models](./channel-models.md) | Digital channel configuration and carrier integration models |
| [Contact Models](./contact-models.md) | Contact management and identity resolution models |
| [WhatsApp Models](./whatsapp-models.md) | WhatsApp Business API integration models |
| [Workflow Models](./workflow-models.md) | Workflow execution and infrastructure models |

---

## Schema Versioning

The data models support schema versioning through the `SchemaVersion` model:

```json
{
  "version": 1,
  "date": "2024-01-15T00:00:00.000Z"
}
```

Schema migrations are tracked to ensure backward compatibility when model structures evolve.