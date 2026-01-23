# Variables Reference

This document provides a complete reference for all Terraform variables and outputs used in the `aws-terraform-bedrock` module. The module enables multi-region AWS Bedrock deployment with application inference profiles, cross-region inference support, guardrails configuration, and CloudWatch monitoring.

## Overview

The `aws-terraform-bedrock` module is organized into a root module and several submodules, each with their own set of variables and outputs. Understanding these variables is essential for properly configuring your AWS Bedrock infrastructure across multiple regions.

### Module Structure

```
aws-terraform-bedrock/
├── main.tf
├── variables.tf
├── outputs.tf
└── modules/
    ├── application-inference/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── guardrails/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## Root Module Variables

The root module serves as the entry point for deploying AWS Bedrock resources. These variables control the overall behavior of the deployment.

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `project_name` | `string` | The name of the project. Used for resource naming and tagging. |
| `environment` | `string` | The deployment environment (e.g., `dev`, `staging`, `prod`). |
| `primary_region` | `string` | The primary AWS region for Bedrock deployment. |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `secondary_regions` | `list(string)` | `[]` | List of secondary AWS regions for cross-region inference support. |
| `enable_cross_region_inference` | `bool` | `false` | Enable cross-region inference capabilities for high availability. |
| `enable_guardrails` | `bool` | `true` | Enable AI safety guardrails for Bedrock models. |
| `enable_monitoring` | `bool` | `true` | Enable CloudWatch monitoring for Bedrock models. |
| `model_configurations` | `map(object)` | `{}` | Configuration map for supported models (Claude, CAI, embeddings). |
| `tags` | `map(string)` | `{}` | Additional tags to apply to all resources. |
| `log_retention_days` | `number` | `30` | Number of days to retain CloudWatch logs. |
| `kms_key_arn` | `string` | `null` | ARN of KMS key for encryption. If null, AWS managed key is used. |

### Variable Definitions

```hcl
# variables.tf - Root Module

variable "project_name" {
  description = "The name of the project used for resource naming and tagging"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "The deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "primary_region" {
  description = "The primary AWS region for Bedrock deployment"
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.primary_region))
    error_message = "Primary region must be a valid AWS region format."
  }
}

variable "secondary_regions" {
  description = "List of secondary AWS regions for cross-region inference"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for region in var.secondary_regions : can(regex("^[a-z]{2}-[a-z]+-[0-9]$", region))
    ])
    error_message = "All secondary regions must be valid AWS region formats."
  }
}

variable "enable_cross_region_inference" {
  description = "Enable cross-region inference capabilities"
  type        = bool
  default     = false
}

variable "enable_guardrails" {
  description = "Enable AI safety guardrails for Bedrock models"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring for Bedrock models"
  type        = bool
  default     = true
}

