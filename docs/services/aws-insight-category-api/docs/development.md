# Development Guide

## Overview

This guide provides comprehensive information for developers working on the `aws-insight-category-api` service. This REST API service manages organization categories within the AWS Insight platform, leveraging a serverless architecture built on AWS Lambda, API Gateway, and DynamoDB.

The service follows a multi-tenant architecture where all resources are scoped to specific organizations, ensuring data isolation and security across different tenants.

---

## Prerequisites

### Required Tools and Software

Before you begin development on this service, ensure you have the following tools installed and configured:

#### AWS CLI (v2.x or later)
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version

# Configure credentials
aws configure
```

#### Terraform (v1.0 or later)
```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform --version
```

#### Node.js (v18.x or later) for Lambda functions
```bash
# Using nvm (recommended)
nvm install 18
nvm use 18

# Verify installation
node --version
npm --version
```

#### Python (v3.9 or later) for utility scripts
```bash
# Verify Python installation
python3 --version
pip3 --version
```

#### Docker (for local DynamoDB)
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io

# Start local DynamoDB
docker run -p 8000:8000 amazon/dynamodb-local
```

### AWS Account Setup

Ensure your AWS account has the following permissions:
- Lambda function management
- API Gateway administration
- DynamoDB table operations
- IAM role creation and management
- CloudWatch Logs access

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=development

# DynamoDB Configuration
DYNAMODB_ENDPOINT=http://localhost:8000
DYNAMODB_TABLE_PREFIX=dev-insight-category

# API Configuration
API_STAGE=dev
LOG_LEVEL=DEBUG

# Testing Configuration
TEST_ORG_ID=test-org-001
```

---

## Local Development Setup

### Step 1: Clone and Initialize the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/aws-insight-category-api.git
cd aws-insight-category-api

# Install dependencies
npm install

# Install Python dependencies for utilities
pip3 install -r requirements.txt
```

### Step 2: Start Local DynamoDB

```bash
# Start DynamoDB Local using Docker Compose
docker-compose up -d dynamodb-local

# Verify DynamoDB is running
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

### Step 3: Create Local DynamoDB Tables

```bash
# Run table creation script
./scripts/create-local-tables.sh

# Or manually create tables
aws dynamodb create-table \
    --table-name dev-insight-category-categories \
    --attribute-definitions \
        AttributeName=organizationId,AttributeType=S \
        AttributeName=categoryId,AttributeType=S \
    --key-schema \
        AttributeName=organizationId,KeyType=HASH \
        AttributeName=categoryId,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000
```

### Step 4: Run the Local Development Server

```bash
# Using SAM CLI for local API Gateway simulation
sam local start-api --env-vars env.json

# Or use serverless-offline
npx serverless offline start
```

### Step 5: Seed Test Data

```bash
# Run the seed script
node scripts/seed-data.js

# Verify data was seeded
aws dynamodb scan \
    --table-name dev-insight-category-categories \
    --endpoint-url http://localhost:8000
```

---

## Project Structure

```
aws-insight-category-api/
├── src/
│   ├── handlers/                    # Lambda function handlers
│   │   ├── categories/
│   │   │   ├── create.js           # POST /organizations/{orgId}/categories
│   │   │   ├── get.js              # GET /organizations/{orgId}/categories/{id}
│   │   │   ├── list.js             # GET /organizations/{orgId}/categories
│   │   │   ├── update.js           # PUT /organizations/{orgId}/categories/{id}
│   │   │   ├── delete.js           # DELETE /organizations/{orgId}/categories/{id}
│   │   │   └── index.js            # Handler exports
│   │   └── templates/
│   │       ├── list.js             # GET /templates
│   │       └── apply.js            # POST /organizations/{orgId}/categories/apply-template
│   ├── lib/
│   │   ├── dynamodb/
│   │   │   ├── client.js           # DynamoDB client configuration
│   │   │   ├── operations.js       # Common CRUD operations
│   │   │   └── expressions.js      # Expression builders
│   │   ├── validation/
│   │   │   ├── schemas.js          # JSON Schema definitions
│   │   │   └── validator.js        # Validation utilities
│   │   ├── response/
│   │   │   └── builder.js          # API response builders
│   │   └── logging/
│   │       └── logger.js           # Structured logging utility
│   ├── models/
│   │   ├── Category.js             # Category model
│   │   ├── CategoryTemplate.js     # Template model
│   │   └── index.js                # Model exports
│   └── utils/
│       ├── errors.js               # Custom error classes
│       ├── pagination.js           # Pagination helpers
│       └── tenant.js               # Multi-tenant utilities
├── terraform/
│   ├── main.tf                     # Main Terraform configuration
│   ├── lambda.tf                   # Lambda function definitions
│   ├── api-gateway.tf              # API Gateway configuration
│   ├── dynamodb.tf                 # DynamoDB table definitions
│   ├── iam.tf                      # IAM roles and policies
│   └── variables.tf                # Terraform variables
├── tests/
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── fixtures/                   # Test fixtures
├── scripts/
│   ├── deploy.sh                   # Deployment script
│   ├── create-local-tables.sh      # Local DynamoDB setup
│   └── seed-data.js                # Test data seeding
├── package.json
├── serverless.yml                  # Serverless Framework config
└── README.md
```

---

## Lambda Handler Pattern

### Standard Handler Structure

All Lambda handlers in this service follow a consistent pattern for maintainability and error handling:

```javascript
// src/handlers/categories/create.js
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, PutCommand } = require('@aws-sdk/lib-dynamodb');
const { v4: uuidv4 } = require('uuid');
const { validateCategory } = require('../../lib/validation/validator');
const { buildResponse, buildErrorResponse } = require('../../lib/response/builder');
const { logger } = require('../../lib/logging/logger');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

