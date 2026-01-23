# terraform-ecs Module Overview

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.0-623CE4?style=flat&logo=terraform)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-ECS-FF9900?style=flat&logo=amazon-aws)](https://aws.amazon.com/ecs/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A production-ready Terraform module that provisions common resources required for AWS Elastic Container Service (ECS), including a comprehensive debugging toolkit task definition for troubleshooting containerized applications in your AWS environment.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Module Architecture](#module-architecture)
- [Usage Examples](#usage-examples)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Support](#support)

---

## Introduction

The `aws-terraform-ecs` module simplifies the deployment and management of AWS ECS infrastructure by providing a reusable, well-structured Terraform module. Whether you're setting up a new ECS cluster from scratch or need reliable debugging capabilities for existing containerized workloads, this module provides the foundational resources you need.

### Why Use This Module?

Managing ECS infrastructure manually can be complex and error-prone. This module addresses common operational challenges by:

- **Standardizing Infrastructure**: Provides consistent, repeatable ECS cluster deployments across environments
- **Enabling Quick Troubleshooting**: Includes pre-configured debug toolkit task definitions for rapid issue diagnosis
- **Following Best Practices**: Implements AWS and Terraform best practices out of the box
- **Reducing Boilerplate**: Eliminates the need to write repetitive ECS resource configurations

### Target Audience

This module is designed primarily for **operators** and DevOps engineers who:

- Manage containerized applications on AWS ECS
- Need reliable debugging tools for production environments
- Want to standardize ECS deployments across multiple projects or teams
- Require infrastructure-as-code solutions for compliance and auditability

---

## Features

| Feature | Description |
|---------|-------------|
| **ECS Cluster Provisioning** | Complete ECS cluster infrastructure with configurable settings for capacity providers, container insights, and tagging |
| **Debug Toolkit Task Definition** | Pre-configured task definition with essential debugging tools for troubleshooting containerized applications |
| **Reusable Module Structure** | Clean, modular Terraform code that can be easily integrated into existing infrastructure |
| **AWS ECS Resource Management** | Comprehensive management of ECS-related resources including task definitions, services, and IAM roles |
| **Multi-Environment Support** | Easily deploy to development, staging, and production environments with variable-driven configuration |
| **Container Insights Integration** | Built-in support for CloudWatch Container Insights for monitoring and observability |

---

## Prerequisites

Before using this module, ensure you have the following installed and configured:

### Required Tools

| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| Terraform | >= 1.0.0 | Infrastructure provisioning |
| AWS CLI | >= 2.0 | AWS authentication and debugging |
| Docker | >= 20.10 | Container runtime (for local testing) |

### AWS Requirements

- **AWS Account** with appropriate permissions to create ECS resources
- **IAM Credentials** configured via AWS CLI, environment variables, or IAM roles
- **VPC and Subnets** (existing or to be created) for ECS cluster networking

### Required IAM Permissions

Your AWS credentials must have permissions for the following services:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Quick Start

Get up and running with the `aws-terraform-ecs` module in just a few steps.

### Step 1: Configure AWS Credentials

Ensure your AWS credentials are properly configured:

```bash
# Option 1: Use AWS CLI configuration
aws configure

# Option 2: Export environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-west-2"
```

### Step 2: Create Your Terraform Configuration

Create a new directory for your Terraform configuration and add the following files:

**`main.tf`**

```hcl
terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "ecs" {
  source = "github.com/your-org/aws-terraform-ecs"

  cluster_name           = var.cluster_name
  environment            = var.environment
  enable_container_insights = true
  enable_debug_toolkit   = true

  # VPC Configuration
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # Tagging
  tags = {
    Project     = "my-application"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

**`variables.tf`**

```hcl
variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "my-ecs-cluster"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "VPC ID for ECS cluster networking"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for ECS tasks"
  type        = list(string)
}
```

**`outputs.tf`**

```hcl
output "cluster_id" {
  description = "The ID of the ECS cluster"
  value       = module.ecs.cluster_id
}

output "cluster_arn" {
  description = "The ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "debug_task_definition_arn" {
  description = "ARN of the debug toolkit task definition"
  value       = module.ecs.debug_task_definition_arn
}
```

### Step 3: Initialize and Deploy

```bash
# Initialize Terraform and download providers
terraform init

# Preview the changes
terraform plan -var="vpc_id=vpc-xxxxxx" -var='subnet_ids=["subnet-xxxxxx", "subnet-yyyyyy"]'

# Apply the configuration
terraform apply -var="vpc_id=vpc-xxxxxx" -var='subnet_ids=["subnet-xxxxxx", "subnet-yyyyyy"]'
```

### Step 4: Verify Deployment

```bash
# List ECS clusters
aws ecs list-clusters

# Describe your new cluster
aws ecs describe-clusters --clusters my-ecs-cluster
```

---

## Module Architecture

The `aws-terraform-ecs` module provisions the following AWS resources:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Account                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      VPC                                   │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                 ECS Cluster                          │  │  │
│  │  │  ┌─────────────────┐  ┌─────────────────────────┐   │  │  │
│  │  │  │  Task           │  │  Debug Toolkit          │   │  │  │
│  │  │  │  Definitions    │  │  Task Definition        │   │  │  │
│  │  │  └─────────────────┘  └─────────────────────────┘   │  │  │
│  │  │                                                      │  │  │
│  │  │  ┌─────────────────┐  ┌─────────────────────────┐   │  │  │
│  │  │  │  IAM Roles      │  │  CloudWatch Log Groups  │   │  │  │
│  │  │  │  & Policies     │  │  (Container Insights)   │   │  │  │
│  │  │  └─────────────────┘  └─────────────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Resource Overview

| Resource | Description |
|----------|-------------|
| `aws_ecs_cluster` | Main ECS cluster with configurable settings |
| `aws_ecs_task_definition` | Task definitions including debug toolkit |
| `aws_iam_role` | Execution and task roles for ECS |
| `aws_iam_role_policy_attachment` | IAM policies for ECS operations |
| `aws_cloudwatch_log_group` | Log groups for container logging |

---

## Usage Examples

### Basic Cluster with Debug Toolkit

```hcl
module "ecs_basic" {
  source = "github.com/your-org/aws-terraform-ecs"

  cluster_name         = "basic-cluster"
  environment          = "dev"
  enable_debug_toolkit = true
  vpc_id               = "vpc-12345678"
  subnet_ids           = ["subnet-aaaaaaaa", "subnet-bbbbbbbb"]
}
```

### Production Cluster with Full Configuration

```hcl
module "ecs_production" {
  source = "github.com/your-org/aws-terraform-ecs"

  cluster_name              = "production-cluster"
  environment               = "prod"
  enable_container_insights = true
  enable_debug_toolkit      = true
  
  # Capacity provider configuration
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy = [
    {
      capacity_provider = "FARGATE"
      weight            = 1
      base              = 1
    },
    {
      capacity_provider = "FARGATE_SPOT"
      weight            = 4
      base              = 0
    }
  ]

  vpc_id     = data.aws_vpc.main.id
  subnet_ids = data.aws_subnets.private.ids

  tags = {
    Project     = "production-app"
    Environment = "prod"
    CostCenter  = "engineering"
    ManagedBy   = "terraform"
  }
}
```

### Running the Debug Toolkit

Once deployed, you can run the debug toolkit task to troubleshoot issues:

```bash
# Run debug toolkit task
aws ecs run-task \
  --cluster my-ecs-cluster \
  --task-definition debug-toolkit \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxx],securityGroups=[sg-xxxxxx],assignPublicIp=ENABLED}"

