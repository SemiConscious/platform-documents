# Architecture Overview

## aws-terraform-bedrock

This document provides a comprehensive technical architecture overview of the aws-terraform-bedrock Terraform module. It covers the module structure, resource relationships, cross-region dependencies, and deployment patterns that enable scalable, secure, and highly available AWS Bedrock GenAI configurations.

---

## Module Structure

The aws-terraform-bedrock module follows a hierarchical structure designed for modularity, reusability, and maintainability. Understanding this structure is essential for operators who need to customize deployments or troubleshoot issues.

### Root Module Organization

```
aws-terraform-bedrock/
├── main.tf                    # Root module entry point
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output value definitions
├── versions.tf                # Provider version constraints
├── locals.tf                  # Local value computations
├── providers.tf               # Provider configurations
├── terraform.tfvars.example   # Example variable values
│
├── modules/                   # Submodule directory
│   ├── inference-profiles/    # Application inference profile management
│   ├── cross-region/          # Cross-region inference configuration
│   ├── guardrails/            # AI safety guardrail definitions
│   ├── monitoring/            # CloudWatch monitoring setup
│   └── iam/                   # IAM roles and policies
│
├── examples/                  # Usage examples
│   ├── single-region/         # Single region deployment
│   ├── multi-region/          # Multi-region deployment
│   └── complete/              # Full-featured deployment
│
└── tests/                     # Terratest validation
    └── integration/           # Integration test suites
```

### Core Configuration Files

The root module orchestrates all submodules and establishes the foundational infrastructure:

```hcl
# main.tf - Root module orchestration
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0"
    }
  }
}

# Primary region provider
provider "aws" {
  region = var.primary_region
  alias  = "primary"
  
  default_tags {
    tags = var.common_tags
  }
}

# Secondary region provider for cross-region deployments
provider "aws" {
  region = var.secondary_region
  alias  = "secondary"
  
  default_tags {
    tags = var.common_tags
  }
}
```

---

## Submodule Relationships

The module employs a layered architecture where each submodule handles specific concerns while maintaining clear dependency relationships.

### Dependency Graph

```
                    ┌─────────────────┐
                    │   Root Module   │
                    │    (main.tf)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │     IAM     │  │  Guardrails │  │  Monitoring │
    │   Module    │  │   Module    │  │   Module    │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           │                │                │
           ▼                ▼                ▼
    ┌─────────────────────────────────────────────┐
    │          Inference Profiles Module          │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │           Cross-Region Module               │
    └─────────────────────────────────────────────┘
```

### Submodule Descriptions

#### IAM Module (`modules/iam/`)

Manages all Identity and Access Management resources required for Bedrock operations:

```hcl
# modules/iam/main.tf
resource "aws_iam_role" "bedrock_execution" {
  name               = "${var.project_name}-bedrock-execution"
  assume_role_policy = data.aws_iam_policy_document.bedrock_assume_role.json
  
  tags = var.tags
}

resource "aws_iam_policy" "bedrock_model_access" {
  name        = "${var.project_name}-bedrock-model-access"
  description = "Policy for accessing Bedrock foundation models"
  policy      = data.aws_iam_policy_document.bedrock_model_access.json
}

data "aws_iam_policy_document" "bedrock_model_access" {
  statement {
    sid    = "BedrockModelInvocation"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:GetFoundationModel",
      "bedrock:ListFoundationModels"
    ]
    resources = var.model_arns
  }
  
  statement {
    sid    = "GuardrailAccess"
    effect = "Allow"
    actions = [
      "bedrock:ApplyGuardrail",
      "bedrock:GetGuardrail"
    ]
    resources = var.guardrail_arns
  }
}
```

#### Inference Profiles Module (`modules/inference-profiles/`)

Configures application inference profiles for consistent model access patterns:

```hcl
# modules/inference-profiles/main.tf
resource "aws_bedrock_inference_profile" "application" {
  for_each = var.inference_profiles
  
  name        = each.value.name
  description = each.value.description
  type        = "APPLICATION"
  
  model_source {
    copy_from = each.value.source_model_arn
  }
  
  tags = merge(var.common_tags, each.value.tags)
}

output "inference_profile_arns" {
  description = "Map of inference profile names to ARNs"
  value = {
    for k, v in aws_bedrock_inference_profile.application : k => v.arn
  }
}
```

#### Guardrails Module (`modules/guardrails/`)

Implements AI safety controls and content filtering:

```hcl
# modules/guardrails/main.tf
resource "aws_bedrock_guardrail" "main" {
  name                      = var.guardrail_name
  description               = var.guardrail_description
  blocked_input_messaging   = var.blocked_input_message
  blocked_outputs_messaging = var.blocked_output_message
  
  dynamic "content_policy_config" {
    for_each = var.content_filters
    content {
      filters_config {
        type            = content_policy_config.value.type
        input_strength  = content_policy_config.value.input_strength
        output_strength = content_policy_config.value.output_strength
      }
    }
  }
  
  dynamic "topic_policy_config" {
    for_each = var.denied_topics
    content {
      topics_config {
        name       = topic_policy_config.value.name
        definition = topic_policy_config.value.definition
        type       = "DENY"
        examples   = topic_policy_config.value.examples
      }
    }
  }
  
  dynamic "word_policy_config" {
    for_each = var.word_filters != null ? [1] : []
    content {
      managed_word_lists_config {
        type = "PROFANITY"
      }
      words_config {
        text = var.word_filters
      }
    }
  }
  
  tags = var.tags
}

resource "aws_bedrock_guardrail_version" "main" {
  guardrail_arn = aws_bedrock_guardrail.main.guardrail_arn
  description   = "Version ${var.guardrail_version}"
}
```

---

## AWS Resource Hierarchy

Understanding the AWS resource hierarchy is critical for proper deployment and troubleshooting.

### Resource Relationship Diagram

```
AWS Account
│
├── Region: us-east-1 (Primary)
│   │
│   ├── AWS Bedrock
│   │   ├── Foundation Models (AWS-managed)
│   │   │   ├── anthropic.claude-3-sonnet-20240229-v1:0
│   │   │   ├── anthropic.claude-3-haiku-20240307-v1:0
│   │   │   └── amazon.titan-embed-text-v1
│   │   │
│   │   ├── Application Inference Profiles
│   │   │   ├── production-claude-sonnet
│   │   │   ├── production-claude-haiku
│   │   │   └── production-embeddings
│   │   │
│   │   └── Guardrails
│   │       ├── content-safety-v1
│   │       └── pii-protection-v1
│   │
│   ├── CloudWatch
│   │   ├── Log Groups
│   │   │   └── /aws/bedrock/model-invocations
│   │   ├── Metrics
│   │   │   └── AWS/Bedrock namespace
│   │   ├── Alarms
│   │   │   ├── bedrock-latency-alarm
│   │   │   └── bedrock-error-rate-alarm
│   │   └── Dashboards
│   │       └── bedrock-operations
│   │
│   └── IAM
│       ├── Roles
│       │   ├── bedrock-execution-role
│       │   └── bedrock-monitoring-role
│       └── Policies
│           ├── bedrock-model-access
│           └── bedrock-logging
│
└── Region: us-west-2 (Secondary)
    │
    └── AWS Bedrock
        ├── Cross-Region Inference Profile References
        └── Replicated Guardrails
```

### Resource Naming Convention

The module follows a consistent naming pattern for all created resources:

```
{project_name}-{environment}-{resource_type}-{region_suffix}
```

Example resource names:
- `myapp-prod-bedrock-execution-use1`
- `myapp-prod-guardrail-content-safety-use1`
- `myapp-prod-inference-profile-claude-usw2`

---

## Cross-Region Resource Dependencies

Multi-region deployments require careful orchestration of resource dependencies to ensure proper order of operations and reference integrity.

### Cross-Region Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Primary Region (us-east-1)                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Bedrock Configuration                     │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │   │
│  │  │   Inference    │  │   Guardrails   │  │   Monitoring  │  │   │
│  │  │   Profiles     │  │                │  │               │  │   │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬───────┘  │   │
│  └──────────┼───────────────────┼───────────────────┼──────────┘   │
│             │                   │                   │               │
└─────────────┼───────────────────┼───────────────────┼───────────────┘
              │                   │                   │
              │    Replication    │    Metrics        │
              │    ─────────────▶ │    Aggregation    │
              │                   │    ◀─────────────────
              │                   │                   │
┌─────────────┼───────────────────┼───────────────────┼───────────────┐
│             ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Bedrock Configuration                      │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐   │  │
│  │  │   Inference    │  │   Guardrails   │  │   Monitoring  │   │  │
│  │  │   Profiles     │  │   (Replica)    │  │   (Local)     │   │  │
│  │  └────────────────┘  └────────────────┘  └───────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                      Secondary Region (us-west-2)                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Cross-Region Module Configuration

