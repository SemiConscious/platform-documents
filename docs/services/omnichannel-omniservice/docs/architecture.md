# System Architecture

## Overview

The **omnichannel-omniservice** is a sophisticated TypeScript NodeJS monorepo that implements a comprehensive omnichannel messaging pipeline. This service acts as a unified messaging gateway, handling inbound and outbound message routing across multiple carriers including WhatsApp, Bandwidth, Twilio, LiveChat, Messagebird, and Inteliquent. Built on AWS Lambda-based processing, the architecture ensures scalability, reliability, and maintainability for high-volume messaging operations.

This documentation provides a comprehensive overview of the system architecture, explaining the pipeline flow, component interactions, AWS infrastructure, and data flow patterns that power the omnichannel messaging capabilities.

---

## High-Level Architecture

### Architectural Overview

The omnichannel-omniservice follows a **serverless microservices architecture** implemented as a monorepo. This design pattern provides several key advantages:

- **Scalability**: AWS Lambda functions scale automatically based on message volume
- **Modularity**: Each carrier integration is isolated, allowing independent development and deployment
- **Resilience**: Failure in one carrier's processing doesn't affect others
- **Cost Efficiency**: Pay-per-execution model reduces infrastructure costs during low-traffic periods

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OMNICHANNEL-OMNISERVICE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     API GATEWAY LAYER                                │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │   │
│  │  │WhatsApp │ │ Twilio  │ │Bandwidth│ │LiveChat │ │Messagebird  │  │   │
│  │  │Webhook  │ │Webhook  │ │Webhook  │ │Webhook  │ │  Webhook    │  │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └──────┬──────┘  │   │
│  └───────┼──────────┼──────────┼──────────┼───────────────┼─────────┘   │
│          │          │          │          │               │             │
│  ┌───────▼──────────▼──────────▼──────────▼───────────────▼─────────┐   │
│  │                  MESSAGE NORMALIZATION LAYER                      │   │
│  │              (Transforms carrier-specific formats)                │   │
│  └─────────────────────────────┬────────────────────────────────────┘   │
│                                │                                         │
│  ┌─────────────────────────────▼────────────────────────────────────┐   │
│  │                    WORKFLOW ENGINE                                │   │
│  │           (Message routing, processing, transformation)           │   │
│  └─────────────────────────────┬────────────────────────────────────┘   │
│                                │                                         │
│  ┌─────────────────────────────▼────────────────────────────────────┐   │
│  │                    PERSISTENCE LAYER                              │   │
│  │           (DynamoDB, S3, SQS, SNS)                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Webhook Receivers** | Accept inbound messages from carriers | AWS API Gateway + Lambda |
| **Message Normalizer** | Transform carrier-specific formats to unified schema | TypeScript processors |
| **Workflow Engine** | Route and process messages based on business rules | Step Functions + Lambda |
| **Media Handler** | Convert and process media attachments | Lambda + S3 |
| **Outbound Router** | Determine optimal carrier for outbound messages | Lambda + DynamoDB |
| **Notification Service** | Send push notifications for message events | SNS + Lambda |

---

## Pipeline Flow Overview

### Message Processing Pipeline

The omnichannel service implements a **bidirectional message pipeline** that handles both inbound (customer-to-system) and outbound (system-to-customer) message flows.

```
                    INBOUND FLOW                          OUTBOUND FLOW
                    ────────────                          ─────────────
                         
    ┌──────────┐    ┌──────────┐                    ┌──────────┐    ┌──────────┐
    │ External │    │ Webhook  │                    │ Internal │    │ Outbound │
    │ Carrier  │───▶│ Receiver │                    │ Service  │───▶│ Router   │
    └──────────┘    └────┬─────┘                    └──────────┘    └────┬─────┘
                         │                                               │
                         ▼                                               ▼
                   ┌──────────┐                                   ┌──────────┐
                   │ Validate │                                   │ Carrier  │
                   │ & Parse  │                                   │ Selector │
                   └────┬─────┘                                   └────┬─────┘
                         │                                               │
                         ▼                                               ▼
                   ┌──────────┐                                   ┌──────────┐
                   │Normalize │                                   │ Format   │
                   │ Message  │                                   │ Message  │
                   └────┬─────┘                                   └────┬─────┘
                         │                                               │
                         ▼                                               ▼
                   ┌──────────┐                                   ┌──────────┐
                   │ Process  │                                   │  Send    │
                   │ Workflow │                                   │ to API   │
                   └────┬─────┘                                   └────┬─────┘
                         │                                               │
                         ▼                                               ▼
                   ┌──────────┐                                   ┌──────────┐
                   │ Store &  │                                   │ Track &  │
                   │ Forward  │                                   │ Confirm  │
                   └──────────┘                                   └──────────┘
```

