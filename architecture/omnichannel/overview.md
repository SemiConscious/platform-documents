# Omnichannel Architecture

> **Last Updated:** 2026-01-19  
> **Source:** omnichannel-omniservice README, repository analysis  
> **Status:** ✅ Complete

---

## Overview

The Omnichannel service enables multi-channel communication (SMS, WhatsApp, Chat, and future channels) alongside traditional voice services. It's built as a TypeScript/Node.js monorepo with AWS Lambda-based microservices.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL CHANNELS                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│   │    SMS      │    │  WhatsApp   │    │    Chat     │    │   Future    │    │
│   │  Carriers   │    │  Business   │    │   Widget    │    │  Channels   │    │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│          │                  │                  │                  │            │
│          └──────────────────┴─────────┬────────┴──────────────────┘            │
│                                       │                                         │
│                                       ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                      API Gateway (REST/WebSocket)                        │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
└───────────────────────────────────────┼─────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────────┐
│                         OMNISERVICE (AWS Lambda)                                 │
├───────────────────────────────────────┼─────────────────────────────────────────┤
│                                       │                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         @omni/rest                                       │  │
│   │                    Public-facing REST API                                │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        @omni/pipeline                                    │  │
│   │             Inbound/Outbound message processing                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                       @omni/websocket                                    │  │
│   │              Real-time updates to clients                                │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                  Supporting Packages                                     │  │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐            │  │
│   │  │  @omni/   │  │  @omni/   │  │  @omni/   │  │  @omni/   │            │  │
│   │  │   core    │  │  common   │  │  billing  │  │eventsCore │            │  │
│   │  └───────────┘  └───────────┘  └───────────┘  └───────────┘            │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
└───────────────────────────────────────┼─────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────────┐
│                              AWS SERVICES                                        │
├───────────────────────────────────────┼─────────────────────────────────────────┤
│   ┌─────────────┐    ┌─────────────┐  │  ┌─────────────┐    ┌─────────────┐   │
│   │  DynamoDB   │    │     SQS     │◄─┴─►│    SNS      │    │     S3      │   │
│   │ Conversations│   │   Queues    │     │   Topics    │    │   Storage   │   │
│   └─────────────┘    └─────────────┘     └─────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Monorepo Structure

The OmniService is built as a **Lerna monorepo** with the following packages:

### Core Packages

| Package | Description |
|---------|-------------|
| `@omni/rest` | Public-facing REST API via API Gateway |
| `@omni/pipeline` | Lambda pipeline for receiving/sending messages |
| `@omni/websocket` | WebSocket API for real-time client updates |
| `@omni/billing` | Billing event publication to RDS |
| `@omni/core` | Shared helpers, models, TypeScript interfaces |
| `@omni/common` | Common code for omni and external services |
| `@omni/eventsCore` | Core modules for event processing |

### External Events Packages

| Package | Description |
|---------|-------------|
| `@omni/eventsRest` | External Events Service REST API |
| `@omni/eventsPipeline` | External Events Service pipeline |

---

## Key Components

### 1. REST API (@omni/rest)

Exposes public-facing REST endpoints for:
- Message sending/receiving
- Conversation management
- User/channel configuration
- Search and filtering

**Deployment:** AWS API Gateway + Lambda

### 2. Message Pipeline (@omni/pipeline)

Handles asynchronous message processing:
- Inbound message routing
- Outbound message delivery
- Carrier integration
- Message transformation
- Retry logic

**Flow:**
```
Carrier → SQS → Lambda Pipeline → Process → DynamoDB/Carrier
```

### 3. WebSocket Service (@omni/websocket)

Provides real-time updates:
- Conversation state changes
- New message notifications
- Typing indicators
- Read receipts

**Technology:** AWS API Gateway WebSocket

### 4. Chat Widget

**Repository:** `redmatter/chat-widget`

Embeddable widget for web chat:
- Customer-facing UI
- Customizable appearance
- Real-time messaging
- File attachments

### 5. OmniClient V2

**Repository:** `redmatter/omniclient-v2`

Agent-facing React components:
- Conversation list
- Message thread view
- Customer information
- Channel switching

---

## Carrier Integrations

The platform integrates with multiple carriers for SMS/messaging:

| Carrier | Capabilities | Region |
|---------|--------------|--------|
| **MessageBird** | SMS, WhatsApp | Global |
| **Bandwidth** | SMS, MMS | US/Canada |
| **Inteliquent** | SMS | US |

### Configuration (SSM Parameters)

```
omni.carrier.message-bird.key
omni.carrier.bandwidth.account-id
omni.carrier.bandwidth.api-secret
omni.carrier.bandwidth.api-token
omni.carrier.bandwidth.application-id
omni.carrier.bandwidth.user-name
omni.carrier.bandwidth.user-password
omni.carrier.inteliquent.api-key
omni.carrier.inteliquent.authorization-header
```

---

## Data Model

### Conversation