```hcl
# modules/cross-region/main.tf
locals {
  regions = toset(var.deployment_regions)
}

# Create inference profiles in each region
module "regional_profiles" {
  for_each = local.regions
  source   = "../inference-profiles"
  
  providers = {
    aws = aws.regions[each.key]
  }
  
  project_name      = var.project_name
  inference_profiles = var.inference_profiles
  guardrail_arn     = module.regional_guardrails[each.key].guardrail_arn
  
  depends_on = [module.regional_guardrails]
}

# Replicate guardrails to each region
module "regional_guardrails" {
  for_each = local.regions
  source   = "../guardrails"
  
  providers = {
    aws = aws.regions[each.key]
  }
  
  guardrail_name        = var.guardrail_config.name
  guardrail_description = var.guardrail_config.description
  content_filters       = var.guardrail_config.content_filters
  denied_topics         = var.guardrail_config.denied_topics
  
  tags = merge(var.common_tags, {
    Region = each.key
  })
}
```

### Dependency Management

Cross-region deployments must handle asynchronous resource creation:

```hcl
# Handle cross-region dependency ordering
resource "time_sleep" "wait_for_primary" {
  depends_on = [module.primary_region]
  
  create_duration = "30s"
}

module "secondary_region" {
  source = "./modules/cross-region"
  
  depends_on = [time_sleep.wait_for_primary]
  
  primary_inference_profile_arns = module.primary_region.inference_profile_arns
  primary_guardrail_arn          = module.primary_region.guardrail_arn
  
  # Additional configuration
}
```

---

## State Management

Proper Terraform state management is essential for multi-region deployments and team collaboration.

### Recommended Backend Configuration

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "bedrock/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-locks"
    
    # Enable state file versioning
    versioning = true
  }
}
```

### State File Structure

For large deployments, consider separating state by environment and region:

```
s3://company-terraform-state/
├── bedrock/
│   ├── production/
│   │   ├── us-east-1/terraform.tfstate
│   │   └── us-west-2/terraform.tfstate
│   ├── staging/
│   │   ├── us-east-1/terraform.tfstate
│   │   └── us-west-2/terraform.tfstate
│   └── development/
│       └── us-east-1/terraform.tfstate
```

### Remote State Data Sources

Access outputs from other state files:

```hcl
# Access primary region outputs from secondary region deployment
data "terraform_remote_state" "primary" {
  backend = "s3"
  
  config = {
    bucket = "company-terraform-state"
    key    = "bedrock/production/us-east-1/terraform.tfstate"
    region = "us-east-1"
  }
}

