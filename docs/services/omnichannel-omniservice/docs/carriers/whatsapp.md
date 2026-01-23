# WhatsApp Integration

## Overview

The WhatsApp Integration within the omnichannel-omniservice provides a robust, enterprise-grade solution for sending and receiving messages through the WhatsApp Business API. This integration enables organizations to leverage WhatsApp as a primary communication channel for customer engagement, support, and transactional messaging.

WhatsApp integration in this service operates as part of a larger omnichannel messaging pipeline, allowing seamless message routing alongside other carriers such as Twilio, Bandwidth, LiveChat, Messagebird, and Inteliquent. The architecture utilizes AWS Lambda functions for scalable, serverless processing of both inbound and outbound message flows.

### Key Capabilities

- **Bidirectional Messaging**: Full support for sending and receiving messages through WhatsApp Business API
- **Template Message Support**: Pre-approved message templates for initiating conversations
- **Rich Media Handling**: Support for images, documents, audio, video, and location sharing
- **Webhook-Based Architecture**: Real-time message delivery and status updates via webhooks
- **DynamoDB Integration**: Persistent message storage and stream-based processing
- **Workflow Orchestration**: Configurable message processing workflows for complex routing scenarios

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│  Webhook         │────▶│  AWS Lambda     │
│   Business API  │     │  Receiver        │     │  Processor      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Outbound      │◀────│  Message         │◀────│  DynamoDB       │
│   Gateway       │     │  Router          │     │  Streams        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Setup Requirements

### Prerequisites

Before configuring the WhatsApp integration, ensure you have the following:

1. **WhatsApp Business Account**: A verified Meta Business account with WhatsApp Business API access
2. **Phone Number**: A dedicated phone number registered with WhatsApp Business API
3. **AWS Account**: Active AWS account with permissions for Lambda, DynamoDB, and API Gateway
4. **Node.js Environment**: Node.js 18.x or higher with npm package manager

### Environment Configuration

Create or update your environment configuration with the following variables:

```typescript
// config/whatsapp.config.ts
export interface WhatsAppConfig {
  // WhatsApp Business API credentials
  businessAccountId: string;
  phoneNumberId: string;
  accessToken: string;
  
  // API endpoints
  apiVersion: string;
  baseUrl: string;
  
  // Webhook configuration
  webhookVerifyToken: string;
  webhookSecret: string;
  
  // Feature flags
  enableMediaDownload: boolean;
  enableReadReceipts: boolean;
  enableTypingIndicators: boolean;
}

export const whatsAppConfig: WhatsAppConfig = {
  businessAccountId: process.env.WHATSAPP_BUSINESS_ACCOUNT_ID || '',
  phoneNumberId: process.env.WHATSAPP_PHONE_NUMBER_ID || '',
  accessToken: process.env.WHATSAPP_ACCESS_TOKEN || '',
  apiVersion: process.env.WHATSAPP_API_VERSION || 'v18.0',
  baseUrl: 'https://graph.facebook.com',
  webhookVerifyToken: process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN || '',
  webhookSecret: process.env.WHATSAPP_WEBHOOK_SECRET || '',
  enableMediaDownload: true,
  enableReadReceipts: true,
  enableTypingIndicators: false
};
```

### AWS Infrastructure Setup

Deploy the required AWS resources using the provided CloudFormation or Terraform templates:

```yaml
# serverless.yml - WhatsApp Lambda Functions
functions:
  whatsappWebhookReceiver:
    handler: src/handlers/whatsapp/webhook.handler
    events:
      - http:
          path: /webhooks/whatsapp
          method: post
      - http:
          path: /webhooks/whatsapp
          method: get
    environment:
      WHATSAPP_VERIFY_TOKEN: ${env:WHATSAPP_WEBHOOK_VERIFY_TOKEN}
      DYNAMODB_TABLE: ${self:custom.messagesTable}

  whatsappOutboundProcessor:
    handler: src/handlers/whatsapp/outbound.handler
    events:
      - stream:
          type: dynamodb
          arn: ${self:custom.outboundStreamArn}
          batchSize: 10
          startingPosition: LATEST
```

### Dependency Installation

Install the required npm packages:

```bash
npm install @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb axios crypto-js
npm install --save-dev @types/node typescript
```

---

## Webhook Configuration

### Webhook Verification Handler

