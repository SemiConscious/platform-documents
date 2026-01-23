# Category Models

This document provides detailed documentation for Category and related request/response models in the aws-insight-category-api service.

## Overview

Categories are the core data model for organizing and classifying insights. They are stored in DynamoDB with a versioning system that maintains historical records while providing quick access to the latest version.

## Entity Relationship Diagram

```
┌─────────────────────────┐
│       Category          │
│─────────────────────────│
│ PK (partition key)      │───────┐
│ SK (sort key)           │       │
│ orgId                   │       │
│ name                    │       │
│ description             │       │
│ data                    │       │
│ type                    │       │
│ trigger                 │       │
│ language                │       │
│ enabled                 │       │
│ createdAt/By            │       │
│ modifiedAt/By           │       │
│ latest                  │       │
└─────────────────────────┘       │
         │                         │
         │ transforms to           │
         ▼                         │
┌─────────────────────────┐       │
│  CategoryListResponse   │       │
│─────────────────────────│       │
│ categoryKey             │◄──────┘
│ name                    │   (extracted from PK)
│ description             │
│ language                │
│ enabled                 │
│ createdBy               │
└─────────────────────────┘
         ▲
         │ created from
         │
┌─────────────────────────┐
│  CategoryCreateRequest  │
│─────────────────────────│
│ categoryName            │
│ description             │
│ definitionString        │
│ definition              │
│ type                    │
│ trigger                 │
│ language                │
│ enabled                 │
└─────────────────────────┘
```

---

## Core Models

### Category

The primary DynamoDB model for insight categories stored in the `INSIGHTS_TABLE`. Categories use a versioning system where `v0` always represents the latest version.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `PK` | string | Yes | Partition key, format: `category/{orgId}/{categoryKey}` |
| `SK` | string | Yes | Sort key, format: `v{version}/{unixTimestamp}` where `v0` is latest |
| `name` | string | Yes | Category name (must be unique per organization) |
| `description` | string | No | Human-readable category description |
| `orgId` | string | Yes | Organization identifier, format: `category/{orgId}` |
| `definitionString` | string | No | Category definition as a string representation |
| `data` | object | No | Category definition data object (from `eventBody.definition`) |
| `type` | string | No | Category type classification |
| `trigger` | string | No | Category trigger mechanism |
| `language` | string | No | Language setting for the category |
| `createdAt` | number | Yes | Unix timestamp of creation |
| `createdBy` | string/number | Yes | User ID who created the category |
| `modifiedAt` | number | Yes | Unix timestamp of last modification |
| `modifiedBy` | string/number | Yes | User ID who last modified the category |
| `enabled` | boolean | No | Whether the category is enabled (defaults to true) |
| `latest` | number | No | Version number for the latest record (only on v0 records) |

#### Validation Rules

- `PK` must follow the format `category/{orgId}/{categoryKey}`
- `SK` must follow the format `v{version}/{unixTimestamp}`
- `name` must be unique within an organization
- `orgId` must include the `category/` prefix
- `createdAt` and `modifiedAt` must be valid Unix timestamps

#### Key Structure

The versioning system uses a dual-key approach:
- **Latest Version**: `SK = v0/{timestamp}` - Always points to the current version
- **Historical Versions**: `SK = v{n}/{timestamp}` - Where `n` is an incrementing version number

#### Example JSON

```json
{
  "PK": "category/12345/sentiment-analysis",
  "SK": "v0/1699876543",
  "name": "Sentiment Analysis",
  "description": "Analyzes customer sentiment from call recordings",
  "orgId": "category/12345",
  "definitionString": "{\"threshold\": 0.7, \"model\": \"nlp-v2\"}",
  "data": {
    "threshold": 0.7,
    "model": "nlp-v2",
    "outputFormat": "detailed"
  },
  "type": "analysis",
  "trigger": "post-recording",
  "language": "en-US",
  "createdAt": 1699876543,
  "createdBy": 789,
  "modifiedAt": 1699876543,
  "modifiedBy": 789,
  "enabled": true,
  "latest": 1
}
```

---

## Request Models

### CategoryCreateRequest

Request body structure for creating a new category via the API.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categoryName` | string | Yes | Name for the new category |
| `description` | string | No | Category description |
| `definitionString` | string | No | Category definition as a string |
| `definition` | object | No | Category definition object (stored as `data` field) |
| `type` | string | No | Category type classification |
| `trigger` | string | No | Category trigger mechanism |
| `language` | string | No | Category language setting |
| `enabled` | boolean | No | Whether the category is enabled (defaults to true) |

#### Validation Rules

- `categoryName` is required and must be non-empty
- `categoryName` must be unique within the organization
- At least one of `definitionString` or `definition` should be provided

#### Example JSON

```json
{
  "categoryName": "Customer Satisfaction Score",
  "description": "Calculates CSAT score based on conversation analysis",
  "definitionString": "{\"scoreRange\": [1, 5], \"factors\": [\"tone\", \"resolution\"]}",
  "definition": {
    "scoreRange": [1, 5],
    "factors": ["tone", "resolution"],
    "weights": {
      "tone": 0.4,
      "resolution": 0.6
    }
  },
  "type": "scoring",
  "trigger": "real-time",
  "language": "en-US",
  "enabled": true
}
```

---

### CategoryUpdateRequest

Request body structure for updating an existing category.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categoryName` | string | No | Updated category name |

