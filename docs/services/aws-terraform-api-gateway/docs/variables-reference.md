# Variables and Outputs Reference

## Overview

This document provides a complete reference for all Terraform variables and outputs used in the `aws-terraform-api-gateway` module. This module provisions AWS API Gateway account-level resources across multiple regions, enabling API Gateway deployments in supported AWS regions with CloudWatch logging capabilities.

Understanding these variables and outputs is essential for operators who need to:
- Configure multi-region API Gateway deployments
- Set up CloudWatch logging for API Gateway
- Integrate the module outputs with other infrastructure components
- Customize the module behavior for specific use cases

---

## Required Variables

Required variables must be specified when using this module. Failure to provide these variables will result in Terraform configuration errors.

### `regions`

| Attribute | Value |
|-----------|-------|
| **Type** | `list(string)` |
| **Default** | None (Required) |
| **Description** | List of AWS regions where API Gateway account-level resources should be provisioned |

This variable defines which AWS regions will have API Gateway account resources configured. The module supports up to 8 AWS regions globally.

**Example:**

```hcl
regions = [
  "us-east-1",
  "us-west-2",
  "eu-west-1",
  "ap-southeast-1"
]
```

**Supported Regions:**
- `us-east-1` (N. Virginia)
- `us-east-2` (Ohio)
- `us-west-1` (N. California)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `eu-central-1` (Frankfurt)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)

**Validation Rules:**
- Must contain at least one region
- All specified regions must be valid AWS region identifiers
- Regions must support API Gateway service

---

### `cloudwatch_role_arn`

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Default** | None (Required) |
| **Description** | ARN of the IAM role that API Gateway will assume to write logs to CloudWatch |

This IAM role must have permissions to write to CloudWatch Logs. The role is applied at the account level for API Gateway.

**Example:**

```hcl
cloudwatch_role_arn = "arn:aws:iam::123456789012:role/api-gateway-cloudwatch-role"
```

**Required IAM Policy for the Role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:PutLogEvents",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**Trust Policy for the Role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

## Optional Variables

Optional variables have default values and can be overridden based on your specific requirements.

### `enable_cloudwatch_logging`

| Attribute | Value |
|-----------|-------|
| **Type** | `bool` |
| **Default** | `true` |
| **Description** | Whether to enable CloudWatch logging for API Gateway at the account level |

When enabled, this configures the API Gateway account settings to use the specified CloudWatch role for logging.

**Example:**

```hcl
# Disable CloudWatch logging (not recommended for production)
enable_cloudwatch_logging = false

# Enable CloudWatch logging (default)
enable_cloudwatch_logging = true
```

**Best Practice:** Always keep this enabled in production environments for debugging and monitoring purposes.

---

### `tags`

| Attribute | Value |
|-----------|-------|
| **Type** | `map(string)` |
| **Default** | `{}` |
| **Description** | A map of tags to apply to all resources created by this module |

Tags help with resource organization, cost allocation, and compliance tracking.

**Example:**

```hcl
tags = {
  Environment = "production"
  Team        = "platform"
  Project     = "api-infrastructure"
  CostCenter  = "CC-12345"
  ManagedBy   = "terraform"
}
```

**Recommended Tags:**
- `Environment` - Deployment environment (dev, staging, production)
- `Team` - Owning team or department
- `Project` - Project or application name
- `ManagedBy` - Infrastructure management tool

---

### `create_cloudwatch_role`

| Attribute | Value |
|-----------|-------|
| **Type** | `bool` |
| **Default** | `false` |
| **Description** | Whether the module should create the CloudWatch IAM role or use an existing one |

When set to `true`, the module creates the IAM role with appropriate permissions. When `false`, you must provide an existing role ARN via `cloudwatch_role_arn`.

**Example:**

```hcl
# Use an existing IAM role
create_cloudwatch_role = false
cloudwatch_role_arn    = "arn:aws:iam::123456789012:role/existing-role"

# Let the module create the role
create_cloudwatch_role = true
```

---

### `cloudwatch_role_name`

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Default** | `"api-gateway-cloudwatch-role"` |
| **Description** | Name of the IAM role to create for CloudWatch logging (only used when `create_cloudwatch_role` is true) |

**Example:**

```hcl
create_cloudwatch_role = true
cloudwatch_role_name   = "custom-apigw-logging-role"
```

---

### `throttling_burst_limit`

| Attribute | Value |
|-----------|-------|
| **Type** | `number` |
| **Default** | `5000` |
| **Description** | Default throttling burst limit for API Gateway stages |

This sets the maximum number of concurrent requests that API Gateway can handle.

**Example:**

```hcl
# Higher limit for high-traffic APIs
throttling_burst_limit = 10000

# Lower limit for development environments
throttling_burst_limit = 1000
```

---

### `throttling_rate_limit`

| Attribute | Value |
|-----------|-------|
| **Type** | `number` |
| **Default** | `10000` |
| **Description** | Default throttling rate limit (requests per second) for API Gateway stages |

**Example:**

```hcl
# Adjust based on expected traffic
throttling_rate_limit = 5000
```

