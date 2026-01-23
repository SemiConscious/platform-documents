# Architecture & Data Flow

## System Overview

The bedrock-metrics-aggregator is an event-driven AWS Lambda function designed to process, aggregate, and publish usage metrics for Amazon Bedrock inference profiles across multiple AWS regions. This service operates as a critical component in a serverless data pipeline that transforms raw Bedrock invocation logs into actionable CloudWatch metrics.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Bedrock Metrics Aggregator Pipeline                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌────────────┐ │
│  │   Amazon     │───▶│   Amazon     │───▶│     Lambda       │───▶│ CloudWatch │ │
│  │     S3       │    │     SQS      │    │   (Aggregator)   │    │  Metrics   │ │
│  │  (Logs)      │    │   (Queue)    │    │                  │    │            │ │
│  └──────────────┘    └──────────────┘    └──────────────────┘    └────────────┘ │
│        │                    │                     │                      │       │
│        │                    │                     │                      │       │
│    S3 Event             Message              Process &              Publish      │
│  Notification           Batching            Aggregate               Metrics      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Design Principles

The architecture follows several key design principles:

1. **Event-Driven Processing**: The Lambda function is triggered by SQS messages, enabling asynchronous, decoupled processing of log files
2. **Scalability**: SQS batching and Lambda concurrency allow the system to handle varying workloads
3. **Fault Tolerance**: Built-in retry mechanisms and dead-letter queue support ensure message processing reliability
4. **Cross-Region Aggregation**: Designed to consolidate metrics from multiple AWS regions into unified views

### Core Components

| Component | Purpose | AWS Service |
|-----------|---------|-------------|
| Log Storage | Stores raw Bedrock invocation logs | Amazon S3 |
| Event Queue | Buffers and delivers S3 event notifications | Amazon SQS |
| Processor | Aggregates metrics and transforms data | AWS Lambda |
| Metrics Store | Stores aggregated custom metrics | Amazon CloudWatch |

---

## Event Flow

The data flow through the bedrock-metrics-aggregator follows a well-defined sequence of operations, from log generation to metric publication.

### Complete Event Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Event Lifecycle                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. LOG GENERATION                                                               │
│     ┌───────────────┐                                                           │
│     │ Bedrock API   │──────▶ Invocation logs written to S3                      │
│     │ Invocations   │                                                           │
│     └───────────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│  2. EVENT NOTIFICATION                                                          │
│     ┌───────────────┐                                                           │
│     │ S3 Event      │──────▶ ObjectCreated event sent to SQS                    │
│     │ Notification  │                                                           │
│     └───────────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│  3. MESSAGE DELIVERY                                                            │
│     ┌───────────────┐                                                           │
│     │ SQS Queue     │──────▶ Batched messages delivered to Lambda               │
│     │ (Batching)    │                                                           │
│     └───────────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│  4. LAMBDA PROCESSING                                                           │
│     ┌───────────────┐                                                           │
│     │ Parse S3      │──────▶ Extract bucket/key from SQS message                │
│     │ Event Info    │                                                           │
│     └───────────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│  5. LOG RETRIEVAL                                                               │
│     ┌───────────────┐                                                           │
│     │ Fetch Log     │──────▶ Download and decompress log file from S3           │
│     │ from S3       │                                                           │
│     └───────────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│  6. METRICS AGGREGATION                                                         │
│     ┌───────────────┐                                                           │
│     │ Aggregate     │──────▶ Sum tokens by inference profile type               │
│     │ Token Usage   │                                                           │
│     └───────────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│  7. METRIC PUBLISHING                                                           │
│     ┌───────────────┐                                                           │
│     │ Publish to    │──────▶ Custom metrics sent to CloudWatch                  │
│     │ CloudWatch    │                                                           │
│     └───────────────┘                                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Event Message Structure

When an S3 event notification arrives via SQS, the Lambda function receives a message with the following structure:

```json
{
  "Records": [
    {
      "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
      "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
      "body": "{\"Records\":[{\"s3\":{\"bucket\":{\"name\":\"bedrock-logs-bucket\"},\"object\":{\"key\":\"logs/2024/01/15/invocation-log.json.gz\"}}}]}",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1545082649183"
      },
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:bedrock-logs-queue"
    }
  ]
}
```

