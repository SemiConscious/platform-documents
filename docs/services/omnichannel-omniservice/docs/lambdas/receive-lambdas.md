# Receive Lambda Functions

## Overview

The Omnichannel-Omniservice platform implements a robust, carrier-agnostic message reception architecture through a series of specialized Lambda functions. Each receive Lambda function serves as the entry point for incoming messages from different communication carriers, normalizing diverse message formats into a unified internal structure for downstream processing.

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│ receiveWhatsApp  │────▶│                 │
└─────────────────┘     └──────────────────┘     │                 │
                                                 │                 │
┌─────────────────┐     ┌──────────────────┐     │                 │
│   Bandwidth     │────▶│ receiveBandwidth │────▶│   Unified       │
└─────────────────┘     └──────────────────┘     │   Message       │
                                                 │   Pipeline      │
┌─────────────────┐     ┌──────────────────┐     │                 │
│   Twilio        │────▶│ receiveTwilio    │────▶│                 │
└─────────────────┘     └──────────────────┘     │                 │
                                                 │                 │
┌─────────────────┐     ┌──────────────────┐     │                 │
│   LiveChat      │────▶│ receiveLiveChat  │────▶│                 │
└─────────────────┘     └──────────────────┘     │                 │
                                                 │                 │
┌─────────────────┐     ┌──────────────────┐     │                 │
│   Messagebird   │────▶│ receiveMessagebird────▶│                 │
└─────────────────┘     └──────────────────┘     │                 │
                                                 │                 │
┌─────────────────┐     ┌──────────────────┐     │                 │
│   Inteliquent   │────▶│ receiveInteliquent───▶│                 │
└─────────────────┘     └──────────────────┘     │                 │
                                                 │                 │
┌─────────────────┐     ┌──────────────────┐     │                 │
│   Test Carrier  │────▶│ receiveTestCarrier───▶│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Common Responsibilities

All receive Lambda functions share these core responsibilities:

1. **Webhook Validation**: Verify incoming requests are authentic and from the expected carrier
2. **Payload Parsing**: Extract message content from carrier-specific formats
3. **Message Normalization**: Transform messages into the unified `InboundMessage` format
4. **Event Publishing**: Dispatch normalized messages to the processing pipeline
5. **Acknowledgment**: Return appropriate responses to carrier webhooks
6. **Error Handling**: Log errors and handle failures gracefully without losing messages

---

## receiveWhatsApp

### Purpose

The `receiveWhatsApp` Lambda function processes incoming messages from the WhatsApp Business API, including text messages, media messages, location sharing, and interactive message responses.

### Endpoint Configuration

```yaml
# serverless.yml
receiveWhatsApp:
  handler: src/handlers/receive/whatsapp.handler
  events:
    - http:
        path: /webhooks/whatsapp
        method: POST
    - http:
        path: /webhooks/whatsapp
        method: GET  # For webhook verification
```

### Webhook Verification

WhatsApp requires webhook verification via a GET request challenge:

```typescript
// src/handlers/receive/whatsapp.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { WhatsAppWebhookValidator } from '../validators/whatsapp-validator';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // Handle webhook verification (GET request)
  if (event.httpMethod === 'GET') {
    return handleVerification(event);
  }
  
  // Handle incoming messages (POST request)
  return handleIncomingMessage(event);
};

const handleVerification = (event: APIGatewayProxyEvent): APIGatewayProxyResult => {
  const mode = event.queryStringParameters?.['hub.mode'];
  const token = event.queryStringParameters?.['hub.verify_token'];
  const challenge = event.queryStringParameters?.['hub.challenge'];

  if (mode === 'subscribe' && token === process.env.WHATSAPP_VERIFY_TOKEN) {
    return {
      statusCode: 200,
      body: challenge || '',
    };
  }

  return {
    statusCode: 403,
    body: JSON.stringify({ error: 'Verification failed' }),
  };
};
```

