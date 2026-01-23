# Architecture & Data Flow

## Overview

The CDC Pipeline service implements a robust Change Data Capture architecture that captures, processes, and distributes database change events from CoreDB to downstream consumers. This document provides a comprehensive explanation of the system architecture, data flow patterns, and the technical mechanisms that ensure reliable event processing.

Understanding this architecture is essential for developers working with the CDC Pipeline, whether integrating new tables, debugging event processing issues, or building downstream consumers that rely on the distributed events.

## High-Level Architecture

### System Overview

The CDC Pipeline follows an event-driven architecture pattern that decouples the source database from downstream consumers through a series of processing stages:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CoreDB    │───▶│   Kinesis   │───▶│   Lambda    │───▶│ EventBridge │
│  (Source)   │    │  (Stream)   │    │ (Processor) │    │   (Bus)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                                     │                   │
       │                                     ▼                   ▼
       │                            ┌─────────────┐    ┌─────────────┐
       │                            │  DynamoDB   │    │  Wallboards │
       │                            │   (State)   │    │ (Consumer)  │
       │                            └─────────────┘    └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        12+ Monitored Tables                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │ Users  │ │ Orders │ │Products│ │Sessions│ │ Events │ │  Logs  │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| CDC Source | AWS DMS / Database Triggers | Captures changes from CoreDB tables |
| Stream Buffer | Amazon Kinesis Data Streams | Buffers and orders change events |
| Event Processor | AWS Lambda | Transforms, redacts, and routes events |
| State Store | Amazon DynamoDB | Maintains processing state and checkpoints |
| Event Bus | Amazon EventBridge | Distributes events to downstream consumers |
| Consumers | Various Services | React to change events (e.g., Wallboards) |

### Architectural Principles

The CDC Pipeline architecture adheres to several key principles:

1. **Eventual Consistency**: Changes propagate asynchronously, ensuring source database performance isn't impacted
2. **At-Least-Once Delivery**: Events may be delivered multiple times; consumers must be idempotent
3. **Ordered Processing**: Events from the same source record maintain ordering within a partition
4. **Fault Isolation**: Failures in downstream processing don't affect upstream capture
5. **Scalability**: Each component can scale independently based on load

## Data Flow Diagram

### Detailed Data Flow

```
                                    CDC PIPELINE DATA FLOW
                                    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                              CAPTURE PHASE                               │
    │  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
    │  │   CoreDB     │  CDC    │   DMS Task   │  JSON   │   Kinesis    │    │
    │  │   Tables     │────────▶│   Instance   │────────▶│   Stream     │    │
    │  │  (INSERT/    │         │              │         │  (Sharded)   │    │
    │  │   UPDATE/    │         └──────────────┘         └──────────────┘    │
    │  │   DELETE)    │                                         │            │
    │  └──────────────┘                                         │            │
    └───────────────────────────────────────────────────────────│────────────┘
                                                                │
                                                                ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                            PROCESSING PHASE                              │
    │                                                                          │
    │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
    │  │   Lambda     │    │   Lambda     │    │   Lambda     │              │
    │  │  Handler 1   │    │  Handler 2   │    │  Handler N   │              │
    │  │  (Shard 1)   │    │  (Shard 2)   │    │  (Shard N)   │              │
    │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
    │         │                   │                   │                       │
    │         ▼                   ▼                   ▼                       │
    │  ┌────────────────────────────────────────────────────────────────┐    │
    │  │                    Processing Steps                             │    │
    │  │  1. Deserialize ─▶ 2. Validate ─▶ 3. Transform ─▶ 4. Redact   │    │
    │  └────────────────────────────────────────────────────────────────┘    │
    │                                    │                                    │
    │                                    ▼                                    │
    │                          ┌──────────────┐                              │
    │                          │   DynamoDB   │                              │
    │                          │ (Checkpoint) │                              │
    │                          └──────────────┘                              │
    └───────────────────────────────────────────────────────────────────│────┘
                                                                        │
                                                                        ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           DISTRIBUTION PHASE                             │
    │                                                                          │
    │  ┌──────────────────────────────────────────────────────────────────┐  │
    │  │                       EventBridge Bus                             │  │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │
    │  │  │ Rule: User  │  │ Rule: Order │  │ Rule: Audit │              │  │
    │  │  │   Changes   │  │   Changes   │  │   Events    │              │  │
    │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │  │
    │  └─────────│────────────────│────────────────│───────────────────────┘  │
    │            │                │                │                          │
    │            ▼                ▼                ▼                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
    │  │ Wallboards  │  │   Search    │  │   Audit     │  │ Analytics   │   │
    │  │  Service    │  │   Service   │  │   Service   │  │  Pipeline   │   │
    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
    └─────────────────────────────────────────────────────────────────────────┘
```

### Event Lifecycle

Each database change follows this lifecycle through the pipeline:

