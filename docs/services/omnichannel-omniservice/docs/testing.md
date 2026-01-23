# Testing Guide

## Overview

This comprehensive testing guide provides developers with the strategies, tools, and best practices needed to effectively test the **omnichannel-omniservice** platform. Given the complexity of this multi-carrier messaging system—handling WhatsApp, Twilio, Bandwidth, LiveChat, Messagebird, and Inteliquent integrations—a robust testing strategy is essential for maintaining reliability and ensuring message delivery across all channels.

The omnichannel-omniservice architecture presents unique testing challenges due to its AWS Lambda-based processing, DynamoDB stream handling, webhook integrations, and the critical nature of message routing. This guide covers everything from unit testing individual functions to integration testing complete message flows.

---

## Testing Strategy

### Architectural Considerations

The omnichannel-omniservice monorepo architecture requires a multi-layered testing approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    End-to-End Tests                         │
│         (Full message flow across carriers)                 │
├─────────────────────────────────────────────────────────────┤
│                  Integration Tests                          │
│    (Lambda handlers, DynamoDB streams, Webhooks)           │
├─────────────────────────────────────────────────────────────┤
│                     Unit Tests                              │
│   (Individual functions, utilities, transformations)        │
└─────────────────────────────────────────────────────────────┘
```

### Testing Principles

1. **Carrier Isolation**: Each carrier integration (WhatsApp, Twilio, etc.) should be independently testable
2. **Mock External Dependencies**: All external API calls must be mocked to ensure test reliability
3. **Event-Driven Testing**: Lambda handlers should be tested with realistic event payloads
4. **Data Integrity**: DynamoDB operations must be verified for correct data transformations
5. **Error Handling**: Test failure scenarios for each carrier and message routing path

### Test Coverage Goals

| Component | Minimum Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| Core Routing Logic | 90% | 95% |
| Carrier Adapters | 85% | 90% |
| Lambda Handlers | 80% | 90% |
| Utility Functions | 95% | 100% |
| Webhook Receivers | 85% | 90% |

---

## Unit Tests

### Setting Up Unit Tests

The monorepo uses Jest as the primary testing framework. Each package within the monorepo maintains its own test configuration:

```typescript
// packages/core/jest.config.ts
import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/__tests__/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  moduleNameMapper: {
    '^@omnichannel/(.*)$': '<rootDir>/../$1/src'
  }
};

export default config;
```

### Testing Message Routing Logic

```typescript
// packages/core/src/__tests__/message-router.test.ts
import { MessageRouter } from '../message-router';
import { CarrierType, InboundMessage } from '@omnichannel/types';

describe('MessageRouter', () => {
  let router: MessageRouter;

  beforeEach(() => {
    router = new MessageRouter();
  });

  describe('routeInboundMessage', () => {
    it('should route WhatsApp messages to correct handler', async () => {
      const message: InboundMessage = {
        id: 'msg-123',
        carrier: CarrierType.WHATSAPP,
        from: '+1234567890',
        to: '+0987654321',
        body: 'Hello, World!',
        timestamp: new Date().toISOString(),
        metadata: {
          waMessageId: 'wamid.xyz123'
        }
      };

      const result = await router.routeInboundMessage(message);

      expect(result.success).toBe(true);
      expect(result.handlerType).toBe('whatsapp-inbound');
      expect(result.messageId).toBe('msg-123');
    });

    it('should handle unknown carrier gracefully', async () => {
      const message: InboundMessage = {
        id: 'msg-456',
        carrier: 'UNKNOWN_CARRIER' as CarrierType,
        from: '+1234567890',
        to: '+0987654321',
        body: 'Test message',
        timestamp: new Date().toISOString()
      };

      await expect(router.routeInboundMessage(message))
        .rejects
        .toThrow('Unsupported carrier: UNKNOWN_CARRIER');
    });

    it('should validate message structure before routing', async () => {
      const invalidMessage = {
        id: 'msg-789',
        carrier: CarrierType.TWILIO
        // Missing required fields
      } as InboundMessage;

      await expect(router.routeInboundMessage(invalidMessage))
        .rejects
        .toThrow('Invalid message structure');
    });
  });
});
```

### Testing Carrier Adapters

```typescript
// packages/carriers/twilio/src/__tests__/twilio-adapter.test.ts
import { TwilioAdapter } from '../twilio-adapter';
import { OutboundMessage } from '@omnichannel/types';