#### Validation Rules

- If `categoryName` is provided, it must be unique within the organization
- At least one field must be provided for update

#### Example JSON

```json
{
  "categoryName": "Updated Category Name"
}
```

> **Note**: The CategoryUpdateRequest model shown here is minimal. In practice, updates typically include additional fields from CategoryCreateRequest (description, definition, type, trigger, language, enabled).

---

### CategoryEventBody

Internal request body structure used for creating/updating categories within Lambda handlers.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categoryName` | string | Yes | Name of the category |
| `description` | string | No | Category description |
| `definitionString` | string | No | Definition as string |
| `definition` | object | No | Definition data object |
| `type` | string | No | Category type |
| `trigger` | string | No | Category trigger |
| `language` | string | No | Language setting |
| `enabled` | boolean | No | Whether the category is enabled |

#### Example JSON

```json
{
  "categoryName": "Compliance Check",
  "description": "Ensures calls meet regulatory compliance requirements",
  "definitionString": "{\"regulations\": [\"GDPR\", \"PCI-DSS\"]}",
  "definition": {
    "regulations": ["GDPR", "PCI-DSS"],
    "strictMode": true,
    "alertThreshold": "critical"
  },
  "type": "compliance",
  "trigger": "post-recording",
  "language": "en-GB",
  "enabled": true
}
```

---

## Response Models

### CategoryListResponse

Response format returned when listing categories. This is a transformed view of the Category model optimized for list displays.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categoryKey` | string | Yes | Unique category identifier extracted from PK |
| `name` | string | Yes | Category name |
| `description` | string | No | Category description |
| `language` | string | No | Category language setting |
| `enabled` | boolean | No | Whether the category is enabled |
| `createdBy` | number | Yes | User ID who created the category |

#### Transformation Rules

- `categoryKey` is extracted from `PK` by removing the `category/{orgId}/` prefix
- Only essential fields are included for list performance

#### Example JSON

```json
{
  "categoryKey": "sentiment-analysis",
  "name": "Sentiment Analysis",
  "description": "Analyzes customer sentiment from call recordings",
  "language": "en-US",
  "enabled": true,
  "createdBy": 789
}
```

#### Example Array Response

```json
[
  {
    "categoryKey": "sentiment-analysis",
    "name": "Sentiment Analysis",
    "description": "Analyzes customer sentiment from call recordings",
    "language": "en-US",
    "enabled": true,
    "createdBy": 789
  },
  {
    "categoryKey": "compliance-check",
    "name": "Compliance Check",
    "description": "Ensures regulatory compliance",
    "language": "en-GB",
    "enabled": true,
    "createdBy": 456
  },
  {
    "categoryKey": "keyword-spotting",
    "name": "Keyword Spotting",
    "description": "Detects specific keywords in conversations",
    "language": "en-US",
    "enabled": false,
    "createdBy": 789
  }
]
```

---

## Supporting Models

### EventParams

Parameters extracted from Lambda events and used for routing and authorization.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | string | No | User ID (parsed to int, defaults to 0) |
| `organisationId` | string | Yes | Organization ID |
| `categoryKey` | string | No | Category unique identifier (for single-item operations) |
| `PK` | string | No | Full partition key for direct DynamoDB lookup |

#### Example JSON

```json
{
  "userId": "789",
  "organisationId": "12345",
  "categoryKey": "sentiment-analysis",
  "PK": "category/12345/sentiment-analysis"
}
```

---

## Common Use Cases

### Creating a New Category

1. Client sends `CategoryCreateRequest` to POST endpoint
2. System validates uniqueness of `categoryName` within organization
3. System generates `categoryKey` from `categoryName`
4. System creates `Category` record with `SK = v0/{timestamp}`

### Updating a Category

1. Client sends `CategoryUpdateRequest` to PUT endpoint with `categoryKey`
2. System retrieves current `v0` record
3. System copies current record to `v{n}/{timestamp}` (historical version)
4. System updates `v0` record with new data and increments `latest`

### Listing Categories

1. Client sends GET request with `organisationId`
2. System queries all `v0` records for the organization
3. System transforms `Category` records to `CategoryListResponse` format
4. Returns array of simplified category objects

---

## Related Documentation

- [Template Models](./template.md) - Documentation for CategoryTemplate and TemplateListResponse
- [Models Overview](./README.md) - High-level overview of all data models