```javascript
// Example event lifecycle representation
const eventLifecycle = {
  // Stage 1: Raw CDC Event from DMS
  captured: {
    timestamp: "2024-01-15T10:30:00.000Z",
    table: "users",
    operation: "UPDATE",
    beforeImage: { id: 123, email: "old@example.com", ssn: "123-45-6789" },
    afterImage: { id: 123, email: "new@example.com", ssn: "123-45-6789" }
  },
  
  // Stage 2: Kinesis Record
  streamed: {
    partitionKey: "users-123",
    sequenceNumber: "49607933946721...",
    approximateArrivalTimestamp: 1705314600123
  },
  
  // Stage 3: Processed & Transformed
  processed: {
    eventId: "evt_abc123",
    eventType: "user.updated",
    entityId: "123",
    changes: {
      email: { old: "old@example.com", new: "new@example.com" }
    },
    metadata: {
      processedAt: "2024-01-15T10:30:01.234Z",
      lambdaRequestId: "req_xyz789"
    }
  },
  
  // Stage 4: Redacted for Distribution
  distributed: {
    eventId: "evt_abc123",
    eventType: "user.updated",
    entityId: "123",
    changes: {
      email: { old: "o**@example.com", new: "n**@example.com" }
    },
    // SSN completely removed - not included in output
    metadata: {
      processedAt: "2024-01-15T10:30:01.234Z"
    }
  }
};
```

## CoreDB Tables Overview

### Monitored Tables

The CDC Pipeline captures changes from 12+ CoreDB tables, each with specific change patterns and downstream consumer requirements:

| Table | Primary Key | CDC Events | Avg Volume | Key Consumers |
|-------|-------------|------------|------------|---------------|
| `users` | `id` | INSERT, UPDATE, DELETE | ~50K/day | Wallboards, Auth |
| `orders` | `order_id` | INSERT, UPDATE | ~200K/day | Wallboards, Fulfillment |
| `products` | `product_id` | INSERT, UPDATE, DELETE | ~10K/day | Search, Inventory |
| `sessions` | `session_id` | INSERT, UPDATE, DELETE | ~500K/day | Analytics, Security |
| `transactions` | `txn_id` | INSERT | ~150K/day | Finance, Audit |
| `inventory` | `sku` | UPDATE | ~80K/day | Wallboards, Alerts |
| `customers` | `customer_id` | INSERT, UPDATE | ~30K/day | CRM, Marketing |
| `shipments` | `shipment_id` | INSERT, UPDATE | ~100K/day | Logistics, Tracking |
| `returns` | `return_id` | INSERT, UPDATE | ~20K/day | Customer Service |
| `reviews` | `review_id` | INSERT, UPDATE, DELETE | ~15K/day | Product, Moderation |
| `audit_logs` | `log_id` | INSERT | ~1M/day | Compliance, Security |
| `configurations` | `config_key` | INSERT, UPDATE, DELETE | ~100/day | All Services |

### Table-Specific Processing Rules

```typescript
// Table configuration definitions
interface TableConfig {
  tableName: string;
  partitionKey: string;
  operations: ('INSERT' | 'UPDATE' | 'DELETE')[];
  redactionRules: RedactionRule[];
  transformations: Transformation[];
  targetEventTypes: EventTypeMapping;
}

const tableConfigurations: TableConfig[] = [
  {
    tableName: 'users',
    partitionKey: 'id',
    operations: ['INSERT', 'UPDATE', 'DELETE'],
    redactionRules: [
      { field: 'ssn', action: 'REMOVE' },
      { field: 'password_hash', action: 'REMOVE' },
      { field: 'email', action: 'PARTIAL_MASK' },
      { field: 'phone', action: 'PARTIAL_MASK' }
    ],
    transformations: [
      { field: 'created_at', type: 'ISO_DATE' },
      { field: 'updated_at', type: 'ISO_DATE' }
    ],
    targetEventTypes: {
      INSERT: 'user.created',
      UPDATE: 'user.updated',
      DELETE: 'user.deleted'
    }
  },
  {
    tableName: 'orders',
    partitionKey: 'order_id',
    operations: ['INSERT', 'UPDATE'],
    redactionRules: [
      { field: 'payment_details', action: 'REMOVE' },
      { field: 'shipping_address', action: 'HASH' }
    ],
    transformations: [
      { field: 'total_amount', type: 'DECIMAL' },
      { field: 'order_date', type: 'ISO_DATE' }
    ],
    targetEventTypes: {
      INSERT: 'order.created',
      UPDATE: 'order.updated'
    }
  }
  // ... additional table configurations
];
```

### Schema Change Handling

The CDC Pipeline implements schema evolution handling to manage database schema changes:

