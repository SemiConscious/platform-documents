# Input Variables Reference

## Overview

This document provides a complete reference for all Terraform input variables used in the `aws-terraform-ecs` module. This module provisions common resources required for AWS ECS, including a debugging toolkit task definition for troubleshooting containerized applications.

Understanding these variables is essential for operators deploying and managing ECS infrastructure. Each variable is documented with its type, default value (if any), validation rules, and practical usage examples.

---

## Required Variables

Required variables must be provided when using this module. Terraform will fail to plan or apply if these values are not specified.

### `cluster_name`

The name of the ECS cluster to create or manage.

| Property | Value |
|----------|-------|
| **Type** | `string` |
| **Required** | Yes |
| **Default** | None |

**Description:** This variable defines the unique identifier for your ECS cluster within the AWS account and region. The cluster name appears in the AWS Console, CLI outputs, and is used for resource tagging.

**Validation Rules:**
- Must be between 1 and 255 characters
- Can only contain letters, numbers, hyphens, and underscores
- Must start with a letter or number

```hcl
variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9_-]{0,254}$", var.cluster_name))
    error_message = "Cluster name must be 1-255 characters, start with alphanumeric, and contain only letters, numbers, hyphens, and underscores."
  }
}
```

**Example Usage:**
```hcl
cluster_name = "production-api-cluster"
```

---

### `vpc_id`

The ID of the VPC where ECS resources will be deployed.

| Property | Value |
|----------|-------|
| **Type** | `string` |
| **Required** | Yes |
| **Default** | None |

**Description:** Specifies the AWS VPC that will host the ECS cluster and associated networking resources. This VPC must already exist and have appropriate subnets configured.

**Validation Rules:**
- Must be a valid VPC ID format (vpc-xxxxxxxxxxxxxxxxx)

```hcl
variable "vpc_id" {
  description = "VPC ID where ECS resources will be deployed"
  type        = string

  validation {
    condition     = can(regex("^vpc-[a-f0-9]{8,17}$", var.vpc_id))
    error_message = "VPC ID must be a valid format (e.g., vpc-12345678 or vpc-1234567890abcdef0)."
  }
}
```

**Example Usage:**
```hcl
vpc_id = "vpc-0a1b2c3d4e5f67890"
```

---

### `subnet_ids`

List of subnet IDs where ECS tasks will run.

| Property | Value |
|----------|-------|
| **Type** | `list(string)` |
| **Required** | Yes |
| **Default** | None |

**Description:** Defines the subnets available for ECS task placement. For high availability, provide subnets across multiple Availability Zones. These subnets should have appropriate routing configured (public subnets for internet-facing services, private subnets for internal services).

**Validation Rules:**
- At least one subnet ID must be provided
- Each ID must be a valid subnet format

```hcl
variable "subnet_ids" {
  description = "List of subnet IDs for ECS task placement"
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) > 0
    error_message = "At least one subnet ID must be provided."
  }

  validation {
    condition     = alltrue([for s in var.subnet_ids : can(regex("^subnet-[a-f0-9]{8,17}$", s))])
    error_message = "All subnet IDs must be valid format (e.g., subnet-12345678)."
  }
}
```

**Example Usage:**
```hcl
subnet_ids = [
  "subnet-0a1b2c3d4e5f67890",
  "subnet-1a2b3c4d5e6f78901",
  "subnet-2a3b4c5d6e7f89012"
]
```

---

## Optional Variables

Optional variables have default values and can be overridden as needed.

### `environment`

The deployment environment name.

| Property | Value |
|----------|-------|
| **Type** | `string` |
| **Required** | No |
| **Default** | `"development"` |

**Description:** Identifies the deployment environment (e.g., development, staging, production). Used for resource tagging and can influence certain configuration defaults.

```hcl
variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production", "dev", "stg", "prod"], var.environment)
    error_message = "Environment must be one of: development, staging, production, dev, stg, prod."
  }
}
```

**Example Usage:**
```hcl
environment = "production"
```

---

### `enable_container_insights`

Enable CloudWatch Container Insights for the ECS cluster.

| Property | Value |
|----------|-------|
| **Type** | `bool` |
| **Required** | No |
| **Default** | `true` |