WhatsApp requires webhook verification before sending events. Implement the verification handler:

```typescript
// src/handlers/whatsapp/webhook.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { whatsAppConfig } from '../../config/whatsapp.config';

export const handler = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  // Handle GET requests for webhook verification
  if (event.httpMethod === 'GET') {
    return handleVerification(event);
  }
  
  // Handle POST requests for incoming messages
  if (event.httpMethod === 'POST') {
    return handleIncomingMessage(event);
  }
  
  return {
    statusCode: 405,
    body: JSON.stringify({ error: 'Method not allowed' })
  };
};

const handleVerification = (
  event: APIGatewayProxyEvent
): APIGatewayProxyResult => {
  const params = event.queryStringParameters || {};
  
  const mode = params['hub.mode'];
  const token = params['hub.verify_token'];
  const challenge = params['hub.challenge'];
  
  if (mode === 'subscribe' && token === whatsAppConfig.webhookVerifyToken) {
    console.log('Webhook verified successfully');
    return {
      statusCode: 200,
      body: challenge || ''
    };
  }
  
  console.error('Webhook verification failed', { mode, token });
  return {
    statusCode: 403,
    body: JSON.stringify({ error: 'Verification failed' })
  };
};
```

### Incoming Message Handler

Process incoming WhatsApp messages and route them through the pipeline:

```typescript
// src/handlers/whatsapp/webhook.ts (continued)
import { validateWebhookSignature } from '../../utils/security';
import { processInboundMessage } from '../../services/message-processor';
import { WhatsAppWebhookPayload, WhatsAppMessage } from '../../types/whatsapp';

const handleIncomingMessage = async (
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> => {
  // Validate webhook signature
  const signature = event.headers['x-hub-signature-256'];
  if (!validateWebhookSignature(event.body || '', signature, whatsAppConfig.webhookSecret)) {
    console.error('Invalid webhook signature');
    return {
      statusCode: 401,
      body: JSON.stringify({ error: 'Invalid signature' })
    };
  }
  
  try {
    const payload: WhatsAppWebhookPayload = JSON.parse(event.body || '{}');
    
    // Process each entry in the webhook payload
    for (const entry of payload.entry || []) {
      for (const change of entry.changes || []) {
        if (change.field === 'messages') {
          await processWhatsAppMessages(change.value);
        }
      }
    }
    
    return {
      statusCode: 200,
      body: JSON.stringify({ status: 'processed' })
    };
  } catch (error) {
    console.error('Error processing webhook', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};

const processWhatsAppMessages = async (value: any): Promise<void> => {
  const messages: WhatsAppMessage[] = value.messages || [];
  const contacts = value.contacts || [];
  
  for (const message of messages) {
    const contact = contacts.find((c: any) => c.wa_id === message.from);
    
    await processInboundMessage({
      carrier: 'whatsapp',
      messageId: message.id,
      from: message.from,
      to: value.metadata?.phone_number_id,
      timestamp: new Date(parseInt(message.timestamp) * 1000),
      type: message.type,
      content: extractMessageContent(message),
      contactName: contact?.profile?.name,
      metadata: {
        whatsappMessageId: message.id,
        contextMessageId: message.context?.id
      }
    });
  }
};
```

### Webhook Security Validation

```typescript
// src/utils/security.ts
import * as crypto from 'crypto';

export const validateWebhookSignature = (
  payload: string,
  signature: string | undefined,
  secret: string
): boolean => {
  if (!signature) {
    return false;
  }
  
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  
  const signatureHash = signature.replace('sha256=', '');
  
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(signatureHash)
  );
};
```

---

## Message Types Supported

The WhatsApp integration supports the following message types for both inbound and outbound communication:

### Text Messages

```typescript
// src/services/whatsapp/message-types.ts
export interface TextMessage {
  type: 'text';
  text: {
    body: string;
    preview_url?: boolean;
  };
}

// Sending a text message
const sendTextMessage = async (
  to: string,
  body: string,
  previewUrl: boolean = false
): Promise<SendMessageResponse> => {
  return sendWhatsAppMessage(to, {
    type: 'text',
    text: {
      body,
      preview_url: previewUrl
    }
  });
};
```

### Interactive Messages

Support for buttons and list messages:

