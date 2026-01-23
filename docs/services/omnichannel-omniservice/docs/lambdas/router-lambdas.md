# Router Lambda Functions

## Overview

The Router Lambda Functions form the core message routing layer of the omnichannel-omniservice system. These Lambda functions are responsible for intelligently directing messages between multiple carriers, internal services, and end-users across various communication channels including WhatsApp, Bandwidth, Twilio, LiveChat, Messagebird, and Inteliquent.

The routing architecture follows an event-driven design pattern where each Lambda function handles specific routing responsibilities:

- **routerInbound**: Processes incoming messages from all carrier webhooks and routes them to appropriate internal handlers
- **routerOutbound**: Manages outgoing message dispatch to the correct carrier based on channel and recipient configuration
- **routerWhatsApp**: Specialized router for WhatsApp-specific message handling, including template messages and media

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           External Carriers                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐         │
│  │ WhatsApp │ │ Twilio   │ │Bandwidth │ │LiveChat  │ │Messagebird │         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘         │
└───────┼────────────┼────────────┼────────────┼─────────────┼────────────────┘
        │            │            │            │             │
        └────────────┴────────────┴─────┬──────┴─────────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   routerInbound   │
                              │      Lambda       │
                              └─────────┬─────────┘
                                        │
                              ┌─────────▼─────────┐
                              │  Message Queue /  │
                              │  Internal Services│
                              └─────────┬─────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   routerOutbound  │
                              │      Lambda       │
                              └─────────┬─────────┘
                                        │
        ┌────────────┬────────────┬─────┴──────┬─────────────┐
        │            │            │            │             │
        ▼            ▼            ▼            ▼             ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ WhatsApp │ │ Twilio   │ │Bandwidth │ │LiveChat  │ │Messagebird│
   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## routerInbound

The `routerInbound` Lambda function serves as the primary entry point for all incoming messages from external carriers. It normalizes diverse carrier-specific message formats into a unified internal schema and routes them to appropriate downstream processors.

### Function Configuration

```yaml
# serverless.yml configuration
routerInbound:
  handler: src/lambdas/router/inbound/handler.main
  memorySize: 512
  timeout: 30
  events:
    - sqs:
        arn: !GetAtt InboundMessageQueue.Arn
        batchSize: 10
        maximumBatchingWindow: 5
  environment:
    ROUTING_TABLE: !Ref RoutingConfigTable
    MESSAGE_STORE_TABLE: !Ref MessageStoreTable
```

### Handler Implementation

```typescript
// src/lambdas/router/inbound/handler.ts
import { SQSEvent, SQSHandler, SQSRecord } from 'aws-lambda';
import { CarrierMessage, NormalizedMessage, RoutingDecision } from '@omni/types';
import { MessageNormalizer } from '@omni/normalizers';
import { RoutingEngine } from '@omni/routing';
import { MessageStore } from '@omni/storage';
import { Logger } from '@omni/logger';

const logger = new Logger('routerInbound');
const normalizer = new MessageNormalizer();
const routingEngine = new RoutingEngine();
const messageStore = new MessageStore();

export const main: SQSHandler = async (event: SQSEvent): Promise<void> => {
  const processingResults = await Promise.allSettled(
    event.Records.map(processInboundRecord)
  );

  const failures = processingResults.filter(
    (result): result is PromiseRejectedResult => result.status === 'rejected'
  );

  if (failures.length > 0) {
    logger.error('Partial batch failure', { 
      failedCount: failures.length,
      totalCount: event.Records.length 
    });
    throw new Error(`Failed to process ${failures.length} records`);
  }
};

async function processInboundRecord(record: SQSRecord): Promise<void> {
  const carrierMessage: CarrierMessage = JSON.parse(record.body);
  
  logger.info('Processing inbound message', {
    messageId: carrierMessage.messageId,
    carrier: carrierMessage.carrier,
    channel: carrierMessage.channel
  });

  // Step 1: Normalize the carrier-specific message
  const normalizedMessage: NormalizedMessage = await normalizer.normalize(
    carrierMessage
  );

  // Step 2: Persist the message
  await messageStore.save({
    ...normalizedMessage,
    direction: 'inbound',
    status: 'received',
    receivedAt: new Date().toISOString()
  });

  // Step 3: Determine routing
  const routingDecision: RoutingDecision = await routingEngine.determineRoute(
    normalizedMessage
  );

  // Step 4: Forward to appropriate handler
  await forwardMessage(normalizedMessage, routingDecision);
}
```

