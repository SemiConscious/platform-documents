# CDC Processor Lambda

## Purpose

The CDC Processor Lambda (`cdcProcessor`) is the core processing engine of the cdc-pipeline service, responsible for handling all Change Data Capture (CDC) events originating from CoreDB tables. This Lambda function serves as the central hub that receives database change events, processes and transforms them according to business rules, and publishes standardized events to Amazon EventBridge for consumption by downstream services.

### Key Responsibilities

- **Event Ingestion**: Receives CDC events from Kinesis streams containing database change records from 12+ CoreDB tables
- **Data Transformation**: Normalizes and transforms raw database changes into standardized event formats
- **Data Redaction**: Applies security policies to redact sensitive information before event distribution
- **State Management**: Maintains processing state in DynamoDB for exactly-once semantics and checkpoint tracking
- **Event Distribution**: Publishes processed events to EventBridge for downstream consumers (e.g., Wallboards service)
- **Error Handling**: Implements comprehensive error handling with dead-letter queue support

### Architecture Context

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   CoreDB    │────▶│   Kinesis   │────▶│  CDC Processor   │────▶│ EventBridge │
│   Tables    │     │   Stream    │     │     Lambda       │     │             │
└─────────────┘     └─────────────┘     └──────────────────┘     └─────────────┘
                                               │                        │
                                               ▼                        ▼
                                        ┌─────────────┐         ┌─────────────┐
                                        │  DynamoDB   │         │  Wallboards │
                                        │   State     │         │   Service   │
                                        └─────────────┘         └─────────────┘
```

---

## Trigger Configuration

The CDC Processor Lambda is configured to be triggered by Amazon Kinesis Data Streams, which receive CDC events from the CoreDB replication pipeline.

### Kinesis Trigger Settings

```yaml
# serverless.yml configuration
functions:
  cdcProcessor:
    handler: src/handlers/cdcProcessor.handler
    timeout: 300
    memorySize: 1024
    reservedConcurrency: 100
    events:
      - stream:
          type: kinesis
          arn: !GetAtt CDCKinesisStream.Arn
          batchSize: 100
          batchWindow: 5
          startingPosition: TRIM_HORIZON
          maximumRetryAttempts: 3
          bisectBatchOnFunctionError: true
          parallelizationFactor: 10
          functionResponseTypes:
            - ReportBatchItemFailures
```

### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `batchSize` | 100 | Maximum number of records per invocation |
| `batchWindow` | 5 seconds | Maximum time to wait for batch to fill |
| `startingPosition` | TRIM_HORIZON | Start reading from oldest available record |
| `maximumRetryAttempts` | 3 | Retry failed batches up to 3 times |
| `bisectBatchOnFunctionError` | true | Split batch on error to isolate failures |
| `parallelizationFactor` | 10 | Number of concurrent Lambda invocations per shard |

### Environment Variables

```bash
# Required environment variables
CDC_EVENT_BUS_NAME=cdc-pipeline-events
CDC_STATE_TABLE=cdc-processor-state
CDC_DLQ_URL=https://sqs.region.amazonaws.com/account/cdc-dlq
LOG_LEVEL=INFO
REDACTION_ENABLED=true
AWS_REGION=us-east-1
```

---

## Input Event Structure

The CDC Processor Lambda receives events from Kinesis in a standardized format that wraps the raw CDC payload from CoreDB's replication mechanism.

### Kinesis Event Envelope

```typescript
// TypeScript interface for the Kinesis event structure
interface KinesisEvent {
  Records: KinesisRecord[];
}

interface KinesisRecord {
  kinesis: {
    kinesisSchemaVersion: string;
    partitionKey: string;
    sequenceNumber: string;
    data: string; // Base64 encoded CDC payload
    approximateArrivalTimestamp: number;
  };
  eventSource: string;
  eventVersion: string;
  eventID: string;
  eventName: string;
  invokeIdentityArn: string;
  awsRegion: string;
  eventSourceARN: string;
}
```

### CDC Payload Structure

After decoding the Base64 data, the CDC payload follows this structure:

```typescript
interface CDCPayload {
  // Metadata
  metadata: {
    timestamp: string;          // ISO 8601 timestamp of the change
    transactionId: string;      // Database transaction ID
    sequenceNumber: number;     // Sequence within transaction
    source: string;             // Source database identifier
  };
  