```typescript
export interface InteractiveMessage {
  type: 'interactive';
  interactive: {
    type: 'button' | 'list' | 'product' | 'product_list';
    header?: {
      type: 'text' | 'image' | 'video' | 'document';
      text?: string;
      image?: MediaObject;
      video?: MediaObject;
      document?: MediaObject;
    };
    body: {
      text: string;
    };
    footer?: {
      text: string;
    };
    action: ButtonAction | ListAction;
  };
}

export interface ButtonAction {
  buttons: Array<{
    type: 'reply';
    reply: {
      id: string;
      title: string;
    };
  }>;
}

export interface ListAction {
  button: string;
  sections: Array<{
    title: string;
    rows: Array<{
      id: string;
      title: string;
      description?: string;
    }>;
  }>;
}

// Example: Sending an interactive button message
const sendButtonMessage = async (to: string): Promise<SendMessageResponse> => {
  return sendWhatsAppMessage(to, {
    type: 'interactive',
    interactive: {
      type: 'button',
      body: {
        text: 'How would you like to proceed?'
      },
      action: {
        buttons: [
          {
            type: 'reply',
            reply: { id: 'btn_yes', title: 'Yes' }
          },
          {
            type: 'reply',
            reply: { id: 'btn_no', title: 'No' }
          },
          {
            type: 'reply',
            reply: { id: 'btn_help', title: 'Need Help' }
          }
        ]
      }
    }
  });
};
```

### Location Messages

```typescript
export interface LocationMessage {
  type: 'location';
  location: {
    latitude: number;
    longitude: number;
    name?: string;
    address?: string;
  };
}

const sendLocationMessage = async (
  to: string,
  lat: number,
  lng: number,
  name?: string,
  address?: string
): Promise<SendMessageResponse> => {
  return sendWhatsAppMessage(to, {
    type: 'location',
    location: {
      latitude: lat,
      longitude: lng,
      name,
      address
    }
  });
};
```

### Contact Messages

```typescript
export interface ContactMessage {
  type: 'contacts';
  contacts: Array<{
    name: {
      formatted_name: string;
      first_name?: string;
      last_name?: string;
    };
    phones?: Array<{
      phone: string;
      type?: 'CELL' | 'MAIN' | 'HOME' | 'WORK';
    }>;
    emails?: Array<{
      email: string;
      type?: 'HOME' | 'WORK';
    }>;
  }>;
}
```

---

## Template Messages

Template messages are pre-approved message formats required for initiating conversations with users outside the 24-hour customer service window.

### Template Structure

```typescript
// src/types/whatsapp-templates.ts
export interface TemplateMessage {
  type: 'template';
  template: {
    name: string;
    language: {
      code: string;
    };
    components?: TemplateComponent[];
  };
}

export interface TemplateComponent {
  type: 'header' | 'body' | 'button';
  parameters?: TemplateParameter[];
  sub_type?: 'quick_reply' | 'url';
  index?: number;
}

export interface TemplateParameter {
  type: 'text' | 'currency' | 'date_time' | 'image' | 'document' | 'video';
  text?: string;
  currency?: {
    fallback_value: string;
    code: string;
    amount_1000: number;
  };
  date_time?: {
    fallback_value: string;
  };
  image?: MediaObject;
  document?: MediaObject;
  video?: MediaObject;
}
```

### Sending Template Messages

```typescript
// src/services/whatsapp/templates.ts
import { sendWhatsAppMessage } from './message-sender';
import { TemplateMessage, TemplateComponent } from '../../types/whatsapp-templates';

export const sendOrderConfirmationTemplate = async (
  to: string,
  orderNumber: string,
  customerName: string,
  totalAmount: number,
  currency: string
): Promise<SendMessageResponse> => {
  const template: TemplateMessage = {
    type: 'template',
    template: {
      name: 'order_confirmation',
      language: {
        code: 'en'
      },
      components: [
        {
          type: 'header',
          parameters: [
            {
              type: 'text',
              text: orderNumber
            }
          ]
        },
        {
          type: 'body',
          parameters: [
            {
              type: 'text',
              text: customerName
            },
            {
              type: 'currency',
              currency: {
                fallback_value: `${currency} ${(totalAmount / 100).toFixed(2)}`,
                code: currency,
                amount_1000: totalAmount * 10
              }
            }
          ]
        }
      ]
    }
  };
  
  return sendWhatsAppMessage(to, template);
};

export const sendAppointmentReminderTemplate = async (
  to: string,
  appointmentDate: Date,
  doctorName: string,
  location: string
): Promise<SendMessageResponse> => {
  const template: TemplateMessage = {
    type: 'template',
    template: {
      name: 'appointment_reminder',
      language: {
        code: 'en'
      },
      components: [
        {
          type: 'body',
          parameters: [
            {
              type: 'date_time',
              date_time: {
                fallback_value: appointmentDate.toLocaleString()
              }
            },
            {
              type: 'text',
              text: doctorName
            },
            {
              type: 'text',
              text: location
            }
          ]
        },
        {
          type: 'button',
          sub_type: 'quick_reply',
          index: 0,
          parameters: [
            {
              type: 'text',
              text: 'confirm_appointment'
            }
          ]
        },
        {
          type: 'button',
          sub_type: 'quick_reply',
          index: 1,
          parameters: [
            {
              type: 'text',
              text: 'reschedule_appointment'
            }
          ]
        }
      ]
    }
  };
  
  return sendWhatsAppMessage(to, template);
};
```

