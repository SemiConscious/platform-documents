# Data Models & Types

This document provides comprehensive documentation of all TypeScript interfaces and data structures used in the bedrock-metrics-aggregator service. These models define the shape of data flowing through the system, from S3 event notifications to aggregated metrics output.

## Overview

The bedrock-metrics-aggregator service uses a collection of interconnected data models organized into three main categories:

1. **Event Processing Models** - Handle incoming S3/SNS notifications
2. **Usage & Metrics Models** - Track and aggregate Bedrock invocation data
3. **Configuration Models** - Define inference profile settings
4. **Utility Types** - Error handling and type mappings

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Event Flow & Data Models                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌─────────────────────┐    ┌──────────────────┐   │
│  │  SNSMessage  │───>│ S3NotificationMessage│───>│S3NotificationRecord│  │
│  └──────────────┘    └─────────────────────┘    └────────┬─────────┘   │
│                                                          │              │
│                                                          ▼              │
│                                                 ┌──────────────────┐    │
│                                                 │ ProcessedS3Record│    │
│                                                 └────────┬─────────┘    │
│                                                          │              │
│                                                          ▼              │
│  ┌──────────────────┐                          ┌──────────────────┐    │
│  │ InferenceProfile │<─────────────────────────│ InvocationUsage  │    │
│  └──────────────────┘                          └────────┬─────────┘    │
│                                                          │              │
│                                                          ▼              │
│                           ┌──────────────┐     ┌──────────────────┐    │
│                           │  MetricsMap  │<────│    MetricData    │    │
│                           └──────────────┘     └──────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Event Processing Models

These models handle the ingestion of S3 event notifications delivered through SNS.

### SNSMessage

Wrapper model for SNS messages containing the raw message payload.

#### Purpose

Represents the outer envelope of an SNS notification. The `Message` field contains a JSON-encoded string that must be parsed to extract the actual S3 notification data.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Message` | `string` | Yes | JSON string payload of the SNS message containing S3 notification data |

#### Validation Rules

- `Message` must be a valid JSON string
- When parsed, must conform to `S3NotificationMessage` structure

#### Example

```json
{
  "Message": "{\"Records\":[{\"s3\":{\"bucket\":{\"name\":\"bedrock-invocation-logs\"},\"object\":{\"key\":\"logs/2024/01/15/invocation-001.json\"}},\"awsRegion\":\"us-east-1\"}]}"
}
```

#### Relationships

- Contains serialized `S3NotificationMessage` in the `Message` field

---

### S3NotificationMessage

Container model for S3 notification records received via SNS.

#### Purpose

Represents the parsed content of an SNS message, containing an array of S3 event records. This is the primary entry point for processing S3 events in the Lambda function.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Records` | `S3NotificationRecord[]` | Yes | Array of S3 notification records, typically containing one record per event |

#### Validation Rules

- `Records` array must contain at least one record
- Each record must conform to `S3NotificationRecord` structure

#### Example

```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "bedrock-invocation-logs"
        },
        "object": {
          "key": "logs/2024/01/15/account-123456789012/us-east-1/invocation-abc123.json"
        }
      },
      "awsRegion": "us-east-1"
    }
  ]
}
```

#### Relationships

- Parsed from `SNSMessage.Message`
- Contains array of `S3NotificationRecord`

---

### S3NotificationRecord

Individual record from an S3 event notification containing bucket and object details.

#### Purpose

Represents a single S3 event with full details about the affected bucket and object. This model preserves the nested structure of AWS S3 event notifications.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `s3` | `object` | Yes | S3 event details containing bucket and object information |
| `s3.bucket` | `object` | Yes | S3 bucket information |
| `s3.bucket.name` | `string` | Yes | Name of the S3 bucket containing the invocation log |
| `s3.object` | `object` | Yes | S3 object information |
| `s3.object.key` | `string` | Yes | Key (path) of the S3 object within the bucket |
| `awsRegion` | `string` | Yes | AWS region where the S3 bucket is located |

#### Validation Rules

- `s3.bucket.name` must be a valid S3 bucket name (3-63 characters, lowercase)
- `s3.object.key` must be URL-encoded if containing special characters
- `awsRegion` must be a valid AWS region identifier

#### Example

```json
{
  "s3": {
    "bucket": {
      "name": "bedrock-invocation-logs"
    },
    "object": {
      "key": "logs/2024/01/15/account-123456789012/us-east-1/claude-3-sonnet/invocation-abc123def456.json"
    }
  },
  "awsRegion": "us-east-1"
}
```

#### Relationships

- Contained within `S3NotificationMessage.Records`
- Transformed into `ProcessedS3Record` for downstream processing

---

### ProcessedS3Record

Flattened S3 record after processing from notification.

#### Purpose

