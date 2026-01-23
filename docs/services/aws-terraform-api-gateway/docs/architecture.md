# Architecture and Design

## Overview

The `aws-terraform-api-gateway` module is a foundational infrastructure component that provisions AWS API Gateway account-level resources across multiple AWS regions. This document explains the architectural decisions, module structure, and design patterns that make this module an essential building block for API Gateway deployments in AWS.

Understanding the architecture of this module is critical for operators who need to deploy, maintain, and troubleshoot API Gateway infrastructure across global AWS environments.

---

## Module Structure

### High-Level Architecture

The module follows a hierarchical structure designed for reusability, maintainability, and multi-region support:

```
aws-terraform-api-gateway/
├── main.tf                    # Root module orchestration
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Module outputs
├── versions.tf                # Terraform and provider version constraints
├── README.md                  # Module documentation
└── modules/
    └── api-gateway/           # Reusable submodule
        ├── main.tf            # API Gateway account resources
        ├── variables.tf       # Submodule variables
        ├── outputs.tf         # Submodule outputs
        └── versions.tf        # Version constraints
```

### Design Philosophy

The module structure adheres to several key design principles:

1. **Composition over Inheritance**: The root module composes multiple instances of the `api-gateway` submodule rather than using complex conditional logic.

2. **Single Responsibility**: Each submodule instance manages API Gateway account resources for exactly one AWS region.

