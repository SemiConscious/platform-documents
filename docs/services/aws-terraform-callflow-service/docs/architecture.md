# Architecture Overview

## Callflow Service (aws-terraform-callflow-service)

### Introduction

The Callflow Service is a serverless AWS-based solution designed for storing and retrieving call flow events. Built entirely using Terraform, this service leverages AWS managed services to provide a scalable, secure, and cost-effective architecture for handling call flow data. This document provides a comprehensive overview of the architecture, explaining how each component interacts and how data flows through the system.

This architecture overview is intended for operators, DevOps engineers, and platform teams who need to understand, deploy, maintain, and troubleshoot the Callflow Service infrastructure.

---

## High-Level Architecture

The Callflow Service follows a serverless, event-driven architecture pattern that eliminates the need for server management while providing automatic scaling and high availability. The architecture consists of the following major layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                    (External Applications / Services)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DNS LAYER                                       │
│                         (Route 53 / Custom Domain)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│                    (API Gateway with OpenAPI 3.0 Spec)                      │
│                         + Lambda Authorizer                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPUTE LAYER                                      │
│              ┌──────────────────┐    ┌──────────────────┐                   │
│              │  Event Storer    │    │  Event Retriever │                   │
│              │     Lambda       │    │     Lambda       │                   │
│              └──────────────────┘    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                      │
│                         (S3 Bucket / Objects)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OBSERVABILITY LAYER                                  │
│           (CloudWatch Logs, Metrics, Alarms, Dashboard)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

The Callflow Service architecture adheres to the following design principles:

1. **Serverless-First**: All compute resources are managed AWS Lambda functions, eliminating server management overhead
2. **Infrastructure as Code**: Complete infrastructure definition using Terraform for reproducibility and version control
3. **Security by Design**: Authentication enforced at the API Gateway level with Lambda Authorizer
4. **Observability Built-In**: Comprehensive logging, metrics, and alerting from the ground up
5. **Scalability**: Automatic scaling based on demand with no manual intervention required

---

## Component Overview

### Core Components

| Component | AWS Service | Purpose | Scaling Model |
|-----------|-------------|---------|---------------|
| API Gateway | Amazon API Gateway | Request routing, validation, rate limiting | Automatic |
| Lambda Authorizer | AWS Lambda | Token validation, authentication | Automatic |
| Event Storer | AWS Lambda | Process and store call flow events | Automatic |
| Event Retriever | AWS Lambda | Query and retrieve stored events | Automatic |
| Storage Backend | Amazon S3 | Persistent event storage | Unlimited |
| Logging | CloudWatch Logs | Centralized log aggregation | Automatic |
| Monitoring | CloudWatch Alarms/Dashboard | Health monitoring and alerting | N/A |
| DNS | Route 53 | Custom domain management | N/A |

### Component Dependencies

```
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌────────────────┐  ┌───────────────┐
│    Lambda      │  │    Lambda     │
│   Authorizer   │  │   Functions   │
└────────────────┘  └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │      S3       │
                    │    Bucket     │
                    └───────────────┘
```

---

## API Gateway Configuration

### OpenAPI 3.0 Specification

The API Gateway is configured using an OpenAPI 3.0 specification, providing a standardized, documented API interface. This approach offers several advantages:

- **Self-Documenting**: API structure is defined in a human-readable format
- **Validation**: Request/response validation based on schema definitions
- **Code Generation**: Client SDKs can be auto-generated from the specification
- **Versioning**: API versions are tracked through the specification

### API Gateway Features

```hcl
# Terraform configuration example for API Gateway
resource "aws_api_gateway_rest_api" "callflow_api" {
  name        = "callflow-service-api"
  description = "Callflow Service API Gateway"
  
  body = file("${path.module}/openapi.yaml")
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_stage" "production" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.callflow_api.id
  stage_name    = "v1"
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format          = jsonencode({
      requestId         = "$context.requestId"
      ip                = "$context.identity.sourceIp"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      resourcePath      = "$context.resourcePath"
      status            = "$context.status"
      responseLength    = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
    })
  }
}
```

