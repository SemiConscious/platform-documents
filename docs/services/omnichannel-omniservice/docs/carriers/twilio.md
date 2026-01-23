# Twilio Integration

## Overview

The Twilio integration within the omnichannel-omniservice platform provides enterprise-grade SMS and MMS messaging capabilities through Twilio's programmable messaging API. This integration enables bidirectional communication flows, allowing your application to send outbound messages to customers and receive inbound messages via webhook endpoints.

Twilio serves as one of the core carriers in the omnichannel messaging pipeline, handling message routing alongside other providers like WhatsApp, Bandwidth, LiveChat, Messagebird, and Inteliquent. The integration leverages AWS Lambda functions for scalable, serverless message processing and DynamoDB for message persistence and state management.

### Key Capabilities

- **Outbound SMS/MMS**: Send text messages and multimedia content to phone numbers worldwide
- **Inbound Message Handling**: Receive and process customer-initiated messages through configurable webhooks
- **Delivery Status Tracking**: Real-time delivery receipts and status callbacks
- **Media Conversion**: Automatic handling of media attachments with format conversion support
- **Workflow Integration**: Seamless integration with the omnichannel workflow engine for message routing and processing

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Twilio API    │────▶│  Webhook Lambda  │────▶│   DynamoDB      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Status Callback │────▶│ Workflow Engine  │────▶│ Message Router  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Setup Requirements

### Prerequisites

Before configuring the Twilio integration, ensure you have the following:

1. **Twilio Account**: An active Twilio account with API credentials
2. **AWS Infrastructure**: Deployed Lambda functions and API Gateway endpoints
3. **DynamoDB Tables**: Required tables for message storage and tracking
4. **Environment Configuration**: Properly configured environment variables

### Twilio Account Configuration

#### Step 1: Obtain API Credentials

Log into your Twilio Console and navigate to **Account > API Keys & Tokens** to retrieve:

```typescript
// Required Twilio credentials
interface TwilioCredentials {
  accountSid: string;      // Your Twilio Account SID (ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
  authToken: string;       // Your Twilio Auth Token
  apiKeySid?: string;      // Optional: API Key SID for enhanced security
  apiKeySecret?: string;   // Optional: API Key Secret
}
```

#### Step 2: Configure Phone Numbers

Ensure you have at least one Twilio phone number configured for messaging:

```typescript
// Phone number configuration
interface TwilioPhoneNumber {
  phoneNumber: string;     // E.164 format: +1234567890
  capabilities: {
    sms: boolean;
    mms: boolean;
    voice: boolean;
  };
  webhookUrls: {
    incomingSms: string;
    statusCallback: string;
  };
}
```

#### Step 3: Environment Variables

Configure the following environment variables in your AWS Lambda functions:

```bash
# Twilio API Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_api_key_secret

# Twilio Phone Numbers
TWILIO_DEFAULT_FROM_NUMBER=+1234567890
TWILIO_MESSAGING_SERVICE_SID=MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Webhook Configuration
TWILIO_STATUS_CALLBACK_URL=https://your-api-gateway.execute-api.region.amazonaws.com/prod/twilio/status
TWILIO_INBOUND_WEBHOOK_URL=https://your-api-gateway.execute-api.region.amazonaws.com/prod/twilio/inbound
```

### Service Installation

Install the required dependencies in your monorepo packages:

```bash
# Navigate to the carrier integration package
cd packages/carriers/twilio

# Install dependencies
npm install twilio @types/twilio

# Install shared dependencies
npm install
```

### TypeScript Configuration

Ensure your TypeScript configuration includes the Twilio types:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "strict": true,
    "esModuleInterop": true,
    "types": ["node", "@types/twilio"]
  }
}
```

---

## Webhook Configuration

### Inbound Message Webhook

The inbound webhook receives messages sent by customers to your Twilio phone numbers.

#### Lambda Handler Implementation

```typescript
// packages/lambdas/twilio-inbound/handler.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { validateTwilioSignature } from '../utils/twilio-validation';
import { InboundMessageProcessor } from '../processors/inbound-message-processor';

