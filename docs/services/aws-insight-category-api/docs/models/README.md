# Data Models Overview

## Introduction

The AWS Insight Category API uses a collection of data models to manage insight categories and templates within a multi-tenant architecture. All persistent data is stored in DynamoDB using a single-table design pattern, with partition keys (PK) and sort keys (SK) enabling efficient querying and versioning.

## Data Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INSIGHTS_TABLE (DynamoDB)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐       ┌─────────────────────┐             │
│  │     Categories      │       │      Templates      │             │
│  │  (Per Organization) │       │   (Shared, orgId=0) │             │
│  │                     │       │                     │             │
│  │  PK: category/      │       │  PK: category/      │             │
│  │      {orgId}/       │       │      0/{templateKey}│             │
│  │      {categoryKey}  │       │                     │             │
│  └─────────────────────┘       └─────────────────────┘             │
│           │                              │                          │
│           └──────────┬───────────────────┘                          │
│                      ▼                                              │
│         ┌─────────────────────┐                                     │
│         │  Version History    │                                     │
│         │  SK: v{n}/{ts}      │                                     │
│         │  SK: v0/{ts} = latest│                                    │
│         └─────────────────────┘                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Model Categories

The API's data models are organized into the following categories:

| Category | Description | Models |
|----------|-------------|--------|
| **Domain Models** | Core business entities stored in DynamoDB | Category, CategoryTemplate |
| **Request Models** | Structures for API input validation | CategoryCreateRequest, CategoryUpdateRequest, CategoryEventBody, EventParams |
| **Response Models** | Formatted data returned to clients | CategoryListResponse, TemplateListResponse, ApiResponse |
| **Constants & Enums** | Standardized values and labels | HttpStatusCodes, LogLabel |

## Detailed Documentation

For comprehensive documentation of each model, refer to the following files:

### Category Models

📄 **[Category Models](./models/category.md)**
- Category (primary domain model)
- CategoryCreateRequest
- CategoryUpdateRequest
- CategoryListResponse
- CategoryEventBody
- EventParams

### Template Models

📄 **[Template Models](./models/template.md)**
- CategoryTemplate
- TemplateListResponse

## Key Concepts

### Multi-Tenancy

The API supports multi-tenant operations through organization-scoped partition keys:

- **Organization Categories**: `PK = category/{orgId}/{categoryKey}`
- **Shared Templates**: `PK = category/0/{templateKey}` (orgId `0` reserved for templates)

### Versioning Strategy

All categories and templates support version history:

| Sort Key Pattern | Purpose |
|------------------|---------|
| `v0/{timestamp}` | Always points to the **latest** version |
| `v{n}/{timestamp}` | Historical version `n` created at `timestamp` |

The `v0` record includes a `latest` field indicating the current version number.

### Entity Relationships

```
┌──────────────────┐         ┌──────────────────┐
│ CategoryTemplate │ ──────> │     Category     │
│   (Blueprint)    │ creates │  (Organization)  │
└──────────────────┘         └──────────────────┘
                                     │
                                     │ has many
                                     ▼
                             ┌──────────────────┐
                             │  Version History │
                             │   (SK: v{n}/...)  │
                             └──────────────────┘
```

- **Templates → Categories**: Templates (orgId=0) can be used as blueprints to create organization-specific categories
- **Categories → Versions**: Each category maintains a complete version history for audit and rollback purposes

### Request/Response Flow

```
Client Request                    Server Response
     │                                  ▲
     ▼                                  │
┌─────────────────┐            ┌─────────────────┐
│ CategoryCreate  │            │  ApiResponse    │
│ Request         │            │  {statusCode,   │
│ CategoryUpdate  │            │   body}         │
│ Request         │            └─────────────────┘
└─────────────────┘                    ▲
     │                                  │
     ▼                                  │
┌─────────────────┐            ┌─────────────────┐
│  EventParams    │ ────────>  │ CategoryList    │
│  (Lambda Event) │            │ Response        │
└─────────────────┘            │ TemplateList    │
                               │ Response        │
                               └─────────────────┘
```

## Common Field Patterns

### Timestamp Fields

| Field | Type | Description |
|-------|------|-------------|
| `createdAt` | `number` | Unix timestamp (milliseconds) of creation |
| `modifiedAt` | `number` | Unix timestamp (milliseconds) of last update |

### Audit Fields

| Field | Type | Description |
|-------|------|-------------|
| `createdBy` | `number/string` | User ID who created the record |
| `modifiedBy` | `number/string` | User ID who last modified the record |

### Key Fields

| Field | Type | Format |
|-------|------|--------|
| `PK` | `string` | `category/{orgId}/{categoryKey}` |
| `SK` | `string` | `v{version}/{unixTimestamp}` |
| `orgId` | `string` | `category/{orgId}` (prefixed) |

## Storage Considerations

- **Single Table Design**: All models share the `INSIGHTS_TABLE` in DynamoDB
- **Access Patterns**: Optimized for querying by organization, category key, and version
- **Sparse Indexes**: Not all fields are present on all record types (e.g., `latest` only on v0 records)

## See Also

- [API Endpoints Documentation](./endpoints.md)
- [Authentication & Authorization](./authentication.md)
- [Error Handling](./errors.md)