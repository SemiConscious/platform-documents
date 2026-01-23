# Prompt Management API

This document covers the API endpoints for managing AI prompt configurations in the Insight Category UI system. Prompts define how the AI analyzes and categorizes voice call content.

## Overview

Prompt management operations are executed through Salesforce Remote Actions, providing secure server-side processing for creating, updating, and deleting prompt configurations. These prompts are used to configure AI-driven analysis of call transcripts.

---

## Endpoints

### Create Prompt

Creates a new AI prompt configuration for call analysis.

```
POST /prompt
```

#### Description

Creates a new prompt configuration that defines how the AI should analyze and categorize voice call content. Prompts can be associated with specific categories or used for general analysis purposes.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `name` | string | body | Yes | Display name for the prompt |
| `description` | string | body | No | Description of the prompt's purpose |
| `promptText` | string | body | Yes | The actual prompt text sent to the AI |
| `categoryId` | string | body | No | Associated category ID (if applicable) |
| `isActive` | boolean | body | No | Whether the prompt is active (default: `true`) |
| `priority` | number | body | No | Execution priority order |

#### Request Example

```bash
curl -X POST \
  'https://your-instance.salesforce.com/apex/InsightCategoryUI/prompt' \
  -H 'Authorization: Bearer <JWT_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Customer Sentiment Analysis",
    "description": "Analyzes customer sentiment during support calls",
    "promptText": "Analyze the following call transcript and identify the overall customer sentiment. Classify as positive, negative, or neutral and provide key indicators.",
    "categoryId": "cat_abc123",
    "isActive": true,
    "priority": 1
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "promptIdFromAPI": "prompt_xyz789",
    "name": "Customer Sentiment Analysis",
    "description": "Analyzes customer sentiment during support calls",
    "promptText": "Analyze the following call transcript and identify the overall customer sentiment. Classify as positive, negative, or neutral and provide key indicators.",
    "categoryId": "cat_abc123",
    "isActive": true,
    "priority": 1,
    "createdAt": "2024-01-15T10:30:00.000Z",
    "createdBy": "user_001",
    "modifiedAt": "2024-01-15T10:30:00.000Z",
    "modifiedBy": "user_001"
  },
  "message": "Prompt created successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | `INVALID_REQUEST` | Missing required fields or invalid data format |
| `401` | `UNAUTHORIZED` | Invalid or expired JWT token |
| `403` | `FORBIDDEN` | User lacks permission to create prompts |
| `409` | `DUPLICATE_NAME` | A prompt with this name already exists |
| `422` | `INVALID_PROMPT_TEXT` | Prompt text exceeds maximum length or contains invalid characters |
| `500` | `INTERNAL_ERROR` | Salesforce Remote Action failed |

---

### Update Prompt

Updates an existing AI prompt configuration.

```
PUT /prompt
```

#### Description

Updates the properties of an existing prompt configuration. All fields provided in the request body will be updated; omitted fields remain unchanged.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `promptIdFromAPI` | string | body | Yes | The unique API identifier of the prompt to update |
| `name` | string | body | No | Updated display name |
| `description` | string | body | No | Updated description |
| `promptText` | string | body | No | Updated prompt text |
| `categoryId` | string | body | No | Updated category association |
| `isActive` | boolean | body | No | Updated active status |
| `priority` | number | body | No | Updated priority order |

#### Request Example

```bash
curl -X PUT \
  'https://your-instance.salesforce.com/apex/InsightCategoryUI/prompt' \
  -H 'Authorization: Bearer <JWT_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "promptIdFromAPI": "prompt_xyz789",
    "name": "Enhanced Customer Sentiment Analysis",
    "promptText": "Analyze the following call transcript for customer sentiment. Classify as positive, negative, or neutral. Additionally, identify specific pain points and satisfaction drivers mentioned by the customer.",
    "isActive": true,
    "priority": 2
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "promptIdFromAPI": "prompt_xyz789",
    "name": "Enhanced Customer Sentiment Analysis",
    "description": "Analyzes customer sentiment during support calls",
    "promptText": "Analyze the following call transcript for customer sentiment. Classify as positive, negative, or neutral. Additionally, identify specific pain points and satisfaction drivers mentioned by the customer.",
    "categoryId": "cat_abc123",
    "isActive": true,
    "priority": 2,
    "createdAt": "2024-01-15T10:30:00.000Z",
    "createdBy": "user_001",
    "modifiedAt": "2024-01-15T14:45:00.000Z",
    "modifiedBy": "user_001"
  },
  "message": "Prompt updated successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | `INVALID_REQUEST` | Missing prompt ID or invalid data format |
| `401` | `UNAUTHORIZED` | Invalid or expired JWT token |
| `403` | `FORBIDDEN` | User lacks permission to update this prompt |
| `404` | `NOT_FOUND` | Prompt with specified ID does not exist |
| `409` | `DUPLICATE_NAME` | Another prompt with this name already exists |
| `422` | `INVALID_PROMPT_TEXT` | Prompt text exceeds maximum length or contains invalid characters |
| `500` | `INTERNAL_ERROR` | Salesforce Remote Action failed |

---

### Delete Prompt

Deletes a prompt by its API identifier.

```
DELETE /prompt/:promptIdFromAPI
```

#### Description

Permanently removes a prompt configuration from the system. This action cannot be undone. If the prompt is currently in use by active analysis jobs, those jobs will need to be reassigned to a different prompt.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `promptIdFromAPI` | string | path | Yes | The unique API identifier of the prompt to delete |

#### Request Example

```bash
curl -X DELETE \
  'https://your-instance.salesforce.com/apex/InsightCategoryUI/prompt/prompt_xyz789' \
  -H 'Authorization: Bearer <JWT_TOKEN>' \
  -H 'Content-Type: application/json'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "promptIdFromAPI": "prompt_xyz789",
    "deleted": true
  },
  "message": "Prompt deleted successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `400` | `INVALID_REQUEST` | Invalid prompt ID format |
| `401` | `UNAUTHORIZED` | Invalid or expired JWT token |
| `403` | `FORBIDDEN` | User lacks permission to delete this prompt |
| `404` | `NOT_FOUND` | Prompt with specified ID does not exist |
| `409` | `PROMPT_IN_USE` | Prompt is currently assigned to active analysis jobs |
| `500` | `INTERNAL_ERROR` | Salesforce Remote Action failed |

---

## Related Documentation

- [Categories API](categories.md) - Manage categories that prompts can be associated with
- [Authentication API](authentication.md) - JWT token management for API authorization
- [Users API](users.md) - User management for prompt assignment