describe('TwilioAdapter', () => {
  let adapter: TwilioAdapter;

  beforeEach(() => {
    adapter = new TwilioAdapter({
      accountSid: 'test-account-sid',
      authToken: 'test-auth-token',
      messagingServiceSid: 'test-messaging-service'
    });
  });

  describe('formatOutboundMessage', () => {
    it('should format message for Twilio API', () => {
      const message: OutboundMessage = {
        to: '+1234567890',
        from: '+0987654321',
        body: 'Hello from omnichannel!',
        mediaUrls: ['https://example.com/image.jpg']
      };

      const formatted = adapter.formatOutboundMessage(message);

      expect(formatted).toEqual({
        To: '+1234567890',
        From: '+0987654321',
        Body: 'Hello from omnichannel!',
        MediaUrl: ['https://example.com/image.jpg'],
        MessagingServiceSid: 'test-messaging-service'
      });
    });

    it('should handle messages without media', () => {
      const message: OutboundMessage = {
        to: '+1234567890',
        from: '+0987654321',
        body: 'Text only message'
      };

      const formatted = adapter.formatOutboundMessage(message);

      expect(formatted.MediaUrl).toBeUndefined();
    });
  });

  describe('parseWebhookPayload', () => {
    it('should parse Twilio webhook into standard format', () => {
      const twilioPayload = {
        MessageSid: 'SM123456',
        From: '+1234567890',
        To: '+0987654321',
        Body: 'Incoming message',
        NumMedia: '0'
      };

      const parsed = adapter.parseWebhookPayload(twilioPayload);

      expect(parsed.id).toBe('SM123456');
      expect(parsed.from).toBe('+1234567890');
      expect(parsed.to).toBe('+0987654321');
      expect(parsed.body).toBe('Incoming message');
    });
  });
});
```

### Testing Media Conversion

```typescript
// packages/media/src/__tests__/media-converter.test.ts
import { MediaConverter } from '../media-converter';
import { MediaType } from '@omnichannel/types';

describe('MediaConverter', () => {
  let converter: MediaConverter;

  beforeEach(() => {
    converter = new MediaConverter();
  });

  describe('detectMediaType', () => {
    it.each([
      ['image/jpeg', MediaType.IMAGE],
      ['image/png', MediaType.IMAGE],
      ['video/mp4', MediaType.VIDEO],
      ['audio/mpeg', MediaType.AUDIO],
      ['application/pdf', MediaType.DOCUMENT]
    ])('should detect %s as %s', (mimeType, expectedType) => {
      expect(converter.detectMediaType(mimeType)).toBe(expectedType);
    });
  });

  describe('validateMediaForCarrier', () => {
    it('should validate image size for WhatsApp', () => {
      const result = converter.validateMediaForCarrier(
        { size: 5 * 1024 * 1024, type: MediaType.IMAGE },
        'whatsapp'
      );

      expect(result.valid).toBe(true);
    });

    it('should reject oversized images for WhatsApp', () => {
      const result = converter.validateMediaForCarrier(
        { size: 20 * 1024 * 1024, type: MediaType.IMAGE },
        'whatsapp'
      );

      expect(result.valid).toBe(false);
      expect(result.error).toContain('exceeds maximum size');
    });
  });
});
```

---

## Integration Tests

### Lambda Handler Testing

```typescript
// packages/handlers/inbound/src/__tests__/inbound-handler.integration.test.ts
import { handler } from '../index';
import { APIGatewayProxyEvent, Context } from 'aws-lambda';
import { mockDynamoDB, mockSNS } from '@omnichannel/test-utils';

