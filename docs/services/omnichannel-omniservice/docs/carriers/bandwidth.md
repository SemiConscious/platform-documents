# Bandwidth Integration

## Overview

The Bandwidth integration within the omnichannel-omniservice provides robust SMS and MMS messaging capabilities through Bandwidth's telecommunications platform. This integration enables bidirectional communication, allowing the service to receive inbound messages from customers via webhooks and send outbound messages through Bandwidth's REST API.

Bandwidth is a leading communications platform-as-a-service (CPaaS) provider that offers direct carrier connectivity, providing reliable message delivery with competitive pricing. The integration supports both SMS (Short Message Service) and MMS (Multimedia Messaging Service), making it suitable for a wide range of business communication needs.

### Key Integration Features

- **Inbound Message Processing**: Receive and process incoming SMS/MMS messages via webhook callbacks
- **Outbound Message Delivery**: Send SMS/MMS messages to customers programmatically
- **Delivery Status Tracking**: Monitor message delivery status through callback notifications
- **Media Handling**: Support for multimedia attachments including images, audio, and video
- **Number Management**: Integration with Bandwidth's phone number provisioning
- **Error Recovery**: Robust error handling with retry mechanisms and dead-letter queue support

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Bandwidth     │────▶│  Webhook Lambda  │────▶│   SQS Queue     │
│   Platform      │     │  (Inbound)       │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Bandwidth     │◀────│  Outbound Lambda │◀────│   Workflow      │
│   API           │     │                  │     │   Processor     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Setup Requirements

### Prerequisites

Before configuring the Bandwidth integration, ensure you have the following:

1. **Bandwidth Account**: An active Bandwidth account with API access enabled
2. **Application ID**: A Bandwidth messaging application configured in your dashboard
3. **API Credentials**: Account ID, API Token, and API Secret
4. **Phone Numbers**: One or more Bandwidth phone numbers provisioned for messaging
5. **AWS Infrastructure**: Lambda functions, API Gateway, and SQS queues deployed

### Environment Configuration

Configure the following environment variables in your Lambda functions and deployment configuration:

```typescript
// config/bandwidth.config.ts
export interface BandwidthConfig {
  accountId: string;
  apiToken: string;
  apiSecret: string;
  applicationId: string;
  baseUrl: string;
  callbackUrl: string;
  mediaBaseUrl: string;
}

export const bandwidthConfig: BandwidthConfig = {
  accountId: process.env.BANDWIDTH_ACCOUNT_ID!,
  apiToken: process.env.BANDWIDTH_API_TOKEN!,
  apiSecret: process.env.BANDWIDTH_API_SECRET!,
  applicationId: process.env.BANDWIDTH_APPLICATION_ID!,
  baseUrl: process.env.BANDWIDTH_BASE_URL || 'https://messaging.bandwidth.com/api/v2',
  callbackUrl: process.env.BANDWIDTH_CALLBACK_URL!,
  mediaBaseUrl: process.env.BANDWIDTH_MEDIA_BASE_URL || 'https://messaging.bandwidth.com/api/v2/users'
};
```

### AWS Secrets Manager Configuration

For production environments, store sensitive credentials in AWS Secrets Manager:

```typescript
// services/secrets.service.ts
import { SecretsManager } from 'aws-sdk';

interface BandwidthSecrets {
  accountId: string;
  apiToken: string;
  apiSecret: string;
  applicationId: string;
}

export async function getBandwidthSecrets(): Promise<BandwidthSecrets> {
  const secretsManager = new SecretsManager();
  
  const response = await secretsManager.getSecretValue({
    SecretId: 'omnichannel/bandwidth/credentials'
  }).promise();
  
  if (!response.SecretString) {
    throw new Error('Bandwidth secrets not found');
  }
  
  return JSON.parse(response.SecretString) as BandwidthSecrets;
}
```

### IAM Permissions

Ensure your Lambda execution role has the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:omnichannel/bandwidth/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:*:*:bandwidth-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/messages*"
    }
  ]
}
```

### Package Dependencies

Install the required npm packages:

```bash
npm install @bandwidth/messaging axios aws-sdk uuid
npm install --save-dev @types/uuid @types/aws-lambda
```

## Webhook Configuration

### Webhook Endpoint Setup

The Bandwidth integration requires webhook endpoints to receive inbound messages and delivery status callbacks. Configure these endpoints in your API Gateway:

```yaml
# serverless.yml
functions:
  bandwidthInboundWebhook:
    handler: src/handlers/bandwidth/inbound.handler
    events:
      - http:
          path: /webhooks/bandwidth/inbound
          method: POST
          cors: true
    environment:
      SQS_QUEUE_URL: !Ref BandwidthInboundQueue
      
  bandwidthStatusWebhook:
    handler: src/handlers/bandwidth/status.handler
    events:
      - http:
          path: /webhooks/bandwidth/status
          method: POST
          cors: true
    environment:
      MESSAGES_TABLE: !Ref MessagesTable