```python
# Schema evolution handler (Python component)
class SchemaEvolutionHandler:
    """Handles schema changes in monitored tables."""
    
    def __init__(self, schema_registry_client):
        self.schema_registry = schema_registry_client
        self.cached_schemas = {}
    
    def handle_schema_change(self, table_name: str, event: dict) -> dict:
        """
        Process events with potential schema changes.
        
        Strategies:
        1. New fields: Include with default handling
        2. Removed fields: Log warning, continue processing
        3. Type changes: Attempt coercion, fail gracefully
        """
        current_schema = self._get_schema(table_name)
        
        # Detect schema drift
        event_fields = set(event.get('afterImage', {}).keys())
        schema_fields = set(current_schema.get('fields', {}).keys())
        
        new_fields = event_fields - schema_fields
        if new_fields:
            logger.warning(
                f"New fields detected in {table_name}: {new_fields}. "
                "Updating schema registry."
            )
            self._update_schema(table_name, event)
        
        return self._normalize_event(event, current_schema)
```

## Lambda Processing Pipeline

### Handler Architecture

The Lambda processing pipeline consists of multiple specialized handlers that work together:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAMBDA PROCESSING PIPELINE                           │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Main Handler (index.ts)                         │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │  │ Record  │  │ Deser-  │  │  Vali-  │  │ Trans-  │  │ Publish │    │  │
│  │  │ Batch   │─▶│ ialize  │─▶│  date   │─▶│  form   │─▶│  Event  │    │  │
│  │  │ Reader  │  │  JSON   │  │ Schema  │  │  Data   │  │  Bridge │    │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│          ┌─────────────────────────┼─────────────────────────┐              │
│          ▼                         ▼                         ▼              │
│  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐       │
│  │   Redaction   │        │     State     │        │     Error     │       │
│  │    Engine     │        │   Manager     │        │    Handler    │       │
│  └───────────────┘        └───────────────┘        └───────────────┘       │
│                                    │                                         │
│                                    ▼                                         │
│                           ┌───────────────┐                                 │
│                           │   DynamoDB    │                                 │
│                           │   (State)     │                                 │
│                           └───────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Main Handler Implementation

```typescript
// src/handlers/cdc-processor.ts
import { KinesisStreamEvent, KinesisStreamRecord, Context } from 'aws-lambda';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, GetCommand } from '@aws-sdk/lib-dynamodb';

interface CDCEvent {
  tableName: string;
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  beforeImage?: Record<string, unknown>;
  afterImage?: Record<string, unknown>;
  timestamp: string;
  sequenceNumber: string;
}

interface ProcessingResult {
  success: boolean;
  eventId?: string;
  error?: Error;
  sequenceNumber: string;
}

const eventBridge = new EventBridgeClient({});
const dynamoDb = DynamoDBDocumentClient.from(new DynamoDBClient({}));

export const handler = async (
  event: KinesisStreamEvent,
  context: Context
): Promise<{ batchItemFailures: { itemIdentifier: string }[] }> => {
  const results: ProcessingResult[] = [];
  const batchItemFailures: { itemIdentifier: string }[] = [];

  console.log(`Processing ${event.Records.length} records from Kinesis`);

  for (const record of event.Records) {
    try {
      const result = await processRecord(record, context);
      results.push(result);
      
      if (!result.success) {
        batchItemFailures.push({
          itemIdentifier: record.kinesis.sequenceNumber
        });
      }
    } catch (error) {
      console.error(`Failed to process record ${record.kinesis.sequenceNumber}:`, error);
      batchItemFailures.push({
        itemIdentifier: record.kinesis.sequenceNumber
      });
    }
  }

  // Log processing summary
  const successCount = results.filter(r => r.success).length;
  console.log(`Processed ${successCount}/${event.Records.length} records successfully`);

  // Return partial batch failure response for retry
  return { batchItemFailures };
};

async function processRecord(
  record: KinesisStreamRecord,
  context: Context
): Promise<ProcessingResult> {
  const sequenceNumber = record.kinesis.sequenceNumber;
  
  // Step 1: Deserialize
  const payload = Buffer.from(record.kinesis.data, 'base64').toString('utf-8');
  const cdcEvent: CDCEvent = JSON.parse(payload);
  
  // Step 2: Check for duplicate processing
  const isDuplicate = await checkDuplicate(sequenceNumber);
  if (isDuplicate) {
    console.log(`Skipping duplicate record: ${sequenceNumber}`);
    return { success: true, sequenceNumber };
  }
  
  // Step 3: Validate
  validateEvent(cdcEvent);
  
  // Step 4: Transform and Redact
  const transformedEvent = transformEvent(cdcEvent);
  const redactedEvent = redactSensitiveData(transformedEvent);
  
  // Step 5: Publish to EventBridge
  const eventId = await publishToEventBridge(redactedEvent);
  
  // Step 6: Update checkpoint
  await updateCheckpoint(sequenceNumber, eventId);
  
  return {
    success: true,
    eventId,
    sequenceNumber
  };
}
```

### Transformation Engine