### Template Management Best Practices

1. **Version Control**: Maintain template versions in your codebase
2. **Localization**: Support multiple languages for international audiences
3. **Testing**: Use the WhatsApp test number before production deployment
4. **Approval Tracking**: Track template approval status in your database

---

## Media Handling

### Supported Media Types

| Media Type | Max Size | Supported Formats |
|------------|----------|-------------------|
| Image | 5 MB | JPEG, PNG |
| Video | 16 MB | MP4, 3GPP |
| Audio | 16 MB | AAC, MP3, OGG, AMR |
| Document | 100 MB | PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX |
| Sticker | 100 KB (static), 500 KB (animated) | WEBP |

### Downloading Media from Incoming Messages

```typescript
// src/services/whatsapp/media-handler.ts
import axios from 'axios';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { whatsAppConfig } from '../../config/whatsapp.config';

export interface MediaDownloadResult {
  mediaId: string;
  s3Key: string;
  mimeType: string;
  size: number;
}

export const downloadAndStoreMedia = async (
  mediaId: string,
  messageId: string
): Promise<MediaDownloadResult> => {
  // Step 1: Get media URL from WhatsApp API
  const mediaUrlResponse = await axios.get(
    `${whatsAppConfig.baseUrl}/${whatsAppConfig.apiVersion}/${mediaId}`,
    {
      headers: {
        Authorization: `Bearer ${whatsAppConfig.accessToken}`
      }
    }
  );
  
  const mediaUrl = mediaUrlResponse.data.url;
  const mimeType = mediaUrlResponse.data.mime_type;
  
  // Step 2: Download the media content
  const mediaResponse = await axios.get(mediaUrl, {
    headers: {
      Authorization: `Bearer ${whatsAppConfig.accessToken}`
    },
    responseType: 'arraybuffer'
  });
  
  // Step 3: Upload to S3
  const s3Client = new S3Client({ region: process.env.AWS_REGION });
  const s3Key = `whatsapp/media/${messageId}/${mediaId}`;
  
  await s3Client.send(new PutObjectCommand({
    Bucket: process.env.MEDIA_BUCKET!,
    Key: s3Key,
    Body: Buffer.from(mediaResponse.data),
    ContentType: mimeType
  }));
  
  return {
    mediaId,
    s3Key,
    mimeType,
    size: mediaResponse.data.byteLength
  };
};
```

### Uploading and Sending Media

```typescript
// src/services/whatsapp/media-sender.ts
export const uploadMediaToWhatsApp = async (
  mediaBuffer: Buffer,
  mimeType: string,
  filename: string
): Promise<string> => {
  const formData = new FormData();
  formData.append('file', new Blob([mediaBuffer], { type: mimeType }), filename);
  formData.append('messaging_product', 'whatsapp');
  formData.append('type', mimeType);
  
  const response = await axios.post(
    `${whatsAppConfig.baseUrl}/${whatsAppConfig.apiVersion}/${whatsAppConfig.phoneNumberId}/media`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${whatsAppConfig.accessToken}`,
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  
  return response.data.id;
};

export const sendImageMessage = async (
  to: string,
  imageSource: { id?: string; link?: string },
  caption?: string
): Promise<SendMessageResponse> => {
  return sendWhatsAppMessage(to, {
    type: 'image',
    image: {
      ...imageSource,
      caption
    }
  });
};