variable "model_configurations" {
  description = "Configuration map for supported Bedrock models"
  type = map(object({
    model_id            = string
    inference_units     = optional(number, 1)
    max_tokens          = optional(number, 4096)
    temperature         = optional(number, 0.7)
    enabled             = optional(bool, true)
    throughput_mode     = optional(string, "on_demand")
    commitment_duration = optional(string, null)
  }))
  default = {}
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

variable "kms_key_arn" {
  description = "ARN of KMS key for encryption. If null, AWS managed key is used"
  type        = string
  default     = null
}
```

---

## Root Module Outputs

The root module exposes outputs that can be used by other Terraform configurations or for reference.

| Output | Type | Description |
|--------|------|-------------|
| `bedrock_endpoint_urls` | `map(string)` | Map of region to Bedrock endpoint URLs. |
| `inference_profile_arns` | `map(string)` | ARNs of created application inference profiles. |
| `guardrail_ids` | `map(string)` | IDs of created guardrails by region. |
| `monitoring_dashboard_url` | `string` | URL to the CloudWatch monitoring dashboard. |
| `cross_region_inference_enabled` | `bool` | Whether cross-region inference is enabled. |
| `configured_models` | `list(string)` | List of configured model IDs. |
| `kms_key_arn` | `string` | ARN of the KMS key used for encryption. |

### Output Definitions

```hcl
# outputs.tf - Root Module

output "bedrock_endpoint_urls" {
  description = "Map of region to Bedrock endpoint URLs"
  value = merge(
    { (var.primary_region) = "https://bedrock-runtime.${var.primary_region}.amazonaws.com" },
    { for region in var.secondary_regions : region => "https://bedrock-runtime.${region}.amazonaws.com" }
  )
}

output "inference_profile_arns" {
  description = "ARNs of created application inference profiles"
  value       = module.application_inference.profile_arns
}

output "guardrail_ids" {
  description = "IDs of created guardrails by region"
  value       = var.enable_guardrails ? module.guardrails[0].guardrail_ids : {}
}

output "monitoring_dashboard_url" {
  description = "URL to the CloudWatch monitoring dashboard"
  value       = var.enable_monitoring ? "https://${var.primary_region}.console.aws.amazon.com/cloudwatch/home?region=${var.primary_region}#dashboards:name=${var.project_name}-${var.environment}-bedrock" : null
}

output "cross_region_inference_enabled" {
  description = "Whether cross-region inference is enabled"
  value       = var.enable_cross_region_inference
}

output "configured_models" {
  description = "List of configured model IDs"
  value       = [for k, v in var.model_configurations : v.model_id if v.enabled]
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = var.kms_key_arn
}
```

---

## Application Inference Submodule Variables

The application inference submodule manages inference profiles for global model access across regions.

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `project_name` | `string` | The name of the project (inherited from root). |
| `environment` | `string` | The deployment environment (inherited from root). |
| `regions` | `list(string)` | List of regions where inference profiles will be created. |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `inference_profiles` | `list(object)` | `[]` | List of inference profile configurations. |
| `default_model_id` | `string` | `"anthropic.claude-3-sonnet-20240229-v1:0"` | Default model ID for profiles. |
| `enable_model_invocation_logging` | `bool` | `true` | Enable logging for model invocations. |
| `s3_logging_bucket` | `string` | `null` | S3 bucket for invocation logs. |
| `cloudwatch_log_group_arn` | `string` | `null` | CloudWatch log group ARN for invocation logs. |
| `tags` | `map(string)` | `{}` | Tags to apply to inference profile resources. |

### Variable Definitions

```hcl
# modules/application-inference/variables.tf

variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The deployment environment"
  type        = string
}

variable "regions" {
  description = "List of regions for inference profile creation"
  type        = list(string)
}

variable "inference_profiles" {
  description = "List of inference profile configurations"
  type = list(object({
    name                = string
    model_id            = string
    description         = optional(string, "")
    inference_units     = optional(number, 1)
    max_tokens          = optional(number, 4096)
    temperature         = optional(number, 0.7)
    top_p               = optional(number, 0.9)
    top_k               = optional(number, 250)
    stop_sequences      = optional(list(string), [])
    throughput_mode     = optional(string, "on_demand")
    commitment_duration = optional(string, null)
  }))
  default = []

  validation {
    condition = alltrue([
      for profile in var.inference_profiles :
      contains(["on_demand", "provisioned"], profile.throughput_mode)
    ])
    error_message = "Throughput mode must be either 'on_demand' or 'provisioned'."
  }
}

variable "default_model_id" {
  description = "Default model ID for inference profiles"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "enable_model_invocation_logging" {
  description = "Enable logging for model invocations"
  type        = bool
  default     = true
}

variable "s3_logging_bucket" {
  description = "S3 bucket for invocation logs"
  type        = string
  default     = null
}

variable "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN for invocation logs"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to inference profile resources"
  type        = map(string)
  default     = {}
}
```

---

## Application Inference Submodule Outputs

| Output | Type | Description |
|--------|------|-------------|
| `profile_arns` | `map(string)` | Map of profile name to ARN. |
| `profile_ids` | `map(string)` | Map of profile name to ID. |
| `profile_endpoints` | `map(string)` | Map of profile name to endpoint URL. |
| `logging_configuration` | `object` | Logging configuration details. |

### Output Definitions

```hcl
# modules/application-inference/outputs.tf

