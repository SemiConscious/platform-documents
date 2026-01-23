# Guardrails Configuration

## Overview

AWS Bedrock Guardrails provide a critical safety layer for your generative AI applications, enabling you to implement responsible AI practices by filtering harmful content, preventing sensitive information disclosure, and ensuring model outputs align with your organization's policies. This documentation covers the comprehensive configuration of guardrails within the `aws-terraform-bedrock` module, helping operators deploy robust content filtering and safety mechanisms across multiple regions.

Guardrails in AWS Bedrock act as configurable safeguards that evaluate both user inputs (prompts) and model outputs (responses) against a set of defined policies. When content violates these policies, the guardrail can block the request, redact sensitive information, or provide alternative responses based on your configuration.

### Key Benefits of Guardrails

- **Content Safety**: Filter harmful, offensive, or inappropriate content from AI interactions
- **Data Protection**: Prevent exposure of sensitive information like PII, credentials, or proprietary data
- **Compliance**: Ensure AI outputs meet regulatory and organizational requirements
- **Customization**: Define topic-specific restrictions and custom word filters
- **Auditability**: Track and monitor guardrail interventions for compliance reporting

### How Guardrails Work

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input ──► Input Guardrail ──► Bedrock Model              │
│                     │                     │                     │
│                     ▼                     ▼                     │
│              [Block/Allow]        Model Response                │
│                                          │                      │
│                                          ▼                      │
│                                  Output Guardrail               │
│                                          │                      │
│                                          ▼                      │
│                                   [Block/Allow/Redact]          │
│                                          │                      │
│                                          ▼                      │
│                                   Final Response to User        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Guardrail Module Structure

The `aws-terraform-bedrock` module organizes guardrails configuration within a dedicated submodule structure, allowing for clean separation of concerns and reusable guardrail definitions across multiple inference profiles and regions.

### Directory Structure

```
aws-terraform-bedrock/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── guardrails/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── content_filters.tf
│   │   ├── topic_policies.tf
│   │   ├── word_policies.tf
│   │   └── sensitive_info.tf
│   ├── inference-profiles/
│   └── monitoring/
└── examples/
    └── guardrails/
        ├── basic/
        ├── advanced/
        └── multi-region/
```

### Module Dependencies

The guardrails module integrates with other components of the `aws-terraform-bedrock` module:

```hcl
# Example module integration
module "bedrock_guardrails" {
  source = "./modules/guardrails"

  guardrail_name        = var.guardrail_name
  guardrail_description = var.guardrail_description
  
  content_policy_config = var.content_policy_config
  topic_policy_config   = var.topic_policy_config
  word_policy_config    = var.word_policy_config
  sensitive_info_config = var.sensitive_info_config
  
  blocked_input_messaging  = var.blocked_input_messaging
  blocked_output_messaging = var.blocked_output_messaging
  
  tags = var.tags
}

# Reference guardrail in inference profile
module "inference_profile" {
  source = "./modules/inference-profiles"

  guardrail_identifier = module.bedrock_guardrails.guardrail_id
  guardrail_version    = module.bedrock_guardrails.guardrail_version
  
  # ... other configuration
}
```

---

## Available Variables

### Core Guardrail Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `guardrail_name` | `string` | Yes | - | Unique name for the guardrail (1-50 characters) |
| `guardrail_description` | `string` | No | `""` | Human-readable description of the guardrail's purpose |
| `blocked_input_messaging` | `string` | Yes | - | Message returned when input is blocked |
| `blocked_output_messaging` | `string` | Yes | - | Message returned when output is blocked |
| `kms_key_arn` | `string` | No | `null` | KMS key ARN for encrypting guardrail configuration |
| `tags` | `map(string)` | No | `{}` | Resource tags for the guardrail |

### Content Policy Variables

```hcl
variable "content_policy_config" {
  description = "Configuration for content filtering policies"
  type = object({
    filters_config = list(object({
      input_strength  = string  # NONE, LOW, MEDIUM, HIGH
      output_strength = string  # NONE, LOW, MEDIUM, HIGH
      type            = string  # SEXUAL, VIOLENCE, HATE, INSULTS, MISCONDUCT, PROMPT_ATTACK
    }))
  })
  default = null
}
```

