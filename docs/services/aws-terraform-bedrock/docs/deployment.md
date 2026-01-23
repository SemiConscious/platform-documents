# Deployment Guide

## aws-terraform-bedrock

This comprehensive deployment guide provides step-by-step instructions for deploying the AWS Terraform Bedrock module across multiple environments. The module enables multi-region AWS Bedrock GenAI configuration, including application inference profiles, cross-region inference support, guardrails, and monitoring capabilities.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Workspace Configuration](#workspace-configuration)
3. [Enabling Bedrock Models (Console Steps)](#enabling-bedrock-models-console-steps)
4. [Terraform Initialization](#terraform-initialization)
5. [Planning and Applying](#planning-and-applying)
6. [Validation Steps](#validation-steps)
7. [Troubleshooting Common Issues](#troubleshooting-common-issues)
8. [Updating Existing Deployments](#updating-existing-deployments)

---

## Prerequisites

Before deploying the aws-terraform-bedrock module, ensure you have the following prerequisites in place:

### Required Tools

| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| Terraform | >= 1.5.0 | Infrastructure provisioning |
| AWS CLI | >= 2.13.0 | AWS authentication and operations |
| Git | >= 2.30.0 | Repository management |

### AWS Account Requirements

1. **AWS Account Access**: You need administrative access or an IAM role with sufficient permissions to:
   - Create and manage AWS Bedrock resources
   - Configure CloudWatch alarms and dashboards
   - Create IAM roles and policies
   - Deploy resources across multiple regions

2. **Service Quotas**: Verify your AWS account has adequate service quotas for Bedrock in your target regions:

```bash
# Check Bedrock service quotas for a specific region
aws service-quotas list-service-quotas \
    --service-code bedrock \
    --region us-east-1
```

3. **IAM Permissions**: Create or ensure your deployment role has the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*",
                "cloudwatch:*",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Network Requirements

- Outbound internet access for Terraform provider downloads
- Access to AWS API endpoints for Bedrock service
- VPC endpoints (optional but recommended for production)

### Authentication Setup

Configure AWS credentials using one of the following methods:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Option 3: AWS SSO (recommended for enterprise)
aws sso login --profile your-profile-name
```

---

## Workspace Configuration

### Directory Structure

Set up your workspace with the following recommended structure:

```
aws-terraform-bedrock/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   └── ... (same structure)
│   └── prod/
│       └── ... (same structure)
├── modules/
│   └── bedrock/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── guardrails.tf
│       ├── monitoring.tf
│       └── inference-profiles.tf
└── README.md
```

### Backend Configuration

Configure remote state storage for team collaboration:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "bedrock/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Environment-Specific Variables

Create a `terraform.tfvars` file for each environment:

```hcl
# environments/dev/terraform.tfvars

# General Configuration
environment = "dev"
project     = "genai-platform"

# Region Configuration
primary_region = "us-east-1"
secondary_regions = ["us-west-2", "eu-west-1"]

# Bedrock Model Configuration
enabled_models = [
  "anthropic.claude-3-sonnet-20240229-v1:0",
  "anthropic.claude-3-haiku-20240307-v1:0",
  "amazon.titan-embed-text-v1"
]

# Cross-Region Inference
enable_cross_region_inference = true

# Guardrails Configuration
guardrails_enabled = true
content_filters = {
  hate_speech       = "HIGH"
  insults           = "MEDIUM"
  sexual_content    = "HIGH"
  violence          = "MEDIUM"
}

# Monitoring Configuration
enable_cloudwatch_monitoring = true
alarm_notification_email     = "team@example.com"

# Tags
tags = {
  Environment = "dev"
  ManagedBy   = "terraform"
  Team        = "ai-platform"
}
```

---

## Enabling Bedrock Models (Console Steps)

Before Terraform can provision Bedrock resources, you must enable model access through the AWS Console. This is a one-time setup per AWS account and region.

### Step 1: Navigate to AWS Bedrock Console

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to **Amazon Bedrock** service
3. Select your target region from the region selector

### Step 2: Request Model Access

1. In the left navigation pane, click **Model access**
2. Click **Manage model access** button
3. Select the models you need for your deployment:

   **Recommended Models:**
   - ✅ Anthropic Claude 3 Sonnet
   - ✅ Anthropic Claude 3 Haiku
   - ✅ Amazon Titan Text Embeddings
   - ✅ Amazon Titan Text Express (optional)

4. Click **Request model access**
5. Accept the End User License Agreement (EULA) for each model provider

### Step 3: Verify Access Status

Wait for model access approval (typically instant for Amazon models, may take up to 24 hours for third-party models):

```bash
# Verify model access via CLI
aws bedrock list-foundation-models \
    --region us-east-1 \
    --query 'modelSummaries[?modelLifecycle.status==`ACTIVE`].modelId'
```

### Step 4: Repeat for All Target Regions

**Important:** Model access must be enabled in each region where you plan to deploy. Repeat steps 1-3 for:
- Primary region (e.g., us-east-1)
- All secondary regions for cross-region inference

---

## Terraform Initialization

### Step 1: Clone and Navigate to Environment

```bash
# Clone the repository (if using version control)
git clone https://github.com/your-org/aws-terraform-bedrock.git
cd aws-terraform-bedrock/environments/dev
```

### Step 2: Initialize Terraform

```bash
# Initialize Terraform with backend configuration
terraform init

# Expected output:
# Initializing the backend...
# Initializing provider plugins...
# - Finding hashicorp/aws versions matching ">= 5.0.0"...
# - Installing hashicorp/aws v5.x.x...
# Terraform has been successfully initialized!
```

### Step 3: Initialize with Upgrade (for existing deployments)

```bash
# Upgrade providers and modules to latest compatible versions
terraform init -upgrade
```

### Step 4: Validate Provider Configuration

```bash
# Verify provider configuration
terraform providers

# Expected output showing AWS provider for multiple regions
```

### Multi-Region Provider Configuration

Ensure your `main.tf` includes provider aliases for multi-region deployment:

```hcl
# main.tf

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
  
  default_tags {
    tags = var.tags
  }
}

# Secondary region provider (US West)
provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
  
  default_tags {
    tags = var.tags
  }
}

# Secondary region provider (EU)
provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
  
  default_tags {
    tags = var.tags
  }
}
```

---

## Planning and Applying

### Step 1: Generate and Review Plan

```bash
# Generate execution plan
terraform plan -out=tfplan

# Review the plan output carefully
# Look for:
# - Resources to be created
# - Resources to be modified
# - Resources to be destroyed
```

### Step 2: Plan Output Analysis

Example plan output to expect:

```
Terraform will perform the following actions:

  # aws_bedrock_guardrail.main will be created
  + resource "aws_bedrock_guardrail" "main" {
      + blocked_input_messaging  = "I cannot process this request."
      + blocked_output_messaging = "I cannot provide this response."
      + id                       = (known after apply)
      + name                     = "genai-platform-dev-guardrail"
      ...
    }

  # aws_cloudwatch_metric_alarm.bedrock_invocations will be created
  + resource "aws_cloudwatch_metric_alarm" "bedrock_invocations" {
      + alarm_name          = "bedrock-high-invocations-dev"
      + comparison_operator = "GreaterThanThreshold"
      ...
    }

Plan: 12 to add, 0 to change, 0 to destroy.
```

### Step 3: Apply Configuration

```bash
# Apply with the saved plan
terraform apply tfplan

# Or apply with auto-approve (use with caution)
terraform apply -auto-approve
```

### Step 4: Environment-Specific Deployment

For different environments, use workspace or directory-based isolation:

```bash
# Using Terraform Workspaces
terraform workspace new staging
terraform workspace select staging
terraform plan -var-file="staging.tfvars"
terraform apply -var-file="staging.tfvars"

# Or using directory-based approach
cd ../staging
terraform init
terraform plan
terraform apply
```

### Step 5: Multi-Region Deployment Sequence

For cross-region deployments, follow this sequence:

```bash
# 1. Deploy primary region first
terraform apply -target=module.bedrock_primary

# 2. Deploy secondary regions
terraform apply -target=module.bedrock_secondary

# 3. Deploy cross-region inference profiles
terraform apply -target=module.inference_profiles

# 4. Complete deployment
terraform apply
```

---

## Validation Steps

### Step 1: Verify Terraform State

```bash
# List all managed resources
terraform state list

# Expected resources:
# aws_bedrock_guardrail.main
# aws_cloudwatch_metric_alarm.bedrock_invocations
# aws_iam_role.bedrock_execution_role
# ...
```

### Step 2: Verify Bedrock Resources via AWS CLI

```bash
# List guardrails
aws bedrock list-guardrails --region us-east-1

# Get guardrail details
aws bedrock get-guardrail \
    --guardrail-identifier "your-guardrail-id" \
    --region us-east-1

# List inference profiles
aws bedrock list-inference-profiles --region us-east-1
```

### Step 3: Test Model Invocation

```bash
# Test Claude model invocation
aws bedrock-runtime invoke-model \
    --model-id "anthropic.claude-3-haiku-20240307-v1:0" \
    --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":256,"messages":[{"role":"user","content":"Hello, Claude!"}]}' \
    --content-type "application/json" \
    --accept "application/json" \
    --region us-east-1 \
    output.json

# View response
cat output.json | jq .
```

### Step 4: Verify CloudWatch Monitoring

```bash
# Check CloudWatch alarms
aws cloudwatch describe-alarms \
    --alarm-name-prefix "bedrock-" \
    --region us-east-1

# Verify CloudWatch dashboard exists
aws cloudwatch list-dashboards \
    --dashboard-name-prefix "bedrock" \
    --region us-east-1
```

### Step 5: Cross-Region Validation

```bash
# Validate resources in each region
for region in us-east-1 us-west-2 eu-west-1; do
    echo "Checking region: $region"
    aws bedrock list-guardrails --region $region --query 'guardrails[].name'
done
```

### Step 6: Automated Validation Script

Create a validation script for CI/CD pipelines:

```bash
#!/bin/bash
# validate-deployment.sh

set -e

REGIONS=("us-east-1" "us-west-2" "eu-west-1")
EXPECTED_GUARDRAIL="genai-platform-dev-guardrail"

echo "Starting deployment validation..."

for region in "${REGIONS[@]}"; do
    echo "Validating region: $region"
    
    # Check guardrail exists
    guardrail=$(aws bedrock list-guardrails \
        --region $region \
        --query "guardrails[?name=='$EXPECTED_GUARDRAIL'].guardrailId" \
        --output text)
    
    if [ -z "$guardrail" ]; then
        echo "ERROR: Guardrail not found in $region"
        exit 1
    fi
    
    echo "✓ Guardrail validated in $region"
done

echo "All validations passed!"
```

---

## Troubleshooting Common Issues

### Issue 1: Model Access Denied

**Symptom:**
```
Error: AccessDeniedException: You don't have access to the model with the specified model ID.
```

**Solution:**
1. Verify model access is enabled in the AWS Console
2. Check the model ID is correct
3. Ensure the IAM role has `bedrock:InvokeModel` permission

```bash
# Verify model access
aws bedrock get-foundation-model-availability \
    --model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
    --region us-east-1
```

### Issue 2: Guardrail Creation Fails

**Symptom:**
```
Error: ValidationException: Guardrail name already exists
```

**Solution:**
```bash
# List existing guardrails
aws bedrock list-guardrails --region us-east-1

# Import existing guardrail into state (if needed)
terraform import aws_bedrock_guardrail.main "guardrail-id"
```

### Issue 3: Cross-Region Inference Profile Errors

**Symptom:**
```
Error: ResourceNotFoundException: The specified inference profile does not exist
```

**Solution:**
1. Ensure models are enabled in all target regions
2. Verify cross-region inference is supported for the model
3. Check IAM permissions include cross-region access

### Issue 4: State Lock Issues

**Symptom:**
```
Error: Error acquiring the state lock
```

**Solution:**
```bash
# Check current lock status
aws dynamodb get-item \
    --table-name terraform-state-lock \
    --key '{"LockID": {"S": "your-bucket/bedrock/terraform.tfstate"}}'

# Force unlock (use with extreme caution)
terraform force-unlock LOCK_ID
```

### Issue 5: Provider Authentication Errors

**Symptom:**
```
Error: error configuring Terraform AWS Provider: no valid credential sources
```

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Refresh SSO credentials if using SSO
aws sso login --profile your-profile

# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_DEFAULT_REGION
```

### Issue 6: CloudWatch Alarm Creation Failures

**Symptom:**
```
Error: InvalidParameterValue: The value for parameter MetricName is not valid
```

**Solution:**
Verify the Bedrock metrics namespace and metric names:

```bash
# List available Bedrock metrics
aws cloudwatch list-metrics \
    --namespace "AWS/Bedrock" \
    --region us-east-1
```

---

## Updating Existing Deployments

### Pre-Update Checklist

- [ ] Review current state: `terraform state list`
- [ ] Backup state file: `terraform state pull > backup.tfstate`
- [ ] Review planned changes thoroughly
- [ ] Notify stakeholders of potential downtime
- [ ] Schedule maintenance window (for production)

### Step 1: Pull Latest Configuration

```bash
# Pull latest changes from version control
git pull origin main

# Review what changed
git diff HEAD~1
```

### Step 2: Update Terraform Providers

```bash
# Upgrade providers to latest compatible versions
terraform init -upgrade

# Lock provider versions
terraform providers lock -platform=linux_amd64 -platform=darwin_amd64
```

### Step 3: Plan and Review Changes

```bash
# Generate detailed plan
terraform plan -detailed-exitcode -out=update.tfplan

# Exit codes:
# 0 = No changes
# 1 = Error
# 2 = Changes present
```

### Step 4: Apply Updates with Minimal Disruption

For guardrail updates (non-breaking):
```bash
terraform apply -target=aws_bedrock_guardrail.main update.tfplan
```

For monitoring updates:
```bash
terraform apply -target=module.monitoring update.tfplan
```

### Step 5: Rolling Updates Across Regions

For multi-region deployments, update one region at a time:

```bash
# Update primary region
terraform apply -target=module.bedrock["us-east-1"]

# Verify primary region
./validate-deployment.sh us-east-1

# Update secondary regions
terraform apply -target=module.bedrock["us-west-2"]
terraform apply -target=module.bedrock["eu-west-1"]
```

### Step 6: Rollback Procedure

If issues arise, rollback using state manipulation:

```bash
# Restore from backup state
terraform state push backup.tfstate

# Or revert to previous configuration
git checkout HEAD~1 -- .
terraform apply
```

### Version Upgrade Considerations

When upgrading major versions of the module:

1. **Review CHANGELOG** for breaking changes
2. **Test in non-production** environment first
3. **Update variable definitions** as needed
4. **Migrate state** if resource addresses changed:

```bash
# Move resources if renamed
terraform state mv old_resource_name new_resource_name

# Remove deprecated resources
terraform state rm deprecated_resource
```

### Post-Update Validation

```bash
# Run full validation suite
./validate-deployment.sh

# Verify Terraform output values
terraform output

# Check resource health
terraform plan # Should show "No changes"
```

---

## Support and Resources

- **AWS Bedrock Documentation**: [AWS Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- **Terraform AWS Provider**: [Terraform Registry](https://registry.terraform.io/providers/hashicorp/aws/latest)
- **Internal Support**: Contact the AI Platform team for assistance

---

*Last Updated: 2024*
*Module Version: 1.0.0*