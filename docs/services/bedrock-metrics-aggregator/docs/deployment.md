# Deployment Guide

## Overview

This comprehensive guide provides step-by-step instructions for deploying and configuring the **bedrock-metrics-aggregator** AWS Lambda function. This service processes Bedrock invocation logs from S3, aggregates cross-region usage metrics for inference profiles, and publishes custom metrics to CloudWatch.

The deployment process involves setting up the necessary AWS infrastructure including IAM roles, SQS queues, S3 bucket notifications, and CloudWatch configurations. By the end of this guide, you will have a fully operational metrics aggregation pipeline for monitoring Bedrock usage across regions.

---

## Prerequisites

Before beginning the deployment process, ensure you have the following prerequisites in place:

### Required Tools and Access

| Requirement | Minimum Version | Purpose |
|-------------|-----------------|---------|
| AWS CLI | 2.x | Deploying and configuring AWS resources |
| Node.js | 18.x or 20.x | Building Lambda function packages |
| npm | 9.x | Managing dependencies |
| AWS Account | N/A | Hosting all resources |
| IAM Permissions | Administrator or specific permissions | Creating and managing AWS resources |

### AWS Services Required

- **AWS Lambda** - Hosts the metrics aggregator function
- **Amazon S3** - Stores Bedrock invocation logs
- **Amazon SQS** - Message queue for event processing
- **Amazon CloudWatch** - Metrics and logging destination
- **AWS IAM** - Identity and access management

### Pre-Deployment Checklist

```bash
# Verify AWS CLI installation and configuration
aws --version
aws sts get-caller-identity

# Verify Node.js and npm installation
node --version
npm --version

# Ensure you have access to the target AWS account
aws s3 ls --region us-east-1
```

### Network Requirements

- The Lambda function requires network access to:
  - Amazon S3 (for reading invocation logs)
  - Amazon SQS (for receiving event messages)
  - Amazon CloudWatch (for publishing metrics)
- If deploying within a VPC, ensure appropriate VPC endpoints are configured

---

## IAM Permissions Required

### Lambda Execution Role

Create an IAM role with the following trust policy and permissions for the Lambda function:

#### Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### Required Permissions Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/bedrock-metrics-aggregator*"
    },
    {
      "Sid": "S3ReadAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bedrock-logs-bucket",
        "arn:aws:s3:::your-bedrock-logs-bucket/*"
      ]
    },
    {
      "Sid": "SQSAccess",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ],
      "Resource": "arn:aws:sqs:*:*:bedrock-metrics-aggregator-queue"
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "Custom/BedrockMetrics"
        }
      }
    }
  ]
}
```

### Creating the IAM Role via CLI

```bash
# Create the execution role
aws iam create-role \
  --role-name bedrock-metrics-aggregator-role \
  --assume-role-policy-document file://trust-policy.json

# Attach the permissions policy
aws iam put-role-policy \
  --role-name bedrock-metrics-aggregator-role \
  --policy-name bedrock-metrics-aggregator-policy \
  --policy-document file://permissions-policy.json

# Attach AWS managed policy for basic Lambda execution
aws iam attach-role-policy \
  --role-name bedrock-metrics-aggregator-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Cross-Account Permissions (Optional)

If Bedrock logs are stored in a different AWS account, add cross-account S3 access:

```json
{
  "Sid": "CrossAccountS3Access",
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::cross-account-bedrock-logs-bucket",
    "arn:aws:s3:::cross-account-bedrock-logs-bucket/*"
  ]
}
```

---

## Environment Variables

Configure the following environment variables for the Lambda function:

### Required Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CLOUDWATCH_NAMESPACE` | CloudWatch namespace for custom metrics | `Custom/BedrockMetrics` |
| `LOG_LEVEL` | Logging verbosity level | `INFO` |
| `AWS_REGION` | Primary AWS region for operations | `us-east-1` |

### Optional Variables

