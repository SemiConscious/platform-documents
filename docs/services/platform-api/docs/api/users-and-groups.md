# Users and Groups API

The Users and Groups API provides endpoints for managing user identities, group memberships, permissions, and user-related operations within the platform. This includes user foreign ID management, permissions retrieval, and client directory operations for user lookups.

## Base URL

All endpoints are relative to: `https://api.platform.example.com`

## Authentication

All endpoints require authentication via bearer token or API key. See [Authentication](authentication.md) for details.

---

## Overview

The Users and Groups API supports:

- **User Foreign IDs**: Manage external system identifiers for users (CRM IDs, SSO identifiers, etc.)
- **Permissions**: Retrieve permission data for users and other entities
- **Client Directory**: Look up and manage user directory entries
- **Client Access**: Control user access permissions and settings

---

## User Foreign IDs

User Foreign IDs allow linking platform users to external system identifiers, enabling integration with CRM systems, SSO providers, and other third-party platforms.

### Get User Foreign IDs

Retrieve foreign ID mappings for a specific user.

```
GET /userforeignid/:orgId/:userId/:foreignIdTypeToken?
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | string | path | Yes | Organization ID |
| `userId` | string | path | Yes | User ID |
| `foreignIdTypeToken` | string | path | No | Optional filter by foreign ID type (e.g., `salesforce`, `crm`, `sso`) |

#### Request Example

```bash
# Get all foreign IDs for a user
curl -X GET "https://api.platform.example.com/userforeignid/org_12345/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"