**Description:** When enabled, CloudWatch Container Insights collects, aggregates, and summarizes metrics and logs from containerized applications. This provides enhanced observability but incurs additional CloudWatch costs.

```hcl
variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}
```

**Example Usage:**
```hcl
# Disable for cost savings in non-production environments
enable_container_insights = false
```

---

### `capacity_providers`

List of capacity providers to associate with the cluster.

| Property | Value |
|----------|-------|
| **Type** | `list(string)` |
| **Required** | No |
| **Default** | `["FARGATE", "FARGATE_SPOT"]` |

**Description:** Defines the capacity providers available for task placement. Fargate provides serverless compute, while Fargate Spot offers significant cost savings for interruption-tolerant workloads.

```hcl
variable "capacity_providers" {
  description = "Capacity providers for the ECS cluster"
  type        = list(string)
  default     = ["FARGATE", "FARGATE_SPOT"]

  validation {
    condition     = alltrue([for cp in var.capacity_providers : contains(["FARGATE", "FARGATE_SPOT"], cp) || can(regex("^[a-zA-Z0-9_-]+$", cp))])
    error_message = "Capacity providers must be FARGATE, FARGATE_SPOT, or a valid custom provider name."
  }
}
```

**Example Usage:**
```hcl
# Use only standard Fargate for production stability
capacity_providers = ["FARGATE"]

# Include Spot for cost optimization
capacity_providers = ["FARGATE", "FARGATE_SPOT"]
```

---

### `default_capacity_provider_strategy`

Default capacity provider strategy for the cluster.

| Property | Value |
|----------|-------|
| **Type** | `list(object)` |
| **Required** | No |
| **Default** | See below |

**Description:** Defines how tasks are distributed across capacity providers when no explicit strategy is specified in the service definition.

```hcl
variable "default_capacity_provider_strategy" {
  description = "Default capacity provider strategy"
  type = list(object({
    capacity_provider = string
    weight           = number
    base             = optional(number, 0)
  }))
  default = [
    {
      capacity_provider = "FARGATE"
      weight           = 1
      base             = 1
    },
    {
      capacity_provider = "FARGATE_SPOT"
      weight           = 4
      base             = 0
    }
  ]
}
```

**Example Usage:**
```hcl
# 100% Fargate for critical workloads
default_capacity_provider_strategy = [
  {
    capacity_provider = "FARGATE"
    weight           = 1
    base             = 0
  }
]

# Cost-optimized: 80% Spot, 20% On-Demand
default_capacity_provider_strategy = [
  {
    capacity_provider = "FARGATE"
    weight           = 1
    base             = 1
  },
  {
    capacity_provider = "FARGATE_SPOT"
    weight           = 4
    base             = 0
  }
]
```

---

### `debug_toolkit_enabled`

Enable the debug toolkit task definition.

| Property | Value |
|----------|-------|
| **Type** | `bool` |
| **Required** | No |
| **Default** | `true` |

**Description:** When enabled, creates a task definition for a debugging toolkit container that can be used for troubleshooting network connectivity, DNS resolution, and other infrastructure issues within the ECS cluster.

```hcl
variable "debug_toolkit_enabled" {
  description = "Enable debug toolkit task definition"
  type        = bool
  default     = true
}
```

**Example Usage:**
```hcl
# Disable in production for security
debug_toolkit_enabled = false
```

---

### `debug_toolkit_image`

Docker image for the debug toolkit container.

| Property | Value |
|----------|-------|
| **Type** | `string` |
| **Required** | No |
| **Default** | `"public.ecr.aws/aws-containers/amazon-ecs-exec-checker:latest"` |

**Description:** Specifies the container image used for the debug toolkit task. The default image includes common troubleshooting tools. You can specify a custom image with additional tools as needed.

```hcl
variable "debug_toolkit_image" {
  description = "Docker image for debug toolkit"
  type        = string
  default     = "public.ecr.aws/aws-containers/amazon-ecs-exec-checker:latest"
}
```

**Example Usage:**
```hcl
# Use a custom debug image from your private registry
debug_toolkit_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/debug-toolkit:v1.2.0"
```

---

### `debug_toolkit_cpu`

CPU units for the debug toolkit task.

