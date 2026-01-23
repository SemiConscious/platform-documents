# Category Management API

This document covers the endpoints for creating, updating, and deleting categories in the Insight voice analytics categorization system. Categories are used to organize and classify call data for analysis.

## Overview

Category management is handled through Salesforce Remote Actions, providing secure CRUD operations for categories that can be applied to users and groups for call analysis purposes.

## Endpoints

### Create Category

Creates a new category for call classification.

```
POST /category
```

#### Description

Creates a new category via Salesforce Remote Action. Categories are used to classify and organize call recordings for analysis within the Insight system.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `name` | string | body | Yes | The display name for the category |
| `description` | string | body | No | A detailed description of the category's purpose |
| `keywords` | string[] | body | No | List of keywords associated with this category |
| `isActive` | boolean | body | No | Whether the category is active (default: `true`) |
| `parentCategoryId` | string | body | No | ID of parent category for hierarchical organization |

#### Request Example

```bash
curl -X POST "https://your-instance.salesforce.com/api/category" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Complaints",
    "description": "Category for tracking customer complaint calls",
    "keywords": ["complaint", "issue", "problem", "dissatisfied"],
    "isActive": true,
    "parentCategoryId": null
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "cat_abc123def456",
    "name": "Customer Complaints",
    "description": "Category for tracking customer complaint calls",
    "keywords": ["complaint", "issue", "problem", "dissatisfied"],
    "isActive": true,
    "parentCategoryId": null,
    "createdAt": "2024-01-15T10:30:00.000Z",
    "createdBy": "user_789xyz",
    "updatedAt": "2024-01-15T10:30:00.000Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_REQUEST` | Missing required fields or invalid data format |
| 401 | `UNAUTHORIZED` | Invalid or expired JWT token |
| 403 | `FORBIDDEN` | User lacks permission to create categories |
| 409 | `DUPLICATE_NAME` | A category with this name already exists |
| 500 | `INTERNAL_ERROR` | Salesforce Remote Action failed |

---

### Update Category

Updates an existing category's properties.

```
PUT /category
```

#### Description

Updates an existing category via Salesforce Remote Action. Allows modification of category properties including name, description, keywords, and active status.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | body | Yes | The unique identifier of the category to update |
| `name` | string | body | No | Updated display name for the category |
| `description` | string | body | No | Updated description of the category's purpose |
| `keywords` | string[] | body | No | Updated list of keywords |
| `isActive` | boolean | body | No | Updated active status |
| `parentCategoryId` | string | body | No | Updated parent category ID |

#### Request Example

```bash
curl -X PUT "https://your-instance.salesforce.com/api/category" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cat_abc123def456",
    "name": "Customer Complaints - Priority",
    "description": "High-priority category for tracking escalated customer complaint calls",
    "keywords": ["complaint", "issue", "problem", "dissatisfied", "escalate", "urgent"],
    "isActive": true
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "cat_abc123def456",
    "name": "Customer Complaints - Priority",
    "description": "High-priority category for tracking escalated customer complaint calls",
    "keywords": ["complaint", "issue", "problem", "dissatisfied", "escalate", "urgent"],
    "isActive": true,
    "parentCategoryId": null,
    "createdAt": "2024-01-15T10:30:00.000Z",
    "createdBy": "user_789xyz",
    "updatedAt": "2024-01-15T14:45:00.000Z",
    "updatedBy": "user_789xyz"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_REQUEST` | Missing category ID or invalid data format |
| 401 | `UNAUTHORIZED` | Invalid or expired JWT token |
| 403 | `FORBIDDEN` | User lacks permission to update categories |
| 404 | `NOT_FOUND` | Category with specified ID does not exist |
| 409 | `DUPLICATE_NAME` | Another category with this name already exists |
| 500 | `INTERNAL_ERROR` | Salesforce Remote Action failed |

---

### Delete Category

Deletes a category by its API ID.

```
DELETE /category/:categoryIdFromAPI
```

#### Description

Permanently deletes a category via Salesforce Remote Action. This action cannot be undone. Categories that are currently assigned to users or groups may require reassignment before deletion.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `categoryIdFromAPI` | string | path | Yes | The unique API identifier of the category to delete |
| `force` | boolean | query | No | Force deletion even if category is assigned (default: `false`) |

#### Request Example

```bash
curl -X DELETE "https://your-instance.salesforce.com/api/category/cat_abc123def456?force=false" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "cat_abc123def456",
    "deleted": true,
    "deletedAt": "2024-01-15T16:00:00.000Z"
  },
  "message": "Category successfully deleted"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_REQUEST` | Invalid category ID format |
| 401 | `UNAUTHORIZED` | Invalid or expired JWT token |
| 403 | `FORBIDDEN` | User lacks permission to delete categories |
| 404 | `NOT_FOUND` | Category with specified ID does not exist |
| 409 | `CATEGORY_IN_USE` | Category is assigned to users/groups; use `force=true` to override |
| 500 | `INTERNAL_ERROR` | Salesforce Remote Action failed |

---

## Related Documentation

- [API Overview](README.md) - General API information and conventions
- [Authentication](authentication.md) - JWT token retrieval and authentication details
- [Prompts API](prompts.md) - AI prompt configuration endpoints
- [Users API](users.md) - User management and retrieval endpoints