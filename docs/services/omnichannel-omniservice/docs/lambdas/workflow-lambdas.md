# Workflow Lambda Functions

## Overview

The Omnichannel-Omniservice platform utilizes a sophisticated event-driven architecture built on AWS Lambda functions to process messages through a configurable workflow pipeline. These Lambda functions form the backbone of the message processing system, handling everything from identity resolution to carrier-specific routing, push notifications, and media processing.

This documentation provides comprehensive coverage of each workflow Lambda function, including their purpose, invocation patterns, input/output schemas, and integration points with other services in the pipeline.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Inbound Message Flow                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Carrier Webhook ──► workFlowIdentityLookup ──► workFlowBiDirectional      │
│                                │                        │                   │
│                                ▼                        ▼                   │
│                        workFlowPreRoute ──────► publishOutbound            │
│                                │                        │                   │
│                                ▼                        ▼                   │
│                        pushNotification         Carrier Delivery           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Supporting Functions                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  dynamoStream ──► Change Data Capture ──► Event Processing                 │
│                                                                             │
│  mediaConvertUpdate ──► Media Processing ──► Storage Update                │
│                                                                             │
│  schemaManager ──► Database Migrations ──► Schema Validation               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Common Patterns

All workflow Lambda functions share common patterns for error handling, logging, and configuration:

```typescript
// Common Lambda handler pattern
import { Context, Callback } from 'aws-lambda';
import { Logger } from '@omni/logger';
import { MetricsCollector } from '@omni/metrics';

interface WorkflowEvent<T> {
  correlationId: string;
  timestamp: string;
  source: string;
  payload: T;
  metadata: Record<string, unknown>;
}

interface WorkflowResponse<T> {
  success: boolean;
  correlationId: string;
  result?: T;
  error?: WorkflowError;
  nextStep?: string;
}

interface WorkflowError {
  code: string;
  message: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}
```

---

## workFlowIdentityLookup

### Purpose

The `workFlowIdentityLookup` Lambda function is the entry point for inbound message processing. It resolves the identity of message senders by correlating carrier-specific identifiers (phone numbers, user IDs, session tokens) with internal customer records.

### Trigger Sources

- API Gateway (webhook receivers)
- SNS Topics (carrier events)
- SQS Queues (batch processing)

### Input Schema

```typescript
interface IdentityLookupEvent {
  correlationId: string;
  carrier: 'whatsapp' | 'twilio' | 'bandwidth' | 'livechat' | 'messagebird' | 'inteliquent';
  channelType: 'sms' | 'mms' | 'chat' | 'voice';
  senderIdentifier: {
    phoneNumber?: string;
    userId?: string;
    sessionId?: string;
    email?: string;
  };
  recipientIdentifier: {
    phoneNumber?: string;
    shortCode?: string;
    businessId?: string;
  };
  message: {
    id: string;
    content: string;
    contentType: 'text' | 'media' | 'location' | 'contact';
    mediaUrls?: string[];
    timestamp: string;
  };
  rawPayload: Record<string, unknown>;
}
```

### Output Schema

```typescript
interface IdentityLookupResult {
  success: boolean;
  correlationId: string;
  identity: {
    customerId: string;
    customerType: 'known' | 'anonymous' | 'new';
    profile?: CustomerProfile;
    preferences?: CustomerPreferences;
    conversationHistory?: ConversationSummary;
  };
  routing: {
    accountId: string;
    businessUnitId: string;
    tenantId: string;
  };
  enrichedMessage: EnrichedMessage;
  nextStep: 'workFlowBiDirectional';
}

interface CustomerProfile {
  firstName?: string;
  lastName?: string;
  email?: string;
  phoneNumbers: string[];
  tags: string[];
  createdAt: string;
  lastContactAt: string;
}

interface CustomerPreferences {
  preferredChannel: string;
  language: string;
  timezone: string;
  optOutStatus: boolean;
  marketingConsent: boolean;
}
```

### Implementation Details

```typescript
// workFlowIdentityLookup/handler.ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';

const dynamoClient = new DynamoDBClient({});
const snsClient = new SNSClient({});

export const handler = async (
  event: IdentityLookupEvent,
  context: Context
): Promise<IdentityLookupResult> => {
  const logger = new Logger({ correlationId: event.correlationId });
  
  try {
    logger.info('Starting identity lookup', { 
      carrier: event.carrier,
      senderIdentifier: event.senderIdentifier 
    });

    // Step 1: Normalize identifier based on carrier
    const normalizedIdentifier = normalizeIdentifier(
      event.carrier, 
      event.senderIdentifier
    );

    // Step 2: Query customer database
    const customerRecord = await lookupCustomer(normalizedIdentifier);

    // Step 3: Resolve routing information
    const routingInfo = await resolveRouting(
      event.recipientIdentifier,
      customerRecord
    );

    // Step 4: Enrich message with context
    const enrichedMessage = await enrichMessage(event.message, customerRecord);

    // Step 5: Publish to next step
    const result: IdentityLookupResult = {
      success: true,
      correlationId: event.correlationId,
      identity: {
        customerId: customerRecord?.id || generateAnonymousId(),
        customerType: customerRecord ? 'known' : 'anonymous',
        profile: customerRecord?.profile,
        preferences: customerRecord?.preferences,
      },
      routing: routingInfo,
      enrichedMessage,
      nextStep: 'workFlowBiDirectional',
    };

    await publishToNextStep(result);
    
    return result;

  } catch (error) {
    logger.error('Identity lookup failed', { error });
    throw new WorkflowError('IDENTITY_LOOKUP_FAILED', error.message, true);
  }
};

function normalizeIdentifier(
  carrier: string, 
  identifier: SenderIdentifier
): string {
  switch (carrier) {
    case 'twilio':
    case 'bandwidth':
    case 'inteliquent':
      return normalizePhoneNumber(identifier.phoneNumber);
    case 'whatsapp':
      return `wa:${normalizePhoneNumber(identifier.phoneNumber)}`;
    case 'livechat':
      return `lc:${identifier.sessionId}`;
    case 'messagebird':
      return identifier.userId || normalizePhoneNumber(identifier.phoneNumber);
    default:
      throw new Error(`Unknown carrier: ${carrier}`);
  }
}
```

