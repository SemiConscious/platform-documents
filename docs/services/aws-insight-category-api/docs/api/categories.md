# Category Endpoints

This document provides detailed documentation for all category CRUD operations in the AWS Insight Category API.

## Overview

Categories allow organisations to classify and organize their insights. Each category belongs to a specific organisation and is identified by a unique category key. The API supports full CRUD operations with soft-delete functionality and version control.

## Base URL

```
https://api.aws-insight.example.com
```

---

## Endpoints

### List Categories

Retrieves all categories for a specific organisation.

```
GET /organisations/{organisationId}/categories
```

#### Description

Returns a list of all active categories belonging to the specified organisation. Deleted categories are excluded from the results.

#### Parameters

| Name | Located In | Type | Required | Description |
|------|------------|------|----------|-------------|
| `organisationId` | path | string | Yes | The unique identifier of the organisation |

#### Request Example

```bash
curl -X GET \
  'https://api.aws-insight.example.com/organisations/org-123456/categories' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json'
```

#### Response Example

**Status: 200 OK**

```json
{
  "success": true,
  "data": [
    {
      "categoryKey": "cat-001",
      "organisationId": "org-123456",
      "name": "Cost Optimization",
      "description": "Insights related to cost reduction opportunities",
      "color": "#4CAF50",
      "icon": "dollar-sign",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z",
      "version": 0
    },
    {
      "categoryKey": "cat-002",
      "organisationId": "org-123456",
      "name": "Security",
      "description": "Security-related insights and recommendations",
      "color": "#F44336",
      "icon": "shield",
      "createdAt": "2024-01-16T14:20:00Z",
      "updatedAt": "2024-01-16T14:20:00Z",
      "version": 0
    }
  ],
  "count": 2
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_ORGANISATION_ID` | The organisation ID format is invalid |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have access to this organisation |
| 404 | `ORGANISATION_NOT_FOUND` | The specified organisation does not exist |
| 500 | `INTERNAL_SERVER_ERROR` | An unexpected error occurred |

---

### Get Category

Retrieves a single category by its partition key and category key.

```
GET /organisations/{organisationId}/categories/{categoryKey}
```

#### Description

Returns the details of a specific category. Returns a 404 error if the category does not exist or has been deleted.

#### Parameters

| Name | Located In | Type | Required | Description |
|------|------------|------|----------|-------------|
| `organisationId` | path | string | Yes | The unique identifier of the organisation |
| `categoryKey` | path | string | Yes | The unique identifier of the category |

#### Request Example

```bash
curl -X GET \
  'https://api.aws-insight.example.com/organisations/org-123456/categories/cat-001' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json'
```

#### Response Example

**Status: 200 OK**

```json
{
  "success": true,
  "data": {
    "categoryKey": "cat-001",
    "organisationId": "org-123456",
    "name": "Cost Optimization",
    "description": "Insights related to cost reduction opportunities",
    "color": "#4CAF50",
    "icon": "dollar-sign",
    "metadata": {
      "priority": "high",
      "department": "finance"
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "version": 0
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_PARAMETERS` | Invalid organisation ID or category key format |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have access to this category |
| 404 | `CATEGORY_NOT_FOUND` | The specified category does not exist or has been deleted |
| 500 | `INTERNAL_SERVER_ERROR` | An unexpected error occurred |

---

### Create Category

Creates a new category for an organisation.

```
POST /organisations/{organisationId}/categories
```

#### Description

Creates a new category with the provided details. The category name must be unique within the organisation. A unique `categoryKey` is automatically generated.

#### Parameters

| Name | Located In | Type | Required | Description |
|------|------------|------|----------|-------------|
| `organisationId` | path | string | Yes | The unique identifier of the organisation |
| `name` | body | string | Yes | The display name of the category (1-100 characters) |
| `description` | body | string | No | A detailed description of the category (max 500 characters) |
| `color` | body | string | No | Hex color code for UI display (e.g., `#4CAF50`) |
| `icon` | body | string | No | Icon identifier for UI display |
| `metadata` | body | object | No | Additional custom metadata as key-value pairs |

#### Request Example

```bash
curl -X POST \
  'https://api.aws-insight.example.com/organisations/org-123456/categories' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Performance",
    "description": "Performance optimization insights and recommendations",
    "color": "#2196F3",
    "icon": "speedometer",
    "metadata": {
      "priority": "medium",
      "department": "engineering"
    }
  }'
```

#### Response Example

**Status: 201 Created**