### Message Normalization

The normalizer transforms carrier-specific payloads into a unified format:

```typescript
// src/normalizers/message-normalizer.ts
import { CarrierMessage, NormalizedMessage, Carrier } from '@omni/types';
import { WhatsAppNormalizer } from './whatsapp-normalizer';
import { TwilioNormalizer } from './twilio-normalizer';
import { BandwidthNormalizer } from './bandwidth-normalizer';
import { LiveChatNormalizer } from './livechat-normalizer';
import { MessagebirdNormalizer } from './messagebird-normalizer';
import { InteliquentNormalizer } from './inteliquent-normalizer';

export class MessageNormalizer {
  private normalizers: Map<Carrier, CarrierNormalizer>;

  constructor() {
    this.normalizers = new Map([
      ['whatsapp', new WhatsAppNormalizer()],
      ['twilio', new TwilioNormalizer()],
      ['bandwidth', new BandwidthNormalizer()],
      ['livechat', new LiveChatNormalizer()],
      ['messagebird', new MessagebirdNormalizer()],
      ['inteliquent', new InteliquentNormalizer()]
    ]);
  }

  async normalize(message: CarrierMessage): Promise<NormalizedMessage> {
    const normalizer = this.normalizers.get(message.carrier);
    
    if (!normalizer) {
      throw new Error(`Unsupported carrier: ${message.carrier}`);
    }

    return normalizer.normalize(message);
  }
}
```

### Input Schema

```typescript
// src/types/carrier-message.ts
export interface CarrierMessage {
  messageId: string;
  carrier: Carrier;
  channel: Channel;
  rawPayload: Record<string, unknown>;
  receivedAt: string;
  webhookId: string;
}

export type Carrier = 
  | 'whatsapp' 
  | 'twilio' 
  | 'bandwidth' 
  | 'livechat' 
  | 'messagebird' 
  | 'inteliquent';

export type Channel = 'sms' | 'mms' | 'whatsapp' | 'webchat' | 'voice';
```

### Output Schema

```typescript
// src/types/normalized-message.ts
export interface NormalizedMessage {
  id: string;
  conversationId: string;
  sender: MessageParticipant;
  recipient: MessageParticipant;
  content: MessageContent;
  metadata: MessageMetadata;
  carrier: Carrier;
  channel: Channel;
  timestamp: string;
}

export interface MessageParticipant {
  id: string;
  type: 'user' | 'agent' | 'bot' | 'system';
  phoneNumber?: string;
  email?: string;
  displayName?: string;
}

export interface MessageContent {
  type: 'text' | 'media' | 'template' | 'interactive' | 'location';
  text?: string;
  media?: MediaContent[];
  template?: TemplateContent;
  interactive?: InteractiveContent;
  location?: LocationContent;
}
```

---

## routerOutbound

The `routerOutbound` Lambda function handles all outgoing message dispatch. It selects the appropriate carrier based on configuration rules, transforms messages into carrier-specific formats, and manages delivery tracking.

### Function Configuration

```yaml
# serverless.yml configuration
routerOutbound:
  handler: src/lambdas/router/outbound/handler.main
  memorySize: 1024
  timeout: 60
  events:
    - sqs:
        arn: !GetAtt OutboundMessageQueue.Arn
        batchSize: 5
        maximumBatchingWindow: 2
  environment:
    CARRIER_CONFIG_TABLE: !Ref CarrierConfigTable
    RATE_LIMIT_TABLE: !Ref RateLimitTable
```

