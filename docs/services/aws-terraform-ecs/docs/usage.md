# Usage Guide

## aws-terraform-ecs

This comprehensive guide provides operators with detailed instructions on how to effectively use the aws-terraform-ecs Terraform module to provision and manage AWS ECS infrastructure. Whether you're deploying a new ECS cluster from scratch or integrating debugging capabilities into an existing infrastructure, this guide covers all essential aspects of module usage.

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Module Source Configuration](#module-source-configuration)
3. [Provider Requirements](#provider-requirements)
4. [Example Configurations](#example-configurations)
5. [Integration with Existing Infrastructure](#integration-with-existing-infrastructure)
6. [Best Practices](#best-practices)

---

## Basic Usage

The aws-terraform-ecs module simplifies the provisioning of AWS ECS resources and includes a built-in debugging toolkit task definition for troubleshooting containerized applications. This section walks you through the fundamental steps to get started.

### Minimum Viable Configuration

At its core, using this module requires minimal configuration to deploy a basic ECS cluster:

```hcl
module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name = "my-application-cluster"
  environment  = "development"
  
  tags = {
    Project     = "my-application"
    ManagedBy   = "terraform"
    Environment = "development"
  }
}
```

### Understanding Module Outputs

After applying the module, you'll have access to several important outputs that can be used in other parts of your infrastructure:

```hcl
# Reference the ECS cluster ARN
output "cluster_arn" {
  description = "The ARN of the created ECS cluster"
  value       = module.ecs.cluster_arn
}

# Reference the debug toolkit task definition
output "debug_task_definition_arn" {
  description = "ARN of the debugging toolkit task definition"
  value       = module.ecs.debug_task_definition_arn
}
```

### Directory Structure

Organize your Terraform configuration following this recommended structure:

```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── production/
├── modules/
│   └── ecs/
└── README.md
```

---

## Module Source Configuration

The aws-terraform-ecs module can be sourced from various locations depending on your organization's infrastructure and security requirements.

### Git Repository Source

For most production deployments, reference the module from a Git repository with version pinning:

```hcl
# Using HTTPS with specific version tag
module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"
  # ... configuration
}

# Using SSH for private repositories
module "ecs" {
  source = "git::ssh://git@github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"
  # ... configuration
}

# Using a specific branch (not recommended for production)
module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=feature/new-capability"
  # ... configuration
}
```

### Terraform Registry Source

If the module is published to the Terraform Registry:

```hcl
module "ecs" {
  source  = "your-org/ecs/aws"
  version = "~> 1.0"
  # ... configuration
}
```

### Local Path Source

For development and testing purposes:

```hcl
module "ecs" {
  source = "../modules/aws-terraform-ecs"
  # ... configuration
}
```

### Version Constraints

Always use version constraints to ensure reproducible deployments:

```hcl
# Exact version (most restrictive)
source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

# Semantic versioning with pessimistic constraint
module "ecs" {
  source  = "your-org/ecs/aws"
  version = "~> 1.0"  # Allows 1.x but not 2.0
}
```

---

## Provider Requirements

The aws-terraform-ecs module requires specific provider configurations to function correctly.

### AWS Provider Configuration

```hcl
terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0, < 6.0.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "aws-terraform-ecs"
    }
  }
}
```

### Multi-Region Deployment

For multi-region setups, configure provider aliases:

```hcl
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

provider "aws" {
  alias  = "secondary"
  region = "us-west-2"
}

module "ecs_primary" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"
  
  providers = {
    aws = aws.primary
  }
  
  cluster_name = "primary-cluster"
  environment  = "production"
}

module "ecs_secondary" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"
  
  providers = {
    aws = aws.secondary
  }
  
  cluster_name = "secondary-cluster"
  environment  = "production"
}
```

### Authentication Methods

Configure AWS authentication based on your deployment environment:

```hcl
# Using environment variables (recommended for CI/CD)
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

# Using AWS profiles
provider "aws" {
  region  = "us-east-1"
  profile = "production"
}

# Using IAM role assumption
provider "aws" {
  region = "us-east-1"
  
  assume_role {
    role_arn     = "arn:aws:iam::123456789012:role/TerraformDeployRole"
    session_name = "terraform-ecs-deployment"
  }
}
```

---

## Example Configurations

This section provides comprehensive examples for various deployment scenarios.

### Development Environment

A lightweight configuration suitable for development and testing:

```hcl
module "ecs_dev" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name = "dev-cluster"
  environment  = "development"
  
  # Enable debug toolkit for troubleshooting
  enable_debug_toolkit = true
  
  # Minimal capacity for cost savings
  cluster_settings = {
    containerInsights = "disabled"
  }
  
  # Use Fargate Spot for cost optimization
  capacity_providers = ["FARGATE_SPOT"]
  
  default_capacity_provider_strategy = [
    {
      capacity_provider = "FARGATE_SPOT"
      weight           = 100
      base             = 0
    }
  ]
  
  tags = {
    Environment = "development"
    CostCenter  = "engineering"
  }
}
```

### Production Environment

A robust configuration with high availability and monitoring:

```hcl
module "ecs_production" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name = "production-cluster"
  environment  = "production"
  
  # Disable debug toolkit in production for security
  enable_debug_toolkit = false
  
  # Enable Container Insights for monitoring
  cluster_settings = {
    containerInsights = "enabled"
  }
  
  # Mixed capacity providers for reliability
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy = [
    {
      capacity_provider = "FARGATE"
      weight           = 70
      base             = 2  # Minimum 2 tasks on regular Fargate
    },
    {
      capacity_provider = "FARGATE_SPOT"
      weight           = 30
      base             = 0
    }
  ]
  
  # Enable execute command for debugging (controlled access)
  enable_execute_command = true
  
  # KMS encryption for logs
  kms_key_id = aws_kms_key.ecs_logs.arn
  
  tags = {
    Environment     = "production"
    CostCenter      = "operations"
    DataClassification = "confidential"
  }
}
```

### Debug Toolkit Usage

The module includes a pre-configured debugging task definition for troubleshooting:

```hcl
# Enable the debug toolkit
module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name         = "my-cluster"
  environment          = "staging"
  enable_debug_toolkit = true
  
  debug_toolkit_config = {
    cpu    = 256
    memory = 512
    image  = "amazonlinux:2"  # Or your custom debug image
    
    # Tools to install in the container
    install_packages = [
      "curl",
      "nslookup",
      "netcat",
      "tcpdump"
    ]
  }
}

# Run a debug task
# aws ecs run-task \
#   --cluster my-cluster \
#   --task-definition ${module.ecs.debug_task_definition_arn} \
#   --launch-type FARGATE \
#   --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

---

## Integration with Existing Infrastructure

Learn how to integrate the aws-terraform-ecs module with your existing AWS infrastructure.

### VPC Integration

Connect the ECS cluster to your existing VPC:

```hcl
# Reference existing VPC
data "aws_vpc" "existing" {
  tags = {
    Name = "production-vpc"
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }
  
  tags = {
    Tier = "private"
  }
}

module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name = "integrated-cluster"
  environment  = "production"
  
  vpc_id     = data.aws_vpc.existing.id
  subnet_ids = data.aws_subnets.private.ids
  
  # Security group configuration
  create_security_group = true
  security_group_rules = {
    ingress_http = {
      type        = "ingress"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = [data.aws_vpc.existing.cidr_block]
    }
  }
}
```

### ALB Integration

Integrate with an existing Application Load Balancer:

```hcl
data "aws_lb" "existing" {
  name = "production-alb"
}

data "aws_lb_listener" "https" {
  load_balancer_arn = data.aws_lb.existing.arn
  port              = 443
}

module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name = "web-cluster"
  environment  = "production"
  
  # ALB integration
  load_balancer_arn = data.aws_lb.existing.arn
  listener_arn      = data.aws_lb_listener.https.arn
}

# Create target group for your service
resource "aws_lb_target_group" "app" {
  name        = "app-target-group"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.existing.id
  target_type = "ip"
  
  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
  }
}
```

### Service Discovery Integration

Enable AWS Cloud Map service discovery:

```hcl
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "internal.local"
  description = "Private DNS namespace for service discovery"
  vpc         = data.aws_vpc.existing.id
}

module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"

  cluster_name = "microservices-cluster"
  environment  = "production"
  
  # Service discovery configuration
  enable_service_discovery   = true
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.main.id
}
```

---

## Best Practices

Follow these best practices to ensure secure, reliable, and cost-effective ECS deployments.

### Security Best Practices

1. **Use IAM Roles for Tasks**: Always assign specific IAM roles to your tasks rather than using instance profiles:

```hcl
resource "aws_iam_role" "task_execution" {
  name = "${var.cluster_name}-task-execution"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}