```typescript
// src/services/transformation-engine.ts
import { TableConfig } from '../config/table-configs';

interface TransformedEvent {
  eventId: string;
  eventType: string;
  entityId: string;
  entityType: string;
  operation: string;
  timestamp: string;
  changes: Record<string, { old?: unknown; new?: unknown }>;
  metadata: {
    sourceTable: string;
    sequenceNumber: string;
    processedAt: string;
    version: string;
  };
}

export class TransformationEngine {
  private tableConfigs: Map<string, TableConfig>;

  constructor(configs: TableConfig[]) {
    this.tableConfigs = new Map(configs.map(c => [c.tableName, c]));
  }

  transform(cdcEvent: CDCEvent): TransformedEvent {
    const config = this.tableConfigs.get(cdcEvent.tableName);
    if (!config) {
      throw new Error(`No configuration found for table: ${cdcEvent.tableName}`);
    }

    const entityId = this.extractEntityId(cdcEvent, config);
    const changes = this.computeChanges(cdcEvent);
    const eventType = config.targetEventTypes[cdcEvent.operation];

    return {
      eventId: this.generateEventId(),
      eventType,
      entityId,
      entityType: cdcEvent.tableName,
      operation: cdcEvent.operation,
      timestamp: cdcEvent.timestamp,
      changes: this.applyTransformations(changes, config.transformations),
      metadata: {
        sourceTable: cdcEvent.tableName,
        sequenceNumber: cdcEvent.sequenceNumber,
        processedAt: new Date().toISOString(),
        version: '1.0'
      }
    };
  }

  private computeChanges(
    cdcEvent: CDCEvent
  ): Record<string, { old?: unknown; new?: unknown }> {
    const changes: Record<string, { old?: unknown; new?: unknown }> = {};
    
    const allFields = new Set([
      ...Object.keys(cdcEvent.beforeImage || {}),
      ...Object.keys(cdcEvent.afterImage || {})
    ]);

    for (const field of allFields) {
      const oldValue = cdcEvent.beforeImage?.[field];
      const newValue = cdcEvent.afterImage?.[field];
      
      if (oldValue !== newValue) {
        changes[field] = { old: oldValue, new: newValue };
      }
    }

    return changes;
  }

  private applyTransformations(
    changes: Record<string, { old?: unknown; new?: unknown }>,
    transformations: Transformation[]
  ): Record<string, { old?: unknown; new?: unknown }> {
    const transformed = { ...changes };

    for (const transformation of transformations) {
      if (transformed[transformation.field]) {
        transformed[transformation.field] = {
          old: this.applyTransformation(
            transformed[transformation.field].old,
            transformation.type
          ),
          new: this.applyTransformation(
            transformed[transformation.field].new,
            transformation.type
          )
        };
      }
    }

    return transformed;
  }

  private applyTransformation(value: unknown, type: string): unknown {
    if (value === null || value === undefined) return value;

    switch (type) {
      case 'ISO_DATE':
        return new Date(value as string | number).toISOString();
      case 'DECIMAL':
        return parseFloat(value as string).toFixed(2);
      case 'UPPERCASE':
        return String(value).toUpperCase();
      case 'LOWERCASE':
        return String(value).toLowerCase();
      default:
        return value;
    }
  }

  private generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private extractEntityId(cdcEvent: CDCEvent, config: TableConfig): string {
    const source = cdcEvent.afterImage || cdcEvent.beforeImage;
    return String(source?.[config.partitionKey] || 'unknown');
  }
}
```

### Redaction Engine

```typescript
// src/services/redaction-engine.ts
import { createHash } from 'crypto';

type RedactionAction = 'REMOVE' | 'HASH' | 'PARTIAL_MASK' | 'FULL_MASK' | 'TOKENIZE';

interface RedactionRule {
  field: string;
  action: RedactionAction;
  maskChar?: string;
  visibleChars?: number;
}

export class RedactionEngine {
  private rules: Map<string, RedactionRule[]>;
  private tokenStore: Map<string, string>;

  constructor(tableRules: Record<string, RedactionRule[]>) {
    this.rules = new Map(Object.entries(tableRules));
    this.tokenStore = new Map();
  }

  redact(
    tableName: string,
    data: Record<string, { old?: unknown; new?: unknown }>
  ): Record<string, { old?: unknown; new?: unknown }> {
    const rules = this.rules.get(tableName) || [];
    const redacted = { ...data };

    for (const rule of rules) {
      if (redacted[rule.field]) {
        if (rule.action === 'REMOVE') {
          delete redacted[rule.field];
        } else {
          redacted[rule.field] = {
            old: this.applyRedaction(redacted[rule.field].old, rule),
            new: this.applyRedaction(redacted[rule.field].new, rule)
          };
        }
      }
    }

    return redacted;
  }

  private applyRedaction(value: unknown, rule: RedactionRule): unknown {
    if (value === null || value === undefined) return value;

    const stringValue = String(value);

    switch (rule.action) {
      case 'HASH':
        return this.hashValue(stringValue);
      
      case 'PARTIAL_MASK':
        return this.partialMask(stringValue, rule.visibleChars || 3, rule.maskChar || '*');
      
      case 'FULL_MASK':
        return rule.maskChar?.repeat(stringValue.length) || '***REDACTED***';
      
      case 'TOKENIZE':
        return this.tokenize(stringValue);
      
      default:
        return value;
    }
  }

  private hashValue(value: string): string {
    return createHash('sha256').update(value).digest('hex').substring(0, 16);
  }

  private partialMask(value: string, visibleChars: number, maskChar: string): string {
    if (value.length <= visibleChars) {
      return maskChar.repeat(value.length);
    }
    
    const visible = value.substring(0, visibleChars);
    const masked = maskChar.repeat(Math.min(value.length - visibleChars, 10));
    return `${visible}${masked}`;
  }

  private tokenize(value: string): string {
    const existingToken = this.tokenStore.get(value);
    if (existingToken) return existingToken;

    const token = `tok_${createHash('md5').update(value).digest('hex').substring(0, 12)}`;
    this.tokenStore.set(value, token);
    return token;
  }
}
```