/**
 * Lambda handler for creating a new category
 * @param {Object} event - API Gateway Lambda Proxy event
 * @param {Object} context - Lambda context
 * @returns {Object} API Gateway Lambda Proxy response
 */
exports.handler = async (event, context) => {
    const requestId = context.awsRequestId;
    
    logger.info('Create category request received', {
        requestId,
        path: event.path,
        organizationId: event.pathParameters?.organizationId
    });

    try {
        // 1. Extract and validate path parameters
        const { organizationId } = event.pathParameters || {};
        
        if (!organizationId) {
            return buildErrorResponse(400, 'Missing organizationId parameter', requestId);
        }

        // 2. Parse and validate request body
        let body;
        try {
            body = JSON.parse(event.body || '{}');
        } catch (parseError) {
            return buildErrorResponse(400, 'Invalid JSON in request body', requestId);
        }

        const validationResult = validateCategory(body);
        if (!validationResult.valid) {
            return buildErrorResponse(400, validationResult.errors, requestId);
        }

        // 3. Build the category item
        const timestamp = new Date().toISOString();
        const categoryId = uuidv4();
        
        const category = {
            organizationId,
            categoryId,
            name: body.name,
            description: body.description || '',
            parentId: body.parentId || null,
            metadata: body.metadata || {},
            status: 'active',
            createdAt: timestamp,
            updatedAt: timestamp,
            createdBy: event.requestContext?.authorizer?.userId || 'system'
        };

        // 4. Persist to DynamoDB
        await docClient.send(new PutCommand({
            TableName: process.env.CATEGORIES_TABLE,
            Item: category,
            ConditionExpression: 'attribute_not_exists(categoryId)'
        }));

        logger.info('Category created successfully', {
            requestId,
            organizationId,
            categoryId
        });

        // 5. Return success response
        return buildResponse(201, category, requestId);

    } catch (error) {
        logger.error('Failed to create category', {
            requestId,
            error: error.message,
            stack: error.stack
        });

        if (error.name === 'ConditionalCheckFailedException') {
            return buildErrorResponse(409, 'Category already exists', requestId);
        }

        return buildErrorResponse(500, 'Internal server error', requestId);
    }
};
```

### Handler Best Practices

1. **Always validate input** before processing
2. **Use structured logging** for observability
3. **Include request IDs** in all log entries
4. **Handle errors gracefully** with appropriate HTTP status codes
5. **Keep handlers thin** - delegate business logic to services

### Response Builder Utility

```javascript
// src/lib/response/builder.js

const CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
};

/**
 * Build a successful API response
 */
exports.buildResponse = (statusCode, data, requestId) => {
    return {
        statusCode,
        headers: {
            ...CORS_HEADERS,
            'Content-Type': 'application/json',
            'X-Request-Id': requestId
        },
        body: JSON.stringify({
            success: true,
            data,
            requestId
        })
    };
};

/**
 * Build an error API response
 */
exports.buildErrorResponse = (statusCode, message, requestId) => {
    return {
        statusCode,
        headers: {
            ...CORS_HEADERS,
            'Content-Type': 'application/json',
            'X-Request-Id': requestId
        },
        body: JSON.stringify({
            success: false,
            error: {
                message,
                statusCode
            },
            requestId
        })
    };
};
```

---

## DynamoDB Operations

### Client Configuration

```javascript
// src/lib/dynamodb/client.js
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient } = require('@aws-sdk/lib-dynamodb');