# Connect to the running task using ECS Exec
aws ecs execute-command \
  --cluster my-ecs-cluster \
  --task <task-id> \
  --container debug-toolkit \
  --interactive \
  --command "/bin/bash"
```

---

## Documentation

For detailed information on specific topics, refer to the following documentation:

| Document | Description |
|----------|-------------|
| [Usage Guide](docs/usage.md) | Comprehensive guide covering all usage scenarios and configuration options |
| [Input Variables Reference](docs/variables.md) | Complete reference for all module input variables with descriptions and defaults |
| [Outputs Reference](docs/outputs.md) | Documentation of all module outputs and how to use them |
| [Debugging Guide](docs/debugging.md) | In-depth guide for using the debug toolkit and troubleshooting ECS applications |

---

## Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository** and clone it locally
2. **Create a feature branch**: `git checkout -b feature/my-new-feature`
3. **Make your changes** following our coding standards
4. **Test thoroughly** using `terraform validate` and `terraform plan`
5. **Submit a pull request** with a clear description of your changes

### Development Guidelines

```bash
# Validate Terraform configuration
terraform fmt -check -recursive
terraform validate

# Run pre-commit hooks (if configured)
pre-commit run --all-files
```

### Reporting Issues

When reporting issues, please include:

- Terraform version (`terraform version`)
- AWS provider version
- Relevant Terraform configuration (sanitized)
- Full error messages
- Steps to reproduce

---

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Ask questions and share ideas in GitHub Discussions
- **Security**: Report security vulnerabilities privately via security advisories

---

## License

This module is released under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ for the DevOps community</strong>
</p>