### Message Processing

```typescript
// src/handlers/receive/whatsapp.ts
import { WhatsAppInboundPayload, WhatsAppMessage } from '../../types/whatsapp';
import { InboundMessage, MessageType } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';

const handleIncomingMessage = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  const validator = new WhatsAppWebhookValidator();
  
  // Validate signature
  const signature = event.headers['x-hub-signature-256'];
  if (!validator.validateSignature(event.body!, signature)) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Invalid signature' }),
    };
  }

  const payload: WhatsAppInboundPayload = JSON.parse(event.body!);
  
  // Process each entry in the webhook payload
  for (const entry of payload.entry) {
    for (const change of entry.changes) {
      if (change.field === 'messages') {
        for (const message of change.value.messages || []) {
          const normalizedMessage = normalizeWhatsAppMessage(message, change.value);
          await publishToEventBridge(normalizedMessage);
        }
      }
    }
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ status: 'received' }),
  };
};

const normalizeWhatsAppMessage = (
  message: WhatsAppMessage,
  metadata: WhatsAppChangeValue
): InboundMessage => {
  return {
    messageId: message.id,
    carrier: 'whatsapp',
    carrierMessageId: message.id,
    from: message.from,
    to: metadata.metadata.display_phone_number,
    timestamp: new Date(parseInt(message.timestamp) * 1000).toISOString(),
    type: mapWhatsAppMessageType(message.type),
    content: extractMessageContent(message),
    metadata: {
      profileName: metadata.contacts?.[0]?.profile?.name,
      businessPhoneNumberId: metadata.metadata.phone_number_id,
    },
  };
};
```

### Supported Message Types

| WhatsApp Type | Unified Type | Description |
|---------------|--------------|-------------|
| `text` | `TEXT` | Plain text messages |
| `image` | `IMAGE` | Image attachments with optional caption |
| `video` | `VIDEO` | Video attachments |
| `audio` | `AUDIO` | Voice notes and audio files |
| `document` | `DOCUMENT` | Document attachments (PDF, etc.) |
| `location` | `LOCATION` | Shared location coordinates |
| `contacts` | `CONTACT` | Shared contact cards |
| `interactive` | `INTERACTIVE` | Button/list responses |
| `button` | `BUTTON_RESPONSE` | Quick reply button responses |

---

## receiveBandwidth

### Purpose

The `receiveBandwidth` Lambda function handles incoming SMS/MMS messages from Bandwidth's messaging platform.

### Endpoint Configuration

```yaml
# serverless.yml
receiveBandwidth:
  handler: src/handlers/receive/bandwidth.handler
  events:
    - http:
        path: /webhooks/bandwidth
        method: POST
```

### Implementation

```typescript
// src/handlers/receive/bandwidth.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { BandwidthCallback, BandwidthMessageType } from '../../types/bandwidth';
import { InboundMessage } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';
import { BandwidthValidator } from '../validators/bandwidth-validator';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const validator = new BandwidthValidator();
  
  // Validate Basic Auth credentials
  const authHeader = event.headers['Authorization'];
  if (!validator.validateBasicAuth(authHeader)) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Unauthorized' }),
    };
  }

  const callbacks: BandwidthCallback[] = JSON.parse(event.body!);
  
  for (const callback of callbacks) {
    // Only process message-received callbacks
    if (callback.type === 'message-received') {
      const normalizedMessage = normalizeBandwidthMessage(callback);
      await publishToEventBridge(normalizedMessage);
    }
    
    // Handle delivery receipts separately
    if (callback.type === 'message-delivered' || callback.type === 'message-failed') {
      await handleDeliveryReceipt(callback);
    }
  }

  return {
    statusCode: 200,
    body: '',
  };
};

const normalizeBandwidthMessage = (callback: BandwidthCallback): InboundMessage => {
  const message = callback.message;
  
  return {
    messageId: generateMessageId(),
    carrier: 'bandwidth',
    carrierMessageId: message.id,
    from: message.from,
    to: message.to[0], // Bandwidth sends as array
    timestamp: callback.time,
    type: message.media?.length ? 'MMS' : 'SMS',
    content: {
      text: message.text,
      media: message.media?.map(url => ({
        url,
        type: inferMediaType(url),
      })),
    },
    metadata: {
      direction: message.direction,
      segmentCount: message.segmentCount,
      applicationId: message.applicationId,
    },
  };
};
```