### Error Handling

| Error Code | Description | Retryable | Resolution |
|------------|-------------|-----------|------------|
| `IDENTITY_NOT_FOUND` | Customer record not found | No | Creates anonymous identity |
| `ROUTING_RESOLUTION_FAILED` | Cannot determine routing | Yes | Check recipient configuration |
| `DATABASE_ERROR` | DynamoDB operation failed | Yes | Automatic retry with backoff |
| `INVALID_IDENTIFIER` | Malformed identifier | No | Validate input at webhook |

---

## workFlowBiDirectional

### Purpose

The `workFlowBiDirectional` Lambda function manages bidirectional conversation state, tracking active conversations and determining whether incoming messages are part of an existing conversation or require new conversation initialization.

### Trigger Sources

- SNS Topic: `workflow-identity-complete`
- Direct Lambda invocation from `workFlowIdentityLookup`

### Input Schema

```typescript
interface BiDirectionalEvent {
  correlationId: string;
  identity: IdentityResult;
  routing: RoutingInfo;
  enrichedMessage: EnrichedMessage;
  conversationContext?: {
    existingConversationId?: string;
    lastMessageTimestamp?: string;
  };
}
```

### Output Schema

```typescript
interface BiDirectionalResult {
  success: boolean;
  correlationId: string;
  conversation: {
    conversationId: string;
    status: 'new' | 'active' | 'reopened' | 'escalated';
    participants: Participant[];
    channel: ChannelInfo;
    metadata: ConversationMetadata;
  };
  messageState: {
    messageId: string;
    sequenceNumber: number;
    deliveryStatus: 'pending' | 'processing';
  };
  routing: EnhancedRoutingInfo;
  nextStep: 'workFlowPreRoute';
}

interface Participant {
  id: string;
  type: 'customer' | 'agent' | 'bot';
  joinedAt: string;
  status: 'active' | 'left' | 'transferred';
}

interface ConversationMetadata {
  startedAt: string;
  lastActivityAt: string;
  messageCount: number;
  sentiment?: 'positive' | 'neutral' | 'negative';
  topics: string[];
  priority: 'low' | 'normal' | 'high' | 'urgent';
}
```

### Implementation Details

```typescript
// workFlowBiDirectional/handler.ts
import { ConversationRepository } from '@omni/repositories';
import { StateManager } from '@omni/state';

export const handler = async (
  event: BiDirectionalEvent,
  context: Context
): Promise<BiDirectionalResult> => {
  const logger = new Logger({ correlationId: event.correlationId });
  const conversationRepo = new ConversationRepository();
  const stateManager = new StateManager();

  try {
    // Step 1: Check for existing active conversation
    const existingConversation = await conversationRepo.findActive({
      customerId: event.identity.customerId,
      channel: event.routing.channelType,
      accountId: event.routing.accountId,
    });

    let conversation: Conversation;
    let status: ConversationStatus;

    if (existingConversation && isConversationValid(existingConversation)) {
      // Continue existing conversation
      conversation = existingConversation;
      status = 'active';
      
      logger.info('Continuing existing conversation', {
        conversationId: conversation.id,
      });
    } else if (existingConversation && isConversationExpired(existingConversation)) {
      // Reopen expired conversation
      conversation = await conversationRepo.reopen(existingConversation.id);
      status = 'reopened';
      
      logger.info('Reopened expired conversation', {
        conversationId: conversation.id,
      });
    } else {
      // Create new conversation
      conversation = await conversationRepo.create({
        customerId: event.identity.customerId,
        accountId: event.routing.accountId,
        channel: event.routing.channelType,
        carrier: event.enrichedMessage.carrier,
        metadata: {
          startedAt: new Date().toISOString(),
          initiatedBy: 'customer',
        },
      });
      status = 'new';
      
      logger.info('Created new conversation', {
        conversationId: conversation.id,
      });
    }

    // Step 2: Update conversation state
    const messageState = await stateManager.addMessage({
      conversationId: conversation.id,
      messageId: event.enrichedMessage.id,
      direction: 'inbound',
      timestamp: new Date().toISOString(),
    });

    // Step 3: Analyze and enrich routing
    const enhancedRouting = await enhanceRouting(
      event.routing,
      conversation,
      event.identity
    );

    return {
      success: true,
      correlationId: event.correlationId,
      conversation: {
        conversationId: conversation.id,
        status,
        participants: conversation.participants,
        channel: conversation.channel,
        metadata: conversation.metadata,
      },
      messageState,
      routing: enhancedRouting,
      nextStep: 'workFlowPreRoute',
    };

  } catch (error) {
    logger.error('BiDirectional processing failed', { error });
    throw new WorkflowError('BIDIRECTIONAL_FAILED', error.message, true);
  }
};

function isConversationValid(conversation: Conversation): boolean {
  const CONVERSATION_TIMEOUT_MS = 24 * 60 * 60 * 1000; // 24 hours
  const lastActivity = new Date(conversation.metadata.lastActivityAt).getTime();
  return Date.now() - lastActivity < CONVERSATION_TIMEOUT_MS;
}
```

### Conversation State Machine

```
┌──────────────────────────────────────────────────────────────┐
│                    Conversation States                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│    ┌─────────┐      ┌─────────┐      ┌──────────┐           │
│    │   NEW   │ ───► │ ACTIVE  │ ───► │ RESOLVED │           │
│    └─────────┘      └─────────┘      └──────────┘           │
│                          │                │                  │
│                          ▼                ▼                  │
│                    ┌──────────┐     ┌──────────┐            │
│                    │ESCALATED │     │ EXPIRED  │            │
│                    └──────────┘     └──────────┘            │
│                          │                │                  │
│                          ▼                ▼                  │
│                    ┌──────────────────────┐                 │
│                    │      REOPENED        │                 │
│                    └──────────────────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## workFlowPreRoute

### Purpose

The `workFlowPreRoute` Lambda function handles pre-routing logic including message validation, content filtering, bot detection, auto-response rules, and routing decision making before messages are dispatched to their final destinations.

### Trigger Sources

- SNS Topic: `workflow-bidirectional-complete`
- SQS Queue: `pre-route-queue` (for batch processing)

### Input Schema

```typescript
interface PreRouteEvent {
  correlationId: string;
  conversation: ConversationInfo;
  messageState: MessageState;
  routing: EnhancedRoutingInfo;
  identity: IdentityResult;
  message: EnrichedMessage;
}
```

### Output Schema

```typescript
interface PreRouteResult {
  success: boolean;
  correlationId: string;
  routingDecision: {
    action: 'route' | 'auto_respond' | 'block' | 'escalate' | 'queue';
    destination: RoutingDestination;
    priority: number;
    tags: string[];
  };
  autoResponse?: {
    enabled: boolean;
    responseType: 'greeting' | 'away' | 'acknowledgment' | 'custom';
    content: string;
  };
  contentAnalysis: {
    spam: boolean;
    sentiment: string;
    intent: string[];
    entities: Entity[];
    language: string;
  };
  transformedMessage: TransformedMessage;
  nextStep: 'publishOutbound' | 'pushNotification' | 'terminate';
}