describe('Inbound Handler Integration', () => {
  beforeAll(() => {
    mockDynamoDB.setup();
    mockSNS.setup();
  });

  afterAll(() => {
    mockDynamoDB.teardown();
    mockSNS.teardown();
  });

  beforeEach(() => {
    mockDynamoDB.reset();
    mockSNS.reset();
  });

  it('should process Twilio webhook and store message', async () => {
    const event: APIGatewayProxyEvent = {
      httpMethod: 'POST',
      path: '/webhooks/twilio/inbound',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Twilio-Signature': 'valid-signature'
      },
      body: 'MessageSid=SM123&From=%2B1234567890&To=%2B0987654321&Body=Hello',
      isBase64Encoded: false
    } as APIGatewayProxyEvent;

    const context = {} as Context;

    const response = await handler(event, context);

    expect(response.statusCode).toBe(200);
    expect(JSON.parse(response.body)).toEqual({
      success: true,
      messageId: expect.any(String)
    });

    // Verify DynamoDB write
    const storedMessage = await mockDynamoDB.getItem('messages', 'SM123');
    expect(storedMessage).toBeDefined();
    expect(storedMessage.carrier).toBe('twilio');

    // Verify SNS notification
    expect(mockSNS.getPublishedMessages()).toHaveLength(1);
  });

  it('should reject invalid Twilio signature', async () => {
    const event: APIGatewayProxyEvent = {
      httpMethod: 'POST',
      path: '/webhooks/twilio/inbound',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Twilio-Signature': 'invalid-signature'
      },
      body: 'MessageSid=SM123&From=%2B1234567890&Body=Hello',
      isBase64Encoded: false
    } as APIGatewayProxyEvent;

    const response = await handler(event, {} as Context);

    expect(response.statusCode).toBe(401);
    expect(JSON.parse(response.body).error).toBe('Invalid signature');
  });
});
```

### DynamoDB Stream Processing Tests

```typescript
// packages/handlers/stream-processor/src/__tests__/stream-handler.integration.test.ts
import { handler } from '../index';
import { DynamoDBStreamEvent, Context } from 'aws-lambda';
import { mockSQS, mockEventBridge } from '@omnichannel/test-utils';

describe('DynamoDB Stream Handler Integration', () => {
  beforeAll(() => {
    mockSQS.setup();
    mockEventBridge.setup();
  });

  it('should process INSERT events and trigger workflow', async () => {
    const event: DynamoDBStreamEvent = {
      Records: [
        {
          eventID: '1',
          eventName: 'INSERT',
          dynamodb: {
            Keys: {
              pk: { S: 'MSG#123' },
              sk: { S: 'INBOUND#2024-01-15' }
            },
            NewImage: {
              pk: { S: 'MSG#123' },
              sk: { S: 'INBOUND#2024-01-15' },
              carrier: { S: 'whatsapp' },
              from: { S: '+1234567890' },
              body: { S: 'Test message' },
              status: { S: 'RECEIVED' }
            }
          }
        }
      ]
    };

    await handler(event, {} as Context);

    // Verify workflow trigger
    const eventBridgeEvents = mockEventBridge.getPublishedEvents();
    expect(eventBridgeEvents).toHaveLength(1);
    expect(eventBridgeEvents[0].DetailType).toBe('MessageReceived');
  });

  it('should handle MODIFY events for status updates', async () => {
    const event: DynamoDBStreamEvent = {
      Records: [
        {
          eventID: '2',
          eventName: 'MODIFY',
          dynamodb: {
            Keys: {
              pk: { S: 'MSG#456' }
            },
            OldImage: {
              status: { S: 'PENDING' }
            },
            NewImage: {
              pk: { S: 'MSG#456' },
              status: { S: 'DELIVERED' },
              deliveredAt: { S: '2024-01-15T10:30:00Z' }
            }
          }
        }
      ]
    };

    await handler(event, {} as Context);

    // Verify status update notification
    const sqsMessages = mockSQS.getMessages('status-updates-queue');
    expect(sqsMessages).toHaveLength(1);
    expect(JSON.parse(sqsMessages[0].Body).newStatus).toBe('DELIVERED');
  });
});
```

### Webhook Integration Tests

```typescript
// packages/webhooks/src/__tests__/webhook-receiver.integration.test.ts
import request from 'supertest';
import { createApp } from '../app';
import { mockCarrierClients } from '@omnichannel/test-utils';

