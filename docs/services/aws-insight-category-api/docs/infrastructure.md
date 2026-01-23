# Infrastructure & Architecture

## Overview

The `aws-insight-category-api` service is a serverless REST API built on AWS infrastructure, designed to manage organization categories within the AWS Insight platform. This document provides comprehensive technical documentation of the system architecture, AWS resources, and deployment configurations that power this multi-tenant, Lambda-based service.

The architecture follows AWS serverless best practices, leveraging API Gateway for request routing, Lambda functions for compute, and DynamoDB for persistent storage. Infrastructure is fully managed through Terraform, enabling reproducible deployments across environments.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (us-east-1)                               │
│                                                                                  │
│  ┌─────────────────┐                                                            │
│  │   CloudFront    │  (Optional CDN Layer)                                      │
│  │   Distribution  │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                      │
│           ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         API Gateway (REST API)                           │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │    │
│  │  │ /categories │  │ /categories │  │ /templates  │  │   /health   │    │    │
│  │  │    GET      │  │    POST     │  │    GET      │  │    GET      │    │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │    │
│  │  ┌─────────────┐  ┌─────────────┐                                       │    │
│  │  │ /categories │  │ /categories │   Stage: {env}                       │    │
│  │  │  /{id} PUT  │  │ /{id} DELETE│   (dev/staging/prod)                 │    │
│  │  └─────────────┘  └─────────────┘                                       │    │
│  └────────────────────────────┬────────────────────────────────────────────┘    │
│                               │                                                  │
│           ┌───────────────────┼───────────────────┐                             │
│           │                   │                   │                              │
│           ▼                   ▼                   ▼                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                    │
│  │ Lambda Function │ │ Lambda Function │ │ Lambda Function │                    │
│  │ category-list   │ │ category-crud   │ │ template-list   │                    │
│  │                 │ │                 │ │                 │                    │
│  │ Runtime: Node18 │ │ Runtime: Node18 │ │ Runtime: Node18 │                    │
│  │ Memory: 256MB   │ │ Memory: 512MB   │ │ Memory: 256MB   │                    │
│  │ Timeout: 30s    │ │ Timeout: 30s    │ │ Timeout: 30s    │                    │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘                    │
│           │                   │                   │                              │
│           └───────────────────┼───────────────────┘                             │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         DynamoDB Tables                                  │    │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐            │    │
│  │  │   insight-categories    │    │  insight-category-      │            │    │
│  │  │                         │    │     templates           │            │    │
│  │  │  PK: organizationId     │    │                         │            │    │
│  │  │  SK: categoryId         │    │  PK: templateId         │            │    │
│  │  │                         │    │  SK: version             │            │    │
│  │  │  GSI: CategoryNameIndex │    │                         │            │    │
│  │  └─────────────────────────┘    └─────────────────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   CloudWatch    │  │    X-Ray        │  │   IAM Roles     │                  │
│  │     Logs        │  │   Tracing       │  │  & Policies     │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │          External Services          │
                    │  ┌─────────────┐  ┌─────────────┐  │
                    │  │   Cognito   │  │   AWS KMS   │  │
                    │  │  User Pool  │  │  (Encryption)│  │
                    │  └─────────────┘  └─────────────┘  │
                    └─────────────────────────────────────┘
```

---

## AWS Services Used

### Core Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **API Gateway** | REST API endpoint management, request routing, throttling | REST API with regional endpoint |
| **AWS Lambda** | Serverless compute for business logic | Node.js 18.x runtime |
| **DynamoDB** | NoSQL database for category and template storage | On-demand capacity mode |
| **IAM** | Access control and service permissions | Least-privilege policies |

### Supporting Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **CloudWatch Logs** | Centralized logging and monitoring | 30-day retention |
| **CloudWatch Metrics** | Performance monitoring and alerting | Custom metrics enabled |
| **AWS X-Ray** | Distributed tracing and debugging | Active tracing enabled |
| **AWS KMS** | Encryption key management | Customer-managed keys (CMK) |
| **Amazon Cognito** | User authentication and authorization | User Pool with custom claims |
| **AWS Secrets Manager** | Secure credential storage | Automatic rotation enabled |

### Infrastructure Management

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Terraform** | Infrastructure as Code | Version 1.5+ |
| **S3** | Terraform state storage | Versioning enabled |
| **DynamoDB** | Terraform state locking | PAY_PER_REQUEST |

---

## Lambda Functions

### Function Overview

The service consists of multiple Lambda functions, each responsible for specific operations:

#### 1. Category List Function (`insight-category-list`)

```hcl
# terraform/modules/lambda/category-list.tf

