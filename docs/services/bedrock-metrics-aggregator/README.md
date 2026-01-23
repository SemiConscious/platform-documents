# Bedrock Metrics Aggregator

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazonaws)](https://aws.amazon.com/lambda/)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-blue?logo=amazonaws)](https://aws.amazon.com/bedrock/)
[![CloudWatch](https://img.shields.io/badge/Amazon-CloudWatch-ff4f8b?logo=amazoncloudwatch)](https://aws.amazon.com/cloudwatch/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AWS Lambda function that processes Amazon Bedrock invocation logs from S3, aggregates cross-region usage metrics for inference profiles, and publishes custom metrics to Amazon CloudWatch for centralized monitoring and cost analysis.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Documentation Index](#documentation-index)
- [Contributing](#contributing)

---

## Overview

The **Bedrock Metrics Aggregator** is an event-driven serverless solution designed to solve the challenge of monitoring and analyzing Amazon Bedrock usage across multiple AWS regions. When using Bedrock's cross-region inference profiles, usage data is scattered across different regions, making it difficult to get a unified view of token consumption and costs.

This service automatically:

1. **Ingests** Bedrock invocation logs delivered to S3
2. **Detects** cross-region and global inference profile usage patterns
3. **Aggregates** input and output token metrics across all regions
4. **Publishes** unified custom metrics to CloudWatch for centralized observability

### Why Use This Service?

| Challenge | Solution |
|-----------|----------|
| Bedrock metrics scattered across regions | Centralized metric aggregation in single CloudWatch namespace |
| Difficulty tracking cross-region inference costs | Token usage aggregation by inference profile type |
| Manual log analysis required | Automated event-driven processing pipeline |
| No visibility into inference profile patterns | Custom metrics for CrossRegion and GlobalCrossRegion profiles |

---

## Key Features

- **🔄 Event-Driven Processing** - SQS/S3 event pipeline for real-time log processing
- **🌍 Cross-Region Detection** - Automatic identification of CrossRegion and GlobalCrossRegion inference profiles
- **📊 Token Aggregation** - Comprehensive tracking of input and output token usage
- **📈 CloudWatch Integration** - Custom metrics publishing with configurable dimensions
- **⚡ Serverless Architecture** - Fully managed, auto-scaling Lambda deployment
- **🔒 Secure by Design** - IAM-based access control with least privilege principles

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Bedrock Metrics Aggregator                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Amazon     │    │   Amazon     │    │    AWS       │    │   Amazon     │
│   Bedrock    │───▶│     S3       │───▶│    SQS       │───▶│   Lambda     │
│  (Regions)   │    │  (Logs)      │    │  (Events)    │    │ (Processor)  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                    │
                                                                    ▼
                                                           ┌──────────────┐
                                                           │   Amazon     │
                                                           │  CloudWatch  │
                                                           │  (Metrics)   │
                                                           └──────────────┘
```

### Data Flow

1. **Bedrock Invocations** - API calls to Bedrock models across multiple regions generate invocation logs
2. **S3 Log Delivery** - Logs are automatically delivered to a centralized S3 bucket
3. **S3 Event Notifications** - New log files trigger SQS messages
4. **Lambda Processing** - The aggregator function processes logs, extracts metrics, and identifies inference profile types
5. **CloudWatch Publishing** - Aggregated metrics are published to CloudWatch custom namespace

For detailed architecture information, see [Architecture & Data Flow](docs/architecture.md).

---

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd bedrock-metrics-aggregator
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

Create a `.env` file or configure your deployment tool with required settings:

```bash
# Example environment configuration
S3_BUCKET_NAME=your-bedrock-logs-bucket
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/bedrock-logs-queue
CLOUDWATCH_NAMESPACE=Custom/BedrockMetrics
AWS_REGION=us-east-1
```

### 4. Deploy

```bash
# Using AWS SAM
sam build
sam deploy --guided

# Or using Serverless Framework
serverless deploy --stage prod
```

### 5. Verify Deployment

```bash
# Check Lambda function status
aws lambda get-function --function-name bedrock-metrics-aggregator

# View CloudWatch metrics namespace
aws cloudwatch list-metrics --namespace Custom/BedrockMetrics
```

---

## Prerequisites

### Required AWS Services

| Service | Purpose | Minimum Permissions |
|---------|---------|---------------------|
| **AWS Lambda** | Function execution | `lambda:*` (for deployment) |
| **Amazon S3** | Bedrock log storage | `s3:GetObject`, `s3:ListBucket` |
| **Amazon SQS** | Event queue | `sqs:ReceiveMessage`, `sqs:DeleteMessage` |
| **Amazon CloudWatch** | Metrics publishing | `cloudwatch:PutMetricData` |
| **AWS IAM** | Role management | `iam:PassRole` |

### Development Tools

- **Node.js** 18.x or later
- **npm** 8.x or later
- **AWS CLI** v2 configured with appropriate credentials
- **AWS SAM CLI** or **Serverless Framework** (for deployment)

### Bedrock Configuration

Ensure Amazon Bedrock is configured with:

1. **Invocation Logging** enabled and routing to S3
2. **Cross-Region Inference Profiles** set up (if using cross-region inference)
3. **S3 Event Notifications** configured to trigger SQS

```bash
# Verify Bedrock logging configuration
aws bedrock get-model-invocation-logging-configuration
```

---

## Deployment

### Option 1: AWS SAM Deployment

```bash
# Build the application
npm run build
sam build

# Deploy with guided prompts
sam deploy --guided

# Or deploy with specific parameters
sam deploy \
  --stack-name bedrock-metrics-aggregator \
  --parameter-overrides \
    LogBucketName=my-bedrock-logs \
    CloudWatchNamespace=Custom/BedrockMetrics \
  --capabilities CAPABILITY_IAM
```

### Option 2: Serverless Framework

```bash
# Install Serverless Framework globally
npm install -g serverless

# Deploy to AWS
serverless deploy --stage prod --region us-east-1
```

### Option 3: AWS CDK

```bash
# Install CDK dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy BedrockMetricsAggregatorStack
```

For detailed deployment instructions, including multi-region setup and production configurations, see [Deployment Guide](docs/deployment.md).

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `S3_BUCKET_NAME` | S3 bucket containing Bedrock logs | - | ✅ Yes |
| `SQS_QUEUE_URL` | SQS queue URL for S3 events | - | ✅ Yes |
| `CLOUDWATCH_NAMESPACE` | Custom CloudWatch namespace | `Custom/BedrockMetrics` | No |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `BATCH_SIZE` | SQS batch processing size | `10` | No |
| `METRIC_RESOLUTION` | CloudWatch metric resolution (seconds) | `60` | No |

### Lambda Configuration

```yaml
# Recommended Lambda settings
Runtime: nodejs18.x
MemorySize: 512
Timeout: 300
ReservedConcurrentExecutions: 10
```

### IAM Policy Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bedrock-logs-bucket",
        "arn:aws:s3:::your-bedrock-logs-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:*:*:bedrock-logs-queue"
    },
    {
      "Effect": "Allow",
      "Action": "cloudwatch:PutMetricData",
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

---

## Documentation Index

Explore the complete documentation for detailed information on specific topics:

| Document | Description |
|----------|-------------|
| 📐 [Architecture & Data Flow](docs/architecture.md) | Detailed system architecture, component interactions, and data flow diagrams |
| 🚀 [Deployment Guide](docs/deployment.md) | Step-by-step deployment instructions for various environments |
| 📦 [Data Models & Types](docs/models.md) | TypeScript interfaces, data schemas, and type definitions |
| 📊 [Monitoring & Metrics](docs/monitoring.md) | CloudWatch metrics reference, dashboards, and alerting setup |

### Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [CloudWatch Custom Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

---

## Troubleshooting

### Common Issues

**Lambda Timeout**
```bash
# Increase timeout if processing large log files
aws lambda update-function-configuration \
  --function-name bedrock-metrics-aggregator \
  --timeout 600
```

**Missing Metrics in CloudWatch**
- Verify the Lambda function has `cloudwatch:PutMetricData` permission
- Check CloudWatch namespace matches your configuration
- Allow 5-10 minutes for metrics to appear in console

**SQS Messages Not Processing**
- Confirm S3 event notifications are configured correctly
- Verify SQS queue policy allows S3 to send messages
- Check Lambda trigger configuration

For more troubleshooting tips, see the [Deployment Guide](docs/deployment.md).

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Built with ❤️ for the AWS community</sub>
</p>