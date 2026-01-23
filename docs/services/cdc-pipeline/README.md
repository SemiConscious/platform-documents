# CDC Pipeline Overview

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)](https://aws.amazon.com/lambda/)
[![EventBridge](https://img.shields.io/badge/AWS-EventBridge-purple?logo=amazon-aws)](https://aws.amazon.com/eventbridge/)
[![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blue?logo=amazon-dynamodb)](https://aws.amazon.com/dynamodb/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)](https://www.docker.com/)
[![Kinesis](https://img.shields.io/badge/AWS-Kinesis-FF9900?logo=amazon-aws)](https://aws.amazon.com/kinesis/)

> A robust Change Data Capture (CDC) pipeline service that captures real-time database changes from CoreDB tables and distributes events to downstream consumers through AWS EventBridge.

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Supported Tables](#supported-tables)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation Index](#documentation-index)

---

## Introduction

The **cdc-pipeline** service is a critical infrastructure component that enables real-time data synchronization across the platform by capturing and processing database changes as they occur. Built on AWS Lambda, this service monitors 12+ CoreDB tables for INSERT, UPDATE, and DELETE operations, transforms the captured data, applies necessary redactions, and publishes standardized events to Amazon EventBridge for consumption by downstream services.

### Why CDC?

Traditional polling-based approaches for detecting database changes are inefficient, resource-intensive, and introduce latency. Change Data Capture (CDC) provides a more elegant solution by:

- **Capturing changes in real-time** as they occur in the source database
- **Reducing database load** by eliminating constant polling queries
- **Ensuring data consistency** across distributed systems
- **Enabling event-driven architectures** with minimal latency

### Primary Use Cases

| Use Case | Description |
|----------|-------------|
| **Wallboards Service** | Real-time updates for operational dashboards and metrics displays |
| **Analytics Pipeline** | Feeding data warehouses with incremental changes |
| **Audit Logging** | Comprehensive tracking of all data modifications |
| **Cache Invalidation** | Triggering cache refreshes when source data changes |
| **Cross-Service Sync** | Keeping microservices in sync without tight coupling |

---

## Key Features

- 🔄 **CDC Processing** - Captures changes from 12+ CoreDB tables in real-time
- ⚡ **AWS Lambda-Based** - Serverless event processing with automatic scaling
- 📡 **EventBridge Integration** - Standardized event distribution to downstream consumers
- 🔒 **Data Redaction** - Automatic PII redaction and data transformation capabilities
- 💾 **State Management** - DynamoDB-backed state persistence for exactly-once processing
- 🌊 **Kinesis Integration** - High-throughput stream processing for burst workloads
- 📊 **75+ Data Models** - Comprehensive model coverage for all captured entities

---

## Architecture Overview

The CDC Pipeline follows an event-driven architecture pattern, leveraging AWS managed services for reliability and scalability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CDC Pipeline Architecture                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CoreDB     │     │   Kinesis    │     │   Lambda     │     │ EventBridge  │
│   (Source)   │────▶│   Stream     │────▶│  Functions   │────▶│   (Target)   │
│              │     │              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                │                      │
                                                │                      │
                                                ▼                      ▼
                                         ┌──────────────┐     ┌──────────────┐
                                         │  DynamoDB    │     │  Downstream  │
                                         │   (State)    │     │  Consumers   │
                                         └──────────────┘     └──────────────┘
```

### Data Flow

1. **Change Detection** - Database triggers or DynamoDB Streams capture changes in CoreDB tables
2. **Stream Ingestion** - Changes are published to Kinesis Data Streams for buffering
3. **Lambda Processing** - Lambda functions consume stream records, applying transformations and redactions
4. **State Management** - Processing checkpoints stored in DynamoDB for exactly-once semantics
5. **Event Publishing** - Transformed events published to EventBridge with standardized schemas
6. **Consumer Delivery** - EventBridge routes events to subscribed downstream services

For detailed architecture documentation, see [Architecture & Data Flow](docs/architecture.md).

---

## Supported Tables

The CDC Pipeline currently monitors the following CoreDB tables:

| Table Name | Event Types | Redaction Applied | Primary Consumers |
|------------|-------------|-------------------|-------------------|
| `users` | INSERT, UPDATE, DELETE | ✅ PII Redacted | Wallboards, Analytics |
| `orders` | INSERT, UPDATE | ✅ Payment Data | Wallboards, Reporting |
| `products` | INSERT, UPDATE, DELETE | ❌ | Catalog Service |
| `inventory` | UPDATE | ❌ | Warehouse, Alerts |
| `customers` | INSERT, UPDATE, DELETE | ✅ PII Redacted | CRM, Analytics |
| `transactions` | INSERT | ✅ Financial Data | Accounting, Audit |
| `sessions` | INSERT, DELETE | ✅ Auth Tokens | Security, Analytics |
| `notifications` | INSERT, UPDATE | ❌ | Messaging Service |
| `audit_logs` | INSERT | ❌ | Compliance, Security |
| `metrics` | INSERT | ❌ | Monitoring, Dashboards |
| `configurations` | UPDATE | ❌ | Config Service |
| `events` | INSERT | ❌ | Event Store |

> **Note:** Additional tables can be configured. See [Configuration Guide](docs/configuration.md) for details.

---

## Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **Node.js** (v18.x or later) - For Lambda function development
- **npm** (v9.x or later) - Package management
- **Docker** (v24.x or later) - Container-based local development
- **AWS CLI** (v2.x) - AWS service interaction
- **AWS SAM CLI** (v1.x) - Local Lambda testing

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cdc-pipeline

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Configure your local environment
# Edit .env with your AWS credentials and configuration
```

### Verify Installation

```bash
# Run health check
npm run health-check

# Validate configuration
npm run validate-config
```

---

## Local Development

### Docker-Based Development Environment

The CDC Pipeline provides a fully containerized local development environment that simulates the AWS infrastructure.

```bash
# Start all local services (LocalStack, DynamoDB Local, etc.)
docker-compose up -d

# Verify services are running
docker-compose ps

# View service logs
docker-compose logs -f cdc-processor
```

### Docker Compose Services

```yaml
# docker-compose.yml overview
services:
  localstack:        # Simulates AWS services (Kinesis, EventBridge, Lambda)
  dynamodb-local:    # Local DynamoDB for state management
  cdc-processor:     # Main CDC processing container
  mock-coredb:       # Simulated CoreDB for testing
```

### Running Lambda Functions Locally

```bash
# Invoke a specific Lambda function locally
npm run invoke:local -- --function processUserChanges --event test/events/user-update.json

# Start local API for manual testing
npm run start:local

# Watch mode for development
npm run dev
```

### Environment Configuration

Create a `.env.local` file for local development:

```bash
# AWS Configuration (LocalStack)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# DynamoDB Configuration
DYNAMODB_ENDPOINT=http://localhost:8000
STATE_TABLE_NAME=cdc-pipeline-state

# Kinesis Configuration
KINESIS_STREAM_NAME=cdc-changes-stream

# EventBridge Configuration
EVENT_BUS_NAME=cdc-events

# Feature Flags
ENABLE_PII_REDACTION=true
ENABLE_DETAILED_LOGGING=true
```

### Multi-Language Development

The CDC Pipeline supports multiple programming languages for different components:

```bash
# TypeScript/JavaScript components
cd lambdas/processors
npm install
npm run build

# Python components (if applicable)
cd lambdas/transformers
pip install -r requirements.txt

# Run all language-specific tests
npm run test:all
```

---

## Testing

### Running the Test Suite

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Structure

```
tests/
├── unit/
│   ├── processors/       # Lambda processor unit tests
│   ├── transformers/     # Data transformation tests
│   ├── redactors/        # PII redaction tests
│   └── models/           # Data model validation tests
├── integration/
│   ├── kinesis/          # Kinesis stream integration
│   ├── eventbridge/      # EventBridge publishing tests
│   └── dynamodb/         # State management tests
└── e2e/
    └── pipeline/         # End-to-end pipeline tests
```

### Testing with Docker

```bash
# Run tests in containerized environment
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific test suite in Docker
docker-compose run --rm test npm run test:integration
```

### Sample Test Event

```json
{
  "eventType": "UPDATE",
  "tableName": "users",
  "timestamp": "2024-01-15T10:30:00Z",
  "before": {
    "id": "usr_123",
    "email": "user@example.com",
    "status": "active"
  },
  "after": {
    "id": "usr_123",
    "email": "user@example.com",
    "status": "inactive"
  }
}
```

---

## Deployment

### Prerequisites for Deployment

1. AWS credentials configured with appropriate permissions
2. Access to the target AWS account
3. Required IAM roles and policies in place

### Deployment Commands

```bash
# Deploy to development environment
npm run deploy:dev

# Deploy to staging environment
npm run deploy:staging

# Deploy to production environment
npm run deploy:prod

# Deploy specific stack/function
npm run deploy -- --stack cdc-processors --env prod
```

### Infrastructure as Code

The CDC Pipeline uses AWS SAM for infrastructure deployment:

```bash
# Build the SAM application
npm run sam:build

# Deploy with guided configuration
npm run sam:deploy:guided

# Validate SAM template
npm run sam:validate
```

### Deployment Checklist

- [ ] All tests passing (`npm test`)
- [ ] Configuration validated (`npm run validate-config`)
- [ ] Docker image built successfully (`docker build -t cdc-pipeline .`)
- [ ] Environment variables configured in AWS Systems Manager
- [ ] EventBridge rules configured for target environment
- [ ] DynamoDB tables provisioned with appropriate capacity
- [ ] Kinesis streams created with correct shard count
- [ ] IAM permissions verified

### Rollback Procedures

```bash
# Rollback to previous version
npm run rollback -- --env prod --version previous

# Rollback to specific version
npm run rollback -- --env prod --version v1.2.3
```

---

## Documentation Index

For detailed information on specific topics, refer to the following documentation:

| Document | Description |
|----------|-------------|
| [Architecture & Data Flow](docs/architecture.md) | Detailed system architecture, data flow diagrams, and design decisions |
| [Lambda Functions Overview](docs/lambdas/README.md) | Documentation for all Lambda functions, triggers, and configurations |
| [Data Models Overview](docs/models/README.md) | Complete reference for all 75 data models used in the pipeline |
| [Configuration Guide](docs/configuration.md) | Environment variables, feature flags, and configuration options |
| [Repository Layer](docs/repositories.md) | Data access patterns and repository implementations |

### Additional Resources

- **Runbooks**: `docs/runbooks/` - Operational procedures and incident response
- **API Reference**: `docs/api/` - Internal API documentation
- **Changelog**: `CHANGELOG.md` - Version history and release notes
- **Contributing**: `CONTRIBUTING.md` - Guidelines for contributors

---

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Lambda timeout | Large batch size | Reduce `BATCH_SIZE` in configuration |
| Missing events | EventBridge rule misconfigured | Verify rule patterns in AWS Console |
| State inconsistency | DynamoDB throttling | Increase table capacity or enable auto-scaling |
| Redaction failures | Invalid PII patterns | Check redaction rules in configuration |

### Getting Help

- **Slack**: `#cdc-pipeline-support`
- **On-Call**: Check PagerDuty for current on-call engineer
- **Issues**: File issues in the GitHub repository

---

## License

This project is proprietary software. See `LICENSE` file for details.

---

<p align="center">
  <sub>Built with ❤️ by the Platform Team</sub>
</p>