3. **DRY (Don't Repeat Yourself)**: Common resource configurations are encapsulated in the reusable submodule, eliminating code duplication across regions.

4. **Explicit Dependencies**: Resource relationships are clearly defined, making the dependency graph predictable and debuggable.

### Submodule Architecture

The `modules/api-gateway` submodule encapsulates all region-specific API Gateway account configuration:

```hcl
# modules/api-gateway/main.tf - Conceptual structure

# API Gateway Account Settings
resource "aws_api_gateway_account" "this" {
  cloudwatch_role_arn = var.cloudwatch_role_arn
}

# Additional region-specific resources
# (CloudWatch log groups, settings, etc.)
```

This submodule is instantiated once per supported region in the root module:

```hcl
# main.tf - Root module pattern

module "api_gateway_us_east_1" {
  source = "./modules/api-gateway"
  
  providers = {
    aws = aws.us_east_1
  }
  
  cloudwatch_role_arn = var.cloudwatch_role_arn
  # Additional configuration...
}

module "api_gateway_eu_west_1" {
  source = "./modules/api-gateway"
  
  providers = {
    aws = aws.eu_west_1
  }
  
  cloudwatch_role_arn = var.cloudwatch_role_arn
  # Additional configuration...
}

# Repeated for all 8 supported regions...
```

---

## Resource Hierarchy

### AWS Resource Relationships

Understanding the resource hierarchy is essential for troubleshooting and maintenance:

```
AWS Account (Global)
│
├── IAM Role (Global - managed by terraform-iam)
│   └── Trust Policy: apigateway.amazonaws.com
│   └── Permissions: CloudWatch Logs write access
│
└── API Gateway Account Settings (Per-Region)
    ├── Region: us-east-1
    │   └── CloudWatch Role ARN → IAM Role
    │
    ├── Region: us-east-2
    │   └── CloudWatch Role ARN → IAM Role
    │
    ├── Region: us-west-1
    │   └── CloudWatch Role ARN → IAM Role
    │
    ├── Region: us-west-2
    │   └── CloudWatch Role ARN → IAM Role
    │
    ├── Region: eu-west-1
    │   └── CloudWatch Role ARN → IAM Role
    │
    ├── Region: eu-west-2
    │   └── CloudWatch Role ARN → IAM Role
    │
    ├── Region: eu-central-1
    │   └── CloudWatch Role ARN → IAM Role
    │
    └── Region: ap-southeast-1
        └── CloudWatch Role ARN → IAM Role
```

### Resource Dependencies

The following diagram illustrates the dependency flow:

```
┌─────────────────────────────────────────────────────────────────┐
│                     terraform-iam module                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         IAM Role: api-gateway-cloudwatch-role             │  │
│  │  • Global resource (not region-specific)                  │  │
│  │  • Trust policy for apigateway.amazonaws.com              │  │
│  │  • Permissions for CloudWatch Logs                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ cloudwatch_role_arn (output)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              aws-terraform-api-gateway module                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ us-east-1   │ │ us-west-2   │ │ eu-west-1   │  ...         │
│  │ API Gateway │ │ API Gateway │ │ API Gateway │              │
│  │ Account     │ │ Account     │ │ Account     │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ (enables)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Individual API Gateway APIs                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ REST API    │ │ HTTP API    │ │ WebSocket   │              │
│  │ (regional)  │ │ (regional)  │ │ API         │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Separate from terraform-iam

### Architectural Decision Record

The decision to separate API Gateway account configuration from the `terraform-iam` module was deliberate and based on several factors:

#### 1. Separation of Concerns

| Aspect | terraform-iam | aws-terraform-api-gateway |
|--------|---------------|---------------------------|
| **Primary Purpose** | Identity and access management | Service-specific configuration |
| **Resource Scope** | Global (IAM is not regional) | Regional (per-region settings) |
| **Change Frequency** | Low (IAM policies are stable) | Medium (new regions, settings) |
| **Blast Radius** | High (affects all services) | Limited (API Gateway only) |

#### 2. Deployment Independence

Separating these modules allows independent deployment lifecycles:

```
terraform-iam                    aws-terraform-api-gateway
     │                                    │
     │ (deploy first)                     │ (deploy second)
     ▼                                    ▼
┌─────────────┐                   ┌─────────────────┐
│ IAM Role    │ ──────────────────│ API GW Account  │
│ created     │   role_arn        │ configured      │
└─────────────┘                   └─────────────────┘
```

This separation means:
- IAM changes don't require API Gateway module updates
- API Gateway configuration can be modified without touching IAM
- Different teams can own different modules
- Rollback scenarios are isolated

#### 3. State File Management

```hcl
# terraform-iam state contains:
# - IAM roles, policies, users, groups
# - Global resources only

# aws-terraform-api-gateway state contains:
# - API Gateway account settings (8 regions)
# - Regional configuration only
```

Smaller, focused state files provide:
- Faster `terraform plan` execution
- Reduced risk of state corruption
- Easier state recovery
- Better access control (least privilege for state access)

#### 4. Testing and Validation

Isolated modules enable targeted testing:

```bash
# Test IAM module independently
cd terraform-iam
terraform plan
terraform apply

# Test API Gateway module independently  
cd aws-terraform-api-gateway
terraform plan
terraform apply
```

---

## Per-Region vs Per-Account Resources

### Understanding AWS API Gateway Resource Scoping

AWS API Gateway has a unique resource model that requires understanding the distinction between account-level and regional resources:

### Per-Account Resources (Global)

These resources exist once per AWS account:

| Resource | Description | Managed By |
|----------|-------------|------------|
| IAM Role for CloudWatch | Service role for API Gateway logging | terraform-iam |
| IAM Policies | Permissions for the service role | terraform-iam |
| Service Quotas | Account-wide API Gateway limits | AWS Service Quotas |

### Per-Region Resources

These resources must be configured in each AWS region where API Gateway is used:

| Resource | Description | Managed By |
|----------|-------------|------------|
| API Gateway Account Settings | CloudWatch role association | aws-terraform-api-gateway |
| CloudWatch Log Groups | Execution/access logs | Individual API modules |
| API Gateway APIs | REST, HTTP, WebSocket APIs | Individual API modules |
| Usage Plans | Throttling and quota settings | Individual API modules |

### Why Per-Region Configuration?

```
┌──────────────────────────────────────────────────────────────┐
│                        AWS Account                            │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  IAM (Global Service)                   │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Role: api-gateway-cloudwatch-role               │  │  │
│  │  │  ARN: arn:aws:iam::123456789:role/api-gw-cw     │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                                │
│              ┌───────────────┼───────────────┐               │
│              ▼               ▼               ▼               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐   │
│  │   us-east-1    │ │   eu-west-1    │ │ ap-southeast-1 │   │
│  │ ┌────────────┐ │ │ ┌────────────┐ │ │ ┌────────────┐ │   │
│  │ │ API GW     │ │ │ │ API GW     │ │ │ │ API GW     │ │   │
│  │ │ Account    │ │ │ │ Account    │ │ │ │ Account    │ │   │
│  │ │ Settings   │ │ │ │ Settings   │ │ │ │ Settings   │ │   │
│  │ │            │ │ │ │            │ │ │ │            │ │   │
│  │ │ CW Role:   │ │ │ │ CW Role:   │ │ │ │ CW Role:   │ │   │
│  │ │ (same ARN) │ │ │ │ (same ARN) │ │ │ │ (same ARN) │ │   │
│  │ └────────────┘ │ │ └────────────┘ │ │ └────────────┘ │   │
│  └────────────────┘ └────────────────┘ └────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

The same IAM role ARN is referenced in each region's API Gateway account settings because:
- IAM is a global service (same role works everywhere)
- API Gateway account settings are regional (must be configured per-region)
- CloudWatch Logs are regional (logs stay in the region where APIs execute)

---

## Integration with API Gateway APIs

### Prerequisite Chain

Before deploying any API Gateway API (REST, HTTP, or WebSocket), this module must be applied:

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT ORDER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. terraform-iam                                                │
│     └── Creates IAM role for CloudWatch logging                 │
│                                                                  │
│  2. aws-terraform-api-gateway                                    │
│     └── Configures API Gateway account settings per region      │
│                                                                  │
│  3. Individual API modules (your application APIs)               │
│     └── Deploy REST/HTTP/WebSocket APIs with logging enabled    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Pattern

Individual API Gateway APIs reference the account-level configuration implicitly:

```hcl
# Example: Deploying an API that benefits from account-level setup

resource "aws_api_gateway_rest_api" "example" {
  name        = "example-api"
  description = "Example REST API"
}

resource "aws_api_gateway_stage" "example" {
  deployment_id = aws_api_gateway_deployment.example.id
  rest_api_id   = aws_api_gateway_rest_api.example.id
  stage_name    = "prod"

  # CloudWatch logging works because aws-terraform-api-gateway
  # configured the account-level CloudWatch role association
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }
}

# This log group receives logs because the account-level
# CloudWatch role has been configured by aws-terraform-api-gateway
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/api-gateway/example-api"
  retention_in_days = 30
}
```

### What Happens Without This Module?

If you attempt to enable API Gateway logging without first applying this module:

```
Error: Error updating API Gateway Account: AccessDeniedException: 
API Gateway does not have permission to write logs to CloudWatch. 
Please ensure that the IAM role has been configured for the account.
```

This error occurs because:
1. API Gateway needs permission to write to CloudWatch Logs
2. The service role must be associated with each region's API Gateway account
3. This association is what `aws-terraform-api-gateway` provides

---

## Summary

The `aws-terraform-api-gateway` module serves as critical infrastructure that:

1. **Enables Observability**: Allows all API Gateway APIs to write logs to CloudWatch
2. **Provides Multi-Region Support**: Configures 8 AWS regions with consistent settings
3. **Maintains Separation of Concerns**: Keeps API Gateway configuration isolated from IAM
4. **Supports Scalability**: Uses a modular design that can easily extend to new regions

Understanding this architecture helps operators:
- Troubleshoot logging issues with API Gateway
- Plan infrastructure deployments correctly
- Maintain and extend the module as requirements evolve
- Communicate dependencies to development teams