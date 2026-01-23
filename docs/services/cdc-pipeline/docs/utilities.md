# Utility Functions

## Overview

The CDC Pipeline service includes a comprehensive suite of utility functions that handle common operations across all Lambda handlers. These utilities provide consistent validation, transformation, redaction, and processing capabilities that ensure data integrity, security, and reliable event handling throughout the pipeline.

This documentation covers the core utility modules that power the CDC Pipeline's data processing capabilities, from initial event parsing through final transformation and redaction before publishing to EventBridge.

---

## Validation Helper

### Purpose

The Validation Helper module provides a centralized validation framework for incoming CDC events, ensuring data consistency and preventing malformed data from propagating through the pipeline.

### Module Location

```
src/utils/validation-helper.ts
```

### Core Functions

#### `validateCdcEvent(event: RawCdcEvent): ValidationResult`

Validates the structure and content of incoming CDC events from Kinesis streams.

```typescript
import { validateCdcEvent, ValidationResult } from './utils/validation-helper';

const rawEvent = {
  tableName: 'core_users',
  operation: 'INSERT',
  timestamp: '2024-01-15T10:30:00Z',
  payload: {
    id: '12345',
    email: 'user@example.com'
  }
};

const result: ValidationResult = validateCdcEvent(rawEvent);

if (result.isValid) {
  // Process the event
  console.log('Event validated successfully');
} else {
  // Handle validation errors
  console.error('Validation failed:', result.errors);
}
```

#### `validateTableSchema(tableName: string, payload: Record<string, unknown>): SchemaValidationResult`

Validates that a payload conforms to the expected schema for a specific CoreDB table.

```typescript
import { validateTableSchema } from './utils/validation-helper';

const schemaResult = validateTableSchema('core_agents', {
  agent_id: 'AGT-001',
  name: 'John Smith',
  status: 'ACTIVE',
  created_at: '2024-01-15T10:30:00Z'
});

if (!schemaResult.isValid) {
  schemaResult.missingFields.forEach(field => {
    console.warn(`Missing required field: ${field}`);
  });
  
  schemaResult.invalidTypes.forEach(({ field, expected, received }) => {
    console.error(`Type mismatch for ${field}: expected ${expected}, got ${received}`);
  });
}
```

#### `validateOperationType(operation: string): boolean`

Validates that the CDC operation type is supported.

```typescript
import { validateOperationType, SUPPORTED_OPERATIONS } from './utils/validation-helper';

// Supported operations: INSERT, UPDATE, DELETE
const isValid = validateOperationType('UPDATE'); // true
const isInvalid = validateOperationType('TRUNCATE'); // false
```

### Validation Rules Reference

| Field | Rule | Error Code |
|-------|------|------------|
| `tableName` | Must be non-empty string, must exist in TABLE_REGISTRY | `INVALID_TABLE_NAME` |
| `operation` | Must be INSERT, UPDATE, or DELETE | `INVALID_OPERATION` |
| `timestamp` | Must be valid ISO 8601 format | `INVALID_TIMESTAMP` |
| `payload` | Must be non-null object | `INVALID_PAYLOAD` |
| `payload.id` | Must be present for UPDATE/DELETE | `MISSING_PRIMARY_KEY` |

### Custom Validators

You can extend validation with custom validators for specific business rules:

```typescript
import { registerCustomValidator, ValidatorFn } from './utils/validation-helper';

const validateAgentStatus: ValidatorFn = (payload) => {
  const validStatuses = ['ACTIVE', 'INACTIVE', 'SUSPENDED'];
  if (payload.status && !validStatuses.includes(payload.status)) {
    return {
      isValid: false,
      error: `Invalid agent status: ${payload.status}`
    };
  }
  return { isValid: true };
};

registerCustomValidator('core_agents', validateAgentStatus);
```

---

## Event Record Transformation

### Purpose

The Event Record Transformation module converts raw CDC events into standardized formats suitable for EventBridge publishing and downstream consumer processing.

### Module Location

```
src/utils/event-transformer.ts
```

### Core Transformation Functions

#### `transformCdcToEventBridge(cdcEvent: CdcEvent): EventBridgeEvent`

Transforms a CDC event into the EventBridge event format.

