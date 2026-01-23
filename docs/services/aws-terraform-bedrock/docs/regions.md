# Regional Configuration

## Overview

The `aws-terraform-bedrock` module supports deploying AWS Bedrock GenAI configurations across multiple AWS regions worldwide. This documentation provides comprehensive guidance on supported regions, region-specific configurations, and how to manage multi-region deployments effectively.

Understanding regional configuration is crucial for operators who need to:
- Deploy AI workloads close to end users for reduced latency
- Comply with data residency requirements
- Implement disaster recovery strategies
- Leverage cross-region inference capabilities

## Supported Regions

The `aws-terraform-bedrock` module currently supports deployment across **10 AWS regions** spanning three major geographic areas: Americas (US), Europe (EU), and Asia-Pacific (APAC).

### Region Availability Matrix

| Region Code | Region Name | Claude Models | CAI Models | Embedding Models | Guardrails | Cross-Region Inference |
|-------------|-------------|---------------|------------|------------------|------------|------------------------|
| `us-east-2` | US East (Ohio) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `us-west-2` | US West (Oregon) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `eu-central-1` | Europe (Frankfurt) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `eu-north-1` | Europe (Stockholm) | ✅ | ⚠️ Limited | ✅ | ✅ | ✅ |
| `eu-west-1` | Europe (Ireland) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `eu-west-2` | Europe (London) | ✅ | ⚠️ Limited | ✅ | ✅ | ✅ |
| `ap-southeast-1` | Asia Pacific (Singapore) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ap-southeast-2` | Asia Pacific (Sydney) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ap-southeast-4` | Asia Pacific (Melbourne) | ✅ | ⚠️ Limited | ⚠️ Limited | ✅ | ✅ |