### Pipeline Stages

1. **Ingestion Stage**: Receive messages via carrier-specific webhooks
2. **Validation Stage**: Verify message integrity, authenticate source
3. **Normalization Stage**: Transform to unified message schema
4. **Processing Stage**: Apply business rules, trigger workflows
5. **Persistence Stage**: Store messages and update conversation state
6. **Delivery Stage**: Route to destination (internal services or external carriers)

---

## Inbound Message Flow

### Detailed Inbound Processing

When a message arrives from an external carrier, it passes through multiple processing stages:

```typescript
// Example: Inbound Message Processing Handler
interface InboundMessageEvent {
  carrier: CarrierType;
  rawPayload: unknown;
  timestamp: string;
  webhookSignature?: string;
}

interface NormalizedMessage {
  messageId: string;
  conversationId: string;
  sender: {
    phoneNumber: string;
    carrierId: string;
    displayName?: string;
  };
  content: {
    type: 'text' | 'media' | 'location' | 'template';
    body: string;
    mediaUrl?: string;
    mediaType?: string;
  };
  metadata: {
    carrier: CarrierType;
    originalPayload: unknown;
    receivedAt: string;
    processedAt: string;
  };
}

type CarrierType = 'whatsapp' | 'twilio' | 'bandwidth' | 'livechat' | 'messagebird' | 'inteliquent';
```

### Inbound Processing Sequence

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     INBOUND MESSAGE PROCESSING                            │
└──────────────────────────────────────────────────────────────────────────┘

  Step 1: Webhook Reception
  ─────────────────────────
  ┌─────────┐     ┌─────────────────┐     ┌──────────────┐
  │Carrier  │────▶│ API Gateway     │────▶│ Lambda       │
  │Webhook  │     │ (Route by path) │     │ (Carrier-    │
  │         │     │                 │     │  specific)   │
  └─────────┘     └─────────────────┘     └──────┬───────┘
                                                  │
  Step 2: Signature Validation                    │
  ────────────────────────────                    ▼
                                          ┌──────────────┐
                                          │ Validate     │
                                          │ Webhook      │──┐
                                          │ Signature    │  │ Invalid
                                          └──────┬───────┘  │
                                                 │ Valid    ▼
  Step 3: Message Parsing                        │    ┌──────────┐
  ───────────────────────                        │    │ Reject   │
                                                 ▼    │ & Log    │
                                          ┌──────────┐└──────────┘
                                          │ Parse    │
                                          │ Carrier  │
                                          │ Format   │
                                          └──────┬───┘
                                                 │
  Step 4: Normalization                          ▼
  ─────────────────────                   ┌──────────────┐
                                          │ Normalize to │
                                          │ Unified      │
                                          │ Schema       │
                                          └──────┬───────┘
                                                 │
  Step 5: Workflow Trigger                       ▼
  ────────────────────────                ┌──────────────┐
                                          │ Start        │
                                          │ Processing   │
                                          │ Workflow     │
                                          └──────┬───────┘
                                                 │
  Step 6: Persistence & Forwarding               ▼
  ────────────────────────────────        ┌──────────────┐
                                          │ Store in     │
                                          │ DynamoDB &   │
                                          │ Forward      │
                                          └──────────────┘
```

### Carrier-Specific Webhook Handlers

Each carrier has dedicated webhook endpoints with specific validation and parsing logic:

| Carrier | Webhook Endpoint | Validation Method |
|---------|------------------|-------------------|
| WhatsApp | `/webhooks/whatsapp` | HMAC signature verification |
| Twilio | `/webhooks/twilio` | Request signature validation |
| Bandwidth | `/webhooks/bandwidth` | Basic auth + callback verification |
| LiveChat | `/webhooks/livechat` | API key validation |
| Messagebird | `/webhooks/messagebird` | Signature header verification |
| Inteliquent | `/webhooks/inteliquent` | Token-based authentication |

### DynamoDB Stream Processing

Inbound messages trigger DynamoDB streams for downstream processing:

```typescript
// DynamoDB Stream Handler
interface DynamoDBStreamEvent {
  eventID: string;
  eventName: 'INSERT' | 'MODIFY' | 'REMOVE';
  dynamodb: {
    NewImage?: Record<string, AttributeValue>;
    OldImage?: Record<string, AttributeValue>;
    StreamViewType: 'NEW_AND_OLD_IMAGES';
  };
}