```typescript
import { transformCdcToEventBridge } from './utils/event-transformer';

const cdcEvent: CdcEvent = {
  tableName: 'core_calls',
  operation: 'INSERT',
  timestamp: '2024-01-15T10:30:00Z',
  beforeImage: null,
  afterImage: {
    call_id: 'CALL-12345',
    agent_id: 'AGT-001',
    duration: 180,
    status: 'COMPLETED'
  }
};

const eventBridgeEvent = transformCdcToEventBridge(cdcEvent);

// Result:
// {
//   Source: 'cdc-pipeline.core_calls',
//   DetailType: 'CDC.INSERT',
//   Detail: {
//     tableName: 'core_calls',
//     operation: 'INSERT',
//     timestamp: '2024-01-15T10:30:00Z',
//     data: { ... },
//     metadata: {
//       version: '1.0',
//       correlationId: 'uuid-...',
//       processedAt: '2024-01-15T10:30:01Z'
//     }
//   },
//   EventBusName: 'cdc-events-bus'
// }
```

#### `transformDeltaRecord(beforeImage: Record, afterImage: Record): DeltaRecord`

Computes the delta between before and after images for UPDATE operations.

```typescript
import { transformDeltaRecord } from './utils/event-transformer';

const delta = transformDeltaRecord(
  { id: '123', status: 'PENDING', priority: 1 },
  { id: '123', status: 'COMPLETED', priority: 1 }
);

// Result:
// {
//   unchangedFields: ['id', 'priority'],
//   changedFields: {
//     status: {
//       before: 'PENDING',
//       after: 'COMPLETED'
//     }
//   }
// }
```

#### `transformBatchRecords(records: CdcEvent[]): BatchTransformResult`

Efficiently transforms multiple CDC events in a batch operation.

```typescript
import { transformBatchRecords } from './utils/event-transformer';

const batchResult = transformBatchRecords(cdcEvents);

console.log(`Transformed: ${batchResult.successful.length}`);
console.log(`Failed: ${batchResult.failed.length}`);

// Process successful transformations
for (const event of batchResult.successful) {
  await publishToEventBridge(event);
}

// Handle failures
for (const failure of batchResult.failed) {
  await sendToDeadLetterQueue(failure.originalEvent, failure.error);
}
```

### Transformation Pipelines

For complex transformations, use the pipeline builder:

```typescript
import { TransformationPipeline } from './utils/event-transformer';

const pipeline = new TransformationPipeline()
  .addStep('validate', validateCdcEvent)
  .addStep('redact', redactSensitiveFields)
  .addStep('enrich', enrichWithMetadata)
  .addStep('format', formatForEventBridge);

const result = await pipeline.execute(rawCdcEvent);
```

---

## Base Types Manipulator

### Purpose

The Base Types Manipulator provides type-safe utilities for working with the core data types used throughout the CDC Pipeline, including type conversions, type guards, and type-safe operations.

### Module Location

```
src/utils/base-types.ts
```

### Type Definitions

```typescript
// Core CDC types
export type CdcOperation = 'INSERT' | 'UPDATE' | 'DELETE';

export interface CdcEventBase {
  tableName: string;
  operation: CdcOperation;
  timestamp: string;
  sequenceNumber: string;
}

export interface CdcInsertEvent extends CdcEventBase {
  operation: 'INSERT';
  afterImage: Record<string, unknown>;
}

export interface CdcUpdateEvent extends CdcEventBase {
  operation: 'UPDATE';
  beforeImage: Record<string, unknown>;
  afterImage: Record<string, unknown>;
}

export interface CdcDeleteEvent extends CdcEventBase {
  operation: 'DELETE';
  beforeImage: Record<string, unknown>;
}

export type CdcEvent = CdcInsertEvent | CdcUpdateEvent | CdcDeleteEvent;
```

### Type Guards

```typescript
import { 
  isInsertEvent, 
  isUpdateEvent, 
  isDeleteEvent,
  isCdcEvent 
} from './utils/base-types';

function processCdcEvent(event: unknown): void {
  if (!isCdcEvent(event)) {
    throw new Error('Invalid CDC event structure');
  }

  if (isInsertEvent(event)) {
    // TypeScript knows event.afterImage exists
    handleInsert(event.afterImage);
  } else if (isUpdateEvent(event)) {
    // TypeScript knows both images exist
    handleUpdate(event.beforeImage, event.afterImage);
  } else if (isDeleteEvent(event)) {
    // TypeScript knows event.beforeImage exists
    handleDelete(event.beforeImage);
  }
}
```

