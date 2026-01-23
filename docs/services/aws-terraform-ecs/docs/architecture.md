# Architecture Overview

## Introduction

The `aws-terraform-ecs` module is a comprehensive Terraform module designed to provision and manage AWS Elastic Container Service (ECS) infrastructure. This module provides a standardized, reusable approach to deploying ECS clusters along with essential supporting resources, including a debugging toolkit task definition specifically designed for troubleshooting containerized applications in production environments.

This architecture documentation is intended for operators, DevOps engineers, and infrastructure teams who need to understand the resources provisioned by this module, their interdependencies, and the security considerations involved in deploying ECS workloads on AWS.

---

## Resource Diagram

The following diagram illustrates the high-level architecture of resources provisioned by the `aws-terraform-ecs` module:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  AWS Account                                     │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                              VPC (Data Source)                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                         Private Subnets                              │  │  │
│  │  │                                                                      │  │  │
│  │  │  ┌────────────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │                      ECS Cluster                                │ │  │  │
│  │  │  │  ┌──────────────────┐    ┌──────────────────────────────────┐  │ │  │  │
│  │  │  │  │   ECS Service    │    │    Debug Toolkit Task Definition │  │ │  │  │
│  │  │  │  │                  │    │                                  │  │ │  │  │
│  │  │  │  │  ┌────────────┐  │    │  ┌─────────────────────────────┐ │  │ │  │  │
│  │  │  │  │  │   Tasks    │  │    │  │   Container Definitions     │ │  │ │  │  │
│  │  │  │  │  │            │  │    │  │   - Network utilities       │ │  │ │  │  │
│  │  │  │  │  └────────────┘  │    │  │   - AWS CLI tools           │ │  │ │  │  │
│  │  │  │  └──────────────────┘    │  │   - Diagnostic commands     │ │  │ │  │  │
│  │  │  │                          │  └─────────────────────────────┘ │  │ │  │  │
│  │  │  │                          └──────────────────────────────────┘  │ │  │  │
│  │  │  └────────────────────────────────────────────────────────────────┘ │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           IAM Resources                                    │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────────┐  │  │
│  │  │ Task Execution Role │  │    Task Role        │  │  Service Role     │  │  │
│  │  │                     │  │                     │  │                   │  │  │
│  │  │ - ECR Pull          │  │ - Application       │  │ - Load Balancer   │  │  │
│  │  │ - CloudWatch Logs   │  │   Permissions       │  │   Registration    │  │  │
│  │  │ - Secrets Manager   │  │ - S3 Access         │  │ - Service         │  │  │
│  │  │                     │  │ - DynamoDB          │  │   Discovery       │  │  │
│  │  └─────────────────────┘  └─────────────────────┘  └───────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        CloudWatch Resources                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                     Log Groups                                       │  │  │
│  │  │  - /ecs/cluster-name/service-logs                                   │  │  │
│  │  │  - /ecs/cluster-name/debug-toolkit                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        Security Groups                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  ECS Tasks Security Group                                            │  │  │
│  │  │  - Ingress: Application ports from ALB                              │  │  │
│  │  │  - Egress: HTTPS to AWS services, application dependencies          │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## ECS Resources Created

### ECS Cluster

The module provisions an ECS cluster that serves as the logical grouping for your containerized services and tasks.

```hcl
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }

  tags = var.tags
}
```

**Key Features:**
- **Container Insights**: Optional CloudWatch Container Insights integration for enhanced monitoring and observability
- **ECS Exec Configuration**: Pre-configured for interactive debugging sessions with containers
- **Capacity Providers**: Support for both Fargate and EC2 launch types

### ECS Cluster Capacity Providers

The module configures capacity providers to manage the underlying compute resources:

```hcl
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = var.capacity_providers

  default_capacity_provider_strategy {
    base              = var.capacity_provider_base
    weight            = var.capacity_provider_weight
    capacity_provider = var.default_capacity_provider
  }
}
```

### Debug Toolkit Task Definition

A critical component of this module is the debug toolkit task definition, which provides operators with essential troubleshooting capabilities:

```hcl
resource "aws_ecs_task_definition" "debug_toolkit" {
  family                   = "${var.cluster_name}-debug-toolkit"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.debug_toolkit_cpu
  memory                   = var.debug_toolkit_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.debug_toolkit_task.arn

  container_definitions = jsonencode([
    {
      name      = "debug-toolkit"
      image     = var.debug_toolkit_image
      essential = true

      command = ["sleep", "infinity"]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.debug_toolkit.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "debug"
        }
      }

      linuxParameters = {
        initProcessEnabled = true
      }
    }
  ])

  tags = var.tags
}
```

**Debug Toolkit Capabilities:**
| Tool Category | Included Tools | Use Case |
|---------------|----------------|----------|
| Network Diagnostics | `curl`, `wget`, `dig`, `nslookup`, `netcat`, `tcpdump` | Network connectivity troubleshooting |
| AWS CLI | `aws-cli`, `session-manager-plugin` | AWS service interaction and debugging |
| Container Utilities | `jq`, `yq`, `vim`, `htop` | Log parsing and system monitoring |
| Database Clients | `psql`, `mysql`, `redis-cli` | Database connectivity testing |

### CloudWatch Log Groups

The module creates dedicated log groups for centralized logging:

```hcl
resource "aws_cloudwatch_log_group" "ecs_cluster" {
  name              = "/ecs/${var.cluster_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "debug_toolkit" {
  name              = "/ecs/${var.cluster_name}/debug-toolkit"
  retention_in_days = var.debug_log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "ecs_exec" {
  name              = "/ecs/${var.cluster_name}/ecs-exec"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
```

---

## AWS Resource Dependencies

Understanding resource dependencies is crucial for proper deployment and troubleshooting. The following diagram illustrates the dependency chain:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Resource Dependency Graph                        │
└─────────────────────────────────────────────────────────────────────┘

Level 0 (Data Sources - Must Exist):
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  AWS Region  │  │     VPC      │  │   Subnets    │  │  AWS Account │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └────────────────┬┴─────────────────┴─────────────────┘
                        │
                        ▼
Level 1 (IAM Resources):
┌─────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │ Task Execution Role  │  │     Task Role        │                 │
│  │ + Policy Attachments │  │ + Policy Attachments │                 │
│  └──────────┬───────────┘  └──────────┬───────────┘                 │
└─────────────┼──────────────────────────┼────────────────────────────┘
              │                          │
              └────────────┬─────────────┘
                           │
                           ▼
Level 2 (Core ECS Resources):
┌─────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │    ECS Cluster       │  │  CloudWatch Logs     │                 │
│  └──────────┬───────────┘  └──────────┬───────────┘                 │
└─────────────┼──────────────────────────┼────────────────────────────┘
              │                          │
              └────────────┬─────────────┘
                           │
                           ▼
Level 3 (Cluster Configuration):
┌─────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌──────────────────────┐                 │
│  │ Capacity Providers   │  │ Task Definitions     │                 │
│  └──────────────────────┘  │ (Debug Toolkit)      │                 │
│                            └──────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Explicit Dependencies Table

| Resource | Depends On | Dependency Type |
|----------|------------|-----------------|
| `aws_ecs_cluster` | VPC, Subnets (data sources) | Implicit |
| `aws_ecs_cluster_capacity_providers` | `aws_ecs_cluster` | Explicit |
| `aws_ecs_task_definition` | `aws_iam_role` (execution, task), `aws_cloudwatch_log_group` | Explicit |
| `aws_iam_role` | `aws_iam_policy_document` | Explicit |
| `aws_iam_role_policy_attachment` | `aws_iam_role`, `aws_iam_policy` | Explicit |
| `aws_cloudwatch_log_group` | None | Independent |
| `aws_security_group` | VPC (data source) | Implicit |

---

## Data Sources Used

The module leverages several AWS data sources to retrieve existing infrastructure information:

### Current AWS Region

```hcl
data "aws_region" "current" {}
```

**Purpose:** Retrieves the current AWS region for constructing ARNs and configuring regional resources.

### Current AWS Account

```hcl
data "aws_caller_identity" "current" {}
```

**Purpose:** Retrieves the AWS account ID for IAM policy construction and resource naming.

### VPC Information

```hcl
data "aws_vpc" "selected" {
  id = var.vpc_id
}
```

