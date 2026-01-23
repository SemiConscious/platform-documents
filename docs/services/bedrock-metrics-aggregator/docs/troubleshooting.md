# Troubleshooting Guide

## Bedrock Metrics Aggregator Service

### Overview

This troubleshooting guide provides comprehensive information for diagnosing and resolving issues with the bedrock-metrics-aggregator Lambda function. The service processes Bedrock invocation logs from S3, aggregates cross-region usage metrics for inference profiles, and publishes custom metrics to CloudWatch. Due to its event-driven architecture involving S3, SQS, and CloudWatch, issues can arise at multiple integration points.

This guide covers common issues, error code references, debugging strategies, and step-by-step resolution procedures to help developers and operators quickly identify and resolve problems.

---

## Common Issues

### 1. Lambda Function Not Triggering

**Symptoms:**
- No CloudWatch logs appearing for the Lambda function
- Metrics not being published despite new log files in S3
- SQS queue depth increasing without processing

**Possible Causes:**
- SQS trigger not properly configured on the Lambda function
- Lambda function is disabled or has incorrect permissions
- Event source mapping is paused or has errors
- Concurrency limits reached

**Resolution Steps:**

```bash
# Check if the event source mapping is active
aws lambda list-event-source-mappings \
  --function-name bedrock-metrics-aggregator \
  --query 'EventSourceMappings[*].[UUID,State,EventSourceArn]'

# If paused, enable the event source mapping
aws lambda update-event-source-mapping \
  --uuid <mapping-uuid> \
  --enabled
```

### 2. Incomplete Metrics Data

**Symptoms:**
- CloudWatch metrics show intermittent gaps
- Token counts appear lower than expected
- Some inference profiles missing from aggregated data

**Possible Causes:**
- Malformed log entries being skipped
- Filtering logic excluding valid cross-region invocations
- S3 object processing failures for specific files

**Resolution Steps:**
1. Enable debug logging to identify skipped records
2. Verify log format matches expected schema
3. Check for inference profile ID patterns in source logs

### 3. High Lambda Duration/Timeouts

**Symptoms:**
- Lambda function timing out (default 15 minutes max)
- Increased SQS message visibility timeout errors
- Partial processing of large log files

**Possible Causes:**
- Extremely large S3 log files
- Network latency to S3 or CloudWatch
- Inefficient parsing of log data

**Resolution Steps:**

```javascript
// Verify Lambda timeout configuration
const lambdaConfig = {
  timeout: 300, // 5 minutes recommended
  memorySize: 512, // Increase for faster processing
  reservedConcurrency: 10 // Prevent thundering herd
};
```

### 4. Duplicate Metrics Published

**Symptoms:**
- Metric values appear doubled or multiplied
- SUM aggregations show inflated numbers
- Same timestamp data points appearing multiple times

**Possible Causes:**
- SQS message reprocessing due to visibility timeout
- Lambda retries on partial failures
- S3 event notifications sent multiple times

---

## Error Codes Reference

| Error Code | Description | Severity | Common Cause |
|------------|-------------|----------|--------------|
| `BMAS-001` | S3 Object Not Found | ERROR | S3 object deleted before processing or invalid key |
| `BMAS-002` | S3 Access Denied | CRITICAL | IAM permissions insufficient for bucket access |
| `BMAS-003` | Invalid Log Format | WARN | Log file doesn't match expected Bedrock format |
| `BMAS-004` | CloudWatch Publish Failed | ERROR | CloudWatch API throttling or permission issues |
| `BMAS-005` | SQS Message Parse Error | WARN | Malformed SQS event structure |
| `BMAS-006` | Inference Profile Not Found | INFO | Log entry doesn't contain cross-region profile |
| `BMAS-007` | Token Count Invalid | WARN | Non-numeric or negative token values in log |
| `BMAS-008` | Region Detection Failed | ERROR | Unable to determine source region from profile ARN |
| `BMAS-009` | Metric Dimension Overflow | ERROR | Too many unique dimensions (>30) in single request |
| `BMAS-010` | Memory Limit Exceeded | CRITICAL | Log file too large for allocated Lambda memory |

### Error Code Details

#### BMAS-001: S3 Object Not Found