### Endpoint Structure

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/events` | Event Storer Lambda | Store new call flow events |
| GET | `/events/{eventId}` | Event Retriever Lambda | Retrieve specific event |
| GET | `/events` | Event Retriever Lambda | Query events with filters |

### Rate Limiting and Throttling

API Gateway is configured with throttling to protect backend services:

- **Burst Limit**: Maximum concurrent requests allowed
- **Rate Limit**: Sustained requests per second
- **Per-Client Throttling**: Optional limits per API key

---

## Lambda Functions

### Event Storer Lambda

The Event Storer Lambda function is responsible for processing incoming call flow events and persisting them to S3 storage.

**Responsibilities:**
- Validate incoming event payload
- Generate unique event identifiers
- Transform data to storage format
- Write events to S3 with appropriate metadata
- Return confirmation response

**Execution Flow:**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Receive   │───▶│   Validate  │───▶│  Transform  │───▶│   Store     │
│   Request   │    │   Payload   │    │    Data     │    │   to S3     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                                      │
                          ▼                                      ▼
                   ┌─────────────┐                        ┌─────────────┐
                   │   Return    │                        │   Return    │
                   │   Error     │                        │   Success   │
                   └─────────────┘                        └─────────────┘
```

**Terraform Configuration:**

```hcl
resource "aws_lambda_function" "event_storer" {
  function_name = "${var.service_name}-event-storer"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs18.x"
  timeout       = 30
  memory_size   = 256
  
  environment {
    variables = {
      S3_BUCKET     = aws_s3_bucket.events.id
      LOG_LEVEL     = "INFO"
      SERVICE_NAME  = var.service_name
    }
  }
  
  tracing_config {
    mode = "Active"
  }
}
```

### Event Retriever Lambda

The Event Retriever Lambda function handles queries for stored call flow events.

**Responsibilities:**
- Parse query parameters
- Build S3 query/list operations
- Retrieve matching events
- Format response payload
- Handle pagination for large result sets

**Query Capabilities:**
- Single event retrieval by ID
- Date range queries
- Filter by call attributes
- Pagination support

### Lambda Authorizer

The Lambda Authorizer provides custom authentication logic at the API Gateway level.

**Authentication Flow:**

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────▶│  API Gateway │────▶│   Lambda     │────▶│  Policy  │
│ Request  │     │              │     │  Authorizer  │     │ Decision │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
     │                                       │                    │
     │                                       ▼                    │
     │                              ┌──────────────┐              │
     │                              │   Validate   │              │
     │                              │    Token     │              │
     │                              └──────────────┘              │
     │                                       │                    │
     │                                       ▼                    │
     │                              ┌──────────────┐              │
     │                              │   Generate   │──────────────┘
     │                              │  IAM Policy  │
     │                              └──────────────┘
     │
     └─────────────────────────────────────────────────────────────▶ Backend Lambda
```

---

## S3 Storage Design

### Bucket Structure

The S3 storage is designed for efficient querying and cost-effective long-term storage:

```
s3://callflow-events-bucket/
├── events/
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── 01/
│   │   │   │   ├── event-uuid-1.json
│   │   │   │   ├── event-uuid-2.json
│   │   │   │   └── ...
│   │   │   └── 02/
│   │   └── 02/
│   └── ...
└── metadata/
    └── indexes/
```

### Storage Configuration

```hcl
resource "aws_s3_bucket" "events" {
  bucket = "${var.service_name}-events-${var.environment}"
}