// Stream processor triggers additional workflows
async function processStreamEvent(event: DynamoDBStreamEvent): Promise<void> {
  switch (event.eventName) {
    case 'INSERT':
      await triggerNewMessageWorkflow(event.dynamodb.NewImage);
      await sendPushNotification(event.dynamodb.NewImage);
      break;
    case 'MODIFY':
      await handleMessageStatusUpdate(event.dynamodb.NewImage, event.dynamodb.OldImage);
      break;
  }
}
```

---

## Outbound Message Flow

### Detailed Outbound Processing

Outbound messages originate from internal services and are routed through the optimal carrier:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     OUTBOUND MESSAGE PROCESSING                           │
└──────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐
  │ Internal        │
  │ Service Request │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐     ┌─────────────────────────────────────────────┐
  │ Outbound API    │     │ Request Validation:                         │
  │ Gateway         │────▶│ • Authentication (API Key / JWT)            │
  │                 │     │ • Rate limiting                             │
  └────────┬────────┘     │ • Payload schema validation                 │
           │              └─────────────────────────────────────────────┘
           ▼
  ┌─────────────────┐     ┌─────────────────────────────────────────────┐
  │ Carrier         │     │ Selection Criteria:                         │
  │ Selection       │────▶│ • Recipient phone number prefix             │
  │ Engine          │     │ • Previous conversation carrier             │
  │                 │     │ • Carrier availability/health               │
  └────────┬────────┘     │ • Cost optimization rules                   │
           │              │ • Message type support                      │
           ▼              └─────────────────────────────────────────────┘
  ┌─────────────────┐
  │ Message         │
  │ Formatter       │────▶ Transform to carrier-specific format
  │                 │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Media           │
  │ Processing      │────▶ Convert media if needed (format, size)
  │                 │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐     ┌─────────────────────────────────────────────┐
  │ Carrier API     │     │ Delivery Handling:                          │
  │ Integration     │────▶│ • Retry logic with exponential backoff      │
  │                 │     │ • Circuit breaker pattern                   │
  └────────┬────────┘     │ • Fallback carrier selection                │
           │              └─────────────────────────────────────────────┘
           ▼
  ┌─────────────────┐
  │ Status          │
  │ Tracking        │────▶ Store delivery status, trigger callbacks
  │                 │
  └─────────────────┘
```

### Outbound Message Schema

```typescript
// Outbound Message Request
interface OutboundMessageRequest {
  to: {
    phoneNumber: string;
    preferredCarrier?: CarrierType;
  };
  from: {
    phoneNumber?: string;
    senderId?: string;
  };
  content: {
    type: 'text' | 'template' | 'media' | 'interactive';
    text?: string;
    templateId?: string;
    templateParams?: Record<string, string>;
    mediaUrl?: string;
    buttons?: InteractiveButton[];
  };
  options?: {
    priority: 'high' | 'normal' | 'low';
    scheduledAt?: string;
    expireAt?: string;
    callbackUrl?: string;
  };
}

// Outbound Message Response
interface OutboundMessageResponse {
  messageId: string;
  status: 'queued' | 'sent' | 'delivered' | 'failed';
  carrier: CarrierType;
  carrierMessageId?: string;
  timestamp: string;
  estimatedDeliveryTime?: string;
}
```

### Carrier Selection Algorithm

```typescript
// Carrier Selection Logic
interface CarrierSelectionContext {
  recipient: string;
  messageType: string;
  conversationHistory?: ConversationHistory;
  carrierHealthStatus: Map<CarrierType, HealthStatus>;
}

async function selectOptimalCarrier(context: CarrierSelectionContext): Promise<CarrierType> {
  // Priority 1: Use same carrier as existing conversation
  if (context.conversationHistory?.lastCarrier) {
    const lastCarrier = context.conversationHistory.lastCarrier;
    if (isCarrierHealthy(lastCarrier, context.carrierHealthStatus)) {
      return lastCarrier;
    }
  }

  // Priority 2: Select based on phone number routing rules
  const routingCarrier = await getRoutingCarrier(context.recipient);
  if (routingCarrier && isCarrierHealthy(routingCarrier, context.carrierHealthStatus)) {
    return routingCarrier;
  }

  // Priority 3: Select based on message type capability
  const capableCarriers = getCarriersForMessageType(context.messageType);
  
  // Priority 4: Select based on cost and availability
  return selectByCostAndAvailability(capableCarriers, context.carrierHealthStatus);
}
```