---

## S3 Notification Processing

The S3 notification processing stage is the entry point for the Lambda function, responsible for extracting relevant information from incoming events and retrieving log files.

### S3 Event Notification Configuration

The S3 bucket must be configured to send notifications to the SQS queue for object creation events:

```yaml
# CloudFormation/SAM Template Example
Resources:
  BedrockLogsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: bedrock-logs-bucket
      NotificationConfiguration:
        QueueConfigurations:
          - Event: 's3:ObjectCreated:*'
            Queue: !GetAtt LogsQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: logs/
                  - Name: suffix
                    Value: .json.gz
```

### Processing Logic

```typescript
// TypeScript implementation for S3 event processing
interface S3EventRecord {
  s3: {
    bucket: {
      name: string;
    };
    object: {
      key: string;
      size: number;
    };
  };
}

async function processS3Event(sqsRecord: SQSRecord): Promise<ProcessingResult> {
  // Parse the nested S3 event from SQS message body
  const s3Event = JSON.parse(sqsRecord.body);
  
  const results: ProcessingResult[] = [];
  
  for (const record of s3Event.Records as S3EventRecord[]) {
    const bucketName = record.s3.bucket.name;
    const objectKey = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));
    
    // Validate the object key matches expected pattern
    if (!isValidLogPath(objectKey)) {
      console.warn(`Skipping invalid log path: ${objectKey}`);
      continue;
    }
    
    // Fetch and decompress the log file
    const logContent = await fetchAndDecompressLog(bucketName, objectKey);
    
    // Parse the log entries
    const logEntries = parseLogEntries(logContent);
    
    results.push({
      bucket: bucketName,
      key: objectKey,
      entries: logEntries
    });
  }
  
  return aggregateResults(results);
}
```

### Log File Format

Bedrock invocation logs stored in S3 follow a specific JSON structure:

```json
{
  "schemaType": "ModelInvocationLog",
  "schemaVersion": "1.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "accountId": "123456789012",
  "region": "us-east-1",
  "requestId": "abc123-def456-ghi789",
  "operation": "InvokeModel",
  "modelId": "arn:aws:bedrock:us-east-1:123456789012:inference-profile/cross-region-profile",
  "input": {
    "inputTokenCount": 150
  },
  "output": {
    "outputTokenCount": 500
  }
}
```

---

## Metrics Aggregation Logic

The metrics aggregation component is the core processing engine that transforms raw log entries into meaningful, aggregated metrics based on inference profile types.

### Inference Profile Detection

The aggregator identifies and categorizes Bedrock inference profiles into three types:

| Profile Type | Pattern | Description |
|--------------|---------|-------------|
| CrossRegion | Contains `cross-region` in ARN | Regional cross-region routing |
| GlobalCrossRegion | Contains `global-cross-region` in ARN | Global cross-region routing |
| Standard | Neither pattern present | Direct model invocation |

```typescript
// Inference profile type detection
enum InferenceProfileType {
  CROSS_REGION = 'CrossRegion',
  GLOBAL_CROSS_REGION = 'GlobalCrossRegion',
  STANDARD = 'Standard'
}

function detectInferenceProfileType(modelId: string): InferenceProfileType {
  if (modelId.includes('global-cross-region')) {
    return InferenceProfileType.GLOBAL_CROSS_REGION;
  } else if (modelId.includes('cross-region')) {
    return InferenceProfileType.CROSS_REGION;
  }
  return InferenceProfileType.STANDARD;
}
```

### Token Aggregation Algorithm