### Type Conversion Utilities

#### `coerceToString(value: unknown): string | null`

Safely converts values to strings with null handling.

```typescript
import { coerceToString } from './utils/base-types';

coerceToString(123);        // '123'
coerceToString(null);       // null
coerceToString(undefined);  // null
coerceToString({ a: 1 });   // '{"a":1}'
```

#### `coerceToNumber(value: unknown): number | null`

Safely converts values to numbers.

```typescript
import { coerceToNumber } from './utils/base-types';

coerceToNumber('123');      // 123
coerceToNumber('12.5');     // 12.5
coerceToNumber('abc');      // null
coerceToNumber(null);       // null
```

#### `coerceToTimestamp(value: unknown): Date | null`

Converts various timestamp formats to Date objects.

```typescript
import { coerceToTimestamp } from './utils/base-types';

coerceToTimestamp('2024-01-15T10:30:00Z');  // Date object
coerceToTimestamp(1705315800000);            // Date object (from epoch ms)
coerceToTimestamp('invalid');                // null
```

### Deep Clone and Merge

```typescript
import { deepClone, deepMerge } from './utils/base-types';

// Deep clone prevents mutation
const original = { nested: { value: 1 } };
const cloned = deepClone(original);
cloned.nested.value = 2;
console.log(original.nested.value); // Still 1

// Deep merge combines objects
const base = { a: 1, nested: { b: 2 } };
const override = { nested: { c: 3 } };
const merged = deepMerge(base, override);
// Result: { a: 1, nested: { b: 2, c: 3 } }
```

---

## Parser Helper

### Purpose

The Parser Helper module provides robust parsing capabilities for various data formats encountered in CDC events, including JSON parsing with error recovery, binary data parsing, and format-specific parsers for different CoreDB table schemas.

### Module Location

```
src/utils/parser-helper.ts
```

### JSON Parsing

#### `safeJsonParse<T>(input: string, defaultValue?: T): T | null`

Safely parses JSON with optional default values.

```typescript
import { safeJsonParse } from './utils/parser-helper';

// Basic usage
const data = safeJsonParse<UserData>('{"name":"John"}');

// With default value
const config = safeJsonParse<Config>(rawConfig, { timeout: 30000 });

// Handles malformed JSON gracefully
const result = safeJsonParse('not-valid-json'); // Returns null
```

#### `parseKinesisRecord(record: KinesisRecord): ParsedRecord`

Parses Kinesis stream records, handling base64 decoding and JSON parsing.

```typescript
import { parseKinesisRecord } from './utils/parser-helper';

export const handler = async (event: KinesisStreamEvent) => {
  for (const record of event.Records) {
    const parsedRecord = parseKinesisRecord(record);
    
    if (parsedRecord.success) {
      await processEvent(parsedRecord.data);
    } else {
      console.error('Parse failed:', parsedRecord.error);
      await sendToDeadLetterQueue(record, parsedRecord.error);
    }
  }
};
```

### Table-Specific Parsers

Each CoreDB table has a dedicated parser that handles its specific schema:

```typescript
import { 
  parseAgentRecord,
  parseCallRecord,
  parseQueueRecord,
  parseInteractionRecord
} from './utils/parser-helper';

// Agent table parser
const agent = parseAgentRecord({
  agent_id: 'AGT-001',
  skills: '["voice","chat"]',  // JSON string in DB
  metadata: '{"team":"support"}'
});
// Automatically parses JSON fields:
// agent.skills = ['voice', 'chat']
// agent.metadata = { team: 'support' }

// Call record parser with duration calculation
const call = parseCallRecord({
  call_id: 'CALL-123',
  start_time: '2024-01-15T10:00:00Z',
  end_time: '2024-01-15T10:05:30Z'
});
// Automatically calculates:
// call.durationSeconds = 330
```

### Binary Data Parser

```typescript
import { parseBinaryPayload } from './utils/parser-helper';

// For tables that store binary/blob data
const binaryResult = parseBinaryPayload(base64EncodedData, {
  encoding: 'utf-8',
  maxSize: 1024 * 1024 // 1MB limit
});

if (binaryResult.truncated) {
  console.warn('Payload was truncated due to size limits');
}
```

