# API Reference Overview

## Introduction

The Platform Service Gateway provides a unified API layer for integrating with multiple CRM platforms and enterprise systems. Built on the CodeIgniter PHP framework with Docker support, this gateway abstracts the complexity of connecting to disparate systems behind a consistent, RESTful interface.

The API supports integration with:
- **Salesforce** - Full CRM data access via SOQL/SOSL queries
- **Microsoft Dynamics** - CRM data operations with metadata support
- **Zendesk** - Ticket, user, and organization management
- **Oracle Fusion** - Enterprise CRM data queries
- **SugarCRM** - CRM platform integration
- **GoodData** - Analytics and dataset management
- **Custom Data Sources** - Flexible integration with proprietary systems
- **Workbooks** - Business application platform integration

## Base URL

```
https://{your-gateway-host}/
```

## Authentication

The Service Gateway supports multiple authentication methods depending on the target platform and endpoint category:

### Token-Based Authentication

Most endpoints require a session token obtained through the authentication flow:

```bash
# Create authentication context
curl -X PUT "https://api.example.com/sgapi_auth/auth" \
  -H "Content-Type: application/json" \
  -d '{"credentials": {...}}'
```

The returned token must be included in subsequent requests as a path parameter.

### Platform-Specific Authentication

| Platform | Authentication Method |
|----------|----------------------|
| Salesforce | OAuth 2.0 / Session Token |
| Microsoft Dynamics | OAuth 2.0 |
| Zendesk | API Token / OAuth |
| Oracle Fusion | Basic Auth / OAuth |
| GoodData | Temporary Token |
| Workbooks | Session-based login |
| Custom | Configurable per integration |

### Session Management

```bash
# Create session context
PUT /sgapi_auth/auth

# Destroy session context
DELETE /sgapi_auth/auth/{token}

# Modify existing context
POST /sgapi_auth/auth/{token}
```

## API Documentation Index

| Category | Endpoints | Documentation |
|----------|-----------|---------------|
| Microsoft Dynamics | 4 | [msdynamics-endpoints.md](msdynamics-endpoints.md) |
| Salesforce | 10+ | [salesforce-endpoints.md](salesforce-endpoints.md) |
| Zendesk | 3 | [zendesk-endpoints.md](zendesk-endpoints.md) |
| Custom Integration | 6 | [custom-endpoints.md](custom-endpoints.md) |
| Generic API | 3 | [generic-endpoints.md](generic-endpoints.md) |
| Feed Management | 10 | [feed-endpoints.md](feed-endpoints.md) |
| Response Models | - | [api-response-models.md](../models/api-response-models.md) |

## Endpoint Categories

### Microsoft Dynamics Endpoints (`/msdynamics/*`)

Query, create, update, and retrieve metadata from Microsoft Dynamics CRM. Supports conditional queries with field selection, ordering, and pagination.

**Key Operations:** Query data, Get metadata, Add objects, Update objects

### Salesforce Endpoints (`/sgapi/*`)

Comprehensive Salesforce integration supporting SOQL/SOSL queries, record CRUD operations, custom API calls, and metadata management.

**Key Operations:** Query (structured/raw), Add/Update/Delete records, Metadata queries, Custom calls

### Zendesk Endpoints (`/zendesk/*`)

Manage Zendesk tickets, users, and organizations through a simplified interface.

**Key Operations:** Query data, Create objects, Update objects

### Custom Integration Endpoints (`/custom/*`)

Flexible integration layer for custom application servers with configurable query and data manipulation capabilities.

**Key Operations:** Query (structured/raw), Add/Update objects, Get object/field lists

### Generic API Endpoints (`/api/*`)

Token-authenticated data operations that route to the appropriate backend based on feed configuration.

**Key Operations:** Query source, Raw query, Add data

### Feed Management Endpoints (`/feed/*`)

Virtual inbox management system for processing message-based data feeds with navigation and filtering capabilities.

**Key Operations:** Auth, Refresh, Filter, Navigate, Read messages, Mark as read

### Workbooks API Endpoints

Direct integration with the Workbooks business platform supporting full CRUD operations and batch processing.

**Key Operations:** Login/Logout, Get/Create/Update/Delete, Batch operations

### GoodData Endpoints (`/gdc/*`)

Analytics platform integration for dataset management and schema retrieval.

**Key Operations:** Get token, List datasets, Get schema

### Statistics & Monitoring (`/stats/*`)

Access cached statistical data for monitoring gateway performance and usage.

## Common Request Patterns

### Query Pattern

Most platforms support a standardized query pattern:

```bash
GET /{platform}/query?object={object}&conditions={conditions}&fields={fields}&orderby={orderby}&limit={limit}
```

| Parameter | Description |
|-----------|-------------|
| `object` | Target object/entity type |
| `conditions` | Filter conditions (platform-specific syntax) |
| `fields` | Comma-separated list of fields to return |
| `orderby` | Sort order specification |
| `limit` | Maximum records to return |

### Raw Query Pattern

For platforms supporting native query languages:

```bash
GET /{platform}/queryraw?query={raw_query}
```

### CRUD Operations

| Operation | Method | Pattern |
|-----------|--------|---------|
| Create | POST | `/{platform}/add` |
| Read | GET | `/{platform}/query` |
| Update | PUT | `/{platform}/update` |
| Delete | DELETE | `/{platform}/deleterecord` (where supported) |

## Response Format

All API responses follow a consistent JSON structure:

```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "count": 100,
    "offset": 0,
    "total": 250
  }
}
```

For detailed response models, see [api-response-models.md](../models/api-response-models.md).

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Invalid or expired token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Unknown endpoint or resource |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |
| `502` | Bad Gateway - Target platform unavailable |
| `503` | Service Unavailable |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "The provided authentication token has expired",
    "details": {}
  }
}
```

### 404 Error Handling

Unknown API calls are routed to the error handler:

```
GET /e404
GET /e404/index
```

Returns standardized error response for unrecognized endpoints.

## Rate Limiting

Rate limits vary by target platform and are generally inherited from the underlying service:

| Platform | Typical Limit | Window |
|----------|---------------|--------|
| Salesforce | 15,000 | 24 hours |
| Microsoft Dynamics | 6,000 | 5 minutes |
| Zendesk | 700 | 1 minute |
| GoodData | Varies | Per project |

The gateway returns `429 Too Many Requests` when limits are exceeded. Check the `Retry-After` header for backoff timing.

## Pagination

For large result sets, use limit and offset parameters:

```bash
GET /msdynamics/query?object=Contact&limit=100&offset=200
```

Response metadata includes pagination information:

```json
{
  "metadata": {
    "count": 100,
    "offset": 200,
    "total": 1500,
    "hasMore": true
  }
}
```

## Best Practices

1. **Session Management** - Reuse authentication tokens; avoid creating new sessions for each request
2. **Field Selection** - Request only needed fields to improve performance
3. **Batch Operations** - Use batch endpoints (where available) for bulk operations
4. **Error Handling** - Implement exponential backoff for rate limit errors
5. **Metadata Caching** - Cache object/field metadata locally to reduce API calls
6. **Connection Pooling** - Maintain persistent connections for high-throughput scenarios

## SDK & Client Libraries

For programmatic access, consider using platform-specific SDKs in conjunction with this gateway, or implement a client wrapper using the patterns documented in this reference.

## Support

For API issues, consult the detailed endpoint documentation linked above or contact your system administrator.