# omnichannel-omniservice

[![Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18.x-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)

> **Omni Channel Service** - A TypeScript NodeJS monorepo implementing an omnichannel messaging pipeline that handles inbound/outbound message routing across multiple carriers (WhatsApp, Bandwidth, Twilio, LiveChat, Messagebird, Inteliquent) with AWS Lambda-based processing.

---

## Table of Contents

- [Overview](#overview)
- [Lambda Architecture](#lambda-architecture)
- [Function Categories](#function-categories)
- [Receive Lambdas](#receive-lambdas)
- [Router Lambdas](#router-lambdas)
- [Workflow Lambdas](#workflow-lambdas)
- [Utility Lambdas](#utility-lambdas)
- [Common Patterns](#common-patterns)
- [Quick Start](#quick-start)
- [Documentation](#documentation)

---

## Overview

The omnichannel-omniservice is a comprehensive messaging infrastructure built on AWS Lambda that enables seamless communication across multiple carriers and channels. This service acts as a unified messaging gateway, abstracting the complexity of individual carrier APIs while providing consistent message handling, routing, and workflow processing.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Carrier Support** | WhatsApp, Twilio, Bandwidth, LiveChat, Messagebird, Inteliquent |
| **Bidirectional Messaging** | Full inbound and outbound message routing pipeline |
| **Webhook Integration** | Dedicated receivers for each carrier's webhook events |
| **Workflow Processing** | Flexible workflow-based message handling and transformation |
| **Push Notifications** | Cross-platform notification delivery |
| **Media Handling** | Automatic media conversion across carrier formats |
| **Stream Processing** | DynamoDB stream-triggered event processing |

---

## Lambda Architecture

The omnichannel-omniservice employs a modular, event-driven architecture using AWS Lambda functions organized in a monorepo structure. Each Lambda function serves a specific purpose within the messaging pipeline.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INBOUND MESSAGE FLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│   │ WhatsApp │    │  Twilio  │    │Bandwidth │    │ LiveChat │        │
│   │ Webhook  │    │ Webhook  │    │ Webhook  │    │ Webhook  │        │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘        │
│        │               │               │               │               │
│        └───────────────┴───────┬───────┴───────────────┘               │
│                                ▼                                        │
│                    ┌───────────────────────┐                           │
│                    │   RECEIVE LAMBDAS     │                           │
│                    │  (Carrier-specific)   │                           │
│                    └───────────┬───────────┘                           │
│                                ▼                                        │
│                    ┌───────────────────────┐                           │
│                    │    ROUTER LAMBDAS     │                           │
│                    │  (Message routing)    │                           │
│                    └───────────┬───────────┘                           │
│                                ▼                                        │
│                    ┌───────────────────────┐                           │
│                    │   WORKFLOW LAMBDAS    │                           │
│                    │ (Business logic)      │                           │
│                    └───────────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Single Responsibility**: Each Lambda handles one specific task
2. **Event-Driven**: Functions are triggered by events (HTTP, SQS, DynamoDB streams)
3. **Stateless Design**: All state is externalized to DynamoDB
4. **Carrier Abstraction**: Unified internal message format across all carriers
5. **Fault Tolerance**: Built-in retry mechanisms and dead-letter queues

---

## Function Categories

The Lambda functions are organized into four primary categories based on their role in the messaging pipeline:

| Category | Purpose | Trigger Types | Count |
|----------|---------|---------------|-------|
| **Receive** | Ingest messages from carrier webhooks | API Gateway, ALB | 6 |
| **Router** | Route messages to appropriate handlers | SQS, SNS | 4 |
| **Workflow** | Execute business logic and transformations | Step Functions, SQS | 5 |
| **Utility** | Support functions (media, notifications) | Various | 3 |

---

## Receive Lambdas

Receive Lambdas are the entry points for inbound messages from external carriers. Each carrier has a dedicated receive Lambda to handle its specific webhook format and authentication requirements.

### Available Receive Functions

```typescript
// packages/pipeline/src/lambdas/receive/

├── whatsapp-receive.ts      // WhatsApp Business API webhooks
├── twilio-receive.ts        // Twilio SMS/MMS webhooks
├── bandwidth-receive.ts     // Bandwidth messaging webhooks
├── livechat-receive.ts      // LiveChat event webhooks
├── messagebird-receive.ts   // Messagebird webhooks
└── inteliquent-receive.ts   // Inteliquent carrier webhooks
```

### Receive Lambda Structure

```typescript
// Example: WhatsApp Receive Lambda
import { APIGatewayProxyHandler } from 'aws-lambda';
import { WhatsAppWebhookParser } from '../parsers/whatsapp';
import { MessageNormalizer } from '../normalizers/message';
import { InboundQueue } from '../queues/inbound';

export const handler: APIGatewayProxyHandler = async (event) => {
  // 1. Validate webhook signature
  const isValid = await WhatsAppWebhookParser.validateSignature(event);
  if (!isValid) {
    return { statusCode: 401, body: 'Invalid signature' };
  }

  // 2. Parse carrier-specific payload
  const rawMessage = WhatsAppWebhookParser.parse(event.body);

  // 3. Normalize to internal format
  const normalizedMessage = MessageNormalizer.normalize(rawMessage, 'whatsapp');

  // 4. Enqueue for routing
  await InboundQueue.enqueue(normalizedMessage);

  return { statusCode: 200, body: 'OK' };
};
```

### Webhook Endpoints

| Carrier | Endpoint | Method | Authentication |
|---------|----------|--------|----------------|
| WhatsApp | `/webhooks/whatsapp` | POST | Signature Verification |
| Twilio | `/webhooks/twilio` | POST | Request Validation |
| Bandwidth | `/webhooks/bandwidth` | POST | Basic Auth |
| LiveChat | `/webhooks/livechat` | POST | API Key |
| Messagebird | `/webhooks/messagebird` | POST | Signature |
| Inteliquent | `/webhooks/inteliquent` | POST | IP Whitelist |

📖 **See [Receive Lambda Functions](docs/lambdas/receive-lambdas.md) for detailed documentation.**

---

## Router Lambdas

Router Lambdas determine the destination and handling path for messages based on configuration rules, message content, and tenant settings.

### Router Function Types

```typescript
// packages/pipeline/src/lambdas/router/

├── inbound-router.ts        // Routes incoming messages to workflows
├── outbound-router.ts       // Routes outgoing messages to carriers
├── carrier-selector.ts      // Selects optimal carrier for delivery
└── failover-router.ts       // Handles carrier failover scenarios
```

### Routing Decision Flow

```typescript
// Example: Inbound Router Lambda
import { SQSHandler } from 'aws-lambda';
import { RoutingEngine } from '../routing/engine';
import { TenantConfig } from '../config/tenant';

export const handler: SQSHandler = async (event) => {
  for (const record of event.Records) {
    const message = JSON.parse(record.body);
    
    // Load tenant-specific routing rules
    const tenantConfig = await TenantConfig.load(message.tenantId);
    
    // Determine routing destination
    const route = await RoutingEngine.evaluate({
      message,
      rules: tenantConfig.routingRules,
      context: {
        carrier: message.sourceCarrier,
        messageType: message.type,
        metadata: message.metadata
      }
    });
    
    // Dispatch to appropriate workflow
    await route.dispatch(message);
  }
};
```

### Routing Rules Configuration

```json
{
  "routingRules": [
    {
      "name": "keyword-routing",
      "conditions": [
        { "field": "body", "operator": "contains", "value": "HELP" }
      ],
      "destination": "support-workflow"
    },
    {
      "name": "default-routing",
      "conditions": [],
      "destination": "standard-workflow"
    }
  ]
}
```

📖 **See [Router Lambda Functions](docs/lambdas/router-lambdas.md) for detailed documentation.**

---

## Workflow Lambdas

Workflow Lambdas implement the core business logic for message processing, including transformations, enrichment, and delivery coordination.

### Workflow Function Types

```typescript
// packages/pipeline/src/lambdas/workflow/

├── message-processor.ts     // Core message processing logic
├── media-transformer.ts     // Media format conversion
├── notification-sender.ts   // Push notification dispatch
├── delivery-coordinator.ts  // Manages delivery attempts
└── stream-processor.ts      // DynamoDB stream event handler
```

### Message Processing Pipeline

```typescript
// Example: Message Processor Lambda
import { StepFunctionHandler } from '../types/stepfunction';
import { MessageEnricher } from '../enrichers/message';
import { ContentFilter } from '../filters/content';
import { DeliveryService } from '../services/delivery';

interface ProcessorInput {
  message: NormalizedMessage;
  workflow: WorkflowConfig;
  context: ProcessingContext;
}

export const handler: StepFunctionHandler<ProcessorInput> = async (input) => {
  const { message, workflow, context } = input;

  // Step 1: Enrich message with additional data
  const enrichedMessage = await MessageEnricher.enrich(message, {
    includeUserProfile: workflow.enrichment.userProfile,
    includeConversationHistory: workflow.enrichment.history,
    lookupContactInfo: workflow.enrichment.contactLookup
  });

  // Step 2: Apply content filters
  const filteredMessage = await ContentFilter.apply(enrichedMessage, {
    profanityFilter: workflow.filters.profanity,
    piiRedaction: workflow.filters.pii,
    spamDetection: workflow.filters.spam
  });

  // Step 3: Execute workflow-specific transformations
  const transformedMessage = await workflow.transform(filteredMessage);

  // Step 4: Coordinate delivery
  const deliveryResult = await DeliveryService.deliver(transformedMessage, {
    priority: context.priority,
    retryPolicy: workflow.delivery.retryPolicy,
    timeout: workflow.delivery.timeout
  });

  return {
    success: deliveryResult.success,
    messageId: transformedMessage.id,
    deliveryId: deliveryResult.id
  };
};
```

📖 **See [Workflow Lambda Functions](docs/lambdas/workflow-lambdas.md) for detailed documentation.**

---

## Utility Lambdas

Utility Lambdas provide supporting functionality for the core messaging pipeline.

### Media Conversion Lambda

Handles media format conversion between carriers:

```typescript
// packages/pipeline/src/lambdas/utility/media-converter.ts

import { S3Handler } from 'aws-lambda';
import { MediaConverter } from '../media/converter';

export const handler: S3Handler = async (event) => {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = record.s3.object.key;
    
    // Determine target format from metadata
    const metadata = await getObjectMetadata(bucket, key);
    const targetCarrier = metadata['x-target-carrier'];
    
    // Convert to carrier-compatible format
    await MediaConverter.convert({
      source: { bucket, key },
      targetFormat: getCarrierMediaFormat(targetCarrier),
      outputBucket: process.env.CONVERTED_MEDIA_BUCKET
    });
  }
};
```

### Push Notification Lambda

Delivers push notifications across platforms:

```typescript
// packages/pipeline/src/lambdas/utility/push-notification.ts

import { SNSHandler } from 'aws-lambda';
import { PushService } from '../services/push';

export const handler: SNSHandler = async (event) => {
  for (const record of event.Records) {
    const notification = JSON.parse(record.Sns.Message);
    
    await PushService.send({
      userId: notification.userId,
      title: notification.title,
      body: notification.body,
      data: notification.payload,
      platforms: ['ios', 'android', 'web']
    });
  }
};
```

---

## Common Patterns

### Error Handling Pattern

All Lambdas implement consistent error handling:

```typescript
import { Logger } from '../logging/logger';
import { ErrorHandler } from '../errors/handler';
import { DeadLetterQueue } from '../queues/dlq';

export const withErrorHandling = <T extends (...args: any[]) => Promise<any>>(
  handler: T,
  options: ErrorHandlingOptions
): T => {
  return (async (...args: Parameters<T>) => {
    const logger = Logger.create({ lambdaName: options.lambdaName });
    
    try {
      return await handler(...args);
    } catch (error) {
      logger.error('Lambda execution failed', { error });
      
      if (ErrorHandler.isRetryable(error)) {
        throw error; // Let Lambda retry
      }
      
      // Send to DLQ for non-retryable errors
      await DeadLetterQueue.send({
        error,
        input: args,
        lambdaName: options.lambdaName,
        timestamp: new Date().toISOString()
      });
      
      return options.defaultResponse;
    }
  }) as T;
};
```

### Message Normalization Pattern

```typescript
// Internal normalized message format
interface NormalizedMessage {
  id: string;
  tenantId: string;
  sourceCarrier: CarrierType;
  direction: 'inbound' | 'outbound';
  from: ContactInfo;
  to: ContactInfo;
  body: string;
  mediaUrls?: string[];
  metadata: Record<string, unknown>;
  timestamp: string;
  originalPayload: unknown;
}
```

### Idempotency Pattern

```typescript
import { IdempotencyStore } from '../stores/idempotency';

export const withIdempotency = async <T>(
  key: string,
  operation: () => Promise<T>
): Promise<T> => {
  // Check if already processed
  const existing = await IdempotencyStore.get(key);
  if (existing) {
    return existing.result as T;
  }
  
  // Execute operation
  const result = await operation();
  
  // Store result for future deduplication
  await IdempotencyStore.set(key, { result }, { ttl: 24 * 60 * 60 });
  
  return result;
};
```

---

## Quick Start

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher
- Docker and Docker Compose
- AWS CLI configured with appropriate credentials
- AWS SAM CLI (for local Lambda testing)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd omnichannel-omniservice

# Install dependencies
npm install

# Bootstrap the monorepo
npm run bootstrap

# Build all packages
npm run build
```

### Local Development

```bash
# Start local DynamoDB
docker-compose up -d dynamodb-local

# Run Lambda locally with SAM
npm run lambda:local -- --function whatsapp-receive

# Run all tests
npm test

# Run tests with coverage
npm run test:coverage
```

### Docker Development

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up

# View logs
docker-compose logs -f pipeline
```

### Deploying

```bash
# Deploy to development
npm run deploy:dev

# Deploy to staging
npm run deploy:staging

# Deploy to production
npm run deploy:prod
```

---

## Documentation

### Lambda Documentation

| Document | Description |
|----------|-------------|
| [Receive Lambda Functions](docs/lambdas/receive-lambdas.md) | Detailed documentation for all carrier webhook receivers |
| [Router Lambda Functions](docs/lambdas/router-lambdas.md) | Message routing logic and configuration |
| [Workflow Lambda Functions](docs/lambdas/workflow-lambdas.md) | Business logic and processing workflows |

### API Reference

This service exposes **16 endpoints** across the various carrier integrations and supports **100 data models** for comprehensive message handling.

### Additional Resources

- **Architecture Decisions**: See `docs/architecture/` for ADRs
- **Carrier Integration Guides**: See `docs/carriers/` for carrier-specific setup
- **Deployment Guide**: See `docs/deployment/` for infrastructure details
- **Troubleshooting**: See `docs/troubleshooting/` for common issues

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is proprietary software. All rights reserved.