interface TwilioInboundPayload {
  MessageSid: string;
  AccountSid: string;
  From: string;
  To: string;
  Body: string;
  NumMedia: string;
  MediaUrl0?: string;
  MediaContentType0?: string;
  FromCity?: string;
  FromState?: string;
  FromCountry?: string;
}

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    // Validate Twilio signature
    const isValid = await validateTwilioSignature(event);
    if (!isValid) {
      return {
        statusCode: 403,
        body: JSON.stringify({ error: 'Invalid signature' }),
      };
    }

    // Parse the incoming message
    const payload = parseUrlEncodedBody(event.body) as TwilioInboundPayload;

    // Process the inbound message
    const processor = new InboundMessageProcessor();
    await processor.process({
      carrier: 'twilio',
      messageSid: payload.MessageSid,
      from: payload.From,
      to: payload.To,
      body: payload.Body,
      mediaCount: parseInt(payload.NumMedia, 10),
      mediaUrls: extractMediaUrls(payload),
      metadata: {
        fromCity: payload.FromCity,
        fromState: payload.FromState,
        fromCountry: payload.FromCountry,
      },
    });

    // Return TwiML response
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/xml' },
      body: '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
    };
  } catch (error) {
    console.error('Inbound webhook error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};
```

#### Configuring Webhooks in Twilio Console

1. Navigate to **Phone Numbers > Manage > Active Numbers**
2. Select your phone number
3. Under **Messaging Configuration**:
   - Set **A MESSAGE COMES IN** webhook URL to your inbound endpoint
   - Set HTTP method to **POST**
   - Configure **PRIMARY HANDLER FAILS** for fallback handling

### Status Callback Webhook

Status callbacks provide delivery receipt information for outbound messages.

```typescript
// packages/lambdas/twilio-status/handler.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { MessageStatusUpdater } from '../services/message-status-updater';

interface TwilioStatusPayload {
  MessageSid: string;
  MessageStatus: TwilioMessageStatus;
  ErrorCode?: string;
  ErrorMessage?: string;
  To: string;
  From: string;
}

type TwilioMessageStatus = 
  | 'accepted'
  | 'queued'
  | 'sending'
  | 'sent'
  | 'delivered'
  | 'undelivered'
  | 'failed'
  | 'read';

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  try {
    const payload = parseUrlEncodedBody(event.body) as TwilioStatusPayload;

    const statusUpdater = new MessageStatusUpdater();
    await statusUpdater.updateStatus({
      messageSid: payload.MessageSid,
      status: mapTwilioStatus(payload.MessageStatus),
      errorCode: payload.ErrorCode,
      errorMessage: payload.ErrorMessage,
      timestamp: new Date().toISOString(),
    });

    return {
      statusCode: 200,
      body: JSON.stringify({ success: true }),
    };
  } catch (error) {
    console.error('Status callback error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};

function mapTwilioStatus(twilioStatus: TwilioMessageStatus): string {
  const statusMap: Record<TwilioMessageStatus, string> = {
    accepted: 'ACCEPTED',
    queued: 'QUEUED',
    sending: 'SENDING',
    sent: 'SENT',
    delivered: 'DELIVERED',
    undelivered: 'UNDELIVERED',
    failed: 'FAILED',
    read: 'READ',
  };
  return statusMap[twilioStatus] || 'UNKNOWN';
}
```

### Webhook Security

#### Signature Validation

Always validate incoming webhook requests using Twilio's request signature:

```typescript
// packages/utils/twilio-validation.ts
import twilio from 'twilio';
import { APIGatewayProxyEvent } from 'aws-lambda';

export async function validateTwilioSignature(
  event: APIGatewayProxyEvent
): Promise<boolean> {
  const authToken = process.env.TWILIO_AUTH_TOKEN;
  const signature = event.headers['X-Twilio-Signature'] || 
                    event.headers['x-twilio-signature'];
  
  if (!authToken || !signature) {
    return false;
  }

  // Reconstruct the full URL
  const protocol = event.headers['X-Forwarded-Proto'] || 'https';
  const host = event.headers['Host'];
  const path = event.path;
  const url = `${protocol}://${host}${path}`;

  // Parse body parameters
  const params = parseUrlEncodedBody(event.body);

  return twilio.validateRequest(authToken, signature, url, params);
}
```

---

## Message Types Supported

### SMS Messages

Standard text messages up to 1600 characters (automatically segmented by Twilio):

```typescript
// packages/services/twilio-outbound-service.ts
import twilio from 'twilio';

interface SendSmsOptions {
  to: string;
  from?: string;
  body: string;
  statusCallback?: string;
  maxPrice?: string;
  validityPeriod?: number;
}

export class TwilioOutboundService {
  private client: twilio.Twilio;

  constructor() {
    this.client = twilio(
      process.env.TWILIO_ACCOUNT_SID,
      process.env.TWILIO_AUTH_TOKEN
    );
  }

  async sendSms(options: SendSmsOptions): Promise<TwilioMessage> {
    const message = await this.client.messages.create({
      to: options.to,
      from: options.from || process.env.TWILIO_DEFAULT_FROM_NUMBER,
      body: options.body,
      statusCallback: options.statusCallback || 
                      process.env.TWILIO_STATUS_CALLBACK_URL,
      maxPrice: options.maxPrice,
      validityPeriod: options.validityPeriod,
    });

    return {
      sid: message.sid,
      status: message.status,
      dateCreated: message.dateCreated,
      direction: message.direction,
    };
  }
}
```

### MMS Messages

Multimedia messages with image, video, or document attachments:

```typescript
interface SendMmsOptions extends SendSmsOptions {
  mediaUrl: string[];
}

async sendMms(options: SendMmsOptions): Promise<TwilioMessage> {
  // Validate media URLs
  for (const url of options.mediaUrl) {
    await this.validateMediaUrl(url);
  }

  const message = await this.client.messages.create({
    to: options.to,
    from: options.from || process.env.TWILIO_DEFAULT_FROM_NUMBER,
    body: options.body,
    mediaUrl: options.mediaUrl,
    statusCallback: options.statusCallback ||
                    process.env.TWILIO_STATUS_CALLBACK_URL,
  });

  return {
    sid: message.sid,
    status: message.status,
    mediaCount: message.numMedia,
    dateCreated: message.dateCreated,
  };
}

private async validateMediaUrl(url: string): Promise<void> {
  // Supported media types
  const supportedTypes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'video/mp4',
    'audio/mpeg',
    'application/pdf',
  ];

  // Check URL accessibility and content type
  const response = await fetch(url, { method: 'HEAD' });
  const contentType = response.headers.get('content-type');

  if (!contentType || !supportedTypes.includes(contentType)) {
    throw new Error(`Unsupported media type: ${contentType}`);
  }
}
```

### Supported Media Types

| Type | MIME Types | Max Size |
|------|------------|----------|
| Images | image/jpeg, image/png, image/gif | 5 MB |
| Videos | video/mp4, video/3gpp | 5 MB |
| Audio | audio/mpeg, audio/ogg | 5 MB |
| Documents | application/pdf | 5 MB |

---

## Error Handling

### Error Categories

The Twilio integration handles several categories of errors:

#### 1. Authentication Errors

```typescript
// packages/errors/twilio-errors.ts
export class TwilioAuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TwilioAuthenticationError';
  }
}

export class TwilioInvalidCredentialsError extends TwilioAuthenticationError {
  readonly errorCode = 20003;
  
  constructor() {
    super('Invalid Twilio credentials. Verify ACCOUNT_SID and AUTH_TOKEN.');
  }
}
```

#### 2. Rate Limiting Errors

```typescript
export class TwilioRateLimitError extends Error {
  readonly retryAfter: number;
  
  constructor(retryAfter: number = 1000) {
    super('Rate limit exceeded. Implement exponential backoff.');
    this.name = 'TwilioRateLimitError';
    this.retryAfter = retryAfter;
  }
}

// Retry logic with exponential backoff
async function sendWithRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      
      if (error instanceof TwilioRateLimitError) {
        const delay = Math.pow(2, attempt) * error.retryAfter;
        await sleep(delay);
        continue;
      }
      
      throw error;
    }
  }
  
  throw lastError;
}
```

#### 3. Message Delivery Errors

```typescript
// Common Twilio error codes
const TWILIO_ERROR_CODES = {
  21211: 'Invalid phone number',
  21612: 'Cannot route to this number',
  21614: 'Invalid mobile number',
  21408: 'Permission denied',
  30003: 'Unreachable destination',
  30004: 'Message blocked',
  30005: 'Unknown destination',
  30006: 'Landline or unreachable carrier',
  30007: 'Carrier violation',
  30008: 'Unknown error',
} as const;