# Get only Salesforce foreign IDs
curl -X GET "https://api.platform.example.com/userforeignid/org_12345/user_67890/salesforce" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "userId": "user_67890",
    "orgId": "org_12345",
    "foreignIds": [
      {
        "foreignIdType": "salesforce",
        "foreignId": "003xx000004TmiUAAS",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z"
      },
      {
        "foreignIdType": "crm",
        "foreignId": "CRM-USER-12345",
        "createdAt": "2024-01-10T08:15:00Z",
        "updatedAt": "2024-01-10T08:15:00Z"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request parameters |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | User or organization not found |
| `500` | Internal server error |

---

### Update User Foreign IDs

Create or update foreign ID mappings for a user.

```
PUT /userforeignid/:orgId/:userId
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | string | path | Yes | Organization ID |
| `userId` | string | path | Yes | User ID |
| `foreignIds` | array | body | Yes | Array of foreign ID objects to set |
| `foreignIds[].foreignIdType` | string | body | Yes | Type/category of the foreign ID |
| `foreignIds[].foreignId` | string | body | Yes | The external system identifier |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/userforeignid/org_12345/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "foreignIds": [
      {
        "foreignIdType": "salesforce",
        "foreignId": "003xx000004TmiUAAS"
      },
      {
        "foreignIdType": "azure_ad",
        "foreignId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
      }
    ]
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Foreign IDs updated successfully",
  "data": {
    "userId": "user_67890",
    "orgId": "org_12345",
    "foreignIds": [
      {
        "foreignIdType": "salesforce",
        "foreignId": "003xx000004TmiUAAS",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-20T14:22:00Z"
      },
      {
        "foreignIdType": "azure_ad",
        "foreignId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "createdAt": "2024-01-20T14:22:00Z",
        "updatedAt": "2024-01-20T14:22:00Z"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body or missing required fields |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | User or organization not found |
| `409` | Conflict - Foreign ID already assigned to another user |
| `500` | Internal server error |

---

### Find Users by Foreign IDs

Search for users within an organization using their foreign ID mappings.

```
POST /userforeignid/:orgId
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | string | path | Yes | Organization ID |
| `foreignIdType` | string | body | Yes | Type of foreign ID to search |
| `foreignIds` | array | body | Yes | Array of foreign ID values to search for |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/userforeignid/org_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "foreignIdType": "salesforce",
    "foreignIds": [
      "003xx000004TmiUAAS",
      "003xx000004XyzABC",
      "003xx000004QrsXYZ"
    ]
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "foreignId": "003xx000004TmiUAAS",
        "userId": "user_67890",
        "userName": "john.doe@example.com",
        "displayName": "John Doe"
      },
      {
        "foreignId": "003xx000004XyzABC",
        "userId": "user_11111",
        "userName": "jane.smith@example.com",
        "displayName": "Jane Smith"
      }
    ],
    "notFound": [
      "003xx000004QrsXYZ"
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body or empty foreignIds array |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | Organization not found |
| `500` | Internal server error |

---

## Permissions

### Get Permissions

Retrieve permissions data for a specific entity (user, group, role, etc.).

```
GET /permissions/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (user ID, group ID, or role name) |
| `type` | string | query | No | Entity type filter (`user`, `group`, `role`) |
| `scope` | string | query | No | Permission scope (`org`, `global`, `resource`) |

#### Request Example

```bash
# Get permissions for a specific user
curl -X GET "https://api.platform.example.com/permissions/user_67890?type=user" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"

# Get permissions for a group
curl -X GET "https://api.platform.example.com/permissions/group_admin?type=group&scope=org" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "entity": "user_67890",
    "entityType": "user",
    "permissions": [
      {
        "permission": "users.read",
        "scope": "org",
        "granted": true,
        "source": "role:admin"
      },
      {
        "permission": "users.write",
        "scope": "org",
        "granted": true,
        "source": "role:admin"
      },
      {
        "permission": "billing.read",
        "scope": "org",
        "granted": true,
        "source": "direct"
      },
      {
        "permission": "dialplan.write",
        "scope": "org",
        "granted": false,
        "source": null
      }
    ],
    "roles": [
      {
        "roleId": "role_admin",
        "roleName": "Organization Admin",
        "assignedAt": "2024-01-01T00:00:00Z"
      }
    ],
    "groups": [
      {
        "groupId": "group_12345",
        "groupName": "Support Team",
        "joinedAt": "2024-01-05T10:00:00Z"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid entity identifier |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot view permissions for this entity |
| `404` | Entity not found |
| `500` | Internal server error |

---

## Client Directory

The Client Directory provides a searchable directory of users within an organization with custom view rendering support.

### Get Client Directory Entry

Retrieve client directory data for a specific entity.

```
GET /clientdirectory/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (user ID, extension, or email) |
| `view` | string | query | No | Custom view format (`full`, `summary`, `contact`) |
| `orgId` | string | query | No | Filter by organization ID |

#### Request Example

```bash
# Get full directory entry
curl -X GET "https://api.platform.example.com/clientdirectory/user_67890?view=full" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"

# Lookup by extension
curl -X GET "https://api.platform.example.com/clientdirectory/1001?orgId=org_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "userId": "user_67890",
    "orgId": "org_12345",
    "displayName": "John Doe",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "extension": "1001",
    "directNumber": "+14155551234",
    "department": "Sales",
    "title": "Account Executive",
    "location": "San Francisco",
    "timezone": "America/Los_Angeles",
    "presence": {
      "status": "available",
      "message": "In the office",
      "lastUpdated": "2024-01-20T09:00:00Z"
    },
    "contactInfo": {
      "mobilePhone": "+14155559999",
      "workPhone": "+14155551234",
      "fax": null
    },
    "avatar": "https://cdn.example.com/avatars/user_67890.jpg"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid entity identifier |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Directory access not permitted |
| `404` | Directory entry not found |
| `500` | Internal server error |

---

### Update Client Directory Entry

Update a user's directory information.

```
PUT /clientdirectory/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (user ID) |
| `displayName` | string | body | No | Display name |
| `firstName` | string | body | No | First name |
| `lastName` | string | body | No | Last name |
| `department` | string | body | No | Department name |
| `title` | string | body | No | Job title |
| `location` | string | body | No | Office location |
| `contactInfo` | object | body | No | Contact information object |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/clientdirectory/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "John A. Doe",
    "department": "Enterprise Sales",
    "title": "Senior Account Executive",
    "contactInfo": {
      "mobilePhone": "+14155558888"
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Directory entry updated successfully",
  "data": {
    "userId": "user_67890",
    "displayName": "John A. Doe",
    "department": "Enterprise Sales",
    "title": "Senior Account Executive",
    "updatedAt": "2024-01-20T15:30:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot modify this directory entry |
| `404` | Directory entry not found |
| `409` | Conflict - Duplicate value for unique field |
| `500` | Internal server error |

---

### Create/Update Client Directory Entry

Create a new directory entry or update an existing one.

```
POST /clientdirectory/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (user ID) |
| `displayName` | string | body | Yes | Display name |
| `email` | string | body | Yes | Email address |
| `firstName` | string | body | No | First name |
| `lastName` | string | body | No | Last name |
| `extension` | string | body | No | Phone extension |
| `department` | string | body | No | Department name |
| `title` | string | body | No | Job title |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/clientdirectory/user_99999" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "New User",
    "email": "new.user@example.com",
    "firstName": "New",
    "lastName": "User",
    "extension": "1050",
    "department": "Marketing"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Directory entry created successfully",
  "data": {
    "userId": "user_99999",
    "displayName": "New User",
    "email": "new.user@example.com",
    "extension": "1050",
    "createdAt": "2024-01-20T16:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body or missing required fields |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot create directory entries |
| `409` | Conflict - Entry already exists or duplicate email/extension |
| `500` | Internal server error |

---

### Delete Client Directory Entry

Remove a directory entry.

```
DELETE /clientdirectory/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity identifier (user ID) |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/clientdirectory/user_99999" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "status": "success",
  "message": "Directory entry deleted successfully",
  "data": {
    "userId": "user_99999",
    "deletedAt": "2024-01-20T17:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid entity identifier |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot delete this directory entry |
| `404` | Directory entry not found |
| `500` | Internal server error |

---

## Client Access

Manage user access permissions and authentication settings.

### Get All Client Access Data

Retrieve all client access configurations.

```
GET /clientaccess
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | string | query | No | Filter by organization ID |
| `status` | string | query | No | Filter by status (`active`, `disabled`, `pending`) |
| `limit` | integer | query | No | Maximum results to return (default: 100) |
| `offset` | integer | query | No | Results offset for pagination |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/clientaccess?orgId=org_12345&status=active&limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "clientAccess": [
      {
        "userId": "user_67890",
        "orgId": "org_12345",
        "status": "active",
        "accessLevel": "standard",
        "lastLogin": "2024-01-20T08:30:00Z",
        "twoFactorEnabled": true,
        "ipRestrictions": [],
        "createdAt": "2024-01-01T00:00:00Z"
      },
      {
        "userId": "user_11111",
        "orgId": "org_12345",
        "status": "active",
        "accessLevel": "admin",
        "lastLogin": "2024-01-19T14:22:00Z",
        "twoFactorEnabled": true,
        "ipRestrictions": ["192.168.1.0/24"],
        "createdAt": "2023-12-01T00:00:00Z"
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 50,
      "offset": 0,
      "hasMore": true
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Insufficient permissions to list client access |
| `500` | Internal server error |

---

### Get Client Access for Entity

Retrieve access configuration for a specific user.

```
GET /clientaccess/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | User ID or email |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/clientaccess/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "userId": "user_67890",
    "orgId": "org_12345",
    "userName": "john.doe@example.com",
    "status": "active",
    "accessLevel": "standard",
    "permissions": {
      "webPortal": true,
      "mobileApp": true,
      "apiAccess": false,
      "softphone": true
    },
    "security": {
      "twoFactorEnabled": true,
      "twoFactorMethod": "totp",
      "passwordLastChanged": "2024-01-10T00:00:00Z",
      "passwordExpiresAt": "2024-04-10T00:00:00Z"
    },
    "restrictions": {
      "ipWhitelist": [],
      "timeRestrictions": null,
      "deviceLimit": 5
    },
    "sessions": {
      "activeSessions": 2,
      "maxSessions": 5
    },
    "audit": {
      "lastLogin": "2024-01-20T08:30:00Z",
      "lastLoginIp": "192.168.1.100",
      "failedLoginAttempts": 0,
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid entity identifier |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot view access data for this user |
| `404` | User not found |
| `500` | Internal server error |

---

### Update Client Access

Update access configuration using PUT method.

```
PUT /clientaccess/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | User ID |
| `status` | string | body | No | Access status (`active`, `disabled`, `pending`) |
| `accessLevel` | string | body | No | Access level (`standard`, `admin`, `restricted`) |
| `permissions` | object | body | No | Permission flags |
| `restrictions` | object | body | No | Access restrictions |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/clientaccess/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "accessLevel": "admin",
    "permissions": {
      "webPortal": true,
      "mobileApp": true,
      "apiAccess": true,
      "softphone": true
    },
    "restrictions": {
      "ipWhitelist": ["192.168.1.0/24", "10.0.0.0/8"],
      "deviceLimit": 10
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Client access updated successfully",
  "data": {
    "userId": "user_67890",
    "accessLevel": "admin",
    "permissions": {
      "webPortal": true,
      "mobileApp": true,
      "apiAccess": true,
      "softphone": true
    },
    "updatedAt": "2024-01-20T18:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot modify access for this user |
| `404` | User not found |
| `500` | Internal server error |

---

### Update Client Access (POST)

Update access configuration using POST method.

```
POST /clientaccess/:entity
```

#### Parameters

Same as PUT method above.

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/clientaccess/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "permissions": {
      "apiAccess": true
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Client access updated successfully",
  "data": {
    "userId": "user_67890",
    "status": "active",
    "updatedAt": "2024-01-20T18:15:00Z"
  }
}
```

---

### Delete Client Access

Remove client access configuration (typically disables access).

```
DELETE /clientaccess/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | User ID |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/clientaccess/user_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "status": "success",
  "message": "Client access revoked successfully",
  "data": {
    "userId": "user_67890",
    "status": "disabled",
    "revokedAt": "2024-01-20T19:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid entity identifier |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Cannot revoke access for this user |
| `404` | User not found |
| `500` | Internal server error |

---

## Related Documentation

- [Authentication](authentication.md) - Token generation and SSO
- [Organizations](organizations.md) - Organization management
- [Billing](billing.md) - Billing profiles and subscription management
- [System](system.md) - System-level operations and logging