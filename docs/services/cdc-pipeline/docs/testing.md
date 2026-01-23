# Testing Guide

## Overview

This comprehensive guide covers testing practices for the CDC Pipeline service, a Change Data Capture system that processes database changes from CoreDB tables and publishes events to EventBridge. Given the critical nature of this service—handling real-time data synchronization across 12+ tables—thorough testing is essential to ensure reliability, data integrity, and proper event distribution to downstream consumers like the Wallboards service.

The CDC Pipeline operates in a complex environment involving AWS Lambda, Kinesis streams, DynamoDB, and EventBridge. This guide provides detailed instructions for writing effective unit tests, integration tests, and leveraging mock utilities to simulate AWS services and database interactions.

## Test Setup

### Prerequisites

Before running tests, ensure you have the following installed:

```bash
# Verify Node.js version (18.x or higher recommended)
node --version

# Verify npm version
npm --version

# Install dependencies including dev dependencies
npm install
```

### Project Test Structure

The CDC Pipeline follows a well-organized test structure:

```
cdc-pipeline/
├── src/
│   ├── handlers/
│   │   └── __tests__/
│   │       ├── kinesis-processor.test.ts
│   │       ├── event-publisher.test.ts
│   │       └── data-transformer.test.ts
│   ├── services/
│   │   └── __tests__/
│   │       ├── cdc-processor.test.ts
│   │       ├── redaction-service.test.ts
│   │       └── state-manager.test.ts
│   └── utils/
│       └── __tests__/
│           └── data-utils.test.ts
├── tests/
│   ├── integration/
│   │   ├── kinesis-to-eventbridge.test.ts
│   │   └── full-pipeline.test.ts
│   ├── mocks/
│   │   ├── aws-mocks.ts
│   │   ├── coredb-mocks.ts
│   │   ├── kinesis-records.ts
│   │   └── test-fixtures.ts
│   └── setup/
│       ├── jest.setup.ts
│       └── test-helpers.ts
├── jest.config.js
└── jest.integration.config.js
```

### Initial Setup Commands

```bash
# Install testing dependencies
npm install --save-dev jest @types/jest ts-jest aws-sdk-client-mock @aws-sdk/client-dynamodb @aws-sdk/client-eventbridge @aws-sdk/client-kinesis

# Create test directories if they don't exist
mkdir -p tests/integration tests/mocks tests/setup

# Run initial test setup validation
npm run test:setup
```

## Jest Configuration

### Main Jest Configuration (`jest.config.js`)

```javascript
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.test.ts',
    '**/*.spec.ts'
  ],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: 'tsconfig.test.json'
    }]
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@mocks/(.*)$': '<rootDir>/tests/mocks/$1',
    '^@fixtures/(.*)$': '<rootDir>/tests/fixtures/$1'
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup/jest.setup.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
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
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  testTimeout: 30000,
  verbose: true,
  clearMocks: true,
  restoreMocks: true
};
```

### Integration Test Configuration (`jest.integration.config.js`)

```javascript
/** @type {import('jest').Config} */
module.exports = {
  ...require('./jest.config'),
  testMatch: ['<rootDir>/tests/integration/**/*.test.ts'],
  testTimeout: 60000,
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup/jest.setup.ts',
    '<rootDir>/tests/setup/integration.setup.ts'
  ],
  maxWorkers: 1, // Run integration tests sequentially
  coverageDirectory: 'coverage/integration'
};
```

### Jest Setup File (`tests/setup/jest.setup.ts`)

```typescript
import { mockClient } from 'aws-sdk-client-mock';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { EventBridgeClient } from '@aws-sdk/client-eventbridge';
import { KinesisClient } from '@aws-sdk/client-kinesis';

// Global mock clients
export const dynamoMock = mockClient(DynamoDBClient);
export const eventBridgeMock = mockClient(EventBridgeClient);
export const kinesisMock = mockClient(KinesisClient);

beforeEach(() => {
  // Reset all mocks before each test
  dynamoMock.reset();
  eventBridgeMock.reset();
  kinesisMock.reset();
  
  // Clear all timers
  jest.clearAllTimers();
  
  // Reset modules to ensure clean state
  jest.resetModules();
});

afterEach(() => {
  // Restore all mocks after each test
  jest.restoreAllMocks();
});

// Global test utilities
global.console = {
  ...console,
  // Suppress console.log during tests unless DEBUG is set
  log: process.env.DEBUG ? console.log : jest.fn(),
  debug: process.env.DEBUG ? console.debug : jest.fn(),
  info: process.env.DEBUG ? console.info : jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};
```

## Environment Variables for Tests

### Test Environment Configuration

Create a `.env.test` file for test-specific environment variables:

```bash
# .env.test - Test Environment Configuration

# AWS Configuration (LocalStack or mocked)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test-access-key
AWS_SECRET_ACCESS_KEY=test-secret-key

# DynamoDB Configuration
DYNAMODB_TABLE_STATE=cdc-pipeline-state-test
DYNAMODB_TABLE_CHECKPOINTS=cdc-pipeline-checkpoints-test
DYNAMODB_ENDPOINT=http://localhost:4566

# EventBridge Configuration
EVENTBRIDGE_BUS_NAME=cdc-events-test
EVENTBRIDGE_ENDPOINT=http://localhost:4566

# Kinesis Configuration
KINESIS_STREAM_NAME=cdc-stream-test
KINESIS_ENDPOINT=http://localhost:4566

# CDC Processing Configuration
CDC_BATCH_SIZE=10
CDC_MAX_RETRIES=3
CDC_RETRY_DELAY_MS=100

# Redaction Configuration
REDACTION_ENABLED=true
REDACTION_FIELDS=ssn,credit_card,password

# Logging
LOG_LEVEL=error
DEBUG_MODE=false

# Test-specific settings
TEST_TIMEOUT=30000
MOCK_EXTERNAL_SERVICES=true
```

### Loading Environment Variables in Tests

```typescript
// tests/setup/env.setup.ts
import dotenv from 'dotenv';
import path from 'path';

// Load test environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env.test') });

// Validate required environment variables
const requiredEnvVars = [
  'AWS_REGION',
  'DYNAMODB_TABLE_STATE',
  'EVENTBRIDGE_BUS_NAME',
  'KINESIS_STREAM_NAME'
];

requiredEnvVars.forEach((envVar) => {
  if (!process.env[envVar]) {
    throw new Error(`Missing required test environment variable: ${envVar}`);
  }
});

// Export test configuration object
export const testConfig = {
  aws: {
    region: process.env.AWS_REGION!,
    dynamodbEndpoint: process.env.DYNAMODB_ENDPOINT,
    eventBridgeEndpoint: process.env.EVENTBRIDGE_ENDPOINT,
    kinesisEndpoint: process.env.KINESIS_ENDPOINT
  },
  tables: {
    state: process.env.DYNAMODB_TABLE_STATE!,
    checkpoints: process.env.DYNAMODB_TABLE_CHECKPOINTS!
  },
  cdc: {
    batchSize: parseInt(process.env.CDC_BATCH_SIZE || '10'),
    maxRetries: parseInt(process.env.CDC_MAX_RETRIES || '3'),
    retryDelayMs: parseInt(process.env.CDC_RETRY_DELAY_MS || '100')
  },
  redaction: {
    enabled: process.env.REDACTION_ENABLED === 'true',
    fields: (process.env.REDACTION_FIELDS || '').split(',')
  }
};
```

## Available Mocks

### AWS Service Mocks

#### DynamoDB Mock (`tests/mocks/aws-mocks.ts`)

```typescript
import { mockClient } from 'aws-sdk-client-mock';
import {
  DynamoDBClient,
  PutItemCommand,
  GetItemCommand,
  QueryCommand,
  UpdateItemCommand,
  DeleteItemCommand
} from '@aws-sdk/client-dynamodb';
import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';

export const createDynamoDBMock = () => {
  const mock = mockClient(DynamoDBClient);

  return {
    mock,
    
    // Mock successful put operation
    mockPutItem: (tableName: string, expectedItem?: Record<string, any>) => {
      mock.on(PutItemCommand, expectedItem ? {
        TableName: tableName,
        Item: marshall(expectedItem)
      } : { TableName: tableName }).resolves({});
    },

    // Mock get operation with response
    mockGetItem: (tableName: string, response: Record<string, any> | null) => {
      mock.on(GetItemCommand, { TableName: tableName }).resolves({
        Item: response ? marshall(response) : undefined
      });
    },

    // Mock query operation
    mockQuery: (tableName: string, items: Record<string, any>[]) => {
      mock.on(QueryCommand, { TableName: tableName }).resolves({
        Items: items.map(item => marshall(item)),
        Count: items.length
      });
    },

    // Mock update operation
    mockUpdateItem: (tableName: string) => {
      mock.on(UpdateItemCommand, { TableName: tableName }).resolves({
        Attributes: {}
      });
    },

    // Mock failure scenarios
    mockPutItemFailure: (tableName: string, error: Error) => {
      mock.on(PutItemCommand, { TableName: tableName }).rejects(error);
    },

    reset: () => mock.reset()
  };
};
```

#### EventBridge Mock

