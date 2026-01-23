# Deployment Guide

## aws-terraform-callflow-service

### Overview

This deployment guide provides comprehensive step-by-step instructions for deploying the Callflow Service module using Terraform. The Callflow Service is an AWS-based solution designed for storing and retrieving call flow events through API Gateway and Lambda functions, with S3 as the storage backend.

This guide is intended for operators responsible for deploying, maintaining, and managing the Callflow Service infrastructure across various environments (development, staging, production).

---

## Prerequisites Checklist

Before beginning the deployment process, ensure all prerequisites are satisfied. Failing to meet these requirements may result in deployment failures or misconfigured infrastructure.

### Required Software

| Software | Minimum Version | Purpose |
|----------|-----------------|---------|
| Terraform | >= 1.5.0 | Infrastructure as Code tool |
| AWS CLI | >= 2.0.0 | AWS credential management and verification |
| Git | >= 2.30.0 | Repository cloning and version control |
| jq | >= 1.6 | JSON parsing for verification scripts |

### Verification Commands

Run the following commands to verify your environment is properly configured:

```bash
# Check Terraform version
terraform version

# Check AWS CLI version
aws --version

# Verify Git installation
git --version

# Verify jq installation
jq --version
```

### AWS Account Requirements

- [ ] AWS account with appropriate permissions
- [ ] Ability to create IAM roles and policies
- [ ] Access to create API Gateway resources
- [ ] Permissions to create Lambda functions
- [ ] S3 bucket creation permissions
- [ ] Route53 access (if using custom DNS)
- [ ] CloudWatch access for logging and monitoring

### Network Requirements

- [ ] VPC configured (if deploying Lambda functions within VPC)
- [ ] Appropriate subnet configurations
- [ ] Security group rules defined
- [ ] NAT Gateway access for Lambda functions (if VPC-deployed)

### Domain Requirements (Optional)

- [ ] Registered domain in Route53 (for custom DNS configuration)
- [ ] ACM certificate for HTTPS endpoints
- [ ] Hosted zone ID available

---

## AWS Credentials Setup

### Option 1: AWS CLI Profile Configuration (Recommended)

Configure named profiles for different environments to prevent accidental deployments to wrong accounts:

```bash
# Configure a new profile
aws configure --profile callflow-dev

# You will be prompted for:
# AWS Access Key ID: [Enter your access key]
# AWS Secret Access Key: [Enter your secret key]
# Default region name: us-east-1
# Default output format: json
```

Verify the profile configuration:

```bash
# Test credentials
aws sts get-caller-identity --profile callflow-dev

# Expected output:
# {
#     "UserId": "AIDAEXAMPLEID",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

### Option 2: Environment Variables

For CI/CD pipelines or temporary sessions:

```bash
# Set environment variables
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"

# For temporary credentials (recommended for production)
export AWS_SESSION_TOKEN="your-session-token"
```

### Option 3: IAM Role Assumption

For cross-account deployments or enhanced security:

```bash
# Assume role command
aws sts assume-role \
  --role-arn "arn:aws:iam::TARGET_ACCOUNT:role/TerraformDeploymentRole" \
  --role-session-name "callflow-deployment" \
  --profile source-profile

# Export the returned credentials
export AWS_ACCESS_KEY_ID="returned-access-key"
export AWS_SECRET_ACCESS_KEY="returned-secret-key"
export AWS_SESSION_TOKEN="returned-session-token"
```

### Required IAM Permissions

Create an IAM policy with the following minimum permissions for deployment:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "APIGatewayPermissions",
      "Effect": "Allow",
      "Action": [
        "apigateway:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LambdaPermissions",
      "Effect": "Allow",
      "Action": [
        "lambda:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Permissions",
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPermissions",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRole",
        "iam:PassRole"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchPermissions",
      "Effect": "Allow",
      "Action": [
        "logs:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Route53Permissions",
      "Effect": "Allow",
      "Action": [
        "route53:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Backend Configuration

### S3 Backend Setup (Recommended for Team Environments)

Create the S3 bucket and DynamoDB table for state management:

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket callflow-terraform-state-${AWS_ACCOUNT_ID} \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket callflow-terraform-state-${AWS_ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket callflow-terraform-state-${AWS_ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "aws:kms"
        }
      }
    ]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name callflow-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Backend Configuration File

Create a `backend.tf` file in your deployment directory:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "callflow-terraform-state-ACCOUNT_ID"
    key            = "callflow-service/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "callflow-terraform-locks"
  }
}
```