### Timestamp Parsing

```typescript
import { parseTimestamp, TimestampFormat } from './utils/parser-helper';

// Auto-detect format
const date1 = parseTimestamp('2024-01-15T10:30:00Z');
const date2 = parseTimestamp('1705315800');
const date3 = parseTimestamp('01/15/2024 10:30:00');

// Explicit format
const date4 = parseTimestamp('15-01-2024', TimestampFormat.DD_MM_YYYY);
```

---

## Redaction Helper

### Purpose

The Redaction Helper module provides security-critical functionality for removing or masking sensitive data before events are published to EventBridge. This ensures PII and other sensitive information is not exposed to downstream consumers that don't require it.

### Module Location

```
src/utils/redaction-helper.ts
```

### Configuration

Redaction rules are configured per table:

```typescript
// config/redaction-rules.ts
export const REDACTION_RULES: RedactionConfig = {
  core_users: {
    remove: ['password_hash', 'security_question', 'security_answer'],
    mask: ['email', 'phone_number', 'ssn'],
    hash: ['external_id']
  },
  core_agents: {
    remove: ['internal_notes'],
    mask: ['personal_email', 'phone'],
    hash: []
  },
  core_calls: {
    remove: ['recording_url'],
    mask: ['caller_phone', 'caller_email'],
    hash: ['customer_id']
  }
};
```

### Core Redaction Functions

#### `redactSensitiveData(tableName: string, payload: Record<string, unknown>): RedactedPayload`

Applies redaction rules based on table configuration.

```typescript
import { redactSensitiveData } from './utils/redaction-helper';

const originalPayload = {
  user_id: 'USR-123',
  email: 'john.doe@example.com',
  phone_number: '+1-555-123-4567',
  password_hash: 'bcrypt$...',
  name: 'John Doe',
  created_at: '2024-01-15T10:30:00Z'
};

const redacted = redactSensitiveData('core_users', originalPayload);

// Result:
// {
//   user_id: 'USR-123',
//   email: 'j***@e***.com',           // Masked
//   phone_number: '+1-555-***-****',   // Masked
//   // password_hash removed entirely
//   name: 'John Doe',
//   created_at: '2024-01-15T10:30:00Z',
//   _redactionApplied: true,
//   _redactedFields: ['email', 'phone_number', 'password_hash']
// }
```

### Masking Strategies

```typescript
import { 
  maskEmail, 
  maskPhone, 
  maskCreditCard,
  maskCustom 
} from './utils/redaction-helper';

// Email masking
maskEmail('john.doe@example.com');  // 'j***@e***.com'

// Phone masking
maskPhone('+1-555-123-4567');       // '+1-555-***-****'

// Credit card masking (last 4 digits visible)
maskCreditCard('4111111111111111'); // '************1111'

// Custom pattern masking
maskCustom('SSN123456789', {
  visibleStart: 3,
  visibleEnd: 0,
  maskChar: 'X'
});  // 'SSNXXXXXXXXX'
```

### Hashing for Correlation

For fields that need to be redacted but still allow correlation across events:

```typescript
import { hashForCorrelation } from './utils/redaction-helper';

const hashedId = hashForCorrelation('customer@example.com');
// Returns consistent hash: 'sha256:a1b2c3d4...'

// Same input always produces same hash
// Different inputs produce different hashes
// Original value cannot be recovered
```

### Conditional Redaction

Apply redaction based on event context:

```typescript
import { conditionalRedact } from './utils/redaction-helper';

const redacted = conditionalRedact(payload, {
  tableName: 'core_calls',
  operation: 'INSERT',
  targetBus: 'wallboards-bus',
  consumerPermissions: ['basic'] // Not 'pii-access'
});
```

### Audit Logging

All redaction operations are logged for compliance:

```typescript
import { RedactionAuditLogger } from './utils/redaction-helper';

const auditLogger = new RedactionAuditLogger({
  tableName: 'redaction_audit',
  retentionDays: 90
});

// Automatically logs:
// - What fields were redacted
// - Which table/record
// - Timestamp
// - Redaction rule applied
```

---

## Async Jobs Utility

### Purpose

