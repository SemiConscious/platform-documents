# API Reference

Complete API documentation for the AWS Insight Category API.

## Overview

The AWS Insight Category API is a RESTful service for managing organization categories within the AWS Insight platform. Built on AWS Lambda and API Gateway with DynamoDB for data persistence, this API provides full CRUD operations for categories and access to category templates.

## Base URL

```
https://{api-gateway-id}.execute-api.{region}.amazonaws.com/{stage}
```

## Authentication

All API requests require authentication via AWS IAM or API Gateway authorizers. Include the appropriate authentication headers with each request:

| Header | Description |
|--------|-------------|
| `Authorization` | Bearer token or AWS Signature Version 4 |
| `x-api-key` | API key (if API key authentication is enabled) |

## Content Type

All requests and responses use JSON format:

```
Content-Type: application/json
```

## API Endpoints Summary

The API provides 6 endpoints organized into two main resource categories:

| Resource | Endpoints | Description |
|----------|-----------|-------------|
| **Categories** | 5 | Full CRUD operations for organization categories |
| **Templates** | 1 | Read-only access to category templates |

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/organisations/{organisationId}/categories` | Create a new category |
| `GET` | `/organisations/{organisationId}/categories` | List all categories |
| `GET` | `/organisations/{organisationId}/categories/{categoryKey}` | Get a single category |
| `PUT` | `/organisations/{organisationId}/categories/{categoryKey}` | Update a category |
| `DELETE` | `/organisations/{organisationId}/categories/{categoryKey}` | Delete a category |
| `GET` | `/templates` | List all templates |

## Detailed Documentation

For complete endpoint specifications including request/response examples, refer to the detailed documentation:

| Documentation | Description | Link |
|---------------|-------------|------|
| **Categories API** | Complete documentation for category CRUD operations | [docs/api/categories.md](categories.md) |
| **Templates API** | Documentation for retrieving category templates | [docs/api/templates.md](templates.md) |

## Common Patterns

### Resource Identification

Categories are identified using a composite key structure:

- **organisationId**: Unique identifier for the organization (path parameter)
- **categoryKey**: Unique identifier for the category within an organization (path parameter)

### Versioning

The API implements a versioning system for categories:

- Each category maintains a current version (`v0`) for quick lookups
- Historical versions are preserved for audit purposes
- Updates create new versions while maintaining data integrity

### Soft Deletes

Categories are soft-deleted rather than permanently removed:

- Deleted categories are marked with `isDeleted: true`
- A new version is created to record the deletion
- Soft-deleted categories can be filtered from query results

## Error Handling

The API returns standard HTTP status codes with consistent error response formats:

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `201` | Resource created |
| `400` | Bad request - Invalid input or validation error |
| `401` | Unauthorized - Authentication required |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not found - Resource does not exist |
| `409` | Conflict - Resource already exists (e.g., duplicate category name) |
| `500` | Internal server error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Category name already exists for this organisation"
  }
}
```

## Validation Rules

The API enforces the following validation rules:

| Rule | Description |
|------|-------------|
| **Unique Category Names** | Category names must be unique within an organization |
| **Required Fields** | All required fields must be provided during creation |
| **Organisation Scope** | Categories are scoped to specific organizations |

## Rate Limiting

API requests are subject to rate limiting to ensure service stability:

| Limit Type | Value |
|------------|-------|
| Requests per second | Determined by API Gateway configuration |
| Burst limit | Determined by API Gateway configuration |

When rate limited, the API returns a `429 Too Many Requests` status code. Implement exponential backoff in your client applications.

## Templates

Templates are predefined categories with `orgId=0` that serve as starting points for organization-specific categories. Templates are read-only through the API.

## Pagination

For endpoints returning lists, the API may implement pagination. Check the detailed endpoint documentation for pagination parameters and response metadata.

## Support

For API issues or questions, consult the detailed documentation linked above or contact the platform support team.