---

## AWS Services Used

### Infrastructure Components

The omnichannel-omniservice leverages a comprehensive set of AWS services:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS INFRASTRUCTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  COMPUTE                           STORAGE                                   │
│  ───────                           ───────                                   │
│  ┌─────────────┐                   ┌─────────────┐                          │
│  │ AWS Lambda  │                   │  DynamoDB   │                          │
│  │ • Handlers  │                   │ • Messages  │                          │
│  │ • Workflows │                   │ • Sessions  │                          │
│  │ • Streams   │                   │ • Routes    │                          │
│  └─────────────┘                   └─────────────┘                          │
│                                                                              │
│  ┌─────────────┐                   ┌─────────────┐                          │
│  │ Step        │                   │     S3      │                          │
│  │ Functions   │                   │ • Media     │                          │
│  │ • Workflows │                   │ • Logs      │                          │
│  └─────────────┘                   │ • Backups   │                          │
│                                    └─────────────┘                          │
│                                                                              │
│  MESSAGING                         NETWORKING                               │
│  ─────────                         ──────────                               │
│  ┌─────────────┐                   ┌─────────────┐                          │
│  │    SQS      │                   │API Gateway  │                          │
│  │ • Queues    │                   │ • REST APIs │                          │
│  │ • DLQ       │                   │ • Webhooks  │                          │
│  └─────────────┘                   └─────────────┘                          │
│                                                                              │
│  ┌─────────────┐                   ┌─────────────┐                          │
│  │    SNS      │                   │   VPC       │                          │
│  │ • Topics    │                   │ • Subnets   │                          │
│  │ • Push      │                   │ • Security  │                          │
│  └─────────────┘                   └─────────────┘                          │
│                                                                              │
│  MONITORING                        SECURITY                                 │
│  ──────────                        ────────                                 │
│  ┌─────────────┐                   ┌─────────────┐                          │
│  │ CloudWatch  │                   │    IAM      │                          │
│  │ • Logs      │                   │ • Roles     │                          │
│  │ • Metrics   │                   │ • Policies  │                          │
│  │ • Alarms    │                   └─────────────┘                          │
│  └─────────────┘                                                            │
│                                    ┌─────────────┐                          │
│  ┌─────────────┐                   │  Secrets    │                          │
│  │  X-Ray      │                   │  Manager    │                          │
│  │ • Tracing   │                   │ • API Keys  │                          │
│  └─────────────┘                   └─────────────┘                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Details

| Service | Usage | Configuration |
|---------|-------|---------------|
| **AWS Lambda** | Message processing, webhook handlers, workflow steps | Node.js 18.x, 512MB-1024MB memory |
| **API Gateway** | REST API endpoints, webhook receivers | Regional deployment, throttling enabled |
| **DynamoDB** | Message storage, conversation state, routing rules | On-demand capacity, GSIs for queries |
| **S3** | Media storage, processed file cache | Lifecycle policies, cross-region replication |
| **SQS** | Message queuing, async processing | FIFO queues for order guarantee |
| **SNS** | Push notifications, event fanout | Topic-based routing |
| **Step Functions** | Complex workflow orchestration | Standard workflows |
| **CloudWatch** | Logging, metrics, alerting | Custom metrics, log insights |
| **Secrets Manager** | Carrier API credentials | Automatic rotation |
| **X-Ray** | Distributed tracing | Sampling rules configured |

### DynamoDB Table Design

```typescript
// Message Table Schema
interface MessageTable {
  // Partition Key
  conversationId: string;
  // Sort Key
  messageId: string;
  
  // Attributes
  direction: 'inbound' | 'outbound';
  carrier: CarrierType;
  sender: string;
  recipient: string;
  content: MessageContent;
  status: MessageStatus;
  timestamps: {
    created: string;
    sent?: string;
    delivered?: string;
    read?: string;
  };
  
  // GSI: carrier-timestamp-index
  // GSI: status-created-index
}

// Conversation Table Schema
interface ConversationTable {
  // Partition Key
  conversationId: string;
  
  // Attributes
  participants: string[];
  carrier: CarrierType;
  state: ConversationState;
  lastMessageAt: string;
  messageCount: number;
  metadata: Record<string, unknown>;
}
```