resource "aws_lambda_function" "category_list" {
  function_name = "${var.environment}-insight-category-list"
  runtime       = "nodejs18.x"
  handler       = "handlers/category-list.handler"
  memory_size   = 256
  timeout       = 30

  environment {
    variables = {
      TABLE_NAME        = aws_dynamodb_table.categories.name
      LOG_LEVEL         = var.log_level
      ENABLE_XRAY       = "true"
      ENVIRONMENT       = var.environment
    }
  }

  tracing_config {
    mode = "Active"
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = local.common_tags
}
```

**Function Details:**

| Property | Value |
|----------|-------|
| **Runtime** | Node.js 18.x |
| **Memory** | 256 MB |
| **Timeout** | 30 seconds |
| **Concurrency** | 100 (reserved) |
| **VPC** | Private subnets |

#### 2. Category CRUD Function (`insight-category-crud`)

```javascript
// src/handlers/category-crud.js

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand, UpdateCommand, DeleteCommand } = require('@aws-sdk/lib-dynamodb');
const { captureAWSv3Client } = require('aws-xray-sdk');

const client = captureAWSv3Client(new DynamoDBClient({}));
const docClient = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  const { httpMethod, pathParameters, body } = event;
  const organizationId = event.requestContext.authorizer.claims['custom:organizationId'];

  switch (httpMethod) {
    case 'POST':
      return createCategory(organizationId, JSON.parse(body));
    case 'PUT':
      return updateCategory(organizationId, pathParameters.id, JSON.parse(body));
    case 'DELETE':
      return deleteCategory(organizationId, pathParameters.id);
    default:
      return { statusCode: 405, body: 'Method Not Allowed' };
  }
};
```

**Function Details:**

| Property | Value |
|----------|-------|
| **Runtime** | Node.js 18.x |
| **Memory** | 512 MB |
| **Timeout** | 30 seconds |
| **Concurrency** | 50 (reserved) |
| **Provisioned Concurrency** | 5 (production only) |

#### 3. Template List Function (`insight-template-list`)

```yaml
# serverless.yml (alternative deployment reference)

functions:
  templateList:
    handler: handlers/template-list.handler
    memorySize: 256
    timeout: 30
    events:
      - http:
          path: /templates
          method: get
          cors: true
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: !Ref CognitoAuthorizer
```

### Lambda IAM Permissions

```hcl
# terraform/modules/lambda/iam.tf

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${var.environment}-lambda-dynamodb-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.categories.arn,
          "${aws_dynamodb_table.categories.arn}/index/*",
          aws_dynamodb_table.templates.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}
```

---

## DynamoDB Schema

### Categories Table (`insight-categories`)

```hcl
# terraform/modules/dynamodb/categories.tf

resource "aws_dynamodb_table" "categories" {
  name           = "${var.environment}-insight-categories"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "organizationId"
  range_key      = "categoryId"

  attribute {
    name = "organizationId"
    type = "S"
  }

  attribute {
    name = "categoryId"
    type = "S"
  }

  attribute {
    name = "categoryName"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "S"
  }

  global_secondary_index {
    name            = "CategoryNameIndex"
    hash_key        = "organizationId"
    range_key       = "categoryName"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "CreatedAtIndex"
    hash_key        = "organizationId"
    range_key       = "createdAt"
    projection_type = "KEYS_ONLY"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = local.common_tags
}
```

#### Table Schema

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| `organizationId` | String | Partition Key | Tenant identifier for multi-tenancy |
| `categoryId` | String | Sort Key | Unique category identifier (UUID) |
| `categoryName` | String | GSI-RK | Human-readable category name |
| `description` | String | - | Category description |
| `parentCategoryId` | String | - | Parent category for hierarchies |
| `metadata` | Map | - | Flexible metadata storage |
| `createdAt` | String | GSI-RK | ISO 8601 timestamp |
| `updatedAt` | String | - | ISO 8601 timestamp |
| `createdBy` | String | - | User ID who created the category |
| `isActive` | Boolean | - | Soft delete flag |

#### Sample Document

```json
{
  "organizationId": "org-12345",
  "categoryId": "cat-abc123",
  "categoryName": "Infrastructure Costs",
  "description": "Categories related to infrastructure and compute costs",
  "parentCategoryId": null,
  "metadata": {
    "color": "#3498db",
    "icon": "server",
    "sortOrder": 1
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-20T14:22:00Z",
  "createdBy": "user-xyz789",
  "isActive": true
}
```

### Templates Table (`insight-category-templates`)

```hcl
# terraform/modules/dynamodb/templates.tf

resource "aws_dynamodb_table" "templates" {
  name           = "${var.environment}-insight-category-templates"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "templateId"
  range_key      = "version"

  attribute {
    name = "templateId"
    type = "S"
  }

  attribute {
    name = "version"
    type = "N"
  }

  attribute {
    name = "templateType"
    type = "S"
  }

  global_secondary_index {
    name            = "TemplateTypeIndex"
    hash_key        = "templateType"
    range_key       = "version"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.common_tags
}
```

#### Access Patterns

| Access Pattern | Key Condition | Index Used |
|----------------|---------------|------------|
| Get all categories for org | `PK = organizationId` | Main table |
| Get specific category | `PK = organizationId, SK = categoryId` | Main table |
| Find category by name | `PK = organizationId, SK = categoryName` | CategoryNameIndex |
| List recent categories | `PK = organizationId, SK begins_with date` | CreatedAtIndex |
| Get template by type | `PK = templateType` | TemplateTypeIndex |

---

## API Gateway Configuration

### REST API Definition

```hcl
# terraform/modules/api-gateway/main.tf

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.environment}-insight-category-api"
  description = "AWS Insight Category Management API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  minimum_compression_size = 1024

  tags = local.common_tags
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId         = "$context.requestId"
      ip                = "$context.identity.sourceIp"
      caller            = "$context.identity.caller"
      user              = "$context.identity.user"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      resourcePath      = "$context.resourcePath"
      status            = "$context.status"
      protocol          = "$context.protocol"
      responseLength    = "$context.responseLength"
      integrationError  = "$context.integrationErrorMessage"
    })
  }

  variables = {
    lambdaAlias = var.environment
  }
}
```

### Resource Definitions

```hcl
# terraform/modules/api-gateway/resources.tf