const config = {
    region: process.env.AWS_REGION || 'us-east-1'
};

// Use local DynamoDB for development
if (process.env.DYNAMODB_ENDPOINT) {
    config.endpoint = process.env.DYNAMODB_ENDPOINT;
}

const client = new DynamoDBClient(config);

const marshallOptions = {
    convertEmptyValues: false,
    removeUndefinedValues: true,
    convertClassInstanceToMap: true
};

const unmarshallOptions = {
    wrapNumbers: false
};

const docClient = DynamoDBDocumentClient.from(client, {
    marshallOptions,
    unmarshallOptions
});

module.exports = { client, docClient };
```

### Common Operations

```javascript
// src/lib/dynamodb/operations.js
const { docClient } = require('./client');
const {
    GetCommand,
    PutCommand,
    UpdateCommand,
    DeleteCommand,
    QueryCommand
} = require('@aws-sdk/lib-dynamodb');

/**
 * Get a single item by primary key
 */
exports.getItem = async (tableName, key) => {
    const response = await docClient.send(new GetCommand({
        TableName: tableName,
        Key: key
    }));
    return response.Item;
};

/**
 * Query items by partition key with optional filters
 */
exports.queryItems = async (tableName, partitionKey, partitionValue, options = {}) => {
    const params = {
        TableName: tableName,
        KeyConditionExpression: `${partitionKey} = :pk`,
        ExpressionAttributeValues: {
            ':pk': partitionValue
        }
    };

    // Add pagination
    if (options.limit) {
        params.Limit = options.limit;
    }
    if (options.exclusiveStartKey) {
        params.ExclusiveStartKey = options.exclusiveStartKey;
    }

    // Add filter expression
    if (options.filterExpression) {
        params.FilterExpression = options.filterExpression;
        Object.assign(params.ExpressionAttributeValues, options.filterValues);
    }

    const response = await docClient.send(new QueryCommand(params));
    
    return {
        items: response.Items,
        lastEvaluatedKey: response.LastEvaluatedKey,
        count: response.Count
    };
};

/**
 * Update an item with optimistic locking
 */
exports.updateItem = async (tableName, key, updates, expectedVersion) => {
    const updateExpressions = [];
    const expressionAttributeNames = {};
    const expressionAttributeValues = {};

    Object.entries(updates).forEach(([field, value], index) => {
        const nameKey = `#field${index}`;
        const valueKey = `:value${index}`;
        
        updateExpressions.push(`${nameKey} = ${valueKey}`);
        expressionAttributeNames[nameKey] = field;
        expressionAttributeValues[valueKey] = value;
    });

    // Always update the timestamp
    updateExpressions.push('#updatedAt = :updatedAt');
    expressionAttributeNames['#updatedAt'] = 'updatedAt';
    expressionAttributeValues[':updatedAt'] = new Date().toISOString();

    const params = {
        TableName: tableName,
        Key: key,
        UpdateExpression: `SET ${updateExpressions.join(', ')}`,
        ExpressionAttributeNames: expressionAttributeNames,
        ExpressionAttributeValues: expressionAttributeValues,
        ReturnValues: 'ALL_NEW'
    };

    // Add optimistic locking condition
    if (expectedVersion !== undefined) {
        params.ConditionExpression = '#version = :expectedVersion';
        expressionAttributeNames['#version'] = 'version';
        expressionAttributeValues[':expectedVersion'] = expectedVersion;
    }

    const response = await docClient.send(new UpdateCommand(params));
    return response.Attributes;
};

/**
 * Soft delete an item
 */
exports.softDeleteItem = async (tableName, key) => {
    return exports.updateItem(tableName, key, {
        status: 'deleted',
        deletedAt: new Date().toISOString()
    });
};
```

### Table Schema Reference

| Table | Partition Key | Sort Key | GSI |
|-------|--------------|----------|-----|
| categories | organizationId | categoryId | parentId-index |
| category-templates | templateId | - | - |
| category-history | categoryId | timestamp | organizationId-index |

---

## Utility Libraries

### Validation Utility

```javascript
// src/lib/validation/validator.js
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

const ajv = new Ajv({ allErrors: true, verbose: true });
addFormats(ajv);