interface RoutingDestination {
  type: 'agent' | 'queue' | 'bot' | 'external';
  id: string;
  name: string;
  metadata: Record<string, unknown>;
}
```

### Implementation Details

```typescript
// workFlowPreRoute/handler.ts
import { RuleEngine } from '@omni/rules';
import { ContentAnalyzer } from '@omni/content-analysis';
import { AutoResponder } from '@omni/auto-responder';

export const handler = async (
  event: PreRouteEvent,
  context: Context
): Promise<PreRouteResult> => {
  const logger = new Logger({ correlationId: event.correlationId });
  const ruleEngine = new RuleEngine(event.routing.accountId);
  const contentAnalyzer = new ContentAnalyzer();
  const autoResponder = new AutoResponder();

  try {
    // Step 1: Content Analysis
    const contentAnalysis = await contentAnalyzer.analyze({
      content: event.message.content,
      contentType: event.message.contentType,
      language: event.identity.preferences?.language || 'en',
    });

    logger.info('Content analysis complete', {
      spam: contentAnalysis.spam,
      sentiment: contentAnalysis.sentiment,
      intent: contentAnalysis.intent,
    });

    // Step 2: Check for spam/block conditions
    if (contentAnalysis.spam || await shouldBlockMessage(event, contentAnalysis)) {
      return {
        success: true,
        correlationId: event.correlationId,
        routingDecision: {
          action: 'block',
          destination: { type: 'queue', id: 'blocked', name: 'Blocked Messages' },
          priority: 0,
          tags: ['blocked', 'spam'],
        },
        contentAnalysis,
        transformedMessage: event.message,
        nextStep: 'terminate',
      };
    }

    // Step 3: Evaluate routing rules
    const routingRules = await ruleEngine.evaluate({
      message: event.message,
      conversation: event.conversation,
      identity: event.identity,
      contentAnalysis,
    });

    // Step 4: Check auto-response conditions
    const autoResponse = await autoResponder.check({
      accountId: event.routing.accountId,
      conversationStatus: event.conversation.status,
      messageIntent: contentAnalysis.intent,
      businessHours: await getBusinessHours(event.routing.accountId),
    });

    // Step 5: Determine routing destination
    const destination = await resolveDestination(routingRules, event);

    // Step 6: Transform message for destination
    const transformedMessage = await transformMessage(
      event.message,
      destination,
      contentAnalysis
    );

    const result: PreRouteResult = {
      success: true,
      correlationId: event.correlationId,
      routingDecision: {
        action: autoResponse.enabled ? 'auto_respond' : 'route',
        destination,
        priority: calculatePriority(contentAnalysis, event.identity),
        tags: generateTags(contentAnalysis, routingRules),
      },
      autoResponse: autoResponse.enabled ? autoResponse : undefined,
      contentAnalysis,
      transformedMessage,
      nextStep: autoResponse.enabled ? 'publishOutbound' : 'pushNotification',
    };

    await publishToNextSteps(result, autoResponse);

    return result;

  } catch (error) {
    logger.error('PreRoute processing failed', { error });
    throw new WorkflowError('PREROUTE_FAILED', error.message, true);
  }
};

async function resolveDestination(
  rules: RuleResult[],
  event: PreRouteEvent
): Promise<RoutingDestination> {
  // Priority-based destination resolution
  const sortedRules = rules.sort((a, b) => b.priority - a.priority);
  
  for (const rule of sortedRules) {
    if (rule.action === 'route_to_agent') {
      return {
        type: 'agent',
        id: rule.agentId,
        name: rule.agentName,
        metadata: { skillSet: rule.skills },
      };
    }
    if (rule.action === 'route_to_queue') {
      return {
        type: 'queue',
        id: rule.queueId,
        name: rule.queueName,
        metadata: { estimatedWait: rule.estimatedWait },
      };
    }
    if (rule.action === 'route_to_bot') {
      return {
        type: 'bot',
        id: rule.botId,
        name: rule.botName,
        metadata: { capabilities: rule.botCapabilities },
      };
    }
  }

  // Default routing
  return {
    type: 'queue',
    id: 'default',
    name: 'Default Queue',
    metadata: {},
  };
}
```

### Routing Rules Configuration

```typescript
// Example routing rules configuration
interface RoutingRule {
  id: string;
  name: string;
  priority: number;
  conditions: RuleCondition[];
  actions: RuleAction[];
  enabled: boolean;
}