### Environment-Specific Backend Configurations

For multiple environments, create separate backend configuration files:

```bash
# Create backend configs directory
mkdir -p backend-configs

# Development backend
cat > backend-configs/dev.hcl << 'EOF'
bucket         = "callflow-terraform-state-dev"
key            = "callflow-service/dev/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "callflow-terraform-locks-dev"
EOF

# Production backend
cat > backend-configs/prod.hcl << 'EOF'
bucket         = "callflow-terraform-state-prod"
key            = "callflow-service/prod/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "callflow-terraform-locks-prod"
EOF
```

Initialize with environment-specific backend:

```bash
terraform init -backend-config=backend-configs/dev.hcl
```

---

## Deployment Steps

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/aws-terraform-callflow-service.git
cd aws-terraform-callflow-service

# Checkout the desired version/tag
git checkout v1.0.0
```

### Step 2: Configure Variables

Create a `terraform.tfvars` file for your environment:

```hcl
# terraform.tfvars

# Environment Configuration
environment = "dev"
project     = "callflow"
region      = "us-east-1"

# API Gateway Configuration
api_name        = "callflow-api"
api_description = "Callflow Service API for event storage and retrieval"
api_stage_name  = "v1"

# Lambda Configuration
lambda_runtime     = "python3.11"
lambda_timeout     = 30
lambda_memory_size = 256

# S3 Configuration
s3_bucket_name = "callflow-events-dev"
s3_versioning  = true

# DNS Configuration (Optional)
enable_custom_domain = true
domain_name          = "api.callflow.example.com"
hosted_zone_id       = "Z1234567890ABC"

# Monitoring Configuration
enable_cloudwatch_alarms    = true
enable_cloudwatch_dashboard = true
alarm_email_endpoints       = ["ops-team@example.com"]

# Tags
tags = {
  Environment = "Development"
  Project     = "Callflow"
  ManagedBy   = "Terraform"
  Owner       = "Platform Team"
}
```

### Step 3: Initialize Terraform

```bash
# Initialize with backend configuration
terraform init -backend-config=backend-configs/dev.hcl

# Expected output:
# Initializing the backend...
# Successfully configured the backend "s3"!
# 
# Initializing provider plugins...
# - Finding latest version of hashicorp/aws...
# - Installing hashicorp/aws...
# 
# Terraform has been successfully initialized!
```

### Step 4: Validate Configuration

```bash
# Validate the Terraform configuration
terraform validate

# Expected output:
# Success! The configuration is valid.
```

### Step 5: Plan the Deployment

```bash
# Generate and review the execution plan
terraform plan -out=tfplan

# Save plan output for review
terraform plan -out=tfplan -no-color > plan-output.txt

# Review specific resources
terraform plan -target=module.api_gateway
```

Review the plan carefully, paying attention to:
- Resources being created
- Resources being modified (changes in-place)
- Resources being destroyed
- Any unexpected changes

### Step 6: Apply the Configuration

```bash
# Apply with saved plan (recommended)
terraform apply tfplan

# Or apply directly with auto-approval (CI/CD only)
terraform apply -auto-approve
```

### Step 7: Save Outputs

```bash
# Display outputs
terraform output

# Save outputs to file
terraform output -json > deployment-outputs.json

# Extract specific values
API_ENDPOINT=$(terraform output -raw api_endpoint)
echo "API Endpoint: $API_ENDPOINT"
```

---

## Verification

### Automated Verification Script

Create and run a verification script:

```bash
#!/bin/bash
# verify-deployment.sh

set -e

echo "=== Callflow Service Deployment Verification ==="

# Get outputs
API_ENDPOINT=$(terraform output -raw api_endpoint)
S3_BUCKET=$(terraform output -raw s3_bucket_name)

echo "1. Verifying API Gateway..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_ENDPOINT}/health")
if [ "$API_RESPONSE" == "200" ] || [ "$API_RESPONSE" == "401" ]; then
    echo "   ✓ API Gateway is responding"
else
    echo "   ✗ API Gateway check failed (HTTP $API_RESPONSE)"
    exit 1
fi

echo "2. Verifying S3 Bucket..."
if aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
    echo "   ✓ S3 bucket exists and is accessible"