## EventBridge Integration

### Event Publishing

```typescript
// src/services/eventbridge-publisher.ts
import { 
  EventBridgeClient, 
  PutEventsCommand,
  PutEventsRequestEntry 
} from '@aws-sdk/client-eventbridge';

interface PublishOptions {
  detailType: string;
  source: string;
  eventBusName: string;
  detail: Record<string, unknown>;
  traceHeader?: string;
}

export class EventBridgePublisher {
  private client: EventBridgeClient;
  private eventBusName: string;
  private sourcePrefix: string;

  constructor(config: { region: string; eventBusName: string; sourcePrefix: string }) {
    this.client = new EventBridgeClient({ region: config.region });
    this.eventBusName = config.eventBusName;
    this.sourcePrefix = config.sourcePrefix;
  }

  async publish(event: TransformedEvent): Promise<string> {
    const entry: PutEventsRequestEntry = {
      EventBusName: this.eventBusName,
      Source: `${this.sourcePrefix}.${event.entityType}`,
      DetailType: event.eventType,
      Detail: JSON.stringify({
        eventId: event.eventId,
        entityId: event.entityId,
        entityType: event.entityType,
        operation: event.operation,
        timestamp: event.timestamp,
        changes: event.changes,
        metadata: event.metadata
      }),
      Time: new Date(event.timestamp)
    };

    const command = new PutEventsCommand({
      Entries: [entry]
    });

    const response = await this.client.send(command);

    if (response.FailedEntryCount && response.FailedEntryCount > 0) {
      const failedEntry = response.Entries?.[0];
      throw new Error(
        `EventBridge publish failed: ${failedEntry?.ErrorCode} - ${failedEntry?.ErrorMessage}`
      );
    }

    return response.Entries?.[0]?.EventId || event.eventId;
  }

  async publishBatch(events: TransformedEvent[]): Promise<Map<string, string>> {
    const results = new Map<string, string>();
    
    // EventBridge allows max 10 entries per request
    const batches = this.chunk(events, 10);

    for (const batch of batches) {
      const entries: PutEventsRequestEntry[] = batch.map(event => ({
        EventBusName: this.eventBusName,
        Source: `${this.sourcePrefix}.${event.entityType}`,
        DetailType: event.eventType,
        Detail: JSON.stringify({
          eventId: event.eventId,
          entityId: event.entityId,
          entityType: event.entityType,
          operation: event.operation,
          timestamp: event.timestamp,
          changes: event.changes,
          metadata: event.metadata
        }),
        Time: new Date(event.timestamp)
      }));

      const command = new PutEventsCommand({ Entries: entries });
      const response = await this.client.send(command);

      response.Entries?.forEach((entry, index) => {
        const originalEvent = batch[index];
        if (entry.EventId) {
          results.set(originalEvent.eventId, entry.EventId);
        }
      });
    }

    return results;
  }

  private chunk<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}
```

### EventBridge Rules Configuration

```yaml
# infrastructure/eventbridge-rules.yml
Resources:
  # Rule for Wallboards service - User events
  WallboardsUserEventsRule:
    Type: AWS::Events::Rule
    Properties:
      Name: cdc-wallboards-user-events
      Description: Route user change events to Wallboards service
      EventBusName: !Ref CDCEventBus
      EventPattern:
        source:
          - prefix: "cdc-pipeline.users"
        detail-type:
          - "user.created"
          - "user.updated"
          - "user.deleted"
      State: ENABLED
      Targets:
        - Id: WallboardsTarget
          Arn: !GetAtt WallboardsQueue.Arn

  # Rule for Wallboards service - Order events
  WallboardsOrderEventsRule:
    Type: AWS::Events::Rule
    Properties:
      Name: cdc-wallboards-order-events
      Description: Route order change events to Wallboards service
      EventBusName: !Ref CDCEventBus
      EventPattern:
        source:
          - prefix: "cdc-pipeline.orders"
        detail-type:
          - "order.created"
          - "order.updated"
      State: ENABLED
      Targets:
        - Id: WallboardsTarget
          Arn: !GetAtt WallboardsQueue.Arn
        - Id: AnalyticsTarget
          Arn: !GetAtt AnalyticsStream.Arn

  # Archive rule for compliance
  CDCArchiveRule:
    Type: AWS::Events::Archive
    Properties:
      ArchiveName: cdc-events-archive
      Description: Archive all CDC events for compliance
      EventPattern:
        source:
          - prefix: "cdc-pipeline"
      RetentionDays: 365
      SourceArn: !GetAtt CDCEventBus.Arn
```