```typescript
// Token aggregation data structure
interface AggregatedMetrics {
  profileType: InferenceProfileType;
  modelId: string;
  region: string;
  inputTokens: number;
  outputTokens: number;
  invocationCount: number;
  timestamp: Date;
}

class MetricsAggregator {
  private metricsMap: Map<string, AggregatedMetrics> = new Map();
  
  aggregateLogEntry(entry: BedrockLogEntry): void {
    const profileType = detectInferenceProfileType(entry.modelId);
    const aggregationKey = this.buildAggregationKey(entry, profileType);
    
    const existing = this.metricsMap.get(aggregationKey);
    
    if (existing) {
      existing.inputTokens += entry.input.inputTokenCount;
      existing.outputTokens += entry.output.outputTokenCount;
      existing.invocationCount += 1;
    } else {
      this.metricsMap.set(aggregationKey, {
        profileType,
        modelId: entry.modelId,
        region: entry.region,
        inputTokens: entry.input.inputTokenCount,
        outputTokens: entry.output.outputTokenCount,
        invocationCount: 1,
        timestamp: new Date(entry.timestamp)
      });
    }
  }
  
  private buildAggregationKey(
    entry: BedrockLogEntry, 
    profileType: InferenceProfileType
  ): string {
    // Aggregate by profile type, model, and hourly bucket
    const hourBucket = new Date(entry.timestamp);
    hourBucket.setMinutes(0, 0, 0);
    
    return `${profileType}|${entry.modelId}|${hourBucket.toISOString()}`;
  }
  
  getAggregatedMetrics(): AggregatedMetrics[] {
    return Array.from(this.metricsMap.values());
  }
}
```

### Aggregation Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Metrics Aggregation Flow                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Raw Log Entries                                                               │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ Entry 1: CrossRegion, Model A, Input: 100, Output: 200                  │   │
│   │ Entry 2: CrossRegion, Model A, Input: 150, Output: 300                  │   │
│   │ Entry 3: GlobalCrossRegion, Model B, Input: 200, Output: 400            │   │
│   │ Entry 4: CrossRegion, Model A, Input: 50, Output: 100                   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                            │
│                                     ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         AGGREGATION ENGINE                               │   │
│   │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                │   │
│   │  │ Group by      │──│ Group by      │──│ Sum Token     │                │   │
│   │  │ Profile Type  │  │ Model ID      │  │ Counts        │                │   │
│   │  └───────────────┘  └───────────────┘  └───────────────┘                │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                            │
│                                     ▼                                            │
│   Aggregated Metrics                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ CrossRegion, Model A: Input: 300, Output: 600, Count: 3                 │   │
│   │ GlobalCrossRegion, Model B: Input: 200, Output: 400, Count: 1           │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## CloudWatch Publishing

The CloudWatch publishing component transforms aggregated metrics into CloudWatch custom metrics with appropriate dimensions and units.

### Metric Namespace and Dimensions

| Metric Name | Unit | Dimensions |
|-------------|------|------------|
| InputTokenCount | Count | ProfileType, ModelId, Region |
| OutputTokenCount | Count | ProfileType, ModelId, Region |
| TotalTokenCount | Count | ProfileType, ModelId, Region |
| InvocationCount | Count | ProfileType, ModelId, Region |

### Publishing Implementation

```typescript
import { 
  CloudWatchClient, 
  PutMetricDataCommand,
  MetricDatum 
} from '@aws-sdk/client-cloudwatch';

const NAMESPACE = 'BedrockMetrics/InferenceProfiles';
const MAX_METRICS_PER_REQUEST = 1000;

class CloudWatchPublisher {
  private client: CloudWatchClient;
  
  constructor(region: string) {
    this.client = new CloudWatchClient({ region });
  }
  
  async publishMetrics(aggregatedMetrics: AggregatedMetrics[]): Promise<void> {
    const metricData: MetricDatum[] = [];
    
    for (const metrics of aggregatedMetrics) {
      const dimensions = [
        { Name: 'ProfileType', Value: metrics.profileType },
        { Name: 'ModelId', Value: this.extractModelName(metrics.modelId) },
        { Name: 'Region', Value: metrics.region }
      ];
      
      // Input tokens metric
      metricData.push({
        MetricName: 'InputTokenCount',
        Value: metrics.inputTokens,
        Unit: 'Count',
        Timestamp: metrics.timestamp,
        Dimensions: dimensions
      });
      
      // Output tokens metric
      metricData.push({
        MetricName: 'OutputTokenCount',
        Value: metrics.outputTokens,
        Unit: 'Count',
        Timestamp: metrics.timestamp,
        Dimensions: dimensions
      });
      
      // Total tokens metric
      metricData.push({
        MetricName: 'TotalTokenCount',
        Value: metrics.inputTokens + metrics.outputTokens,
        Unit: 'Count',
        Timestamp: metrics.timestamp,
        Dimensions: dimensions
      });
      
      // Invocation count metric
      metricData.push({
        MetricName: 'InvocationCount',
        Value: metrics.invocationCount,
        Unit: 'Count',
        Timestamp: metrics.timestamp,
        Dimensions: dimensions
      });
    }
    
    // Batch publish in chunks of 1000
    await this.batchPublish(metricData);
  }
  
  private async batchPublish(metricData: MetricDatum[]): Promise<void> {
    for (let i = 0; i < metricData.length; i += MAX_METRICS_PER_REQUEST) {
      const batch = metricData.slice(i, i + MAX_METRICS_PER_REQUEST);
      
      const command = new PutMetricDataCommand({
        Namespace: NAMESPACE,
        MetricData: batch
      });
      
      await this.client.send(command);
      
      console.log(`Published ${batch.length} metrics to CloudWatch`);
    }
  }
  
  private extractModelName(modelId: string): string {
    // Extract friendly model name from ARN
    const match = modelId.match(/inference-profile\/(.+)$/);
    return match ? match[1] : modelId;
  }
}
```

