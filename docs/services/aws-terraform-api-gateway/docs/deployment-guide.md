# Deployment Guide

## Overview

This deployment guide provides comprehensive step-by-step instructions for deploying the `aws-terraform-api-gateway` Terraform module to AWS accounts. Whether you're setting up API Gateway account-level resources for the first time, expanding to new regions, or migrating from an existing `terraform-iam` configuration, this guide covers all deployment scenarios.

The `aws-terraform-api-gateway` module provisions AWS API Gateway account-level resources across multiple regions, including CloudWatch logging role setup and modular configurations for up to 8 AWS regions globally.

---

## First-Time Deployment

### Prerequisites

Before deploying the `aws-terraform-api-gateway` module for the first time, ensure you have the following prerequisites in place:

1. **Terraform Installation**: Terraform version 1.0.0 or later installed locally
2. **AWS CLI**: AWS CLI configured with appropriate credentials
3. **IAM Permissions**: Sufficient AWS IAM permissions to create:
   - IAM roles and policies
   - API Gateway account settings
   - CloudWatch log groups and resource policies
4. **Backend Configuration**: S3 bucket and DynamoDB table for Terraform state (recommended)

### Initial Setup Steps

#### Step 1: Clone and Configure the Module

Begin by cloning the repository and navigating to the module directory:

```bash
# Clone the repository
git clone https://github.com/your-org/aws-terraform-api-gateway.git
cd aws-terraform-api-gateway

# Review the module structure
tree -L 2
```

#### Step 2: Configure Backend State

Create or update your backend configuration file. This is critical for team collaboration and state management:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "api-gateway/account-level/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

#### Step 3: Configure Provider and Variables

Set up your AWS provider configuration for multi-region deployment:

```hcl
# providers.tf
provider "aws" {
  region = "us-east-1"
  alias  = "us_east_1"
}

provider "aws" {
  region = "us-west-2"
  alias  = "us_west_2"
}

provider "aws" {
  region = "eu-west-1"
  alias  = "eu_west_1"
}

# Add additional providers for each region you plan to deploy
```

Create your variables file:

```hcl
# terraform.tfvars
environment           = "production"
enable_cloudwatch_logs = true
log_retention_days    = 30

# Regions to deploy API Gateway account settings
enabled_regions = [
  "us-east-1",
  "us-west-2",
  "eu-west-1"
]

tags = {
  Project     = "api-gateway-infrastructure"
  ManagedBy   = "terraform"
  Environment = "production"
}
```

#### Step 4: Initialize and Plan

Execute the initial Terraform workflow:

```bash
# Initialize Terraform and download providers
terraform init

# Validate the configuration
terraform validate

# Generate and review the execution plan
terraform plan -out=tfplan

# Review the plan output carefully before proceeding
```

#### Step 5: Apply the Configuration

Once you've reviewed the plan and confirmed the resources to be created:

```bash
# Apply the Terraform plan
terraform apply tfplan

# Alternatively, apply directly with auto-approve (use with caution)
terraform apply -auto-approve
```

#### Step 6: Verify Deployment

After successful deployment, verify the resources were created correctly:

```bash
# List created resources
terraform state list

# Show specific resource details
terraform state show module.api_gateway_us_east_1.aws_api_gateway_account.main

# Verify via AWS CLI
aws apigateway get-account --region us-east-1
```

---

## Adding New Regions

### Expanding to Additional AWS Regions

The modular design of `aws-terraform-api-gateway` makes it straightforward to add new regions to your deployment.

#### Step 1: Add Provider Configuration

Add a new provider block for the target region:

```hcl
# providers.tf - Add new provider
provider "aws" {
  region = "ap-southeast-1"
  alias  = "ap_southeast_1"
}
```

#### Step 2: Update Region Configuration

Add the new region to your enabled regions list:

```hcl
# terraform.tfvars
enabled_regions = [
  "us-east-1",
  "us-west-2",
  "eu-west-1",
  "ap-southeast-1"  # New region added
]
```

#### Step 3: Add Module Instance

Create a new module instance for the region using the `api-gateway` submodule:

```hcl
# main.tf - Add new module instance
module "api_gateway_ap_southeast_1" {
  source = "./modules/api-gateway"
  
  providers = {
    aws = aws.ap_southeast_1
  }
  
  region                 = "ap-southeast-1"
  cloudwatch_role_arn    = module.iam_cloudwatch_role.role_arn
  enable_cloudwatch_logs = var.enable_cloudwatch_logs
  
  tags = var.tags
}
```

#### Step 4: Plan and Apply Changes

```bash
# Review changes for the new region
terraform plan -target=module.api_gateway_ap_southeast_1

# Apply only the new region (recommended for safety)
terraform apply -target=module.api_gateway_ap_southeast_1

# Or apply all changes
terraform apply
```

### Supported Regions Reference

The module supports the following 8 AWS regions:

| Region Code | Region Name | Notes |
|-------------|-------------|-------|
| us-east-1 | US East (N. Virginia) | Primary region |
| us-east-2 | US East (Ohio) | |
| us-west-1 | US West (N. California) | |
| us-west-2 | US West (Oregon) | |
| eu-west-1 | Europe (Ireland) | |
| eu-central-1 | Europe (Frankfurt) | |
| ap-southeast-1 | Asia Pacific (Singapore) | |
| ap-northeast-1 | Asia Pacific (Tokyo) | |

---

## Migration from terraform-iam

### Overview

If you're currently managing API Gateway account-level resources through a `terraform-iam` module or similar configuration, follow this migration guide to transition to `aws-terraform-api-gateway`.

### Pre-Migration Checklist

- [ ] Document current API Gateway account settings in each region
- [ ] Identify all CloudWatch log groups associated with API Gateway
- [ ] Export current Terraform state for reference
- [ ] Schedule maintenance window for the migration
- [ ] Notify stakeholders of potential API Gateway configuration changes

### Migration Steps

#### Step 1: Export Current State

```bash
# Export current state for backup
terraform state pull > terraform-iam-backup.tfstate

# List resources to be migrated
terraform state list | grep -E "api_gateway|apigateway"
```

#### Step 2: Import Existing Resources

Import existing API Gateway account settings into the new module:

```bash
# Import API Gateway account settings for each region
terraform import \
  module.api_gateway_us_east_1.aws_api_gateway_account.main \
  us-east-1

terraform import \
  module.api_gateway_us_west_2.aws_api_gateway_account.main \
  us-west-2

# Import CloudWatch IAM role if it exists
terraform import \
  module.cloudwatch_role.aws_iam_role.api_gateway_cloudwatch \
  api-gateway-cloudwatch-role
```

#### Step 3: Remove Resources from Old Module

After confirming successful import, remove resources from the old module:

```bash
# In the terraform-iam directory
terraform state rm aws_api_gateway_account.main
terraform state rm aws_iam_role.api_gateway_cloudwatch
```

#### Step 4: Verify Migration

```bash
# Verify no changes are needed (drift detection)
terraform plan

# Expected output should show no changes
# "No changes. Your infrastructure matches the configuration."
```

### Rollback Procedure

If migration issues occur, restore from backup:

```bash
# Restore previous state
terraform state push terraform-iam-backup.tfstate

# Verify restoration
terraform plan
```

---

## State Management

### State File Organization

Proper state management is crucial for the `aws-terraform-api-gateway` module, especially in multi-region deployments.

#### Recommended State Structure

```
s3://your-terraform-state-bucket/
├── api-gateway/
│   ├── account-level/
│   │   └── terraform.tfstate      # Account-level resources (IAM roles)
│   ├── us-east-1/
│   │   └── terraform.tfstate      # Region-specific resources
│   ├── us-west-2/
│   │   └── terraform.tfstate
│   └── eu-west-1/
│       └── terraform.tfstate
```

#### State Locking Configuration

Ensure state locking is properly configured to prevent concurrent modifications:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "api-gateway/account-level/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # Enable versioning for state file recovery
    # (Configure on S3 bucket, not here)
  }
}
```

#### State Operations Reference

```bash
# View current state
terraform state list

# Move resources between state files
terraform state mv \
  module.api_gateway.aws_api_gateway_account.main \
  module.api_gateway_v2.aws_api_gateway_account.main

# Remove resource from state (without destroying)
terraform state rm module.api_gateway_deprecated.aws_api_gateway_account.main