The Async Jobs Utility manages long-running operations, retry logic, and job state persistence using DynamoDB. It provides a robust framework for handling operations that may take longer than a single Lambda invocation.

### Module Location

```
src/utils/async-jobs.ts
```

### Job Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PENDING   │────▶│  PROCESSING │────▶│  COMPLETED  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    
                           ▼                    
                    ┌─────────────┐     ┌─────────────┐
                    │   RETRYING  │────▶│   FAILED    │
                    └─────────────┘     └─────────────┘
```

### Creating Jobs

```typescript
import { AsyncJobManager, JobPriority } from './utils/async-jobs';

const jobManager = new AsyncJobManager({
  tableName: 'cdc-pipeline-jobs',
  maxRetries: 3,
  retryBackoffMs: [1000, 5000, 30000] // Exponential backoff
});

// Create a new async job
const job = await jobManager.createJob({
  type: 'BULK_TRANSFORMATION',
  payload: {
    tableName: 'core_agents',
    recordIds: ['AGT-001', 'AGT-002', 'AGT-003'],
    transformationType: 'SCHEMA_MIGRATION'
  },
  priority: JobPriority.HIGH,
  ttlHours: 24
});

console.log(`Created job: ${job.jobId}`);
```

### Processing Jobs

```typescript
import { AsyncJobManager, JobStatus } from './utils/async-jobs';

// Poll and process jobs
export const jobProcessor = async () => {
  const jobManager = new AsyncJobManager({ tableName: 'cdc-pipeline-jobs' });
  
  const pendingJobs = await jobManager.getPendingJobs({
    limit: 10,
    priority: JobPriority.HIGH
  });

  for (const job of pendingJobs) {
    await jobManager.updateStatus(job.jobId, JobStatus.PROCESSING);
    
    try {
      const result = await processJob(job);
      await jobManager.completeJob(job.jobId, result);
    } catch (error) {
      await jobManager.handleJobFailure(job.jobId, error);
    }
  }
};
```

### Retry Logic

```typescript
import { withRetry, RetryConfig } from './utils/async-jobs';

const retryConfig: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 1000,
  maxDelayMs: 30000,
  backoffMultiplier: 2,
  retryableErrors: ['ETIMEDOUT', 'ECONNRESET', 'ThrottlingException']
};

const result = await withRetry(
  () => publishToEventBridge(event),
  retryConfig
);
```

### Job Chaining

```typescript
import { JobChain } from './utils/async-jobs';

const chain = new JobChain('data-migration')
  .addStep('validate', validateDataJob)
  .addStep('transform', transformDataJob)
  .addStep('publish', publishDataJob)
  .onFailure(handleChainFailure)
  .onComplete(handleChainComplete);

await chain.execute(initialPayload);
```

### Dead Letter Queue Integration

```typescript
import { AsyncJobManager } from './utils/async-jobs';

const jobManager = new AsyncJobManager({
  tableName: 'cdc-pipeline-jobs',
  deadLetterQueue: {
    queueUrl: process.env.DLQ_URL,
    sendAfterRetries: 3
  }
});

// Failed jobs are automatically sent to DLQ after max retries
```

---

## Constants Reference

### Module Location

```
src/utils/constants.ts
```

### Table Registry

```typescript
export const TABLE_REGISTRY = {
  CORE_USERS: 'core_users',
  CORE_AGENTS: 'core_agents',
  CORE_CALLS: 'core_calls',
  CORE_QUEUES: 'core_queues',
  CORE_INTERACTIONS: 'core_interactions',
  CORE_CONTACTS: 'core_contacts',
  CORE_CAMPAIGNS: 'core_campaigns',
  CORE_SKILLS: 'core_skills',
  CORE_TEAMS: 'core_teams',
  CORE_SCHEDULES: 'core_schedules',
  CORE_METRICS: 'core_metrics',
  CORE_AUDIT_LOG: 'core_audit_log'
} as const;

export type TableName = typeof TABLE_REGISTRY[keyof typeof TABLE_REGISTRY];
```

### Event Types

```typescript
export const EVENT_TYPES = {
  CDC_INSERT: 'CDC.INSERT',
  CDC_UPDATE: 'CDC.UPDATE',
  CDC_DELETE: 'CDC.DELETE',
  CDC_BATCH: 'CDC.BATCH',
  CDC_ERROR: 'CDC.ERROR'
} as const;