### Event Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CDC Event Schema",
  "description": "Schema for Change Data Capture events published to EventBridge",
  "type": "object",
  "required": ["eventId", "eventType", "entityId", "entityType", "operation", "timestamp", "changes", "metadata"],
  "properties": {
    "eventId": {
      "type": "string",
      "description": "Unique identifier for this event",
      "pattern": "^evt_[0-9]+_[a-z0-9]+$"
    },
    "eventType": {
      "type": "string",
      "description": "Type of the event",
      "enum": [
        "user.created", "user.updated", "user.deleted",
        "order.created", "order.updated",
        "product.created", "product.updated", "product.deleted",
        "inventory.updated",
        "transaction.created"
      ]
    },
    "entityId": {
      "type": "string",
      "description": "Primary key of the affected entity"
    },
    "entityType": {
      "type": "string",
      "description": "Type/table of the affected entity"
    },
    "operation": {
      "type": "string",
      "enum": ["INSERT", "UPDATE", "DELETE"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp when the change occurred in the source database"
    },
    "changes": {
      "type": "object",
      "description": "Map of changed fields with old and new values",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "old": {},
          "new": {}
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["sourceTable", "processedAt", "version"],
      "properties": {
        "sourceTable": {
          "type": "string"
        },
        "sequenceNumber": {
          "type": "string"
        },
        "processedAt": {
          "type": "string",
          "format": "date-time"
        },
        "version": {
          "type": "string"
        }
      }
    }
  }
}
```

## Error Handling Strategy

### Error Classification

The CDC Pipeline classifies errors into categories that determine handling behavior:

```typescript
// src/errors/error-classifier.ts
export enum ErrorCategory {
  TRANSIENT = 'TRANSIENT',           // Temporary failures, should retry
  PERMANENT = 'PERMANENT',           // Non-recoverable, send to DLQ
  POISON_MESSAGE = 'POISON_MESSAGE', // Invalid data, needs investigation
  THROTTLING = 'THROTTLING',         // Rate limited, backoff and retry
  CONFIGURATION = 'CONFIGURATION'    // Config error, needs intervention
}

interface ClassifiedError {
  category: ErrorCategory;
  retryable: boolean;
  maxRetries: number;
  backoffMs: number;
  shouldAlert: boolean;
  dlqAction: 'SKIP' | 'STORE' | 'STORE_AND_ALERT';
}

export class ErrorClassifier {
  classify(error: Error): ClassifiedError {
    // AWS SDK errors
    if (error.name === 'ProvisionedThroughputExceededException') {
      return {
        category: ErrorCategory.THROTTLING,
        retryable: true,
        maxRetries: 5,
        backoffMs: 1000,
        shouldAlert: false,
        dlqAction: 'SKIP'
      };
    }

    if (error.name === 'ServiceUnavailable' || error.name === 'InternalServerError') {
      return {
        category: ErrorCategory.TRANSIENT,
        retryable: true,
        maxRetries: 3,
        backoffMs: 500,
        shouldAlert: false,
        dlqAction: 'SKIP'
      };
    }

    // Validation errors
    if (error.name === 'ValidationError' || error.name === 'SchemaError') {
      return {
        category: ErrorCategory.POISON_MESSAGE,
        retryable: false,
        maxRetries: 0,
        backoffMs: 0,
        shouldAlert: true,
        dlqAction: 'STORE_AND_ALERT'
      };
    }

    // JSON parsing errors
    if (error.name === 'SyntaxError' && error.message.includes('JSON')) {
      return {
        category: ErrorCategory.POISON_MESSAGE,
        retryable: false,
        maxRetries: 0,
        backoffMs: 0,
        shouldAlert: true,
        dlqAction: 'STORE_AND_ALERT'
      };
    }

    // Default: treat as permanent
    return {
      category: ErrorCategory.PERMANENT,
      retryable: false,
      maxRetries: 0,
      backoffMs: 0,
      shouldAlert: true,
      dlqAction: 'STORE'
    };
  }
}
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ERROR HANDLING FLOW                                │
│                                                                              │
│  ┌─────────────┐                                                            │
│  │   Error     │                                                            │
│  │  Occurred   │                                                            │
│  └──────┬──────┘                                                            │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────┐     ┌─────────────┐                                       │
│  │  Classify   │────▶│  TRANSIENT  │────┐                                  │
│  │   Error     │     └─────────────┘    │                                  │
│  └──────┬──────┘                        │                                  │
│         │                               ▼                                   │
│         │            ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│         │            │   THROTTLE  │  │   Exponential│  │   Retry     │    │
│         ├───────────▶│   Check     │─▶│   Backoff   │─▶│   Request   │    │
│         │            └─────────────┘  └─────────────┘  └──────┬──────┘    │
│         │                                                      │           │
│         │            ┌─────────────┐                          │           │
│         │            │  PERMANENT  │◀─────────────────────────┘           │
│         ├───────────▶│   Error     │     (after max retries)              │
│         │            └──────┬──────┘                                       │
│         │                   │                                              │
│         │            ┌─────────────┐                                       │
│         │            │   POISON    │                                       │
│         └───────────▶│   MESSAGE   │                                       │
│                      └──────┬──────┘                                       │
│                             │                                              │
│                             ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐│
│  │                        Dead Letter Queue                               ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   ││
│  │  │   Store     │  │    Log      │  │   Alert     │                   ││
│  │  │   Event     │  │   Details   │  │   (if req)  │                   ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   ││
│  └───────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dead Letter Queue Handler