```typescript
import { mockClient } from 'aws-sdk-client-mock';
import {
  EventBridgeClient,
  PutEventsCommand,
  PutEventsCommandOutput
} from '@aws-sdk/client-eventbridge';

export const createEventBridgeMock = () => {
  const mock = mockClient(EventBridgeClient);

  return {
    mock,

    // Mock successful event publishing
    mockPutEvents: (expectedEntries?: number) => {
      mock.on(PutEventsCommand).resolves({
        FailedEntryCount: 0,
        Entries: Array(expectedEntries || 1).fill({
          EventId: `event-${Date.now()}`
        })
      });
    },

    // Mock partial failure
    mockPutEventsPartialFailure: (failedCount: number, totalCount: number) => {
      const entries = [];
      for (let i = 0; i < totalCount; i++) {
        if (i < failedCount) {
          entries.push({
            ErrorCode: 'InternalError',
            ErrorMessage: 'Internal service error'
          });
        } else {
          entries.push({ EventId: `event-${i}` });
        }
      }
      
      mock.on(PutEventsCommand).resolves({
        FailedEntryCount: failedCount,
        Entries: entries
      });
    },

    // Mock complete failure
    mockPutEventsFailure: (error: Error) => {
      mock.on(PutEventsCommand).rejects(error);
    },

    // Get sent events for verification
    getSentEvents: (): any[] => {
      return mock.commandCalls(PutEventsCommand).map(call => call.args[0].input);
    },

    reset: () => mock.reset()
  };
};
```

#### Kinesis Mock

```typescript
import { mockClient } from 'aws-sdk-client-mock';
import {
  KinesisClient,
  PutRecordCommand,
  PutRecordsCommand,
  GetRecordsCommand
} from '@aws-sdk/client-kinesis';

export const createKinesisMock = () => {
  const mock = mockClient(KinesisClient);

  return {
    mock,

    // Mock put record
    mockPutRecord: (streamName: string) => {
      mock.on(PutRecordCommand, { StreamName: streamName }).resolves({
        ShardId: 'shardId-000000000000',
        SequenceNumber: '49590338271490256608559692538361571095921575989136588818'
      });
    },

    // Mock put records (batch)
    mockPutRecords: (streamName: string, recordCount: number) => {
      mock.on(PutRecordsCommand, { StreamName: streamName }).resolves({
        FailedRecordCount: 0,
        Records: Array(recordCount).fill({
          ShardId: 'shardId-000000000000',
          SequenceNumber: '49590338271490256608559692538361571095921575989136588818'
        })
      });
    },

    // Create mock Kinesis event for Lambda testing
    createKinesisEvent: (records: any[]): AWSLambda.KinesisStreamEvent => {
      return {
        Records: records.map((record, index) => ({
          kinesis: {
            kinesisSchemaVersion: '1.0',
            partitionKey: `partition-${index}`,
            sequenceNumber: `seq-${index}`,
            data: Buffer.from(JSON.stringify(record)).toString('base64'),
            approximateArrivalTimestamp: Date.now() / 1000
          },
          eventSource: 'aws:kinesis',
          eventVersion: '1.0',
          eventID: `shardId-000000000000:${index}`,
          eventName: 'aws:kinesis:record',
          invokeIdentityArn: 'arn:aws:iam::123456789012:role/lambda-role',
          awsRegion: 'us-east-1',
          eventSourceARN: 'arn:aws:kinesis:us-east-1:123456789012:stream/test-stream'
        }))
      };
    },

    reset: () => mock.reset()
  };
};
```

### CoreDB Mocks (`tests/mocks/coredb-mocks.ts`)

```typescript
// Mock CDC records for different CoreDB tables
export const createCDCRecordMock = (
  tableName: string,
  operation: 'INSERT' | 'UPDATE' | 'DELETE',
  data: Record<string, any>
) => {
  return {
    tableName,
    operation,
    timestamp: new Date().toISOString(),
    transactionId: `txn-${Date.now()}`,
    sequenceNumber: Math.floor(Math.random() * 1000000),
    data: {
      before: operation === 'INSERT' ? null : { ...data, modifiedAt: '2024-01-01T00:00:00Z' },
      after: operation === 'DELETE' ? null : data
    },
    metadata: {
      source: 'coredb',
      version: '1.0',
      schemaVersion: 1
    }
  };
};

// Pre-built fixtures for common tables
export const cdcFixtures = {
  users: {
    insert: createCDCRecordMock('users', 'INSERT', {
      id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
      createdAt: new Date().toISOString()
    }),
    update: createCDCRecordMock('users', 'UPDATE', {
      id: 'user-123',
      email: 'updated@example.com',
      name: 'Updated User',
      modifiedAt: new Date().toISOString()
    }),
    delete: createCDCRecordMock('users', 'DELETE', {
      id: 'user-123'
    })
  },

  orders: {
    insert: createCDCRecordMock('orders', 'INSERT', {
      orderId: 'order-456',
      userId: 'user-123',
      status: 'pending',
      totalAmount: 99.99,
      createdAt: new Date().toISOString()
    }),
    statusUpdate: createCDCRecordMock('orders', 'UPDATE', {
      orderId: 'order-456',
      status: 'completed',
      completedAt: new Date().toISOString()
    })
  },

  inventory: {
    update: createCDCRecordMock('inventory', 'UPDATE', {
      productId: 'prod-789',
      quantity: 50,
      warehouseId: 'wh-001',
      lastUpdated: new Date().toISOString()
    })
  }
};

// Mock for sensitive data that should be redacted
export const sensitiveDataFixtures = {
  userWithPII: createCDCRecordMock('users', 'INSERT', {
    id: 'user-sensitive',
    email: 'sensitive@example.com',
    ssn: '123-45-6789',
    creditCard: '4111111111111111',
    password: 'hashed_password_value',
    phone: '+1-555-123-4567'
  })
};
```