### Handler Implementation

```typescript
// src/lambdas/router/outbound/handler.ts
import { SQSEvent, SQSHandler } from 'aws-lambda';
import { OutboundMessage, DeliveryResult, CarrierConfig } from '@omni/types';
import { CarrierSelector } from '@omni/routing';
import { CarrierClientFactory } from '@omni/carriers';
import { RateLimiter } from '@omni/rate-limiting';
import { DeliveryTracker } from '@omni/tracking';
import { Logger } from '@omni/logger';

const logger = new Logger('routerOutbound');
const carrierSelector = new CarrierSelector();
const clientFactory = new CarrierClientFactory();
const rateLimiter = new RateLimiter();
const deliveryTracker = new DeliveryTracker();

export const main: SQSHandler = async (event: SQSEvent): Promise<void> => {
  for (const record of event.Records) {
    const outboundMessage: OutboundMessage = JSON.parse(record.body);
    
    try {
      await processOutboundMessage(outboundMessage);
    } catch (error) {
      logger.error('Failed to process outbound message', {
        messageId: outboundMessage.id,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }
};

async function processOutboundMessage(message: OutboundMessage): Promise<void> {
  logger.info('Processing outbound message', {
    messageId: message.id,
    channel: message.channel,
    recipientId: message.recipient.id
  });

  // Step 1: Select optimal carrier
  const carrierConfig: CarrierConfig = await carrierSelector.selectCarrier({
    channel: message.channel,
    recipientCountry: message.recipient.country,
    messageType: message.content.type,
    priority: message.priority
  });

  // Step 2: Check rate limits
  const rateLimitResult = await rateLimiter.checkLimit({
    carrier: carrierConfig.carrier,
    accountId: carrierConfig.accountId,
    channel: message.channel
  });

  if (!rateLimitResult.allowed) {
    logger.warn('Rate limit exceeded, requeueing message', {
      messageId: message.id,
      retryAfter: rateLimitResult.retryAfter
    });
    await requeueWithDelay(message, rateLimitResult.retryAfter);
    return;
  }

  // Step 3: Transform and send
  const carrierClient = clientFactory.getClient(carrierConfig.carrier);
  const transformedPayload = await carrierClient.transformMessage(message);
  
  const deliveryResult: DeliveryResult = await carrierClient.send(
    transformedPayload,
    carrierConfig
  );

  // Step 4: Track delivery
  await deliveryTracker.recordDelivery({
    messageId: message.id,
    carrier: carrierConfig.carrier,
    carrierMessageId: deliveryResult.carrierMessageId,
    status: deliveryResult.status,
    sentAt: new Date().toISOString()
  });
}
```

### Carrier Selection Logic