```typescript
// src/handlers/dlq-processor.ts
import { SQSEvent, SQSRecord, Context } from 'aws-lambda';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

interface DLQMessage {
  originalEvent: unknown;
  error: {
    name: string;
    message: string;
    stack?: string;
  };
  metadata: {
    failedAt: string;
    retryCount: number;
    lastRetryAt?: string;
    sourceArn: string;
  };
}

const sns = new SNSClient({});
const s3 = new S3Client({});

export const handler = async (event: SQSEvent, context: Context): Promise<void> => {
  for (const record of event.Records) {
    await processDLQMessage(record, context);
  }
};

async function processDLQMessage(record: SQSRecord, context: Context): Promise<void> {
  const message: DLQMessage = JSON.parse(record.body);
  const messageId = record.messageId;

  console.log('Processing DLQ message:', {
    messageId,
    errorName: message.error.name,
    errorMessage: message.error.message,
    retryCount: message.metadata.retryCount
  });

  // Store failed event in S3 for investigation
  await s3.send(new PutObjectCommand({
    Bucket: process.env.DLQ_ARCHIVE_BUCKET,
    Key: `failed-events/${new Date().toISOString().split('T')[0]}/${messageId}.json`,
    Body: JSON.stringify(message, null, 2),
    ContentType: 'application/json',
    Metadata: {
      'error-name': message.error.name,
      'retry-count': String(message.metadata.retryCount),
      'failed-at': message.metadata.failedAt
    }
  }));

  // Send alert for critical errors
  if (shouldAlert(message)) {
    await sns.send(new PublishCommand({
      TopicArn: process.env.ALERT_TOPIC_ARN,
      Subject: `CDC Pipeline DLQ Alert: ${message.error.name}`,
      Message: JSON.stringify({
        severity: 'HIGH',
        service: 'cdc-pipeline',
        errorType: message.error.name,
        errorMessage: message.error.message,
        failedAt: message.metadata.failedAt,
        retryCount: message.metadata.retryCount,
        archiveLocation: `s3://${process.env.DLQ_ARCHIVE_BUCKET}/failed-events/${messageId}.json`
      }, null, 2),
      MessageAttributes: {
        severity: { DataType: 'String', StringValue: 'HIGH' },
        service: { DataType: 'String', StringValue: 'cdc-pipeline' }
      }
    }));
  }
}

function shouldAlert(message: DLQMessage): boolean {
  const alertableErrors = ['ValidationError', 'SchemaError', 'ConfigurationError'];
  return alertableErrors.includes(message.error.name);
}
```

## Retry Mechanisms

### Exponential Backoff Implementation

```typescript
// src/utils/retry.ts
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterFactor: number;
}

interface RetryResult<T> {
  success: boolean;
  result?: T;
  error?: Error;
  attempts: number;
  totalDelayMs: number;
}

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig,
  errorClassifier: ErrorClassifier
): Promise<RetryResult<T>> {
  let lastError: Error | undefined;
  let attempts = 0;
  let totalDelayMs = 0;

  while (attempts < config.maxRetries) {
    attempts++;

    try {
      const result = await operation();
      return {
        success: true,
        result,
        attempts,
        totalDelayMs
      };
    } catch (error) {
      lastError = error as Error;
      const classification = errorClassifier.classify(lastError);

      console.log(`Attempt ${attempts} failed:`, {
        error: lastError.message,
        category: classification.category,
        retryable: classification.retryable
      });

      if (!classification.retryable) {
        break;
      }

      if (attempts < config.maxRetries) {
        const delay = calculateDelay(attempts, config);
        totalDelayMs += delay;
        
        console.log(`Waiting ${delay}ms before retry ${attempts + 1}`);
        await sleep(delay);
      }
    }
  }

  return {
    success: false,
    error: lastError,
    attempts,
    totalDelayMs
  };
}