### CloudWatch Metrics Dashboard Example

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Token Usage by Profile Type",
        "metrics": [
          ["BedrockMetrics/InferenceProfiles", "TotalTokenCount", "ProfileType", "CrossRegion"],
          [".", ".", ".", "GlobalCrossRegion"]
        ],
        "period": 3600,
        "stat": "Sum"
      }
    }
  ]
}
```

---

## AWS Service Dependencies

The bedrock-metrics-aggregator relies on several AWS services, each requiring specific IAM permissions and configurations.

### Service Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AWS Service Dependencies                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           LAMBDA FUNCTION                                 │   │
│  │                    (bedrock-metrics-aggregator)                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│              │              │              │              │                      │
│              ▼              ▼              ▼              ▼                      │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐   │
│  │   Amazon S3    │ │  Amazon SQS    │ │  CloudWatch    │ │  CloudWatch    │   │
│  │   (GetObject)  │ │  (Receive/     │ │  (PutMetric    │ │  Logs          │   │
│  │                │ │   Delete)      │ │   Data)        │ │  (Logging)     │   │
│  └────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Required IAM Permissions

```yaml
# IAM Policy for Lambda execution role
Statement:
  # S3 permissions for reading log files
  - Effect: Allow
    Action:
      - s3:GetObject
      - s3:GetObjectVersion
    Resource: 
      - arn:aws:s3:::bedrock-logs-bucket/logs/*
  
  # SQS permissions for message processing
  - Effect: Allow
    Action:
      - sqs:ReceiveMessage
      - sqs:DeleteMessage
      - sqs:GetQueueAttributes
    Resource:
      - arn:aws:sqs:*:*:bedrock-logs-queue
  
  # CloudWatch Metrics permissions
  - Effect: Allow
    Action:
      - cloudwatch:PutMetricData
    Resource: '*'
    Condition:
      StringEquals:
        cloudwatch:namespace: BedrockMetrics/InferenceProfiles
  
  # CloudWatch Logs permissions
  - Effect: Allow
    Action:
      - logs:CreateLogGroup
      - logs:CreateLogStream
      - logs:PutLogEvents
    Resource:
      - arn:aws:logs:*:*:log-group:/aws/lambda/bedrock-metrics-aggregator*
```

### Service Configuration Requirements

| Service | Configuration | Value |
|---------|--------------|-------|
| Lambda | Timeout | 300 seconds (recommended) |
| Lambda | Memory | 512 MB minimum |
| SQS | Visibility Timeout | 360 seconds |
| SQS | Batch Size | 10 messages |
| S3 | Event Types | s3:ObjectCreated:* |

---

## Error Handling Strategy

Robust error handling is critical for maintaining data integrity and ensuring reliable metric publishing.

### Error Categories and Handling

```typescript
// Error handling implementation
enum ErrorType {
  S3_ACCESS_ERROR = 'S3_ACCESS_ERROR',
  PARSE_ERROR = 'PARSE_ERROR',
  CLOUDWATCH_PUBLISH_ERROR = 'CLOUDWATCH_PUBLISH_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR'
}

class MetricsProcessingError extends Error {
  constructor(
    public type: ErrorType,
    message: string,
    public retryable: boolean,
    public context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'MetricsProcessingError';
  }
}

async function processWithErrorHandling(
  sqsEvent: SQSEvent
): Promise<SQSBatchResponse> {
  const batchItemFailures: SQSBatchItemFailure[] = [];
  
  for (const record of sqsEvent.Records) {
    try {
      await processRecord(record);
    } catch (error) {
      if (error instanceof MetricsProcessingError) {
        console.error({
          errorType: error.type,
          message: error.message,
          retryable: error.retryable,
          context: error.context,
          messageId: record.messageId
        });
        
        // Only add to failures if retryable
        if (error.retryable) {
          batchItemFailures.push({
            itemIdentifier: record.messageId
          });
        }
      } else {
        // Unexpected errors are retryable
        console.error('Unexpected error:', error);
        batchItemFailures.push({
          itemIdentifier: record.messageId
        });
      }
    }
  }
  
  return { batchItemFailures };
}
```

### Retry Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Retry Strategy                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐                                                            │
│  │  SQS Message    │                                                            │
│  │  Received       │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│           ▼                                                                      │
│  ┌─────────────────┐     Success     ┌─────────────────┐                       │
│  │  Process        │────────────────▶│  Delete from    │                       │
│  │  Message        │                 │  Queue          │                       │
│  └────────┬────────┘                 └─────────────────┘                       │
│           │                                                                      │
│           │ Failure                                                              │
│           ▼                                                                      │
│  ┌─────────────────┐                                                            │
│  │  Retryable?     │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│      ┌────┴────┐                                                                │
│      │         │                                                                 │
│     Yes        No                                                                │
│      │         │                                                                 │
│      ▼         ▼                                                                 │
│  ┌─────────┐ ┌─────────────────┐                                                │
│  │ Return  │ │ Log Error &     │                                                │
│  │ to Queue│ │ Remove from     │                                                │
│  │ (Retry) │ │ Queue           │                                                │
│  └────┬────┘ └─────────────────┘                                                │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────────┐                                                            │
│  │  Max Retries    │                                                            │
│  │  Exceeded?      │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│          Yes                                                                     │
│           │                                                                      │
│           ▼                                                                      │
│  ┌─────────────────┐                                                            │
│  │  Move to DLQ    │                                                            │
│  └─────────────────┘                                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Dead Letter Queue Configuration

```yaml
# SQS Queue with DLQ configuration
Resources:
  LogsQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: bedrock-logs-queue
      VisibilityTimeout: 360
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt LogsDLQ.Arn
        maxReceiveCount: 3
  
  LogsDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: bedrock-logs-dlq
      MessageRetentionPeriod: 1209600  # 14 days
```

### Monitoring and Alerting

Configure CloudWatch Alarms for operational visibility:

```typescript
// Key metrics to monitor
const monitoringMetrics = [
  {
    name: 'ApproximateNumberOfMessagesVisible',
    threshold: 1000,
    description: 'Queue backlog alert'
  },
  {
    name: 'ApproximateAgeOfOldestMessage',
    threshold: 3600, // 1 hour
    description: 'Processing lag alert'
  },
  {
    name: 'NumberOfMessagesReceived',
    threshold: 0,
    comparison: 'LessThanThreshold',
    description: 'No messages being processed'
  }
];
```

### Best Practices Summary

1. **Partial Batch Failure Handling**: Use `SQSBatchResponse` to report individual message failures without failing the entire batch
2. **Idempotency**: Design processing to be idempotent, allowing safe retries
3. **Structured Logging**: Include correlation IDs and context in all log entries
4. **Graceful Degradation**: Continue processing valid records even when some fail
5. **DLQ Monitoring**: Set up alerts on DLQ message count for manual intervention

---

This architecture provides a scalable, fault-tolerant solution for aggregating Bedrock metrics across regions, enabling comprehensive visibility into inference profile usage patterns.