const exampleRules: RoutingRule[] = [
  {
    id: 'vip-customer-rule',
    name: 'VIP Customer Priority Routing',
    priority: 100,
    conditions: [
      { field: 'identity.profile.tags', operator: 'contains', value: 'vip' },
    ],
    actions: [
      { type: 'route_to_queue', queueId: 'vip-support', priority: 'high' },
    ],
    enabled: true,
  },
  {
    id: 'billing-intent-rule',
    name: 'Billing Intent Routing',
    priority: 80,
    conditions: [
      { field: 'contentAnalysis.intent', operator: 'contains', value: 'billing' },
    ],
    actions: [
      { type: 'route_to_queue', queueId: 'billing-team' },
      { type: 'add_tag', tag: 'billing-inquiry' },
    ],
    enabled: true,
  },
];
```

---

## publishOutbound

### Purpose

The `publishOutbound` Lambda function handles the final step of outbound message delivery, preparing messages for carrier-specific delivery, managing delivery queues, and coordinating with carrier APIs for message transmission.

### Trigger Sources

- SNS Topic: `workflow-preroute-complete`
- SQS Queue: `outbound-message-queue`
- Direct invocation for immediate delivery

### Input Schema

```typescript
interface PublishOutboundEvent {
  correlationId: string;
  messageType: 'reply' | 'auto_response' | 'broadcast' | 'notification';
  recipient: {
    customerId: string;
    channelIdentifier: string;
    carrier: CarrierType;
    channel: ChannelType;
  };
  message: {
    content: string;
    contentType: 'text' | 'media' | 'template' | 'interactive';
    mediaUrls?: string[];
    templateId?: string;
    templateParams?: Record<string, string>;
    buttons?: MessageButton[];
  };
  routing: {
    accountId: string;
    conversationId: string;
    fromNumber?: string;
    businessId?: string;
  };
  options: {
    priority: 'low' | 'normal' | 'high';
    scheduledAt?: string;
    expiresAt?: string;
    trackDelivery: boolean;
    trackRead: boolean;
  };
}
```

### Output Schema

```typescript
interface PublishOutboundResult {
  success: boolean;
  correlationId: string;
  delivery: {
    messageId: string;
    carrierMessageId?: string;
    status: 'queued' | 'sent' | 'delivered' | 'failed';
    carrier: CarrierType;
    timestamp: string;
    cost?: number;
  };
  tracking: {
    trackingId: string;
    webhookUrl: string;
    expectedDeliveryTime?: string;
  };
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
}
```

### Implementation Details

```typescript
// publishOutbound/handler.ts
import { CarrierFactory } from '@omni/carriers';
import { MessageRepository } from '@omni/repositories';
import { DeliveryTracker } from '@omni/tracking';

export const handler = async (
  event: PublishOutboundEvent,
  context: Context
): Promise<PublishOutboundResult> => {
  const logger = new Logger({ correlationId: event.correlationId });
  const messageRepo = new MessageRepository();
  const deliveryTracker = new DeliveryTracker();

  try {
    // Step 1: Create carrier client
    const carrierClient = CarrierFactory.create(event.recipient.carrier, {
      accountId: event.routing.accountId,
    });

    // Step 2: Transform message for carrier
    const carrierMessage = await carrierClient.transformMessage({
      content: event.message.content,
      contentType: event.message.contentType,
      mediaUrls: event.message.mediaUrls,
      templateId: event.message.templateId,
      templateParams: event.message.templateParams,
    });

    // Step 3: Create message record
    const messageRecord = await messageRepo.create({
      correlationId: event.correlationId,
      conversationId: event.routing.conversationId,
      direction: 'outbound',
      carrier: event.recipient.carrier,
      channel: event.recipient.channel,
      content: event.message.content,
      status: 'pending',
      metadata: {
        messageType: event.messageType,
        priority: event.options.priority,
      },
    });

    // Step 4: Send via carrier
    let deliveryResult: CarrierDeliveryResult;
    
    if (event.options.scheduledAt) {
      // Schedule for future delivery
      deliveryResult = await carrierClient.schedule({
        message: carrierMessage,
        to: event.recipient.channelIdentifier,
        from: event.routing.fromNumber,
        scheduledAt: event.options.scheduledAt,
      });
    } else {
      // Immediate delivery
      deliveryResult = await carrierClient.send({
        message: carrierMessage,
        to: event.recipient.channelIdentifier,
        from: event.routing.fromNumber,
      });
    }

    // Step 5: Update message status
    await messageRepo.update(messageRecord.id, {
      status: deliveryResult.success ? 'sent' : 'failed',
      carrierMessageId: deliveryResult.messageId,
      sentAt: new Date().toISOString(),
      carrierResponse: deliveryResult.rawResponse,
    });

    // Step 6: Setup delivery tracking
    let tracking: TrackingInfo | undefined;
    if (event.options.trackDelivery || event.options.trackRead) {
      tracking = await deliveryTracker.setup({
        messageId: messageRecord.id,
        carrierMessageId: deliveryResult.messageId,
        carrier: event.recipient.carrier,
        trackDelivery: event.options.trackDelivery,
        trackRead: event.options.trackRead,
      });
    }

    logger.info('Message published successfully', {
      messageId: messageRecord.id,
      carrierMessageId: deliveryResult.messageId,
      carrier: event.recipient.carrier,
    });

    return {
      success: true,
      correlationId: event.correlationId,
      delivery: {
        messageId: messageRecord.id,
        carrierMessageId: deliveryResult.messageId,
        status: deliveryResult.success ? 'sent' : 'failed',
        carrier: event.recipient.carrier,
        timestamp: new Date().toISOString(),
        cost: deliveryResult.cost,
      },
      tracking: tracking ? {
        trackingId: tracking.id,
        webhookUrl: tracking.webhookUrl,
        expectedDeliveryTime: tracking.estimatedDelivery,
      } : undefined,
    };

  } catch (error) {
    logger.error('Outbound publishing failed', { error });
    
    // Determine if error is retryable
    const isRetryable = isRetryableError(error);
    
    if (isRetryable && context.getRemainingTimeInMillis() > 10000) {
      // Retry with exponential backoff
      await delay(calculateBackoff(event.retryCount || 0));
      return handler({ ...event, retryCount: (event.retryCount || 0) + 1 }, context);
    }

    throw new WorkflowError('PUBLISH_OUTBOUND_FAILED', error.message, isRetryable);
  }
};
```

### Carrier-Specific Implementations

```typescript
// carriers/twilio.ts
export class TwilioCarrier implements Carrier {
  async send(params: SendParams): Promise<CarrierDeliveryResult> {
    const client = new Twilio(this.accountSid, this.authToken);
    
    const message = await client.messages.create({
      body: params.message.content,
      to: params.to,
      from: params.from,
      mediaUrl: params.message.mediaUrls,
      statusCallback: this.webhookUrl,
    });

    return {
      success: true,
      messageId: message.sid,
      status: message.status,
      rawResponse: message,
    };
  }
}

