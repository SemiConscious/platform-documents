# Infrastructure Architecture

> **Last Updated:** 2026-01-19  
> **Source:** Terraform modules, repository analysis  
> **Status:** ✅ Complete

---

## Overview

Natterbox infrastructure is managed via Infrastructure as Code (IaC) using Terraform for AWS resources and Salt Stack for configuration management on EC2 instances.

---

## Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          INFRASTRUCTURE LAYERS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        CI/CD & Deployment                                │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │   GitHub    │  │   Bamboo    │  │ CodeBuild/  │  │  Guardian   │    │  │
│   │  │   Actions   │  │             │  │ Pipeline    │  │   (Salt)    │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         Terraform Modules                                │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │  Network    │  │  Compute    │  │  Database   │  │  Services   │    │  │
│   │  │   (VPC)     │  │  (ECS/EC2)  │  │  (RDS)      │  │  (Lambda)   │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                          AWS Foundation                                  │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │    IAM      │  │     KMS     │  │    Route    │  │   Account   │    │  │
│   │  │   Roles     │  │    Keys     │  │     53      │  │   Config    │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## AWS Account Structure

| Account | Purpose | Regions |
|---------|---------|---------|
| **prod** | Production workloads | us-east-2, us-west-2, eu-west-2, eu-central-1, ap-southeast-1, ap-southeast-2 |
| **stage** | Staging environment | eu-west-2, ap-southeast-2 |
| **dev01** | Development | us-east-2, us-west-2 |
| **qa01** | QA testing | us-east-2, us-west-2 |
| **qa02** | Additional QA | us-east-2, us-west-2 |
| **nexus** | Global shared services | us-east-1 (global) |
| **build** | CI/CD infrastructure | us-east-1 |
| **security** | Security tooling | us-east-1 |

---

## Network Architecture

### RT VPC Structure

Each RT region VPC contains security zones:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            RT Region VPC                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         RED ZONE (Public)                                │  │
│   │  • Public PBX/SIP subnets                                               │  │
│   │  • CTI subnets                                                          │  │
│   │  • WebPhone subnets                                                     │  │
│   │  • VPN subnets                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                       AMBER ZONE (Internal)                              │  │
│   │  • Core API subnets                                                     │  │
│   │  • Service Gateway subnets                                              │  │
│   │  • FreeSWITCH (FSX) subnets                                             │  │
│   │  • CAI WebSocket subnets                                                │  │
│   │  • NAT subnets                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        GREEN ZONE (Data)                                 │  │
│   │  • Database subnets (RDS, Aurora)                                       │  │
│   │  • VPN DB subnets                                                       │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Network Components

| Component | Purpose |
|-----------|---------|
| **Internet Gateway** | Public internet access |
| **NAT Gateways** | Outbound internet for private subnets (one per AZ) |
| **VPN Gateway** | Connection to on-premise DCs |
| **Global Accelerator** | Low-latency global routing for CTI |
| **VPC Peering** | Cross-region RT VPC connectivity |
| **Transit Gateway** | Hub connectivity for complex routing |

### VPC Endpoints

Private connectivity to AWS services:
- S3 (Gateway)
- DynamoDB (Gateway)
- ECR API/Docker (Interface)
- CloudWatch Logs (Interface)
- Secrets Manager (Interface)
- SSM (Interface)
- ECS (Interface)

---

## Terraform Structure

### Module Organization

```
aws-terraform-*/
├── README.md              # Documentation
├── main.tf               # Main resources
├── variables.tf          # Input variables
├── outputs.tf            # Output values
├── versions.tf           # Provider versions
├── aws.tf                # AWS provider config
├── role/                 # IAM role submodule
│   ├── main.tf
│   └── variables.tf
└── docs/                 # Additional documentation
```

### Key Terraform Modules

#### Foundation

| Module | Description |
|--------|-------------|
| `terraform-terraform-accounts` | Account configuration and outputs |
| `aws-terraform-iam` | IAM roles and policies |
| `aws-terraform-kms-keys` | KMS key management |

#### Networking

| Module | Description |
|--------|-------------|
| `aws-terraform-network-rt` | RT VPC, subnets, ALBs, VPNs |
| `aws-terraform-network-info` | Network configuration data |
| `aws-terraform-transit-gateway` | Transit gateway setup |
| `aws-terraform-customer-gateway` | VPN customer gateways |

#### Compute

| Module | Description |
|--------|-------------|
| `aws-terraform-rt-core-api` | Core API ECS service |
| `aws-terraform-fsx8` | FreeSWITCH PHP 8 instances |
| `aws-terraform-rt-pbx` | PBX EC2 instances |
| `aws-terraform-rt-sip` | SIP proxy instances |

#### Services

| Module | Description |
|--------|-------------|
| `aws-terraform-omnichannel` | Omnichannel infrastructure |
| `aws-terraform-cai` | CAI service infrastructure |
| `aws-terraform-lumina-pipeline` | Observability pipeline |
| `aws-terraform-bedrock` | AI/Bedrock configuration |

