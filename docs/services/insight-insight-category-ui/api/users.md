# Users API

This document covers the user retrieval and management endpoints for the Insight Category UI system.

## Overview

The Users API provides access to user data from Salesforce, enabling the application to retrieve user information for category and prompt assignment workflows. Users can be associated with categories and prompts to control which call analysis configurations apply to specific individuals or groups.

---

## Endpoints

### Get All Users

Retrieves all users from the connected Salesforce organization.

```
GET /users
```

#### Description

Fetches the complete list of users from Salesforce via Remote Action. This endpoint is typically used to populate user selection interfaces when assigning categories or prompts to specific users or groups.

#### Request Parameters

This endpoint does not require any parameters.

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| — | — | — | — | No parameters required |

#### Request Example

```bash
curl -X GET \
  'https://your-instance.salesforce.com/apex/InsightCategoryUI/users' \
  -H 'Authorization: Bearer <jwt_token>' \
  -H 'Content-Type: application/json'
```

#### Response Example

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "005xx000001SvogAAC",
        "name": "John Smith",
        "email": "john.smith@company.com",
        "username": "john.smith@company.com.sandbox",
        "profileId": "00exx000001HKmYAAW",
        "profileName": "Standard User",
        "isActive": true,
        "userRole": {
          "id": "00Exx000001HKmZAAW",
          "name": "Sales Representative"
        },
        "department": "Sales",
        "title": "Account Executive",
        "createdDate": "2023-01-15T10:30:00.000Z",
        "lastModifiedDate": "2024-01-20T14:45:00.000Z"
      },
      {
        "id": "005xx000001SvohAAC",
        "name": "Jane Doe",
        "email": "jane.doe@company.com",
        "username": "jane.doe@company.com.sandbox",
        "profileId": "00exx000001HKmYAAW",
        "profileName": "Standard User",
        "isActive": true,
        "userRole": {
          "id": "00Exx000001HKmaAAG",
          "name": "Sales Manager"
        },
        "department": "Sales",
        "title": "Regional Sales Manager",
        "createdDate": "2022-06-10T08:15:00.000Z",
        "lastModifiedDate": "2024-01-18T09:30:00.000Z"
      },
      {
        "id": "005xx000001SvoiAAC",
        "name": "Bob Johnson",
        "email": "bob.johnson@company.com",
        "username": "bob.johnson@company.com.sandbox",
        "profileId": "00exx000001HKmZAAW",
        "profileName": "System Administrator",
        "isActive": true,
        "userRole": {
          "id": "00Exx000001HKmbAAG",
          "name": "IT Administrator"
        },
        "department": "IT",
        "title": "System Administrator",
        "createdDate": "2021-03-22T11:00:00.000Z",
        "lastModifiedDate": "2024-01-22T16:20:00.000Z"
      }
    ],
    "totalCount": 3
  },
  "timestamp": "2024-01-22T18:30:00.000Z"
}
```

#### Error Responses

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| `401` | `UNAUTHORIZED` | Invalid or expired JWT token |
| `403` | `FORBIDDEN` | User lacks permission to view user list |
| `500` | `INTERNAL_SERVER_ERROR` | Salesforce Remote Action failed |
| `503` | `SERVICE_UNAVAILABLE` | Salesforce connection unavailable |

**Error Response Example (401 Unauthorized)**

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired authentication token",
    "details": "Please obtain a new JWT token via the /jwt endpoint"
  },
  "timestamp": "2024-01-22T18:30:00.000Z"
}
```

**Error Response Example (500 Internal Server Error)**

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "Failed to retrieve users from Salesforce",
    "details": "Remote Action 'getAllUsers' encountered an unexpected error"
  },
  "timestamp": "2024-01-22T18:30:00.000Z"
}
```

---

## Usage Examples

### Fetching Users for Category Assignment

When creating or editing a category, you'll typically need to fetch users to display in a selection interface:

```javascript
// Redux action example
import { createAsyncThunk } from '@reduxjs/toolkit';
import { salesforceRemoteActions } from '@/shared/api';

export const fetchAllUsers = createAsyncThunk(
  'users/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await salesforceRemoteActions.getAllUsers();
      return response.data.users;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);
```

### Filtering Active Users

The response includes user status, allowing you to filter for active users only:

```javascript
const activeUsers = users.filter(user => user.isActive);
```

---

## Related Documentation

- [Authentication API](./authentication.md) - JWT token retrieval for API authorization
- [Categories API](./categories.md) - Managing categories that can be assigned to users
- [Prompts API](./prompts.md) - Managing AI prompts that can be assigned to users
- [API Overview](./README.md) - General API information and conventions