resource "aws_s3_bucket_versioning" "events" {
  bucket = aws_s3_bucket.events.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "events" {
  bucket = aws_s3_bucket.events.id

  rule {
    id     = "archive-old-events"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "events" {
  bucket = aws_s3_bucket.events.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
```

### Data Retention

| Storage Class | Retention Period | Use Case |
|---------------|------------------|----------|
| STANDARD | 0-90 days | Active data, frequent access |
| STANDARD_IA | 90-365 days | Infrequent access, compliance |
| GLACIER | 365+ days | Archive, long-term retention |

---

## Authentication Flow

### Token-Based Authentication

The service uses a custom Lambda Authorizer for token-based authentication:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. Client Request
   ┌────────────────────────────────────────────────────────────┐
   │  GET /events HTTP/1.1                                      │
   │  Host: api.callflow.example.com                           │
   │  Authorization: Bearer <token>                             │
   └────────────────────────────────────────────────────────────┘
                              │
                              ▼
2. API Gateway extracts Authorization header
                              │
                              ▼
3. Lambda Authorizer invoked with token
   ┌────────────────────────────────────────────────────────────┐
   │  {                                                         │
   │    "type": "TOKEN",                                        │
   │    "authorizationToken": "Bearer <token>",                │
   │    "methodArn": "arn:aws:execute-api:..."                 │
   │  }                                                         │
   └────────────────────────────────────────────────────────────┘
                              │
                              ▼
4. Token validation (signature, expiry, claims)
                              │
                              ▼
5. IAM Policy generated and cached
   ┌────────────────────────────────────────────────────────────┐
   │  {                                                         │
   │    "principalId": "user-123",                             │
   │    "policyDocument": {                                     │
   │      "Statement": [{                                       │
   │        "Effect": "Allow",                                  │
   │        "Action": "execute-api:Invoke",                    │
   │        "Resource": "arn:aws:execute-api:..."              │
   │      }]                                                    │
   │    }                                                       │
   │  }                                                         │
   └────────────────────────────────────────────────────────────┘
                              │
                              ▼
6. Request forwarded to backend Lambda (if authorized)
```

### Authorization Caching

The Lambda Authorizer response is cached to improve performance:

```hcl
resource "aws_api_gateway_authorizer" "main" {
  name                   = "callflow-authorizer"
  rest_api_id            = aws_api_gateway_rest_api.callflow_api.id
  authorizer_uri         = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials = aws_iam_role.authorizer.arn
  
  # Cache authorization results for 5 minutes
  authorizer_result_ttl_in_seconds = 300
  
  identity_source = "method.request.header.Authorization"
  type            = "TOKEN"
}
```

---

## Data Flow Diagram

### Event Storage Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVENT STORAGE DATA FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐         ┌─────────────┐         ┌──────────────┐
│  Client  │────────▶│   Route 53  │────────▶│  API Gateway │
│          │  HTTPS  │   (DNS)     │         │              │
└──────────┘         └─────────────┘         └──────┬───────┘
                                                    │
                                    ┌───────────────┴───────────────┐
                                    │                               │
                                    ▼                               ▼
                           ┌──────────────┐                ┌──────────────┐
                           │   Lambda     │   Validate     │   Event      │
                           │  Authorizer  │◀──────────────▶│   Storer     │
                           └──────────────┘   (if auth ok) │   Lambda     │
                                    │                      └──────┬───────┘
                                    │                             │
                                    ▼                             │
                           ┌──────────────┐                       │
                           │  CloudWatch  │◀──────────────────────┤
                           │    Logs      │    Structured         │
                           └──────────────┘    JSON Logs          │
                                                                  │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │      S3      │
                                                          │    Bucket    │
                                                          └──────────────┘
```

### Event Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT RETRIEVAL DATA FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐         ┌─────────────┐         ┌──────────────┐
│  Client  │────────▶│   Route 53  │────────▶│  API Gateway │
│  (Query) │  HTTPS  │   (DNS)     │         │              │
└──────────┘         └─────────────┘         └──────┬───────┘
                                                    │
                                    ┌───────────────┴───────────────┐
                                    │                               │
                                    ▼                               ▼
                           ┌──────────────┐                ┌──────────────┐
                           │   Lambda     │   Validate     │   Event      │
                           │  Authorizer  │◀──────────────▶│  Retriever   │
                           └──────────────┘   (if auth ok) │   Lambda     │
                                                           └──────┬───────┘
                                                                  │
                                         ┌────────────────────────┤
                                         │                        │
                                         ▼                        ▼
                                 ┌──────────────┐         ┌──────────────┐
                                 │  CloudWatch  │         │      S3      │
                                 │    Logs      │         │    Bucket    │
                                 └──────────────┘         └──────┬───────┘
                                                                  │
                                                                  │
                           ┌──────────────────────────────────────┘
                           │
                           ▼
┌──────────┐         ┌──────────────┐
│  Client  │◀────────│   Response   │
│          │  JSON   │   (Events)   │
└──────────┘         └──────────────┘
```

---

## Observability Architecture

### CloudWatch Integration

```hcl
# Log Groups
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.service_name}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "lambda_storer" {
  name              = "/aws/lambda/${var.service_name}-event-storer"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "lambda_retriever" {
  name              = "/aws/lambda/${var.service_name}-event-retriever"
  retention_in_days = 30
}

# Alarm for Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.service_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda function errors exceeded threshold"
  
  dimensions = {
    FunctionName = aws_lambda_function.event_storer.function_name
  }
}
```

### Dashboard Metrics

The CloudWatch Dashboard provides visibility into:

| Metric Category | Metrics Tracked |
|-----------------|-----------------|
| API Gateway | Request count, latency (p50, p95, p99), 4xx/5xx errors |
| Lambda Functions | Invocation count, duration, errors, throttles |
| S3 | Request count, bucket size, object count |
| Authorizer | Cache hit rate, validation failures |

---

## Summary

The Callflow Service architecture provides a robust, scalable, and secure solution for managing call flow events. Key architectural decisions include:

1. **Serverless compute** eliminates infrastructure management overhead
2. **API Gateway with OpenAPI** provides standardized, documented endpoints
3. **Custom Lambda Authorizer** enables flexible authentication logic
4. **S3 storage with lifecycle policies** optimizes cost and performance
5. **Comprehensive observability** ensures operational visibility

For deployment instructions and configuration details, refer to the accompanying deployment guide and configuration reference documentation.