### Bandwidth Callback Types

| Callback Type | Action |
|---------------|--------|
| `message-received` | Process as inbound message |
| `message-delivered` | Update delivery status |
| `message-failed` | Log failure and trigger retry logic |
| `message-sending` | Update status to "sending" |

---

## receiveTwilio

### Purpose

The `receiveTwilio` Lambda function processes incoming SMS/MMS messages via Twilio's webhook system.

### Endpoint Configuration

```yaml
# serverless.yml
receiveTwilio:
  handler: src/handlers/receive/twilio.handler
  events:
    - http:
        path: /webhooks/twilio
        method: POST
```

### Implementation

```typescript
// src/handlers/receive/twilio.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import * as twilio from 'twilio';
import { TwilioInboundPayload } from '../../types/twilio';
import { InboundMessage } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // Validate Twilio signature
  const twilioSignature = event.headers['X-Twilio-Signature'];
  const url = `https://${event.headers.Host}${event.path}`;
  
  const params = parseFormUrlEncoded(event.body!);
  
  const isValid = twilio.validateRequest(
    process.env.TWILIO_AUTH_TOKEN!,
    twilioSignature,
    url,
    params
  );

  if (!isValid) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Invalid signature' }),
    };
  }

  const payload = params as TwilioInboundPayload;
  const normalizedMessage = normalizeTwilioMessage(payload);
  
  await publishToEventBridge(normalizedMessage);

  // Return TwiML response (empty response to acknowledge)
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/xml',
    },
    body: '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
  };
};

const normalizeTwilioMessage = (payload: TwilioInboundPayload): InboundMessage => {
  const mediaItems = [];
  
  // Twilio sends media as NumMedia and MediaUrl0, MediaUrl1, etc.
  const numMedia = parseInt(payload.NumMedia || '0');
  for (let i = 0; i < numMedia; i++) {
    mediaItems.push({
      url: payload[`MediaUrl${i}`],
      contentType: payload[`MediaContentType${i}`],
    });
  }

  return {
    messageId: generateMessageId(),
    carrier: 'twilio',
    carrierMessageId: payload.MessageSid,
    from: payload.From,
    to: payload.To,
    timestamp: new Date().toISOString(),
    type: numMedia > 0 ? 'MMS' : 'SMS',
    content: {
      text: payload.Body,
      media: mediaItems,
    },
    metadata: {
      accountSid: payload.AccountSid,
      messagingServiceSid: payload.MessagingServiceSid,
      fromCity: payload.FromCity,
      fromState: payload.FromState,
      fromCountry: payload.FromCountry,
    },
  };
};

const parseFormUrlEncoded = (body: string): Record<string, string> => {
  const params: Record<string, string> = {};
  const pairs = body.split('&');
  
  for (const pair of pairs) {
    const [key, value] = pair.split('=');
    params[decodeURIComponent(key)] = decodeURIComponent(value || '');
  }
  
  return params;
};
```

---

## receiveLiveChat

### Purpose

The `receiveLiveChat` Lambda function handles incoming messages from LiveChat integrations, supporting real-time chat sessions with agents and customers.

### Endpoint Configuration

```yaml
# serverless.yml
receiveLiveChat:
  handler: src/handlers/receive/livechat.handler
  events:
    - http:
        path: /webhooks/livechat
        method: POST