  // Change details
  table: string;                // Source table name (e.g., "agents", "queues")
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  
  // Data
  before: Record<string, any> | null;  // Previous state (null for INSERT)
  after: Record<string, any> | null;   // New state (null for DELETE)
  
  // Changed columns (for UPDATE operations)
  changedColumns?: string[];
}
```

### Example Raw CDC Event

```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:45.123Z",
    "transactionId": "txn-abc123",
    "sequenceNumber": 1,
    "source": "coredb-primary"
  },
  "table": "agents",
  "operation": "UPDATE",
  "before": {
    "agent_id": "agent-001",
    "status": "available",
    "skills": ["support", "sales"],
    "last_activity": "2024-01-15T10:25:00.000Z"
  },
  "after": {
    "agent_id": "agent-001",
    "status": "busy",
    "skills": ["support", "sales"],
    "last_activity": "2024-01-15T10:30:45.000Z"
  },
  "changedColumns": ["status", "last_activity"]
}
```

---

## Processing Logic by Table

The CDC Processor implements table-specific processing logic for each of the 12+ supported CoreDB tables. Each table has its own transformation rules, redaction policies, and EventBridge event types.

### Supported Tables Overview

| Table | Event Type | Priority | Redaction Required |
|-------|-----------|----------|-------------------|
| `agents` | AgentStatusChanged | High | Yes |
| `queues` | QueueMetricsUpdated | High | No |
| `calls` | CallStateChanged | Critical | Yes |
| `contacts` | ContactUpdated | Medium | Yes |
| `skills` | SkillDefinitionChanged | Low | No |
| `routing_profiles` | RoutingProfileUpdated | Medium | No |
| `users` | UserProfileUpdated | Low | Yes |
| `teams` | TeamMembershipChanged | Low | No |
| `schedules` | ScheduleUpdated | Medium | No |
| `metrics_realtime` | RealtimeMetricsUpdated | Critical | No |
| `metrics_historical` | HistoricalMetricsUpdated | Low | No |
| `audit_logs` | AuditEventCreated | Medium | Yes |

### Table-Specific Processors

#### Agents Table Processor

```typescript
// src/processors/agentsProcessor.ts

import { CDCPayload, ProcessedEvent } from '../types';
import { redactSensitiveFields } from '../utils/redaction';

const SENSITIVE_FIELDS = ['phone_number', 'email', 'ssn_last_four'];

export async function processAgentChange(payload: CDCPayload): Promise<ProcessedEvent> {
  const { operation, before, after, metadata } = payload;
  
  // Apply redaction to sensitive fields
  const redactedBefore = before ? redactSensitiveFields(before, SENSITIVE_FIELDS) : null;
  const redactedAfter = after ? redactSensitiveFields(after, SENSITIVE_FIELDS) : null;
  
  // Determine specific event type based on what changed
  let eventType = 'AgentUpdated';
  
  if (operation === 'INSERT') {
    eventType = 'AgentCreated';
  } else if (operation === 'DELETE') {
    eventType = 'AgentDeleted';
  } else if (payload.changedColumns?.includes('status')) {
    eventType = 'AgentStatusChanged';
  } else if (payload.changedColumns?.includes('skills')) {
    eventType = 'AgentSkillsUpdated';
  }
  
  return {
    eventType,
    eventVersion: '1.0',
    timestamp: metadata.timestamp,
    source: 'cdc-pipeline',
    correlationId: metadata.transactionId,
    payload: {
      operation,
      entityId: (after?.agent_id || before?.agent_id) as string,
      entityType: 'agent',
      before: redactedBefore,
      after: redactedAfter,
      changedFields: payload.changedColumns || [],
    },
  };
}
```

#### Calls Table Processor

```typescript
// src/processors/callsProcessor.ts

import { CDCPayload, ProcessedEvent } from '../types';
import { redactSensitiveFields } from '../utils/redaction';

const SENSITIVE_FIELDS = ['customer_phone', 'customer_email', 'recording_url', 'transcript'];

