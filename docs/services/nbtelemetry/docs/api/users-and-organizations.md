# Users and Organizations API

This document covers endpoints for managing users, user groups, and organization resources within the nbtelemetry service.

## Overview

The Users and Organizations API provides functionality to:
- Retrieve current user information
- Manage users within an organisation
- Manage user groups
- Update user availability states and profiles

All endpoints (except `/v1/user/me`) are scoped to a specific organisation using the `{orgid}` path parameter.

---

## Endpoints

### Get Current User

Retrieve information about the currently authenticated user.

```
GET /v1/user/me
```

#### Description

Returns the profile and details of the user associated with the current access token. This is useful for applications to identify the logged-in user and their permissions.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/user/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "id": "usr_12345",
  "email": "john.doe@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "organisationId": "org_67890",
  "role": "admin",
  "status": "active",
  "createdAt": "2023-01-15T10:30:00Z",
  "lastLogin": "2024-01-20T14:22:00Z",
  "permissions": [
    "calls.read",
    "users.read",
    "analytics.read"
  ]
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - Insufficient permissions |
| 500 | Internal Server Error |

---

### Get All Users for Organisation

Retrieve all users belonging to a specific organisation.

```
GET /v1/organisation/{orgid}/user
```

#### Description

Returns a list of all users within the specified organisation. This endpoint supports pagination and filtering capabilities.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |
| limit | Query | integer | No | Maximum number of users to return (default: 50) |
| offset | Query | integer | No | Number of records to skip for pagination |
| status | Query | string | No | Filter by user status (active, inactive, suspended) |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org_67890/user?limit=20&status=active" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "data": [
    {
      "id": "usr_12345",
      "email": "john.doe@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "role": "admin",
      "status": "active",
      "extension": "1001",
      "department": "Sales",
      "createdAt": "2023-01-15T10:30:00Z"
    },
    {
      "id": "usr_12346",
      "email": "jane.smith@example.com",
      "firstName": "Jane",
      "lastName": "Smith",
      "role": "user",
      "status": "active",
      "extension": "1002",
      "department": "Support",
      "createdAt": "2023-02-20T09:15:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  }
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No access to this organisation |
| 404 | Not Found - Organisation does not exist |
| 500 | Internal Server Error |

---

### Get Specific User

Retrieve details of a specific user within an organisation.

```
GET /v1/organisation/{orgid}/user/{userid}
```

#### Description

Returns detailed information about a specific user, including their profile, permissions, and current availability state.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |
| userid | Path | string | Yes | User identifier |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org_67890/user/usr_12345" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "id": "usr_12345",
  "email": "john.doe@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "organisationId": "org_67890",
  "role": "admin",
  "status": "active",
  "extension": "1001",
  "department": "Sales",
  "phoneNumbers": [
    {
      "type": "direct",
      "number": "+1-555-123-4567"
    },
    {
      "type": "mobile",
      "number": "+1-555-987-6543"
    }
  ],
  "availability": {
    "profileId": "avail_001",
    "currentState": "available",
    "updatedAt": "2024-01-20T14:00:00Z"
  },
  "groups": [
    {
      "id": "grp_001",
      "name": "Sales Team"
    }
  ],
  "permissions": [
    "calls.read",
    "calls.write",
    "analytics.read"
  ],
  "createdAt": "2023-01-15T10:30:00Z",
  "updatedAt": "2024-01-18T11:45:00Z"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No access to this user |
| 404 | Not Found - User or organisation does not exist |
| 500 | Internal Server Error |

---

### Update User Profile State

Update a user's availability state or profile information.

```
PATCH /v1/organisation/{orgid}/user/{userid}
```

#### Description

Updates the specified user's availability state, profile settings, or other mutable properties. This is commonly used to change a user's availability status (e.g., available, busy, away).

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |
| userid | Path | string | Yes | User identifier |
| Content-Type | Header | string | Yes | Must be `application/json` |
| availabilityState | Body | string | No | New availability state |
| availabilityProfileId | Body | string | No | ID of availability profile to apply |
| firstName | Body | string | No | User's first name |
| lastName | Body | string | No | User's last name |
| department | Body | string | No | User's department |

#### Request Example

```bash
curl -X PATCH "https://api.natterbox.com/v1/organisation/org_67890/user/usr_12345" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "availabilityState": "busy",
    "availabilityProfileId": "avail_001"
  }'
```

#### Response Example

```json
{
  "id": "usr_12345",
  "email": "john.doe@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "availability": {
    "profileId": "avail_001",
    "currentState": "busy",
    "updatedAt": "2024-01-20T15:30:00Z"
  },
  "updatedAt": "2024-01-20T15:30:00Z",
  "message": "User profile updated successfully"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid request body or parameters |
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No permission to update this user |
| 404 | Not Found - User or organisation does not exist |
| 422 | Unprocessable Entity - Invalid availability state |
| 500 | Internal Server Error |

---

### Get All User Groups

Retrieve all user groups for an organisation.

```
GET /v1/organisation/{orgid}/user-group
```

#### Description

Returns a list of all user groups defined within the organisation. User groups are used to organize users for routing, permissions, and reporting purposes.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org_67890/user-group" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "data": [
    {
      "id": "grp_001",
      "name": "Sales Team",
      "description": "Outbound sales representatives",
      "memberCount": 12,
      "createdAt": "2023-01-10T08:00:00Z"
    },
    {
      "id": "grp_002",
      "name": "Support Team",
      "description": "Customer support agents",
      "memberCount": 8,
      "createdAt": "2023-01-10T08:15:00Z"
    },
    {
      "id": "grp_003",
      "name": "Management",
      "description": "Team leads and managers",
      "memberCount": 4,
      "createdAt": "2023-01-10T08:30:00Z"
    }
  ],
  "total": 3
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No access to this organisation |
| 404 | Not Found - Organisation does not exist |
| 500 | Internal Server Error |

---

### Get Specific User Group

Retrieve details of a specific user group.

```
GET /v1/organisation/{orgid}/user-group/{groupid}
```

#### Description

Returns detailed information about a specific user group, including its members and configuration.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |
| groupid | Path | string | Yes | User group identifier |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org_67890/user-group/grp_001" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "id": "grp_001",
  "name": "Sales Team",
  "description": "Outbound sales representatives",
  "organisationId": "org_67890",
  "settings": {
    "callDistribution": "round-robin",
    "maxWaitTime": 120,
    "overflowGroup": "grp_002"
  },
  "members": [
    {
      "id": "usr_12345",
      "email": "john.doe@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "role": "member",
      "joinedAt": "2023-01-15T10:30:00Z"
    },
    {
      "id": "usr_12346",
      "email": "jane.smith@example.com",
      "firstName": "Jane",
      "lastName": "Smith",
      "role": "lead",
      "joinedAt": "2023-01-12T09:00:00Z"
    }
  ],
  "memberCount": 12,
  "createdAt": "2023-01-10T08:00:00Z",
  "updatedAt": "2024-01-15T16:20:00Z"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No access to this user group |
| 404 | Not Found - User group or organisation does not exist |
| 500 | Internal Server Error |

---

### Get Availability Profiles

Retrieve all availability profiles for an organisation.

```
GET /v1/organisation/{orgid}/availability/profile
```

#### Description

Returns all availability profiles configured for the organisation. Availability profiles define the possible states a user can be in (e.g., available, busy, away, DND).

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org_67890/availability/profile" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "data": [
    {
      "id": "avail_001",
      "name": "Standard Profile",
      "description": "Default availability profile for all users",
      "isDefault": true,
      "states": [
        "available",
        "busy",
        "away",
        "dnd",
        "offline"
      ],
      "createdAt": "2023-01-05T12:00:00Z"
    },
    {
      "id": "avail_002",
      "name": "Support Profile",
      "description": "Availability profile for support team",
      "isDefault": false,
      "states": [
        "available",
        "on-call",
        "wrap-up",
        "break",
        "offline"
      ],
      "createdAt": "2023-02-10T14:30:00Z"
    }
  ],
  "total": 2
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No access to this organisation |
| 404 | Not Found - Organisation does not exist |
| 500 | Internal Server Error |

---

### Get Availability Profile States

Retrieve the states for a specific availability profile.

```
GET /v1/organisation/{orgid}/availability/profile/{profileId}/state
```

#### Description

Returns detailed information about all states defined in a specific availability profile, including their configuration and routing behavior.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| Authorization | Header | string | Yes | Bearer token from authentication |
| orgid | Path | string | Yes | Organisation identifier |
| profileId | Path | string | Yes | Availability profile identifier |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org_67890/availability/profile/avail_001/state" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

```json
{
  "profileId": "avail_001",
  "profileName": "Standard Profile",
  "states": [
    {
      "id": "state_001",
      "name": "available",
      "displayName": "Available",
      "color": "#28a745",
      "acceptsCalls": true,
      "routing": {
        "enabled": true,
        "priority": 1
      }
    },
    {
      "id": "state_002",
      "name": "busy",
      "displayName": "Busy",
      "color": "#dc3545",
      "acceptsCalls": false,
      "routing": {
        "enabled": false,
        "forwardTo": "voicemail"
      }
    },
    {
      "id": "state_003",
      "name": "away",
      "displayName": "Away",
      "color": "#ffc107",
      "acceptsCalls": false,
      "routing": {
        "enabled": false,
        "forwardTo": "group"
      }
    },
    {
      "id": "state_004",
      "name": "dnd",
      "displayName": "Do Not Disturb",
      "color": "#6c757d",
      "acceptsCalls": false,
      "routing": {
        "enabled": false,
        "forwardTo": "voicemail"
      }
    },
    {
      "id": "state_005",
      "name": "offline",
      "displayName": "Offline",
      "color": "#343a40",
      "acceptsCalls": false,
      "routing": {
        "enabled": false,
        "forwardTo": null
      }
    }
  ]
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - No access to this organisation |
| 404 | Not Found - Profile or organisation does not exist |
| 500 | Internal Server Error |

---

## Related Documentation

- [Authentication](authentication.md) - Token management and authentication flows
- [Call Analytics](call-analytics.md) - Recording and transcription analytics
- [Configuration](configuration.md) - Dial plans, SIP devices, and system configuration