### Topic Policy Variables

```hcl
variable "topic_policy_config" {
  description = "Configuration for topic-based restrictions"
  type = object({
    topics_config = list(object({
      name       = string
      definition = string
      examples   = list(string)
      type       = string  # DENY
    }))
  })
  default = null
}
```

### Word Policy Variables

```hcl
variable "word_policy_config" {
  description = "Configuration for word-based filtering"
  type = object({
    managed_word_lists_config = list(object({
      type = string  # PROFANITY
    }))
    words_config = list(object({
      text = string
    }))
  })
  default = null
}
```

### Sensitive Information Variables

```hcl
variable "sensitive_info_config" {
  description = "Configuration for PII and sensitive data handling"
  type = object({
    pii_entities_config = list(object({
      action = string  # BLOCK, ANONYMIZE
      type   = string  # See supported PII types below
    }))
    regexes_config = list(object({
      action      = string
      description = string
      name        = string
      pattern     = string
    }))
  })
  default = null
}
```

---

## Content Filtering Options

### Content Filter Types

AWS Bedrock guardrails support filtering across six primary content categories:

| Filter Type | Description | Use Cases |
|-------------|-------------|-----------|
| `SEXUAL` | Sexual or adult content | General audience applications, workplace tools |
| `VIOLENCE` | Violent content or imagery | Child-safe applications, educational platforms |
| `HATE` | Hate speech and discriminatory content | All production applications |
| `INSULTS` | Insulting or demeaning language | Customer-facing applications |
| `MISCONDUCT` | Criminal or unethical activities | Enterprise applications, financial services |
| `PROMPT_ATTACK` | Prompt injection and jailbreak attempts | Security-critical applications |

### Filter Strength Levels

Each content filter can be configured with different strength levels for input and output:

- **NONE**: No filtering applied
- **LOW**: Filters only highly confident violations
- **MEDIUM**: Balanced filtering (recommended for most use cases)
- **HIGH**: Aggressive filtering (may have higher false positive rate)

### Example Content Filter Configuration

```hcl
# modules/guardrails/content_filters.tf

locals {
  # Standard enterprise content filtering
  enterprise_content_filters = {
    filters_config = [
      {
        type            = "SEXUAL"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "VIOLENCE"
        input_strength  = "MEDIUM"
        output_strength = "HIGH"
      },
      {
        type            = "HATE"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "INSULTS"
        input_strength  = "MEDIUM"
        output_strength = "MEDIUM"
      },
      {
        type            = "MISCONDUCT"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "PROMPT_ATTACK"
        input_strength  = "HIGH"
        output_strength = "NONE"  # Only relevant for input
      }
    ]
  }
}
```

---

## Configuring Custom Guardrails

### Basic Guardrail Configuration

```hcl
# terraform/environments/production/guardrails.tf

module "production_guardrails" {
  source = "../../modules/guardrails"

  guardrail_name        = "production-ai-safety-guardrail"
  guardrail_description = "Production guardrail for customer-facing AI applications"

  # Blocked messages
  blocked_input_messaging  = "Your request could not be processed. Please rephrase your question."
  blocked_output_messaging = "I'm unable to provide a response to that request. Please try a different question."

  # Content filtering
  content_policy_config = {
    filters_config = [
      {
        type            = "SEXUAL"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "VIOLENCE"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "HATE"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "INSULTS"
        input_strength  = "MEDIUM"
        output_strength = "MEDIUM"
      },
      {
        type            = "MISCONDUCT"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "PROMPT_ATTACK"
        input_strength  = "HIGH"
        output_strength = "NONE"
      }
    ]
  }

  tags = {
    Environment = "production"
    Team        = "ai-platform"
    CostCenter  = "ai-safety"
  }
}
```

### Advanced Guardrail with Topic Restrictions