### Test Fixtures (`tests/mocks/test-fixtures.ts`)

```typescript
import { cdcFixtures, createCDCRecordMock } from './coredb-mocks';

// Generate batch of CDC records for load testing
export const generateCDCBatch = (
  count: number,
  tableName: string = 'users',
  operation: 'INSERT' | 'UPDATE' | 'DELETE' = 'INSERT'
): any[] => {
  return Array.from({ length: count }, (_, index) => 
    createCDCRecordMock(tableName, operation, {
      id: `record-${index}`,
      data: `test-data-${index}`,
      timestamp: new Date().toISOString()
    })
  );
};

// Mixed operation batch for realistic testing
export const generateMixedCDCBatch = (count: number): any[] => {
  const operations: Array<'INSERT' | 'UPDATE' | 'DELETE'> = ['INSERT', 'UPDATE', 'DELETE'];
  const tables = ['users', 'orders', 'inventory', 'products', 'customers'];
  
  return Array.from({ length: count }, (_, index) => {
    const operation = operations[index % operations.length];
    const table = tables[index % tables.length];
    
    return createCDCRecordMock(table, operation, {
      id: `mixed-${index}`,
      value: Math.random() * 1000,
      timestamp: new Date().toISOString()
    });
  });
};

// Error scenario fixtures
export const errorFixtures = {
  malformedRecord: {
    // Missing required fields
    tableName: 'users',
    // Missing operation, timestamp, data
  },
  
  invalidJson: 'not-valid-json{',
  
  oversizedRecord: createCDCRecordMock('users', 'INSERT', {
    id: 'oversized',
    largeData: 'x'.repeat(1024 * 1024) // 1MB of data
  }),
  
  unsupportedTable: createCDCRecordMock('unknown_table', 'INSERT', {
    id: 'unknown'
  })
};
```

## Writing Unit Tests

### Testing Lambda Handlers