```json
{
  "errorCode": "BMAS-001",
  "message": "S3 object not found",
  "details": {
    "bucket": "bedrock-logs-bucket",
    "key": "logs/2024/01/15/invocation-log.json.gz",
    "requestId": "ABC123DEF456"
  }
}
```

**Resolution:** Verify the S3 object exists and hasn't been moved by lifecycle policies. Check if the SQS message contains stale references.

#### BMAS-004: CloudWatch Publish Failed

```json
{
  "errorCode": "BMAS-004",
  "message": "Failed to publish metrics to CloudWatch",
  "details": {
    "namespace": "Bedrock/CrossRegionMetrics",
    "errorType": "ThrottlingException",
    "retryAttempts": 3
  }
}
```

**Resolution:** Implement exponential backoff, batch metric submissions, or request a CloudWatch API quota increase.

---

## Debugging Steps

### Step 1: Enable Enhanced Logging

Configure the Lambda function environment variable to enable debug-level logging:

```bash
aws lambda update-function-configuration \
  --function-name bedrock-metrics-aggregator \
  --environment "Variables={LOG_LEVEL=DEBUG,ENABLE_TRACE=true}"
```

### Step 2: Trace a Single Message

To trace a specific S3 event through the pipeline:

```python
# Python debugging script for local testing
import json
import boto3

def trace_s3_event(bucket, key):
    """
    Trace processing of a specific S3 object
    """
    s3_client = boto3.client('s3')
    
    # Fetch the object
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        print(f"✓ S3 Object retrieved: {len(content)} bytes")
    except s3_client.exceptions.NoSuchKey:
        print(f"✗ Error BMAS-001: Object not found")
        return
    except s3_client.exceptions.AccessDenied:
        print(f"✗ Error BMAS-002: Access denied")
        return
    
    # Parse the log content
    try:
        logs = json.loads(content)
        print(f"✓ Parsed {len(logs)} log entries")
    except json.JSONDecodeError as e:
        print(f"✗ Error BMAS-003: Invalid format - {e}")
        return
    
    # Check for cross-region inference profiles
    cross_region_count = 0
    for entry in logs:
        if is_cross_region_profile(entry.get('inferenceProfileArn', '')):
            cross_region_count += 1
    
    print(f"✓ Found {cross_region_count} cross-region invocations")

def is_cross_region_profile(arn):
    """Check if ARN indicates cross-region inference profile"""
    return 'CrossRegion' in arn or 'GlobalCrossRegion' in arn
```

### Step 3: Validate SQS Message Format

```javascript
// Node.js validation for SQS message structure
const validateSQSEvent = (event) => {
  const errors = [];
  
  if (!event.Records || !Array.isArray(event.Records)) {
    errors.push('BMAS-005: Missing Records array');
    return errors;
  }
  
  event.Records.forEach((record, index) => {
    try {
      const body = JSON.parse(record.body);
      
      // S3 event notification structure
      if (!body.Records || !body.Records[0].s3) {
        errors.push(`BMAS-005: Record ${index} missing S3 event data`);
      }
      
      const s3Event = body.Records[0].s3;
      if (!s3Event.bucket?.name || !s3Event.object?.key) {
        errors.push(`BMAS-005: Record ${index} missing bucket/key`);
      }
    } catch (e) {
      errors.push(`BMAS-005: Record ${index} JSON parse failed`);
    }
  });
  
  return errors;
};
```

### Step 4: Test CloudWatch Connectivity

```bash
# Test CloudWatch metrics publishing permissions
aws cloudwatch put-metric-data \
  --namespace "Bedrock/CrossRegionMetrics/Test" \
  --metric-name "TestMetric" \
  --value 1 \
  --unit Count \
  --dimensions InferenceProfile=test-profile
```

---

## Log Analysis

### CloudWatch Logs Insights Queries

#### Find All Errors in Last 24 Hours

```sql
fields @timestamp, @message, errorCode
| filter @message like /BMAS-0/
| sort @timestamp desc
| limit 100
```

#### Analyze Processing Duration

```sql
fields @timestamp, @duration, @memorySize, @maxMemoryUsed
| filter @type = "REPORT"
| stats avg(@duration) as avgDuration, 
        max(@duration) as maxDuration,
        avg(@maxMemoryUsed/@memorySize*100) as avgMemoryPercent
  by bin(1h)
```