```

### Implementation

```typescript
// src/handlers/receive/livechat.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import * as crypto from 'crypto';
import { LiveChatWebhookPayload, LiveChatEventType } from '../../types/livechat';
import { InboundMessage } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // Validate webhook signature
  const signature = event.headers['X-Signature'];
  const expectedSignature = crypto
    .createHmac('sha256', process.env.LIVECHAT_WEBHOOK_SECRET!)
    .update(event.body!)
    .digest('hex');

  if (signature !== expectedSignature) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Invalid signature' }),
    };
  }

  const payload: LiveChatWebhookPayload = JSON.parse(event.body!);
  
  // Handle different LiveChat event types
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
      console.log(`Unhandled LiveChat action: ${payload.action}`);
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ status: 'processed' }),
  };
};

const handleIncomingEvent = async (payload: LiveChatWebhookPayload): Promise<void> => {
  const { chat_id, event } = payload.payload;
  
  // Only process message events
  if (event.type !== 'message') {
    return;
  }

  const normalizedMessage: InboundMessage = {
    messageId: generateMessageId(),
    carrier: 'livechat',
    carrierMessageId: event.id,
    from: event.author_id,
    to: chat_id,
    timestamp: event.created_at,
    type: 'CHAT',
    content: {
      text: event.text,
      media: event.attachments?.map(att => ({
        url: att.url,
        type: att.content_type,
        name: att.name,
      })),
    },
    metadata: {
      chatId: chat_id,
      threadId: payload.payload.thread_id,
      authorType: event.author_type, // 'customer' or 'agent'
      visibility: event.visibility,
    },
  };

  await publishToEventBridge(normalizedMessage);
};
```

### LiveChat Event Types

| Event Type | Description |
|------------|-------------|
| `incoming_chat` | New chat session started |
| `incoming_event` | New message or event in existing chat |
| `chat_deactivated` | Chat session ended |
| `chat_transferred` | Chat transferred to another agent/group |
| `agent_assigned` | Agent assigned to chat |

---

## receiveMessagebird

### Purpose

The `receiveMessagebird` Lambda function processes incoming messages from Messagebird's Conversations API, supporting SMS, WhatsApp, and other channels through a unified interface.

### Endpoint Configuration

```yaml
# serverless.yml
receiveMessagebird:
  handler: src/handlers/receive/messagebird.handler
  events:
    - http:
        path: /webhooks/messagebird
        method: POST
```

### Implementation

```typescript
// src/handlers/receive/messagebird.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import * as crypto from 'crypto';
import { 
  MessagebirdWebhookPayload, 
  MessagebirdMessage,
  MessagebirdChannel 
} from '../../types/messagebird';
import { InboundMessage } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // Validate webhook signature
  const signature = event.headers['MessageBird-Signature'];
  const timestamp = event.headers['MessageBird-Request-Timestamp'];
  
  if (!validateMessagebirdSignature(event.body!, signature, timestamp)) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Invalid signature' }),
    };
  }

  const payload: MessagebirdWebhookPayload = JSON.parse(event.body!);
  
  // Handle message.created webhook
  if (payload.type === 'message.created' && payload.message.direction === 'received') {
    const normalizedMessage = normalizeMessagebirdMessage(payload);
    await publishToEventBridge(normalizedMessage);
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ status: 'received' }),
  };
};

const validateMessagebirdSignature = (
  body: string,
  signature: string,
  timestamp: string
): boolean => {
  const payload = timestamp + '\n' + body;
  const expectedSignature = crypto
    .createHmac('sha256', process.env.MESSAGEBIRD_SIGNING_KEY!)
    .update(payload)
    .digest('base64');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
};

