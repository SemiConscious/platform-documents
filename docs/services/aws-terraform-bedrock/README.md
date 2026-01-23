# AWS Terraform Bedrock Module

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.0-623CE4?style=flat-square&logo=terraform)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Multi-Region](https://img.shields.io/badge/Multi--Region-Supported-success?style=flat-square)](docs/regions.md)

A production-ready Terraform module for deploying and managing AWS Bedrock GenAI infrastructure across multiple regions. This module provides comprehensive configuration for inference profiles, cross-region inference, AI safety guardrails, and CloudWatch monitoring.

---

## Overview

The `aws-terraform-bedrock` module simplifies the deployment of AWS Bedrock generative AI services by providing a unified, declarative approach to infrastructure management. Whether you're deploying Claude models for conversational AI, embedding models for semantic search, or custom AI applications, this module handles the complexity of multi-region deployments, safety guardrails, and operational monitoring.

### What This Module Provides

| Capability | Description |
|------------|-------------|
| **Multi-Region Deployment** | Deploy Bedrock resources across multiple AWS regions with consistent configuration |
| **Inference Profiles** | Configure application inference profiles for optimized global model access |
| **Cross-Region Inference** | Enable seamless failover and load distribution across regions |
| **AI Safety Guardrails** | Implement content filtering, topic restrictions, and PII detection |
| **Monitoring & Alerting** | CloudWatch dashboards, metrics, and alarms for Bedrock operations |
| **Model Support** | Full support for Claude, Amazon Titan, and embedding models |

### Key Benefits

- **Infrastructure as Code**: Version-controlled, repeatable deployments
- **Production-Ready**: Built-in best practices for security, monitoring, and resilience
- **Flexible Configuration**: Modular design allows selective feature enablement
- **Compliance-Friendly**: Guardrails support regulatory and organizational AI policies

---

## Prerequisites

Before deploying this module, ensure you have the following:

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Terraform | >= 1.0.0 | Infrastructure provisioning |
| AWS CLI | >= 2.0 | AWS authentication and testing |
| Git | Latest | Repository management |

### AWS Requirements

1. **AWS Account** with appropriate permissions
2. **Bedrock Model Access** enabled in target regions
3. **IAM Permissions** for Bedrock, CloudWatch, and IAM resources

```bash
# Verify AWS CLI configuration
aws sts get-caller-identity

# Check Bedrock access in your region
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[*].modelId'
```

### Required IAM Permissions

Your deployment role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:PutDashboard",
        "cloudwatch:DeleteDashboard",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Quick Start

Get up and running with AWS Bedrock infrastructure in minutes.

### Step 1: Clone the Module

```bash
git clone <repository-url> aws-terraform-bedrock
cd aws-terraform-bedrock
```

### Step 2: Configure Variables

Create a `terraform.tfvars` file with your configuration:

```hcl
# terraform.tfvars

# Project Configuration
project_name = "my-genai-platform"
environment  = "production"

# Primary deployment region
primary_region = "us-east-1"

# Enable multi-region deployment
enable_multi_region = true
secondary_regions   = ["us-west-2", "eu-west-1"]

# Model Configuration
enabled_models = [
  "anthropic.claude-3-sonnet-20240229-v1:0",
  "anthropic.claude-3-haiku-20240307-v1:0",
  "amazon.titan-embed-text-v1"
]

# Enable features
enable_guardrails = true
enable_monitoring = true
enable_cross_region_inference = true

# Tags
tags = {
  Project     = "GenAI Platform"
  ManagedBy   = "Terraform"
  Environment = "production"
}
```

### Step 3: Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Review the execution plan
terraform plan -out=tfplan

# Apply the configuration
terraform apply tfplan
```

### Step 4: Verify Deployment

```bash
# View outputs
terraform output

# Test Bedrock access
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --region us-east-1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello!"}]}' \
  --cli-binary-format raw-in-base64-out \
  output.json
```

---

## Module Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AWS Terraform Bedrock Module                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   US-EAST-1     │    │   US-WEST-2     │    │   EU-WEST-1     │        │
│  │   (Primary)     │◄──►│   (Secondary)   │◄──►│   (Secondary)   │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                  │
│  ┌────────▼────────────────────────────────────────────▼────────┐         │
│  │                   Cross-Region Inference                      │         │
│  │              (Automatic Failover & Load Balancing)            │         │
│  └───────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────┐         │
│  │                    Inference Profiles                          │         │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │         │
│  │  │   Claude    │  │   Titan     │  │   Embedding Models  │   │         │
│  │  │   Models    │  │   Models    │  │                     │   │         │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │         │
│  └───────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  ┌─────────────────────────┐    ┌────────────────────────────────┐        │
│  │      Guardrails         │    │        CloudWatch Monitoring   │        │
│  │  ┌──────────────────┐   │    │  ┌─────────────────────────┐  │        │
│  │  │ Content Filters  │   │    │  │ Dashboards & Metrics    │  │        │
│  │  │ Topic Policies   │   │    │  │ Alarms & Notifications  │  │        │
│  │  │ PII Detection    │   │    │  │ Log Insights            │  │        │
│  │  │ Word Filters     │   │    │  └─────────────────────────┘  │        │
│  │  └──────────────────┘   │    └────────────────────────────────┘        │
│  └─────────────────────────┘                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Module Structure

```
aws-terraform-bedrock/
├── main.tf                    # Root module configuration
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output definitions
├── versions.tf                # Provider version constraints
├── terraform.tfvars.example   # Example configuration
│
├── modules/
│   ├── inference-profiles/    # Inference profile configurations
│   ├── guardrails/            # AI safety guardrail resources
│   ├── monitoring/            # CloudWatch monitoring setup
│   └── cross-region/          # Cross-region inference config
│
├── docs/                      # Detailed documentation
│   ├── deployment.md
│   ├── inference-profiles.md
│   ├── guardrails.md
│   ├── monitoring.md
│   └── regions.md
│
└── examples/                  # Example configurations
    ├── basic/
    ├── multi-region/
    └── enterprise/
```

---

## Supported Regions

AWS Bedrock is available in select regions. This module supports deployment to the following:

| Region | Code | Claude Models | Titan Models | Embedding | Cross-Region |
|--------|------|:-------------:|:------------:|:---------:|:------------:|
| US East (N. Virginia) | `us-east-1` | ✅ | ✅ | ✅ | ✅ |
| US West (Oregon) | `us-west-2` | ✅ | ✅ | ✅ | ✅ |
| EU (Frankfurt) | `eu-central-1` | ✅ | ✅ | ✅ | ✅ |
| EU (Ireland) | `eu-west-1` | ✅ | ✅ | ✅ | ✅ |
| Asia Pacific (Tokyo) | `ap-northeast-1` | ✅ | ✅ | ✅ | ✅ |
| Asia Pacific (Singapore) | `ap-southeast-1` | ✅ | ✅ | ✅ | ✅ |

> **Note**: Model availability varies by region. See [Regional Configuration](docs/regions.md) for detailed availability matrices.

---

## Configuration Examples

### Basic Single-Region Deployment

```hcl
module "bedrock" {
  source = "./aws-terraform-bedrock"

  project_name   = "my-ai-app"
  environment    = "development"
  primary_region = "us-east-1"

  enabled_models = [
    "anthropic.claude-3-haiku-20240307-v1:0"
  ]

  enable_guardrails = false
  enable_monitoring = true
}
```

### Enterprise Multi-Region with Full Features

```hcl
module "bedrock_enterprise" {
  source = "./aws-terraform-bedrock"

  project_name        = "enterprise-genai"
  environment         = "production"
  primary_region      = "us-east-1"
  enable_multi_region = true
  secondary_regions   = ["us-west-2", "eu-west-1", "ap-northeast-1"]

  enabled_models = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "amazon.titan-embed-text-v1",
    "amazon.titan-text-express-v1"
  ]

  # Guardrails Configuration
  enable_guardrails = true
  guardrail_config = {
    content_filter_strength = "HIGH"
    enable_pii_detection    = true
    blocked_topics          = ["violence", "illegal_activities"]
    word_filters            = ["competitor_name"]
  }

  # Monitoring Configuration
  enable_monitoring = true
  monitoring_config = {
    create_dashboard      = true
    enable_alarms         = true
    alarm_sns_topic_arn   = "arn:aws:sns:us-east-1:123456789012:alerts"
    latency_threshold_ms  = 5000
    error_rate_threshold  = 0.05
  }

  # Cross-Region Inference
  enable_cross_region_inference = true
  inference_config = {
    failover_enabled      = true
    load_balancing_policy = "latency-based"
  }

  tags = {
    Project     = "Enterprise GenAI"
    CostCenter  = "AI-001"
    Compliance  = "SOC2"
  }
}
```

---

## Documentation

Comprehensive documentation is available for all aspects of this module:

| Document | Description |
|----------|-------------|
| [📘 Deployment Guide](docs/deployment.md) | Complete deployment instructions, prerequisites, and step-by-step setup |
| [🔧 Inference Profiles Configuration](docs/inference-profiles.md) | Configure application inference profiles for optimized model access |
| [🛡️ Guardrails Configuration](docs/guardrails.md) | AI safety guardrails, content filtering, and compliance controls |
| [📊 Monitoring Configuration](docs/monitoring.md) | CloudWatch dashboards, metrics, alarms, and observability setup |
| [🌍 Regional Configuration](docs/regions.md) | Multi-region deployment, failover strategies, and regional limitations |

---

## Outputs

After deployment, the module provides these outputs:

```hcl
# View all outputs
terraform output

# Key outputs include:
# - inference_profile_arns   : ARNs for created inference profiles
# - guardrail_ids            : IDs of deployed guardrails
# - dashboard_urls           : CloudWatch dashboard URLs
# - cross_region_endpoints   : Endpoints for cross-region inference
```

---

## Related Resources

### AWS Documentation
- [AWS Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Bedrock API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)

### Terraform Resources
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)

### Model Documentation
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Amazon Titan Models](https://aws.amazon.com/bedrock/titan/)

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Model access denied | Ensure Bedrock model access is enabled in AWS Console |
| Region not supported | Verify region supports required models |
| Quota exceeded | Request quota increase via AWS Support |
| Guardrail validation failed | Review guardrail configuration syntax |

For detailed troubleshooting, see the [Deployment Guide](docs/deployment.md#troubleshooting).

---

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

## License

This module is released under the MIT License. See [LICENSE](LICENSE) for details.