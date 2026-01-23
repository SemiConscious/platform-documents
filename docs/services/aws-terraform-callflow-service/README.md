# Callflow Service Terraform Module

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.0-623CE4?logo=terraform)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Provider-FF9900?logo=amazonaws)](https://aws.amazon.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/)

## Overview

The **Callflow Service Terraform Module** provisions a complete AWS-based service for storing and retrieving call flow events. This serverless architecture leverages API Gateway, Lambda functions, and S3 storage to provide a scalable, cost-effective solution for managing telephony call flow data.

### What is the Callflow Service?

The Callflow Service enables applications to:

- **Store call flow events** — Capture and persist call flow data from telephony systems
- **Retrieve call flow events** — Query and access historical call flow information via REST API
- **Authenticate requests** — Secure API access through Lambda-based authorization
- **Monitor operations** — Track service health with CloudWatch dashboards and alarms

This module is designed for **operators** who need to deploy and manage the Callflow Service infrastructure in AWS environments.

### Key Features

| Feature | Description |
|---------|-------------|
| **API Gateway (OpenAPI 3.0)** | RESTful API with OpenAPI specification for standardized integration |
| **Lambda Authorizer** | Custom authentication logic for secure API access |
| **Event Storer Lambda** | Processes and persists incoming call flow events |
| **Event Retriever Lambda** | Handles queries and returns call flow data |
| **S3 Storage Backend** | Durable, scalable storage for call flow events |
| **CloudWatch Logging** | JSON-formatted logs for easy parsing and analysis |
| **CloudWatch Alarms** | Automated alerting for service health issues |
| **CloudWatch Dashboard** | Visual monitoring of key service metrics |
| **DNS Configuration** | Custom domain support for API endpoints |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Callflow Service Architecture                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────┐      ┌─────────────────┐      ┌────────────────────┐        │
│    │  Client  │─────▶│   Route 53      │─────▶│    API Gateway     │        │
│    │  Apps    │      │   (DNS)         │      │   (OpenAPI 3.0)    │        │
│    └──────────┘      └─────────────────┘      └─────────┬──────────┘        │
│                                                         │                    │
│                                               ┌─────────▼──────────┐        │
│                                               │  Lambda Authorizer │        │
│                                               │  (Authentication)  │        │
│                                               └─────────┬──────────┘        │
│                                                         │                    │
│                            ┌────────────────────────────┴───────────┐       │
│                            │                                        │       │
│                  ┌─────────▼─────────┐              ┌───────────────▼────┐  │
│                  │   Event Storer    │              │   Event Retriever  │  │
│                  │     Lambda        │              │       Lambda       │  │
│                  └─────────┬─────────┘              └───────────┬────────┘  │
│                            │                                    │           │
│                            └────────────────┬───────────────────┘           │
│                                             │                               │
│                                   ┌─────────▼─────────┐                     │
│                                   │    S3 Bucket      │                     │
│                                   │  (Event Storage)  │                     │
│                                   └───────────────────┘                     │
│                                                                              │
│    ┌────────────────────────────────────────────────────────────────────┐   │
│    │                         CloudWatch                                  │   │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│    │  │    Logs      │  │   Alarms     │  │  Dashboard   │              │   │
│    │  │ (JSON format)│  │  (Alerts)    │  │ (Monitoring) │              │   │
│    │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│    └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pre-requisites

Before deploying the Callflow Service, ensure you have the following:

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| [Terraform](https://www.terraform.io/downloads) | >= 1.0.0 | Infrastructure provisioning |
| [AWS CLI](https://aws.amazon.com/cli/) | >= 2.0 | AWS authentication and management |
| [Git](https://git-scm.com/) | >= 2.0 | Source control |

### AWS Requirements

- **AWS Account** with appropriate permissions
- **IAM credentials** configured locally (via `aws configure` or environment variables)
- **S3 bucket** for Terraform state (recommended for production)
- **Route 53 hosted zone** (if using custom DNS)

### Required IAM Permissions

The deploying user/role needs permissions for:

```
- apigateway:*
- lambda:*
- s3:*
- logs:*
- cloudwatch:*
- iam:*
- route53:* (if using DNS configuration)
```

> **Note:** For production environments, scope these permissions appropriately using least-privilege principles.

### Verify Prerequisites

```bash
# Check Terraform version
terraform version
# Expected: Terraform v1.x.x

# Verify AWS CLI configuration
aws sts get-caller-identity
# Expected: JSON output with Account, UserId, and Arn

# Test AWS permissions
aws lambda list-functions --max-items 1
# Expected: No permission errors
```

---

## Quick Start

Get the Callflow Service running in your AWS environment with these steps:

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd aws-terraform-callflow-service
```

### Step 2: Configure Backend (Recommended)

Create a `backend.tf` file for remote state management:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "callflow-service/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Step 3: Create Variable Definitions

Create a `terraform.tfvars` file with your configuration:

```hcl
# terraform.tfvars

# Required Variables
environment     = "dev"
project_name    = "callflow"
aws_region      = "us-east-1"

# S3 Configuration
s3_bucket_name  = "callflow-events-dev"

# API Gateway Configuration
api_gateway_stage_name = "v1"

# DNS Configuration (optional)
domain_name     = "callflow-api.example.com"
hosted_zone_id  = "Z1234567890ABC"

# Logging Configuration
log_retention_days = 30

# Alarm Configuration
alarm_sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:alerts"

# Tags
tags = {
  Environment = "dev"
  Project     = "callflow"
  ManagedBy   = "terraform"
}
```

### Step 4: Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of hashicorp/aws...
- Installing hashicorp/aws v5.x.x...

Terraform has been successfully initialized!
```

### Step 5: Review the Execution Plan

```bash
terraform plan -out=tfplan
```

Review the planned changes carefully. You should see resources for:
- API Gateway REST API and resources
- Lambda functions (Authorizer, Event Storer, Event Retriever)
- S3 bucket for event storage
- IAM roles and policies
- CloudWatch log groups, alarms, and dashboard
- Route 53 records (if DNS configured)

### Step 6: Apply the Configuration

```bash
terraform apply tfplan
```

Type `yes` when prompted to confirm the deployment.

### Step 7: Verify Deployment

```bash
# Get the API endpoint
terraform output api_gateway_endpoint

# Test the health endpoint (adjust based on your API)
curl -X GET "$(terraform output -raw api_gateway_endpoint)/health"
```

---

## Module Dependencies

This module requires the following Terraform providers:

```hcl
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0.0"
    }
  }
}
```

### External Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| AWS Provider | Core AWS resource management | Yes |
| Random Provider | Generate unique resource names | Yes |
| Archive Provider | Package Lambda function code | Yes |

---

## Module Outputs

After successful deployment, the module provides the following outputs:

```hcl
# Key outputs available after deployment
output "api_gateway_endpoint"     # Base URL for the API
output "api_gateway_id"           # API Gateway ID
output "s3_bucket_name"           # Name of the events storage bucket
output "s3_bucket_arn"            # ARN of the events storage bucket
output "lambda_authorizer_arn"    # ARN of the authorizer function
output "lambda_storer_arn"        # ARN of the event storer function
output "lambda_retriever_arn"     # ARN of the event retriever function
output "cloudwatch_dashboard_url" # URL to the monitoring dashboard
```

Retrieve outputs after deployment:

```bash
# List all outputs
terraform output

# Get specific output
terraform output api_gateway_endpoint
```

---

## Documentation Index

For comprehensive information about the Callflow Service, refer to the following documentation:

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture.md) | Detailed system architecture, component interactions, and design decisions |
| [Deployment Guide](docs/deployment.md) | Step-by-step deployment instructions for various environments |
| [Configuration Reference](docs/configuration.md) | Complete reference of all input variables and configuration options |
| [API Specification](docs/api-specification.md) | OpenAPI 3.0 specification with endpoint details and examples |
| [Operations Guide](docs/operations.md) | Day-to-day operations, monitoring, troubleshooting, and maintenance |

---

## Common Operations

### Update the Service

```bash
# Pull latest changes
git pull origin main

# Review and apply changes
terraform plan -out=tfplan
terraform apply tfplan
```

### View Logs

```bash
# View Lambda logs via AWS CLI
aws logs tail /aws/lambda/callflow-event-storer --follow

# View API Gateway access logs
aws logs tail /aws/apigateway/callflow-api --follow
```

### Destroy Resources

```bash
# WARNING: This destroys all resources including stored data
terraform destroy
```

---

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| `Error: No valid credential sources` | AWS credentials not configured | Run `aws configure` or set environment variables |
| `Error: S3 bucket already exists` | Bucket name collision | Choose a unique `s3_bucket_name` |
| `Error: Access Denied` | Insufficient IAM permissions | Verify IAM policy includes required permissions |
| `Error: InvalidDomainName` | Route 53 hosted zone not found | Verify `hosted_zone_id` is correct |

### Getting Help

1. Check the [Operations Guide](docs/operations.md) for detailed troubleshooting
2. Review CloudWatch logs for error details
3. Open an issue in the repository with:
   - Terraform version (`terraform version`)
   - Error message
   - Relevant configuration (sanitized)

---

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.