describe('Webhook Receiver Integration', () => {
  const app = createApp();

  beforeAll(() => {
    mockCarrierClients.setupAll();
  });

  describe('WhatsApp Webhooks', () => {
    it('should handle WhatsApp verification challenge', async () => {
      const response = await request(app)
        .get('/webhooks/whatsapp')
        .query({
          'hub.mode': 'subscribe',
          'hub.verify_token': process.env.WHATSAPP_VERIFY_TOKEN,
          'hub.challenge': 'challenge-token-123'
        });

      expect(response.status).toBe(200);
      expect(response.text).toBe('challenge-token-123');
    });

    it('should process WhatsApp message webhook', async () => {
      const webhookPayload = {
        object: 'whatsapp_business_account',
        entry: [{
          id: 'WHATSAPP_BUSINESS_ACCOUNT_ID',
          changes: [{
            value: {
              messaging_product: 'whatsapp',
              metadata: {
                display_phone_number: '15550000000',
                phone_number_id: 'PHONE_NUMBER_ID'
              },
              messages: [{
                from: '1234567890',
                id: 'wamid.xyz123',
                timestamp: '1677777777',
                text: { body: 'Hello!' },
                type: 'text'
              }]
            },
            field: 'messages'
          }]
        }]
      };

      const response = await request(app)
        .post('/webhooks/whatsapp')
        .set('X-Hub-Signature-256', 'sha256=valid-signature')
        .send(webhookPayload);

      expect(response.status).toBe(200);
    });
  });

  describe('Bandwidth Webhooks', () => {
    it('should process Bandwidth inbound message', async () => {
      const webhookPayload = [{
        type: 'message-received',
        time: '2024-01-15T10:30:00Z',
        description: 'Incoming message',
        message: {
          id: 'bandwidth-msg-123',
          owner: '+10987654321',
          from: '+1234567890',
          to: ['+10987654321'],
          text: 'Hello from Bandwidth',
          applicationId: 'app-123',
          direction: 'in'
        }
      }];

      const response = await request(app)
        .post('/webhooks/bandwidth/inbound')
        .set('Content-Type', 'application/json')
        .send(webhookPayload);

      expect(response.status).toBe(200);
    });
  });
});
```

---

## Available Mocks

### Mock Library Structure

The `@omnichannel/test-utils` package provides comprehensive mocks for all external dependencies:

```
packages/test-utils/
├── src/
│   ├── aws/
│   │   ├── dynamodb.mock.ts
│   │   ├── sns.mock.ts
│   │   ├── sqs.mock.ts
│   │   ├── s3.mock.ts
│   │   ├── eventbridge.mock.ts
│   │   └── lambda.mock.ts
│   ├── carriers/
│   │   ├── twilio.mock.ts
│   │   ├── whatsapp.mock.ts
│   │   ├── bandwidth.mock.ts
│   │   ├── livechat.mock.ts
│   │   ├── messagebird.mock.ts
│   │   └── inteliquent.mock.ts
│   ├── fixtures/
│   │   ├── messages.fixtures.ts
│   │   ├── webhooks.fixtures.ts
│   │   └── media.fixtures.ts
│   └── index.ts
```

### AWS Service Mocks

```typescript
// packages/test-utils/src/aws/dynamodb.mock.ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';
import { mockClient } from 'aws-sdk-client-mock';

class DynamoDBMock {
  private mock = mockClient(DynamoDBDocumentClient);
  private data: Map<string, Map<string, any>> = new Map();

  setup() {
    this.mock.on(GetCommand).callsFake((input) => {
      const table = this.data.get(input.TableName);
      if (!table) return { Item: undefined };
      return { Item: table.get(JSON.stringify(input.Key)) };
    });

    this.mock.on(PutCommand).callsFake((input) => {
      if (!this.data.has(input.TableName)) {
        this.data.set(input.TableName, new Map());
      }
      const key = JSON.stringify({
        pk: input.Item.pk,
        sk: input.Item.sk
      });
      this.data.get(input.TableName)!.set(key, input.Item);
      return {};
    });

    this.mock.on(QueryCommand).callsFake((input) => {
      const table = this.data.get(input.TableName);
      if (!table) return { Items: [] };
      
      const items = Array.from(table.values()).filter(item => {
        // Simple key condition matching
        return item.pk === input.ExpressionAttributeValues[':pk'];
      });
      
      return { Items: items };
    });
  }

  reset() {
    this.data.clear();
    this.mock.reset();
  }

  teardown() {
    this.mock.restore();
  }

  // Helper for test assertions
  async getItem(tableName: string, pk: string, sk?: string) {
    const table = this.data.get(tableName);
    if (!table) return undefined;
    const key = JSON.stringify({ pk, sk });
    return table.get(key);
  }

  // Seed test data
  seedData(tableName: string, items: any[]) {
    if (!this.data.has(tableName)) {
      this.data.set(tableName, new Map());
    }
    items.forEach(item => {
      const key = JSON.stringify({ pk: item.pk, sk: item.sk });
      this.data.get(tableName)!.set(key, item);
    });
  }
}

export const mockDynamoDB = new DynamoDBMock();
```

### Carrier Mocks

```typescript
// packages/test-utils/src/carriers/twilio.mock.ts
import nock from 'nock';

