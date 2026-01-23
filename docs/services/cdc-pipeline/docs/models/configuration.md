# Configuration Models

This document covers the configuration-related data models used in the CDC Pipeline, including environment settings, redaction configuration, and system parameters.

## Overview

Configuration models in the CDC Pipeline define how the system behaves across different environments, how sensitive data is protected through redaction, and how external services (SSM, DynamoDB) are configured. These models are essential for:

- **Environment Management**: Defining deployment contexts (LOCAL, DEV, QA, PRD)
- **Data Protection**: Configuring redaction rules for sensitive information
- **Service Configuration**: Managing database credentials and AWS service parameters
- **Logging Configuration**: Setting up structured logging with redaction support

## Entity Relationships

```
┌─────────────────────┐     ┌─────────────────────┐
│    Environment      │     │    EnvVariables     │
│      (Enum)         │────▶│  (Runtime Config)   │
└─────────────────────┘     └─────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────────┐
                            │  SSMConfigParams    │
                            └─────────────────────┘
                                      │
                                      ▼
┌─────────────────────┐     ┌─────────────────────┐
│ ParameterHandlerProps│◀───│ SSMDBParametersName │
└─────────────────────┘     └─────────────────────┘
          │                           │
          ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ ParameterResponse   │     │ DatabaseCredentials │
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│  RedactionConfig    │────▶│  ObjectRedaction    │
└─────────────────────┘     └─────────────────────┘
          │                           │
          ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│  LoggerConfigOptions│     │   RegexRedaction    │
└─────────────────────┘     └─────────────────────┘
```

---

## Environment Models

### Environment

Enum representing deployment environments for the CDC Pipeline.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| LOCAL | string | Yes | Local development environment |
| DEV | string | Yes | Development environment |
| QA | string | Yes | QA/Testing environment |
| PRD | string | Yes | Production environment |

**Usage Context:**
- Determines service endpoints and configurations
- Controls logging verbosity and redaction settings
- Affects feature flags and behavior

**Example:**
```json
{
  "environment": "DEV"
}
```

**Common Use Cases:**
- Conditional configuration loading based on deployment target
- Environment-specific endpoint resolution
- Debug/verbose logging enablement in non-production environments

---

### EnvVariables

Environment configuration variables required for CDC Pipeline operation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| serviceName | string | Yes | Name of the service (e.g., "cdc-pipeline") |
| eventBusARN | string | Yes | ARN of the target EventBridge bus |
| eventBridgeEndpoint | string | Yes | EventBridge endpoint URL |
| dynamoHashTableName | string | Yes | DynamoDB table name for deduplication hashing |

**Validation Rules:**
- `serviceName` must be a non-empty string
- `eventBusARN` must be a valid AWS ARN format
- `eventBridgeEndpoint` must be a valid URL
- `dynamoHashTableName` must match DynamoDB naming conventions

**Example:**
```json
{
  "serviceName": "cdc-pipeline",
  "eventBusARN": "arn:aws:events:us-east-1:123456789012:event-bus/cdc-events",
  "eventBridgeEndpoint": "https://events.us-east-1.amazonaws.com",
  "dynamoHashTableName": "cdc-pipeline-dedup-table"
}
```

**Relationships:**
- Used by Lambda handlers to initialize services
- Referenced by EventBridge client for publishing events
- Consumed by DynamoDB client for deduplication operations

---

## Redaction Models

### IRedactor

Generic interface for implementing redaction strategies.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| redact | function<T> | Yes | Method to redact sensitive data from input of type T |

**Usage Context:**
- Implemented by concrete redaction classes
- Provides type-safe redaction across different data structures

**Example Implementation:**
```typescript
class MyRedactor implements IRedactor {
  redact<T>(data: T): T {
    // Redaction logic
    return redactedData;
  }
}
```

---

### RegexRedaction

Configuration for regex-based pattern matching and redaction.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| replaceWith | string | Yes | String to replace matched content with |
| regexPattern | RegExp | Yes | Regular expression pattern to identify sensitive data |

**Validation Rules:**
- `regexPattern` must be a valid JavaScript RegExp
- `replaceWith` should be a safe replacement string (typically asterisks or "[REDACTED]")