```typescript
// src/routing/carrier-selector.ts
import { CarrierConfig, CarrierSelectionCriteria, CarrierScore } from '@omni/types';
import { CarrierConfigRepository } from '@omni/repositories';
import { CarrierHealthChecker } from '@omni/health';

export class CarrierSelector {
  private configRepo: CarrierConfigRepository;
  private healthChecker: CarrierHealthChecker;

  constructor() {
    this.configRepo = new CarrierConfigRepository();
    this.healthChecker = new CarrierHealthChecker();
  }

  async selectCarrier(criteria: CarrierSelectionCriteria): Promise<CarrierConfig> {
    // Get all available carriers for the channel
    const availableCarriers = await this.configRepo.getCarriersForChannel(
      criteria.channel
    );

    // Filter by capability and region
    const eligibleCarriers = availableCarriers.filter(carrier => 
      this.meetsRequirements(carrier, criteria)
    );

    if (eligibleCarriers.length === 0) {
      throw new Error(`No eligible carriers for criteria: ${JSON.stringify(criteria)}`);
    }

    // Score and rank carriers
    const scoredCarriers: CarrierScore[] = await Promise.all(
      eligibleCarriers.map(async carrier => ({
        carrier,
        score: await this.calculateScore(carrier, criteria)
      }))
    );

    // Sort by score (highest first)
    scoredCarriers.sort((a, b) => b.score - a.score);

    // Return highest-scoring healthy carrier
    for (const { carrier } of scoredCarriers) {
      const isHealthy = await this.healthChecker.isHealthy(carrier.carrier);
      if (isHealthy) {
        return carrier;
      }
    }

    throw new Error('No healthy carriers available');
  }

  private async calculateScore(
    carrier: CarrierConfig, 
    criteria: CarrierSelectionCriteria
  ): Promise<number> {
    let score = 0;

    // Base score from carrier priority
    score += carrier.priority * 10;

    // Cost optimization
    const costScore = 100 - (carrier.costPerMessage * 10);
    score += costScore;

    // Delivery rate bonus
    const deliveryRate = await this.getDeliveryRate(carrier.carrier);
    score += deliveryRate * 50;

    // Latency penalty
    const avgLatency = await this.getAverageLatency(carrier.carrier);
    score -= avgLatency / 100;

    // Priority boost for urgent messages
    if (criteria.priority === 'high' && carrier.supportsHighPriority) {
      score += 20;
    }

    return score;
  }
}
```

### Input Schema

```typescript
// src/types/outbound-message.ts
export interface OutboundMessage {
  id: string;
  conversationId: string;
  sender: MessageParticipant;
  recipient: OutboundRecipient;
  content: MessageContent;
  channel: Channel;
  priority: 'low' | 'normal' | 'high';
  scheduledAt?: string;
  expiresAt?: string;
  metadata: OutboundMetadata;
}

export interface OutboundRecipient extends MessageParticipant {
  country: string;
  timezone?: string;
  preferredCarrier?: Carrier;
  optInStatus: OptInStatus;
}

export interface OutboundMetadata {
  campaignId?: string;
  templateId?: string;
  source: 'api' | 'workflow' | 'agent' | 'bot';
  retryCount: number;
  maxRetries: number;
}
```

---

## routerWhatsApp

The `routerWhatsApp` Lambda function provides specialized handling for WhatsApp messages, including template message management, media handling, and WhatsApp Business API-specific features.

### Function Configuration

```yaml
# serverless.yml configuration
routerWhatsApp:
  handler: src/lambdas/router/whatsapp/handler.main
  memorySize: 1024
  timeout: 45
  events:
    - sqs:
        arn: !GetAtt WhatsAppMessageQueue.Arn
        batchSize: 10
  environment:
    WHATSAPP_BUSINESS_API_URL: ${ssm:/omni/whatsapp/api-url}
    WHATSAPP_ACCESS_TOKEN: ${ssm:/omni/whatsapp/access-token~true}
    TEMPLATE_CACHE_TABLE: !Ref TemplateCacheTable
```

### Handler Implementation