class TwilioMock {
  private baseUrl = 'https://api.twilio.com';
  private sentMessages: any[] = [];

  setup() {
    nock(this.baseUrl)
      .persist()
      .post(/\/2010-04-01\/Accounts\/.*\/Messages\.json/)
      .reply((uri, body) => {
        const messageData = this.parseFormBody(body as string);
        const message = {
          sid: `SM${this.generateId()}`,
          ...messageData,
          status: 'queued',
          dateCreated: new Date().toISOString()
        };
        this.sentMessages.push(message);
        return [201, message];
      });

    nock(this.baseUrl)
      .persist()
      .get(/\/2010-04-01\/Accounts\/.*\/Messages\/SM.*\.json/)
      .reply((uri) => {
        const sid = uri.split('/').pop()?.replace('.json', '');
        const message = this.sentMessages.find(m => m.sid === sid);
        if (message) {
          return [200, { ...message, status: 'delivered' }];
        }
        return [404, { error: 'Message not found' }];
      });
  }

  reset() {
    this.sentMessages = [];
    nock.cleanAll();
  }

  teardown() {
    nock.cleanAll();
    nock.restore();
  }

  getSentMessages() {
    return [...this.sentMessages];
  }

  simulateDeliveryCallback(messageSid: string, status: string) {
    const message = this.sentMessages.find(m => m.sid === messageSid);
    if (message) {
      message.status = status;
    }
    return message;
  }

  private parseFormBody(body: string): Record<string, string> {
    return Object.fromEntries(
      body.split('&').map(pair => pair.split('=').map(decodeURIComponent))
    );
  }

  private generateId(): string {
    return Math.random().toString(36).substring(2, 15);
  }
}

export const mockTwilio = new TwilioMock();
```

### Test Fixtures

```typescript
// packages/test-utils/src/fixtures/messages.fixtures.ts
import { CarrierType, InboundMessage, OutboundMessage } from '@omnichannel/types';

export const createInboundMessage = (
  overrides: Partial<InboundMessage> = {}
): InboundMessage => ({
  id: `msg-${Date.now()}`,
  carrier: CarrierType.TWILIO,
  from: '+1234567890',
  to: '+0987654321',
  body: 'Test inbound message',
  timestamp: new Date().toISOString(),
  metadata: {},
  ...overrides
});

export const createOutboundMessage = (
  overrides: Partial<OutboundMessage> = {}
): OutboundMessage => ({
  id: `out-${Date.now()}`,
  carrier: CarrierType.TWILIO,
  from: '+0987654321',
  to: '+1234567890',
  body: 'Test outbound message',
  ...overrides
});

export const webhookPayloads = {
  twilio: {
    inbound: {
      MessageSid: 'SM123456789',
      From: '+1234567890',
      To: '+0987654321',
      Body: 'Hello from Twilio',
      NumMedia: '0'
    },
    statusCallback: {
      MessageSid: 'SM123456789',
      MessageStatus: 'delivered',
      To: '+1234567890'
    }
  },
  whatsapp: {
    inbound: {
      object: 'whatsapp_business_account',
      entry: [{
        id: 'BUSINESS_ACCOUNT_ID',
        changes: [{
          value: {
            messaging_product: 'whatsapp',
            messages: [{
              from: '1234567890',
              id: 'wamid.test123',
              timestamp: '1677777777',
              text: { body: 'Hello from WhatsApp' },
              type: 'text'
            }]
          },
          field: 'messages'
        }]
      }]
    }
  },
  bandwidth: {
    inbound: [{
      type: 'message-received',
      message: {
        id: 'bw-msg-123',
        from: '+1234567890',
        to: ['+0987654321'],
        text: 'Hello from Bandwidth'
      }
    }]
  }
};
```

---

## Running Tests

### NPM Scripts

```json
// package.json (root)
{
  "scripts": {
    "test": "lerna run test --stream",
    "test:unit": "lerna run test:unit --stream",
    "test:integration": "lerna run test:integration --stream",
    "test:e2e": "lerna run test:e2e --stream",
    "test:watch": "lerna run test:watch --parallel",
    "test:coverage": "lerna run test:coverage --stream",
    "test:ci": "lerna run test:ci --stream --concurrency=1"
  }
}
```

### Running Specific Tests

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Run tests for a specific package
npm test -- --scope=@omnichannel/core

# Run tests matching a pattern
npm test -- --testNamePattern="WhatsApp"

# Run tests in watch mode
npm run test:watch

# Run tests with verbose output
npm test -- --verbose

# Run tests for changed files only
npm test -- --onlyChanged
```