else
    echo "   ✗ S3 bucket verification failed"
    exit 1
fi

echo "3. Verifying Lambda Functions..."
FUNCTIONS=("event-storer" "event-retriever" "authorizer")
for func in "${FUNCTIONS[@]}"; do
    FUNC_STATE=$(aws lambda get-function --function-name "callflow-${func}" --query 'Configuration.State' --output text 2>/dev/null)
    if [ "$FUNC_STATE" == "Active" ]; then
        echo "   ✓ Lambda function callflow-${func} is active"
    else
        echo "   ✗ Lambda function callflow-${func} check failed"
        exit 1
    fi
done

echo "4. Verifying CloudWatch Log Groups..."
LOG_GROUPS=$(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/callflow" --query 'logGroups[].logGroupName' --output text)
if [ -n "$LOG_GROUPS" ]; then
    echo "   ✓ CloudWatch log groups created"
else
    echo "   ✗ CloudWatch log groups not found"
    exit 1
fi

echo ""
echo "=== All verifications passed! ==="
echo "API Endpoint: $API_ENDPOINT"
```

### Manual Verification Steps

#### 1. Verify API Gateway

```bash
# Get API Gateway ID
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='callflow-api'].id" --output text)

# List resources
aws apigateway get-resources --rest-api-id $API_ID

# Check stage deployment
aws apigateway get-stage --rest-api-id $API_ID --stage-name v1
```

#### 2. Verify Lambda Functions

```bash
# List Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'callflow')]"

# Test Event Storer function
aws lambda invoke \
  --function-name callflow-event-storer \
  --payload '{"test": "data"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

#### 3. Verify S3 Bucket

```bash
# Check bucket exists and has proper configuration
aws s3api get-bucket-versioning --bucket callflow-events-dev
aws s3api get-bucket-encryption --bucket callflow-events-dev
aws s3api get-bucket-lifecycle-configuration --bucket callflow-events-dev
```

#### 4. Verify CloudWatch Resources

```bash
# List alarms
aws cloudwatch describe-alarms --alarm-name-prefix "callflow"

# List dashboards
aws cloudwatch list-dashboards --dashboard-name-prefix "callflow"
```

---

## Updating the Module

### Minor Updates (Variable Changes)

```bash
# Update tfvars file with new values
vi terraform.tfvars

# Plan changes
terraform plan -out=update-plan

# Review and apply
terraform apply update-plan
```

### Major Updates (Module Version Upgrade)

```bash
# Backup current state
terraform state pull > backup-state-$(date +%Y%m%d).json

# Update module version in your configuration
# main.tf
module "callflow" {
  source  = "your-org/callflow-service/aws"
  version = "2.0.0"  # Updated version
  # ... variables
}

# Reinitialize to get new module version
terraform init -upgrade

# Plan with detailed output
terraform plan -out=upgrade-plan

# Review changes carefully
terraform show upgrade-plan

# Apply after verification
terraform apply upgrade-plan
```

### Rolling Back Changes

```bash
# If you need to rollback, restore previous state
terraform state push backup-state-YYYYMMDD.json

# Or use previous module version
terraform init -upgrade
terraform apply
```

### Blue-Green Deployment Strategy

For zero-downtime updates:

```hcl
# Create new environment alongside existing
variable "deployment_color" {
  default = "blue"  # Switch to "green" for new deployment
}

# Use color in resource naming
resource "aws_lambda_function" "event_storer" {
  function_name = "callflow-event-storer-${var.deployment_color}"
  # ...
}
```

---

## Destroying Resources

### Pre-Destruction Checklist

- [ ] Confirm the correct workspace/environment is selected
- [ ] Verify no active traffic to the service
- [ ] Export any required data from S3
- [ ] Download CloudWatch logs if needed
- [ ] Notify stakeholders of planned destruction

### Safe Destruction Process

```bash
# Verify current workspace
terraform workspace show

# List all resources to be destroyed
terraform state list

# Plan destruction
terraform plan -destroy -out=destroy-plan

# Review the destroy plan carefully
terraform show destroy-plan

# IMPORTANT: Manually verify you're destroying the correct environment
echo "You are about to destroy resources in: $(terraform workspace show)"
echo "AWS Account: $(aws sts get-caller-identity --query Account --output text)"
read -p "Type 'yes' to confirm: " confirmation

if [ "$confirmation" == "yes" ]; then
    terraform apply destroy-plan
fi
```