#### Track Token Aggregation

```sql
fields @timestamp, inputTokens, outputTokens, inferenceProfile
| filter @message like /aggregated/
| stats sum(inputTokens) as totalInput, 
        sum(outputTokens) as totalOutput
  by inferenceProfile, bin(1h)
```

#### Identify Failed S3 Objects

```sql
fields @timestamp, bucket, key, errorCode
| filter errorCode in ['BMAS-001', 'BMAS-002', 'BMAS-003']
| sort @timestamp desc
| limit 50
```

### Log Format Reference

The Lambda function produces structured JSON logs:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "requestId": "abc-123-def-456",
  "component": "S3Processor",
  "message": "Processing complete",
  "metrics": {
    "recordsProcessed": 150,
    "crossRegionInvocations": 45,
    "inputTokensAggregated": 125000,
    "outputTokensAggregated": 87500,
    "processingTimeMs": 2340
  }
}
```

---

## S3 Permission Issues

### Required IAM Permissions

The Lambda execution role must have the following S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectTagging"
      ],
      "Resource": [
        "arn:aws:s3:::bedrock-logs-bucket/*",
        "arn:aws:s3:::bedrock-logs-bucket"
      ]
    },
    {
      "Sid": "S3ListAccess",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::bedrock-logs-bucket"
    }
  ]
}
```

### Diagnosing S3 Access Issues

```bash
# Check if the Lambda role can access the bucket
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/bedrock-metrics-aggregator-role \
  --role-session-name test-session

# Using the assumed role credentials, test S3 access
aws s3api head-object \
  --bucket bedrock-logs-bucket \
  --key logs/2024/01/15/sample-log.json.gz
```

### Common S3 Permission Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `AccessDenied` | Missing `s3:GetObject` permission | Add GetObject to IAM policy |
| `AccessDenied` (KMS) | S3 bucket uses KMS encryption | Add `kms:Decrypt` permission |
| `NoSuchBucket` | Bucket doesn't exist or wrong region | Verify bucket name and region |
| `InvalidAccessKeyId` | Role credentials expired | Check Lambda execution role |

### Cross-Account S3 Access