export async function processCallChange(payload: CDCPayload): Promise<ProcessedEvent> {
  const { operation, before, after, metadata } = payload;
  
  // Determine call state transition
  const previousState = before?.call_state;
  const currentState = after?.call_state;
  
  // Apply aggressive redaction for PII
  const redactedAfter = after ? redactSensitiveFields(after, SENSITIVE_FIELDS) : null;
  
  // Enrich with computed fields
  const enrichedPayload = {
    operation,
    entityId: (after?.call_id || before?.call_id) as string,
    entityType: 'call',
    callState: currentState,
    previousState,
    stateTransition: previousState && currentState ? `${previousState}->${currentState}` : null,
    duration: calculateDuration(before, after),
    queueId: after?.queue_id || before?.queue_id,
    agentId: after?.agent_id || before?.agent_id,
    before: null, // Never include 'before' state for calls (contains PII)
    after: redactedAfter,
  };
  
  return {
    eventType: determineCallEventType(operation, previousState, currentState),
    eventVersion: '1.0',
    timestamp: metadata.timestamp,
    source: 'cdc-pipeline',
    correlationId: metadata.transactionId,
    payload: enrichedPayload,
  };
}

function determineCallEventType(
  operation: string,
  previousState?: string,
  currentState?: string
): string {
  if (operation === 'INSERT') return 'CallInitiated';
  if (operation === 'DELETE') return 'CallRecordDeleted';
  
  // State-based event types
  const stateEventMap: Record<string, string> = {
    'queued': 'CallQueued',
    'ringing': 'CallRinging',
    'connected': 'CallConnected',
    'on_hold': 'CallOnHold',
    'transferred': 'CallTransferred',
    'ended': 'CallEnded',
    'missed': 'CallMissed',
    'abandoned': 'CallAbandoned',
  };
  
  return stateEventMap[currentState || ''] || 'CallStateChanged';
}
```

#### Queues Table Processor

```typescript
// src/processors/queuesProcessor.ts

import { CDCPayload, ProcessedEvent } from '../types';
import { getQueueMetrics } from '../services/metricsService';

export async function processQueueChange(payload: CDCPayload): Promise<ProcessedEvent> {
  const { operation, before, after, metadata } = payload;
  
  const queueId = (after?.queue_id || before?.queue_id) as string;
  
  // Enrich with real-time metrics for queue updates
  let realtimeMetrics = null;
  if (operation !== 'DELETE') {
    try {
      realtimeMetrics = await getQueueMetrics(queueId);
    } catch (error) {
      console.warn(`Failed to fetch realtime metrics for queue ${queueId}:`, error);
    }
  }
  
  return {
    eventType: operation === 'INSERT' ? 'QueueCreated' : 
               operation === 'DELETE' ? 'QueueDeleted' : 'QueueMetricsUpdated',
    eventVersion: '1.0',
    timestamp: metadata.timestamp,
    source: 'cdc-pipeline',
    correlationId: metadata.transactionId,
    payload: {
      operation,
      entityId: queueId,
      entityType: 'queue',
      before,
      after,
      changedFields: payload.changedColumns || [],
      realtimeMetrics,
    },
  };
}
```

### Processing Pipeline

```typescript
// src/handlers/cdcProcessor.ts

import { KinesisStreamEvent, KinesisStreamBatchResponse } from 'aws-lambda';
import { processAgentChange } from '../processors/agentsProcessor';
import { processCallChange } from '../processors/callsProcessor';
import { processQueueChange } from '../processors/queuesProcessor';
import { publishToEventBridge } from '../services/eventBridgeService';
import { updateProcessingState } from '../services/stateService';
import { sendToDLQ } from '../services/dlqService';

const PROCESSOR_MAP: Record<string, (payload: CDCPayload) => Promise<ProcessedEvent>> = {
  'agents': processAgentChange,
  'calls': processCallChange,
  'queues': processQueueChange,
  'contacts': processContactChange,
  'skills': processSkillChange,
  'routing_profiles': processRoutingProfileChange,
  'users': processUserChange,
  'teams': processTeamChange,
  'schedules': processScheduleChange,
  'metrics_realtime': processRealtimeMetricsChange,
  'metrics_historical': processHistoricalMetricsChange,
  'audit_logs': processAuditLogChange,
};

