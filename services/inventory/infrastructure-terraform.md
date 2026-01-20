# Infrastructure as Code Repository Inventory

> **Last Updated**: 2026-01-20
> **Maintainers**: Platform Infrastructure Team, DevOps Team
> **Classification**: Internal Technical Documentation

## Overview

This document provides a comprehensive inventory of all Infrastructure as Code (IaC) repositories used at Red Matter/Natterbox. The infrastructure is primarily managed using Terraform for AWS resources and Salt Stack for configuration management.

---

## Table of Contents

1. [Repository Categories](#repository-categories)
2. [Core Foundation Modules](#core-foundation-modules)
3. [Networking Modules](#networking-modules)
4. [Real-Time Platform (RT) Modules](#real-time-platform-rt-modules)
5. [Security and IAM Modules](#security-and-iam-modules)
6. [DNS and Certificate Management](#dns-and-certificate-management)
7. [Event Processing Modules](#event-processing-modules)
8. [Configuration Management (Salt Stack)](#configuration-management-salt-stack)
9. [Supporting Infrastructure Modules](#supporting-infrastructure-modules)
10. [Module Dependency Graph](#module-dependency-graph)
11. [Workspace Naming Conventions](#workspace-naming-conventions)
12. [Provider Requirements](#provider-requirements)

---

## Repository Categories

| Category | Purpose | Count |
|----------|---------|-------|
| Core Foundation | Account management, builds, base infrastructure | 5+ |
| Networking | VPC, subnets, VPN, peering, load balancers | 3+ |
| Real-Time Platform | PBX, SIP, Core API, ECS, TTS services | 10+ |
| Security & IAM | IAM roles, security tools, WAF | 4+ |
| DNS & Certificates | Route53, ACM, DNSSEC | 2+ |
| Event Processing | Kinesis, EventBridge, Lambda pipelines | 3+ |
| Configuration Management | Salt Stack, AMI builders | 3+ |

---

## Core Foundation Modules

### terraform-accounts

**Repository**: `redmatter/terraform-terraform-accounts`

**Purpose**: Central source of truth for AWS account information including account IDs, types, and environment configurations.

**Key Features**:
- Outputs account IDs for all environments
- Defines account types (dev, qa, stage, prod)
- Used by all other Terraform modules for account resolution

**Workspaces**: Global - used as data source by other modules

**Outputs**:
| Output | Description |
|--------|-------------|
| `account_ids` | Map of workspace names to AWS account IDs |
| `account_types` | Map of account to environment type |
| `available_accounts` | List of all available account workspaces |

---

### terraform-build

**Repository**: `redmatter/aws-terraform-build`

**Purpose**: Provisions build infrastructure including S3 artifact buckets and ECR repositories.

**AWS Services Provisioned**:
- S3 buckets for build artifacts
- ECR repositories for container images
- IAM roles for CI/CD pipelines

**Dependencies**:
- `terraform-accounts`

**Workspaces**: Per-account (e.g., `dev01`, `qa01`, `stage`, `prod`)

---

### terraform-bedrock

**Repository**: `redmatter/aws-terraform-bedrock`

**Purpose**: Provisions AWS Bedrock AI/ML infrastructure for conversational AI capabilities.

**AWS Services Provisioned**:
- Amazon Bedrock inference endpoints
- IAM roles for Bedrock access
- CloudWatch logging for Bedrock usage

**Variables**:
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `assume_role_name` | string | Role to assume when applying state | `TerraformApplyAdmin` |
| `aws_profile` | string | Local IAM profile for AWS access | `terraform` |
| `map_migrated_tag` | string | Tag for AWS migration credits | `mig5QIKUES7BE` |

**Provider Requirements**:
```hcl
terraform {
  required_version = "~> 1.0"
}

provider "aws" {
  version = "~> 4.0"
}
```

---

## Networking Modules

### terraform-network-rt

**Repository**: `redmatter/aws-terraform-network-rt`

**Purpose**: Network provisioning for the RT (Real-Time) platform. Sets up VPCs, VPNs, subnets, security groups, and load balancers.

**AWS Services Provisioned**:
- VPCs with multi-AZ support
- Subnets (public, private, VPN, NAT)
- Internet Gateways
- NAT Gateways
- Application Load Balancers (ALB)
- Network Load Balancers (NLB)
- VPN Connections
- VPC Peering
- VPC Endpoints (ECR, ECS, CloudWatch, SSM, etc.)
- Security Groups
- Route Tables
- Global Accelerators (for CTI)

**Network Zones**:
| Zone | Purpose |
|------|---------|
| Red Internal | Internal services requiring high security |
| Red Public | Public-facing voice services |
| Red VPN | VPN termination |
| Amber Internal | Internal application services |
| Amber NAT | NAT gateway subnets |
| Green VPN DB | Database VPN connectivity |

**Key Variables**:
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `deployed_regions` | map(set(string)) | Map of account to deployed RT regions | See below |
| `ssl_policy_alb` | string | AWS SSL policy for ALBs | `ELBSecurityPolicy-TLS13-1-2-2021-06` |
| `ssl_policy_nlb` | string | AWS SSL policy for NLBs | `ELBSecurityPolicy-TLS13-1-2-2021-06` |
| `lb_deletion_protection` | bool | Enable LB deletion protection | `true` |
| `max_subnet_azs` | number | Maximum AZs to support | `4` |

**Deployed Regions by Account**:
```hcl
deployed_regions = {
  dev01 = ["us-east-2", "us-west-2"]
  qa01  = ["us-east-2", "us-west-2"]
  qa02  = ["us-east-2", "us-west-2"]
  stage = ["ap-southeast-2", "eu-west-2"]
  prod  = ["ap-southeast-1", "ap-southeast-2", "eu-central-1", 
           "eu-west-2", "us-east-2", "us-west-2"]
}
```

**Key Outputs**:
| Output | Description |
|--------|-------------|
| `vpc_id` | ID of the provisioned VPC |
| `alb_red_internal_arn` | ARN of the red-internal ALB |
| `alb_amber_internal_arn` | ARN of the amber-internal ALB |
| `subnet_ids_red_*` | Subnet IDs for red zone |
| `subnet_ids_amber_*` | Subnet IDs for amber zone |
| `security_group_id_*` | Security group IDs |

**Dependencies**:
- `terraform-accounts`
- `terraform-acm`
- `terraform-customer-gateway`
- `terraform-network-info`
- `terraform-transit-gateway`

**Workspaces**: `{account}-{region}` (e.g., `stage-apse2`, `prod-euw2`)

---

### terraform-network-info

**Repository**: `redmatter/aws-terraform-network-info`

**Purpose**: Acts as the source of truth for network ranges and configuration across different environments and platform types. Does not deploy resources.

**Use Cases**:
- Provides CIDR blocks for subnets
- Defines network topology
- Cross-environment network reference

---

## Real-Time Platform (RT) Modules

### terraform-rt-ecs

**Repository**: `redmatter/aws-terraform-rt-ecs`

**Purpose**: Provisions the ECS cluster for the real-time platform.

**AWS Services Provisioned**:
- ECS Cluster

**Variables**:
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `ecs_cluster_name` | string | Name of the ECS cluster | `RT` |
| `project` | string | AWS-friendly project name | `RTECS` |

**Outputs**:
| Output | Description |
|--------|-------------|
| `rt_cluster_id` | ID of the ECS Cluster |
| `rt_cluster_name` | Name of the ECS Cluster |
| `tf_module_version` | Version of the deployed module |

**Provider Requirements**:
```hcl
terraform {
  required_version = "~> 1.0"
}

provider "aws" {
  version = "~> 3.65"
}
```

**Dependencies**:
- `terraform-accounts`

---

### terraform-rt-core-api

**Repository**: `redmatter/aws-terraform-rt-core-api`

**Purpose**: Provisions the Core API container in ECS for the real-time platform.

**AWS Services Provisioned**:
- ECS Service (Fargate)
- ECS Task Definitions
- Application Load Balancer Listener Rules
- CloudWatch Log Groups
- CloudWatch Alarms
- CloudWatch Dashboard
- Auto Scaling (Target Tracking, Scheduled)
- Security Groups
- Route53 Records
- SNS Topics (Alarms)
- Lambda (Health Checks)
- SSM Parameters

**Key Variables**:
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `daytime_min_task_count` | map | Minimum tasks during business hours | dev: 2, prod: 12 |
| `offhours_min_task_count` | map | Minimum tasks off-hours | dev: 1, prod: 3 |
| `max_task_count` | map | Maximum task count | dev: 4, prod: 20 |
| `task_cpu` | string | CPU units for task | `1024` |
| `task_memory` | string | Memory for task | `2048` |
| `log_retention_days` | number | CloudWatch log retention | `30` |
| `subdomain` | string | Subdomain for ALB listener | `coreapi-local` |
| `subdomain_alias` | string | Additional subdomain | `coreapi` |

**Outputs**:
| Output | Description |
|--------|-------------|
| `domain_name` | Domain name for Core API access |
| `core_api_version` | Deployed version of core-api |
| `security_group_id_core_api` | Security group ID |
| `sns_alarms_topic_arn` | ARN of alarms SNS topic |
| `cascade_alarm_names` | Critical alarms for region health |

**Dependencies**:
- `terraform-accounts`
- `terraform-build`
- `terraform-network-info`
- `terraform-network-rt`
- `terraform-rt-ecs`
- `terraform-rt-rds`

**Provider Requirements**:
```hcl
terraform {
  required_version = "~> 1.0"
}

provider "aws" {
  version = "~> 5.81"
}
```

---

### terraform-rt-pbx

**Repository**: `redmatter/aws-terraform-rt-pbx`

**Purpose**: Provisions RT PBX (FreeSWITCH) instances with supporting resources.

**AWS Services Provisioned**:
- EC2 Instances (PBX servers)
- EBS Volumes (root and data)
- Network Interfaces (private and public)
- Elastic IPs
- Network Load Balancer (for ESL)
- Target Groups
- Security Groups
- Route53 Records
- CloudWatch Alarms
- CloudWatch Dashboard
- Lambda (Health Checks)
- IAM Roles and Policies
- SNS Topics

**Key Variables**:
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `instance_types` | map(string) | EC2 instance types per workspace | prod: `m6a.2xlarge` |
| `root_volume_gb` | map | Root volume size | dev: 16, prod: 128 |
| `data_volume_gb` | map | Data volume size (/var/lib/freeswitch) | dev: 8, prod: 500 |
| `esl_port` | number | ESL load balancing port | `8021` |
| `role` | string | EC2 instance role | `pbx` |
| `network_zone` | string | Network zone grain | `red` |

**Host Placement (Production)**:
```hcl
host_placement = {
  "prod-euw2" = {
    "01a" = "eu-west-2a"
    "01b" = "eu-west-2b"
    "01c" = "eu-west-2c"
    "02a" = "eu-west-2a"
    "02b" = "eu-west-2b"
    "02c" = "eu-west-2c"
    "03a" = "eu-west-2a"
  }
}
```

**Dependencies**:
- `terraform-accounts`
- `terraform-build`
- `terraform-network-info`
- `terraform-network-rt`
- `terraform-salt-master`
- `terraform-rt-core-api`
- `terraform-rt-sip`
- `terraform-rt-tts`
- `terraform-rt-transcribed`
- `terraform-fsx`
- `terraform-platform`
- `terraform-lumina-distributor`

**AMI Requirement**: Salt minion AMI built using `aws-ami-builder`

---

### terraform-rt-sip

**Repository**: `redmatter/aws-terraform-rt-sip`

**Purpose**: Provisions SIP EC2 instances along with supporting resources.

**AWS Services Provisioned**:
- EC2 Instances (SIP servers)
- Security Groups
- Route53 Records

---

### terraform-rt-tts

**Repository**: `redmatter/aws-terraform-rt-tts`

**Purpose**: Provisions the Text-to-Speech (TTS) service in ECS for the real-time platform.

---

### terraform-rt-transcribed

**Repository**: `redmatter/aws-terraform-rt-transcribed`

**Purpose**: Provisions the TranscribeD service in ECS for the real-time platform (speech-to-text).

---

## Security and IAM Modules

### terraform-iam

**Repository**: `redmatter/aws-terraform-iam`

**Purpose**: Central IAM management for all AWS accounts. Manages users, groups, roles, and policies.

**Key Features**:
- Cross-account role assumption
- Service-linked roles
- CI/CD IAM configurations
- MFA enforcement

---

### terraform-security-tools

**Repository**: `redmatter/aws-terraform-security-tools`

**Purpose**: Provisions security monitoring and compliance tools.

**AWS Services**:
- AWS Config
- GuardDuty
- Security Hub
- CloudTrail aggregation

---

### terraform-waf

**Repository**: `redmatter/aws-terraform-waf`

**Purpose**: Provisions AWS WAF (Web Application Firewall) rules and web ACLs.

**Key Features**:
- Rate limiting rules
- SQL injection protection
- XSS protection
- Geo-blocking capabilities
- Bot control

---

### terraform-security-configs

**Repository**: `redmatter/aws-terraform-security-configs`

**Purpose**: Manages general security configurations for AWS infrastructure on a regional basis.

---

## DNS and Certificate Management

### terraform-dns

**Repository**: `redmatter/aws-terraform-dns`

**Purpose**: Bootstraps Route 53 for DNS management across all environments.

**Hosted Zone Types**:
| Type | Example | Purpose |
|------|---------|---------|
| Primary Domain | `redmatter-stage.pub` | Internal infrastructure |
| Branded Domain | `natterbox-stage.pub` | Customer-facing |
| Public Domain | `natterbox-stage.net` | RT platform |
| SIP Subdomain | `sip.natterbox-stage.net` | Voice services |

**Key Variables**:
| Variable | Type | Description |
|----------|------|-------------|
| `primary_domains` | map(string) | Primary domain per workspace |
| `public_domains` | map(string) | Public domain per workspace |
| `branded_domains` | map(list(string)) | Branded domains per workspace |
| `continent_region_map` | map(string) | AWS continent to RM region mapping |
| `country_region_map` | map(string) | ISO country to RM region mapping |

**DNSSEC Support**: Full DNSSEC implementation with KSK management

**Key Outputs**:
| Output | Description |
|--------|-------------|
| `primary_domain` | Primary domain for the account |
| `public_domain` | Public domain for the account |
| `primary_zone_id` | Zone ID of primary domain |
| `public_zone_id` | Zone ID of public domain |
| `all_domains_map` | Map of all domains to zone IDs |
| `name_servers` | Route 53 name servers |

**Provider Requirements**:
```hcl
terraform {
  required_version = "~> 1.0"
}

provider "aws" {
  version = "~> 4.27"
}
```

---

### terraform-acm

**Repository**: `redmatter/aws-terraform-acm`

**Purpose**: Provisions and manages SSL/TLS certificates via AWS Certificate Manager.

**Key Features**:
- Wildcard certificate provisioning
- DNS validation automation
- Multi-region certificate replication

---

## Event Processing Modules

### terraform-events

**Repository**: `redmatter/aws-terraform-events`

**Purpose**: Provisions event processing infrastructure using EventBridge and related services.

---

### terraform-platform

**Repository**: `redmatter/aws-terraform-platform`

**Purpose**: Provisions the Kinesis stream for FreeSWITCH ESL events (used by fs-to-aws).

**AWS Services**:
- Kinesis Data Streams
- Kinesis Firehose
- Lambda consumers

---

### terraform-lumina-region-distributor

**Repository**: `redmatter/aws-terraform-lumina-region-distributor`

**Purpose**: Kinesis Data Stream and Lambda Function for distributing Lumina (PBX observability) events to different regions.

---

### terraform-lumina-pipeline

**Repository**: `redmatter/aws-terraform-lumina-pipeline`

**Purpose**: Pipeline infrastructure for Lumina observability data.

---

## Configuration Management (Salt Stack)

### infrastructure-salt-stack

**Repository**: `redmatter/infrastructure-salt-stack`

**Purpose**: Salt Stack configuration management for all server infrastructure.

**Structure**:
```
infrastructure-salt-stack/
├── docs/                    # Documentation
│   ├── deployment.md
│   ├── grains.md
│   ├── networking.md
│   └── versions.md
├── etc/                     # Configuration files
│   ├── master              # Salt master config
│   ├── minion              # Salt minion config
│   └── grains.*            # Environment grains
├── srv/
│   ├── custom/             # Custom Salt modules
│   │   └── _modules/       # Custom execution modules
│   ├── pillar/             # Pillar data
│   │   ├── common/         # Common configurations
│   │   ├── docker/         # Docker container configs
│   │   ├── mysql/          # MySQL configurations
│   │   ├── network/        # Network configurations
│   │   └── unsecure/       # Non-sensitive configs
│   ├── reactor/            # Reactor configurations
│   └── salt/               # Salt states
│       ├── atlassianproxy/
│       ├── bak/            # Backup configurations
│       ├── bld/            # Build server
│       └── ...
└── docker-compose.yml      # Local development
```

**Key State Modules**:
| State | Purpose |
|-------|---------|
| `docker/container/*` | Docker container configurations |
| `pbx/*` | PBX server configuration |
| `sip/*` | SIP server configuration |
| `mysql/*` | MySQL/MariaDB configuration |
| `network/*` | Network configuration |
| `tls/*` | TLS certificate management |

**Grain-Based Targeting**:
- `role`: Server role (pbx, sip, api, etc.)
- `network_zone`: Network zone (red, amber, green)
- `dc`: Data center location
- `environment`: Environment type (dev, qa, stage, prod)

---

### terraform-salt-master

**Repository**: `redmatter/aws-terraform-salt-master`

**Purpose**: Provisions Salt Master EC2 instance with supporting resources.

**AWS Services**:
- EC2 Instance
- Security Groups
- IAM Role

---

### aws-ami-builder

**Repository**: `redmatter/aws-ami-builder`

**Purpose**: Packer configurations for building AMIs, particularly Salt minion images.

**Key AMIs Built**:
- Salt minion base AMI
- Shared to appropriate regions and accounts from dev01

---

## Supporting Infrastructure Modules

### terraform-omnichannel

**Repository**: `redmatter/aws-terraform-omnichannel`

**Purpose**: Provisions omnichannel communication infrastructure (chat, SMS, email integration).

**Key Variables**:
| Variable | Type | Description | Default |
|----------|------|-------------|---------|
| `assume_role_name` | string | Role for state application | `TerraformApplyAdmin` |
| `aws_profile` | string | Local IAM profile | `terraform` |

---

### terraform-fsx

**Repository**: `redmatter/aws-terraform-fsx`

**Purpose**: Provisions FSx (FreeSWITCH Extension) service in ECS for the real-time platform.

---

### terraform-eci

**Repository**: `redmatter/aws-terraform-eci`

**Purpose**: Enterprise Communication Integration infrastructure.

---

### terraform-cai

**Repository**: `redmatter/aws-terraform-cai`

**Purpose**: Conversational AI infrastructure including CAI service deployments.

---

### terraform-rt-cai-websocket

**Repository**: `redmatter/aws-terraform-rt-cai-websocket`

**Purpose**: Deploys CAI WebSocket service to RT platform for real-time AI interactions.

---

### terraform-hosted-runners-build

**Repository**: `redmatter/terraform-hosted-runners-build`

**Purpose**: Deploys GitHub CodeBuild self-hosted runners infrastructure.

---

### terraform-rt-deepgram

**Repository**: `redmatter/terraform-rt-deepgram`

**Purpose**: Deepgram speech-to-text integration for RT platform.

---

## Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FOUNDATION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │ terraform-       │    │ terraform-       │    │ terraform-       │      │
│  │ accounts         │◄───│ network-info     │    │ build            │      │
│  │ (Account IDs)    │    │ (CIDR Blocks)    │    │ (S3/ECR)         │      │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘      │
│           │                       │                       │                 │
└───────────┼───────────────────────┼───────────────────────┼─────────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NETWORKING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │ terraform-dns    │    │ terraform-       │◄───│ terraform-       │      │
│  │ (Route53/DNSSEC) │    │ network-rt       │    │ acm              │      │
│  └────────┬─────────┘    │ (VPC/Subnets/LB) │    │ (Certificates)   │      │
│           │              └────────┬─────────┘    └──────────────────┘      │
│           │                       │                                         │
└───────────┼───────────────────────┼─────────────────────────────────────────┘
            │                       │
            │                       ▼
            │    ┌──────────────────────────────────────────────────────────┐
            │    │                    RT PLATFORM LAYER                      │
            │    ├──────────────────────────────────────────────────────────┤
            │    │                                                          │
            │    │  ┌──────────────┐    ┌──────────────┐                   │
            │    │  │ terraform-   │    │ terraform-   │                   │
            │    │  │ rt-ecs       │◄───│ salt-master  │                   │
            │    │  │ (ECS Cluster)│    │              │                   │
            │    │  └──────┬───────┘    └──────────────┘                   │
            │    │         │                                                │
            │    │         ▼                                                │
            │    │  ┌──────────────────────────────────────────────────┐   │
            │    │  │                RT SERVICES                        │   │
            │    │  │                                                   │   │
            │    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
            │    │  │  │ rt-      │  │ rt-      │  │ rt-      │       │   │
            │    │  │  │ core-api │  │ pbx      │  │ sip      │       │   │
            └────┼──┼─►│          │  │          │  │          │       │   │
                 │  │  └──────────┘  └────┬─────┘  └──────────┘       │   │
                 │  │                      │                           │   │
                 │  │  ┌──────────┐  ┌────▼─────┐  ┌──────────┐       │   │
                 │  │  │ rt-tts   │  │ rt-      │  │ rt-      │       │   │
                 │  │  │          │◄─┤ transcr- │  │ fsx      │       │   │
                 │  │  │          │  │ ibed     │  │          │       │   │
                 │  │  └──────────┘  └──────────┘  └──────────┘       │   │
                 │  │                                                   │   │
                 │  └──────────────────────────────────────────────────┘   │
                 │                                                          │
                 └──────────────────────────────────────────────────────────┘
```

### Detailed Dependency Chain for RT Deployment

```
                                    terraform-accounts
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
            terraform-dns          terraform-network-info    terraform-build
                    │                      │                      │
                    │                      ▼                      │
                    │              terraform-network-rt ◄─────────┤
                    │                      │                      │
                    │    ┌─────────────────┼──────────────────┐   │
                    │    │                 │                  │   │
                    │    ▼                 ▼                  ▼   │
                    │ terraform-      terraform-        terraform-│
                    │ rt-ecs          rt-rds            salt-master
                    │    │                                    │   │
                    │    └─────────────┐  ┌──────────────────┘   │
                    │                  │  │                      │
                    │                  ▼  ▼                      │
                    │            terraform-rt-core-api           │
                    │                  │                         │
                    │    ┌─────────────┼─────────────────┐      │
                    │    │             │                 │      │
                    ▼    ▼             ▼                 ▼      ▼
              terraform-  terraform-  terraform-  terraform-  terraform-
              rt-sip      rt-pbx      rt-tts      rt-transcr. platform
                              │
                              ▼
                    terraform-lumina-distributor
```

---

## Workspace Naming Conventions

### Account-Level Workspaces
```
{account}
```
Examples: `dev01`, `qa01`, `qa02`, `stage`, `prod`

### Regional Workspaces
```
{account}-{region_shortcode}
```

**Region Short Codes**:
| Short Code | AWS Region |
|------------|------------|
| `use2` | us-east-2 |
| `usw2` | us-west-2 |
| `euw2` | eu-west-2 |
| `euc1` | eu-central-1 |
| `apse1` | ap-southeast-1 |
| `apse2` | ap-southeast-2 |

Examples: `stage-apse2`, `prod-euw2`, `dev01-use2`

### Role Module Workspaces
Role modules (IAM resources) use account-level workspaces since IAM is global:
```
{account}
```

---

## Provider Requirements

### Standard Provider Configuration

Most modules use the following pattern:

```hcl
terraform {
  required_version = "~> 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Varies by module
    }
    random = {
      source = "hashicorp/random"
    }
  }
  
  backend "s3" {
    bucket         = "rm-terraform-state"
    key            = "module-name/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = local.region
  
  assume_role {
    role_arn = "arn:aws:iam::${local.account_id}:role/${var.assume_role_name}"
  }
}
```

### Common Provider Versions by Module

| Module | AWS Provider Version | Terraform Version |
|--------|---------------------|-------------------|
| terraform-rt-ecs | ~> 3.65 | ~> 1.0 |
| terraform-rt-pbx | ~> 5.78 | ~> 1.0 |
| terraform-rt-core-api | ~> 5.81 | ~> 1.0 |
| terraform-dns | ~> 4.27 | ~> 1.0 |
| terraform-network-rt | ~> 5.0 | ~> 1.0 |

---

## Deployment Workflow

### Standard Terraform Deployment

1. **Clone the repository**:
```bash
git clone git@github.com:redmatter/aws-terraform-{module}.git
cd terraform-{module}
```

2. **Deploy role module (if exists)**:
```bash
cd role
terraform init
terraform workspace new {account}
terraform apply
cd ..
```

3. **Deploy main module**:
```bash
terraform init
terraform workspace new {account}-{region}
terraform apply
```

### Multi-Region Deployment Order

For new regions, deploy in the following order:

1. `terraform-accounts` (if new account)
2. `terraform-dns`
3. `terraform-acm`
4. `terraform-network-rt`
5. `terraform-rt-ecs`
6. `terraform-salt-master`
7. `terraform-rt-rds`
8. `terraform-rt-core-api`
9. `terraform-rt-sip`
10. `terraform-rt-pbx`
11. `terraform-rt-tts`
12. `terraform-rt-transcribed`

---

## SSM Parameters

Many modules require SSM parameters to be created before deployment:

| Parameter | Module | Description |
|-----------|--------|-------------|
| `rt.core-api.core-db.password` | rt-core-api | Core DB password |
| `rt.opsgenie.cloudwatch_endpoint` | network-rt | OpsGenie webhook URL |
| `rt.pagerduty.cloudwatch_endpoint` | network-rt | PagerDuty webhook URL (prod) |
| `dns.opsgenie.cloudwatch_endpoint` | dns | OpsGenie webhook for DNS |
| `rt.certificate.default.key` | network-rt | Default TLS certificate key |
| `rt.certificate.default.chain` | network-rt | Default TLS certificate chain |

---

## Version Control and Tags

All modules use:
- **Git flow**: Feature branches → develop → master/main
- **Semantic versioning**: via `terraform-git-version` module
- **Automated documentation**: via `terraform-docs`
- **Pre-commit hooks**: For formatting and validation

---

## Related Documentation

- [AWS Docs](https://github.com/redmatter/aws-docs) - General AWS documentation
- [Salt Stack Deployment](https://github.com/redmatter/infrastructure-salt-stack/blob/master/docs/deployment.md)
- [Network Zones](https://github.com/redmatter/infrastructure-salt-stack/blob/master/docs/networking.md)
- [BYOIP Guide](https://github.com/redmatter/aws-terraform-network-rt/blob/master/docs/byoip.md)
- [DNSSEC Setup](https://github.com/redmatter/aws-terraform-dns/blob/master/dnssec.md)
