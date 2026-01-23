# Outputs Reference

## Overview

This document provides comprehensive documentation for all outputs exposed by the `aws-terraform-ecs` Terraform module. Outputs are the mechanism by which Terraform modules expose values to calling modules, allowing you to reference and use the provisioned resources in other parts of your infrastructure.

The `aws-terraform-ecs` module provisions essential AWS ECS infrastructure components and exposes various outputs that enable you to integrate the ECS cluster, debug toolkit task definition, and related resources into your broader infrastructure setup.

---

## Available Outputs

The `aws-terraform-ecs` module exposes the following outputs for use in your Terraform configurations:

| Output Name | Type | Description |
|-------------|------|-------------|
| `ecs_cluster_id` | `string` | The unique identifier of the provisioned ECS cluster |
| `ecs_cluster_arn` | `string` | The Amazon Resource Name (ARN) of the ECS cluster |
| `ecs_cluster_name` | `string` | The name of the ECS cluster |
| `debug_toolkit_task_definition_arn` | `string` | ARN of the debug toolkit task definition for troubleshooting |
| `debug_toolkit_task_definition_family` | `string` | Family name of the debug toolkit task definition |
| `debug_toolkit_task_definition_revision` | `number` | Revision number of the debug toolkit task definition |
| `ecs_cluster_capacity_providers` | `list(string)` | List of capacity providers associated with the cluster |
| `ecs_service_discovery_namespace_id` | `string` | ID of the service discovery namespace (if enabled) |
| `ecs_service_discovery_namespace_arn` | `string` | ARN of the service discovery namespace (if enabled) |
| `ecs_execution_role_arn` | `string` | ARN of the ECS task execution IAM role |
| `ecs_task_role_arn` | `string` | ARN of the ECS task IAM role |

---

## Output Descriptions

### ECS Cluster Outputs

#### `ecs_cluster_id`

The unique identifier assigned to the ECS cluster by AWS. This ID is required when registering services or running tasks within the cluster.

```hcl
# Example output value
"arn:aws:ecs:us-east-1:123456789012:cluster/my-ecs-cluster"
```

**Use Cases:**
- Registering new ECS services
- Running standalone tasks
- Configuring auto-scaling policies
- Setting up CloudWatch alarms

#### `ecs_cluster_arn`

The full Amazon Resource Name (ARN) of the ECS cluster. This is used for IAM policies, cross-account access, and AWS resource tagging.

```hcl
# Example output value
"arn:aws:ecs:us-east-1:123456789012:cluster/my-ecs-cluster"
```

**Use Cases:**
- IAM policy resource specifications
- Cross-account cluster access
- AWS resource tagging and organization
- EventBridge rule targets

#### `ecs_cluster_name`

The human-readable name of the ECS cluster. Useful for logging, monitoring dashboards, and CLI commands.

```hcl
# Example output value
"my-ecs-cluster"
```

### Debug Toolkit Outputs

#### `debug_toolkit_task_definition_arn`

The ARN of the pre-configured debug toolkit task definition. This task definition includes common debugging tools and utilities for troubleshooting containerized applications running on ECS.

```hcl
# Example output value
"arn:aws:ecs:us-east-1:123456789012:task-definition/debug-toolkit:3"
```

**Use Cases:**
- Running ad-hoc debugging sessions
- Network connectivity troubleshooting
- Container health diagnostics
- Log inspection and analysis

#### `debug_toolkit_task_definition_family`

The family name of the debug toolkit task definition. Task definitions in the same family are considered versions of each other.

```hcl
# Example output value
"debug-toolkit"
```

#### `debug_toolkit_task_definition_revision`

The revision number of the current debug toolkit task definition. Each time you update a task definition, a new revision is created.

```hcl
# Example output value
3
```

### IAM Role Outputs

#### `ecs_execution_role_arn`

The ARN of the IAM role that ECS uses to pull container images and publish container logs. This role is assumed by the ECS agent.

```hcl
# Example output value
"arn:aws:iam::123456789012:role/ecs-execution-role"
```

#### `ecs_task_role_arn`

The ARN of the IAM role that containers in your tasks can assume. Use this to grant your application containers access to AWS services.

```hcl
# Example output value
"arn:aws:iam::123456789012:role/ecs-task-role"
```

---

## Using Outputs in Other Modules

### Basic Output Reference

When using the `aws-terraform-ecs` module, you can reference its outputs using the standard Terraform output syntax:

```hcl
# Root module calling the aws-terraform-ecs module
module "ecs_infrastructure" {
  source = "path/to/aws-terraform-ecs"
  
  # Module input variables
  cluster_name = "production-cluster"
  environment  = "production"
  # ... additional configuration
}

# Reference outputs from the module
output "cluster_id" {
  description = "The ECS cluster ID for downstream use"
  value       = module.ecs_infrastructure.ecs_cluster_id
}
```

### Passing Outputs to Other Modules

A common pattern is to pass ECS infrastructure outputs to service-specific modules:

```hcl
# Provision base ECS infrastructure
module "ecs_infrastructure" {
  source = "path/to/aws-terraform-ecs"
  
  cluster_name = "production-cluster"
  environment  = "production"
}

# Deploy an application service using the ECS cluster
module "web_application" {
  source = "path/to/ecs-service-module"
  
  # Pass ECS cluster outputs
  ecs_cluster_id        = module.ecs_infrastructure.ecs_cluster_id
  ecs_cluster_name      = module.ecs_infrastructure.ecs_cluster_name
  task_execution_role   = module.ecs_infrastructure.ecs_execution_role_arn
  task_role             = module.ecs_infrastructure.ecs_task_role_arn
  
  # Service-specific configuration
  service_name   = "web-api"
  container_port = 8080
}

# Deploy another service on the same cluster
module "worker_service" {
  source = "path/to/ecs-service-module"
  
  ecs_cluster_id      = module.ecs_infrastructure.ecs_cluster_id
  ecs_cluster_name    = module.ecs_infrastructure.ecs_cluster_name
  task_execution_role = module.ecs_infrastructure.ecs_execution_role_arn
  task_role           = module.ecs_infrastructure.ecs_task_role_arn
  
  service_name = "background-worker"
}
```

### Using Outputs with Data Sources

You can combine module outputs with Terraform data sources for advanced configurations:

```hcl
module "ecs_infrastructure" {
  source       = "path/to/aws-terraform-ecs"
  cluster_name = "production-cluster"
}

# Use the cluster ARN in an IAM policy document
data "aws_iam_policy_document" "ecs_access" {
  statement {
    effect = "Allow"
    actions = [
      "ecs:DescribeServices",
      "ecs:UpdateService",
    ]
    resources = [
      "${module.ecs_infrastructure.ecs_cluster_arn}/*"
    ]
  }
}
```

---

## Examples

### Example 1: Complete Infrastructure Setup

This example demonstrates a complete ECS infrastructure setup with output references:

```hcl
# terraform/main.tf

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

# Provision ECS infrastructure
module "ecs_infrastructure" {
  source = "path/to/aws-terraform-ecs"
  
  cluster_name = "${var.environment}-ecs-cluster"
  environment  = var.environment
  
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Export all outputs for use by other configurations
output "ecs_cluster_id" {
  description = "ECS Cluster ID"
  value       = module.ecs_infrastructure.ecs_cluster_id
}

output "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  value       = module.ecs_infrastructure.ecs_cluster_arn
}

output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = module.ecs_infrastructure.ecs_cluster_name
}

output "debug_toolkit_task_arn" {
  description = "Debug toolkit task definition ARN"
  value       = module.ecs_infrastructure.debug_toolkit_task_definition_arn
}

output "execution_role_arn" {
  description = "ECS execution role ARN"
  value       = module.ecs_infrastructure.ecs_execution_role_arn
}

output "task_role_arn" {
  description = "ECS task role ARN"
  value       = module.ecs_infrastructure.ecs_task_role_arn
}
```

### Example 2: Running the Debug Toolkit

Use the debug toolkit output to run troubleshooting tasks:

```hcl
# Run debug toolkit as a standalone task
resource "aws_ecs_task_set" "debug_session" {
  count = var.enable_debug_session ? 1 : 0
  
  cluster         = module.ecs_infrastructure.ecs_cluster_id
  task_definition = module.ecs_infrastructure.debug_toolkit_task_definition_arn
  service         = aws_ecs_service.main.id
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.debug_security_group_id]
    assign_public_ip = false
  }
}
```

You can also run the debug toolkit using the AWS CLI:

```bash
# Using outputs via terraform output command
CLUSTER_ARN=$(terraform output -raw ecs_cluster_arn)
TASK_DEF_ARN=$(terraform output -raw debug_toolkit_task_arn)

# Run the debug toolkit task
aws ecs run-task \
  --cluster "$CLUSTER_ARN" \
  --task-definition "$TASK_DEF_ARN" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=DISABLED}"
```

### Example 3: CloudWatch Alarms with Cluster Outputs

Create monitoring alarms using the cluster outputs:

```hcl
resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  alarm_name          = "${module.ecs_infrastructure.ecs_cluster_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ECS cluster CPU utilization exceeds 80%"
  
  dimensions = {
    ClusterName = module.ecs_infrastructure.ecs_cluster_name
  }
  
  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]
}
```

### Example 4: Cross-Stack References with Terraform Remote State

When working with multiple Terraform configurations, use remote state to share outputs:

```hcl
# In infrastructure stack (writes outputs)
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "ecs-infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

module "ecs_infrastructure" {
  source       = "path/to/aws-terraform-ecs"
  cluster_name = "shared-ecs-cluster"
}

output "ecs_cluster_id" {
  value = module.ecs_infrastructure.ecs_cluster_id
}

# In application stack (reads outputs)
data "terraform_remote_state" "ecs_infrastructure" {
  backend = "s3"
  
  config = {
    bucket = "my-terraform-state"
    key    = "ecs-infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_ecs_service" "application" {
  name            = "my-application"
  cluster         = data.terraform_remote_state.ecs_infrastructure.outputs.ecs_cluster_id
  task_definition = aws_ecs_task_definition.application.arn
  desired_count   = 2
}
```

---

## Best Practices

1. **Always use output references** instead of hardcoding resource identifiers to maintain infrastructure consistency.

2. **Document custom outputs** when extending the module to ensure team members understand available values.

3. **Use sensitive outputs** for any values that might contain confidential information.

4. **Validate outputs** in your CI/CD pipeline to catch configuration drift early.

5. **Version your module** to ensure output compatibility across infrastructure updates.

---

## Troubleshooting

### Output Not Available

If an output returns `null` or is not available, verify that:
- The module has been applied successfully
- The resource creating the output was not skipped due to conditional logic
- You're referencing the correct output name (outputs are case-sensitive)

### Circular Dependencies

Avoid circular dependencies by structuring your module hierarchy properly. The ECS infrastructure module should be at the base layer, with service modules depending on its outputs.