export async function handler(
  event: KinesisStreamEvent
): Promise<KinesisStreamBatchResponse> {
  const batchItemFailures: { itemIdentifier: string }[] = [];
  
  for (const record of event.Records) {
    const sequenceNumber = record.kinesis.sequenceNumber;
    
    try {
      // Decode and parse the CDC payload
      const payload = decodeCDCPayload(record.kinesis.data);
      
      // Get the appropriate processor for this table
      const processor = PROCESSOR_MAP[payload.table];
      
      if (!processor) {
        console.warn(`No processor found for table: ${payload.table}`);
        continue; // Skip unknown tables without failing
      }
      
      // Process the change
      const processedEvent = await processor(payload);
      
      // Check for duplicate processing (idempotency)
      const isDuplicate = await checkDuplicate(
        payload.metadata.transactionId,
        payload.metadata.sequenceNumber
      );
      
      if (!isDuplicate) {
        // Publish to EventBridge
        await publishToEventBridge(processedEvent);
        
        // Update processing state
        await updateProcessingState({
          transactionId: payload.metadata.transactionId,
          sequenceNumber: payload.metadata.sequenceNumber,
          processedAt: new Date().toISOString(),
          table: payload.table,
        });
      }
      
    } catch (error) {
      console.error(`Error processing record ${sequenceNumber}:`, error);
      
      // Add to batch failures for retry
      batchItemFailures.push({ itemIdentifier: sequenceNumber });
      
      // Send to DLQ after max retries
      if (isMaxRetryExceeded(record)) {
        await sendToDLQ(record, error);
      }
    }
  }
  
  return { batchItemFailures };
}
```

---

## Output to EventBridge

The CDC Processor publishes standardized events to Amazon EventBridge, enabling downstream services to subscribe to specific event types.

### EventBridge Event Structure

```typescript
interface EventBridgeEvent {
  Source: string;
  DetailType: string;
  Detail: string; // JSON stringified ProcessedEvent
  EventBusName: string;
  Time: Date;
  Resources?: string[];
}
```

### Event Publishing Service

```typescript
// src/services/eventBridgeService.ts

import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';

const client = new EventBridgeClient({ region: process.env.AWS_REGION });
const EVENT_BUS_NAME = process.env.CDC_EVENT_BUS_NAME || 'cdc-pipeline-events';

export async function publishToEventBridge(event: ProcessedEvent): Promise<void> {
  const command = new PutEventsCommand({
    Entries: [
      {
        Source: 'cdc-pipeline',
        DetailType: event.eventType,
        Detail: JSON.stringify(event),
        EventBusName: EVENT_BUS_NAME,
        Time: new Date(event.timestamp),
        Resources: [
          `arn:aws:cdc-pipeline:${process.env.AWS_REGION}:${event.payload.entityType}/${event.payload.entityId}`,
        ],
      },
    ],
  });

  const response = await client.send(command);
  
  if (response.FailedEntryCount && response.FailedEntryCount > 0) {
    const failedEntry = response.Entries?.find(e => e.ErrorCode);
    throw new Error(
      `EventBridge publish failed: ${failedEntry?.ErrorCode} - ${failedEntry?.ErrorMessage}`
    );
  }
}

export async function publishBatchToEventBridge(events: ProcessedEvent[]): Promise<void> {
  // EventBridge supports max 10 events per batch
  const batches = chunk(events, 10);
  
  for (const batch of batches) {
    const command = new PutEventsCommand({
      Entries: batch.map(event => ({
        Source: 'cdc-pipeline',
        DetailType: event.eventType,
        Detail: JSON.stringify(event),
        EventBusName: EVENT_BUS_NAME,
        Time: new Date(event.timestamp),
      })),
    });
    
    await client.send(command);
  }
}
```

### Event Types Reference

| Event Type | DetailType | Downstream Consumers |
|-----------|------------|---------------------|
| `AgentStatusChanged` | `cdc.agent.status-changed` | Wallboards, Routing Engine |
| `AgentSkillsUpdated` | `cdc.agent.skills-updated` | Routing Engine |
| `CallInitiated` | `cdc.call.initiated` | Analytics, Wallboards |
| `CallQueued` | `cdc.call.queued` | Wallboards, Alerting |
| `CallConnected` | `cdc.call.connected` | Wallboards, CRM Integration |
| `CallEnded` | `cdc.call.ended` | Analytics, Billing |
| `QueueMetricsUpdated` | `cdc.queue.metrics-updated` | Wallboards, Alerting |

### Sample EventBridge Rule for Wallboards

```json
{
  "Name": "wallboards-agent-status-rule",
  "EventPattern": {
    "source": ["cdc-pipeline"],
    "detail-type": [
      "AgentStatusChanged",
      "QueueMetricsUpdated",
      "CallStateChanged"
    ]
  },
  "Targets": [
    {
      "Id": "wallboards-lambda",
      "Arn": "arn:aws:lambda:us-east-1:123456789:function:wallboards-processor"
    }
  ]
}
```

---

## Error Handling

The CDC Processor implements a comprehensive error handling strategy to ensure reliability and data consistency.

### Error Categories

```typescript
// src/errors/index.ts