```typescript
// src/handlers/__tests__/kinesis-processor.test.ts
import { handler } from '../kinesis-processor';
import { createKinesisMock, createEventBridgeMock, createDynamoDBMock } from '@mocks/aws-mocks';
import { cdcFixtures, generateCDCBatch } from '@mocks/test-fixtures';

describe('Kinesis Processor Handler', () => {
  const kinesisMock = createKinesisMock();
  const eventBridgeMock = createEventBridgeMock();
  const dynamoMock = createDynamoDBMock();

  beforeEach(() => {
    kinesisMock.reset();
    eventBridgeMock.reset();
    dynamoMock.reset();
    
    // Default successful mocks
    eventBridgeMock.mockPutEvents();
    dynamoMock.mockPutItem(process.env.DYNAMODB_TABLE_STATE!);
  });

  describe('successful processing', () => {
    it('should process a single INSERT record successfully', async () => {
      // Arrange
      const event = kinesisMock.createKinesisEvent([cdcFixtures.users.insert]);
      
      // Act
      const result = await handler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
      
      const sentEvents = eventBridgeMock.getSentEvents();
      expect(sentEvents).toHaveLength(1);
      expect(sentEvents[0].Entries[0].DetailType).toBe('CDC.users.INSERT');
    });

    it('should process multiple records in batch', async () => {
      // Arrange
      const records = generateCDCBatch(10, 'orders', 'INSERT');
      const event = kinesisMock.createKinesisEvent(records);
      
      // Act
      const result = await handler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
      
      const sentEvents = eventBridgeMock.getSentEvents();
      expect(sentEvents[0].Entries).toHaveLength(10);
    });

    it('should handle UPDATE operations correctly', async () => {
      // Arrange
      const event = kinesisMock.createKinesisEvent([cdcFixtures.orders.statusUpdate]);
      
      // Act
      await handler(event, {} as any, () => {});
      
      // Assert
      const sentEvents = eventBridgeMock.getSentEvents();
      const eventDetail = JSON.parse(sentEvents[0].Entries[0].Detail);
      
      expect(eventDetail.operation).toBe('UPDATE');
      expect(eventDetail.data.before).toBeDefined();
      expect(eventDetail.data.after).toBeDefined();
    });

    it('should handle DELETE operations correctly', async () => {
      // Arrange
      const event = kinesisMock.createKinesisEvent([cdcFixtures.users.delete]);
      
      // Act
      await handler(event, {} as any, () => {});
      
      // Assert
      const sentEvents = eventBridgeMock.getSentEvents();
      const eventDetail = JSON.parse(sentEvents[0].Entries[0].Detail);
      
      expect(eventDetail.operation).toBe('DELETE');
      expect(eventDetail.data.after).toBeNull();
    });
  });

  describe('error handling', () => {
    it('should return failed item when EventBridge publishing fails', async () => {
      // Arrange
      eventBridgeMock.mockPutEventsFailure(new Error('EventBridge unavailable'));
      const event = kinesisMock.createKinesisEvent([cdcFixtures.users.insert]);
      
      // Act
      const result = await handler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(1);
      expect(result.batchItemFailures[0].itemIdentifier).toBeDefined();
    });

    it('should handle malformed records gracefully', async () => {
      // Arrange
      const malformedEvent = {
        Records: [{
          kinesis: {
            data: Buffer.from('invalid-json{').toString('base64')
          }
        }]
      };
      
      // Act
      const result = await handler(malformedEvent as any, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(1);
    });

    it('should handle partial EventBridge failures', async () => {
      // Arrange
      const records = generateCDCBatch(5, 'users', 'INSERT');
      const event = kinesisMock.createKinesisEvent(records);
      eventBridgeMock.mockPutEventsPartialFailure(2, 5);
      
      // Act
      const result = await handler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(2);
    });
  });

  describe('state management', () => {
    it('should save checkpoint after successful processing', async () => {
      // Arrange
      const event = kinesisMock.createKinesisEvent([cdcFixtures.users.insert]);
      
      // Act
      await handler(event, {} as any, () => {});
      
      // Assert
      const dynamoCalls = dynamoMock.mock.commandCalls(PutItemCommand);
      expect(dynamoCalls.length).toBeGreaterThan(0);
    });
  });
});
```

### Testing Services

```typescript
// src/services/__tests__/redaction-service.test.ts
import { RedactionService } from '../redaction-service';
import { sensitiveDataFixtures } from '@mocks/test-fixtures';

describe('RedactionService', () => {
  let redactionService: RedactionService;

  beforeEach(() => {
    redactionService = new RedactionService({
      enabled: true,
      fields: ['ssn', 'creditCard', 'password']
    });
  });

  describe('redact', () => {
    it('should redact SSN field', () => {
      // Arrange
      const data = { ssn: '123-45-6789', name: 'John Doe' };
      
      // Act
      const result = redactionService.redact(data);
      
      // Assert
      expect(result.ssn).toBe('[REDACTED]');
      expect(result.name).toBe('John Doe');
    });

    it('should redact credit card numbers', () => {
      // Arrange
      const data = { creditCard: '4111111111111111', amount: 99.99 };
      
      // Act
      const result = redactionService.redact(data);
      
      // Assert
      expect(result.creditCard).toBe('[REDACTED]');
      expect(result.amount).toBe(99.99);
    });

    it('should redact nested sensitive fields', () => {
      // Arrange
      const data = {
        user: {
          profile: {
            ssn: '987-65-4321'
          }
        }
      };
      
      // Act
      const result = redactionService.redact(data);
      
      // Assert
      expect(result.user.profile.ssn).toBe('[REDACTED]');
    });

    it('should redact sensitive fields in arrays', () => {
      // Arrange
      const data = {
        users: [
          { name: 'User 1', ssn: '111-11-1111' },
          { name: 'User 2', ssn: '222-22-2222' }
        ]
      };
      
      // Act
      const result = redactionService.redact(data);
      
      // Assert
      expect(result.users[0].ssn).toBe('[REDACTED]');
      expect(result.users[1].ssn).toBe('[REDACTED]');
      expect(result.users[0].name).toBe('User 1');
    });

    it('should not modify original data object', () => {
      // Arrange
      const originalData = { ssn: '123-45-6789', name: 'Test' };
      const originalSsn = originalData.ssn;
      
      // Act
      redactionService.redact(originalData);
      
      // Assert
      expect(originalData.ssn).toBe(originalSsn);
    });

    it('should handle null and undefined values', () => {
      // Arrange
      const data = { ssn: null, creditCard: undefined, name: 'Test' };
      
      // Act
      const result = redactionService.redact(data);
      
      // Assert
      expect(result.ssn).toBeNull();
      expect(result.creditCard).toBeUndefined();
    });
  });

  describe('when disabled', () => {
    beforeEach(() => {
      redactionService = new RedactionService({
        enabled: false,
        fields: ['ssn', 'creditCard']
      });
    });

    it('should not redact any fields when disabled', () => {
      // Arrange
      const data = { ssn: '123-45-6789', creditCard: '4111111111111111' };
      
      // Act
      const result = redactionService.redact(data);
      
      // Assert
      expect(result.ssn).toBe('123-45-6789');
      expect(result.creditCard).toBe('4111111111111111');
    });
  });
});
```