const categorySchema = {
    type: 'object',
    required: ['name'],
    properties: {
        name: {
            type: 'string',
            minLength: 1,
            maxLength: 255,
            pattern: '^[a-zA-Z0-9\\s\\-_]+$'
        },
        description: {
            type: 'string',
            maxLength: 1000
        },
        parentId: {
            type: ['string', 'null'],
            format: 'uuid'
        },
        metadata: {
            type: 'object',
            additionalProperties: true
        }
    },
    additionalProperties: false
};

const validateCategory = ajv.compile(categorySchema);

exports.validateCategory = (data) => {
    const valid = validateCategory(data);
    return {
        valid,
        errors: valid ? null : validateCategory.errors.map(err => ({
            field: err.instancePath || err.params.missingProperty,
            message: err.message
        }))
    };
};
```

### Pagination Helper

```javascript
// src/utils/pagination.js

const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;

/**
 * Parse pagination parameters from query string
 */
exports.parsePaginationParams = (queryStringParameters = {}) => {
    const limit = Math.min(
        parseInt(queryStringParameters.limit, 10) || DEFAULT_PAGE_SIZE,
        MAX_PAGE_SIZE
    );

    let exclusiveStartKey = null;
    if (queryStringParameters.nextToken) {
        try {
            exclusiveStartKey = JSON.parse(
                Buffer.from(queryStringParameters.nextToken, 'base64').toString()
            );
        } catch (e) {
            // Invalid token, ignore
        }
    }

    return { limit, exclusiveStartKey };
};

/**
 * Build pagination response
 */
exports.buildPaginatedResponse = (items, lastEvaluatedKey, totalCount) => {
    const response = {
        items,
        count: items.length
    };

    if (totalCount !== undefined) {
        response.totalCount = totalCount;
    }

    if (lastEvaluatedKey) {
        response.nextToken = Buffer.from(
            JSON.stringify(lastEvaluatedKey)
        ).toString('base64');
    }

    return response;
};
```

### Multi-Tenant Utilities

```javascript
// src/utils/tenant.js

/**
 * Extract organization ID from event
 */
exports.getOrganizationId = (event) => {
    // From path parameters
    if (event.pathParameters?.organizationId) {
        return event.pathParameters.organizationId;
    }

    // From authorization context
    if (event.requestContext?.authorizer?.organizationId) {
        return event.requestContext.authorizer.organizationId;
    }

    return null;
};

/**
 * Validate organization access
 */
exports.validateOrganizationAccess = (event, targetOrgId) => {
    const userOrgId = event.requestContext?.authorizer?.organizationId;
    const userRole = event.requestContext?.authorizer?.role;

    // Super admins can access any organization
    if (userRole === 'super_admin') {
        return true;
    }

    // Users can only access their own organization
    return userOrgId === targetOrgId;
};
```

---

## Testing

### Unit Testing

We use Jest for unit testing. Tests are located in the `tests/unit` directory.

```javascript
// tests/unit/handlers/categories/create.test.js
const { handler } = require('../../../../src/handlers/categories/create');
const { mockClient } = require('aws-sdk-client-mock');
const { DynamoDBDocumentClient, PutCommand } = require('@aws-sdk/lib-dynamodb');

const ddbMock = mockClient(DynamoDBDocumentClient);

describe('Create Category Handler', () => {
    beforeEach(() => {
        ddbMock.reset();
        process.env.CATEGORIES_TABLE = 'test-categories';
    });

    it('should create a category successfully', async () => {
        ddbMock.on(PutCommand).resolves({});

        const event = {
            pathParameters: { organizationId: 'org-123' },
            body: JSON.stringify({
                name: 'Test Category',
                description: 'A test category'
            }),
            requestContext: {
                authorizer: { userId: 'user-123' }
            }
        };

        const context = { awsRequestId: 'req-123' };
        const response = await handler(event, context);

        expect(response.statusCode).toBe(201);
        
        const body = JSON.parse(response.body);
        expect(body.success).toBe(true);
        expect(body.data.name).toBe('Test Category');
        expect(body.data.organizationId).toBe('org-123');
    });

    it('should return 400 for invalid input', async () => {
        const event = {
            pathParameters: { organizationId: 'org-123' },
            body: JSON.stringify({
                // Missing required 'name' field
                description: 'A test category'
            })
        };

        const context = { awsRequestId: 'req-123' };
        const response = await handler(event, context);

        expect(response.statusCode).toBe(400);
    });

    it('should return 400 for missing organizationId', async () => {
        const event = {
            pathParameters: {},
            body: JSON.stringify({ name: 'Test' })
        };

        const context = { awsRequestId: 'req-123' };
        const response = await handler(event, context);

        expect(response.statusCode).toBe(400);
    });
});
```

### Integration Testing

```javascript
// tests/integration/categories.test.js
const axios = require('axios');

