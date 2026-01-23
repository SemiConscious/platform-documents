# Insight Category API Overview

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)](https://aws.amazon.com/lambda/)
[![API Gateway](https://img.shields.io/badge/AWS-API%20Gateway-purple?logo=amazon-aws)](https://aws.amazon.com/api-gateway/)
[![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blue?logo=amazon-dynamodb)](https://aws.amazon.com/dynamodb/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-623CE4?logo=terraform)](https://www.terraform.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A REST API service for managing organization categories in the AWS Insight platform. Built with a serverless architecture using AWS Lambda functions, API Gateway, and DynamoDB for data persistence. This service provides comprehensive CRUD operations for organization categories with multi-tenant support.

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [API Domain & Environments](#api-domain--environments)
- [Documentation Index](#documentation-index)
- [Development Setup](#development-setup)
- [Related Services](#related-services)
- [Contributing](#contributing)

---

## Introduction

The **aws-insight-category-api** service is the backbone of category management within the AWS Insight platform. It enables organizations to create, organize, and manage hierarchical categories that can be applied across various resources and insights within the platform.

### What Problem Does This Solve?

Organizations using the AWS Insight platform need a flexible way to categorize and organize their resources, reports, and insights. This service provides:

- **Centralized Category Management**: A single source of truth for all organization categories
- **Multi-Tenant Isolation**: Each organization's categories are securely isolated from others
- **Template Support**: Pre-built category templates to accelerate onboarding
- **Scalable Architecture**: Serverless design that scales automatically with demand

### Who Should Use This Service?

This documentation is intended for:

- **Backend Developers** integrating with the Category API
- **Platform Engineers** deploying and managing the infrastructure
- **DevOps Teams** maintaining the CI/CD pipelines
- **Frontend Developers** building UIs that consume category data

---

## Key Features

| Feature | Description |
|---------|-------------|
| **CRUD Operations** | Full create, read, update, and delete capabilities for categories |
| **Category Templates** | Pre-defined templates for common category structures |
| **Multi-Tenant Architecture** | Organization-scoped resources with strict tenant isolation |
| **Serverless Design** | Lambda-based functions for cost-effective, auto-scaling performance |
| **Infrastructure as Code** | Terraform-managed infrastructure for reproducible deployments |
| **RESTful API** | Standard REST conventions with API Gateway integration |

---

## Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **AWS CLI** (v2.x or later) - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Terraform** (v1.0 or later) - [Installation Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- **SAM CLI** (optional, for local testing) - [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/aws-insight-category-api.git
cd aws-insight-category-api
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

### 3. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"
```

### 4. Verify Deployment

After deployment, test the API endpoint:

```bash
# Get the API endpoint from Terraform output
API_ENDPOINT=$(terraform output -raw api_gateway_url)

# Test the health endpoint
curl -X GET "${API_ENDPOINT}/health"
```

Expected response:

```json
{
  "status": "healthy",
  "service": "aws-insight-category-api",
  "version": "1.0.0"
}
```

### 5. Make Your First API Call

```bash
# Create a new category
curl -X POST "${API_ENDPOINT}/v1/organizations/{org-id}/categories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "Infrastructure",
    "description": "Infrastructure-related insights and resources",
    "color": "#3498db",
    "icon": "server"
  }'
```

---

## Architecture Overview

The aws-insight-category-api follows a serverless microservices architecture pattern, leveraging AWS managed services for scalability and reliability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                       │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────────────────┐   │
│  │               │    │               │    │                           │   │
│  │  API Gateway  │───▶│    Lambda     │───▶│       DynamoDB            │   │
│  │   (REST)      │    │   Functions   │    │   (Categories Table)      │   │
│  │               │    │               │    │                           │   │
│  └───────────────┘    └───────────────┘    └───────────────────────────┘   │
│         │                    │                         │                    │
│         ▼                    ▼                         ▼                    │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────────────────┐   │
│  │   CloudWatch  │    │    X-Ray      │    │    DynamoDB Streams       │   │
│  │    Logging    │    │   Tracing     │    │   (Event Propagation)     │   │
│  └───────────────┘    └───────────────┘    └───────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Purpose | Technology |
|-----------|---------|------------|
| **API Gateway** | Request routing, authentication, rate limiting | AWS API Gateway (REST) |
| **Lambda Functions** | Business logic execution | AWS Lambda (multi-runtime) |
| **DynamoDB** | Primary data store for categories | AWS DynamoDB |
| **CloudWatch** | Logging and monitoring | AWS CloudWatch |
| **X-Ray** | Distributed tracing | AWS X-Ray |
| **DynamoDB Streams** | Event-driven integrations | AWS DynamoDB Streams |

### Data Flow

1. **Inbound Request**: Client sends HTTP request to API Gateway
2. **Authentication**: API Gateway validates JWT token with Cognito
3. **Request Routing**: API Gateway routes to appropriate Lambda function
4. **Business Logic**: Lambda processes request, validates input
5. **Data Persistence**: Lambda interacts with DynamoDB
6. **Response**: Lambda returns response through API Gateway to client

---

## API Domain & Environments

### Base URLs

| Environment | Base URL | Purpose |
|-------------|----------|---------|
| **Development** | `https://api-dev.insight.example.com/category` | Development and testing |
| **Staging** | `https://api-staging.insight.example.com/category` | Pre-production validation |
| **Production** | `https://api.insight.example.com/category` | Live production traffic |

### API Versioning

The API uses URL path versioning. Current version: **v1**

```
https://api.insight.example.com/category/v1/organizations/{org-id}/categories
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/organizations/{org-id}/categories` | List all categories |
| `POST` | `/v1/organizations/{org-id}/categories` | Create a new category |
| `GET` | `/v1/organizations/{org-id}/categories/{id}` | Get category by ID |
| `PUT` | `/v1/organizations/{org-id}/categories/{id}` | Update a category |
| `DELETE` | `/v1/organizations/{org-id}/categories/{id}` | Delete a category |
| `GET` | `/v1/templates` | List available category templates |

> 📖 For complete API documentation, see the [API Reference](docs/api/README.md).

### Authentication

All API requests require a valid JWT token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

Tokens are issued by AWS Cognito. Contact your platform administrator for access credentials.

---

## Documentation Index

Comprehensive documentation is available for all aspects of this service:

### Core Documentation

| Document | Description |
|----------|-------------|
| [**API Reference**](docs/api/README.md) | Complete API endpoint documentation with request/response examples |
| [**Data Models Overview**](docs/models/README.md) | Detailed schema definitions for all 12 data models |
| [**Infrastructure & Architecture**](docs/infrastructure.md) | Deep dive into the AWS architecture and design decisions |

### Infrastructure

| Document | Description |
|----------|-------------|
| [**Terraform README**](terraform/README.md) | Infrastructure as Code setup, variables, and deployment guides |

### Additional Resources

- **OpenAPI Specification**: Available at `/docs/openapi.yaml`
- **Postman Collection**: Import from `/docs/postman/collection.json`
- **Architecture Decision Records**: Located in `/docs/adr/`

---

## Development Setup

### Local Development Environment

#### 1. Set Up Local DynamoDB

```bash
# Using Docker
docker run -d -p 8000:8000 amazon/dynamodb-local

# Verify DynamoDB is running
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

#### 2. Create Local Tables

```bash
# Create the categories table locally
aws dynamodb create-table \
  --table-name categories-local \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

#### 3. Configure Environment Variables

Create a `.env.local` file:

```bash
# .env.local
AWS_REGION=us-east-1
DYNAMODB_ENDPOINT=http://localhost:8000
TABLE_NAME=categories-local
LOG_LEVEL=DEBUG
```

#### 4. Run Lambda Functions Locally (SAM CLI)

```bash
# Build the functions
sam build

# Start local API
sam local start-api --env-vars .env.local

# Test locally
curl http://localhost:3000/v1/organizations/test-org/categories
```

### Running Tests

```bash
# Unit tests
make test-unit

# Integration tests (requires local DynamoDB)
make test-integration

# All tests with coverage
make test-coverage
```

### Code Quality

```bash
# Run linters
make lint

# Format code
make format

# Security scan
make security-scan
```

### Deployment Pipeline

The service uses a GitOps workflow:

```
feature/* branch → PR → main branch → dev → staging → production
                    ↓
              Automated Tests
              Code Review Required
```

---

## Related Services

The aws-insight-category-api integrates with several other services in the AWS Insight platform:

| Service | Relationship | Description |
|---------|--------------|-------------|
| **aws-insight-auth-api** | Upstream | Provides JWT token validation and user context |
| **aws-insight-resource-api** | Consumer | Uses categories to tag and organize resources |
| **aws-insight-report-api** | Consumer | Associates reports with categories |
| **aws-insight-notification-api** | Subscriber | Receives category change events via DynamoDB Streams |
| **aws-insight-frontend** | Client | Primary UI consumer of the Category API |

### Event Integration

This service publishes events to DynamoDB Streams for the following operations:

- `CATEGORY_CREATED`
- `CATEGORY_UPDATED`
- `CATEGORY_DELETED`
- `TEMPLATE_APPLIED`

Downstream services can subscribe to these events for real-time synchronization.

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Refresh your JWT token |
| `403 Forbidden` | Insufficient permissions | Verify organization membership |
| `404 Not Found` | Category doesn't exist | Check category ID and organization scope |
| `429 Too Many Requests` | Rate limit exceeded | Implement exponential backoff |

### Getting Help

- **Slack**: `#aws-insight-support`
- **Email**: platform-team@example.com
- **Issue Tracker**: [GitHub Issues](https://github.com/your-org/aws-insight-category-api/issues)

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development workflow
- Pull request process
- Coding standards

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>Built with ❤️ by the AWS Insight Platform Team</strong>
</p>