// carriers/whatsapp.ts
export class WhatsAppCarrier implements Carrier {
  async send(params: SendParams): Promise<CarrierDeliveryResult> {
    const response = await this.client.post('/messages', {
      messaging_product: 'whatsapp',
      recipient_type: 'individual',
      to: params.to,
      type: params.message.contentType,
      [params.message.contentType]: this.formatContent(params.message),
    });

    return {
      success: response.data.messages?.[0]?.id !== undefined,
      messageId: response.data.messages?.[0]?.id,
      status: 'sent',
      rawResponse: response.data,
    };
  }
}
```

---

## pushNotification

### Purpose

The `pushNotification` Lambda function handles push notification delivery to mobile applications and agent desktops, ensuring real-time alerts for incoming messages and important events.

### Trigger Sources

- SNS Topic: `workflow-notification-trigger`
- EventBridge: Scheduled notifications
- Direct invocation for urgent alerts

### Input Schema

```typescript
interface PushNotificationEvent {
  correlationId: string;
  notificationType: 'new_message' | 'assignment' | 'escalation' | 'reminder' | 'alert';
  recipients: NotificationRecipient[];
  payload: {
    title: string;
    body: string;
    data: Record<string, unknown>;
    actions?: NotificationAction[];
    image?: string;
    sound?: string;
    badge?: number;
  };
  options: {
    priority: 'low' | 'normal' | 'high' | 'critical';
    ttl?: number;
    collapseKey?: string;
    channelId?: string;
  };
  context: {
    conversationId?: string;
    messageId?: string;
    accountId: string;
  };
}

interface NotificationRecipient {
  userId: string;
  deviceTokens: DeviceToken[];
  preferences: NotificationPreferences;
}

interface DeviceToken {
  token: string;
  platform: 'ios' | 'android' | 'web';
  appId: string;
}
```

### Output Schema

```typescript
interface PushNotificationResult {
  success: boolean;
  correlationId: string;
  deliveryResults: DeliveryResult[];
  summary: {
    total: number;
    sent: number;
    failed: number;
    skipped: number;
  };
}

interface DeliveryResult {
  recipientId: string;
  platform: string;
  status: 'sent' | 'failed' | 'skipped';
  messageId?: string;
  error?: string;
}
```

### Implementation Details

```typescript
// pushNotification/handler.ts
import { FirebaseMessaging } from '@omni/firebase';
import { APNSClient } from '@omni/apns';
import { WebPushClient } from '@omni/webpush';

export const handler = async (
  event: PushNotificationEvent,
  context: Context
): Promise<PushNotificationResult> => {
  const logger = new Logger({ correlationId: event.correlationId });
  const deliveryResults: DeliveryResult[] = [];

  try {
    for (const recipient of event.recipients) {
      // Check notification preferences
      if (!shouldNotify(recipient.preferences, event.notificationType)) {
        deliveryResults.push({
          recipientId: recipient.userId,
          platform: 'all',
          status: 'skipped',
        });
        continue;
      }

      // Send to each device
      for (const device of recipient.deviceTokens) {
        const result = await sendToDevice(device, event.payload, event.options);
        deliveryResults.push({
          recipientId: recipient.userId,
          platform: device.platform,
          ...result,
        });
      }
    }

    const summary = calculateSummary(deliveryResults);
    
    logger.info('Push notifications processed', { summary });

    return {
      success: summary.failed < summary.total,
      correlationId: event.correlationId,
      deliveryResults,
      summary,
    };

  } catch (error) {
    logger.error('Push notification processing failed', { error });
    throw new WorkflowError('PUSH_NOTIFICATION_FAILED', error.message, true);
  }
};

async function sendToDevice(
  device: DeviceToken,
  payload: NotificationPayload,
  options: NotificationOptions
): Promise<Partial<DeliveryResult>> {
  switch (device.platform) {
    case 'android':
      return sendAndroidNotification(device, payload, options);
    case 'ios':
      return sendIOSNotification(device, payload, options);
    case 'web':
      return sendWebNotification(device, payload, options);
    default:
      return { status: 'failed', error: 'Unknown platform' };
  }
}

async function sendAndroidNotification(
  device: DeviceToken,
  payload: NotificationPayload,
  options: NotificationOptions
): Promise<Partial<DeliveryResult>> {
  const firebase = new FirebaseMessaging();
  
  const message = {
    token: device.token,
    notification: {
      title: payload.title,
      body: payload.body,
      imageUrl: payload.image,
    },
    data: payload.data,
    android: {
      priority: mapPriority(options.priority),
      ttl: options.ttl ? `${options.ttl}s` : undefined,
      collapseKey: options.collapseKey,
      notification: {
        channelId: options.channelId,
        sound: payload.sound,
      },
    },
  };

  const response = await firebase.send(message);
  
  return {
    status: 'sent',
    messageId: response.messageId,
  };
}

async function sendIOSNotification(
  device: DeviceToken,
  payload: NotificationPayload,
  options: NotificationOptions
): Promise<Partial<DeliveryResult>> {
  const apns = new APNSClient();
  
  const notification = {
    aps: {
      alert: {
        title: payload.title,
        body: payload.body,
      },
      sound: payload.sound || 'default',
      badge: payload.badge,
      'mutable-content': 1,
    },
    ...payload.data,
  };

  const response = await apns.send(device.token, notification, {
    priority: options.priority === 'critical' ? 10 : 5,
    expiration: options.ttl ? Math.floor(Date.now() / 1000) + options.ttl : 0,
    collapseId: options.collapseKey,
  });

  return {
    status: response.success ? 'sent' : 'failed',
    messageId: response.apnsId,
    error: response.error,
  };
}
```

---

## dynamoStream

### Purpose

The `dynamoStream` Lambda function processes DynamoDB Streams events for change data capture, enabling real-time synchronization, event sourcing, and triggering downstream workflows based on data changes.

### Trigger Sources

- DynamoDB Streams (conversations, messages, customers tables)

### Input Schema

```typescript
interface DynamoStreamEvent {
  Records: DynamoStreamRecord[];
}