const normalizeMessagebirdMessage = (payload: MessagebirdWebhookPayload): InboundMessage => {
  const { message, conversation } = payload;
  
  return {
    messageId: generateMessageId(),
    carrier: 'messagebird',
    carrierMessageId: message.id,
    from: message.from,
    to: message.to,
    timestamp: message.createdDatetime,
    type: mapMessagebirdType(message.type),
    content: extractMessagebirdContent(message),
    metadata: {
      conversationId: conversation.id,
      channelId: conversation.channelId,
      platform: message.platform, // 'sms', 'whatsapp', 'facebook', etc.
      contactId: conversation.contact.id,
    },
  };
};

const extractMessagebirdContent = (message: MessagebirdMessage): MessageContent => {
  switch (message.type) {
    case 'text':
      return { text: message.content.text };
    case 'image':
      return {
        media: [{
          url: message.content.image.url,
          type: 'image',
          caption: message.content.image.caption,
        }],
      };
    case 'location':
      return {
        location: {
          latitude: message.content.location.latitude,
          longitude: message.content.location.longitude,
        },
      };
    default:
      return { text: JSON.stringify(message.content) };
  }
};
```

---

## receiveInteliquent

### Purpose

The `receiveInteliquent` Lambda function processes incoming SMS messages from Inteliquent's messaging platform, primarily used for toll-free and local number messaging.

### Endpoint Configuration

```yaml
# serverless.yml
receiveInteliquent:
  handler: src/handlers/receive/inteliquent.handler
  events:
    - http:
        path: /webhooks/inteliquent
        method: POST
```

### Implementation

```typescript
// src/handlers/receive/inteliquent.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { InteliquentInboundPayload } from '../../types/inteliquent';
import { InboundMessage } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // Inteliquent uses IP whitelisting and API key validation
  const apiKey = event.headers['X-API-Key'];
  
  if (apiKey !== process.env.INTELIQUENT_WEBHOOK_API_KEY) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Unauthorized' }),
    };
  }

  // Inteliquent sends XML payload
  const payload = parseInteliquentXML(event.body!);
  
  // Handle multiple messages in batch
  for (const message of payload.messages) {
    const normalizedMessage = normalizeInteliquentMessage(message);
    await publishToEventBridge(normalizedMessage);
  }

  // Return acknowledgment in expected format
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/xml',
    },
    body: '<?xml version="1.0"?><response><status>ok</status></response>',
  };
};

const normalizeInteliquentMessage = (message: InteliquentMessage): InboundMessage => {
  return {
    messageId: generateMessageId(),
    carrier: 'inteliquent',
    carrierMessageId: message.messageId,
    from: normalizePhoneNumber(message.from),
    to: normalizePhoneNumber(message.to),
    timestamp: new Date(message.timestamp).toISOString(),
    type: 'SMS',
    content: {
      text: message.body,
    },
    metadata: {
      carrier: message.carrier,
      region: message.region,
      encoding: message.encoding,
    },
  };
};

const parseInteliquentXML = (xmlBody: string): InteliquentInboundPayload => {
  // XML parsing implementation
  const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: '@_',
  });
  
  return parser.parse(xmlBody);
};
```

---

## receiveTestCarrier

### Purpose

The `receiveTestCarrier` Lambda function provides a testing endpoint for development and integration testing, simulating carrier behavior without connecting to actual carrier APIs.

### Endpoint Configuration

```yaml
# serverless.yml
receiveTestCarrier:
  handler: src/handlers/receive/test-carrier.handler
  events:
    - http:
        path: /webhooks/test
        method: POST
```

### Implementation

```typescript
// src/handlers/receive/test-carrier.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { InboundMessage } from '../../types/unified';
import { publishToEventBridge } from '../../services/event-bridge';

