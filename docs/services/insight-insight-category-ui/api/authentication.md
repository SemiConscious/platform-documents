# Authentication API

This document covers the authentication and configuration endpoints for the Insight Category UI application. These endpoints handle JWT token retrieval and namespace configuration from Salesforce.

## Overview

The authentication endpoints provide essential functionality for establishing secure communication between the frontend application and backend services. All authentication operations are performed through Salesforce Remote Actions.

## Endpoints

### Get JWT Token

Retrieves a JSON Web Token (JWT) from Salesforce for authenticating subsequent API requests.

```
GET /jwt
```

#### Description

This endpoint fetches a JWT token from Salesforce that is used to authenticate and authorize requests to the Insight analytics backend services. The token should be included in the `Authorization` header of subsequent API calls.

#### Request Parameters

This endpoint does not require any parameters.

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| — | — | — | — | No parameters required |

#### Request Example

```bash
curl -X GET \
  'https://your-instance.salesforce.com/apex/InsightCategoryUI/jwt' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<salesforce_session_id>'
```

#### Response Example

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDVYWDAwMDAwMWFiY2RFRkciLCJvcmdJZCI6IjAwRFhYMDAwMDAwYWJjZCIsImlhdCI6MT699876543,"exp":1699880143,"iss":"salesforce"}",
    "expiresIn": 3600,
    "tokenType": "Bearer"
  }
}
```

#### Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| `401` | `UNAUTHORIZED` | Invalid or expired Salesforce session |
| `403` | `FORBIDDEN` | User does not have permission to access Insight features |
| `500` | `INTERNAL_SERVER_ERROR` | Failed to generate JWT token |
| `503` | `SERVICE_UNAVAILABLE` | Salesforce Remote Action service is unavailable |

#### Usage Notes

- The JWT token is typically valid for 1 hour (3600 seconds)
- Store the token securely and refresh before expiration
- Include the token in subsequent requests: `Authorization: Bearer <token>`

---

### Get Namespace Configuration

Retrieves the namespace configuration from Salesforce for the Insight application.

```
GET /namespace
```

#### Description

This endpoint returns the Salesforce namespace prefix configuration used by the Insight application. The namespace is essential for correctly referencing Salesforce objects, fields, and Remote Actions in managed package installations.

#### Request Parameters

This endpoint does not require any parameters.

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| — | — | — | — | No parameters required |

#### Request Example

```bash
curl -X GET \
  'https://your-instance.salesforce.com/apex/InsightCategoryUI/namespace' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<salesforce_session_id>'
```

#### Response Example

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "namespace": "InsightVA",
    "prefix": "InsightVA__",
    "isManaged": true
  }
}
```

**Response for Unmanaged Package (200 OK)**

```json
{
  "success": true,
  "data": {
    "namespace": "",
    "prefix": "",
    "isManaged": false
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `namespace` | `string` | The namespace prefix without underscores |
| `prefix` | `string` | The full prefix to use when referencing custom objects/fields (includes `__`) |
| `isManaged` | `boolean` | Indicates whether the package is installed as a managed package |

#### Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| `401` | `UNAUTHORIZED` | Invalid or expired Salesforce session |
| `500` | `INTERNAL_SERVER_ERROR` | Failed to retrieve namespace configuration |
| `503` | `SERVICE_UNAVAILABLE` | Salesforce Remote Action service is unavailable |

#### Usage Notes

- The namespace configuration should be retrieved once during application initialization
- Use the `prefix` value when constructing references to custom Salesforce objects and fields
- For unmanaged packages, the namespace and prefix will be empty strings

---

## Authentication Flow

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Browser   │     │  Salesforce VF  │     │  Insight Backend │
│  (React App)│     │     Page        │     │     Services     │
└──────┬──────┘     └────────┬────────┘     └────────┬─────────┘
       │                     │                       │
       │  1. Load App        │                       │
       │────────────────────>│                       │
       │                     │                       │
       │  2. GET /namespace  │                       │
       │────────────────────>│                       │
       │                     │                       │
       │  3. Namespace Config│                       │
       │<────────────────────│                       │
       │                     │                       │
       │  4. GET /jwt        │                       │
       │────────────────────>│                       │
       │                     │                       │
       │  5. JWT Token       │                       │
       │<────────────────────│                       │
       │                     │                       │
       │  6. API Request with Bearer Token           │
       │─────────────────────────────────────────────>
       │                     │                       │
       │  7. API Response    │                       │
       │<─────────────────────────────────────────────
       │                     │                       │
```

## Related Documentation

- [Categories API](./categories.md) - Category management endpoints
- [Prompts API](./prompts.md) - AI prompt configuration endpoints
- [Users API](./users.md) - User management endpoints