```typescript
// src/lambdas/router/whatsapp/handler.ts
import { SQSEvent, SQSHandler } from 'aws-lambda';
import { WhatsAppMessage, WhatsAppResponse, SessionWindow } from '@omni/types';
import { WhatsAppClient } from '@omni/carriers/whatsapp';
import { SessionManager } from '@omni/session';
import { TemplateManager } from '@omni/templates';
import { MediaProcessor } from '@omni/media';
import { Logger } from '@omni/logger';

const logger = new Logger('routerWhatsApp');
const whatsAppClient = new WhatsAppClient();
const sessionManager = new SessionManager();
const templateManager = new TemplateManager();
const mediaProcessor = new MediaProcessor();

export const main: SQSHandler = async (event: SQSEvent): Promise<void> => {
  for (const record of event.Records) {
    const message: WhatsAppMessage = JSON.parse(record.body);
    await routeWhatsAppMessage(message);
  }
};

async function routeWhatsAppMessage(message: WhatsAppMessage): Promise<void> {
  const recipientPhone = message.recipient.phoneNumber;
  
  // Check 24-hour session window
  const session: SessionWindow = await sessionManager.getSession(recipientPhone);
  
  if (session.isWithinWindow) {
    // Can send any message type within session window
    await sendSessionMessage(message);
  } else {
    // Must use approved template outside session window
    await sendTemplateMessage(message);
  }
}

async function sendSessionMessage(message: WhatsAppMessage): Promise<void> {
  logger.info('Sending session message', {
    messageId: message.id,
    recipientPhone: message.recipient.phoneNumber
  });

  let payload: WhatsAppAPIPayload;

  switch (message.content.type) {
    case 'text':
      payload = buildTextPayload(message);
      break;
    case 'media':
      payload = await buildMediaPayload(message);
      break;
    case 'interactive':
      payload = buildInteractivePayload(message);
      break;
    case 'location':
      payload = buildLocationPayload(message);
      break;
    default:
      throw new Error(`Unsupported message type: ${message.content.type}`);
  }

  const response = await whatsAppClient.sendMessage(payload);
  await handleResponse(message.id, response);
}

async function sendTemplateMessage(message: WhatsAppMessage): Promise<void> {
  logger.info('Sending template message (outside session window)', {
    messageId: message.id,
    templateId: message.metadata.templateId
  });

  if (!message.metadata.templateId) {
    throw new Error('Template ID required for messages outside session window');
  }

  // Get approved template
  const template = await templateManager.getTemplate(message.metadata.templateId);
  
  if (!template || template.status !== 'approved') {
    throw new Error(`Template not found or not approved: ${message.metadata.templateId}`);
  }

  // Build template payload with variable substitution
  const payload = buildTemplatePayload(message, template);
  
  const response = await whatsAppClient.sendMessage(payload);
  await handleResponse(message.id, response);
}

async function buildMediaPayload(message: WhatsAppMessage): Promise<WhatsAppAPIPayload> {
  const media = message.content.media![0];
  
  // Process and upload media if needed
  const processedMedia = await mediaProcessor.processForWhatsApp(media);
  
  return {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: message.recipient.phoneNumber,
    type: processedMedia.type,
    [processedMedia.type]: {
      link: processedMedia.url,
      caption: media.caption
    }
  };
}
```

### Template Management

```typescript
// src/templates/template-manager.ts
import { WhatsAppTemplate, TemplateVariable } from '@omni/types';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';

export class TemplateManager {
  private docClient: DynamoDBDocument;
  private tableName: string;

  constructor() {
    const client = new DynamoDBClient({});
    this.docClient = DynamoDBDocument.from(client);
    this.tableName = process.env.TEMPLATE_CACHE_TABLE!;
  }

  async getTemplate(templateId: string): Promise<WhatsAppTemplate | null> {
    const result = await this.docClient.get({
      TableName: this.tableName,
      Key: { templateId }
    });

    return result.Item as WhatsAppTemplate | null;
  }

  substituteVariables(
    template: WhatsAppTemplate, 
    variables: Record<string, string>
  ): WhatsAppTemplate {
    const substituted = { ...template };
    
    for (const component of substituted.components) {
      if (component.parameters) {
        component.parameters = component.parameters.map(param => {
          if (param.type === 'text' && param.text) {
            return {
              ...param,
              text: this.replaceVariables(param.text, variables)
            };
          }
          return param;
        });
      }
    }

    return substituted;
  }

  private replaceVariables(text: string, variables: Record<string, string>): string {
    return text.replace(/\{\{(\w+)\}\}/g, (match, key) => {
      return variables[key] || match;
    });
  }
}
```

### Session Window Management