output "profile_arns" {
  description = "Map of profile name to ARN"
  value = {
    for k, v in aws_bedrockagent_agent.inference_profiles : k => v.agent_arn
  }
}

output "profile_ids" {
  description = "Map of profile name to ID"
  value = {
    for k, v in aws_bedrockagent_agent.inference_profiles : k => v.agent_id
  }
}

output "profile_endpoints" {
  description = "Map of profile name to endpoint URL"
  value = {
    for k, v in aws_bedrockagent_agent.inference_profiles :
    k => "https://bedrock-agent-runtime.${var.regions[0]}.amazonaws.com/agents/${v.agent_id}"
  }
}

output "logging_configuration" {
  description = "Logging configuration details"
  value = {
    enabled            = var.enable_model_invocation_logging
    s3_bucket          = var.s3_logging_bucket
    cloudwatch_log_group = var.cloudwatch_log_group_arn
  }
}
```

---

## Guardrails Submodule Variables

The guardrails submodule configures AI safety measures for Bedrock models.

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `project_name` | `string` | The name of the project. |
| `environment` | `string` | The deployment environment. |
| `guardrail_name` | `string` | Name for the guardrail resource. |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `blocked_input_messaging` | `string` | `"I cannot process this request due to content policy restrictions."` | Message displayed when input is blocked. |
| `blocked_output_messaging` | `string` | `"I cannot provide this response due to content policy restrictions."` | Message displayed when output is blocked. |
| `content_policy_config` | `object` | See below | Configuration for content filtering policies. |
| `word_policy_config` | `object` | `null` | Configuration for word-based filtering. |
| `sensitive_information_policy_config` | `object` | `null` | Configuration for PII/sensitive data handling. |
| `topic_policy_config` | `object` | `null` | Configuration for topic-based filtering. |
| `kms_key_arn` | `string` | `null` | KMS key ARN for guardrail encryption. |
| `tags` | `map(string)` | `{}` | Tags for guardrail resources. |

### Variable Definitions

```hcl
# modules/guardrails/variables.tf

variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The deployment environment"
  type        = string
}

variable "guardrail_name" {
  description = "Name for the guardrail resource"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-_]+$", var.guardrail_name))
    error_message = "Guardrail name must contain only alphanumeric characters, hyphens, and underscores."
  }
}

variable "blocked_input_messaging" {
  description = "Message displayed when input is blocked"
  type        = string
  default     = "I cannot process this request due to content policy restrictions."
}

variable "blocked_output_messaging" {
  description = "Message displayed when output is blocked"
  type        = string
  default     = "I cannot provide this response due to content policy restrictions."
}

variable "content_policy_config" {
  description = "Configuration for content filtering policies"
  type = object({
    filters_config = list(object({
      input_strength  = string
      output_strength = string
      type            = string
    }))
  })
  default = {
    filters_config = [
      {
        input_strength  = "HIGH"
        output_strength = "HIGH"
        type            = "HATE"
      },
      {
        input_strength  = "HIGH"
        output_strength = "HIGH"
        type            = "INSULTS"
      },
      {
        input_strength  = "HIGH"
        output_strength = "HIGH"
        type            = "SEXUAL"
      },
      {
        input_strength  = "HIGH"
        output_strength = "HIGH"
        type            = "VIOLENCE"
      },
      {
        input_strength  = "HIGH"
        output_strength = "HIGH"
        type            = "MISCONDUCT"
      },
      {
        input_strength  = "MEDIUM"
        output_strength = "MEDIUM"
        type            = "PROMPT_ATTACK"
      }
    ]
  }

  validation {
    condition = alltrue([
      for filter in var.content_policy_config.filters_config :
      contains(["NONE", "LOW", "MEDIUM", "HIGH"], filter.input_strength) &&
      contains(["NONE", "LOW", "MEDIUM", "HIGH"], filter.output_strength) &&
      contains(["HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT", "PROMPT_ATTACK"], filter.type)
    ])
    error_message = "Invalid content policy filter configuration."
  }
}