export class CDCProcessingError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CDCProcessingError';
  }
}

export const ErrorCodes = {
  // Retryable errors
  EVENTBRIDGE_THROTTLE: { code: 'EB_THROTTLE', retryable: true },
  DYNAMODB_THROTTLE: { code: 'DDB_THROTTLE', retryable: true },
  NETWORK_ERROR: { code: 'NETWORK_ERR', retryable: true },
  
  // Non-retryable errors
  INVALID_PAYLOAD: { code: 'INVALID_PAYLOAD', retryable: false },
  UNKNOWN_TABLE: { code: 'UNKNOWN_TABLE', retryable: false },
  REDACTION_FAILED: { code: 'REDACTION_FAILED', retryable: false },
  SCHEMA_MISMATCH: { code: 'SCHEMA_MISMATCH', retryable: false },
};
```

### Retry Strategy

```typescript
// src/utils/retry.ts

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 100,
  maxDelayMs: 5000,
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (!isRetryable(error) || attempt === config.maxRetries) {
        throw error;
      }
      
      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt),
        config.maxDelayMs
      );
      
      await sleep(delay);
    }
  }
  
  throw lastError;
}
```

### Dead Letter Queue Integration

```typescript
// src/services/dlqService.ts

import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';

const sqsClient = new SQSClient({ region: process.env.AWS_REGION });
const DLQ_URL = process.env.CDC_DLQ_URL;

export async function sendToDLQ(
  record: KinesisRecord,
  error: Error
): Promise<void> {
  const dlqMessage = {
    originalRecord: {
      sequenceNumber: record.kinesis.sequenceNumber,
      partitionKey: record.kinesis.partitionKey,
      data: record.kinesis.data,
      approximateArrivalTimestamp: record.kinesis.approximateArrivalTimestamp,
    },
    error: {
      message: error.message,
      name: error.name,
      stack: error.stack,
    },
    processingAttempts: getProcessingAttempts(record),
    failedAt: new Date().toISOString(),
  };

  await sqsClient.send(new SendMessageCommand({
    QueueUrl: DLQ_URL,
    MessageBody: JSON.stringify(dlqMessage),
    MessageAttributes: {
      'ErrorType': {
        DataType: 'String',
        StringValue: error.name,
      },
      'SequenceNumber': {
        DataType: 'String',
        StringValue: record.kinesis.sequenceNumber,
      },
    },
  }));
}
```

### Monitoring and Alerting

```typescript
// src/utils/metrics.ts

import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

const cloudwatch = new CloudWatchClient({ region: process.env.AWS_REGION });

export async function recordMetric(
  metricName: string,
  value: number,
  dimensions: Record<string, string>
): Promise<void> {
  await cloudwatch.send(new PutMetricDataCommand({
    Namespace: 'CDC-Pipeline',
    MetricData: [
      {
        MetricName: metricName,
        Value: value,
        Unit: 'Count',
        Dimensions: Object.entries(dimensions).map(([name, value]) => ({
          Name: name,
          Value: value,
        })),
      },
    ],
  }));
}