export const sendDocumentMessage = async (
  to: string,
  documentSource: { id?: string; link?: string },
  filename: string,
  caption?: string
): Promise<SendMessageResponse> => {
  return sendWhatsAppMessage(to, {
    type: 'document',
    document: {
      ...documentSource,
      filename,
      caption
    }
  });
};
```

### Media Conversion Service

Handle media format conversions for compatibility:

```typescript
// src/services/whatsapp/media-converter.ts
import { spawn } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

export const convertAudioToOgg = async (
  inputBuffer: Buffer,
  inputFormat: string
): Promise<Buffer> => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'audio-'));
  const inputPath = path.join(tempDir, `input.${inputFormat}`);
  const outputPath = path.join(tempDir, 'output.ogg');
  
  try {
    await fs.writeFile(inputPath, inputBuffer);
    
    await new Promise<void>((resolve, reject) => {
      const ffmpeg = spawn('ffmpeg', [
        '-i', inputPath,
        '-c:a', 'libopus',
        '-b:a', '64k',
        outputPath
      ]);
      
      ffmpeg.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`FFmpeg exited with code ${code}`));
      });
    });
    
    return await fs.readFile(outputPath);
  } finally {
    await fs.rm(tempDir, { recursive: true });
  }
};
```

---

## Error Handling

### Error Types and Codes

```typescript
// src/types/whatsapp-errors.ts
export enum WhatsAppErrorCode {
  // Authentication errors
  INVALID_ACCESS_TOKEN = 190,
  ACCESS_TOKEN_EXPIRED = 463,
  
  // Rate limiting
  RATE_LIMIT_EXCEEDED = 80007,
  
  // Message errors
  RECIPIENT_NOT_VALID = 131026,
  MESSAGE_UNDELIVERABLE = 131047,
  MEDIA_DOWNLOAD_ERROR = 131052,
  TEMPLATE_NOT_FOUND = 132000,
  TEMPLATE_PARAMS_MISMATCH = 132001,
  
  // Business errors
  PHONE_NUMBER_NOT_REGISTERED = 131031,
  OUTSIDE_MESSAGE_WINDOW = 131048,
  RE_ENGAGEMENT_REQUIRED = 131027
}

export interface WhatsAppError {
  code: number;
  title: string;
  message: string;
  error_subcode?: number;
  error_data?: {
    details: string;
  };
}

export class WhatsAppApiError extends Error {
  public readonly code: number;
  public readonly title: string;
  public readonly errorData?: any;
  public readonly isRetryable: boolean;
  
  constructor(error: WhatsAppError) {
    super(error.message);
    this.name = 'WhatsAppApiError';
    this.code = error.code;
    this.title = error.title;
    this.errorData = error.error_data;
    this.isRetryable = this.determineRetryable(error.code);
  }
  
  private determineRetryable(code: number): boolean {
    const retryableCodes = [
      WhatsAppErrorCode.RATE_LIMIT_EXCEEDED,
      WhatsAppErrorCode.MEDIA_DOWNLOAD_ERROR
    ];
    return retryableCodes.includes(code);
  }
}
```

### Error Handler Implementation

```typescript
// src/services/whatsapp/error-handler.ts
import { WhatsAppApiError, WhatsAppErrorCode } from '../../types/whatsapp-errors';
import { logError, logWarning } from '../../utils/logger';
import { MessageStatus } from '../../types/message';

export interface ErrorHandlingResult {
  shouldRetry: boolean;
  retryDelay?: number;
  newStatus: MessageStatus;
  notifyAdmin: boolean;
}

export const handleWhatsAppError = async (
  error: WhatsAppApiError,
  messageId: string,
  attemptCount: number
): Promise<ErrorHandlingResult> => {
  logError('WhatsApp API error', {
    messageId,
    errorCode: error.code,
    errorMessage: error.message,
    attemptCount
  });
  
  switch (error.code) {
    case WhatsAppErrorCode.RATE_LIMIT_EXCEEDED:
      return handleRateLimitError(attemptCount);
    
    case WhatsAppErrorCode.OUTSIDE_MESSAGE_WINDOW:
      return handleMessageWindowError(messageId);
    
    case WhatsAppErrorCode.RECIPIENT_NOT_VALID:
      return handleInvalidRecipientError(messageId);
    
    case WhatsAppErrorCode.TEMPLATE_NOT_FOUND:
    case WhatsAppErrorCode.TEMPLATE_PARAMS_MISMATCH:
      return handleTemplateError(error, messageId);
    
    case WhatsAppErrorCode.INVALID_ACCESS_TOKEN:
    case WhatsAppErrorCode.ACCESS_TOKEN_EXPIRED:
      return handleAuthenticationError();
    
    default:
      return handleUnknownError(error, messageId);
  }
};