**Purpose:** Retrieves VPC details for security group configuration and network planning.

### Subnet Information

```hcl
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  tags = {
    Tier = "private"
  }
}
```

**Purpose:** Identifies private subnets for ECS task placement.

### IAM Policy Documents

```hcl
data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ecs_task_execution_policy" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "${aws_cloudwatch_log_group.ecs_cluster.arn}:*",
      "${aws_cloudwatch_log_group.debug_toolkit.arn}:*",
    ]
  }
}
```

**Purpose:** Constructs least-privilege IAM policies for task execution and runtime permissions.

---

## Security Considerations

### IAM Permissions

The module implements the principle of least privilege across all IAM resources:

#### Task Execution Role

The task execution role is used by the ECS agent to pull container images and write logs:

```hcl
resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.cluster_name}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```

**Security Best Practices:**
- ✅ Uses AWS managed policy for standard permissions
- ✅ Custom policies scoped to specific resources
- ✅ No wildcard resource permissions where avoidable

#### Debug Toolkit Task Role

The debug toolkit task role requires elevated permissions for troubleshooting:

```hcl
resource "aws_iam_role" "debug_toolkit_task" {
  name               = "${var.cluster_name}-debug-toolkit-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json

  tags = var.tags
}

# Attach policies based on debugging requirements
resource "aws_iam_role_policy" "debug_toolkit_permissions" {
  name = "debug-toolkit-permissions"
  role = aws_iam_role.debug_toolkit_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeTasks",
          "ecs:ListTasks",
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/Environment" = var.environment
          }
        }
      }
    ]
  })
}
```

> ⚠️ **Warning:** The debug toolkit task role has broader permissions than application task roles. Restrict access to running debug toolkit tasks to authorized operators only.

### Network Security

#### Security Group Configuration

```hcl
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.cluster_name}-ecs-tasks"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  # No ingress rules by default - add as needed for your services
  
  egress {
    description = "Allow HTTPS outbound for AWS services"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}
```

**Network Security Best Practices:**

| Consideration | Recommendation | Implementation |
|---------------|----------------|----------------|
| Ingress Rules | Restrict to required ports only | Define per-service security groups |
| Egress Rules | Limit to necessary destinations | Use VPC endpoints where possible |
| VPC Endpoints | Reduce internet exposure | Create endpoints for ECR, CloudWatch, S3 |
| Private Subnets | Deploy tasks in private subnets | Use NAT Gateway for outbound traffic |

### Secrets Management

For applications requiring secrets, the module supports AWS Secrets Manager and SSM Parameter Store integration:

```hcl
# Additional policy for secrets access (attach to task execution role)
data "aws_iam_policy_document" "secrets_access" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.cluster_name}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameters",
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.cluster_name}/*"
    ]
  }
}
```

### Encryption

The module ensures data encryption at rest and in transit:

- **CloudWatch Logs:** Encrypted using AWS managed keys by default; supports customer-managed KMS keys
- **ECS Task Storage:** Fargate ephemeral storage encrypted by default
- **Secrets:** Encrypted at rest using AWS KMS

```hcl
# Optional: Customer-managed KMS key for CloudWatch Logs
resource "aws_cloudwatch_log_group" "ecs_cluster" {
  name              = "/ecs/${var.cluster_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn  # Optional customer-managed key

  tags = var.tags
}
```

### Audit and Compliance

To maintain compliance and enable auditing:

1. **CloudTrail Integration:** All ECS API calls are logged to CloudTrail
2. **Container Insights:** Provides detailed performance and diagnostic data
3. **ECS Exec Logging:** All interactive sessions are logged to CloudWatch

```hcl
# ECS Exec audit logging configuration
resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }
}
```

---

## Summary

The `aws-terraform-ecs` module provides a secure, well-architected foundation for running containerized applications on AWS ECS. Key architectural highlights include:

- **Modular Design:** Reusable components that can be customized per environment
- **Security-First Approach:** Least-privilege IAM policies and network isolation
- **Operational Excellence:** Built-in debugging toolkit and comprehensive logging
- **Scalability:** Support for multiple capacity providers and auto-scaling patterns

For questions or issues, consult the module's variable documentation or reach out to the infrastructure team.