### Testing Data Transformers

```typescript
// src/services/__tests__/cdc-processor.test.ts
import { CDCProcessor } from '../cdc-processor';
import { cdcFixtures, errorFixtures } from '@mocks/test-fixtures';

describe('CDCProcessor', () => {
  let processor: CDCProcessor;

  beforeEach(() => {
    processor = new CDCProcessor({
      supportedTables: ['users', 'orders', 'inventory'],
      transformers: {
        users: (record) => ({
          ...record,
          entityType: 'USER'
        }),
        orders: (record) => ({
          ...record,
          entityType: 'ORDER'
        })
      }
    });
  });

  describe('processRecord', () => {
    it('should transform user records correctly', async () => {
      // Arrange
      const record = cdcFixtures.users.insert;
      
      // Act
      const result = await processor.processRecord(record);
      
      // Assert
      expect(result.entityType).toBe('USER');
      expect(result.tableName).toBe('users');
    });

    it('should validate required fields', async () => {
      // Arrange
      const invalidRecord = errorFixtures.malformedRecord;
      
      // Act & Assert
      await expect(processor.processRecord(invalidRecord as any))
        .rejects.toThrow('Missing required field: operation');
    });

    it('should reject unsupported tables', async () => {
      // Arrange
      const unsupportedRecord = errorFixtures.unsupportedTable;
      
      // Act & Assert
      await expect(processor.processRecord(unsupportedRecord))
        .rejects.toThrow('Unsupported table: unknown_table');
    });

    it('should handle records without transformer', async () => {
      // Arrange
      const inventoryRecord = cdcFixtures.inventory.update;
      
      // Act
      const result = await processor.processRecord(inventoryRecord);
      
      // Assert
      // Should pass through without transformation
      expect(result.tableName).toBe('inventory');
      expect(result.entityType).toBeUndefined();
    });
  });

  describe('processBatch', () => {
    it('should process all records in batch', async () => {
      // Arrange
      const batch = [
        cdcFixtures.users.insert,
        cdcFixtures.orders.insert,
        cdcFixtures.users.update
      ];
      
      // Act
      const results = await processor.processBatch(batch);
      
      // Assert
      expect(results.successful).toHaveLength(3);
      expect(results.failed).toHaveLength(0);
    });

    it('should continue processing after individual failures', async () => {
      // Arrange
      const batch = [
        cdcFixtures.users.insert,
        errorFixtures.malformedRecord as any,
        cdcFixtures.orders.insert
      ];
      
      // Act
      const results = await processor.processBatch(batch);
      
      // Assert
      expect(results.successful).toHaveLength(2);
      expect(results.failed).toHaveLength(1);
      expect(results.failed[0].error).toBeDefined();
    });
  });
});
```

## Writing Integration Tests

### Full Pipeline Integration Test