```typescript
interface Conversation {
  conversationId: string;
  organizationId: string;
  channelType: 'SMS' | 'WHATSAPP' | 'CHAT';
  status: 'OPEN' | 'CLOSED' | 'ARCHIVED';
  participants: Participant[];
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}
```

### Message

```typescript
interface Message {
  messageId: string;
  conversationId: string;
  direction: 'INBOUND' | 'OUTBOUND';
  content: MessageContent;
  status: 'PENDING' | 'SENT' | 'DELIVERED' | 'FAILED';
  timestamp: string;
  metadata: Record<string, any>;
}
```

---

## Message Flow

### Inbound Message

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Carrier   │     │  API        │     │  Pipeline   │     │  DynamoDB   │
│             │     │  Gateway    │     │  Lambda     │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │ Webhook          │                   │                   │
       │─────────────────►│                   │                   │
       │                  │ SQS Message       │                   │
       │                  │──────────────────►│                   │
       │                  │                   │ Store Message     │
       │                  │                   │──────────────────►│
       │                  │                   │                   │
       │                  │                   │ Notify (WebSocket)│
       │                  │                   │──────────────────►│ Agents
       │                  │                   │                   │
```

### Outbound Message

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent     │     │  REST       │     │  Pipeline   │     │   Carrier   │
│   Client    │     │  API        │     │  Lambda     │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │ Send Message     │                   │                   │
       │─────────────────►│                   │                   │
       │                  │ Queue Message     │                   │
       │                  │──────────────────►│                   │
       │                  │                   │ Send via Carrier  │
       │                  │                   │──────────────────►│
       │                  │                   │ Delivery Callback │
       │                  │                   │◄──────────────────│
       │ Status Update    │                   │                   │
       │◄─────────────────│◄──────────────────│                   │
       │                  │                   │                   │
```

---

## Development

### Prerequisites

- Node.js v18+
- npm
- Docker (for local DynamoDB)

### Setup

```bash
# Clone repository
git clone git@github.com:redmatter/omnichannel-omniservice.git
cd omnichannel-omniservice

# Install dependencies (all packages)
npm install --include=dev

# Build all packages
npx lerna run build

# Run tests
npx lerna run test:unit
```

### Common Commands

```bash
# Build specific package
npx lerna run build --scope=@omni/rest

# Run linting
npx lerna run lint

# Build OpenAPI specs
npx lerna run build:openapi

# Clean all build artifacts
make clean

# Deploy to dev environment
npx lerna run --scope=@omni/rest make:lambda-deploy -- deploy-rest PROFILE=dev01-admin REGION=us-east-2
```

### Local Testing

Integration tests require local DynamoDB:

```bash
# Start local DynamoDB
npm run pretest:integration

# Run integration tests
npm run test:integration

# Stop local DynamoDB
npm run posttest:integration
```

---

## Error Handling

The service uses typed error classes:

| Error Class | isUser | isRetryable | Use Case |
|-------------|--------|-------------|----------|
| `ValidationError` | ✅ | ❌ | Invalid input data |
| `NotFoundError` | ✅ | ❌ | Resource not found |
| `ForbiddenError` | ✅ | ❌ | Access denied |
| `ConflictError` | ✅ | ❌ | Resource conflict |
| `AuthenticationError` | ✅ | ❌ | Auth failed |
| `ResourceError` | ❌ | ✅ | External service down |
| `DataError` | ❌ | ❌ | Internal data issues |
| `OperationalError` | ❌ | ✅ | General internal error |
| `PermanentError` | ❌ | ❌ | Unrecoverable error |

---

## Key Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| `omnichannel-omniservice` | Main monorepo | TypeScript |
| `omnichannel-omnisettings` | Settings service | TypeScript |
| `chat-widget` | Embeddable chat widget | TypeScript |
| `omniclient-v2` | Agent UI components | TypeScript |
| `omnichannel-omniclient` | Legacy client | JavaScript |

---

## Terraform Modules

| Module | Description |
|--------|-------------|
| `aws-terraform-omnichannel` | Main omnichannel infrastructure |
| `aws-terraform-omnichannel-territory-setup` | Territory-specific setup |
| `aws-terraform-omnichannel-settings` | Settings service infrastructure |
| `aws-terraform-omnichannel-region-setup` | Region-specific setup |
| `aws-omnichannel-client-v2` | Client infrastructure |

---

## Configuration

### SSM Parameters Required

```
omni.pubnub.test.secret-key
omni.pubnub.test.publish-key
omni.pubnub.test.subscribe-key
omni.rm-coreapi.auth-token
```

### Core API Integration

The service interacts with Core API for:
- User details
- Number information
- Salesforce data connector info

Set `CORE_API_HOST=MOCK` for local development without Core API.

---

## Related Documentation

- [Voice Routing Overview](../voice-routing/overview.md)
- [Salesforce Integration](../salesforce-integration/overview.md)
- [Confluence: OmniChannel Configuration](https://natterbox.atlassian.net/wiki/spaces/OCP/pages/1284112397/Configuration)

---

*Documentation compiled from omnichannel-omniservice README and repository analysis*