function calculateDelay(attempt: number, config: RetryConfig): number {
  // Exponential backoff: baseDelay * 2^attempt
  const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt - 1);
  
  // Cap at max delay
  const cappedDelay = Math.min(exponentialDelay, config.maxDelayMs);
  
  // Add jitter to prevent thundering herd
  const jitter = cappedDelay * config.jitterFactor * Math.random();
  
  return Math.floor(cappedDelay + jitter);
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Circuit Breaker Pattern

```typescript
// src/utils/circuit-breaker.ts
enum CircuitState {
  CLOSED = 'CLOSED',     // Normal operation
  OPEN = 'OPEN',         // Failing fast
  HALF_OPEN = 'HALF_OPEN' // Testing recovery
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  recoveryTimeoutMs: number;
  halfOpenRequests: number;
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private lastFailureTime: number = 0;
  private halfOpenSuccesses: number = 0;

  constructor(
    private name: string,
    private config: CircuitBreakerConfig
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    // Check if circuit should transition from OPEN to HALF_OPEN
    if (this.state === CircuitState.OPEN) {
      const timeSinceFailure = Date.now() - this.lastFailureTime;
      if (timeSinceFailure >= this.config.recoveryTimeoutMs) {
        this.transitionTo(CircuitState.HALF_OPEN);
      } else {
        throw new CircuitOpenError(
          `Circuit ${this.name} is OPEN. Try again in ${
            this.config.recoveryTimeoutMs - timeSinceFailure
          }ms`
        );
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.halfOpenSuccesses++;
      if (this.halfOpenSuccesses >= this.config.halfOpenRequests) {
        this.transitionTo(CircuitState.CLOSED);
      }
    }
    this.failures = 0;
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      this.transitionTo(CircuitState.OPEN);
    } else if (this.failures >= this.config.failureThreshold) {
      this.transitionTo(CircuitState.OPEN);
    }
  }

  private transitionTo(newState: CircuitState): void {
    console.log(`Circuit ${this.name}: ${this.state} -> ${newState}`);
    this.state = newState;
    
    if (newState === CircuitState.CLOSED) {
      this.failures = 0;
    } else if (newState === CircuitState.HALF_OPEN) {
      this.halfOpenSuccesses = 0;
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}

export class CircuitOpenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CircuitOpenError';
  }
}
```

### Retry Configuration by Component

| Component | Max Retries | Base Delay | Max Delay | Jitter |
|-----------|-------------|------------|-----------|--------|
| Kinesis Read | 3 | 100ms | 1s | 0.2 |
| DynamoDB Write | 5 | 50ms | 500ms | 0.1 |
| EventBridge Publish | 3 | 200ms | 2s | 0.3 |
| State Update | 5 | 100ms | 1s | 0.2 |

### Checkpoint Management

```typescript
// src/services/checkpoint-manager.ts
import { DynamoDBDocumentClient, PutCommand, GetCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';

interface Checkpoint {
  shardId: string;
  sequenceNumber: string;
  lastProcessedAt: string;
  eventsProcessed: number;
  lastEventId: string;
}

export class CheckpointManager {
  constructor(
    private dynamoDb: DynamoDBDocumentClient,
    private tableName: string
  ) {}

  async saveCheckpoint(checkpoint: Checkpoint): Promise<void> {
    await this.dynamoDb.send(new PutCommand({
      TableName: this.tableName,
      Item: {
        pk: `SHARD#${checkpoint.shardId}`,
        sk: 'CHECKPOINT',
        ...checkpoint,
        updatedAt: new Date().toISOString()
      },
      ConditionExpression: 'attribute_not_exists(sequenceNumber) OR sequenceNumber < :seq',
      ExpressionAttributeValues: {
        ':seq': checkpoint.sequenceNumber
      }
    }));
  }

  async getCheckpoint(shardId: string): Promise<Checkpoint | null> {
    const response = await this.dynamoDb.send(new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `SHARD#${shardId}`,
        sk: 'CHECKPOINT'
      }
    }));

    return response.Item as Checkpoint || null;
  }

  async isDuplicate(shardId: string, sequenceNumber: string): Promise<boolean> {
    const checkpoint = await this.getCheckpoint(shardId);
    if (!checkpoint) return false;
    
    return sequenceNumber <= checkpoint.sequenceNumber;
  }
}
```

## Summary

The CDC Pipeline architecture provides a robust, scalable solution for capturing and distributing database changes. Key architectural decisions include:

1. **Event-Driven Design**: Decouples source systems from consumers through asynchronous event processing
2. **Multi-Stage Pipeline**: Enables independent scaling and failure isolation at each stage
3. **Comprehensive Error Handling**: Classifies errors and applies appropriate retry strategies
4. **Data Protection**: Built-in redaction ensures sensitive data never leaves the pipeline
5. **Observability**: Extensive logging and metrics at each processing stage

For implementation details on specific components, refer to:
- [Lambda Function Setup](./lambda-setup.md)
- [EventBridge Configuration](./eventbridge-config.md)
- [Monitoring & Alerting](./monitoring.md)