const handleRateLimitError = (attemptCount: number): ErrorHandlingResult => {
  const baseDelay = 1000;
  const maxDelay = 60000;
  const retryDelay = Math.min(baseDelay * Math.pow(2, attemptCount), maxDelay);
  
  return {
    shouldRetry: attemptCount < 5,
    retryDelay,
    newStatus: 'pending',
    notifyAdmin: attemptCount >= 3
  };
};

const handleMessageWindowError = async (
  messageId: string
): Promise<ErrorHandlingResult> => {
  logWarning('Message outside 24-hour window', { messageId });
  
  // Queue for template message conversion
  await queueForTemplateConversion(messageId);
  
  return {
    shouldRetry: false,
    newStatus: 'requires_template',
    notifyAdmin: false
  };
};

const handleInvalidRecipientError = (
  messageId: string
): ErrorHandlingResult => {
  return {
    shouldRetry: false,
    newStatus: 'failed',
    notifyAdmin: false
  };
};

const handleTemplateError = (
  error: WhatsAppApiError,
  messageId: string
): ErrorHandlingResult => {
  logError('Template error', {
    messageId,
    errorCode: error.code,
    errorData: error.errorData
  });
  
  return {
    shouldRetry: false,
    newStatus: 'failed',
    notifyAdmin: true
  };
};

const handleAuthenticationError = (): ErrorHandlingResult => {
  return {
    shouldRetry: false,
    newStatus: 'failed',
    notifyAdmin: true
  };
};

const handleUnknownError = (
  error: WhatsAppApiError,
  messageId: string
): ErrorHandlingResult => {
  logError('Unknown WhatsApp error', {
    messageId,
    error
  });
  
  return {
    shouldRetry: error.isRetryable,
    retryDelay: 5000,
    newStatus: error.isRetryable ? 'pending' : 'failed',
    notifyAdmin: true
  };
};
```

### Retry Mechanism

```typescript
// src/services/whatsapp/retry-handler.ts
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';

const sqsClient = new SQSClient({ region: process.env.AWS_REGION });

export const queueForRetry = async (
  messageId: string,
  payload: any,
  delaySeconds: number
): Promise<void> => {
  const command = new SendMessageCommand({
    QueueUrl: process.env.WHATSAPP_RETRY_QUEUE_URL!,
    MessageBody: JSON.stringify({
      messageId,
      payload,
      timestamp: Date.now()
    }),
    DelaySeconds: Math.min(delaySeconds, 900) // SQS max is 15 minutes
  });
  
  await sqsClient.send(command);
};
```

### Monitoring and Alerting

```typescript
// src/services/whatsapp/monitoring.ts
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

const cloudwatchClient = new CloudWatchClient({ region: process.env.AWS_REGION });

export const recordMetric = async (
  metricName: string,
  value: number,
  dimensions?: Record<string, string>
): Promise<void> => {
  const dimensionList = dimensions
    ? Object.entries(dimensions).map(([Name, Value]) => ({ Name, Value }))
    : [];
  
  await cloudwatchClient.send(new PutMetricDataCommand({
    Namespace: 'OmniChannel/WhatsApp',
    MetricData: [
      {
        MetricName: metricName,
        Value: value,
        Unit: 'Count',
        Dimensions: dimensionList,
        Timestamp: new Date()
      }
    ]
  }));
};

// Usage examples
export const recordMessageSent = () => recordMetric('MessagesSent', 1);
export const recordMessageFailed = (errorCode: number) => 
  recordMetric('MessagesFailed', 1, { ErrorCode: String(errorCode) });
export const recordWebhookReceived = () => recordMetric('WebhooksReceived', 1);
```

---

## Related Resources

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Message Templates Guidelines](https://developers.facebook.com/docs/whatsapp/message-templates)
- [Webhook Configuration Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- Internal: Omnichannel Message Router Documentation
- Internal: DynamoDB Stream Processing Guide