# Development Guide

## Omnichannel-OmniService

This comprehensive development guide provides everything you need to start contributing to the omnichannel-omniservice, a TypeScript NodeJS monorepo that implements a sophisticated omnichannel messaging pipeline. This service handles inbound and outbound message routing across multiple carriers including WhatsApp, Bandwidth, Twilio, LiveChat, Messagebird, and Inteliquent, all powered by AWS Lambda-based processing.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Monorepo Structure](#monorepo-structure)
4. [Running Tests](#running-tests)
5. [Mock Data](#mock-data)
6. [Debugging](#debugging)
7. [Code Style Guidelines](#code-style-guidelines)

---

## Prerequisites

Before you begin development on the omnichannel-omniservice, ensure your development environment meets the following requirements.

### Required Software

| Software | Minimum Version | Recommended Version | Purpose |
|----------|----------------|---------------------|---------|
| Node.js | 18.x | 20.x LTS | Runtime environment |
| npm | 9.x | 10.x | Package management |
| AWS CLI | 2.x | Latest | AWS service interaction |
| Docker | 20.x | Latest | Local service emulation |
| Git | 2.30+ | Latest | Version control |

### Node.js Installation

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
nvm alias default 20

# Verify installation
node --version  # Should output v20.x.x
npm --version   # Should output 10.x.x
```

### AWS Configuration

```bash
# Configure AWS credentials
aws configure

# Enter your credentials when prompted:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Required AWS Permissions

Your AWS user/role needs the following permissions for local development:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*",
        "lambda:*",
        "sqs:*",
        "sns:*",
        "s3:*",
        "logs:*",
        "ssm:GetParameter*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Development Tools

```bash
# Install global development tools
npm install -g typescript ts-node serverless @aws-amplify/cli

# Install AWS SAM CLI for local Lambda testing
brew install aws-sam-cli  # macOS
# or
pip install aws-sam-cli   # Linux/Windows
```

---

## Local Development Setup

### Repository Setup

```bash
# Clone the repository
git clone https://github.com/your-org/omnichannel-omniservice.git
cd omnichannel-omniservice

# Install dependencies for all packages in the monorepo
npm install

# Bootstrap the monorepo (links local packages)
npm run bootstrap

# Build all packages
npm run build
```

### Environment Configuration

Create environment files for local development:

```bash
# Copy example environment files
cp .env.example .env.local

# Edit the environment file with your configuration
nano .env.local
```

Example `.env.local` configuration:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=development

# DynamoDB Local
DYNAMODB_ENDPOINT=http://localhost:8000
DYNAMODB_TABLE_PREFIX=dev_

# Carrier API Keys (use test/sandbox credentials)
TWILIO_ACCOUNT_SID=ACtest_xxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=test_auth_token
BANDWIDTH_API_TOKEN=test_bandwidth_token
WHATSAPP_API_KEY=test_whatsapp_key
MESSAGEBIRD_API_KEY=test_messagebird_key
LIVECHAT_API_KEY=test_livechat_key
INTELIQUENT_API_KEY=test_inteliquent_key

# Logging
LOG_LEVEL=debug
NODE_ENV=development

# Local Services
LOCAL_SQS_ENDPOINT=http://localhost:9324
LOCAL_SNS_ENDPOINT=http://localhost:9911
```

### Local Services Setup

Start local AWS services using Docker:

```bash
# Start DynamoDB Local
docker run -d -p 8000:8000 amazon/dynamodb-local

# Start LocalStack for SQS/SNS/S3
docker run -d \
  -p 4566:4566 \
  -p 4571:4571 \
  -e SERVICES=sqs,sns,s3,lambda \
  -e DEBUG=1 \
  localstack/localstack

# Or use docker-compose (recommended)
docker-compose -f docker-compose.local.yml up -d
```

Example `docker-compose.local.yml`:

```yaml
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
      - SERVICES=sqs,sns,s3,lambda
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - "./localstack-data:/tmp/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Initialize Local Database

```bash
# Create local DynamoDB tables
npm run db:create-tables

# Seed development data
npm run db:seed

# Verify tables were created
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

### Start Development Server

```bash
# Start all services in development mode
npm run dev

# Or start specific packages
npm run dev --workspace=@omnichannel/inbound-handler
npm run dev --workspace=@omnichannel/outbound-router
```

---

## Monorepo Structure

The omnichannel-omniservice uses a modular monorepo architecture organized as follows:

```
omnichannel-omniservice/
├── packages/
│   ├── core/                          # Shared core utilities
│   │   ├── src/
│   │   │   ├── models/               # Data models (100+ models)
│   │   │   ├── interfaces/           # TypeScript interfaces
│   │   │   ├── utils/                # Utility functions
│   │   │   ├── constants/            # Shared constants
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── carriers/                      # Carrier integrations
│   │   ├── twilio/
│   │   │   ├── src/
│   │   │   │   ├── handlers/         # Lambda handlers
│   │   │   │   ├── services/         # Business logic
│   │   │   │   └── webhooks/         # Webhook processors
│   │   │   └── package.json
│   │   ├── bandwidth/
│   │   ├── whatsapp/
│   │   ├── messagebird/
│   │   ├── livechat/
│   │   └── inteliquent/
│   │
│   ├── inbound-pipeline/             # Inbound message processing
│   │   ├── src/
│   │   │   ├── handlers/
│   │   │   │   ├── webhook-receiver.ts
│   │   │   │   ├── message-normalizer.ts
│   │   │   │   └── routing-handler.ts
│   │   │   ├── processors/
│   │   │   └── validators/
│   │   └── package.json
│   │
│   ├── outbound-pipeline/            # Outbound message processing
│   │   ├── src/
│   │   │   ├── handlers/
│   │   │   │   ├── message-sender.ts
│   │   │   │   ├── carrier-router.ts
│   │   │   │   └── delivery-tracker.ts
│   │   │   └── services/
│   │   └── package.json
│   │
│   ├── workflow-engine/              # Workflow processing
│   │   ├── src/
│   │   │   ├── workflows/
│   │   │   ├── steps/
│   │   │   └── orchestrator/
│   │   └── package.json
│   │
│   ├── media-converter/              # Media conversion handling
│   │   ├── src/
│   │   │   ├── converters/
│   │   │   ├── processors/
│   │   │   └── storage/
│   │   └── package.json
│   │
│   ├── push-notifications/           # Push notification service
│   │   ├── src/
│   │   │   ├── handlers/
│   │   │   └── providers/
│   │   └── package.json
│   │
│   └── dynamodb-streams/             # DynamoDB stream processors
│       ├── src/
│       │   ├── handlers/
│       │   └── processors/
│       └── package.json
│
├── infrastructure/                    # Infrastructure as Code
│   ├── serverless/
│   │   ├── serverless.yml
│   │   └── resources/
│   ├── terraform/
│   └── cloudformation/
│
├── scripts/                          # Development scripts
│   ├── db-create-tables.ts
│   ├── db-seed.ts
│   └── local-invoke.ts
│
├── tests/                            # Integration/E2E tests
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
├── docs/                             # Documentation
├── package.json                      # Root package.json
├── tsconfig.base.json               # Base TypeScript config
├── lerna.json                       # Lerna configuration
└── nx.json                          # Nx configuration (optional)
```

### Package Dependencies

```typescript
// packages/core/package.json
{
  "name": "@omnichannel/core",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "dependencies": {
    "aws-sdk": "^2.1400.0",
    "zod": "^3.22.0",
    "dayjs": "^1.11.0"
  }
}

// packages/carriers/twilio/package.json
{
  "name": "@omnichannel/carrier-twilio",
  "version": "1.0.0",
  "dependencies": {
    "@omnichannel/core": "^1.0.0",
    "twilio": "^4.14.0"
  }
}
```

### Cross-Package Imports

```typescript
// packages/inbound-pipeline/src/handlers/webhook-receiver.ts
import { Message, CarrierType, normalizePhone } from '@omnichannel/core';
import { TwilioMessageParser } from '@omnichannel/carrier-twilio';
import { BandwidthMessageParser } from '@omnichannel/carrier-bandwidth';

export const handler = async (event: APIGatewayEvent): Promise<APIGatewayProxyResult> => {
  const carrierType = determineCarrier(event);
  
  let normalizedMessage: Message;
  
  switch (carrierType) {
    case CarrierType.TWILIO:
      normalizedMessage = TwilioMessageParser.parse(event.body);
      break;
    case CarrierType.BANDWIDTH:
      normalizedMessage = BandwidthMessageParser.parse(event.body);
      break;
    // ... other carriers
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify({ received: true })
  };
};
```

---

## Running Tests

### Test Structure

```
tests/
├── unit/                    # Unit tests (per package)
│   ├── core/
│   ├── carriers/
│   └── pipelines/
├── integration/            # Integration tests
│   ├── carrier-integrations/
│   ├── pipeline-flows/
│   └── database/
├── e2e/                    # End-to-end tests
│   ├── inbound-flow.test.ts
│   └── outbound-flow.test.ts
└── fixtures/               # Test fixtures and mocks
    ├── messages/
    ├── carriers/
    └── database/
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests for specific package
npm test --workspace=@omnichannel/core
npm test --workspace=@omnichannel/carrier-twilio

# Run tests with coverage
npm run test:coverage

# Run integration tests
npm run test:integration

# Run e2e tests (requires local services)
npm run test:e2e

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- --testPathPattern="webhook-receiver"
```

### Jest Configuration

```typescript
// jest.config.ts
import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/packages', '<rootDir>/tests'],
  testMatch: ['**/*.test.ts', '**/*.spec.ts'],
  collectCoverageFrom: [
    'packages/**/src/**/*.ts',
    '!packages/**/src/**/*.d.ts',
    '!packages/**/src/**/index.ts'
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
    '@omnichannel/(.*)': '<rootDir>/packages/$1/src'
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  globalSetup: '<rootDir>/tests/global-setup.ts',
  globalTeardown: '<rootDir>/tests/global-teardown.ts'
};

export default config;
```

### Writing Tests

```typescript
// packages/carriers/twilio/src/__tests__/twilio-parser.test.ts
import { TwilioMessageParser } from '../services/twilio-parser';
import { twilioInboundSMS, twilioInboundMMS } from '@test-fixtures/carriers/twilio';

describe('TwilioMessageParser', () => {
  describe('parse', () => {
    it('should correctly parse inbound SMS message', () => {
      const result = TwilioMessageParser.parse(twilioInboundSMS);
      
      expect(result).toMatchObject({
        id: expect.any(String),
        carrier: 'twilio',
        type: 'sms',
        from: '+15551234567',
        to: '+15559876543',
        body: 'Hello, World!',
        timestamp: expect.any(Date)
      });
    });

    it('should correctly parse inbound MMS with media', () => {
      const result = TwilioMessageParser.parse(twilioInboundMMS);
      
      expect(result.media).toHaveLength(1);
      expect(result.media[0]).toMatchObject({
        url: expect.any(String),
        contentType: 'image/jpeg'
      });
    });

    it('should throw error for invalid payload', () => {
      expect(() => TwilioMessageParser.parse({})).toThrow('Invalid Twilio payload');
    });
  });
});
```

---

## Mock Data

### Mock Fixtures Location

```
tests/fixtures/
├── messages/
│   ├── inbound/
│   │   ├── sms.json
│   │   ├── mms.json
│   │   └── whatsapp.json
│   └── outbound/
│       ├── single.json
│       └── broadcast.json
├── carriers/
│   ├── twilio/
│   │   ├── webhook-sms.json
│   │   ├── webhook-mms.json
│   │   └── status-callback.json
│   ├── bandwidth/
│   ├── whatsapp/
│   └── messagebird/
└── database/
    ├── conversations.json
    ├── messages.json
    └── contacts.json
```

### Using Mock Data

```typescript
// tests/fixtures/carriers/twilio/index.ts
export const twilioInboundSMS = {
  MessageSid: 'SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  AccountSid: 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  From: '+15551234567',
  To: '+15559876543',
  Body: 'Hello, World!',
  NumMedia: '0',
  ApiVersion: '2010-04-01'
};

export const twilioInboundMMS = {
  ...twilioInboundSMS,
  NumMedia: '1',
  MediaUrl0: 'https://api.twilio.com/xxx/Media/MExxxx',
  MediaContentType0: 'image/jpeg'
};

export const twilioStatusCallback = {
  MessageSid: 'SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  MessageStatus: 'delivered',
  To: '+15559876543',
  From: '+15551234567'
};
```

### Creating Mock Services

```typescript
// tests/mocks/carrier-services.ts
import { jest } from '@jest/globals';

export const mockTwilioClient = {
  messages: {
    create: jest.fn().mockResolvedValue({
      sid: 'SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
      status: 'queued',
      dateCreated: new Date()
    }),
    list: jest.fn().mockResolvedValue([])
  }
};

export const mockBandwidthClient = {
  Message: {
    send: jest.fn().mockResolvedValue({
      id: 'msg-xxxxx',
      state: 'accepted'
    })
  }
};

// Use in tests
jest.mock('twilio', () => {
  return jest.fn().mockImplementation(() => mockTwilioClient);
});
```

### Database Seed Data

```typescript
// scripts/db-seed.ts
import { DynamoDB } from 'aws-sdk';
import conversations from '../tests/fixtures/database/conversations.json';
import messages from '../tests/fixtures/database/messages.json';

const dynamodb = new DynamoDB.DocumentClient({
  endpoint: process.env.DYNAMODB_ENDPOINT || 'http://localhost:8000'
});

async function seedDatabase() {
  // Seed conversations
  for (const conversation of conversations) {
    await dynamodb.put({
      TableName: 'dev_conversations',
      Item: conversation
    }).promise();
  }
  
  // Seed messages
  for (const message of messages) {
    await dynamodb.put({
      TableName: 'dev_messages',
      Item: message
    }).promise();
  }
  
  console.log('Database seeded successfully');
}

seedDatabase().catch(console.error);
```

---

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Lambda Function",
      "type": "node",
      "request": "launch",
      "runtimeArgs": [
        "-r",
        "ts-node/register"
      ],
      "args": [
        "${workspaceFolder}/scripts/local-invoke.ts",
        "--function",
        "${input:functionName}",
        "--event",
        "${workspaceFolder}/tests/fixtures/events/${input:eventFile}"
      ],
      "env": {
        "NODE_ENV": "development",
        "AWS_REGION": "us-east-1"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Debug Current Test File",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": [
        "${relativeFile}",
        "--runInBand",
        "--no-cache"
      ],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    },
    {
      "name": "Debug All Tests",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": ["--runInBand", "--no-cache"],
      "console": "integratedTerminal"
    }
  ],
  "inputs": [
    {
      "id": "functionName",
      "type": "pickString",
      "description": "Select Lambda function",
      "options": [
        "inbound-webhook-receiver",
        "outbound-message-sender",
        "carrier-router",
        "media-converter"
      ]
    },
    {
      "id": "eventFile",
      "type": "promptString",
      "description": "Event file name (e.g., twilio-sms.json)"
    }
  ]
}
```

### Local Lambda Invocation

```typescript
// scripts/local-invoke.ts
import { handler as inboundHandler } from '../packages/inbound-pipeline/src/handlers/webhook-receiver';
import { handler as outboundHandler } from '../packages/outbound-pipeline/src/handlers/message-sender';
import { readFileSync } from 'fs';

const functionMap: Record<string, Function> = {
  'inbound-webhook-receiver': inboundHandler,
  'outbound-message-sender': outboundHandler
};

async function invoke(functionName: string, eventPath: string) {
  const event = JSON.parse(readFileSync(eventPath, 'utf-8'));
  const handler = functionMap[functionName];
  
  if (!handler) {
    throw new Error(`Unknown function: ${functionName}`);
  }
  
  console.log(`Invoking ${functionName} with event:`, JSON.stringify(event, null, 2));
  
  const result = await handler(event, {} as any);
  
  console.log('Result:', JSON.stringify(result, null, 2));
  return result;
}

// Parse CLI arguments and invoke
const args = process.argv.slice(2);
const functionIndex = args.indexOf('--function');
const eventIndex = args.indexOf('--event');

if (functionIndex !== -1 && eventIndex !== -1) {
  invoke(args[functionIndex + 1], args[eventIndex + 1]);
}
```

### Logging Best Practices

```typescript
// packages/core/src/utils/logger.ts
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
    bindings: (bindings) => ({
      service: 'omnichannel-omniservice',
      ...bindings
    })
  },
  redact: ['password', 'apiKey', 'authToken', 'Authorization']
});

export const createLogger = (context: string) => {
  return logger.child({ context });
};

// Usage in handlers
import { createLogger } from '@omnichannel/core';

const log = createLogger('inbound-webhook-receiver');

export const handler = async (event: APIGatewayEvent) => {
  log.info({ eventId: event.requestContext.requestId }, 'Processing webhook');
  
  try {
    // Processing logic
    log.debug({ carrier: 'twilio' }, 'Parsed carrier');
  } catch (error) {
    log.error({ error, eventId: event.requestContext.requestId }, 'Processing failed');
    throw error;
  }
};
```

### CloudWatch Logs Debugging

```bash
# View logs for specific function
aws logs tail /aws/lambda/omnichannel-inbound-webhook --follow

# Filter logs by request ID
aws logs filter-log-events \
  --log-group-name /aws/lambda/omnichannel-inbound-webhook \
  --filter-pattern "request-id-xxxxx"

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/omnichannel-inbound-webhook \
  --filter-pattern "ERROR"
```

---

## Code Style Guidelines

### TypeScript Configuration

```json
// tsconfig.base.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "resolveJsonModule": true,
    "paths": {
      "@omnichannel/*": ["packages/*/src"]
    }
  }
}
```

### ESLint Configuration

```javascript
// .eslintrc.js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/typescript',
    'prettier'
  ],
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'import/order': [
      'error',
      {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
        'newlines-between': 'always',
        alphabetize: { order: 'asc' }
      }
    ],
    'no-console': ['warn', { allow: ['warn', 'error'] }]
  }
};
```

### Prettier Configuration

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always"
}
```

### Code Style Examples

```typescript
// ✅ Good: Well-structured interface with documentation
/**
 * Represents a normalized message across all carriers
 */
export interface NormalizedMessage {
  /** Unique message identifier */
  id: string;
  /** Source carrier type */
  carrier: CarrierType;
  /** Message sender phone number in E.164 format */
  from: string;
  /** Message recipient phone number in E.164 format */
  to: string;
  /** Message body content */
  body: string;
  /** Optional media attachments */
  media?: MediaAttachment[];
  /** Message timestamp */
  timestamp: Date;
  /** Carrier-specific metadata */
  metadata?: Record<string, unknown>;
}

// ✅ Good: Clear error handling with typed errors
export class CarrierError extends Error {
  constructor(
    message: string,
    public readonly carrier: CarrierType,
    public readonly code: string,
    public readonly statusCode: number = 500
  ) {
    super(message);
    this.name = 'CarrierError';
  }
}

// ✅ Good: Functional approach with clear types
export const normalizePhoneNumber = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '');
  
  if (cleaned.length === 10) {
    return `+1${cleaned}`;
  }
  
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+${cleaned}`;
  }
  
  if (phone.startsWith('+')) {
    return phone;
  }
  
  throw new Error(`Invalid phone number format: ${phone}`);
};

// ✅ Good: Lambda handler with proper typing and error handling
export const handler: APIGatewayProxyHandler = async (event, context) => {
  const log = createLogger('webhook-receiver');
  const requestId = context.awsRequestId;
  
  log.info({ requestId }, 'Processing incoming webhook');
  
  try {
    const carrier = identifyCarrier(event);
    const message = await parseMessage(carrier, event.body);
    
    await routeMessage(message);
    
    log.info({ requestId, messageId: message.id }, 'Message processed successfully');
    
    return {
      statusCode: 200,
      body: JSON.stringify({ success: true, messageId: message.id })
    };
  } catch (error) {
    log.error({ requestId, error }, 'Failed to process webhook');
    
    if (error instanceof CarrierError) {
      return {
        statusCode: error.statusCode,
        body: JSON.stringify({ error: error.message, code: error.code })
      };
    }
    
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Examples:
```
feat(twilio): add MMS media attachment support
fix(inbound): correct phone number normalization for international numbers
docs(readme): update local development setup instructions
test(bandwidth): add integration tests for status callbacks
refactor(core): extract message validation into separate module
```

### Pre-commit Hooks

```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged",
      "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
  },
  "lint-staged": {
    "*.ts": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

---

## Getting Help

- **Internal Documentation**: Check the `/docs` directory for additional guides
- **API Documentation**: Available at `/docs/api` after running `npm run docs:generate`
- **Slack Channel**: `#omnichannel-dev`
- **Issue Tracker**: GitHub Issues for bug reports and feature requests

For questions about carrier-specific implementations, refer to the carrier documentation in `packages/carriers/[carrier]/README.md`.