Provides a simplified, flattened structure for S3 record data after initial processing. This model removes unnecessary nesting while preserving essential information needed to retrieve the invocation log file.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bucket` | `object` | Yes | S3 bucket information |
| `bucket.name` | `string` | Yes | Name of the S3 bucket |
| `object` | `object` | Yes | S3 object information |
| `object.key` | `string` | Yes | Key of the S3 object |
| `awsRegion` | `string` | Yes | AWS region of the S3 bucket |

#### Validation Rules

- Same validation rules as `S3NotificationRecord`
- Object key should be URL-decoded before use with S3 API

#### Example

```json
{
  "bucket": {
    "name": "bedrock-invocation-logs"
  },
  "object": {
    "key": "logs/2024/01/15/account-123456789012/us-east-1/claude-3-sonnet/invocation-abc123def456.json"
  },
  "awsRegion": "us-east-1"
}
```

#### Relationships

- Transformed from `S3NotificationRecord`
- Used to fetch invocation log files from S3

---

## Usage & Metrics Models

These models track Bedrock model invocations and aggregate usage metrics.

### InvocationUsage

Tracks usage metrics for a single Bedrock model invocation.

#### Purpose

Captures comprehensive details about a single Bedrock API invocation, including token counts, routing information, and metadata. This is the primary data structure extracted from invocation log files.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `modelId` | `string` | Yes | Identifier of the Bedrock model used (e.g., `anthropic.claude-3-sonnet-20240229-v1:0`) |
| `profileName` | `string` | Yes | Name of the inference profile used for routing |
| `inputTokens` | `number` | Yes | Number of input tokens processed in the request |
| `outputTokens` | `number` | Yes | Number of output tokens generated in the response |
| `totalTokens` | `number` | Yes | Total tokens (input + output) for the invocation |
| `sourceRegion` | `string` | Yes | AWS region where the request originated |
| `destinationRegion` | `string` | Yes | AWS region where the model was actually invoked |
| `timestamp` | `string` | Yes | ISO 8601 timestamp of the invocation |
| `consumer` | `string` | Yes | Identifier of the consuming application or service |
| `inferenceType` | `string` | Yes | Type of inference performed (e.g., `ON_DEMAND`, `PROVISIONED`) |

#### Validation Rules

- `inputTokens`, `outputTokens`, `totalTokens` must be non-negative integers
- `totalTokens` should equal `inputTokens + outputTokens`
- `timestamp` must be a valid ISO 8601 date string
- `sourceRegion` and `destinationRegion` must be valid AWS region identifiers

#### Example

```json
{
  "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
  "profileName": "production-claude-sonnet",
  "inputTokens": 1250,
  "outputTokens": 856,
  "totalTokens": 2106,
  "sourceRegion": "us-east-1",
  "destinationRegion": "us-west-2",
  "timestamp": "2024-01-15T14:32:17.456Z",
  "consumer": "customer-service-chatbot",
  "inferenceType": "ON_DEMAND"
}
```

#### Relationships

- References `InferenceProfile` via `profileName`
- Aggregated into `MetricData`

#### Common Use Cases

1. **Per-invocation logging** - Track individual API calls for debugging
2. **Cost attribution** - Associate usage with specific consumers
3. **Cross-region analysis** - Monitor routing patterns between regions

---

### MetricData

Aggregated metric data for token usage and invocation counts.

#### Purpose

Stores aggregated metrics for a group of invocations, typically bucketed by time period, model, or consumer. This compact structure enables efficient storage and querying of usage statistics.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `inputTokens` | `number` | Yes | Total input tokens across all aggregated invocations |
| `outputTokens` | `number` | Yes | Total output tokens across all aggregated invocations |
| `invocations` | `number` | Yes | Total number of invocations in this aggregation |

#### Validation Rules

- All fields must be non-negative integers
- `invocations` must be at least 1 if `inputTokens` or `outputTokens` are non-zero

#### Example

```json
{
  "inputTokens": 45230,
  "outputTokens": 28456,
  "invocations": 127
}
```

#### Relationships

- Aggregated from multiple `InvocationUsage` records
- Stored in `MetricsMap` with dimensional keys

#### Common Use Cases

1. **Hourly/daily summaries** - Aggregate usage over time periods
2. **Per-model metrics** - Track usage by model identifier
3. **Consumer billing** - Calculate total usage per consumer

---

### MetricsMap

Dictionary mapping string keys to MetricData objects.

#### Purpose

Provides a flexible key-value structure for storing aggregated metrics across multiple dimensions. Keys typically encode dimensional information like model ID, consumer, region, or time bucket.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `[key: string]` | `MetricData` | N/A | Dynamic key to MetricData mapping; keys represent aggregation dimensions |

#### Validation Rules

- Keys should follow a consistent naming convention
- Values must conform to `MetricData` structure
- Empty maps are valid

#### Example

```json
{
  "anthropic.claude-3-sonnet-20240229-v1:0|customer-service-chatbot|2024-01-15": {
    "inputTokens": 45230,
    "outputTokens": 28456,
    "invocations": 127
  },
  "anthropic.claude-3-haiku-20240307-v1:0|document-processor|2024-01-15": {
    "inputTokens": 128900,
    "outputTokens": 34200,
    "invocations": 892
  },
  "amazon.titan-text-express-v1|analytics-service|2024-01-15": {
    "inputTokens": 67800,
    "outputTokens": 45600,
    "invocations": 234
  }
}
```

#### Key Naming Conventions

| Pattern | Description | Example |
|---------|-------------|---------|
| `{modelId}\|{consumer}\|{date}` | Daily metrics by model and consumer | `claude-3\|chatbot\|2024-01-15` |
| `{region}\|{hour}` | Hourly regional metrics | `us-east-1\|2024-01-15T14` |
| `{profileName}` | Metrics by inference profile | `production-claude-sonnet` |

#### Relationships

- Contains `MetricData` values
- Populated from aggregated `InvocationUsage` records

---

## Configuration Models

### InferenceProfile

Configuration for a Bedrock inference profile including region settings and optimization options.

#### Purpose

Defines the configuration for routing Bedrock inference requests, including regional deployment settings, caching policies, and performance optimizations. Inference profiles enable sophisticated request routing across multiple regions.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `region` | `string` | Yes | AWS region for the inference profile deployment |
| `profileName` | `string` | Yes | Unique name identifying the inference profile |
| `rmProfileName` | `string` | Yes | Resource management profile name for capacity allocation |
| `cacheMinTokens` | `string` | Yes | Minimum token threshold for prompt caching (as string for configuration flexibility) |
| `optimisedLatency` | `boolean` | Yes | Whether latency optimization is enabled for this profile |
| `inferenceProfileArn` | `string` | Yes | Full ARN of the inference profile resource |
| `merged_profile_map_value` | `string` | Yes | Merged profile mapping value for cross-region routing |

#### Validation Rules

- `region` must be a valid AWS region identifier
- `profileName` must be unique within the account
- `inferenceProfileArn` must be a valid ARN format: `arn:aws:bedrock:{region}:{account}:inference-profile/{name}`
- `cacheMinTokens` must be a numeric string

#### Example

```json
{
  "region": "us-east-1",
  "profileName": "production-claude-sonnet",
  "rmProfileName": "high-throughput-rm",
  "cacheMinTokens": "1024",
  "optimisedLatency": true,
  "inferenceProfileArn": "arn:aws:bedrock:us-east-1:123456789012:inference-profile/production-claude-sonnet",
  "merged_profile_map_value": "us-east-1:production-claude-sonnet,us-west-2:production-claude-sonnet-west"
}
```

#### Relationships

- Referenced by `InvocationUsage.profileName`
- Determines routing behavior for invocations

#### Common Use Cases

1. **Multi-region deployment** - Configure failover between regions
2. **Performance tuning** - Enable latency optimization for time-sensitive workloads
3. **Cost optimization** - Configure caching thresholds to reduce redundant processing

---

## Utility Types

### ErrorCode

Enumeration of error codes for the application.

#### Purpose

Provides standardized error codes for consistent error handling and reporting throughout the application.

#### Fields

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `UNKNOWN` | `string` | Yes | Unknown or unclassified error code |

#### Example

```json
{
  "errorCode": "UNKNOWN",
  "message": "An unexpected error occurred during metrics aggregation"
}
```

#### Usage Pattern

```typescript
// Error handling example
try {
  await processInvocationLog(record);
} catch (error) {
  logger.error({
    errorCode: ErrorCode.UNKNOWN,
    message: error.message,
    stack: error.stack
  });
}
```

---

## Model Relationships Summary

| Source Model | Relationship | Target Model | Description |
|--------------|--------------|--------------|-------------|
| `SNSMessage` | contains (serialized) | `S3NotificationMessage` | Message payload contains JSON string |
| `S3NotificationMessage` | contains | `S3NotificationRecord[]` | Array of event records |
| `S3NotificationRecord` | transforms to | `ProcessedS3Record` | Flattened for processing |
| `InvocationUsage` | references | `InferenceProfile` | Via `profileName` field |
| `InvocationUsage` | aggregates into | `MetricData` | Multiple invocations combine |
| `MetricsMap` | contains | `MetricData` | Key-value storage |

---

## Type Definitions Reference

For TypeScript implementations, the complete type definitions:

```typescript
interface SNSMessage {
  Message: string;
}

interface S3NotificationMessage {
  Records: S3NotificationRecord[];
}

interface S3NotificationRecord {
  s3: {
    bucket: {
      name: string;
    };
    object: {
      key: string;
    };
  };
  awsRegion: string;
}

interface ProcessedS3Record {
  bucket: {
    name: string;
  };
  object: {
    key: string;
  };
  awsRegion: string;
}

interface InvocationUsage {
  modelId: string;
  profileName: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  sourceRegion: string;
  destinationRegion: string;
  timestamp: string;
  consumer: string;
  inferenceType: string;
}

interface MetricData {
  inputTokens: number;
  outputTokens: number;
  invocations: number;
}

interface MetricsMap {
  [key: string]: MetricData;
}

interface InferenceProfile {
  region: string;
  profileName: string;
  rmProfileName: string;
  cacheMinTokens: string;
  optimisedLatency: boolean;
  inferenceProfileArn: string;
  merged_profile_map_value: string;
}

enum ErrorCode {
  UNKNOWN = 'UNKNOWN'
}
```