```json
{
  "success": true,
  "data": {
    "categoryKey": "cat-003",
    "organisationId": "org-123456",
    "name": "Performance",
    "description": "Performance optimization insights and recommendations",
    "color": "#2196F3",
    "icon": "speedometer",
    "metadata": {
      "priority": "medium",
      "department": "engineering"
    },
    "createdAt": "2024-01-20T09:15:00Z",
    "updatedAt": "2024-01-20T09:15:00Z",
    "version": 0
  },
  "message": "Category created successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_PARAMETERS` | Request body validation failed |
| 400 | `INVALID_ORGANISATION_ID` | The organisation ID format is invalid |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have permission to create categories |
| 404 | `ORGANISATION_NOT_FOUND` | The specified organisation does not exist |
| 409 | `CATEGORY_NAME_EXISTS` | A category with this name already exists in the organisation |
| 500 | `INTERNAL_SERVER_ERROR` | An unexpected error occurred |

---

### Update Category

Updates an existing category.

```
PUT /organisations/{organisationId}/categories/{categoryKey}
```

#### Description

Updates the specified category with new data. This operation creates a new version of the category, deletes the old v0 entry, and stores the updated data. The category name must remain unique within the organisation if changed.

#### Parameters

| Name | Located In | Type | Required | Description |
|------|------------|------|----------|-------------|
| `organisationId` | path | string | Yes | The unique identifier of the organisation |
| `categoryKey` | path | string | Yes | The unique identifier of the category to update |
| `name` | body | string | No | The updated display name (1-100 characters) |
| `description` | body | string | No | The updated description (max 500 characters) |
| `color` | body | string | No | Updated hex color code |
| `icon` | body | string | No | Updated icon identifier |
| `metadata` | body | object | No | Updated custom metadata (replaces existing metadata) |

#### Request Example

```bash
curl -X PUT \
  'https://api.aws-insight.example.com/organisations/org-123456/categories/cat-001' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Cost Optimization & Savings",
    "description": "Updated insights for cost reduction and savings opportunities",
    "color": "#8BC34A",
    "metadata": {
      "priority": "critical",
      "department": "finance",
      "reviewRequired": true
    }
  }'
```

#### Response Example

**Status: 200 OK**

```json
{
  "success": true,
  "data": {
    "categoryKey": "cat-001",
    "organisationId": "org-123456",
    "name": "Cost Optimization & Savings",
    "description": "Updated insights for cost reduction and savings opportunities",
    "color": "#8BC34A",
    "icon": "dollar-sign",
    "metadata": {
      "priority": "critical",
      "department": "finance",
      "reviewRequired": true
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-20T11:45:00Z",
    "version": 1
  },
  "message": "Category updated successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_PARAMETERS` | Request body validation failed |
| 400 | `INVALID_ORGANISATION_ID` | The organisation ID format is invalid |
| 400 | `INVALID_CATEGORY_KEY` | The category key format is invalid |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have permission to update this category |
| 404 | `CATEGORY_NOT_FOUND` | The specified category does not exist or has been deleted |
| 409 | `CATEGORY_NAME_EXISTS` | Another category with this name already exists |
| 500 | `INTERNAL_SERVER_ERROR` | An unexpected error occurred |

---

### Delete Category

Soft deletes a category by marking it as deleted.

```
DELETE /organisations/{organisationId}/categories/{categoryKey}
```

#### Description

Performs a soft delete on the specified category. Rather than permanently removing the data, this operation creates a new version with the `isDeleted=true` flag. The category will no longer appear in list operations but can potentially be recovered if needed.

#### Parameters

| Name | Located In | Type | Required | Description |
|------|------------|------|----------|-------------|
| `organisationId` | path | string | Yes | The unique identifier of the organisation |
| `categoryKey` | path | string | Yes | The unique identifier of the category to delete |

#### Request Example

```bash
curl -X DELETE \
  'https://api.aws-insight.example.com/organisations/org-123456/categories/cat-002' \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json'
```

#### Response Example

**Status: 200 OK**

```json
{
  "success": true,
  "message": "Category deleted successfully",
  "data": {
    "categoryKey": "cat-002",
    "organisationId": "org-123456",
    "deletedAt": "2024-01-20T14:30:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_PARAMETERS` | Invalid organisation ID or category key format |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have permission to delete this category |
| 404 | `CATEGORY_NOT_FOUND` | The specified category does not exist or has already been deleted |
| 409 | `CATEGORY_IN_USE` | The category cannot be deleted because it is currently in use |
| 500 | `INTERNAL_SERVER_ERROR` | An unexpected error occurred |

---

## Related Documentation

- [API Overview](README.md) - General API information and authentication
- [Template Endpoints](templates.md) - Documentation for category templates