// Usage in processor
await recordMetric('RecordsProcessed', 1, { Table: payload.table });
await recordMetric('ProcessingErrors', 1, { 
  Table: payload.table, 
  ErrorCode: error.code 
});
```

---

## Performance Considerations

### Memory and Timeout Configuration

| Table Category | Memory | Timeout | Justification |
|---------------|--------|---------|---------------|
| Real-time metrics | 1024 MB | 60s | High throughput, simple processing |
| Calls | 1024 MB | 120s | Medium throughput, enrichment required |
| Historical data | 512 MB | 300s | Low throughput, batch processing |

### Optimization Strategies

#### 1. Batch Processing Optimization

```typescript
// Process records in parallel within a batch
export async function processBatch(records: KinesisRecord[]): Promise<void> {
  // Group records by table for efficient processing
  const recordsByTable = groupBy(records, r => 
    decodeCDCPayload(r.kinesis.data).table
  );
  
  // Process each table's records in parallel
  await Promise.all(
    Object.entries(recordsByTable).map(async ([table, tableRecords]) => {
      const processor = PROCESSOR_MAP[table];
      const processedEvents = await Promise.all(
        tableRecords.map(r => processor(decodeCDCPayload(r.kinesis.data)))
      );
      
      // Batch publish to EventBridge
      await publishBatchToEventBridge(processedEvents);
    })
  );
}
```

#### 2. Connection Pooling

```typescript
// Reuse AWS SDK clients across invocations
const eventBridgeClient = new EventBridgeClient({ 
  region: process.env.AWS_REGION,
  maxAttempts: 3,
});

const dynamoDBClient = new DynamoDBClient({
  region: process.env.AWS_REGION,
  maxAttempts: 3,
});
```

#### 3. Payload Size Management

```typescript
// Limit payload size to stay within EventBridge limits (256KB)
function truncatePayload(payload: any, maxSize: number = 250000): any {
  const stringified = JSON.stringify(payload);
  
  if (stringified.length <= maxSize) {
    return payload;
  }
  
  // Remove large fields progressively
  const truncated = { ...payload };
  delete truncated.before; // Remove 'before' state first
  
  if (JSON.stringify(truncated).length > maxSize) {
    // Further truncation logic
    truncated.after = summarizeRecord(truncated.after);
  }
  
  return truncated;
}
```

### Scaling Considerations

- **Shard Count**: The CDC Processor scales with Kinesis shard count. Each shard can support up to 1,000 records/second
- **Parallelization Factor**: Set to 10, allowing 10 concurrent Lambda invocations per shard
- **Reserved Concurrency**: Set to 100 to prevent throttling during peak loads
- **Provisioned Concurrency**: Consider enabling for latency-sensitive event types (e.g., AgentStatusChanged)

---

## Examples

### Complete Processing Flow Example

```typescript
// Example: Processing an agent status change from start to finish

// 1. Input: Raw Kinesis record arrives
const kinesisRecord = {
  kinesis: {
    sequenceNumber: "49590338271490256608559692540925702759324208523137515522",
    data: "eyJtZXRhZGF0YSI6eyJ0aW1lc3RhbXAiOiIyMDI0LTAxLTE1VDEwOjMwOjQ1LjEyM1oiLCJ0cmFuc2FjdGlvbklkIjoidHhuLWFiYzEyMyJ9LCJ0YWJsZSI6ImFnZW50cyIsIm9wZXJhdGlvbiI6IlVQREFURSIsImJlZm9yZSI6eyJhZ2VudF9pZCI6ImFnZW50LTAwMSIsInN0YXR1cyI6ImF2YWlsYWJsZSJ9LCJhZnRlciI6eyJhZ2VudF9pZCI6ImFnZW50LTAwMSIsInN0YXR1cyI6ImJ1c3kifX0="
  }
};

// 2. Decoded CDC payload
const cdcPayload = {
  metadata: {
    timestamp: "2024-01-15T10:30:45.123Z",
    transactionId: "txn-abc123"
  },
  table: "agents",
  operation: "UPDATE",
  before: { agent_id: "agent-001", status: "available" },
  after: { agent_id: "agent-001", status: "busy" }
};

// 3. Processed event (after transformation and redaction)
const processedEvent = {
  eventType: "AgentStatusChanged",
  eventVersion: "1.0",
  timestamp: "2024-01-15T10:30:45.123Z",
  source: "cdc-pipeline",
  correlationId: "txn-abc123",
  payload: {
    operation: "UPDATE",
    entityId: "agent-001",
    entityType: "agent",
    before: { agent_id: "agent-001", status: "available" },
    after: { agent_id: "agent-001", status: "busy" },
    changedFields: ["status"]
  }
};

// 4. Published to EventBridge
// Detail-Type: AgentStatusChanged
// Source: cdc-pipeline
// Event bus: cdc-pipeline-events
```

### Testing the CDC Processor Locally

```typescript
// tests/cdcProcessor.test.ts

