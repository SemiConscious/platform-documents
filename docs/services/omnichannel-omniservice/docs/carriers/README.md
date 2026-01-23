# Carrier Integrations Overview

[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?style=flat-square&logo=aws-lambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

> **Omni Channel Service** - A TypeScript NodeJS monorepo implementing an omnichannel messaging pipeline that handles inbound/outbound message routing across multiple carriers (WhatsApp, Bandwidth, Twilio, LiveChat, Messagebird, Inteliquent) with AWS Lambda-based processing.

---

## Table of Contents

- [Overview](#overview)
- [Supported Carriers](#supported-carriers)
- [Carrier Capabilities Matrix](#carrier-capabilities-matrix)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Common Integration Patterns](#common-integration-patterns)
- [Adding New Carriers](#adding-new-carriers)
- [API Reference](#api-reference)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## Overview

The `omnichannel-omniservice` is a comprehensive messaging infrastructure that unifies communication across six major carriers into a single, consistent API. Whether you're sending SMS via Twilio, engaging customers on WhatsApp, or managing live chat sessions, this service provides a standardized interface for all your messaging needs.

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Carrier Support** | Seamless integration with WhatsApp, Twilio, Bandwidth, LiveChat, Messagebird, and Inteliquent |
| **Unified Message Routing** | Single pipeline for both inbound and outbound messages across all carriers |
| **Webhook Management** | Centralized webhook receivers for all carrier callbacks |
| **Media Handling** | Automatic media conversion and normalization across carriers |
| **Push Notifications** | Real-time notification delivery for message events |
| **DynamoDB Streams** | Event-driven processing for message state changes |
| **Modular Architecture** | Monorepo structure enabling independent carrier module development |

---

## Supported Carriers

The service currently supports **6 carriers** with varying capabilities:

### 1. WhatsApp Business API
The world's most popular messaging platform with rich media support, templates, and interactive messages.

### 2. Bandwidth
Enterprise-grade SMS/MMS and voice services with excellent deliverability and competitive pricing.

### 3. Twilio
Industry-leading communication platform with comprehensive SMS, MMS, and programmable messaging features.

### 4. LiveChat
Real-time customer service chat integration for web and mobile applications.

### 5. Messagebird
Global omnichannel communications platform with extensive international reach.

### 6. Inteliquent
Carrier-grade voice and messaging services for enterprise applications.

---

## Carrier Capabilities Matrix

| Capability | WhatsApp | Bandwidth | Twilio | LiveChat | Messagebird | Inteliquent |
|------------|:--------:|:---------:|:------:|:--------:|:-----------:|:-----------:|
| **SMS** | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **MMS** | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Rich Media** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Templates** | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| **Interactive Messages** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Delivery Reports** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Read Receipts** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Two-Way Messaging** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Webhooks** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Media Conversion** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

### Carrier-Specific Limits

| Carrier | Max Message Size | Media Size Limit | Rate Limit |
|---------|-----------------|------------------|------------|
| WhatsApp | 4,096 chars | 16 MB | 80 msg/sec |
| Bandwidth | 2,048 chars | 3.75 MB | 1 msg/sec |
| Twilio | 1,600 chars | 5 MB | 400 msg/sec |
| LiveChat | Unlimited | 10 MB | N/A |
| Messagebird | 1,000 chars | 1 MB | 30 msg/sec |
| Inteliquent | 160 chars | N/A | 10 msg/sec |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway / ALB                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │  Inbound  │   │  Outbound │   │  Webhook  │
            │  Handler  │   │  Handler  │   │ Receivers │
            └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                  │               │               │
                  └───────────────┼───────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │   Message Router Core   │
                    │   (Workflow Engine)     │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │WhatsApp │ │Bandwidth│ │ Twilio  │ │LiveChat │ │  More   │
   │ Carrier │ │ Carrier │ │ Carrier │ │ Carrier │ │Carriers │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │           │           │
        └───────────┴───────────┼───────────┴───────────┘
                                ▼
                    ┌─────────────────────────┐
                    │    DynamoDB Tables      │
                    │  (Messages, Sessions)   │
                    └─────────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Node.js** 18.x or higher
- **npm** 8.x or higher
- **Docker** (for containerized deployment)
- **AWS CLI** configured with appropriate credentials
- Access to at least one carrier account (for testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/omnichannel-omniservice.git
cd omnichannel-omniservice

# Install dependencies
npm install

# Bootstrap the monorepo
npm run bootstrap

# Build all packages
npm run build
```

### Environment Configuration

Create a `.env` file in the root directory:

```bash
# Core Configuration
NODE_ENV=development
AWS_REGION=us-east-1

# Carrier API Keys
WHATSAPP_API_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
BANDWIDTH_API_TOKEN=your_bandwidth_token
BANDWIDTH_API_SECRET=your_bandwidth_secret
BANDWIDTH_ACCOUNT_ID=your_account_id
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
LIVECHAT_LICENSE_ID=your_livechat_license
MESSAGEBIRD_API_KEY=your_messagebird_key
INTELIQUENT_API_KEY=your_inteliquent_key

# DynamoDB Configuration
DYNAMODB_TABLE_MESSAGES=omni-messages
DYNAMODB_TABLE_SESSIONS=omni-sessions
```

### Running Locally

```bash
# Start the development server
npm run dev

# Run with Docker
docker-compose up -d

# Run specific carrier module
npm run dev --workspace=@omni/carrier-whatsapp
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests for specific carrier
npm test --workspace=@omni/carrier-twilio

# Run integration tests
npm run test:integration
```

---

## Common Integration Patterns

### Pattern 1: Sending an Outbound Message

```typescript
import { MessageRouter } from '@omni/core';
import { OutboundMessage, CarrierType } from '@omni/types';

const router = new MessageRouter();

// Send a message through the unified interface
const message: OutboundMessage = {
  id: 'msg_123456',
  carrier: CarrierType.TWILIO,
  to: '+1234567890',
  from: '+0987654321',
  content: {
    type: 'text',
    body: 'Hello from Omnichannel Service!'
  },
  metadata: {
    campaignId: 'camp_001',
    priority: 'high'
  }
};

const result = await router.send(message);
console.log(`Message sent with ID: ${result.carrierId}`);
```

### Pattern 2: Handling Inbound Webhooks

```typescript
import { WebhookHandler } from '@omni/webhooks';
import { InboundMessage, CarrierType } from '@omni/types';

const webhookHandler = new WebhookHandler();

// Register carrier-specific webhook processors
webhookHandler.register(CarrierType.WHATSAPP, async (payload: any) => {
  const message: InboundMessage = {
    carrier: CarrierType.WHATSAPP,
    from: payload.from,
    to: payload.to,
    content: {
      type: payload.type,
      body: payload.text?.body || payload.media?.url
    },
    timestamp: new Date(payload.timestamp * 1000),
    rawPayload: payload
  };
  
  await processInboundMessage(message);
});

// Express route example
app.post('/webhooks/whatsapp', async (req, res) => {
  await webhookHandler.handle(CarrierType.WHATSAPP, req.body);
  res.status(200).send('OK');
});
```

### Pattern 3: Carrier-Agnostic Message Processing

```typescript
import { MessageProcessor, CarrierFactory } from '@omni/core';

class UnifiedMessageProcessor extends MessageProcessor {
  async process(message: InboundMessage): Promise<void> {
    // Normalize message across carriers
    const normalizedMessage = this.normalize(message);
    
    // Apply business logic
    const response = await this.generateResponse(normalizedMessage);
    
    // Send response through same carrier
    const carrier = CarrierFactory.create(message.carrier);
    await carrier.send({
      to: message.from,
      from: message.to,
      content: response
    });
  }
  
  private normalize(message: InboundMessage): NormalizedMessage {
    return {
      text: this.extractText(message),
      media: this.extractMedia(message),
      sender: message.from,
      channel: message.carrier,
      timestamp: message.timestamp
    };
  }
}
```

### Pattern 4: Media Conversion Pipeline

```typescript
import { MediaConverter } from '@omni/media';
import { CarrierType } from '@omni/types';

const converter = new MediaConverter();

// Convert media for target carrier compatibility
const convertedMedia = await converter.convert({
  sourceUrl: 'https://example.com/image.png',
  sourceCarrier: CarrierType.WHATSAPP,
  targetCarrier: CarrierType.BANDWIDTH,
  options: {
    maxSize: 3.75 * 1024 * 1024, // Bandwidth limit
    format: 'jpeg',
    quality: 85
  }
});
```

---

## Adding New Carriers

Follow this step-by-step guide to add a new carrier integration:

### Step 1: Create Carrier Package

```bash
# Create new package in packages directory
mkdir -p packages/carrier-newcarrier/src
cd packages/carrier-newcarrier

# Initialize package
npm init -y
```

### Step 2: Define Package Structure

```
packages/carrier-newcarrier/
├── src/
│   ├── index.ts
│   ├── client.ts
│   ├── webhook-handler.ts
│   ├── message-transformer.ts
│   └── types.ts
├── tests/
│   ├── client.test.ts
│   └── webhook-handler.test.ts
├── package.json
└── tsconfig.json
```

### Step 3: Implement the Carrier Interface

```typescript
// src/client.ts
import { 
  CarrierClient, 
  OutboundMessage, 
  SendResult,
  CarrierCapabilities 
} from '@omni/types';

export class NewCarrierClient implements CarrierClient {
  private apiKey: string;
  private baseUrl: string;
  
  constructor(config: NewCarrierConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://api.newcarrier.com';
  }
  
  async send(message: OutboundMessage): Promise<SendResult> {
    const transformedMessage = this.transformOutbound(message);
    
    const response = await fetch(`${this.baseUrl}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(transformedMessage)
    });
    
    const result = await response.json();
    
    return {
      success: response.ok,
      carrierId: result.id,
      timestamp: new Date(),
      rawResponse: result
    };
  }
  
  getCapabilities(): CarrierCapabilities {
    return {
      sms: true,
      mms: true,
      richMedia: false,
      templates: true,
      deliveryReports: true,
      readReceipts: false,
      maxMessageSize: 1600,
      maxMediaSize: 5 * 1024 * 1024
    };
  }
  
  private transformOutbound(message: OutboundMessage): any {
    // Transform to carrier-specific format
    return {
      destination: message.to,
      source: message.from,
      text: message.content.body,
      // ... carrier-specific fields
    };
  }
}
```

### Step 4: Implement Webhook Handler

```typescript
// src/webhook-handler.ts
import { WebhookProcessor, InboundMessage, CarrierType } from '@omni/types';

export class NewCarrierWebhookHandler implements WebhookProcessor {
  async process(payload: any): Promise<InboundMessage> {
    // Validate webhook signature
    this.validateSignature(payload);
    
    // Transform to normalized format
    return {
      carrier: CarrierType.NEW_CARRIER,
      from: payload.sender,
      to: payload.recipient,
      content: {
        type: this.mapContentType(payload.type),
        body: payload.message
      },
      timestamp: new Date(payload.timestamp),
      rawPayload: payload
    };
  }
  
  private validateSignature(payload: any): void {
    // Implement carrier-specific signature validation
  }
  
  private mapContentType(type: string): ContentType {
    const typeMap: Record<string, ContentType> = {
      'text': 'text',
      'image': 'image',
      'video': 'video',
      'audio': 'audio',
      'file': 'document'
    };
    return typeMap[type] || 'text';
  }
}
```

### Step 5: Register the Carrier

```typescript
// In packages/core/src/carrier-registry.ts
import { NewCarrierClient } from '@omni/carrier-newcarrier';

CarrierRegistry.register(CarrierType.NEW_CARRIER, {
  client: NewCarrierClient,
  webhookHandler: NewCarrierWebhookHandler,
  capabilities: {
    sms: true,
    mms: true,
    // ... define capabilities
  }
});
```

### Step 6: Add Tests

```typescript
// tests/client.test.ts
import { NewCarrierClient } from '../src/client';

describe('NewCarrierClient', () => {
  let client: NewCarrierClient;
  
  beforeEach(() => {
    client = new NewCarrierClient({
      apiKey: 'test-api-key'
    });
  });
  
  it('should send a text message', async () => {
    const result = await client.send({
      to: '+1234567890',
      from: '+0987654321',
      content: { type: 'text', body: 'Test message' }
    });
    
    expect(result.success).toBe(true);
    expect(result.carrierId).toBeDefined();
  });
});
```

---

## API Reference

The service exposes **16 endpoints** across multiple modules. Here are the key endpoints:

### Message Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/messages/send` | Send outbound message |
| `GET` | `/api/v1/messages/:id` | Get message by ID |
| `GET` | `/api/v1/messages/:id/status` | Get message delivery status |
| `POST` | `/api/v1/messages/bulk` | Send bulk messages |

### Webhook Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhooks/whatsapp` | WhatsApp webhook receiver |
| `POST` | `/webhooks/bandwidth` | Bandwidth webhook receiver |
| `POST` | `/webhooks/twilio` | Twilio webhook receiver |
| `POST` | `/webhooks/livechat` | LiveChat webhook receiver |
| `POST` | `/webhooks/messagebird` | Messagebird webhook receiver |
| `POST` | `/webhooks/inteliquent` | Inteliquent webhook receiver |

### Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/carriers` | List available carriers |
| `GET` | `/api/v1/carriers/:id/status` | Get carrier health status |
| `GET` | `/api/v1/health` | Service health check |

---

## Documentation

For detailed information about specific carriers and advanced topics, refer to the following documentation:

### Carrier-Specific Guides

- [WhatsApp Integration](docs/carriers/whatsapp.md) - Complete guide to WhatsApp Business API integration
- [Bandwidth Integration](docs/carriers/bandwidth.md) - Bandwidth SMS/MMS setup and configuration
- [Twilio Integration](docs/carriers/twilio.md) - Twilio programmable messaging integration
- [LiveChat Integration](docs/carriers/livechat.md) - LiveChat real-time messaging setup

### Additional Resources

- [API Documentation](docs/api/README.md) - Complete API reference with examples
- [Data Models](docs/models/README.md) - Overview of 100+ data models
- [Deployment Guide](docs/deployment/README.md) - AWS Lambda and Docker deployment
- [Security Guide](docs/security/README.md) - Authentication and webhook verification

---

## Troubleshooting

### Common Issues

#### 1. Webhook Signature Validation Failures

```bash
Error: Invalid webhook signature for carrier: whatsapp
```

**Solution:** Ensure your webhook secret is correctly configured:
```bash
# Verify environment variable
echo $WHATSAPP_WEBHOOK_SECRET

# Regenerate webhook secret in WhatsApp Business Manager
```

#### 2. Rate Limiting Errors

```bash
Error: Rate limit exceeded for carrier: twilio (429)
```

**Solution:** Implement exponential backoff or use the built-in queue:
```typescript
const router = new MessageRouter({
  rateLimiting: {
    enabled: true,
    strategy: 'queue',
    maxRetries: 3
  }
});
```

#### 3. Media Conversion Timeouts

```bash
Error: Media conversion timeout after 30000ms
```

**Solution:** Increase timeout or optimize media before sending:
```typescript
const converter = new MediaConverter({
  timeout: 60000, // 60 seconds
  maxConcurrent: 5
});
```

#### 4. DynamoDB Stream Processing Delays

If messages are not being processed in real-time:

```bash
# Check stream status
aws dynamodb describe-table --table-name omni-messages

# Verify Lambda trigger
aws lambda list-event-source-mappings --function-name omni-stream-processor
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code style and standards
- Pull request process
- Testing requirements
- Carrier integration guidelines

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>Built with ❤️ by the Omnichannel Team</strong>
</p>