> **Note:** Model availability may change as AWS expands Bedrock services. Always verify current availability in the [AWS Bedrock documentation](https://docs.aws.amazon.com/bedrock/).

## Region Configuration Files

Each supported region has its own configuration file located in the `regions/` directory of the module. These files define region-specific settings, model availability, and default configurations.

### Directory Structure

```
aws-terraform-bedrock/
├── main.tf
├── variables.tf
├── outputs.tf
├── regions/
│   ├── us-east-2.tf
│   ├── us-west-2.tf
│   ├── eu-central-1.tf
│   ├── eu-north-1.tf
│   ├── eu-west-1.tf
│   ├── eu-west-2.tf
│   ├── ap-southeast-1.tf
│   ├── ap-southeast-2.tf
│   └── ap-southeast-4.tf
├── scripts/
│   └── compress_region_outputs.sh
└── modules/
    ├── inference-profile/
    ├── guardrails/
    └── monitoring/
```

### Configuration File Structure

Each region configuration file follows a standardized structure:

```hcl
# regions/example-region.tf

locals {
  region_code = "example-region-1"
  region_name = "Example Region (City)"
  
  # Model availability for this region
  available_models = {
    claude = {
      "claude-3-sonnet"    = true
      "claude-3-haiku"     = true
      "claude-3-opus"      = true
      "claude-instant-v1"  = true
    }
    cai = {
      "cai-standard"       = true
      "cai-advanced"       = false  # Not available in this region
    }
    embedding = {
      "titan-embed-text"   = true
      "titan-embed-image"  = true
    }
  }
  
  # Region-specific endpoints
  endpoints = {
    bedrock_runtime = "bedrock-runtime.${local.region_code}.amazonaws.com"
    bedrock_agent   = "bedrock-agent.${local.region_code}.amazonaws.com"
  }
  
  # Cross-region inference targets
  cross_region_targets = [
    "us-east-2",
    "us-west-2"
  ]
}
```

## US Regions (us-east-2, us-west-2)

The US regions provide the most comprehensive AWS Bedrock feature set and are recommended as primary deployment targets for North American workloads.

### US East (Ohio) - us-east-2

US East (Ohio) serves as a primary region with full model availability and is often used as the hub for cross-region inference configurations.

```hcl
# terraform.tfvars - US East Configuration

region = "us-east-2"

bedrock_config = {
  environment = "production"
  
  inference_profiles = {
    primary = {
      name        = "prod-inference-ohio"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
      
      # Enable cross-region failover
      cross_region_inference = {
        enabled = true
        target_regions = ["us-west-2", "eu-west-1"]
        failover_priority = ["us-west-2", "eu-west-1"]
      }
    }
  }
  
  guardrails = {
    content_filters = {
      hate_speech    = "HIGH"
      sexual_content = "HIGH"
      violence       = "MEDIUM"
      insults        = "MEDIUM"
    }
    
    topic_policies = {
      denied_topics = ["illegal_activities", "medical_advice"]
    }
  }
  
  monitoring = {
    cloudwatch_enabled     = true
    log_retention_days     = 30
    detailed_metrics       = true
    alarm_notification_arn = "arn:aws:sns:us-east-2:123456789012:bedrock-alerts"
  }
}
```

### US West (Oregon) - us-west-2

US West (Oregon) provides excellent latency for West Coast users and serves as an ideal secondary region for disaster recovery.

```hcl
# terraform.tfvars - US West Configuration

region = "us-west-2"

bedrock_config = {
  environment = "production"
  
  inference_profiles = {
    # Optimized for low-latency West Coast applications
    realtime = {
      name        = "prod-realtime-oregon"
      model_id    = "anthropic.claude-3-haiku-20240307-v1:0"
      throughput  = "provisioned"
      
      provisioned_config = {
        model_units = 2
        auto_scaling = {
          min_capacity = 1
          max_capacity = 5
          target_utilization = 70
        }
      }
    }
    
    # Batch processing profile
    batch = {
      name        = "prod-batch-oregon"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
    }
  }
  
  # Region-specific tagging
  tags = {
    Region      = "us-west-2"
    CostCenter  = "ai-platform-west"
    Compliance  = "SOC2"
  }
}
```

### US Regions Best Practices

1. **Primary/Secondary Architecture**: Use `us-east-2` as primary and `us-west-2` as secondary for high availability
2. **Latency Optimization**: Deploy user-facing applications to the region closest to your user base
3. **Cost Management**: Leverage on-demand throughput for variable workloads; use provisioned for predictable traffic
4. **Compliance**: US regions support FedRAMP Moderate for government workloads

## EU Regions (eu-central-1, eu-north-1, eu-west-1, eu-west-2)

European regions are essential for GDPR compliance and serving EU-based customers with data residency requirements.

### Europe (Frankfurt) - eu-central-1

Frankfurt serves as the primary EU hub with full feature availability.

```hcl
# terraform.tfvars - EU Central Configuration

region = "eu-central-1"

bedrock_config = {
  environment = "production-eu"
  
  # GDPR-compliant configuration
  data_residency = {
    enforce_region_boundary = true
    allowed_regions         = ["eu-central-1", "eu-west-1", "eu-north-1"]
    cross_region_inference  = {
      enabled = true
      # Only allow inference within EU regions
      target_regions = ["eu-west-1", "eu-north-1"]
    }
  }
  
  inference_profiles = {
    eu_primary = {
      name        = "prod-eu-frankfurt"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
    }
  }
  
  # Enhanced logging for GDPR audit requirements
  monitoring = {
    cloudwatch_enabled     = true
    log_retention_days     = 90  # Extended for compliance
    detailed_metrics       = true
    audit_logging          = true
    
    log_exports = {
      s3_bucket = "bedrock-audit-logs-eu"
      kms_key   = "arn:aws:kms:eu-central-1:123456789012:key/audit-key"
    }
  }
  
  tags = {
    DataClassification = "GDPR-Regulated"
    Region            = "eu-central-1"
  }
}
```

### Europe (Stockholm) - eu-north-1

Stockholm offers enhanced sustainability with AWS's commitment to renewable energy.

```hcl
# terraform.tfvars - EU North Configuration

region = "eu-north-1"

bedrock_config = {
  environment = "production-eu-north"
  
  inference_profiles = {
    sustainable = {
      name        = "prod-sustainable-stockholm"
      model_id    = "anthropic.claude-3-haiku-20240307-v1:0"
      throughput  = "on-demand"
      
      # Note: Some CAI models have limited availability
      fallback_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    }
  }
  
  tags = {
    Sustainability = "renewable-powered"
    Region         = "eu-north-1"
  }
}
```

### Europe (Ireland) - eu-west-1

Ireland is one of AWS's oldest and most mature EU regions with excellent connectivity.

```hcl
# terraform.tfvars - EU West (Ireland) Configuration

region = "eu-west-1"

bedrock_config = {
  environment = "production-eu-west"
  
  inference_profiles = {
    ireland_primary = {
      name        = "prod-ireland-primary"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
    }
  }
  
  # Leverage Ireland as EU failover hub
  cross_region_inference = {
    enabled = true
    role    = "secondary"  # Receives traffic from eu-central-1
    target_regions = ["eu-central-1", "eu-west-2"]
  }
}
```

### Europe (London) - eu-west-2

London provides dedicated UK data residency post-Brexit.

```hcl
# terraform.tfvars - EU West (London) Configuration

region = "eu-west-2"

bedrock_config = {
  environment = "production-uk"
  
  # UK-specific data residency
  data_residency = {
    enforce_region_boundary = true
    allowed_regions         = ["eu-west-2"]  # UK data stays in UK
    cross_region_inference  = {
      enabled = false  # Disabled for strict UK data residency
    }
  }
  
  inference_profiles = {
    uk_only = {
      name        = "prod-uk-london"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
    }
  }
  
  tags = {
    DataResidency = "UK-Only"
    Compliance    = "UK-GDPR"
  }
}
```

## APAC Regions (ap-southeast-1, ap-southeast-2, ap-southeast-4)

Asia-Pacific regions serve customers across Southeast Asia and Oceania with region-optimized deployments.

### Asia Pacific (Singapore) - ap-southeast-1

Singapore serves as the primary APAC hub with excellent connectivity across the region.

```hcl
# terraform.tfvars - APAC Singapore Configuration

region = "ap-southeast-1"

bedrock_config = {
  environment = "production-apac"
  
  inference_profiles = {
    apac_primary = {
      name        = "prod-apac-singapore"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
      
      cross_region_inference = {
        enabled = true
        target_regions = ["ap-southeast-2", "ap-southeast-4"]
        failover_priority = ["ap-southeast-2", "ap-southeast-4"]
      }
    }
  }
  
  # Multi-language guardrails for APAC markets
  guardrails = {
    content_filters = {
      hate_speech    = "HIGH"
      sexual_content = "HIGH"
      violence       = "MEDIUM"
    }
    
    # Support for multiple APAC languages
    language_config = {
      supported_languages = ["en", "zh", "ja", "ko", "th", "vi", "id"]
      default_language    = "en"
    }
  }
  
  tags = {
    Region     = "ap-southeast-1"
    CostCenter = "apac-ai-platform"
  }
}
```

### Asia Pacific (Sydney) - ap-southeast-2

Sydney provides coverage for Australia and New Zealand.

```hcl
# terraform.tfvars - APAC Sydney Configuration

region = "ap-southeast-2"

bedrock_config = {
  environment = "production-anz"
  
  inference_profiles = {
    anz_primary = {
      name        = "prod-anz-sydney"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
    }
    
    # Embedding models for local search applications
    embedding = {
      name        = "prod-embed-sydney"
      model_id    = "amazon.titan-embed-text-v1"
      throughput  = "on-demand"
    }
  }
  
  tags = {
    Region     = "ap-southeast-2"
    Market     = "ANZ"
  }
}
```

### Asia Pacific (Melbourne) - ap-southeast-4

Melbourne provides additional Australian coverage and disaster recovery options.

```hcl
# terraform.tfvars - APAC Melbourne Configuration

region = "ap-southeast-4"

bedrock_config = {
  environment = "production-anz-dr"
  
  # Note: Limited model availability - verify before deployment
  inference_profiles = {
    melbourne_dr = {
      name        = "prod-dr-melbourne"
      model_id    = "anthropic.claude-3-sonnet-20240229-v1:0"
      throughput  = "on-demand"
      
      # Configure as DR target for Sydney
      role = "disaster-recovery"
      primary_region = "ap-southeast-2"
    }
  }
  
  # Reduced monitoring for DR region
  monitoring = {
    cloudwatch_enabled = true
    log_retention_days = 14
    detailed_metrics   = false
  }
  
  tags = {
    Region   = "ap-southeast-4"
    Purpose  = "disaster-recovery"
  }
}
```

## Adding New Regions

When AWS releases Bedrock support in new regions, follow this process to add support to your deployment.

### Step 1: Create Region Configuration File

```hcl
# regions/new-region-1.tf

locals {
  new_region_config = {
    region_code = "new-region-1"
    region_name = "New Region (City)"
    
    # Verify model availability with AWS documentation
    available_models = {
      claude = {
        "claude-3-sonnet"    = true
        "claude-3-haiku"     = true
        "claude-3-opus"      = false  # Verify availability
        "claude-instant-v1"  = true
      }
      cai = {
        "cai-standard"       = false  # Verify availability
        "cai-advanced"       = false
      }
      embedding = {
        "titan-embed-text"   = true
        "titan-embed-image"  = false  # Verify availability
      }
    }
    
    endpoints = {
      bedrock_runtime = "bedrock-runtime.new-region-1.amazonaws.com"
      bedrock_agent   = "bedrock-agent.new-region-1.amazonaws.com"
    }
    
    # Define which regions can receive cross-region inference
    cross_region_targets = []  # Update after testing
  }
}

# Region-specific provider configuration
provider "aws" {
  alias  = "new_region"
  region = "new-region-1"
}
```

### Step 2: Update Variables File

```hcl
# variables.tf - Add new region to allowed values

variable "region" {
  description = "AWS region for Bedrock deployment"
  type        = string
  
  validation {
    condition = contains([
      "us-east-2",
      "us-west-2",
      "eu-central-1",
      "eu-north-1",
      "eu-west-1",
      "eu-west-2",
      "ap-southeast-1",
      "ap-southeast-2",
      "ap-southeast-4",
      "new-region-1"  # Add new region
    ], var.region)
    error_message = "Region must be a supported Bedrock region."
  }
}
```

### Step 3: Test New Region

```bash
#!/bin/bash
# scripts/test_new_region.sh

REGION="new-region-1"

echo "Testing Bedrock availability in ${REGION}..."

# Test Bedrock Runtime endpoint
aws bedrock-runtime list-foundation-models \
  --region ${REGION} \
  --output table

# Test inference profile creation
terraform plan \
  -var="region=${REGION}" \
  -target=module.inference_profile

# Run integration tests
terraform test \
  -var="region=${REGION}"
```

### Step 4: Update Documentation

After successful testing, update this documentation to include the new region in the Supported Regions table and create a dedicated configuration section.

## Region Output Compression Scripts

For large multi-region deployments, managing Terraform outputs can become unwieldy. The module includes compression scripts to streamline output management.

### Output Compression Script

```bash
#!/bin/bash
# scripts/compress_region_outputs.sh
# Compresses and aggregates outputs from multi-region deployments

set -euo pipefail

OUTPUT_DIR="${1:-./outputs}"
COMPRESSED_FILE="${2:-region_outputs.tar.gz}"

echo "Collecting region outputs..."

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Define regions to process
REGIONS=(
  "us-east-2"
  "us-west-2"
  "eu-central-1"
  "eu-north-1"
  "eu-west-1"
  "eu-west-2"
  "ap-southeast-1"
  "ap-southeast-2"
  "ap-southeast-4"
)

# Collect outputs from each region
for region in "${REGIONS[@]}"; do
  echo "Processing ${region}..."
  
  # Export Terraform outputs to JSON
  terraform output -json \
    -state="terraform.${region}.tfstate" \
    > "${OUTPUT_DIR}/${region}_outputs.json" 2>/dev/null || \
    echo "{}" > "${OUTPUT_DIR}/${region}_outputs.json"
done

# Create aggregated summary
echo "Creating aggregated summary..."
cat > "${OUTPUT_DIR}/summary.json" << EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "regions": $(echo "${REGIONS[@]}" | jq -R 'split(" ")'),
  "outputs_path": "${OUTPUT_DIR}"
}
EOF

# Compress outputs
echo "Compressing outputs to ${COMPRESSED_FILE}..."
tar -czvf "${COMPRESSED_FILE}" -C "${OUTPUT_DIR}" .

# Generate checksum
sha256sum "${COMPRESSED_FILE}" > "${COMPRESSED_FILE}.sha256"

echo "Output compression complete."
echo "  Archive: ${COMPRESSED_FILE}"
echo "  Checksum: ${COMPRESSED_FILE}.sha256"
```

### Output Decompression and Parsing

```bash
#!/bin/bash
# scripts/parse_region_outputs.sh
# Extracts and parses compressed region outputs

set -euo pipefail

COMPRESSED_FILE="${1:-region_outputs.tar.gz}"
EXTRACT_DIR="${2:-./extracted_outputs}"

# Verify checksum
if [[ -f "${COMPRESSED_FILE}.sha256" ]]; then
  echo "Verifying checksum..."
  sha256sum -c "${COMPRESSED_FILE}.sha256"
fi

# Extract outputs
echo "Extracting outputs..."
mkdir -p "${EXTRACT_DIR}"
tar -xzvf "${COMPRESSED_FILE}" -C "${EXTRACT_DIR}"

# Parse and display summary
echo ""
echo "=== Region Output Summary ==="
jq -r '.regions[]' "${EXTRACT_DIR}/summary.json" | while read -r region; do
  echo ""
  echo "Region: ${region}"
  echo "---"
  
  if [[ -f "${EXTRACT_DIR}/${region}_outputs.json" ]]; then
    # Display key outputs
    jq -r 'to_entries[] | "  \(.key): \(.value.value // .value)"' \
      "${EXTRACT_DIR}/${region}_outputs.json" 2>/dev/null || \
      echo "  No outputs found"
  fi
done
```

### Usage Example

```bash
# Compress outputs after deployment
./scripts/compress_region_outputs.sh ./region_outputs bedrock_outputs.tar.gz

# Parse and review outputs
./scripts/parse_region_outputs.sh bedrock_outputs.tar.gz ./review

# Upload to S3 for archival
aws s3 cp bedrock_outputs.tar.gz s3://my-terraform-outputs/bedrock/
aws s3 cp bedrock_outputs.tar.gz.sha256 s3://my-terraform-outputs/bedrock/
```

## Troubleshooting

### Common Regional Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Model not available | Region doesn't support model | Check availability matrix; use fallback model |
| Cross-region inference fails | Network/IAM configuration | Verify VPC peering and IAM roles |
| High latency | Geographic distance | Deploy to region closer to users |
| Quota exceeded | Regional service limits | Request quota increase via AWS Support |

### Verifying Region Configuration

```bash
# Verify Bedrock service availability in a region
aws bedrock list-foundation-models \
  --region us-east-2 \
  --query 'modelSummaries[*].[modelId,modelName]' \
  --output table

# Check current quotas
aws service-quotas list-service-quotas \
  --service-code bedrock \
  --region us-east-2
```

## Related Documentation

- [Multi-Region Deployment Guide](./multi-region-deployment.md)
- [Cross-Region Inference Configuration](./cross-region-inference.md)
- [Guardrails Configuration](./guardrails.md)
- [Monitoring and Observability](./monitoring.md)