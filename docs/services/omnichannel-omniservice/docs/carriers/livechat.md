# LiveChat Integration

## Overview

The LiveChat Integration within the omnichannel-omniservice provides seamless connectivity between your messaging infrastructure and LiveChat's real-time customer communication platform. This integration enables bidirectional message routing, allowing your agents to handle customer conversations through LiveChat while maintaining unified message processing across all supported carriers.

LiveChat is a powerful customer service platform that provides real-time chat capabilities, visitor tracking, and agent management features. The omnichannel-omniservice integration abstracts the complexity of LiveChat's API, providing a standardized interface for message handling that aligns with other carrier integrations in the system.

### Key Capabilities

- **Real-time bidirectional messaging**: Send and receive messages through LiveChat in real-time
- **Webhook-based event processing**: Receive instant notifications for chat events, messages, and status changes
- **Agent routing**: Route conversations to appropriate agents based on configurable rules
- **Rich media support**: Handle text, files, images, and other media types
- **Conversation state management**: Track and manage conversation lifecycle events
- **Unified message format**: Messages are normalized to the omnichannel standard format

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   LiveChat      │────▶│  Webhook Receiver    │────▶│  Message        │
│   Platform      │     │  (AWS Lambda)        │     │  Router         │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        ▲                                                    │
        │                                                    ▼
        │               ┌──────────────────────┐     ┌─────────────────┐
        └───────────────│  Outbound Handler    │◀────│  Workflow       │
                        │  (AWS Lambda)        │     │  Processor      │
                        └──────────────────────┘     └─────────────────┘
```

## Setup Requirements

### Prerequisites

Before configuring the LiveChat integration, ensure you have the following:

1. **LiveChat Account**: An active LiveChat account with API access enabled
2. **API Credentials**: LiveChat API key and account ID
3. **AWS Infrastructure**: Deployed Lambda functions and API Gateway endpoints
4. **DynamoDB Tables**: Required tables for message and conversation storage

### Environment Configuration

Configure the following environment variables in your Lambda functions:

```typescript
// Environment variables for LiveChat integration
interface LiveChatConfig {
  LIVECHAT_API_KEY: string;          // Your LiveChat API key
  LIVECHAT_ACCOUNT_ID: string;       // Your LiveChat account identifier
  LIVECHAT_WEBHOOK_SECRET: string;   // Secret for webhook signature validation
  LIVECHAT_API_BASE_URL: string;     // Base URL for LiveChat API (default: https://api.livechatinc.com)
  LIVECHAT_API_VERSION: string;      // API version (default: v3.4)
}
```

### Installation Steps

1. **Install Dependencies**

```bash
# Navigate to the livechat package directory
cd packages/livechat

# Install required dependencies
npm install

# Build the package
npm run build
```

2. **Configure API Credentials**

Create or update your configuration in the secrets manager or environment:

```typescript
// packages/livechat/src/config/livechat.config.ts
import { LiveChatConfig } from '../types';

export const liveChatConfig: LiveChatConfig = {
  apiKey: process.env.LIVECHAT_API_KEY!,
  accountId: process.env.LIVECHAT_ACCOUNT_ID!,
  webhookSecret: process.env.LIVECHAT_WEBHOOK_SECRET!,
  apiBaseUrl: process.env.LIVECHAT_API_BASE_URL || 'https://api.livechatinc.com',
  apiVersion: process.env.LIVECHAT_API_VERSION || 'v3.4',
};
```

3. **Deploy Lambda Functions**

```bash
# Deploy the LiveChat webhook receiver
npm run deploy:livechat-webhook

# Deploy the LiveChat outbound handler
npm run deploy:livechat-outbound
```

4. **Verify Deployment**

```bash
# Test the webhook endpoint
curl -X POST https://your-api-gateway-url/livechat/webhook \
  -H "Content-Type: application/json" \
  -d '{"action": "ping"}'
```

### Required IAM Permissions

Ensure your Lambda execution role includes the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/messages",
        "arn:aws:dynamodb:*:*:table/conversations"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:livechat/*"
    }
  ]
}
```

## Webhook Configuration

### Setting Up Webhooks in LiveChat

1. **Access LiveChat Developer Console**
   - Navigate to https://developers.livechatinc.com/console/
   - Select your application or create a new one