import { handler } from '../src/handlers/cdcProcessor';
import { mockKinesisEvent } from './fixtures';

describe('CDC Processor', () => {
  it('should process agent status change', async () => {
    const event = mockKinesisEvent({
      table: 'agents',
      operation: 'UPDATE',
      before: { agent_id: 'test-agent', status: 'available' },
      after: { agent_id: 'test-agent', status: 'busy' },
    });

    const result = await handler(event);
    
    expect(result.batchItemFailures).toHaveLength(0);
    expect(mockEventBridge.putEvents).toHaveBeenCalledWith(
      expect.objectContaining({
        Entries: expect.arrayContaining([
          expect.objectContaining({
            DetailType: 'AgentStatusChanged',
          }),
        ]),
      })
    );
  });

  it('should handle unknown table gracefully', async () => {
    const event = mockKinesisEvent({
      table: 'unknown_table',
      operation: 'INSERT',
      after: { id: '123' },
    });

    const result = await handler(event);
    
    // Should not fail, just skip
    expect(result.batchItemFailures).toHaveLength(0);
  });

  it('should redact sensitive fields', async () => {
    const event = mockKinesisEvent({
      table: 'agents',
      operation: 'INSERT',
      after: { 
        agent_id: 'test-agent', 
        email: 'test@example.com',
        phone_number: '+1234567890'
      },
    });

    await handler(event);
    
    const publishedEvent = mockEventBridge.putEvents.mock.calls[0][0];
    const detail = JSON.parse(publishedEvent.Entries[0].Detail);
    
    expect(detail.payload.after.email).toBe('[REDACTED]');
    expect(detail.payload.after.phone_number).toBe('[REDACTED]');
  });
});
```

### Invoking with AWS CLI (Testing)

```bash
# Create a test event file
cat > test-event.json << 'EOF'
{
  "Records": [
    {
      "kinesis": {
        "kinesisSchemaVersion": "1.0",
        "partitionKey": "agent-001",
        "sequenceNumber": "49590338271490256608559692540925702759324208523137515522",
        "data": "eyJtZXRhZGF0YSI6eyJ0aW1lc3RhbXAiOiIyMDI0LTAxLTE1VDEwOjMwOjQ1LjEyM1oiLCJ0cmFuc2FjdGlvbklkIjoidHhuLWFiYzEyMyIsInNlcXVlbmNlTnVtYmVyIjoxLCJzb3VyY2UiOiJjb3JlZGItcHJpbWFyeSJ9LCJ0YWJsZSI6ImFnZW50cyIsIm9wZXJhdGlvbiI6IlVQREFURSIsImJlZm9yZSI6eyJhZ2VudF9pZCI6ImFnZW50LTAwMSIsInN0YXR1cyI6ImF2YWlsYWJsZSJ9LCJhZnRlciI6eyJhZ2VudF9pZCI6ImFnZW50LTAwMSIsInN0YXR1cyI6ImJ1c3kifSwiY2hhbmdlZENvbHVtbnMiOlsic3RhdHVzIl19",
        "approximateArrivalTimestamp": 1705315845.123
      },
      "eventSource": "aws:kinesis",
      "eventVersion": "1.0",
      "eventID": "shardId-000000000000:49590338271490256608559692540925702759324208523137515522",
      "eventName": "aws:kinesis:record",
      "invokeIdentityArn": "arn:aws:iam::123456789012:role/cdc-processor-role",
      "awsRegion": "us-east-1",
      "eventSourceARN": "arn:aws:kinesis:us-east-1:123456789012:stream/cdc-stream"
    }
  ]
}
EOF

# Invoke the Lambda locally using SAM
sam local invoke cdcProcessor --event test-event.json

# Or invoke deployed Lambda
aws lambda invoke \
  --function-name cdc-pipeline-cdcProcessor \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json
```

---

## Appendix: Data Models Reference

The CDC Processor works with 75 documented data models. Key models relevant to CDC processing include:

- `AgentRecord`: Agent profile and status information
- `CallRecord`: Call metadata and state transitions
- `QueueRecord`: Queue configuration and real-time metrics
- `ContactRecord`: Customer contact information (heavily redacted)

For complete data model documentation, refer to the [Data Models Reference](../data-models/README.md).