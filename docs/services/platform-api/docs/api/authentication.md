# Authentication Endpoints

This document covers all authentication, authorization, OAuth, and session management endpoints for the Platform API.

## Overview

The Platform API supports multiple authentication mechanisms:
- **Token-based authentication** - Standard API tokens for service-to-service communication
- **Two-factor authentication (2FA)** - TOTP-based second factor for enhanced security
- **Salesforce SSO** - Single sign-on integration with Salesforce
- **Temporary authentication** - Short-lived tokens for specific operations

## Base URL

All endpoints are relative to: `https://api.platform.example.com`

---

## Endpoints

### Create Authentication Token

Creates an authentication token for the specified entity type.

```
GET /auth/:entity
```

#### Description

Generates an authentication token for a user, service, or other entity. The token can be used in subsequent API requests via the `Authorization` header.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity type for authentication (e.g., `user`, `service`, `admin`) |
| `username` | string | query | Yes | Username or identifier for the entity |
| `password` | string | query | Yes | Password or secret key |
| `org_id` | integer | query | No | Organization ID (required for user entities) |
| `ttl` | integer | query | No | Token time-to-live in seconds (default: 3600) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/auth/user?username=john.doe&password=secret123&org_id=1001" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    "expires_at": "2024-01-15T14:30:00Z",
    "token_type": "Bearer",
    "entity": {
      "id": 12345,
      "type": "user",
      "org_id": 1001
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing required parameters |
| 401 | Unauthorized - Invalid credentials |
| 403 | Forbidden - Account locked or disabled |
| 404 | Not Found - Entity type not recognized |
| 429 | Too Many Requests - Rate limit exceeded |

---

### Service Authentication

Authenticates a service or performs authentication with POST data.

```
POST /auth/:entity
```

#### Description

Performs service-level authentication using POST body for credentials. Preferred for sensitive authentication data that should not appear in URLs or server logs.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity type (e.g., `service`, `api`, `system`) |
| `client_id` | string | body | Yes | Service client identifier |
| `client_secret` | string | body | Yes | Service client secret |
| `scope` | string | body | No | Requested permission scope (comma-separated) |
| `grant_type` | string | body | No | OAuth grant type (default: `client_credentials`) |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/auth/service" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "client_id": "svc_billing_processor",
    "client_secret": "sk_live_abc123xyz789",
    "scope": "billing:read,billing:write",
    "grant_type": "client_credentials"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "access_token": "srv_token_abc123def456ghi789",
    "token_type": "Bearer",
    "expires_in": 7200,
    "scope": "billing:read,billing:write",
    "service": {
      "client_id": "svc_billing_processor",
      "name": "Billing Processor Service"
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid request body |
| 401 | Unauthorized - Invalid client credentials |
| 403 | Forbidden - Service disabled or scope not permitted |
| 422 | Unprocessable Entity - Invalid grant type |

---

### Destroy Authentication Token (Logout)

Invalidates the current authentication token.

```
DELETE /auth
```

#### Description

Destroys the current session and invalidates the authentication token. After calling this endpoint, the token can no longer be used for authenticated requests.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `Authorization` | string | header | Yes | Bearer token to invalidate |
| `all_sessions` | boolean | query | No | If `true`, invalidates all tokens for the user (default: `false`) |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/auth" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "message": "Token successfully invalidated",
  "data": {
    "logged_out_at": "2024-01-15T12:45:30Z",
    "sessions_terminated": 1
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - No valid token provided |
| 500 | Internal Server Error - Failed to invalidate token |

---

### Get Two-Factor Authentication Barcode

Generates a QR code for setting up two-factor authentication.

```
GET /auth/twofactor/barcode
```

#### Description

Returns a QR code image that can be scanned by authenticator apps (Google Authenticator, Authy, etc.) to set up TOTP-based two-factor authentication.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `Authorization` | string | header | Yes | Bearer token for authenticated user |
| `format` | string | query | No | Image format: `png`, `svg` (default: `png`) |
| `size` | integer | query | No | QR code size in pixels (default: 200) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/auth/twofactor/barcode?format=png&size=250" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -o qrcode.png
```

#### Response Example

Returns binary image data with appropriate Content-Type header (`image/png` or `image/svg+xml`).

For JSON response (when `Accept: application/json`):

```json
{
  "status": "success",
  "data": {
    "barcode_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADI...",
    "provisioning_uri": "otpauth://totp/Platform:john.doe?secret=JBSWY3DPEHPK3PXP&issuer=Platform",
    "expires_at": "2024-01-15T13:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - 2FA already enabled for this account |
| 409 | Conflict - 2FA setup already in progress |

---

### Get Two-Factor Authentication Secret

Retrieves the TOTP secret for manual two-factor authentication setup.

```
GET /auth/twofactor/secret
```

#### Description

Returns the raw TOTP secret key for users who prefer to manually enter it into their authenticator app instead of scanning a QR code.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `Authorization` | string | header | Yes | Bearer token for authenticated user |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/auth/twofactor/secret" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "secret": "JBSWY3DPEHPK3PXP",
    "algorithm": "SHA1",
    "digits": 6,
    "period": 30,
    "issuer": "Platform",
    "account_name": "john.doe@example.com",
    "provisioning_uri": "otpauth://totp/Platform:john.doe@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Platform&algorithm=SHA1&digits=6&period=30"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - 2FA already enabled for this account |
| 409 | Conflict - 2FA setup already in progress |

---

### Create Salesforce SSO Token (GET)

Creates a Salesforce Single Sign-On authentication token.

```
GET /auth/salesforce
```

#### Description

Initiates Salesforce SSO authentication flow. Returns a redirect URL or token based on the OAuth flow configuration.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `org_id` | integer | query | Yes | Organization ID configured for Salesforce SSO |
| `redirect_uri` | string | query | No | URI to redirect after authentication |
| `state` | string | query | No | Opaque state value for CSRF protection |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/auth/salesforce?org_id=1001&redirect_uri=https://app.example.com/callback&state=xyz123" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "authorization_url": "https://login.salesforce.com/services/oauth2/authorize?client_id=xxx&redirect_uri=yyy&response_type=code&state=xyz123",
    "state": "xyz123",
    "expires_in": 300
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing organization ID |
| 404 | Not Found - Organization not configured for Salesforce SSO |
| 503 | Service Unavailable - Salesforce integration unavailable |

---

### Create Salesforce SSO Token (POST)

Completes Salesforce SSO authentication with authorization code.

```
POST /auth/salesforce
```

#### Description

Exchanges a Salesforce authorization code for an access token and creates a Platform API session.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `org_id` | integer | body | Yes | Organization ID |
| `code` | string | body | Yes | Authorization code from Salesforce OAuth callback |
| `redirect_uri` | string | body | Yes | Must match the redirect_uri used in authorization request |
| `state` | string | body | No | State value for validation |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/auth/salesforce" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "org_id": 1001,
    "code": "aPrxJqP9Qx2...",
    "redirect_uri": "https://app.example.com/callback",
    "state": "xyz123"
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "token": "platform_token_abc123def456",
    "token_type": "Bearer",
    "expires_at": "2024-01-15T16:00:00Z",
    "user": {
      "id": 12345,
      "email": "john.doe@example.com",
      "org_id": 1001,
      "salesforce_user_id": "005xx000001234AAA"
    },
    "salesforce": {
      "instance_url": "https://na1.salesforce.com",
      "access_token": "sf_access_token_xyz..."
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing required parameters |
| 401 | Unauthorized - Invalid authorization code |
| 403 | Forbidden - User not permitted for SSO |
| 404 | Not Found - Organization not found or SSO not configured |
| 409 | Conflict - State mismatch (potential CSRF) |

---

### Create Temporary Authentication Token

Creates a short-lived temporary authentication token for specific operations.

```
POST /tempauth
```

#### Description

Generates a temporary authentication token with limited scope and short expiration. Useful for one-time operations, file uploads, or delegated access scenarios.

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `Authorization` | string | header | Yes | Bearer token of the requesting user/service |
| `purpose` | string | body | Yes | Purpose of the temporary token (e.g., `file_upload`, `device_provision`, `report_download`) |
| `scope` | string | body | No | Limited scope for the token (subset of original permissions) |
| `ttl` | integer | body | No | Time-to-live in seconds (max: 3600, default: 300) |
| `single_use` | boolean | body | No | If `true`, token is invalidated after first use (default: `false`) |
| `metadata` | object | body | No | Additional metadata to associate with the token |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/tempauth" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "purpose": "file_upload",
    "scope": "files:write",
    "ttl": 600,
    "single_use": true,
    "metadata": {
      "max_file_size": 10485760,
      "allowed_types": ["audio/wav", "audio/mp3"]
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "temp_token": "tmp_abc123def456ghi789jkl012",
    "expires_at": "2024-01-15T12:55:00Z",
    "purpose": "file_upload",
    "scope": "files:write",
    "single_use": true,
    "metadata": {
      "max_file_size": 10485760,
      "allowed_types": ["audio/wav", "audio/mp3"]
    },
    "created_by": {
      "user_id": 12345,
      "org_id": 1001
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid purpose or parameters |
| 401 | Unauthorized - Invalid or missing authorization token |
| 403 | Forbidden - Not permitted to create temporary tokens |
| 422 | Unprocessable Entity - Requested scope exceeds permissions |
| 429 | Too Many Requests - Rate limit for temporary token creation exceeded |

---

## Authentication Usage

### Using Tokens in Requests

Once you have obtained an authentication token, include it in the `Authorization` header of subsequent requests:

```bash
curl -X GET "https://api.platform.example.com/users/12345" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Refresh

Tokens should be refreshed before expiration by obtaining a new token with valid credentials. There is no dedicated refresh endpoint; simply re-authenticate using the standard authentication endpoints.

### Two-Factor Authentication Flow

1. User authenticates with username/password via `GET /auth/user`
2. If 2FA is enabled, response includes `requires_2fa: true`
3. User calls the same endpoint with additional `totp_code` parameter
4. Full authentication token is returned upon successful 2FA verification

```bash
# Step 1: Initial authentication
curl -X GET "https://api.platform.example.com/auth/user?username=john.doe&password=secret123&org_id=1001"

# Response: {"status": "pending", "requires_2fa": true, "session_token": "2fa_session_xyz"}

# Step 2: Complete with TOTP code
curl -X GET "https://api.platform.example.com/auth/user?session_token=2fa_session_xyz&totp_code=123456"
```

---

## Related Documentation

- [Users and Groups](users-and-groups.md) - User management endpoints
- [Organizations](organizations.md) - Organization management
- [System](system.md) - System-level operations and QR code generation