```typescript
// tests/integration/full-pipeline.test.ts
import { handler as kinesisHandler } from '../../src/handlers/kinesis-processor';
import { DynamoDBClient, GetItemCommand, ScanCommand } from '@aws-sdk/client-dynamodb';
import { unmarshall } from '@aws-sdk/util-dynamodb';
import { generateCDCBatch, cdcFixtures } from '../mocks/test-fixtures';
import { createKinesisMock } from '../mocks/aws-mocks';

// These tests require LocalStack or actual AWS resources
describe('CDC Pipeline Integration Tests', () => {
  const kinesisMock = createKinesisMock();
  let dynamoClient: DynamoDBClient;

  beforeAll(async () => {
    dynamoClient = new DynamoDBClient({
      region: process.env.AWS_REGION,
      endpoint: process.env.DYNAMODB_ENDPOINT
    });
    
    // Ensure test tables exist
    await setupTestTables();
  });

  afterAll(async () => {
    await cleanupTestTables();
  });

  beforeEach(async () => {
    // Clear test data
    await clearTestData();
  });

  describe('End-to-end processing', () => {
    it('should process CDC records from Kinesis to EventBridge', async () => {
      // Arrange
      const testRecords = [
        cdcFixtures.users.insert,
        cdcFixtures.orders.insert
      ];
      const event = kinesisMock.createKinesisEvent(testRecords);
      
      // Act
      const result = await kinesisHandler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
      
      // Verify checkpoint was saved
      const checkpoint = await getLatestCheckpoint();
      expect(checkpoint).toBeDefined();
      expect(checkpoint.processedCount).toBe(2);
    });

    it('should maintain processing state across invocations', async () => {
      // Arrange - First batch
      const firstBatch = generateCDCBatch(5, 'users', 'INSERT');
      const firstEvent = kinesisMock.createKinesisEvent(firstBatch);
      
      // Act - Process first batch
      await kinesisHandler(firstEvent, {} as any, () => {});
      
      // Arrange - Second batch
      const secondBatch = generateCDCBatch(3, 'users', 'INSERT');
      const secondEvent = kinesisMock.createKinesisEvent(secondBatch);
      
      // Act - Process second batch
      await kinesisHandler(secondEvent, {} as any, () => {});
      
      // Assert - Verify cumulative state
      const state = await getProcessingState();
      expect(state.totalProcessed).toBe(8);
    });

    it('should handle high-volume batches', async () => {
      // Arrange
      const largeBatch = generateCDCBatch(100, 'orders', 'INSERT');
      const event = kinesisMock.createKinesisEvent(largeBatch);
      
      // Act
      const startTime = Date.now();
      const result = await kinesisHandler(event, {} as any, () => {});
      const duration = Date.now() - startTime;
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
      expect(duration).toBeLessThan(30000); // Should complete within 30 seconds
    });
  });

  describe('Error recovery', () => {
    it('should recover from transient DynamoDB errors', async () => {
      // Arrange - Simulate DynamoDB throttling
      jest.spyOn(dynamoClient, 'send')
        .mockRejectedValueOnce(new Error('Throughput exceeded'))
        .mockResolvedValueOnce({} as any);
      
      const event = kinesisMock.createKinesisEvent([cdcFixtures.users.insert]);
      
      // Act
      const result = await kinesisHandler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
    });
  });

  // Helper functions
  async function setupTestTables() {
    // Create test tables in LocalStack/DynamoDB Local
    // Implementation depends on your test infrastructure
  }

  async function cleanupTestTables() {
    // Clean up test tables
  }

  async function clearTestData() {
    // Clear data from test tables
  }

  async function getLatestCheckpoint() {
    const result = await dynamoClient.send(new GetItemCommand({
      TableName: process.env.DYNAMODB_TABLE_CHECKPOINTS,
      Key: { pk: { S: 'LATEST' } }
    }));
    return result.Item ? unmarshall(result.Item) : null;
  }

  async function getProcessingState() {
    const result = await dynamoClient.send(new ScanCommand({
      TableName: process.env.DYNAMODB_TABLE_STATE
    }));
    return {
      totalProcessed: result.Items?.length || 0
    };
  }
});
```

### Table-Specific Integration Tests

```typescript
// tests/integration/table-processing.test.ts
describe('Table-Specific CDC Processing', () => {
  // Test processing for each of the 12+ CoreDB tables
  const supportedTables = [
    'users',
    'orders',
    'inventory',
    'products',
    'customers',
    'transactions',
    'shipments',
    'returns',
    'reviews',
    'categories',
    'promotions',
    'notifications'
  ];

  describe.each(supportedTables)('Processing %s table', (tableName) => {
    it(`should process INSERT events for ${tableName}`, async () => {
      // Arrange
      const record = createCDCRecordMock(tableName, 'INSERT', {
        id: `${tableName}-test-id`,
        createdAt: new Date().toISOString()
      });
      const event = kinesisMock.createKinesisEvent([record]);
      
      // Act
      const result = await kinesisHandler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
    });

    it(`should process UPDATE events for ${tableName}`, async () => {
      // Arrange
      const record = createCDCRecordMock(tableName, 'UPDATE', {
        id: `${tableName}-test-id`,
        updatedAt: new Date().toISOString()
      });
      const event = kinesisMock.createKinesisEvent([record]);
      
      // Act
      const result = await kinesisHandler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
    });

    it(`should process DELETE events for ${tableName}`, async () => {
      // Arrange
      const record = createCDCRecordMock(tableName, 'DELETE', {
        id: `${tableName}-test-id`
      });
      const event = kinesisMock.createKinesisEvent([record]);
      
      // Act
      const result = await kinesisHandler(event, {} as any, () => {});
      
      // Assert
      expect(result.batchItemFailures).toHaveLength(0);
    });
  });
});
```

## Running Tests

### NPM Scripts

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:unit": "jest --testPathIgnorePatterns=integration",
    "test:integration": "jest --config jest.integration.config.js",
    "test:ci": "jest --ci --coverage --reporters=default --reporters=jest-junit",
    "test:debug": "node --inspect-brk node_modules/.bin/jest --runInBand",
    "test:verbose": "jest --verbose --no-coverage",
    "test:changed": "jest --onlyChanged",
    "test:setup": "ts-node tests/setup/validate-env.ts"
  }
}
```

### Running Different Test Suites

```bash
# Run all tests
npm test

