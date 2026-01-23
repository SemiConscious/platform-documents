# Inference Profiles Configuration

## Overview

Inference profiles in the AWS Terraform Bedrock module provide a powerful abstraction layer for managing access to foundation models across multiple AWS regions. They enable organizations to create consistent, named endpoints for AI model inference while supporting sophisticated deployment patterns such as cross-region failover, load distribution, and model versioning.

This documentation covers the complete configuration of application inference profiles, including Claude Copilot profiles, CAI (Conversational AI) profiles, and embedding model profiles. Understanding these configurations is essential for operators deploying enterprise-grade GenAI solutions with AWS Bedrock.

### What Are Inference Profiles?

An inference profile is a logical resource that acts as a pointer to one or more foundation models. Rather than invoking models directly by their ARN, applications reference inference profiles, which provides several benefits:

- **Abstraction**: Applications don't need to know the underlying model ARN or region
- **Flexibility**: Model versions can be updated without changing application code
- **Resilience**: Cross-region inference enables automatic failover
- **Governance**: Centralized control over which models applications can access
- **Cost Management**: Traffic can be routed based on capacity and pricing

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Application Inference Profile** | A named resource that maps to a specific foundation model configuration |
| **Cross-Region Inference** | Capability to route inference requests across multiple AWS regions |
| **Model ARN** | The Amazon Resource Name uniquely identifying a Bedrock foundation model |
| **Inference Profile ARN** | The ARN of the inference profile resource itself |

---

## Application Inference Profiles

Application inference profiles are the primary mechanism for exposing Bedrock models to your applications. Each profile encapsulates model selection, region configuration, and access policies.

### Basic Profile Structure

```hcl
# terraform/inference_profiles.tf

resource "aws_bedrock_inference_profile" "application_profile" {
  inference_profile_name = "my-application-profile"
  description            = "Primary inference profile for production workloads"
  
  model_source {
    copy_from = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
  }

  tags = {
    Environment = "production"
    Application = "my-genai-app"
    CostCenter  = "ai-platform"
  }
}
```

### Multi-Model Profile Configuration

For organizations using multiple models, define profiles in a structured manner:

```hcl
# terraform/variables.tf

variable "inference_profiles" {
  description = "Map of inference profile configurations"
  type = map(object({
    name        = string
    description = string
    model_id    = string
    region      = string
    tags        = map(string)
  }))
  
  default = {
    primary_claude = {
      name        = "claude-primary"
      description = "Primary Claude model for general inference"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      region      = "us-east-1"
      tags        = { tier = "primary" }
    }
    secondary_claude = {
      name        = "claude-secondary"
      description = "Secondary Claude model for failover"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      region      = "us-west-2"
      tags        = { tier = "secondary" }
    }
  }
}
```

```hcl
# terraform/main.tf

resource "aws_bedrock_inference_profile" "profiles" {
  for_each = var.inference_profiles

  inference_profile_name = each.value.name
  description            = each.value.description

  model_source {
    copy_from = "arn:aws:bedrock:${each.value.region}::foundation-model/${each.value.model_id}"
  }

  tags = merge(
    var.common_tags,
    each.value.tags,
    {
      ProfileKey = each.key
    }
  )
}
```

---

## Cross-Region Inference Architecture

Cross-region inference is a critical capability for enterprise deployments, providing resilience against regional outages and enabling global scalability.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│                                                                  │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│    │   App A      │    │   App B      │    │   App C      │    │
│    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    │
│           │                   │                   │             │
└───────────┼───────────────────┼───────────────────┼─────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Inference Profile Layer                         │
│                                                                  │
│    ┌──────────────────────────────────────────────────────┐    │
│    │           Cross-Region Inference Profile              │    │
│    │                                                       │    │
│    │   Primary: us-east-1    │    Failover: us-west-2    │    │
│    └──────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│    AWS Bedrock        │       │    AWS Bedrock        │
│    us-east-1          │       │    us-west-2          │
│                       │       │                       │
│  ┌─────────────────┐  │       │  ┌─────────────────┐  │
│  │ Claude 3 Sonnet │  │       │  │ Claude 3 Sonnet │  │
│  └─────────────────┘  │       │  └─────────────────┘  │
└───────────────────────┘       └───────────────────────┘
```

### Configuring Cross-Region Inference

```hcl
# terraform/cross_region.tf