```hcl
# terraform/environments/production/guardrails_advanced.tf

module "financial_services_guardrails" {
  source = "../../modules/guardrails"

  guardrail_name        = "financial-services-guardrail"
  guardrail_description = "Guardrail for financial advisory applications"

  blocked_input_messaging  = "This request cannot be processed due to content policy restrictions."
  blocked_output_messaging = "I cannot provide information on this topic. Please consult a qualified professional."

  # Content filtering
  content_policy_config = {
    filters_config = [
      {
        type            = "MISCONDUCT"
        input_strength  = "HIGH"
        output_strength = "HIGH"
      },
      {
        type            = "PROMPT_ATTACK"
        input_strength  = "HIGH"
        output_strength = "NONE"
      }
    ]
  }

  # Topic restrictions
  topic_policy_config = {
    topics_config = [
      {
        name       = "investment-advice"
        definition = "Specific investment recommendations, stock picks, or financial advice that could be construed as professional financial guidance"
        type       = "DENY"
        examples = [
          "Which stocks should I buy right now?",
          "Should I invest in cryptocurrency?",
          "Tell me which mutual funds will perform best",
          "Is now a good time to buy real estate?"
        ]
      },
      {
        name       = "tax-advice"
        definition = "Specific tax advice, tax evasion strategies, or guidance that should come from a licensed tax professional"
        type       = "DENY"
        examples = [
          "How can I avoid paying taxes?",
          "What tax loopholes can I use?",
          "Should I claim this as a business expense?"
        ]
      },
      {
        name       = "competitor-discussion"
        definition = "Detailed comparisons or recommendations involving competitor financial products or services"
        type       = "DENY"
        examples = [
          "Is your competitor's savings account better?",
          "Compare your rates to other banks",
          "Why should I choose you over Bank XYZ?"
        ]
      }
    ]
  }

  # Word filtering
  word_policy_config = {
    managed_word_lists_config = [
      {
        type = "PROFANITY"
      }
    ]
    words_config = [
      { text = "guaranteed returns" },
      { text = "risk-free investment" },
      { text = "get rich quick" },
      { text = "insider information" }
    ]
  }

  # Sensitive information handling
  sensitive_info_config = {
    pii_entities_config = [
      {
        type   = "US_SOCIAL_SECURITY_NUMBER"
        action = "BLOCK"
      },
      {
        type   = "CREDIT_DEBIT_CARD_NUMBER"
        action = "ANONYMIZE"
      },
      {
        type   = "US_BANK_ACCOUNT_NUMBER"
        action = "BLOCK"
      },
      {
        type   = "US_BANK_ROUTING_NUMBER"
        action = "BLOCK"
      },
      {
        type   = "EMAIL"
        action = "ANONYMIZE"
      },
      {
        type   = "PHONE"
        action = "ANONYMIZE"
      }
    ]
    regexes_config = [
      {
        name        = "internal-account-id"
        description = "Internal account identifier format"
        pattern     = "ACC-[A-Z]{2}[0-9]{8}"
        action      = "ANONYMIZE"
      },
      {
        name        = "internal-employee-id"
        description = "Internal employee identifier"
        pattern     = "EMP[0-9]{6}"
        action      = "BLOCK"
      }
    ]
  }

  kms_key_arn = data.aws_kms_key.bedrock.arn

  tags = {
    Environment  = "production"
    Team         = "financial-ai"
    Compliance   = "sox-pci"
    DataCategory = "financial"
  }
}
```

### Multi-Region Guardrail Deployment

```hcl
# terraform/environments/production/guardrails_multi_region.tf

locals {
  deployment_regions = ["us-east-1", "us-west-2", "eu-west-1"]
  
  guardrail_config = {
    name        = "global-ai-safety-guardrail"
    description = "Global guardrail for multi-region AI deployment"
    
    content_policy = {
      filters_config = [
        {
          type            = "HATE"
          input_strength  = "HIGH"
          output_strength = "HIGH"
        },
        {
          type            = "PROMPT_ATTACK"
          input_strength  = "HIGH"
          output_strength = "NONE"
        }
      ]
    }
  }
}

# Deploy guardrails to each region
module "regional_guardrails" {
  source   = "../../modules/guardrails"
  for_each = toset(local.deployment_regions)

  providers = {
    aws = aws.regional[each.key]
  }

  guardrail_name        = "${local.guardrail_config.name}-${each.key}"
  guardrail_description = "${local.guardrail_config.description} (${each.key})"

  blocked_input_messaging  = "Request blocked by content policy."
  blocked_output_messaging = "Response blocked by content policy."

  content_policy_config = local.guardrail_config.content_policy

  tags = {
    Environment = "production"
    Region      = each.key
    ManagedBy   = "terraform"
  }
}

# Output guardrail IDs for each region
output "guardrail_ids" {
  description = "Map of region to guardrail ID"
  value = {
    for region, guardrail in module.regional_guardrails :
    region => guardrail.guardrail_id
  }
}
```