# Run tests in watch mode during development
npm run test:watch

# Run only unit tests (excludes integration)
npm run test:unit

# Run integration tests
npm run test:integration

# Run tests with coverage report
npm run test:coverage

# Run tests for CI/CD pipeline
npm run test:ci

# Run specific test file
npm test -- src/handlers/__tests__/kinesis-processor.test.ts

# Run tests matching a pattern
npm test -- --testNamePattern="should process INSERT"

# Run tests for a specific table/service
npm test -- --testPathPattern="redaction"

# Debug tests
npm run test:debug
```

### Running Tests with LocalStack

For integration tests that require AWS services:

```bash
# Start LocalStack
docker-compose -f docker-compose.test.yml up -d

# Wait for LocalStack to be ready
./scripts/wait-for-localstack.sh

# Run integration tests
npm run test:integration

# Stop LocalStack
docker-compose -f docker-compose.test.yml down
```

Docker Compose configuration for LocalStack:

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=dynamodb,kinesis,events
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - "./scripts/localstack-init:/docker-entrypoint-initaws.d"
```

## Coverage Requirements

### Minimum Coverage Thresholds

The CDC Pipeline service enforces the following coverage requirements:

| Metric     | Minimum | Target | Critical Paths |
|------------|---------|--------|----------------|
| Lines      | 80%     | 90%    | 95%            |
| Branches   | 80%     | 85%    | 90%            |
| Functions  | 80%     | 90%    | 95%            |
| Statements | 80%     | 90%    | 95%            |

### Critical Paths Requiring Higher Coverage

The following components require 95%+ coverage:

```javascript
// jest.config.js - Critical path coverage
coverageThreshold: {
  global: {
    branches: 80,
    functions: 80,
    lines: 80,
    statements: 80
  },
  // Critical paths with higher requirements
  './src/handlers/kinesis-processor.ts': {
    branches: 95,
    functions: 95,
    lines: 95,
    statements: 95
  },
  './src/services/redaction-service.ts': {
    branches: 95,
    functions: 95,
    lines: 95,
    statements: 95
  },
  './src/services/event-publisher.ts': {
    branches: 90,
    functions: 90,
    lines: 90,
    statements: 90
  }
}
```

### Viewing Coverage Reports

```bash
# Generate and view coverage report
npm run test:coverage

# Open HTML coverage report
open coverage/lcov-report/index.html

# View coverage summary in terminal
cat coverage/coverage-summary.json | jq '.total'
```

### Coverage Report Example

```
----------------------------|---------|----------|---------|---------|
File                        | % Stmts | % Branch | % Funcs | % Lines |
----------------------------|---------|----------|---------|---------|
All files                   |   87.42 |    82.15 |   89.23 |   87.01 |
 handlers                   |   92.31 |    88.46 |   94.12 |   92.00 |
  kinesis-processor.ts      |   96.55 |    92.31 |  100.00 |   96.30 |
  event-publisher.ts        |   88.00 |    84.62 |   88.24 |   87.50 |
 services                   |   85.71 |    79.17 |   86.67 |   85.29 |
  cdc-processor.ts          |   88.89 |    83.33 |   90.00 |   88.46 |
  redaction-service.ts      |   95.24 |    91.67 |   95.00 |   95.00 |
  state-manager.ts          |   73.00 |    62.50 |   75.00 |   72.41 |
 utils                      |   84.21 |    78.95 |   85.71 |   83.78 |
----------------------------|---------|----------|---------|---------|
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test CDC Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:unit -- --ci
      
      - name: Start LocalStack
        run: docker-compose -f docker-compose.test.yml up -d
      
      - name: Run integration tests
        run: npm run test:integration -- --ci
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true
          
      - name: Check coverage thresholds
        run: |
          npm run test:coverage -- --ci
          if [ $? -ne 0 ]; then
            echo "Coverage thresholds not met"
            exit 1
          fi
```

---

## Summary

This testing guide provides comprehensive coverage of testing practices for the CDC Pipeline service. Key takeaways:

1. **Test Structure**: Organize tests alongside source code with integration tests in a dedicated directory
2. **Mocking**: Use `aws-sdk-client-mock` for AWS services and custom fixtures for CDC records
3. **Coverage**: Maintain 80% minimum coverage with higher thresholds for critical paths
4. **Integration Tests**: Use LocalStack for realistic AWS service testing
5. **CI/CD**: Automate testing with GitHub Actions or similar platforms

For questions or improvements to this testing guide, please open an issue or submit a pull request.