locals {
  supported_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]
  
  cross_region_models = {
    claude_sonnet = {
      model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
      regions  = ["us-east-1", "us-west-2"]
    }
    claude_haiku = {
      model_id = "anthropic.claude-3-haiku-20240307-v1:0"
      regions  = ["us-east-1", "us-west-2", "eu-west-1"]
    }
  }
}

# Primary region provider
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

# Secondary region provider
provider "aws" {
  alias  = "secondary"
  region = "us-west-2"
}

# Cross-region inference profile with automatic failover
resource "aws_bedrock_inference_profile" "cross_region_claude" {
  provider = aws.primary
  
  inference_profile_name = "claude-cross-region-production"
  description            = "Cross-region Claude profile with automatic failover"

  model_source {
    copy_from = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
  }

  tags = {
    CrossRegion     = "true"
    PrimaryRegion   = "us-east-1"
    FailoverRegion  = "us-west-2"
    Environment     = "production"
  }
}

# Regional profile for secondary region
resource "aws_bedrock_inference_profile" "regional_claude_secondary" {
  provider = aws.secondary
  
  inference_profile_name = "claude-regional-secondary"
  description            = "Regional Claude profile for us-west-2"

  model_source {
    copy_from = "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
  }

  tags = {
    CrossRegion = "false"
    Region      = "us-west-2"
    Environment = "production"
  }
}
```

### Cross-Region Routing Logic

Implement intelligent routing in your application layer:

```python
# Example Python application code for cross-region inference
import boto3
from botocore.exceptions import ClientError
import logging

class CrossRegionInferenceClient:
    def __init__(self, primary_region: str, failover_regions: list):
        self.primary_region = primary_region
        self.failover_regions = failover_regions
        self.clients = self._initialize_clients()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_clients(self):
        clients = {}
        all_regions = [self.primary_region] + self.failover_regions
        for region in all_regions:
            clients[region] = boto3.client('bedrock-runtime', region_name=region)
        return clients
    
    def invoke_model(self, inference_profile_arn: str, body: dict):
        regions_to_try = [self.primary_region] + self.failover_regions
        
        for region in regions_to_try:
            try:
                response = self.clients[region].invoke_model(
                    modelId=inference_profile_arn,
                    body=json.dumps(body)
                )
                return response
            except ClientError as e:
                self.logger.warning(f"Failed in {region}: {e}")
                continue
        
        raise Exception("All regions failed")
```

---

## Claude Copilot Profiles

Claude Copilot profiles are specialized inference profiles optimized for code generation, code review, and developer assistance use cases.

### Profile Configuration

```hcl
# terraform/claude_copilot_profiles.tf

variable "claude_copilot_config" {
  description = "Configuration for Claude Copilot inference profiles"
  type = object({
    enabled           = bool
    model_version     = string
    regions           = list(string)
    max_tokens        = number
    temperature       = number
  })
  
  default = {
    enabled           = true
    model_version     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    regions           = ["us-east-1", "us-west-2"]
    max_tokens        = 8192
    temperature       = 0.3
  }
}

resource "aws_bedrock_inference_profile" "claude_copilot" {
  count = var.claude_copilot_config.enabled ? 1 : 0

  inference_profile_name = "claude-copilot-production"
  description            = "Claude Copilot profile for code assistance"

  model_source {
    copy_from = "arn:aws:bedrock:${var.claude_copilot_config.regions[0]}::foundation-model/${var.claude_copilot_config.model_version}"
  }

  tags = {
    UseCase      = "copilot"
    ModelFamily  = "claude"
    MaxTokens    = tostring(var.claude_copilot_config.max_tokens)
    Temperature  = tostring(var.claude_copilot_config.temperature)
    Environment  = var.environment
  }
}

# Copilot profile for code review tasks
resource "aws_bedrock_inference_profile" "claude_copilot_review" {
  count = var.claude_copilot_config.enabled ? 1 : 0

  inference_profile_name = "claude-copilot-code-review"
  description            = "Claude Copilot profile optimized for code review"

  model_source {
    copy_from = "arn:aws:bedrock:${var.claude_copilot_config.regions[0]}::foundation-model/${var.claude_copilot_config.model_version}"
  }

  tags = {
    UseCase      = "code-review"
    ModelFamily  = "claude"
    Environment  = var.environment
  }
}