variable "word_policy_config" {
  description = "Configuration for word-based filtering"
  type = object({
    managed_word_lists_config = optional(list(object({
      type = string
    })), [])
    words_config = optional(list(object({
      text = string
    })), [])
  })
  default = null
}

variable "sensitive_information_policy_config" {
  description = "Configuration for PII/sensitive data handling"
  type = object({
    pii_entities_config = list(object({
      action = string
      type   = string
    }))
    regexes_config = optional(list(object({
      action      = string
      description = string
      name        = string
      pattern     = string
    })), [])
  })
  default = null
}

variable "topic_policy_config" {
  description = "Configuration for topic-based filtering"
  type = object({
    topics_config = list(object({
      definition = string
      examples   = list(string)
      name       = string
      type       = string
    }))
  })
  default = null
}

variable "kms_key_arn" {
  description = "KMS key ARN for guardrail encryption"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags for guardrail resources"
  type        = map(string)
  default     = {}
}
```

---

## Guardrails Submodule Outputs

| Output | Type | Description |
|--------|------|-------------|
| `guardrail_ids` | `map(string)` | Map of region to guardrail ID. |
| `guardrail_arns` | `map(string)` | Map of region to guardrail ARN. |
| `guardrail_version` | `string` | Current version of the guardrail. |
| `guardrail_status` | `string` | Status of the guardrail (READY, CREATING, etc.). |

### Output Definitions

```hcl
# modules/guardrails/outputs.tf

output "guardrail_ids" {
  description = "Map of region to guardrail ID"
  value = {
    for k, v in aws_bedrock_guardrail.main : k => v.guardrail_id
  }
}

output "guardrail_arns" {
  description = "Map of region to guardrail ARN"
  value = {
    for k, v in aws_bedrock_guardrail.main : k => v.guardrail_arn
  }
}

output "guardrail_version" {
  description = "Current version of the guardrail"
  value       = aws_bedrock_guardrail.main[keys(aws_bedrock_guardrail.main)[0]].version
}

output "guardrail_status" {
  description = "Status of the guardrail"
  value       = aws_bedrock_guardrail.main[keys(aws_bedrock_guardrail.main)[0]].status
}
```

---

## Default Values

The following table summarizes the default values for all configurable variables:

| Module | Variable | Default Value |
|--------|----------|---------------|
| Root | `secondary_regions` | `[]` |
| Root | `enable_cross_region_inference` | `false` |
| Root | `enable_guardrails` | `true` |
| Root | `enable_monitoring` | `true` |
| Root | `log_retention_days` | `30` |
| Application Inference | `default_model_id` | `anthropic.claude-3-sonnet-20240229-v1:0` |
| Application Inference | `enable_model_invocation_logging` | `true` |
| Guardrails | `content_policy_config` | All filters at HIGH except PROMPT_ATTACK at MEDIUM |

---

## Environment-Specific Overrides

Different environments typically require different configurations. Below are recommended configurations for each environment.

### Development Environment

```hcl
# terraform.tfvars.dev

project_name     = "my-genai-app"
environment      = "dev"
primary_region   = "us-east-1"
secondary_regions = []

enable_cross_region_inference = false
enable_guardrails             = true
enable_monitoring             = true
log_retention_days            = 7

model_configurations = {
  claude_sonnet = {
    model_id        = "anthropic.claude-3-sonnet-20240229-v1:0"
    inference_units = 1
    max_tokens      = 2048
    temperature     = 0.7
    enabled         = true
    throughput_mode = "on_demand"
  }
}