```

2. **Enable Encryption**: Always enable encryption for logs and data at rest:

```hcl
module "ecs" {
  source = "git::https://github.com/your-org/aws-terraform-ecs.git?ref=v1.0.0"
  
  # Enable encryption
  kms_key_id               = aws_kms_key.ecs.arn
  enable_encryption_at_rest = true
}
```

3. **Limit Debug Toolkit Access**: Only enable the debug toolkit in non-production environments or with strict access controls.

### Operational Best Practices

1. **Use Terraform State Locking**: Always use remote state with locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "ecs/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

2. **Implement Tagging Strategy**: Consistent tagging enables cost allocation and resource management:

```hcl
locals {
  common_tags = {
    Environment  = var.environment
    Project      = var.project_name
    ManagedBy    = "terraform"
    Owner        = var.team_email
    CostCenter   = var.cost_center
  }
}
```

3. **Monitor and Alert**: Integrate with CloudWatch for monitoring:

```hcl
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${module.ecs.cluster_name}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "ECS cluster CPU utilization is high"
  
  dimensions = {
    ClusterName = module.ecs.cluster_name
  }
}
```

### Cost Optimization

1. **Use Fargate Spot**: For fault-tolerant workloads, use Fargate Spot to reduce costs by up to 70%
2. **Right-size Tasks**: Regularly review and adjust CPU/memory allocations
3. **Enable Container Insights Selectively**: Only enable in production to avoid unnecessary costs

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Module not found | Incorrect source URL | Verify Git URL and authentication |
| Provider version conflict | Incompatible versions | Update provider constraints |
| Permission denied | Missing IAM permissions | Review and update IAM policies |
| Task fails to start | Resource constraints | Check CPU/memory limits |

### Getting Help

- Review the module's README and CHANGELOG
- Check AWS ECS service quotas
- Examine CloudWatch logs for detailed error messages
- Use the debug toolkit to troubleshoot network connectivity

---

This usage guide provides a comprehensive foundation for deploying and managing ECS infrastructure using the aws-terraform-ecs module. For specific configurations or advanced use cases, consult the module's source code and AWS ECS documentation.