interface DynamoStreamRecord {
  eventID: string;
  eventName: 'INSERT' | 'MODIFY' | 'REMOVE';
  eventVersion: string;
  eventSource: string;
  awsRegion: string;
  dynamodb: {
    Keys: Record<string, AttributeValue>;
    NewImage?: Record<string, AttributeValue>;
    OldImage?: Record<string, AttributeValue>;
    SequenceNumber: string;
    SizeBytes: number;
    StreamViewType: 'NEW_IMAGE' | 'OLD_IMAGE' | 'NEW_AND_OLD_IMAGES' | 'KEYS_ONLY';
  };
  eventSourceARN: string;
}
```

### Implementation Details

```typescript
// dynamoStream/handler.ts
import { DynamoDBStreamEvent } from 'aws-lambda';
import { unmarshall } from '@aws-sdk/util-dynamodb';
import { EventBridge } from '@aws-sdk/client-eventbridge';

const eventBridge = new EventBridge({});

export const handler = async (
  event: DynamoDBStreamEvent,
  context: Context
): Promise<void> => {
  const logger = new Logger({ function: 'dynamoStream' });
  
  const processedEvents: ProcessedEvent[] = [];

  for (const record of event.Records) {
    try {
      const tableName = extractTableName(record.eventSourceARN);
      const eventType = record.eventName;
      
      const newImage = record.dynamodb.NewImage 
        ? unmarshall(record.dynamodb.NewImage) 
        : undefined;
      const oldImage = record.dynamodb.OldImage 
        ? unmarshall(record.dynamodb.OldImage) 
        : undefined;

      // Route to appropriate handler based on table
      switch (tableName) {
        case 'conversations':
          await handleConversationChange(eventType, newImage, oldImage);
          break;
        case 'messages':
          await handleMessageChange(eventType, newImage, oldImage);
          break;
        case 'customers':
          await handleCustomerChange(eventType, newImage, oldImage);
          break;
        default:
          logger.warn('Unknown table in stream', { tableName });
      }

      processedEvents.push({
        recordId: record.eventID,
        status: 'success',
      });

    } catch (error) {
      logger.error('Failed to process stream record', {
        recordId: record.eventID,
        error,
      });
      
      processedEvents.push({
        recordId: record.eventID,
        status: 'failed',
        error: error.message,
      });
    }
  }

  logger.info('Stream processing complete', {
    total: event.Records.length,
    successful: processedEvents.filter(e => e.status === 'success').length,
    failed: processedEvents.filter(e => e.status === 'failed').length,
  });
};

async function handleConversationChange(
  eventType: string,
  newImage: any,
  oldImage: any
): Promise<void> {
  if (eventType === 'INSERT') {
    // New conversation created
    await publishEvent('conversation.created', {
      conversationId: newImage.id,
      customerId: newImage.customerId,
      channel: newImage.channel,
      createdAt: newImage.createdAt,
    });
  } else if (eventType === 'MODIFY') {
    // Check for status changes
    if (oldImage?.status !== newImage?.status) {
      await publishEvent('conversation.status_changed', {
        conversationId: newImage.id,
        previousStatus: oldImage.status,
        newStatus: newImage.status,
        changedAt: new Date().toISOString(),
      });
    }
    
    // Check for assignment changes
    if (oldImage?.assignedTo !== newImage?.assignedTo) {
      await publishEvent('conversation.assigned', {
        conversationId: newImage.id,
        previousAssignee: oldImage?.assignedTo,
        newAssignee: newImage.assignedTo,
        assignedAt: new Date().toISOString(),
      });
    }
  } else if (eventType === 'REMOVE') {
    await publishEvent('conversation.deleted', {
      conversationId: oldImage.id,
      deletedAt: new Date().toISOString(),
    });
  }
}

async function handleMessageChange(
  eventType: string,
  newImage: any,
  oldImage: any
): Promise<void> {
  if (eventType === 'INSERT') {
    await publishEvent('message.created', {
      messageId: newImage.id,
      conversationId: newImage.conversationId,
      direction: newImage.direction,
      createdAt: newImage.createdAt,
    });
  } else if (eventType === 'MODIFY') {
    // Track delivery status updates
    if (oldImage?.deliveryStatus !== newImage?.deliveryStatus) {
      await publishEvent('message.delivery_updated', {
        messageId: newImage.id,
        previousStatus: oldImage.deliveryStatus,
        newStatus: newImage.deliveryStatus,
        updatedAt: new Date().toISOString(),
      });
    }
  }
}

async function publishEvent(
  eventType: string,
  detail: Record<string, unknown>
): Promise<void> {
  await eventBridge.putEvents({
    Entries: [{
      Source: 'omni.workflow',
      DetailType: eventType,
      Detail: JSON.stringify(detail),
      EventBusName: process.env.EVENT_BUS_NAME,
    }],
  });
}
```

---

## mediaConvertUpdate

### Purpose

The `mediaConvertUpdate` Lambda function processes AWS MediaConvert job completion events, updating media records with converted file locations and triggering downstream processing for transcoded media content.

### Trigger Sources

- CloudWatch Events (MediaConvert job state changes)
- SNS Topic: `media-convert-notifications`

### Input Schema

```typescript
interface MediaConvertUpdateEvent {
  version: string;
  id: string;
  'detail-type': 'MediaConvert Job State Change';
  source: 'aws.mediaconvert';
  account: string;
  time: string;
  region: string;
  detail: {
    status: 'SUBMITTED' | 'PROGRESSING' | 'COMPLETE' | 'CANCELED' | 'ERROR';
    jobId: string;
    queue: string;
    userMetadata: {
      messageId: string;
      conversationId: string;
      accountId: string;
      originalFileName: string;
    };
    outputGroupDetails?: OutputGroupDetail[];
    errorCode?: number;
    errorMessage?: string;
  };
}

interface OutputGroupDetail {
  outputDetails: {
    outputFilePaths: string[];
    durationInMs: number;
    videoDetails?: {
      widthInPx: number;
      heightInPx: number;
    };
  }[];
  type: string;
}
```

### Implementation Details

```typescript
// mediaConvertUpdate/handler.ts
import { MediaRepository } from '@omni/repositories';
import { S3Client, CopyObjectCommand } from '@aws-sdk/client-s3';