# Copilot profile for documentation generation
resource "aws_bedrock_inference_profile" "claude_copilot_docs" {
  count = var.claude_copilot_config.enabled ? 1 : 0

  inference_profile_name = "claude-copilot-documentation"
  description            = "Claude Copilot profile for documentation generation"

  model_source {
    copy_from = "arn:aws:bedrock:${var.claude_copilot_config.regions[0]}::foundation-model/${var.claude_copilot_config.model_version}"
  }

  tags = {
    UseCase      = "documentation"
    ModelFamily  = "claude"
    Environment  = var.environment
  }
}
```

### Recommended Claude Models for Copilot Use Cases

| Use Case | Recommended Model | Rationale |
|----------|-------------------|-----------|
| Code Generation | Claude 3.5 Sonnet | Best balance of speed and code quality |
| Code Review | Claude 3.5 Sonnet | Strong reasoning for identifying issues |
| Documentation | Claude 3 Opus | Highest quality for detailed documentation |
| Quick Completions | Claude 3 Haiku | Fastest response for autocomplete |

---

## CAI Profiles

Conversational AI (CAI) profiles are designed for chatbot, virtual assistant, and conversational interface applications.

### CAI Profile Configuration

```hcl
# terraform/cai_profiles.tf

variable "cai_profile_config" {
  description = "Configuration for Conversational AI inference profiles"
  type = map(object({
    name              = string
    description       = string
    model_id          = string
    primary_region    = string
    enable_guardrails = bool
    use_case          = string
  }))
  
  default = {
    customer_support = {
      name              = "cai-customer-support"
      description       = "CAI profile for customer support chatbots"
      model_id          = "anthropic.claude-3-sonnet-20240229-v1:0"
      primary_region    = "us-east-1"
      enable_guardrails = true
      use_case          = "customer-support"
    }
    internal_assistant = {
      name              = "cai-internal-assistant"
      description       = "CAI profile for internal employee assistance"
      model_id          = "anthropic.claude-3-haiku-20240307-v1:0"
      primary_region    = "us-east-1"
      enable_guardrails = true
      use_case          = "internal-assistant"
    }
    sales_copilot = {
      name              = "cai-sales-copilot"
      description       = "CAI profile for sales team assistance"
      model_id          = "anthropic.claude-3-sonnet-20240229-v1:0"
      primary_region    = "us-west-2"
      enable_guardrails = true
      use_case          = "sales"
    }
  }
}

resource "aws_bedrock_inference_profile" "cai_profiles" {
  for_each = var.cai_profile_config

  inference_profile_name = each.value.name
  description            = each.value.description

  model_source {
    copy_from = "arn:aws:bedrock:${each.value.primary_region}::foundation-model/${each.value.model_id}"
  }

  tags = {
    ProfileType       = "cai"
    UseCase           = each.value.use_case
    GuardrailsEnabled = tostring(each.value.enable_guardrails)
    Environment       = var.environment
    CostCenter        = "conversational-ai"
  }
}

# Output CAI profile ARNs for application consumption
output "cai_profile_arns" {
  description = "Map of CAI profile names to their ARNs"
  value = {
    for key, profile in aws_bedrock_inference_profile.cai_profiles :
    key => profile.inference_profile_arn
  }
}
```

### CAI Profile Best Practices

1. **Guardrails Integration**: Always enable guardrails for customer-facing CAI profiles
2. **Model Selection**: Use Haiku for high-volume, low-latency scenarios; Sonnet for complex conversations
3. **Regional Placement**: Deploy profiles close to your user base for lower latency
4. **Monitoring**: Enable detailed CloudWatch metrics for conversation quality tracking

---

## CAI Embedding Profiles

Embedding profiles are specialized for vector embedding generation, essential for RAG (Retrieval-Augmented Generation) architectures.

### Embedding Profile Configuration

```hcl
# terraform/embedding_profiles.tf

variable "embedding_config" {
  description = "Configuration for embedding model inference profiles"
  type = object({
    titan_embeddings = object({
      enabled    = bool
      model_id   = string
      dimensions = number
    })
    cohere_embeddings = object({
      enabled    = bool
      model_id   = string
      dimensions = number
    })
  })
  
  default = {
    titan_embeddings = {
      enabled    = true
      model_id   = "amazon.titan-embed-text-v2:0"
      dimensions = 1024
    }
    cohere_embeddings = {
      enabled    = false
      model_id   = "cohere.embed-english-v3"
      dimensions = 1024
    }
  }
}