const API_URL = process.env.API_URL || 'http://localhost:3000';
const TEST_ORG_ID = 'test-org-integration';

describe('Categories API Integration Tests', () => {
    let createdCategoryId;

    it('should create a new category', async () => {
        const response = await axios.post(
            `${API_URL}/organizations/${TEST_ORG_ID}/categories`,
            {
                name: 'Integration Test Category',
                description: 'Created by integration test'
            }
        );

        expect(response.status).toBe(201);
        expect(response.data.data.categoryId).toBeDefined();
        
        createdCategoryId = response.data.data.categoryId;
    });

    it('should retrieve the created category', async () => {
        const response = await axios.get(
            `${API_URL}/organizations/${TEST_ORG_ID}/categories/${createdCategoryId}`
        );

        expect(response.status).toBe(200);
        expect(response.data.data.name).toBe('Integration Test Category');
    });

    it('should list categories for the organization', async () => {
        const response = await axios.get(
            `${API_URL}/organizations/${TEST_ORG_ID}/categories`
        );

        expect(response.status).toBe(200);
        expect(Array.isArray(response.data.data.items)).toBe(true);
    });

    afterAll(async () => {
        // Cleanup: Delete test category
        if (createdCategoryId) {
            await axios.delete(
                `${API_URL}/organizations/${TEST_ORG_ID}/categories/${createdCategoryId}`
            );
        }
    });
});
```

### Running Tests

```bash
# Run all unit tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- tests/unit/handlers/categories/create.test.js

# Run integration tests
npm run test:integration

# Run tests in watch mode
npm run test:watch
```

---

## Logging & Debugging

### Structured Logging

```javascript
// src/lib/logging/logger.js
const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
};

const currentLevel = LOG_LEVELS[process.env.LOG_LEVEL] || LOG_LEVELS.INFO;

const formatMessage = (level, message, metadata = {}) => {
    return JSON.stringify({
        timestamp: new Date().toISOString(),
        level,
        message,
        service: 'aws-insight-category-api',
        ...metadata
    });
};

exports.logger = {
    debug: (message, metadata) => {
        if (currentLevel <= LOG_LEVELS.DEBUG) {
            console.log(formatMessage('DEBUG', message, metadata));
        }
    },
    info: (message, metadata) => {
        if (currentLevel <= LOG_LEVELS.INFO) {
            console.log(formatMessage('INFO', message, metadata));
        }
    },
    warn: (message, metadata) => {
        if (currentLevel <= LOG_LEVELS.WARN) {
            console.warn(formatMessage('WARN', message, metadata));
        }
    },
    error: (message, metadata) => {
        if (currentLevel <= LOG_LEVELS.ERROR) {
            console.error(formatMessage('ERROR', message, metadata));
        }
    }
};
```

### CloudWatch Logs Insights Queries

```sql
-- Find all errors in the last hour
fields @timestamp, @message, @requestId
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

-- Track request duration
fields @timestamp, @requestId, @duration
| filter @type = "REPORT"
| stats avg(@duration), max(@duration), min(@duration) by bin(5m)

-- Find specific request
fields @timestamp, @message
| filter @requestId = "your-request-id"
| sort @timestamp asc
```

### Local Debugging

```bash
# Debug Lambda locally with SAM CLI
sam local invoke CreateCategoryFunction \
    --event events/create-category.json \
    --debug

# Enable verbose logging
export LOG_LEVEL=DEBUG
sam local start-api

# Use VS Code debugger
# Add to .vscode/launch.json:
{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "node",
            "request": "attach",
            "name": "Attach to SAM CLI",
            "address": "localhost",
            "port": 5858,
            "localRoot": "${workspaceRoot}",
            "remoteRoot": "/var/task"
        }
    ]
}
```

### Common Debugging Scenarios

| Issue | Diagnostic Steps |
|-------|-----------------|
| 502 Bad Gateway | Check Lambda logs for unhandled exceptions |
| Timeout errors | Increase Lambda timeout, check DynamoDB latency |
| Permission denied | Verify IAM role policies |
| Data not found | Verify partition/sort key values |
| Validation errors | Check request payload against schema |

---

## Additional Resources

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)

For questions or issues, contact the platform team or create an issue in the repository.