**Example:**
```json
{
  "replaceWith": "[REDACTED]",
  "regexPattern": "/\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/gi"
}
```

**Common Patterns:**
- Email addresses
- Phone numbers
- Credit card numbers
- Social Security numbers

---

### RedactionConfig

Configuration options for the redaction service with pattern definitions and feature flags.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| keyPatterns | RegExp[] | No | Regex patterns to match sensitive keys in objects |
| overrideKeyPatterns | boolean | No | If true, replaces default key patterns; otherwise merges |
| piiPatterns | RegExp[] | No | Regex patterns to match PII data values |
| overridePIIPatterns | boolean | No | If true, replaces default PII patterns; otherwise merges |
| whiteListKeys | string[] | No | Keys to explicitly exclude from redaction |
| overrideWhitelistKeys | boolean | No | If true, replaces default whitelist; otherwise merges |
| enablePIIVerification | boolean | No | Enable scanning values for PII patterns |
| enableBase64Verification | boolean | No | Enable detection and handling of base64-encoded content |
| enableKeyVerification | boolean | No | Enable key-based redaction |

**Validation Rules:**
- All pattern arrays must contain valid RegExp objects
- Boolean flags default to `false` if not specified
- Whitelist keys are case-sensitive

**Example:**
```json
{
  "keyPatterns": ["/password/i", "/secret/i", "/apiKey/i", "/token/i"],
  "overrideKeyPatterns": false,
  "piiPatterns": ["/\\b\\d{3}-\\d{2}-\\d{4}\\b/", "/\\b\\d{16}\\b/"],
  "overridePIIPatterns": false,
  "whiteListKeys": ["publicId", "displayName", "createdAt"],
  "overrideWhitelistKeys": false,
  "enablePIIVerification": true,
  "enableBase64Verification": true,
  "enableKeyVerification": true
}
```

**Relationships:**
- Consumed by `ObjectRedaction` for runtime configuration
- Used by `LoggerConfigOptions` for logging redaction
- Applied across all CDC record processing

---

### ObjectRedaction

Runtime redaction configuration with resolved patterns ready for execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| piiPatterns | RegExp[] | Yes | Resolved PII patterns after merging defaults |
| keyPatterns | RegExp[] | Yes | Resolved key patterns after merging defaults |
| whiteListKeys | string[] | Yes | Resolved whitelist keys after merging defaults |
| obfuscationString | string | Yes | String used to replace sensitive data (e.g., "****") |
| enablePIIVerification | boolean | Yes | Whether PII verification is active |
| enableBase64Verification | boolean | Yes | Whether base64 verification is active |
| enableKeyVerification | boolean | Yes | Whether key verification is active |

**Validation Rules:**
- `obfuscationString` must not be empty
- All pattern arrays must be initialized (can be empty)
- All boolean flags must have explicit values

**Example:**
```json
{
  "piiPatterns": [
    "/\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/gi",
    "/\\b\\d{3}-\\d{2}-\\d{4}\\b/g"
  ],
  "keyPatterns": [
    "/password/i",
    "/secret/i",
    "/token/i",
    "/authorization/i"
  ],
  "whiteListKeys": ["id", "orgId", "userId", "timestamp"],
  "obfuscationString": "[REDACTED]",
  "enablePIIVerification": true,
  "enableBase64Verification": true,
  "enableKeyVerification": true
}
```

**Relationships:**
- Created from `RedactionConfig` with defaults merged
- Used directly by redaction engine during processing
- Applied to both logging output and event payloads

---

## SSM Parameter Models

### SSMConfigParams

AWS SSM client configuration for parameter retrieval.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| region | string | Yes | AWS region (e.g., "us-east-1") |
| endpoint | string | No | Custom SSM endpoint URL for local development |

**Validation Rules:**
- `region` must be a valid AWS region identifier
- `endpoint` if provided, must be a valid URL

**Example:**
```json
{
  "region": "us-east-1",
  "endpoint": "http://localhost:4566"
}
```

**Common Use Cases:**
- Production: Region only, using default AWS endpoint
- Local development: Custom endpoint pointing to LocalStack

---

### ParameterHandlerProps