interface TestCarrierPayload {
  from: string;
  to: string;
  text?: string;
  mediaUrl?: string;
  mediaType?: string;
  simulateError?: boolean;
  errorType?: 'timeout' | 'invalid' | 'server_error';
  delay?: number;
}

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // Only allow in non-production environments
  if (process.env.ENVIRONMENT === 'production') {
    return {
      statusCode: 404,
      body: JSON.stringify({ error: 'Not found' }),
    };
  }

  // Simple API key validation for test endpoint
  const testApiKey = event.headers['X-Test-API-Key'];
  if (testApiKey !== process.env.TEST_CARRIER_API_KEY) {
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Unauthorized' }),
    };
  }

  const payload: TestCarrierPayload = JSON.parse(event.body!);

  // Simulate delay if requested
  if (payload.delay) {
    await sleep(payload.delay);
  }

  // Simulate errors for testing error handling
  if (payload.simulateError) {
    return handleSimulatedError(payload.errorType);
  }

  const normalizedMessage: InboundMessage = {
    messageId: generateMessageId(),
    carrier: 'test',
    carrierMessageId: `test-${Date.now()}`,
    from: payload.from,
    to: payload.to,
    timestamp: new Date().toISOString(),
    type: payload.mediaUrl ? 'MMS' : 'SMS',
    content: {
      text: payload.text,
      media: payload.mediaUrl ? [{
        url: payload.mediaUrl,
        type: payload.mediaType || 'image/jpeg',
      }] : undefined,
    },
    metadata: {
      isTest: true,
      environment: process.env.ENVIRONMENT,
    },
  };

  await publishToEventBridge(normalizedMessage);

  return {
    statusCode: 200,
    body: JSON.stringify({
      status: 'received',
      messageId: normalizedMessage.messageId,
      timestamp: normalizedMessage.timestamp,
    }),
  };
};

const handleSimulatedError = (errorType?: string): APIGatewayProxyResult => {
  switch (errorType) {
    case 'timeout':
      // This would be handled by API Gateway timeout
      throw new Error('Simulated timeout');
    case 'invalid':
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Invalid payload' }),
      };
    case 'server_error':
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'Internal server error' }),
      };
    default:
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'Unknown error' }),
      };
  }
};

const sleep = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));
```

### Test Scenarios

Use the test carrier to verify:

```bash
# Basic text message
curl -X POST https://api.example.com/webhooks/test \
  -H "Content-Type: application/json" \
  -H "X-Test-API-Key: your-test-key" \
  -d '{
    "from": "+15551234567",
    "to": "+15559876543",
    "text": "Test message"
  }'

# MMS message
curl -X POST https://api.example.com/webhooks/test \
  -H "Content-Type: application/json" \
  -H "X-Test-API-Key: your-test-key" \
  -d '{
    "from": "+15551234567",
    "to": "+15559876543",
    "text": "Check this image",
    "mediaUrl": "https://example.com/image.jpg",
    "mediaType": "image/jpeg"
  }'

# Error simulation
curl -X POST https://api.example.com/webhooks/test \
  -H "Content-Type: application/json" \
  -H "X-Test-API-Key: your-test-key" \
  -d '{
    "from": "+15551234567",
    "to": "+15559876543",
    "simulateError": true,
    "errorType": "server_error"
  }'
```

---

## Input/Output Contracts

### Unified Inbound Message Schema

All receive Lambda functions normalize carrier-specific payloads into this unified schema:

```typescript
// src/types/unified.ts

interface InboundMessage {
  /** Unique message identifier generated by the system */
  messageId: string;
  
  /** Source carrier identifier */
  carrier: CarrierType;
  
  /** Original message ID from the carrier */
  carrierMessageId: string;
  
  /** Sender phone number or identifier */
  from: string;
  
  /** Recipient phone number or identifier */
  to: string;
  
  /** ISO 8601 timestamp */
  timestamp: string;
  
  /** Normalized message type */
  type: MessageType;
  
  /** Message content */
  content: MessageContent;
  
  /** Carrier-specific metadata */
  metadata: Record<string, unknown>;
}

type CarrierType = 
  | 'whatsapp'
  | 'bandwidth'
  | 'twilio'
  | 'livechat'
  | 'messagebird'
  | 'inteliquent'
  | 'test';