# /categories resource
resource "aws_api_gateway_resource" "categories" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "categories"
}

# /categories/{id} resource
resource "aws_api_gateway_resource" "category_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.categories.id
  path_part   = "{id}"
}

# GET /categories method
resource "aws_api_gateway_method" "get_categories" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.categories.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id

  request_parameters = {
    "method.request.querystring.limit"  = false
    "method.request.querystring.cursor" = false
    "method.request.querystring.filter" = false
  }
}
```

### Throttling and Usage Plans

```hcl
# terraform/modules/api-gateway/usage-plans.tf

resource "aws_api_gateway_usage_plan" "standard" {
  name        = "${var.environment}-standard-usage-plan"
  description = "Standard rate limiting for API consumers"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = 10000
    offset = 0
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }
}

resource "aws_api_gateway_usage_plan" "premium" {
  name        = "${var.environment}-premium-usage-plan"
  description = "Premium rate limiting for high-volume consumers"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = 100000
    offset = 0
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 500
    rate_limit  = 200
  }
}
```

### CORS Configuration

```hcl
# terraform/modules/api-gateway/cors.tf

resource "aws_api_gateway_method" "options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.categories.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.categories.id
  http_method = aws_api_gateway_method.options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({ statusCode = 200 })
  }
}

resource "aws_api_gateway_method_response" "options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.categories.id
  http_method = aws_api_gateway_method.options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}
```

---

## Authorization Flow

### Authentication Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Client    │────▶│   Cognito    │────▶│   API GW     │
│  Application │     │  User Pool   │     │  Authorizer  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │  1. Authenticate   │                    │
       │───────────────────▶│                    │
       │                    │                    │
       │  2. JWT Tokens     │                    │
       │◀───────────────────│                    │
       │                    │                    │
       │  3. API Request w/ Token               │
       │────────────────────────────────────────▶│
       │                    │                    │
       │                    │  4. Validate Token │
       │                    │◀───────────────────│
       │                    │                    │
       │                    │  5. Token Valid    │
       │                    │───────────────────▶│
       │                    │                    │
       │  6. API Response                        │
       │◀────────────────────────────────────────│
```

### Cognito User Pool Configuration

```hcl
# terraform/modules/cognito/main.tf

resource "aws_cognito_user_pool" "main" {
  name = "${var.environment}-insight-user-pool"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  schema {
    attribute_data_type = "String"
    name                = "organizationId"
    required            = false
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    attribute_data_type = "String"
    name                = "role"
    required            = false
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 64
    }
  }

  tags = local.common_tags
}
```

### API Gateway Authorizer

```hcl
# terraform/modules/api-gateway/authorizer.tf

resource "aws_api_gateway_authorizer" "cognito" {
  name            = "cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.main.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [var.cognito_user_pool_arn]
  identity_source = "method.request.header.Authorization"

  # Cache authorization for 300 seconds
  authorizer_result_ttl_in_seconds = 300
}
```

### Token Validation in Lambda

```javascript
// src/middleware/auth.js

const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

const client = jwksClient({
  jwksUri: `https://cognito-idp.${process.env.AWS_REGION}.amazonaws.com/${process.env.USER_POOL_ID}/.well-known/jwks.json`,
  cache: true,
  cacheMaxEntries: 5,
  cacheMaxAge: 600000 // 10 minutes
});