| Variable | Description | Default | Example Value |
|----------|-------------|---------|---------------|
| `BATCH_SIZE` | Number of records to process per batch | `100` | `250` |
| `METRICS_RETENTION_DAYS` | CloudWatch metrics retention period | `30` | `90` |
| `ENABLE_CROSS_REGION_DETECTION` | Enable CrossRegion inference profile detection | `true` | `true` |
| `ENABLE_GLOBAL_CROSS_REGION` | Enable GlobalCrossRegion inference profile detection | `true` | `true` |
| `DLQ_ENABLED` | Enable dead-letter queue processing | `true` | `true` |
| `MAX_RETRY_ATTEMPTS` | Maximum retry attempts for failed processing | `3` | `5` |

### Environment Variable Configuration Example

```bash
# Set environment variables via AWS CLI
aws lambda update-function-configuration \
  --function-name bedrock-metrics-aggregator \
  --environment "Variables={
    CLOUDWATCH_NAMESPACE=Custom/BedrockMetrics,
    LOG_LEVEL=INFO,
    BATCH_SIZE=100,
    ENABLE_CROSS_REGION_DETECTION=true,
    ENABLE_GLOBAL_CROSS_REGION=true,
    MAX_RETRY_ATTEMPTS=3
  }"
```

### Environment Variables in CloudFormation/SAM

```yaml
# SAM template environment configuration
Environment:
  Variables:
    CLOUDWATCH_NAMESPACE: Custom/BedrockMetrics
    LOG_LEVEL: INFO
    BATCH_SIZE: "100"
    ENABLE_CROSS_REGION_DETECTION: "true"
    ENABLE_GLOBAL_CROSS_REGION: "true"
    MAX_RETRY_ATTEMPTS: "3"
```

---

## SQS Queue Configuration

### Creating the Main Queue

```bash
# Create the main processing queue
aws sqs create-queue \
  --queue-name bedrock-metrics-aggregator-queue \
  --attributes '{
    "VisibilityTimeout": "300",
    "MessageRetentionPeriod": "1209600",
    "ReceiveMessageWaitTimeSeconds": "20",
    "DelaySeconds": "0"
  }'
```

### Creating the Dead-Letter Queue (DLQ)

```bash
# Create the DLQ for failed messages
aws sqs create-queue \
  --queue-name bedrock-metrics-aggregator-dlq \
  --attributes '{
    "MessageRetentionPeriod": "1209600"
  }'

# Get the DLQ ARN
DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/bedrock-metrics-aggregator-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)
```

### Configuring Redrive Policy

```bash
# Configure the main queue to use the DLQ
aws sqs set-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/bedrock-metrics-aggregator-queue \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"'$DLQ_ARN'\",\"maxReceiveCount\":\"3\"}"
  }'
```

### SQS Queue Policy

Allow S3 to send messages to the queue:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ToSendMessage",
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:us-east-1:YOUR_ACCOUNT_ID:bedrock-metrics-aggregator-queue",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:s3:::your-bedrock-logs-bucket"
        }
      }
    }
  ]
}
```

### CloudFormation Template for SQS

```yaml
Resources:
  BedrockMetricsQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: bedrock-metrics-aggregator-queue
      VisibilityTimeout: 300
      MessageRetentionPeriod: 1209600
      ReceiveMessageWaitTimeSeconds: 20
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt BedrockMetricsDLQ.Arn
        maxReceiveCount: 3

  BedrockMetricsDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: bedrock-metrics-aggregator-dlq
      MessageRetentionPeriod: 1209600

  SQSQueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      Queues:
        - !Ref BedrockMetricsQueue
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Sid: AllowS3ToSendMessage
            Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sqs:SendMessage
            Resource: !GetAtt BedrockMetricsQueue.Arn
            Condition:
              ArnLike:
                aws:SourceArn: !Sub "arn:aws:s3:::${BedrockLogsBucket}"
```

---

## S3 Event Configuration

### Configuring S3 Bucket Notifications

```bash
# Create the notification configuration JSON
cat > s3-notification-config.json << 'EOF'
{
  "QueueConfigurations": [
    {
      "Id": "BedrockLogsToSQS",
      "QueueArn": "arn:aws:sqs:us-east-1:YOUR_ACCOUNT_ID:bedrock-metrics-aggregator-queue",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "bedrock-logs/"
            },
            {
              "Name": "suffix",
              "Value": ".json"
            }
          ]
        }
      }
    }
  ]
}
EOF