# Titan Embedding Profile
resource "aws_bedrock_inference_profile" "titan_embeddings" {
  count = var.embedding_config.titan_embeddings.enabled ? 1 : 0

  inference_profile_name = "titan-embeddings-production"
  description            = "Titan embedding model for vector generation"

  model_source {
    copy_from = "arn:aws:bedrock:us-east-1::foundation-model/${var.embedding_config.titan_embeddings.model_id}"
  }

  tags = {
    ProfileType  = "embedding"
    ModelFamily  = "titan"
    Dimensions   = tostring(var.embedding_config.titan_embeddings.dimensions)
    Environment  = var.environment
  }
}

# Cohere Embedding Profile (optional)
resource "aws_bedrock_inference_profile" "cohere_embeddings" {
  count = var.embedding_config.cohere_embeddings.enabled ? 1 : 0

  inference_profile_name = "cohere-embeddings-production"
  description            = "Cohere embedding model for multilingual vector generation"

  model_source {
    copy_from = "arn:aws:bedrock:us-east-1::foundation-model/${var.embedding_config.cohere_embeddings.model_id}"
  }

  tags = {
    ProfileType  = "embedding"
    ModelFamily  = "cohere"
    Dimensions   = tostring(var.embedding_config.cohere_embeddings.dimensions)
    Environment  = var.environment
  }
}

# Dedicated embedding profile for document processing
resource "aws_bedrock_inference_profile" "document_embeddings" {
  inference_profile_name = "document-embeddings-batch"
  description            = "Embedding profile optimized for batch document processing"

  model_source {
    copy_from = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
  }

  tags = {
    ProfileType  = "embedding"
    UseCase      = "document-processing"
    BatchEnabled = "true"
    Environment  = var.environment
  }
}
```

### Embedding Model Comparison

| Model | Dimensions | Languages | Use Case |
|-------|------------|-----------|----------|
| Titan Embed v2 | 256-1024 | 25+ | General purpose, cost-effective |
| Cohere Embed v3 | 1024 | 100+ | Multilingual, high accuracy |
| Cohere Embed English | 1024 | English | English-only, optimized |

---

## Adding New Inference Profiles

When adding new inference profiles to your deployment, follow this structured approach:

### Step 1: Define Profile Variables

```hcl
# terraform/variables.tf

variable "new_profile_config" {
  description = "Configuration for the new inference profile"
  type = object({
    name           = string
    description    = string
    model_id       = string
    primary_region = string
    tags           = map(string)
  })
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.new_profile_config.name))
    error_message = "Profile name must contain only lowercase letters, numbers, and hyphens."
  }
  
  validation {
    condition     = contains(["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"], var.new_profile_config.primary_region)
    error_message = "Primary region must be a supported Bedrock region."
  }
}
```

### Step 2: Create the Resource

```hcl
# terraform/new_profile.tf