type MessageType =
  | 'SMS'
  | 'MMS'
  | 'TEXT'
  | 'IMAGE'
  | 'VIDEO'
  | 'AUDIO'
  | 'DOCUMENT'
  | 'LOCATION'
  | 'CONTACT'
  | 'INTERACTIVE'
  | 'BUTTON_RESPONSE'
  | 'CHAT';

interface MessageContent {
  /** Text content of the message */
  text?: string;
  
  /** Media attachments */
  media?: MediaItem[];
  
  /** Location data */
  location?: LocationData;
  
  /** Contact card data */
  contact?: ContactData;
}

interface MediaItem {
  /** URL to the media file */
  url: string;
  
  /** MIME type */
  type: string;
  
  /** Optional filename */
  name?: string;
  
  /** Optional caption */
  caption?: string;
  
  /** File size in bytes */
  size?: number;
}

interface LocationData {
  latitude: number;
  longitude: number;
  name?: string;
  address?: string;
}
```

### EventBridge Event Schema

```typescript
interface InboundMessageEvent {
  version: '0';
  id: string;
  'detail-type': 'InboundMessage';
  source: 'omnichannel.receive';
  account: string;
  time: string;
  region: string;
  detail: {
    messageId: string;
    carrier: CarrierType;
    payload: InboundMessage;
    receivedAt: string;
    processingId: string;
  };
}
```

### API Response Contracts

**Success Response:**
```json
{
  "statusCode": 200,
  "body": {
    "status": "received",
    "messageId": "msg_abc123"
  }
}
```

**Error Response:**
```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid payload",
    "code": "INVALID_PAYLOAD",
    "details": "Missing required field: from"
  }
}
```

---

## Error Handling

### Error Classification

The receive Lambda functions implement a comprehensive error classification system:

```typescript
// src/errors/receive-errors.ts

enum ErrorCode {
  // Authentication errors (4xx)
  INVALID_SIGNATURE = 'INVALID_SIGNATURE',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  
  // Validation errors (4xx)
  INVALID_PAYLOAD = 'INVALID_PAYLOAD',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  INVALID_PHONE_NUMBER = 'INVALID_PHONE_NUMBER',
  
  // Processing errors (5xx)
  NORMALIZATION_FAILED = 'NORMALIZATION_FAILED',
  PUBLISH_FAILED = 'PUBLISH_FAILED',
  
  // External errors
  CARRIER_ERROR = 'CARRIER_ERROR',
  RATE_LIMITED = 'RATE_LIMITED',
}

class ReceiveError extends Error {
  constructor(
    message: string,
    public code: ErrorCode,
    public statusCode: number,
    public isRetryable: boolean = false,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ReceiveError';
  }
}
```

### Retry Strategy

```typescript
// src/middleware/retry-handler.ts

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors: ErrorCode[];
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 100,
  maxDelayMs: 5000,
  retryableErrors: [
    ErrorCode.PUBLISH_FAILED,
    ErrorCode.RATE_LIMITED,
  ],
};

const withRetry = async <T>(
  operation: () => Promise<T>,
  config: RetryConfig = defaultRetryConfig
): Promise<T> => {
  let lastError: Error;
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (error instanceof ReceiveError && !error.isRetryable) {
        throw error;
      }
      
      if (attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelayMs * Math.pow(2, attempt),
          config.maxDelayMs
        );
        await sleep(delay);
      }
    }
  }
  
  throw lastError!;
};
```

### Dead Letter Queue Handling

Messages that fail processing are sent to a Dead Letter Queue for later analysis:

```typescript
// src/services/dlq-handler.ts

import { SQS } from 'aws-sdk';

const sqs = new SQS();

interface DLQMessage {
  originalPayload: string;
  carrier: CarrierType;
  error: {
    code: string;
    message: string;
    stack?: string;
  };
  timestamp: string;
  retryCount: number;
}