If logs are stored in a different AWS account:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CrossAccountAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::LAMBDA_ACCOUNT_ID:role/bedrock-metrics-aggregator-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::bedrock-logs-bucket/*"
    }
  ]
}
```

---

## SQS Configuration Problems

### Queue Configuration Requirements

```yaml
# Recommended SQS queue settings
QueueAttributes:
  VisibilityTimeout: 900        # 6x Lambda timeout
  MessageRetentionPeriod: 1209600  # 14 days
  MaximumMessageSize: 262144    # 256 KB
  ReceiveMessageWaitTimeSeconds: 20  # Long polling
  
# Dead Letter Queue configuration
RedrivePolicy:
  deadLetterTargetArn: arn:aws:sqs:us-east-1:123456789012:bedrock-metrics-dlq
  maxReceiveCount: 3
```

### Diagnosing SQS Issues

#### Check Queue Metrics

```bash
# Get queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-metrics-queue \
  --attribute-names All
```

#### Monitor Dead Letter Queue

```bash
# Check DLQ message count
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-metrics-dlq \
  --attribute-names ApproximateNumberOfMessages
```

#### Reprocess DLQ Messages

```javascript
// Node.js script to reprocess DLQ messages
const AWS = require('aws-sdk');
const sqs = new AWS.SQS();

const reprocessDLQ = async () => {
  const dlqUrl = 'https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-metrics-dlq';
  const mainQueueUrl = 'https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-metrics-queue';
  
  let processedCount = 0;
  
  while (true) {
    const response = await sqs.receiveMessage({
      QueueUrl: dlqUrl,
      MaxNumberOfMessages: 10,
      WaitTimeSeconds: 5
    }).promise();
    
    if (!response.Messages || response.Messages.length === 0) {
      break;
    }
    
    for (const message of response.Messages) {
      // Send to main queue
      await sqs.sendMessage({
        QueueUrl: mainQueueUrl,
        MessageBody: message.Body
      }).promise();
      
      // Delete from DLQ
      await sqs.deleteMessage({
        QueueUrl: dlqUrl,
        ReceiptHandle: message.ReceiptHandle
      }).promise();
      
      processedCount++;
    }
  }
  
  console.log(`Reprocessed ${processedCount} messages`);
};
```

### SQS Permission Requirements

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SQSAccess",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:bedrock-metrics-queue"
    }
  ]
}
```

---

## CloudWatch Publishing Failures

### Required CloudWatch Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "Bedrock/CrossRegionMetrics"
        }
      }
    }
  ]
}
```

### Handling Throttling

CloudWatch has limits on PutMetricData API calls (150 transactions per second per account per region). Implement batching and backoff:

```javascript
const AWS = require('aws-sdk');
const cloudwatch = new AWS.CloudWatch();

const publishMetricsWithBackoff = async (metricData, maxRetries = 5) => {
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      // Batch metrics (max 1000 per request, 150 TPS)
      const batches = chunkArray(metricData, 20); // 20 metrics per batch
      
      for (const batch of batches) {
        await cloudwatch.putMetricData({
          Namespace: 'Bedrock/CrossRegionMetrics',
          MetricData: batch
        }).promise();
        
        // Rate limiting delay
        await sleep(10);
      }
      
      return { success: true };
    } catch (error) {
      if (error.code === 'Throttling') {
        const delay = Math.pow(2, retries) * 100;
        console.warn(`Throttled, retrying in ${delay}ms`);
        await sleep(delay);
        retries++;
      } else {
        throw error;
      }
    }
  }
  
  throw new Error('BMAS-004: Max retries exceeded for CloudWatch publishing');
};

const chunkArray = (array, size) => {
  const chunks = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
```

### Metric Dimension Best Practices

CloudWatch has limits on dimensions:
- Maximum 30 dimensions per metric
- Dimension names/values max 255 characters

```javascript
const createMetricDimensions = (invocation) => {
  // Keep dimensions concise to avoid BMAS-009
  const dimensions = [
    {
      Name: 'InferenceProfileType',
      Value: invocation.profileType // CrossRegion or GlobalCrossRegion
    },
    {
      Name: 'ModelId',
      Value: truncate(invocation.modelId, 255)
    },
    {
      Name: 'SourceRegion',
      Value: invocation.sourceRegion
    }
  ];
  
  // Add optional dimensions carefully
  if (invocation.applicationId) {
    dimensions.push({
      Name: 'ApplicationId',
      Value: truncate(invocation.applicationId, 255)
    });
  }
  
  return dimensions;
};
```

### Verifying Published Metrics

```bash
# List metrics in the namespace
aws cloudwatch list-metrics \
  --namespace "Bedrock/CrossRegionMetrics"

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace "Bedrock/CrossRegionMetrics" \
  --metric-name "InputTokens" \
  --dimensions Name=InferenceProfileType,Value=CrossRegion \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

---

## Quick Reference Checklist

### Pre-Deployment Verification

- [ ] Lambda execution role has S3 read permissions
- [ ] Lambda execution role has SQS receive/delete permissions
- [ ] Lambda execution role has CloudWatch putMetricData permission
- [ ] SQS queue visibility timeout ≥ 6x Lambda timeout
- [ ] Dead letter queue configured with appropriate maxReceiveCount
- [ ] S3 bucket notifications configured to send to SQS
- [ ] Lambda memory allocated appropriately for log file sizes

### Post-Incident Review

- [ ] Check CloudWatch Logs for error codes
- [ ] Review DLQ for failed messages
- [ ] Verify IAM permissions haven't changed
- [ ] Check for service limit increases needed
- [ ] Review S3 lifecycle policies for log retention
- [ ] Validate SQS message format from S3 notifications

---

## Support and Escalation

If issues persist after following this guide:

1. **Collect diagnostics:**
   - Lambda function ARN and version
   - CloudWatch Log group with relevant timeframe
   - Sample SQS messages from DLQ
   - Error codes encountered

2. **Check AWS Service Health Dashboard** for regional issues affecting S3, SQS, Lambda, or CloudWatch

3. **Contact the platform team** with collected diagnostics and steps already attempted