```typescript
// src/session/session-manager.ts
import { SessionWindow, SessionRecord } from '@omni/types';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';

const SESSION_WINDOW_HOURS = 24;

export class SessionManager {
  private docClient: DynamoDBDocument;
  private tableName: string;

  async getSession(phoneNumber: string): Promise<SessionWindow> {
    const result = await this.docClient.get({
      TableName: this.tableName,
      Key: { phoneNumber }
    });

    if (!result.Item) {
      return { isWithinWindow: false, windowStart: null, windowEnd: null };
    }

    const session = result.Item as SessionRecord;
    const windowEnd = new Date(session.lastInboundAt);
    windowEnd.setHours(windowEnd.getHours() + SESSION_WINDOW_HOURS);

    const now = new Date();
    const isWithinWindow = now < windowEnd;

    return {
      isWithinWindow,
      windowStart: session.lastInboundAt,
      windowEnd: windowEnd.toISOString(),
      remainingMinutes: isWithinWindow 
        ? Math.floor((windowEnd.getTime() - now.getTime()) / 60000)
        : 0
    };
  }

  async updateSession(phoneNumber: string): Promise<void> {
    await this.docClient.put({
      TableName: this.tableName,
      Item: {
        phoneNumber,
        lastInboundAt: new Date().toISOString(),
        ttl: Math.floor(Date.now() / 1000) + (SESSION_WINDOW_HOURS * 3600)
      }
    });
  }
}
```

---

## Routing Logic

The routing logic in the omnichannel-omniservice follows a multi-tier decision process to ensure optimal message delivery.

### Routing Decision Flow

```typescript
// src/routing/routing-engine.ts
import { NormalizedMessage, RoutingDecision, RoutingRule } from '@omni/types';
import { RoutingRulesRepository } from '@omni/repositories';
import { RoutingContext } from './routing-context';

export class RoutingEngine {
  private rulesRepo: RoutingRulesRepository;

  async determineRoute(message: NormalizedMessage): Promise<RoutingDecision> {
    const context = await this.buildRoutingContext(message);
    const rules = await this.rulesRepo.getActiveRules();

    // Priority-ordered rule evaluation
    for (const rule of rules) {
      if (this.evaluateRule(rule, context)) {
        return this.buildDecision(rule, context);
      }
    }

    // Default routing
    return this.getDefaultRoute(context);
  }

  private evaluateRule(rule: RoutingRule, context: RoutingContext): boolean {
    // Evaluate all conditions
    for (const condition of rule.conditions) {
      if (!this.evaluateCondition(condition, context)) {
        return false;
      }
    }
    return true;
  }

  private evaluateCondition(
    condition: RuleCondition, 
    context: RoutingContext
  ): boolean {
    const contextValue = this.getContextValue(condition.field, context);
    
    switch (condition.operator) {
      case 'equals':
        return contextValue === condition.value;
      case 'contains':
        return String(contextValue).includes(String(condition.value));
      case 'matches':
        return new RegExp(String(condition.value)).test(String(contextValue));
      case 'in':
        return (condition.value as string[]).includes(String(contextValue));
      case 'greaterThan':
        return Number(contextValue) > Number(condition.value);
      default:
        return false;
    }
  }
}
```

### Routing Rules Configuration

```typescript
// Example routing rules
const routingRules: RoutingRule[] = [
  {
    id: 'whatsapp-priority',
    name: 'WhatsApp High Priority',
    priority: 100,
    conditions: [
      { field: 'channel', operator: 'equals', value: 'whatsapp' },
      { field: 'content.type', operator: 'equals', value: 'template' }
    ],
    action: {
      target: 'routerWhatsApp',
      queue: 'whatsapp-priority-queue'
    }
  },
  {
    id: 'inbound-support',
    name: 'Support Request Routing',
    priority: 90,
    conditions: [
      { field: 'metadata.intent', operator: 'equals', value: 'support' }
    ],
    action: {
      target: 'supportWorkflow',
      queue: 'support-queue'
    }
  },
  {
    id: 'media-processing',
    name: 'Media Message Processing',
    priority: 80,
    conditions: [
      { field: 'content.type', operator: 'equals', value: 'media' }
    ],
    action: {
      target: 'mediaProcessor',
      queue: 'media-processing-queue',
      preprocessor: 'mediaConverter'
    }
  }
];
```