tags = {
  Environment = "dev"
  CostCenter  = "development"
  ManagedBy   = "terraform"
}
```

### Staging Environment

```hcl
# terraform.tfvars.staging

project_name      = "my-genai-app"
environment       = "staging"
primary_region    = "us-east-1"
secondary_regions = ["us-west-2"]

enable_cross_region_inference = true
enable_guardrails             = true
enable_monitoring             = true
log_retention_days            = 30

model_configurations = {
  claude_sonnet = {
    model_id        = "anthropic.claude-3-sonnet-20240229-v1:0"
    inference_units = 2
    max_tokens      = 4096
    temperature     = 0.7
    enabled         = true
    throughput_mode = "on_demand"
  }
  embedding_model = {
    model_id        = "amazon.titan-embed-text-v1"
    inference_units = 1
    enabled         = true
    throughput_mode = "on_demand"
  }
}

tags = {
  Environment = "staging"
  CostCenter  = "staging"
  ManagedBy   = "terraform"
}
```

### Production Environment

```hcl
# terraform.tfvars.prod

project_name      = "my-genai-app"
environment       = "prod"
primary_region    = "us-east-1"
secondary_regions = ["us-west-2", "eu-west-1"]

enable_cross_region_inference = true
enable_guardrails             = true
enable_monitoring             = true
log_retention_days            = 365

kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

model_configurations = {
  claude_sonnet = {
    model_id            = "anthropic.claude-3-sonnet-20240229-v1:0"
    inference_units     = 5
    max_tokens          = 4096
    temperature         = 0.5
    enabled             = true
    throughput_mode     = "provisioned"
    commitment_duration = "ONE_MONTH"
  }
  claude_haiku = {
    model_id        = "anthropic.claude-3-haiku-20240307-v1:0"
    inference_units = 10
    max_tokens      = 4096
    temperature     = 0.7
    enabled         = true
    throughput_mode = "provisioned"
  }
  embedding_model = {
    model_id        = "amazon.titan-embed-text-v1"
    inference_units = 3
    enabled         = true
    throughput_mode = "provisioned"
  }
}

tags = {
  Environment  = "prod"
  CostCenter   = "production"
  ManagedBy    = "terraform"
  Compliance   = "SOC2"
  DataClass    = "confidential"
}
```

### Using Workspace-Based Configuration

```hcl
# main.tf

locals {
  env_config = {
    dev = {
      log_retention_days            = 7
      enable_cross_region_inference = false
      inference_units               = 1
    }
    staging = {
      log_retention_days            = 30
      enable_cross_region_inference = true
      inference_units               = 2
    }
    prod = {
      log_retention_days            = 365
      enable_cross_region_inference = true
      inference_units               = 5
    }
  }

  current_env = local.env_config[terraform.workspace]
}

module "bedrock" {
  source = "./modules/aws-terraform-bedrock"

  project_name                  = var.project_name
  environment                   = terraform.workspace
  primary_region                = var.primary_region
  log_retention_days            = local.current_env.log_retention_days
  enable_cross_region_inference = local.current_env.enable_cross_region_inference
  
  # ... additional configuration
}
```

---

## Best Practices

1. **Always use variables files**: Store environment-specific values in separate `.tfvars` files rather than hardcoding values.

2. **Encrypt sensitive data**: Always provide a `kms_key_arn` for production environments to ensure data encryption.

3. **Enable guardrails in production**: Keep `enable_guardrails = true` for production to ensure AI safety compliance.

4. **Configure appropriate log retention**: Use longer retention periods for production (365+ days) for compliance and auditing.

5. **Use provisioned throughput for production**: Configure `throughput_mode = "provisioned"` for production workloads to ensure consistent performance.

6. **Tag all resources**: Always provide comprehensive tags for cost allocation and resource management.