# Apply the notification configuration
aws s3api put-bucket-notification-configuration \
  --bucket your-bedrock-logs-bucket \
  --notification-configuration file://s3-notification-config.json
```

### S3 Bucket Structure

Ensure your S3 bucket follows this recommended structure for Bedrock logs:

```
your-bedrock-logs-bucket/
├── bedrock-logs/
│   ├── us-east-1/
│   │   ├── 2024/
│   │   │   ├── 01/
│   │   │   │   ├── 01/
│   │   │   │   │   ├── invocation-log-001.json
│   │   │   │   │   └── invocation-log-002.json
│   ├── us-west-2/
│   │   └── ...
│   └── eu-west-1/
│       └── ...
```

### CloudFormation S3 Configuration

```yaml
Resources:
  BedrockLogsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "bedrock-logs-${AWS::AccountId}"
      NotificationConfiguration:
        QueueConfigurations:
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt BedrockMetricsQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: bedrock-logs/
                  - Name: suffix
                    Value: .json
      LifecycleConfiguration:
        Rules:
          - Id: ExpireOldLogs
            Status: Enabled
            ExpirationInDays: 90
            Prefix: bedrock-logs/
```

---

## CloudWatch Setup

### Creating CloudWatch Dashboard

```bash
# Create a CloudWatch dashboard for Bedrock metrics
aws cloudwatch put-dashboard \
  --dashboard-name "BedrockMetricsAggregator" \
  --dashboard-body file://dashboard.json
```

### Dashboard Configuration (dashboard.json)

```json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Total Input Tokens",
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          ["Custom/BedrockMetrics", "InputTokens", "InferenceProfile", "CrossRegion"],
          [".", ".", ".", "GlobalCrossRegion"]
        ],
        "region": "us-east-1",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Total Output Tokens",
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          ["Custom/BedrockMetrics", "OutputTokens", "InferenceProfile", "CrossRegion"],
          [".", ".", ".", "GlobalCrossRegion"]
        ],
        "region": "us-east-1",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Invocation Count",
        "view": "timeSeries",
        "stacked": true,
        "metrics": [
          ["Custom/BedrockMetrics", "InvocationCount", "Region", "us-east-1"],
          [".", ".", ".", "us-west-2"],
          [".", ".", ".", "eu-west-1"]
        ],
        "region": "us-east-1",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Lambda Function Metrics",
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          ["AWS/Lambda", "Invocations", "FunctionName", "bedrock-metrics-aggregator"],
          [".", "Errors", ".", "."],
          [".", "Duration", ".", "."]
        ],
        "region": "us-east-1",
        "period": 60
      }
    }
  ]
}
```

### CloudWatch Alarms

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name "BedrockMetricsAggregator-Errors" \
  --alarm-description "Alarm when Lambda function errors exceed threshold" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=bedrock-metrics-aggregator \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:alerts-topic

# Create alarm for DLQ messages
aws cloudwatch put-metric-alarm \
  --alarm-name "BedrockMetricsAggregator-DLQ" \
  --alarm-description "Alarm when messages appear in DLQ" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=QueueName,Value=bedrock-metrics-aggregator-dlq \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:alerts-topic
```

### Log Groups Configuration

```bash
# Create log group with retention policy
aws logs create-log-group \
  --log-group-name /aws/lambda/bedrock-metrics-aggregator

aws logs put-retention-policy \
  --log-group-name /aws/lambda/bedrock-metrics-aggregator \
  --retention-in-days 30
```

---

## Deployment Steps

### Step 1: Clone and Build the Project

```bash
# Clone the repository
git clone https://github.com/your-org/bedrock-metrics-aggregator.git
cd bedrock-metrics-aggregator

# Install dependencies
npm install

# Run tests
npm test

# Build the deployment package
npm run build
```

### Step 2: Package the Lambda Function

```bash
# Create deployment package
cd dist
zip -r ../deployment-package.zip .
cd ..

# Alternatively, using npm script
npm run package
```