---

## Applying Guardrails to Inference Profiles

### Associating Guardrails with Inference Profiles

Once guardrails are created, they must be associated with inference profiles to take effect. The `aws-terraform-bedrock` module supports this through the inference profile configuration.

```hcl
# terraform/environments/production/inference_profiles.tf

module "claude_inference_profile" {
  source = "../../modules/inference-profiles"

  profile_name        = "claude-3-sonnet-production"
  profile_description = "Production inference profile for Claude 3 Sonnet"
  
  model_source = "anthropic.claude-3-sonnet-20240229-v1:0"
  
  # Associate guardrail
  guardrail_configuration = {
    guardrail_identifier = module.production_guardrails.guardrail_id
    guardrail_version    = module.production_guardrails.guardrail_version
  }

  # Cross-region inference support
  cross_region_inference = {
    enabled = true
    regions = ["us-east-1", "us-west-2"]
  }

  tags = {
    Environment = "production"
    Model       = "claude-3-sonnet"
  }
}
```

### Guardrail Version Management

AWS Bedrock guardrails support versioning, allowing you to update guardrail configurations without immediately affecting production workloads.

```hcl
# modules/guardrails/outputs.tf

output "guardrail_id" {
  description = "The unique identifier of the guardrail"
  value       = aws_bedrock_guardrail.this.guardrail_id
}

output "guardrail_arn" {
  description = "The ARN of the guardrail"
  value       = aws_bedrock_guardrail.this.guardrail_arn
}

output "guardrail_version" {
  description = "The current version of the guardrail"
  value       = aws_bedrock_guardrail.this.version
}

output "guardrail_status" {
  description = "The status of the guardrail"
  value       = aws_bedrock_guardrail.this.status
}
```

### Version Pinning Strategy

```hcl
# Using specific guardrail versions for stability
module "stable_inference_profile" {
  source = "../../modules/inference-profiles"

  profile_name = "claude-stable-production"
  model_source = "anthropic.claude-3-sonnet-20240229-v1:0"

  guardrail_configuration = {
    guardrail_identifier = module.production_guardrails.guardrail_id
    # Pin to specific version for stability
    guardrail_version    = "1"  # Or use "DRAFT" for testing
  }

  tags = {
    Environment     = "production"
    GuardrailPolicy = "stable"
  }
}

# Using latest version for staging (auto-updates)
module "staging_inference_profile" {
  source = "../../modules/inference-profiles"

  profile_name = "claude-staging"
  model_source = "anthropic.claude-3-sonnet-20240229-v1:0"

  guardrail_configuration = {
    guardrail_identifier = module.staging_guardrails.guardrail_id
    # Use DRAFT to test new guardrail configurations
    guardrail_version    = "DRAFT"
  }

  tags = {
    Environment     = "staging"
    GuardrailPolicy = "testing"
  }
}
```

---

## Testing Guardrails

### Pre-Deployment Testing

Before deploying guardrails to production, thoroughly test them using the DRAFT version:

```hcl
# terraform/environments/testing/guardrails_test.tf

module "test_guardrails" {
  source = "../../modules/guardrails"

  guardrail_name        = "test-guardrail-${formatdate("YYYYMMDD", timestamp())}"
  guardrail_description = "Test guardrail for validation"

  blocked_input_messaging  = "TEST: Input blocked"
  blocked_output_messaging = "TEST: Output blocked"

  content_policy_config = var.test_content_policy

  tags = {
    Environment = "testing"
    Purpose     = "guardrail-validation"
    TTL         = "24h"
  }
}

# Output for testing scripts
output "test_guardrail_id" {
  value = module.test_guardrails.guardrail_id
}
```

### Test Script Example

Create a testing script to validate guardrail behavior:

```bash
#!/bin/bash
# scripts/test_guardrails.sh

set -e

GUARDRAIL_ID="${1:-$(terraform output -raw test_guardrail_id)}"
GUARDRAIL_VERSION="${2:-DRAFT}"
REGION="${3:-us-east-1}"

echo "Testing guardrail: $GUARDRAIL_ID (version: $GUARDRAIL_VERSION)"

# Test cases
declare -a test_cases=(
  '{"text": "Hello, how can I help you today?", "expected": "PASS"}'
  '{"text": "How do I hack into a computer?", "expected": "BLOCK"}'
  '{"text": "Tell me about your competitor products", "expected": "BLOCK"}'
  '{"text": "My SSN is 123-45-6789", "expected": "BLOCK_OR_ANONYMIZE"}'
)

for test_case in "${test_cases[@]}"; do
  text=$(echo "$test_case" | jq -r '.text')
  expected=$(echo "$test_case" | jq -r '.expected')
  
  echo "Testing: $text"
  
  result=$(aws bedrock-runtime apply-guardrail \
    --guardrail-identifier "$GUARDRAIL_ID" \
    --guardrail-version "$GUARDRAIL_VERSION" \
    --source INPUT \
    --content "[{\"text\": {\"text\": \"$text\"}}]" \
    --region "$REGION" \
    --output json 2>&1)
  
  action=$(echo "$result" | jq -r '.action')
  
  echo "  Expected: $expected, Got: $action"
  
  if [[ "$expected" == "PASS" && "$action" == "NONE" ]] || \
     [[ "$expected" == "BLOCK" && "$action" == "GUARDRAIL_INTERVENED" ]] || \
     [[ "$expected" == "BLOCK_OR_ANONYMIZE" && "$action" != "NONE" ]]; then
    echo "  ✅ PASSED"
  else
    echo "  ❌ FAILED"
    exit 1
  fi
done

echo ""
echo "All guardrail tests passed!"
```

### Monitoring Guardrail Activity

Integrate with CloudWatch for guardrail monitoring:

```hcl
# terraform/environments/production/guardrails_monitoring.tf

resource "aws_cloudwatch_metric_alarm" "guardrail_intervention_rate" {
  alarm_name          = "bedrock-guardrail-high-intervention-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "GuardrailIntervention"
  namespace           = "AWS/Bedrock"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "High rate of guardrail interventions detected"

  dimensions = {
    GuardrailId = module.production_guardrails.guardrail_id
  }

  alarm_actions = [aws_sns_topic.ai_alerts.arn]

  tags = {
    Environment = "production"
    Component   = "guardrails"
  }
}

resource "aws_cloudwatch_dashboard" "guardrails" {
  dashboard_name = "bedrock-guardrails-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Guardrail Interventions by Type"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Bedrock", "GuardrailIntervention", "GuardrailId", module.production_guardrails.guardrail_id, "InterventionType", "CONTENT_FILTER"],
            ["...", "TOPIC_POLICY"],
            ["...", "WORD_POLICY"],
            ["...", "SENSITIVE_INFO"]
          ]
          stat   = "Sum"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Guardrail Processing Latency"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Bedrock", "GuardrailLatency", "GuardrailId", module.production_guardrails.guardrail_id]
          ]
          stat   = "Average"
          period = 60
        }
      }
    ]
  })
}
```

### Best Practices for Guardrail Testing

1. **Use DRAFT versions** for initial testing before creating versioned guardrails
2. **Create comprehensive test suites** covering edge cases and expected behaviors
3. **Test in isolation** before integrating with inference profiles
4. **Monitor false positives** and adjust filter strengths accordingly
5. **Document expected behaviors** for each guardrail configuration
6. **Implement gradual rollouts** using version pinning
7. **Set up alerting** for unusual intervention patterns
8. **Regularly review and update** topic policies and word lists

---

## Troubleshooting Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| High false positive rate | Filter strength too aggressive | Reduce input/output strength from HIGH to MEDIUM |
| Guardrail not triggering | Version mismatch or not associated | Verify guardrail version and inference profile association |
| Latency increase | Complex regex patterns | Simplify regex patterns or reduce pattern count |
| Topic policy not working | Vague definition | Provide more specific definitions and examples |
| PII not detected | Uncommon format | Add custom regex patterns for specific formats |

For additional support, consult the [AWS Bedrock Guardrails documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) or open an issue in the module repository.