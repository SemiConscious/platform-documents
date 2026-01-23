# CDC Pipeline Service

[![Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=aws-lambda)](https://aws.amazon.com/lambda/)
[![EventBridge](https://img.shields.io/badge/AWS-EventBridge-FF4F8B?logo=amazon-aws)](https://aws.amazon.com/eventbridge/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)](https://www.docker.com/)
[![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-4053D6?logo=amazon-dynamodb)](https://aws.amazon.com/dynamodb/)

A Change Data Capture (CDC) pipeline service that captures database changes from CoreDB tables and processes them through AWS Lambda, publishing events to EventBridge for downstream consumers like the Wallboards service.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Lambda Functions Index](#lambda-functions-index)
- [Getting Started](#getting-started)
- [Common Patterns](#common-patterns)
- [Lambda Helper Utilities](#lambda-helper-utilities)
- [Error Handling](#error-handling)
- [Data Models](#data-models)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## Overview

The CDC Pipeline Service provides real-time data synchronization by capturing changes from 12+ CoreDB tables and distributing them to downstream services. This event-driven architecture enables:

- **Real-time Data Propagation**: Changes are captured and processed within milliseconds
- **Decoupled Architecture**: Downstream services consume events without direct database access
- **Data Transformation**: Built-in redaction and transformation capabilities for sensitive data
- **Reliable State Management**: DynamoDB-backed state tracking for exactly-once processing
- **Scalable Processing**: Kinesis stream integration for high-throughput scenarios

### Key Features

| Feature | Description |
|---------|-------------|
| CDC Processing | Captures changes from 12+ CoreDB tables in real-time |
| Lambda Processing | Serverless event processing with automatic scaling |
| EventBridge Integration | Fan-out event distribution to multiple consumers |
| Data Redaction | PII and sensitive data handling capabilities |
| State Management | DynamoDB-based checkpointing and state tracking |
| Stream Processing | Kinesis integration for high-volume data flows |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CDC Pipeline Architecture                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  CoreDB  │────▶│   Kinesis   │────▶│  CDC Processor   │────▶│ EventBridge │
│  Tables  │     │   Stream    │     │     Lambda       │     │    Bus      │
└──────────┘     └─────────────┘     └──────────────────┘     └─────────────┘
                                              │                       │
                                              ▼                       ▼
                                     ┌──────────────┐         ┌─────────────┐
                                     │   DynamoDB   │         │  Wallboards │
                                     │ State Store  │         │  + Others   │
                                     └──────────────┘         └─────────────┘
```

### Data Flow

1. **Capture**: Database triggers capture INSERT, UPDATE, DELETE operations on CoreDB tables
2. **Stream**: Changes are published to Kinesis streams for reliable delivery
3. **Process**: Lambda functions consume stream records, applying transformations and redactions
4. **Distribute**: Processed events are published to EventBridge for downstream consumption
5. **Track**: Processing state is maintained in DynamoDB for reliability and idempotency

---

## Lambda Functions Index

The CDC Pipeline consists of multiple Lambda functions, each responsible for specific processing tasks:

| Lambda Function | Purpose | Trigger | Documentation |
|-----------------|---------|---------|---------------|
| `cdc-processor` | Main CDC event processor | Kinesis Stream | [CDC Processor Lambda](docs/lambdas/cdc-processor.md) |
| `health-check` | EventBridge connectivity health monitoring | CloudWatch Events | [EventBridge Health Check Lambda](docs/lambdas/health-check.md) |
| `state-manager` | DynamoDB state management and checkpointing | Internal | - |
| `data-redactor` | PII and sensitive data redaction | Internal | - |
| `dead-letter-processor` | Failed event reprocessing | SQS DLQ | - |

### Function Responsibilities

#### CDC Processor Lambda
The core processing engine that handles incoming change events:
- Deserializes Kinesis records
- Applies table-specific transformation logic
- Publishes formatted events to EventBridge
- Manages processing checkpoints

#### Health Check Lambda
Monitors the overall health of the CDC pipeline:
- Validates EventBridge connectivity
- Checks Kinesis stream status
- Reports metrics to CloudWatch

---

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- AWS CLI configured with appropriate credentials
- Node.js 18+ (for local development tooling)
- Access to CoreDB and AWS resources

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd cdc-pipeline
```

2. **Install dependencies**

```bash
npm install
```

3. **Configure environment**

Create a `.env` file based on the provided template:

```bash
cp .env.example .env
```

Configure the required environment variables:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Kinesis Configuration
KINESIS_STREAM_NAME=coredb-cdc-stream
KINESIS_BATCH_SIZE=100

# EventBridge Configuration
EVENT_BUS_NAME=cdc-events
EVENT_SOURCE=cdc-pipeline

# DynamoDB Configuration
STATE_TABLE_NAME=cdc-pipeline-state
CHECKPOINT_TABLE_NAME=cdc-pipeline-checkpoints

# Processing Configuration
ENABLE_DATA_REDACTION=true
MAX_RETRY_ATTEMPTS=3
```

4. **Build Docker containers**

```bash
docker build -t cdc-pipeline:latest .
```

5. **Run locally with SAM**

```bash
npm run local:start
```

### Quick Start - Local Testing

Test the CDC processor with a sample event:

```bash
# Invoke the CDC processor locally
npm run invoke:local -- --function cdc-processor --event events/sample-cdc-event.json
```

---

## Common Patterns

### Pattern 1: Table-Specific Event Handling

Each CoreDB table has specific transformation logic applied:

```javascript
// Example transformation configuration
const tableTransformers = {
  'users': {
    redactFields: ['ssn', 'email', 'phone'],
    eventType: 'user.changed',
    includeFields: ['id', 'name', 'status', 'updated_at']
  },
  'orders': {
    redactFields: ['payment_details'],
    eventType: 'order.changed',
    includeFields: ['id', 'user_id', 'status', 'total', 'created_at']
  },
  'agents': {
    redactFields: [],
    eventType: 'agent.changed',
    includeFields: ['*']
  }
};
```

### Pattern 2: Batch Processing with Checkpointing

```javascript
// Checkpoint management for reliable processing
async function processWithCheckpoint(records, context) {
  const checkpoint = await getLastCheckpoint(context.functionName);
  
  for (const record of records) {
    if (record.sequenceNumber <= checkpoint) {
      continue; // Skip already processed records
    }
    
    await processRecord(record);
    await updateCheckpoint(context.functionName, record.sequenceNumber);
  }
}
```

### Pattern 3: EventBridge Event Structure

All CDC events follow a consistent structure:

```json
{
  "version": "1.0",
  "source": "cdc-pipeline",
  "detail-type": "CDC.TableChange",
  "detail": {
    "table": "users",
    "operation": "UPDATE",
    "timestamp": "2024-01-15T10:30:00Z",
    "before": { "status": "active" },
    "after": { "status": "inactive" },
    "keys": { "id": "user-123" },
    "metadata": {
      "transactionId": "txn-456",
      "sequenceNumber": "12345678901234567890"
    }
  }
}
```

---

## Lambda Helper Utilities

The CDC Pipeline provides several utility modules for common operations:

### EventBridge Publisher

```javascript
const { publishEvent } = require('./lib/eventbridge-publisher');

// Publish a CDC event
await publishEvent({
  eventBusName: process.env.EVENT_BUS_NAME,
  source: 'cdc-pipeline',
  detailType: 'CDC.TableChange',
  detail: {
    table: 'users',
    operation: 'UPDATE',
    data: transformedRecord
  }
});
```

### Data Redactor

```javascript
const { redactSensitiveFields } = require('./lib/data-redactor');

// Redact PII from a record
const safeRecord = redactSensitiveFields(record, {
  fields: ['ssn', 'email', 'phone'],
  replacement: '[REDACTED]'
});
```

### State Manager

```javascript
const { StateManager } = require('./lib/state-manager');

const stateManager = new StateManager({
  tableName: process.env.STATE_TABLE_NAME
});

// Store processing state
await stateManager.saveState('processor-1', {
  lastProcessedSequence: '12345',
  processedCount: 1000,
  lastUpdated: new Date().toISOString()
});

// Retrieve state
const state = await stateManager.getState('processor-1');
```

### Kinesis Record Parser

```javascript
const { parseKinesisRecords } = require('./lib/kinesis-parser');

// Parse and decode Kinesis records
const cdcEvents = parseKinesisRecords(event.Records);
// Returns array of decoded CDC change events
```

---

## Error Handling

### Retry Strategy

The CDC Pipeline implements exponential backoff for transient failures:

```javascript
const retryConfig = {
  maxAttempts: 3,
  baseDelayMs: 100,
  maxDelayMs: 5000,
  retryableErrors: [
    'ProvisionedThroughputExceededException',
    'ThrottlingException',
    'ServiceUnavailable'
  ]
};
```

### Dead Letter Queue Processing

Failed events are sent to an SQS Dead Letter Queue for manual review and reprocessing:

```javascript
// DLQ event structure
{
  "originalEvent": { /* original CDC event */ },
  "error": {
    "message": "Processing failed after 3 attempts",
    "code": "TRANSFORMATION_ERROR",
    "stack": "..."
  },
  "attempts": 3,
  "lastAttempt": "2024-01-15T10:35:00Z"
}
```

### Error Categories

| Error Type | Handling Strategy | Retryable |
|------------|-------------------|-----------|
| `PARSE_ERROR` | Log and skip | No |
| `TRANSFORMATION_ERROR` | Retry with backoff | Yes |
| `EVENTBRIDGE_ERROR` | Retry with backoff | Yes |
| `STATE_ERROR` | Alert and retry | Yes |
| `VALIDATION_ERROR` | Log and skip | No |

### CloudWatch Alarms

Configure alarms for critical error conditions:

```yaml
# CloudWatch alarm for high error rate
CDCProcessorErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: cdc-processor-errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
```

---

## Data Models

The CDC Pipeline processes events from **75 data models** across CoreDB. Key model categories include:

- **User Models**: Users, profiles, preferences, sessions
- **Agent Models**: Agents, skills, availability, states
- **Communication Models**: Calls, chats, emails, interactions
- **Queue Models**: Queues, routing rules, priorities
- **Reporting Models**: Metrics, aggregations, summaries

Refer to the model documentation for complete schema definitions.

---

## Documentation

### Lambda Function Documentation

- [CDC Processor Lambda](docs/lambdas/cdc-processor.md) - Detailed documentation for the main CDC processing Lambda
- [EventBridge Health Check Lambda](docs/lambdas/health-check.md) - Health monitoring Lambda documentation

### Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
- [Amazon Kinesis Documentation](https://docs.aws.amazon.com/kinesis/)

---

## Troubleshooting

### Common Issues

#### 1. Events Not Appearing in EventBridge

**Symptoms**: CDC events are processed but not visible to downstream consumers.

**Solutions**:
```bash
# Check EventBridge rule configuration
aws events list-rules --event-bus-name cdc-events

# Verify Lambda has EventBridge permissions
aws lambda get-function-configuration --function-name cdc-processor
```

#### 2. High Lambda Latency

**Symptoms**: Processing time exceeds expected thresholds.

**Solutions**:
- Increase Lambda memory allocation
- Review batch size configuration
- Check DynamoDB provisioned capacity

#### 3. Checkpoint Desync

**Symptoms**: Duplicate events being processed.

**Solutions**:
```bash
# Reset checkpoint for a specific processor
npm run checkpoint:reset -- --processor cdc-processor-1

# View current checkpoint state
npm run checkpoint:status
```

### Useful Commands

```bash
# View Lambda logs
npm run logs:tail -- --function cdc-processor

# Check pipeline health
npm run health:check

# Manually trigger health check Lambda
npm run invoke -- --function health-check

# Process DLQ messages
npm run dlq:process
```

---

## Contributing

Please refer to the team's contribution guidelines for information on submitting changes to the CDC Pipeline service.

---

## Support

For issues or questions regarding the CDC Pipeline service, contact the platform team or open an issue in the repository.