---

## Input/Output Contracts

### Common Input Contracts

#### SQS Event Wrapper

```typescript
// All router Lambda functions receive SQS events
interface SQSEvent {
  Records: SQSRecord[];
}

interface SQSRecord {
  messageId: string;
  receiptHandle: string;
  body: string; // JSON-serialized message payload
  attributes: SQSRecordAttributes;
  messageAttributes: Record<string, SQSMessageAttribute>;
  md5OfBody: string;
  eventSource: 'aws:sqs';
  eventSourceARN: string;
  awsRegion: string;
}
```

#### Inbound Message Contract

```typescript
interface InboundMessagePayload {
  messageId: string;
  carrier: Carrier;
  channel: Channel;
  rawPayload: CarrierSpecificPayload;
  receivedAt: string;
  webhookMetadata: {
    webhookId: string;
    signature: string;
    timestamp: string;
  };
}
```

#### Outbound Message Contract

```typescript
interface OutboundMessagePayload {
  id: string;
  conversationId: string;
  sender: {
    id: string;
    type: 'agent' | 'bot' | 'system';
    displayName?: string;
  };
  recipient: {
    id: string;
    phoneNumber: string;
    country: string;
    optInStatus: 'opted_in' | 'opted_out' | 'pending';
  };
  content: {
    type: 'text' | 'media' | 'template' | 'interactive';
    text?: string;
    media?: MediaContent[];
    template?: TemplateReference;
    interactive?: InteractiveContent;
  };
  channel: Channel;
  priority: 'low' | 'normal' | 'high';
  metadata: {
    source: string;
    campaignId?: string;
    templateId?: string;
    retryCount: number;
  };
}
```

### Output Contracts

#### Delivery Result

```typescript
interface DeliveryResult {
  success: boolean;
  messageId: string;
  carrierMessageId: string;
  carrier: Carrier;
  status: DeliveryStatus;
  timestamp: string;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
}

type DeliveryStatus = 
  | 'sent' 
  | 'delivered' 
  | 'failed' 
  | 'rejected' 
  | 'queued';
```

#### Routing Decision

```typescript
interface RoutingDecision {
  targetFunction: string;
  targetQueue: string;
  priority: number;
  metadata: {
    ruleId: string;
    ruleName: string;
    matchedConditions: string[];
  };
  transformations?: MessageTransformation[];
}
```

### Error Response Contract

```typescript
interface RouterError {
  errorType: RouterErrorType;
  errorCode: string;
  message: string;
  messageId: string;
  carrier?: Carrier;
  retryable: boolean;
  retryAfter?: number;
  context: Record<string, unknown>;
}

type RouterErrorType = 
  | 'CARRIER_ERROR'
  | 'VALIDATION_ERROR'
  | 'RATE_LIMIT_ERROR'
  | 'ROUTING_ERROR'
  | 'TEMPLATE_ERROR'
  | 'SESSION_ERROR'
  | 'INTERNAL_ERROR';
```

---

## Best Practices and Common Pitfalls

### Best Practices

1. **Always validate message contracts** before processing to fail fast
2. **Implement idempotency** using message IDs to handle reprocessing
3. **Use structured logging** with correlation IDs for traceability
4. **Monitor carrier health** and implement circuit breakers
5. **Cache frequently accessed data** like templates and routing rules

### Common Pitfalls

1. **Ignoring session windows** for WhatsApp messages leads to delivery failures
2. **Not handling partial batch failures** can cause message loss
3. **Overlooking rate limits** results in carrier blocks
4. **Missing retry logic** for transient failures
5. **Hardcoding carrier configurations** instead of using dynamic config