# Reference primary region resources
locals {
  primary_guardrail_arn = data.terraform_remote_state.primary.outputs.guardrail_arn
  primary_profile_arns  = data.terraform_remote_state.primary.outputs.inference_profile_arns
}
```

### State Locking

DynamoDB-based state locking prevents concurrent modifications:

```hcl
# Create the DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
  
  tags = {
    Purpose = "Terraform state locking"
  }
}
```

---

## Architecture Diagrams

### Complete System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud Infrastructure                              │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        VPC (Optional - for VPC Endpoints)                │   │
│  │                                                                          │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │   │
│  │   │  Private     │    │  Private     │    │  Private     │             │   │
│  │   │  Subnet AZ-A │    │  Subnet AZ-B │    │  Subnet AZ-C │             │   │
│  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘             │   │
│  │          │                   │                   │                      │   │
│  │          └───────────────────┼───────────────────┘                      │   │
│  │                              │                                          │   │
│  │                    ┌─────────▼─────────┐                               │   │
│  │                    │  VPC Endpoint     │                               │   │
│  │                    │  (bedrock-runtime)│                               │   │
│  │                    └─────────┬─────────┘                               │   │
│  └──────────────────────────────┼──────────────────────────────────────────┘   │
│                                 │                                               │
│  ┌──────────────────────────────┼──────────────────────────────────────────┐   │
│  │                              ▼                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │                      AWS Bedrock Service                         │    │   │
│  │  │                                                                  │    │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │    │   │
│  │  │  │   Foundation    │  │   Application   │  │   Guardrails    │  │    │   │
│  │  │  │     Models      │  │   Inference     │  │                 │  │    │   │
│  │  │  │                 │  │    Profiles     │  │  ┌───────────┐  │  │    │   │
│  │  │  │  • Claude 3     │  │                 │  │  │ Content   │  │  │    │   │
│  │  │  │  • Claude 3.5   │  │  • prod-claude  │  │  │ Filters   │  │  │    │   │
│  │  │  │  • Titan        │  │  • prod-embed   │  │  └───────────┘  │  │    │   │
│  │  │  │  • Cohere       │  │  • dev-claude   │  │  ┌───────────┐  │  │    │   │
│  │  │  │                 │  │                 │  │  │ Topic     │  │  │    │   │
│  │  │  └─────────────────┘  └─────────────────┘  │  │ Policies  │  │  │    │   │
│  │  │                                            │  └───────────┘  │  │    │   │
│  │  │                                            │  ┌───────────┐  │  │    │   │
│  │  │                                            │  │ PII       │  │  │    │   │
│  │  │                                            │  │ Detection │  │  │    │   │
│  │  │                                            │  └───────────┘  │  │    │   │
│  │  │                                            └─────────────────┘  │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                          │   │
│  │                           AWS Bedrock Region                             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         Monitoring & Observability                        │   │
│  │                                                                           │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │   │
│  │  │   CloudWatch   │  │   CloudWatch   │  │      CloudWatch            │  │   │
│  │  │   Log Groups   │  │    Alarms      │  │      Dashboards            │  │   │
│  │  │                │  │                │  │                            │  │   │
│  │  │ • Invocations  │  │ • Latency      │  │ • Model Usage              │  │   │
│  │  │ • Guardrail    │  │ • Error Rate   │  │ • Guardrail Triggers       │  │   │
│  │  │   Violations   │  │ • Throttling   │  │ • Cost Analysis            │  │   │
│  │  └────────────────┘  └────────────────┘  └────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌──────────────────┐
│   Application    │
│     Client       │
└────────┬─────────┘
         │
         │ 1. API Request
         ▼
┌────────────────────────────────────────────────────────────────────┐
│                        AWS API Gateway                              │
│                    (Optional - for REST API)                        │
└────────┬───────────────────────────────────────────────────────────┘
         │
         │ 2. Invoke Model
         ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Application Inference Profile                    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Request Processing                        │   │
│  │                                                              │   │
│  │  3. ┌──────────────┐    4. ┌──────────────┐                 │   │
│  │     │   IAM Auth   │ ──▶   │  Guardrail   │                 │   │
│  │     │   Check      │       │  Evaluation  │                 │   │
│  │     └──────────────┘       └──────┬───────┘                 │   │
│  │                                   │                          │   │
│  │           ┌───────────────────────┼────────────────────┐    │   │
│  │           │                       │                    │    │   │
│  │           ▼                       ▼                    ▼    │   │
│  │     ┌──────────┐           ┌──────────┐          ┌──────────┐  │
│  │     │  PASS    │           │  BLOCK   │          │  MODIFY  │  │
│  │     └────┬─────┘           └────┬─────┘          └────┬─────┘  │
│  │          │                      │                     │     │   │
│  │          │                      │                     │     │   │
│  └──────────┼──────────────────────┼─────────────────────┼─────┘   │
│             │                      │                     │         │
└─────────────┼──────────────────────┼─────────────────────┼─────────┘
              │                      │                     │
              │ 5. Model             │ Return Error        │ 6. Modified
              │    Invocation        │                     │    Request
              ▼                      ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Foundation Model (Claude)                       │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Model Inference                             │  │
│  │                                                                │  │
│  │   7. Process Prompt → Generate Response → Stream Output       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────────────────────────┘
         │
         │ 8. Response
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Output Guardrail Evaluation                       │
│                                                                      │
│   9. Content Filter → PII Detection → Word Filter → Topic Check     │
└────────┬────────────────────────────────────────────────────────────┘
         │
         │ 10. Final Response
         ▼
┌──────────────────┐      ┌──────────────────────────────────────────┐
│   Application    │      │              CloudWatch                   │
│     Client       │      │   11. Metrics, Logs, Traces              │
└──────────────────┘      └──────────────────────────────────────────┘
```

---

## Best Practices and Recommendations

### Module Versioning

Always pin module versions in production deployments:

```hcl
module "bedrock" {
  source  = "github.com/your-org/aws-terraform-bedrock?ref=v2.1.0"
  
  # Configuration
}
```

### Environment Isolation

Use workspaces or separate state files for environment isolation:

```bash
# Using workspaces
terraform workspace new production
terraform workspace new staging

# Apply to specific environment
terraform workspace select production
terraform apply -var-file="environments/production.tfvars"
```

### Security Considerations

1. **Least Privilege IAM**: Configure IAM policies with minimal required permissions
2. **Encryption**: Enable encryption at rest for all log groups
3. **VPC Endpoints**: Use VPC endpoints for private connectivity to Bedrock
4. **Guardrails**: Implement comprehensive guardrails for all production workloads

---

## Conclusion

This architecture overview provides the foundational understanding needed to deploy, maintain, and troubleshoot the aws-terraform-bedrock module. The modular design enables flexible deployments while maintaining consistency and security across multiple AWS regions. For specific implementation details, refer to the individual submodule documentation and example configurations.