---

## Module Outputs

Outputs provide information about the resources created by the module, enabling integration with other Terraform configurations.

### `api_gateway_account_ids`

| Attribute | Value |
|-----------|-------|
| **Type** | `map(string)` |
| **Description** | Map of region names to API Gateway account resource IDs |

**Example Output:**

```hcl
api_gateway_account_ids = {
  "us-east-1"      = "us-east-1"
  "us-west-2"      = "us-west-2"
  "eu-west-1"      = "eu-west-1"
  "ap-southeast-1" = "ap-southeast-1"
}
```

**Usage:**

```hcl
# Reference in another module
output "primary_region_account_id" {
  value = module.api_gateway.api_gateway_account_ids["us-east-1"]
}
```

---

### `cloudwatch_role_arn`

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Description** | ARN of the CloudWatch IAM role used by API Gateway |

Returns either the created role ARN or the provided existing role ARN.

**Example Output:**

```
arn:aws:iam::123456789012:role/api-gateway-cloudwatch-role
```

**Usage:**

```hcl
# Use in dependent resources
resource "aws_api_gateway_stage" "example" {
  # ... other configuration
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.example.arn
  }
  
  depends_on = [module.api_gateway]
}
```

---

### `configured_regions`

| Attribute | Value |
|-----------|-------|
| **Type** | `list(string)` |
| **Description** | List of regions where API Gateway account resources were configured |

**Example Output:**

```hcl
configured_regions = [
  "us-east-1",
  "us-west-2",
  "eu-west-1",
  "ap-southeast-1"
]
```

---

### `cloudwatch_role_name`

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Description** | Name of the CloudWatch IAM role |

**Example Output:**

```
api-gateway-cloudwatch-role
```

---

## Usage Examples

### Basic Multi-Region Configuration

```hcl
module "api_gateway_account" {
  source = "path/to/aws-terraform-api-gateway"

  regions = [
    "us-east-1",
    "us-west-2"
  ]

  create_cloudwatch_role = true
  cloudwatch_role_name   = "api-gateway-logging-role"

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

output "configured_regions" {
  description = "Regions where API Gateway is configured"
  value       = module.api_gateway_account.configured_regions
}

output "cloudwatch_role" {
  description = "CloudWatch role ARN for API Gateway"
  value       = module.api_gateway_account.cloudwatch_role_arn
}
```

### Using Existing IAM Role

```hcl
# First, create or reference an existing IAM role
data "aws_iam_role" "existing_apigw_role" {
  name = "existing-api-gateway-role"
}

module "api_gateway_account" {
  source = "path/to/aws-terraform-api-gateway"

  regions = [
    "us-east-1",
    "eu-west-1",
    "ap-northeast-1"
  ]

  create_cloudwatch_role = false
  cloudwatch_role_arn    = data.aws_iam_role.existing_apigw_role.arn

  tags = {
    Environment = "staging"
    Team        = "platform"
  }
}
```

### Full Production Configuration

```hcl
module "api_gateway_account" {
  source = "path/to/aws-terraform-api-gateway"

  # Deploy to all supported regions
  regions = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-central-1",
    "ap-southeast-1",
    "ap-northeast-1"
  ]

  # CloudWatch configuration
  enable_cloudwatch_logging = true
  create_cloudwatch_role    = true
  cloudwatch_role_name      = "prod-api-gateway-cloudwatch-role"

  # Throttling configuration
  throttling_burst_limit = 10000
  throttling_rate_limit  = 20000

  # Comprehensive tagging
  tags = {
    Environment  = "production"
    Team         = "platform-engineering"
    Project      = "global-api-infrastructure"
    CostCenter   = "CC-PLATFORM-001"
    ManagedBy    = "terraform"
    Compliance   = "sox-pci"
    BackupPolicy = "daily"
  }
}

# Export all outputs for use by other modules
output "api_gateway_config" {
  description = "Complete API Gateway account configuration"
  value = {
    account_ids       = module.api_gateway_account.api_gateway_account_ids
    cloudwatch_role   = module.api_gateway_account.cloudwatch_role_arn
    configured_regions = module.api_gateway_account.configured_regions
  }
}
```

---

## Common Pitfalls and Troubleshooting

### IAM Role Not Assumed

**Problem:** API Gateway cannot write to CloudWatch Logs.

**Solution:** Ensure the IAM role has the correct trust policy allowing `apigateway.amazonaws.com` to assume the role.

### Region Not Supported

**Problem:** Terraform fails with unsupported region error.

**Solution:** Verify the region is in the list of supported regions and that your AWS account has API Gateway enabled in that region.

### Duplicate Account Settings

**Problem:** Error about API Gateway account settings already existing.

**Solution:** Import existing account settings or ensure only one module manages API Gateway account-level resources per region.

```bash
terraform import 'module.api_gateway_account.aws_api_gateway_account.this["us-east-1"]' us-east-1
```

---

## Related Documentation

- [AWS API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [Terraform AWS Provider - API Gateway Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_account)
- [CloudWatch Logs for API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)