| Property | Value |
|----------|-------|
| **Type** | `number` |
| **Required** | No |
| **Default** | `256` |

**Description:** CPU units to allocate to the debug toolkit task (1024 units = 1 vCPU). The default of 256 (0.25 vCPU) is sufficient for most troubleshooting activities.

```hcl
variable "debug_toolkit_cpu" {
  description = "CPU units for debug toolkit task"
  type        = number
  default     = 256

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.debug_toolkit_cpu)
    error_message = "CPU must be a valid Fargate value: 256, 512, 1024, 2048, or 4096."
  }
}
```

---

### `debug_toolkit_memory`

Memory (MB) for the debug toolkit task.

| Property | Value |
|----------|-------|
| **Type** | `number` |
| **Required** | No |
| **Default** | `512` |

**Description:** Memory in megabytes to allocate to the debug toolkit task. Must be a valid combination with the CPU value per Fargate requirements.

```hcl
variable "debug_toolkit_memory" {
  description = "Memory (MB) for debug toolkit task"
  type        = number
  default     = 512

  validation {
    condition     = var.debug_toolkit_memory >= 512 && var.debug_toolkit_memory <= 30720
    error_message = "Memory must be between 512 MB and 30720 MB."
  }
}
```

---

### `tags`

Additional tags to apply to all resources.

| Property | Value |
|----------|-------|
| **Type** | `map(string)` |
| **Required** | No |
| **Default** | `{}` |

**Description:** A map of tags to apply to all resources created by this module. These tags are merged with any default tags configured in the AWS provider.

```hcl
variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
```

**Example Usage:**
```hcl
tags = {
  Project     = "api-platform"
  Team        = "platform-engineering"
  CostCenter  = "12345"
  ManagedBy   = "terraform"
}
```

---

## Variable Defaults Summary

| Variable | Default Value |
|----------|---------------|
| `environment` | `"development"` |
| `enable_container_insights` | `true` |
| `capacity_providers` | `["FARGATE", "FARGATE_SPOT"]` |
| `debug_toolkit_enabled` | `true` |
| `debug_toolkit_image` | `"public.ecr.aws/aws-containers/amazon-ecs-exec-checker:latest"` |
| `debug_toolkit_cpu` | `256` |
| `debug_toolkit_memory` | `512` |
| `tags` | `{}` |

---

## Complete Example Configuration

Below is a comprehensive example demonstrating all variables:

```hcl
module "ecs_cluster" {
  source = "path/to/aws-terraform-ecs"

  # Required variables
  cluster_name = "production-api-cluster"
  vpc_id       = "vpc-0a1b2c3d4e5f67890"
  subnet_ids   = [
    "subnet-0a1b2c3d4e5f67890",
    "subnet-1a2b3c4d5e6f78901",
    "subnet-2a3b4c5d6e7f89012"
  ]

  # Optional variables
  environment               = "production"
  enable_container_insights = true
  capacity_providers        = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy = [
    {
      capacity_provider = "FARGATE"
      weight           = 1
      base             = 2
    },
    {
      capacity_provider = "FARGATE_SPOT"
      weight           = 3
      base             = 0
    }
  ]

  # Debug toolkit configuration
  debug_toolkit_enabled = false  # Disabled for production
  debug_toolkit_cpu     = 256
  debug_toolkit_memory  = 512

  # Resource tags
  tags = {
    Project     = "api-platform"
    Environment = "production"
    Team        = "platform-engineering"
    ManagedBy   = "terraform"
  }
}
```

---

## Best Practices

1. **Use Terraform Workspaces or Variables Files:** Maintain separate `.tfvars` files for each environment to manage variable values consistently.

2. **Validate VPC and Subnet Configuration:** Ensure your VPC has proper internet gateway or NAT gateway configuration before deploying ECS resources.

3. **Disable Debug Toolkit in Production:** For security compliance, disable the debug toolkit in production environments and enable only when needed.

4. **Optimize Capacity Provider Strategy:** Use Fargate Spot for cost savings on non-critical workloads, but ensure critical services have adequate on-demand capacity.

5. **Tag Resources Consistently:** Apply comprehensive tags for cost allocation, compliance tracking, and resource management.