export const EVENT_SOURCES = {
  CDC_PIPELINE: 'cdc-pipeline',
  CDC_PIPELINE_DLQ: 'cdc-pipeline.dlq',
  CDC_PIPELINE_RETRY: 'cdc-pipeline.retry'
} as const;
```

### Error Codes

```typescript
export const ERROR_CODES = {
  // Validation errors (1xxx)
  INVALID_EVENT_FORMAT: 'E1001',
  MISSING_REQUIRED_FIELD: 'E1002',
  INVALID_TABLE_NAME: 'E1003',
  INVALID_OPERATION: 'E1004',
  SCHEMA_VALIDATION_FAILED: 'E1005',

  // Processing errors (2xxx)
  TRANSFORMATION_FAILED: 'E2001',
  REDACTION_FAILED: 'E2002',
  SERIALIZATION_FAILED: 'E2003',
  
  // Publishing errors (3xxx)
  EVENTBRIDGE_PUBLISH_FAILED: 'E3001',
  KINESIS_WRITE_FAILED: 'E3002',
  DYNAMODB_WRITE_FAILED: 'E3003',

  // System errors (4xxx)
  TIMEOUT: 'E4001',
  OUT_OF_MEMORY: 'E4002',
  THROTTLED: 'E4003'
} as const;
```

### Configuration Defaults

```typescript
export const DEFAULTS = {
  BATCH_SIZE: 100,
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
  JOB_TTL_HOURS: 24,
  EVENT_BUS_NAME: 'cdc-events-bus',
  DLQ_RETENTION_DAYS: 14,
  METRICS_NAMESPACE: 'CDC-Pipeline'
} as const;
```

### Environment Variables

```typescript
export const ENV_VARS = {
  // Required
  EVENT_BUS_NAME: process.env.EVENT_BUS_NAME!,
  JOBS_TABLE_NAME: process.env.JOBS_TABLE_NAME!,
  KINESIS_STREAM_ARN: process.env.KINESIS_STREAM_ARN!,

  // Optional with defaults
  LOG_LEVEL: process.env.LOG_LEVEL || 'INFO',
  BATCH_SIZE: parseInt(process.env.BATCH_SIZE || '100'),
  ENABLE_METRICS: process.env.ENABLE_METRICS === 'true'
} as const;
```

---

## Best Practices

### 1. Always Validate Before Processing

```typescript
const result = validateCdcEvent(event);
if (!result.isValid) {
  await logValidationError(result.errors);
  return; // Don't process invalid events
}
```

### 2. Apply Redaction Early

```typescript
// Redact immediately after parsing
const parsed = parseKinesisRecord(record);
const redacted = redactSensitiveData(parsed.tableName, parsed.payload);
// All downstream processing uses redacted data
```

### 3. Use Type Guards for Safety

```typescript
if (isUpdateEvent(event)) {
  // Compiler knows beforeImage and afterImage exist
  const delta = transformDeltaRecord(event.beforeImage, event.afterImage);
}
```

### 4. Implement Proper Error Handling

```typescript
try {
  await processEvent(event);
} catch (error) {
  if (isRetryableError(error)) {
    await jobManager.scheduleRetry(event, error);
  } else {
    await sendToDeadLetterQueue(event, error);
  }
}
```

### 5. Monitor Utility Performance

```typescript
import { metrics } from './utils/metrics';

const start = Date.now();
const result = transformBatchRecords(records);
metrics.recordDuration('transformation.batch', Date.now() - start);
metrics.recordCount('transformation.success', result.successful.length);
metrics.recordCount('transformation.failure', result.failed.length);
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Validation always fails | Schema mismatch | Check TABLE_REGISTRY and schema definitions |
| Redaction not applied | Table not in config | Add table to REDACTION_RULES |
| Jobs stuck in PROCESSING | Lambda timeout | Increase timeout or break into smaller jobs |
| Parse errors | Encoding issues | Use explicit encoding in parser options |

### Debug Mode

Enable debug logging for utilities:

```typescript
import { setDebugMode } from './utils/debug';

setDebugMode({
  validation: true,
  transformation: true,
  redaction: true,
  asyncJobs: true
});
```

This will output detailed logs for each utility operation, helpful for troubleshooting in development environments.