### Step 3: Create or Update the Lambda Function

#### New Deployment

```bash
# Create the Lambda function
aws lambda create-function \
  --function-name bedrock-metrics-aggregator \
  --runtime nodejs20.x \
  --handler index.handler \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/bedrock-metrics-aggregator-role \
  --zip-file fileb://deployment-package.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={
    CLOUDWATCH_NAMESPACE=Custom/BedrockMetrics,
    LOG_LEVEL=INFO,
    ENABLE_CROSS_REGION_DETECTION=true
  }" \
  --description "Aggregates Bedrock metrics from invocation logs"
```

#### Update Existing Deployment

```bash
# Update function code
aws lambda update-function-code \
  --function-name bedrock-metrics-aggregator \
  --zip-file fileb://deployment-package.zip

# Update function configuration if needed
aws lambda update-function-configuration \
  --function-name bedrock-metrics-aggregator \
  --timeout 300 \
  --memory-size 512
```

### Step 4: Configure Event Source Mapping

```bash
# Create event source mapping from SQS to Lambda
aws lambda create-event-source-mapping \
  --function-name bedrock-metrics-aggregator \
  --event-source-arn arn:aws:sqs:us-east-1:YOUR_ACCOUNT_ID:bedrock-metrics-aggregator-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 30 \
  --function-response-types ReportBatchItemFailures
```

### Step 5: Deploy Using SAM (Alternative)

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Bedrock Metrics Aggregator

Globals:
  Function:
    Timeout: 300
    MemorySize: 512

Resources:
  BedrockMetricsAggregatorFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: bedrock-metrics-aggregator
      CodeUri: ./dist
      Handler: index.handler
      Runtime: nodejs20.x
      Description: Aggregates Bedrock metrics from invocation logs
      Environment:
        Variables:
          CLOUDWATCH_NAMESPACE: Custom/BedrockMetrics
          LOG_LEVEL: INFO
          ENABLE_CROSS_REGION_DETECTION: "true"
      Policies:
        - S3ReadPolicy:
            BucketName: !Ref BedrockLogsBucket
        - SQSPollerPolicy:
            QueueName: !GetAtt BedrockMetricsQueue.QueueName
        - CloudWatchPutMetricPolicy: {}
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt BedrockMetricsQueue.Arn
            BatchSize: 10
            MaximumBatchingWindowInSeconds: 30
            FunctionResponseTypes:
              - ReportBatchItemFailures
```

```bash
# Deploy using SAM
sam build
sam deploy --guided
```

### Step 6: Multi-Region Deployment (Optional)

For cross-region metrics aggregation, deploy to multiple regions:

```bash
#!/bin/bash
REGIONS=("us-east-1" "us-west-2" "eu-west-1")

for region in "${REGIONS[@]}"; do
  echo "Deploying to $region..."
  
  aws lambda create-function \
    --function-name bedrock-metrics-aggregator \
    --runtime nodejs20.x \
    --handler index.handler \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/bedrock-metrics-aggregator-role \
    --zip-file fileb://deployment-package.zip \
    --timeout 300 \
    --memory-size 512 \
    --region $region \
    --environment "Variables={
      CLOUDWATCH_NAMESPACE=Custom/BedrockMetrics,
      LOG_LEVEL=INFO,
      AWS_REGION=$region
    }"
done
```

---

## Verification

### Step 1: Verify Lambda Function Deployment

```bash
# Check function configuration
aws lambda get-function \
  --function-name bedrock-metrics-aggregator

# Check function state
aws lambda get-function \
  --function-name bedrock-metrics-aggregator \
  --query 'Configuration.State'
```

### Step 2: Verify Event Source Mapping

```bash
# List event source mappings
aws lambda list-event-source-mappings \
  --function-name bedrock-metrics-aggregator

# Check mapping state
aws lambda list-event-source-mappings \
  --function-name bedrock-metrics-aggregator \
  --query 'EventSourceMappings[*].State'