resource "aws_bedrock_inference_profile" "new_profile" {
  inference_profile_name = var.new_profile_config.name
  description            = var.new_profile_config.description

  model_source {
    copy_from = "arn:aws:bedrock:${var.new_profile_config.primary_region}::foundation-model/${var.new_profile_config.model_id}"
  }

  tags = merge(
    var.common_tags,
    var.new_profile_config.tags,
    {
      CreatedBy   = "terraform"
      CreatedDate = timestamp()
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}
```

### Step 3: Export Outputs

```hcl
# terraform/outputs.tf

output "new_profile_arn" {
  description = "ARN of the newly created inference profile"
  value       = aws_bedrock_inference_profile.new_profile.inference_profile_arn
}

output "new_profile_id" {
  description = "ID of the newly created inference profile"
  value       = aws_bedrock_inference_profile.new_profile.inference_profile_id
}
```

### Step 4: Validate and Apply

```bash
# Validate the configuration
terraform validate

# Plan the changes
terraform plan -var-file="environments/production.tfvars"

# Apply with approval
terraform apply -var-file="environments/production.tfvars"
```

---

## Profile Naming Conventions

Consistent naming conventions are essential for managing inference profiles at scale.

### Standard Naming Pattern

```
{model-family}-{use-case}-{environment}[-{region}]
```

### Examples

| Profile Name | Components |
|--------------|------------|
| `claude-copilot-production` | Claude model, copilot use case, production environment |
| `titan-embeddings-staging-usw2` | Titan model, embeddings use case, staging, us-west-2 |
| `cai-customer-support-prod` | CAI profile, customer support, production |

### Naming Rules

```hcl
# terraform/locals.tf

locals {
  # Standardized naming function
  profile_name = join("-", compact([
    var.model_family,    # e.g., "claude", "titan", "cohere"
    var.use_case,        # e.g., "copilot", "embeddings", "cai"
    var.environment,     # e.g., "production", "staging", "dev"
    var.include_region ? var.region_short : null  # e.g., "use1", "usw2"
  ]))
  
  # Region short codes
  region_short_codes = {
    "us-east-1"      = "use1"
    "us-west-2"      = "usw2"
    "eu-west-1"      = "euw1"
    "ap-northeast-1" = "apne1"
  }
}
```

---

## Outputs Reference

The module provides comprehensive outputs for integration with applications and downstream infrastructure.

### Complete Outputs Configuration

```hcl
# terraform/outputs.tf

# Claude Copilot Outputs
output "claude_copilot_profile_arn" {
  description = "ARN of the Claude Copilot inference profile"
  value       = try(aws_bedrock_inference_profile.claude_copilot[0].inference_profile_arn, null)
}

output "claude_copilot_profile_id" {
  description = "ID of the Claude Copilot inference profile"
  value       = try(aws_bedrock_inference_profile.claude_copilot[0].inference_profile_id, null)
}

# CAI Profile Outputs
output "cai_profiles" {
  description = "Map of all CAI inference profiles"
  value = {
    for key, profile in aws_bedrock_inference_profile.cai_profiles : key => {
      arn         = profile.inference_profile_arn
      id          = profile.inference_profile_id
      name        = profile.inference_profile_name
      description = profile.description
    }
  }
}

# Embedding Profile Outputs
output "embedding_profiles" {
  description = "Map of embedding inference profiles"
  value = {
    titan = try({
      arn  = aws_bedrock_inference_profile.titan_embeddings[0].inference_profile_arn
      id   = aws_bedrock_inference_profile.titan_embeddings[0].inference_profile_id
      name = aws_bedrock_inference_profile.titan_embeddings[0].inference_profile_name
    }, null)
    cohere = try({
      arn  = aws_bedrock_inference_profile.cohere_embeddings[0].inference_profile_arn
      id   = aws_bedrock_inference_profile.cohere_embeddings[0].inference_profile_id
      name = aws_bedrock_inference_profile.cohere_embeddings[0].inference_profile_name
    }, null)
  }
}

# Cross-Region Profile Outputs
output "cross_region_profiles" {
  description = "Cross-region inference profile configurations"
  value = {
    primary = {
      arn    = aws_bedrock_inference_profile.cross_region_claude.inference_profile_arn
      region = "us-east-1"
    }
    secondary = {
      arn    = aws_bedrock_inference_profile.regional_claude_secondary.inference_profile_arn
      region = "us-west-2"
    }
  }
}

# Consolidated Output for Application Configuration
output "inference_profile_config" {
  description = "Complete inference profile configuration for application consumption"
  value = {
    copilot = {
      primary_arn = try(aws_bedrock_inference_profile.claude_copilot[0].inference_profile_arn, null)
    }
    cai = {
      for key, profile in aws_bedrock_inference_profile.cai_profiles :
      key => profile.inference_profile_arn
    }
    embeddings = {
      titan  = try(aws_bedrock_inference_profile.titan_embeddings[0].inference_profile_arn, null)
      cohere = try(aws_bedrock_inference_profile.cohere_embeddings[0].inference_profile_arn, null)
    }
  }
  sensitive = false
}
```

### Using Outputs in Applications

```yaml
# Example: Exporting outputs to SSM Parameter Store
resource "aws_ssm_parameter" "inference_profile_config" {
  name  = "/${var.environment}/bedrock/inference-profiles"
  type  = "String"
  value = jsonencode(output.inference_profile_config)
  
  tags = var.common_tags
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Profile creation fails | Model not available in region | Verify model availability in target region |
| Cross-region routing fails | IAM permissions | Ensure cross-region invoke permissions |
| Embedding dimension mismatch | Wrong model version | Verify model supports required dimensions |

### Validation Commands

```bash
# List all inference profiles
aws bedrock list-inference-profiles --region us-east-1

# Describe specific profile
aws bedrock get-inference-profile \
  --inference-profile-identifier "claude-copilot-production" \
  --region us-east-1

# Test inference profile
aws bedrock-runtime invoke-model \
  --model-id "arn:aws:bedrock:us-east-1:123456789012:inference-profile/claude-copilot-production" \
  --body '{"prompt": "Hello"}' \
  --region us-east-1 \
  output.json
```