---

## Data Flow Diagrams

### Complete System Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE DATA FLOW DIAGRAM                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              EXTERNAL CARRIERS
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
    │WhatsApp │ │ Twilio  │ │Bandwidth│ │LiveChat │ │Msgbird  │ │Inteliq.  │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘
         │          │          │          │          │           │
         └────────┬─┴──────────┴──────────┴──────────┴───────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        API GATEWAY (WEBHOOKS)                            │
    │   /webhooks/whatsapp  /webhooks/twilio  /webhooks/bandwidth  etc.       │
    └─────────────────────────────────┬───────────────────────────────────────┘
                                      │
                  ┌───────────────────┴───────────────────┐
                  │                                       │
                  ▼                                       ▼
    ┌──────────────────────┐               ┌──────────────────────┐
    │  INBOUND LAMBDA      │               │  OUTBOUND LAMBDA     │
    │  ┌────────────────┐  │               │  ┌────────────────┐  │
    │  │ Validate       │  │               │  │ Route Request  │  │
    │  │ Parse          │  │               │  │ Select Carrier │  │
    │  │ Normalize      │  │               │  │ Format Message │  │
    │  └────────────────┘  │               │  └────────────────┘  │
    └──────────┬───────────┘               └──────────┬───────────┘
               │                                      │
               ▼                                      ▼
    ┌──────────────────────┐               ┌──────────────────────┐
    │      SQS QUEUES      │               │    CARRIER APIs      │
    │  ┌────────────────┐  │               │  ┌────────────────┐  │
    │  │ Inbound Queue  │  │               │  │ WhatsApp API   │  │
    │  │ Media Queue    │  │               │  │ Twilio API     │  │
    │  │ DLQ            │  │               │  │ Bandwidth API  │  │
    │  └────────────────┘  │               │  │ etc.           │  │
    └──────────┬───────────┘               │  └────────────────┘  │
               │                           └──────────────────────┘
               ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                     STEP FUNCTIONS                            │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
    │  │ Message     │  │ Media       │  │ Notification        │   │
    │  │ Processing  │──│ Conversion  │──│ Workflow            │   │
    │  │ Workflow    │  │ Workflow    │  │                     │   │
    │  └─────────────┘  └─────────────┘  └─────────────────────┘   │
    └──────────────────────────┬───────────────────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
    ┌────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │   DYNAMODB     │ │     S3      │ │      SNS        │
    │ ┌────────────┐ │ │ ┌─────────┐ │ │ ┌─────────────┐ │
    │ │ Messages   │ │ │ │ Media   │ │ │ │ Push        │ │
    │ │ Convos     │ │ │ │ Files   │ │ │ │ Notifications││
    │ │ Routes     │ │ │ │ Logs    │ │ │ │ Events      │ │
    │ └────────────┘ │ │ └─────────┘ │ │ └─────────────┘ │
    └───────┬────────┘ └─────────────┘ └─────────────────┘
            │
            ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                   DYNAMODB STREAMS                            │
    │          (Triggers downstream processing)                     │
    └──────────────────────────┬───────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    ┌────────────────────┐          ┌────────────────────┐
    │ Stream Processor   │          │ Analytics Pipeline │
    │ Lambda             │          │ (Future)           │
    └────────────────────┘          └────────────────────┘
```

### Media Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MEDIA PROCESSING FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │ Inbound Media   │
    │ (URL/Base64)    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐     ┌────────────────────────────────────────────┐
    │ Download/Decode │     │ Supported Formats:                         │
    │ Media           │────▶│ • Images: JPEG, PNG, GIF, WebP             │
    └────────┬────────┘     │ • Video: MP4, 3GP                          │
             │              │ • Audio: MP3, OGG, AMR                      │
             ▼              │ • Documents: PDF, DOC, XLS                  │
    ┌─────────────────┐     └────────────────────────────────────────────┘
    │ Validate        │
    │ • Size limits   │
    │ • Format check  │
    │ • Malware scan  │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Store Original  │
    │ in S3           │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐     ┌────────────────────────────────────────────┐
    │ Convert/Process │     │ Processing Options:                        │
    │ (if needed)     │────▶│ • Resize images for thumbnails             │
    └────────┬────────┘     │ • Transcode video for compatibility        │
             │              │ • Compress for size limits                 │
             ▼              └────────────────────────────────────────────┘
    ┌─────────────────┐
    │ Store Processed │
    │ Version in S3   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Generate        │
    │ Signed URL      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Return Media    │
    │ Reference       │
    └─────────────────┘
```