Properties for SSM parameter retrieval operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| parameterName | string | Yes | Full SSM parameter path/name |
| version | number | No | Specific parameter version to retrieve |
| label | string | No | Parameter label for versioned parameters |
| withDecryption | boolean | No | Whether to decrypt SecureString parameters |

**Validation Rules:**
- `parameterName` must follow SSM path conventions (e.g., `/cdc-pipeline/database/host`)
- `version` if provided, must be a positive integer
- `withDecryption` should be `true` for sensitive parameters

**Example:**
```json
{
  "parameterName": "/cdc-pipeline/database/password",
  "version": 3,
  "label": "production",
  "withDecryption": true
}
```

---

### ParameterOptions

Optional parameters for SSM retrieval (excludes parameterName).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | number | No | Specific parameter version |
| label | string | No | Parameter label |
| withDecryption | boolean | No | Decrypt SecureString parameters |

**Example:**
```json
{
  "withDecryption": true
}
```

---

### ParameterResponse

Response structure from SSM parameter retrieval.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | The parameter name that was retrieved |
| value | string | Yes | The parameter value (decrypted if requested) |

**Example:**
```json
{
  "name": "/cdc-pipeline/database/host",
  "value": "database.cluster-abc123.us-east-1.rds.amazonaws.com"
}
```

---

### SSMDBParametersName

Constant object mapping database credential parameter paths in SSM.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| HOST | string | Yes | SSM path for database host |
| PORT | string | Yes | SSM path for database port |
| DATABASE | string | Yes | SSM path for database name |
| PASSWORD | string | Yes | SSM path for database password |
| USERNAME | string | Yes | SSM path for database username |

**Example:**
```json
{
  "HOST": "/cdc-pipeline/database/host",
  "PORT": "/cdc-pipeline/database/port",
  "DATABASE": "/cdc-pipeline/database/name",
  "PASSWORD": "/cdc-pipeline/database/password",
  "USERNAME": "/cdc-pipeline/database/username"
}
```

**Relationships:**
- Used by credential loading functions to construct `DatabaseCredentials`
- Referenced during service initialization

---

## Database Configuration Models

### DatabaseCredentials

Database connection credentials assembled from SSM parameters.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| host | string | Yes | Database host address |
| port | number | Yes | Database port number |
| database | string | Yes | Database name |
| username | string | Yes | Database username |
| password | string | Yes | Database password |

**Validation Rules:**
- `host` must be a valid hostname or IP address
- `port` must be between 1 and 65535
- `database`, `username`, and `password` must be non-empty strings

**Example:**
```json
{
  "host": "database.cluster-abc123.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "database": "cdc_pipeline",
  "username": "cdc_service_account",
  "password": "[REDACTED]"
}
```

**Security Notes:**
- Never log password values
- Always use `withDecryption: true` when retrieving from SSM
- Credentials should be cached with appropriate TTL

---

### DatabaseInstanceStatus

Enum for database instance availability status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AVAILABLE | string | Yes | Database is available and accepting connections |
| UNAVAILABLE | string | Yes | Database is unavailable |

**Example:**
```json
{
  "status": "AVAILABLE"
}
```

---

### PreparedQuery

Definition for a prepared SQL query.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| queryName | string | Yes | Unique name identifier for the query |
| queryStatement | string | Yes | SQL query statement with parameter placeholders |

**Validation Rules:**
- `queryName` should be unique within the application
- `queryStatement` must be valid SQL

**Example:**
```json
{
  "queryName": "getOrgByGroupId",
  "queryStatement": "SELECT org_id FROM group_maps WHERE group_id = $1"
}
```

---

## Logging Configuration Models

### LoggerConfigOptions

Configuration options for the structured logger service.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| service | string | Yes | Service name for log attribution |
| disableRedaction | boolean | No | Flag to disable all redaction (for debugging) |
| redactionConfig | RedactionConfig | No | Configuration for redaction rules |

**Validation Rules:**
- `service` should match the deployed service name
- `disableRedaction` should only be `true` in local development

**Example:**
```json
{
  "service": "cdc-pipeline",
  "disableRedaction": false,
  "redactionConfig": {
    "enablePIIVerification": true,
    "enableKeyVerification": true,
    "enableBase64Verification": true
  }
}
```

---

### LoggerRedaction

