# Terraform Module Technical Reference

> **Last Updated**: 2026-01-20
> **Maintainers**: Platform Infrastructure Team
> **Classification**: Internal Technical Documentation

## Overview

This document provides detailed technical specifications for each Terraform module including all variables, outputs, AWS resources, and custom configurations.

---

## Table of Contents

1. [terraform-network-rt - Complete Reference](#terraform-network-rt---complete-reference)
2. [terraform-rt-core-api - Complete Reference](#terraform-rt-core-api---complete-reference)
3. [terraform-rt-pbx - Complete Reference](#terraform-rt-pbx---complete-reference)
4. [terraform-dns - Complete Reference](#terraform-dns---complete-reference)
5. [terraform-fsx - Complete Reference](#terraform-fsx---complete-reference)
6. [terraform-waf - Complete Reference](#terraform-waf---complete-reference)

---

## terraform-network-rt - Complete Reference

### Repository
`redmatter/aws-terraform-network-rt`

### Description
Network provisioning for the RT (Real-Time) platform. Sets up VPCs, VPNs, subnets, security groups, and load balancers.

### File Structure
```
aws-terraform-network-rt/
├── main.tf                 # Main resource definitions
├── variables.tf            # Input variable definitions
├── outputs.tf              # Output definitions
├── terraform.tf            # Provider and backend config
├── modules/
│   ├── alb/               # Application Load Balancer module
│   ├── nlb/               # Network Load Balancer module
│   ├── endpoints/         # VPC Endpoint definitions
│   ├── global-accelerator/# Global Accelerator for CTI
│   └── vpn/               # VPN connection module
├── data/                   # External data sources
│   └── aws-services.json   # AWS service definitions
├── docs/                   # Additional documentation
│   ├── byoip.md           # Bring Your Own IP documentation
│   └── security-groups.md  # Security group documentation
└── role/                   # IAM role module
    ├── main.tf
    └── variables.tf
```

### Complete Variables Reference

| Variable | Type | Description | Default | Required |
|----------|------|-------------|---------|----------|
| `assume_role_name` | string | IAM role to assume for state application | `TerraformApplyAdmin` | No |
| `aws_profile` | string | Local IAM profile for AWS access | `terraform` | No |
| `map_migrated_tag` | string | AWS migration tracking tag value | `mig5QIKUES7BE` | No |
| `deployed_regions` | map(set(string)) | Map of accounts to deployed regions | See below | No |
| `ssl_policy_alb` | string | SSL policy for Application Load Balancers | `ELBSecurityPolicy-TLS13-1-2-2021-06` | No |
| `ssl_policy_nlb` | string | SSL policy for Network Load Balancers | `ELBSecurityPolicy-TLS13-1-2-2021-06` | No |
| `lb_deletion_protection` | bool | Enable deletion protection on load balancers | `true` | No |
| `max_subnet_azs` | number | Maximum number of AZs to provision subnets in | `4` | No |
| `vpc_flow_log_retention` | number | Days to retain VPC Flow Logs | `30` | No |
| `enable_global_accelerator` | bool | Enable Global Accelerator for CTI endpoints | `true` | No |

### Default Deployed Regions
```hcl
variable "deployed_regions" {
  default = {
    dev01 = ["us-east-2", "us-west-2"]
    qa01  = ["us-east-2", "us-west-2"]
    qa02  = ["us-east-2", "us-west-2"]
    stage = ["ap-southeast-2", "eu-west-2"]
    prod  = [
      "ap-southeast-1",  # Singapore
      "ap-southeast-2",  # Sydney
      "eu-central-1",    # Frankfurt
      "eu-west-2",       # London
      "us-east-2",       # Ohio
      "us-west-2"        # Oregon
    ]
  }
}
```

### AWS Resources Created

#### VPC Resources
| Resource | Count | Description |
|----------|-------|-------------|
| `aws_vpc` | 1 | Main VPC for the region |
| `aws_subnet` | ~24 | Public, private, VPN, NAT subnets across AZs |
| `aws_internet_gateway` | 1 | Internet gateway for public access |
| `aws_nat_gateway` | 1-4 | NAT gateways per AZ |
| `aws_eip` | 1-4 | Elastic IPs for NAT gateways |
| `aws_route_table` | ~8 | Route tables for different zones |
| `aws_route_table_association` | ~24 | Subnet to route table associations |

#### Load Balancers
| Resource | Type | Zone | Purpose |
|----------|------|------|---------|
| `alb-red-internal` | ALB | Red Internal | Internal API services |
| `alb-amber-internal` | ALB | Amber Internal | Application services |
| `nlb-red-public` | NLB | Red Public | Voice/SIP traffic |
| `nlb-cti` | NLB | Amber | CTI WebSocket connections |

#### VPC Endpoints
| Endpoint | Service | Type |
|----------|---------|------|
| `ecr.api` | ECR API | Interface |
| `ecr.dkr` | ECR Docker | Interface |
| `ecs` | ECS | Interface |
| `ecs-agent` | ECS Agent | Interface |
| `ecs-telemetry` | ECS Telemetry | Interface |
| `logs` | CloudWatch Logs | Interface |
| `ssm` | Systems Manager | Interface |
| `ssmmessages` | SSM Messages | Interface |
| `secretsmanager` | Secrets Manager | Interface |
| `s3` | S3 | Gateway |
| `dynamodb` | DynamoDB | Gateway |

#### Security Groups
| Security Group | Purpose | Key Rules |
|----------------|---------|-----------|
| `sg-alb-red-internal` | Internal ALB | HTTPS from VPC |
| `sg-alb-amber-internal` | Amber ALB | HTTPS from VPC |
| `sg-nlb-red-public` | Public NLB | SIP/RTP from internet |
| `sg-ecs-services` | ECS tasks | From ALBs only |
| `sg-pbx` | PBX instances | SIP/RTP/ESL |
| `sg-sip` | SIP instances | SIP from BYOIP |
| `sg-vpn` | VPN connections | IPSec |
| `sg-endpoints` | VPC endpoints | HTTPS from VPC |

### Complete Outputs Reference

| Output | Type | Description |
|--------|------|-------------|
| `vpc_id` | string | ID of the provisioned VPC |
| `vpc_cidr_block` | string | CIDR block of the VPC |
| `alb_red_internal_arn` | string | ARN of red-internal ALB |
| `alb_red_internal_dns` | string | DNS name of red-internal ALB |
| `alb_amber_internal_arn` | string | ARN of amber-internal ALB |
| `alb_amber_internal_dns` | string | DNS name of amber-internal ALB |
| `nlb_red_public_arn` | string | ARN of red-public NLB |
| `nlb_cti_arn` | string | ARN of CTI NLB |
| `nlb_cti_dns` | string | DNS name of CTI NLB |
| `subnet_ids_red_internal` | list(string) | Red internal subnet IDs |
| `subnet_ids_red_public` | list(string) | Red public subnet IDs |
| `subnet_ids_red_vpn` | list(string) | Red VPN subnet IDs |
| `subnet_ids_amber_internal` | list(string) | Amber internal subnet IDs |
| `subnet_ids_amber_nat` | list(string) | Amber NAT subnet IDs |
| `subnet_ids_green_vpn_db` | list(string) | Green VPN DB subnet IDs |
| `security_group_id_alb_red` | string | Red ALB security group ID |
| `security_group_id_alb_amber` | string | Amber ALB security group ID |
| `security_group_id_ecs` | string | ECS security group ID |
| `security_group_id_pbx` | string | PBX security group ID |
| `security_group_id_sip` | string | SIP security group ID |
| `security_group_id_endpoints` | string | VPC endpoints security group ID |
| `global_accelerator_arn` | string | Global Accelerator ARN (if enabled) |
| `global_accelerator_dns` | string | Global Accelerator DNS name |
| `route53_private_zone_id` | string | Private hosted zone ID |
| `nat_gateway_public_ips` | list(string) | Public IPs of NAT gateways |

### Dependencies
```hcl
data "terraform_remote_state" "accounts" {
  backend   = "s3"
  workspace = local.account
  config = {
    bucket = "rm-terraform-state"
    key    = "accounts/terraform.tfstate"
    region = "eu-west-1"
  }
}

data "terraform_remote_state" "acm" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = "rm-terraform-state"
    key    = "acm/terraform.tfstate"
    region = "eu-west-1"
  }
}

data "terraform_remote_state" "network_info" {
  backend   = "s3"
  workspace = "default"
  config = {
    bucket = "rm-terraform-state"
    key    = "network-info/terraform.tfstate"
    region = "eu-west-1"
  }
}
```

---

## terraform-rt-core-api - Complete Reference

### Repository
`redmatter/aws-terraform-rt-core-api`

### Description
Provisions the Core API container in ECS for the real-time platform.

### File Structure
```
aws-terraform-rt-core-api/
├── main.tf                 # Main ECS service definition
├── variables.tf            # Input variable definitions
├── outputs.tf              # Output definitions
├── terraform.tf            # Provider and backend config
├── alarms.tf              # CloudWatch alarms
├── autoscaling.tf         # Auto-scaling configuration
├── dashboard.tf           # CloudWatch dashboard
├── healthcheck.tf         # Health check Lambda
├── iam.tf                 # IAM roles and policies
├── security-groups.tf     # Security group definitions
└── role/                  # IAM role module
```

### Complete Variables Reference

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `assume_role_name` | string | Role to assume | `TerraformApplyAdmin` |
| `aws_profile` | string | AWS profile | `terraform` |
| `map_migrated_tag` | string | Migration tag | `mig5QIKUES7BE` |
| `daytime_min_task_count` | map(number) | Min tasks during business hours | See below |
| `offhours_min_task_count` | map(number) | Min tasks off-hours | See below |
| `max_task_count` | map(number) | Maximum task count | See below |
| `task_cpu` | string | CPU units (vCPU * 1024) | `1024` |
| `task_memory` | string | Memory in MB | `2048` |
| `log_retention_days` | number | Log retention period | `30` |
| `subdomain` | string | Primary subdomain | `coreapi-local` |
| `subdomain_alias` | string | Alias subdomain | `coreapi` |
| `health_check_path` | string | ALB health check path | `/health` |
| `health_check_interval` | number | Health check interval | `30` |
| `health_check_timeout` | number | Health check timeout | `5` |
| `health_check_healthy_threshold` | number | Healthy threshold | `2` |
| `health_check_unhealthy_threshold` | number | Unhealthy threshold | `3` |
| `deregistration_delay` | number | Target deregistration delay | `60` |
| `enable_cpu_alarm` | bool | Enable CPU alarm | `true` |
| `enable_memory_alarm` | bool | Enable memory alarm | `true` |
| `cpu_alarm_threshold` | number | CPU alarm threshold % | `80` |
| `memory_alarm_threshold` | number | Memory alarm threshold % | `80` |

### Default Task Counts
```hcl
variable "daytime_min_task_count" {
  default = {
    dev01 = 2
    qa01  = 2
    qa02  = 2
    stage = 4
    prod  = 12
  }
}

variable "offhours_min_task_count" {
  default = {
    dev01 = 1
    qa01  = 1
    qa02  = 1
    stage = 2
    prod  = 3
  }
}

variable "max_task_count" {
  default = {
    dev01 = 4
    qa01  = 4
    qa02  = 4
    stage = 8
    prod  = 20
  }
}
```

### AWS Resources Created

| Resource Type | Resource Name | Description |
|---------------|---------------|-------------|
| `aws_ecs_service` | `core-api` | ECS Fargate service |
| `aws_ecs_task_definition` | `core-api` | Task definition |
| `aws_lb_target_group` | `core-api` | ALB target group |
| `aws_lb_listener_rule` | `core-api` | ALB listener rule |
| `aws_cloudwatch_log_group` | `/ecs/core-api` | Log group |
| `aws_cloudwatch_metric_alarm` | Multiple | CPU, memory, 5xx alarms |
| `aws_cloudwatch_dashboard` | `core-api` | Monitoring dashboard |
| `aws_appautoscaling_target` | `core-api` | Auto-scaling target |
| `aws_appautoscaling_policy` | Multiple | Target tracking policies |
| `aws_appautoscaling_scheduled_action` | Multiple | Scheduled scaling |
| `aws_security_group` | `core-api` | Service security group |
| `aws_route53_record` | Multiple | DNS records |
| `aws_sns_topic` | `core-api-alarms` | Alarm notifications |
| `aws_lambda_function` | `core-api-health-check` | Health check Lambda |
| `aws_iam_role` | `core-api-task` | Task execution role |
| `aws_iam_role` | `core-api-execution` | Task execution role |
| `aws_ssm_parameter` | Multiple | Configuration parameters |

### ECS Task Definition
```json
{
  "family": "core-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/core-api-execution",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/core-api-task",
  "containerDefinitions": [
    {
      "name": "core-api",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/core-api:VERSION",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"},
        {"name": "PORT", "value": "8080"},
        {"name": "AWS_REGION", "value": "REGION"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:ssm:REGION:ACCOUNT:parameter/rt/core-api/database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/core-api",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Auto-Scaling Configuration
```hcl
resource "aws_appautoscaling_target" "core_api" {
  max_capacity       = var.max_task_count[local.account]
  min_capacity       = var.daytime_min_task_count[local.account]
  resource_id        = "service/${data.terraform_remote_state.ecs.outputs.rt_cluster_name}/core-api"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU Target Tracking
resource "aws_appautoscaling_policy" "cpu" {
  name               = "core-api-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.core_api.resource_id
  scalable_dimension = aws_appautoscaling_target.core_api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.core_api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Scheduled Scaling - Business Hours
resource "aws_appautoscaling_scheduled_action" "scale_up_business_hours" {
  name               = "core-api-scale-up"
  service_namespace  = aws_appautoscaling_target.core_api.service_namespace
  resource_id        = aws_appautoscaling_target.core_api.resource_id
  scalable_dimension = aws_appautoscaling_target.core_api.scalable_dimension
  schedule           = "cron(0 7 ? * MON-FRI *)"
  timezone           = "Europe/London"

  scalable_target_action {
    min_capacity = var.daytime_min_task_count[local.account]
  }
}

# Scheduled Scaling - Off Hours
resource "aws_appautoscaling_scheduled_action" "scale_down_off_hours" {
  name               = "core-api-scale-down"
  service_namespace  = aws_appautoscaling_target.core_api.service_namespace
  resource_id        = aws_appautoscaling_target.core_api.resource_id
  scalable_dimension = aws_appautoscaling_target.core_api.scalable_dimension
  schedule           = "cron(0 20 ? * MON-FRI *)"
  timezone           = "Europe/London"

  scalable_target_action {
    min_capacity = var.offhours_min_task_count[local.account]
  }
}
```

### Complete Outputs Reference

| Output | Type | Description |
|--------|------|-------------|
| `domain_name` | string | Full domain name for Core API |
| `core_api_version` | string | Deployed version |
| `security_group_id_core_api` | string | Security group ID |
| `sns_alarms_topic_arn` | string | Alarms SNS topic ARN |
| `cascade_alarm_names` | list(string) | Critical alarms for cascading |
| `cloudwatch_log_group_name` | string | Log group name |
| `task_definition_arn` | string | Task definition ARN |
| `service_name` | string | ECS service name |
| `target_group_arn` | string | Target group ARN |
| `iam_task_role_arn` | string | Task IAM role ARN |
| `iam_execution_role_arn` | string | Execution IAM role ARN |
| `health_check_lambda_arn` | string | Health check Lambda ARN |

### Required SSM Parameters

| Parameter | Description |
|-----------|-------------|
| `/rt/core-api/database-url` | Database connection string |
| `/rt/core-api/jwt-secret` | JWT signing secret |
| `/rt/core-api/redis-url` | Redis connection string |
| `/rt/core-api/salesforce-client-id` | Salesforce OAuth client ID |
| `/rt/core-api/salesforce-client-secret` | Salesforce OAuth secret |

---

## terraform-rt-pbx - Complete Reference

### Repository
`redmatter/aws-terraform-rt-pbx`

### Description
Provisions RT PBX (FreeSWITCH) EC2 instances with supporting resources.

### Complete Variables Reference

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `assume_role_name` | string | Role to assume | `TerraformApplyAdmin` |
| `aws_profile` | string | AWS profile | `terraform` |
| `map_migrated_tag` | string | Migration tag | `mig5QIKUES7BE` |
| `instance_types` | map(string) | EC2 instance types | See below |
| `root_volume_gb` | map(number) | Root volume size | See below |
| `data_volume_gb` | map(number) | Data volume size | See below |
| `esl_port` | number | ESL load balancing port | `8021` |
| `role` | string | EC2 instance role grain | `pbx` |
| `network_zone` | string | Network zone grain | `red` |
| `host_placement` | map(map(string)) | Host to AZ mapping | See below |
| `enable_detailed_monitoring` | bool | Enable detailed monitoring | `true` |
| `enable_termination_protection` | bool | Termination protection | `true` (prod) |

### Instance Type Defaults
```hcl
variable "instance_types" {
  default = {
    "dev01" = "t3.medium"
    "qa01"  = "t3.large"
    "qa02"  = "t3.large"
    "stage" = "m6a.xlarge"
    "prod"  = "m6a.2xlarge"
  }
}

variable "root_volume_gb" {
  default = {
    dev01 = 16
    qa01  = 32
    qa02  = 32
    stage = 64
    prod  = 128
  }
}

variable "data_volume_gb" {
  default = {
    dev01 = 8
    qa01  = 16
    qa02  = 16
    stage = 100
    prod  = 500
  }
}
```

### Host Placement Configuration (Production)
```hcl
variable "host_placement" {
  default = {
    "prod-euw2" = {
      "01a" = "eu-west-2a"
      "01b" = "eu-west-2b"
      "01c" = "eu-west-2c"
      "02a" = "eu-west-2a"
      "02b" = "eu-west-2b"
      "02c" = "eu-west-2c"
      "03a" = "eu-west-2a"
    }
    "prod-use2" = {
      "01a" = "us-east-2a"
      "01b" = "us-east-2b"
      "01c" = "us-east-2c"
      "02a" = "us-east-2a"
      "02b" = "us-east-2b"
    }
    # ... other regions
  }
}
```

### AWS Resources Created (Per Host)

| Resource Type | Description |
|---------------|-------------|
| `aws_instance` | EC2 PBX instance |
| `aws_ebs_volume` | Data volume for FreeSWITCH |
| `aws_volume_attachment` | Attach data volume |
| `aws_network_interface` | Private network interface |
| `aws_network_interface` | Public network interface (voice) |
| `aws_eip` | Elastic IP for public interface |
| `aws_eip_association` | EIP to ENI association |
| `aws_route53_record` | DNS records (internal + public) |
| `aws_lb_target_group_attachment` | ESL NLB target |
| `aws_cloudwatch_metric_alarm` | Instance health alarms |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `pbx_instance_ids` | map(string) | Map of host names to instance IDs |
| `pbx_private_ips` | map(string) | Map of host names to private IPs |
| `pbx_public_ips` | map(string) | Map of host names to public IPs |
| `pbx_esl_nlb_dns` | string | ESL NLB DNS name |
| `pbx_esl_nlb_arn` | string | ESL NLB ARN |
| `security_group_id_pbx` | string | PBX security group ID |

### Security Group Rules

```hcl
# SIP/RTP Traffic (Public Interface)
ingress {
  description = "SIP from BYOIP ranges"
  from_port   = 5060
  to_port     = 5060
  protocol    = "udp"
  cidr_blocks = var.byoip_cidr_blocks
}

ingress {
  description = "RTP media"
  from_port   = 16384
  to_port     = 32767
  protocol    = "udp"
  cidr_blocks = ["0.0.0.0/0"]
}

# ESL (Private Interface)
ingress {
  description = "ESL from Core API"
  from_port   = 8021
  to_port     = 8021
  protocol    = "tcp"
  security_groups = [data.terraform_remote_state.core_api.outputs.security_group_id_core_api]
}

# Salt Master
ingress {
  description = "Salt from master"
  from_port   = 4505
  to_port     = 4506
  protocol    = "tcp"
  security_groups = [data.terraform_remote_state.salt_master.outputs.security_group_id]
}
```

---

## terraform-dns - Complete Reference

### Repository
`redmatter/aws-terraform-dns`

### Description
Bootstraps Route 53 for DNS management with DNSSEC support.

### Complete Variables Reference

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `assume_role_name` | string | Role to assume | `TerraformApplyAdmin` |
| `aws_profile` | string | AWS profile | `terraform` |
| `primary_domains` | map(string) | Primary internal domains | See below |
| `public_domains` | map(string) | Public RT domains | See below |
| `branded_domains` | map(list(string)) | Customer-facing domains | See below |
| `dnssec_enabled` | bool | Enable DNSSEC | `true` (prod) |

### Domain Configuration
```hcl
variable "primary_domains" {
  default = {
    dev01 = "redmatter-dev01.pub"
    qa01  = "redmatter-qa01.pub"
    qa02  = "redmatter-qa02.pub"
    stage = "redmatter-stage.pub"
    prod  = "redmatter.io"
  }
}

variable "public_domains" {
  default = {
    dev01 = "natterbox-dev01.net"
    qa01  = "natterbox-qa01.net"
    qa02  = "natterbox-qa02.net"
    stage = "natterbox-stage.net"
    prod  = "natterbox.net"
  }
}

variable "branded_domains" {
  default = {
    dev01 = ["natterbox-dev01.pub"]
    qa01  = ["natterbox-qa01.pub"]
    qa02  = ["natterbox-qa02.pub"]
    stage = ["natterbox-stage.pub"]
    prod  = ["natterbox.pub", "natterbox.com"]
  }
}
```

### AWS Resources Created

| Resource Type | Description |
|---------------|-------------|
| `aws_route53_zone` | Primary hosted zone |
| `aws_route53_zone` | Public hosted zone |
| `aws_route53_zone` | Branded hosted zones |
| `aws_route53_zone` | SIP subdomain zone |
| `aws_route53_key_signing_key` | DNSSEC KSK |
| `aws_route53_hosted_zone_dnssec` | DNSSEC configuration |
| `aws_kms_key` | KMS key for DNSSEC |
| `aws_cloudwatch_metric_alarm` | DNSSEC validation alarms |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `primary_domain` | string | Primary domain |
| `public_domain` | string | Public domain |
| `primary_zone_id` | string | Primary zone ID |
| `public_zone_id` | string | Public zone ID |
| `sip_zone_id` | string | SIP subdomain zone ID |
| `branded_zone_ids` | map(string) | Branded zone IDs |
| `all_domains_map` | map(string) | All domains to zone IDs |
| `name_servers` | map(list(string)) | NS records per zone |
| `dnssec_ds_records` | map(string) | DS records for registrar |

---

## terraform-fsx - Complete Reference

### Repository
`redmatter/aws-terraform-fsx`

### Description
Provisions FSx (FreeSWITCH Extension) service in ECS.

### Variables

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `task_cpu` | string | CPU units | `512` |
| `task_memory` | string | Memory MB | `1024` |
| `min_task_count` | map(number) | Minimum tasks | dev: 1, prod: 2 |
| `max_task_count` | map(number) | Maximum tasks | dev: 2, prod: 6 |
| `subdomain` | string | Service subdomain | `fsx` |

### Resources Created

| Resource | Description |
|----------|-------------|
| `aws_ecs_service` | FSx ECS service |
| `aws_ecs_task_definition` | FSx task definition |
| `aws_lb_target_group` | ALB target group |
| `aws_cloudwatch_log_group` | Log group |
| `aws_appautoscaling_target` | Auto-scaling target |
| `aws_appautoscaling_policy` | Scaling policies |

---

## terraform-waf - Complete Reference

### Repository
`redmatter/aws-terraform-waf`

### Description
Provisions AWS WAF rules and web ACLs.

### Variables

| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `rate_limit` | number | Requests per 5 min | `2000` |
| `rate_limit_uri` | number | Per-URI rate limit | `1000` |
| `enable_sql_injection_protection` | bool | SQL injection rules | `true` |
| `enable_xss_protection` | bool | XSS protection rules | `true` |
| `enable_bot_control` | bool | Bot control rules | `true` (prod) |
| `blocked_countries` | list(string) | Geo-blocked countries | `[]` |

### WAF Rules Created

| Rule | Priority | Description |
|------|----------|-------------|
| `AWSManagedRulesCommonRuleSet` | 1 | Common vulnerabilities |
| `AWSManagedRulesSQLiRuleSet` | 2 | SQL injection |
| `AWSManagedRulesKnownBadInputsRuleSet` | 3 | Known bad inputs |
| `AWSManagedRulesLinuxRuleSet` | 4 | Linux-specific attacks |
| `RateLimitRule` | 5 | Rate limiting |
| `GeoBlockRule` | 6 | Geographic blocking |

---

## Additional Module Quick Reference

### terraform-omnichannel
- **Purpose**: Omnichannel communication infrastructure
- **AWS Services**: Lambda, API Gateway, DynamoDB, SQS

### terraform-bedrock
- **Purpose**: AWS Bedrock AI/ML infrastructure
- **AWS Services**: Bedrock, IAM, CloudWatch

### terraform-security-tools
- **Purpose**: Security monitoring and compliance
- **AWS Services**: GuardDuty, Security Hub, Config, CloudTrail

### terraform-iam
- **Purpose**: Central IAM management
- **AWS Services**: IAM users, groups, roles, policies

### terraform-acm
- **Purpose**: Certificate management
- **AWS Services**: ACM certificates with DNS validation

### terraform-events
- **Purpose**: Event processing infrastructure
- **AWS Services**: EventBridge, Lambda, SNS

### terraform-platform
- **Purpose**: Kinesis streams for ESL events
- **AWS Services**: Kinesis Data Streams, Kinesis Firehose

---

## Provider Version Matrix

| Module | AWS Provider | Terraform | Notes |
|--------|-------------|-----------|-------|
| network-rt | ~> 5.0 | ~> 1.0 | Latest features |
| rt-core-api | ~> 5.81 | ~> 1.0 | ECS improvements |
| rt-ecs | ~> 3.65 | ~> 1.0 | Legacy stable |
| rt-pbx | ~> 5.78 | ~> 1.0 | EC2 improvements |
| dns | ~> 4.27 | ~> 1.0 | DNSSEC support |
| waf | ~> 5.0 | ~> 1.0 | WAFv2 |
| fsx | ~> 5.0 | ~> 1.0 | ECS |
| omnichannel | ~> 5.0 | ~> 1.0 | Lambda |
| bedrock | ~> 4.0 | ~> 1.0 | AI services |

---

## Workspace Quick Reference

### Format: `{account}-{region_code}`

| Workspace | Account | Region | Environment |
|-----------|---------|--------|-------------|
| `dev01-use2` | dev01 | us-east-2 | Development |
| `dev01-usw2` | dev01 | us-west-2 | Development |
| `qa01-use2` | qa01 | us-east-2 | QA |
| `qa01-usw2` | qa01 | us-west-2 | QA |
| `qa02-use2` | qa02 | us-east-2 | QA |
| `qa02-usw2` | qa02 | us-west-2 | QA |
| `stage-apse2` | stage | ap-southeast-2 | Staging |
| `stage-euw2` | stage | eu-west-2 | Staging |
| `prod-apse1` | prod | ap-southeast-1 | Production |
| `prod-apse2` | prod | ap-southeast-2 | Production |
| `prod-euc1` | prod | eu-central-1 | Production |
| `prod-euw2` | prod | eu-west-2 | Production |
| `prod-use2` | prod | us-east-2 | Production |
| `prod-usw2` | prod | us-west-2 | Production |