2. **Register Webhook URL**

```typescript
// Example webhook registration using LiveChat API
import axios from 'axios';

async function registerWebhook(webhookUrl: string): Promise<void> {
  const response = await axios.post(
    'https://api.livechatinc.com/v3.4/configuration/action/register_webhook',
    {
      url: webhookUrl,
      description: 'Omnichannel Service Webhook',
      action: 'incoming_chat',
      secret_key: process.env.LIVECHAT_WEBHOOK_SECRET,
      owner_client_id: process.env.LIVECHAT_CLIENT_ID,
    },
    {
      headers: {
        'Authorization': `Bearer ${process.env.LIVECHAT_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
    }
  );
  
  console.log('Webhook registered:', response.data);
}
```

### Supported Webhook Events

Configure webhooks for the following events:

| Event Name | Description | Handler |
|------------|-------------|---------|
| `incoming_chat` | New chat session started | `handleIncomingChat` |
| `incoming_event` | New message received in chat | `handleIncomingEvent` |
| `chat_deactivated` | Chat session ended | `handleChatDeactivated` |
| `agent_changed` | Agent assigned/reassigned | `handleAgentChanged` |
| `chat_transferred` | Chat transferred to another agent | `handleChatTransferred` |
| `incoming_rich_message_postback` | User clicked rich message button | `handleRichMessagePostback` |

### Webhook Handler Implementation

```typescript
// packages/livechat/src/handlers/webhook.handler.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { verifyWebhookSignature } from '../utils/security';
import { LiveChatWebhookPayload } from '../types';
import { MessageRouter } from '@omnichannel/core';