export function handleTwilioError(errorCode: number): string {
  return TWILIO_ERROR_CODES[errorCode] || `Unknown error: ${errorCode}`;
}
```

### Error Handling Best Practices

```typescript
// packages/services/twilio-message-service.ts
export class TwilioMessageService {
  async sendMessage(request: MessageRequest): Promise<MessageResponse> {
    try {
      const result = await this.twilioClient.messages.create({
        to: request.to,
        from: request.from,
        body: request.body,
      });

      return {
        success: true,
        messageSid: result.sid,
        status: result.status,
      };
    } catch (error) {
      // Log error for monitoring
      console.error('Twilio message send failed:', {
        error: error.message,
        code: error.code,
        moreInfo: error.moreInfo,
        to: request.to,
      });

      // Handle specific error types
      if (error.code === 21211) {
        throw new InvalidPhoneNumberError(request.to);
      }

      if (error.code === 21408) {
        throw new PermissionDeniedError('Geographic permissions not enabled');
      }

      if (error.status === 429) {
        throw new TwilioRateLimitError(error.retryAfter);
      }

      // Store failed message for retry queue
      await this.storeFailedMessage(request, error);

      throw new MessageDeliveryError(
        `Failed to send message: ${error.message}`,
        error.code
      );
    }
  }

  private async storeFailedMessage(
    request: MessageRequest,
    error: Error
  ): Promise<void> {
    await this.dynamoDb.put({
      TableName: process.env.FAILED_MESSAGES_TABLE,
      Item: {
        id: uuid(),
        carrier: 'twilio',
        request,
        error: {
          message: error.message,
          code: (error as any).code,
        },
        retryCount: 0,
        createdAt: new Date().toISOString(),
      },
    });
  }
}
```

### Monitoring and Alerting

Implement CloudWatch metrics for error tracking:

```typescript
// packages/monitoring/twilio-metrics.ts
import { CloudWatch } from 'aws-sdk';

const cloudwatch = new CloudWatch();

export async function recordTwilioError(
  errorCode: number,
  phoneNumber: string
): Promise<void> {
  await cloudwatch.putMetricData({
    Namespace: 'OmniChannel/Twilio',
    MetricData: [
      {
        MetricName: 'MessageErrors',
        Value: 1,
        Unit: 'Count',
        Dimensions: [
          { Name: 'ErrorCode', Value: errorCode.toString() },
          { Name: 'Carrier', Value: 'twilio' },
        ],
      },
    ],
  }).promise();
}
```

---

## Summary

The Twilio integration provides a robust, scalable foundation for SMS and MMS messaging within the omnichannel-omniservice platform. Key implementation considerations include:

1. **Security**: Always validate Twilio webhook signatures and use API keys for enhanced credential management
2. **Reliability**: Implement retry logic with exponential backoff for rate-limited requests
3. **Monitoring**: Track delivery status and error rates through CloudWatch metrics
4. **Scalability**: Leverage AWS Lambda for automatic scaling during traffic spikes

For additional support, consult the [Twilio API Documentation](https://www.twilio.com/docs/sms) and the internal service architecture documentation.