```

### Inbound Webhook Handler

```typescript
// handlers/bandwidth/inbound.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { SQS } from 'aws-sdk';
import { v4 as uuidv4 } from 'uuid';

interface BandwidthInboundMessage {
  type: string;
  time: string;
  description: string;
  to: string;
  message: {
    id: string;
    owner: string;
    applicationId: string;
    time: string;
    segmentCount: number;
    direction: string;
    to: string[];
    from: string;
    text: string;
    media?: string[];
    tag?: string;
  };
}

const sqs = new SQS();

export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  try {
    // Validate webhook signature (recommended for production)
    if (!validateWebhookSignature(event)) {
      return {
        statusCode: 401,
        body: JSON.stringify({ error: 'Invalid signature' })
      };
    }

    const callbacks: BandwidthInboundMessage[] = JSON.parse(event.body || '[]');
    
    for (const callback of callbacks) {
      if (callback.type === 'message-received') {
        const normalizedMessage = {
          id: uuidv4(),
          carrierId: callback.message.id,
          carrier: 'bandwidth',
          direction: 'inbound',
          from: callback.message.from,
          to: callback.message.to[0],
          body: callback.message.text,
          media: callback.message.media || [],
          timestamp: callback.message.time,
          metadata: {
            applicationId: callback.message.applicationId,
            segmentCount: callback.message.segmentCount,
            tag: callback.message.tag
          }
        };

        await sqs.sendMessage({
          QueueUrl: process.env.SQS_QUEUE_URL!,
          MessageBody: JSON.stringify(normalizedMessage),
          MessageGroupId: callback.message.from,
          MessageDeduplicationId: callback.message.id
        }).promise();
      }
    }

    return {
      statusCode: 200,
      body: JSON.stringify({ success: true })
    };
  } catch (error) {
    console.error('Bandwidth inbound webhook error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
}

function validateWebhookSignature(event: APIGatewayProxyEvent): boolean {
  // Implement Bandwidth webhook signature validation
  // See: https://dev.bandwidth.com/docs/messaging/webhooks/
  const signature = event.headers['X-Bandwidth-Signature'];
  // Validation logic here
  return true; // Placeholder
}
```

### Delivery Status Webhook Handler

```typescript
// handlers/bandwidth/status.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { DynamoDB } from 'aws-sdk';

interface BandwidthStatusCallback {
  type: string;
  time: string;
  description: string;
  to: string;
  message: {
    id: string;
    owner: string;
    applicationId: string;
    direction: string;
    to: string[];
    from: string;
    text: string;
    tag?: string;
  };
  errorCode?: number;
  errorDescription?: string;
}

const dynamodb = new DynamoDB.DocumentClient();

export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  try {
    const callbacks: BandwidthStatusCallback[] = JSON.parse(event.body || '[]');
    
    for (const callback of callbacks) {
      const status = mapBandwidthStatus(callback.type);
      
      await dynamodb.update({
        TableName: process.env.MESSAGES_TABLE!,
        Key: { carrierId: callback.message.id },
        UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt, errorCode = :errorCode, errorDescription = :errorDescription',
        ExpressionAttributeNames: {
          '#status': 'status'
        },
        ExpressionAttributeValues: {
          ':status': status,
          ':updatedAt': new Date().toISOString(),
          ':errorCode': callback.errorCode || null,
          ':errorDescription': callback.errorDescription || null
        }
      }).promise();
    }

    return {
      statusCode: 200,
      body: JSON.stringify({ success: true })
    };
  } catch (error) {
    console.error('Bandwidth status webhook error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
}

function mapBandwidthStatus(bandwidthType: string): string {
  const statusMap: Record<string, string> = {
    'message-sending': 'sending',
    'message-delivered': 'delivered',
    'message-failed': 'failed'
  };
  return statusMap[bandwidthType] || 'unknown';
}
```

### Bandwidth Dashboard Configuration

Configure your Bandwidth application to send callbacks to your webhook endpoints:

1. Log in to the [Bandwidth Dashboard](https://dashboard.bandwidth.com/)
2. Navigate to **Applications** → **Messaging Applications**
3. Select or create your messaging application
4. Configure the callback URLs:
   - **Inbound Callback URL**: `https://your-api-gateway.amazonaws.com/prod/webhooks/bandwidth/inbound`
   - **Status Callback URL**: `https://your-api-gateway.amazonaws.com/prod/webhooks/bandwidth/status`
5. Set callback credentials if using basic authentication
6. Save the application configuration

## Message Types Supported

### SMS Messages

Standard text messages up to 160 characters (or concatenated for longer messages):

```typescript
// services/bandwidth/sms.service.ts
import axios from 'axios';
import { bandwidthConfig } from '../../config/bandwidth.config';

interface SendSmsRequest {
  to: string;
  from: string;
  text: string;
  tag?: string;
  priority?: 'default' | 'high';
}

interface SendSmsResponse {
  id: string;
  owner: string;
  applicationId: string;
  time: string;
  segmentCount: number;
  direction: string;
  to: string[];
  from: string;
  text: string;
  tag?: string;
}

export async function sendSms(request: SendSmsRequest): Promise<SendSmsResponse> {
  const url = `${bandwidthConfig.baseUrl}/users/${bandwidthConfig.accountId}/messages`;
  
  const payload = {
    applicationId: bandwidthConfig.applicationId,
    to: [request.to],
    from: request.from,
    text: request.text,
    tag: request.tag,
    priority: request.priority
  };

  const response = await axios.post<SendSmsResponse>(url, payload, {
    auth: {
      username: bandwidthConfig.apiToken,
      password: bandwidthConfig.apiSecret
    },
    headers: {
      'Content-Type': 'application/json'
    }
  });

  return response.data;
}
```

### MMS Messages

Multimedia messages with support for images, audio, video, and other file types:

```typescript
// services/bandwidth/mms.service.ts
import axios from 'axios';
import { bandwidthConfig } from '../../config/bandwidth.config';

interface SendMmsRequest {
  to: string;
  from: string;
  text?: string;
  media: string[];
  tag?: string;
}

interface MediaUploadResponse {
  mediaUrl: string;
}

export async function sendMms(request: SendMmsRequest): Promise<any> {
  const url = `${bandwidthConfig.baseUrl}/users/${bandwidthConfig.accountId}/messages`;
  
  const payload = {
    applicationId: bandwidthConfig.applicationId,
    to: [request.to],
    from: request.from,
    text: request.text || '',
    media: request.media,
    tag: request.tag
  };

  const response = await axios.post(url, payload, {
    auth: {
      username: bandwidthConfig.apiToken,
      password: bandwidthConfig.apiSecret
    },
    headers: {
      'Content-Type': 'application/json'
    }
  });

  return response.data;
}

export async function uploadMedia(
  mediaContent: Buffer,
  contentType: string,
  fileName: string
): Promise<MediaUploadResponse> {
  const url = `${bandwidthConfig.mediaBaseUrl}/${bandwidthConfig.accountId}/media/${fileName}`;
  
  await axios.put(url, mediaContent, {
    auth: {
      username: bandwidthConfig.apiToken,
      password: bandwidthConfig.apiSecret
    },
    headers: {
      'Content-Type': contentType
    }
  });

  return {
    mediaUrl: url
  };
}
```

### Supported Media Types

| Media Type | File Extensions | Max Size |
|------------|-----------------|----------|
| Images | .jpg, .jpeg, .png, .gif | 3.75 MB |
| Audio | .mp3, .wav, .ogg | 3.75 MB |
| Video | .mp4, .3gp | 3.75 MB |
| vCard | .vcf | 3.75 MB |
| Calendar | .ics | 3.75 MB |

### Group Messages

Send messages to multiple recipients:

```typescript
// services/bandwidth/group.service.ts
export async function sendGroupMessage(
  to: string[],
  from: string,
  text: string,
  media?: string[]
): Promise<any> {
  const url = `${bandwidthConfig.baseUrl}/users/${bandwidthConfig.accountId}/messages`;
  
  const payload = {
    applicationId: bandwidthConfig.applicationId,
    to: to, // Array of up to 10 recipients
    from: from,
    text: text,
    media: media || []
  };

  const response = await axios.post(url, payload, {
    auth: {
      username: bandwidthConfig.apiToken,
      password: bandwidthConfig.apiSecret
    }
  });

  return response.data;
}
```

## Error Handling

### Error Code Reference

Bandwidth provides specific error codes for different failure scenarios:

| Error Code | Description | Resolution |
|------------|-------------|------------|
| 4001 | Invalid 'to' number | Validate phone number format |
| 4002 | Invalid 'from' number | Verify number is provisioned |
| 4003 | Message text required | Include text or media |
| 4720 | No routes available | Contact Bandwidth support |
| 4750 | Carrier rejected | Check carrier restrictions |
| 4770 | Invalid destination | Verify recipient number |
| 5100 | Internal error | Retry with exponential backoff |
| 5200 | Timeout | Retry the request |
| 5500 | Carrier service unavailable | Retry later |

### Error Handler Implementation

```typescript
// services/bandwidth/error-handler.ts
export interface BandwidthError {
  type: string;
  description: string;
  code: number;
}

export class BandwidthApiError extends Error {
  public code: number;
  public type: string;
  public isRetryable: boolean;

  constructor(error: BandwidthError) {
    super(error.description);
    this.name = 'BandwidthApiError';
    this.code = error.code;
    this.type = error.type;
    this.isRetryable = this.determineRetryable(error.code);
  }

  private determineRetryable(code: number): boolean {
    // 5xxx errors are typically retryable
    const retryableCodes = [5100, 5200, 5500, 5501, 5502];
    return retryableCodes.includes(code) || (code >= 5000 && code < 6000);
  }
}

export function handleBandwidthError(error: any): never {
  if (error.response?.data) {
    const bandwidthError = error.response.data;
    throw new BandwidthApiError({
      type: bandwidthError.type || 'unknown',
      description: bandwidthError.description || error.message,
      code: bandwidthError.code || error.response.status
    });
  }
  throw error;
}
```

### Retry Strategy Implementation

```typescript
// services/bandwidth/retry.service.ts
import { BandwidthApiError } from './error-handler';

interface RetryConfig {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const defaultRetryConfig: RetryConfig = {
  maxAttempts: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = defaultRetryConfig
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (error instanceof BandwidthApiError && !error.isRetryable) {
        throw error;
      }
      
      if (attempt < config.maxAttempts) {
        const delay = Math.min(
          config.baseDelayMs * Math.pow(2, attempt - 1),
          config.maxDelayMs
        );
        
        console.log(`Retry attempt ${attempt}/${config.maxAttempts} after ${delay}ms`);
        await sleep(delay);
      }
    }
  }
  
  throw lastError;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Dead Letter Queue Processing

Configure a dead letter queue for messages that fail after all retry attempts:

```typescript
// handlers/bandwidth/dlq-processor.ts
import { SQSEvent, SQSHandler } from 'aws-lambda';
import { DynamoDB, SNS } from 'aws-sdk';

const dynamodb = new DynamoDB.DocumentClient();
const sns = new SNS();

export const handler: SQSHandler = async (event: SQSEvent) => {
  for (const record of event.Records) {
    const failedMessage = JSON.parse(record.body);
    
    // Store failed message for investigation
    await dynamodb.put({
      TableName: process.env.FAILED_MESSAGES_TABLE!,
      Item: {
        id: failedMessage.id,
        carrier: 'bandwidth',
        message: failedMessage,
        failedAt: new Date().toISOString(),
        errorDetails: record.attributes
      }
    }).promise();
    
    // Alert operations team
    await sns.publish({
      TopicArn: process.env.ALERTS_TOPIC_ARN!,
      Subject: 'Bandwidth Message Delivery Failed',
      Message: JSON.stringify({
        messageId: failedMessage.id,
        to: failedMessage.to,
        error: failedMessage.lastError
      })
    }).promise();
  }
};
```

### Logging and Monitoring

Implement comprehensive logging for troubleshooting:

```typescript
// utils/logger.ts
import { Logger } from '@aws-lambda-powertools/logger';

export const logger = new Logger({
  serviceName: 'bandwidth-integration',
  logLevel: process.env.LOG_LEVEL || 'INFO'
});

// Usage in handlers
export function logBandwidthRequest(operation: string, request: any): void {
  logger.info('Bandwidth API request', {
    operation,
    to: request.to,
    from: request.from,
    hasMedia: !!request.media?.length
  });
}

export function logBandwidthResponse(operation: string, response: any): void {
  logger.info('Bandwidth API response', {
    operation,
    messageId: response.id,
    segmentCount: response.segmentCount
  });
}

export function logBandwidthError(operation: string, error: any): void {
  logger.error('Bandwidth API error', {
    operation,
    errorCode: error.code,
    errorMessage: error.message,
    isRetryable: error.isRetryable
  });
}
```

### Best Practices

1. **Always validate phone numbers** before sending to avoid 4xxx errors
2. **Use message tags** to correlate callbacks with your internal records
3. **Implement idempotency** using message deduplication IDs
4. **Monitor delivery rates** and set up alerts for unusual failure patterns
5. **Store message history** in DynamoDB for audit and troubleshooting
6. **Use high priority** sparingly and only for time-sensitive messages
7. **Compress media files** to stay within size limits and reduce costs