# Refresh state to match actual infrastructure
terraform refresh
```

---

## Deployment Order and Dependencies

### Resource Dependency Graph

Understanding the deployment order is critical for successful provisioning:

```
┌─────────────────────────────────────┐
│  1. IAM Role for CloudWatch Logs    │
│     (Account-level, single region)  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  2. IAM Role Policy Attachment      │
│     (CloudWatch Logs permissions)   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  3. API Gateway Account Settings    │
│     (Per-region configuration)      │
│     - Region 1 (us-east-1)         │
│     - Region 2 (us-west-2)         │
│     - Region N...                   │
└─────────────────────────────────────┘
```

### Deployment Commands with Dependencies

```bash
# Deploy IAM resources first
terraform apply -target=module.cloudwatch_role

# Deploy API Gateway account settings per region
terraform apply -target=module.api_gateway_us_east_1
terraform apply -target=module.api_gateway_us_west_2

# Or deploy everything in correct order
terraform apply
```

### Cross-Module Dependencies

When integrating with other modules, ensure proper dependency ordering:

```hcl
# Explicit dependency declaration
module "api_gateway_us_east_1" {
  source = "./modules/api-gateway"
  
  # Explicit dependency on IAM role
  depends_on = [module.cloudwatch_role]
  
  cloudwatch_role_arn = module.cloudwatch_role.role_arn
  # ... other configuration
}
```

---

## Troubleshooting Common Issues

### Issue 1: CloudWatch Role Already Exists

**Symptom**: Error message indicating the IAM role already exists

```
Error: Error creating IAM Role api-gateway-cloudwatch-role: EntityAlreadyExists
```

**Solution**:

```bash
# Import the existing role
terraform import module.cloudwatch_role.aws_iam_role.main api-gateway-cloudwatch-role

# Verify import and re-plan
terraform plan
```

### Issue 2: API Gateway Account Settings Conflict

**Symptom**: Error when applying API Gateway account settings

```
Error: Error updating API Gateway Account: ConflictException: CloudWatch Logs role ARN is already set
```

**Solution**:

```bash
# Check current account settings
aws apigateway get-account --region us-east-1

# Import existing settings
terraform import module.api_gateway_us_east_1.aws_api_gateway_account.main us-east-1

# Plan to verify state alignment
terraform plan
```

### Issue 3: State Lock Timeout

**Symptom**: Terraform hangs or times out acquiring state lock

```
Error: Error acquiring the state lock
```

**Solution**:

```bash
# Check for existing locks in DynamoDB
aws dynamodb scan --table-name terraform-state-lock

# Force unlock (use with extreme caution)
terraform force-unlock LOCK_ID

# Verify no other operations are running before force-unlock
```

### Issue 4: Provider Configuration Errors

**Symptom**: Provider alias not found or region mismatch

```
Error: Provider configuration not present
```

**Solution**:

Ensure all provider aliases are correctly defined and referenced:

```hcl
# Verify provider block exists
provider "aws" {
  region = "us-east-1"
  alias  = "us_east_1"  # Must match module reference
}

# Verify module uses correct provider
module "api_gateway_us_east_1" {
  source = "./modules/api-gateway"
  
  providers = {
    aws = aws.us_east_1  # Must match alias above
  }
}
```

### Issue 5: Insufficient Permissions

**Symptom**: Access denied errors during deployment

```
Error: Error creating IAM Role: AccessDenied
```

**Solution**:

Ensure the deploying IAM user/role has the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "logs:CreateLogGroup",
        "logs:PutResourcePolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

### Diagnostic Commands

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform-debug.log

# Run plan with detailed output
terraform plan -detailed-exitcode

# Validate configuration syntax
terraform validate

# Format check
terraform fmt -check -recursive
```

---

## Next Steps

After successfully deploying the `aws-terraform-api-gateway` module:

1. **Configure Monitoring**: Set up CloudWatch alarms for API Gateway metrics
2. **Enable Access Logging**: Configure access logging for individual API Gateways
3. **Review Security**: Audit IAM policies and API Gateway resource policies
4. **Document Changes**: Update runbooks and operational documentation

For additional support, refer to the module's README or open an issue in the repository.