export const sendToDLQ = async (
  payload: unknown,
  carrier: CarrierType,
  error: Error
): Promise<void> => {
  const dlqMessage: DLQMessage = {
    originalPayload: JSON.stringify(payload),
    carrier,
    error: {
      code: error instanceof ReceiveError ? error.code : 'UNKNOWN',
      message: error.message,
      stack: error.stack,
    },
    timestamp: new Date().toISOString(),
    retryCount: 0,
  };

  await sqs.sendMessage({
    QueueUrl: process.env.RECEIVE_DLQ_URL!,
    MessageBody: JSON.stringify(dlqMessage),
    MessageAttributes: {
      carrier: {
        DataType: 'String',
        StringValue: carrier,
      },
    },
  }).promise();
};
```

### Logging and Observability

```typescript
// src/middleware/logging.ts

import { Logger } from '@aws-lambda-powertools/logger';
import { Metrics, MetricUnits } from '@aws-lambda-powertools/metrics';
import { Tracer } from '@aws-lambda-powertools/tracer';

const logger = new Logger({ serviceName: 'omnichannel-receive' });
const metrics = new Metrics({ namespace: 'Omnichannel/Receive' });
const tracer = new Tracer({ serviceName: 'omnichannel-receive' });

export const logInboundMessage = (
  carrier: CarrierType,
  message: InboundMessage
): void => {
  logger.info('Inbound message received', {
    carrier,
    messageId: message.messageId,
    from: maskPhoneNumber(message.from),
    to: maskPhoneNumber(message.to),
    type: message.type,
    hasMedia: !!message.content.media?.length,
  });
  
  metrics.addMetric('MessagesReceived', MetricUnits.Count, 1);
  metrics.addDimension('Carrier', carrier);
  metrics.addDimension('MessageType', message.type);
};

export const logError = (
  carrier: CarrierType,
  error: Error,
  context: Record<string, unknown>
): void => {
  logger.error('Error processing inbound message', {
    carrier,
    errorCode: error instanceof ReceiveError ? error.code : 'UNKNOWN',
    errorMessage: error.message,
    ...context,
  });
  
  metrics.addMetric('ProcessingErrors', MetricUnits.Count, 1);
  metrics.addDimension('Carrier', carrier);
  metrics.addDimension('ErrorCode', 
    error instanceof ReceiveError ? error.code : 'UNKNOWN'
  );
};

const maskPhoneNumber = (phone: string): string => {
  if (phone.length <= 4) return '****';
  return phone.slice(0, -4).replace(/./g, '*') + phone.slice(-4);
};
```

### Error Response Mapping

| Error Code | HTTP Status | Carrier Action |
|------------|-------------|----------------|
| `INVALID_SIGNATURE` | 401 | Reject (no retry) |
| `UNAUTHORIZED` | 401 | Reject (no retry) |
| `INVALID_PAYLOAD` | 400 | Reject (no retry) |
| `PUBLISH_FAILED` | 500 | Retry with backoff |
| `RATE_LIMITED` | 429 | Retry with backoff |
| `NORMALIZATION_FAILED` | 500 | Send to DLQ |

---

## Best Practices

### Security Considerations

1. **Always validate webhook signatures** - Never process messages without verifying authenticity
2. **Use environment-specific secrets** - Different credentials for dev/staging/production
3. **Implement IP whitelisting** where carriers support it
4. **Mask sensitive data in logs** - Phone numbers, message content

### Performance Optimization

1. **Return acknowledgments quickly** - Process asynchronously when possible
2. **Use connection pooling** for database connections
3. **Implement circuit breakers** for downstream services
4. **Monitor cold start times** and optimize bundle sizes

### Testing Recommendations

1. Use the `receiveTestCarrier` endpoint for integration testing
2. Create carrier-specific mock payloads for unit tests
3. Test signature validation with both valid and invalid signatures
4. Verify error handling with simulated failures