### Handling S3 Bucket Destruction

S3 buckets with objects cannot be destroyed by default. Handle this:

```bash
# Option 1: Empty the bucket first
aws s3 rm s3://callflow-events-dev --recursive

# Option 2: Use force_destroy in Terraform (set before initial deployment)
# In your module configuration:
s3_force_destroy = true

# Then destroy
terraform destroy
```

### Partial Destruction

To destroy specific resources only:

```bash
# Destroy specific resource
terraform destroy -target=module.callflow.aws_lambda_function.event_storer

# Destroy multiple specific resources
terraform destroy \
  -target=module.callflow.aws_cloudwatch_dashboard.main \
  -target=module.callflow.aws_cloudwatch_metric_alarm.errors
```

---

## Troubleshooting Deployment Issues

### Common Issues and Solutions

#### Issue 1: State Lock Error

**Symptoms:**
```
Error: Error acquiring the state lock
Lock Info:
  ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Path:      callflow-terraform-state/terraform.tfstate
  Operation: OperationTypeApply
```

**Solution:**
```bash
# Verify no other deployment is running
# Then force unlock (use with caution!)
terraform force-unlock xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### Issue 2: API Gateway Deployment Failure

**Symptoms:**
```
Error: Error creating API Gateway Deployment: BadRequestException
```

**Solution:**
```bash
# Verify OpenAPI spec is valid
aws apigateway get-export \
  --rest-api-id API_ID \
  --stage-name v1 \
  --export-type oas30 \
  api-spec.json

# Check for missing integrations
aws apigateway get-resources --rest-api-id API_ID
```

#### Issue 3: Lambda Function Creation Timeout

**Symptoms:**
```
Error: Error creating Lambda function: timeout while waiting for state to become 'success'
```

**Solution:**
```bash
# Check if Lambda function was partially created
aws lambda get-function --function-name callflow-event-storer

# If exists, import into state
terraform import module.callflow.aws_lambda_function.event_storer callflow-event-storer

# Retry apply
terraform apply
```

#### Issue 4: IAM Permission Denied

**Symptoms:**
```
Error: error creating IAM Role: AccessDenied
```

**Solution:**
```bash
# Verify current permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names iam:CreateRole

# Request additional permissions from administrator
```

#### Issue 5: S3 Bucket Already Exists

**Symptoms:**
```
Error: Error creating S3 bucket: BucketAlreadyExists
```

**Solution:**
```bash
# Check if bucket exists in your account
aws s3api head-bucket --bucket callflow-events-dev

# If it exists and should be managed by Terraform
terraform import module.callflow.aws_s3_bucket.events callflow-events-dev

# Or use a different bucket name in tfvars
s3_bucket_name = "callflow-events-dev-2"
```

### Debugging Techniques

#### Enable Terraform Debug Logging

```bash
# Enable detailed logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform-debug.log

# Run terraform command
terraform apply

# Review logs
cat terraform-debug.log
```

#### Check AWS CloudTrail

```bash
# Look for recent API errors
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateFunction \
  --start-time $(date -d '1 hour ago' --iso-8601=seconds) \
  --query 'Events[].CloudTrailEvent' \
  --output text | jq -r '.errorCode, .errorMessage'
```

#### Validate Lambda Function Logs

```bash
# Stream recent logs
aws logs tail /aws/lambda/callflow-event-storer --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/callflow-event-storer \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000)
```

### Getting Help

If issues persist after trying these solutions:

1. Check the [GitHub Issues](https://github.com/your-org/aws-terraform-callflow-service/issues) for similar problems
2. Review AWS Service Health Dashboard
3. Contact the platform team with:
   - Terraform version (`terraform version`)
   - Full error message
   - Terraform debug logs
   - AWS account ID and region
   - Time of occurrence

---

## Quick Reference

### Essential Commands

```bash
# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# Destroy
terraform destroy

# Show current state
terraform show

# List resources
terraform state list

# Get outputs
terraform output
```

### Environment-Specific Deployment

```bash
# Development
terraform workspace select dev
terraform apply -var-file=environments/dev.tfvars

# Production
terraform workspace select prod
terraform apply -var-file=environments/prod.tfvars
```

---

*Last Updated: 2024*
*Module Version: 1.0.0*
*Maintained by: Platform Engineering Team*