---

## Package Dependencies

### Monorepo Structure

The omnichannel-omniservice is organized as a monorepo with the following package structure:

```
omnichannel-omniservice/
├── packages/
│   ├── core/                    # Shared utilities and types
│   ├── carriers/                # Carrier integrations
│   │   ├── whatsapp/
│   │   ├── twilio/
│   │   ├── bandwidth/
│   │   ├── livechat/
│   │   ├── messagebird/
│   │   └── inteliquent/
│   ├── handlers/                # Lambda handlers
│   │   ├── inbound/
│   │   ├── outbound/
│   │   └── streams/
│   ├── workflows/               # Step Function definitions
│   ├── media/                   # Media processing
│   └── notifications/           # Push notification service
├── infrastructure/              # CDK/Terraform definitions
└── package.json                 # Root package.json
```

### Core Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.x",
    "@aws-sdk/client-s3": "^3.x",
    "@aws-sdk/client-sqs": "^3.x",
    "@aws-sdk/client-sns": "^3.x",
    "@aws-sdk/client-secrets-manager": "^3.x",
    "aws-lambda": "^1.x",
    "axios": "^1.x",
    "zod": "^3.x",
    "uuid": "^9.x",
    "winston": "^3.x"
  },
  "devDependencies": {
    "typescript": "^5.x",
    "eslint": "^8.x",
    "jest": "^29.x",
    "aws-cdk-lib": "^2.x"
  }
}
```

### Package Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PACKAGE DEPENDENCY GRAPH                                │
└─────────────────────────────────────────────────────────────────────────────┘

                            ┌───────────────┐
                            │    @core      │
                            │  (Base Types, │
                            │   Utilities)  │
                            └───────┬───────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │  @carriers/*  │       │   @handlers   │       │  @workflows   │
    │ (WhatsApp,    │       │  (Lambda      │       │ (Step         │
    │  Twilio, etc) │       │   Functions)  │       │  Functions)   │
    └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │    @media     │               │@notifications │
            │  (Processing) │               │   (Push)      │
            └───────────────┘               └───────────────┘
```

### Carrier Package Interfaces

Each carrier package implements a standard interface:

```typescript
// packages/core/src/interfaces/carrier.ts
interface CarrierAdapter {
  readonly name: CarrierType;
  readonly capabilities: CarrierCapabilities;
  
  // Inbound processing
  validateWebhook(payload: unknown, signature?: string): boolean;
  parseInboundMessage(payload: unknown): NormalizedMessage;
  
  // Outbound processing
  formatOutboundMessage(message: NormalizedMessage): unknown;
  sendMessage(message: unknown): Promise<CarrierResponse>;
  
  // Status handling
  getMessageStatus(messageId: string): Promise<MessageStatus>;
  parseStatusCallback(payload: unknown): StatusUpdate;
}

interface CarrierCapabilities {
  supportsText: boolean;
  supportsMedia: boolean;
  supportsTemplates: boolean;
  supportsInteractive: boolean;
  supportsLocation: boolean;
  maxMediaSize: number;
  supportedMediaTypes: string[];
}
```

---

## Summary

The omnichannel-omniservice architecture provides a robust, scalable foundation for multi-carrier messaging operations. Key architectural highlights include:

1. **Serverless-First Design**: Leveraging AWS Lambda and Step Functions for automatic scaling and cost efficiency
2. **Modular Carrier Integration**: Each carrier is isolated in its own package, enabling independent development and testing
3. **Unified Message Schema**: Normalized message format simplifies downstream processing and analytics
4. **Event-Driven Processing**: DynamoDB streams and SQS enable asynchronous, decoupled processing
5. **Comprehensive Observability**: CloudWatch and X-Ray integration for monitoring and debugging
6. **Security by Design**: Secrets Manager, IAM roles, and webhook signature validation protect the system

This architecture supports the current carrier integrations while providing clear extension points for adding new carriers and capabilities in the future.