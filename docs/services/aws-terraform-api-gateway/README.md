# AWS API Gateway Terraform Module

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.0-623CE4?logo=terraform)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-API%20Gateway-FF9900?logo=amazon-aws)](https://aws.amazon.com/api-gateway/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Multi-Region](https://img.shields.io/badge/Regions-8%20Supported-green)](docs/architecture.md)

A production-ready Terraform module for provisioning AWS API Gateway account-level resources across multiple regions, enabling seamless API Gateway deployments in supported AWS regions with centralized CloudWatch logging configuration.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Supported Regions](#supported-regions)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Module Architecture](#module-architecture)
- [Usage Examples](#usage-examples)
- [Documentation](#documentation)
- [Related Modules](#related-modules)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

The `aws-terraform-api-gateway` module provides a standardized approach to configuring AWS API Gateway account-level settings across your AWS infrastructure. Unlike individual API configurations, this module focuses on the foundational account-level resources that must be in place before deploying API Gateway instances.

### What This Module Does

API Gateway requires certain account-level configurations to function properly, particularly for CloudWatch logging integration. This module handles:

1. **IAM Role Creation**: Sets up the required IAM role that allows API Gateway to write logs to CloudWatch
2. **Account Settings Configuration**: Configures the API Gateway account settings in each region
3. **Multi-Region Support**: Provides consistent configuration across 8 AWS regions globally
4. **Logging Infrastructure**: Ensures CloudWatch logging is properly configured for API Gateway access and execution logs

### Why Use This Module?

- **Consistency**: Ensures uniform API Gateway configuration across all regions
- **Compliance**: Centralizes logging configuration for audit and compliance requirements
- **Automation**: Eliminates manual setup steps that are often forgotten or misconfigured
- **Reusability**: Modular design allows selective regional deployment

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🌍 **Multi-Region Support** | Deploy account-level resources across 8 AWS regions simultaneously |
| 📊 **CloudWatch Integration** | Automatic IAM role setup for API Gateway logging to CloudWatch |
| 🔧 **Modular Architecture** | Reusable `api-gateway` submodule for custom configurations |
| 🔒 **Security Best Practices** | Follows AWS security recommendations for IAM permissions |
| 📝 **Infrastructure as Code** | Version-controlled, repeatable infrastructure deployment |

---

## Supported Regions

This module supports API Gateway account configuration in the following AWS regions:

| Region Code | Region Name | Geographic Area |
|-------------|-------------|-----------------|
| `us-east-1` | N. Virginia | North America |
| `us-east-2` | Ohio | North America |
| `us-west-1` | N. California | North America |
| `us-west-2` | Oregon | North America |
| `eu-west-1` | Ireland | Europe |
| `eu-west-2` | London | Europe |
| `eu-central-1` | Frankfurt | Europe |
| `ap-southeast-1` | Singapore | Asia Pacific |

> **Note**: Additional regions can be added by extending the module configuration. See the [Architecture and Design](docs/architecture.md) documentation for details.

---

## Prerequisites

Before using this module, ensure you have the following:

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Terraform | >= 1.0.0 | Infrastructure provisioning |
| AWS CLI | >= 2.0 | AWS authentication and testing |

### AWS Requirements

- **AWS Account**: Active AWS account with appropriate permissions
- **IAM Permissions**: Ability to create IAM roles and configure API Gateway settings
- **AWS Credentials**: Configured via environment variables, AWS CLI profile, or instance role

### Required IAM Permissions

The user or role executing this Terraform module needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:PATCH",
        "apigateway:UpdateAccount"
      ],
      "Resource": "arn:aws:apigateway:*::/account"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/api-gateway-cloudwatch-*"
    }
  ]
}
```

---

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/aws-terraform-api-gateway.git
cd aws-terraform-api-gateway
```

### Step 2: Configure AWS Credentials

Ensure your AWS credentials are configured:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Option 2: AWS CLI profile
aws configure --profile your-profile
export AWS_PROFILE="your-profile"
```

### Step 3: Create Your Terraform Configuration

Create a new file called `main.tf`:

```hcl
# main.tf - API Gateway Account Configuration

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

# Primary region provider
provider "aws" {
  region = "us-east-1"
  alias  = "us_east_1"
}

# Additional region provider
provider "aws" {
  region = "eu-west-1"
  alias  = "eu_west_1"
}

# Deploy API Gateway account settings to US East 1
module "api_gateway_us_east_1" {
  source = "./modules/api-gateway"
  
  providers = {
    aws = aws.us_east_1
  }
  
  environment              = "production"
  enable_cloudwatch_logs   = true
  cloudwatch_role_name     = "api-gateway-cloudwatch-us-east-1"
  