Subset of logger configuration specifically for redaction settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| disableRedaction | boolean | No | Flag to disable redaction |
| redactionConfig | RedactionConfig | No | Redaction configuration rules |

**Example:**
```json
{
  "disableRedaction": false,
  "redactionConfig": {
    "enablePIIVerification": true
  }
}
```

---

## DynamoDB Configuration Models

### DynamoDBActionParams

Parameters for DynamoDB operations used in deduplication and state management.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| queryDescription | string | Yes | Description of the query for logging/debugging |
| tableName | string | Yes | DynamoDB table name |
| pk | string | Yes | Primary key value |
| additionalColumns | Map<string, unknown> | No | Additional columns to include in the operation |
| disableLogging | boolean | No | Flag to disable query logging (for high-frequency operations) |

**Validation Rules:**
- `tableName` must match DynamoDB naming conventions
- `pk` must be a non-empty string
- `additionalColumns` values must be DynamoDB-compatible types

**Example:**
```json
{
  "queryDescription": "Check deduplication hash",
  "tableName": "cdc-pipeline-dedup-table",
  "pk": "event-hash-abc123def456",
  "additionalColumns": {
    "ttl": 1704067200,
    "processedAt": "2024-01-01T00:00:00Z"
  },
  "disableLogging": false
}
```

---

## Health Check Models

### EventBridgeHC

Enum for EventBridge health check status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OK | string | Yes | EventBridge is healthy and accepting events |
| IN_ALARM | string | Yes | EventBridge is in alarm state |
| UNKNOWN | string | Yes | Health status cannot be determined |

**Example:**
```json
{
  "healthStatus": "OK"
}
```

**Common Use Cases:**
- Health check endpoints
- Circuit breaker decisions
- Monitoring and alerting

---

## HTTP Configuration Models

### HeaderItem

HTTP header key-value pair for request configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | HTTP header name |
| value | string | Yes | HTTP header value |

**Example:**
```json
{
  "name": "Authorization",
  "value": "Bearer [REDACTED]"
}
```

---

### IRequester

Interface for HTTP requester implementations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| addHeaders | function | Yes | Method to add HTTP headers to requests |
| get | function<T> | Yes | Generic GET request method returning type T |

**Example Implementation:**
```typescript
class HttpRequester implements IRequester {
  private headers: HeaderItem[] = [];
  
  addHeaders(headers: HeaderItem[]): void {
    this.headers.push(...headers);
  }
  
  async get<T>(url: string): Promise<T> {
    // HTTP GET implementation
  }
}
```

---

## Complete Configuration Example

Below is a comprehensive example showing how configuration models work together:

```json
{
  "environment": "DEV",
  "envVariables": {
    "serviceName": "cdc-pipeline",
    "eventBusARN": "arn:aws:events:us-east-1:123456789012:event-bus/cdc-events",
    "eventBridgeEndpoint": "https://events.us-east-1.amazonaws.com",
    "dynamoHashTableName": "cdc-pipeline-dedup-dev"
  },
  "ssmConfig": {
    "region": "us-east-1"
  },
  "databaseCredentials": {
    "host": "dev-db.cluster-abc123.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "database": "cdc_pipeline_dev",
    "username": "cdc_service",
    "password": "[RETRIEVED_FROM_SSM]"
  },
  "loggerConfig": {
    "service": "cdc-pipeline",
    "disableRedaction": false,
    "redactionConfig": {
      "enablePIIVerification": true,
      "enableKeyVerification": true,
      "enableBase64Verification": true,
      "whiteListKeys": ["id", "orgId", "userId", "timestamp", "recordType"]
    }
  },
  "redactionConfig": {
    "keyPatterns": ["/password/i", "/secret/i", "/token/i", "/authorization/i", "/apiKey/i"],
    "piiPatterns": [
      "/\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/gi",
      "/\\b\\d{3}-\\d{2}-\\d{4}\\b/g",
      "/\\b\\d{16}\\b/g"
    ],
    "obfuscationString": "[REDACTED]"
  }
}
```

---

## Related Documentation

- [Records Models](./records.md) - Documentation for CDC record types that consume these configurations
- [Events Models](./events.md) - Documentation for event structures published to EventBridge
- [Models Overview](./README.md) - High-level overview of all data models