export const handler = async (
  event: MediaConvertUpdateEvent,
  context: Context
): Promise<void> => {
  const logger = new Logger({ jobId: event.detail.jobId });
  const mediaRepo = new MediaRepository();
  const s3Client = new S3Client({});

  const { status, jobId, userMetadata } = event.detail;

  try {
    logger.info('Processing MediaConvert update', { status, jobId });

    switch (status) {
      case 'COMPLETE':
        await handleJobComplete(event, mediaRepo, s3Client, logger);
        break;
      case 'ERROR':
        await handleJobError(event, mediaRepo, logger);
        break;
      case 'PROGRESSING':
        await handleJobProgress(event, mediaRepo, logger);
        break;
      case 'CANCELED':
        await handleJobCanceled(event, mediaRepo, logger);
        break;
    }

  } catch (error) {
    logger.error('Failed to process MediaConvert update', { error });
    throw error;
  }
};

async function handleJobComplete(
  event: MediaConvertUpdateEvent,
  mediaRepo: MediaRepository,
  s3Client: S3Client,
  logger: Logger
): Promise<void> {
  const { userMetadata, outputGroupDetails } = event.detail;

  // Extract output file paths
  const outputFiles: OutputFile[] = [];
  
  for (const group of outputGroupDetails || []) {
    for (const output of group.outputDetails) {
      for (const path of output.outputFilePaths) {
        outputFiles.push({
          path,
          type: group.type,
          duration: output.durationInMs,
          dimensions: output.videoDetails,
        });
      }
    }
  }

  // Update media record
  await mediaRepo.update(userMetadata.messageId, {
    status: 'converted',
    convertedAt: new Date().toISOString(),
    outputs: outputFiles.map(file => ({
      url: generateCloudFrontUrl(file.path),
      type: file.type,
      duration: file.duration,
      dimensions: file.dimensions,
    })),
    metadata: {
      jobId: event.detail.jobId,
      processingTime: calculateProcessingTime(event),
    },
  });

  // Publish completion event
  await publishMediaEvent('media.conversion.complete', {
    messageId: userMetadata.messageId,
    conversationId: userMetadata.conversationId,
    outputs: outputFiles,
  });

  logger.info('Media conversion complete', {
    messageId: userMetadata.messageId,
    outputCount: outputFiles.length,
  });
}

async function handleJobError(
  event: MediaConvertUpdateEvent,
  mediaRepo: MediaRepository,
  logger: Logger
): Promise<void> {
  const { userMetadata, errorCode, errorMessage } = event.detail;

  await mediaRepo.update(userMetadata.messageId, {
    status: 'conversion_failed',
    error: {
      code: errorCode,
      message: errorMessage,
      failedAt: new Date().toISOString(),
    },
  });

  await publishMediaEvent('media.conversion.failed', {
    messageId: userMetadata.messageId,
    errorCode,
    errorMessage,
  });

  logger.error('Media conversion failed', {
    messageId: userMetadata.messageId,
    errorCode,
    errorMessage,
  });
}
```

---

## schemaManager

### Purpose

The `schemaManager` Lambda function handles database schema migrations, validation, and management for DynamoDB tables and other data stores, ensuring consistent data structures across the platform.

### Trigger Sources

- CloudFormation Custom Resource
- Manual invocation for migrations
- CI/CD pipeline triggers

### Input Schema

```typescript
interface SchemaManagerEvent {
  action: 'migrate' | 'validate' | 'rollback' | 'status';
  targetVersion?: string;
  options?: {
    dryRun?: boolean;
    force?: boolean;
    tables?: string[];
  };
  requestType?: 'Create' | 'Update' | 'Delete'; // For CloudFormation
  resourceProperties?: Record<string, unknown>;
}
```

### Implementation Details

```typescript
// schemaManager/handler.ts
import { DynamoDBClient, CreateTableCommand, UpdateTableCommand } from '@aws-sdk/client-dynamodb';
import { MigrationRunner } from '@omni/migrations';

export const handler = async (
  event: SchemaManagerEvent,
  context: Context
): Promise<SchemaManagerResult> => {
  const logger = new Logger({ function: 'schemaManager' });
  const dynamoClient = new DynamoDBClient({});
  const migrationRunner = new MigrationRunner(dynamoClient);

  try {
    switch (event.action) {
      case 'migrate':
        return await runMigrations(migrationRunner, event, logger);
      case 'validate':
        return await validateSchema(dynamoClient, event, logger);
      case 'rollback':
        return await rollbackMigrations(migrationRunner, event, logger);
      case 'status':
        return await getMigrationStatus(migrationRunner, logger);
      default:
        throw new Error(`Unknown action: ${event.action}`);
    }
  } catch (error) {
    logger.error('Schema management failed', { error });
    throw error;
  }
};

async function runMigrations(
  runner: MigrationRunner,
  event: SchemaManagerEvent,
  logger: Logger
): Promise<SchemaManagerResult> {
  const migrations = await runner.getPendingMigrations(event.targetVersion);
  
  if (event.options?.dryRun) {
    return {
      success: true,
      action: 'migrate',
      dryRun: true,
      pendingMigrations: migrations.map(m => m.name),
    };
  }

  const results: MigrationResult[] = [];
  
  for (const migration of migrations) {
    logger.info('Running migration', { name: migration.name });
    
    try {
      await migration.up();
      results.push({ name: migration.name, status: 'success' });
    } catch (error) {
      results.push({ name: migration.name, status: 'failed', error: error.message });
      
      if (!event.options?.force) {
        break;
      }
    }
  }

  return {
    success: results.every(r => r.status === 'success'),
    action: 'migrate',
    results,
  };
}