const getSigningKey = (header, callback) => {
  client.getSigningKey(header.kid, (err, key) => {
    if (err) return callback(err);
    const signingKey = key.getPublicKey();
    callback(null, signingKey);
  });
};

const validateToken = async (token) => {
  return new Promise((resolve, reject) => {
    jwt.verify(token, getSigningKey, {
      algorithms: ['RS256'],
      issuer: `https://cognito-idp.${process.env.AWS_REGION}.amazonaws.com/${process.env.USER_POOL_ID}`
    }, (err, decoded) => {
      if (err) return reject(err);
      resolve(decoded);
    });
  });
};

const extractOrganizationId = (event) => {
  const claims = event.requestContext.authorizer?.claims;
  return claims?.['custom:organizationId'] || claims?.organizationId;
};

module.exports = { validateToken, extractOrganizationId };
```

---

## Environment Configuration

### Environment Variables

```hcl
# terraform/environments/prod/terraform.tfvars

environment = "prod"
aws_region  = "us-east-1"

# Lambda Configuration
lambda_memory_size     = 512
lambda_timeout         = 30
lambda_log_retention   = 30
provisioned_concurrency = 5

# DynamoDB Configuration
dynamodb_billing_mode = "PAY_PER_REQUEST"
enable_pitr          = true
enable_encryption    = true

# API Gateway Configuration
api_throttle_rate_limit  = 100
api_throttle_burst_limit = 200
api_quota_limit          = 50000

# Monitoring
enable_xray_tracing = true
log_level           = "INFO"
alarm_email         = "ops-team@example.com"

# VPC Configuration
vpc_cidr              = "10.0.0.0/16"
private_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnet_cidrs   = ["10.0.101.0/24", "10.0.102.0/24"]
```

### Environment-Specific Configuration

| Variable | Development | Staging | Production |
|----------|-------------|---------|------------|
| `lambda_memory_size` | 256 MB | 256 MB | 512 MB |
| `lambda_timeout` | 30s | 30s | 30s |
| `provisioned_concurrency` | 0 | 2 | 5 |
| `log_level` | DEBUG | INFO | INFO |
| `enable_pitr` | false | true | true |
| `api_throttle_rate_limit` | 10 | 50 | 100 |
| `alarm_email` | dev@example.com | staging@example.com | ops@example.com |

### Terraform Backend Configuration

```hcl
# terraform/backend.tf

terraform {
  backend "s3" {
    bucket         = "insight-terraform-state"
    key            = "category-api/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # Enable state locking
    skip_metadata_api_check = false
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.5.0"
}
```

### Deployment Commands

```bash
# Initialize Terraform
terraform init -backend-config="environments/${ENV}/backend.hcl"

# Plan changes
terraform plan -var-file="environments/${ENV}/terraform.tfvars" -out=tfplan

# Apply changes
terraform apply tfplan

# Destroy (use with caution)
terraform destroy -var-file="environments/${ENV}/terraform.tfvars"
```

### CloudWatch Alarms

```hcl
# terraform/modules/monitoring/alarms.tf

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.environment}-category-api-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Lambda function error rate too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.category_crud.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${var.environment}-category-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 20
  alarm_description   = "API Gateway 5XX error rate too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = var.environment
  }
}
```

---

## Best Practices and Recommendations

### Security

1. **Encryption at Rest**: All DynamoDB tables use AWS KMS customer-managed keys
2. **Encryption in Transit**: TLS 1.2+ enforced on all API endpoints
3. **Least Privilege**: IAM roles scoped to specific resources and actions
4. **Secret Management**: Sensitive configuration stored in AWS Secrets Manager

### Performance

1. **Lambda Cold Starts**: Use provisioned concurrency in production
2. **DynamoDB**: On-demand capacity eliminates capacity planning
3. **API Gateway Caching**: Consider enabling response caching for read-heavy endpoints

### Monitoring

1. **X-Ray Tracing**: Enabled for end-to-end request tracing
2. **CloudWatch Dashboards**: Create custom dashboards for key metrics
3. **Alerting**: Configure alarms for error rates, latency, and throttling

### Cost Optimization

1. **Right-sizing**: Review Lambda memory allocation based on actual usage
2. **Reserved Capacity**: Consider reserved capacity for predictable workloads
3. **Log Retention**: Set appropriate retention periods to control costs

---

## Related Documentation

- [API Reference](./api-reference.md)
- [Data Models](./data-models.md)
- [Deployment Guide](./deployment.md)
- [Troubleshooting Guide](./troubleshooting.md)