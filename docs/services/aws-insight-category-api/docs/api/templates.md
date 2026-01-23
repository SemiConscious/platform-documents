# Template Endpoints

This document covers the category template retrieval endpoints for the AWS Insight Category API.

## Overview

Templates are pre-defined category configurations that can be used as starting points for creating organisation-specific categories. Templates are stored as categories with `organisationId=0`, distinguishing them from organisation-specific categories.

---

## Endpoints

### Get All Templates

Retrieves all category templates available in the system.

```
GET /templates
```

#### Description

Returns a list of all category templates (categories with `orgId=0`). These templates serve as predefined category configurations that organisations can use as a basis for creating their own categories.

#### Request Parameters

This endpoint does not require any parameters.

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| — | — | — | — | No parameters required |

#### Request Example

```bash
curl -X GET \
  'https://api.example.com/templates' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json'
```

#### Response Example

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": [
    {
      "categoryKey": "TEMPLATE#cost-center",
      "organisationId": "0",
      "name": "Cost Center",
      "description": "Template for tracking cost centers across the organisation",
      "color": "#3498db",
      "icon": "dollar-sign",
      "sortOrder": 1,
      "isSystem": true,
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T10:30:00.000Z",
      "version": 0
    },
    {
      "categoryKey": "TEMPLATE#environment",
      "organisationId": "0",
      "name": "Environment",
      "description": "Template for categorizing resources by environment (dev, staging, prod)",
      "color": "#27ae60",
      "icon": "server",
      "sortOrder": 2,
      "isSystem": true,
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T10:30:00.000Z",
      "version": 0
    },
    {
      "categoryKey": "TEMPLATE#project",
      "organisationId": "0",
      "name": "Project",
      "description": "Template for organizing resources by project",
      "color": "#9b59b6",
      "icon": "folder",
      "sortOrder": 3,
      "isSystem": true,
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T10:30:00.000Z",
      "version": 0
    }
  ],
  "count": 3
}
```

**Empty Response (200 OK)**

```json
{
  "success": true,
  "data": [],
  "count": 0
}
```

#### Error Responses

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have permission to access templates |
| 500 | `INTERNAL_SERVER_ERROR` | An unexpected error occurred while retrieving templates |

**Error Response Example (500)**

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred while retrieving templates"
  }
}
```

---

## Related Documentation

- [Categories Endpoints](./categories.md) - Managing organisation-specific categories
- [API Overview](./README.md) - General API information and authentication