// Example migration definition
const migrations: Migration[] = [
  {
    name: '001_create_conversations_table',
    version: '1.0.0',
    async up() {
      await dynamoClient.send(new CreateTableCommand({
        TableName: 'conversations',
        KeySchema: [
          { AttributeName: 'pk', KeyType: 'HASH' },
          { AttributeName: 'sk', KeyType: 'RANGE' },
        ],
        AttributeDefinitions: [
          { AttributeName: 'pk', AttributeType: 'S' },
          { AttributeName: 'sk', AttributeType: 'S' },
          { AttributeName: 'gsi1pk', AttributeType: 'S' },
          { AttributeName: 'gsi1sk', AttributeType: 'S' },
        ],
        GlobalSecondaryIndexes: [
          {
            IndexName: 'gsi1',
            KeySchema: [
              { AttributeName: 'gsi1pk', KeyType: 'HASH' },
              { AttributeName: 'gsi1sk', KeyType: 'RANGE' },
            ],
            Projection: { ProjectionType: 'ALL' },
          },
        ],
        BillingMode: 'PAY_PER_REQUEST',
        StreamSpecification: {
          StreamEnabled: true,
          StreamViewType: 'NEW_AND_OLD_IMAGES',
        },
      }));
    },
    async down() {
      await dynamoClient.send(new DeleteTableCommand({
        TableName: 'conversations',
      }));
    },
  },
];
```

---

## Workflow Steps

### Complete Message Processing Pipeline

The following diagram illustrates the complete workflow for processing an inbound message through all Lambda functions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Complete Workflow Pipeline                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Webhook Reception                                                  │
│  ─────────────────────────                                                  │
│  Carrier Webhook ──► API Gateway ──► Webhook Handler Lambda                 │
│                                              │                              │
│                                              ▼                              │
│  Step 2: Identity Resolution                                                │
│  ────────────────────────────                                               │
│  workFlowIdentityLookup ──► Customer Lookup ──► Identity Enrichment        │
│                                              │                              │
│                                              ▼                              │
│  Step 3: Conversation Management                                            │
│  ────────────────────────────────                                           │
│  workFlowBiDirectional ──► State Check ──► Conversation Create/Resume      │
│                                              │                              │
│                                              ▼                              │
│  Step 4: Pre-Routing                                                        │
│  ────────────────────                                                       │
│  workFlowPreRoute ──► Content Analysis ──► Rule Evaluation ──► Routing     │
│                              │                                              │
│                              ├──► Auto Response Path                       │
│                              │         │                                   │
│                              │         ▼                                   │
│                              │    publishOutbound                          │
│                              │                                              │
│                              └──► Agent Notification Path                  │
│                                        │                                   │
│                                        ▼                                   │
│  Step 5: Notification                                                       │
│  ────────────────────                                                       │
│  pushNotification ──► Device Delivery ──► Real-time Alert                  │
│                                                                             │
│  Step 6: Agent Response                                                     │
│  ──────────────────────                                                     │
│  Agent Reply ──► publishOutbound ──► Carrier API ──► Customer              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step Configuration

Each workflow step can be configured through environment variables and DynamoDB configuration tables:

```typescript
// Workflow step configuration
interface WorkflowStepConfig {
  stepId: string;
  enabled: boolean;
  timeout: number;
  retryPolicy: {
    maxRetries: number;
    backoffMultiplier: number;
    maxBackoff: number;
  };
  conditions: StepCondition[];
  nextSteps: NextStepConfig[];
}

const defaultStepConfigs: WorkflowStepConfig[] = [
  {
    stepId: 'workFlowIdentityLookup',
    enabled: true,
    timeout: 30000,
    retryPolicy: {
      maxRetries: 3,
      backoffMultiplier: 2,
      maxBackoff: 10000,
    },
    conditions: [],
    nextSteps: [
      { stepId: 'workFlowBiDirectional', condition: 'always' },
    ],
  },
  {
    stepId: 'workFlowBiDirectional',
    enabled: true,
    timeout: 30000,
    retryPolicy: {
      maxRetries: 3,
      backoffMultiplier: 2,
      maxBackoff: 10000,
    },
    conditions: [],
    nextSteps: [
      { stepId: 'workFlowPreRoute', condition: 'always' },
    ],
  },
  {
    stepId: 'workFlowPreRoute',
    enabled: true,
    timeout: 45000,
    retryPolicy: {
      maxRetries: 3,
      backoffMultiplier: 2,
      maxBackoff: 15000,
    },
    conditions: [],
    nextSteps: [
      { stepId: 'publishOutbound', condition: 'auto_response_enabled' },
      { stepId: 'pushNotification', condition: 'route_to_agent' },
      { stepId: 'terminate', condition: 'blocked' },
    ],
  },
];
```

### Error Handling and Dead Letter Queues

All workflow functions implement standardized error handling with dead letter queue support:

```typescript
// Dead letter queue configuration
const dlqConfig = {
  queueName: 'workflow-dlq',
  messageRetentionPeriod: 1209600, // 14 days
  visibilityTimeout: 300,
  maxReceiveCount: 3,
};

// Error handling wrapper
async function withErrorHandling<T>(
  fn: () => Promise<T>,
  context: WorkflowContext
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof WorkflowError && error.retryable) {
      throw error; // Allow Lambda retry
    }
    
    // Send to DLQ for non-retryable errors
    await sendToDLQ({
      correlationId: context.correlationId,
      stepId: context.stepId,
      error: {
        message: error.message,
        stack: error.stack,
        code: error.code,
      },
      originalEvent: context.originalEvent,
      timestamp: new Date().toISOString(),
    });
    
    throw error;
  }
}
```

### Monitoring and Observability

All workflow Lambda functions emit standardized metrics and logs:

```typescript
// Metrics emission
const metrics = {
  namespace: 'OmniChannel/Workflow',
  dimensions: {
    FunctionName: context.functionName,
    AccountId: event.routing?.accountId,
    Carrier: event.carrier,
  },
};

await cloudWatch.putMetricData({
  Namespace: metrics.namespace,
  MetricData: [
    {
      MetricName: 'ProcessingTime',
      Value: processingTime,
      Unit: 'Milliseconds',
      Dimensions: Object.entries(metrics.dimensions).map(([Name, Value]) => ({
        Name,
        Value,
      })),
    },
    {
      MetricName: 'MessageProcessed',
      Value: 1,
      Unit: 'Count',
      Dimensions: Object.entries(metrics.dimensions).map(([Name, Value]) => ({
        Name,
        Value,
      })),
    },
  ],
});
```

### Best Practices

1. **Idempotency**: All workflow functions should be idempotent, using correlation IDs to prevent duplicate processing.

2. **Timeout Configuration**: Set appropriate timeouts for each function based on expected processing time plus buffer.

3. **Cold Start Optimization**: Use provisioned concurrency for latency-sensitive functions like `workFlowIdentityLookup`.

4. **Batch Processing**: Utilize SQS batching for high-volume scenarios to reduce Lambda invocations.

5. **Circuit Breakers**: Implement circuit breaker patterns for external carrier API calls to prevent cascade failures.