export async function handleWebhook(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  try {
    // Verify webhook signature
    const signature = event.headers['X-Signature'];
    const isValid = verifyWebhookSignature(
      event.body!,
      signature!,
      process.env.LIVECHAT_WEBHOOK_SECRET!
    );

    if (!isValid) {
      return {
        statusCode: 401,
        body: JSON.stringify({ error: 'Invalid signature' }),
      };
    }

    const payload: LiveChatWebhookPayload = JSON.parse(event.body!);

    // Route based on webhook action
    switch (payload.action) {
      case 'incoming_chat':
        await handleIncomingChat(payload);
        break;
      case 'incoming_event':
        await handleIncomingEvent(payload);
        break;
      case 'chat_deactivated':
        await handleChatDeactivated(payload);
        break;
      default:
        console.log('Unhandled webhook action:', payload.action);
    }

    return {
      statusCode: 200,
      body: JSON.stringify({ success: true }),
    };
  } catch (error) {
    console.error('Webhook processing error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
}

async function handleIncomingChat(payload: LiveChatWebhookPayload): Promise<void> {
  const normalizedMessage = normalizeLiveChatMessage(payload);
  await MessageRouter.route(normalizedMessage);
}

async function handleIncomingEvent(payload: LiveChatWebhookPayload): Promise<void> {
  // Process incoming message event
  const { chat_id, event } = payload.payload;
  
  if (event.type === 'message') {
    const normalizedMessage = {
      id: event.id,
      conversationId: chat_id,
      carrier: 'livechat',
      direction: 'inbound',
      content: event.text,
      timestamp: new Date(event.created_at),
      metadata: {
        authorId: event.author_id,
        authorType: event.author_type,
      },
    };

    await MessageRouter.route(normalizedMessage);
  }
}

async function handleChatDeactivated(payload: LiveChatWebhookPayload): Promise<void> {
  // Handle conversation closure
  const { chat_id } = payload.payload;
  await ConversationService.close(chat_id, 'livechat');
}
```

### Webhook Signature Verification

```typescript
// packages/livechat/src/utils/security.ts
import crypto from 'crypto';

export function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}
```

## Message Types Supported

### Text Messages

Standard text messages are the most common type:

```typescript
// Inbound text message structure
interface LiveChatTextMessage {
  type: 'message';
  id: string;
  created_at: string;
  author_id: string;
  text: string;
  properties?: Record<string, unknown>;
}

// Sending outbound text message
async function sendTextMessage(chatId: string, text: string): Promise<void> {
  await liveChatClient.sendEvent(chatId, {
    type: 'message',
    text: text,
    visibility: 'all',
  });
}
```

### File Attachments

Support for file uploads including documents, images, and other media:

```typescript
interface LiveChatFileMessage {
  type: 'file';
  id: string;
  created_at: string;
  author_id: string;
  name: string;
  url: string;
  content_type: string;
  size: number;
  thumbnail_url?: string;
}

// Handling file attachments
async function handleFileMessage(
  payload: LiveChatFileMessage
): Promise<NormalizedMessage> {
  // Download and store file if needed
  const fileMetadata = await MediaService.processFile({
    url: payload.url,
    filename: payload.name,
    contentType: payload.content_type,
  });

  return {
    id: payload.id,
    type: 'file',
    content: payload.url,
    metadata: {
      filename: payload.name,
      contentType: payload.content_type,
      size: payload.size,
      localPath: fileMetadata.storagePath,
    },
  };
}
```

### Rich Messages

Interactive messages with buttons, cards, and quick replies:

```typescript
interface LiveChatRichMessage {
  type: 'rich_message';
  id: string;
  template_id: string;
  elements: RichMessageElement[];
}

interface RichMessageElement {
  title: string;
  subtitle?: string;
  image?: {
    url: string;
  };
  buttons?: Array<{
    text: string;
    type: 'webview' | 'message' | 'url';
    value: string;
    postback_id: string;
  }>;
}

// Sending rich message
async function sendRichMessage(
  chatId: string,
  template: RichMessageTemplate
): Promise<void> {
  await liveChatClient.sendEvent(chatId, {
    type: 'rich_message',
    template_id: template.id,
    elements: template.elements,
  });
}
```

### System Messages

Handling system events and notifications:

```typescript
interface LiveChatSystemMessage {
  type: 'system_message';
  id: string;
  created_at: string;
  text: string;
  system_message_type: 'routing.archived' | 'routing.idle' | 'routing.unassigned';
}
```

### Message Normalization

All LiveChat message types are normalized to the omnichannel standard format:

```typescript
// packages/livechat/src/utils/normalizer.ts
import { NormalizedMessage, LiveChatEvent } from '../types';

export function normalizeLiveChatMessage(
  event: LiveChatEvent
): NormalizedMessage {
  const baseMessage = {
    id: event.id,
    carrier: 'livechat' as const,
    direction: 'inbound' as const,
    timestamp: new Date(event.created_at),
    rawPayload: event,
  };

  switch (event.type) {
    case 'message':
      return {
        ...baseMessage,
        type: 'text',
        content: event.text,
      };

    case 'file':
      return {
        ...baseMessage,
        type: 'media',
        content: event.url,
        metadata: {
          filename: event.name,
          contentType: event.content_type,
          size: event.size,
        },
      };

    case 'rich_message':
      return {
        ...baseMessage,
        type: 'interactive',
        content: JSON.stringify(event.elements),
        metadata: {
          templateId: event.template_id,
        },
      };

    default:
      return {
        ...baseMessage,
        type: 'unknown',
        content: JSON.stringify(event),
      };
  }
}
```

## Error Handling

### Error Categories

The LiveChat integration handles several categories of errors:

| Error Category | HTTP Codes | Retry Strategy |
|---------------|------------|----------------|
| Authentication | 401, 403 | No retry, alert required |
| Rate Limiting | 429 | Exponential backoff |
| Server Errors | 500, 502, 503 | Retry with backoff |
| Client Errors | 400, 404 | No retry, log error |
| Network Errors | N/A | Retry with backoff |

### Error Handler Implementation

```typescript
// packages/livechat/src/utils/error-handler.ts
import { LiveChatError, RetryConfig } from '../types';

export class LiveChatErrorHandler {
  private static readonly DEFAULT_RETRY_CONFIG: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    exponentialBase: 2,
  };

  static async withRetry<T>(
    operation: () => Promise<T>,
    config: RetryConfig = this.DEFAULT_RETRY_CONFIG
  ): Promise<T> {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        
        if (!this.isRetryable(error)) {
          throw error;
        }

        if (attempt < config.maxRetries) {
          const delay = this.calculateDelay(attempt, config);
          console.log(`Retry attempt ${attempt + 1} after ${delay}ms`);
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  private static isRetryable(error: unknown): boolean {
    if (error instanceof LiveChatApiError) {
      const retryableCodes = [429, 500, 502, 503, 504];
      return retryableCodes.includes(error.statusCode);
    }
    
    // Network errors are retryable
    if (error instanceof Error && error.message.includes('ECONNRESET')) {
      return true;
    }

    return false;
  }

  private static calculateDelay(attempt: number, config: RetryConfig): number {
    const delay = config.baseDelay * Math.pow(config.exponentialBase, attempt);
    return Math.min(delay, config.maxDelay);
  }

  private static sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Custom error class for LiveChat API errors
export class LiveChatApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly errorCode?: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'LiveChatApiError';
  }
}
```

### Rate Limit Handling

```typescript
// packages/livechat/src/utils/rate-limiter.ts
import { RateLimiter } from 'limiter';

export class LiveChatRateLimiter {
  private limiter: RateLimiter;

  constructor() {
    // LiveChat allows 10 requests per second by default
    this.limiter = new RateLimiter({
      tokensPerInterval: 10,
      interval: 'second',
    });
  }

  async acquire(): Promise<void> {
    const remainingRequests = await this.limiter.removeTokens(1);
    
    if (remainingRequests < 0) {
      // Wait for token to become available
      await this.sleep(Math.abs(remainingRequests) * 100);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### Dead Letter Queue Processing

Failed messages are sent to a DLQ for later processing:

```typescript
// packages/livechat/src/handlers/dlq.handler.ts
import { SQSEvent, SQSHandler } from 'aws-lambda';
import { AlertService } from '@omnichannel/core';

export const handleDLQ: SQSHandler = async (event: SQSEvent) => {
  for (const record of event.Records) {
    const failedMessage = JSON.parse(record.body);
    
    console.error('Processing failed message from DLQ:', {
      messageId: failedMessage.id,
      error: failedMessage.error,
      attempts: failedMessage.attempts,
    });

    // Alert if message has failed multiple times
    if (failedMessage.attempts >= 3) {
      await AlertService.sendAlert({
        severity: 'high',
        title: 'LiveChat Message Processing Failed',
        message: `Message ${failedMessage.id} failed after ${failedMessage.attempts} attempts`,
        metadata: failedMessage,
      });
    }

    // Attempt to reprocess or archive
    try {
      await reprocessMessage(failedMessage);
    } catch (error) {
      await archiveFailedMessage(failedMessage, error);
    }
  }
};
```

### Logging and Monitoring

```typescript
// packages/livechat/src/utils/logger.ts
import { Logger } from '@omnichannel/core';

export const liveChatLogger = new Logger({
  service: 'livechat-integration',
  level: process.env.LOG_LEVEL || 'info',
});

// Usage in handlers
liveChatLogger.info('Processing incoming chat', {
  chatId: payload.chat_id,
  visitorId: payload.visitor_id,
});

liveChatLogger.error('Failed to send message', {
  chatId,
  error: error.message,
  stack: error.stack,
});
```

### Best Practices for Error Handling

1. **Always validate webhook signatures** before processing any payload
2. **Implement idempotency** using message IDs to prevent duplicate processing
3. **Use structured logging** for easier debugging and monitoring
4. **Set up CloudWatch alarms** for error rate thresholds
5. **Implement circuit breakers** for external API calls
6. **Store failed messages** in DLQ for manual review and reprocessing
7. **Monitor rate limit headers** and adjust request patterns accordingly

```typescript
// Example circuit breaker implementation
import CircuitBreaker from 'opossum';

const options = {
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
};

const breaker = new CircuitBreaker(sendToLiveChat, options);

breaker.on('open', () => {
  liveChatLogger.warn('Circuit breaker opened - LiveChat API unavailable');
});

breaker.on('halfOpen', () => {
  liveChatLogger.info('Circuit breaker half-open - testing LiveChat API');
});

breaker.on('close', () => {
  liveChatLogger.info('Circuit breaker closed - LiveChat API recovered');
});
```

---

## Additional Resources

- [LiveChat Platform API Documentation](https://developers.livechatinc.com/docs/messaging/api/)
- [Omnichannel Service Architecture Guide](./architecture.md)
- [Carrier Integration Patterns](./carrier-patterns.md)
- [Monitoring and Alerting Setup](./monitoring.md)