  tags = {
    Project     = "api-infrastructure"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Deploy API Gateway account settings to EU West 1
module "api_gateway_eu_west_1" {
  source = "./modules/api-gateway"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  environment              = "production"
  enable_cloudwatch_logs   = true
  cloudwatch_role_name     = "api-gateway-cloudwatch-eu-west-1"
  
  tags = {
    Project     = "api-infrastructure"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

### Step 4: Initialize and Apply

```bash
# Initialize Terraform and download providers
terraform init

# Preview the changes
terraform plan

# Apply the configuration
terraform apply
```

### Step 5: Verify Deployment

```bash
# Check API Gateway account settings in each region
aws apigateway get-account --region us-east-1
aws apigateway get-account --region eu-west-1
```

---

## Module Architecture

The module follows a hierarchical structure designed for flexibility and reusability:

```
aws-terraform-api-gateway/
├── main.tf                    # Root module orchestration
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output value definitions
├── versions.tf                # Terraform and provider versions
├── modules/
│   └── api-gateway/           # Reusable API Gateway submodule
│       ├── main.tf            # API Gateway account resources
│       ├── iam.tf             # IAM role for CloudWatch
│       ├── variables.tf       # Submodule variables
│       └── outputs.tf         # Submodule outputs
├── examples/
│   ├── single-region/         # Single region deployment example
│   ├── multi-region/          # Multi-region deployment example
│   └── complete/              # Full configuration example
└── docs/
    ├── deployment-guide.md    # Detailed deployment instructions
    ├── variables-reference.md # Variables and outputs reference
    └── architecture.md        # Architecture documentation
```

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Root Module                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Provider Configuration                   │  │
│  │   (Multiple AWS providers for each target region)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ api-gateway │     │ api-gateway │     │ api-gateway │       │
│  │ us-east-1   │     │ eu-west-1   │     │ ap-south-1  │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                    │                    │             │
└─────────┼────────────────────┼────────────────────┼─────────────┘
          ▼                    ▼                    ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │ IAM Role    │     │ IAM Role    │     │ IAM Role    │
   │ CloudWatch  │     │ CloudWatch  │     │ CloudWatch  │
   │ API Gateway │     │ API Gateway │     │ API Gateway │
   │ Account     │     │ Account     │     │ Account     │
   └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Usage Examples

### Basic Single-Region Deployment

```hcl
module "api_gateway" {
  source = "github.com/your-org/aws-terraform-api-gateway//modules/api-gateway"
  
  environment            = "production"
  enable_cloudwatch_logs = true
  
  tags = {
    Environment = "production"
  }
}
```

### Multi-Region Deployment with Custom Configuration

```hcl
locals {
  regions = {
    us_east_1 = {
      region = "us-east-1"
      name   = "primary"
    }
    eu_west_1 = {
      region = "eu-west-1"
      name   = "europe"
    }
    ap_southeast_1 = {
      region = "ap-southeast-1"
      name   = "asia"
    }
  }
}

# Generate providers dynamically
provider "aws" {
  for_each = local.regions
  alias    = each.key
  region   = each.value.region
}

module "api_gateway" {
  for_each = local.regions
  source   = "./modules/api-gateway"
  
  providers = {
    aws = aws[each.key]
  }
  
  environment              = "production"
  enable_cloudwatch_logs   = true
  cloudwatch_role_name     = "api-gateway-cloudwatch-${each.value.name}"
  
  tags = {
    Region      = each.value.region
    Environment = "production"
  }
}
```

### Integration with Existing Infrastructure

```hcl
# Use existing IAM role for CloudWatch
data "aws_iam_role" "existing_cloudwatch_role" {
  name = "existing-api-gateway-cloudwatch-role"
}

module "api_gateway" {
  source = "./modules/api-gateway"
  
  environment               = "production"
  enable_cloudwatch_logs    = true
  create_cloudwatch_role    = false
  cloudwatch_role_arn       = data.aws_iam_role.existing_cloudwatch_role.arn
  
  tags = {
    Environment = "production"
  }
}
```

---

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [📦 Deployment Guide](docs/deployment-guide.md) | Step-by-step instructions for deploying this module in various scenarios |
| [📋 Variables and Outputs Reference](docs/variables-reference.md) | Complete reference for all input variables and output values |
| [🏗️ Architecture and Design](docs/architecture.md) | Detailed architecture diagrams and design decisions |

### Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [CloudWatch Logs for API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)

---

## Related Modules

This module works well with the following Terraform modules:

| Module | Description |
|--------|-------------|
| `aws-terraform-vpc` | VPC infrastructure for private API endpoints |
| `aws-terraform-route53` | DNS configuration for custom domain names |
| `aws-terraform-acm` | SSL/TLS certificates for API Gateway |
| `aws-terraform-waf` | Web Application Firewall for API protection |
| `aws-terraform-lambda` | Lambda functions as API Gateway backends |

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "CloudWatch Logs role ARN must be set in account settings"

**Cause**: The API Gateway account settings don't have a CloudWatch role configured.

**Solution**: Ensure `enable_cloudwatch_logs` is set to `true`:

```hcl
module "api_gateway" {
  source                 = "./modules/api-gateway"
  enable_cloudwatch_logs = true
  # ...
}
```

#### Issue: "AccessDenied when assuming CloudWatch role"

**Cause**: The IAM role trust policy doesn't allow API Gateway to assume it.

**Solution**: Verify the trust relationship includes API Gateway:

```hcl
# The module automatically configures this, but verify:
data "aws_iam_policy_document" "api_gateway_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}
```

#### Issue: "Resource already exists in another region"

**Cause**: IAM roles are global resources; using the same name across regions causes conflicts.

**Solution**: Use region-specific role names:

```hcl
cloudwatch_role_name = "api-gateway-cloudwatch-${var.region}"
```

### Getting Help

- Check the [Variables Reference](docs/variables-reference.md) for configuration options
- Review the [Architecture Guide](docs/architecture.md) for design context
- Open an issue on GitHub for bugs or feature requests

---

## Contributing

We welcome contributions! Please see our contributing guidelines for details on:

- Code style and formatting
- Testing requirements
- Pull request process

---

## License

This module is released under the MIT License. See [LICENSE](LICENSE) for details.

---

**Maintained by the Platform Engineering Team** | [Report an Issue](https://github.com/your-org/aws-terraform-api-gateway/issues)