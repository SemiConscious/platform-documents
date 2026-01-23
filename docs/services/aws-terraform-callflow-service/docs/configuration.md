# Configuration Reference

## AWS Terraform Callflow Service

This document provides a comprehensive configuration reference for the `aws-terraform-callflow-service`, a Terraform-based infrastructure service designed to provision and manage call flow resources on Amazon Web Services. This service handles the deployment of telephony infrastructure including Amazon Connect, Lambda functions, API Gateway endpoints, DynamoDB tables, and associated networking components required for a complete call center solution.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Approach](#configuration-approach)
3. [Required Variables](#required-variables)
4. [Optional Variables](#optional-variables)
5. [Module Outputs](#module-outputs)
6. [Provider Configuration](#provider-configuration)
7. [Backend Configuration](#backend-configuration)
8. [Environment-Specific Settings](#environment-specific-settings)
9. [Example Configurations](#example-configurations)
10. [Security Considerations](#security-considerations)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The `aws-terraform-callflow-service` utilizes Terraform to declaratively manage AWS infrastructure for call flow operations. The configuration system follows a layered approach where base configurations can be overridden by environment-specific values, allowing for consistent infrastructure patterns across development, staging, and production environments while accommodating environment-specific requirements.

### Architecture Components

- **Amazon Connect**: Contact center instance and call flow configurations
- **AWS Lambda**: Serverless functions for call processing logic
- **Amazon API Gateway**: RESTful API endpoints for external integrations
- **Amazon DynamoDB**: NoSQL database for call metadata and routing rules
- **Amazon S3**: Storage for call recordings and configuration files
- **Amazon CloudWatch**: Monitoring, logging, and alerting
- **AWS IAM**: Identity and access management policies
- **Amazon VPC**: Network isolation and security groups

---

## Configuration Approach

This service employs a multi-layered configuration strategy:

1. **Terraform Variables (`.tfvars` files)**: Primary configuration mechanism for infrastructure parameters
2. **Environment Variables**: Runtime configuration and sensitive credential management
3. **Backend Configuration**: State management and locking configuration
4. **Module-Level Variables**: Component-specific configurations passed to child modules

### Configuration File Hierarchy

```
terraform/
├── variables.tf           # Variable declarations
├── terraform.tfvars       # Default values (base configuration)
├── environments/
│   ├── dev.tfvars         # Development overrides
│   ├── staging.tfvars     # Staging overrides
│   └── prod.tfvars        # Production overrides
├── backend/
│   ├── dev.hcl            # Dev backend configuration
│   ├── staging.hcl        # Staging backend configuration
│   └── prod.hcl           # Production backend configuration
└── modules/
    ├── connect/
    ├── lambda/
    ├── api-gateway/
    └── dynamodb/
```

---

## Required Variables

The following variables must be configured for the service to deploy successfully. Missing any of these will cause Terraform to fail during the planning phase.

| Variable Name | Type | Description | Format | Example Value |
|--------------|------|-------------|--------|---------------|
| `aws_region` | string | AWS region where resources will be deployed | AWS region code | `us-east-1` |
| `environment` | string | Deployment environment identifier | Alphanumeric, lowercase | `production` |
| `project_name` | string | Project identifier used in resource naming | Alphanumeric with hyphens | `callflow-service` |
| `vpc_id` | string | VPC ID for network resource deployment | AWS VPC ID format | `vpc-0abc123def456789` |
| `subnet_ids` | list(string) | List of subnet IDs for Lambda and other resources | List of AWS subnet IDs | `["subnet-abc123", "subnet-def456"]` |
| `connect_instance_id` | string | Amazon Connect instance identifier | Connect instance ID | `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee` |
| `contact_flow_name` | string | Name of the primary contact flow | String, max 256 chars | `MainCallFlow` |
| `admin_email` | string | Administrator email for notifications | Valid email address | `admin@company.com` |
| `domain_name` | string | Domain name for API Gateway custom domain | FQDN | `api.callflow.company.com` |
| `certificate_arn` | string | ACM certificate ARN for HTTPS | AWS ACM ARN | `arn:aws:acm:us-east-1:123456789:certificate/abc-123` |
| `dynamodb_table_name` | string | Name for the DynamoDB routing table | Alphanumeric with hyphens | `callflow-routing-rules` |
| `s3_recordings_bucket` | string | S3 bucket name for call recordings | Valid S3 bucket name | `company-callflow-recordings-prod` |

### Required Environment Variables

These environment variables must be set in your shell or CI/CD environment before running Terraform commands:

| Variable Name | Description | Type | Format | Example Value |
|--------------|-------------|------|--------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key for authentication | string | 20-character alphanumeric | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key for authentication | string | 40-character string | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_DEFAULT_REGION` | Default AWS region (fallback) | string | AWS region code | `us-east-1` |
| `TF_VAR_db_password` | Database password for RDS (if used) | string | Complex password | `MyS3cur3P@ssw0rd!` |
| `TF_VAR_api_key` | API key for external integrations | string | UUID or token | `sk_live_abc123def456` |
| `TF_VAR_twilio_auth_token` | Twilio authentication token (if integrated) | string | 32-character hex | `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6` |

---

## Optional Variables

These variables have sensible defaults but can be customized based on your requirements.

### General Configuration

| Variable Name | Type | Default | Description | Example Value |
|--------------|------|---------|-------------|---------------|
| `tags` | map(string) | `{}` | Additional resource tags | `{Owner = "DevOps", CostCenter = "IT-123"}` |
| `enable_deletion_protection` | bool | `true` | Prevent accidental resource deletion | `false` |
| `log_retention_days` | number | `90` | CloudWatch log retention period in days | `365` |
| `enable_xray_tracing` | bool | `true` | Enable AWS X-Ray distributed tracing | `false` |
| `kms_key_arn` | string | `null` | Custom KMS key for encryption (uses AWS managed if null) | `arn:aws:kms:us-east-1:123456789:key/abc-123` |

### Lambda Configuration

| Variable Name | Type | Default | Description | Example Value |
|--------------|------|---------|-------------|---------------|
| `lambda_runtime` | string | `python3.11` | Lambda function runtime | `nodejs18.x` |
| `lambda_memory_size` | number | `256` | Memory allocation in MB | `512` |
| `lambda_timeout` | number | `30` | Function timeout in seconds | `60` |
| `lambda_reserved_concurrency` | number | `-1` | Reserved concurrent executions (-1 for unreserved) | `100` |
| `lambda_provisioned_concurrency` | number | `0` | Provisioned concurrency for reduced cold starts | `5` |
| `lambda_layers` | list(string) | `[]` | Additional Lambda layer ARNs | `["arn:aws:lambda:us-east-1:123456789:layer:my-layer:1"]` |
| `lambda_environment_variables` | map(string) | `{}` | Additional environment variables for Lambda | `{LOG_LEVEL = "DEBUG"}` |

### API Gateway Configuration

| Variable Name | Type | Default | Description | Example Value |
|--------------|------|---------|-------------|---------------|
| `api_gateway_stage_name` | string | `v1` | API Gateway deployment stage name | `v2` |
| `api_throttling_rate_limit` | number | `1000` | Requests per second limit | `5000` |
| `api_throttling_burst_limit` | number | `2000` | Maximum concurrent requests | `10000` |
| `enable_api_caching` | bool | `false` | Enable API Gateway response caching | `true` |
| `api_cache_ttl` | number | `300` | Cache time-to-live in seconds | `600` |
| `api_cache_size` | string | `0.5` | Cache cluster size in GB | `1.6` |
| `enable_waf` | bool | `true` | Enable AWS WAF protection | `true` |
| `cors_allowed_origins` | list(string) | `["*"]` | CORS allowed origins | `["https://app.company.com"]` |
| `api_key_required` | bool | `true` | Require API key for requests | `false` |

### DynamoDB Configuration

| Variable Name | Type | Default | Description | Example Value |
|--------------|------|---------|-------------|---------------|
| `dynamodb_billing_mode` | string | `PAY_PER_REQUEST` | DynamoDB billing mode | `PROVISIONED` |
| `dynamodb_read_capacity` | number | `5` | Provisioned read capacity units | `100` |
| `dynamodb_write_capacity` | number | `5` | Provisioned write capacity units | `50` |
| `dynamodb_enable_autoscaling` | bool | `true` | Enable DynamoDB auto-scaling | `false` |
| `dynamodb_autoscale_min_read` | number | `5` | Minimum read capacity for auto-scaling | `10` |
| `dynamodb_autoscale_max_read` | number | `100` | Maximum read capacity for auto-scaling | `1000` |
| `dynamodb_autoscale_min_write` | number | `5` | Minimum write capacity for auto-scaling | `10` |
| `dynamodb_autoscale_max_write` | number | `100` | Maximum write capacity for auto-scaling | `500` |
| `dynamodb_enable_point_in_time_recovery` | bool | `true` | Enable point-in-time recovery | `true` |
| `dynamodb_enable_streams` | bool | `false` | Enable DynamoDB Streams | `true` |
| `dynamodb_stream_view_type` | string | `NEW_AND_OLD_IMAGES` | Stream view type | `KEYS_ONLY` |

### Amazon Connect Configuration

| Variable Name | Type | Default | Description | Example Value |
|--------------|------|---------|-------------|---------------|
| `connect_hours_of_operation` | string | `24x7` | Hours of operation template | `business_hours` |
| `connect_queue_max_contacts` | number | `100` | Maximum contacts in queue | `500` |
| `connect_queue_outbound_caller_id` | string | `""` | Outbound caller ID number | `+15551234567` |
| `connect_recording_enabled` | bool | `true` | Enable call recording | `true` |
| `connect_recording_storage_type` | string | `S3` | Recording storage type | `KINESIS_VIDEO_STREAM` |
| `connect_enable_contact_lens` | bool | `false` | Enable Contact Lens analytics | `true` |
| `connect_enable_voiceid` | bool | `false` | Enable Voice ID authentication | `true` |

### Monitoring and Alerting

| Variable Name | Type | Default | Description | Example Value |
|--------------|------|---------|-------------|---------------|
| `enable_cloudwatch_alarms` | bool | `true` | Create CloudWatch alarms | `true` |
| `alarm_sns_topic_arn` | string | `""` | SNS topic ARN for alarm notifications | `arn:aws:sns:us-east-1:123456789:alerts` |
| `lambda_error_threshold` | number | `5` | Lambda error count threshold for alarm | `10` |
| `api_5xx_error_threshold` | number | `10` | API Gateway 5xx error threshold | `25` |
| `api_latency_threshold` | number | `3000` | API latency threshold in ms | `5000` |
| `dynamodb_throttle_threshold` | number | `1` | DynamoDB throttle event threshold | `5` |
| `enable_dashboard` | bool | `true` | Create CloudWatch dashboard | `true` |

---

## Module Outputs

The following outputs are exposed by this Terraform configuration and can be used by other modules or external systems.

| Output Name | Type | Description | Example Value |
|------------|------|-------------|---------------|
| `api_gateway_url` | string | Base URL for the API Gateway endpoint | `https://abc123.execute-api.us-east-1.amazonaws.com/v1` |
| `api_gateway_id` | string | API Gateway REST API ID | `abc123def4` |
| `api_gateway_stage_arn` | string | ARN of the deployed API stage | `arn:aws:apigateway:us-east-1::/restapis/abc123/stages/v1` |
| `lambda_function_arns` | map(string) | Map of Lambda function names to ARNs | `{processor = "arn:aws:lambda:...", router = "arn:aws:lambda:..."}` |
| `lambda_function_names` | list(string) | List of created Lambda function names | `["callflow-processor", "callflow-router"]` |
| `dynamodb_table_arn` | string | ARN of the DynamoDB routing table | `arn:aws:dynamodb:us-east-1:123456789:table/callflow-routing` |
| `dynamodb_table_name` | string | Name of the DynamoDB table | `callflow-routing-rules-prod` |
| `dynamodb_stream_arn` | string | ARN of DynamoDB stream (if enabled) | `arn:aws:dynamodb:us-east-1:123456789:table/callflow/stream/...` |
| `s3_bucket_arn` | string | ARN of the recordings S3 bucket | `arn:aws:s3:::company-callflow-recordings-prod` |
| `s3_bucket_name` | string | Name of the S3 bucket | `company-callflow-recordings-prod` |
| `connect_instance_arn` | string | ARN of the Amazon Connect instance | `arn:aws:connect:us-east-1:123456789:instance/abc-123` |
| `connect_contact_flow_id` | string | ID of the created contact flow | `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee` |
| `cloudwatch_log_groups` | map(string) | Map of component names to log group names | `{lambda = "/aws/lambda/callflow", api = "/aws/api-gateway/callflow"}` |
| `iam_role_arns` | map(string) | Map of IAM role names to ARNs | `{lambda_exec = "arn:aws:iam::..."}` |
| `kms_key_arn` | string | ARN of the KMS key used for encryption | `arn:aws:kms:us-east-1:123456789:key/abc-123` |
| `vpc_security_group_ids` | list(string) | Security group IDs created by this module | `["sg-abc123", "sg-def456"]` |

---

## Provider Configuration

### AWS Provider

The AWS provider configuration requires proper setup for authentication and regional deployment.

```hcl
# providers.tf

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "aws-terraform-callflow-service"
    }
  }

  # Assume role configuration for cross-account deployments
  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "TerraformCallflowDeployment"
    external_id  = var.assume_role_external_id
  }
}

# Secondary provider for us-east-1 (required for CloudFront certificates)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
```

### Provider Configuration Variables

| Variable Name | Type | Default | Required | Description |
|--------------|------|---------|----------|-------------|
| `assume_role_arn` | string | `null` | No | IAM role ARN to assume for deployment |
| `assume_role_external_id` | string | `null` | No | External ID for assume role |
| `provider_max_retries` | number | `3` | No | Maximum API retry attempts |

---

## Backend Configuration

Terraform state should be stored remotely for team collaboration and state locking. This service uses S3 with DynamoDB for state management.

### Backend Configuration Files

**backend/dev.hcl**
```hcl
bucket         = "company-terraform-state-dev"
key            = "callflow-service/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-locks-dev"
encrypt        = true
kms_key_id     = "alias/terraform-state-key-dev"
```

**backend/staging.hcl**
```hcl
bucket         = "company-terraform-state-staging"
key            = "callflow-service/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-locks-staging"
encrypt        = true
kms_key_id     = "alias/terraform-state-key-staging"
```

**backend/prod.hcl**
```hcl
bucket         = "company-terraform-state-prod"
key            = "callflow-service/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-locks-prod"
encrypt        = true
kms_key_id     = "alias/terraform-state-key-prod"
```

### Initializing with Backend

```bash
# Initialize for development
terraform init -backend-config=backend/dev.hcl

# Initialize for staging
terraform init -backend-config=backend/staging.hcl

# Initialize for production
terraform init -backend-config=backend/prod.hcl
```

---

## Environment-Specific Settings

### Development Environment

**environments/dev.tfvars**
```hcl
# General Configuration
environment    = "dev"
aws_region     = "us-east-1"
project_name   = "callflow-service"

# Network Configuration
vpc_id     = "vpc-dev123456789"
subnet_ids = ["subnet-dev1a", "subnet-dev1b"]

# Amazon Connect
connect_instance_id = "dev-connect-instance-id"
contact_flow_name   = "DevCallFlow"

# Domain Configuration
domain_name     = "api-dev.callflow.company.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/dev-cert"

# Storage
dynamodb_table_name  = "callflow-routing-rules-dev"
s3_recordings_bucket = "company-callflow-recordings-dev"

# Admin
admin_email = "dev-team@company.com"

# Lambda Settings (reduced for cost savings)
lambda_memory_size            = 128
lambda_timeout                = 30
lambda_reserved_concurrency   = -1
lambda_provisioned_concurrency = 0

# API Gateway Settings
api_gateway_stage_name    = "dev"
api_throttling_rate_limit = 100
api_throttling_burst_limit = 200
enable_api_caching        = false
cors_allowed_origins      = ["*"]

# DynamoDB Settings
dynamodb_billing_mode                = "PAY_PER_REQUEST"
dynamodb_enable_autoscaling          = false
dynamodb_enable_point_in_time_recovery = false

# Monitoring (reduced for dev)
log_retention_days       = 7
enable_cloudwatch_alarms = false
enable_dashboard         = false

# Security
enable_deletion_protection = false
enable_waf                 = false

# Additional Tags
tags = {
  Owner       = "Development Team"
  CostCenter  = "DEV-001"
  AutoShutdown = "true"
}
```

### Staging Environment

**environments/staging.tfvars**
```hcl
# General Configuration
environment    = "staging"
aws_region     = "us-east-1"
project_name   = "callflow-service"

# Network Configuration
vpc_id     = "vpc-staging123456"
subnet_ids = ["subnet-stg1a", "subnet-stg1b", "subnet-stg1c"]

# Amazon Connect
connect_instance_id = "staging-connect-instance-id"
contact_flow_name   = "StagingCallFlow"

# Domain Configuration
domain_name     = "api-staging.callflow.company.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/staging-cert"

# Storage
dynamodb_table_name  = "callflow-routing-rules-staging"
s3_recordings_bucket = "company-callflow-recordings-staging"

# Admin
admin_email = "staging-alerts@company.com"

# Lambda Settings (production-like for testing)
lambda_memory_size            = 256
lambda_timeout                = 30
lambda_reserved_concurrency   = 50
lambda_provisioned_concurrency = 2

# API Gateway Settings
api_gateway_stage_name    = "staging"
api_throttling_rate_limit = 500
api_throttling_burst_limit = 1000
enable_api_caching        = true
api_cache_ttl             = 300
cors_allowed_origins      = ["https://staging.company.com"]

# DynamoDB Settings
dynamodb_billing_mode                  = "PROVISIONED"
dynamodb_read_capacity                 = 10
dynamodb_write_capacity                = 10
dynamodb_enable_autoscaling            = true
dynamodb_autoscale_min_read            = 5
dynamodb_autoscale_max_read            = 50
dynamodb_autoscale_min_write           = 5
dynamodb_autoscale_max_write           = 25
dynamodb_enable_point_in_time_recovery = true

# Monitoring
log_retention_days       = 30
enable_cloudwatch_alarms = true
alarm_sns_topic_arn      = "arn:aws:sns:us-east-1:123456789:staging-alerts"
enable_dashboard         = true

# Security
enable_deletion_protection = true
enable_waf                 = true

# Additional Tags
tags = {
  Owner      = "QA Team"
  CostCenter = "QA-002"
}
```

### Production Environment

**environments/prod.tfvars**
```hcl
# General Configuration
environment    = "prod"
aws_region     = "us-east-1"
project_name   = "callflow-service"

# Network Configuration
vpc_id     = "vpc-prod123456789"
subnet_ids = ["subnet-prod1a", "subnet-prod1b", "subnet-prod1c"]

# Amazon Connect
connect_instance_id         = "prod-connect-instance-id"
contact_flow_name           = "ProductionCallFlow"
connect_queue_max_contacts  = 500
connect_recording_enabled   = true
connect_enable_contact_lens = true
connect_enable_voiceid      = true

# Domain Configuration
domain_name     = "api.callflow.company.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/prod-cert"

# Storage
dynamodb_table_name  = "callflow-routing-rules-prod"
s3_recordings_bucket = "company-callflow-recordings-prod"

# Admin
admin_email = "ops-alerts@company.com"

# Lambda Settings (optimized for production)
lambda_memory_size             = 512
lambda_timeout                 = 60
lambda_reserved_concurrency    = 200
lambda_provisioned_concurrency = 10

# API Gateway Settings
api_gateway_stage_name     = "v1"
api_throttling_rate_limit  = 5000
api_throttling_burst_limit = 10000
enable_api_caching         = true
api_cache_ttl              = 300
api_cache_size             = "1.6"
api_key_required           = true
cors_allowed_origins       = ["https://app.company.com", "https://admin.company.com"]

# DynamoDB Settings
dynamodb_billing_mode                  = "PROVISIONED"
dynamodb_read_capacity                 = 100
dynamodb_write_capacity                = 50
dynamodb_enable_autoscaling            = true
dynamodb_autoscale_min_read            = 50
dynamodb_autoscale_max_read            = 1000
dynamodb_autoscale_min_write           = 25
dynamodb_autoscale_max_write           = 500
dynamodb_enable_point_in_time_recovery = true
dynamodb_enable_streams                = true
dynamodb_stream_view_type              = "NEW_AND_OLD_IMAGES"

# Monitoring (comprehensive for production)
log_retention_days         = 365
enable_cloudwatch_alarms   = true
alarm_sns_topic_arn        = "arn:aws:sns:us-east-1:123456789:prod-critical-alerts"
lambda_error_threshold     = 5
api_5xx_error_threshold    = 10
api_latency_threshold      = 2000
dynamodb_throttle_threshold = 1
enable_dashboard           = true
enable_xray_tracing        = true

# Security
enable_deletion_protection = true
enable_waf                 = true
kms_key_arn               = "arn:aws:kms:us-east-1:123456789:key/prod-key-id"

# Additional Tags
tags = {
  Owner          = "Platform Team"
  CostCenter     = "PROD-003"
  Compliance     = "SOC2"
  DataClass      = "Confidential"
  BackupSchedule = "daily"
}
```

---

## Example Configurations

### Complete .env File Example

```bash
# AWS Credentials
# WARNING: Never commit this file to version control
# Use AWS IAM roles or instance profiles in production

# AWS Authentication
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-east-1"

# Optional: Assume Role Configuration
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/TerraformDeployRole"
export AWS_ROLE_SESSION_NAME="TerraformSession"

# Terraform Variables (sensitive values)
export TF_VAR_db_password="MyS3cur3D@t@b@s3P@ss!"
export TF_VAR_api_key="sk_test_EXAMPLE_KEY_REPLACE_WITH_REAL"
export TF_VAR_twilio_auth_token="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
export TF_VAR_datadog_api_key="dd_api_key_abc123"
export TF_VAR_pagerduty_integration_key="pd_integration_xyz789"

# Terraform Backend Configuration (optional, can use backend.hcl instead)
export TF_CLI_ARGS_init="-backend-config=backend/prod.hcl"

# Terraform Behavior
export TF_LOG="INFO"
export TF_LOG_PATH="./terraform.log"
export TF_INPUT="false"

# CI/CD Pipeline Variables
export CI_COMMIT_SHA="abc123def456"
export CI_PIPELINE_ID="12345"
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  terraform:
    image: hashicorp/terraform:1.5
    working_dir: /workspace
    volumes:
      - ./terraform:/workspace
      - ~/.aws:/root/.aws:ro
    environment:
      - AWS_PROFILE=${AWS_PROFILE:-default}
      - TF_VAR_environment=${ENVIRONMENT:-dev}
      - TF_VAR_db_password=${DB_PASSWORD}
      - TF_VAR_api_key=${API_KEY}
    env_file:
      - .env
    entrypoint: ["/bin/sh", "-c"]
    command: ["terraform init -backend-config=backend/${ENVIRONMENT:-dev}.hcl && terraform plan -var-file=environments/${ENVIRONMENT:-dev}.tfvars"]

  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,dynamodb,lambda,apigateway,iam,kms,logs
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - ./localstack-data:/tmp/localstack/data
```

### Kubernetes ConfigMap and Secrets

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: callflow-terraform-config
  namespace: infrastructure
data:
  AWS_DEFAULT_REGION: "us-east-1"
  TF_VAR_environment: "prod"
  TF_VAR_project_name: "callflow-service"
  TF_VAR_log_retention_days: "365"
  TF_VAR_enable_cloudwatch_alarms: "true"
  TF_VAR_enable_waf: "true"
  TF_VAR_api_throttling_rate_limit: "5000"
  TF_VAR_lambda_memory_size: "512"
  TF_IN_AUTOMATION: "true"

---
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: callflow-terraform-secrets
  namespace: infrastructure
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"
  AWS_SECRET_ACCESS_KEY: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  TF_VAR_db_password: "MyS3cur3D@t@b@s3P@ss!"
  TF_VAR_api_key: "sk_live_abc123def456"
  TF_VAR_twilio_auth_token: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

---
# kubernetes/terraform-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: terraform-apply
  namespace: infrastructure
spec:
  template:
    spec:
      serviceAccountName: terraform-sa
      containers:
      - name: terraform
        image: hashicorp/terraform:1.5
        workingDir: /workspace
        command: ["/bin/sh", "-c"]
        args:
          - |
            terraform init -backend-config=backend/prod.hcl
            terraform apply -var-file=environments/prod.tfvars -auto-approve
        envFrom:
        - configMapRef:
            name: callflow-terraform-config
        - secretRef:
            name: callflow-terraform-secrets
        volumeMounts:
        - name: terraform-code
          mountPath: /workspace
      volumes:
      - name: terraform-code
        persistentVolumeClaim:
          claimName: terraform-code-pvc
      restartPolicy: Never
  backoffLimit: 2
```

---

## Security Considerations

### Sensitive Value Management

1. **Never commit secrets to version control**
   - Use `.gitignore` to exclude `.env`, `*.tfvars` with secrets, and state files
   - Store secrets in AWS Secrets Manager, HashiCorp Vault, or CI/CD secret management

2. **Environment Variable Security**
   ```bash
   # .gitignore
   .env
   .env.*
   *.tfvars.sensitive
   terraform.tfstate
   terraform.tfstate.backup
   .terraform/
   ```

3. **Sensitive Variable Declaration**
   ```hcl
   # variables.tf
   variable "db_password" {
     type        = string
     description = "Database password"
     sensitive   = true
   }

   variable "api_key" {
     type        = string
     description = "API authentication key"
     sensitive   = true
   }
   ```

4. **AWS Secrets Manager Integration**
   ```hcl
   # secrets.tf
   data "aws_secretsmanager_secret_version" "db_credentials" {
     secret_id = "callflow-service/${var.environment}/db-credentials"
   }

   locals {
     db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)
   }
   ```

### IAM Best Practices

1. **Least Privilege Principle**: Create specific IAM roles for Terraform with only required permissions
2. **Use Assume Role**: Avoid long-lived credentials; use AssumeRole with limited session duration
3. **Enable MFA**: Require MFA for sensitive operations
4. **Audit Logging**: Enable CloudTrail for all Terraform API calls

### Network Security

1. **VPC Endpoints**: Use VPC endpoints for AWS service communication
2. **Security Groups**: Apply restrictive security group rules
3. **Private Subnets**: Deploy Lambda and other resources in private subnets
4. **WAF Protection**: Enable AWS WAF for API Gateway endpoints

### Encryption

1. **State File Encryption**: Always enable encryption for Terraform state
2. **KMS Keys**: Use customer-managed KMS keys for sensitive data
3. **TLS Everywhere**: Enforce HTTPS for all API endpoints
4. **Secrets Rotation**: Implement automatic rotation for credentials

---

## Troubleshooting

### Common Configuration Issues

| Issue | Symptom | Resolution |
|-------|---------|------------|
| Missing required variable | `Error: No value for required variable` | Ensure all required variables are defined in `.tfvars` or environment |
| Invalid AWS credentials | `Error: NoCredentialProviders` | Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set correctly |
| Backend initialization failure | `Error: Failed to get state` | Check S3 bucket permissions and DynamoDB table existence |
| VPC not found | `Error: VPC not found` | Verify `vpc_id` exists in the target region |
| Subnet unavailable | `Error: Subnet not available` | Ensure subnets exist and are in the correct availability zones |
| Certificate validation | `Error: Certificate not validated` | Confirm ACM certificate is validated and in correct region |
| Lambda timeout | `Error: Task timed out` | Increase `lambda_timeout` value or optimize function code |
| DynamoDB throttling | `ProvisionedThroughputExceededException` | Enable auto-scaling or increase provisioned capacity |
| API Gateway 5xx errors | High 5xx error rate | Check Lambda function logs and increase memory/timeout |

### Debugging Commands

```bash
# Validate configuration syntax
terraform validate

# Show planned changes with detailed output
terraform plan -var-file=environments/dev.tfvars -detailed-exitcode

# Enable debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=./terraform-debug.log
terraform apply -var-file=environments/dev.tfvars

# Show current state
terraform show

# List all resources in state
terraform state list

# Show specific resource details
terraform state show aws_lambda_function.processor

# Refresh state from AWS
terraform refresh -var-file=environments/dev.tfvars

# Import existing resource
terraform import aws_dynamodb_table.routing arn:aws:dynamodb:us-east-1:123456789:table/existing-table
```

### Health Check Verification

```bash
# Test API Gateway endpoint
curl -X GET https://api.callflow.company.com/v1/health \
  -H "x-api-key: your-api-key"

# Check Lambda function status
aws lambda get-function --function-name callflow-processor-prod

# Verify DynamoDB table
aws dynamodb describe-table --table-name callflow-routing-rules-prod

# Test Connect instance
aws connect describe-instance --instance-id your-instance-id
```

---

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Amazon Connect Administrator Guide](https://docs.aws.amazon.com/connect/latest/adminguide/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)