```

### Step 3: Test with Sample Event

```bash
# Create a test event
cat > test-event.json << 'EOF'
{
  "Records": [
    {
      "messageId": "test-message-id",
      "body": "{\"Records\":[{\"s3\":{\"bucket\":{\"name\":\"your-bedrock-logs-bucket\"},\"object\":{\"key\":\"bedrock-logs/test-invocation.json\"}}}]}"
    }
  ]
}
EOF

# Invoke Lambda with test event
aws lambda invoke \
  --function-name bedrock-metrics-aggregator \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# Check the response
cat response.json
```

### Step 4: Verify CloudWatch Logs

```bash
# Get latest log stream
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name /aws/lambda/bedrock-metrics-aggregator \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --query 'logStreams[0].logStreamName' \
  --output text)

# Fetch recent logs
aws logs get-log-events \
  --log-group-name /aws/lambda/bedrock-metrics-aggregator \
  --log-stream-name "$LOG_STREAM" \
  --limit 50
```

### Step 5: Verify CloudWatch Metrics

```bash
# Check if custom metrics are being published
aws cloudwatch list-metrics \
  --namespace Custom/BedrockMetrics

# Get specific metric data
aws cloudwatch get-metric-statistics \
  --namespace Custom/BedrockMetrics \
  --metric-name InputTokens \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

### Step 6: Verify SQS Queue Processing

```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/bedrock-metrics-aggregator-queue \
  --attribute-names All

# Check DLQ for failed messages
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID/bedrock-metrics-aggregator-dlq \
  --attribute-names ApproximateNumberOfMessages
```

### Verification Checklist

| Component | Verification Command | Expected Result |
|-----------|---------------------|-----------------|
| Lambda Function | `get-function` | State: Active |
| Event Source Mapping | `list-event-source-mappings` | State: Enabled |
| SQS Queue | `get-queue-attributes` | Queue accessible |
| S3 Notifications | `get-bucket-notification-configuration` | Queue configured |
| CloudWatch Logs | `describe-log-streams` | Log streams present |
| CloudWatch Metrics | `list-metrics` | Custom metrics visible |
| DLQ | `get-queue-attributes` | 0 messages (healthy) |

### Troubleshooting Common Issues

#### Lambda Not Processing Messages

```bash
# Check event source mapping status
aws lambda get-event-source-mapping \
  --uuid YOUR_MAPPING_UUID

# Enable the mapping if disabled
aws lambda update-event-source-mapping \
  --uuid YOUR_MAPPING_UUID \
  --enabled
```

#### Permission Errors

```bash
# Test S3 access
aws s3 ls s3://your-bedrock-logs-bucket/bedrock-logs/ \
  --profile lambda-role-test

# Verify IAM role policies
aws iam list-attached-role-policies \
  --role-name bedrock-metrics-aggregator-role
```

#### CloudWatch Metrics Not Appearing

```bash
# Check Lambda logs for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/bedrock-metrics-aggregator \
  --filter-pattern "ERROR"

# Verify namespace configuration
echo $CLOUDWATCH_NAMESPACE
```

---

## Post-Deployment Maintenance

### Monitoring and Alerts

1. **Set up CloudWatch Alarms** for Lambda errors and DLQ messages
2. **Create dashboards** for operational visibility
3. **Enable AWS X-Ray** for distributed tracing (optional)

### Regular Maintenance Tasks

- Review and rotate CloudWatch log retention
- Monitor DLQ for failed messages
- Update Lambda function code as needed
- Review and optimize memory/timeout settings based on metrics

### Scaling Considerations

- Adjust SQS batch size based on processing requirements
- Configure reserved concurrency if needed
- Consider provisioned concurrency for consistent performance

---

## Conclusion

You have successfully deployed the bedrock-metrics-aggregator Lambda function. The service is now configured to:

1. Receive S3 event notifications via SQS when new Bedrock logs are created
2. Process invocation logs and detect CrossRegion/GlobalCrossRegion inference profiles
3. Aggregate token usage metrics (input and output tokens)
4. Publish custom metrics to CloudWatch for monitoring and analysis

For ongoing operations, monitor the CloudWatch dashboard and respond to any alarms. Regularly review the DLQ for failed messages and adjust configuration as needed based on observed patterns.