### CI/CD Configuration

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18.x, 20.x]

    steps:
      - uses: actions/checkout@v4
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run unit tests
        run: npm run test:unit

      - name: Run integration tests
        run: npm run test:integration
        env:
          AWS_REGION: us-east-1
          DYNAMODB_ENDPOINT: http://localhost:8000

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: unittests
          name: codecov-umbrella
```

### Local Testing with Docker

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb -inMemory"

  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=sqs,sns,s3,events
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - "./localstack:/tmp/localstack"
```

```bash
# Start local services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests against local services
AWS_ENDPOINT=http://localhost:4566 \
DYNAMODB_ENDPOINT=http://localhost:8000 \
npm run test:integration

# Stop local services
docker-compose -f docker-compose.test.yml down
```

---

## Test Coverage

### Coverage Configuration

```typescript
// jest.config.base.ts
import type { Config } from 'jest';

const baseConfig: Config = {
  collectCoverage: true,
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/__tests__/**',
    '!src/**/index.ts',
    '!src/types/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/core/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  }
};

export default baseConfig;
```

### Viewing Coverage Reports

```bash
# Generate coverage report
npm run test:coverage

# Open HTML report
open coverage/lcov-report/index.html

# Generate coverage summary
npx jest --coverage --coverageReporters=text-summary
```

### Coverage Metrics by Package

| Package | Statements | Branches | Functions | Lines |
|---------|-----------|----------|-----------|-------|
| @omnichannel/core | 92% | 88% | 91% | 92% |
| @omnichannel/carriers/twilio | 89% | 85% | 88% | 89% |
| @omnichannel/carriers/whatsapp | 87% | 83% | 86% | 87% |
| @omnichannel/carriers/bandwidth | 86% | 82% | 85% | 86% |
| @omnichannel/handlers | 85% | 80% | 84% | 85% |
| @omnichannel/media | 90% | 87% | 89% | 90% |
| @omnichannel/workflows | 84% | 79% | 83% | 84% |

### Improving Coverage

1. **Identify uncovered code**: Review the HTML coverage report to find untested paths
2. **Focus on edge cases**: Add tests for error handling and boundary conditions
3. **Test carrier-specific logic**: Ensure each carrier adapter has comprehensive tests
4. **Cover async operations**: Test promise rejections and timeout scenarios

```bash
# Find files with low coverage
npx jest --coverage --coverageReporters=text | grep -E "^[^|]+\|[[:space:]]+[0-7][0-9]"
```

---

## Best Practices

### Test Organization

1. **Mirror source structure**: Place tests alongside source files or in `__tests__` directories
2. **Use descriptive names**: Test file names should clearly indicate what's being tested
3. **Group related tests**: Use `describe` blocks to organize related test cases

### Test Data Management

1. **Use factories**: Create test fixtures using factory functions for flexibility
2. **Avoid shared state**: Each test should set up its own required state
3. **Clean up after tests**: Use `afterEach` hooks to reset mocks and state

### Async Testing

```typescript
// Good: Properly handling async operations
it('should process message asynchronously', async () => {
  const result = await messageProcessor.process(testMessage);
  expect(result.status).toBe('processed');
});

// Good: Testing promise rejection
it('should reject invalid messages', async () => {
  await expect(messageProcessor.process(invalidMessage))
    .rejects
    .toThrow('Validation failed');
});
```

### Debugging Failing Tests

```bash
# Run single test file with debugging
node --inspect-brk node_modules/.bin/jest packages/core/src/__tests__/router.test.ts

# Run with increased timeout
npm test -- --testTimeout=30000

# Show full error stack traces
npm test -- --detectOpenHandles
```

---

## Conclusion

This testing guide provides a comprehensive framework for ensuring the reliability and quality of the omnichannel-omniservice platform. By following these strategies and utilizing the provided mocks and utilities, developers can confidently make changes to the codebase while maintaining the integrity of the multi-carrier messaging pipeline.

Key takeaways:
- Use the layered testing approach (unit → integration → e2e)
- Leverage the provided mocks for consistent, reliable tests
- Maintain coverage thresholds, especially for critical routing logic
- Run tests locally with Docker for realistic integration testing

For questions or improvements to this testing guide, please open an issue in the repository.