---

## Deployment Workflow

### Terraform Workspace Convention

Workspaces follow the pattern: `ACCOUNT-REGIONSHORTNAME`

| Workspace | Account | Region |
|-----------|---------|--------|
| `prod-usw2` | prod | us-west-2 |
| `prod-euw2` | prod | eu-west-2 |
| `stage-apse2` | stage | ap-southeast-2 |
| `dev01-use2` | dev01 | us-east-2 |

### Deployment Commands

```bash
# Initialize
terraform init

# Select workspace
terraform workspace select prod-usw2

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Deployment Dependencies

```
terraform-accounts
       │
       ▼
terraform-iam ──────────────────┐
       │                        │
       ▼                        ▼
terraform-network-rt ──► terraform-acm
       │
       ├────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
terraform-rt-core-api   terraform-rt-pbx        terraform-rt-sip
       │                        │                        │
       └────────────────────────┴────────────────────────┘
                                │
                                ▼
                    terraform-omnichannel
                    terraform-cai
                    terraform-lumina-pipeline
```

---

## Salt Stack Configuration

### Guardian System

Guardian manages Salt Stack deployments to EC2 instances:

**Repository:** `redmatter/guardian`

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Guardian     │────►│   Salt Master   │────►│   EC2 Minions   │
│    (Control)    │     │                 │     │   (PBX, SIP)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Salt States

**Repository:** `redmatter/salt-states`

Configuration states for:
- FreeSWITCH installation and config
- OpenSIPS installation and config
- System packages
- Monitoring agents
- SSL certificates

### Pillar Data

**Repository:** `redmatter/salt-pillar-*`

Environment-specific configuration:
- Database credentials
- API keys
- Service endpoints
- Feature flags

---

## CI/CD Architecture

### Pipeline Types

| Type | Tool | Use Case |
|------|------|----------|
| **Terraform** | CodeBuild | Infrastructure changes |
| **ECS Services** | CodePipeline | Container deployments |
| **Lambda** | SAM/CloudFormation | Serverless deployments |
| **Salt/Guardian** | Bamboo | EC2 configuration |
| **Salesforce** | GitHub Actions | SFDX package deployment |

### GitHub Actions Workflows

**Repository:** `redmatter/github-action-*`

| Action | Purpose |
|--------|---------|
| `github-action-apex-build` | Salesforce Apex CI |
| `github-action-tf-wrapper` | Terraform plan/apply |
| `github-action-lambda-deploy` | Lambda deployment |

### RMHT (Red Matter Helm Tool)

**Repository:** `redmatter/rmht`

Release management and deployment orchestration.

---

## Monitoring & Alerting

### CloudWatch

- Metrics collection
- Log aggregation
- Alarms via SNS

### OpsGenie Integration

```
CloudWatch Alarm → SNS Topic → OpsGenie Endpoint
```

### Pagerduty (Production)

```
CloudWatch Alarm → SNS Topic → Pagerduty (Automat-IT)
```

---

## Key Terraform Repositories

| Repository | Description |
|------------|-------------|
| `aws-terraform-network-rt` | RT VPC networking |
| `aws-terraform-iam` | IAM configuration |
| `aws-terraform-rt-core-api` | Core API infrastructure |
| `aws-terraform-fsx8` | FreeSWITCH infrastructure |
| `aws-terraform-omnichannel` | Omnichannel infrastructure |
| `aws-terraform-cai` | CAI infrastructure |
| `aws-terraform-bedrock` | Bedrock AI configuration |
| `aws-terraform-lumina-pipeline` | Observability pipeline |

---

## SSM Parameters

Common SSM parameters used across services:

| Parameter | Description |
|-----------|-------------|
| `rt.opsgenie.cloudwatch_endpoint` | OpsGenie webhook URL |
| `rt.certificate.default.key` | Default SSL certificate key |
| `rt.certificate.default.chain` | Default certificate chain |
| `omni.rm-coreapi.auth-token` | Core API auth token |

---

## Security

### Network Security

- **Security Groups** - Least privilege access
- **NACLs** - Subnet-level filtering
- **WAF** - Web application firewall on ALBs

### Secrets Management

- **SSM Parameter Store** - Configuration secrets
- **Secrets Manager** - Rotatable credentials
- **KMS** - Encryption keys

### Compliance

- **CloudTrail** - API audit logging
- **Config** - Resource compliance
- **GuardDuty** - Threat detection

---

## Related Documentation

- [Global Architecture](../global-architecture.md)
- [Terraform Module Catalog](../../terraform-modules/catalog.md)
- [Confluence: Network RT Docs](https://natterbox.atlassian.net/wiki/spaces/PE/)

---

*Documentation compiled from Terraform module READMEs and repository analysis*
